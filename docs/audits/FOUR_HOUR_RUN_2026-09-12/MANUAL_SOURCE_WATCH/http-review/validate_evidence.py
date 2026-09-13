"""Read-only closed evidence verification; no repository, execution, or network needed."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import jsonschema

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'MANIFEST.json').read_bytes())
jsonschema.validate(manifest, json.loads((root / 'MANIFEST.schema.json').read_bytes()))
expected = {row['path'] for row in manifest['files']}
assert len(expected) == len(manifest['files']), 'duplicate path'
actual = set()
for path in root.rglob('*'):
    assert not path.is_symlink(), 'symlink'
    assert path.is_file() or path.is_dir(), 'nonordinary entry'
    if path.is_file() and path.name != 'MANIFEST.json':
        actual.add(path.relative_to(root).as_posix())
assert actual == expected, 'closed inventory mismatch'
for row in manifest['files']:
    relative = PurePosixPath(row['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    path = root / relative
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == row['sha256'] and path.stat().st_size == row['size_bytes']
receipt = json.loads((root / 'REVIEW_RECEIPT.json').read_bytes())
jsonschema.validate(receipt, json.loads((root / 'REVIEW_RECEIPT.schema.json').read_bytes()))
for row in receipt['reviewed_sources'] + [receipt['test_log'], receipt['coverage']]:
    assert row in manifest['files'], 'unbound receipt input'
assert receipt['tests_passed'] == 94
print('Verified closed offline review evidence; 94 focused tests recorded; no live HTTP.')
