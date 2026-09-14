"""Strict bounded independent transaction review records."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undeclared fields and scalar coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Hash-bound copied evidence member."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Source(Strict):
    """Exact proposed source and authority, not an intake receipt."""
    source_id: str
    authority_id: Literal['CO-COUNTY-GUNNISON']
    layer_id: Literal['08_County_Authorities']
    sha256: str
    size_bytes: int
    pages: int
    original_filename: str
    original_acquisition_at_verified: None


class Audit(Strict):
    """Agent-attributed review conclusion with explicit execution limits."""
    schema_version: Literal[1]
    reviewer: Literal['Plato']
    agent_path: Literal['/root/state_refresh_plan']
    recorded_at: str
    disposition: Literal['no_blocking_issue_found_fixed_three_source_preparation']
    preparation_directory_claim: str
    reviewed_package: list[Asset]
    sources: list[Source]
    code_reviewed: list[str]
    independent_cases_passed: list[str]
    findings: list[str]
    failed_attempts: list[str]
    limitations: list[str]
    actual_repository_apply_performed: Literal[False]
    public_requests: Literal[0]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]


class Manifest(Strict):
    """Closed audit payload inventory."""
    schema_version: Literal[1]
    files: list[Asset]
    recorded_at: str
