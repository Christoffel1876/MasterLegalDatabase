"""Verify this closed review packet only; never invoke transaction or network code."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from models import Expectations, FinalReview, Manifest, ReadOnlyCheck


def validate(base: Path) -> dict:
    """Check ordinary files, exact hashes and the typed bounded review assertions."""
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise ValueError('Review path is a symlink')
    manifest = Manifest.model_validate_json((base / 'FINAL_MANIFEST.json').read_bytes())
    names = [r.path for r in manifest.files]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate manifest member')
    actual = set()
    for path in base.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Nonordinary member')
        if path.is_file():
            actual.add(path.relative_to(base).as_posix())
    if actual != set(names) | {'FINAL_MANIFEST.json'}:
        raise ValueError('Closed inventory differs')
    for ref in manifest.files:
        relative = Path(ref.path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Manifest path escape')
        content = (base / relative).read_bytes()
        if len(content) != ref.size_bytes or hashlib.sha256(content).hexdigest() != ref.sha256:
            raise ValueError('Payload digest or size differs: ' + ref.path)
    expectations = Expectations.model_validate_json((base / 'EXPECTATIONS.json').read_bytes())
    review = FinalReview.model_validate_json((base / 'FINAL_REVIEW.json').read_bytes())
    check = ReadOnlyCheck.model_validate_json((base / 'READ_ONLY_CHECK.json').read_bytes())
    if check.before != check.after or check.completed_at < check.started_at:
        raise ValueError('Read-only observations conflict')
    if len(check.before) != 10 or check.completed_at > review.completed_at:
        raise ValueError('Recorded scope or timing differs')
    ref = review.expectations
    content = (base / 'EXPECTATIONS.json').read_bytes()
    if ref.sha256 != hashlib.sha256(content).hexdigest() or ref.size_bytes != len(content):
        raise ValueError('Frozen expectation binding differs')
    if any(c.exact_matches for c in expectations.comparisons):
        raise ValueError('Unexpected duplicate finding')
    for model, name in [(Expectations, 'EXPECTATIONS'), (FinalReview, 'FINAL_REVIEW'),
                        (ReadOnlyCheck, 'READ_ONLY_CHECK'), (Manifest, 'FINAL_MANIFEST')]:
        if json.loads((base / (name + '.schema.json')).read_bytes()) != model.model_json_schema():
            raise ValueError('Schema differs: ' + name)
    return {'status': 'verified_closed_review', 'payloads': len(names), 'sources': 2,
            'directly_viewed_full_pages': 5, 'scope': review.status,
            'repository_state_rechecked': False, 'transaction_executed': False,
            'public_requests': 0, 'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    print(json.dumps(validate(Path(__file__).absolute().parent), indent=2))
