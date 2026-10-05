"""Strict bounded chain audit with received and root-run custody separated."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject scalar coercion and unknown fields."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Identify an exact byte sequence."""

    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Evidence(Strict):
    """Original identity and retained exact copy or declared public derivative."""

    original: Asset
    retained: Asset
    mode: Literal['exact', 'public_derivative']
    transformation: str


class Link(Strict):
    """Observed catalog or parent anchor, not an adopted-law finding."""

    parent_path: str
    parent_sha256: str
    raw_href: str
    resolved_url: str
    anchor_text: str
    row_text: str


class Source(Strict):
    """First-two-page identity check with remaining pages explicitly unread."""

    source_key: str
    source: Asset
    receipt: Asset
    requested_url: str
    root_recorded_started_at: str
    root_recorded_completed_at: str
    http_status: Literal[200]
    curl_exit_code: Literal[0]
    redirects: Literal[0]
    reported_ssl_verify_result: Literal[0]
    physical_pages: int
    native_characters_all_pages: Literal[0]
    visually_inspected_pages: list[int]
    unread_pages: list[int]
    inspected_images: list[Asset]
    printed_execution_date: str
    printed_recording_date: str
    reception_number: str
    identity_observation: str
    signature_qualification: str
    adoption_currentness_inferred: Literal[False] = False


class Counts(Strict):
    """Recount of the supplied completed run, not a transport guard warranty."""

    events: int
    distinct_urls: int
    retained_response_bytes: int
    maximum_response_bytes: int
    action_limit: Literal[30] = 30
    distinct_url_limit: Literal[20] = 20
    total_byte_limit: Literal[30000000] = 30000000
    response_byte_limit: Literal[10000000] = 10000000
    redirects: int
    http_200: int
    curl_exit_zero: int
    delivered_payloads: int
    inventory_listed_payloads: int
    valid_inventory_entries: int
    valid_checksums: int
    deliberate_exclusions: list[str]
    first_request_start_claim: str
    last_request_end_claim: str
    reservation_replay: Literal['pass']
    shared_log_fields_replay: Literal['pass']


class Audit(Strict):
    """Finite offline audit; no chain completeness or current-law promotion."""

    schema_version: Literal[1] = 1
    prepared_at: str
    scope: str
    packet: Asset
    sherlock_inventory: Asset
    evidence: list[Evidence]
    counts: Counts
    anchored_event_ids: list[str]
    search_actions: list[str]
    catalog_links: list[Link]
    amended_label_occurrences: Literal[0]
    amended_reception_occurrences: Literal[0]
    ordinary_25_291_occurrences: Literal[1]
    sources: list[Source]
    findings: list[str]
    limitations: list[str]
    sherlock_followup_sent: Literal[False] = False
    sherlock_status_basis: Literal['parent_reports_last_observed_standing_down']
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    canonical_changed: Literal[False] = False
    public_actions_by_auditor: Literal[0] = 0


class Manifest(Strict):
    """Public audit closure; raw omitted header/metadata values are not included."""

    files: list[Asset]
    exclusions: list[str]
