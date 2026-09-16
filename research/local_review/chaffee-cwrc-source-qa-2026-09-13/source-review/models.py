"""Strict source-review records for the fourteen-page scanned CWRC ordinance."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
PageNo = Annotated[int, Field(ge=1, le=14)]


class Strict(BaseModel):
    """Reject coercion and unexpected fields."""
    model_config = ConfigDict(strict=True, extra='forbid')


class Ref(Strict):
    """Package-relative exact file identity."""
    path: str
    sha256: Digest
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """Half-open byte span in a derived text file, never in the source PDF."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: Digest


class Markup(Strict):
    """Visually observed lexical mark extent in a checked transcript segment."""
    kind: Literal['underline', 'strikethrough', 'superscript', 'italic']
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)
    qualification: str


class Segment(Strict):
    """A full printed paragraph, heading, or explicitly uncertain execution region."""
    id: str
    page: PageNo
    kind: Literal['heading', 'paragraph', 'recorder_metadata', 'execution_label',
                  'handwriting_uncertain', 'seal']
    context: str
    ocr_line_numbers: list[int]
    ocr_span: Span | None
    ocr_text: str
    checked_text: str | None
    checked_span: Span | None
    pixel_rect: tuple[int, int, int, int]
    image_path: str
    crop_paths: list[str]
    continuation_of: str | None
    markup: list[Markup]
    notes: list[str]


class Page(Strict):
    """Complete physical source page and unchanged extraction candidates."""
    page: PageNo
    image: Ref
    width: Literal[2550]
    height: Literal[3300]
    native: Ref
    ocr_event: Ref
    ocr_stdout: Ref
    ocr_stderr: Ref
    ocr_candidate: Ref
    checked_transcript: Ref
    ocr_line_count: int = Field(gt=0)
    segment_ids: list[str]
    full_page_viewed: Literal[True]
    half_page_crops_viewed: Literal[True]
    footer_and_borders: str


class Observation(Strict):
    """A bounded image-supported finding; no interpretation or current-law status."""
    id: str
    segment_ids: list[str]
    statement: str
    qualification: str


class DateClaim(Strict):
    """Literal source date or relative interval with its printed role."""
    value: str
    role: str
    segment_ids: list[str]
    independent_legal_verification: Literal[False]


class Acquisition(Strict):
    """Actual new HTTP custody distinct from any future canonical intake."""
    source_event: Ref
    frozen_retrieval_manifest: Ref
    requested_url: str
    final_url: str
    actual_started_at: str
    actual_completed_at: str
    http_status: Literal[200]
    actual_repository_received_at: None
    method: Literal['atlas_directed_public_http']
    qualification: str


class SourceQA(Strict):
    """Complete scanned-source review and its explicit research-only limits."""
    schema_version: Literal['chaffee-cwrc-source-qa-1']
    source_id: Literal['chaffee-cwrc-ordinance-2026-02-atlas-directed']
    authority_id: Literal['CO-COUNTY-CHAFFEE']
    layer_id: Literal['08_County_Authorities']
    source_sha: Digest
    source: Ref
    prepared_at: str
    review_status: Literal['checked_passages']
    method: str
    scope: str
    native_method: str
    ocr_method: str
    transcription_conventions: list[str]
    source_role: str
    acquisition: Acquisition
    pages: list[Page] = Field(min_length=14, max_length=14)
    segments: list[Segment]
    observations: list[Observation]
    date_claims: list[DateClaim]
    external_reports_consulted: Literal[False]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    verified_adoption_date: None
    verified_effective_date: None
    limitations: list[str]


class Manifest(Strict):
    """Closed payload inventory; the manifest itself is the external root of trust."""
    schema_version: Literal['cwrc-closed-payloads-1']
    created_at: str
    files: list[Ref]
    payload_count: int = Field(gt=0)


class Crop(Strict):
    """Exact source-PNG crop identity; top-left pixel coordinates."""
    page: PageNo
    source_path: str
    source_sha256: Digest
    rect: tuple[int, int, int, int]
    path: str
    sha256: Digest
    size_bytes: int = Field(gt=0)
    method: str


class Correction(Strict):
    """Image-reviewed replacement of an OCR line, preserved separately from candidate."""
    page: PageNo
    line: int = Field(gt=0)
    raw_ocr: str
    checked: str | None
    reason: str
