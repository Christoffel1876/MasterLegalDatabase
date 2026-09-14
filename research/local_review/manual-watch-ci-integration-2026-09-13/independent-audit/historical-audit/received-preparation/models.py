"""Strict preparation custody records; importing performs no work."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
class Ref(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 path:str;sha256:str=Field(pattern='^[0-9a-f]{64}$');size_bytes:int=Field(ge=0)
class Preparation(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 status:Literal['PREPARED_ONLY_NOT_INSTALLED_NOT_DEPLOYED'];prepared_at:str
 install_files:list[Ref];immutable_input_count:Literal[88];source_pairs:Literal[4];selected_sources:Literal[8]
 max_source_events:Literal[16];max_source_response_bytes:Literal[16000000];max_source_run_seconds:Literal[1200]
 scheduled_http_enabled_by_default:Literal[False];manual_http_enabled_by_default:Literal[False]
 source_http_requests:Literal[0];primary_document_urls_observed:Literal[6]
 final_focused_tests:int;final_combined_tests:int;branch_inclusive_coverage_percent:float
 local_python:str;python311_syntax_checked:Literal[True];linux_execution_tested:Literal[False]
 unchanged_maintained_input_pins:Literal[True];legal_currentness:Literal['not_verified'];limitations:list[str]
class Manifest(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 kind:Literal['manual_watch_ci_preparation'];prepared_at:str;files:list[Ref]
