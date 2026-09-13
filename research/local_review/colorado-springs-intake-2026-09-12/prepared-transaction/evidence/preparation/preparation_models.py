"""Strict, unexecuted two-source municipal intake proposal."""
from typing import Literal
from pydantic import AwareDatetime,BaseModel,ConfigDict,Field,model_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
    path:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes:int=Field(ge=0)
class Copy(Strict):
    original_path:str
    preserved:Asset
    kind:Literal['source','http_receipt','parent_html','baseline','code_reference','review_metadata','identity_image']
class Referral(Strict):
    parent_url:str
    parent_html:Asset
    original_data_src:str
    original_viewer_src:str
    encoded_file_argument:str
    resolved_url:str
    transformation:Literal['Read data-src; decode the pdf.js file argument exactly once; require both to equal the exact requested PDF URL.']
    parent_reservation:Asset
    parent_result:Asset
    parent_public_headers:Asset
class Source(Strict):
    source_id:Literal['SD014-01','SD014-02']
    proposed_record_id:str
    authority_id:Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    layer_id:Literal['10_Municipal_Authorities']
    issuer:str
    document_role:str
    original:Asset
    original_received_body_path:str
    page_count:Literal[7]
    http_url:str
    request_started_at:AwareDatetime
    response_completed_at:AwareDatetime
    http_status:Literal[200]
    redirect_count:Literal[0]
    complete_response:Literal[True]
    acquisition_method:Literal['manual_official_download']
    response_receipts:list[Asset]
    referral:Referral
    source_printed_date_claim:str
    date_role:str
    verified_adoption_date:None
    verified_effective_date:None
    actual_future_repository_received_at:None
    source_qa_scope:str
    source_qa_metadata:Asset
    legal_currentness:Literal['not_verified']
    answer_safe:Literal[False]
    qualifications:list[str]
class RecordTemplate(Strict):
    record_id:str
    layer_id:Literal['10_Municipal_Authorities']
    authority_id:Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    official_source_name:str
    official_source_url:str
    acquisition_method:Literal['manual_official_download']
    received_from:str
    reviewer_name:str
    reviewer_email:None
    custody_note:str
    source_file:Asset
    original_filename:str
    expected_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes:int=Field(ge=1)
    source_format:Literal['pdf']
    allow_duplicate:Literal[False]
    intake_id:None
    archive_path:None
    received_at:None
    status:Literal['proposed_not_applied']
    intended_record_status:Literal['archived_pending_pipeline']
    archive_path_template:str
    legal_currentness:Literal['not_verified']
class Baseline(Strict):
    repository_path:str
    preserved:Asset
    records:int|None=Field(ge=0)
class Dedupe(Strict):
    observed_at:AwareDatetime
    ordinary_raw_files_screened:int
    symlink_paths:list[str]
    same_size_files_hashed:list[Asset]
    matching_raw_files:list[str]
    matching_lfs_pointers:list[str]
    matching_raw_manifest_records:list[str]
    matching_ledger_records:list[str]
    proposed_id_collisions:list[str]
    metadata_search_inputs:list[Asset]
    exact_metadata_pattern_counts:dict[str,int]
    limitation:str
class Preparation(Strict):
    schema_version:Literal['1.0']
    status:Literal['PREPARED_NOT_APPLIED']
    prepared_at:AwareDatetime
    actual_repository_received_at:None
    repository_mutations:Literal[0]
    public_requests:Literal[0]
    sources:list[Source]=Field(min_length=2,max_length=2)
    proposed_records:list[RecordTemplate]=Field(min_length=2,max_length=2)
    current_raw_records:Literal[59]
    current_ledger_records:Literal[60]
    current_verified_originals:Literal[59]
    preserved_missing_ledger_only_ids:list[str]
    expected_raw_records_after_two_new_intakes:Literal[61]
    expected_ledger_records_after_two_new_intakes:Literal[62]
    expected_verified_originals_after_two_new_intakes:Literal[61]
    baseline:list[Baseline]
    copies:list[Copy]
    dedupe:Dedupe
    host_validation:Literal['Both exact official URLs accepted by current require_official_source_url; no policy change.']
    request_schema_validation:Literal['Two real ManualSourceIntakeRequest instances validated; two archive_manual_source(dry_run=True) previews validated as ManualSourceIntakeRecord. Preview receipt times are preparation-only, never final intake times.']
    reconciliation:Asset
    required_preflight:list[str]
    warnings:list[str]
    @model_validator(mode='after')
    def distinct(self):
        if [s.source_id for s in self.sources]!=['SD014-01','SD014-02']:raise ValueError('source order')
        if len({s.original.sha256 for s in self.sources})!=2:raise ValueError('duplicate source bytes')
        if [s.proposed_record_id for s in self.sources]!=[r.record_id for r in self.proposed_records]:raise ValueError('record identity mismatch')
        for s,r in zip(self.sources,self.proposed_records,strict=True):
            if s.original!=r.source_file or s.original.sha256!=r.expected_sha256 or s.http_url!=r.official_source_url:raise ValueError('source-record binding mismatch')
        return self
class Inventory(Strict):
    status:Literal['PREPARED_NOT_APPLIED']
    files:list[Asset]
    exclusions:Literal['FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only. Frozen review metadata may refer to external full QA packages explicitly not duplicated here.']
