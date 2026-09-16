"""Strict closure receipts; no collector or repository mutation entry point."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, Field

from capture import Event, Ref, Strict
from review_models import DiscoveredLink


class AttemptLog(Strict):
    """Ordered actual outcomes, including the failed local DNS attempt."""
    status: Literal['closed_no_further_requests']
    events: list[Event] = Field(min_length=31, max_length=31)


class Backlog(Strict):
    """Observed links only; no implied official ownership or opened content."""
    status: Literal['discovered_but_unopened_not_acquired']
    links: list[DiscoveredLink]
    qualification: str


class AdditionalRender(Strict):
    """One complete physical page rendered after structural inspection."""
    event_id: str
    source: Ref
    physical_page: int
    render_dpi: Literal[150]
    render: Ref


class Baseline(Strict):
    """Exact working inputs, separately attributed from Git observations."""
    captured_at: AwareDatetime
    earlier_observed_head: str
    earlier_observation_time: AwareDatetime | None
    head_at_copy: str
    git_commands_used: Literal[False]
    working_file_commit_equality: str
    files: list[Ref]
    jsonl_row_counts: dict[str, int]
    lfs_pointers: dict[str, str]
    authority_ids: list[str]
    selected_legacy_rows: int
    selected_rows_basis: str
    notes: list[str]


class MethodPeriod(Strict):
    """The preserved helper version used for a contiguous event range."""
    first_event: str
    last_event: str
    script: Ref
    qualification: str


class MethodReceipt(Strict):
    """Provenance of helper changes and later parent-reported checkpoints."""
    recorded_at: AwareDatetime
    capture_versions: list[MethodPeriod]
    latest_parent_reported_head: str
    parent_reported_raw_rows: Literal[59]
    parent_reported_ledger_rows: Literal[60]
    limits: list[str]


class Verification(Strict):
    """Read-only replay results, not source currency certification."""
    status: Literal['passed']
    payload_files: int
    event_count: Literal[31]
    exact_requested_urls: Literal[30]
    pdf_count: Literal[8]
    physical_pages: Literal[403]
    native_pages_replayed: Literal[403]
    rendered_pages_replayed: int
    viewed_page_records: Literal[14]
    historical_rows_streamed: Literal[48390]
    legacy_matching_rows: Literal[16]
    unopened_urls: Literal[381]
    private_header_events: Literal[7]
    legal_currentness: Literal['not_verified']
    raw_size_probe: Literal['historical_local_check_not_replayed_portably']
