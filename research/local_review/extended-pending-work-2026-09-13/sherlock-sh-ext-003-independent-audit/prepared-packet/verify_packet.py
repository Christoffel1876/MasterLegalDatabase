"""Read-only integrity verification of immutable prepared files, excluding later deliveries."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Asset(BaseModel):
    """Bind an exact prepared payload."""

    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Manifest(BaseModel):
    """The immutable preparation, distinct from any future delivery or dispatch."""

    model_config = ConfigDict(extra="forbid", strict=True)
    assignment_id: Literal["SH-EXT-003"]
    status: Literal["PREPARED_NOT_DISPATCHED"]
    frozen_at: AwareDatetime
    files: list[Asset]
    public_actions_by_preparation: Literal[0]
    hidden_network_requests_measured: Literal[False]
    legal_currentness: Literal["not_verified"]


def main() -> int:
    """Verify closed prepared-file membership and exact bytes without importing acquisition code."""
    root = Path(__file__).resolve().parent
    data = (root / "FINAL_MANIFEST.json").read_bytes()
    manifest = Manifest.model_validate_json(data)
    schema = json.loads((root / "FINAL_MANIFEST.schema.json").read_bytes())
    if schema != Manifest.model_json_schema():
        raise ValueError("Manifest schema differs")
    jsonschema.validate(json.loads(data), schema)
    expected = {ref.path for ref in manifest.files} | {"FINAL_MANIFEST.json"}
    if len(expected) != len(manifest.files) + 1:
        raise ValueError("Duplicate prepared payload")
    actual = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] == "deliveries":
            continue
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Nonordinary prepared member")
        if path.is_file():
            actual.add(relative.as_posix())
    if actual != expected:
        raise ValueError("Prepared membership differs")
    for ref in manifest.files:
        relative = Path(ref.path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe prepared path")
        path = root / relative
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != ref.sha256 or path.stat().st_size != ref.size_bytes:
            raise ValueError("Prepared bytes differ: " + ref.path)
    sys.stdout.write(json.dumps({"status": "passed", "prepared_payloads": len(manifest.files),
        "assignment_id": manifest.assignment_id, "dispatch": "not_performed",
        "public_actions_by_preparation": 0, "legal_currentness": "not_verified"}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
