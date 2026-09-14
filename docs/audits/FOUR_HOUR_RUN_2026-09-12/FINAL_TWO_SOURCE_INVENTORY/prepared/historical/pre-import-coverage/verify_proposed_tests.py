"""Test prepared inventory code against retained production inputs without installing it."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "MasterLegalDatabase"


def main() -> int:
    """Redirect only exact pending inventory paths while all original evidence stays read-only."""
    sys.path.insert(0, str(ROOT))
    import geode.pipeline

    spec = importlib.util.spec_from_file_location(
        "geode.pipeline.manual_review_inventory", HERE / "proposed/manual_review_inventory.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    geode.pipeline.manual_review_inventory = module
    old_safe = module.safe_path
    module.safe_path = lambda root, relative: (
        HERE / "proposed/join-plan.json" if root == ROOT and relative == module.PLAN.as_posix()
        else old_safe(root, relative))
    substitutions = {ROOT / module.PLAN: HERE / "proposed/join-plan.json"}
    for name in ["inventory.json", "inventory.schema.json", "README.md"]:
        substitutions[ROOT / module.PACKAGE / name] = HERE / "proposed/inventory" / name
    snapshot = Path("_SNAPSHOTS/BEFORE_FINAL_TWO_2026-09-13")
    for name in ["join-plan.json", "inventory.json", "inventory.schema.json", "README.md"]:
        substitutions[ROOT / module.PACKAGE / snapshot / name] = (
            HERE / "proposed/inventory" / snapshot / name)
    read = Path.read_bytes
    Path.read_bytes = lambda self: read(substitutions.get(self, self))
    try:
        source = (HERE / "proposed/test_manual_review_inventory.py").read_text()
        source = source.replace(
            "Path(__file__).resolve().parents[1]", "Path(" + repr(str(ROOT)) + ")")
        with tempfile.TemporaryDirectory(prefix="geode-final-two-inventory-tests-") as folder:
            test = Path(folder) / "test_inventory_prepared.py"
            test.write_text(source)
            return pytest.main([str(test), "-q", "-p", "no:cacheprovider",
                                "--cov=geode.pipeline.manual_review_inventory", "--cov-branch",
                                "--cov-report=json:" + str(HERE / "coverage.json")])
    finally:
        Path.read_bytes = read


if __name__ == "__main__":
    raise SystemExit(main())
