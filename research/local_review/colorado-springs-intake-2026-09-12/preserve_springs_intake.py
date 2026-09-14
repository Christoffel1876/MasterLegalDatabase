"""Preserve the completed, root-reviewed two-source intake without modifying its evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

BASE = Path('/Users/mcoors/Documents/Project Geode')
REPO = BASE / 'MasterLegalDatabase'
SOURCE = BASE / 'handoffs/run-2026-09-12/colorado-springs-intake-transaction'
OUT = REPO / 'research/local_review/colorado-springs-intake-2026-09-12'


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    path: str
    sha256: str
    size_bytes: int


class Acceptance(Strict):
    schema_version: Literal[1] = 1
    reviewer: Literal['Atlas'] = 'Atlas'
    verified_at: str
    status: Literal['accepted_custody_only'] = 'accepted_custody_only'
    receipt: Asset
    intent: Asset
    actual_repository_received_at: str
    raw_records: Literal[61] = 61
    ledger_records: Literal[62] = 62
    missing_historical_intake_ids: list[str]
    checks: list[str]
    limitations: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False


class Inventory(Strict):
    schema_version: Literal[1] = 1
    files: list[Asset]
    excluded_files: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def asset(path: Path) -> Asset:
    data = path.read_bytes()
    return Asset(path=path.relative_to(OUT).as_posix(), sha256=sha(data), size_bytes=len(data))


def typed(path: Path, value: BaseModel) -> None:
    path.write_text(value.model_dump_json(indent=2) + '\n')


def main() -> None:
    if OUT.exists():
        raise ValueError('Never replace an existing preservation package')
    receipt = json.loads((SOURCE / 'execution/RECEIPT.json').read_bytes())
    assert receipt['intent_sha256'] == 'fa9ab7c7a44b2836a8f2fd149472bdf52b872828a21794ee8d903faceebe70ce'
    assert sha((SOURCE / 'FINAL_MANIFEST.json').read_bytes()) == 'b27e2e97af28a9fe969518ca01187d0b8df91f27440670cbd657f8c41cb00298'
    for change in receipt['intent']['changes']:
        for item in (change['after'], change['snapshot']):
            data = (REPO / item['path']).read_bytes()
            assert sha(data) == item['sha256'] and len(data) == item['size_bytes']
    OUT.mkdir(parents=True)
    shutil.copytree(SOURCE, OUT / 'prepared-transaction', ignore=shutil.ignore_patterns('transaction.lock'))
    shutil.copy2(__file__, OUT / 'preserve_springs_intake.py')
    for item in receipt['originals']:
        source = REPO / item['path']
        assert sha(source.read_bytes()) == item['sha256']
        dest = OUT / 'completed-canonical' / item['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    for change in receipt['intent']['changes']:
        for item in (change['after'], change['snapshot']):
            dest = OUT / 'completed-canonical' / item['path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / item['path'], dest)
    report = json.loads((REPO / '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json').read_bytes())
    acceptance = Acceptance(
        verified_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        receipt=asset(OUT / 'prepared-transaction/execution/RECEIPT.json'),
        intent=asset(OUT / 'prepared-transaction/execution/INTENT.json'),
        actual_repository_received_at=receipt['actual_repository_received_at'],
        missing_historical_intake_ids=report['archive_verification']['missing_ledger_only_intake_ids'],
        checks=[
            'Root read all 624 transaction lines, 486 test lines and complete portable validator.',
            'Root portable preparation validation passed, binding 105 inventoried payloads and 56 recorded passing tests.',
            'Root actual read-only dry run passed before apply with no repository writes.',
            'Root actual apply and separate verification returned verified_complete, 61 raw and 62 ledger records.',
            'Exact original 59 raw and 60 ledger byte prefixes, same 5927-byte suffix, source hashes and preimages verified.',
            'Final reconciliation is a no-op; no source registry, policy, code or legal status was promoted.'
        ],
        limitations=[
            'Acquisition at 23:10 UTC is distinct from actual repository intake at 23:56 UTC.',
            'Source-printed dates do not establish current legal effect; older Code Services numeric tables are not fully reviewed.',
            'Process interruption/replay tested; abrupt power-loss durability not established.',
            'Full corpus validation is a separate checkpoint operation, not claimed by this custody acceptance.',
            'Prepared transaction retains historical paths and must not be executed from this relocated evidence copy; use validate_package.py only.'
        ])
    typed(OUT / 'ACCEPTANCE.json', acceptance)
    (OUT / 'ACCEPTANCE.schema.json').write_text(json.dumps(Acceptance.model_json_schema(), indent=2) + '\n')
    shutil.copy2(BASE / 'handoffs/run-2026-09-12/validate_springs_intake_preservation.py', OUT / 'validate_package.py')
    (OUT / 'README.md').write_text('''# Colorado Springs completed source intake

Two immutable City of Colorado Springs Fire Department PDFs were received into the municipal raw archive at **2026-09-12 23:56:16.492216 UTC**. The available originals increased from 59 to 61; the ledger increased from 60 to 62 and retains one separately identified missing historical file. Original prefixes remain byte-for-byte intact.

`ACCEPTANCE.json` records Atlas's review and actual application/verification. `prepared-transaction/` preserves the frozen preparation and actual execution receipts; `completed-canonical/` preserves the exact resulting records, raw originals and old preimages. The empty advisory lock file is omitted. There are no changes to legal currentness, source registration or daily monitoring.

The safe, portable, read-only entrypoint is `validate_package.py`. Run it with the reviewed Python environment, for example `python -I -B /absolute/path/to/this/package/validate_package.py`. It verifies exact files, schemas, receipt/intent/source bindings, prefix/suffix preservation, and the missing historical ledger entry. It does not need the repository. Historical transaction/build scripts contain their original path assumptions and are retained as evidence only: do not run them from this copy.

The older 2015-titled schedule has structural and selected-context review. The modern construction schedule has a separate accepted 128-row extraction review. Source-printed dates and references between schedules do not establish adoption, supersession or legal currentness. No fee calculation is certified.
''')
    manifest = Inventory(files=[asset(p) for p in sorted(OUT.rglob('*'), key=str) if p.is_file()],
                         excluded_files=['INVENTORY.json', 'INVENTORY.schema.json'])
    typed(OUT / 'INVENTORY.json', manifest)
    (OUT / 'INVENTORY.schema.json').write_text(json.dumps(Inventory.model_json_schema(), indent=2) + '\n')
    print(json.dumps({'path': str(OUT), 'files': len(manifest.files) + 2,
                      'acceptance_sha256': sha((OUT / 'ACCEPTANCE.json').read_bytes()),
                      'receipt_sha256': acceptance.receipt.sha256}))


if __name__ == '__main__':
    main()
