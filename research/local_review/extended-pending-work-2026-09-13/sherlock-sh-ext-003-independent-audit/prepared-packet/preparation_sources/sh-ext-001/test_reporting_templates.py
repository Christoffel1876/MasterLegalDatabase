"""Offline synthetic checks of the reporting budgets; no public actions or source acquisition."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models import ActionLog, Reservation, Result


def reservation(number: int, authority: str | None = None) -> Reservation:
    """Create a clearly synthetic reservation for counter validation only."""
    return Reservation(action_id=f"SHEXT001-A{number:03}",
        authority_id=authority or ("CO-COUNTY-PUEBLO" if number % 2 else "CO-COUNTY-FREMONT"),
        reserved_at=datetime(2026, 9, 13, 2, tzinfo=timezone.utc), tool_name="synthetic_test",
        action_kind="open", requested_url=f"https://example.invalid/{number}",
        basis="Offline fixture; never opened", budget_checked=True)


def result(number: int) -> Result:
    """Pair a synthetic result with a reservation without claiming source bytes."""
    return Result(action_id=f"SHEXT001-A{number:03}", finished_at=None,
        time_unknown_reason="Synthetic test only", observed_final_url=None,
        visible_redirect_urls=[], outcome="tool_preflight_error", body_role="no_body",
        retained_assets=[], pdf_magic_checked=False, pdf_parse_succeeded=False,
        physical_pages=None, notes="No public request occurred")


def test_valid_recorded_budget() -> None:
    """One pending action and a completed prior action are allowed."""
    log = ActionLog(reservations=[reservation(1), reservation(2)], results=[result(1)])
    assert not log.hidden_network_requests_measured


@pytest.mark.parametrize("case", ["total", "authority", "distinct", "duplicate", "unreserved",
                                  "multiple_pending"])
def test_counter_refusals(case: str) -> None:
    """Reject over-cap, duplicate and unreserved reporting states."""
    if case == "total":
        values = [reservation(i) for i in range(1, 42)]
    elif case == "authority":
        values = [reservation(i, "CO-COUNTY-PUEBLO") for i in range(1, 22)]
    elif case == "distinct":
        values = [reservation(i) for i in range(1, 32)]
    elif case == "duplicate":
        values = [reservation(1), reservation(1)]
    else:
        values = [reservation(1), reservation(2)]
    results = [result(i) for i in range(1, len(values) + 1)]
    if case == "unreserved":
        results = [result(3)]
    elif case == "multiple_pending":
        results = []
    with pytest.raises(ValueError):
        ActionLog(reservations=values, results=results)


def test_parser_claim_requires_actual_pdf_evidence() -> None:
    """A PDF-suffixed name or successful-looking tool note cannot fabricate an original."""
    data = result(1).model_dump(mode="json")
    data.update(pdf_parse_succeeded=True, physical_pages=1)
    with pytest.raises(ValueError):
        Result.model_validate_json(__import__("json").dumps(data))
