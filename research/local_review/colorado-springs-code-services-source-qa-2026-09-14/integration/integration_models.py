"""Strict metadata-only installation and acceptance records."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Disallow unknown fields and coerced scalars."""
    model_config=ConfigDict(extra='forbid',strict=True)


class Asset(Strict):
    """Exact file identity relative to its stated package root."""
    path: str
    sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int=Field(ge=0)


class Preparation(Strict):
    """Preimage receipt captured before any authorized maintained change."""
    recorded_at: str
    source_id: str
    repository_claim: str
    qa_package_claim: str
    accepted_qa_manifest: Asset
    snapshot_path: str
    before: list[Asset]
    planned_maintained_targets: list[str]
    expected_before: list[int]
    expected_after: list[int]
    authorization: str
    legal_currentness: Literal['not_verified']


class Acceptance(Strict):
    """Atlas's separately recorded, source-scoped acceptance."""
    reviewer: Literal['Atlas']
    recorded_by: Literal['Plato']
    recorded_at: str
    disposition: Literal['accepted_source_fidelity_for_metadata_only_review_join']
    source_id: str
    source_sha256: str
    authority_id: str
    source_review: Asset
    source_review_schema: Asset
    frozen_manifest: Asset
    root_direct_image_notes: Asset
    root_full_pages_directly_viewed: list[int]
    root_check_scope: str
    original_review_status_preserved: bool
    external_ebenezer_report_consulted_before_acceptance: Literal[False]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    limitations: list[str]


class Command(Strict):
    """An actual command, interval, status and retained ordinary output."""
    argv: list[str]
    started_at: str
    finished_at: str
    exit_code: int
    log: Asset


class Execution(Strict):
    """Actual installation/check results; no implied publication."""
    status: Literal['installed_and_focused_verified']
    started_at: str
    finished_at: str
    preparation: Asset
    acceptance: Asset
    before: list[Asset]
    after: list[Asset]
    unchanged_schemas: list[Asset]
    source_id: str
    counts: list[int]
    preserved_other_source_rows: int
    preserved_prior_review_joins: int
    preserved_authority_joins: int
    source_row_comparison: str
    prior_review_comparison: str
    raw_manifest_unchanged: bool
    legacy_ledger_unchanged: bool
    tests: list[Command]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    limitations: list[str]


class Inventory(Strict):
    """Closed package inventory, excluding its own file."""
    files: list[Asset]
