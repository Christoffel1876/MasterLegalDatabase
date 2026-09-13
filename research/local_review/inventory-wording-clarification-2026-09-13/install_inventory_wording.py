"""Install a verified wording-only correction after the installed suite has passed."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import hashlib
import json
import os
import shutil
import subprocess
import sys

from pydantic import BaseModel, ConfigDict

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1] / 'MasterLegalDatabase'
PREP = RUN / 'extended-run/final-inventory-wording-clarification'
PACKAGE = ROOT / 'research/local_review/manual-source-review-inventory-2026-09-11'
OUT = ROOT / 'research/local_review/inventory-wording-clarification-2026-09-13'
VISUAL = Path('/Users/mcoors/.codex/visualizations/2026/09/09/01a08848-5f8e-7c51-9b66-fd82eff860fe/geode-source-review-inventory.html')


class Receipt(BaseModel):
    """Evidence of an additive metadata clarification with unchanged source records."""
    model_config = ConfigDict(extra='forbid', strict=True)
    status: Literal['installed_verified']
    installed_at: datetime
    proposal_manifest_sha256: str
    full_suite_status_before_install: Literal['passed']
    inventory_sha256: str
    visual_sha256: str
    unchanged_code_and_custody: dict[str, str]
    all_source_rows_and_joins_unchanged: Literal[True]
    legal_currentness: Literal['not_verified']
    scope: str


def sha(path: Path) -> str:
    """Hash one exact ordinary file."""
    assert path.is_file() and not path.is_symlink()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Validate, preserve preimages, atomically install and check the companions."""
    result = json.loads((ROOT / 'docs/audits/FOUR_HOUR_RUN_2026-09-12/VERIFICATION_CATCHUP_INTEGRATION/RESULT.json').read_bytes())
    assert result['status'] == 'passed' and result['changed_during_run'] == []
    assert not OUT.exists()
    manifest_sha = sha(PREP / 'FINAL_MANIFEST.json')
    assert manifest_sha == '8c8e61d4e16fd5e4f57b0d13d102b2de5863240ea11d2a6c8abb5100a5f92354'
    subprocess.run([sys.executable, '-B', str(PREP / 'verify.py')], check=True)
    record = json.loads((PREP / 'CLARIFICATION.json').read_bytes())
    for item in record['inputs']:
        path = Path(item['path'])
        path = path if path.is_absolute() else ROOT / path
        assert sha(path) == item['sha256'] and path.stat().st_size == item['size_bytes']
    names = ['join-plan.json', 'inventory.json', 'inventory.schema.json', 'README.md']
    for name in names:
        assert (PACKAGE / name).read_bytes() == (PREP / 'preimages' / name).read_bytes()
    assert VISUAL.read_bytes() == (PREP / 'preimages' / VISUAL.name).read_bytes()
    guards = {name: sha(ROOT / name) for name in [
        'geode/pipeline/manual_review_inventory.py', 'tests/test_manual_review_inventory.py',
        '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json', '_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json']}
    shutil.copytree(PREP, OUT / 'proposal')
    shutil.copy2(__file__, OUT / Path(__file__).name)
    sys.path.insert(0, str(ROOT))
    from geode.utils.file_io import atomic_write_text
    for name in names:
        if (PACKAGE / name).read_bytes() != (PREP / 'proposed' / name).read_bytes():
            atomic_write_text(PACKAGE / name, (PREP / 'proposed' / name).read_text(), ROOT)
    # Exact visual preimage was preserved above; only the nonvisual digest attribute changes.
    temporary = VISUAL.with_name(VISUAL.name + '.clarification-tmp')
    assert not temporary.exists()
    temporary.write_bytes((PREP / 'proposed' / VISUAL.name).read_bytes())
    os.replace(temporary, VISUAL)
    check = subprocess.run([sys.executable, '-B', '-m', 'geode.pipeline.manual_review_inventory',
        '--root', str(ROOT), '--check'], cwd=ROOT, capture_output=True)
    (OUT / 'installed-check.log').write_bytes(check.stdout + check.stderr)
    assert check.returncode == 0, (check.stdout + check.stderr).decode()
    assert guards == {name: sha(ROOT / name) for name in guards}
    for item in record['outputs']:
        path = VISUAL if Path(item['path']).name == VISUAL.name else PACKAGE / Path(item['path']).name
        assert sha(path) == item['sha256']
    receipt = Receipt(status='installed_verified', installed_at=datetime.now(timezone.utc),
        proposal_manifest_sha256=manifest_sha, full_suite_status_before_install='passed',
        inventory_sha256=sha(PACKAGE / 'inventory.json'), visual_sha256=sha(VISUAL),
        unchanged_code_and_custody=guards, all_source_rows_and_joins_unchanged=True,
        legal_currentness='not_verified', scope='Only the first limitation and linked inventory digest changed. All 64 source rows, authority/review joins, dates and review scopes remain exact. Prior four-viewport UI QA remains applicable to identical visible content; no new browser run is claimed.')
    (OUT / 'INSTALLATION.schema.json').write_text(json.dumps(Receipt.model_json_schema(), indent=2) + '\n')
    (OUT / 'INSTALLATION.json').write_text(receipt.model_dump_json(indent=2) + '\n')
    (OUT / 'README.md').write_text('---\ntitle: Inventory wording clarification\nstatus: installed_verified\n---\n\n'
        'The first limitation now says “Every row” instead of the stale “All 61 rows.” '
        'All 64 source rows and their authority and review joins remain unchanged. '
        'The proposal preserves exact preimages. INSTALLATION.json records this later wording correction. '
        'The inventory check passed after installation; no runtime or test code changed.\n')
    print(receipt.model_dump_json(indent=2))


if __name__ == '__main__':
    main()
