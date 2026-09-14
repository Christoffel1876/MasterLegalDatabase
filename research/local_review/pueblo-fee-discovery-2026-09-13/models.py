"""Strict source-discovery and immutable-custody models; no legal promotion."""
from __future__ import annotations

from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject undeclared report fields."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Exact packet-relative byte custody."""
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Limits(Strict):
    """This finite assignment's ceilings, not observed counts."""
    maximum_events: Literal[12]
    maximum_distinct_urls: Literal[10]
    maximum_source_bytes: Literal[5000000]
    maximum_total_body_bytes: Literal[12000000]
    maximum_request_seconds: Literal[30]
    hard_stop: AwareDatetime


class DateClaim(Strict):
    """Keep printed or file-metadata dates distinct from legal dates."""
    text: str
    basis: Literal["printed_footer", "content_disposition", "pdf_metadata", "old_url_slug"]
    physical_pages: list[int]
    qualification: str


class Source(Strict):
    """One observed city fee source; not a canonical intake or full numeric review."""
    source_id: Literal["PUEBLO-FEE-01"]
    authority_id: Literal["CO-MUNICIPAL-PUEBLO"]
    authority_name: Literal["City of Pueblo"]
    source_role: Literal["official_city_planning_fee_schedule"]
    title: str
    official_parent: Ref
    parent_url: str
    anchor_label: str
    anchor_href: str
    requested_url: str
    final_url: str
    event_ids: list[str]
    original: Ref
    physical_pages: Literal[4]
    native_bytes: Literal[4923]
    native_extraction_scope: Literal["all_four_pages_uncorrected"]
    directly_viewed_pages: list[int]
    rendered_pages: list[int]
    date_claims: list[DateClaim]
    review_notes: list[str]
    adoption_date: None
    effective_date: None
    legal_currentness: Literal["not_verified"]
    full_table_qa: Literal[False]
    answer_safe: Literal[False]

    @model_validator(mode="after")
    def bounded(self) -> Source:
        """Do not let this limited discovery be relabeled as a complete visual review."""
        if self.directly_viewed_pages != [1, 4] or self.rendered_pages != [1, 4]:
            raise ValueError("Only first and last pages belong to this discovery visual scope")
        return self


class Gap(Strict):
    """A failed or intentionally unopened part of the assignment."""
    authority_id: Literal["CO-COUNTY-PUEBLO", "CO-MUNICIPAL-PUEBLO"]
    status: Literal["blocked_http_403", "unverified_reported_lead", "unopened", "not_assessed"]
    url: str | None
    detail: str


class Report(Strict):
    """Finite acquisition results and their explicit limits."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal["complete_bounded_discovery_with_county_gap"]
    limits: Limits
    events: int = Field(ge=0, le=12)
    distinct_urls: int = Field(ge=0, le=10)
    retained_body_bytes: int = Field(ge=0, le=12000000)
    http_responses: int
    local_transport_failures: int
    pdfs_preserved: Literal[1]
    sources: list[Source] = Field(min_length=1, max_length=1)
    gaps: list[Gap] = Field(min_length=2)
    acquisition_notes: list[str]
    comparison: Ref
    comparison_limits: list[str]
    privacy: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    canonical_changes: Literal[False]


class Manifest(Strict):
    """Closed immutable file inventory for portable offline validation."""
    schema_version: Literal[1]
    files: list[Ref]
    legal_currentness: Literal["not_verified"]

    @model_validator(mode="after")
    def unique(self) -> Manifest:
        """Reject duplicate custody members."""
        names = [r.path for r in self.files]
        if len(names) != len(set(names)) or names != sorted(names):
            raise ValueError("Inventory must be unique and sorted")
        return self
