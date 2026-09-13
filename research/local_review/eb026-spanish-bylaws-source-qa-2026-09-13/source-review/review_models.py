"""Strict source-fidelity evidence models for one Spanish bylaws PDF."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = "el-paso-boh-bylaws-spanish-sd011"
SOURCE_SHA = "1b8367a5710b5159ea479ad588ee5dee9850e1e9451b0115d2770a2d4aae6c7f"


class Strict(BaseModel):
    """Reject undeclared data and coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class FileRef(Strict):
    """A package-relative immutable byte identity."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class NativeLine(Strict):
    """An exact native line and its PDF-coordinate location, not inferred OCR."""

    id: str
    physical_page: int = Field(ge=1, le=6)
    line_number: int = Field(ge=1)
    byte_start: int = Field(ge=0)
    byte_end: int = Field(gt=0)
    candidate_byte_start: int = Field(ge=0)
    candidate_byte_end: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bbox_pdf_points: list[float] = Field(min_length=4, max_length=4)


class Segment(Strict):
    """A whole visual paragraph, heading, or separately retained native whitespace."""

    id: str
    physical_page: int = Field(ge=1, le=6)
    first_line: int = Field(ge=1)
    last_line: int = Field(ge=1)
    kind: Literal["cover", "heading", "paragraph", "footer", "extraction_whitespace"]
    context: str
    byte_start: int = Field(ge=0)
    byte_end: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    line_ids: list[str] = Field(min_length=1)
    continues_from: str | None
    continues_to: str | None
    visual_disposition: Literal["wording_matches_visible_source", "native_whitespace_only"]
    qualification: str


class Page(Strict):
    """The complete page image, native stream and actual visual inspection scope."""

    physical_page: int = Field(ge=1, le=6)
    image: FileRef
    native: FileRef
    candidate_native_start: int = Field(ge=0)
    candidate_native_end: int = Field(gt=0)
    width_points: Literal[612.0]
    height_points: Literal[792.0]
    image_width: Literal[2550]
    image_height: Literal[3300]
    full_page_viewed: Literal[True]
    visible_date_footer: None
    lines: list[NativeLine] = Field(min_length=1)
    segments: list[Segment] = Field(min_length=1)
    visual_notes: str


class Crop(Strict):
    """An actually viewed detail crop; exact pixels and PDF rerenders stay distinct."""

    id: str
    physical_page: int = Field(ge=1, le=6)
    image: FileRef
    method: Literal["pdf_clip_pymupdf", "exact_poppler_pixel_crop"]
    rectangle: list[int] = Field(min_length=4, max_length=4)
    coordinate_unit: Literal["pdf_points", "source_png_pixels"]
    viewed: Literal[True]
    observation: str


class Observation(Strict):
    """A source-supported qualification, with exact native anchors and full context."""

    id: str
    kind: Literal["source_anomaly", "layout", "conditional_wording", "date_role", "typography"]
    segment_ids: list[str] = Field(min_length=1)
    literal_anchors: list[str] = Field(min_length=1)
    crop_ids: list[str]
    disposition: Literal["preserve_source", "native_formatting_limit"]
    finding: str


class Scope(Strict):
    """Visual judgment is recorded separately from deterministic byte checks."""

    method: Literal["preparation_candidate_aware_direct_image_review"]
    reviewer: Literal["Ptolemy (Codex subagent)"]
    full_physical_pages: list[int]
    full_page_display_size: Literal["1376x1780 from 2550x3300 input"]
    full_pages_viewed_before_text_comparison: Literal[True]
    prior_preparation_exposure: Literal[True]
    external_reports_consulted: Literal[False]
    english_versions_consulted: Literal[False]
    translation_equivalence_assessed: Literal[False]
    native_utf8_bytes: Literal[13558]
    native_lines: Literal[180]
    nonwhitespace_lines: Literal[178]
    inspected_crops: Literal[15]
    excluded_scope: list[str]


class Review(Strict):
    """A bounded Spanish source-fidelity review awaiting independent root acceptance."""

    schema_version: Literal["geode.eb026.spanish-bylaws.source-qa.v1"]
    source_id: Literal["el-paso-boh-bylaws-spanish-sd011"]
    source_sha256: Literal[SOURCE_SHA]
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    layer_id: Literal["08_County_Authorities"]
    source: FileRef
    candidate: FileRef
    packet_manifest: FileRef
    packet_manifest_sha256: Literal[
        "ace3738bac6375b17f01ae0c4390350d5aeeacb1b9473838c57832dcd09427f5"
    ]
    canonical_record: FileRef
    custody: FileRef
    received_at: Literal["2026-09-12T22:59:48.795762Z"]
    acquisition_method: Literal["received_review_package"]
    independently_verified_http_at: None
    issue_date: None
    adoption_date: None
    effective_date: None
    date_limitation: str
    prepared_at: AwareDatetime
    status: Literal["initial_direct_source_qa_pending_root_acceptance"]
    review_kind: Literal["checked_passages"]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    fullscope: Scope
    pages: list[Page] = Field(min_length=6, max_length=6)
    crops: list[Crop] = Field(min_length=15, max_length=15)
    observations: list[Observation]
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def fixed_scope(self) -> Review:
        """Reject changed page coverage and duplicate segment/observation identities."""
        if [p.physical_page for p in self.pages] != list(range(1, 7)):
            raise ValueError("Six complete ordered physical pages required")
        if self.fullscope.full_physical_pages != list(range(1, 7)):
            raise ValueError("Visual scope differs")
        ids = [s.id for p in self.pages for s in p.segments]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate paragraph identity")
        obs_ids = [o.id for o in self.observations]
        if len(obs_ids) != len(set(obs_ids)):
            raise ValueError("Duplicate observation identity")
        return self


class Manifest(Strict):
    """Closed portable package identity, excluding only its own manifest file."""

    schema_version: Literal["geode.eb026.source-qa.inventory.v1"]
    created_at: AwareDatetime
    status: Literal["frozen_initial_source_qa"]
    files: list[FileRef]
    public_requests: Literal[0]
    canonical_writes: Literal[0]
    source_changes: Literal[0]


class Validation(Strict):
    """Measured offline verification; no automatic visual/legal certification."""

    status: Literal["passed"]
    physical_pages: Literal[6]
    native_bytes: Literal[13558]
    native_lines: Literal[180]
    paragraph_segments: int
    crop_replays: Literal[15]
    full_page_render_replays: int
    legal_currentness: Literal["not_verified"]
    visual_judgment_automatically_certified: Literal[False]
