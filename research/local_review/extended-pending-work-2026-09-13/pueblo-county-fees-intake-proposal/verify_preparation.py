"""Read-only closed preparation checks; no apply path and no public source access."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema


def ordinary(root: Path, name: str) -> Path:
    """Require an ordinary confined file and ordinary ancestors."""
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name:
        raise ValueError('unsafe relative member')
    path = root / relative
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('nonordinary member')
    return path


def read_ref(root: Path, ref: dict) -> bytes:
    """Validate and return the consumed bytes."""
    raw = ordinary(root, ref['path']).read_bytes()
    if (len(raw) != ref['size_bytes'] or
            hashlib.sha256(raw).hexdigest() != ref['sha256']):
        raise ValueError('member changed: ' + ref['path'])
    return raw


def schema_check(root: Path, name: str) -> dict:
    """Validate a copied strict schema against its record."""
    raw = json.loads(ordinary(root, name + '.json').read_bytes())
    schema = json.loads(ordinary(root, name + '.schema.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(raw)
    return raw


def members(root: Path, ignore_execution: bool = False) -> set[str]:
    """Reject aliases and special files while enumerating payloads."""
    result = set()
    for path in root.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('nonordinary payload')
        name = path.relative_to(root).as_posix()
        if path.is_file() and not (ignore_execution and name.startswith('execution/')):
            result.add(name)
    return result


def closed(root: Path, manifest: dict, extra: set[str]) -> None:
    """Verify every listed payload and exact closed file membership."""
    names = [r['path'] for r in manifest['files']]
    if len(names) != len(set(names)) or members(root) != set(names) | extra:
        raise ValueError('closed copied packet differs')
    for ref in manifest['files']:
        read_ref(root, ref)


def verify(root: Path, expected: str, repository: Path | None = None) -> dict:
    """Verify portable custody; optional current-tree preflight remains read-only."""
    root = root.expanduser().absolute()
    raw = ordinary(root, 'FINAL_MANIFEST.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('external manifest pin differs')
    manifest = schema_check(root, 'FINAL_MANIFEST')
    names = [ref['path'] for ref in manifest['files']]
    if (len(names) != len(set(names)) or
            members(root, True) != set(names) | {'FINAL_MANIFEST.json'}):
        raise ValueError('closed preparation differs')
    for ref in manifest['files']:
        read_ref(root, ref)
    plan = schema_check(root, 'PREPARATION')
    proposed = schema_check(root, 'PROPOSED_RECORD')
    validation = schema_check(root, 'VALIDATION')
    if proposed != plan['template'] or validation['canonical_mutations'] != 0:
        raise ValueError('prepared record/status differs')
    for item in plan['baseline']:
        read_ref(root, item['preserved'])
    for field in ['source_review', 'source_review_schema', 'independent_review',
                  'root_source_qa_approval', 'custody_audit_manifest']:
        read_ref(root, plan[field])
    source = read_ref(root, proposed['source'])
    approval = json.loads(read_ref(root, plan['root_source_qa_approval']))
    if (len(source) != 75214 or hashlib.sha256(source).hexdigest() !=
            '1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084'
            or approval['source']['sha256'] != proposed['source']['sha256']
            or approval['source_qa']['sha256'] != plan['source_review']['sha256']
            or approval['authority_id'] != proposed['authority_id']
            or approval['source_id'] != proposed['record_id']):
        raise ValueError('source/authority/review identity differs')
    if proposed['original_filename'] != Path(proposed['source']['path']).name:
        raise ValueError('incoming basename differs')
    review_root = root / 'inputs/independent-review'
    review_bytes = ordinary(review_root, 'FINAL_MANIFEST.json').read_bytes()
    if hashlib.sha256(review_bytes).hexdigest() != approval['independent_manifest_sha256']:
        raise ValueError('independent review pin differs')
    closed(review_root, json.loads(review_bytes), {'FINAL_MANIFEST.json'})
    custody_root = root / Path(plan['custody_audit_manifest']['path']).parent
    closed(custody_root, json.loads(read_ref(root, plan['custody_audit_manifest'])),
           {'FINAL_MANIFEST.json'})
    execution = root / 'execution'
    allowed = {'LOCK', 'INTENT.json', 'RECEIPT.json'} | {
        'preimages/' + Path(b['repository_path']).name for b in plan['baseline']}
    if execution.exists():
        if not execution.is_dir() or members(execution) - allowed:
            raise ValueError('unknown execution member')
        for item in plan['baseline']:
            saved = execution / 'preimages' / Path(item['repository_path']).name
            if saved.exists() and saved.read_bytes() != read_ref(root, item['preserved']):
                raise ValueError('execution preimage differs')
        for stem in ['INTENT', 'RECEIPT']:
            path = execution / (stem + '.json')
            if path.exists():
                schema = json.loads(ordinary(root, stem + '.schema.json').read_bytes())
                jsonschema.Draft202012Validator(schema).validate(json.loads(path.read_bytes()))
    live = None
    if repository is not None:
        # Closed, externally pinned code is imported only for its read-only entry path.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        spec = importlib.util.spec_from_file_location('prepared_pueblo_intake', root / 'transaction.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        live = module.run(repository, base=root, verify=(execution / 'RECEIPT.json').is_file())
    return {'status': 'PASS', 'payloads': len(names), 'canonical_mutations_by_verifier': 0,
            'public_requests': 0, 'live_readonly_result': live,
            'historical_claims_limit': 'No source acquisition or visual review is rerun.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).absolute().parent)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--repository', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.root, args.manifest_sha256, args.repository)
    except (ValueError, OSError) as error:
        sys.stderr.write(str(error) + '\n')
        raise SystemExit(1)
    sys.stdout.write(json.dumps(result, indent=2) + '\n')
