"""Typed offline handoff custody and reproducible preparation results."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, Field

from watch import g


class Example(g.Strict):
    """A closed injected-HTTP example, never an actual publisher check."""
    name: str
    manifest: g.Ref
    report: g.Ref
    expected_statuses: list[str]
    public_requests_made: Literal[0] = 0


class Preparation(g.Strict):
    """The handoff's exact plan, code, evidence subset and offline-test outcome."""
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_DISPATCHED']
    plan: g.Ref
    implementation: g.Ref
    reused_guard: g.Ref
    tests: g.Ref
    test_log: g.Ref
    test_exit_code: Literal[0]
    focused_tests_passed: Literal[71]
    focused_coverage_percent: float = Field(ge=90, le=100)
    coverage_basis: Literal['new watch.py statements and branches; reused frozen guard excluded']
    coverage_summary: dict[str, int | float | str]
    original_source_package: str
    copied_source_subset: list[g.Ref]
    original_packet_completely_copied: Literal[False]
    examples: list[Example]
    public_requests_made: Literal[0]
    scheduler_installed: Literal[False]
    canonical_updates: Literal[False]
    legal_currentness: Literal['not_verified']
    limitations: list[str]


class Check(g.Strict):
    """Portable closure checks, explicitly excluding source access."""
    status: Literal['passed']
    prototype_files: int
    copied_custody_files: Literal[21]
    sources: Literal[2]
    pdf_baseline_pages: Literal[14]
    offline_examples: Literal[3]
    offline_example_request_events: Literal[5]
    public_requests_made_by_verifier: Literal[0]
    legal_currentness: Literal['not_verified']
