"""Strict source-fidelity records for one image-only county resolution."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = 'gunnison-iwuic-resolution-2022-33-sh-ext-003'
SOURCE_SHA = '0b2dc2e2bdff25b849b29de9285e993d7a353a9209cffbccad2ebc79c7f7b99d'


class Strict(BaseModel):
    """Reject extra fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """An exact relative file identity; historical paths are never opened."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """A half-open UTF-8 byte range, including a declared separator if any."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')

    @model_validator(mode='after')
    def ordered(self) -> 'Span':
        """Reject inverted spans."""
        if self.end < self.start:
            raise ValueError('Inverted byte span')
        return self


class Passage(Strict):
    """A checked image passage or explicitly separate reviewer annotation."""
    id: str
    page: int = Field(ge=1, le=4)
    kind: Literal['printed_text', 'mixed_printed_and_handwritten',
                  'handwriting_annotation', 'graphic_annotation']
    image: Asset
    locator: str
    crop_paths: list[str]
    text: str
    reviewed_transcript: Asset
    reviewed_span: Span
    continuation_of: str | None
    notes: list[str]


class Page(Strict):
    """Full physical page and unchanged machine evidence."""
    number: int = Field(ge=1, le=4)
    image: Asset
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    native: Asset
    native_spans: list[Span]
    native_status: Literal['empty_image_only']
    ocr_json: Asset
    ocr_text: Asset
    ocr_observation_spans: list[Span]
    candidate_span: Span
    reviewed_transcript: Asset


class DateStatement(Strict):
    """Source date or edition role, never a verified operative date."""
    literal: str
    role: str
    passage_ids: list[str]
    qualification: str


class Amendment(Strict):
    """Exact document amendment instruction, not an enacted RuleUnit."""
    id: str
    target_literal: str
    instruction_literal: str
    passage_ids: list[str]
    targets_within_literal: list[str]
    qualification: str


class Discrepancy(Strict):
    """Checked OCR discrepancy; original OCR remains untouched."""
    id: str
    page: int = Field(ge=1, le=4)
    ocr_span: Span
    ocr_text_literal: str
    reviewed_passage_ids: list[str]
    finding: str


class Provenance(Strict):
    """Canonical receipt custody separate from supplier's acquisition claims."""
    acquisition_method: Literal['received_review_package']
    official_source_url_verified: None
    official_acquisition_at_verified: None
    supplied_requested_url: str
    supplied_started_at: str
    supplied_finished_at: str
    supplied_times_status: Literal['reported_not_independently_verified']
    repository_received_at: str
    canonical_archive_path_claim: str
    canonical_record: Asset
    intake_receipt: Asset
    receipt_status: Literal['canonical_intake_record_bound_not_fresh_http_verification']


class Inspection(Strict):
    """Reviewer attestation, recorded after the tool image inspections."""
    reviewer: Literal['Plato']
    recorded_at: str
    exposure: str
    full_pages: list[Asset]
    crops: list[Asset]
    full_page_count: Literal[4]
    crop_count: Literal[7]
    chronology: str
    external_reports_consulted: Literal[False]
    handwriting_identities_authenticated: Literal[False]


class Review(Strict):
    """Complete scoped source transcription with explicit legal limits."""
    schema_version: Literal[1]
    source_id: Literal['gunnison-iwuic-resolution-2022-33-sh-ext-003']
    authority_id: Literal['CO-COUNTY-GUNNISON']
    layer: Literal['08_County_Authorities']
    source: Asset
    source_role: str
    status: Literal['complete_visible_source_fidelity_review_qualified_handwriting']
    review_kind: Literal['checked_passages']
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    reviewed_at: str
    method: str
    scope: str
    normalization: str
    provenance: Provenance
    candidate: Asset
    packet_manifest: Asset
    inspection: Asset
    pages: list[Page]
    checked_passages: list[Passage]
    amendment_instructions: list[Amendment]
    dates: list[DateStatement]
    ocr_discrepancies: list[Discrepancy]
    limitations: list[str]
    findings: list[str]
    custody: list[Asset]


class Manifest(Strict):
    """Closed inventory excluding only itself and its exported schema."""
    schema_version: Literal[1]
    status: Literal['frozen_source_fidelity_review_not_current_law']
    created_at: str
    files: list[Asset]


class Validation(Strict):
    """Actual mechanical replay, without implied visual or legal certification."""
    recorded_at: str
    status: Literal['passed']
    source_sha256: str
    full_pages: Literal[4]
    crops_replayed: Literal[7]
    native_bytes: Literal[0]
    ocr_bytes: int
    candidate_bytes: int
    reviewed_bytes: int
    passages: int
    tests: int
    rerendered_pages: int
    limitations: list[str]
