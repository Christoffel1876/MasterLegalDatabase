"""Strict custody audit records; source-content and current-law review are outside this scope."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undeclared fields and scalar coercion."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Bind exact local evidence bytes."""

    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Event(Strict):
    """Separate reported transport observations from independently checked retained bytes."""

    action_id: str
    authority_id: Literal['CO-COUNTY-PUEBLO']
    requested_url: str
    reported_final_url: str
    reported_reserved_at: AwareDatetime
    reported_finished_at: AwareDatetime
    reported_http_status: int
    reported_visible_redirects: list[str]
    retained_role: Literal['received_pdf', 'received_access_denial_html']
    body: Asset
    byte_identical_duplicate: Asset
    reservation: Asset
    result: Asset
    headers: Asset
    structural_pdf_pages: int | None
    pdf_encrypted: bool | None
    pdf_repaired: bool | None
    terminal_pdf_eof_present: bool | None
    html_title: str | None
    observed_header_names: list[str]
    private_header_names_detected: list[str]
    headers_and_result_byte_counts_match: bool
    notes: list[str]


class Referral(Strict):
    """An exact retained rendered-DOM anchor, not an authenticated raw HTTP response."""

    authority_id: Literal['CO-COUNTY-PUEBLO']
    parent_url: str
    parent: Asset
    parent_role: Literal['retained_browser_rendered_dom']
    parent_title: str
    parent_h1: list[str]
    exact_href: str
    exact_label: str
    resolved_url: str
    anchor_match_count: int
    target_role: Literal['fee_schedule_link', 'commissioner_catalog_lead']
    limitations: list[str]


class LegacyComparison(Strict):
    """A complete streamed metadata comparison, with no implied original-byte availability."""

    edition: Literal['pinned_commit', 'working_tree']
    pinned_commit: str | None
    repository_path: str
    full_file_sha256: str
    full_file_bytes: int
    full_rows: int
    compared_urls: list[str]
    compared_sha256s: list[str]
    exact_url_field_matches: int
    digest_matches: int
    decoded_url_matches: int
    proposed_id_matches: int
    matching_original_lines: Asset
    original_line_numbers: list[int]
    full_stream_included: Literal[False]
    actual_historical_original_bytes_compared: Literal[False]
    limitations: list[str]


class CurrentIntakeComparison(Strict):
    """A full current manual-manifest/ledger scan at the audit time."""

    repository_path: str
    file: Asset
    rows: int
    sha256_matches: int
    exact_url_matches: int
    proposed_id_matches: int
    proposed_source_id: str
    captured_at: AwareDatetime


class Finding(Strict):
    """A bounded observation with supporting retained inputs and explicit limits."""

    finding_id: str
    disposition: Literal['verified', 'qualified', 'intake_eligible_with_conditions']
    statement: str
    evidence: list[str]
    limits: list[str]


class Audit(Strict):
    """Independent custody verification, not PDF fee-table or legal-currentness certification."""

    assignment_id: Literal['SH-EXT-002']
    status: Literal['custody_verified_with_qualifications_pending_intake']
    audited_at: AwareDatetime
    delivery_captured_at: AwareDatetime
    authorization: Asset
    directed_proposal: Asset
    parent_manifest: Asset
    events: list[Event]
    referrals: list[Referral]
    legacy: list[LegacyComparison]
    current_intake: list[CurrentIntakeComparison]
    findings: list[Finding]
    inventory_listed_files: Literal[25]
    inventory_claims_verified: Literal[True]
    actual_delivery_files: Literal[27]
    unlisted_delivery_files: list[str]
    independent_distinct_response_bodies: Literal[2]
    retained_response_body_bytes: Literal[81082]
    declared_actions: Literal[2]
    declared_distinct_urls: Literal[2]
    declared_visible_redirects: Literal[0]
    recorded_serial_order_consistent: Literal[True]
    reported_research_completed_before_cutoff: Literal[True]
    delivery_bytes_captured_before_report_cutoff: Literal[True]
    hidden_network_requests_measured: Literal[False]
    transport_command_retained: Literal[False]
    independent_source_visual_pages: Literal[0]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    public_requests_by_auditor: Literal[0]
    canonical_intakes_by_auditor: Literal[0]


class IntakeRecommendation(Strict):
    """A proposal only; actual receipt time and archive filename await an approved transaction."""

    status: Literal['proposed_not_applied']
    source_id: str
    authority_id: Literal['CO-COUNTY-PUEBLO']
    layer_id: Literal['08_County_Authorities']
    incoming_source: Asset
    original_filename: str
    official_source_url: str
    official_source_name: str
    acquisition_method: Literal['received_review_package']
    actual_future_received_at: None
    archive_path: None
    original_acquisition_time: None
    reported_acquisition_interval: list[str]
    required_final_status: Literal['archived_pending_pipeline']
    expected_canonical_pdf_count: Literal[1]
    legal_currentness: Literal['not_verified']
    prerequisites: list[str]
    exclusions: list[str]


class Manifest(Strict):
    """Closed portable audit payload membership."""

    status: Literal['frozen']
    files: list[Asset]
