"""Strict records for a two-page, image-based source review; no legal promotion."""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = "larimer-equity-fee-resolution-sd007-04"
SOURCE_SHA = "9ef9ae74a016628f3b8c6fac3f0ce7d0d76579472251c60725e56da524f19437"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def confined(self) -> Asset:
        p = PurePosixPath(self.path)
        if p.is_absolute() or ".." in p.parts or str(p) != self.path:
            raise ValueError("Asset path must be an ordinary package-relative path")
        return self


class TextBlock(Strict):
    id: str
    physical_page: Literal[1, 2]
    role: Literal["title", "recital", "resolution_lead", "operative", "eligibility"]
    text: str
    start_byte: int = Field(ge=0)
    end_byte: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_basis: Literal["manual_page_transcription_utf8_not_native_source_text"]
    region_px: tuple[int, int, int, int]
    region_precision: Literal["approximate_locator_in_full_300dpi_image"]
    parent_id: str | None = None

    @model_validator(mode="after")
    def matches(self) -> TextBlock:
        raw = self.text.encode("utf-8")
        if (self.end_byte - self.start_byte != len(raw)
                or hashlib.sha256(raw).hexdigest() != self.sha256):
            raise ValueError("Manual transcription span bytes differ")
        return self


class Page(Strict):
    physical_page: Literal[1, 2]
    image: Asset
    native_text: Asset
    native_bytes: Literal[0]
    printed_body: Asset
    width_px: Literal[2550]
    height_px: Literal[3300]
    full_page_directly_viewed: Literal[True]
    blocks: list[TextBlock]


class Crop(Strict):
    id: str
    physical_page: Literal[2]
    image: Asset
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    dpi: Literal[300]
    directly_viewed: Literal[True]


class ExecutionRegion(Strict):
    id: str
    physical_page: Literal[2]
    region_px: tuple[int, int, int, int]
    printed_fragments: list[str]
    observation: str
    handwriting_reading: str | None
    signature_identity: None = None
    authenticity_verified: Literal[False] = False
    qualification: str
    crop_ids: list[str]


class Observation(Strict):
    id: str
    kind: Literal["scope", "condition", "date", "source_defect", "dependency", "execution"]
    block_ids: list[str]
    execution_ids: list[str]
    statement: str
    limitation: str


class Custody(Strict):
    manual_manifest: Asset
    manual_line_number: Literal[33]
    manual_line_sha256: str
    source_provenance: Asset
    provenance_line_number: Literal[6]
    provenance_line_sha256: str
    canonical_archive_path: str
    intake_id: str
    repository_received_at: AwareDatetime
    acquisition_method: Literal["received_review_package"]
    original_acquisition_time: None = None
    supplied_requested_url: str
    supplied_final_url: str
    supplied_time_claim: str
    supplied_method_claim: str
    supplied_http_status: Literal[200]
    source_http_acquisition_verified: Literal[False]
    intake_status: Literal["archived_pending_pipeline"]
    copied_at: AwareDatetime
    limitation: str


class Review(Strict):
    review_id: Literal["ATLAS-LARIMER-EQUITY-RESOLUTION-2026-09-11-SESSION2"]
    source_id: Literal["larimer-equity-fee-resolution-sd007-04"]
    authority_id: Literal["CO-COUNTY-LARIMER"]
    authority_basis: str
    source: Asset
    source_unchanged: Literal[True]
    expected_physical_pages: Literal[2]
    review_mode: Literal["atlas_candidate_aware_source_qa_not_blind"]
    prior_exposure: str
    external_assignment: None = None
    external_reports_consulted: Literal[False]
    status: Literal["printed_body_transcribed_execution_observations_qualified"]
    reviewed_at: AwareDatetime
    transcription_convention: str
    native_extractor: Literal["PyMuPDF 1.28.2 text flags=195 sort=False"]
    rendering_engine: Literal["Poppler pdftoppm 26.05.0"]
    rendering_dpi: Literal[300]
    pages: list[Page]
    crops: list[Crop]
    execution: list[ExecutionRegion]
    observations: list[Observation]
    custody: Custody
    attachments_present: Literal[False]
    attachment_a_reference_observed: Literal[False]
    signature_marks_observed: Literal[3]
    execution_area_completed_as_visual_observation: Literal[True]
    adopted_status_verified: Literal[False]
    adoption_date_verified: None = None
    effective_date_verified: None = None
    legal_currentness: Literal["not_verified"]
    semantic_or_coverage_promotion: Literal[False]
    limitations: list[str]

    @model_validator(mode="after")
    def scope(self) -> Review:
        if (self.source.sha256 != SOURCE_SHA or self.source.size_bytes != 1116210
                or [p.physical_page for p in self.pages] != [1, 2]
                or [len(p.blocks) for p in self.pages] != [11, 10]):
            raise ValueError("Wrong source or incomplete two-page body scope")
        ids = [b.id for p in self.pages for b in p.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate body block")
        for p in self.pages:
            pos = 0
            for b in p.blocks:
                if b.physical_page != p.physical_page or b.start_byte != pos:
                    raise ValueError("Page-local transcription gap or order change")
                x0, y0, x1, y1 = b.region_px
                if not 0 <= x0 < x1 <= 2550 or not 0 <= y0 < y1 <= 3300:
                    raise ValueError("Block locator outside page")
                if b.parent_id and b.parent_id not in ids:
                    raise ValueError("Missing condition parent")
                pos = b.end_byte
            if pos != p.printed_body.size_bytes:
                raise ValueError("Unaccounted transcription bytes")
        ex = {e.id for e in self.execution}
        for o in self.observations:
            if not set(o.block_ids) <= set(ids) or not set(o.execution_ids) <= ex:
                raise ValueError("Observation has no declared source locator")
        return self


class Inventory(Strict):
    schema_version: Literal[1]
    files: list[Asset]
    excluded_self: Literal["MANIFEST.json"]
    legal_currentness: Literal["not_verified"]
