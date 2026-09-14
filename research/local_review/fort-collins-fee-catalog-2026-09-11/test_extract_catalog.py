"""Offline source fidelity, byte custody and deterministic replay checks."""
from __future__ import annotations

import copy
import hashlib
import html
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

import extract_catalog as catalog

BASE = Path(__file__).parent


def test_snapshot_replay_and_schema() -> None:
    """The full preserved source reproduces the distributed record and schema."""
    result = catalog.extract(BASE)
    raw = (BASE / 'extraction.json').read_bytes()
    assert catalog.serialize(result) == raw
    schema = json.loads((BASE / 'extraction.schema.json').read_bytes())
    assert schema == catalog.Extraction.model_json_schema()
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    assert result.source_capture_completed_at.isoformat() == '2026-09-10T22:06:37.843075+00:00'


def test_all_source_bytes_and_content_bindings() -> None:
    """Independently verify every slice and token's ownership and exact text."""
    d = json.loads((BASE / 'extraction.json').read_bytes())
    body = (BASE / 'source/SD004-14.html').read_bytes()
    slices = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            if set(value) == {'start', 'end', 'sha256'}:
                slices.append(value)
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(d)
    for part in slices:
        assert 0 <= part['start'] <= part['end'] <= len(body)
        assert hashlib.sha256(body[part['start']:part['end']]).hexdigest() == part['sha256']
    fragments = {f['id']: f for f in d['text_fragments']}
    assert len(fragments) == len(d['text_fragments'])
    for f in fragments.values():
        raw = body[f['source']['start']:f['source']['end']].decode('utf-8')
        expected = ('\n' if f['kind'] == 'br_break' else
                    html.unescape(raw) if f['kind'] in {'entity', 'character_reference'} else raw)
        assert f['dom_text'] == expected
        assert hashlib.sha256(expected.encode()).hexdigest() == f['dom_text_sha256']
    owners = Counter()
    ordered_starts = []
    contents = {}
    for block in d['blocks']:
        items = ([cell for row in block['table_rows'] for cell in row['cells']]
                 if block['kind'] == 'table' else [block])
        for item in items:
            owners.update(item['fragment_ids'])
            contents[item['id']] = item
            if item['dom_text'] is not None:
                dom = ''.join(fragments[fid]['dom_text'] for fid in item['fragment_ids'])
                assert item['dom_text'] == dom
                assert item['normalized_text'] == catalog.normalize(dom)
            ordered_starts.extend(fragments[fid]['source']['start'] for fid in item['fragment_ids'])
    assert ordered_starts == sorted(ordered_starts)
    assert all(count == 1 for count in owners.values())
    nonblank = {fid for fid, f in fragments.items() if catalog.normalize(f['dom_text'])}
    assert nonblank <= owners.keys()
    assert set(fragments) - owners.keys() == set(
        d['coverage']['unassigned_whitespace_fragment_ids'])
    assert len(nonblank) == 674
    element_anchors = [el for el in d['elements'] if el['tag'] == 'a' and
                       any(a['name'] == 'href' for a in el['attributes'])]
    assert len(element_anchors) == len(d['anchors']) == 48
    assert {a['locator'] for a in element_anchors} == {a['element_locator'] for a in d['anchors']}
    assert len(slices) == 5144
    for date in d['printed_date_mentions']:
        text = contents[date['content_id']]['normalized_text']
        assert text[date['normalized_start']:date['normalized_end']] == date['literal']


def test_tables_lists_and_distinct_source_conditions() -> None:
    """All nine tables and material fee prose survive, without parent-list duplication."""
    d = catalog.extract(BASE)
    tables = [b for b in d.blocks if b.kind == 'table']
    assert [len(b.table_rows) for b in tables] == [14, 25, 5, 5, 3, 7, 5, 6, 6]
    assert sum(len(row.cells) for b in tables for row in b.table_rows) == 238
    assert d.coverage.list_item_fragment_count == 213
    by_component = {c.label: '\n'.join(b.normalized_text or '' for b in d.blocks
                                      if b.component_id == c.id) for c in d.components}
    assert 'Jan. 1, 2024' in by_component['Development Review Fees']
    assert 'January 1, 2026' in by_component[
        'Capital Expansion Fees (including Transportation Capital Expansion Fees)']
    utility = by_component['Utilities Fees']
    for phrase in ['in 2022', '$63,800', '$0.196', '1.92', '$214.04']:
        assert phrase in utility
    assert any(a.raw_href_decoded == '/utilityfees@fortcollins.gov' for a in d.anchors)
    cef = by_component['Capital Expansion Fees (including Transportation Capital Expansion Fees)']
    for phrase in ['$268', '$376', '$457', '$535', '$600', '$653', '$698', '$702', '$414', '$165']:
        assert phrase in cef
    assert all(not a.resource_opened_by_this_extraction for a in d.anchors)
    assert any(b.parent_list_item_locator for b in d.blocks if b.kind == 'list_item_fragment')


def test_parser_preserves_entity_whitespace_unicode_and_void_tags() -> None:
    """HTML decoding is explicit; native Unicode and source spellings remain bound."""
    body = ('<div>A\u00a0 &amp; B &#x2013; C &copy<br/>\n'
            '<img src="x"/></img><span/> D</div>').encode()
    parser = catalog.SourceParser(body)
    parser.feed(parser.text)
    parser.close()
    fragments = catalog.text_fragments(parser.nodes[0])
    assert ''.join(f.dom_text for f in fragments) == 'A\u00a0 & B – C ©\n\n D'
    assert catalog.normalize(' e\u0301\u00a0\n X ') == 'e\u0301 X'
    assert all(f.source.sha256 == catalog.sha256(body[f.source.start:f.source.end])
               for f in fragments)
    assert catalog.ancestor(parser.nodes[0], lambda _: False) is None


def test_parser_reports_closure_repairs_and_unmatched_tags() -> None:
    """Malformed structure cannot silently appear as repaired source evidence."""
    parser = catalog.SourceParser(b'<div><span>x</div>')
    parser.feed(parser.text)
    assert len(parser.implicit_closures) == 1
    bad = catalog.SourceParser(b'</other>')
    with pytest.raises(ValueError, match='Unmatched'):
        bad.feed(bad.text)


@pytest.mark.parametrize('mutation', ['unknown', 'repeat', 'missing', 'count'])
def test_schema_rejects_invalid_accounting(mutation: str) -> None:
    """Strict output validation rejects extraneous fields and declared content loss."""
    d = json.loads((BASE / 'extraction.json').read_bytes())
    if mutation == 'unknown':
        d['claim_current_law'] = True
    elif mutation == 'repeat':
        d['blocks'].append(copy.deepcopy(d['blocks'][0]))
    elif mutation == 'missing':
        d['coverage']['unassigned_nonblank_fragment_ids'] = ['t000489']
    else:
        d['coverage']['assigned_nonblank_text_fragment_count'] -= 1
    with pytest.raises(ValidationError):
        catalog.Extraction.model_validate_json(json.dumps(d))


def test_bad_ranges_table_duplicates_and_symlink_are_rejected(tmp_path: Path) -> None:
    """Reject ambiguous table transcripts, inverted slices and symlink file inputs."""
    with pytest.raises(ValidationError):
        catalog.ByteRange(start=2, end=1, sha256='a' * 64)
    d = catalog.extract(BASE)
    table = next(b for b in d.blocks if b.kind == 'table').model_dump()
    table['dom_text'] = 'duplicate'
    with pytest.raises(ValidationError, match='only in cells'):
        catalog.Block.model_validate(table)
    table['dom_text'] = None
    table['kind'] = 'paragraph'
    with pytest.raises(ValidationError, match='Non-table'):
        catalog.Block.model_validate(table)
    image = next(b for b in d.blocks if b.kind == 'image').model_dump()
    image['fragment_ids'] = ['x']
    with pytest.raises(ValidationError, match='Image alt'):
        catalog.Block.model_validate(image)
    link = tmp_path / 'link.html'
    link.symlink_to(BASE / 'source/SD004-14.html')
    with pytest.raises(ValueError, match='Symlink'):
        catalog.file_identity(link, tmp_path)


def test_cli_write_once_replay_and_tamper_detection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLI rejects source/output/schema tampering and refuses overwriting saved evidence."""
    shutil.copytree(BASE / 'source', tmp_path / 'source')
    shutil.copyfile(BASE / 'extract_catalog.py', tmp_path / 'extract_catalog.py')
    monkeypatch.setattr(catalog, '__file__', str(tmp_path / 'extract_catalog.py'))
    monkeypatch.setattr(sys, 'argv', ['extract_catalog.py'])
    assert catalog.main() == 0
    with pytest.raises(FileExistsError):
        catalog.main()
    monkeypatch.setattr(sys, 'argv', ['extract_catalog.py', '--verify'])
    assert catalog.main() == 0
    extraction = (tmp_path / 'extraction.json').read_bytes()
    (tmp_path / 'extraction.json').write_bytes(extraction + b' ')
    with pytest.raises(ValueError, match='deterministic source replay'):
        catalog.main()
    (tmp_path / 'extraction.json').write_bytes(extraction)
    (tmp_path / 'extraction.schema.json').write_bytes(b'{}')
    with pytest.raises(ValueError, match='Exported schema'):
        catalog.main()
    (tmp_path / 'source/SD004-14.html').write_bytes(b'changed')
    with pytest.raises(ValueError, match='Source body differs'):
        catalog.main()
