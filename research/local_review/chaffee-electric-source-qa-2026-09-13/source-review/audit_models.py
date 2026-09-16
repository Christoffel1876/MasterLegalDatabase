"""Strict independent audit records for an unchanged source-QA draft and revision."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject extra fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact relative file identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """Half-open bytes in the selected transcript, with literal content retained."""
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class Row(Strict):
    """One actual data row, heading row or explicit editorial merged-cell rendering."""
    kind: Literal['header', 'data', 'merged_heading_with_editorial_placeholder']
    cells: list[Span]


class Fragment(Strict):
    """Complete table fragment with original column associations and markup."""
    table_id: str
    block_id: str
    page: int = Field(ge=1, le=7)
    rows: list[Row]


class Finding(Strict):
    """Auditor observation, distinct from original author's claims."""
    id: str
    classification: Literal['structural_omission', 'qualified_printed_glyph', 'confirmed_scope']
    original_evidence: list[Asset]
    description: str
    disposition: str


class Audit(Strict):
    """Source-fidelity review acceptance is bounded and never current-law approval."""
    schema_version: Literal[1]
    reviewer: Literal['Plato']
    recorded_at: str
    status: Literal['accepted_scoped_revision_pending_root_integration']
    source_id: Literal['chaffee-electric-ordinance-2026-01-atlas-directed']
    authority_id: Literal['CO-COUNTY-CHAFFEE']
    source: Asset
    original_review: Asset
    original_transcript: Asset
    selected_review: Asset
    selected_schema: Asset
    selected_transcript: Asset
    copy_receipt: Asset
    revision_receipt: Asset
    inspection: Asset
    original_draft_files_preserved: Literal[70]
    full_pages_inspected: Literal[7]
    supplied_crops_inspected: Literal[9]
    additional_crops_inspected: int
    logical_tables: Literal[7]
    physical_fragments: Literal[8]
    data_rows: Literal[12]
    table_fragments: list[Fragment]
    findings: list[Finding]
    limitations: list[str]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    external_bot_reports_consulted: Literal[False]


class Crop(Strict):
    """Reproducible full-resolution pixel-slice evidence."""
    source_image: Asset
    xyxy: tuple[int, int, int, int]
    crop: Asset
    method: Literal['exact_RGB_pixel_slice_no_resampling']


class Inspection(Strict):
    """Actual reviewer image inspection recorded retrospectively."""
    reviewer: Literal['Plato']
    recorded_at: str
    method: str
    full_pages: list[Asset]
    supplied_crops: list[Asset]
    supplemental_crops: list[Crop]
    uncertainty: str


class Manifest(Strict):
    """Closed audit inventory, excluding only itself and schema."""
    status: Literal['frozen_source_audit_not_current_law']
    created_at: str
    files: list[Asset]


class GapProof(Strict):
    """Reproducible historical failure without editing the initial record."""
    checked_at: str
    original_review: Asset
    original_transcript: Asset
    last_recorded_block_end: int
    transcript_bytes: int
    unrepresented_suffix: Span
    observed_error: Literal['Uncovered terminal paragraph']
    disposition: Literal['repaired_only_in_separate_root_revision']


class Checks(Strict):
    """Completed checks and their actual test output, with explicit limits."""
    recorded_at: str
    status: Literal['passed']
    test_count: int
    test_log: Asset
    full_pages_rerendered: Literal[7]
    initial_failure_preserved: Literal[True]
    limitations: list[str]
