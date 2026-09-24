"""Strict source-review integration evidence; no legal or acquisition promotion."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unknown keys and implicit value coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Exact repository-relative immutable identity."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Check(Strict):
    """Actual local verification outcome and retained output."""

    command: str
    exit_code: Literal[0]
    evidence: Asset
    timing: Asset | None
    scope: str


class Execution(Strict):
    """One accepted review join; original sources and historical scope remain fixed."""

    recorded_at: AwareDatetime
    base_commit: Literal["06504e53ca64734b05eb2362bd48d04b1f223078"]
    source_id: Literal["el-paso-ldc-chapter-2-sd011"]
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    source_sha256: Literal["f3d527fd6a9da5b0043672582dda812dc9c3dfe9958d8b53eec876957ed10953"]
    status: Literal["metadata_only_integration_verified"]
    before_counts: tuple[Literal[70], Literal[37], Literal[33]]
    after_counts: tuple[Literal[70], Literal[38], Literal[32]]
    preserved_authority_joins: Literal[70]
    preserved_review_joins: Literal[37]
    unchanged_other_rows: Literal[69]
    source_passages: Literal[119]
    structural_links: Literal[5]
    snapshot_directory: str
    preimages: list[Asset]
    installed_files: list[Asset]
    unchanged_inputs: list[Asset]
    accepted_review_inputs: list[Asset]
    checks: list[Check]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    coverage_promotion: Literal[False]
    limitations: list[str]


class Manifest(Strict):
    """Closed local receipt payload inventory, excluding only its own bytes."""

    files: list[Asset]
