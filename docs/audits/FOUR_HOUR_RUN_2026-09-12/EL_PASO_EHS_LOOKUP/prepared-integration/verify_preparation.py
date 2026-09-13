"""Verify the closed handoff and optional unchanged production preimages, without writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Require exact declared handoff fields and scalar types."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Identify one ordinary retained payload."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Freeze(Strict):
    """Record completed local draft checks without implying installation or legal currency."""

    status: Literal["prepared_not_installed"]
    frozen_at: AwareDatetime
    source_id: Literal["el-paso-boh-ehs-fees-sd011"]
    source_sha256: Literal["1b0529fb7514bcc50c0dd36c903ca361f6ab431712b4aebc48bca8e3f5373622"]
    proposed_files: list[Asset]
    production_preimages_unchanged: Literal[True]
    production_checked_at: AwareDatetime
    source_rows: Literal[65]
    groups: Literal[7]
    contexts: Literal[37]
    unchanged_native_bytes: Literal[8060]
    prior_source_count: Literal[6]
    prior_output_files_identical: Literal[12]
    focused_tests_passed: int = Field(ge=1)
    focused_test_log: Asset
    coverage_report: Asset
    new_adapter_executed_statements: int = Field(ge=0)
    new_adapter_missing_statements: int = Field(ge=0)
    new_adapter_executed_branches: int = Field(ge=0)
    new_adapter_missing_branches: int = Field(ge=0)
    new_adapter_branch_inclusive_percent: float = Field(ge=0, le=100)
    independent_review: str
    legal_currentness: Literal["not_verified"]
    production_installation: Literal["not_attempted"]
    public_requests: Literal[0]
    limitations: list[str]


class Manifest(Strict):
    """Closed inventory of every payload except this manifest itself."""

    version: Literal[1]
    status: Literal["prepared_not_installed"]
    frozen_at: AwareDatetime
    files: list[Asset]

    @model_validator(mode="after")
    def unique(self) -> Manifest:
        """Reject duplicate and unsafe inventory identities."""
        names = [ref.path for ref in self.files]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate payload identity")
        for name in names:
            p = Path(name)
            if p.is_absolute() or ".." in p.parts or p.as_posix() != name:
                raise ValueError("Unsafe payload path")
        return self


def digest(path: Path) -> str:
    """Hash exact bytes without building an extra whole-file buffer."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def validate(root: Path, production: Path | None = None) -> dict:
    """Check all retained bytes and optional live preimages without invoking proposal code."""
    manifest = Manifest.model_validate_json((root / "FINAL_MANIFEST.json").read_bytes())
    expected = {ref.path for ref in manifest.files} | {"FINAL_MANIFEST.json"}
    actual, directories = set(), set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError("Nonordinary handoff member")
        (directories if path.is_dir() else actual).add(path.relative_to(root).as_posix())
    expected_dirs = {p.as_posix() for name in expected for p in Path(name).parents
                     if p.as_posix() != "."}
    if actual != expected or directories != expected_dirs:
        raise ValueError("Handoff closed inventory differs")
    for ref in manifest.files:
        path = root / ref.path
        if path.stat().st_size != ref.size_bytes or digest(path) != ref.sha256:
            raise ValueError("Payload hash or size differs: " + ref.path)
    for name, model in [("FINAL_MANIFEST", Manifest), ("FREEZE", Freeze)]:
        schema = json.loads((root / (name + ".schema.json")).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError("Exported schema differs: " + name)
        data = json.loads((root / (name + ".json")).read_bytes())
        jsonschema.Draft202012Validator(schema).validate(data)
        model.model_validate_json(json.dumps(data))
    freeze = Freeze.model_validate_json((root / "FREEZE.json").read_bytes())
    inventory = {ref.path: ref for ref in manifest.files}
    for ref in [*freeze.proposed_files, freeze.focused_test_log, freeze.coverage_report]:
        if inventory.get(ref.path) != ref:
            raise ValueError("Freeze receipt references a different payload")
    if production is not None:
        baseline = json.loads((root / "BASELINE.json").read_bytes())
        for raw in baseline["production_files"]:
            ref = Asset.model_validate_json(json.dumps(raw))
            path = production / ref.path
            if path.is_symlink() or not path.is_file():
                raise ValueError("Production preimage is not an ordinary file")
            if path.stat().st_size != ref.size_bytes or digest(path) != ref.sha256:
                raise ValueError("Production baseline has changed: " + ref.path)
    return {"status": "passed", "payloads": len(manifest.files),
            "production_preimages_checked": production is not None,
            "production_installation": "not_attempted", "legal_currentness": "not_verified"}


def main() -> int:
    """Run read-only closure verification and optionally check live production preimages."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-production-preimages", type=Path)
    arguments = parser.parse_args()
    result = validate(Path(__file__).resolve().parent, arguments.check_production_preimages)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
