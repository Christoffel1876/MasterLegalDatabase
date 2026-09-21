"""Read-only receipt closure and exact live installed inventory preservation checks."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import jsonschema
from pydantic import TypeAdapter

from integration_models import Asset, Execution, Manifest, Start

HERE=Path(__file__).resolve().parent


def checked(root: Path, ref: Asset) -> bytes:
    """Read only a safe local exact identity; never follow a stored external location."""
    relative=Path(ref.path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe receipt path')
    path=root/relative
    if any(x.is_symlink() for x in (path,*path.parents)):
        raise ValueError('Symlinked receipt path')
    raw=path.read_bytes()
    if (sha256(raw).hexdigest(),len(raw))!=(ref.sha256,ref.size_bytes):
        raise ValueError('Receipt identity differs: '+ref.path)
    return raw


def main() -> None:
    """Verify closed receipts, prior snapshots and the exact installed source-only delta."""
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=HERE.parents[2])
    args=parser.parse_args();root=args.root.resolve()
    manifest=Manifest.model_validate_json((HERE/'FINAL_MANIFEST.json').read_bytes())
    jsonschema.validate(manifest.model_dump(mode='json'),
                        json.loads((HERE/'FINAL_MANIFEST.schema.json').read_bytes()))
    expected={x.path for x in manifest.files}
    actual={p.relative_to(root).as_posix() for p in HERE.rglob('*') if p.is_file()}
    if actual!=expected|{(HERE/'FINAL_MANIFEST.json').relative_to(root).as_posix()}:
        raise ValueError('Closed integration receipt membership differs')
    for asset in manifest.files:
        checked(root,asset)
    receipt=Execution.model_validate_json((HERE/'EXECUTION.json').read_bytes())
    jsonschema.validate(receipt.model_dump(mode='json'),
                        json.loads((HERE/'EXECUTION.schema.json').read_bytes()))
    start=Start.model_validate_json(checked(root,receipt.application_checkpoint))
    jsonschema.validate(start.model_dump(mode='json'),
                        json.loads((HERE/'APPLICATION_STARTED.schema.json').read_bytes()))
    preimages=TypeAdapter(list[Asset]).validate_json((HERE/'PREIMAGES.json').read_bytes())
    jsonschema.validate(json.loads((HERE/'PREIMAGES.json').read_bytes()),
                        json.loads((HERE/'PREIMAGES.schema.json').read_bytes()))
    if preimages!=start.before:
        raise ValueError('Preimage record differs')
    for asset in [receipt.accepted_source,receipt.accepted_wrapper_inventory,
                  receipt.prepared_plan,receipt.source_review_artifact,
                  receipt.source_review_schema,*receipt.snapshot_files,
                  *receipt.installed_files,*receipt.unchanged_required_files]:
        checked(root,asset)
    package=root/'research/local_review/manual-source-review-inventory-2026-09-11'
    before=root/receipt.snapshot_directory
    old_plan=json.loads((before/'join-plan.json').read_bytes())
    plan=json.loads((package/'join-plan.json').read_bytes())
    old=json.loads((before/'inventory.json').read_bytes())
    new=json.loads((package/'inventory.json').read_bytes())
    assert plan['authorities']==old_plan['authorities'] and len(plan['authorities'])==70
    assert plan['reviews'][:36]==old_plan['reviews'] and len(plan['reviews'])==37
    assert plan['reviews'][36]['record_id']==receipt.source_id
    assert (len(new['sources']),new['rows_with_review'],new['rows_without_review'])==(70,37,33)
    for prior,current in zip(old['sources'],new['sources'],strict=True):
        candidate=dict(current)
        if current['record_id']==receipt.source_id:
            candidate.update(reviews=None,review_status='metadata_only_review_unknown')
        assert candidate==prior, current['record_id']
    for name in ['inventory.schema.json','join-plan.schema.json']:
        assert (before/name).read_bytes()==(package/name).read_bytes()
    assert new['legal_currentness']=='not_verified'
    assert not new['answer_safe'] and not new['coverage_promotion']
    sys.stdout.write('PASS: closed integration receipt; 70/37/33; all 70 authority joins, '
                     '36 prior reviews, 69 other rows and unchanged raw/control/custody pins.\n')


if __name__=='__main__':
    main()
