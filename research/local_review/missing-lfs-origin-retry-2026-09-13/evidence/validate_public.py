"""Check public availability evidence without network, imports or private-path access."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent


def safe(path: str) -> Path:
    """Confine evidence to ordinary public files."""
    rel = Path(path)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Unsafe public evidence path')
    current = HERE
    for part in rel.parts:
        current /= part
        if current.is_symlink():
            raise ValueError('Symlink public evidence')
    if not current.is_file():
        raise ValueError('Missing public evidence')
    return current


def load(name: str) -> dict:
    """Load one exact public JSON artifact."""
    return json.loads(safe(name).read_bytes())


def main() -> None:
    """Replay exact byte, schema, object-error and zero-recovery bindings."""
    manifest = load('FINAL_MANIFEST.json')
    jsonschema.Draft202012Validator(load('FINAL_MANIFEST.schema.json')).validate(manifest)
    expected = {x['path'] for x in manifest['files']} | {'FINAL_MANIFEST.json'}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    if expected != actual:
        raise ValueError('Public subset inventory is not closed')
    for item in manifest['files']:
        data = safe(item['path']).read_bytes()
        if len(data) != item['size_bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Public payload differs')
    attempt = load('ATTEMPT.json')
    disposition = load('DISPOSITION.json')
    for name, obj in [('ATTEMPT', attempt), ('DISPOSITION', disposition)]:
        jsonschema.Draft202012Validator(load(name + '.schema.json')).validate(obj)
    error = safe(disposition['public_error_output']['path']).read_bytes()
    if hashlib.sha256(error).hexdigest() != disposition['private_error_output_sha256']:
        raise ValueError('Public error does not match the recorded original stream')
    lines = error.decode('utf-8').splitlines()
    if len(lines) != 4 or lines[0] != 'Fetching reference ' + attempt['requested_commit']:
        raise ValueError('Unexpected error output structure')
    objects = {x['oid']: x for x in disposition['objects']}
    if set(objects) != {t['object_sha256'] for t in attempt['targets']}:
        raise ValueError('Requested and reported objects differ')
    for target in attempt['targets']:
        obj = objects[target['object_sha256']]
        if obj['path'] != target['path'] or obj['expected_size_bytes'] != target['object_size_bytes']:
            raise ValueError('Object identity association changed')
        line = lines[obj['source_output_line'] - 1]
        expected_line = (f'[{obj["oid"]}] Object does not exist on the server: '
                         '[404] Object does not exist on the server')
        if line != expected_line:
            raise ValueError('Object-error line does not support disposition')
    if (attempt['process_exit_code'] != 2 or attempt['timed_out'] or
            attempt['retained_storage_file_count'] or attempt['retained_storage_bytes'] or
            not attempt['canonical_pointer_bytes_unchanged'] or
            not attempt['repository_config_bytes_unchanged']):
        raise ValueError('Execution result conflicts with final disposition')
    sys.stdout.write(f'PASS: {len(manifest["files"])} closed public payloads; '
                     'two exact client-reported object404s; zero recovered bytes.\n')


if __name__ == '__main__':
    main()
