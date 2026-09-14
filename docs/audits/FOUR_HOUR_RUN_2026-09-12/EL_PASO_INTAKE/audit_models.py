"""Strict acceptance evidence for an additive custody inventory update."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Asset(BaseModel):
    """An exact byte identity relative to the declared evidence root."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class InventoryUpdate(BaseModel):
    """Record only the tested additive change and unchanged legal-reliance boundary."""
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal[1]
    checked_at: AwareDatetime
    old_sources: Literal[46]
    new_sources: Literal[59]
    old_review_linked: Literal[19]
    new_review_linked: Literal[19]
    old_metadata_only: Literal[27]
    new_metadata_only: Literal[40]
    old_source_rows_identical: Literal[True]
    old_authority_joins_identical: Literal[True]
    old_review_joins_identical: Literal[True]
    added_ids: list[str] = Field(min_length=13, max_length=13)
    added_authority: Literal['CO-COUNTY-EL_PASO']
    added_review_links: Literal[0]
    added_verified_http_bindings: Literal[0]
    portable_package_manifest: Asset
    portable_receipt: Asset
    old_files: list[Asset]
    new_files: list[Asset]
    live_legacy_coverage_ledger: Asset
    package_local_snapshot_paths: list[str]
    existing_inventory_tests_passed: Literal[60]
    actual_join_fixture_tests_passed: Literal[5]
    deterministic_check_passed: Literal[True]
    portable_check_passed: Literal[True]
    actual_archive_check_passed: Literal[True]
    inherited_full_corpus_errors: Literal[2]
    full_corpus_valid: Literal[False]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    coverage_promotion: Literal[False]
