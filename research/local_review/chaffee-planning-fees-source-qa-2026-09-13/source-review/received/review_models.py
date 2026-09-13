"""Strict source-fidelity evidence; all amounts and source dates are literal strings."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
    path:str
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)
class Span(Strict):
    path:str
    start:int=Field(ge=0)
    end:int=Field(gt=0)
    text:str
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
    @model_validator(mode='after')
    def ordered(self):
        if self.end<=self.start:raise ValueError('Empty/reversed span')
        return self
class Row(Strict):
    id:str
    page:Literal[1,2]
    group_id:str
    application:str
    fee:str
    application_native:list[Span]=Field(min_length=1)
    fee_native:Span
    related_note_ids:list[str]
class Group(Strict):
    id:str
    heading:str
    parent_heading:str|None
    pages:list[int]
    row_ids:list[str]
    heading_native:Span
    column_headings:tuple[str,str]|None
    heading_on_page2:bool
class Passage(Strict):
    id:str
    page:Literal[1,2]
    kind:Literal['header','title','footer','note','hourly_condition','parent_heading','column_heading']
    text:str
    native:list[Span]=Field(min_length=1)
    applies_to_rows:list[str]
class NativeLine(Strict):
    page:Literal[1,2]
    line:int=Field(gt=0)
    span:Span
    associated_with:str|None
class Graphic(Strict):
    page:Literal[1,2]
    observation:str
    identity_or_authenticity_verified:Literal[False]
class Review(Strict):
    source_id:Literal['chaffee-planning-application-fees-atlas-directed']
    authority_id:Literal['CO-COUNTY-CHAFFEE']
    source:Asset
    reviewed_at:str
    reviewer:Literal['Atlas']
    status:Literal['complete_source_fidelity_pending_independent_review']
    review_kind:Literal['checked_tables']
    legal_currentness:Literal['not_verified']
    answer_safe:Literal[False]
    method:str
    source_pages:list[Asset]=Field(min_length=2,max_length=2)
    native_pages:list[Asset]=Field(min_length=2,max_length=2)
    native_lines:list[NativeLine]
    groups:list[Group]=Field(min_length=10,max_length=10)
    rows:list[Row]=Field(min_length=49,max_length=49)
    passages:list[Passage]
    graphics:list[Graphic]=Field(min_length=2,max_length=2)
    inspected_full_pages:tuple[Literal[1],Literal[2]]
    crops:list[Asset]
    source_date_claims:list[str]
    verified_effective_date:None
    limitations:list[str]
    custody:list[Asset]
