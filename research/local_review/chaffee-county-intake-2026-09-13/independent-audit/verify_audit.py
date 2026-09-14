"""Verify retained audit evidence offline without importing or applying the transaction."""
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pymupdf

from audit_models import Audit, Manifest
from run_checks import Checks

ROOT = Path(__file__).resolve().parent
PREPARATION_SHA = 'a8f768ff4c00bf55ba2db4712d67183f8c739e8e59777fa9bfed77f1bd12ef4b'
TRANSACTION_SHA = 'f6ba9314dbfb9c8fd546be3111485603bef5acdd544d6706bf3cd2bf6aca23fb'
MANIFEST_SHA = 'a27a0932e382605d4213ea0e2645725504b97539ba306668b2408d09e7ab0f86'


def require(value: bool, message: str) -> None:
    """Fail deterministically even when Python assertions are disabled."""
    if not value:
        raise ValueError(message)


def sha(data: bytes) -> str:
    """Hash the consumed buffer."""
    return hashlib.sha256(data).hexdigest()


def capture(root: Path) -> dict[str, bytes]:
    """Capture bounded ordinary local evidence once; reject links and extra directories."""
    require(root.is_dir() and not any(p.is_symlink() for p in [root, *root.parents]),
            'Unsafe audit directory')
    output = {}
    total = 0
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'Linked evidence')
        if path.is_dir():
            continue
        require(path.is_file() and path.stat().st_size <= 40_000_000, 'Unsafe evidence file')
        raw = path.read_bytes()
        total += len(raw)
        require(total <= 100_000_000, 'Audit byte budget exceeded')
        output[path.relative_to(root).as_posix()] = raw
    ancestors = {str(p) for name in output for p in Path(name).parents}
    require(all(p.relative_to(root).as_posix() in ancestors
                for p in root.rglob('*') if p.is_dir()), 'Unexpected empty directory')
    return output


def checked(files: dict[str, bytes], ref: Any, prefix: str = '') -> bytes:
    """Read only a path-safe pinned captured buffer."""
    if hasattr(ref, 'model_dump'):
        ref = ref.model_dump()
    name = prefix + ref['path']
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == name,
            'Unsafe reference')
    require(name in files, 'Missing evidence: ' + name)
    raw = files[name]
    require(sha(raw) == ref['sha256'] and len(raw) == ref['size_bytes'],
            'Changed evidence: ' + name)
    return raw


def verify(root: Path = ROOT) -> dict[str, Any]:
    """Validate closed custody, source/HTTP joins and actual nonmutating command receipts."""
    files = capture(root)
    final = Manifest.model_validate_json(files['FINAL_MANIFEST.json'])
    require(json.loads(files['FINAL_MANIFEST.schema.json']) == Manifest.model_json_schema(),
            'Manifest schema differs')
    names = {a.path for a in final.files}
    require(len(names) == len(final.files)
            and set(files) == names | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'},
            'Closed inventory differs')
    for ref in final.files:
        checked(files, ref)
    audit = Audit.model_validate_json(files['AUDIT.json'])
    require(json.loads(files['AUDIT.schema.json']) == Audit.model_json_schema(),
            'Audit schema differs')
    for ref, pin in [(audit.reviewed_preparation, PREPARATION_SHA),
                     (audit.reviewed_transaction, TRANSACTION_SHA),
                     (audit.reviewed_manifest, MANIFEST_SHA)]:
        require(sha(checked(files, ref)) == pin, 'Reviewed identity differs')
    receipt = json.loads(checked(files, audit.copy_receipt))
    jsonschema.validate(receipt, json.loads(files['COPY_RECEIPT.schema.json']))
    expected = set()
    for ref in receipt['files']:
        checked(files, ref)
        expected.add(ref['path'])
    require(len(receipt['files']) == len(expected) == 106, 'Copy scope differs')
    require(expected == {name for name in files if name.startswith('reviewed-preparation/')},
            'Copied preparation membership differs')
    prior = json.loads(checked(files, audit.reviewed_manifest))
    require({a['path'] for a in prior['files']} | {'FINAL_MANIFEST.json'}
            == {p.removeprefix('reviewed-preparation/') for p in expected},
            'Original preparation inventory differs')
    for ref in prior['files']:
        checked(files, ref, 'reviewed-preparation/')
    plan = json.loads(checked(files, audit.reviewed_preparation))
    jsonschema.validate(plan, json.loads(files['reviewed-preparation/PREPARATION.schema.json']))
    require((plan['raw_before'], plan['ledger_before'], plan['raw_after'], plan['ledger_after'])
            == (67, 68, 69, 70), 'Fixed count scope differs')
    require([s.source_id for s in audit.sources] == [t['record_id'] for t in plan['templates']],
            'Source order differs')
    for source, template, provenance in zip(audit.sources, plan['templates'], plan['provenance']):
        raw = checked(files, source.original)
        require(raw == checked(files, template['source'], 'reviewed-preparation/')
                == checked(files, provenance['response_body'], 'reviewed-preparation/'),
                'Source/body copy differs')
        require(source.official_source_url == template['official_source_url']
                == provenance['requested_url'] == provenance['final_url']
                and source.authority_id == template['authority_id'] == provenance['authority_id'],
                'Ownership or endpoint differs')
        require(source.observed_get_completed_at.isoformat().replace('+00:00', 'Z')
                == provenance['http_completed_at']
                and source.observed_get_started_at.isoformat().replace('+00:00', 'Z')
                == provenance['http_started_at'], 'Observed acquisition time differs')
        with pymupdf.open(stream=raw, filetype='pdf') as pdf:
            require(pdf.page_count == source.physical_pages and not pdf.is_repaired
                    and not pdf.is_encrypted, 'Selected PDF structure differs')
    for item in plan['baseline'][:2]:
        raw = checked(files, item['preserved'], 'reviewed-preparation/')
        with io.BytesIO(raw) as handle:
            require(sum(1 for line in handle if json.loads(line)) == item['records'],
                    'Preserved JSONL count differs')
    checks = Checks.model_validate_json(checked(files, audit.checks))
    require(json.loads(files['CHECKS.schema.json']) == Checks.model_json_schema(),
            'Check schema differs')
    require(checks.status == 'passed' and checks.repository_metadata_runtime_unchanged
            and checks.original_packet_unchanged and not checks.original_execution_directory_created
            and checks.repository_pins_before == checks.repository_pins_after
            and checks.original_packet_pins_before == checks.original_packet_pins_after,
            'Read-only evidence failed')
    require([r.label for r in checks.commands]
            == ['portable', 'live-preflight', 'independent-probes'], 'Command scope differs')
    for result in checks.commands:
        require(result.exit_code == 0 and result.started_at <= result.completed_at,
                'Failed command or chronology')
        stdout = checked(files, result.stdout)
        checked(files, result.stderr)
        if result.label == 'independent-probes':
            require(len(stdout.splitlines()) == 8
                    and all(x.endswith(b'_passed') for x in stdout.splitlines()),
                    'Independent probe results differ')
        elif result.label == 'live-preflight':
            data = json.loads(stdout)
            require(data['canonical_mutations'] == 0 and data['status'] == 'dry_run'
                    and data['actual_repository_received_at'] is None,
                    'Live command was not unapplied read-only preflight')
    return {'status': 'passed_preapply_audit', 'payloads': len(names), 'sources': 2,
            'physical_pages': 21, 'independent_probes': 8, 'canonical_apply': False,
            'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    sys.stdout.write(json.dumps(verify(), sort_keys=True) + '\n')
