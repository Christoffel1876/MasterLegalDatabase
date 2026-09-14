"""Verify the immutable installation receipt without running watchers or historical tools."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

import jsonschema

from models import Acceptance, Asset, Inventory, ScanEntry

EXCLUDED = '24554bb0b1dd44a41e6dcb7db72e17e9f4a739a6b7d5ccd9fd59a4edd12aa411'
INSTALLATION = '5a9e25492d0fe21f1a2ff44a90d705550cb1eb7b8bd9733ea627fc9257819d5b'


def ordinary(root: Path, name: str) -> Path:
    """Resolve only canonical ordinary relative files under the selected root."""
    rel = PurePosixPath(name)
    if (rel.is_absolute() or '\\' in name or
            any(part in {'', '.', '..'} for part in name.split('/'))):
        raise ValueError('Unsafe relative evidence path')
    path = root.joinpath(*rel.parts)
    if not path.is_file() or any(item.is_symlink() for item in [path, *path.parents]):
        raise ValueError('Nonordinary evidence')
    return path


def checked(root: Path, ref: Asset) -> bytes:
    """Check exact ordinary bytes against the retained identity."""
    data = ordinary(root, ref.path).read_bytes()
    if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError('Evidence identity mismatch')
    return data


def validate(root: Path, repository: Path | None = None) -> dict[str, object]:
    """Replay metadata closure and optionally the installed files and runtime pins."""
    manifest = Inventory.model_validate_json(ordinary(root, 'FINAL_MANIFEST.json').read_bytes())
    refs = {ref.path: ref for ref in manifest.files}
    if len(refs) != len(manifest.files):
        raise ValueError('Duplicate evidence reference')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in audit')
        if path.is_file() and path != root / 'FINAL_MANIFEST.json':
            actual.add(path.relative_to(root).as_posix())
    if actual != set(refs):
        raise ValueError('Audit is not closed')
    for ref in manifest.files:
        checked(root, ref)
        if ref.sha256 == EXCLUDED:
            raise ValueError('Excluded user content copied into audit')
    raw = ordinary(root, 'ACCEPTANCE.json').read_bytes()
    receipt = Acceptance.model_validate_json(raw)
    schema = json.loads(ordinary(root, 'ACCEPTANCE.schema.json').read_bytes())
    if schema != Acceptance.model_json_schema():
        raise ValueError('Acceptance schema differs from strict model')
    jsonschema.validate(json.loads(raw), schema)
    install_raw = checked(root, receipt.installation)
    if hashlib.sha256(install_raw).hexdigest() != INSTALLATION:
        raise ValueError('Wrong root installation receipt')
    install = json.loads(install_raw)
    for stem in ['INSTALLATION', 'INVENTORY']:
        jsonschema.validate(
            json.loads(ordinary(root, 'wrapper-metadata/' + stem + '.json').read_bytes()),
            json.loads(ordinary(root, 'wrapper-metadata/' + stem + '.schema.json').read_bytes()))
    if install['installed_files'] != [ref.model_dump() for ref in receipt.installed_files]:
        raise ValueError('Installation map differs')
    if (install['status'] != 'installed_locally_not_deployed' or install['answer_safe'] or
            install['legal_currentness'] != 'not_verified'):
        raise ValueError('Installation scope changed')
    wrapper_inventory = json.loads(checked(root, receipt.wrapper_inventory))
    if len(wrapper_inventory['files']) != receipt.wrapper_payload_count:
        raise ValueError('Wrapper scope differs')
    scanned = {}
    with ordinary(root, 'SCANNED_PATHS.jsonl').open('rb') as handle:
        for line in handle:
            row = ScanEntry.model_validate_json(line)
            if row.path in scanned or row.excluded_basename_match:
                raise ValueError('Duplicate or excluded scan path')
            if not any(row.path.startswith(prefix + '/')
                       for prefix in receipt.scanned_wrapper_roots):
                raise ValueError('Scan escaped its declared wrapper roots')
            if row.excluded_size_match != (row.size_bytes == 36560):
                raise ValueError('Size screening differs')
            if row.sha256_if_size_matches == EXCLUDED:
                raise ValueError('Excluded bytes in canonical wrapper')
            scanned[row.path] = row
    full_hashes = {}
    with ordinary(root, 'HASHED_WRAPPER_FILES.jsonl').open('rb') as handle:
        for line in handle:
            row = Asset.model_validate_json(line)
            if row.path in full_hashes or row.sha256 == EXCLUDED:
                raise ValueError('Duplicate hash entry or excluded exact contents')
            full_hashes[row.path] = row
    if set(scanned) != set(full_hashes):
        raise ValueError('Full hash scan and path scan differ')
    if (len(scanned) != receipt.scanned_file_count or
            sum(row.size_bytes for row in scanned.values()) != receipt.scanned_byte_sizes_total or
            any(row.size_bytes != full_hashes[path].size_bytes for path, row in scanned.items())):
        raise ValueError('Scan counts or byte identities differ')
    if (receipt.original_user_file.sha256 != EXCLUDED or
            receipt.original_user_file.size_bytes != 36560):
        raise ValueError('Wrong original user-file identity')
    if repository is not None:
        for ref in [*receipt.installed_files, *receipt.immutable_inputs]:
            checked(repository, ref)
        wrapper = repository / receipt.wrapper_path
        for data in wrapper_inventory['files']:
            checked(wrapper, Asset.model_validate(data))
        if (wrapper / 'INVENTORY.json').read_bytes() != checked(root, receipt.wrapper_inventory):
            raise ValueError('Canonical wrapper inventory changed')
    return {'status': 'pass', 'installed_files': 10, 'runtime_inputs': 87,
            'wrapper_payloads': receipt.wrapper_payload_count,
            'publication_scanned_files': len(scanned), 'forbidden_content_matches': 0,
            'current_repository_rechecked': repository is not None,
            'source_requests': 0, 'deployment_verified': False}


def main() -> None:
    """Run portable evidence verification, with optional current local-byte checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--repository-root', type=Path)
    arguments = parser.parse_args()
    sys.stdout.write(json.dumps(validate(arguments.root, arguments.repository_root)) + '\n')


if __name__ == '__main__':
    main()
