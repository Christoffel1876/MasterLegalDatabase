"""Typed records for the bounded Arapahoe adopting-instrument access check."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Input(Strict):
    historical_path: str
    preserved_copy: Asset
    purpose: str


class Event(Strict):
    event_id: str
    requested_url: str
    kind: Literal['web_tool_open', 'web_tool_click', 'reported_redirect', 'ordinary_http_get']
    parent_event: str | None
    observed_link_label: str | None
    referral_evidence: str
    result: str
    output_assets: list[Asset]
    raw_http_status: int | None
    started_at: datetime | None
    completed_at: datetime | None
    tool_crawl_label: str | None
    qualification: str


class Excerpt(Strict):
    excerpt_id: str
    physical_page: int = Field(ge=1, le=2)
    source_sha256: str = Field(pattern='^[a-f0-9]{64}$')
    native: Asset
    image: Asset
    start_byte: int = Field(ge=0)
    end_byte_exclusive: int = Field(gt=0)
    exact_native: str
    observation: str
    limit: str

    @model_validator(mode='after')
    def byte_length(self):
        if len(self.exact_native.encode()) != self.end_byte_exclusive-self.start_byte:
            raise ValueError('native span length differs')
        return self


class DateRole(Strict):
    literal: str
    role: str
    source_event_or_excerpt: str
    qualification: str


class Audit(Strict):
    audit_id: Literal['ARAPAHOE-RESOLUTION-26-224-ACCESS-2026-09-11']
    completed_at: datetime
    deadline: datetime
    stop_reason: Literal['eight_counted_public_events_reached']
    public_events_counted: Literal[8]
    distinct_observed_targets: list[str] = Field(min_length=6, max_length=6)
    event_counting_limit: str
    events: list[Event] = Field(min_length=8, max_length=8)
    retained_inputs: list[Input]
    subject_fee_source: Asset
    subject_fee_source_id: Literal['arapahoe-planning-fees-sd002-14']
    related_resolution_response: Asset
    related_resolution_pdf_copy: Asset
    related_resolution_pages: Literal[2]
    related_resolution_sha256: Literal['8f1e94f6332fc9c36ee479f4673e2f85a533b2b777f29cbfc9757c2adcd41e6c']
    related_resolution_status: Literal['unnumbered_unfilled_resolution_attachment']
    physical_pages_directly_viewed: list[int]
    extraction_settings: str
    rendering_settings: str
    excerpts: list[Excerpt]
    date_roles: list[DateRole]
    confirmed_resolution_26_224_identity: Literal[False]
    confirmed_adoption_date: None
    confirmed_effective_date: None
    final_minutes_preserved: Literal[False]
    legal_currentness: Literal['not_verified']
    repository_or_packet_changed: Literal[False]
    external_assignment: None
    findings: list[str]
    unresolved: list[str]
    limitations: list[str]

    @model_validator(mode='after')
    def scope(self):
        if [e.event_id for e in self.events] != [f'E{i:03d}' for i in range(1,9)]:
            raise ValueError('event order/count differs')
        if set(e.requested_url for e in self.events) != set(self.distinct_observed_targets):
            raise ValueError('target count differs')
        if self.completed_at > self.deadline:
            raise ValueError('task completed after deadline')
        if self.physical_pages_directly_viewed != [1,2]:
            raise ValueError('page coverage differs')
        return self


class Inventory(Strict):
    files: list[Asset]
    excluded_self: Literal['evidence-manifest.json']
