"""Read-only closed preparation verification; never apply or run historical code."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import jsonschema
from models import Manifest, Preparation


def checked(root: Path, name: str, sha256: str, size: int) -> bytes:
    """Return exactly one ordinary checked file buffer."""
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name:
        raise ValueError('unsafe member')
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('nonordinary member')
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError('member differs: ' + name)
    return raw


def verify(root: Path, pin: str) -> dict[str, str | int]:
    """Verify local closure, strict preparation, subset provenance and source formats."""
    for path in [root, *root.rglob('*')]:
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('nonordinary closure entry')
    raw = (root / 'FINAL_MANIFEST.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('closed manifest pin differs')
    manifest = Manifest.model_validate_json(raw)
    declared = {item.path for item in manifest.files}
    if len(declared) != len(manifest.files):
        raise ValueError('duplicate member')
    observed = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    observed = {name for name in observed if not name.startswith('execution/')}
    if observed != declared | {'FINAL_MANIFEST.json'}:
        raise ValueError('closed membership differs')
    buffers = {a.path: checked(root, a.path, a.sha256, a.size_bytes) for a in manifest.files}
    for name, data in buffers.items():
        if name.endswith('.json') and not name.endswith('.schema.json'):
            schema = name[:-5] + '.schema.json'
            if schema in buffers:
                jsonschema.validate(json.loads(data), json.loads(buffers[schema]))
    plan = Preparation.model_validate_json(buffers['PREPARATION.json'])
    for prefix in ['inputs/queue', 'inputs/roles/custer', 'inputs/roles/delta']:
        original = json.loads(buffers[prefix + '/FINAL_MANIFEST.json'])
        members = {a['path']: a for a in original['files']}
        for name, data in buffers.items():
            if not name.startswith(prefix + '/'):
                continue
            short = name[len(prefix) + 1:]
            if short == 'FINAL_MANIFEST.json':
                continue
            asset = members[short]
            if (hashlib.sha256(data).hexdigest() != asset['sha256']
                    or len(data) != asset.get('size_bytes', asset.get('bytes'))):
                raise ValueError('copied subset differs from its original manifest')
    import transaction as tx
    tx.check_custody(root, plan)
    tx.execution_paths(root, plan)
    return dict(status='passed_closed_preparation_only', payloads=len(manifest.files),
                source_bytes=sum(t.source.size_bytes for t in plan.templates))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.manifest_sha256), indent=2))
