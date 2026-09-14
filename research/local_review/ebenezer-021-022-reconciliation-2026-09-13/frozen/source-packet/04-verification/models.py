"""Strict source-only identities and the sealed two-document review packet."""
from __future__ import annotations
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject unknown fields and coercion of recorded Python values."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """Bind exact bytes using a package-relative or recorded historical path."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Page(Strict):
    """Identify one complete physical-page image without transcription hints."""
    physical_page: int = Field(ge=1)
    image: Ref
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class Identity(Strict):
    """Expose only source identity and complete page images before pass one."""
    assignment_id: Literal['EB-PDF-021', 'EB-PDF-022']
    source_id: Literal['douglas-ehs-fees-atlas-directed', 'pueblo-planning-fees-atlas-directed']
    authority_id: Literal['CO-COUNTY-DOUGLAS', 'CO-MUNICIPAL-PUEBLO']
    expected_pages: int = Field(ge=1, le=4)
    original: Ref
    pages: list[Page]

    @model_validator(mode='after')
    def bind_identity(self) -> Identity:
        """Require the fixed county/city/page relationship and exact page sequence."""
        expected = {
            'EB-PDF-021': ('douglas-ehs-fees-atlas-directed', 'CO-COUNTY-DOUGLAS', 1),
            'EB-PDF-022': ('pueblo-planning-fees-atlas-directed', 'CO-MUNICIPAL-PUEBLO', 4),
        }
        if (self.source_id, self.authority_id, self.expected_pages) != expected[self.assignment_id]:
            raise ValueError('Assignment, source and authority differ')
        if [p.physical_page for p in self.pages] != list(range(1, self.expected_pages + 1)):
            raise ValueError('Missing, repeated or reordered page')
        return self


class Identities(Strict):
    """The only pre-freeze metadata for the two queued sources."""
    schema_version: Literal[1] = 1
    packet_id: Literal['ebenezer-021-022-2026-09-13'] = 'ebenezer-021-022-2026-09-13'
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    documents: list[Identity] = Field(min_length=2, max_length=2)
    authority_limit: Literal['Collection identity only; no legal-authority conclusion.'] = (
        'Collection identity only; no legal-authority conclusion.')
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Extraction(Strict):
    """Retain uncorrected native output and its physical-page packaging boundaries."""
    source_id: str
    source_sha256: str
    method: Literal['Page.get_text("text", sort=False, flags=195)']
    extractor: Literal['PyMuPDF'] = 'PyMuPDF'
    extractor_version: Literal['1.28.2'] = '1.28.2'
    candidate_status: Literal['machine_native_text_unreviewed'] = 'machine_native_text_unreviewed'
    candidate: Ref
    page_native: list[Ref]
    prior_native: list[Ref]
    prior_native_exact_match: Literal[True] = True
    separators_are_packaging_not_source: Literal[True] = True


class Render(Strict):
    """Record actual bounded renderer execution and complete output image bindings."""
    source_id: str
    source_sha256: str
    renderer: Literal['Poppler pdftoppm'] = 'Poppler pdftoppm'
    renderer_version: str
    command: list[str]
    dpi: Literal[300] = 300
    started_at: AwareDatetime
    completed_at: AwareDatetime
    timeout_seconds: Literal[30] = 30
    returncode: Literal[0] = 0
    stderr: Ref
    pages: list[Page]


class Custody(Strict):
    """Seal prior provenance references from the independent source-first pass."""
    source_id: str
    original_input: Ref
    source_sha256: str
    official_url: str
    earlier_http_completed_at: AwareDatetime
    actual_repository_received_at: None = None
    repository_intake_binding: Literal['not_part_of_this_packet'] = 'not_part_of_this_packet'
    currentness: Literal['not_verified'] = 'not_verified'
    scope: Literal['Exact accepted source copy only; no new acquisition or legal finding.'] = (
        'Exact accepted source copy only; no new acquisition or legal finding.')


class Preparation(Strict):
    """Bind preparation methods and roles without certifying an external review."""
    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    inputs: list[Custody] = Field(min_length=2, max_length=2)
    extraction: list[Extraction] = Field(min_length=2, max_length=2)
    renders: list[Render] = Field(min_length=2, max_length=2)
    prior_findings_in_source_only_materials: Literal[False] = False
    original_pdf_bytes_changed: Literal[False] = False
    public_requests: Literal[0] = 0
    no_new_document_at_or_after: AwareDatetime
    stop_at: AwareDatetime
    stop_after: Literal['EB-PDF-022'] = 'EB-PDF-022'


class Manifest(Strict):
    """Close exact source, candidate, custody and verification packet membership."""
    schema_version: Literal[1] = 1
    packet_id: Literal['ebenezer-021-022-2026-09-13'] = 'ebenezer-021-022-2026-09-13'
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    frozen_at: AwareDatetime
    files: list[Ref]
    identities: Ref
    preparation: Ref
    instructions: Ref
    legal_currentness: Literal['not_verified'] = 'not_verified'
