"""Strict source-fidelity review records; no adoption or current-law determination."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unrecognized fields and coercion in review evidence."""
    model_config = ConfigDict(strict=True, extra="forbid")


class Asset(Strict):
    """Exact copied or newly generated artifact identity."""
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """An exact UTF-8 byte range in an unchanged page or packaged candidate."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Observation(Strict):
    """One unaltered engine line, including its original confidence and normalized box."""
    id: str
    index: int = Field(ge=0)
    text: str
    bbox: list[float]
    confidence: float
    page_span: Span
    candidate_span: Span
    reviewed_block_ids: list[str]


class Page(Strict):
    """Source and OCR identities for one full physical page."""
    physical_page: int = Field(ge=1, le=4)
    image: Asset
    width: Literal[2550]
    height: Literal[3300]
    native_attempt: Asset
    ocr_json: Asset
    ocr_text: Asset
    candidate_span: Span
    observations: list[Observation]


class Block(Strict):
    """Visually checked wording, preserved independently from raw OCR."""
    id: str
    page: int = Field(ge=1, le=4)
    kind: str
    text: str
    association: str | None
    observation_ids: list[str]
    comparison: Literal["normalized_wording_agrees", "ocr_correction_required",
                        "visual_only_graphic_or_blank"]
    comparison_note: str


class TableFragment(Strict):
    """A physical row fragment with explicit column and page associations."""
    id: str
    logical_row: Literal["TIER1", "TIER2", "TIER3", "ROAD"]
    page: int = Field(ge=3, le=4)
    approximate_pixel_box: list[int]
    label_block: str
    fee_block: str
    characteristic_blocks: list[str]
    continuation_from: str | None


class TableRow(Strict):
    """One logical source row; never a computed fee or applicability rule."""
    id: Literal["TIER1", "TIER2", "TIER3", "ROAD"]
    fragments: list[str]
    event_type: str
    fee_text: str
    characteristics: list[str]
    header_block: Literal["P3-T-H"]
    proposal_context: Literal["P3-P2"]
    conditional_implementation: Literal["P4-P2"]
    dnr_footnote: str | None
    qualification: str


class Finding(Strict):
    """A bounded observed OCR or source-layout issue with no operative-effect inference."""
    id: str
    block_ids: list[str]
    observation_ids: list[str]
    finding: str


class Crop(Strict):
    """A directly inspected pixel slice with reproducible source coordinates."""
    image_page: int
    pixel_box: list[int]
    asset: Asset


class SourceQA(Strict):
    """Complete four-page source-fidelity review, pending independent acceptance."""
    source_id: Literal["larimer-equity-fee-memo-sd007-05"]
    authority_id: Literal["CO-COUNTY-LARIMER"]
    status: Literal["complete_source_fidelity_review_pending_root_acceptance"]
    reviewed_at: str
    review_method: str
    source: Asset
    source_first: Asset
    candidate: Asset
    packet_manifest: Asset
    selected_packet_payloads: list[dict[str, str]]
    provenance: dict[str, str | None]
    pages: list[Page]
    blocks: list[Block]
    table_fragments: list[TableFragment]
    table_rows: list[TableRow]
    findings: list[Finding]
    crops: list[Crop]
    consulted_root_notes: Asset
    root_notes_consulted_after_source_freeze: Literal[True]
    external_ebenezer_reports_consulted: Literal[False]
    complete_physical_pages: Literal[4]
    complete_source_blocks: Literal[82]
    original_ocr_observations: Literal[181]
    candidate_size_bytes: Literal[9796]
    original_ocr_body_bytes: Literal[9344]
    source_type: Literal["staff_recommendation_memo"]
    adopted_effect: Literal["not_verified"]
    legal_currentness: Literal["not_verified"]
    limitations: list[str]


class Manifest(Strict):
    """Closed review payload inventory."""
    frozen_at: str
    status: Literal["complete_source_fidelity_review_pending_root_acceptance"]
    files: list[Asset]
