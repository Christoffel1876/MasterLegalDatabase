"""Strict source-bound historical fee rows; no current-law or numeric normalization."""
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal
import hashlib
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Asset(Strict):
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    bytes:int=Field(ge=0)
    @field_validator('path')
    @classmethod
    def safe(cls,v):
        p=PurePosixPath(v)
        if p.is_absolute() or '..' in p.parts or str(p)!=v or '\\' in v:raise ValueError('unsafe path')
        return v
class Span(Strict):
    page:int=Field(ge=1,le=3)
    start:int=Field(ge=0)
    end:int=Field(ge=0)
    text:str
    sha256:str
    @model_validator(mode='after')
    def exact(self):
        b=self.text.encode()
        if len(b)!=self.end-self.start or hashlib.sha256(b).hexdigest()!=self.sha256:raise ValueError('span bytes')
        return self
class Line(Strict):
    number:int
    bbox:tuple[float,float,float,float]
    evidence:Span
class Page(Strict):
    number:int
    native:Asset
    image:Asset
    layout:Asset
    lines:list[Line]
    directly_viewed:Literal[True]=True
class Cell(Strict):
    column_id:str
    evidence:list[Span]
    native_text:str | None
    glyph_bbox:tuple[float,float,float,float] | None
    annotation:str
    @model_validator(mode='after')
    def unchanged(self):
        expected=''.join(x.text for x in self.evidence)
        if self.native_text is not None and self.native_text!=expected:raise ValueError('cell text changed')
        if self.native_text is None and self.evidence:raise ValueError('null cell has text')
        return self
class Row(Strict):
    id:str
    table_id:str
    page:int
    order:int
    source_lines:tuple[int,int]
    evidence:Span
    cells:list[Cell]
    parent_context_ids:list[str]
    annotation:str
class Table(Strict):
    id:str
    page:int
    title:str
    columns:list[str]
    row_ids:list[str]
    context_ids:list[str]
    authority_note:str
class Context(Strict):
    id:str
    page:int
    evidence:Span
    applies_to:list[str]
    note:str
class Observation(Strict):
    id:str
    related_ids:list[str]
    evidence:list[Span]
    finding:str
    treatment:str
class HTMLObservation(Strict):
    source:Asset
    snapshot_text:Asset
    source_url:str
    retrieved_at:datetime
    exact_claim:str
    start_byte:int
    end_byte:int
    claim_sha256:str
    note:str
class Crop(Strict):
    id:str
    page:int
    clip:tuple[float,float,float,float]
    scale:float
    image:Asset
    directly_viewed:Literal[True]=True
class Review(Strict):
    review_id:Literal['ATLAS-MESA-PLANNING-FEES-2026-09-11']
    authority_id:Literal['CO-COUNTY-MESA']
    source:Asset
    candidate:Asset
    source_url:str
    acquired_at:datetime
    completed_at:datetime
    engine_version:Literal['1.28.2']
    native_flags:Literal[195]
    native_sort:Literal[False]
    native_bytes:int
    native_byte_changes:Literal[0]
    review_mode:Literal['atlas_candidate_aware_not_blind']
    external_assignment:None
    status:Literal['all_three_pages_source_rows_and_associations_reviewed']
    legal_currentness:Literal['not_verified']
    adoption_effectiveness:Literal['not_verified']
    pages:list[Page]
    tables:list[Table]
    rows:list[Row]
    contexts:list[Context]
    observations:list[Observation]
    html_claims:list[HTMLObservation]
    crops:list[Crop]
    limits:list[str]
    @model_validator(mode='after')
    def relations(self):
        if [p.number for p in self.pages]!=[1,2,3]:raise ValueError('three ordered pages')
        ts={t.id:t for t in self.tables};rs={r.id:r for r in self.rows};cs={c.id:c for c in self.contexts}
        if len(ts)!=len(self.tables) or len(rs)!=len(self.rows) or len(cs)!=len(self.contexts):raise ValueError('duplicate identity')
        for t in self.tables:
            actual=[r for r in self.rows if r.table_id==t.id]
            if [r.id for r in actual]!=t.row_ids or [r.order for r in actual]!=list(range(1,len(actual)+1)):raise ValueError('row count/order')
            if not set(t.context_ids)<=cs.keys():raise ValueError('missing table context')
            for r in actual:
                if r.page!=t.page or [c.column_id for c in r.cells]!=t.columns:raise ValueError('row/column mismatch')
        for r in self.rows:
            if not set(r.parent_context_ids)<=cs.keys():raise ValueError('missing row conditions')
            for c in r.cells:
                for s in c.evidence:
                    if s.page!=r.page or s.start<r.evidence.start or s.end>r.evidence.end:raise ValueError('cell escapes source row')
        if self.native_bytes!=sum(p.native.bytes for p in self.pages):raise ValueError('native total')
        return self
class Layout(Strict):
    source_sha256:str
    page:int
    native_sha256:str
    rawdict:dict
class Inventory(Strict):
    files:list[Asset]
    excluded_self:Literal['evidence-manifest.json']
    @model_validator(mode='after')
    def unique(self):
        paths=[a.path for a in self.files]
        if paths!=sorted(set(paths)):raise ValueError('inventory order/duplicates')
        return self
