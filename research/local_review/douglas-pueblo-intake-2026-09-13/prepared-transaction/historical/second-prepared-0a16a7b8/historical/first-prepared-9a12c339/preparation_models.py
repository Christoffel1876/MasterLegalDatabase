from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime

class Strict(BaseModel): model_config=ConfigDict(extra='forbid',strict=True)

class Asset(Strict):
 path:str;sha256:str=Field(pattern=r'^[a-f0-9]{64}$');size_bytes:int=Field(ge=0)

class Source(Strict):
 source_id:str;proposed_record_id:str;authority_id:str;layer_id:Literal['08_County_Authorities','10_Municipal_Authorities'];original:Asset;http_url:str;request_started_at:AwareDatetime;response_completed_at:AwareDatetime;http_status:Literal[200];physical_pages:int;issuer:str;source_date_claims:list[str];legal_currentness:Literal['not_verified'];actual_repository_received_at:None;review_scope:str;qualifications:list[str];evidence:list[Asset];referral_parent_url:str;referral_parent_body:Asset;referral_label:str;referral_href:str;referral_selected_url:str;redirect_events:list[Asset]

class Template(Strict):
 record_id:str;layer_id:str;official_source_name:str;official_source_url:str;acquisition_method:Literal['manual_official_download'];received_from:str;reviewer_name:str;reviewer_email:None;custody_note:str;expected_sha256:str;allow_duplicate:Literal[False];source_file:Asset;original_filename:str;intake_id:None;archive_path:None;received_at:None;status:Literal['proposed_not_applied']

class Baseline(Strict): repository_path:str;preserved:Asset;records:int|None

class Preparation(Strict):
 schema_version:Literal[1];status:Literal['PREPARED_NOT_APPLIED'];prepared_at:AwareDatetime;canonical_mutations:Literal[0];public_requests:Literal[0];sources:list[Source];proposed_records:list[Template];baseline:list[Baseline];raw_before:Literal[61];raw_after:Literal[63];ledger_before:Literal[62];ledger_after:Literal[64];missing_ledger_only_ids:list[str];duplicate_check:str;legacy_id_check:str

class Manifest(Strict): schema_version:Literal[1];files:list[Asset]
