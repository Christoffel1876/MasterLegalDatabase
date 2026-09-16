"""Strict records for a seven-page source transcription; no legal effect inference."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
    path:str
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)
class Span(Strict):
    start:int=Field(ge=0)
    end:int=Field(ge=1)
    text:str
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
class Block(Strict):
    id:str
    page:int=Field(ge=1,le=7)
    kind:Literal['printed_context','table_fragment','editorial_graphic_note']
    transcript_span:Span
    image:Asset
class Mark(Strict):
    page:int=Field(ge=1,le=7)
    kind:Literal['underline','strikethrough','superscript']
    transcript_span:Span
    meaning:Literal['visible_typography_only_not_operative_status']='visible_typography_only_not_operative_status'
class Page(Strict):
    number:int=Field(ge=1,le=7)
    image:Asset
    native:Asset
    native_status:Literal['empty_image_only']='empty_image_only'
    native_spans:list[Span]=Field(max_length=0)
    ocr_json:Asset
    ocr_text:Asset
    transcript_span:Span
    full_image_directly_viewed:Literal[True]=True
class Table(Strict):
    id:str
    title:str
    pages:list[int]
    fragment_block_ids:list[str]
    context_block_ids:list[str]
    physical_data_rows:int=Field(ge=1)
    qualifiers:list[str]
class Link(Strict):
    id:str
    kind:Literal['cross_page_continuation','local_note']
    from_block_id:str
    to_block_id:str
    reason:str
class DateClaim(Strict):
    literal:str
    role:str
    block_ids:list[str]
    external_verification:Literal[False]=False
class Review(Strict):
    schema_version:Literal[1]=1
    source_id:Literal['chaffee-electric-ordinance-2026-01-atlas-directed']
    authority_id:Literal['CO-COUNTY-CHAFFEE']
    reviewer:Literal['Atlas']='Atlas'
    reviewed_at:str
    status:Literal['complete_scoped_source_review_pending_independent_audit']='complete_scoped_source_review_pending_independent_audit'
    source:Asset
    transcript:Asset
    method:str
    full_pages:list[int]
    focused_crops:list[Asset]
    pages:list[Page]=Field(min_length=7,max_length=7)
    blocks:list[Block]
    marks:list[Mark]
    tables:list[Table]=Field(min_length=7,max_length=7)
    links:list[Link]
    dates:list[DateClaim]
    observed_get_completed_at:str
    acquisition_evidence:list[Asset]
    repository_intake_at_review:None=None
    effective_date:None=None
    native_bytes:Literal[0]=0
    ocr_bytes:int
    observations:list[str]
    limitations:list[str]
    external_reviews_consulted:Literal[True]=True
    legal_currentness:Literal['not_verified']='not_verified'
    answer_safe:Literal[False]=False
class Manifest(Strict):
    created_at:str
    files:list[Asset]
