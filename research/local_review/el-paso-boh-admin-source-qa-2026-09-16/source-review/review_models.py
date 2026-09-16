"""Strict complete native-source fidelity review, with no legal-status promotion."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = 'el-paso-boh-admin-regulations-sd011'
SOURCE_SHA = '64d72ce1f7783dcf7fb5a3f6956e8ba4845c4839318613a1dee09d99716625d7'


class Strict(BaseModel):
    """Reject unknown fields and implicit coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact relative payload identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """Half-open UTF-8 byte range of the named parent asset."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')

    @model_validator(mode='after')
    def ordered(self) -> 'Span':
        """Reject inverted byte ranges."""
        if self.end < self.start:
            raise ValueError('Inverted span')
        return self


class Line(Strict):
    """Every native byte belongs to one unchanged physical-page line."""
    number: int = Field(ge=1)
    native_span: Span
    candidate_span: Span
    raw_text: str
    passage_id: str | None
    whitespace_only: bool


class Page(Strict):
    """Complete physical page image and unchanged extraction."""
    physical_page: int = Field(ge=1, le=7)
    image: Asset
    width_px: Literal[2550]
    height_px: Literal[3300]
    native: Asset
    candidate_span: Span
    native_lines: list[Line]
    checked_passage_ids: list[str]
    coverage: str
    full_image_directly_viewed: Literal[True]
    unchecked_substantive_regions: list[str]


class Passage(Strict):
    """Image-checked wording; whitespace normalization is explicitly separate."""
    id: str
    page: int = Field(ge=1, le=7)
    kind: Literal['cover_text', 'section_heading', 'paragraph', 'footer_date']
    section: str | None
    label_as_printed: str | None
    parent_id: str | None
    image: Asset
    native: Asset
    native_span: Span
    candidate_span: Span
    native_line_start: int
    native_line_end: int
    text: str
    visible_markup: list[str]
    crop_ids: list[str]
    notes: list[str]


class Link(Strict):
    """Source structure continuing across physical pages, not an inferred legal chain."""
    id: str
    kind: Literal['section_continues', 'enumeration_continues', 'nested_under']
    from_id: str
    to_id: str
    note: str


class Finding(Strict):
    """Preserved source anomaly, structural risk or uncertainty."""
    id: str
    category: Literal['source_anomaly', 'structure', 'date_role', 'extraction_whitespace',
                      'exception_scope', 'encoding_limit']
    passage_ids: list[str]
    finding: str
    candidate_change_required: Literal[False]


class DateStatement(Strict):
    """Printed source date qualified by its actual role."""
    literal: str
    role: str
    passage_ids: list[str]
    operative_date_certified: Literal[False]
    qualification: str


class Provenance(Strict):
    """Actual repository receipt separate from supplied HTTP claims."""
    acquisition_method: Literal['received_review_package']
    original_http_independently_verified: Literal[False]
    verified_http_acquired_at: None
    supplied_url: str
    supplied_acquisition_started_at: AwareDatetime
    supplied_acquisition_completed_at: AwareDatetime
    repository_received_at: AwareDatetime
    canonical_path_claim: str
    canonical_record: Asset
    selected_source_provenance: Asset
    intake_receipt: Asset
    intake_intent: Asset


class Review(Strict):
    """Full seven-page source fidelity, not current or answer-safe legal evidence."""
    schema_version: Literal[1]
    source_id: Literal['el-paso-boh-admin-regulations-sd011']
    authority_id: Literal['CO-COUNTY-EL_PASO']
    layer: Literal['08_County_Authorities']
    issuer: str
    source_role: str
    source: Asset
    status: Literal['complete_candidate_aware_source_fidelity_review_pending_atlas_acceptance']
    review_kind: Literal['checked_passages']
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    reviewer: Literal['Plato']
    reviewed_at: AwareDatetime
    method: str
    prior_exposure: str
    external_reports_consulted: Literal[False]
    scope: str
    normalization: str
    candidate: Asset
    packet_manifest: Asset
    packet_preparation: Asset
    inspection: Asset
    provenance: Provenance
    pages: list[Page]
    checked_passages: list[Passage]
    structural_links: list[Link]
    dates: list[DateStatement]
    findings: list[Finding]
    substantive_candidate_corrections: list[str]
    table_count: Literal[0]
    limitations: list[str]


class Crop(Strict):
    """Exact original pixel slice used after full-page review."""
    id: str
    page: int
    input_path: str
    input_sha256: str
    pixel_box: list[int]
    output_path: str
    output_sha256: str
    method: str


class Inspection(Strict):
    """Actual reviewer attestation recorded after image tool use, not tool-authenticated chronology."""
    reviewer: Literal['Plato']
    recorded_at: AwareDatetime
    method: Literal['direct_view_image_full_pages_then_native_comparison_and_crops']
    full_pages: list[Asset]
    crops: list[Crop]
    full_pages_displayed_size: str
    prior_exposure: str
    native_candidate_read_after_full_images: Literal[True]
    external_reports_consulted: Literal[False]
    chronology_limit: str


class Manifest(Strict):
    """Closed payload inventory excluding itself only."""
    schema_version: Literal[1]
    status: Literal['frozen_source_fidelity_review_not_current_law']
    created_at: AwareDatetime
    files: list[Asset]


class Validation(Strict):
    """Recorded mechanical checks, separate from the visual attestation."""
    recorded_at: AwareDatetime
    status: Literal['passed']
    pages: Literal[7]
    native_bytes: Literal[19118]
    candidate_bytes: Literal[19272]
    passages: int
    native_lines: int
    crop_count: Literal[4]
    tests_run: int
    checks: list[str]
    limitations: list[str]
