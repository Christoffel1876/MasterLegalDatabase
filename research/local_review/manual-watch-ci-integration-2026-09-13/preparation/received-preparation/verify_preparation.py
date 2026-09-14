"""Read-only closed custody/schema checks; never run HTTP, tests or historical builders."""
from __future__ import annotations

import argparse
import hashlib
import types
import json
import sys
from pathlib import Path

import jsonschema

from models import Manifest, Preparation


def verify(root: Path, repository: Path | None = None) -> dict:
    """Verify captured preparation buffers and optional existing immutable dependencies."""
    root = root.resolve()
    manifest_bytes = (root / 'FINAL_MANIFEST.json').read_bytes()
    manifest = Manifest.model_validate_json(manifest_bytes)
    names = [r.path for r in manifest.files]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate payload')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlinked payload')
        if path.is_file() and path != root / 'FINAL_MANIFEST.json':
            actual.add(path.relative_to(root).as_posix())
    if actual != set(names):
        raise ValueError('Missing or unexpected payload')
    captured = {}
    for ref in manifest.files:
        rel = Path(ref.path)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Unsafe payload path')
        data = (root / rel).read_bytes()
        if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
            raise ValueError('Payload differs: ' + ref.path)
        captured[ref.path] = data
    for file in ['PREPARATION', 'FINAL_MANIFEST']:
        data = manifest_bytes if file == 'FINAL_MANIFEST' else captured[file + '.json']
        schema = json.loads(captured[file + '.schema.json'])
        jsonschema.Draft202012Validator(schema).validate(json.loads(data))
    prep = Preparation.model_validate_json(captured['PREPARATION.json'])
    proposed = {k for k in captured if k.startswith('proposed/')}
    if proposed != {r.path for r in prep.install_files}:
        raise ValueError('Install map differs')
    for ref in prep.install_files:
        data = captured[ref.path]
        if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
            raise ValueError('Install identity differs')
    runner = root / 'proposed/scripts/manual_source_watch_ci.py'
    module = types.ModuleType('verified_ci_models')
    module.__file__ = str(runner)
    sys.modules[module.__name__] = module
    code = compile(captured['proposed/scripts/manual_source_watch_ci.py'], str(runner), 'exec')
    exec(code, module.__dict__)
    plan_data = captured['proposed/config/manual_source_watch_ci.json']
    if hashlib.sha256(plan_data).hexdigest() != module.CONFIG_SHA:
        raise ValueError('Runner plan identity differs')
    plan = module.Plan.model_validate_json(plan_data)
    if len(plan.immutable_inputs) != 88 or len(plan.pairs) != 4:
        raise ValueError('Scope differs')
    exports = [('manual_source_watch_ci.schema.json', module.Plan),
               ('manual_source_watch_ci-summary.schema.json', module.Summary),
               ('manual_source_watch_ci-process.schema.json', module.ProcessReceipt),
               ('manual_source_watch_ci-progress.schema.json', module.ProgressSnapshot)]
    for name, model in exports:
        if json.loads(captured['proposed/config/' + name]) != model.model_json_schema():
            raise ValueError('Published schema differs')
    run_prefix = 'evidence/real-offline-run/'
    for name, data in captured.items():
        if name.startswith(run_prefix) and name.endswith('.process.json'):
            receipt = module.ProcessReceipt.model_validate_json(data)
            for ref in [receipt.stdout, receipt.stderr]:
                output = captured[run_prefix + ref.path]
                if len(output) != ref.size_bytes or hashlib.sha256(output).hexdigest() != ref.sha256:
                    raise ValueError('Process output identity differs')
        if name.startswith(run_prefix) and name.endswith('/snapshot.json'):
            receipt = module.ProgressSnapshot.model_validate_json(data)
            for ref in receipt.files:
                output = captured[run_prefix + ref.path]
                if len(output) != ref.size_bytes or hashlib.sha256(output).hexdigest() != ref.sha256:
                    raise ValueError('Progress preimage differs')
    module.Summary.model_validate_json(captured[run_prefix + 'summary.json'])
    if repository is not None:
        for ref in plan.immutable_inputs:
            module.check_ref(repository.absolute(), ref)
    return {'status': 'PASS', 'payloads': len(names), 'sources': 8, 'pairs': 4,
            'prepared_only': True, 'public_source_requests': 0,
            'repository_pins_checked': repository is not None}


def main() -> int:
    """Check only retained files and explicitly requested local repository pins."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path)
    args = parser.parse_args()
    sys.stdout.write(json.dumps(verify(Path(__file__).parent, args.repository_root), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
