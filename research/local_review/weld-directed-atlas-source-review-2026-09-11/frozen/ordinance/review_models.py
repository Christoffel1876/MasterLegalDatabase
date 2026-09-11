"""Typed five-page Weld ordinance source QA without legal-currentness promotion."""
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)
    @field_validator('path')
    @classmethod
    def confined(cls, value: str) -> str:
        p = PurePosixPath(value)
        if p.is_absolute() or '..' in p.parts or '\\' in value or p.as_posix() != value:
            raise ValueError('Confined relative path required')
        return value

class Span(Strict):
    start_byte: int = Field(ge=0)
    end_byte_exclusive: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    @model_validator(mode='after')
    def bytes_match(self) -> Span:
        raw=self.text.encode()
        if len(raw)!=self.end_byte_exclusive-self.start_byte or sha256(raw).hexdigest()!=self.sha256:
            raise ValueError('Span identity differs')
        return self

class Page(Strict):
    physical_page: int = Field(ge=1,le=5)
    primary_image: Asset
    primary_rendering: Literal['Poppler pdftoppm 26.05.0, 150 dpi, PNG']
    secondary_image: Asset | None
    secondary_rendering: str | None
    native_file: Asset
    native_text: str
    native_sha256: str
    printed_header: str | None
    primary_footer_visible: bool
    secondary_footer_visible: bool | None
    full_page_visually_checked: Literal[True]
    @model_validator(mode='after')
    def native_identity(self) -> Page:
        raw=self.native_text.encode()
        if sha256(raw).hexdigest()!=self.native_sha256 or self.native_file.sha256!=self.native_sha256 or len(raw)!=self.native_file.size_bytes:
            raise ValueError('Native byte identity differs')
        return self

class Observation(Strict):
    id: str
    physical_page: int = Field(ge=1,le=5)
    kind: Literal['wording','source_role','source_anomaly','image_only','rendering_limit']
    region: str
    native_span: Span | None
    source_image: Asset
    finding: str
    limits: str
    changes_native_text: Literal[False]
    legal_currentness: Literal['not_verified']
    @model_validator(mode='after')
    def evidence(self) -> Observation:
        if self.kind not in ('image_only','rendering_limit') and self.native_span is None:
            raise ValueError('Native-bound observation required')
        return self

class SourceDate(Strict):
    role: str
    stated_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    physical_page: int = Field(ge=1,le=5)
    span: Span
    legal_event_independently_verified: Literal[False]

class Crop(Strict):
    id: str
    physical_page: int = Field(ge=1,le=5)
    file: Asset
    method: Literal['pymupdf_300dpi_pdf_clip','pillow_primary_png_crop']
    rect: list[int] = Field(min_length=4,max_length=4)
    inspected: Literal[True]

class Review(Strict):
    schema_version: Literal[1]
    reviewed_at: datetime
    source_id: Literal['weld-ordinance26-01']
    authority_id: Literal['CO-COUNTY-WELD']
    source: Asset
    source_role: Literal['adopted_amendment_instrument_as_stated_in_source']
    document_scope: str
    review_mode: Literal['candidate_aware_direct_source_qa_not_blind']
    external_reports_consulted: Literal[False]
    source_retrieval_performed_by_this_reviewer: Literal[False]
    source_url: str
    acquisition_receipt: Asset
    expected_pages: Literal[5]
    native_bytes: Literal[9284]
    native_extraction: Literal['PyMuPDF 1.28.2; get_text(text, sort=False, flags=195)']
    pages: list[Page] = Field(min_length=5,max_length=5)
    observations: list[Observation]
    stated_dates: list[SourceDate]
    crops: list[Crop]
    source_adoption_date: Literal['2026-04-06']
    source_effective_date: Literal['2026-04-15']
    printed_vote_aye: Literal[4]
    printed_vote_nay: Literal[1]
    handwritten_signatures_observed: Literal[False]
    seal_graphic_observed: Literal[True]
    complete_consolidated_chapter: Literal[False]
    missing_native_word_correction_identified: Literal[False]
    source_changed: Literal[False]
    network_requests: Literal[0]
    repository_changes: Literal[False]
    legal_currentness: Literal['not_verified']
    limits: list[str]
    @field_validator('reviewed_at')
    @classmethod
    def aware(cls,v:datetime)->datetime:
        if v.utcoffset() is None:raise ValueError('Aware time required')
        return v
    @model_validator(mode='after')
    def complete(self)->Review:
        if [p.physical_page for p in self.pages]!=list(range(1,6)):
            raise ValueError('All five pages required')
        if sum(len(p.native_text.encode()) for p in self.pages)!=self.native_bytes:
            raise ValueError('Native coverage incomplete')
        if len({o.id for o in self.observations})!=len(self.observations):
            raise ValueError('Duplicate observation')
        for o in self.observations:
            p=self.pages[o.physical_page-1]
            if o.source_image!=p.primary_image:raise ValueError('Wrong source image')
            if o.native_span:
                s=o.native_span
                if p.native_text.encode()[s.start_byte:s.end_byte_exclusive]!=s.text.encode():
                    raise ValueError('Observation byte span differs')
        for d in self.stated_dates:
            s=d.span;p=self.pages[d.physical_page-1]
            if p.native_text.encode()[s.start_byte:s.end_byte_exclusive]!=s.text.encode():
                raise ValueError('Date source span differs')
        return self

class CustodyRow(Strict):
    original_path: str
    local: Asset

class Custody(Strict):
    copied_at: datetime
    files: list[CustodyRow]
    original_files_unchanged: Literal[True]
    source_response_body_identical_to_pdf: Literal[True]
    scope: str

class Manifest(Strict):
    frozen_at: datetime
    files: list[Asset]
    file_count: int
    legal_currentness: Literal['not_verified']
    @model_validator(mode='after')
    def complete(self)->Manifest:
        if len(self.files)!=self.file_count or len({x.path for x in self.files})!=self.file_count:
            raise ValueError('File inventory mismatch')
        return self
