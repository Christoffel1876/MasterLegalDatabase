"""Typed custody and structural-validation receipts; no visual/legal certification."""
from __future__ import annotations
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Copy(Strict):
    original_path: str
    retained: Asset
    mode: Literal["exact"]


class Custody(Strict):
    captured_at: AwareDatetime
    source_review_sha256: str
    original_root_review_folder: str
    packet_manifest_sha256: str
    items: list[Copy]
    packet_scope: str
    root_visual_claims_independently_repeated: Literal[False]
    public_requests: Literal[0]


class CheckResult(Strict):
    status: Literal["passed_structural_source_bindings_only"]
    source_sha256: str
    source_pages: Literal[6]
    native_bytes: Literal[10216]
    candidate_bytes: Literal[10894]
    physical_table_fragments: Literal[5]
    physical_rows: Literal[75]
    fee_rows: Literal[65]
    native_spans_checked: int
    visibly_blank_cells_as_recorded: Literal[1]
    merged_placeholder_cells: int
    passage_bindings: Literal[27]
    link_bindings: Literal[11]
    crop_pixel_replays: Literal[15]
    footer_limitations_preserved: Literal[6]
    visually_certified_footer_year: None
    new_visual_review_pages: Literal[0]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    translation_equivalence_verified: Literal[False]
    external_reports_consulted: Literal[False]


class RunResult(CheckResult):
    full_page_png_replays: Literal[0, 6]
    public_requests: Literal[0]


class ValidationReceipt(Strict):
    started_at: AwareDatetime
    completed_at: AwareDatetime
    status: Literal["structural_source_replay_passed_visual_judgments_not_repeated"]
    source_review_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    result: RunResult
    tests_passed: Literal[54]
    combined_branch_coverage_percent: float = Field(ge=90, le=100)
    code_and_test_evidence: list[Asset]
    commands: list[str]
    discrepancy_and_resolution: str
    interpretation_limits: list[str]
    canonical_changes: Literal[0]
    public_requests: Literal[0]


class Manifest(Strict):
    status: Literal["FROZEN_INDEPENDENT_STRUCTURAL_VALIDATOR"]
    files: list[Asset]
