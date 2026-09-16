"""Strict, bounded independent transaction review evidence."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int

class Reproduction(Strict):
    network_requests: Literal[0]
    temporary_fixture_only: Literal[True]
    returned: Literal['ValueError']
    error: str
    raw_ids: list[str]
    ledger_ids: list[str]
    unrelated_record_promoted_to_ledger: Literal[True]
    report_records: Literal[3]

class Review(Strict):
    status: Literal['BLOCKING_FINDING_HOLD_APPLY']
    reviewed_at: AwareDatetime
    proposal_manifest_sha256: str
    checked_assets: list[Asset]
    original_payloads_verified: int
    focused_tests_passed: int
    actual_readonly_preflight: str
    source_provenance_assessment: str
    finding: str
    required_repair: list[str]
    canonical_mutations: Literal[0]
    public_requests: Literal[0]
    limitations: list[str]

class Manifest(Strict):
    status: Literal['FROZEN_PRE_REPAIR_REVIEW']
    files: list[Asset]
