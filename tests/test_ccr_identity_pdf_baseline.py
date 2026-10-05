"""Targeted identity, exact source binding and native-union refusal tests."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_ccr_identity_pdf_baseline import (
    Asset, Binding, Identity, compare_rows, coverage, document_pair, key, pages,
    unique_rows, validate_union,
)


def row(rule: str = '3', digest: str = 'a' * 64) -> Identity:
    """Build one typed source-bound selector without corpus I/O."""
    ref = Asset(path='source.pdf', sha256=digest, bytes=12)
    return Identity(department_id='1', agency_id='2', rule_id=rule,
        source_citation='1 CCR 2-3', source_kind='department_inventory',
        source_metadata=ref, history_url='https://www.sos.state.co.us/CCR/DisplayRule.do',
        source_cutoff_claim='2026-08-13', observed_at_claim='2026-10-05T00:00:00Z',
        bindings=[Binding(version_id='9', designation='current',
            pdf_url='https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=9',
            pdf=ref, word_url=None, word=None, physical_pages=1)])


def native(digest: str = 'a' * 64) -> dict:
    """One complete native page identity for an exact source PDF."""
    return {digest: pages.Original(sha256=digest, pages=[pages.Page(
        physical_page=1, text_sha256='b' * 64, text_bytes=2)])}


def test_exact_identity_union() -> None:
    record = row()
    assert validate_union([record], native(), {key(record)}) == {
        'department_count': 1, 'listed_identities': 1, 'pdf_bound_identities': 1,
        'paired_identities': 0, 'unique_pdf_originals': 1, 'unique_physical_pages': 1}


def test_duplicate_selector_refused() -> None:
    with pytest.raises(ValueError, match='Duplicate'):
        unique_rows([row(), row()])


@pytest.mark.parametrize('change', ['missing', 'foreign', 'changed_pdf', 'changed_version'])
def test_missing_foreign_or_changed_binding(change: str) -> None:
    record = row()
    if change == 'missing':
        changed = []
    elif change == 'foreign':
        changed = [row(rule='4')]
    elif change == 'changed_pdf':
        changed = [row(digest='c' * 64)]
    else:
        changed = [record.model_copy(update={'bindings': [record.bindings[0].model_copy(
            update={'version_id': '10'})]})]
    with pytest.raises(ValueError, match='Missing, foreign or changed'):
        compare_rows(changed, [record])


def test_declared_duplicate_cannot_mask_missing_identity() -> None:
    with pytest.raises(ValueError, match='Duplicate'):
        compare_rows([row(), row()], [row(), row(rule='4')])


@pytest.mark.parametrize('expected', [set(), {('1', '2', '4')}])
def test_selector_union_exact(expected: set) -> None:
    with pytest.raises(ValueError, match='Missing or foreign'):
        validate_union([row()], native(), expected)


@pytest.mark.parametrize('data', [{}, native('c' * 64), native() | native('c' * 64)])
def test_native_pdf_union_exact(data: dict) -> None:
    record = row()
    with pytest.raises(ValueError, match='does not equal'):
        validate_union([record], data, {key(record)})


def test_native_page_count_bound() -> None:
    record = row()
    record.bindings[0].physical_pages = 2
    with pytest.raises(ValueError, match='page count'):
        validate_union([record], native(), {key(record)})


def test_literal_history_document_pair() -> None:
    pdf = 'https://www.sos.state.co.us/CCR/GenerateRulePdf.do?ruleVersionId=9'
    word = pdf + '&type=word'
    assert document_pair([pdf, word]) == (pdf, word)
    for urls in ([pdf], [word], [pdf, pdf, word], [pdf, word, word]):
        with pytest.raises(ValueError, match='exactly one'):
            document_pair(urls)


def test_source_reference_changed(tmp_path: Path) -> None:
    raw = b'original'
    (tmp_path / 'body').write_bytes(raw)
    ref = Asset(path='body', sha256=coverage.sha(raw), bytes=len(raw))
    assert coverage.read(tmp_path, ref) == raw
    (tmp_path / 'body').write_bytes(b'changed!')
    with pytest.raises(ValueError, match='hash differs'):
        coverage.read(tmp_path, ref)


def test_source_symlink_refused(tmp_path: Path) -> None:
    (tmp_path / 'body').write_bytes(b'x')
    (tmp_path / 'alias').symlink_to(tmp_path / 'body')
    with pytest.raises(ValueError, match='Symlink'):
        coverage.read(tmp_path, Asset(path='alias', sha256=coverage.sha(b'x'), bytes=1))


@pytest.mark.parametrize('name', ['../outside', '/absolute', 'a/../b', 'a\\b'])
def test_source_path_escape_refused(name: str) -> None:
    with pytest.raises(ValueError):
        Asset(path=name, sha256='0' * 64, bytes=0)


def test_index_schema_mismatch_refused(tmp_path: Path) -> None:
    import json
    from verify_ccr_identity_pdf_baseline import read_index
    raw = b'{}'
    (tmp_path / 'INDEX.json').write_bytes(raw)
    (tmp_path / 'INDEX.schema.json').write_text(json.dumps({'type': 'object'}))
    with pytest.raises(ValueError, match='Index schema differs'):
        read_index(tmp_path / 'INDEX.json', coverage.sha(raw))


def test_index_pin_change_refused(tmp_path: Path) -> None:
    import json
    from verify_ccr_identity_pdf_baseline import Index, read_index
    (tmp_path / 'INDEX.json').write_bytes(b'{}')
    (tmp_path / 'INDEX.schema.json').write_text(json.dumps(Index.model_json_schema()))
    with pytest.raises(ValueError, match='Index pin differs'):
        read_index(tmp_path / 'INDEX.json', '0' * 64)
