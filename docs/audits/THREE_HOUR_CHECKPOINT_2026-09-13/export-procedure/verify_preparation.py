"""Read-only validation of procedure pins and its closed preparation inventory."""
from hashlib import sha256
from pathlib import Path
import json
import sys

import jsonschema

from preparation_models import Manifest, Preparation


def main() -> None:
    """Validate all pinned payloads without importing or running the export procedure."""
    root = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((root/'FINAL_MANIFEST.json').read_bytes())
    preparation = Preparation.model_validate_json((root/'PREPARATION.json').read_bytes())
    for name, value in [('FINAL_MANIFEST', manifest), ('PREPARATION', preparation)]:
        jsonschema.validate(value.model_dump(mode='json'),
                            json.loads((root/(name+'.schema.json')).read_bytes()))
    expected = {asset.path for asset in manifest.files}
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in procedure package')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if len(expected) != len(manifest.files) or actual != expected | {'FINAL_MANIFEST.json'}:
        raise ValueError('Closed inventory differs')
    for asset in manifest.files + preparation.files:
        path = Path(asset.path)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe package member')
        raw = (root/path).read_bytes()
        if (sha256(raw).hexdigest(), len(raw)) != (asset.sha256, asset.size_bytes):
            raise ValueError('Pinned payload differs: '+asset.path)
    if '23 passed' not in (root/'final-tests.log').read_text():
        raise ValueError('Final fixture result differs')
    sys.stdout.write('PASS: prepared procedure and schemas pinned; no export has run.\n')


if __name__ == '__main__':
    main()
