"""Strict evidence for independent review of the additive fixed-source revision."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int

class Review(Strict):
    status: Literal['NO_BLOCKING_FINDING_IN_REVIEWED_FIXED_SOURCE_REVISION']
    observed_at: AwareDatetime
    reviewed_inputs: list[Asset]
    input_hashes_unchanged_during_final_test_and_preflight: Literal[True]
    canonical_guard_hashes: list[Asset]
    canonical_guards_unchanged_by_readonly_preflight: Literal[True]
    independent_tests_passed: Literal[13]
    resolved_counterexample_seams: list[str]
    other_checks: list[str]
    actual_readonly_preflight: str
    original_blocking_audit_manifest_sha256: str
    revision_final_manifest_included_in_this_review: Literal[False]
    scope_limits: list[str]
    canonical_writes: Literal[0]
    public_requests: Literal[0]

class Manifest(Strict):
    status: Literal['FROZEN_INDEPENDENT_REVISION_REVIEW']
    files: list[Asset]
