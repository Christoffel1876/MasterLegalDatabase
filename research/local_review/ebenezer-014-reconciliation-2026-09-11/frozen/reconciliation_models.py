"""Strict source-bound reconciliation of the external EB014 reports."""
from collections import Counter
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class FileRef(Strict):
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)

    @field_validator('path')
    @classmethod
    def safe(cls, value):
        p = PurePosixPath(value)
        if (p.is_absolute() or '..' in p.parts or '\\' in value or ':' in value
                or p.as_posix() != value or value == '.'):
            raise ValueError('Canonical relative audit paths only')
        return value

class Decision(Strict):
    id: str
    kind: Literal['external_finding', 'external_erratum', 'unresolved_theme']
    disposition: Literal['accepted', 'qualified', 'rejected', 'source_observation']
    external_report: Literal['PASS2_REVIEW.md']
    external_line: int = Field(ge=1)
    external_claim: str
    physical_pages: list[int] = Field(min_length=1)
    page_images: list[FileRef] = Field(min_length=1)
    atlas_observation_ids: list[str]
    source_observation: str
    qualification: str
    native_text_change_required: Literal[False]
    legal_currentness: Literal['not_verified']

    @model_validator(mode='after')
    def valid_pages(self):
        if self.physical_pages != sorted(set(self.physical_pages)):
            raise ValueError('Sorted unique pages required')
        if min(self.physical_pages) < 1 or max(self.physical_pages) > 7:
            raise ValueError('Page outside source')
        if len(self.page_images) != len(self.physical_pages):
            raise ValueError('Missing full-page evidence')
        return self

class Counts(Strict):
    finding_rows: Literal[21]
    critical: Literal[2]
    minor: Literal[12]
    info: Literal[7]
    errata_rows: Literal[3]
    unresolved_themes: Literal[5]
    arithmetic_matches: Literal[True]
    unique_error_count_certified: Literal[False]

class Reconciliation(Strict):
    schema_version: Literal[1]
    assignment: Literal['EB-PDF-014']
    source_id: Literal['fort-collins-land-use-article-1-sd005-07']
    authority_id: Literal['CO-MUNICIPAL-FORT_COLLINS']
    reviewed_at: datetime
    comparison_commit: str = Field(pattern=r'^[0-9a-f]{40}$')
    status: Literal['reconciled_with_qualifications_no_source_changes']
    review_mode: Literal['candidate_aware_direct_image_review_with_native_support']
    physical_pages_directly_inspected: list[int]
    directly_inspected_crops: list[FileRef] = Field(min_length=11, max_length=11)
    source_pdf: FileRef
    native_candidate: FileRef
    committed_review: FileRef
    receipts: list[FileRef]
    supplemental_evidence: list[FileRef]
    external_counts: Counts
    decisions: list[Decision] = Field(min_length=29, max_length=29)
    disposition_counts: dict[str, int]
    method_and_limits: list[str]
    original_source_and_candidate_changed: Literal[False]
    external_reports_changed: Literal[False]
    production_changes: Literal[False]
    network_requests: Literal[0]
    legal_currentness: Literal['not_verified']

    @field_validator('reviewed_at')
    @classmethod
    def aware(cls, value):
        if value.utcoffset() is None:
            raise ValueError('Timezone required')
        return value

    @model_validator(mode='after')
    def complete(self):
        if self.physical_pages_directly_inspected != list(range(1, 8)):
            raise ValueError('All seven pages must be inspected')
        expected = {
            'external_finding': {f'EB014-P2-{i:03}' for i in range(1, 22)},
            'external_erratum': {f'E{i}' for i in range(1, 4)},
            'unresolved_theme': {f'U{i}' for i in range(1, 6)},
        }
        ids = [x.id for x in self.decisions]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate decision')
        for kind, values in expected.items():
            if {x.id for x in self.decisions if x.kind == kind} != values:
                raise ValueError('Missing or unexpected decision')
        if dict(Counter(x.disposition for x in self.decisions)) != self.disposition_counts:
            raise ValueError('Count mismatch')
        return self

class FontSpan(Strict):
    physical_page: int = Field(ge=1, le=7)
    text: str
    font: str
    flags: int
    bbox: list[float] = Field(min_length=4, max_length=4)

class SourceSupport(Strict):
    source_pdf: FileRef
    pymupdf_version: Literal['1.28.2']
    selected_font_spans: list[FontSpan]
    page2_uri_annotations: list[dict[str, str | int | list[float]]]
    purpose: str
    network_requests: Literal[0]
    legal_currentness: Literal['not_verified']

class FinalManifest(Strict):
    frozen_at: datetime
    files: list[FileRef]
    file_count: int
    legal_currentness: Literal['not_verified']

    @model_validator(mode='after')
    def count(self):
        if len(self.files) != self.file_count or len({f.path for f in self.files}) != self.file_count:
            raise ValueError('Final file inventory mismatch')
        return self
