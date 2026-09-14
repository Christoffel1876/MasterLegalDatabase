"""Run four inventory preservation cases with explicit in-memory draft path substitutions."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "MasterLegalDatabase"


def main() -> int:
    """Read production evidence while directing the selected plan and snapshot to handoff copies."""
    sys.path.insert(0, str(ROOT))
    import geode.pipeline

    spec = importlib.util.spec_from_file_location(
        "geode.pipeline.manual_review_inventory", HERE / "proposed/manual_review_inventory.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    geode.pipeline.manual_review_inventory = module
    prior_safe = module.safe_path
    module.safe_path = lambda root, path: (
        HERE / "proposed/join-plan.json"
        if root == ROOT and path == module.PLAN.as_posix() else prior_safe(root, path))
    substitutions = {ROOT / module.PLAN: HERE / "proposed/join-plan.json"}
    before = Path("_SNAPSHOTS/BEFORE_EL_PASO_EHS_2026-09-13")
    for name in ["join-plan.json", "inventory.json", "inventory.schema.json", "README.md"]:
        substitutions[ROOT / module.PACKAGE / before / name] = (
            HERE / "proposed/inventory" / before / name)
    read = Path.read_bytes
    Path.read_bytes = lambda self: read(substitutions.get(self, self))
    try:
        source = (HERE / "proposed/test_manual_review_inventory.py").read_text()
        source = source.replace("Path(__file__).resolve().parents[1]", repr(str(ROOT)))
        source = source.replace("root = " + repr(str(ROOT)), "root = Path(" + repr(str(ROOT)) + ")")
        with tempfile.TemporaryDirectory(prefix="geode-ehs-inventory-cases-") as folder:
            path = Path(folder) / "test_inventory_prepared.py"
            path.write_text(source)
            return pytest.main([str(path), "-q", "-p", "no:cacheprovider", "-k",
                "accepted_equity_review or planning_scan_join or springs_and_later or "
                "english_ehs_join"])
    finally:
        Path.read_bytes = read


if __name__ == "__main__":
    raise SystemExit(main())
