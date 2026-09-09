"""Regression tests for the local manifest freshness report."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from geode.freshness_report import build_freshness_report


@pytest.mark.parametrize("saved_age", [0, 999, None])
def test_recalculates_saved_age_from_last_checked(tmp_path: Path, saved_age: int | None) -> None:
    """A stale saved zero must not make an old layer appear freshly checked."""

    manifest_path = _write_manifest(
        tmp_path,
        [{"id": "04_Rulemaking", "last_checked": "2026-07-08", "staleness_days": saved_age}],
    )
    before = manifest_path.read_bytes()

    rows = build_freshness_report(tmp_path, today=date(2026, 9, 9))

    assert rows[0]["staleness_days"] == 63
    assert rows[0]["last_checked"] == "2026-07-08"
    assert rows[0]["reported_as_of"] == "2026-09-09"
    assert rows[0]["network_refresh_performed"] is False
    assert manifest_path.read_bytes() == before


@pytest.mark.parametrize("last_checked", [None, "", "unknown", "2026-02-30", 0, "2026-09-10"])
def test_unusable_dates_remain_unknown(tmp_path: Path, last_checked: object) -> None:
    """Absent, invalid, and future dates cannot be rescued by a saved age."""

    _write_manifest(
        tmp_path,
        [{"id": "04_Rulemaking", "last_checked": last_checked, "staleness_days": 0}],
    )

    rows = build_freshness_report(tmp_path, today=date(2026, 9, 9))

    assert rows[0]["staleness_days"] is None
    assert rows[0]["last_checked"] == last_checked


def test_missing_check_date_does_not_fall_back_to_ingestion(tmp_path: Path) -> None:
    """An ingestion date does not establish when sources were last checked."""

    _write_manifest(
        tmp_path,
        [{"id": "04_Rulemaking", "last_ingested": "2026-09-09", "staleness_days": 0}],
    )

    rows = build_freshness_report(tmp_path, today=date(2026, 9, 9))

    assert rows[0]["last_checked"] is None
    assert rows[0]["staleness_days"] is None


def test_injected_report_date_controls_age_and_preserves_manifest_fields(tmp_path: Path) -> None:
    """Reporting at different dates changes the age without changing corpus status."""

    _write_manifest(
        tmp_path,
        [
            {
                "id": "04_Rulemaking",
                "last_checked": "2026-09-09",
                "record_count": 7,
                "status": "ready",
            }
        ],
    )

    same_day = build_freshness_report(tmp_path, today=date(2026, 9, 9))[0]
    next_day = build_freshness_report(tmp_path, today=date(2026, 9, 10))[0]

    assert same_day["staleness_days"] == 0
    assert next_day["staleness_days"] == 1
    assert next_day["reported_as_of"] == "2026-09-10"
    assert next_day["record_count"] == 7
    assert next_day["status"] == "ready"
    assert next_day["policy"] == {"rulemaking": {"max_staleness_days": 20}}


def _write_manifest(root: Path, layers: list[dict[str, object]]) -> Path:
    """Write a minimal manifest fixture for local reporting."""

    manifest_path = root / "_CONTROL_PLANE" / "MASTER_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "data_layers": layers,
                "freshness_policy": {"rulemaking": {"max_staleness_days": 20}},
            }
        ),
        encoding="utf-8",
    )
    return manifest_path
