"""Verify independent revision review custody without executing intake code."""
from pathlib import Path
import hashlib
import json
import sys
from review_models import Manifest, Review

root = Path(__file__).resolve().parent
manifest = Manifest.model_validate_json((root / 'FINAL_MANIFEST.json').read_bytes())
expected = {a.path for a in manifest.files} | {'FINAL_MANIFEST.json'}
actual = set()
for path in root.rglob('*'):
    if path.is_symlink() or not (path.is_file() or path.is_dir()):
        raise ValueError('Nonordinary evidence')
    if path.is_file():
        actual.add(path.relative_to(root).as_posix())
if expected != actual or len(expected) != len(manifest.files) + 1:
    raise ValueError('Closed membership differs')
for item in manifest.files:
    rel = Path(item.path)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Unsafe reference')
    path = root / rel
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    if digest != item.sha256 or path.stat().st_size != item.size_bytes:
        raise ValueError('Evidence differs')
review = Review.model_validate_json((root / 'REVIEW.json').read_bytes())
for model, name in [(Review, 'REVIEW'), (Manifest, 'FINAL_MANIFEST')]:
    if json.loads((root / (name + '.schema.json')).read_bytes()) != model.model_json_schema():
        raise ValueError('Schema differs')
for item in review.reviewed_inputs:
    raw = (root / 'reviewed-inputs' / item.path).read_bytes()
    if len(raw) != item.size_bytes or hashlib.sha256(raw).hexdigest() != item.sha256:
        raise ValueError('Reviewed input differs')
if '13 passed' not in (root / 'independent-tests.log').read_text():
    raise ValueError('Test receipt differs')
preflight = json.loads((root / 'live-dry-run.stdout.txt').read_bytes())
if (preflight['raw_before'], preflight['ledger_before'],
    preflight['raw_after'], preflight['ledger_after']) != (63, 64, 64, 65):
    raise ValueError('Preflight scope differs')
if preflight['canonical_mutations'] != 0 or preflight['actual_repository_received_at'] is not None:
    raise ValueError('Preflight status differs')
sys.stdout.write(json.dumps({'status': 'passed', 'review': review.status,
                            'independent_tests': 13, 'canonical_writes': 0}) + '\n')
