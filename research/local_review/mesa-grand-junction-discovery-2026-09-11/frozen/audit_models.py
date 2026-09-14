"""Strict research-only records for the bounded Atlas discovery package."""
from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Authority = Literal['CO-COUNTY-MESA', 'CO-MUNICIPAL-GRAND_JUNCTION']
Category = Literal['land_use_zoning', 'building_fire', 'fees', 'adopted_changes']
class Strict(BaseModel):
    """Reject undeclared record fields."""
    model_config = ConfigDict(extra='forbid')
class FileRecord(Strict):
    """Bind one immutable file to its exact bytes."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int = Field(ge=0)
class Custody(Strict):
    """Inventory this local package without claiming legal completeness."""
    schema_version: Literal[1] = 1
    task_id: Literal['atlas-mesa-grand-junction-discovery-2026-09-11']
    created_at: datetime
    legal_currentness: Literal['not_verified'] = 'not_verified'
    excludes: list[str]
    files: list[FileRecord]
class Basis(Strict):
    """Identify a retained catalog anchor or pinned registry row."""
    event_id: str | None
    input_source_ids: list[str]
    label: str
    note: str
class Legacy(Strict):
    """Separate exact attempted URLs from parent-catalog association."""
    requested_url_matches: int = Field(ge=0)
    parent_source_url_matches: int = Field(ge=0)
    requested_match_source_ids: list[str]
    parent_match_source_ids: list[str]
    known_digests_at_requested_url: list[str]
    preserved_digest_equal_records: int = Field(ge=0)
    preserved_digest_equal_source_ids: list[str]
    interpretation: str
class Priority(Strict):
    """One source resource, never an assertion of a complete authority corpus."""
    priority_id: str
    authority_id: Authority
    categories: list[Category] = Field(min_length=1)
    title: str
    url: str
    role: str
    acquisition_status: Literal['source_preserved', 'linked_unopened', 'redirect_only']
    source_event_id: str | None
    unfollowed_redirect_url: str | None = None
    basis: list[Basis] = Field(min_length=1)
    existing_registry_source_ids: list[str]
    legacy: Legacy
    date_and_scope_notes: list[str]
    gaps: list[str] = Field(min_length=1)
    legal_currentness: Literal['not_verified'] = 'not_verified'
class Cell(Strict):
    """A bounded discovery result for one requested authority/category pair."""
    authority_id: Authority
    category: Category
    priority_ids: list[str]
    supporting_event_ids: list[str]
    status: Literal['preserved_partial', 'catalog_and_leads_only']
    gap: str
    completeness: Literal['not_assessed'] = 'not_assessed'
    legal_currentness: Literal['not_verified'] = 'not_verified'
class VisualScope(Strict):
    """Record actual full-page inspection separately from structural extraction."""
    event_id: str
    source_pages: int
    full_pages_viewed: list[int]
    render_paths: list[str]
    scope: str
    observations: list[str]
class Summary(Strict):
    """Bind all finite counts to events and source preservation."""
    public_events: int = Field(le=20)
    distinct_requested_urls: int = Field(le=12)
    http_200: int
    http_301: int
    transport_failures: int
    response_body_bytes: int
    accepted_200_bytes: int
    pdf_count: int
    pdf_structural_pages: int
    full_pages_visually_checked: int
    priority_count: int = Field(le=8)
    checklist_rows: Literal[8]
class Report(Strict):
    """Research-only discovery and custody outcome for two separate authorities."""
    schema_version: Literal[1] = 1
    task_id: Literal['atlas-mesa-grand-junction-discovery-2026-09-11']
    prepared_at: datetime
    stop_at: datetime
    input_commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    initial_observed_commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    input_commit_note: str
    scope: str
    legal_currentness: Literal['not_verified'] = 'not_verified'
    completeness: Literal['not_assessed'] = 'not_assessed'
    summary: Summary
    priorities: list[Priority] = Field(max_length=8)
    checklist: list[Cell] = Field(min_length=8, max_length=8)
    pdf_review: list[VisualScope]
    findings: list[str]
    explicit_unopened_gaps: list[str]
    limitations: list[str]
    @model_validator(mode='after')
    def check_sets(self) -> Report:
        """Require eight distinct authority/category pairs and unique resource leads."""
        ids=[p.priority_id for p in self.priorities]
        if len(ids)!=len(set(ids)) or len({p.url for p in self.priorities})!=len(ids):
            raise ValueError('priority IDs and resource URLs must be unique')
        keys={(c.authority_id,c.category) for c in self.checklist}
        expected={(a,c) for a in ('CO-COUNTY-MESA','CO-MUNICIPAL-GRAND_JUNCTION')
                  for c in ('land_use_zoning','building_fire','fees','adopted_changes')}
        if keys!=expected: raise ValueError('checklist scope is incomplete or duplicated')
        ps={p.priority_id:p for p in self.priorities}
        for c in self.checklist:
            for i in c.priority_ids:
                if i not in ps or ps[i].authority_id!=c.authority_id:
                    raise ValueError('checklist priority ownership mismatch')
        if self.prepared_at.tzinfo is None or self.stop_at.tzinfo is None:
            raise ValueError('aware receipt times required')
        return self

class InputFile(Strict):
    """Bind one read-only input and its relevant-row extract."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int
    matching_rows: int
    extract_path: str
class Inputs(Strict):
    """Record the comparison commit and exact input file digests."""
    commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    observed_at: datetime
    files: list[InputFile]
    note: str
class Extract(Strict):
    """Preserve inherited parsed records without asserting their correctness."""
    input_path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    rows: list[dict]
class Page(Strict):
    """Bind exact native text from one PDF physical page."""
    physical_page: int
    native_path: str
    native_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    native_bytes: int
class PDF(Strict):
    """Preserve structural metadata independently of visual inspection."""
    event_id: str
    pdf_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    pages: int
    is_repaired: bool
    is_encrypted: bool
    metadata: dict
    native_flags: int
    native_sort: bool
    native_pages: list[Page]
class Validation(Strict):
    """Record one completed read-only validation."""
    task_id: Literal['atlas-mesa-grand-junction-discovery-2026-09-11']
    validated_at: datetime
    passed: Literal[True]
    checked_files: int
    event_count: int
    distinct_targets: int
    priority_count: int
    checklist_rows: int
    pdf_count: int
    pdf_pages: int
    viewed_pages: int
    note: str
