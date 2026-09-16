"""Read-only public subset and final review verification; never execute copied runners."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

import jsonschema

from models import Inventory, Receipt

EXCLUDED_SHA = '24554bb0b1dd44a41e6dcb7db72e17e9f4a739a6b7d5ccd9fd59a4edd12aa411'
EXCLUDED_PATH = 'received-preparation/preimages/geode/schemas/models 2.py'
BASE_MANIFEST = '3d5aeb6c957ba6b9a7a9e1521814a716f9a7005110bb80a313fc046f94f7d6c3'


def read(root: Path, name: str) -> bytes:
    """Read only ordinary canonical relative paths beneath the declared packet."""
    path = PurePosixPath(name)
    if path.is_absolute() or '\\' in name or any(p in {'', '.', '..'} for p in name.split('/')):
        raise ValueError('Unsafe public path')
    full = root.joinpath(*path.parts)
    if any(p.is_symlink() for p in [full, *full.parents]) or not full.is_file():
        raise ValueError('Nonordinary public input')
    return full.read_bytes()


def digest(data: bytes) -> str:
    """Hash exact bytes without interpreting excluded content."""
    return hashlib.sha256(data).hexdigest()


def validate(root: Path) -> dict[str, object]:
    """Check all public bytes, the disclosed omission and the latest typed verdict."""
    manifest = Inventory.model_validate_json(read(root, 'FINAL_MANIFEST.json'))
    paths = [a.path for a in manifest.files]
    actual = set()
    for p in root.rglob('*'):
        if p.is_symlink():
            raise ValueError('Symlink in public packet')
        if p.is_file() and p != root / 'FINAL_MANIFEST.json':
            actual.add(p.relative_to(root).as_posix())
    if len(paths) != len(set(paths)) or actual != set(paths):
        raise ValueError('Public closure differs')
    for a in manifest.files:
        raw = read(root, a.path)
        if digest(raw) == EXCLUDED_SHA:
            raise ValueError('Excluded user content is present under a public filename')
        if digest(raw) != a.sha256 or len(raw) != a.size_bytes:
            raise ValueError('Public payload differs')
    receipt = Receipt.model_validate_json(read(root, 'REVIEW.json'))
    schema = json.loads(read(root, 'REVIEW.schema.json'))
    if schema != Receipt.model_json_schema():
        raise ValueError('Public receipt schema differs')
    jsonschema.validate(json.loads(read(root, 'REVIEW.json')), schema)
    excluded = receipt.historical.excluded_original_members[0]
    if (excluded.path != EXCLUDED_PATH or excluded.sha256 != EXCLUDED_SHA or
            excluded.size_bytes != 36560):
        raise ValueError('Wrong historical exclusion')
    original = read(root, 'historical-audit/FINAL_MANIFEST.json')
    if digest(original) != BASE_MANIFEST:
        raise ValueError('Historical original manifest differs')
    old = json.loads(original)
    expected = {a['path'] for a in old['files']} - {EXCLUDED_PATH}
    got = {p.relative_to(root / 'historical-audit').as_posix()
           for p in (root / 'historical-audit').rglob('*')
           if p.is_file() and p != root / 'historical-audit/FINAL_MANIFEST.json'}
    if expected != got:
        raise ValueError('Historical subset differs from the one declared omission')
    for a in old['files']:
        if a['path'] == EXCLUDED_PATH:
            continue
        raw = read(root / 'historical-audit', a['path'])
        if digest(raw) != a['sha256'] or len(raw) != a['size_bytes']:
            raise ValueError('Retained historical evidence changed')
    for a in [receipt.corrected_runner, receipt.corrected_config, *receipt.evidence]:
        raw = read(root, a.path)
        if digest(raw) != a.sha256 or len(raw) != a.size_bytes:
            raise ValueError('Corrected evidence differs')
    plan = json.loads(read(root, receipt.corrected_config.path))
    if len(plan['immutable_inputs']) != 87:
        raise ValueError('Wrong final pin count')
    if any('models 2.py' in a['path'] for a in plan['immutable_inputs']):
        raise ValueError('Excluded file remains an operational dependency')
    refs = {a['path']: (a['sha256'], a['size_bytes']) for a in plan['immutable_inputs']}
    checked = {a.path: (a.sha256, a.size_bytes) for a in receipt.pin_checks}
    if refs != checked or len(checked) != 87:
        raise ValueError('Final tracking receipt does not match selected dependencies')
    old_plan = json.loads(read(root, 'historical-audit/received-final/config/'
                              'manual_source_watch_ci.json'))
    old_plan['immutable_inputs'] = [a for a in old_plan['immutable_inputs']
                                   if a['path'] != 'geode/schemas/models 2.py']
    if old_plan != plan:
        raise ValueError('Final source selection or caps differ from the reviewed scope')
    summary = json.loads(read(root, 'actual-readiness/summary.json'))
    jsonschema.validate(summary, json.loads(read(root, 'actual-readiness/summary.schema.json')))
    if (summary['status'] != 'ready' or summary['execution_requested'] or
            summary['legal_currentness'] != 'not_verified' or len(summary['pairs']) != 4):
        raise ValueError('Actual readiness claims differ')
    process_paths = sorted((root / 'actual-readiness').glob('*.process.json'))
    if len(process_paths) != 4:
        raise ValueError('Wrong actual readiness process count')
    process_schema = json.loads(read(root, 'actual-readiness/process-receipt.schema.json'))
    for path in process_paths:
        process = json.loads(read(root, path.relative_to(root).as_posix()))
        jsonschema.validate(process, process_schema)
        if process['exit_code'] != 0 or process['retried']:
            raise ValueError('Readiness process did not complete once')
    return {'status': 'pass', 'payloads': len(paths), 'final_pins': 87,
            'historical_exclusions': 1, 'public_source_requests': 0}


def main() -> None:
    """Validate a portable public packet without source access or installation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    arguments = parser.parse_args()
    sys.stdout.write(json.dumps(validate(arguments.root)) + '\n')


if __name__ == '__main__':
    main()
