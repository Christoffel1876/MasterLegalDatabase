"""Close the nine measured offline findings without altering production or source evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent


class Ref(BaseModel):
    """Closed audit-relative file identity."""
    model_config = ConfigDict(strict=True, extra="forbid")
    path: str
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    size_bytes: int


class Manifest(BaseModel):
    """A frozen bounded audit, not a claim of source corruption in the actual repository."""
    model_config = ConfigDict(strict=True, extra="forbid")
    frozen_at: AwareDatetime
    status: Literal["confirmed_temporal_evidence_binding_failures"]
    source_adapters_affected: Literal[7] = 7
    reproduced_cases: Literal[9] = 9
    production_evidence_mutated: Literal[False] = False
    public_requests: Literal[0] = 0
    files: list[Ref]


def main() -> None:
    """Validate measured claims before preserving a closed inventory."""
    data = json.loads((HERE / "PROBES.json").read_bytes())
    events = data["events"]
    if (len(events) != 9 or len({e["source_id"] for e in events}) != 7 or
            any(e["status"] != "returned_injected_evidence" or
                not e["source_files_restored_in_fixture"] for e in events)):
        raise ValueError("Measured reproduction claims differ")
    refs = []
    for path in sorted(HERE.rglob("*")):
        if path.is_file():
            raw = path.read_bytes()
            refs.append(Ref(path=path.relative_to(HERE).as_posix(),
                            sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    manifest = Manifest(frozen_at=datetime.now(timezone.utc),
        status="confirmed_temporal_evidence_binding_failures", files=refs)
    raw = manifest.model_dump_json(indent=2) + "\n"
    Manifest.model_validate_json(raw)
    with (HERE / "FINAL_MANIFEST.json").open("x") as handle:
        handle.write(raw)
    with (HERE / "FINAL_MANIFEST.schema.json").open("x") as handle:
        handle.write(json.dumps(Manifest.model_json_schema(), indent=2) + "\n")


if __name__ == "__main__":
    main()
