"""Bounded inspection of two already observed SOS hearing-detail links."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "register-daily-diagnosis/fetch_once.py"
TARGETS = (
    "https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00337",
    "https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00328",
)


class Plan(BaseModel):
    """Finite read scope; recording permission is not evidence of HTTP completion."""

    model_config = ConfigDict(extra="forbid", strict=True)
    authorized_at: AwareDatetime
    targets: tuple[str, str]
    maximum_requests: Literal[6] = 6
    maximum_seconds_per_chain: Literal[30] = 30
    maximum_body_bytes: Literal[5_000_000] = 5_000_000
    retries: Literal[0] = 0
    helper_sha256: str
    parent_comparison_sha256: str
    fresh_acquisition_is_separate: Literal[True] = True
    legal_currentness: Literal["not_verified"] = "not_verified"


def immutable(path: Path, data: bytes) -> None:
    """Write a new local artifact atomically, refusing a prior capture."""
    if path.exists():
        raise ValueError(f"Existing capture must not be overwritten: {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(data)
    temporary.replace(path)


def main() -> None:
    """Keep each request chain isolated and stop after an access denial."""
    helper = ORIGINAL.read_bytes()
    comparison = HERE.parent / "register-daily-diagnosis/FRESH_COMPARISON.json"
    expected = "d54bb813ba1adde708a0c4d724340224f3ceb19f4632e5b305ab728dd0abea70"
    if hashlib.sha256(comparison.read_bytes()).hexdigest() != expected:
        raise ValueError("Parent comparison changed")
    plan = Plan(
        authorized_at=datetime.now(timezone.utc), targets=TARGETS,
        helper_sha256=hashlib.sha256(helper).hexdigest(),
        parent_comparison_sha256=expected,
    )
    immutable(HERE / "PLAN.json", plan.model_dump_json(indent=2).encode() + b"\n")
    immutable(HERE / "PLAN.schema.json",
              (json.dumps(Plan.model_json_schema(), indent=2) + "\n").encode())
    immutable(HERE / "fetch_once_frozen.py", helper)
    spec = importlib.util.spec_from_file_location("detail_fetch", HERE / "fetch_once_frozen.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for number, url in enumerate(TARGETS, 1):
        folder = HERE / f"target-{number:02d}"
        folder.mkdir(exist_ok=False)
        module.HERE, module.URL = folder, url
        module.main()
        receipt = module.Capture.model_validate_json((folder / "FETCH_RECEIPT.json").read_bytes())
        if any(event.http_status in {401, 403, 407} for event in receipt.events):
            break


if __name__ == "__main__":
    main()
