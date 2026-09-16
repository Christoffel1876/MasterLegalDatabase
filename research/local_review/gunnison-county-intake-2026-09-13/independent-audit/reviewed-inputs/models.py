"""Fixed three-source Gunnison preservation contract; no execution time at preparation."""
from __future__ import annotations
from pathlib import PurePosixPath
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

SourceID = Literal[
    "gunnison-building-fees-resolution-2025-24-sh-ext-003",
    "gunnison-building-code-resolution-2023-22-sh-ext-003",
    "gunnison-iwuic-resolution-2022-33-sh-ext-003",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def safe(cls, value):
        p = PurePosixPath(value)
        if p.is_absolute() or ".." in p.parts or "\\" in value or p.as_posix() != value:
            raise ValueError("unsafe asset path")
        return value


class Baseline(Strict):
    repository_path: str
    preserved: Asset
    records: int | None


class Provenance(Strict):
    source_id: SourceID
    action_id: str
    authority_id: Literal["CO-COUNTY-GUNNISON"]
    source: Asset
    physical_pages: int = Field(ge=1)
    parent: Asset
    parent_url: str
    original_href: str
    visible_label: str
    reservation: Asset
    result: Asset
    public_headers: Asset
    requested_url_reported: str
    final_url_reported: str
    http_status_reported: Literal[200]
    reported_reserved_at: AwareDatetime
    reported_finished_at: AwareDatetime
    verified_original_acquired_at: None
    original_tool_command_retained: Literal[False]
    prior_visually_reviewed_pages: list[int]
    new_visually_reviewed_pages: list[int] = Field(max_length=0)
    prior_role_observations: list[str]
    historical_digest_lines: list[int]
    legal_currentness: Literal["not_verified"]
    limitations: list[str]


class Template(Strict):
    record_id: SourceID
    authority_id: Literal["CO-COUNTY-GUNNISON"]
    layer_id: Literal["08_County_Authorities"]
    official_source_name: str
    official_source_url: None
    acquisition_method: Literal["received_review_package"]
    source: Asset
    original_filename: str
    custody_note: str
    actual_repository_received_at: None
    intake_id: None
    archive_path: None

    @model_validator(mode="after")
    def filename(self):
        if PurePosixPath(self.source.path).name != self.original_filename:
            raise ValueError("original_filename differs from actual incoming basename")
        return self


class Preparation(Strict):
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal["PREPARED_NOT_APPLIED"]
    comparison_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    templates: list[Template] = Field(min_length=3, max_length=3)
    provenance: list[Provenance] = Field(min_length=3, max_length=3)
    baseline: list[Baseline]
    runtime_pins: dict[str, str]
    custody_subset: list[Asset]
    recommendation: Asset
    recommendation_manifest: Asset
    legacy_guard: Asset
    raw_before: int = Field(ge=0)
    ledger_before: int = Field(ge=0)
    raw_after: int = Field(ge=3)
    ledger_after: int = Field(ge=3)
    public_requests: Literal[0]
    canonical_mutations: Literal[0]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]

    @model_validator(mode="after")
    def identities(self):
        if len({t.record_id for t in self.templates}) != 3:
            raise ValueError("duplicate source IDs")
        if len({t.source.sha256 for t in self.templates}) != 3:
            raise ValueError("duplicate source digests")
        if [t.record_id for t in self.templates] != [p.source_id for p in self.provenance]:
            raise ValueError("provenance source order differs")
        if any(t.source != p.source for t, p in zip(self.templates, self.provenance)):
            raise ValueError("provenance source binding differs")
        if self.raw_after != self.raw_before + 3 or self.ledger_after != self.ledger_before + 3:
            raise ValueError("fixed three-source count differs")
        return self


class Manifest(Strict):
    schema_version: Literal[1]
    files: list[Asset]
    scope: Literal["closed_preparation_excluding_future_execution"]


class CommandResult(Strict):
    label: Literal["focused_tests", "live_read_only_preflight"]
    command: list[str]
    working_directory: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    exit_code: Literal[0]
    stdout: Asset
    stderr: Asset


class Validation(Strict):
    status: Literal["passed_preparation_only"]
    completed_at: AwareDatetime
    preparation_sha256: str
    transaction_sha256: str
    results: list[CommandResult]
    test_count: Literal[64]
    combined_branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    coverage: Asset
    canonical_managed_sha256_before: dict[str, str]
    canonical_managed_sha256_after: dict[str, str]
    canonical_managed_bytes_unchanged: Literal[True]
    actual_execution_directory_created: Literal[False]
    limitations: list[str]
