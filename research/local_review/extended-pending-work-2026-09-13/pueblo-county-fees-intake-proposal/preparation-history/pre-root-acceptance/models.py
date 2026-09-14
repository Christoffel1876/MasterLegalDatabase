"""Typed preparation for one received Pueblo County source; no legal promotion."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    """Reject extra fields and scalar coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    """Exact ordinary-file identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)

class Baseline(Strict):
    """Frozen existing bytes, never a reconstructed prefix."""
    repository_path: str
    preserved: Asset
    records: int | None

class Template(Strict):
    """Only future repository receipt fields are unresolved."""
    record_id: Literal['pueblo-county-planning-fees-sh-ext-002']
    authority_id: Literal['CO-COUNTY-PUEBLO']
    layer_id: Literal['08_County_Authorities']
    official_source_name: str
    official_source_url: None
    acquisition_method: Literal['received_review_package']
    source: Asset
    original_filename: Literal['original.pdf']
    custody_note: str
    actual_repository_received_at: None
    intake_id: None
    archive_path: None

class Provenance(Strict):
    """Reported transport and adoption claims remain separate from local custody."""
    requested_url_reported: str
    final_url_reported: str
    http_status_reported: Literal[200]
    reported_reserved_at: AwareDatetime
    reported_finished_at: AwareDatetime
    independently_verified_http_time: None
    original_tool_command_retained: Literal[False]
    parent_representation: Literal['received_browser_DOM_derivative']
    catalog_status_reported: Literal[403]
    adoption_date: None
    effective_date: None
    legal_currentness: Literal['not_verified']
    limitations: list[str]

class Preparation(Strict):
    """Fixed inputs for a separately authorized append; preparation is not execution."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_APPLIED']
    comparison_commit: str = Field(pattern=r'^[0-9a-f]{40}$')
    template: Template
    provenance: Provenance
    baseline: list[Baseline]
    runtime_pins: dict[str, str]
    source_review: Asset
    source_review_schema: Asset
    independent_review: Asset
    root_source_qa_approval: Literal['pending']
    raw_before: int = Field(ge=0)
    ledger_before: int = Field(ge=0)
    raw_after: int = Field(ge=1)
    ledger_after: int = Field(ge=1)
    public_requests: Literal[0]
    canonical_mutations: Literal[0]

class Manifest(Strict):
    """Closed immutable preparation payloads, excluding future execution state."""
    schema_version: Literal[1]
    files: list[Asset]
