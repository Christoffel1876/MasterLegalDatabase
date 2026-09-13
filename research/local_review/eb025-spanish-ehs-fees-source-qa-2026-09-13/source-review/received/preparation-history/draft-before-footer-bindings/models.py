from pydantic import BaseModel,ConfigDict,Field,model_validator
from typing import Literal
class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
 path:str
 sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
 size_bytes:int=Field(ge=0)
class Span(Strict):
 page:int=Field(ge=1,le=6)
 start_byte:int=Field(ge=0)
 end_byte:int=Field(ge=0)
 text:str
 sha256:str
class Page(Strict):
 page:int
 png:Asset
 native:Asset
 text:str
 full_image_directly_viewed:Literal[True]=True
 limits:str
class Cell(Strict):
 column:int
 span_columns:int
 bbox:list[float]|None
 representation:str
 text:str|None
 native_span:Span|None
class Row(Strict):
 row_id:str
 physical_page:int
 physical_table:int
 physical_row:int
 role:Literal['title','column_headers','category','fee','continuation']
 category_source_row:str|None
 cells:list[Cell]
class Passage(Strict):
 id:str
 role:str
 span:Span
 visual_note:str
class Link(Strict):
 id:str
 source_rows:list[str]
 target_passages:list[str]
 kind:Literal['footnote','continuation','section_context']
 note:str
class Crop(Strict):
 asset:Asset
 source_page:int
 source_sha256:str
 box_pixels:list[int]
 method:Literal['exact source pixels via PyMuPDF Pixmap.copy; no resampling']
class Review(Strict):
 schema_version:Literal[1]=1
 assignment:Literal['EB-PDF-025']='EB-PDF-025'
 source_id:Literal['el-paso-boh-ehs-fees-spanish-sd011']='el-paso-boh-ehs-fees-spanish-sd011'
 authority_id:Literal['CO-COUNTY-EL_PASO']='CO-COUNTY-EL_PASO'
 language:Literal['Spanish']='Spanish'
 prepared_at:str
 source:Asset
 candidate:Asset
 pages:list[Page]
 rows:list[Row]
 passages:list[Passage]
 links:list[Link]
 crops:list[Crop]
 native_bytes:int
 candidate_bytes:int
 physical_table_rows:Literal[75]=75
 fee_rows:Literal[65]=65
 full_pages_directly_viewed:list[int]
 method:str
 observations:list[str]
 limitations:list[str]
 legal_currentness:Literal['not_verified']='not_verified'
 answer_safe:Literal[False]=False
 translation_equivalence_verified:Literal[False]=False
 source_modified:Literal[False]=False
 native_modified:Literal[False]=False
 external_reports_consulted:Literal[False]=False
 @model_validator(mode='after')
 def scope(self):
  if [p.page for p in self.pages]!=[1,2,3,4,5,6] or self.full_pages_directly_viewed!=[1,2,3,4,5,6]:raise ValueError('Six full pages required')
  if len(self.rows)!=75 or sum(r.role=='fee' for r in self.rows)!=65:raise ValueError('Table scope differs')
  if len({r.row_id for r in self.rows})!=75:raise ValueError('Duplicate row')
  return self
