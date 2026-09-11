"""Strict, local-only schema for the Sherlock009 custody and acquisition audit."""
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Sha256 = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class FileRef(StrictModel):
    path: str
    sha256: Sha256
    size_bytes: int = Field(ge=0)

    @field_validator('path')
    @classmethod
    def relative_path(cls, value: str) -> str:
        p = PurePosixPath(value)
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('Audit references must stay inside the audit directory')
        return value

class CustodySummary(StrictModel):
    files: int = Field(ge=1)
    bytes: int = Field(ge=1)
    symlinks: Literal[0]
    advertised_hashes_checked: Literal[6]
    top_level_aliases_checked: Literal[5]
    nested_aliases_checked: Literal[33]
    inventory_files: Literal[51]
    inventory_bytes: Literal[19290536]
    main_tar_files: Literal[54]
    main_tar_missing_inventory_files: Literal[0]
    browser_tar_files: Literal[33]
    browser_tar_missing_inventory_files: Literal[18]
    all_originals_unchanged: Literal[True]

class AcquisitionSummary(StrictModel):
    consolidated_rows: Literal[13]
    reported_public_events: Literal[12]
    local_reread_events: Literal[1]
    distinct_public_targets: Literal[9]
    distinct_https_urls: Literal[8]
    distinct_search_queries: Literal[1]
    minimum_public_attempts_supported: Literal[13]
    exact_public_event_count: None
    exact_event_completeness_verified: Literal[False]
    max_public_events: Literal[30]
    max_distinct_targets: Literal[20]
    cap_breach_demonstrated: Literal[False]
    cap_compliance_certified: Literal[False]
    browser_http_status_verified: Literal[False]
    browser_acquisition_times_verified: Literal[False]

class SourceAssessment(StrictModel):
    priority_id: Literal['SD009-01', 'SD009-02', 'SD009-03']
    authority_id: Literal['CO-COUNTY-LARIMER']
    file: FileRef
    pages: int = Field(ge=1)
    inspected_physical_pages: list[int] = Field(min_length=1)
    claimed_requested_url: str
    claimed_final_url: str
    provenance_class: Literal[
        'received_pdf_download_claim_not_http_verified', 'browser_print_derivative'
    ]
    exact_delivered_bytes_verified: Literal[True]
    exact_publisher_original_verified: Literal[False]
    acquisition_time: None
    role: Literal['staff_recommendation', 'unsigned_extension_draft', 'board_minutes']
    metadata_notes: list[str]
    visible_source_findings: list[str]
    legal_currentness: Literal['not_verified']

    @model_validator(mode='after')
    def valid_pages(self):
        p = self.inspected_physical_pages
        if len(p) != len(set(p)) or min(p) < 1 or max(p) > self.pages:
            raise ValueError('Inspected pages must be unique and within this PDF')
        if self.priority_id == 'SD009-02' and self.provenance_class != 'browser_print_derivative':
            raise ValueError('The addendum must retain its browser-print provenance')
        return self

class Finding(StrictModel):
    id: str = Field(pattern=r'^ATLAS-SD009-[0-9]{2}$')
    disposition: Literal['accept', 'qualify', 'correct', 'gap']
    title: str
    detail: str
    evidence_paths: list[str] = Field(min_length=1)

class Excerpt(StrictModel):
    source_priority_id: Literal['SD009-01', 'SD009-02', 'SD009-03']
    physical_page: int = Field(ge=1)
    region: str
    wording: str
    qualification: str
    image: FileRef

class Audit(StrictModel):
    schema_version: Literal[1]
    assignment: Literal['geode-source-discovery-009']
    reviewed_at: datetime
    reviewer: Literal['Atlas / Codex independent intake audit']
    review_mode: Literal['candidate_aware_direct_page_and_custody_review']
    disposition: Literal['accept_custody_with_provenance_and_claim_corrections']
    legal_currentness: Literal['not_verified']
    production_changes: Literal[False]
    network_requests: Literal[0]
    comparison_commit: str = Field(pattern=r'^[0-9a-f]{40}$')
    custody: CustodySummary
    acquisition: AcquisitionSummary
    priority_records: Literal[8]
    new_pdf_artifacts: Literal[3]
    prior_resource_references: Literal[1]
    gap_placeholders: Literal[4]
    total_structural_pdf_pages: Literal[27]
    directly_inspected_full_pages: Literal[10]
    full_minutes_transcription_certified: Literal[False]
    supporting_files: list[FileRef]
    sources: list[SourceAssessment] = Field(min_length=3, max_length=3)
    findings: list[Finding]
    excerpts: list[Excerpt]
    unresolved_gaps: list[str]

    @field_validator('reviewed_at')
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Review time needs a timezone')
        return value

    @model_validator(mode='after')
    def unique_ids_and_pages(self):
        if len({s.priority_id for s in self.sources}) != 3:
            raise ValueError('Source IDs must be unique')
        if len({f.id for f in self.findings}) != len(self.findings):
            raise ValueError('Finding IDs must be unique')
        if sum(s.pages for s in self.sources) != self.total_structural_pdf_pages:
            raise ValueError('Structural page count mismatch')
        if sum(len(s.inspected_physical_pages) for s in self.sources) != 10:
            raise ValueError('Inspected-page scope mismatch')
        for e in self.excerpts:
            s = next(s for s in self.sources if s.priority_id == e.source_priority_id)
            if e.physical_page not in s.inspected_physical_pages:
                raise ValueError('Excerpt page must have been directly inspected')
        return self
