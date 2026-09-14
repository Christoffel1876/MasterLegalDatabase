"""Strict source-review records; machine text and visual judgments remain separate."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject unknown fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """An exact ordinary package file."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class OCRLine(Strict):
    """Unchanged Apple Vision candidate and normalized bottom-origin geometry."""
    text: str
    confidence: float
    bbox: list[float] = Field(min_length=4, max_length=4)


class OCRResult(Strict):
    """Exact parsed local engine output, not reviewed correctness."""
    revision: int
    os_version: str
    lines: list[OCRLine]


class Note(Strict):
    """Visual qualification tied to a physical page and optional transcript span."""
    id: str
    kind: Literal['execution', 'source_anomaly', 'table', 'exception_scope',
                  'date_role', 'layout', 'uncertain_glyph', 'transcription_correction']
    statement: str
    transcript_start: int | None
    transcript_end: int | None
    exact_transcript: str | None
    crop: Asset | None


class Span(Strict):
    """A complete byte interval in a reviewed page-local UTF-8 transcript."""
    page: int = Field(ge=1, le=16)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class Block(Strict):
    """A source-context block; pixel box is a containing region, not glyph precision."""
    id: str
    role: Literal['heading', 'body', 'recording_stamp', 'printed_pagination']
    span: Span
    pixel_box: list[int] = Field(min_length=4, max_length=4)
    continuation_of: str | None


class Association(Strict):
    """Literal climatic-design entry with its parent heading and full source span."""
    id: str
    label: str
    value: str
    span: Span
    parent_heading: str
    context_block_ids: list[str]


class Marking(Strict):
    """Visible non-plain-text feature, kept outside the exact wording."""
    id: str
    kind: Literal['struck', 'handwritten_fill', 'signature_presence', 'seal_presence',
                  'subscript', 'underlining', 'barcode_presence']
    page: int
    span: Span | None
    statement: str
    pixel_box: list[int] = Field(min_length=4, max_length=4)
    identity_verified: Literal[False]


class Page(Strict):
    """Complete physical page, empty native text and separate reviewed transcript."""
    number: int = Field(ge=1, le=16)
    image: Asset
    native: Asset
    native_byte_count: Literal[0]
    ocr: Asset
    ocr_text: Asset
    transcript: Asset
    image_width: int
    image_height: int
    full_image_viewed: Literal[True]
    review_method: Literal['candidate_aware_direct_image_source_qa']
    notes: list[Note]
    blocks: list[Block]


class Custody(Strict):
    """Repository receipt is distinct from supplied original HTTP claims."""
    source_id: Literal['gunnison-building-code-resolution-2023-22-sh-ext-003']
    authority_id: Literal['CO-COUNTY-GUNNISON']
    layer_id: Literal['08_County_Authorities']
    acquisition_method: Literal['received_review_package']
    official_source_url: None
    original_http_acquisition_verified: Literal[False]
    received_at: str
    record_line: int
    manifest: Asset
    exact_record: Asset
    preparation: Asset
    receipt: Asset
    supplied_url: str
    limits: list[str]


class Review(Strict):
    """All sixteen pages reviewed without promotion to current law."""
    schema_version: Literal['1.0']
    source: Asset
    source_id: Literal['gunnison-building-code-resolution-2023-22-sh-ext-003']
    authority_id: Literal['CO-COUNTY-GUNNISON']
    page_count: Literal[16]
    native_total_bytes: Literal[0]
    source_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    external_reports_consulted: Literal[False]
    review_method: Literal['candidate_aware_direct_image_source_qa']
    legal_adoption_verified: Literal[False]
    signature_identity_verified: Literal[False]
    created_at: str
    custody: Custody
    pages: list[Page] = Field(min_length=16, max_length=16)
    limitations: list[str]
    associations: list[Association]
    markings: list[Marking]

    @model_validator(mode='after')
    def complete_pages(self) -> 'Review':
        """Require physical order and complete sixteen-page coverage."""
        if [p.number for p in self.pages] != list(range(1, 17)):
            raise ValueError('Complete physical pages 1–16 required')
        if len({n.id for p in self.pages for n in p.notes}) != sum(
            len(p.notes) for p in self.pages
        ):
            raise ValueError('Duplicate note ID')
        return self


class Manifest(Strict):
    """Closed ordinary-file inventory; its own file is excluded."""
    schema_version: Literal['1.0']
    status: Literal['source_review_only_currentness_not_verified']
    files: list[Asset]


class ProcessReceipt(Strict):
    """Actual local command result, including failures without suppression."""
    started_at: str
    completed_at: str
    command: list[str]
    returncode: int
    stdout: Asset
    stderr: Asset
