"""Preserve final lookup implementation and observed validation without changing sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2] / "MasterLegalDatabase"
AUDIT = ROOT / "docs/audits/FOUR_HOUR_RUN_2026-09-12/GREELEY_CRS_LOOKUPS"
PREP = BASE.parent / "greeley-lookup-extension"
CHANGES = (
    "scripts/research_source_lookup.py", "tests/test_research_source_lookup.py",
    "docs/RESEARCH_SOURCE_LOOKUP.md", "scripts/crs_source_lookup.py",
    "tests/test_crs_source_lookup.py", "docs/CRS_SOURCE_LOOKUP.md",
)
PINS = (
    "2a1e2f3a82214dc1fc85511b4dda13b53ff171bb02aa530a5ed837005ec3a33e",
    "479c678632457079d9698e225fe077bae08878fb7e58d7983e0887d8e666bef2",
    "1dfa9ed4d72ca5b7c24cb661321ac0e9f3adbae1d34b06386ecba74c85e154c7",
    "0dd62f447ec46bd9d8a9a3a205c07f6fc899a6d3befb93c9c487777fc2d55a31",
    "902ae41d069d5681728373328a01fbb92df10ac0318f9c93e93d4010155a3ece",
    "9ed6aebfac3d29b8f4c23e6cc765a34e050a0c80619deba8a68680ad11e11bc3",
)


class Strict(BaseModel):
    """Reject unrecognized validation receipt fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class File(Strict):
    """Pin an ordinary file to its bytes."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Receipt(Strict):
    """Separate observed test success from legal interpretation and coverage limits."""

    recorded_at: AwareDatetime
    status: Literal["passed_scoped_lookups"]
    parent_commit: str
    changed_files: list[File]
    evidence: list[File]
    full_suite_command: list[str]
    full_suite_exit_code: Literal[0]
    full_suite_summary: str
    full_suite_count: int
    full_geode_combined_coverage_percent: float
    focused_greeley_tests: Literal[187]
    focused_greeley_combined_coverage_percent: float
    focused_crs_tests: Literal[81]
    focused_crs_combined_coverage_percent: float
    root_actual_cli_cases: Literal[2]
    root_police_cells: list[str]
    root_pif_adoption_condition_retained: Literal[True]
    source_bytes_unchanged: Literal[True]
    legal_currentness: Literal["not_verified"]
    limitations: list[str]


def digest(data: bytes) -> str:
    """Return the SHA-256 of exact content."""
    return hashlib.sha256(data).hexdigest()


def file_ref(path: Path, base: Path = ROOT) -> File:
    """Reject nonordinary evidence and return a relative file reference."""
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"Nonordinary file: {path}")
    data = path.read_bytes()
    return File(path=path.relative_to(base).as_posix(), sha256=digest(data), size_bytes=len(data))


def write_once(path: Path, data: bytes) -> None:
    """Install a new artifact atomically without overwriting previous artifacts."""
    if path.exists():
        raise ValueError(f"Refusing overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(data)
    temporary.replace(path)


def main() -> None:
    """Require root's actual successful process result and preserve its matching log."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed-exit-code", type=int, required=True)
    args = parser.parse_args()
    if args.observed_exit_code != 0:
        raise ValueError("No successful full-suite process observation")
    changes = [file_ref(ROOT / name) for name in CHANGES]
    if [item.sha256 for item in changes] != list(PINS):
        raise ValueError("Production files changed after focused validation")
    log = (BASE / "pytest.log").read_bytes()
    match = re.search(rb"(\d+ passed, \d+ warnings in [^\r\n]+)", log)
    if match is None or b"FAILED " in log or b"ERROR " in log:
        raise ValueError("No clean final full-suite summary")
    summary = match[1].decode()
    coverage_path = Path("/private/tmp/geode-four-hour-lookups-coverage.json")
    full_coverage = json.loads(coverage_path.read_bytes())["totals"]["percent_covered"]
    manifest = json.loads((PREP / "FINAL_MANIFEST.json").read_bytes())
    for item in manifest["files"]:
        actual = file_ref(PREP / item["path"], PREP)
        if actual.model_dump() != item:
            raise ValueError(f"Frozen Greeley handoff changed: {item['path']}")
    impact = json.loads((BASE / "root-impact-row.json").read_bytes())
    pif = json.loads((BASE / "root-pif-row.json").read_bytes())
    cells = [cell["text"] for cell in impact["rows"][0]["cells"]]
    expected = ["Retail/Restaurant", "1,000 Sq. Ft of Building", "$1,004", "-2.09%", "$983"]
    if impact["status"] != "matched" or len(impact["rows"]) != 1 or cells != expected:
        raise ValueError("Root actual police-row check failed")
    if (pif["status"] != "matched" or len(pif["rows"]) != 1
            or "assuming they are adopted" not in pif["mandatory_qualification"]):
        raise ValueError("Root actual conditional PIF check failed")
    for item in manifest["files"]:
        write_once(AUDIT / "greeley-implementation" / item["path"],
                   (PREP / item["path"]).read_bytes())
    write_once(AUDIT / "greeley-implementation/FINAL_MANIFEST.json",
               (PREP / "FINAL_MANIFEST.json").read_bytes())
    for original, relative in (
        (BASE / "pytest.log", "full-tests.log"), (coverage_path, "full-coverage.json"),
        (BASE / "root-impact-row.json", "root-impact-row.json"),
        (BASE / "root-pif-row.json", "root-pif-row.json"),
        (Path(__file__), "preserve_results.py"),
    ):
        write_once(AUDIT / relative, original.read_bytes())
    write_once(AUDIT / "README.md", (
        "---\ntitle: Greeley and CRS lookup validation\nlegal_currentness: not_verified\n---\n\n"
        "# Verified source lookups\n\n"
        "The fee lookup now preserves the 30-row Greeley impact-fee grid and separate"
        " seven-plus-one-row proposed PIF notice. A separate CRS 2026 command returns"
        " the reviewed passages for sections 1-1-101, 1-1-102 and 1-1-103.\n\n"
        "Every source remains a checked historical snapshot. No fee arithmetic,"
        " applicability or current-law determination is made. The PIF adoption"
        " condition is retained in every result. The superseding Greeley title"
        " correction governs over the preserved withdrawn finding.\n\n"
        "Root ran two actual Greeley CLI queries from /private/tmp. The separate"
        " CRS_LOOKUP audit retains its focused integration checks. Final production"
        " hashes and the completed full-suite process/log are bound in VERIFICATION.json."
        " Overall geode coverage remains below 90%; the changed lookup modules"
        " individually exceed 90% in their focused suites.\n"
    ).encode())
    write_once(AUDIT / "VERIFICATION.schema.json",
               (json.dumps(Receipt.model_json_schema(), indent=2) + "\n").encode())
    evidence = [file_ref(p) for p in sorted(AUDIT.rglob("*")) if p.is_file()]
    record = Receipt(
        recorded_at=datetime.now(timezone.utc), status="passed_scoped_lookups",
        parent_commit="a6fe4888e5c8b5290b64b786307fcffd9bcab13e",
        changed_files=changes, evidence=evidence,
        full_suite_command=["PYTHONDONTWRITEBYTECODE=1",
                            "COVERAGE_FILE=/private/tmp/geode-four-hour-lookups-coverage",
                            "/private/tmp/geode-status-venv/bin/python", "-B", "-m",
                            "pytest", "tests/", "-q", "--cov=geode",
                            "--cov-report=term-missing",
                            "--cov-report=json:/private/tmp/geode-four-hour-lookups-coverage.json"],
        full_suite_exit_code=0, full_suite_summary=summary,
        full_suite_count=int(summary.split()[0]),
        full_geode_combined_coverage_percent=full_coverage,
        focused_greeley_tests=187, focused_greeley_combined_coverage_percent=96.5338,
        focused_crs_tests=81, focused_crs_combined_coverage_percent=99.38,
        root_actual_cli_cases=2, root_police_cells=cells,
        root_pif_adoption_condition_retained=True, source_bytes_unchanged=True,
        legal_currentness="not_verified", limitations=[
            "Counts describe fixed review scope, not legal requirement counts or completeness.",
            "The last Greeley test-only formatting edit had a focused case rerun; the full suite"
            " here covers the final bytes of all changes.",
            "Source acquisition, repository receipt and review times remain distinct.",
            "The 2026 CRS source does not authenticate the missing 2025 original or all 1008 pages.",
            "Native extraction artifacts and unresolved source anomalies remain qualified.",
            "No public publication or corpus promotion occurred through these read-only adapters.",
        ],
    )
    write_once(AUDIT / "VERIFICATION.json", record.model_dump_json(indent=2).encode() + b"\n")
    print(record.full_suite_summary)
    print(file_ref(AUDIT / "VERIFICATION.json").model_dump_json())


if __name__ == "__main__":
    main()
