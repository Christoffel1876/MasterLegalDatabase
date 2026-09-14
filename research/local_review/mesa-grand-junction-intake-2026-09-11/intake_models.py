"""Strict custody models for the three-source Mesa/Grand Junction intake."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
SHA=Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
    path:str
    sha256:SHA
    size_bytes:int=Field(ge=0)
class Copy(Strict):
    original:Asset
    preserved:Asset
    method:Literal['exact_copy','set_cookie_lines_omitted']
    omitted_lines:int=Field(ge=0)
    original_retained_at:str
class DateAssertion(Strict):
    value:str
    role:str
    physical_page:int=Field(ge=1)
    qualification:Literal['source_statement_only_not_independently_verified']
class Source(Strict):
    source_id:str
    authority_id:Literal['CO-COUNTY-MESA','CO-MUNICIPAL-GRAND_JUNCTION']
    layer_id:Literal['08_County_Authorities','10_Municipal_Authorities']
    role:Literal['county_land_development_code_edition','municipal_fire_code_adoption_and_amendment_instrument','municipal_fire_prevention_service_fee_schedule']
    priority_id:str
    event_id:str
    staged_original:Asset
    event:Asset
    http_started_at:AwareDatetime
    http_completed_at:AwareDatetime
    exact_requested_url:str
    exact_final_url:str
    tls_verified:Literal[True]
    http_status:Literal[200]
    redirects:Literal[0]
    physical_pages:int
    native_utf8_bytes:int
    discovery_visually_reviewed_pages:list[int]
    intake_title_scope_pages_viewed:list[int]
    full_text_semantically_reviewed:Literal[False]
    legacy_registry_source_ids:list[str]
    historical_digest_match_records:int=Field(ge=0)
    dates:list[DateAssertion]
    legal_currentness:Literal['not_verified']
    status:Literal['archived_pending_pipeline']
    scope_qualifications:list[str]
    @model_validator(mode='after')
    def owner(self):
        if (self.authority_id=='CO-COUNTY-MESA') != (self.layer_id=='08_County_Authorities'):
            raise ValueError('County/municipality ownership mismatch')
        if self.role.startswith('county_') != (self.authority_id=='CO-COUNTY-MESA'):
            raise ValueError('Role ownership mismatch')
        return self
class Record(Strict):
    intake_id:str
    record_id:str
    layer_id:str
    official_source_name:str
    official_source_url:str|None
    acquisition_method:str
    received_from:str
    reviewer_name:str
    reviewer_email:str|None
    custody_note:str
    original_filename:str
    archive_path:str
    sha256:SHA
    size_bytes:int=Field(ge=1)
    source_format:str
    received_at:AwareDatetime
    status:Literal['archived_pending_pipeline']
    blocked_queue_match:Literal[False]
    boundary:str
class Dedupe(Strict):
    checked_at:AwareDatetime
    raw_manifest:Asset
    manual_ledger:Asset
    raw_records:Literal[40]
    ledger_records:Literal[41]
    ordinary_raw_files_screened:int
    candidate_sizes:list[int]
    matching_size_files:list[Asset]
    raw_manifest_matches:list[str]
    ledger_matches:list[str]
    source_id_collisions:list[str]
    metadata_inputs:list[Asset]
    boundary:str
class Preparation(Strict):
    prepared_at:AwareDatetime
    status:Literal['validated_before_authorized_append']
    sources:list[Source]=Field(min_length=3,max_length=3)
    copied_discovery_files:list[Copy]
    requests:list[Asset]
    request_schema:Asset
    record_schema:Asset
    dedupe:Dedupe
    discovery_validation_passed:Literal[True]
    discovery_public_events:Literal[13]
    discovery_distinct_targets:Literal[12]
    no_network_during_intake:Literal[True]
class Transaction(Strict):
    repository_path:str
    before:Asset
    after:Asset
    snapshot:Asset
class Corpus(Strict):
    started_at:AwareDatetime
    completed_at:AwareDatetime
    command:list[str]
    exit_code:int
    stdout:Asset
    stderr:Asset
    inherited_issue_paths:list[str]
    unexpected_issues:list[str]
class Receipt(Strict):
    schema_version:Literal[1]
    completed_at:AwareDatetime
    status:Literal['completed_archived_pending_pipeline']
    preparation:Asset
    records:Asset
    provenance:Asset
    record_schema:Asset
    sources:list[Source]=Field(min_length=3,max_length=3)
    canonical_originals:list[Asset]=Field(min_length=3,max_length=3)
    transactions:list[Transaction]=Field(min_length=3,max_length=3)
    files:list[Asset]
    actual_repository_received_at:AwareDatetime
    raw_before_records:Literal[40]
    raw_after_records:Literal[43]
    ledger_before_records:Literal[41]
    ledger_after_records:Literal[44]
    exact_raw_prefix_preserved:Literal[True]
    exact_ledger_prefix_preserved:Literal[True]
    other_raw_files_unchanged:Literal[True]
    reconciliation_replay_added_ids:list[str]
    reconciliation_replay_report_changed:Literal[False]
    full_corpus:Corpus
    source_pages:Literal[250]
    original_pdf_bytes:Literal[9258844]
    legal_currentness:Literal['not_verified']
    coverage_or_rule_unit_changes:Literal['none']
    limitations:list[str]
    @model_validator(mode='after')
    def fixed_scope(self):
        expected=[('mesa-land-development-code-atlas-directed','8b1af5f7ba0383c45304bf134ad88d49faa1d179ffde1959e7d36db9c0a5ca9b',219),('grand-junction-ifc-ordinance-5269-atlas-directed','79795d6650664c33808b3877e97b04fd31a84ab1a6bda8ab658c3153cbbe3993',29),('grand-junction-fire-fees-atlas-directed','1f7faf078188c26fa803e4ec6225d20caad2fcce48f69d2d2ae9563c96732884',2)]
        if [(s.source_id,s.staged_original.sha256,s.physical_pages) for s in self.sources]!=expected:
            raise ValueError('Unexpected source set')
        if self.reconciliation_replay_added_ids:raise ValueError('Non-idempotent reconciliation')
        return self
