"""Read-only closed wrapper and accepted source-fidelity verification."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
import jsonschema

ROOT=Path(__file__).resolve().parent


def read(name: str) -> bytes:
    """Read a confined ordinary local file."""
    parts=PurePosixPath(name)
    if parts.is_absolute() or '..' in parts.parts:
        raise ValueError('Unsafe relative path')
    path=ROOT/parts
    if not path.is_file() or any(p.is_symlink() for p in [path,*path.parents]):
        raise ValueError('Unsafe local artifact')
    return path.read_bytes()


def checked(asset: dict[str, object]) -> bytes:
    """Require exactly the expected file identity."""
    raw=read(str(asset['path']))
    if len(raw)!=asset['size_bytes'] or hashlib.sha256(raw).hexdigest()!=asset['sha256']:
        raise ValueError('Artifact identity differs: '+str(asset['path']))
    return raw


def inventory_check() -> dict[str, object]:
    """Reject missing, unbound, renamed or modified wrapper payloads."""
    manifest=json.loads(read('INVENTORY.json'))
    jsonschema.validate(manifest,json.loads(read('INVENTORY.schema.json')))
    names=[a['path'] for a in manifest['files']]
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    if len(names)!=len(set(names)) or actual!=set(names)|{'INVENTORY.json'}:
        raise ValueError('Closed inventory differs')
    for asset in manifest['files']:
        checked(asset)
    return manifest


def main() -> None:
    """Validate the wrapper, then execute its exact copied local source verifier."""
    before=inventory_check()
    acceptance=json.loads(read('ACCEPTANCE.json'))
    jsonschema.validate(acceptance,json.loads(read('ACCEPTANCE.schema.json')))
    qa=json.loads(checked(acceptance['source_review']))
    jsonschema.validate(qa,json.loads(checked(acceptance['source_review_schema'])))
    checked(acceptance['frozen_manifest'])
    checked(acceptance['root_direct_image_notes'])
    if (qa['source_id']!=acceptance['source_id'] or
            qa['source_sha256']!=acceptance['source_sha256'] or
            qa['authority_id']!=acceptance['authority_id']):
        raise ValueError('Acceptance identity mismatch')
    if acceptance['answer_safe'] or acceptance['legal_currentness']!='not_verified':
        raise ValueError('Unapproved legal promotion')
    result=subprocess.run([sys.executable,'-B',str(ROOT/'source-review/verify_review.py')],
                          check=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(result.returncode)
    if inventory_check()!=before:
        raise ValueError('Wrapper changed during verification')
    sys.stdout.buffer.write(result.stdout)
    sys.stdout.write('Accepted wrapper: closed local identities and scope verified.\n')


if __name__=='__main__':
    main()
