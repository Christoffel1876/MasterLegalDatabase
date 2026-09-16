"""Seal this preparation once, after tests; never apply canonical records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from models import Asset, Manifest

ROOT = Path(__file__).absolute().parent


def main() -> None:
    """Create the final strict closed inventory without changing an existing seal."""
    destination = ROOT / 'FINAL_MANIFEST.json'
    if destination.exists():
        raise ValueError('Existing seal; do not rerun the historical builder')
    schema = ROOT / 'FINAL_MANIFEST.schema.json'
    with schema.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(Manifest.model_json_schema(), indent=2) + '\n')
    items = []
    for path in sorted(ROOT.rglob('*'), key=lambda item: item.relative_to(ROOT).as_posix()):
        if path.is_symlink():
            raise ValueError('Linked preparation member')
        if path.is_file():
            body = path.read_bytes()
            items.append(Asset(path=path.relative_to(ROOT).as_posix(),
                               sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body)))
    record = Manifest(schema_version=1, files=items,
                      scope='closed_preparation_excluding_future_execution')
    body = (record.model_dump_json(indent=2) + '\n').encode('utf-8')
    Manifest.model_validate_json(body)
    temporary = destination.with_suffix('.tmp')
    with temporary.open('xb') as handle:
        handle.write(body)
    temporary.replace(destination)


if __name__ == '__main__':
    main()
