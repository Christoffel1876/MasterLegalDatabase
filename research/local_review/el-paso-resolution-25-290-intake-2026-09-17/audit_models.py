"""Strict final intake/audit records, separate from legal source interpretation."""
from typing import Literal
from pydantic import AwareDatetime, Field
from models import Asset, Strict


class Comparison(Strict):
    """Exact metadata-only comparison against a whole streamed current JSONL file."""
    artifact: Asset
    rows: int = Field(ge=0)
    source_id_matches: list[int]
    source_sha_matches: list[int]
    exact_source_url_matches: list[int]
    meaning: Literal['metadata_equality_only_not_currentness_or_retrieval_proof']


class Check(Strict):
    """Actual focused offline check and its unchanged captured output."""
    command: str
    exit_code: Literal[0]
    result: str
    evidence: Asset


class FinalAudit(Strict):
    """Completed custody addition with unchanged historical source and review bindings."""
    recorded_at: AwareDatetime
    status: Literal['completed_custody_only_intake']
    source_id: Literal['el-paso-boa-resolution-25-290-directed-lead']
    source_sha256: Literal['754e98fb7908b66e54a192cefca9817f7bb4cf2a428cf7c469d59f7cfdcdf427']
    actual_repository_received_at: AwareDatetime
    recorded_http_completed_at: AwareDatetime
    raw_before: Literal[70]
    raw_after: Literal[71]
    ledger_before: Literal[71]
    ledger_after: Literal[72]
    prior_review_joins_preserved: Literal[38]
    prior_rows_preserved: Literal[70]
    reviews_after: Literal[38]
    unmapped_after: Literal[33]
    source_date_claims: list[str]
    inventory_snapshot: str
    installed_files: list[Asset]
    unchanged_inputs: list[Asset]
    snapshots: list[Asset]
    checks: list[Check]
    legacy_comparison: Comparison
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    limitations: list[str]
