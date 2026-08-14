"""Checks for required session freshness onboarding artifacts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "_CONTROL_PLANE"


def test_session_freshness_artifacts_exist_and_parse() -> None:
    """The session review must have readable instructions and valid JSON contracts."""
    guide = CONTROL / "SESSION_START_FRESHNESS.md"
    priorities = CONTROL / "FRESHNESS_PRIORITIES.json"
    schema = CONTROL / "SESSION_FRESHNESS_REPORT.schema.json"

    assert guide.exists()
    assert priorities.exists()
    assert schema.exists()

    priority_data = json.loads(priorities.read_text(encoding="utf-8"))
    schema_data = json.loads(schema.read_text(encoding="utf-8"))

    assert priority_data["review_frequency"] == "every_session"
    assert priority_data["review_actor"] == "brief_freshness_subagent"
    assert len(priority_data["priority_areas"]) >= 3
    assert "official Colorado sources" in guide.read_text(encoding="utf-8")
    assert "freshness-search subagent" in guide.read_text(encoding="utf-8")
    assert "current" in guide.read_text(encoding="utf-8").lower()
    assert "internet search is required" in guide.read_text(encoding="utf-8")
    assert "publication" in guide.read_text(encoding="utf-8").lower()
    assert "source_url" in schema_data["candidate_required_fields"]
    assert "needs_validation" in schema_data["allowed_statuses"]


def test_existing_freshness_report_discloses_network_boundary() -> None:
    """A local freshness report must not be mistaken for a live source refresh."""
    report = json.loads((CONTROL / "SOURCE_FRESHNESS_REPORT.json").read_text(encoding="utf-8"))
    assert report["network_refresh_performed"] is False
    assert "external source refresh" in report["boundary"].lower()


def test_read_order_includes_session_freshness_review() -> None:
    """Freshness review must occur before normal retrieval."""
    read_order = json.loads((CONTROL / "AI_READ_ORDER.json").read_text(encoding="utf-8"))
    steps = read_order["steps"]
    assert any("SESSION_START_FRESHNESS" in step["file"] for step in steps)
    freshness_order = next(step["order"] for step in steps if "SESSION_START_FRESHNESS" in step["file"])
    manifest_order = next(step["order"] for step in steps if "MASTER_MANIFEST" in step["file"])
    assert freshness_order < manifest_order