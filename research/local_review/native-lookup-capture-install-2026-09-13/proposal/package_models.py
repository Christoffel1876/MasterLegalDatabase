"""Strict custody records for a prepared, uninstalled native lookup repair."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Asset(BaseModel):
    """One exact ordinary payload file, relative to the handoff root."""
    model_config = ConfigDict(strict=True, extra="forbid")
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class TestRun(BaseModel):
    """A measured run bound to its actual implementation and unchanged log."""
    model_config = ConfigDict(strict=True, extra="forbid")
    implementation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    log: Asset
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    deselected: int = Field(ge=0)
    qualification: str


class Verification(BaseModel):
    """Bounded technical results; no installation or legal-effect assertion."""
    model_config = ConfigDict(strict=True, extra="forbid")
    frozen_at: AwareDatetime
    status: Literal["prepared_pending_independent_root_acceptance"]
    preimage: Asset
    proposed: Asset
    tests: Asset
    documentation: Asset
    historical_audit_manifest: Asset
    measured_runs: list[TestRun]
    coverage: Asset
    branch_inclusive_percent: float = Field(ge=0, le=100)
    original_classes_unchanged: int
    douglas_pueblo_functions_unchanged: list[str]
    main_function_unchanged: Literal[True]
    normal_output_fixture_files: Literal[18]
    source_schemas_unchanged: Literal[True]
    public_requests: Literal[0]
    production_writes: Literal[0]
    legal_currentness: Literal["not_verified"]
    limitations: list[str]


class Manifest(BaseModel):
    """Closed file inventory with external custody digest supplied at handoff."""
    model_config = ConfigDict(strict=True, extra="forbid")
    frozen_at: AwareDatetime
    status: Literal["prepared_pending_independent_root_acceptance"]
    files: list[Asset]
