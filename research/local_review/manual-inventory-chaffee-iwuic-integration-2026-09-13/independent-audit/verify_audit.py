"""Read-only closed-audit verification; no Git, source review or staging."""
from pathlib import Path
import hashlib
import json
import sys
import jsonschema


def verify() -> dict:
    """Verify all sealed payloads and known strict metadata schemas."""
    root = Path(__file__).absolute().parent
    if any(p.is_symlink() for p in [root, *root.parents]):
        raise ValueError('linked audit root')
    manifest = json.loads((root / 'FINAL_MANIFEST.json').read_bytes())
    jsonschema.validate(manifest, json.loads((root / 'FINAL_MANIFEST.schema.json').read_bytes()))
    names = [f['path'] for f in manifest['files']]
    actual = [p for p in root.rglob('*')]
    if any(p.is_symlink() for p in actual):
        raise ValueError('linked audit member')
    if len(names) != len(set(names)) or {p.relative_to(root).as_posix() for p in actual
            if p.is_file()} != set(names) | {'FINAL_MANIFEST.json'}:
        raise ValueError('audit inventory mismatch')
    captured = {}
    for item in manifest['files']:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('unsafe audit member')
        body = (root / relative).read_bytes()
        if len(body) != item['size_bytes'] or hashlib.sha256(body).hexdigest() != item['sha256']:
            raise ValueError('audit byte identity differs')
        captured[item['path']] = body
    for name, body in captured.items():
        if name.endswith('.schema.json'):
            data_name = name.replace('.schema.json', '.json')
            if data_name in captured:
                jsonschema.validate(json.loads(captured[data_name]), json.loads(body))
    selected = json.loads(captured['NEEDED_FORCE_ADD.json'])['files']
    expected = ('\0'.join(x['path'] for x in selected) + '\0').encode()
    if captured['needed-force-add.nul'] != expected:
        raise ValueError('pathspec differs from typed selection')
    return {'status': 'PASS', 'payloads': len(names), 'force_add_candidates': len(selected),
            'staged': False, 'repository_state_rechecked': False}


if __name__ == '__main__':
    sys.stdout.write(json.dumps(verify()) + '\n')
