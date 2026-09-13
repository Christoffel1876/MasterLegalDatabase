"""Strict models for a post-report custody/method audit, not a source-meaning review."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

class Copy(Strict):
    original_relative_path: str
    retained: Asset
    observed_mtime_ns: int
    copy_mode: Literal['exact_bytes']

class Custody(Strict):
    started_at: AwareDatetime
    completed_at: AwareDatetime
    status: Literal['frozen_before_report_interpretation']
    copies: list[Copy]
    source_review_pin: Asset
    original_files_unchanged_at_capture: Literal[True]
    ui_execution_witnessed_by_this_auditor: Literal[False]
    public_requests: Literal[0]

class Binding(Strict):
    label: str
    claimed: str | None
    observed: str
    matches: bool | None
    evidence_paths: list[str]

class FindingClaim(Strict):
    finding_id: str
    claimed_classification: str
    claimed_summary: str
    source_meaning_assessed: Literal[False]

class DocumentAudit(Strict):
    assignment: Literal['EB-PDF-025', 'EB-PDF-026']
    source_id: str
    report_directory: str
    expected_pages: Literal[6]
    pdf_pages_observed: Literal[6]
    bindings: list[Binding]
    claimed_status: str
    declared_method: str
    declared_critical_count: int
    claimed_findings: list[FindingClaim]
    chronology_claims: dict[str, str]
    method_evidence: list[str]
    unresolved_or_missing_evidence: list[str]
    source_meaning_assessed: Literal[False]

class Audit(Strict):
    audited_at: AwareDatetime
    status: Literal['post_report_custody_checked_substantive_reconciliation_pending']
    custody_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    documents: list[DocumentAudit]
    shared_limits: list[str]
    original_source_qa_changed: Literal[False]
    new_visual_review_pages: Literal[0]
    public_requests: Literal[0]
    canonical_changes: Literal[0]

class Manifest(Strict):
    status: Literal['FROZEN_POST_REPORT_CUSTODY_METHOD_AUDIT']
    files: list[Asset]
