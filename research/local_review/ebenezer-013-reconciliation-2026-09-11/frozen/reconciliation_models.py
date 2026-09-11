"""Strict source-bound reconciliation of external EB013 report claims."""
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)

class FileRef(Strict):
    path:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes:int=Field(ge=0)
    @field_validator('path')
    @classmethod
    def safe(cls,value):
        p=PurePosixPath(value)
        if p.is_absolute() or '..' in p.parts:raise ValueError('Relative audit paths only')
        return value

class Decision(Strict):
    id:str
    kind:Literal['external_finding','external_erratum','atlas_supplement']
    disposition:Literal['accepted','qualified','rejected','source_observation']
    external_report:Literal['PASS2_REVIEW.md','PASS1_frozen.md']
    external_line:int=Field(ge=1)
    external_claim:str
    physical_pages:list[int]=Field(min_length=1)
    page_images:list[FileRef]=Field(min_length=1)
    atlas_annotation_ids:list[str]
    source_observation:str
    qualification:str
    native_text_change_required:Literal[False]
    legal_currentness:Literal['not_verified']

    @model_validator(mode='after')
    def valid_pages(self):
        if len(self.physical_pages)!=len(set(self.physical_pages)):
            raise ValueError('Duplicate page')
        if min(self.physical_pages)<1 or max(self.physical_pages)>8:
            raise ValueError('Page outside source')
        if len(self.page_images)!=len(self.physical_pages):
            raise ValueError('Missing full-page evidence')
        return self

class ExternalCounts(Strict):
    finding_rows:Literal[23]
    critical:Literal[10]
    minor:Literal[7]
    info_preserved:Literal[4]
    unresolved:Literal[2]
    errata_rows:Literal[4]
    reported_actionable_or_uncertain:Literal[19]
    unique_error_count_certified:Literal[False]
    count_arithmetic_matches:Literal[True]

class Reconciliation(Strict):
    schema_version:Literal[1]
    assignment:Literal['EB-PDF-013']
    source_id:Literal['fort-collins-wildfire-code-sd005-05']
    authority_id:Literal['CO-MUNICIPAL-FORT_COLLINS']
    reviewed_at:datetime
    comparison_commit:str=Field(pattern=r'^[0-9a-f]{40}$')
    status:Literal['reconciled_with_qualifications_no_source_changes']
    review_mode:Literal['candidate_aware_direct_image_review_with_native_support']
    physical_pages_directly_inspected:list[int]
    source_pdf:FileRef
    native_candidate:FileRef
    committed_review:FileRef
    receipts:list[FileRef]
    supplemental_evidence:list[FileRef]
    external_counts:ExternalCounts
    decisions:list[Decision]
    disposition_counts:dict[str,int]
    method_and_limits:list[str]
    original_source_and_candidate_changed:Literal[False]
    external_reports_changed:Literal[False]
    production_changes:Literal[False]
    network_requests:Literal[0]
    legal_currentness:Literal['not_verified']

    @field_validator('reviewed_at')
    @classmethod
    def aware(cls,v):
        if v.utcoffset() is None:raise ValueError('Timezone required')
        return v
    @model_validator(mode='after')
    def complete(self):
        if self.physical_pages_directly_inspected!=list(range(1,9)):
            raise ValueError('All eight pages must be directly inspected')
        ids=[d.id for d in self.decisions]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate decision ID')
        if {d.id for d in self.decisions if d.kind=='external_finding'}!={f'EB013-P2-{i:03}' for i in range(1,24)}:
            raise ValueError('Every external finding must be reconciled exactly once')
        if {d.id for d in self.decisions if d.kind=='external_erratum'}!={f'EB013-P1-E{i:02}' for i in range(1,5)}:
            raise ValueError('Every erratum must be reconciled exactly once')
        from collections import Counter
        if dict(Counter(d.disposition for d in self.decisions))!=self.disposition_counts:
            raise ValueError('Disposition count mismatch')
        return self
