"""Portable, read-only audit seal verification; never runs the reviewed transaction."""
import hashlib
import json
import sys
from pathlib import Path

import jsonschema

from audit_models import Audit, Manifest

ROOT = Path(__file__).resolve().parent


def verify(root: Path = ROOT) -> int:
    """Validate all exact copied evidence, typed conclusion and recorded outcomes."""
    manifest = Manifest.model_validate_json((root / 'FINAL_MANIFEST.json').read_bytes())
    paths = {a.path for a in manifest.files}
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    assert len(paths) == len(manifest.files)
    assert actual == paths | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'}
    for asset in manifest.files:
        path = root / asset.path
        assert not Path(asset.path).is_absolute() and '..' not in Path(asset.path).parts
        assert not any(p.is_symlink() for p in [path, *path.parents])
        data = path.read_bytes()
        assert len(data) == asset.size_bytes
        assert hashlib.sha256(data).hexdigest() == asset.sha256
    raw = (root / 'AUDIT.json').read_bytes()
    audit = Audit.model_validate_json(raw)
    jsonschema.validate(json.loads(raw), json.loads((root / 'AUDIT.schema.json').read_bytes()))
    assert len(audit.sources) == 3
    assert [s.pages for s in audit.sources] == [3, 16, 4]
    assert sum(s.size_bytes for s in audit.sources) == 923643
    for asset in audit.reviewed_package:
        data = (root / asset.path).read_bytes()
        assert len(data) == asset.size_bytes
        assert hashlib.sha256(data).hexdigest() == asset.sha256
    checks = json.loads((root / 'READ_ONLY_CHECKS.json').read_bytes())
    jsonschema.validate(checks, json.loads((root / 'READ_ONLY_CHECKS.schema.json').read_bytes()))
    assert checks['managed_before'] == checks['managed_after']
    assert checks['execution_directory_present'] is False
    for event in checks['events']:
        assert event['exit_code'] == 0
        for stream in ['stdout', 'stderr']:
            data = (root / event[stream + '_path']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == event[stream + '_sha256']
    output = (root / 'probes-v2.stdout.txt').read_text().splitlines()
    assert output == audit.independent_cases_passed and len(output) == 4
    assert (root / 'probes-v2.stderr.txt').read_bytes() == b''
    assert b'symlink in reconciliation path' in (root / 'probes.stderr.txt').read_bytes()
    return len(manifest.files)


if __name__ == '__main__':
    sys.stdout.write(f'PASS: {verify()} closed audit payloads; no canonical apply.\n')
