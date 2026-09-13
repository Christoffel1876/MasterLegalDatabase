"""Preserve the verified installed test repair as an unchanged local review package."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os

from pydantic import BaseModel, ConfigDict

BASE = Path('/Users/mcoors/Documents/Project Geode')
SOURCE = BASE / 'handoffs/run-2026-09-12/extended-run/manual-watch-installed-test-repair'
DEST = BASE / 'MasterLegalDatabase/research/local_review/manual-watch-test-repair-2026-09-13'


class File(BaseModel):
    """One exact file copied without editing its contents."""
    model_config = ConfigDict(extra='forbid')
    path: str
    sha256: str
    size_bytes: int


class Receipt(BaseModel):
    """Actual preservation event, separate from the earlier test execution."""
    model_config = ConfigDict(extra='forbid')
    preserved_at: datetime
    status: str
    files: list[File]


def save(path: Path, raw: bytes) -> None:
    """Atomically create a new file, refusing replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Destination already exists')
    temp = path.with_name(path.name + '.tmp')
    with temp.open('xb') as handle:
        handle.write(raw)
    os.replace(temp, path)


def main() -> None:
    """Capture all inputs, validate the receipt and preserve the exact closed package."""
    if DEST.exists():
        raise ValueError('Refusing to reuse preservation folder')
    pins = {
        'FINAL_MANIFEST.json':
        '734fdd195ab85ab3f1ba1d7a477c00bb08d492bf319505726e20a0da692492bf',
        'RECEIPT.json':
        '2f40d15493b00d9143b498a7402201e6d07b9163a5763771186d4a7db2426bb2',
    }
    buffers = {}
    for path in sorted(SOURCE.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in preserved package')
        if path.is_file():
            buffers[path.relative_to(SOURCE).as_posix()] = path.read_bytes()
    for name, expected in pins.items():
        if hashlib.sha256(buffers[name]).hexdigest() != expected:
            raise ValueError('Frozen repair identity differs')
    files = [File(path='frozen/' + name, sha256=hashlib.sha256(raw).hexdigest(),
                  size_bytes=len(raw)) for name, raw in buffers.items()]
    receipt = Receipt(preserved_at=datetime.now(timezone.utc),
                      status='copied_unchanged_after_root_portable_verification', files=files)
    for name, raw in buffers.items():
        save(DEST / 'frozen' / name, raw)
        if (SOURCE / name).read_bytes() != raw:
            raise ValueError('Source changed during copy')
    save(DEST / 'PRESERVATION.schema.json',
         (json.dumps(Receipt.model_json_schema(), indent=2) + '\n').encode())
    save(DEST / 'PRESERVATION.json', (receipt.model_dump_json(indent=2) + '\n').encode())
    save(DEST / Path(__file__).name, Path(__file__).read_bytes())
    print(receipt.model_dump_json())


if __name__ == '__main__':
    main()
