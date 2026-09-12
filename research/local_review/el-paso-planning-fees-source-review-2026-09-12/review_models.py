"""Strict image-bound review records; native, OCR and visual text stay distinct."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
SOURCE_SHA='c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12'
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
 path:str
 sha256:str=Field(pattern='^[a-f0-9]{64}$')
 size_bytes:int=Field(ge=0)
class Cell(Strict):
 column:Literal['application_type','application_fee','project_type','heading','page_label']
 text:str
 state:Literal['visible_text','visibly_blank','visible_text_with_clipped_unresolved_tail']
 pixel_bbox:tuple[int,int,int,int]
 superscript_footnotes:list[int]=Field(default_factory=list)
 transcript_start_byte:int=Field(ge=0)
 transcript_end_byte:int=Field(ge=0)
 native_start_byte:None=None
 native_end_byte:None=None
 @model_validator(mode='after')
 def bound(self):
  x0,y0,x1,y1=self.pixel_bbox
  if not 0<=x0<x1<=2200 or not 0<=y0<y1<=1700:raise ValueError('Cell bbox outside 2200x1700 page')
  if self.transcript_end_byte-self.transcript_start_byte != len(self.text.encode()):raise ValueError('Visual transcript byte length differs')
  if (self.state=='visibly_blank') != (self.text==''):raise ValueError('Blank-cell state differs')
  if any(i<1 or i>15 for i in self.superscript_footnotes):raise ValueError('Invalid footnote')
  return self
class Row(Strict):
 id:str
 physical_page:int=Field(ge=1,le=5)
 role:Literal['fee_row','section_header','column_headers','title','footnote','general_note','page_label']
 section_header_id:str|None=None
 fee_header_id:str|None=None
 note_id:int|None=None
 cells:list[Cell]
class Page(Strict):
 physical_page:int=Field(ge=1,le=5)
 source_image:Asset
 width_px:Literal[2200]=2200
 height_px:Literal[1700]=1700
 pdf_width_pt:Literal[792.0]=792.0
 pdf_height_pt:Literal[612.0]=612.0
 native_file:Asset
 native_status:Literal['empty_native_text_layer']='empty_native_text_layer'
 native_size_bytes:Literal[0]=0
class VisualTranscript(Strict):
 schema_version:Literal[1]=1
 source_id:Literal['el-paso-planning-fees-sd011']='el-paso-planning-fees-sd011'
 authority_id:Literal['CO-COUNTY-EL_PASO']='CO-COUNTY-EL_PASO'
 source_sha256:Literal[SOURCE_SHA]=SOURCE_SHA
 frozen_at:str
 visual_observations:Asset
 review_mode:Literal['source_images_first_then_empty_native_comparison_before_ocr']
 ocr_consulted_at_freeze:Literal[False]=False
 pages:list[Page]
 transcript:Asset
 rows:list[Row]
 unresolved_row_ids:list[str]
 limitations:list[str]
 source_date_claim:str
 verified_effective_date:None=None
 currentness:Literal['not_verified']='not_verified'
 @model_validator(mode='after')
 def integrity(self):
  if [p.physical_page for p in self.pages]!=[1,2,3,4,5]:raise ValueError('Missing/duplicate/reordered page')
  ids=[r.id for r in self.rows]
  if len(ids)!=len(set(ids)):raise ValueError('Duplicate row')
  headers={r.id for r in self.rows if r.role=='section_header'}
  for r in self.rows:
   if r.section_header_id and r.section_header_id not in headers:raise ValueError('Unknown section header')
   if r.role=='fee_row':
    if [c.column for c in r.cells]!=['application_type','application_fee','project_type']:raise ValueError('Fee columns reordered/absent')
    if r.fee_header_id!='P1-COLUMNS':raise ValueError('Fee header missing')
  if len([r for r in self.rows if r.role=='fee_row'])!=104:raise ValueError('Expected 104 fee rows')
  if [r.note_id for r in self.rows if r.role=='footnote']!=list(range(1,16)):raise ValueError('Footnotes incomplete')
  if len([r for r in self.rows if r.role=='general_note'])!=3:raise ValueError('General notes incomplete')
  clipped=[r.id for r in self.rows if any(c.state=='visible_text_with_clipped_unresolved_tail' for c in r.cells)]
  if clipped!=self.unresolved_row_ids or clipped!=['P3-ENG-14']:raise ValueError('Clipping must remain explicitly unresolved')
  return self
class Review(Strict):
 schema_version:Literal[1]=1
 source_id:Literal['el-paso-planning-fees-sd011']='el-paso-planning-fees-sd011'
 authority_id:Literal['CO-COUNTY-EL_PASO']='CO-COUNTY-EL_PASO'
 source_pdf:Asset
 visual_transcript:Asset
 visual_transcript_sha256:str
 completed_at:str
 status:Literal['five_pages_source_reviewed_with_explicit_unresolved_clipped_tail']
 page_coverage:list[int]
 source_fee_rows:Literal[104]=104
 source_footnotes:Literal[15]=15
 source_general_notes:Literal[3]=3
 native_extraction:dict
 ocr_comparison:dict
 custody:dict
 observations:list[str]
 unresolved_regions:list[str]
 fully_legible_complete_extraction:Literal[False]=False
 currentness:Literal['not_verified']='not_verified'
 answer_safe:Literal[False]=False
class Inventory(Strict):
 schema_version:Literal[1]=1
 files:list[Asset]
 exclusions:Literal['FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only']
 @model_validator(mode='after')
 def unique(self):
  if len({r.path for r in self.files})!=len(self.files):raise ValueError('Duplicate manifest entry')
  return self
class Erratum(Strict):
 id:str
 row_id:str
 column:Literal['application_type']
 before:str
 after:str
 source_crop:Asset
 source_page:int=Field(ge=1,le=5)
 pixel_bbox:tuple[int,int,int,int]
 basis:str
class VisualErrata(Strict):
 frozen_original:Asset
 prepared_at:str
 entries:list[Erratum]
 originals_modified:Literal[False]=False
class ReviewedGrid(VisualTranscript):
 review_mode:Literal['candidate_aware_visual_grid_after_separate_ocr_comparison']
 ocr_consulted_at_freeze:Literal[True]=True
 initial_visual_transcript:Asset
 visual_errata:Asset
 ocr_receipt:Asset
class OCRCell(Strict):
 row_id:str
 physical_page:int=Field(ge=1,le=5)
 column:Literal['application_type','application_fee','project_type']
 ocr_observation_indices:list[int]
 ocr_text:str
 visual_text_with_footnote_markers:str
 equal_after_whitespace_collapse:bool
 disposition:Literal['comparison_agreement_not_proof','ocr_omitted_visible_project_code','ocr_superscript_misread_or_omitted','ocr_fee_punctuation_error','source_spacing_or_line_wrap_preserved']
class OCRComparison(Strict):
 status:Literal['uncorrected_ocr_compared_to_image_reviewed_grid']
 reviewed_grid:Asset
 ocr_receipt:Asset
 method:Literal['observation_bbox_center_in_recorded_cell_then_engine_order; comparison only']
 cells:list[OCRCell]
 final_differences:int=Field(ge=0)
 original_visual_errors_corrected_additively:Literal[3]=3
 confidence_interpretation:Literal['Engine scores are not verification or a probability of legal accuracy.']
class NativeSummary(Strict):
 engine:Literal['PyMuPDF']='PyMuPDF'
 version:str
 method:Literal['Page.get_text("text", sort=False, flags=195)']
 page_files:list[Asset]
 page_count:Literal[5]=5
 total_utf8_bytes:Literal[0]=0
 status:Literal['empty_native_text_on_all_five_pages']='empty_native_text_on_all_five_pages'
 candidate_with_page_markers:Asset
class OCRSummary(Strict):
 status:Literal['machine_ocr_unreviewed_preserved_with_separate_visual_comparison']
 receipt:Asset
 comparison:Asset
 engine:Literal['Apple Vision']='Apple Vision'
 revision:Literal[3]=3
 actual_os_version:str
 expected_pages:Literal[5]=5
 returned_pages:Literal[5]=5
 engine_observation_count:int
 failed_attempts_before_success:Literal[2]=2
 engine_rerun_required_for_offline_verification:Literal[False]=False
class Custody(Strict):
 acquisition_method:Literal['received_review_package']
 received_from:Literal['Sherlock']
 claimed_source_url:str
 claimed_final_url:str
 claimed_http_acquisition_at:str
 verified_http_acquisition_at:None=None
 actual_repository_received_at:str
 intake_status:Literal['archived_pending_pipeline']
 intake_receipt:Asset
 source_provenance_manifest:Asset
 source_provenance_line_number:Literal[1]=1
 source_provenance_line_sha256:str
 source_referral_html:Asset
 source_public_headers:Asset
 limitations:list[str]
class SourceQA(Strict):
 schema_version:Literal[1]=1
 source_id:Literal['el-paso-planning-fees-sd011']='el-paso-planning-fees-sd011'
 authority_id:Literal['CO-COUNTY-EL_PASO']='CO-COUNTY-EL_PASO'
 source_pdf:Asset
 initial_visual_transcript:Asset
 reviewed_grid:Asset
 visual_errata:Asset
 completed_at:str
 status:Literal['five_pages_source_reviewed_with_explicit_unresolved_clipped_tail']
 page_coverage:list[int]
 source_fee_rows:Literal[104]=104
 source_footnotes:Literal[15]=15
 source_general_notes:Literal[3]=3
 native_extraction:NativeSummary
 ocr_comparison:OCRSummary
 custody:Custody
 observations:list[str]
 unresolved_regions:list[str]
 fully_legible_complete_extraction:Literal[False]=False
 currentness:Literal['not_verified']='not_verified'
 verified_adoption_date:None=None
 verified_effective_date:None=None
 answer_safe:Literal[False]=False
class TamperResults(Strict):
 prepared_at:str
 command:list[str]
 tests_passed:int
 tests_failed:Literal[0]=0
 receipt_scope:Literal['Offline integrity/refusal tests, not independent visual correctness.']
 stdout_sha256:str
