"""Read-only, offline verification of the closed scanner-audit evidence."""
from hashlib import sha256
from pathlib import Path
import json
import sys

import jsonschema

from audit_models import Audit, Manifest


def verify(root: Path) -> None:
    """Verify closure, schemas, exact scan selections, and recorded probe outcomes."""
    manifest = Manifest.model_validate_json((root/'FINAL_MANIFEST.json').read_bytes())
    jsonschema.validate(manifest.model_dump(mode='json'),
                        json.loads((root/'FINAL_MANIFEST.schema.json').read_bytes()))
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in audit')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    expected = {asset.path for asset in manifest.files}
    if len(expected) != len(manifest.files) or actual != expected | {'FINAL_MANIFEST.json'}:
        raise ValueError('Audit closure differs')
    for asset in manifest.files:
        path = Path(asset.path)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe manifest path')
        raw = (root/path).read_bytes()
        if (sha256(raw).hexdigest(), len(raw)) != (asset.sha256, asset.size_bytes):
            raise ValueError('Audit payload differs: '+asset.path)
    audit = Audit.model_validate_json((root/'AUDIT.json').read_bytes())
    jsonschema.validate(audit.model_dump(mode='json'),
                        json.loads((root/'AUDIT.schema.json').read_bytes()))
    for asset in [audit.original_scanner, audit.proposed_scanner,
                  audit.original_scan, audit.proposed_scan]:
        raw = (root/asset.path).read_bytes()
        if (sha256(raw).hexdigest(), len(raw)) != (asset.sha256, asset.size_bytes):
            raise ValueError('Audit record identity differs')
    for name, counts in [('before-final-install', (17, 2441, 85)),
                         ('proposed-runs/reviewed-current-no-staging', (19, 2511, 87))]:
        folder = root/name
        scan = json.loads((folder/'SCAN.json').read_bytes())
        jsonschema.validate(scan, json.loads((folder/'SCAN.schema.json').read_bytes()))
        files = scan['files']
        paths = [asset['path'] for asset in files]
        if len(paths) != len(set(paths)):
            raise ValueError('Duplicate scan path')
        force = [asset['path'] for asset in files if asset['ignored'] and not asset['tracked']]
        if (scan['wrappers'], len(paths), len(force)) != counts:
            raise ValueError('Scan counts differ')
        if scan['new_raw_originals'] != 6:
            raise ValueError('Raw append scope differs')
        for filename, names in [('paths.nul', paths), ('force-add.nul', force)]:
            expected_bytes = b'\0'.join(name.encode() for name in names)+b'\0'
            if (folder/filename).read_bytes() != expected_bytes:
                raise ValueError('NUL selection differs')
        if set(paths) & set(scan['excluded_user_paths']):
            raise ValueError('Excluded user path selected')
    log = (root/'original-reproduction.stdout.log').read_text()
    tail = log[log.index('{\n  "scanner_sha256"'):]
    result = json.loads(tail)
    if result['scanner_sha256'] != audit.original_scanner.sha256:
        raise ValueError('Original reproduction pin differs')
    if result['expected_wrapper_payload_sha256'] == result['returned_payload_sha256']:
        raise ValueError('Original reproduction did not reproduce')
    if result['actual_production_occurrence_asserted']:
        raise ValueError('Reproduction scope overstated')
    if '9 passed' not in (root/'focused-tests.log').read_text():
        raise ValueError('Focused result absent')
    sys.stdout.write('PASS: closed audit, two scan inventories, preserved repro, nine tests.\n')


if __name__ == '__main__':
    verify(Path(__file__).resolve().parent)
