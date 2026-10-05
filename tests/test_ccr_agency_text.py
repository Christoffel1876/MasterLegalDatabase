"""Offline native research checks with complete synthetic captured source evidence."""
from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pymupdf
import pytest

from geode.pipeline import ccr_agency_capture_v2 as c
from geode.pipeline import ccr_agency_text as m
from tests.test_ccr_agency_capture_v2 import Fixture, _replace, _save, packet


@pytest.fixture
def source(packet: Fixture, tmp_path: Path) -> tuple[Path, str]:
    """Build an independently verified synthetic source capture for native tests."""
    root, plan, bodies = packet
    pin = _save(root, plan, bodies)
    output = tmp_path / 'capture'
    manifest = c.build(root, root / 'PLAN.json', output, pin)
    return output, c.sha(c.encoded(manifest))


def _build(source: tuple[Path, str], tmp_path: Path) -> tuple[Path, str]:
    root, pin = source
    output = tmp_path / 'native'
    manifest = m.build(root, output, m.InputPlan(capture_manifest_sha256=pin))
    return output, c.sha(c.encoded(manifest))


def _reseal(output: Path) -> str:
    value = json.loads((output / 'MANIFEST.json').read_bytes())
    value['files'] = [m._asset(p.relative_to(output).as_posix(), p.read_bytes()).model_dump()
                      for p in sorted(output.rglob('*'))
                      if p.is_file() and p != output / 'MANIFEST.json']
    raw = c.encoded(m.Manifest.model_validate_json(json.dumps(value)))
    (output / 'MANIFEST.json').write_bytes(raw)
    return c.sha(raw)


def test_portable_whole_page_and_no_match(source: tuple[Path, str], tmp_path: Path) -> None:
    """Search returns an entire physical page and truthful partial/unsupported scope."""
    output, pin = _build(source, tmp_path)
    moved = tmp_path / 'relocated'
    shutil.copytree(output, moved)
    manifest = m.verify(moved, pin)
    result = m.query(moved, pin, 'SYNTHETIC')
    assert manifest.page_associations == 1 and manifest.unique_physical_pages == 1
    assert result.hits[0].native_text == 'SYNTHETIC SOURCE ONLY\n'
    assert result.hits[0].document.response.claim.requested_url.startswith('https://')
    assert result.hits[0].document.version.designation == 'current'
    assert result.scope.catalog_agencies == 2
    assert len(result.scope.unselected_listing_rules) == 2
    assert result.scope.unsupported_word_associations == 1
    assert result.scope.unselected_agency_ids == ['133']
    assert not result.answer_safe and not result.scope.department_complete
    citation = m.query(moved, pin, '5 CCR 1002-1', mode='citation')
    assert citation.total_matching_page_associations == 1
    empty = m.query(moved, pin, 'not present anywhere')
    assert not empty.hits and empty.scope == result.scope
    assert 'No match' in empty.warning
    source_manifest = (source[0] / 'MANIFEST.json').read_bytes()
    assert (moved / 'capture/MANIFEST.json').read_bytes() == source_manifest


@pytest.mark.parametrize('text,mode,limit', [('', 'phrase', 1), (' ', 'phrase', 1),
                                          ('x' * 501, 'phrase', 1), ('x', 'legal', 1),
                                          ('x', 'phrase', 0), ('x', 'phrase', 51)])
def test_bad_query_before_source_access(tmp_path: Path, text: str, mode: str, limit: int) -> None:
    """Invalid query modes and unbounded results refuse before opening any source package."""
    with pytest.raises(ValueError):
        m.query(tmp_path / 'absent', 'a' * 64, text, mode=mode, limit=limit)


@pytest.mark.parametrize('values', [[], ['b' * 64, 'a' * 64], ['a' * 64, 'a' * 64]])
def test_selection_model_refusals(values: list[str]) -> None:
    """Selections name whole hashes once and never silently coalesce caller mistakes."""
    with pytest.raises(ValueError):
        m.InputPlan(capture_manifest_sha256='a' * 64, selected_pdf_sha256=values)


def test_absent_selection_and_wrong_pins(source: tuple[Path, str], tmp_path: Path) -> None:
    """Exact caller pins and membership constrain which original may become searchable."""
    root, pin = source
    with pytest.raises(ValueError, match='manifest pin'):
        m.build(root, tmp_path / 'wrong', m.InputPlan(capture_manifest_sha256='f' * 64))
    with pytest.raises(ValueError, match='absent'):
        m.build(root, tmp_path / 'unselected', m.InputPlan(
            capture_manifest_sha256=pin, selected_pdf_sha256=['f' * 64]))
    output, manifest_pin = _build(source, tmp_path)
    with pytest.raises(ValueError, match='Native manifest pin'):
        m.verify(output, 'f' * 64)
    with pytest.raises(ValueError, match='already exists'):
        m.build(root, output, m.InputPlan(capture_manifest_sha256=pin))
    assert m.verify(output, manifest_pin).scope.capture_selected_rules == 1


@pytest.mark.parametrize('mutation', ['extra', 'missing', 'symlink', 'fifo', 'directory',
                                     'native', 'schema', 'record', 'embedded_body',
                                     'embedded_schema', 'embedded_capture',
                                     'input', 'manifest_count'])
def test_mutation_and_reseal_refusals(source: tuple[Path, str], tmp_path: Path,
                                     mutation: str) -> None:
    """Resealing does not bless altered native pages, source bytes, identities or schemas."""
    output, pin = _build(source, tmp_path)
    if mutation == 'extra':
        (output / 'private.txt').write_text('extra')
    elif mutation == 'missing':
        (output / 'documents.jsonl').unlink()
    elif mutation == 'symlink':
        (output / 'extra').symlink_to(output / 'INPUT.json')
    elif mutation == 'fifo':
        os.mkfifo(output / 'pipe')
    elif mutation == 'directory':
        (output / 'empty').mkdir()
    else:
        if mutation == 'native':
            next((output / 'native').rglob('*.txt')).write_text('FABRICATED UNREVIEWED TEXT')
        elif mutation == 'schema':
            (output / 'Page.schema.json').write_text('{}')
        elif mutation == 'record':
            body = (output / 'documents.jsonl').read_bytes().replace(
                b'Source title 1', b'Fabricated title')
            (output / 'documents.jsonl').write_bytes(body)
        elif mutation.startswith('embedded'):
            if mutation == 'embedded_body':
                next((output / 'capture/bodies').glob('*')).write_bytes(b'changed')
            elif mutation == 'embedded_schema':
                (output / 'capture/Plan.schema.json').write_text('{}')
            else:
                (output / 'capture/CAPTURE.json').write_text('{}')
        elif mutation == 'input':
            value = json.loads((output / 'INPUT.json').read_bytes())
            value['capture_manifest_sha256'] = 'a' * 64
            (output / 'INPUT.json').write_text(json.dumps(value))
        else:
            value = json.loads((output / 'MANIFEST.json').read_bytes())
            value['page_associations'] = 2
            (output / 'MANIFEST.json').write_text(json.dumps(value))
        pin = _reseal(output)
    with pytest.raises((ValueError, FileNotFoundError)):
        m.verify(output, pin)


def test_captured_buffer_native_derivation(source: tuple[Path, str], tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """A post-capture original mutation cannot contaminate emitted native text."""
    root, _ = source
    real = m._outputs

    def mutate(plan: m.InputPlan, original: dict[str, bytes]
               ) -> tuple[dict[str, bytes], m.Manifest]:
        next((root / 'bodies').glob('*')).write_bytes(b'LATE MUTATION')
        return real(plan, original)

    monkeypatch.setattr(m, '_outputs', mutate)
    output, pin = _build(source, tmp_path)
    assert m.query(output, pin, 'SYNTHETIC').hits


def test_empty_native_retained_without_invented_text(packet: Fixture, tmp_path: Path) -> None:
    """A blank scanned-style page is a retained empty native page, not discarded evidence."""
    root, plan, bodies = packet
    with pymupdf.open() as pdf:
        pdf.new_page()
        raw = pdf.tobytes()
    _replace(plan, bodies, 'pdf', raw)
    pin = _save(root, plan, bodies)
    captured = tmp_path / 'blank-capture'
    manifest = c.build(root, root / 'PLAN.json', captured, pin)
    output, native_pin = _build((captured, c.sha(c.encoded(manifest))), tmp_path)
    result = m.query(output, native_pin, 'anything')
    assert result.scope.empty_native_associations == 1
    assert result.total_matching_page_associations == 0
    assert m.verify(output, native_pin).unique_physical_pages == 1


def test_aliases_and_explicit_whole_pdf_selection(packet: Fixture, tmp_path: Path) -> None:
    """Aliases preserve both source associations while selected/unselected PDF scope is explicit."""
    root, plan, bodies = packet
    history = next(r for r in plan['responses'] if r['role'] == 'history')
    raw = bodies[history['body']['path']]
    from tests.test_ccr_agency_capture_v2 import _version
    raw = raw.replace(b'<b>Archived Versions</b>',
                      ('<b>Future Versions</b>' + _version('11', '5 CCR 1002-1')
                       + '<b>Archived Versions</b>').encode())
    _replace(plan, bodies, 'history', raw)
    first_pdf = plan['responses'][-2]['body']['sha256']
    for old in copy.deepcopy(plan['responses'][-2:]):
        old['association_id'] += '_future'
        for key in ['requested_url', 'observed_final_url']:
            old['claim'][key] = old['claim'][key].replace('ruleVersionId=10', 'ruleVersionId=11')
        plan['responses'].append(old)
    pin = _save(root, plan, bodies)
    captured = tmp_path / 'aliases'
    manifest = c.build(root, root / 'PLAN.json', captured, pin)
    output, native_pin = _build((captured, c.sha(c.encoded(manifest))), tmp_path)
    result = m.query(output, native_pin, 'synthetic', limit=1)
    assert result.total_matching_page_associations == 2 and result.truncated
    assert m.verify(output, native_pin).unique_physical_pages == 1
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((30, 30), 'DISTINCT FUTURE ORIGINAL')
        _replace(plan, bodies, 'pdf_future', pdf.tobytes())
    pin = _save(root, plan, bodies)
    captured2 = tmp_path / 'distinct'
    manifest = c.build(root, root / 'PLAN.json', captured2, pin)
    output2 = tmp_path / 'selected-native'
    native_manifest = m.build(captured2, output2, m.InputPlan(
        capture_manifest_sha256=c.sha(c.encoded(manifest)), selected_pdf_sha256=[first_pdf]))
    selected_pin = c.sha(c.encoded(native_manifest))
    no_match = m.query(output2, selected_pin, 'DISTINCT FUTURE')
    assert not no_match.hits and len(no_match.scope.unselected_pdf_sha256) == 1
    assert native_manifest.scope.capture_document_associations == 4


@pytest.mark.parametrize('cap', ['MAX_FILES', 'MAX_TOTAL_BYTES', 'MAX_DOCUMENTS', 'MAX_PAGES',
                                'MAX_TEXT_BYTES', 'MAX_FILE_BYTES'])
def test_native_caps_refuse_before_write(source: tuple[Path, str], tmp_path: Path,
                                        monkeypatch: pytest.MonkeyPatch, cap: str) -> None:
    """Original, extraction and actual closed-output budgets are enforced separately."""
    root, pin = source
    monkeypatch.setattr(m, cap, 0)
    with pytest.raises(ValueError):
        m.build(root, tmp_path / 'blocked', m.InputPlan(capture_manifest_sha256=pin))
    assert not (tmp_path / 'blocked').exists()


def test_atomic_partial_is_preserved(source: tuple[Path, str], tmp_path: Path,
                                     monkeypatch: pytest.MonkeyPatch) -> None:
    """Failed publication preserves its partial directory and cannot be silently resumed."""
    root, pin = source
    original = m.atomic_new
    calls = 0

    def fail(path: Path, raw: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError('simulated interruption')
        original(path, raw)

    monkeypatch.setattr(m, 'atomic_new', fail)
    output = tmp_path / 'partial'
    with pytest.raises(OSError):
        m.build(root, output, m.InputPlan(capture_manifest_sha256=pin))
    assert output.is_dir() and not (output / 'MANIFEST.json').exists()
    with pytest.raises(ValueError, match='already exists'):
        m.build(root, output, m.InputPlan(capture_manifest_sha256=pin))


def test_cli_all_routes(source: tuple[Path, str], tmp_path: Path,
                        capsys: pytest.CaptureFixture[str]) -> None:
    """CLI results are strict model JSON and expose only offline research operations."""
    root, pin = source
    output = tmp_path / 'cli-native'
    assert m.main(['build', '--source', str(root), '--capture-sha256', pin,
                   '--output', str(output)]) == 0
    manifest = m.Manifest.model_validate_json(capsys.readouterr().out)
    manifest_pin = c.sha(c.encoded(manifest))
    common = ['--root', str(output), '--manifest-sha256', manifest_pin]
    assert m.main(['verify', *common]) == 0
    m.Manifest.model_validate_json(capsys.readouterr().out)
    assert m.main(['query', *common, '--text', 'SYNTHETIC']) == 0
    assert m.QueryResult.model_validate_json(capsys.readouterr().out).hits


@pytest.mark.parametrize('mutation', ['schema', 'scope', 'projection', 'extra', 'member'])
def test_resealed_embedded_source_semantics(source: tuple[Path, str], tmp_path: Path,
                                          mutation: str) -> None:
    """A new external capture pin cannot bypass V2's schema, projection and semantic gates."""
    root, _ = source
    if mutation == 'schema':
        (root / 'Plan.schema.json').write_text('{}')
    elif mutation == 'scope':
        value = json.loads((root / 'CAPTURE.json').read_bytes())
        value['selected_rule_count'] = 2
        (root / 'CAPTURE.json').write_text(json.dumps(value))
    elif mutation == 'projection':
        value = json.loads((root / 'PLAN.json').read_bytes())
        old = value['responses'][-1]['body']['path']
        new = 'bodies/renamed.bin'
        (root / old).rename(root / new)
        value['responses'][-1]['body']['path'] = new
        (root / 'PLAN.json').write_text(json.dumps(value))
    elif mutation == 'extra':
        (root / 'extra.json').write_text('{}')
    else:
        (root / 'CAPTURE.json').write_text('{}')
    refs = [c.Asset(path=p.relative_to(root).as_posix(), sha256=c.sha(p.read_bytes()),
                    bytes=p.stat().st_size) for p in sorted(root.rglob('*'))
            if p.is_file() and p.name != 'MANIFEST.json']
    raw = c.encoded(c.Manifest(files=refs))
    (root / 'MANIFEST.json').write_bytes(raw)
    with pytest.raises(ValueError):
        m.build(root, tmp_path / 'refused', m.InputPlan(capture_manifest_sha256=c.sha(raw)))


def test_manifest_inclusive_native_cap(source: tuple[Path, str], tmp_path: Path,
                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """A package whose payload alone fits still needs room for its exact manifest."""
    output, pin = _build(source, tmp_path)
    manifest = m.Manifest.model_validate_json((output / 'MANIFEST.json').read_bytes())
    monkeypatch.setattr(m, 'MAX_TOTAL_BYTES', sum(r.size_bytes for r in manifest.files))
    with pytest.raises(ValueError, match='budget'):
        m.verify(output, pin)
