"""Strict, source-specific review records; no legal-status inference."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unknown fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact local evidence identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """Half-open UTF-8 byte range."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class Block(Strict):
    """Visible text or explicitly separated graphic annotation."""
    id: str
    page: int = Field(ge=1, le=3)
    kind: Literal['printed_text', 'mixed_printed_and_handwritten',
                  'handwriting_annotation', 'graphic_annotation']
    image: Asset
    region_xyxy: tuple[int, int, int, int]
    text: str
    transcript: Asset
    transcript_span: Span
    notes: list[str]


class Fee(Strict):
    """Reviewer decomposition of a printed fee clause, not a RuleUnit."""
    id: str
    block_id: str
    amount_literal: str
    amount_in_block: Span
    label_literal: str
    conditions_block_ids: list[str]
    subsection: str
    notes: list[str]


class Page(Strict):
    """Complete physical page and unchanged extraction evidence."""
    number: int
    image: Asset
    native: Asset
    native_spans: list[Span]
    native_status: Literal['empty_image_only']
    ocr_json: Asset
    ocr_text: Asset
    ocr_observation_spans: list[Span]
    reviewed_transcript: Asset
    width: Literal[2550]
    height: Literal[3300]


class DateStatement(Strict):
    """A date's source role; no conversion into operative effect."""
    literal: str
    role: str
    block_ids: list[str]
    qualification: str


class Review(Strict):
    """Complete scoped image review with original provenance limits."""
    schema_version: Literal[1]
    source_id: Literal['gunnison-building-fees-resolution-2025-24-sh-ext-003']
    authority_id: Literal['CO-COUNTY-GUNNISON']
    layer: Literal['08_County_Authorities']
    source: Asset
    source_role: str
    status: Literal['complete_visible_source_fidelity_review_qualified_handwriting']
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    reviewed_at: str
    method: str
    official_acquisition_at_verified: None
    supplied_requested_url: str
    supplied_acquisition_interval: tuple[str, str]
    supplied_time_status: Literal['reported_not_independently_verified']
    source_bytes_intake_status_at_review: Literal['received_package_canonical_intake_not_asserted']
    pages: list[Page]
    blocks: list[Block]
    fees: list[Fee]
    dates: list[DateStatement]
    limitations: list[str]
    findings: list[str]
    custody: list[Asset]


class Manifest(Strict):
    """Closed inventory excluding only itself and its exported schema."""
    schema_version: Literal[1]
    status: Literal['frozen_source_fidelity_review_not_current_law']
    created_at: str
    files: list[Asset]
