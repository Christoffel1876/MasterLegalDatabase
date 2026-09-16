"""Hash-only portable review-packet validation; never execute saved watch code."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject undeclared or coerced audit fields."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Confined immutable file identity."""
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def confined(self) -> Ref:
        """Reject absolute, traversing or noncanonical references."""
        p = Path(self.path)
        if p.is_absolute() or ".." in p.parts or p.as_posix() != self.path or not p.parts:
            raise ValueError("Unsafe inventory path")
        return self


class Coverage(Strict):
    """Keep combined and branch-only measurements separate."""
    adapter_branch_inclusive_percent: float = Field(ge=0, le=100)
    helper_branch_inclusive_percent: float = Field(ge=0, le=100)
    combined_branch_inclusive_percent: float = Field(ge=0, le=100)
    adapter_branch_only_percent: float = Field(ge=0, le=100)
    helper_branch_only_percent: float = Field(ge=0, le=100)


class Manifest(Strict):
    """Closed review receipt with explicit historical and fixture limits."""
    schema_version: Literal[1]
    frozen_at: AwareDatetime
    disposition: Literal["one_recovery_bug_fixed_focused_checks_passed"]
    initial_production_pin_count_verified: Literal[8]
    production_files_changed: list[str] = Field(min_length=2, max_length=2)
    focused_tests_passed: Literal[173]
    focused_warnings: Literal[5]
    focused_duration_seconds: Literal[23.96]
    coverage: Coverage
    public_requests: Literal[0]
    original_reproduction_clock: Literal["injected_fixture_clock"]
    regressions: list[str] = Field(min_length=2)
    full_suite_status: Literal["parent_running_separately_not_certified_here"]
    verifier_scope: Literal["closed_hash_schema_check_only_no_code_or_network_execution"]
    files: list[Ref]
    limitations: list[str] = Field(min_length=3)
    legal_currentness: Literal["not_verified"]

    @model_validator(mode="after")
    def identities(self) -> Manifest:
        """Pin the two-file repair scope and unique ordered custody."""
        if self.production_files_changed != ["geode/pipeline/manual_watch_http.py",
                                             "tests/test_manual_source_watch.py"]:
            raise ValueError("Repair scope differs")
        names = [f.path for f in self.files]
        if names != sorted(set(names)):
            raise ValueError("Duplicate or unsorted inventory")
        return self


def verify(root: Path) -> Manifest:
    """Check bytes and schemas only, without importing any saved implementation."""
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("Symlinked packet ancestor")
    record = Manifest.model_validate_json((root / "FINAL_MANIFEST.json").read_bytes())
    if json.loads((root / "FINAL_MANIFEST.schema.json").read_bytes()) != Manifest.model_json_schema():
        raise ValueError("Schema mismatch")
    names = {f.path for f in record.files} | {"FINAL_MANIFEST.json"}
    expected_dirs = {p.as_posix() for name in names for p in Path(name).parents if str(p) != "."}
    files, dirs = set(), set()
    for p in root.rglob("*"):
        if p.is_symlink() or not (p.is_dir() or p.is_file()):
            raise ValueError("Nonordinary packet member")
        (dirs if p.is_dir() else files).add(p.relative_to(root).as_posix())
    if files != names or dirs != expected_dirs:
        raise ValueError("Closed inventory differs")
    for ref in record.files:
        path = root / ref.path
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if path.stat().st_size != ref.size_bytes or digest != ref.sha256:
            raise ValueError("Evidence differs: " + ref.path)
    return record


if __name__ == "__main__":
    result = verify(Path(__file__).absolute().parent)
    sys.stdout.write(json.dumps({
        "status": "verified_frozen_review_packet", "files": len(result.files),
        "focused_tests_passed": result.focused_tests_passed,
        "saved_scripts_executed": False, "network_executed": False,
        "legal_currentness": "not_verified",
    }, indent=2) + "\n")
