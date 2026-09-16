"""Types for packaging an unchanged, already completed Atlas source review."""

from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Strict(BaseModel):
    """Reject coercions and unknown record fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """An ordinary package-relative file and its exact byte identity."""

    path: str
    sha256: Digest
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def relative_path(cls, value: str) -> str:
        """Reject paths that could escape the portable package."""
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or "\\" in value:
            raise ValueError("ordinary package-relative path required")
        if not value or str(path) != value:
            raise ValueError("normalized nonempty path required")
        return value


class PackageStatus(Strict):
    """Packaging status without replacing the retained review or provenance."""

    package_id: Literal["weld-building-fees-atlas-source-review-2026-09-11"]
    packaged_at: datetime
    source_id: Literal["weld-building-fees-sd008-01"]
    source_sha256: Literal["8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27"]
    historical_handoff_path: str
    frozen_file_count: Literal[49]
    frozen_total_bytes: Literal[5634545]
    frozen_inventory: Asset
    frozen_review: Asset
    physical_pages_reviewed: Literal[5]
    native_bytes_retained: Literal[14311]
    native_byte_changes: Literal[0]
    fee_value_referral_rows: Literal[107]
    valuation_matrix_cells: Literal[252]
    review_mode: Literal["atlas_candidate_aware_not_blind"]
    source_qa_status: Literal["internal_source_qa_complete"]
    external_assignment: None
    acquisition_method: Literal["received_review_package"]
    successful_requested_version_and_final_url: Literal["unconfirmed"]
    original_http_acquisition_time: None
    official_source_url: None
    repository_received_at: datetime
    source_face_label: Literal["JANUARY 2026"]
    source_revision_notation: Literal["Revised 012/25"]
    date_interpretation: Literal["schedule_label_and_unparsed_revision_only"]
    source_pipeline_status: Literal["archived_pending_pipeline"]
    adopted_status: Literal["not_verified"]
    legal_currentness: Literal["not_verified"]
    semantic_or_coverage_promotion: Literal[False]
    limits: list[str] = Field(min_length=1)

    @field_validator("packaged_at", "repository_received_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        """Keep packaging and receipt times explicit and timezone-aware."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone-aware time required")
        return value


class Inventory(Strict):
    """Complete portable inventory, excluding only its own file."""

    schema_version: Literal[1]
    package_id: Literal["weld-building-fees-atlas-source-review-2026-09-11"]
    files: list[Asset]
    excluded_self: Literal["evidence-manifest.json"]

    @model_validator(mode="after")
    def ordered_unique_paths(self) -> "Inventory":
        """Require a deterministic, duplicate-free inventory."""
        paths = [asset.path for asset in self.files]
        if paths != sorted(set(paths)):
            raise ValueError("unique sorted inventory paths required")
        return self
