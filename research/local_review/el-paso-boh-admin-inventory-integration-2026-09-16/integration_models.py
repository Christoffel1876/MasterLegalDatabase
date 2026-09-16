"""Strict actual integration receipt, preserving predecessor and currentness limits."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unknown keys and implicit coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Repository-relative exact file identity."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Start(Strict):
    """Recorded application checkpoint after preimage capture and initial file writes."""
    started_at: AwareDatetime
    scope: Literal['one metadata review join only']
    preimage_directory: str
    before: list[Asset]
    accepted_source: Asset


class Check(Strict):
    """Actual command result; absent exact start/end timestamps remain null."""
    command: str
    exit_code: Literal[0]
    evidence: Asset
    started_at: None
    finished_at: None
    qualification: str


class Execution(Strict):
    """One installed review link with exact unchanged baseline checks."""
    schema_version: Literal[1]
    recorded_at: AwareDatetime
    status: Literal['installed_and_focused_checks_passed_metadata_only']
    source_id: Literal['el-paso-boh-admin-regulations-sd011']
    authority_id: Literal['CO-COUNTY-EL_PASO']
    source_sha256: Literal['64d72ce1f7783dcf7fb5a3f6956e8ba4845c4839318613a1dee09d99716625d7']
    accepted_source: Asset
    accepted_wrapper_inventory: Asset
    prepared_plan: Asset
    application_checkpoint: Asset
    snapshot_directory: str
    snapshot_files: list[Asset]
    installed_files: list[Asset]
    unchanged_required_files: list[Asset]
    before_originals: Literal[70]
    before_reviewed: Literal[36]
    before_unmapped: Literal[34]
    after_originals: Literal[70]
    after_reviewed: Literal[37]
    after_unmapped: Literal[33]
    preserved_authority_joins: Literal[70]
    preserved_review_joins: Literal[36]
    unchanged_other_rows: Literal[69]
    target_only_changed_fields: list[Literal['reviews', 'review_status']]
    source_review_artifact: Asset
    source_review_schema: Asset
    checks: list[Check]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    coverage_promotion: Literal[False]
    limitations: list[str]


class Manifest(Strict):
    """Closed compact receipt folder; manifest excludes itself only."""
    schema_version: Literal[1]
    recorded_at: AwareDatetime
    files: list[Asset]
