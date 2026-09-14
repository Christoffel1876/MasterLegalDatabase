"""Additive review/custody records; frozen Atlas transcription and QA remain unchanged."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime


class Strict(BaseModel):
    """Reject unknown fields and scalar coercion."""
    model_config=ConfigDict(extra='forbid',strict=True)


class Asset(Strict):
    """One exact package-relative original or derived file."""
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)


class Crop(Strict):
    """Exact reproducible crop settings and declared source of those settings."""
    image:Asset
    physical_page:Literal[1]
    displayed_pdf_clip:list[float]=Field(min_length=4,max_length=4)
    matrix_scale:Literal[4]
    renderer:Literal['PyMuPDF 1.28.2']
    alpha:Literal[False]
    settings_provenance:str
    original_creation_timestamp:None
    visual_scope:str


class RowCheck(Strict):
    """A bounded comparison of five displayed positions, not an applicability decision."""
    row_id:str
    source_qa_row_index:int=Field(ge=0,lt=44)
    displayed_fields:dict[str,str|None]
    cell_positions_reviewed:Literal[5]
    physical_page:Literal[1]
    result:Literal['supported_at_review_resolution']


class Review(Strict):
    """Record independent source/candidate-aware QA without changing earlier evidence."""
    schema_version:Literal[1]
    source_id:Literal['douglas-county-ehs-fees-dcr03']
    issuer:Literal['Douglas County Health Department']
    source_authority_id:Literal['CO-COUNTY-DOUGLAS']
    authority_scope:Literal['issuer identity only; row citations and state/county captions remain source claims']
    completed_at:AwareDatetime
    review_mode:Literal['candidate-aware independent source check; not blind or a new external review']
    source:Asset
    frozen_pass1:Asset
    frozen_qa:Asset
    native:Asset
    original_full_image:Asset
    independent_poppler_image:Asset
    original_input_files:list[Asset]
    reviewed_rows:list[RowCheck]=Field(min_length=44,max_length=44)
    checked_context_ids:list[str]=Field(min_length=7,max_length=7)
    crops:list[Crop]=Field(min_length=5,max_length=5)
    nonblank_native_cell_lines:Literal[218]
    blank_fee_positions:Literal[2]
    total_native_lines:Literal[232]
    total_native_bytes:Literal[4923]
    display_normalizations:list[str]
    additional_transcription_errata:list[str]
    observations:list[str]
    source_printed_dates:list[str]
    acquisition_started_at:AwareDatetime
    acquisition_completed_at:AwareDatetime
    canonical_intake_performed_by_this_task:Literal[False]
    legal_currentness:Literal['not_verified']
    answer_safe:Literal[False]
    limitations:list[str]


class Manifest(Strict):
    """A closed package; the manifest JSON alone is excluded from its own inventory."""
    schema_version:Literal[1]
    frozen_at:AwareDatetime
    files:list[Asset]
    self_excluded:Literal['FINAL_MANIFEST.json']
    status:Literal['source_qa_portable_pending_intake']
    legal_currentness:Literal['not_verified']


class Verification(Strict):
    """Bind offline tests and render replay without claiming legal accuracy."""
    status:Literal['passed']
    started_at:AwareDatetime
    completed_at:AwareDatetime
    test_count:int=Field(ge=12)
    tests_stdout:Asset
    tests_stderr:Asset
    validation_stdout:Asset
    validation_stderr:Asset
    source_qa_unchanged:Literal[True]
    frozen_pass1_unchanged:Literal[True]
    source_unchanged:Literal[True]
    branch_inclusive_coverage:float=Field(ge=90,le=100)
    coverage:Asset
    native_replayed:Literal[True]
    original_full_png_replayed:Literal[True]
    five_crops_replayed:Literal[True]
    independent_poppler_replayed:Literal[True]
    limitations:list[str]
