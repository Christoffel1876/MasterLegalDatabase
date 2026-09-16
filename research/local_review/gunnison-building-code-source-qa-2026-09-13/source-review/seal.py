"""Seal a new packet or preserve a prior inventory before additive resealing."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
from models import Asset, Manifest
from prepare import ROOT, write


def main() -> None:
    """Validate every new inventory record before atomic publication."""
    path = ROOT / 'FINAL_MANIFEST.json'
    if path.exists():
        raw = path.read_bytes()
        old = ROOT / 'preparation-history/manifests' / (hashlib.sha256(raw).hexdigest() + '.json')
        write(old, raw)
    files = []
    for candidate in sorted(ROOT.rglob('*')):
        if candidate.is_symlink():
            raise ValueError('No symlinks in package')
        if not candidate.is_file() or candidate == path:
            continue
        if '__pycache__' in candidate.parts or '.pytest_cache' in candidate.parts:
            raise ValueError('Unexpected cache file; preserve outside the closed packet')
        raw = candidate.read_bytes()
        files.append(Asset(path=candidate.relative_to(ROOT).as_posix(),
                           sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    record = Manifest(schema_version='1.0', status='source_review_only_currentness_not_verified',
                      files=files)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(record.model_dump_json(indent=2) + '\n')
    temporary.replace(path)


if __name__ == '__main__':
    main()
