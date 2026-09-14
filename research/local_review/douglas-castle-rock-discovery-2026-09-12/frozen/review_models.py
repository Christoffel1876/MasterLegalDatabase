"""Strict discovery, referral, comparison and qualified-intake records."""
from __future__ import annotations
from typing import Literal
from pydantic import AwareDatetime, Field
from capture import Strict, Ref

Authority = Literal['CO-COUNTY-DOUGLAS', 'CO-MUNICIPAL-CASTLE_ROCK']
Category = Literal['identity_service_area', 'codified_rules', 'adopted_changes',
                   'land_use_zoning', 'building_fire', 'permits_licenses', 'fees', 'taxes',
                   'health_environment', 'roads_utilities', 'enforcement_appeals',
                   'policies_guidance']

class Referral(Strict):
    """One source-opening justification, with no inferred file-name route."""
    event_id: str
    type: Literal['registry_seed', 'anchor', 'redirect', 'dns_route_retry']
    parent_event: str | None
    seed_source_id: str | None

class Snippet(Strict):
    """Exact derived-text bytes traceable to the retained original."""
    original: Ref
    text_file: Ref
    physical_page: int | None
    start_byte: int
    end_byte: int
    text: str
    text_sha256: str
    method: Literal['unaltered native PDF extraction', 'HTML text derivative']

class Statement(Strict):
    """A source statement or anomaly, not an adopted-effect conclusion."""
    kind: str
    value: str
    evidence: Snippet
    qualification: str

class Priority(Strict):
    """Exactly one pending source resource; successful response is separate from law text."""
    priority_id: str = Field(pattern=r'^DCR-(0[1-9]|1[0-2])$')
    authority_id: Authority
    title: str
    event_id: str
    url: str
    body: Ref
    evidence_role: str
    substantive_text_retained: bool
    pdf_pages: int | None
    categories: list[Category]
    source_statements: list[Statement]
    limits: list[str]
    intake_status: Literal['pending_root_verification'] = 'pending_root_verification'
    legal_currentness: Literal['not_verified'] = 'not_verified'
    verified_adoption_date: None = None
    verified_effective_date: None = None

class ChecklistRow(Strict):
    """Category discovery status, never a complete law-coverage claim."""
    authority_id: Authority
    category: Category
    status: Literal['candidate_found', 'searched_not_found', 'access_blocked', 'not_searched']
    event_ids: list[str]
    evidence_role: str
    substantive_text_retained: bool
    qualification: str
    legal_currentness: Literal['not_verified'] = 'not_verified'

class LinkObservation(Strict):
    """A discovered source anchor's exact retained position."""
    event_id: str
    anchor_index_zero_based: int
    href: str
    label: str

class DiscoveredLink(Strict):
    """Distinct discovered URL and actual opened/unopened disposition."""
    url: str
    observations: list[LinkObservation]
    event_ids_opened: list[str]
    disposition: Literal['opened', 'unopened', 'not_public_https_source_target']
    reason: str

class LegacyMatch(Strict):
    """One exact full-manifest line matching a current request or body digest."""
    line_number: int
    line_sha256: str
    source_id: str | None
    authority_id: str | None
    source_url: str | None
    requested_url: str | None
    final_url: str | None
    historical_sha256: str | None
    matching_event_ids: list[str]
    match_fields: list[str]
    historical_raw_path_claim: str | None

class RawSizeCandidate(Strict):
    """Actual locally present raw bytes checked by matching size, not a path guess."""
    repository_relative_path: str
    sha256: str
    bytes: int
    identical_event_ids: list[str]

class Comparison(Strict):
    """Full-stream baseline comparisons and bounded local raw digest checks."""
    recorded_at: AwareDatetime
    legacy_manifest: Ref
    streamed_rows: Literal[48390]
    authority_selected_rows: Literal[33]
    matches: list[LegacyMatch]
    actual_raw_size_candidates: list[RawSizeCandidate]
    absent_pdf_legacy_digest_matches: list[str]
    limits: list[str]

class ViewedPage(Strict):
    """A complete rendered physical page inspected during this discovery."""
    event_id: str
    physical_page: int
    source: Ref
    image: Ref
    render_dpi: Literal[150]
    scope: Literal['source identity/date/layout sampling; not complete transcription review']

class Discovery(Strict):
    """Finite completed discovery with unresolved source and legal-status gaps."""
    recorded_at: AwareDatetime
    status: Literal['completed_pending_root_verification']
    legal_currentness: Literal['not_verified']
    event_count: Literal[31]
    distinct_exact_requested_urls: Literal[30]
    http_response_count: int
    http_status_counts: dict[str, int]
    transport_failures: Literal[1]
    automatic_redirects_followed: Literal[0]
    public_started_at: AwareDatetime
    public_finished_at: AwareDatetime
    stopped_below_cap: Literal[True]
    public_limits: str
    retained_response_bytes: int
    genuine_pdf_count: Literal[8]
    total_pdf_physical_pages: Literal[403]
    pdf_native_status: Literal['machine_native_text_unreviewed']
    referrals: list[Referral] = Field(min_length=31, max_length=31)
    priorities: list[Priority] = Field(min_length=12, max_length=12)
    checklist: list[ChecklistRow] = Field(min_length=24, max_length=24)
    discovered_links: list[DiscoveredLink]
    viewed_pages: list[ViewedPage]
    remaining_gaps: list[str]
    no_canonical_edits: Literal[True]
    no_git_commands: Literal[True]
    no_external_messages_or_forms: Literal[True]

class InventoryItem(Ref):
    """Closed custody with raw response headers explicitly local only."""
    visibility: Literal['ordinary_evidence', 'local_only_private_headers']

class Manifest(Strict):
    """All files except the manifest itself, with exact private-header labeling."""
    status: Literal['closed_local_discovery_pending_root_verification']
    assets: list[InventoryItem]
