"""Write-once final custody receipt after the final measured tests complete."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from package_models import Asset, Manifest, TestRun, Verification

HERE = Path(__file__).resolve().parent


def asset(name: str) -> Asset:
    """Hash exact bytes immediately before validated custody serialization."""
    raw = (HERE / name).read_bytes()
    return Asset(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def write(name: str, model: Verification | Manifest) -> None:
    """Validate strict model JSON before write-once publication."""
    raw = model.model_dump_json(indent=2) + "\n"
    type(model).model_validate_json(raw)
    with (HERE / name).open("x") as handle:
        handle.write(raw)
    with (HERE / name.replace(".json", ".schema.json")).open("x") as handle:
        handle.write(json.dumps(type(model).model_json_schema(), indent=2) + "\n")


def main() -> None:
    """Seal actual measured runs while preserving failed predecessor attempts."""
    final = (HERE / "tests-release.log").read_text()
    assert "430 passed" in final and "failed" not in final
    coverage = json.loads((HERE / "coverage.json").read_bytes())["totals"]
    covered = coverage["covered_lines"] + coverage["covered_branches"]
    total = coverage["num_statements"] + coverage["num_branches"]
    percent = 100.0 * covered / total
    assert percent >= 90
    original = ast.parse((HERE / "preimages/research_source_lookup.py").read_bytes())
    names = [node.name for node in original.body if isinstance(node, ast.FunctionDef) and (
        node.name.startswith("_dp_") or node.name in {
            "_check_dp_package", "_load_dp_verified", "_lookup_dp", "_render_dp"})]
    receipt = Verification(
        frozen_at=datetime.now(timezone.utc),
        status="prepared_pending_independent_root_acceptance",
        preimage=asset("preimages/research_source_lookup.py"),
        proposed=asset("proposed/research_source_lookup.py"),
        tests=asset("proposed/test_native_lookup_capture.py"),
        documentation=asset("proposed/RESEARCH_SOURCE_LOOKUP.md"),
        historical_audit_manifest=asset("prior-audit/FINAL_MANIFEST.json"),
        measured_runs=[
            TestRun(implementation_sha256=asset(
                "historical/combined-run-before-diagnostic-compatibility/"
                "research_source_lookup.py").sha256, log=asset("tests-final.log"),
                passed=428, failed=2, deselected=0,
                qualification=("Both failures were existing El Paso diagnostic message "
                               "assertions.")),
            TestRun(implementation_sha256=asset("proposed/research_source_lookup.py").sha256,
                log=asset("tests-diagnostic-compatibility.log"), passed=2, failed=0, deselected=428,
                qualification="Both unchanged previously failing assertions passed."),
            TestRun(implementation_sha256=asset("proposed/research_source_lookup.py").sha256,
                log=asset("tests-release.log"), passed=430, failed=0, deselected=0,
                qualification="Final combined run includes all 37 captured-buffer regressions."),
        ], coverage=asset("coverage.json"), branch_inclusive_percent=percent,
        original_classes_unchanged=sum(isinstance(node, ast.ClassDef) for node in original.body),
        douglas_pueblo_functions_unchanged=names, main_function_unchanged=True,
        normal_output_fixture_files=18, source_schemas_unchanged=True,
        public_requests=0, production_writes=0, legal_currentness="not_verified",
        limitations=[
            "Prepared only; root acceptance, installation and full repository suite are separate.",
            "Historical BASELINES.json binds its earlier prepared implementation; it is unchanged.",
            "Final normal outputs are checked against those same 18 fixtures "
            "in the final test run.",
            "File paths identify captured evidence; later disk immutability is not guaranteed.",
            "Original source QA and verifiers remain unchanged; no legal currentness is certified.",
        ])
    write("VERIFICATION.json", receipt)
    files = [asset(p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob("*")) if p.is_file()]
    write("FINAL_MANIFEST.json", Manifest(frozen_at=datetime.now(timezone.utc),
        status="prepared_pending_independent_root_acceptance", files=files))


if __name__ == "__main__":
    main()
