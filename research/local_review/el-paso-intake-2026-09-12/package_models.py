"""Read-only portable custody models; no relocated transaction is imported or executed."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject unexpected fields and implicit scalar coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Bind a confined ordinary file to its exact bytes."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> Asset:
        """Reject absolute and parent-traversing artifact names."""
        if Path(self.path).is_absolute() or '..' in Path(self.path).parts:
            raise ValueError('Unconfined artifact')
        return self


class Record(Strict):
    """Validate all nineteen fields of each final pending received-PDF custody record."""
    intake_id: str
    record_id: str
    layer_id: Literal['08_County_Authorities']
    official_source_name: str
    official_source_url: str
    acquisition_method: Literal['received_review_package']
    received_from: str
    reviewer_name: str
    reviewer_email: None
    custody_note: str
    original_filename: Literal['original.pdf']
    archive_path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(gt=0)
    source_format: Literal['pdf']
    received_at: AwareDatetime
    status: Literal['archived_pending_pipeline']
    blocked_queue_match: Literal[False]
    boundary: str


class Source(Strict):
    """Keep canonical archive identity bound to the exact received provenance row."""
    record: Record
    authority_id: Literal['CO-COUNTY-EL_PASO']
    preserved_original: Asset
    provenance: Asset
    provenance_jsonl_row: int = Field(ge=0)
    review_status: Literal['metadata_only_review_unknown']
    verified_http_acquired_at: None
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]


class Prefix(Strict):
    """Preserve exact before/after bytes and their original repository destination."""
    repository_path: str
    before: Asset
    after: Asset
    before_records: int = Field(ge=0)
    after_records: int = Field(ge=0)


class Receipt(Strict):
    """Describe completed custody while preserving the intermediate failed preparation."""
    schema_version: Literal[1]
    packaged_at: AwareDatetime
    status: Literal['completed_custody_portable_preservation']
    original_actual_repository_received_at: AwareDatetime
    original_completed_at: AwareDatetime
    transaction_manifest: Asset
    transaction_payloads: Literal[159]
    recovery_inventory: Asset
    original_intent: Asset
    original_completion_receipt: Asset
    exact_suffix: Asset
    prefixes: list[Prefix] = Field(min_length=2, max_length=2)
    before_report: Asset
    after_report: Asset
    legacy_coverage_ledger_repository_path: Literal['_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json']
    unchanged_legacy_coverage_ledger: Asset
    before_corpus_validation: Asset
    after_corpus_validation: Asset
    sources: list[Source] = Field(min_length=13, max_length=13)
    inherited_missing_originals: Literal[1]
    full_corpus_valid: Literal[False]
    unchanged_inherited_lfs_error_paths: list[str] = Field(min_length=2, max_length=2)
    private_raw_headers_excluded: Literal[True]
    relocated_write_scripts_executed: Literal[False]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    coverage_promotion: Literal[False]
    limitations: list[str]


class Inventory(Strict):
    """Close portable package membership; its own inventory alone is self-excluded."""
    schema_version: Literal[1]
    files: list[Asset]
    self_exclusion: Literal['PACKAGE_INVENTORY.json']
