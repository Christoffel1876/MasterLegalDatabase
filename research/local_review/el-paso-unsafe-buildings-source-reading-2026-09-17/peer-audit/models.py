"""Strict independent visual-audit and mechanical-binding records."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Forbid unrecognized fields and implicit scalar coercion."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact retained bytes, not a claim about legal meaning."""

    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class PageCheck(Strict):
    """Human visual judgment on a complete physical page."""

    physical_page: int = Field(ge=1, le=8)
    image: Asset
    full_page_directly_viewed: Literal[True] = True
    comparison: str
    uncertainty: str


class Observation(Strict):
    """A confirmed bounded source observation or unresolved limitation."""

    id: str
    physical_pages: list[int]
    result: Literal['confirmed', 'qualified']
    description: str
    legal_inference: Literal[False] = False


class Crop(Strict):
    """Direct PDF crop inspected as supplementary visual evidence."""

    physical_page: int = Field(ge=1, le=8)
    rectangle_points: list[float] = Field(min_length=4, max_length=4)
    matrix_scale: Literal[3.0] = 3.0
    renderer: Literal['PyMuPDF 1.28.2'] = 'PyMuPDF 1.28.2'
    image: Asset
    directly_viewed: Literal[True] = True


class CanonicalBinding(Strict):
    """Tracked canonical identity checked without rewriting prior records."""

    commit: str
    raw_manifest: Asset
    raw_line: int
    intake_ledger: Asset
    ledger_line: int
    source: Asset
    inventory: Asset
    inventory_source_index: int
    record_id: str
    authority_id: str
    exact_raw_and_ledger_line_match: Literal[True] = True
    exact_canonical_source_match: Literal[True] = True
    actual_repository_received_at: str
    acquisition_method: Literal['received_review_package']
    verified_http_acquired_at: None = None


class Replay(Strict):
    """Observed mechanical replay, distinct from direct visual inspection."""

    command: list[str]
    cwd: str
    exit_code: Literal[0]
    stdout: str
    stderr: str
    scope: str


class Audit(Strict):
    """Bounded peer review of the frozen Atlas research derivative."""

    schema_version: Literal[1] = 1
    reviewer: Literal['Ptolemy'] = 'Ptolemy'
    prepared_at: str
    source_id: Literal['el-paso-unsafe-buildings-18-03-sd011']
    authority_id: Literal['CO-COUNTY-EL_PASO']
    target_manifest: Asset
    source: Asset
    review: Asset
    corrected_reading: Asset
    native: Asset
    pages: list[PageCheck]
    supplementary_crops: list[Crop]
    observations: list[Observation]
    canonical: CanonicalBinding
    replay: Replay
    method: str
    visual_order: str
    external_review_consulted: Literal[False] = False
    actionable_discrepancies: list[str]
    disposition: Literal['no_actionable_discrepancy_within_stated_scope']
    limitations: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    canonical_changed: Literal[False] = False


class Manifest(Strict):
    """Closed audit inventory including the exact reviewed predecessor."""

    schema_version: Literal[1] = 1
    exclusions: list[str]
    files: list[Asset]
