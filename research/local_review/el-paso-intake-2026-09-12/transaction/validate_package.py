"""Validate the frozen preparation package without applying its transaction."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import jsonschema

sys.dont_write_bytecode = True
BASE = Path(__file__).absolute().parent
sys.path.insert(0, str(BASE))
from package_models import Package, Validation


def verify() -> dict:
    """Check closed membership, ordinary paths, exact hashes and typed validation evidence."""
    if any(p.is_symlink() for p in (BASE, *BASE.parents)):
        raise ValueError("Symlink package path")
    package = Package.model_validate_json((BASE / "FINAL_MANIFEST.json").read_bytes())
    names = [item.path for item in package.files]
    if names != sorted(set(names)):
        raise ValueError("Unordered or duplicate package paths")
    excluded = set(package.excluded_files)
    actual = set()
    for path in BASE.rglob("*"):
        relative = path.relative_to(BASE).as_posix()
        if any(relative.startswith(prefix) for prefix in package.excluded_prefixes):
            continue
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise ValueError("Nonordinary package member: " + relative)
        if path.is_file() and relative not in excluded:
            actual.add(relative)
    if actual != set(names):
        raise ValueError("Package membership changed")
    for item in package.files:
        path = Path(item.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Package member escapes root")
        raw = (BASE / path).read_bytes()
        if len(raw) != item.size_bytes or hashlib.sha256(raw).hexdigest() != item.sha256:
            raise ValueError("Package hash mismatch: " + item.path)
    validation = Validation.model_validate_json((BASE / "VALIDATION.json").read_bytes())
    for name, model in [("FINAL_MANIFEST", Package), ("VALIDATION", Validation)]:
        data = json.loads((BASE / (name + ".json")).read_bytes())
        schema = json.loads((BASE / (name + ".schema.json")).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError("Schema mismatch: " + name)
        jsonschema.Draft202012Validator(schema).validate(data)
    indexed = {item.path: item for item in package.files}
    for item in [validation.implementation, validation.tests, validation.fixture_test_log,
                 validation.combined_coverage, validation.actual_dry_run.stdout,
                 validation.actual_dry_run.stderr]:
        if indexed.get(item.path) != item:
            raise ValueError("Validation/package evidence binding mismatch")
    return {"status": "verified_prepared_not_applied", "files": len(names),
            "fixture_tests": 30, "actual_apply_claimed": False,
            "legal_currentness": "not_verified"}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(), indent=2) + "\n")
