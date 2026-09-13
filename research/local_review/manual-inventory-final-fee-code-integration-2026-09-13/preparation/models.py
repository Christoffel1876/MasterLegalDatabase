"""Strict receipts for a fixed metadata-only inventory integration."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unexpected fields and implicit coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact local bytes with a declared relative path."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Review(Strict):
    """Bind one exact accepted source QA without changing historical fields."""
    source_id: str
    source_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    authority_id: str
    acceptance: Asset
    acceptance_schema: Asset
    review: Asset
    review_schema: Asset
    review_kind: Literal['checked_passages', 'checked_tables']


class Target(Strict):
    """Exactly one authorized maintained target with immutable before and after copies."""
    repository_path: str
    before: Asset
    after: Asset


class Preparation(Strict):
    """Tested proposed files, not evidence that an installation already occurred."""
    recorded_at: AwareDatetime
    status: Literal['prepared_tested_not_installed']
    reviewer: Literal['Plato']
    targets: list[Target]
    reviews: list[Review]
    actual_intake_receipt: Asset
    actual_intake_received_at: AwareDatetime
    raw_manifest: Asset
    prior_sources: Literal[69]
    prior_review_links: Literal[33]
    proposed_sources: Literal[70]
    proposed_review_links: Literal[35]
    proposed_unmapped: Literal[35]
    old_authority_joins_preserved: Literal[69]
    old_review_joins_preserved: Literal[33]
    only_old_row_with_new_review: Literal['gunnison-building-code-resolution-2023-22-sh-ext-003']
    test_log: Asset
    initial_failure_log: Asset | None
    coverage: Asset
    passed_tests: int = Field(ge=129)
    branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    limitations: list[str]
    public_requests: Literal[0]
    canonical_source_writes: Literal[0]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]


class InstallReceipt(Strict):
    """Actual metadata installation with preserved preimages and completed local check."""
    started_at: AwareDatetime
    completed_at: AwareDatetime
    status: Literal['installed_and_verified']
    preparation_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    targets: list[Target]
    snapshot_directory: str
    verifier_exit_code: Literal[0]
    verifier_stdout: Asset
    verifier_stderr: Asset
    raw_manifest_before: Asset
    raw_manifest_after: Asset
    source_files_changed: Literal[False]
    records: Literal[70]
    reviewed: Literal[35]
    unmapped: Literal[35]


class Manifest(Strict):
    """Preparation inventory excludes only final inventory and later execution evidence."""
    recorded_at: AwareDatetime
    status: Literal['closed_inventory_preparation']
    files: list[Asset]
    exclusions: Literal['FINAL_MANIFEST.json, FINAL_MANIFEST.schema.json, execution/**']
