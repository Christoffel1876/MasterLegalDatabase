"""Strict records for the bounded post-report reconciliation audit."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    """Reject undeclared fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """An immutable package-relative byte binding."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

    @field_validator('path')
    @classmethod
    def safe_path(cls, value: str) -> str:
        """Forbid absolute, alias, traversal and platform-dependent paths."""
        if value.startswith('/') or '\\' in value:
            raise ValueError('unsafe path')
        if any(p in ('', '.', '..') for p in value.split('/')):
            raise ValueError('unsafe path component')
        return value


class FindingCheck(Strict):
    """A reported claim and the scope of this independent check."""
    finding_id: str = Field(pattern=r'^EB02[56]-P2-00[1-9]$')
    reported_classification: Literal['critical', 'minor']
    disposition: str
    report_claim_matches: Literal[True]
    evidence_hashes_match: Literal[True]
    visual_evidence: list[str]
    observation: str
    actionable_issue: str | None


class Audit(Strict):
    """No assertion of process independence or current law."""
    recorded_at: datetime
    reviewer: Literal['Popper']
    status: Literal['no_actionable_issue_in_recorded_scope']
    reconciliation: Asset
    reconciliation_inventory: Asset
    source_audit_manifest_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    findings: list[FindingCheck]
    directly_viewed: list[Asset]
    delivered_bindings_checked: Literal[124]
    limitations: list[str]
    public_requests: Literal[0]
    repository_edits: Literal[False]
    legal_currentness: Literal['not_verified']
    translation_equivalence_verified: Literal[False]
    historical_execution_independence_established: Literal[False]


class Manifest(Strict):
    """Closed evidence inventory; manifest excludes its own bytes."""
    files: list[Asset]
