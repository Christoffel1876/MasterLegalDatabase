"""Strict one-resolution custody preparation, distinct from any source/legal review."""
from pathlib import PurePosixPath
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

SourceID = Literal["el-paso-boa-resolution-25-290-directed-lead"]
URL = "https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf"

class Strict(BaseModel):
    """Reject extra fields and coercion."""
    model_config = ConfigDict(extra="forbid", strict=True)

class Asset(Strict):
    """Exact ordinary relative file identity."""
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def safe(cls, value: str) -> str:
        """Refuse path traversal and ambiguous path spelling."""
        p = PurePosixPath(value)
        if p.is_absolute() or ".." in p.parts or "\\" in value or p.as_posix() != value:
            raise ValueError("unsafe asset path")
        return value

class Baseline(Strict):
    """Exact prior managed file."""
    repository_path: str
    preserved: Asset
    records: int | None

class Provenance(Strict):
    """Recorded successful official HTTP acquisition and separate source claims."""
    source_id: SourceID
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    source: Asset
    parent: Asset
    parent_event: Asset
    source_event: Asset
    parent_url: Literal["https://planningdevelopment.elpasoco.com/"]
    official_source_url: Literal[
        "https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf"]
    anchor_text: Literal["Resolution to Dissolve"]
    physical_pages: Literal[2]
    recorded_http_started_at: AwareDatetime
    recorded_http_completed_at: AwareDatetime
    original_http_status: Literal[200]
    actual_repository_received_at: None
    source_dates: list[str]
    document_role: str
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    limitations: list[str]

class Template(Strict):
    """Validated future record with unknown intake timestamp until actual application."""
    record_id: SourceID
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    layer_id: Literal["08_County_Authorities"]
    official_source_name: str
    official_source_url: Literal[
        "https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf"]
    acquisition_method: Literal["manual_official_download"]
    source: Asset
    original_filename: Literal["original.pdf"]
    custody_note: str
    actual_repository_received_at: None
    intake_id: None
    archive_path: None

    @model_validator(mode="after")
    def filename(self) -> "Template":
        """Bind actual incoming basename rather than an invented publisher filename."""
        if PurePosixPath(self.source.path).name != self.original_filename:
            raise ValueError("incoming basename differs")
        return self

class Preparation(Strict):
    """Fixed one-source transaction limits; variable baseline sizes support offline fixtures."""
    prepared_at: AwareDatetime
    status: Literal["PREPARED_NOT_APPLIED"]
    comparison_commit: str
    templates: list[Template] = Field(min_length=1, max_length=1)
    provenance: list[Provenance] = Field(min_length=1, max_length=1)
    baseline: list[Baseline]
    runtime_pins: dict[str, str]
    custody_subset: list[Asset]
    parent_packet_manifest: Asset
    legacy_guard: Asset
    raw_before: int
    ledger_before: int
    raw_after: int
    ledger_after: int
    public_requests: Literal[0]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]

    @model_validator(mode="after")
    def exact(self) -> "Preparation":
        """Bind one exact source/authority across template and provenance."""
        t, p = self.templates[0], self.provenance[0]
        if t.record_id != p.source_id or t.source != p.source or t.authority_id != p.authority_id:
            raise ValueError("provenance identity differs")
        if self.raw_after != self.raw_before + 1 or self.ledger_after != self.ledger_before + 1:
            raise ValueError("one-source count differs")
        return self

class Manifest(Strict):
    """Closed static package; execution and acceptance are additive after preparation."""
    files: list[Asset]
    exclusions: list[str]
