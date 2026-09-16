"""Verify this portable frozen package without importing repository code or applying intake."""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path

import jsonschema

sys.dont_write_bytecode = True
BASE = Path(__file__).absolute().parent
sys.path.insert(0, str(BASE))
from package_models import Asset, Package, Validation


def verify() -> dict:
    """Validate exact membership, schemas, evidence bindings and preserved preparation."""
    if any(p.is_symlink() for p in (BASE, *BASE.parents)):
        raise ValueError("Symlink package path")
    package = Package.model_validate_json((BASE / "FINAL_MANIFEST.json").read_bytes())
    if package.excluded_prefixes != ["execution/"] or package.excluded_files != [
        "FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"
    ]:
        raise ValueError("Unexpected exclusions")
    names = [item.path for item in package.files]
    if names != sorted(set(names)):
        raise ValueError("Duplicate or unordered package paths")
    actual = set()
    for path in BASE.rglob("*"):
        relative = path.relative_to(BASE).as_posix()
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise ValueError("Nonordinary package member: " + relative)
        if relative.startswith("execution/"):
            continue
        if path.is_file() and relative not in package.excluded_files:
            actual.add(relative)
    if set(names) != actual:
        raise ValueError("Package membership changed")
    indexed = {item.path: item for item in package.files}
    for item in package.files:
        relative = Path(item.path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Package path escape")
        path = BASE / relative
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != item.sha256 or path.stat().st_size != item.size_bytes:
            raise ValueError("Package hash/size mismatch: " + item.path)
    validation = Validation.model_validate_json((BASE / "VALIDATION.json").read_bytes())
    for name, model in [("FINAL_MANIFEST", Package), ("VALIDATION", Validation)]:
        data = json.loads((BASE / (name + ".json")).read_bytes())
        schema = json.loads((BASE / (name + ".schema.json")).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError("Schema mismatch: " + name)
        jsonschema.Draft202012Validator(schema).validate(data)
    references = [validation.implementation, validation.tests, validation.coverage,
                  validation.approved_preparation_manifest]
    for command in [validation.focused_tests, validation.actual_dry_run]:
        references.extend([command.stdout, command.stderr])
    for item in references:
        if indexed.get(item.path) != item:
            raise ValueError("Validation evidence binding mismatch")
    coverage = json.loads((BASE / validation.coverage.path).read_bytes())
    if coverage["totals"]["percent_covered"] != validation.branch_inclusive_coverage_percent:
        raise ValueError("Coverage summary mismatch")
    test_stdout = (BASE / validation.focused_tests.stdout.path).read_text()
    if "56 passed, 5 warnings" not in test_stdout:
        raise ValueError("Focused test outcome mismatch")
    dry_text = (BASE / validation.actual_dry_run.stderr.path).read_text()
    start, end = dry_text.index("{"), dry_text.rindex("}") + 1
    result = json.loads(dry_text[start:end])
    if result != {"status": "dry_run_ready", "sources": 2, "repository_writes": 0,
                  "actual_repository_received_at": None, "legal_currentness": "not_verified"}:
        raise ValueError("Actual read-only result mismatch")
    prep_root = "evidence/preparation/"
    prep = json.loads((BASE / prep_root / "PREPARATION.json").read_bytes())
    if [s["proposed_record_id"] for s in prep["sources"]] != validation.expected_source_ids:
        raise ValueError("Approved source IDs changed")
    original_manifest = json.loads((BASE / validation.approved_preparation_manifest.path).read_bytes())
    if validation.approved_preparation_manifest.sha256 != (
        "5b0e8cf0cd835d793c99ae1c32f50d287e9760ae854fa8fa69e911c1b6b21142"
    ):
        raise ValueError("Unapproved preparation manifest")
    for original in original_manifest["files"]:
        expected = Asset(**{**original, "path": prep_root + original["path"]})
        if indexed.get(expected.path) != expected:
            raise ValueError("Frozen preparation copy differs")
    baseline_map = {b["repository_path"]: b["preserved"] for b in prep["baseline"]}
    for baseline in validation.baselines:
        original = baseline_map[baseline.before.path]
        expected = Asset(**{**original, "path": prep_root + original["path"]})
        if indexed.get(expected.path) != expected or (
            baseline.before.sha256 != expected.sha256
            or baseline.before.size_bytes != expected.size_bytes
        ):
            raise ValueError("Actual baseline/preparation mismatch")
    return {"status": "verified_prepared_not_applied", "files": len(names),
            "focused_tests": validation.tests_passed,
            "branch_inclusive_coverage": validation.branch_inclusive_coverage_percent,
            "actual_apply_claimed": False, "legal_currentness": "not_verified"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("%s", json.dumps(verify(), indent=2))
