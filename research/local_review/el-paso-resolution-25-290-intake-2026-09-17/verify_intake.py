"""Read-only closure, transaction and exact inventory delta verifier."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import jsonschema

from models import Asset, Manifest

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def check(root: Path, item: Asset) -> bytes:
    """Read only safe ordinary pinned bytes."""
    path = root / item.path
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('Nonordinary evidence')
    raw = path.read_bytes()
    if (sha256(raw).hexdigest(), len(raw)) != (item.sha256, item.size_bytes):
        raise ValueError('Evidence changed: ' + item.path)
    return raw


def main() -> None:
    """Replay exact custody without applying an intake or trusting a shell status alone."""
    manifest = Manifest.model_validate_json((BASE / 'FINAL_MANIFEST.json').read_bytes())
    actual = {p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()}
    names = {item.path for item in manifest.files}
    if len(names) != len(manifest.files) or actual != names | {'FINAL_MANIFEST.json'}:
        raise ValueError('Closed package membership differs')
    for item in manifest.files:
        check(BASE, item)
    jsonschema.validate(manifest.model_dump(mode='json'),
                        json.loads((BASE / 'FINAL_MANIFEST.schema.json').read_bytes()))
    import transaction as tx
    result = tx.run(ROOT, verify=True)
    if (result['raw_records'], result['ledger_records']) != (71, 72):
        raise ValueError('Intake counts differ')
    sys.path.insert(0, str(ROOT))
    from geode.pipeline import manual_review_inventory as inv
    from audit_models import FinalAudit
    audit = FinalAudit.model_validate_json((BASE / 'FINAL_AUDIT.json').read_bytes())
    jsonschema.validate(audit.model_dump(mode='json'),
                        json.loads((BASE / 'FINAL_AUDIT.schema.json').read_bytes()))
    for item in audit.installed_files + audit.unchanged_inputs + audit.snapshots:
        check(ROOT, item)
    before = ROOT / audit.inventory_snapshot
    old = inv.Inventory.model_validate_json((before / 'inventory.json').read_bytes())
    old_plan = inv.JoinPlan.model_validate_json((before / 'join-plan.json').read_bytes())
    new = inv.build_inventory(ROOT)
    plan = inv.JoinPlan.model_validate_json((ROOT / inv.PLAN).read_bytes())
    inv.check_inventory(ROOT, new)
    assert new.sources[:70] == old.sources and len(new.sources) == 71
    assert plan.authorities[:70] == old_plan.authorities and len(plan.authorities) == 71
    assert plan.reviews == old_plan.reviews and len(plan.reviews) == 38
    assert (new.rows_with_review, new.rows_without_review) == (38, 33)
    row = new.sources[70]
    assert row.record_id == audit.source_id and row.reviews is None
    assert row.verified_http_acquired_at.isoformat() == '2026-09-16T21:52:46.950742+00:00'
    assert row.intake_received_at == audit.actual_repository_received_at
    assert row.intake_received_at > row.verified_http_acquired_at
    assert row.authority_id == 'CO-COUNTY-EL_PASO'
    assert not row.answer_safe and row.legal_currentness == 'not_verified'
    sys.stdout.write('PASS: closed one-source intake; exact old70/71 prefixes; '
                     '71 raw /72 ledger; inventory71/38/33; old70 rows and38 joins preserved.\n')


if __name__ == '__main__':
    main()
