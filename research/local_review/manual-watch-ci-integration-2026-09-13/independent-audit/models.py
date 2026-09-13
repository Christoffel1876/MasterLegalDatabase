"""Typed public correction and final87-input watch review; no user-file content."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undeclared or coerced publication evidence."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact retained ordinary file identity."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class HistoricalSubset(Strict):
    """An exact one-file omission, never a claim that original closure still passes."""
    root: Literal['historical-audit']
    original_manifest: Asset
    excluded_original_members: list[Asset] = Field(min_length=1, max_length=1)
    complete_original_packet_retained: Literal[False]
    historical_verifiers_must_not_be_executed: Literal[True]
    reason: str


class PinCheck(Strict):
    """Each final explicit repository dependency must exist in ordinary Git storage."""
    path: str
    sha256: str
    size_bytes: int
    tracked: Literal[True]
    lfs_filter: Literal['unspecified']


class Receipt(Strict):
    """Latest operational verdict supersedes the invalid88-pin checkout conclusion."""
    status: Literal['reviewed_prepared_only_no_runtime_blocker']
    recorded_at: str
    historical: HistoricalSubset
    corrected_runner: Asset
    corrected_config: Asset
    final_explicit_pin_count: Literal[87]
    pin_checks: list[PinCheck] = Field(min_length=87, max_length=87)
    source_selection_unchanged: Literal[True]
    excluded_file_present_in_sparse_copy: Literal[False]
    actual_readiness_processes: Literal[4]
    focused_tests: int
    independent_tests: int
    schema_exports_match: Literal[True]
    corrections: list[str]
    evidence: list[Asset]
    public_source_requests: Literal[0]
    canonical_changes: Literal[False]
    linux_execution_verified: Literal[False]
    installed_or_enabled_by_audit: Literal[False]
    legal_currentness: Literal['not_verified']
    limitations: list[str]


class Inventory(Strict):
    """Closed public payload set with no excluded file bytes under any name."""
    kind: Literal['public_manual_watch_ci_review']
    files: list[Asset]
