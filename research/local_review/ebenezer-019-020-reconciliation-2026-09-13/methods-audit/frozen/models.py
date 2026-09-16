"""Strict custody/method review records; no visual source or legal-accuracy certification."""
from pathlib import PurePosixPath
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Ref(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)
    @model_validator(mode='after')
    def confined(self) -> 'Ref':
        p = PurePosixPath(self.path)
        if p.is_absolute() or '..' in p.parts or str(p) != self.path:
            raise ValueError('Unsafe evidence path')
        return self

class SuppliedPrompt(Strict):
    source: Literal['agent_transcript_jsonl_tool_use_input']
    transcript_line: int = Field(gt=0)
    description: str
    attachments: list[str]
    prompt: str

class PromptCheck(Strict):
    artifact: Ref
    supplied_transcript_line: int
    prompt_utf8_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    prompt_utf8_bytes: int
    prompt_characters: int
    attachment_count: int
    purpose: str
    exact_parent_transcript_available: Literal[False] = False
    provenance: Literal['received_transcript_extract_claim_not_independently_authenticated'] = (
        'received_transcript_extract_claim_not_independently_authenticated')
    observations: list[str]

class NativePage(Strict):
    schema_version: Literal[1]
    source_id: str
    source_sha256: str
    physical_page: int
    expected_pages: int
    source_image_sha256: str
    extracted_at: AwareDatetime
    engine: Literal['PyMuPDF']
    engine_version: Literal['1.28.2']
    method: Literal['Page.get_text("text", sort=False, flags=195)']
    text: str
    text_sha256: str
    text_size_bytes: int
    status: Literal['machine_native_text_unreviewed']
    changes: Literal['none']

class PageCheck(Strict):
    physical_page: int
    image: Ref
    dimensions: tuple[int, int]
    evidence: Ref
    native_sha256: str
    native_bytes: int
    candidate_start_byte: int
    candidate_end_byte_exclusive: int
    native_reproduction: Literal['exact']
    external_receipt_image_match: Literal[True]
    direct_visual_review_in_this_audit: Literal[False] = False

class SourceCheck(Strict):
    assignment_id: Literal['EB-PDF-019', 'EB-PDF-020']
    source_id: str
    authority_id: Literal['CO-COUNTY-WELD']
    source: Ref
    source_canonical_path: str
    canonical_sha256_match: Literal[True]
    source_pdf_pages: int
    candidate: Ref
    external_reported_candidate_sha_match: Literal[True]
    actual_manifest_identity_match_now: Literal[True]
    historical_worker_pdf_rehash: Literal['not_performed_reported_absent']
    historical_worker_manifest_identity_lookup: Literal['not_performed_reported_unopened']
    pages: list[PageCheck]

class Issue(Strict):
    issue_id: str
    classification: Literal['identity_verified_now', 'method_limit', 'procedure_deviation',
                            'addendum_clarification', 'inherited_visual_disposition']
    statement: str
    evidence: list[str]
    consequence: str
    new_visual_finding: Literal[False] = False

class Audit(Strict):
    schema_version: Literal[1] = 1
    audited_at: AwareDatetime
    status: Literal['custody_verified_methods_qualified_pending_root_disposition']
    reviewed_scope: str
    original_manifest: Ref
    received_package_receipt: Ref
    frozen_receipt_files_verified: int
    clarification_tar: Ref
    tar_regular_members: int
    tar_directory_members: int
    supplied_inventory_files_verified: int
    loose_clarification_matches_tar: Literal[True]
    prompt_checks: list[PromptCheck] = Field(min_length=5, max_length=5)
    source_checks: list[SourceCheck] = Field(min_length=2, max_length=2)
    received_report_files: list[Ref]
    issues: list[Issue]
    public_requests: Literal[0] = 0
    source_edits: Literal[0] = 0
    direct_visual_pages_reviewed: Literal[0] = 0
    source_accuracy_certification: Literal[False] = False
    historical_blindness_certification: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'

class Manifest(Strict):
    schema_version: Literal[1] = 1
    files: list[Ref]
    exclusions: list[str]
    status: Literal['frozen_custody_methods_audit']
    @model_validator(mode='after')
    def unique(self) -> 'Manifest':
        if len({r.path for r in self.files}) != len(self.files):
            raise ValueError('Duplicate manifest paths')
        return self
