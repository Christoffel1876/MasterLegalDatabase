"""Seal the prepared handoff once; never execute or mutate canonical records."""
import hashlib
import json
import os
from pathlib import Path

from models import Asset, Manifest

HERE = Path(__file__).absolute().parent


def main() -> None:
    """Include every ordinary prepared payload and its schema, excluding only this seal."""
    destination = HERE / 'FINAL_MANIFEST.json'
    if destination.exists():
        raise ValueError('Final preparation already sealed')
    schema = HERE / 'FINAL_MANIFEST.schema.json'
    schema.write_text(json.dumps(Manifest.model_json_schema(), indent=2) + '\n')
    files = []
    for top, dirs, names in os.walk(HERE, followlinks=False):
        for name in dirs + names:
            if (Path(top) / name).is_symlink():
                raise ValueError('linked preparation member')
        for name in names:
            path = Path(top) / name
            if not path.is_file():
                raise ValueError('nonordinary preparation member')
            relative = path.relative_to(HERE).as_posix()
            if relative.startswith('execution/'):
                raise ValueError('Unexpected canonical execution during preparation')
            body = path.read_bytes()
            files.append(Asset(path=relative, sha256=hashlib.sha256(body).hexdigest(),
                               size_bytes=len(body)))
    manifest = Manifest(schema_version=1, files=sorted(files, key=lambda a: a.path),
                        scope='closed_preparation_excluding_future_execution')
    raw = manifest.model_dump_json(indent=2).encode() + b'\n'
    Manifest.model_validate_json(raw)
    temporary = HERE / 'FINAL_MANIFEST.tmp'; temporary.write_bytes(raw)
    os.replace(temporary, destination)
    print(hashlib.sha256(raw).hexdigest(), len(files), sum(a.size_bytes for a in files))


if __name__ == '__main__':
    main()
