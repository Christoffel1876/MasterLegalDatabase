"""Verify this closed preparation; optional canonical preflight never opens public HTTP."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path
from typing import Any

import jsonschema
from preparation_models import Design, Manifest, Ref, Validation

BASE = Path(__file__).resolve().parent


def ordinary(path: Path) -> Path:
    """Reject symlinks, including ancestor aliases, and nonordinary files."""
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Unsafe file: ' + str(path))
    return path


def checked(root: Path, ref: Ref) -> bytes:
    """Return only the exact bytes checked against the supplied identity."""
    data = ordinary(root / ref.path).read_bytes()
    if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError('Evidence mismatch: ' + ref.path)
    return data


def no_external_refs(value: Any) -> None:
    """Schemas are declarative local data; no remote resolution is allowed."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'$ref', '$dynamicRef', '$recursiveRef'} and not child.startswith('#'):
                raise ValueError('External schema reference')
            no_external_refs(child)
    elif isinstance(value, list):
        for child in value:
            no_external_refs(child)


def verify(root: Path | None = None) -> dict[str, Any]:
    """Check every payload before optionally importing staged maintained modules."""
    manifest = Manifest.model_validate_json(ordinary(BASE / 'FINAL_MANIFEST.json').read_bytes())
    actual = set()
    for path in BASE.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in closed package')
        if path.is_file() and path.relative_to(BASE).as_posix() != 'FINAL_MANIFEST.json':
            actual.add(path.relative_to(BASE).as_posix())
    if actual != {item.path for item in manifest.files}:
        raise ValueError('Closed package inventory mismatch')
    for item in manifest.files:
        checked(BASE, item)
    validation = Validation.model_validate_json((BASE / 'VALIDATION.json').read_bytes())
    Design.model_validate_json((BASE / 'DESIGN.json').read_bytes())
    for path in sorted((BASE / 'proposed/config').glob('*.json')):
        if path.name.endswith('.schema.json'):
            continue
        schema = json.loads(path.with_suffix('.schema.json').read_bytes())
        no_external_refs(schema)
        jsonschema.Draft202012Validator(schema).validate(json.loads(path.read_bytes()))
    result = dict(status='closed_preparation_valid', files=len(manifest.files),
                  proposed_files=len(manifest.installation_files), public_requests=0,
                  canonical_preflight='not_requested', legal_currentness='not_verified')
    if root is not None:
        root = root.absolute()
        if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError('Unsafe supplied repository root')
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        def refuse(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError('Network disabled for preparation verification')
        socket.getaddrinfo = refuse
        for name in ('manual_watch_http_v2', 'manual_source_watch_batches'):
            qualified = 'geode.pipeline.' + name
            path = BASE / 'proposed/geode/pipeline' / (name + '.py')
            spec = importlib.util.spec_from_file_location(qualified, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[qualified] = module
            spec.loader.exec_module(module)
        watch = module
        watch.g.transport = refuse
        for batch, relative in watch.SELECTIONS.items():
            plan = watch.load_plan(BASE / 'proposed' / relative, root=root,
                                   catalog_path=BASE / 'proposed' / watch.CATALOG)
            if plan.batch_id != batch:
                raise ValueError('Wrong preflight batch')
        for item in validation.old_springs_inputs:
            checked(root, item)
        result['canonical_preflight'] = 'six_sources_three_batches_passed'
    # Recheck every file so a validation-time mutation cannot receive a clean receipt.
    for item in manifest.files:
        checked(BASE, item)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    sys.stdout.write(json.dumps(verify(args.root), indent=2) + '\n')
