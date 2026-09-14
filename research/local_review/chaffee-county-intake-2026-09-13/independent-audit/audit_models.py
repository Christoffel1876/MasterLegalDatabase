"""Strict bounded preapply review; no approval of source legal effect."""
from typing import Literal

from pydantic import AwareDatetime, Field

from run_checks import Asset, Strict


class Source(Strict):
    """Exact selected source and observed acquisition, before repository intake."""
    source_id: str
    authority_id: Literal['CO-COUNTY-CHAFFEE']
    layer_id: Literal['08_County_Authorities']
    original: Asset
    physical_pages: int = Field(ge=1)
    official_source_url: str
    acquisition_method: Literal['manual_official_download']
    observed_get_started_at: AwareDatetime
    observed_get_completed_at: AwareDatetime
    future_repository_received_at: None
    status: Literal['archived_pending_pipeline']


class Audit(Strict):
    """Independent inspected scope and actual verification, with no canonical apply."""
    reviewer: Literal['Plato']
    recorded_at: AwareDatetime
    disposition: Literal['no_blocker_found_in_fixed_two_source_preapply_scope']
    reviewed_preparation: Asset
    reviewed_transaction: Asset
    reviewed_manifest: Asset
    copy_receipt: Asset
    checks: Asset
    sources: list[Source] = Field(min_length=2, max_length=2)
    baseline_raw_records: Literal[67]
    baseline_ledger_records: Literal[68]
    proposed_raw_records: Literal[69]
    proposed_ledger_records: Literal[70]
    actual_intake_occurred_in_this_audit: Literal[False]
    independent_probe_cases: Literal[8]
    observations: list[str]
    limitations: list[str]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    public_requests: Literal[0]


class Manifest(Strict):
    """Closed audit inventory excluding only itself and schema."""
    recorded_at: AwareDatetime
    status: Literal['frozen_preapply_audit_not_canonical_execution']
    files: list[Asset]
