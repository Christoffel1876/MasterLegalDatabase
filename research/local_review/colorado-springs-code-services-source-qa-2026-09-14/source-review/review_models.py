"""Strict source-fidelity evidence models; no legal-effect assertions."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):
    """Reject extra fields and coercion in evidence records."""
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    """A byte-bound external packet asset or local audit payload."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

class Line(Strict):
    """One complete native line, including its original final LF."""
    id: str
    page: int
    start: int
    end: int
    candidate_start: int
    candidate_end: int
    text: str
    sha256: str
    bbox: list[float]
    colors: list[int]
    visibility: Literal['visible', 'white_encoded_not_visible']

class Row(Strict):
    """Visible fee association with separate, unconverted source cells."""
    id: str
    page: int
    label_refs: list[str]
    fee_refs: list[list[str]]
    columns: list[str]
    group_refs: list[str]
    context_refs: list[str]
    note: str

class Paragraph(Strict):
    """Heading and body linked according to the rendered source layout."""
    id: str
    page: int
    heading_refs: list[str]
    body_refs: list[str]
    kind: Literal['definition', 'context']

class Crop(Strict):
    """Exact pixel slice of an unchanged full source image."""
    asset: Asset
    page: int
    pixel_box: list[int]
    inspected_at: str | None

class QA(Strict):
    """Complete source-page review with custody and explicit limitations."""
    schema_version: Literal['cs-code-fees-qa-1']
    source_id: Literal['colorado-springs-code-services-fees-2015-atlas-directed']
    authority_id: Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    review_kind: Literal['checked_tables']
    status: Literal['complete_source_fidelity_review_pending_atlas_acceptance']
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    source_year_as_printed: Literal['2015']
    adoption_date: None
    effective_date: None
    packet_root_claim: str
    canonical_original_claim: str
    assets: list[Asset]
    source_sha256: str
    candidate_sha256: str
    full_pages_inspected: list[int]
    full_page_inspection_interval: list[str]
    method: str
    lines: list[Line]
    rows: list[Row]
    paragraphs: list[Paragraph]
    crops: list[Crop]
    findings: list[str]
    limitations: list[str]

class Seal(Strict):
    """Closed inventory of the local audit, excluding the seal itself."""
    files: list[Asset]
