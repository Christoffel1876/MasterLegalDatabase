"""Strict models for a pending Weld intake preparation; no write functions."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal,Annotated
import json,hashlib,os
import jsonschema
from pydantic import BaseModel,ConfigDict,Field
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord,ManualSourceIntakeRequest,archive_manual_source,reconcile_manual_source_intake
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
ACCESS=ROOT.parent/'handoffs/atlas-reviews/weld-directed-access-2026-09-11'
HAND=ACCESS/'intake-preparation'
OUT=ROOT/'research/local_review/weld-directed-intake-2026-09-11'
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
SHA=Annotated[str,Field(pattern=r'^[0-9a-f]{64}$')]
class Asset(Strict):
 path:str
 sha256:SHA
 size_bytes:int=Field(ge=0)
class Baseline(Strict):
 repository_path:str
 frozen:Asset
 records:int|None
class Match(Strict):
 metadata_file:str
 metadata_file_sha256:SHA
 location:str
 source_id:str|None
 review_id:str|None
 source_hash:str|None
 exact_url:str|None
 relative_original_path:str|None
 actual_local_original_present:bool|None
 relation:str
class Dedupe(Strict):
 checked_at:datetime
 raw_manifest_records:Literal[38]
 manual_ledger_records:Literal[39]
 ordinary_raw_files_size_screened:Literal[542]
 matching_size_files_hashed:Literal[0]
 raw_files_equal_digest:Literal[0]
 symlinks_encountered:Literal[0]
 raw_manifest_matches:list[str]
 manual_ledger_matches:list[str]
 proposed_record_id_collisions:list[str]
 legacy_matches:list[Match]
 baseline:list[Baseline]
 qualification:str
class Source(Strict):
 proposed_record_id:str
 authority_id:Literal['CO-COUNTY-WELD']
 source_original:Asset
 preserved_from:str
 successful_event_id:str
 exact_requested_url:str
 exact_final_url:str
 http_started_at:datetime
 http_completed_at:datetime
 http_status:Literal[200]
 content_type:Literal['application/pdf']
 verified_tls:Literal[True]
 source_page_count:Literal[3,5]
 native_nonblank_pages:Literal[3,5]
 native_utf8_bytes:int
 source_role_review_status:Literal['pending_root_reconciliation']
 source_role_provisional:str
 source_scope_provisional:str
 source_publication_date:None
 adoption_date:None
 effective_date:None
 original_http_headers:Asset
 public_derived_headers:Asset
 header_transformation:Literal['Only Set-Cookie header lines omitted; all other bytes retained unchanged']
 access_receipt:Asset
 historical_recorded_sha256:SHA
 newly_measured_digest_equals_recorded_digest:Literal[True]
 historical_original_bytes_reopened:Literal[False]
 request:Asset
 dry_run_preview:Asset
 dry_run_preview_is_actual_intake:Literal[False]
 actual_repository_received_at:None
 legal_currentness:Literal['not_verified']
class Preparation(Strict):
 schema_version:Literal[1]
 prepared_at:datetime
 status:Literal['pending_source_role_reconciliation_and_explicit_internal_go_ahead']
 apply_available:Literal[False]
 raw_archive_or_control_changes:Literal['none']
 sources:list[Source]
 dedupe:Asset
 request_schema:Asset
 preview_schema:Asset
 payloads:list[Asset]
 proposed_after_counts:dict[str,int]
 application_constraints:list[str]
 scope_limits:list[str]
 legal_currentness:Literal['not_verified']

