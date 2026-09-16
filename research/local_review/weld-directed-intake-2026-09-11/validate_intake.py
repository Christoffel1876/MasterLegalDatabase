"""Verify the completed two-source Weld intake without writing or fetching files."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Literal

sys.dont_write_bytecode = True
import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict
from intake_models import Asset, Receipt, Record, Source

BASE = Path(__file__).resolve().parent


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class CorpusResult(Strict):
    checked_at: AwareDatetime
    exit_code: Literal[1]
    status: Literal['failed_with_two_inherited_errors']
    inherited_issue_count: Literal[2]
    affected_paths: list[str]
    result_basis: Literal['root_report_and_preserved_execution_log']
    new_issue_reported: Literal[False]
    log: Asset


class Closure(Strict):
    schema_version: Literal[1]
    validated_at: AwareDatetime
    status: Literal['passed_transaction_and_portable_checks']
    receipt: Asset
    files: list[Asset]
    raw_manifest_records: Literal[40]
    ledger_records: Literal[41]
    physical_pages: Literal[8]
    native_bytes: Literal[16651]
    source_reviews_copied_unchanged: Literal[71]
    live_repository_validation: Literal['passed']
    relocated_portable_validation: Literal['passed_with_original_workspace_reads_denied']
    rejected_mutations: list[str]
    full_corpus_validation: CorpusResult
    legal_currentness: Literal['not_verified']
    coverage_or_rule_unit_changes: Literal['none']
    limitations: list[str]


def check(base: Path, asset: Asset) -> bytes:
    """Require a confined, ordinary file with exactly the recorded bytes."""
    rel = Path(asset.path)
    assert not rel.is_absolute() and rel.parts and '..' not in rel.parts, asset.path
    path = base / rel
    assert not any(p.is_symlink() for p in (path, *path.parents)), asset.path
    assert path.is_file() and path.resolve().is_relative_to(base.resolve()), asset.path
    data = path.read_bytes()
    assert len(data) == asset.size_bytes, asset.path
    assert hashlib.sha256(data).hexdigest() == asset.sha256, asset.path
    return data


def schema_check(data: bytes, schema: bytes) -> None:
    """Validate serialized data against its exported JSON schema."""
    validator = jsonschema.Draft202012Validator(json.loads(schema))
    validator.check_schema(validator.schema)
    validator.validate(json.loads(data))


def module(path: Path, name: str):
    """Load an already hash-verified local verifier with a distinct module name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def validate(repo_root: Path | None = None) -> dict:
    """Check portable transaction evidence, optionally against the live repository."""
    raw_receipt = (BASE / 'intake-receipt.json').read_bytes()
    receipt = Receipt.model_validate_json(raw_receipt)
    schema_check(raw_receipt, (BASE / 'intake-receipt.schema.json').read_bytes())
    assert len({a.path for a in receipt.payloads}) == len(receipt.payloads)
    for item in receipt.payloads:
        check(BASE, item)
    for item in receipt.preparation_preimages:
        check(BASE, item)
    assert len(receipt.audit_copies) == 71
    for item in receipt.audit_copies:
        check(BASE, item.frozen)

    record_bytes = check(BASE, receipt.record_stream)
    source_bytes = check(BASE, receipt.provenance_stream)
    record_schema = check(BASE, receipt.record_schema)
    source_schema = check(BASE, receipt.source_schema)
    assert record_bytes.endswith(b'\n') and source_bytes.endswith(b'\n')
    records = [Record.model_validate_json(line) for line in record_bytes.splitlines()]
    sources = [Source.model_validate_json(line) for line in source_bytes.splitlines()]
    assert len(records) == len(sources) == 2 and sources == receipt.sources
    for line in record_bytes.splitlines():
        schema_check(line, record_schema)
    for line in source_bytes.splitlines():
        schema_check(line, source_schema)

    transaction_paths = [
        '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json',
    ]
    assert [t.repository_path for t in receipt.transactions] == transaction_paths
    for i, transaction in enumerate(receipt.transactions):
        before = check(BASE, transaction.before)
        after = check(BASE, transaction.after)
        assert transaction.snapshot.sha256 == transaction.before.sha256
        assert transaction.snapshot.size_bytes == transaction.before.size_bytes
        assert transaction.snapshot.path.startswith('_SNAPSHOTS/snapshot_')
        assert transaction.snapshot.path.endswith('/' + transaction.repository_path)
        if i < 2:
            assert before.endswith(b'\n') and after == before + record_bytes
            assert len(before.splitlines()) == [38, 39][i]
            assert len(after.splitlines()) == [40, 41][i]
            for line in after.splitlines():
                Record.model_validate_json(line)
                schema_check(line, record_schema)
        else:
            report_before, report_after = json.loads(before), json.loads(after)
            assert report_before['records'] == 39 and report_after['records'] == 41
            assert report_before['archive_verification']['manifest_records'] == 38
            assert report_after['archive_verification']['manifest_records'] == 40
            assert report_after['pending_pipeline_use'] == 41
            assert report_after['latest_record_id'] == sources[-1].source_id
            missing = 'missing_ledger_only_intake_ids'
            assert report_before['archive_verification'][missing] == report_after['archive_verification'][missing]
            assert len(report_after['archive_verification'][missing]) == 1
        if repo_root is not None:
            check(repo_root, transaction.snapshot)
            # This intake is frozen at 40/41. Later appends require a new receipt;
            # this check deliberately reports a changed baseline instead of guessing.
            check(repo_root, Asset(path=transaction.repository_path,
                                  sha256=transaction.after.sha256,
                                  size_bytes=transaction.after.size_bytes))

    for index, (record, source) in enumerate(zip(records, sources, strict=True)):
        assert record.record_id == source.source_id
        assert record.intake_id == source.intake_id
        assert record.archive_path == source.canonical_original.path
        assert record.sha256 == source.canonical_original.sha256
        assert record.size_bytes == source.canonical_original.size_bytes
        assert record.received_at == source.repository_received_at
        assert record.official_source_url == source.exact_requested_url == source.exact_final_url
        assert record.layer_id == '08_County_Authorities' and record.source_format == 'pdf'
        assert record.status == 'archived_pending_pipeline' and not record.blocked_queue_match
        assert record.acquisition_method == 'manual_official_download'
        assert source.http_started_at < source.http_completed_at < source.repository_received_at
        assert source.repository_received_at < receipt.completed_at
        source_pdf = check(BASE, source.staged_original)
        if repo_root is not None:
            assert check(repo_root, source.canonical_original) == source_pdf
        with pymupdf.open(stream=source_pdf, filetype='pdf') as doc:
            assert len(doc) == source.physical_pages
            assert not doc.is_encrypted and not doc.is_repaired
            assert sum(len(p.get_text('text', sort=False, flags=195).encode()) for p in doc) == source.native_bytes
        access = json.loads(check(BASE, source.access_receipt))
        event = next(e for e in access['attempts'] if e['event_id'] == f'ATLAS-WELD-0{index+3}')
        assert event['target_url'] == event['final_url'] == source.exact_requested_url
        assert event['response_body']['sha256'] == event['retained_original']['sha256'] == record.sha256
        assert event['response_body']['size_bytes'] == record.size_bytes
        assert event['http_status'] == 200 and event['curl_exit_code'] == 0
        assert datetime.fromisoformat(event['started_at'].replace('Z', '+00:00')) == source.http_started_at
        assert datetime.fromisoformat(event['finished_at'].replace('Z', '+00:00')) == source.http_completed_at
        assert event['response_headers']['sha256'] == source.original_header_identity.sha256
        check(BASE, source.public_headers)
        review_bytes = check(BASE, source.reviewed_source)
        schema_check(review_bytes, check(BASE, source.reviewed_source_schema))
        review = json.loads(review_bytes)
        assert review['source']['sha256'] == record.sha256
        if index == 0:
            assert len(source.source_dates) == len(review['stated_dates']) == 11
            for n, date in enumerate(source.source_dates):
                assert date.review_pointer == f'#/stated_dates/{n}'
                assert (date.value, date.role) == (review['stated_dates'][n]['stated_date'], review['stated_dates'][n]['role'])
        else:
            assert len(source.source_dates) == 1
            assert source.source_dates[0].value == review['source_year_assertion'] == '2026'
            assert source.source_dates[0].role == 'schedule_year_assertion'
            assert source.source_dates[0].review_pointer == '#/source_year_assertion'
            assert review['adoption_date'] is review['effective_date'] is None

    ordinal_dir = BASE / sources[0].reviewed_source_directory
    old_path = sys.path[:]
    old_model = sys.modules.pop('review_models', None)
    try:
        sys.path.insert(0, str(ordinal_dir))
        ordinal = module(ordinal_dir / 'validate_source_review.py', '_weld_ordinance_frozen_validator')
        ordinal_result = ordinal.validate(check_originals=False).model_dump(mode='json')
    finally:
        sys.path[:] = old_path
        sys.modules.pop('review_models', None)
        if old_model is not None:
            sys.modules['review_models'] = old_model
    ehs_dir = BASE / sources[1].reviewed_source_directory
    ehs = module(ehs_dir / 'build_review.py', '_weld_ehs_frozen_validator')
    ehs_result = ehs.verify(ehs.Review.model_validate_json((ehs_dir / 'SOURCE_QA.json').read_bytes()))
    ehs_manifest = json.loads((ehs_dir / 'FINAL_MANIFEST.json').read_bytes())
    schema_check((ehs_dir / 'FINAL_MANIFEST.json').read_bytes(),
                 (ehs_dir / 'FINAL_MANIFEST.schema.json').read_bytes())
    for entry in ehs_manifest['files']:
        check(ehs_dir, Asset.model_validate(entry))
    assert ordinal_result['source_pages'] == 5 and ordinal_result['native_bytes'] == 9284
    assert ehs_result['rows'] == 137 and ehs_result['groups'] == 11
    assert ehs_result['printed_fee_cells'] == 136 and ehs_result['blank_fee_cells'] == 1
    assert receipt.after_reconciliation.added_intake_ids == [r.intake_id for r in records]
    assert receipt.idempotency_reconciliation.report_needs_update is False

    if (BASE / 'FINAL_VALIDATION.json').exists():
        # Additive closure inventory preserves the original transaction receipt.
        final = json.loads((BASE / 'FINAL_VALIDATION.json').read_bytes())
        Closure.model_validate_json((BASE / 'FINAL_VALIDATION.json').read_bytes())
        schema_check((BASE / 'FINAL_VALIDATION.json').read_bytes(),
                     (BASE / 'FINAL_VALIDATION.schema.json').read_bytes())
        actual = {p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()
                  and p.name not in {'FINAL_VALIDATION.json', 'FINAL_VALIDATION.schema.json'}}
        assert actual == {a['path'] for a in final['files']}
        for item in final['files']:
            check(BASE, Asset.model_validate(item))
        assert check(BASE, Asset.model_validate(final['receipt'])) == raw_receipt
        check(BASE, Asset.model_validate(final['full_corpus_validation']['log']))
        assert final['status'] == 'passed_transaction_and_portable_checks'
        assert final['legal_currentness'] == 'not_verified'
        assert final['full_corpus_validation']['exit_code'] == 1
        assert final['full_corpus_validation']['inherited_issue_count'] == 2
        assert final['full_corpus_validation']['affected_paths'] == [
            '_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json', '08_County_Authorities/_index.jsonl']
    return {
        'status': 'passed', 'mode': 'live_repository' if repo_root is not None else 'portable',
        'raw_manifest_records': 40, 'ledger_records': 41, 'sources': 2,
        'physical_pages': 8, 'native_utf8_bytes': 16651,
        'unchanged_copied_review_files': 71, 'ehs_fee_rows': 137, 'ehs_service_groups': 11,
        'raw_and_ledger_exact_prefixes_preserved': True,
        'original_workspace_paths_required': False,
        'legal_currentness': 'not_verified',
        'coverage_or_rule_unit_changes': 'none',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, help='Also verify exact live canonical files and snapshots.')
    args = parser.parse_args()
    print(json.dumps(validate(args.repo_root.resolve() if args.repo_root else None), indent=2))
