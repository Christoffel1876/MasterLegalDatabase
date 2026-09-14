"""Read-only checks of the selective CRS lookup integration and recorded CLI evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path, PureWindowsPath
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

AUDIT = Path("docs/audits/FOUR_HOUR_RUN_2026-09-12/CRS_LOOKUP")
PROTOTYPE_SHA = "6f0ddee7d2083d2d616456c043691057b96d634a691373cf661d1d0218b5a084"


class Strict(BaseModel):
    """Reject undeclared or coerced integration-evidence fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """One exact file with a declared local path base."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0, le=10_000_000)

    @model_validator(mode="after")
    def confined(self) -> Ref:
        """Refuse path escapes and ambiguous aliases."""
        path = Path(self.path)
        if (path.is_absolute() or ".." in path.parts or str(path) != self.path
                or PureWindowsPath(self.path).drive or "\\" in self.path
                or self.path in {"", "."}):
            raise ValueError("Unconfined evidence reference")
        return self


class CliCheck(Strict):
    """A real isolated CLI invocation from a temporary directory outside the checkout."""

    section_id: str
    mode: Literal["source_only", "current_law"]
    command: list[str]
    actual_cwd: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    exit_code: Literal[0, 2]
    status: Literal["matched", "outside_scope", "refused_mode"]
    stdout: Ref
    stderr: Ref
    temporary_directory_empty_after: Literal[True]


class Receipt(Strict):
    """Selective-integration checks; no claim of full-suite success or current law."""

    verified_at: AwareDatetime
    status: Literal["selectively_integrated_pending_root_full_suite"]
    implementation_files: list[Ref]
    source_manifest: Ref
    source_review: Ref
    root_source_acceptance: Ref
    prototype_manifest: Ref
    prototype_manifest_sha256: Literal[PROTOTYPE_SHA] = PROTOTYPE_SHA
    prototype_subset_files: list[Ref]
    prototype_paths_omitted_from_subset: list[str]
    code_adaptation_diff: Ref
    test_adaptation_diff: Ref
    focused_test_command: list[str]
    focused_test_exit: Literal[0]
    focused_tests_passed: Literal[81]
    branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    focused_test_log: Ref
    cli_checks: list[CliCheck] = Field(min_length=5, max_length=5)
    reviewed_ids: tuple[Literal["CRS-1-1-101", "CRS-1-1-102", "CRS-1-1-103"], ...]
    statutory_paragraphs: Literal[6]
    native_regions: Literal[19]
    public_requests: Literal[0]
    full_suite_run: Literal[False]
    duplicate_production_source_copy: Literal[False]
    prior_2025_prototype_changed: Literal[False]
    legal_currentness: Literal["not_verified"]
    limitations: list[str]


class Inventory(Strict):
    """Closed audit subset, distinct from the full historical prototype inventory."""

    files: list[Ref]
    excluded_files: Literal["INVENTORY.json only"]


def file_ref(base: Path, name: str) -> Ref:
    """Stream a file hash after refusing links and special files."""
    Ref(path=name, sha256="0" * 64, size_bytes=0)
    path = base / name
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Missing or symlinked file")
    with path.open("rb") as handle:
        sha = hashlib.file_digest(handle, "sha256").hexdigest()
    return Ref(path=name, sha256=sha, size_bytes=path.stat().st_size)


def check(base: Path, ref: Ref) -> None:
    """Verify an exact, confined file reference."""
    if file_ref(base, ref.path) != ref:
        raise ValueError(f"Evidence differs: {ref.path}")


def verify(root: Path) -> Receipt:
    """Validate the closed audit, adaptation provenance and replay all three source selections."""
    if ".." in root.parts:
        raise ValueError("Root traversal refused")
    root = root.absolute()
    folder = root / AUDIT
    inventory = Inventory.model_validate_json((folder / "INVENTORY.json").read_bytes())
    expected = {ref.path for ref in inventory.files}
    if len(expected) != len(inventory.files):
        raise ValueError("Duplicate inventory members")
    actual = set()
    for path in folder.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Unexpected file type")
        if path.is_file() and path != folder / "INVENTORY.json":
            actual.add(path.relative_to(folder).as_posix())
    if actual != expected:
        raise ValueError("Missing or additional audit member")
    for ref in inventory.files:
        check(folder, ref)
    receipt = Receipt.model_validate_json((folder / "VERIFICATION.json").read_bytes())
    for ref in [*receipt.implementation_files, receipt.source_manifest, receipt.source_review,
                receipt.root_source_acceptance]:
        check(root, ref)
    for ref in [receipt.prototype_manifest, *receipt.prototype_subset_files,
                receipt.code_adaptation_diff, receipt.test_adaptation_diff,
                receipt.focused_test_log]:
        check(folder, ref)
    if receipt.prototype_manifest.sha256 != PROTOTYPE_SHA:
        raise ValueError("Prototype identity changed")
    prototype = json.loads((folder / receipt.prototype_manifest.path).read_bytes())
    prior = {ref["path"]: ref for ref in prototype["files"]}
    kept = {str(Path(ref.path).relative_to("prototype-subset"))
            for ref in receipt.prototype_subset_files}
    if set(receipt.prototype_paths_omitted_from_subset) != (
            set(prior) | {"MANIFEST.json"}) - kept:
        raise ValueError("Prototype subset exclusions differ")
    for ref in receipt.prototype_subset_files:
        name = str(Path(ref.path).relative_to("prototype-subset"))
        if name != "MANIFEST.json" and (ref.sha256 != prior[name]["sha256"]
                                       or ref.size_bytes != prior[name]["size_bytes"]):
            raise ValueError("Prototype subset bytes changed")
    spec = importlib.util.spec_from_file_location(
        "verified_crs_lookup", root / "scripts/crs_source_lookup.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if json.loads((folder / "RESULT.schema.json").read_bytes()) != module.Result.model_json_schema():
        raise ValueError("Result schema differs")
    if json.loads((folder / "VERIFICATION.schema.json").read_bytes()) != Receipt.model_json_schema():
        raise ValueError("Receipt schema differs")
    if json.loads((folder / "INVENTORY.schema.json").read_bytes()) != Inventory.model_json_schema():
        raise ValueError("Inventory schema differs")
    if receipt.reviewed_ids != module.IDS:
        raise ValueError("Reviewed selection changed")
    expected_checks = [(sid, "source_only", 0, "matched") for sid in module.IDS] + [
        ("CRS-1-1-104", "source_only", 2, "outside_scope"),
        ("CRS-1-1-101", "current_law", 2, "refused_mode")]
    if [(c.section_id, c.mode, c.exit_code, c.status) for c in receipt.cli_checks] != expected_checks:
        raise ValueError("CLI evidence scope differs")
    for cli in receipt.cli_checks:
        check(folder, cli.stdout)
        check(folder, cli.stderr)
        saved = module.Result.model_validate_json((folder / cli.stdout.path).read_bytes())
        if saved != module.lookup(module.DEFAULT_SOURCE, cli.section_id, mode=cli.mode):
            raise ValueError("CLI response replay differs")
        if saved.status != cli.status or cli.started_at > cli.completed_at:
            raise ValueError("CLI status or timing mismatch")
    for ref in inventory.files:
        check(folder, ref)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    result = verify(args.root)
    sys.stdout.write("PASS: three reviewed source selections and five recorded CLI checks; "
                     "full suite remains a separate root check.\n")
