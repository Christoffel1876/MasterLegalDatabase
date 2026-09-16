"""Strict source-preserving schema for EB017's conditional notice and two tables."""
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class FileRef(Strict):
    path:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes:int=Field(ge=0)
    @field_validator('path')
    @classmethod
    def confined(cls,v):
        p=PurePosixPath(v)
        if p.is_absolute() or '..' in p.parts:raise ValueError('Relative confined path required')
        return v
class Span(Strict):
    physical_page:Literal[1,2]
    start_byte:int=Field(ge=0)
    end_byte_exclusive:int=Field(gt=0)
    text:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
class NativePage(Strict):
    physical_page:Literal[1,2]
    image:FileRef
    native_receipt:FileRef
    native_text:str
    native_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    native_bytes:int=Field(gt=0)
    candidate_start_byte:int=Field(ge=0)
    candidate_end_byte_exclusive:int=Field(gt=0)
    partition:list[Span]
    full_image_directly_reviewed:Literal[True]
class Header(Strict):
    column:int=Field(ge=1,le=3)
    display_text:str|None
    native_span:Span|None
    visibly_blank:bool
class Cell(Strict):
    column:Literal[1,2,3]
    display_text:str
    native_span:Span
    native_occurrence:int=Field(ge=0)
    pdf_bbox:list[float]=Field(min_length=4,max_length=4)
    source_dollar_sign:Literal['$']|None
class Row(Strict):
    row_id:str
    source_row:int=Field(ge=1)
    cells:list[Cell]=Field(min_length=3,max_length=3)
class Table(Strict):
    table_id:Literal['tap_size','single_family']
    physical_page:Literal[2]
    source_position:Literal['left','right']
    heading_text:str
    heading_span:Span
    headers:list[Header]=Field(min_length=3,max_length=3)
    rows:list[Row]
    interpretation_boundary:str
class Observation(Strict):
    id:str
    physical_pages:list[int]
    native_spans:list[Span]
    finding:str
    qualification:str
class ImageOnly(Strict):
    id:str
    physical_page:Literal[1]
    image:FileRef
    source_region:str
    text_lines:list[str]
    native_text_present:Literal[False]
    qualification:str
class Review(Strict):
    schema_version:Literal[1]
    assignment_id:Literal['EB-PDF-017']
    source_id:Literal['greeley-water-sewer-proposed-pif-notice-sd008-08']
    authority_id:Literal['CO-MUNICIPAL-GREELEY']
    prepared_at:datetime
    review_mode:Literal['candidate_aware_source_review_before_external_report']
    external_reports_consulted:Literal[False]
    source_status:Literal['proposed_fee_notice_with_conditional_schedule']
    source_pdf:FileRef
    candidate:FileRef
    input_custody:FileRef
    pages:list[NativePage]=Field(min_length=2,max_length=2)
    tables:list[Table]=Field(min_length=2,max_length=2)
    observations:list[Observation]
    image_only:list[ImageOnly]
    inspected_crops:list[FileRef]
    all_native_bytes:Literal[1316]
    table_data_cells:Literal[24]
    native_changes:Literal['none']
    legal_currentness:Literal['not_verified']
    legal_effect_verified:Literal[False]
    source_and_packet_changed:Literal[False]
    network_requests:Literal[0]
    limits:list[str]
    @field_validator('prepared_at')
    @classmethod
    def aware(cls,v):
        if v.utcoffset() is None:raise ValueError('Timezone required')
        return v
    @model_validator(mode='after')
    def verify_counts(self):
        if [p.physical_page for p in self.pages]!=[1,2]:raise ValueError('Both pages required')
        if {o.id for o in self.observations}!={f'EB017-O{i:02}' for i in range(1,11)}:
            raise ValueError('All ten source observations required')
        if {o.id for o in self.image_only}!={'EB017-IMAGE-01','EB017-IMAGE-02'}:
            raise ValueError('Logo and complete footer observations required')
        if [t.table_id for t in self.tables]!=['tap_size','single_family']:
            raise ValueError('Two separate source tables required')
        if [len(t.rows) for t in self.tables]!=[7,1]:raise ValueError('Wrong source row count')
        if sum(len(r.cells) for t in self.tables for r in t.rows)!=24:
            raise ValueError('All24 data cells required')
        for table in self.tables:
            if [h.column for h in table.headers]!=[1,2,3]:raise ValueError('Header order')
            for row in table.rows:
                if [c.column for c in row.cells]!=[1,2,3]:raise ValueError('Column order')
                for c in row.cells:
                    if (c.source_dollar_sign=='$')!=c.display_text.startswith('$'):
                        raise ValueError('Do not invent or drop printed dollar signs')
        if sum(c.source_dollar_sign=='$' for t in self.tables for r in t.rows for c in r.cells)!=4:
            raise ValueError('Only four source cells have dollar signs')
        return self
