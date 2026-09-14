"""Freeze the bounded independent audit once, using strict validated records."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

from audit_models import Audit, Manifest, Source
from run_checks import Checks, asset

HERE = Path(__file__).resolve().parent


def save(name: str, value: object) -> None:
    """Validate the model and exported schema before any JSON output is written."""
    schema = type(value).model_json_schema()
    encoded = value.model_dump_json(indent=2) + '\n'
    jsonschema.validate(json.loads(encoded), schema)
    with (HERE / (name + '.schema.json')).open('x') as handle:
        handle.write(json.dumps(schema, indent=2) + '\n')
    with (HERE / (name + '.json')).open('x') as handle:
        handle.write(encoded)


def seal() -> None:
    """Record observed checks without source-content or canonical-application approval."""
    if (HERE / 'FINAL_MANIFEST.json').exists():
        raise ValueError('Already frozen; preserve this audit unchanged')
    checks = Checks.model_validate_json((HERE / 'CHECKS.json').read_bytes())
    assert checks.status == 'passed'
    plan = json.loads((HERE / 'reviewed-preparation/PREPARATION.json').read_bytes())
    template, provenance = plan['templates'][0], plan['provenance'][0]
    original = asset(HERE / 'reviewed-preparation' / template['source']['path'])
    source = Source.model_validate_json(json.dumps({
        'source_id': template['record_id'], 'authority_id': template['authority_id'],
        'layer_id': template['layer_id'], 'original': original.model_dump(),
        'physical_pages': provenance['physical_pages'],
        'official_source_url': template['official_source_url'],
        'acquisition_method': 'manual_official_download',
        'observed_get_started_at': provenance['http_started_at'],
        'observed_get_completed_at': provenance['http_completed_at'],
        'future_repository_received_at': None, 'status': 'archived_pending_pipeline'}))
    audit = Audit(reviewer='Plato', recorded_at=datetime.now(timezone.utc),
        disposition='no_blocker_found_in_fixed_one_source_preapply_scope',
        reviewed_preparation=asset(HERE / 'reviewed-preparation/PREPARATION.json'),
        reviewed_transaction=asset(HERE / 'reviewed-preparation/transaction.py'),
        reviewed_manifest=asset(HERE / 'reviewed-preparation/FINAL_MANIFEST.json'),
        copy_receipt=asset(HERE / 'COPY_RECEIPT.json'), checks=asset(HERE / 'CHECKS.json'),
        sources=[source], baseline_raw_records=69, baseline_ledger_records=70,
        proposed_raw_records=70, proposed_ledger_records=71,
        actual_intake_occurred_in_this_audit=False, independent_probe_cases=8,
        observations=[
            'All 252 prepared payloads and their manifest were captured and copied exactly. '
            'The supplied strict schema and complete public retrieval subset pass offline verification.',
            'The one County source is exactly the 206,144-byte two-page PDF. Its incoming basename '
            'is original.pdf. The model and runtime bind its single source ID, county layer, exact '
            'official-linked Revize URL, PDF digest and preserved observed download body.',
            'The county parent HTML/base/anchor is supplied historical evidence. The prior actual '
            'county 302 result, public Location header and body anchor independently agree on the '
            'Revize endpoint. The new actual A001 HTTP200 evidence is a distinct later GET.',
            'Observed GET completion is 2026-09-13T16:44:33.133961Z. No intake time is prepared. '
            'A synthetic intake clock before acquisition completion is refused before an intent exists.',
            'The live dry-run recomputed baseline report/available originals and checked immutable '
            'preimages, runtime and exact source policy; it reported 69/70 to 70/71 with zero writes.',
            'Temporary application preserves old JSONL prefixes exactly, writes the original once, '
            'derives the report only from captured records, and resumes a missing completion receipt '
            'without changing canonical bytes or original file modification times.',
            'Independent original/referral ABA probes use only captured verified buffers. Report-ahead '
            'states, foreign suffixes and linked incoming originals are refused without promoting them.',
            'Independent local comparison confirms no exact selected ID, URL or digest among the full '
            '48,390 legacy rows, current raw/ledger and two registries. All 573 present ordinary raw '
            'files were size-screened; none matched 206,144 bytes.',
            'Eight retained header files contained no Authorization, Proxy-Authorization, Cookie or '
            'Set-Cookie field names. Only names were inspected; omitted header values cannot be replayed.',
        ],
        limitations=[
            'This is a bounded single-agent read-only preapply audit, not canonical execution, a '
            'full fee transcription, legal effect, currentness, coverage or answer-safety approval.',
            'The declared 77-test/92.236842-percent preparation result is producer evidence. This audit '
            'ran its own eight-case temporary replay suite, portable verifier and live read-only preflight.',
            'The author synthetic one-record baseline constructor is reused explicitly. Assertions '
            'are independent; fixture application is only temporary and never targets the real corpus.',
            'The first probe adaptation accidentally duplicated a selector, omitted the parent case and '
            'reported eight lines without uniqueness. Its exact code/outputs are historical under '
            'initial-probe-adaptation; the corrected final run requires eight unique case outcomes.',
            'Exact duplicate absence is limited to present local metadata/ordinary raw files; it does '
            'not include missing LFS bodies, external research copies or alternate URL spellings.',
            'The transaction is a fixed reviewed batch with serialized authorized writers, not a '
            'general multi-writer database. Process-failure replay does not prove power-loss durability '
            'or directory fsync. An unexpected canonical change must stop for review.',
            'The public header derivatives are a retained subset. This audit does not authenticate '
            'unavailable original header values or the historical parent acquisition chronology.',
        ], legal_currentness='not_verified', answer_safe=False, public_requests=0)
    save('AUDIT', audit)
    manifest = Manifest(recorded_at=datetime.now(timezone.utc),
        status='frozen_preapply_audit_not_canonical_execution',
        files=[asset(p) for p in sorted(HERE.rglob('*')) if p.is_file()])
    save('FINAL_MANIFEST', manifest)
    sys.stdout.write('Frozen ' + str(len(manifest.files)) + ' audit payloads\n')


if __name__ == '__main__':
    seal()
