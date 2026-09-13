"""Strict evidence contracts for an offline, bounded delivery audit."""
from __future__ import annotations
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    """Reject unexpected fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

class CustodyItem(Strict):
    original: Asset
    retained: Asset
    mode: Literal['exact', 'set_cookie_redacted']
    redacted_lines: list[int]

class Custody(Strict):
    captured_at: AwareDatetime
    original_delivery: str
    supplied_inventory_entries: int
    supplied_inventory_mismatches: list[str]
    unlisted_original_files: list[str]
    items: list[CustodyItem]
    scope: str

class Match(Strict):
    line: int
    raw_line_sha256: str
    source_id: str
    requested_url: str | None
    source_url: str | None
    recorded_sha256: str | None
    recorded_raw_path: str | None
    reasons: list[str]
    mapped_repository_path: str | None
    mapped_path_state: Literal['not_checked', 'missing', 'ordinary_present', 'nonordinary']
    available_sha256: str | None

class Legacy(Strict):
    current_commit_observed: str
    pinned_commit: str
    stream: Asset
    pinned_stream_sha256: str
    current_rows: int
    pinned_rows: int
    identical_streams: bool
    matching_rows: list[Match]
    comparison_scope: str
    limitations: list[str]

class Referral(Strict):
    action_id: str
    parent_action_id: str
    parent: Asset
    parent_url: str
    original_href: str
    html_base_href: str | None
    visible_label: str
    resolved_url: str
    attempted_url: str
    exact_browser_resolution_match: bool

class PDF(Strict):
    action_id: str
    source: Asset
    authority_id: Literal['CO-COUNTY-GUNNISON']
    physical_pages: int
    is_repaired: bool
    encrypted: bool
    terminal_eof: bool
    first_page_image: Asset
    render_command: list[str]
    reviewed_pages: list[int]
    role_observations: list[str]
    historical_digest_lines: list[int]
    historical_exact_request_lines: list[int]
    canonical_manual_digest_lines: list[int]
    limitations: list[str]

class Budget(Strict):
    actions: int
    distinct_urls: int
    chaffee_actions: int
    gunnison_actions: int
    accepted_body_bytes: int
    maximum_body_bytes: int
    response_bodies: int
    no_body_results: int
    first_reservation: str
    last_result: str
    serial_nonoverlap: bool
    pending_actions: int
    actual_reservation31: Literal[False]
    rejected_next_input: Asset
    rejected_next_log: Asset
    stale_status_actions: int
    command_log_actions: int
    hidden_wire_requests_measured: Literal[False]

class Finding(Strict):
    finding_id: str
    severity: Literal['qualification', 'correction', 'gap']
    statement: str
    evidence: list[str]

class Audit(Strict):
    assignment_id: Literal['SH-EXT-003']
    prepared_packet_manifest_sha256: str
    actual_dispatch_claim: str
    worker_timing_claims_independently_witnessed: Literal[False]
    measured_local_audit_at: AwareDatetime
    budget: Budget
    referrals: list[Referral]
    pdfs: list[PDF]
    findings: list[Finding]
    legal_currentness: Literal['not_verified']
    public_requests_by_audit: Literal[0]
    source_review_scope: Literal['first physical page of each of three PDFs; 3 of 23 pages']

class Manifest(Strict):
    status: Literal['FROZEN_OFFLINE_AUDIT']
    files: list[Asset]
    public_requests: Literal[0]

class Validation(Strict):
    status: Literal['passed']
    checks: list[str]
    public_requests: Literal[0]

class IntakeCandidate(Strict):
    action_id: str
    authority_id: Literal['CO-COUNTY-GUNNISON']
    layer_id: Literal['08_County_Authorities']
    source: Asset
    received_document_role: str
    supplied_requested_url: str
    proposed_acquisition_method: Literal['received_review_package']
    proposed_official_source_url: None
    canonical_manual_digest_matches: list[int]
    historical_digest_matches: list[int]
    required_preflight: list[str]

class IntakeRecommendation(Strict):
    status: Literal['PROPOSAL_ONLY_NOT_APPLIED']
    candidates: list[IntakeCandidate]
    canonical_writes_by_audit: Literal[0]
    legal_currentness: Literal['not_verified']
