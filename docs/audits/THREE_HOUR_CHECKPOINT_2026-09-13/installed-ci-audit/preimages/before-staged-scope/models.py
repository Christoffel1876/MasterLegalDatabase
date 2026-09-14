"""Strict records for a read-only installed CI and publication-boundary check."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undeclared or coerced audit fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact ordinary file identity, interpreted relative to its declared scope."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class ScanEntry(Strict):
    """Size-screen every file for exact excluded-byte identity without broad body reads."""
    path: str
    size_bytes: int = Field(ge=0)
    excluded_basename_match: bool
    excluded_size_match: bool
    sha256_if_size_matches: str | None


class Acceptance(Strict):
    """Bounded current installation evidence; neither deployment nor source certification."""
    status: Literal['accepted_with_recorded_limits']
    checked_at: str
    repository_head: str
    installed_files: list[Asset] = Field(min_length=10, max_length=10)
    immutable_inputs: list[Asset] = Field(min_length=87, max_length=87)
    all_87_inputs_tracked_non_lfs: Literal[True]
    wrapper_path: str
    wrapper_inventory: Asset
    wrapper_payload_count: Literal[494]
    installation: Asset
    proposal_manifest_sha256: str
    independent_manifest_sha256: str
    discovered_untracked_path_count: int
    scanned_wrapper_roots: list[str]
    scanned_file_count: int
    scanned_byte_sizes_total: int
    exact_digest_candidates: int
    excluded_basename_hits: list[str] = Field(max_length=0)
    excluded_content_hits: list[str] = Field(max_length=0)
    original_user_file: Asset
    original_matches_prior_identity: Literal[True]
    schema_validation_passed: Literal[True]
    copied_public_verifiers_passed: Literal[True]
    source_requests: Literal[0]
    canonical_writes: Literal[False]
    full_suite_rerun: Literal[False]
    deployment_verified: Literal[False]
    linux_execution_verified: Literal[False]
    legal_currentness: Literal['not_verified']
    findings: list[str] = Field(max_length=0)
    limitations: list[str]


class Inventory(Strict):
    """Closed metadata-only audit payload inventory."""
    files: list[Asset]
