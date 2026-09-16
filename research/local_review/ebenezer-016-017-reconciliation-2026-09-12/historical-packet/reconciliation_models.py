"""Strict additive reconciliation and closed-package contracts."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    """Reject undeclared fields and silent coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact file identity within this new package."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Copy(Strict):
    """Historical source location is context, not a live validation dependency."""
    historical_path: str
    frozen: Asset


class Decision(Strict):
    """A specific report claim and direct source-page disposition."""
    claim_id: str
    report: str
    report_line: int = Field(ge=1)
    report_line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    disposition: Literal['candidate_supported', 'confirmed_difference', 'qualified',
                         'source_feature', 'packaging_observation', 'unresolved',
                         'rejected_external_claim']
    source_physical_pages: list[int]
    source_basis: str


class Document(Strict):
    """Separate actual local custody, assisted chronology and direct Atlas review."""
    assignment_id: Literal['EB-PDF-016', 'EB-PDF-017']
    source_id: str
    authority_id: Literal['CO-MUNICIPAL-GREELEY']
    report: Asset
    completion_receipt: Asset
    source_pdf: Asset
    candidate: Asset
    source_images: list[Asset]
    baseline_review: Asset
    page_count: int
    direct_review_pages: list[int]
    review_method: str
    external_method: Literal['caption_mediated_source_first']
    external_chronology_verified: Literal[False]
    original_pdf_rehashed_by_atlas: Literal[True]
    external_pdf_presence_claim: str
    source_and_candidate_changed: Literal[False]
    decisions: list[Decision]
    source_role: str
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]


class Reconciliation(Strict):
    """Additive review only; does not alter prior frozen QA or canonical records."""
    schema_version: Literal[1]
    received_at: AwareDatetime
    prepared_at: AwareDatetime
    status: Literal['external_reviews_reconciled_with_qualifications']
    copies: list[Copy]
    documents: list[Document]
    supplementary_custody: str
    missing_claimed_artifacts: list[str]
    limitations: list[str]


class Binding(Strict):
    """Exact historical line identified by a later qualification."""
    path: str
    line: int = Field(ge=1)
    line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

class TitleArtifact(Strict):
    """Native text exists but is not visible in the directly reviewed full render."""
    physical_page: Literal[2, 3]
    image: Asset
    native_text: str
    native_start_byte: int
    native_end_byte_exclusive: int
    candidate_start_byte: int
    candidate_end_byte_exclusive: int
    text_sha256: str
    prior_visibility_claim: Literal['visible']
    atlas_render_observation: Literal['not_visible_in_checked_render']

class Supplement(Strict):
    """Qualify a newly found baseline error without rewriting its frozen evidence."""
    recorded_at: AwareDatetime
    status: Literal['additive_baseline_visibility_correction']
    bindings: list[Binding]
    native_title_artifacts: list[TitleArtifact]
    findings: list[str]
    source_and_candidate_changed: Literal[False]
    frozen_baseline_changed: Literal[False]
    legal_currentness: Literal['not_verified']

class Manifest(Strict):
    """Closed payload inventory; excludes only this manifest and its schema."""
    frozen_at: AwareDatetime
    status: Literal['closed_root_reconciliation']
    files: list[Asset]
    excluded: list[str]
    legal_currentness: Literal['not_verified']
