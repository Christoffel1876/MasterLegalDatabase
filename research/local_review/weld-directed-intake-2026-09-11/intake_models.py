"""Strict final custody records for the authorized two-source Weld intake."""
from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


class Strict(BaseModel):
    """Disallow undeclared fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """File identity; containing fields state its package or repository scope."""
    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(ge=0)]


class Record(Strict):
    """Portable equivalent of the existing manual intake record fields."""
    intake_id: str
    record_id: str
    layer_id: str
    official_source_name: str
    official_source_url: str | None = None
    acquisition_method: str
    received_from: str
    reviewer_name: str
    reviewer_email: str | None = None
    custody_note: str
    original_filename: str
    archive_path: str
    sha256: str
    size_bytes: int = Field(ge=1)
    source_format: str
    received_at: datetime
    status: str
    blocked_queue_match: bool
    boundary: str


class Copy(Strict):
    """Unchanged audit input copied into the portable package."""
    original_path: str
    frozen: Asset


class DateRole(Strict):
    """A source-stated date, never independently certified legal effect."""
    value: str
    role: str
    review_pointer: str
    independent_legal_event_verification: Literal[False]


class Source(Strict):
    """Reviewed scope and preserved HTTP/archival custody for one original."""
    source_id: str
    authority_id: Literal['CO-COUNTY-WELD']
    intake_id: str
    source_role: Literal['county_zoning_amendment_instrument',
                         'county_environmental_health_services_fee_schedule']
    staged_original: Asset
    canonical_original: Asset
    exact_requested_url: str
    exact_final_url: str
    http_started_at: AwareDatetime
    http_completed_at: AwareDatetime
    http_status: Literal[200]
    tls_verified: Literal[True]
    redirects_followed: Literal[0]
    repository_received_at: AwareDatetime
    acquisition_method: Literal['manual_official_download']
    acquisition_description: str
    access_receipt: Asset
    public_headers: Asset
    original_header_identity: Asset
    header_derivation: str
    reviewed_source: Asset
    reviewed_source_schema: Asset
    reviewed_source_directory: str
    physical_pages: Literal[3, 5]
    native_bytes: Literal[7367, 9284]
    legacy_registry_or_container_ids: list[str]
    source_dates: list[DateRole]
    legal_adoption_date_independently_verified: None
    legal_effective_date_independently_verified: None
    source_publication_date_independently_verified: None
    reviewed_scope_qualifications: list[str]
    legal_currentness: Literal['not_verified']
    pipeline_status: Literal['archived_pending_pipeline']


class Reconciliation(Strict):
    """Measured narrow reconciliation result, with unrelated history retained."""
    status: Literal['dry_run', 'updated', 'no_change']
    added_intake_ids: list[str]
    ledger_records_before: int
    ledger_records_after: int
    report_needs_update: bool
    raw_manifest_records: Literal[40]
    missing_ledger_only_originals: list[str]


class Transaction(Strict):
    """Before and after bytes and a canonical preimage snapshot."""
    repository_path: str
    before: Asset
    after: Asset
    snapshot: Asset


class Receipt(Strict):
    """Completed intake with portable source, audit and transaction evidence."""
    schema_version: Literal[1]
    status: Literal['completed_archived_pending_pipeline']
    authorized_by: Literal['root internal go-ahead after source-role reconciliation']
    completed_at: AwareDatetime
    record_stream: Asset
    provenance_stream: Asset
    record_schema: Asset
    source_schema: Asset
    transactions: Annotated[list[Transaction], Field(min_length=3, max_length=3)]
    sources: Annotated[list[Source], Field(min_length=2, max_length=2)]
    audit_copies: list[Copy]
    payloads: list[Asset]
    preparation_preimages: list[Asset]
    raw_manifest_before_records: Literal[38]
    raw_manifest_after_records: Literal[40]
    ledger_before_records: Literal[39]
    ledger_after_records: Literal[41]
    raw_existing_prefix_unchanged: Literal[True]
    ledger_existing_prefix_unchanged: Literal[True]
    ordinary_raw_files_screened_before: Literal[542]
    matching_size_raw_files_before: Literal[0]
    other_raw_files_unchanged: Literal[True]
    before_reconciliation: Reconciliation | None
    after_reconciliation: Reconciliation
    idempotency_reconciliation: Reconciliation
    legal_currentness: Literal['not_verified']
    coverage_or_rule_unit_changes: Literal['none']
    limitations: list[str]

    @model_validator(mode='after')
    def source_set(self) -> Receipt:
        """Require exactly the two approved source identities and frozen review paths."""
        expected = [
            ('weld-ordinance-26-01-atlas-directed', 5, 9284,
             '2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0'),
            ('weld-ehs-fees-2026-atlas-directed', 3, 7367,
             '852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3'),
        ]
        for source, wanted in zip(self.sources, expected, strict=True):
            actual = (source.source_id, source.physical_pages, source.native_bytes,
                      source.canonical_original.sha256)
            if actual != wanted or source.staged_original.sha256 != wanted[3]:
                raise ValueError('Unexpected source identity or scope')
            directory = f'evidence/source-reviews/{source.source_id}'
            if source.reviewed_source_directory != directory:
                raise ValueError('Review directory must be package-relative and fixed')
            if source.reviewed_source.path != directory + '/SOURCE_QA.json':
                raise ValueError('Unexpected review path')
        if self.idempotency_reconciliation.added_intake_ids:
            raise ValueError('Reconciliation is not idempotent')
        return self
