"""Preserve actual reviewed County execution and demonstrate a repeat is a no-op."""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1] / 'MasterLegalDatabase'
PREP = BASE / 'extended-run/pueblo-county-fees-intake-revision'
OUT = REPO / 'research/local_review/pueblo-county-intake-2026-09-13'
sys.dont_write_bytecode = True
sys.path.insert(0, str(PREP))
import transaction as tx
from models import Asset

class Acceptance(BaseModel):
    """Root acceptance of one actual byte-custody intake, never legal currentness."""
    model_config = ConfigDict(extra='forbid', strict=True)
    status: Literal['accepted_completed_byte_custody_intake']
    verified_at: datetime
    source_id: Literal['pueblo-county-planning-fees-sh-ext-002']
    authority_id: Literal['CO-COUNTY-PUEBLO']
    preparation_manifest_sha256: str
    reviewed_transaction_sha256: str
    actual_execution: tx.Receipt
    canonical_source: Asset
    snapshots: list[Asset]
    package_files: list[Asset]
    repeat_application_byte_identical: Literal[True]
    original_prefixes_byte_identical: Literal[True]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    limitations: list[str]

def asset(root, path):
    raw = path.read_bytes()
    return Asset(path=path.relative_to(root).as_posix(),
        sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))

def main():
    assert not OUT.exists()
    before = {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [REPO / tx.RAW, REPO / tx.LEDGER, REPO / tx.REPORT]}
    receipt = tx.Receipt.model_validate_json(json.dumps(tx.run(REPO, base=PREP, verify=True)))
    repeat = tx.run(REPO, base=PREP, apply=True)
    assert repeat == receipt.model_dump(mode='json')
    assert before == {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in before}
    intent = tx.Intent.model_validate_json((PREP / 'execution/INTENT.json').read_bytes())
    assert intent.record.official_source_url is None
    plan = tx.load_plan()
    for name in [tx.RAW, tx.LEDGER]:
        previous = tx.capture(PREP, next(b.preserved for b in plan.baseline if b.repository_path == name))
        assert (REPO / name).read_bytes() == previous + (intent.record.model_dump_json() + '\n').encode()
    shutil.copytree(PREP, OUT / 'prepared-transaction')
    shutil.copy2(__file__, OUT / 'preserve_county_applied.py')
    snapshots = [REPO / '_SNAPSHOTS' / intent.record.intake_id / name for name in [tx.RAW, tx.LEDGER, tx.REPORT]]
    record = Acceptance(status='accepted_completed_byte_custody_intake', verified_at=datetime.now(timezone.utc),
        source_id=tx.ID, authority_id='CO-COUNTY-PUEBLO',
        preparation_manifest_sha256=hashlib.sha256((PREP / 'FINAL_MANIFEST.json').read_bytes()).hexdigest(),
        reviewed_transaction_sha256=hashlib.sha256((PREP / 'transaction.py').read_bytes()).hexdigest(),
        actual_execution=receipt, canonical_source=asset(REPO, REPO / intent.record.archive_path),
        snapshots=[asset(REPO, p) for p in snapshots],
        package_files=[asset(OUT,p) for p in sorted(OUT.rglob('*')) if p.is_file()],
        repeat_application_byte_identical=True, original_prefixes_byte_identical=True,
        legal_currentness='not_verified', answer_safe=False,
        limitations=['Source-fidelity acceptance remains separately bounded to two pages/88 physical rows.',
            'Received review package: official_source_url null; reported HTTP provenance is separate and not independently witnessed.',
            'No adoption/effective date/currentness or complete county corpus certification.',
            'Inherited missing ledger-only executive-order original remains unchanged.',
            'Original proposal blocked by a reproduced concurrent foreign-record promotion; exact revised fixed-source writer only was applied.'])
    (OUT / 'ROOT_ACCEPTANCE.schema.json').write_text(json.dumps(Acceptance.model_json_schema(), indent=2)+'\n')
    (OUT / 'ROOT_ACCEPTANCE.json').write_text(record.model_dump_json(indent=2)+'\n')
    (OUT / 'README.md').write_text('# Pueblo County fee source — intake completed\n\n'
        'The reviewed fixed-source revision was applied at '+receipt.actual_repository_received_at.isoformat()+
        '. Raw manifest64 /ledger65. Exact prior JSONL prefixes, source hash, snapshots, verification and repeat no-op passed. '
        'The canonical source is a received review package. The earlier prepared status is historical; execution/INTENT.json and RECEIPT.json record actual application. '
        'The original proposal remains blocked historical evidence and must not be applied. No legal currentness or answer-safety promotion.\n')
    pending = REPO / 'research/local_review/extended-pending-work-2026-09-13/COUNTY_REVISION_DISPOSITION.md'
    pending.write_text('# Additive County intake disposition\n\nOriginal preserved proposal remains unchanged and must not be applied: independent review reproduced a foreign-record reconciliation race. '
        'The revised fixed-source transaction dcacd5e6de2cb8bc7b3e37a8dcc20b705f97c8e90747768227b4b8b8b478c5f2 passed44 combined cases and root plus independent checks. '
        'Actual completion is separately preserved at research/local_review/pueblo-county-intake-2026-09-13/. Original reported provenance and all source bytes remain unchanged.\n')
    print(record.model_dump_json(indent=2, exclude={'package_files','snapshots'}))

if __name__ == '__main__':
    main()
