"""Strict evidence records for the prepared, unapplied two-source transaction."""
from __future__ import annotations

from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject unknown evidence fields and scalar coercion."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """One ordinary file bound to its exact bytes."""
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Baseline(Strict):
    """Record the unchanged actual repository inputs across read-only validation."""
    before: Asset
    after: Asset

    @model_validator(mode="after")
    def unchanged(self) -> Baseline:
        """Reject any claimed baseline change during preparation."""
        if self.before != self.after:
            raise ValueError("Real repository baseline changed")
        return self


class Invocation(Strict):
    """Bind a locally observed command and its exact output streams."""
    argv: list[str]
    cwd: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    exit_code: Literal[0]
    stdout: Asset
    stderr: Asset

    @model_validator(mode="after")
    def ordered(self) -> Invocation:
        """Retain actual observed command order."""
        if self.completed_at < self.started_at:
            raise ValueError("Completion precedes invocation")
        return self


class Validation(Strict):
    """Distinguish synthetic apply tests from actual read-only repository checks."""
    schema_version: Literal[1]
    status: Literal["prepared_not_applied"]
    frozen_at: AwareDatetime
    implementation: Asset
    tests: Asset
    focused_tests: Invocation
    tests_passed: Literal[56]
    test_warnings: Literal[5]
    coverage: Asset
    branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    coverage_scope: Literal["56 focused tests, including actual read-only two-record preflight"]
    actual_dry_run: Invocation
    baselines: list[Baseline] = Field(min_length=3, max_length=3)
    approved_preparation_manifest: Asset
    expected_source_ids: list[str] = Field(min_length=2, max_length=2)
    baseline_raw_records: Literal[59]
    baseline_ledger_records: Literal[60]
    expected_raw_after: Literal[61]
    expected_ledger_after: Literal[62]
    missing_historical_original: Literal["MSI-20260707T221329208329Z-EO-2019-007"]
    real_repository_apply_performed: Literal[False]
    real_execution_directory_exists: Literal[False]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    full_corpus_validation: Literal["not_run_by_this_subtask"]
    tested_recovery_scope: Literal["process_interruption_and_deterministic_replay"]
    power_loss_durability_verified: Literal[False]


class Package(Strict):
    """Closed preparation membership; eventual execution artifacts remain separate."""
    schema_version: Literal[1]
    status: Literal["prepared_not_applied"]
    frozen_at: AwareDatetime
    files: list[Asset] = Field(min_length=90)
    excluded_prefixes: list[Literal["execution/"]]
    excluded_files: list[Literal["FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"]]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
