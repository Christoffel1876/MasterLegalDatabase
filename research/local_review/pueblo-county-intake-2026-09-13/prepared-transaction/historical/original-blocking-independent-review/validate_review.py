"""Verify frozen pre-repair review evidence without running a transaction."""
from pathlib import Path
import hashlib
import json
import sys
from review_models import Manifest, Review, Reproduction

root = Path(__file__).resolve().parent
manifest = Manifest.model_validate_json((root / 'FINAL_MANIFEST.json').read_bytes())
expected = {x.path for x in manifest.files} | {'FINAL_MANIFEST.json'}
actual = set()
for path in root.rglob('*'):
    if path.is_symlink() or not (path.is_file() or path.is_dir()):
        raise ValueError('Nonordinary evidence')
    if path.is_file():
        actual.add(path.relative_to(root).as_posix())
if actual != expected or len(expected) != len(manifest.files) + 1:
    raise ValueError('Closed membership differs')
for item in manifest.files:
    rel = Path(item.path)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Unsafe path')
    path = root / rel
    with path.open('rb') as handle:
        sha = hashlib.file_digest(handle, 'sha256').hexdigest()
    if sha != item.sha256 or path.stat().st_size != item.size_bytes:
        raise ValueError('Hash/size differs')
review = Review.model_validate_json((root / 'REVIEW.json').read_bytes())
proof = Reproduction.model_validate_json((root / 'REPRODUCTION.json').read_bytes())
for model, name in [(Manifest, 'FINAL_MANIFEST'), (Review, 'REVIEW'),
                    (Reproduction, 'REPRODUCTION')]:
    if json.loads((root / (name + '.schema.json')).read_bytes()) != model.model_json_schema():
        raise ValueError('Schema differs')
for item in review.checked_assets:
    path = root / 'reviewed-inputs' / item.path
    if hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256:
        raise ValueError('Reviewed input binding differs')
if 'MSI-foreign' not in proof.ledger_ids or not proof.unrelated_record_promoted_to_ledger:
    raise ValueError('Recorded counterexample differs')
sys.stdout.write(json.dumps({'status': 'passed', 'review_disposition': review.status,
                            'canonical_mutations': 0, 'public_requests': 0}) + '\n')
