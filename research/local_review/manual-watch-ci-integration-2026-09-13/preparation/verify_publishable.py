"""Validate only this publishable tree; never invoke historical verifiers or public HTTP."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import types
from pathlib import Path

import jsonschema

from models import Manifest, PublicReceipt

BAD_SHA = '24554bb0b1dd44a41e6dcb7db72e17e9f4a739a6b7d5ccd9fd59a4edd12aa411'
OMITTED = 'preimages/geode/schemas/models 2.py'


def digest(data: bytes) -> str:
    """Compute an exact byte identity."""
    return hashlib.sha256(data).hexdigest()


def verify(root: Path, repository: Path | None = None) -> dict[str, object]:
    """Check current closure, one documented omission, schemas and the exact operational delta."""
    manifest_bytes = (root / 'FINAL_MANIFEST.json').read_bytes()
    manifest = Manifest.model_validate_json(manifest_bytes)
    data = {}
    for ref in manifest.files:
        rel = Path(ref.path)
        if rel.is_absolute() or '..' in rel.parts or ref.path in data:
            raise ValueError('Unsafe/duplicate payload')
        path = root / rel
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError('Symlinked payload')
        body = path.read_bytes()
        if digest(body) != ref.sha256 or len(body) != ref.size_bytes or digest(body) == BAD_SHA:
            raise ValueError('Changed or forbidden user-content payload')
        data[ref.path] = body
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlinked public tree')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != set(data) | {'FINAL_MANIFEST.json'}:
        raise ValueError('Public tree is not closed')
    for name, body in [('FINAL_MANIFEST', manifest_bytes),
                       ('PUBLIC_RECEIPT', data['PUBLIC_RECEIPT.json'])]:
        schema = json.loads(data[name + '.schema.json'])
        jsonschema.Draft202012Validator(schema).validate(json.loads(body))
    receipt = PublicReceipt.model_validate_json(data['PUBLIC_RECEIPT.json'])
    prior_bytes = data[receipt.predecessor_manifest.path]
    if digest(prior_bytes) != receipt.predecessor_manifest.sha256:
        raise ValueError('Wrong historical manifest')
    prior = json.loads(prior_bytes)
    refs = {r['path']: r for r in prior['files']}
    if len(refs) != 154 or set(o.path for o in receipt.omitted) != {OMITTED}:
        raise ValueError('Wrong historical omission scope')
    omission = receipt.omitted[0]
    if refs[OMITTED] != {
            'path': omission.path, 'sha256': omission.sha256, 'size_bytes': omission.size_bytes}:
        raise ValueError('Omitted member identity differs')
    prefix = 'received-preparation/'
    expected = {prefix + name for name in refs if name != OMITTED}
    expected.add(prefix + 'FINAL_MANIFEST.json')
    if {name for name in data if name.startswith(prefix)} != expected:
        raise ValueError('Historical public subset membership differs')
    for name, ref in refs.items():
        if name == OMITTED:
            continue
        body = data[prefix + name]
        if len(body) != ref['size_bytes'] or digest(body) != ref['sha256']:
            raise ValueError('Historical retained member changed')
    current_files = {r.path for r in receipt.install_files}
    if {name for name in data if name.startswith('proposed/')} != current_files:
        raise ValueError('Install map differs')
    for ref in receipt.install_files:
        if digest(data[ref.path]) != ref.sha256 or len(data[ref.path]) != ref.size_bytes:
            raise ValueError('Install file identity differs')
    plan_name = 'proposed/config/manual_source_watch_ci.json'
    old_plan = json.loads(data[prefix + plan_name])
    plan = json.loads(data[plan_name])
    expected_plan = dict(old_plan)
    expected_plan['immutable_inputs'] = [r for r in old_plan['immutable_inputs']
                                        if r['path'] != 'geode/schemas/models 2.py']
    if plan != expected_plan or len(plan['immutable_inputs']) != 87:
        raise ValueError('Plan differs beyond exact unrelated-pin removal')
    runner_name = 'proposed/scripts/manual_source_watch_ci.py'
    old_sha, new_sha = digest(data[prefix + plan_name]), digest(data[plan_name])
    expected_runner = data[prefix + runner_name].replace(old_sha.encode(), new_sha.encode())
    if data[runner_name] != expected_runner:
        raise ValueError('Runner differs beyond the exact config digest')
    module = types.ModuleType('public_ci_verified_models')
    module.__file__ = str(root / runner_name)
    sys.modules[module.__name__] = module
    exec(compile(data[runner_name], module.__file__, 'exec'), module.__dict__)
    parsed = module.Plan.model_validate_json(data[plan_name])
    exports = [('manual_source_watch_ci.schema.json', module.Plan),
               ('manual_source_watch_ci-summary.schema.json', module.Summary),
               ('manual_source_watch_ci-process.schema.json', module.ProcessReceipt),
               ('manual_source_watch_ci-progress.schema.json', module.ProgressSnapshot)]
    for name, model in exports:
        if json.loads(data['proposed/config/' + name]) != model.model_json_schema():
            raise ValueError('Final exported schema differs')
    tracked = json.loads(data['evidence/TRACKED_INPUTS.json'])['inputs']
    if len(tracked) != 87 or any(not r['git_tracked'] for r in tracked):
        raise ValueError('Recorded tracking check differs')
    if [{k: r[k] for k in ('path', 'sha256', 'size_bytes')} for r in tracked] != plan['immutable_inputs']:
        raise ValueError('Tracking identities differ')
    sparse = json.loads(data['evidence/SPARSE_READINESS.json'])
    if (sparse['result_status'] != 'ready' or not sparse['unrelated_models2_absent']
            or sparse['copied_git_tracked_dependency_count'] != 87):
        raise ValueError('Sparse readiness proof differs')
    if repository is not None:
        for ref in parsed.immutable_inputs:
            module.check_ref(repository.absolute(), ref)
    return {'status': 'PASS', 'public_payloads': len(data), 'retained_original_payloads': 153,
            'original_payloads': 154, 'omitted_user_file_contents': 1, 'final_pins': 87,
            'prepared_only': True, 'source_requests': 0,
            'repository_pins_checked': repository is not None}


def main() -> int:
    """Check retained public data and optionally local repository input pins."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path)
    args = parser.parse_args()
    sys.stdout.write(json.dumps(verify(Path(__file__).parent.resolve(), args.repository_root),
                               indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
