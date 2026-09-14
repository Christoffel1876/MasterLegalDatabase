"""Verify frozen integration hashes and the bounded inventory delta without writing."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Reject undeclared integration fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class FileRef(StrictModel):
    """Bind exact ordinary bytes in the handoff or repository."""

    domain: Literal["handoff", "repository"]
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Tests(StrictModel):
    """Retain the actual focused check counts and coverage measures."""

    passed: int = Field(gt=0)
    failed: Literal[0]
    elapsed_seconds: float = Field(gt=0)
    combined_coverage_percent: float = Field(ge=90, le=100)
    lookup_coverage_percent: float = Field(ge=90, le=100)
    lookup_branch_percent: float = Field(ge=90, le=100)
    inventory_coverage_percent: float = Field(ge=90, le=100)


class Integration(StrictModel):
    """Describe this additive integration without legal-readiness promotion."""

    schema_version: Literal[1]
    prepared_at: AwareDatetime
    scope: Literal["six_source_lookup_and_61_source_review_inventory"]
    source_id: Literal["colorado-springs-construction-fees-atlas-directed"]
    historical_review_alias: Literal["SD014-02"]
    source_rows: Literal[128]
    source_tables: Literal[9]
    native_lines: Literal[410]
    mandatory_context_blocks: Literal[80]
    inventory_sources: Literal[61]
    inventory_mapped: Literal[21]
    inventory_unmapped: Literal[40]
    unchanged_old_review_joins: Literal[20]
    unchanged_old_lookup_outputs: Literal[5]
    new_authority_joins: list[str] = Field(min_length=2, max_length=2)
    later_http_binding_sources: list[str] = Field(min_length=3, max_length=3)
    tests: Tests
    limitations: list[str] = Field(min_length=5)
    files: list[FileRef] = Field(min_length=15)
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    canonical_writes_by_integration: Literal[False]


def ordinary(root: Path, name: str) -> Path:
    """Return a confined ordinary file after rejecting lexical path and symlink attacks."""
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("Unsafe evidence path")
    path = root / relative
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Symlink evidence path")
    if not path.is_file():
        raise ValueError("Missing ordinary evidence file")
    return path


def verify(root: Path, handoff: Path) -> Integration:
    """Check immutable inputs and exact allowed differences from the saved 59-row snapshot."""
    receipt = Integration.model_validate_json((handoff / "INTEGRATION.json").read_bytes())
    schema = json.loads((handoff / "INTEGRATION.schema.json").read_bytes())
    if schema != Integration.model_json_schema():
        raise ValueError("Integration schema differs")
    identities = [(ref.domain, ref.path) for ref in receipt.files]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate evidence identity")
    for ref in receipt.files:
        path = ordinary(root if ref.domain == "repository" else handoff, ref.path)
        body = path.read_bytes()
        if len(body) != ref.size_bytes or hashlib.sha256(body).hexdigest() != ref.sha256:
            raise ValueError("Evidence differs: " + ref.path)
    folder = root / "research/local_review/manual-source-review-inventory-2026-09-11"
    old = folder / "_SNAPSHOTS/BEFORE_SPRINGS_2026-09-13"
    before = json.loads((old / "join-plan.json").read_bytes())
    after = json.loads((folder / "join-plan.json").read_bytes())
    if after["reviews"][:20] != before["reviews"] or len(after["reviews"]) != 21:
        raise ValueError("Prior review joins changed")
    if after["legacy_ledger"] != before["legacy_ledger"]:
        raise ValueError("Legacy coverage ledger pin changed")
    if len(after["authorities"]) != 61 or len(before["authorities"]) != 59:
        raise ValueError("Authority join count differs")
    changed = []
    for previous, current in zip(before["authorities"], after["authorities"][:59], strict=True):
        if previous != current:
            a, b = dict(previous), dict(current)
            a.pop("verified_http", None)
            b.pop("verified_http", None)
            if a != b or current.get("verified_http") is None:
                raise ValueError("An unapproved old authority field changed")
            changed.append(current["record_id"])
    if sorted(changed) != sorted(receipt.later_http_binding_sources):
        raise ValueError("Later Greeley HTTP bindings differ")
    if [r["record_id"] for r in after["authorities"][59:]] != receipt.new_authority_joins:
        raise ValueError("New source identities differ")
    inventory = json.loads((folder / "inventory.json").read_bytes())
    if (len(inventory["sources"]), inventory["rows_with_review"],
            inventory["rows_without_review"]) != (61, 21, 40):
        raise ValueError("Inventory scope counts differ")
    return receipt


def main() -> int:
    """Print a small verification receipt; never invoke a relocated intake writer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.root.absolute(), Path(__file__).absolute().parent)
    sys.stdout.write(json.dumps({
        "status": "verified_additive_integration", "files": len(result.files),
        "inventory_sources": 61, "mapped_reviews": 21, "unmapped_reviews": 40,
        "unchanged_old_lookup_outputs": 5, "legal_currentness": "not_verified",
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
