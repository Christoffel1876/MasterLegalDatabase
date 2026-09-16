"""Strict closeout receipt for received review files, not source-content approval."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int

class Check(Strict):
    name: str
    expected_sha256: str
    actual_sha256: str
    matches: bool
    evidence_path: str

class Document(Strict):
    assignment_id: Literal['EB-PDF-023','EB-PDF-024']
    source_id: str
    original_delivery: str
    expected_pages: int
    worker_status: Literal['completed_pending_atlas_verification']
    reported_completion_at: AwareDatetime
    reported_candidate_release_at: AwareDatetime
    reported_pass1_freeze_at: AwareDatetime
    checks: list[Check]
    pass2_reopened_pages_claim: list[int]
    independent_execution_witness: Literal[False]
    retained_reopen_report: str
    retained_individual_reopen_read_notes: list[str]
    method: Literal['caption_mediated_assisted_review']
    limitations: list[str]
    content_findings_accepted_by_this_receipt: Literal[False]

class Receipt(Strict):
    observed_at: AwareDatetime
    completed_worker_documents: list[str]
    pending_worker_documents: list[str]
    pending_atlas_verification: list[str]
    documents: list[Document]
    packet_manifest_sha256: str
    packet_payloads_hash_checked: int
    packet_payloads_copied: Literal['manifest_and_identity_metadata_only']
    original_files: list[Asset]
    retained_files: list[Asset]
    limitations: list[str]
    source_pages_visually_reviewed_by_this_task: Literal[0]
    network_requests: Literal[0]

class Manifest(Strict):
    status: Literal['FROZEN_CLOSEOUT_RECEIPT']
    files: list[Asset]

class RootObservation(Strict):
    recorded_at: AwareDatetime
    observer: Literal['Atlas root agent']
    observation_time: None
    evidence_origin: Literal['parent agent message to this subagent']
    statement: str
    observed_directly_by_receipt_author: Literal[False]
