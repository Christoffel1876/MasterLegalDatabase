"""Model definitions copied from the unchanged original builder, without execution logic."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)

class Asset(Strict):
    path:str
    sha256:str
    size_bytes:int

class Cell(Strict):
    field:str
    displayed_text:str|None
    native_text:str|None
    native_line:int|None
    utf8_start:int|None
    utf8_end:int|None
    unrotated_bbox:list[float]|None
    displayed_bbox:list[float]|None
    blank_region:list[float]|None

class Row(Strict):
    row_id:str
    table:Literal['county','state']
    table_caption_id:str
    footnote_id:str|None
    cells:list[Cell]=Field(min_length=5,max_length=5)

class Context(Strict):
    context_id:str
    kind:Literal['caption','footnote','column_header','image_only_wordmark']
    text:str
    native_lines:list[int]
    unrotated_bbox:list[float]|None
    displayed_bbox:list[float]|None
    applies_to:list[str]

class Erratum(Strict):
    row_id:str
    field:str
    frozen_text:str
    image_supported_text:str
    evidence:Asset
    explanation:str

class QA(Strict):
    schema_version:Literal[1]=1
    source_id:Literal['douglas-county-ehs-fees-dcr03']='douglas-county-ehs-fees-dcr03'
    reviewer:Literal['Atlas']='Atlas'
    completed_at:str
    source:Asset
    source_url:str
    physical_pages:Literal[1]=1
    page_rotation_degrees:Literal[90]=90
    native:Asset
    full_image:Asset
    pass1:Asset
    rows:list[Row]=Field(min_length=44,max_length=44)
    contexts:list[Context]
    errata:list[Erratum]
    observations:list[str]
    limitations:list[str]
    review_status:Literal['source_checked_pending_intake']='source_checked_pending_intake'
    legal_currentness:Literal['not_verified']='not_verified'
    answer_safe:Literal[False]=False

