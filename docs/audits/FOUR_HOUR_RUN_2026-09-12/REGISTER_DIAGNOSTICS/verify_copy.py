"""Verify the immutable implementation subdirectory; allow later parent acceptance files."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent


class Asset(BaseModel):
    """One exact copied implementation artifact."""

    model_config = ConfigDict(strict=True, extra="forbid")
    path: str
    original_path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(ge=0)


class Receipt(BaseModel):
    """Copy custody distinct from broader testing and deployment acceptance."""

    model_config = ConfigDict(strict=True, extra="forbid")
    copied_at: AwareDatetime
    source_manifest_sha256: str
    source_payload_count: Literal[33]
    copied_file_count: Literal[34]
    status: Literal["frozen_implementation_copied_full_suite_acceptance_separate"]
    source_root: str
    scope: Literal["closed implementation subdirectory only; parent permits later acceptance"]
    assets: list[Asset] = Field(min_length=34, max_length=34)


def main() -> None:
    """Validate the copied receipt and original closed manifest without executing code."""
    raw = (HERE / "COPY_RECEIPT.json").read_bytes()
    receipt = Receipt.model_validate_json(raw)
    jsonschema.validate(
        json.loads(raw), json.loads((HERE / "COPY_RECEIPT.schema.json").read_bytes())
    )
    names = {row.path for row in receipt.assets}
    assert len(names) == 34
    entries = list((HERE / "implementation").rglob("*"))
    assert not any(p.is_symlink() for p in [HERE, *HERE.parents, HERE / "implementation", *entries])
    assert {p.relative_to(HERE).as_posix() for p in entries if p.is_file()} == names
    expected_dirs = {
        parent.as_posix() for name in names for parent in Path(name).parents
        if parent not in (Path("."), Path("implementation"))
    }
    assert {p.relative_to(HERE).as_posix() for p in entries if p.is_dir()} == expected_dirs
    for row in receipt.assets:
        path = Path(row.path)
        assert not path.is_absolute() and ".." not in path.parts
        assert row.path.startswith("implementation/")
        data = (HERE / path).read_bytes()
        assert len(data) == row.bytes and hashlib.sha256(data).hexdigest() == row.sha256
    manifest_bytes = (HERE / "implementation/FINAL_MANIFEST.json").read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == receipt.source_manifest_sha256
    manifest = json.loads(manifest_bytes)
    jsonschema.validate(manifest, json.loads(
        (HERE / "implementation/FINAL_MANIFEST.schema.json").read_bytes()
    ))
    mapped = {row.path.removeprefix("implementation/"): row for row in receipt.assets}
    assert set(mapped) == {row["path"] for row in manifest["assets"]} | {"FINAL_MANIFEST.json"}
    assert len(manifest["assets"]) == 33
    for row in manifest["assets"]:
        assert mapped[row["path"]].sha256 == row["sha256"]
        assert mapped[row["path"]].bytes == row["bytes"]
    sys.stdout.write(json.dumps({
        "status": "exact_frozen_implementation_copy_verified", "copied_files": 34,
        "closed_payloads": 33, "full_suite_acceptance": "separate", "executed_code": False,
    }) + "\n")


if __name__ == "__main__":
    main()
