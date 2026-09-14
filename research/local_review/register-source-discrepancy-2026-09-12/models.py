"""Strict custody models for a public subset of the Register diagnosis."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    """Reject unknown fields and coercions in newly written custody records."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """An ordinary file inside this closed package."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(ge=0, le=50_000_000)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        """Require a normalized, nonempty relative POSIX path."""
        path = PurePosixPath(value)
        if not value or path.is_absolute() or str(path) != value or ".." in path.parts:
            raise ValueError("Invalid relative evidence path")
        if "\\" in value:
            raise ValueError("Backslashes are not evidence separators")
        return value


class Copy(Asset):
    """An exact copy with an original path retained only as a custody claim."""

    original_path: str


class Exclusion(Strict):
    """A private file omitted from this explicitly incomplete export."""

    original_path: str
    original_relative_path: str
    original_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_bytes: int = Field(gt=0)
    would_be_package_path: str
    public_derivative: Asset
    removed_field_names: list[Literal["set-cookie"]] = Field(min_length=1, max_length=1)
    checked_at: AwareDatetime
    local_exact_derivative_replay: Literal[True]
    procedure: Literal["remove named sensitive fields and folded continuations; keep other bytes"]
    portable_raw_replay: Literal[False]


class Subset(Strict):
    """A frozen selection, not a replacement for the complete original packet."""

    original_root: str
    package_prefix: str
    original_file_count: int = Field(gt=0)
    copied_file_count: int = Field(gt=0)
    excluded_file_count: int = Field(gt=0)
    original_complete_manifest_sha256: str | None
    complete_original_packet_exported: Literal[False]


class PassiveView(Strict):
    """An escaped byte-faithful text display with active source markup disabled."""

    source: Asset
    view: Asset
    encoding: Literal["iso-8859-1"]
    method: Literal["HTML-escape entire decoded original inside pre; restrictive CSP"]


class Custody(Strict):
    """Qualified preservation of source evidence, without a notice status decision."""

    packaged_at: AwareDatetime
    status: Literal["public_subset_source_discrepancy_preserved_legal_status_unresolved"]
    legal_currentness: Literal["not_verified"]
    new_network_requests: Literal[0]
    canonical_notice_mutations: Literal[False]
    source_subsets: list[Subset] = Field(min_length=2, max_length=2)
    copies: list[Copy] = Field(min_length=115, max_length=115)
    exclusions: list[Exclusion] = Field(min_length=3, max_length=3)
    passive_views: list[PassiveView] = Field(min_length=6, max_length=6)
    local_selected_payload_scan: Literal["no omitted header value found in selected payloads"]
    scan_scope: str
    limitations: list[str] = Field(min_length=5)


class Manifest(Strict):
    """Inventory of every package payload except this manifest itself."""

    status: Literal["closed_public_subset"]
    assets: list[Asset]


class CheckResult(Strict):
    """A reproducible source and custody check, not a currentness determination."""

    status: Literal["verified_offline_public_subset"]
    payloads: int
    exact_copied_files: Literal[115]
    excluded_private_headers: Literal[3]
    archived_notice_rows: Literal[50]
    fresh_notice_rows: Literal[48]
    common_notice_rows_unchanged_except_number: Literal[48]
    missing_notice_ids: list[str] = Field(min_length=2, max_length=2)
    unchanged_detail_fields_per_docket: dict[str, int]
    original_detail_bodies_byte_equal: Literal[False]
    raw_header_derivation_replayed_in_portable_package: Literal[False]
    legal_currentness: Literal["not_verified"]
    new_network_requests: Literal[0]
