"""Strict records for the bounded packaging-scanner audit."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unknown keys and coercion in audit records."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """One unchanged local payload relative to this audit."""

    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Finding(Strict):
    """A scoped finding and its observed or proposed disposition."""

    id: str
    status: Literal['reproduced', 'verified', 'qualified', 'proposed']
    statement: str
    evidence: list[str]


class Audit(Strict):
    """Agent-authored review, distinct from publication authorization."""

    reviewer: Literal['Plato']
    recorded_at: AwareDatetime
    status: Literal['proposed_revision_validated_not_installed']
    original_scanner: Asset
    proposed_scanner: Asset
    original_scan: Asset
    proposed_scan: Asset
    findings: list[Finding]
    commands: list[str]
    focused_tests_passed: int = Field(ge=0)
    production_mutations: Literal[0]
    public_requests: Literal[0]
    git_mutations: Literal[0]
    limitations: list[str]


class Manifest(Strict):
    """Closed payload inventory, excluding only this manifest itself."""

    recorded_at: AwareDatetime
    status: Literal['frozen_independent_audit']
    files: list[Asset]
