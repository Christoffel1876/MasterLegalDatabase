"""Strict, research-only source QA records; no calculated fee or legal-currentness model."""
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
 path:str
 sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 size_bytes:int=Field(ge=0)
class Span(Strict):
 text:str
 bbox:list[float]=Field(min_length=4,max_length=4)
 font:str
 flags:int
 size:float
class NativeLine(Strict):
 line_id:str
 text:str
 start:int=Field(ge=0)
 end:int=Field(gt=0)
 bbox:list[float]=Field(min_length=4,max_length=4)
 spans:list[Span]
class Geometry(Strict):
 page:int=Field(ge=1,le=7)
 native_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 size_bytes:int=Field(gt=0)
 lines:list[NativeLine]
class Cell(Strict):
 role:Literal['label','fee_as_printed']
 line_ids:list[str]=Field(min_length=1)
 exact_native_text:str
 native_ranges:list[list[int]]
 pdf_bboxes:list[list[float]]
 pixel_bboxes:list[list[int]]
class FeeRow(Strict):
 row_id:str
 table_id:str
 physical_page:int=Field(ge=2,le=5)
 label:Cell
 fee_as_printed:Cell
 global_context_ids:list[str]
 table_context_ids:list[str]
 definition_ids:list[str]
 context_rule:Literal['Return the complete global context, linked table notes and definitions with this source row; conditions remain source wording, not an applicability decision.']
class BlockPart(Strict):
 page:int=Field(ge=1,le=7)
 line_ids:list[str]
 exact_native_text:str
 native_ranges:list[list[int]]
 pdf_bboxes:list[list[float]]
 pixel_bboxes:list[list[int]]
class Block(Strict):
 block_id:str
 kind:Literal['heading','definition','table_note','general_note','implementation','other_schedule_reference','printed_date','cover','contents','footer','native_whitespace']
 parts:list[BlockPart]=Field(min_length=1)
 notes:list[str]
class Table(Strict):
 table_id:str
 heading_block_id:str
 page_order:list[int]
 row_ids:list[str]
 column_roles:Literal['Unlabeled left description and right fee columns; roles are visual associations, not invented printed column headings.']
class Page(Strict):
 physical_page:int=Field(ge=1,le=7)
 source_rect_points:list[float]
 image:Asset
 image_dimensions:list[int]
 native:Asset
 geometry:Asset
 native_line_count:int
 direct_full_image_viewed:Literal[True]
class Provenance(Strict):
 method:Literal['Atlas direct ordinary HTTPS GET retained complete response']
 request_started_at:Literal['2026-09-12T23:10:46.676197Z']
 response_finished_at:Literal['2026-09-12T23:10:47.380038Z']
 official_url:Literal['https://coloradosprings.gov/system/files/2026-07/2026%20Fee%20Schedule%20Construction%20Services.pdf']
 http_status:Literal[200]
 redirect_count:Literal[0]
 event:int=Field(ge=1)
 receipts:list[Asset]
 header_dates_are_legal_dates:Literal[False]
class QA(Strict):
 schema_version:Literal['1.0']
 source_id:Literal['SD014-02']
 authority_id:Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
 issuer:Literal['Colorado Springs Fire Department, Division of the Fire Marshal']
 collector_qualification:str
 source:Asset
 source_sha256:Literal['e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a']
 page_count:Literal[7]
 source_status:Literal['fee_schedule_as_received']
 legal_currentness:Literal['not_verified']
 adoption_verification:Literal['not_verified']
 effective_date_verification:Literal['printed_claim_only']
 printed_effective_date:Literal['07/01/2026']
 review_method:Literal['Atlas source-first direct image QA followed by native comparison; title and role known, not blind']
 reviewed_at:str
 source_first_observations:Asset
 source_first_observations_sha256:Literal['e382da7c1be63d5b7b26be5f0d43d35b1fe55a4486346377fe8895cfbfdbbc97']
 provenance:Provenance
 native_engine:Literal['PyMuPDF 1.28.2 get_text(text, sort=False); UTF-8 unchanged per physical page']
 native_byte_basis:Literal['Zero-based half-open UTF-8 offsets in the named unchanged physical-page native file; PDF bboxes in points, crop bboxes in 200 dpi original-image pixels.']
 native_byte_count:int
 pages:list[Page]=Field(min_length=7,max_length=7)
 tables:list[Table]=Field(min_length=9,max_length=9)
 fee_rows:list[FeeRow]=Field(min_length=128,max_length=128)
 blocks:list[Block]
 all_native_lines_assigned_once:Literal[True]
 all_context_must_accompany_fee_rows:Literal[True]
 comparison_findings:list[str]
 source_anomalies:list[str]
 limits:list[str]
class Crop(Strict):
 path:str
 page:int=Field(ge=1,le=7)
 pixel_bbox:list[int]=Field(min_length=4,max_length=4)
 parent_sha256:str
 sha256:str
class Inventory(Strict):
 schema_version:Literal['1.0']
 status:Literal['frozen_source_qa_pending_root_independent_acceptance']
 source_sha256:Literal['e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a']
 files:list[Asset]
 excluded_paths:Literal['FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only; all other ordinary package files are included.']
 @model_validator(mode='after')
 def distinct(self):
  if len({x.path for x in self.files})!=len(self.files):raise ValueError('duplicate inventory path')
  return self
class Reservation(Strict):
 event:Literal[2]
 source_id:Literal['SD014-02']
 url:str
 hop:Literal[0]
 plan_sha256:str
 reserved_at:str
 deadline:str
 byte_allowance:int
class HTTPResult(Strict):
 event:Literal[2]
 reservation_sha256:str
 finished_at:str
 outcome:Literal['complete']
 http_status:Literal[200]
 body:Asset
 public_headers:Asset
 partial_body:Literal[False]
 content_magic:Literal['pdf']
 charged_bytes:Literal[258393]
 redirect_url:None
 error_type:None
 byte_basis:str
 legal_currentness:Literal['not_verified']
class Headers(Strict):
 headers:dict[str,str]
 rejected_fields:list[str]
 request_url:str
class ValidationResult(Strict):
 status:Literal['validated_source_qa_no_currentness_promotion']
 source_sha256:str
 physical_pages:Literal[7]
 fee_rows:Literal[128]
 tables:Literal[9]
 definition_records:Literal[13]
 table_notes:Literal[3]
 native_bytes:Literal[14423]
 native_lines:Literal[410]
 crops:Literal[12]
 files_verified:int
 legal_currentness:Literal['not_verified']
class TestReceipt(Strict):
 run_at:str
 command:list[str]
 exit_code:Literal[0]
 log:Asset
 coverage_note:str
