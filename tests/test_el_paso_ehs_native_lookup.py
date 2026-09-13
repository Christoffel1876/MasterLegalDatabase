"""El Paso English source adapter regressions against accepted exact evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from scripts import research_source_lookup as lookup

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "tests/fixtures/el_paso_ehs_native_lookup"


@pytest.fixture
def copied_root(tmp_path: Path) -> Path:
    """Copy only accepted English evidence and its exact canonical custody into a fixture."""
    shutil.copytree(ROOT / lookup.EHS_PACKAGE, tmp_path / lookup.EHS_PACKAGE)
    destination = tmp_path / lookup.EHS_ACCEPTANCE
    destination.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / lookup.EHS_ACCEPTANCE, destination)
    line = (ROOT / lookup.EHS_PACKAGE / 'source/canonical-record.jsonl').read_bytes()
    record = json.loads(line)
    original = tmp_path / record['archive_path']
    original.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / record['archive_path'], original)
    manifest = tmp_path / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    manifest.write_bytes(line)
    return tmp_path


@pytest.mark.parametrize('source_id', [
    lookup.SOURCE_ID, lookup.GREELEY_SOURCE_ID, lookup.WELD_SOURCE_ID,
    *lookup.GRID_SOURCES, lookup.SPRINGS_SOURCE_ID,
])
def test_all_six_existing_outputs_unchanged(source_id: str) -> None:
    """Complete old JSON and Markdown output must be byte-identical to the pinned baseline."""
    result = lookup.lookup(ROOT, source_id, list_rows=True)
    folder = HERE / 'legacy-fixtures'
    actual_json = (result.model_dump_json(indent=2) + '\n').replace(str(ROOT), '__REPOSITORY__')
    actual_md = lookup.render_markdown(result).replace(str(ROOT), '__REPOSITORY__')
    assert actual_json == (folder / f'{source_id}.json').read_text()
    assert actual_md == (folder / f'{source_id}.md').read_text()


def test_all_rows_context_and_native_bindings() -> None:
    """Preserve all65rows,37contexts, group continuation and exact service/fee bytes."""
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, list_rows=True)
    assert result.status == 'matched' and len(result.rows) == 65 and len(result.context) == 37
    assert len({r.group for r in result.rows}) == 7
    row = next(r for r in result.rows if r.row_id == 'R031')
    assert row.physical_page == 3 and row.group_physical_page == 2
    assert row.fee == '$211.50 in 2024 ($368 in 2025)'
    for row in result.rows:
        for part in [row.label_native, row.fee_native, row.group_native]:
            raw = Path(part.native_file.path).read_bytes()[part.start:part.end]
            assert raw.decode() == part.text and hashlib.sha256(raw).hexdigest() == part.sha256
    assert result.source.original_http_acquired_at is None
    assert not result.source.original_http_independently_verified
    assert result.source.intake_received_at.isoformat() == '2026-09-12T22:59:48.795762+00:00'
    assert result.source.printed_approval_claim == 'October 25, 2023'
    assert result.source.printed_effective_claim == 'January 1, 2024'
    assert result.adoption_date is result.effective_date is None


@pytest.mark.parametrize('phrase,identity', [
    ('OWTS New Permit', 'R020'), ('OWTS Major Repair', 'R022'),
    ('RFE HACCP Plan Review Written', 'R059'), ('Special Event Permit- Full Menu', 'R058'),
])
def test_row_only_match_keeps_all_conditions(phrase: str, identity: str) -> None:
    """A narrow row search never strips notes, the Section2exception or source anomalies."""
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, phrase)
    assert [r.row_id for r in result.rows] == [identity]
    context = {c.context_id: c for c in result.context}
    assert set(lookup.EHS_GLOBAL) <= context.keys()
    assert 'except as' in context['B'].text and 'Section 2' in context['B'].text
    assert '$100 per day' in context['B'].text
    assert 'No fees will be assessed' in context['OTHER2'].text
    assert 'Inspection”' in context['D7'].text
    if identity == 'R020':
        assert 'STAR' in result.rows[0].linked_context
    if identity == 'R058':
        assert '$298.00 1 Event' in result.rows[0].fee
        assert '$298.00 for' not in result.rows[0].fee
    text = lookup.render_markdown(result)
    assert 'per-visit' in text and 'communicable' in text and 'Section 2' in text


@pytest.mark.parametrize('phrase', ['complaint investigations', '100 per day', '2024 FEE SCHEDULE'])
def test_context_search_does_not_invent_rows(phrase: str) -> None:
    """Shared notes/captions can match independently from actual service/fee cells."""
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, phrase)
    assert result.status == 'matched_context_only' and not result.rows
    assert result.matched_context_ids and len(result.context) == 37


def test_no_match_and_literal_zero() -> None:
    """Absence of a matching row is qualified, including numeric token boundaries."""
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, '0 per six months')
    assert result.status == 'no_matching_row' and not result.rows and len(result.context) == 37
    assert 'does not establish free' in lookup.render_markdown(result)


@pytest.mark.parametrize(
    'phrase', ['current fee', 'What do I owe?', 'applicable permit', 'effective'])
def test_refusal_before_source_access(phrase: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Current-law requests cannot be converted into source reporting."""
    monkeypatch.setattr(lookup, '_load_ehs_verified', lambda *a: pytest.fail('must not load'))
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, phrase)
    assert result.status == 'refused_current_law'
    assert not result.rows and not result.evidence_verified
    assert result.source is None and result.answer_safe is False


@pytest.mark.parametrize('source_id', ['el-paso-boh-ehs-fees-spanish-sd011', 'el-paso-fees', ''])
def test_unsupported_ids(source_id: str) -> None:
    """Only the exact English canonical identity is newly admitted."""
    with pytest.raises(ValueError, match='Unsupported'):
        lookup.lookup(ROOT, source_id, list_rows=True)


@pytest.mark.parametrize('name', ['SOURCE_QA.json', 'native/page-0003.txt',
                                 'pages/page-0005.png', 'build_review.py'])
def test_package_tamper_refused(copied_root: Path, name: str) -> None:
    """Every closed review/source dependency is checked before verifier execution."""
    path = copied_root / lookup.EHS_PACKAGE / name
    path.write_bytes(path.read_bytes() + b'tamper')
    with pytest.raises(ValueError):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_canonical_duplicate_refused(copied_root: Path) -> None:
    """A repeated selected raw record is ambiguous even if each line has the old bytes."""
    path = copied_root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    with path.open('rb') as handle:
        line = next(handle)
    with path.open('ab') as handle:
        handle.write(line)
    with pytest.raises(ValueError, match='canonical record'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_resealed_wrong_row_rejected_by_source_verifier(
        copied_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Replacing all test outer hashes cannot bless a fee detached from the source grid."""
    package = copied_root / lookup.EHS_PACKAGE
    path = package / 'SOURCE_QA.json'
    data = json.loads(path.read_bytes()); data['rows'][0]['fee'] = '$999.00'
    path.write_text(json.dumps(data))
    manifest_path = package / 'FINAL_MANIFEST.json'
    manifest = json.loads(manifest_path.read_bytes())
    for ref in manifest['files']:
        if ref['path'] == 'SOURCE_QA.json':
            ref.update(sha256=lookup._digest(path), size_bytes=path.stat().st_size)
    manifest_path.write_text(json.dumps(manifest))
    for name in ['SOURCE_QA.json', 'FINAL_MANIFEST.json']:
        monkeypatch.setitem(lookup.EHS_PINS, name, lookup._digest(package / name))
    acceptance_path = copied_root / lookup.EHS_ACCEPTANCE
    acceptance = json.loads(acceptance_path.read_bytes())
    for ref in acceptance['copied_originals']:
        if ref['path'] in {'SOURCE_QA.json', 'FINAL_MANIFEST.json'}:
            value = package / ref['path']
            ref.update(sha256=lookup._digest(value), size_bytes=value.stat().st_size)
    acceptance_path.write_text(json.dumps(acceptance))
    monkeypatch.setattr(lookup, 'EHS_ACCEPTANCE_SHA', lookup._digest(acceptance_path))
    with pytest.raises(ValueError, match='source verification failed'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_symlink_original_refused(copied_root: Path) -> None:
    """Canonical source identity cannot be redirected outside its ordinary local file."""
    record_path = copied_root / lookup.EHS_PACKAGE / 'source/canonical-record.jsonl'
    record = json.loads(record_path.read_bytes())
    path = copied_root / record['archive_path']
    path.unlink(); path.symlink_to(copied_root / lookup.EHS_PACKAGE / 'source/original.pdf')
    with pytest.raises(ValueError, match='symlinked'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_dropped_context_and_injected_markdown() -> None:
    """Output schema requires complete context, and renderer escapes injected text."""
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, 'OWTS New Permit')
    data = result.model_dump(mode='json'); data['context'].pop()
    with pytest.raises(ValueError, match='context required'):
        lookup.EhsLookupResult.model_validate_json(json.dumps(data))
    bad = result.model_copy(deep=True)
    bad.context[0].native.text = '<script>bad()</script>'
    assert '<script>' not in lookup.render_markdown(bad)




@pytest.mark.parametrize('query,text,expected', [
    ('Section 2', 'except as otherwise provided by Section 2,', True),
    ('Section 2', 'Section 25', False),
    ('Section 2', 'Section 2-3', False),
    ('Section 2', 'Section 2.1', False),
    ('211.5', '$211.50 in 2024', False),
    ('0', '$100 per day', False),
])
def test_ehs_section_punctuation_and_amount_boundaries(
        query: str, text: str, expected: bool) -> None:
    """Section prose punctuation differs from a truncated numeric amount or citation."""
    assert lookup._ehs_matches(query, text) is expected


def test_section_two_exception_is_context_match() -> None:
    """The complete exception remains searchable before its literal prose comma."""
    result = lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, 'Section 2')
    assert result.status == 'matched_context_only' and not result.rows
    assert 'B' in result.matched_context_ids
    context = next(c for c in result.context if c.context_id == 'B')
    assert 'Section 2,' in context.native.text and '$100 per day' in context.native.text


@pytest.fixture(scope='module')
def verified_ehs_result() -> Any:
    """Reuse a verified source response when probing strict output model invariants."""
    return lookup.lookup(ROOT, lookup.EHS_SOURCE_ID, list_rows=True)


@pytest.mark.parametrize('change', ['span', 'page', 'scope', 'refusal', 'status', 'empty_context'])
def test_output_invariant_rejections(change: str, verified_ehs_result: Any) -> None:
    """Detached spans, lost conditions and contradictory statuses fail strict output validation."""
    data = verified_ehs_result.model_dump(mode='json')
    if change == 'span':
        data['rows'][0]['fee_native']['sha256'] = '0' * 64
    elif change == 'page':
        data['rows'][0]['label_native']['physical_page'] = 5
    elif change == 'scope':
        data['rows'][0]['linked_context'].remove('B')
    elif change == 'refusal':
        data['status'] = 'refused_current_law'
    elif change == 'status':
        data['status'] = 'no_matching_row'
    else:
        data.update(status='matched_context_only', rows=[], matched_context_ids=[])
    with pytest.raises(ValueError):
        lookup.EhsLookupResult.model_validate_json(json.dumps(data))


@pytest.mark.parametrize('change', ['acceptance', 'directory', 'symlink', 'scope'])
def test_package_boundary_failures(
        change: str, copied_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unaccepted scope, changed acceptance and undeclared members cannot enter the adapter."""
    package = copied_root / lookup.EHS_PACKAGE
    acceptance = copied_root / lookup.EHS_ACCEPTANCE
    if change in {'acceptance', 'scope'}:
        data = json.loads(acceptance.read_bytes())
        data['legal_currentness'] = 'verified'
        acceptance.write_text(json.dumps(data))
        if change == 'scope':
            monkeypatch.setattr(lookup, 'EHS_ACCEPTANCE_SHA', lookup._digest(acceptance))
    elif change == 'directory':
        (package / 'undeclared').mkdir()
    else:
        (package / 'linked-source').symlink_to(package / 'source/original.pdf')
    with pytest.raises(ValueError):
        lookup._check_ehs_package(copied_root)


def test_bad_verifier_receipt_refused(copied_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful subprocess exit cannot replace the exact source-verifier receipt."""
    from types import SimpleNamespace
    monkeypatch.setattr(lookup.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout='{}'))
    with pytest.raises(ValueError, match='source verification failed'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_source_package_mutation_during_verifier(
        copied_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A changed post-verifier hash set prevents publishing otherwise valid source output."""
    check = lookup._check_ehs_package
    calls = []

    def changed(root: Path) -> dict[str, str]:
        """Represent a changed identity observed after an actual isolated verifier run."""
        hashes = check(root)
        calls.append(True)
        if len(calls) == 2:
            hashes['changed'] = '0' * 64
        return hashes

    monkeypatch.setattr(lookup, '_check_ehs_package', changed)
    with pytest.raises(ValueError, match='changed during verification'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_oversize_manifest_refused(copied_root: Path) -> None:
    """The canonical stream's byte bound is enforced before iterating any source rows."""
    path = copied_root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    with path.open('ab') as handle:
        handle.truncate(8_000_001)
    with pytest.raises(ValueError, match='size bound'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)


def test_canonical_pdf_tamper_refused(copied_root: Path) -> None:
    """A valid copied QA package cannot stand in for a changed actual canonical original."""
    record = json.loads((copied_root / lookup.EHS_PACKAGE /
                         'source/canonical-record.jsonl').read_bytes())
    path = copied_root / record['archive_path']
    data = bytearray(path.read_bytes())
    data[-1] ^= 1
    path.write_bytes(data)
    with pytest.raises(ValueError, match='canonical original differs'):
        lookup.lookup(copied_root, lookup.EHS_SOURCE_ID, list_rows=True)
