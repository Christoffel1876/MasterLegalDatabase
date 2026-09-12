"""Typed custody for a prepared, unapplied transaction and its validation evidence."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject unexpected evidence fields and scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Bind one ordinary file to exact bytes."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Baseline(Strict):
    """Preserve the real repository file hashes across a read-only execution."""

    before: Asset
    after: Asset

    @model_validator(mode="after")
    def unchanged(self) -> Baseline:
        """Reject any actual baseline change during this preparation."""
        if self.before != self.after:
            raise ValueError("Real repository baseline changed")
        return self


class Invocation(Strict):
    """Record one observed command without inferring unrecorded test timestamps."""

    argv: list[str]
    cwd: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    exit_code: Literal[0]
    stdout: Asset
    stderr: Asset


class Validation(Strict):
    """Separate actual read-only validation from synthetic fixture application."""

    schema_version: Literal[1]
    status: Literal["prepared_not_applied"]
    frozen_at: AwareDatetime
    implementation: Asset
    tests: Asset
    fixture_test_log: Asset
    fixture_tests_passed: Literal[30]
    fixture_test_warnings: Literal[5]
    fixture_seconds_reported: Literal[10.7]
    combined_coverage: Asset
    combined_coverage_percent: float = Field(ge=90, le=100)
    coverage_scope: Literal["fixture_tests_plus_actual_read_only_cli"]
    actual_dry_run: Invocation
    baselines: list[Baseline] = Field(min_length=3, max_length=3)
    baseline_raw_records: Literal[46]
    baseline_ledger_records: Literal[47]
    real_repository_apply_performed: Literal[False]
    real_execution_directory_exists: Literal[False]
    expected_after_if_applied: Literal["59 raw / 60 ledger; same one missing historical original"]
    full_corpus_validation: Literal["not_run_by_this_subtask"]
    tested_recovery_scope: Literal["process_interruption_and_deterministic_replay"]
    power_loss_durability_verified: Literal[False]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


class Package(Strict):
    """Freeze distributable assets while declaring excluded local test/runtime paths."""

    schema_version: Literal[1]
    status: Literal["prepared_not_applied"]
    frozen_at: AwareDatetime
    files: list[Asset] = Field(min_length=150)
    excluded_prefixes: list[str]
    excluded_files: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]

