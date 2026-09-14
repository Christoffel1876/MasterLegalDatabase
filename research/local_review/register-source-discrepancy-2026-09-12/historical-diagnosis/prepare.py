"""Copy a bounded read-only Register diagnosis baseline, once."""

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
REPO = WORKSPACE / "MasterLegalDatabase"
sys.path.insert(0, str(REPO))
from geode.pipeline.register_daily import RefreshState

URL = (
    "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026"
    "&Volume=49&yearPublishNumber=15&Month=8&Year=2026"
)


class Asset(BaseModel):
    """Exact immutable copied input."""

    model_config = ConfigDict(extra="forbid")
    original_path: str
    path: str
    sha256: str
    bytes: int


class Receipt(BaseModel):
    """Time of local custody capture, separate from source retrieval."""

    model_config = ConfigDict(extra="forbid")
    captured_at: datetime
    purpose: str
    issue_url: str
    assets: list[Asset]


def main() -> None:
    """Preserve logs, implementation and exact existing source/state evidence."""

    items = []
    prior = WORKSPACE / "handoffs/run-2026-09-12/daily-workflow-status"
    for source in [prior / "register-34694019784.log", *sorted((prior / "register-report").iterdir())]:
        items.append((source, "hosted/" + source.relative_to(prior).as_posix()))
    names = [
        "_CONTROL_PLANE/REGISTER_REFRESH_STATE.json",
        "04_Rulemaking/_meta/rulemaking_notices_meta.jsonl",
        "04_Rulemaking/_index.jsonl",
        "04_Rulemaking/_dataset/register_daily_sources.jsonl",
        "04_Rulemaking/2026/register_2026_Q3.jsonl",
        "geode/pipeline/register_daily.py", "geode/connectors/register_daily_parser.py",
        "geode/connectors/register_scraper.py", "geode/schemas/models.py",
        "geode/utils/file_io.py", "scripts/publish_register_update.py",
        ".github/workflows/register-daily.yml",
    ]
    state = RefreshState.model_validate_json((REPO / names[0]).read_bytes())
    artifact = state.sources[URL]
    assert artifact.sha256 == state.issues[URL].source_sha256
    old_source = REPO / artifact.path
    assert hashlib.sha256(old_source.read_bytes()).hexdigest() == artifact.sha256
    names.append(artifact.path)
    for name in names:
        items.append((REPO / name, "baseline/" + name))
    assets = []
    for source, name in items:
        target = HERE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists()
        before = source.read_bytes()
        with target.open("xb") as handle:
            handle.write(before)
        assert source.read_bytes() == target.read_bytes() == before
        assets.append(Asset(original_path=str(source), path=name,
                            sha256=hashlib.sha256(before).hexdigest(), bytes=len(before)))
    receipt = Receipt(captured_at=datetime.now(timezone.utc), issue_url=URL,
                      purpose="Read-only diagnosis; no corpus or pipeline mutation", assets=assets)
    (HERE / "BASELINE_RECEIPT.json").write_text(receipt.model_dump_json(indent=2) + "\n")
    (HERE / "BASELINE_RECEIPT.schema.json").write_text(
        json.dumps(Receipt.model_json_schema(), indent=2) + "\n"
    )
    sys.stdout.write(json.dumps({"assets": len(assets), "old_issue": state.issues[URL].model_dump(mode="json"), "old_source": artifact.model_dump(mode="json")}) + "\n")


if __name__ == "__main__":
    main()
