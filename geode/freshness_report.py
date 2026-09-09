"""Freshness report CLI for Project Geode."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from geode.utils.file_io import read_json
from geode.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the freshness report CLI parser."""

    parser = argparse.ArgumentParser(description="Report Project Geode layer freshness.")
    parser.add_argument("--root", default=Path.cwd(), type=Path)
    return parser


def build_freshness_report(root: Path, today: date | None = None) -> list[dict[str, object]]:
    """Calculate local manifest check ages without checking official sources.

    Stored staleness values are historical and cannot establish the current age.
    Missing, invalid, or future check dates therefore have an unknown age.
    """

    today = today or date.today()
    manifest = read_json(root / "_CONTROL_PLANE" / "MASTER_MANIFEST.json")
    policy = manifest.get("freshness_policy", {})
    rows: list[dict[str, object]] = []
    for layer in manifest.get("data_layers", []):
        if not isinstance(layer, dict):
            continue
        last_checked = layer.get("last_checked")
        staleness_days = _days_since_check(last_checked, today)
        rows.append(
            {
                "id": layer.get("id"),
                "record_count": layer.get("record_count"),
                "last_checked": last_checked,
                "staleness_days": staleness_days,
                "policy": policy,
                "status": layer.get("status"),
                "reported_as_of": today.isoformat(),
                "network_refresh_performed": False,
            }
        )
    return rows


def _days_since_check(last_checked: object, today: date) -> int | None:
    """Return the check age only when a valid nonfuture date is recorded."""

    if not isinstance(last_checked, str):
        return None
    try:
        checked_date = date.fromisoformat(last_checked)
    except ValueError:
        return None
    age = (today - checked_date).days
    return age if age >= 0 else None


def main() -> int:
    """Run the freshness report command."""

    configure_logging()
    args = build_parser().parse_args()
    rows = build_freshness_report(args.root.resolve())
    LOGGER.info("Local manifest report only; no official sources were checked.")
    for row in rows:
        LOGGER.info(
            "%s records=%s staleness=%s status=%s",
            row["id"],
            row["record_count"],
            row["staleness_days"],
            row["status"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
