"""Strict custody and bounded-access facts; no enacted-law conclusion."""
from __future__ import annotations
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

class Input(Strict):
    original_path: str
    captured_at: AwareDatetime
    evidence_role: Literal["prior_atlas_audit", "prior_external_claims", "prior_page_snapshot", "prior_access_audit"]
    copy: Asset

class Action(Strict):
    event_id: str
    tool: Literal["curl_direct_https", "web_open", "web_search", "web_click"]
    requested_url: str | None
    query: str | None = None
    search_domains: list[str] = Field(default_factory=list)
    request_window_start: AwareDatetime
    request_window_end: AwareDatetime
    time_precision: Literal["direct_microsecond_receipt", "tool_call_whole_second_window"]
    result_asset: Asset
    outcome: Literal["dns_failure_no_http", "tool_text_derivative", "empty_search_result", "tool_preflight_nonretryable_error"]
    observed_final_url: str | None = None
    redirect_target_reported: str | None = None
    publisher_http_status: None = None
    original_publisher_body_received: Literal[False] = False
    cached_crawl_label: str | None = None
    limitation: str

    @model_validator(mode="after")
    def checks(self):
        if self.request_window_end < self.request_window_start:
            raise ValueError("Time window is reversed")
        if (self.requested_url is None) == (self.query is None):
            raise ValueError("Exactly one requested URL or search query is required")
        if self.tool == "web_search" and (self.query is None or not self.search_domains):
            raise ValueError("Search requires its exact query and domain restriction")
        return self

class Support(Strict):
    asset_path: str
    locator: str
    excerpt: str = Field(min_length=1)

class Finding(Strict):
    finding_id: str
    classification: Literal["fresh_tool_observation", "prior_audit_fact", "unresolved"]
    statement: str
    evidence: list[Support] = Field(min_length=1)

class Audit(Strict):
    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    authority_id: Literal["CO-COUNTY-LARIMER"] = "CO-COUNTY-LARIMER"
    status: Literal["bounded_attempt_complete_unresolved"] = "bounded_attempt_complete_unresolved"
    legal_currentness: Literal["not_verified"] = "not_verified"
    scope: str
    actions: list[Action] = Field(min_length=8, max_length=8)
    requested_action_count: Literal[8] = 8
    reported_redirect_count: Literal[1] = 1
    conservative_observed_action_plus_redirect_count: Literal[9] = 9
    distinct_requested_urls: list[str] = Field(min_length=4, max_length=4)
    distinct_requested_and_reported_final_urls: list[str] = Field(min_length=5, max_length=5)
    distinct_search_queries: list[str] = Field(min_length=2, max_length=2)
    conservative_url_and_query_target_count: Literal[7] = 7
    exact_underlying_http_request_count: None = None
    publisher_originals_acquired: Literal[0] = 0
    pdfs_acquired: Literal[0] = 0
    new_pdf_pages_visually_reviewed: Literal[0] = 0
    public_access_stopped_at: AwareDatetime
    public_cutoff: AwareDatetime
    inputs: list[Input]
    findings: list[Finding]
    unresolved: list[str]
    limitations: list[str]
    acceptance_or_registration_performed: Literal[False] = False
    external_messages_sent: Literal[False] = False
    canonical_files_changed: Literal[False] = False

    @model_validator(mode="after")
    def totals(self):
        if len({a.event_id for a in self.actions}) != 8:
            raise ValueError("Eight unique requested actions required")
        urls = {a.requested_url for a in self.actions if a.requested_url}
        final = urls | {a.observed_final_url for a in self.actions if a.observed_final_url}
        queries = {a.query for a in self.actions if a.query}
        if sorted(urls) != self.distinct_requested_urls or sorted(final) != self.distinct_requested_and_reported_final_urls:
            raise ValueError("URL counts disagree with actual actions")
        if sorted(queries) != self.distinct_search_queries:
            raise ValueError("Query counts disagree with actual actions")
        if self.public_access_stopped_at > self.public_cutoff:
            raise ValueError("Public access exceeded deadline")
        if any(a.request_window_end > self.public_access_stopped_at for a in self.actions):
            raise ValueError("Action occurs after recorded stop")
        return self

class Manifest(Strict):
    schema_version: Literal[1] = 1
    created_at: AwareDatetime
    status: Literal["frozen_bounded_unresolved_evidence"] = "frozen_bounded_unresolved_evidence"
    files: list[Asset]
    excluded: Literal["FINAL_MANIFEST.json; FINAL_MANIFEST.schema.json"] = "FINAL_MANIFEST.json; FINAL_MANIFEST.schema.json"

