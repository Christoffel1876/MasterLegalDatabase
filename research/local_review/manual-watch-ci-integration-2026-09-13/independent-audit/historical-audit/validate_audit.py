"""Read-only closure verifier for the independent prepared-CI review receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

import jsonschema

from audit_models import Audit, Inventory


def ordinary(root: Path, name: str) -> Path:
    """Refuse absolute, traversal, ambiguous and linked evidence paths."""
    pure = PurePosixPath(name)
    if (pure.is_absolute() or '\\' in name or
            any(part in {'', '.', '..'} for part in name.split('/'))):
        raise ValueError('Unconfined evidence path')
    path = root.joinpath(*pure.parts)
    if any(item.is_symlink() for item in [path, *path.parents]) or not path.is_file():
        raise ValueError('Nonordinary evidence')
    return path


def validate(root: Path) -> dict[str, int | str]:
    """Verify retained bytes and typed results without importing the proposed runner."""
    manifest = Inventory.model_validate_json(ordinary(root, 'FINAL_MANIFEST.json').read_bytes())
    names = [asset.path for asset in manifest.files]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate file identity')
    actual = []
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Linked payload')
        if path.is_file() and path != root / 'FINAL_MANIFEST.json':
            actual.append(path.relative_to(root).as_posix())
    if set(actual) != set(names):
        raise ValueError('Closed inventory differs')
    for asset in manifest.files:
        raw = ordinary(root, asset.path).read_bytes()
        if len(raw) != asset.size_bytes or hashlib.sha256(raw).hexdigest() != asset.sha256:
            raise ValueError('Evidence identity mismatch: ' + asset.path)
    schema = json.loads(ordinary(root, 'AUDIT.schema.json').read_bytes())
    if schema != Audit.model_json_schema():
        raise ValueError('Schema differs from strict model')
    raw = ordinary(root, 'AUDIT.json').read_bytes()
    record = Audit.model_validate_json(raw)
    jsonschema.validate(json.loads(raw), schema)
    if record.stage != 'frozen_independent_review':
        raise ValueError('Review not frozen')
    for asset in record.inputs:
        value = ordinary(root, asset.path).read_bytes()
        if (len(value) != asset.size_bytes or
                hashlib.sha256(value).hexdigest() != asset.sha256):
            raise ValueError('Reviewed input mismatch')
    for check in record.checks:
        for name in check.evidence:
            ordinary(root, name)
    for finding in record.findings:
        for name in finding.evidence:
            ordinary(root, name)
    return {'status': 'pass', 'payloads': len(names), 'checks': len(record.checks),
            'public_requests': record.public_requests}


def main() -> None:
    """Verify a supplied portable packet without network or repository dependencies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    arguments = parser.parse_args()
    sys.stdout.write(json.dumps(validate(arguments.root)) + '\n')


if __name__ == '__main__':
    main()
