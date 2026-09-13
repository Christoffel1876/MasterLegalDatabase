"""Exercise dropped fee context, false source identity and incomplete native coverage."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

import verify_source_review as v

SOURCE = Path(__file__).parent.parent / 'pueblo-county-fees-source-review-revision'


@pytest.fixture
def data() -> tuple[dict[str, Any], dict[str, bytes]]:
    """Load independent copies of the exact currently reviewed source data."""
    qa = json.loads((SOURCE / 'SOURCE_QA.json').read_bytes())
    buffers = {p['native']['path']: (SOURCE / p['native']['path']).read_bytes()
               for p in qa['pages']}
    return qa, buffers


def test_complete_preserved_source() -> None:
    """Both source pages and all fee/continuation/note rows must verify together."""
    result = v.verify(SOURCE)
    assert result.physical_rows == 88 and result.labeled_fee_rows == 69
    assert result.legal_currentness == 'not_verified' and result.canonical_intakes == 0


@pytest.mark.parametrize('mutation', [
    'page_order', 'duplicate_row', 'row_page', 'row_id', 'fee_count', 'legal_date',
    'native_line_order', 'native_line_text', 'native_terminator', 'native_suffix',
    'column_roles', 'cell_wording', 'unknown_line', 'span_bounds', 'span_text',
    'row_association', 'column_association', 'unknown_context', 'bad_context_role',
    'marker_detached', 'byte_gap', 'byte_overlap', 'continuation_detached',
    'global_note_bound_to_appeals', 'land_division_detached', 'certificate_note_detached',
])
def test_structural_corruption_refused(
    data: tuple[dict[str, Any], dict[str, bytes]], mutation: str,
) -> None:
    """Do not let a coherent-looking table lose physical provenance or fee qualifications."""
    qa, buffers = copy.deepcopy(data)
    page = qa['pages'][0]
    row = page['rows'][2]
    cell = row['cells'][0]
    span = cell['spans'][0]
    by_id = {r['row_id']: r for p in qa['pages'] for r in p['rows']}
    if mutation == 'page_order':
        qa['pages'].reverse()
    elif mutation == 'duplicate_row':
        page['rows'][1]['row_id'] = row['row_id']
    elif mutation == 'row_page':
        row['physical_page'] = 2
    elif mutation == 'row_id':
        row['row_id'] = 'P1-99'
    elif mutation == 'fee_count':
        row['kind'] = 'continuation'
    elif mutation == 'legal_date':
        qa['adoption_date'] = '2025-05-08'
    elif mutation == 'native_line_order':
        page['native_lines'].reverse()
    elif mutation == 'native_line_text':
        page['native_lines'][0]['text'] += '!'
    elif mutation in {'native_terminator', 'native_suffix'}:
        name = page['native']['path']
        if mutation == 'native_suffix':
            buffers[name] += b'unassigned'
        else:
            pos = page['native_lines'][0]['end']
            buffers[name] = buffers[name][:pos] + b'X' + buffers[name][pos + 1:]
    elif mutation == 'column_roles':
        row['cells'].reverse()
    elif mutation == 'cell_wording':
        cell['native_text'] += ' exempt'
    elif mutation == 'unknown_line':
        span['line_id'] = 'P1-L999'
    elif mutation == 'span_bounds':
        span['start'] = -1
    elif mutation == 'span_text':
        span['text'] += '!'
        cell['native_text'] = '\n'.join(s['text'] for s in cell['spans'])
    elif mutation == 'row_association':
        span['bbox'][1:4:2] = [0, 1]
    elif mutation == 'column_association':
        span['bbox'][0:3:2] = [500, 600]
    elif mutation == 'unknown_context':
        row['section_context_ids'] = ['P1-99']
    elif mutation == 'bad_context_role':
        row['section_context_ids'] = ['P1-05']
    elif mutation == 'marker_detached':
        marked = next(r for r in by_id.values() if r['explicit_markers'])
        marked['note_ids_from_explicit_marker'] = []
    elif mutation in {'byte_gap', 'byte_overlap'}:
        if mutation == 'byte_gap':
            cell['spans'].pop()
        else:
            cell['spans'].append(copy.deepcopy(span))
        cell['native_text'] = '\n'.join(s['text'] for s in cell['spans'])
    elif mutation == 'continuation_detached':
        by_id['P1-04']['continues_row_id'] = None
    elif mutation == 'global_note_bound_to_appeals':
        by_id['P2-42']['section_context_ids'] = ['P2-38']
    elif mutation == 'land_division_detached':
        by_id['P2-01']['section_context_ids'] = []
    elif mutation == 'certificate_note_detached':
        by_id['P2-24']['group_marker_context_only'] = []
    with pytest.raises(ValueError):
        v.check_structure(qa, buffers)


def test_bad_source_asset() -> None:
    """An attractive filename cannot replace exact original PDF identity."""
    with pytest.raises(ValueError, match='Asset mismatch'):
        v.capture(SOURCE, {'path': 'original.pdf', 'sha256': '0' * 64, 'size_bytes': 75214})


@pytest.mark.parametrize('name', ['../original.pdf', '/private/tmp/fake.pdf', 'absent.pdf'])
def test_unsafe_or_missing_path(name: str) -> None:
    """Do not read outside the explicitly supplied ordinary package."""
    with pytest.raises(ValueError):
        v.ordinary(SOURCE, name)


def test_byte_limit() -> None:
    """Reject a response larger than the local verification read bound."""
    with pytest.raises(ValueError, match='byte cap'):
        v.ordinary(SOURCE, 'original.pdf', 10)


def test_resealed_review_not_trusted() -> None:
    """The caller cannot substitute a newly computed QA identity."""
    with pytest.raises(ValueError, match='QA pin'):
        v.verify(SOURCE, '0' * 64)


def test_late_schema_swap_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Schema text is itself pinned before JSON Schema sees any resolver directive."""
    original = v.ordinary

    def swapped(root: Path, name: str, limit: int = 2_000_000) -> bytes:
        if name == 'SOURCE_QA.schema.json':
            return b'{"$ref":"https://invalid.example/schema"}'
        return original(root, name, limit)

    monkeypatch.setattr(v, 'ordinary', swapped)
    with pytest.raises(ValueError, match='schema differs'):
        v.verify(SOURCE)
