"""Read-only verification of the small accepted-review wrapper."""
import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path, PurePosixPath
from acceptance_models import Acceptance, Asset, Inventory

ROOT = Path(__file__).resolve().parent


def read(name: str) -> bytes:
    """Read only an ordinary file inside this acceptance package."""
    part = PurePosixPath(name)
    if part.is_absolute() or '..' in part.parts:
        raise ValueError('Unsafe relative path')
    path = ROOT / part
    if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Nonordinary payload')
    return path.read_bytes()


def check(asset: Asset) -> bytes:
    """Verify an asset's exact retained bytes."""
    raw = read(asset.path)
    if (len(raw), hashlib.sha256(raw).hexdigest()) != (asset.size_bytes, asset.sha256):
        raise ValueError('Payload changed: ' + asset.path)
    return raw


def main() -> None:
    """Check the closed package and replay the bounded source verifier."""
    before = read('INVENTORY.json')
    inv = Inventory.model_validate_json(before)
    names = [a.path for a in inv.files]
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    if len(names) != len(set(names)) or actual != set(names) | {'INVENTORY.json'}:
        raise ValueError('Closed inventory mismatch')
    for asset in inv.files:
        check(asset)
    for name, model in [('ACCEPTANCE', Acceptance), ('INVENTORY', Inventory)]:
        if json.loads(read(name + '.schema.json')) != model.model_json_schema():
            raise ValueError('Schema differs from model')
    accepted = Acceptance.model_validate_json(read('ACCEPTANCE.json'))
    qa = json.loads(check(accepted.source_review))
    check(accepted.source_review_schema)
    check(accepted.frozen_manifest)
    check(accepted.root_reading)
    if (qa['source_id'], qa['source']['sha256'], qa['authority_id']) != (
            accepted.source_id, accepted.source_sha256, accepted.authority_id):
        raise ValueError('Source identity mismatch')
    if accepted.pages_directly_inspected != list(range(1, 8)):
        raise ValueError('Incomplete acceptance')
    if qa['legal_currentness'] != 'not_verified' or qa['answer_safe']:
        raise ValueError('Unexpected legal promotion')
    subprocess.run(
        [sys.executable, '-B', str(ROOT / 'source-review/verify_review.py')], check=True,
    )
    if read('INVENTORY.json') != before:
        raise ValueError('Inventory changed during verification')
    logging.info('PASS: exact source, seven-page review, preserved evidence and limited scope')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
