"""Read-only validation of the unexecuted Weld source-intake preparation."""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path

import jsonschema
import pymupdf

sys.dont_write_bytecode = True
from preparation_models import Dedupe, Preparation, Source
from geode.pipeline.manual_source_intake import (
    ManualSourceIntakeRecord,
    ManualSourceIntakeRequest,
    archive_manual_source,
)

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def digest(path: Path) -> str:
    """Compute an ordinary file's exact byte digest."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Unsafe or missing input: {path}')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, int | str]:
    """Verify the pending proposal and fail if its live baseline has changed."""
    raw = (BASE / 'PREPARATION.json').read_bytes()
    proposal = Preparation.model_validate_json(raw)
    jsonschema.Draft202012Validator(
        json.loads((BASE / 'PREPARATION.schema.json').read_bytes())
    ).validate(json.loads(raw))
    for item in proposal.payloads:
        relative = Path(item.path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Payload path outside preparation')
        path = BASE / relative
        if digest(path) != item.sha256 or path.stat().st_size != item.size_bytes:
            raise ValueError('Preparation payload changed')
    check = Dedupe.model_validate_json((BASE / 'dedupe.json').read_bytes())
    for baseline in check.baseline:
        current = ROOT / baseline.repository_path
        old = BASE / baseline.frozen.path
        if current.read_bytes() != old.read_bytes():
            raise ValueError('Live baseline changed; prepare a newly reviewed transaction')
        if baseline.records is not None:
            count = 0
            with current.open() as stream:
                for line in stream:
                    ManualSourceIntakeRecord.model_validate_json(line)
                    count += 1
            if count != baseline.records:
                raise ValueError('Baseline row count changed')
    source_records = []
    with (BASE / 'source-provenance.jsonl').open() as stream:
        for line in stream:
            source_records.append(Source.model_validate_json(line))
    if source_records != proposal.sources:
        raise ValueError('Source provenance differs from preparation')
    for source in proposal.sources:
        original = BASE / source.source_original.path
        if digest(original) != source.source_original.sha256:
            raise ValueError('Staged source changed')
        with pymupdf.open(original) as pdf:
            if (len(pdf) != source.source_page_count or pdf.is_repaired
                    or pdf.is_encrypted):
                raise ValueError('Staged PDF structure changed')
        request = ManualSourceIntakeRequest.model_validate_json(
            (BASE / source.request.path).read_bytes()
        )
        if (request.record_id != source.proposed_record_id
                or request.official_source_url != source.exact_requested_url
                or request.expected_sha256 != source.source_original.sha256
                or request.allow_duplicate):
            raise ValueError('Request identity or duplicate policy changed')
        preview = ManualSourceIntakeRecord.model_validate_json(
            (BASE / source.dry_run_preview.path).read_bytes()
        )
        repeated = archive_manual_source(
            ROOT, request, dry_run=True, timestamp=preview.received_at
        )
        if repeated != preview or preview.status != 'dry_run_pending_archive':
            raise ValueError('Dry-run result changed or falsely claims archive completion')
        if preview.blocked_queue_match:
            raise ValueError('Unexpected blocked-queue relationship')
    return {
        'status': 'prepared_not_applied', 'sources': 2,
        'raw_manifest_records': 38, 'manual_ledger_records': 39,
        'raw_files_size_screened_at_preparation': 542,
        'legacy_metadata_references': len(check.legacy_matches),
        'payloads_checked': len(proposal.payloads),
        'source_role_review': 'pending_root_reconciliation',
        'legal_currentness': 'not_verified',
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('%s', json.dumps(validate(), indent=2))
