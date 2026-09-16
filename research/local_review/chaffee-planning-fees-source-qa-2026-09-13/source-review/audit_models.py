"""Strict independent audit of two retained source pages and their native associations."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undeclared or coerced audit fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact retained ordinary file."""
    path: str
    sha256:str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Inventory(Strict):
    """Closed inventory of all independent packet payloads."""
    status: Literal['independent_source_audit_no_legal_promotion']
    files: list[Asset]


class Finding(Strict):
    """Actionable source or evidence qualification, never a silent correction."""
    id: str
    severity: Literal['correction', 'qualification', 'no_issue']
    statement: str
    evidence: list[str]


class Audit(Strict):
    """Source checks distinguished from original reviewer process claims."""
    schema_version: Literal['1.0']
    source_id: Literal['chaffee-planning-application-fees-atlas-directed']
    authority_id: Literal['CO-COUNTY-CHAFFEE']
    source_sha256:str
    draft_qa: Asset
    examined_pages: Literal[2]
    examined_existing_crops: Literal[8]
    fee_rows: Literal[49]
    groups: Literal[10]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    method: Literal['candidate_aware_independent_direct_image_review']
    created_at: str
    findings: list[Finding]
    custody_evidence: list[Asset]
    limitations: list[str]


class RowGeometry(Strict):
    """Original PDF point coordinates of each complete application/fee native line."""
    row_id: str
    page: int
    application_boxes: list[list[float]]
    fee_box: list[float]
    fee_start: int
    application_end: int


class Geometry(Strict):
    """Reproducible geometry, not an independent glyph-recognition result."""
    source_sha256:str
    engine: Literal['PyMuPDF 1.28.2 flags195 sortFalse']
    coordinate_basis: Literal['PDF points, upper-left origin']
    rows: list[RowGeometry] = Field(min_length=49, max_length=49)


class HeaderProof(Strict):
    """Exact added pixel crop, separate from native or source text."""
    source: Asset
    crop: Asset
    rect: tuple[Literal[0], Literal[0], Literal[2550], Literal[350]]
    observation: str


class ValidationReceipt(Strict):
    """Observed local checks; no acquisition or legal conclusion."""
    status: Literal['pass']
    recorded_at: str
    test_count: int
    combined_branch_coverage_percent: float
    tested_code: list[Asset]
    checks: list[str]
    limitations: list[str]
