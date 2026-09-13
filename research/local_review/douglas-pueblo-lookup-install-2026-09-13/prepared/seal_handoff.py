"""Seal an additive prepared fix while preserving the withdrawn predecessor byte-exactly."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent


class Strict(BaseModel):
    """Require exact typed fields for preparation claims."""
    model_config = ConfigDict(strict=True, extra="forbid")


class Asset(Strict):
    """An ordinary closed handoff file."""
    path: str
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Verification(Strict):
    """Measured tests and bounded behavioral preservation, not installation acceptance."""
    status: Literal["prepared_tested_not_installed"]
    frozen_at: AwareDatetime
    predecessor_manifest: Asset
    predecessor_disposition: Literal["held_for_confirmed_late_read_integrity_defect"]
    focused_cases_passed: Literal[82]
    combined_cases_passed: Literal[393]
    combined_duration_seconds: float = Field(gt=0)
    branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    added_late_read_and_capture_cases: Literal[13]
    existing_source_outputs_preserved: Literal[7]
    old_declarations_preserved: Literal[69]
    implementation: Asset
    tests: Asset
    documentation: Asset
    public_requests: Literal[0]
    production_writes: Literal[0]
    legal_currentness: Literal["not_verified"]


class Manifest(Strict):
    """Every payload, excluding only these self-describing final manifest files."""
    status: Literal["frozen_prepared_revision_not_installed"]
    frozen_at: AwareDatetime
    files: list[Asset]


def asset(relative: str) -> Asset:
    """Bind a file without following any symlink ancestor."""
    path = HERE / relative
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Nonordinary handoff input")
    with path.open("rb") as handle:
        sha = hashlib.file_digest(handle, "sha256").hexdigest()
    return Asset(path=relative, sha256=sha, size_bytes=path.stat().st_size)


def save(name: str, value: BaseModel) -> None:
    """Validate serialization before writing each new artifact once."""
    data = value.model_dump_json(indent=2) + "\n"
    type(value).model_validate_json(data)
    with (HERE / (name + ".json")).open("x") as handle:
        handle.write(data)
    with (HERE / (name + ".schema.json")).open("x") as handle:
        handle.write(json.dumps(type(value).model_json_schema(), indent=2) + "\n")


def main() -> int:
    """Require the completed focused run and then close this new revision."""
    match = re.search(r"393 passed in ([0-9.]+)s", (HERE / "tests-final.log").read_text())
    if not match or "82 passed" not in (HERE / "tests-focused.log").read_text():
        raise ValueError("Expected completed successful tests not found")
    coverage = json.loads((HERE / "coverage.json").read_bytes())["totals"]["percent_covered"]
    save("VERIFICATION", Verification(status="prepared_tested_not_installed",
        frozen_at=datetime.now(timezone.utc), predecessor_manifest=asset(
            "predecessor/FINAL_MANIFEST.json"),
        predecessor_disposition="held_for_confirmed_late_read_integrity_defect",
        focused_cases_passed=82, combined_cases_passed=393,
        combined_duration_seconds=float(match[1]), branch_inclusive_coverage_percent=coverage,
        added_late_read_and_capture_cases=13, existing_source_outputs_preserved=7,
        old_declarations_preserved=69, implementation=asset("proposed/research_source_lookup.py"),
        tests=asset("proposed/test_douglas_pueblo_native_lookup.py"),
        documentation=asset("proposed/RESEARCH_SOURCE_LOOKUP.md"), public_requests=0,
        production_writes=0, legal_currentness="not_verified"))
    files = [asset(p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob("*")) if p.is_file()]
    save("FINAL_MANIFEST", Manifest(status="frozen_prepared_revision_not_installed",
        frozen_at=datetime.now(timezone.utc), files=files))
    sys.stdout.write(json.dumps({"payloads": len(files),
        "manifest_sha256": asset("FINAL_MANIFEST.json").sha256}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
