"""Read-only offline hash, binding, closure and exact text-comparison replay."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import sys
from models import Audit, Manifest


def sha(data: bytes) -> str:
    """Return a SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def read(root: Path, name: str) -> bytes:
    """Read one ordinary contained file, refusing unsafe paths and symlinks."""
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('Unsafe relative path')
    p = root
    for part in rel.parts:
        p = p / part
        if p.is_symlink():
            raise ValueError('Symlink refused')
    if not p.is_file():
        raise ValueError('Missing ordinary file')
    return p.read_bytes()


def normalize(text: str) -> str:
    """Collapse whitespace and normalize only the right curly apostrophe."""
    return re.sub(r'\s+', ' ', text.replace('’', "'")).strip()


def body(text: str, external: bool) -> str:
    """Select transcript body, excluding explicitly delimited reviewer notes."""
    value = text.split('## Physical page 7', 1)[1]
    if not external:
        return value.split('## Physical page 8', 1)[0].strip()
    value = value[value.index('11.1 '):]
    end = 'Section14: Severability Clause.'
    return value[:value.index(end) + len(end)]


def checks(root: Path) -> dict:
    """Replay nested delivery bindings and the packet/source comparison."""
    delivery = root / 'received'
    results = {}
    for name in ('HASH_INVENTORY.txt', 'CHECKSUMS.sha256'):
        entries = {}
        for line in read(delivery, name).decode().splitlines():
            if not line or line.startswith(('#', 'utc:', 'assignment:')):
                continue
            match = re.fullmatch(r'([a-f0-9]{64})  (.+)', line)
            if not match:
                raise ValueError('Malformed checksum line')
            digest, path = match.groups()
            if path in entries or sha(read(delivery, path)) != digest:
                raise ValueError('Duplicate or invalid checksum')
            entries[path] = digest
        results[name] = entries
    freeze = json.loads(read(delivery, 'PASS1_FREEZE_RECEIPT.json'))
    leaves = dict(freeze['bindings'])
    crops = leaves.pop('original-crops')
    if len(crops) != 8:
        raise ValueError('Eight crop bindings required')
    for ref in crops.values():
        leaves[ref['path']] = ref
    for path, ref in leaves.items():
        data = read(delivery, path)
        if sha(data) != ref['sha256'] or len(data) != ref['size_bytes']:
            raise ValueError('Freeze binding mismatch')
    complete = json.loads(read(delivery, 'COMPLETION_RECEIPT.json'))
    for path, digest in complete['hashes'].items():
        if sha(read(delivery, path)) != digest:
            raise ValueError('Completion binding mismatch')
    packet = json.loads(read(root, 'packet/MANIFEST.json'))
    for ref in packet['files']:
        data = read(root / 'packet', ref['path'])
        if sha(data) != ref['sha256'] or len(data) != ref['size_bytes']:
            raise ValueError('Packet binding mismatch')
    for dest, src in [('source/page-7.png', '01-source-only/page-7.png'),
                      ('02-candidate/candidate.txt', '02-candidate/candidate.txt')]:
        if read(delivery, dest) != read(root / 'packet', src):
            raise ValueError('Assigned source or candidate differs')
    a = body(read(delivery, 'PASS1_frozen.md').decode(), True)
    b = body(read(root, 'root-reading/CORRECTED_READING.md').decode(), False)
    if normalize(a) != normalize(b):
        raise ValueError('Transcript body differs after permitted normalization')
    return dict(listed_hashes=len(results['HASH_INVENTORY.txt']),
                listed_checksums=len(results['CHECKSUMS.sha256']),
                freeze_leaf_bindings=len(leaves),
                completion_hash_bindings=len(complete['hashes']),
                normalized_body_sha256=sha(normalize(a).encode()))


def main() -> None:
    """Validate the complete independent packet without writing any file."""
    root = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json(read(root, 'MANIFEST.json'))
    expected = {ref.path for ref in manifest.files}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if len(expected) != len(manifest.files) or actual != expected | {'MANIFEST.json'}:
        raise ValueError('Independent packet closure mismatch')
    for ref in manifest.files:
        data = read(root, ref.path)
        if sha(data) != ref.sha256 or len(data) != ref.size_bytes:
            raise ValueError('Independent packet hash mismatch')
    audit = Audit.model_validate_json(read(root, 'AUDIT.json'))
    for key, value in checks(root).items():
        if getattr(audit, key) != value:
            raise ValueError('Audit recount mismatch')
    for name, model in [('AUDIT.schema.json', Audit), ('MANIFEST.schema.json', Manifest)]:
        if json.loads(read(root, name)) != model.model_json_schema():
            raise ValueError('Schema differs from strict model')
    files = {p.relative_to(root / 'received').as_posix()
             for p in (root / 'received').rglob('*') if p.is_file()}
    if files != {ref.path for ref in audit.received_files}:
        raise ValueError('Received inventory mismatch')
    for ref in audit.received_files:
        data = read(root / 'received', ref.path)
        if len(data) != ref.size_bytes or sha(data) != ref.sha256:
            raise ValueError('Received identity mismatch')
    sys.stdout.write(json.dumps({'status': 'PASS', **checks(root)}) + '\n')


if __name__ == '__main__':
    main()
