"""Validate the additive review inventory without running the historical reproducer."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
from models import Check, Manifest, Review


def validate(base: Path) -> dict:
    """Check only this packet's closed ordinary files, hashes and typed records."""
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise ValueError('Symlink root')
    manifest = Manifest.model_validate_json((base / 'FINAL_MANIFEST.json').read_bytes())
    paths = [item.path for item in manifest.files]
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate file')
    actual = set()
    for p in base.rglob('*'):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise ValueError('Nonordinary member')
        if p.is_file():
            actual.add(p.relative_to(base).as_posix())
    if actual != set(paths) | {'FINAL_MANIFEST.json'}:
        raise ValueError('Closed membership differs')
    for item in manifest.files:
        p = Path(item.path)
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('Path escape')
        body = (base / p).read_bytes()
        if len(body) != item.size_bytes or hashlib.sha256(body).hexdigest() != item.sha256:
            raise ValueError('Payload differs: ' + item.path)
    review = Review.model_validate_json((base / 'REVIEW.json').read_bytes())
    check = Check.model_validate_json((base / 'FINAL_READ_ONLY_CHECK.json').read_bytes())
    if check.before != check.after or check.completed_at < check.started_at:
        raise ValueError('Pin or time mismatch')
    if check.completed_at > review.reviewed_at:
        raise ValueError('Review predates final check')
    for cls, stem in [(Review, 'REVIEW'), (Check, 'FINAL_READ_ONLY_CHECK'), (Manifest, 'FINAL_MANIFEST')]:
        if json.loads((base / (stem + '.schema.json')).read_bytes()) != cls.model_json_schema():
            raise ValueError('Schema differs')
    return {'status': 'verified_closed_additive_review', 'payloads': len(paths),
            'decision': review.status, 'transaction_executed': False,
            'historical_reproducer_executed': False, 'public_requests': 0}


if __name__ == '__main__':
    print(json.dumps(validate(Path(__file__).absolute().parent), indent=2))
