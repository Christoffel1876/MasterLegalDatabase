"""Strict preparation inventory and validation receipts; never operative-law metadata."""
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class File(Strict):
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)
class Inventory(Strict):
    schema_version:Literal[1]
    status:Literal['PREPARED_NOT_APPLIED']
    prepared_at:AwareDatetime
    files:list[File]
    mutable_execution_directory:Literal['execution']
    execution_directory_present_at_freeze:Literal[False]
    sources:Literal[2]
    physical_pages:Literal[5]
    original_bytes:Literal[377549]
    legal_currentness:Literal['not_verified']
    preparation_canonical_writes:Literal[0]
    public_requests:Literal[0]
class Validation(Strict):
    schema_version:Literal[1]
    checked_at:AwareDatetime
    status:Literal['ready_for_root_review_not_applied']
    tests_passed:Literal[61]
    branch_inclusive_coverage_percent:float
    transaction:File
    tests:File
    preparation:File
    source_provenance:File
    preserved_prefixes:list[File]
    command_receipts:list[File]
    raw_before:Literal[61]
    ledger_before:Literal[62]
    raw_after_if_applied:Literal[63]
    ledger_after_if_applied:Literal[64]
    current_intake_time:None
    legal_currentness:Literal['not_verified']
    qualifications:list[str]
    canonical_writes:Literal[0]
    public_requests:Literal[0]
