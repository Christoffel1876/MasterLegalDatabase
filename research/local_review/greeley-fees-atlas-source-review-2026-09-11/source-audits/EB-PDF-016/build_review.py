"""Build or verify the candidate-aware three-page EB016 source review."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal
import jsonschema
import pymupdf
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT=Path('/Users/mcoors/Documents/Project Geode')
PACKET=ROOT/'handoffs/grok-pdf-review-2026-09-11-batch-5'
SID='greeley-development-impact-fee-memo-sd008-07'
OUT=ROOT/'handoffs/atlas-reviews'/SID/'pre-review-2026-09-11'
SOURCE_SHA='9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709'
CANDIDATE_SHA='1c45252c6c814258f5a2e8380001f282a609ad9db81ec3947655b871346296f9'
SHA=Annotated[str,Field(pattern=r'^[0-9a-f]{64}$')]
PAGE=Annotated[int,Field(ge=1,le=3)]
RECT=Annotated[list[float],Field(min_length=4,max_length=4)]
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return ' '.join(s.split())
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Ref(Strict):
 path:str
 sha256:SHA
 size_bytes:Annotated[int,Field(gt=0)]
class InputCopy(Strict):
 original_path:str
 frozen:Ref
 role:str
class Span(Strict):
 physical_page:PAGE
 start_byte:Annotated[int,Field(ge=0)]
 end_byte_exclusive:Annotated[int,Field(gt=0)]
 candidate_start_byte:Annotated[int,Field(ge=0)]
 candidate_end_byte_exclusive:Annotated[int,Field(gt=0)]
 text:str
 sha256:SHA
 @model_validator(mode='after')
 def valid(self):
  b=self.text.encode()
  if not b or sha(b)!=self.sha256 or len(b)!=self.end_byte_exclusive-self.start_byte or len(b)!=self.candidate_end_byte_exclusive-self.candidate_start_byte:raise ValueError('Bad span')
  return self
class Chunk(Strict):
 id:str
 role:Literal['layout_whitespace','native_artifact','header','body','table']
 visibility:Literal['visible','not_visible_in_checked_render','layout_whitespace']
 span:Span
class Page(Strict):
 physical_page:PAGE
 source_sha256:SHA
 image:Ref
 evidence:Ref
 native_file:Ref
 native_sha256:SHA
 native_text:str
 candidate_start_byte:int
 candidate_end_byte_exclusive:int
 chunks:list[Chunk]
 printed_page_label:str|None
 full_page_visually_checked:Literal[True]
 @model_validator(mode='after')
 def valid(self):
  b=self.native_text.encode();pos=0
  if sha(b)!=self.native_sha256 or len(b)!=self.candidate_end_byte_exclusive-self.candidate_start_byte:raise ValueError('Page bytes')
  for c in self.chunks:
   s=c.span
   if s.physical_page!=self.physical_page or s.start_byte!=pos or b[pos:s.end_byte_exclusive]!=s.text.encode():raise ValueError('Partition')
   pos=s.end_byte_exclusive
  if pos!=len(b):raise ValueError('Nonexhaustive partition')
  return self
class Crop(Strict):
 id:str
 physical_page:PAGE
 pdf_rect_points:RECT
 file:Ref
 method:Literal['PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False']
 visually_checked:Literal[True]
class Cell(Strict):
 column_start:Annotated[int,Field(ge=1,le=8)]
 column_span:Annotated[int,Field(ge=1,le=8)]
 text:str
 status:Literal['native_bound_visible_text','visually_blank']
 native_spans:list[Span]
 @model_validator(mode='after')
 def valid(self):
  if self.status=='visually_blank':
   if self.text or self.native_spans:raise ValueError('Invented blank cell text')
  elif not self.native_spans or self.text!=norm(' '.join(s.text for s in self.native_spans)):raise ValueError('Cell not exact whitespace-normalized spans')
  return self
class Row(Strict):
 id:str
 role:Literal['caption','column_header','group_header','fee','weight','percent_change','spacer']
 fee_group_header_row_id:str|None
 pdf_rect_points:RECT
 cells:list[Cell]
 @model_validator(mode='after')
 def valid(self):
  occupied=[]
  for c in self.cells:occupied+=list(range(c.column_start,c.column_start+c.column_span))
  if len(set(occupied))!=len(occupied):raise ValueError('Overlapping grid cells')
  if (self.role=='fee')!=(self.fee_group_header_row_id is not None):raise ValueError('Fee group binding shape')
  return self
class Table(Strict):
 id:str
 physical_page:PAGE
 source_sha256:SHA
 source_image_sha256:SHA
 column_count:Annotated[int,Field(ge=1,le=8)]
 pdf_rect_points:RECT
 column_role_notes:list[str]
 header_reference_row_ids:list[str]
 native_span:Span
 rows:list[Row]
 visual_association_notes:list[str]
 @model_validator(mode='after')
 def valid(self):
  for r in self.rows:
   occupied=[n for c in r.cells for n in range(c.column_start,c.column_start+c.column_span)]
   if sorted(occupied)!=list(range(1,self.column_count+1)):raise ValueError('Incomplete table row')
   for c in r.cells:
    if any(s.physical_page!=self.physical_page for s in c.native_spans):raise ValueError('Foreign table text')
  return self
class Observation(Strict):
 id:str
 physical_page:PAGE
 source_sha256:SHA
 source_image_sha256:SHA
 kind:Literal['source_wording','date_role','reading_order','native_not_visible','image_only','scope_boundary','source_arithmetic','source_layout']
 pdf_rect_points:RECT
 native_spans:list[Span]
 image_only_words:str|None
 finding:str
 limitation:str
 crop_ids:list[str]
 legal_effect:Literal['not_determined']
class Review(Strict):
 schema_version:Literal[1]
 reviewed_at:datetime
 source_id:Literal['greeley-development-impact-fee-memo-sd008-07']
 assignment_id:Literal['EB-PDF-016']
 status:Literal['three_page_candidate_aware_source_qa_complete_pending_parent_integration']
 legal_currentness:Literal['not_verified']
 review_mode:Literal['candidate_aware_not_blind']
 external_review_consulted:Literal[False]
 prior_exposure:str
 input_copies:list[InputCopy]
 source:Ref
 candidate:Ref
 packet_manifest:Ref
 expected_pages:Literal[3]
 pages:list[Page]
 crops:list[Crop]
 tables:list[Table]
 observations:list[Observation]
 text_edits_applied:Annotated[list[str],Field(max_length=0)]
 normalization_policy:str
 no_arithmetic_recomputation:Literal[True]
 fee_row_count:Literal[30]
 footnotes_observed:list[str]
 provenance_limits:list[str]
 limits:list[str]
 @model_validator(mode='after')
 def valid(self):
  if self.source.sha256!=SOURCE_SHA or self.candidate.sha256!=CANDIDATE_SHA:raise ValueError('Wrong inputs')
  if [p.physical_page for p in self.pages]!=[1,2,3]:raise ValueError('Page set')
  pages={p.physical_page:p for p in self.pages}
  spans=[]
  for t in self.tables:
   if t.source_sha256!=SOURCE_SHA or t.source_image_sha256!=pages[t.physical_page].image.sha256:raise ValueError('Table source')
   spans.append(t.native_span)
   for row in t.rows:
    for c in row.cells:spans+=c.native_spans
  for o in self.observations:
   if o.source_sha256!=SOURCE_SHA or o.source_image_sha256!=pages[o.physical_page].image.sha256:raise ValueError('Observation source')
   if any(s.physical_page!=o.physical_page for s in o.native_spans):raise ValueError('Observation page')
   spans+=o.native_spans
  for p in self.pages:
   if p.source_sha256!=SOURCE_SHA:raise ValueError('Page source')
   spans += [c.span for c in p.chunks]
  for s in spans:
   p=pages[s.physical_page]
   if p.native_text.encode()[s.start_byte:s.end_byte_exclusive]!=s.text.encode():raise ValueError('Span bytes mismatch')
   if p.candidate_start_byte+s.start_byte!=s.candidate_start_byte or p.candidate_start_byte+s.end_byte_exclusive!=s.candidate_end_byte_exclusive:raise ValueError('Candidate offset')
  ids=[r.id for t in self.tables for r in t.rows]
  if len(ids)!=len(set(ids)):raise ValueError('Duplicate row ID')
  if any(rid not in ids for t in self.tables for rid in t.header_reference_row_ids):raise ValueError('Missing cross-page header')
  for t in self.tables:
   headers={r.id for r in t.rows if r.role=='group_header'}
   if any(r.fee_group_header_row_id not in headers for r in t.rows if r.role=='fee'):raise ValueError('Missing fee group header')
  if sum(r.role=='fee' for t in self.tables for r in t.rows)!=30:raise ValueError('Not 30 fees')
  if len(self.tables)!=3:raise ValueError('Not three table regions')
  for t in self.tables:
   # Every non-whitespace native table byte belongs to exactly one cell.
   b=pages[t.physical_page].native_text.encode();counts=[0]*len(b)
   for r in t.rows:
    for c in r.cells:
     for s in c.native_spans:
      for i in range(s.start_byte,s.end_byte_exclusive):counts[i]+=1
   for i in range(t.native_span.start_byte,t.native_span.end_byte_exclusive):
    if not chr(b[i]).isspace() and counts[i]!=1:raise ValueError(f'Table non-whitespace coverage {t.id} at {i}: {counts[i]}')
  return self

CLIPS=[('p1-header',1,(45,30,565,225)),('p1-body',1,(45,235,570,623)),('p1-eaf',1,(45,622,545,732)),('p2-prose',2,(48,60,570,220)),('p2-police-fire',2,(48,225,532,490)),('p2-park-trails-storm',2,(48,492,533,696)),('p3-transportation',3,(48,70,535,198))]

def ref(p):return Ref(path=str(p.relative_to(OUT)),sha256=sha(p.read_bytes()),size_bytes=p.stat().st_size)
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise ValueError(f'Would overwrite {p}')
 else:p.write_bytes(b)
def build():
 assert not (OUT/'SOURCE_QA.json').exists()
 manifest=json.loads((PACKET/'manifest.json').read_bytes());md=next(d for d in manifest['documents'] if d['source_id']==SID)
 copies=[]
 def copy(rel,dst,role):
  src=PACKET/rel;target=OUT/dst;save(target,src.read_bytes());r=ref(target)
  copies.append(InputCopy(original_path=str(src),frozen=r,role=role));return r
 original=copy(md['original']['path'],'inputs/original.pdf','Exact retained original; source custody, not a new acquisition')
 candidate=copy(md['candidate']['path'],'inputs/candidate.txt','Entire untouched page-marked native candidate')
 packet=copy('manifest.json','inputs/packet-manifest.json','Frozen batch manifest; only EB016 references are in this bounded review')
 assert original.sha256==md['original']['sha256'] and candidate.sha256==md['candidate']['sha256']
 canonical=Path(md['provenance']['canonical_raw_pdf']['path']);assert canonical.read_bytes()==(OUT/original.path).read_bytes()
 pdata={};pages=[]
 for item in md['pages']:
  n=item['physical_page'];im=copy(item['image']['path'],f'inputs/page-{n:04d}.png','Full original 300 dpi Poppler page render')
  ev=copy(item['evidence']['path'],f'inputs/page-{n:04d}.json','Unaltered native extraction evidence')
  data=json.loads((OUT/ev.path).read_bytes());text=data['text'];b=text.encode();start=item['candidate_text_offset_bytes']
  assert sha(b)==item['text_sha256'] and (OUT/candidate.path).read_bytes()[start:item['candidate_text_end_byte_exclusive']]==b
  assert sha((PACKET/item['image']['path']).read_bytes())==data['source_image_sha256']
  save(OUT/f'original-native/page-{n:04d}.txt',b)
  pdata[n]={'text':text,'b':b,'start':start,'im':im,'ev':ev,'native':ref(OUT/f'original-native/page-{n:04d}.txt'),'lines':[]}
  pos=0
  for line in text.splitlines(keepends=True):pdata[n]['lines'].append((pos,pos+len(line.encode()),line));pos+=len(line.encode())
 def span(n,a,b):
  raw=pdata[n]['b'][a:b];return Span(physical_page=n,start_byte=a,end_byte_exclusive=b,candidate_start_byte=pdata[n]['start']+a,candidate_end_byte_exclusive=pdata[n]['start']+b,text=raw.decode(),sha256=sha(raw))
 def ls(n,i):
  a,b,_=pdata[n]['lines'][i];return span(n,a,b)
 def find(n,s,after=0):return pdata[n]['b'].index(s.encode(),after)
 def region(n,s,end=None):
  a=find(n,s);b=find(n,end,a+len(s.encode())) if end else len(pdata[n]['b']);return span(n,a,b)
 def linecell(n,i,c,cs=1):return cell(c,[ls(n,i)],cs)
 def cell(c,spans,cs=1):return Cell(column_start=c,column_span=cs,text=norm(' '.join(s.text for s in spans)),status='native_bound_visible_text',native_spans=spans)
 def blank(c,cs=1):return Cell(column_start=c,column_span=cs,text='',status='visually_blank',native_spans=[])
 def row(rid,role,rect,cells):return Row(id=rid,role=role,fee_group_header_row_id=rid.rsplit('-fee-',1)[0]+'-header' if role=='fee' else None,pdf_rect_points=list(map(float,rect)),cells=cells)
 for n,d in pdata.items():
  b=d['b'];head=find(n,'2026 Development Impact Fee Schedule');headend=head+len('2026 Development Impact Fee Schedule \n'.encode())
  if n==1:
   artifact=find(n,'-A\n');table=find(n,'2026 EAF – Weighting and Percent Change by Indicator')
   cuts=[(0,artifact,'layout_whitespace','layout_whitespace'),(artifact,head,'native_artifact','not_visible_in_checked_render'),(head,headend,'header','visible'),(headend,table,'body','visible'),(table,len(b),'table','visible')]
  else:
   table=find(n,'Fee Structure' if n==2 else 'Transportation Development Fee')
   cuts=[(0,head,'layout_whitespace','layout_whitespace'),(head,headend,'header','visible')]
   if table>headend:cuts.append((headend,table,'body','visible'))
   cuts.append((table,len(b),'table','visible'))
  chunks=[Chunk(id=f'p{n}-chunk-{i}',role=role,visibility=vis,span=span(n,a,z)) for i,(a,z,role,vis) in enumerate(cuts,1)]
  pages.append(Page(physical_page=n,source_sha256=SOURCE_SHA,image=d['im'],evidence=d['ev'],native_file=d['native'],native_sha256=sha(b),native_text=d['text'],candidate_start_byte=d['start'],candidate_end_byte_exclusive=d['start']+len(b),chunks=chunks,printed_page_label=None,full_page_visually_checked=True))
 # EAF grid: line indexes derive from the untouched native table tail.
 t1=region(1,'2026 EAF – Weighting and Percent Change by Indicator');ix=next(i for i,x in enumerate(pdata[1]['lines']) if x[0]==t1.start_byte)
 def e(offset):return ls(1,ix+offset)
 # Native header order is interleaved; each word is bound separately.
 rows1=[row('eaf-caption','caption',(58,627,534,643),[cell(1,[e(0)],8)]),row('eaf-header','column_header',(58,643,534,688),[
  blank(1),cell(2,[e(2),e(4),e(10)]),cell(3,[e(5),e(11)]),cell(4,[e(6),e(12)]),cell(5,[e(7),e(13)]),cell(6,[e(8),e(14)]),cell(7,[e(3),e(9),e(15)]),cell(8,[e(22),e(23),e(24)])]),
  row('eaf-weight','weight',(58,688,534,704),[cell(1,[e(1)])]+[cell(c,[e(14+c)]) for c in range(2,8)]+[blank(8)]),
  row('eaf-change','percent_change',(58,704,534,721),[cell(c,[e(24+c)]) for c in range(1,9)])]
 table1=Table(id='eaf',physical_page=1,source_sha256=SOURCE_SHA,source_image_sha256=pdata[1]['im'].sha256,column_count=8,pdf_rect_points=[58.,627.,534.,721.],column_role_notes=['Row label','Greeley Utility Customers','CDOT CCI','ENR CCI','ENR BCI','Assessed Value','Greeley MSA Employment','Economic Adjustment Factor'],header_reference_row_ids=['eaf-header'],native_span=t1,rows=rows1,visual_association_notes=['Header words are noncontiguous in native reading order; listed spans follow each visible cell top to bottom.','Top-left header and Economic Adjustment Factor weight cell are visibly blank, not zero.','All percentages are printed strings; weighting and results were not recalculated.'])
 # Main fee grid, complete headers, group headers, separators and 23 data rows.
 rows2=[row('fees-column-header','column_header',(58,229,523,261),[linecell(2,434,1,2),cell(3,[ls(2,435),ls(2,438)]),cell(4,[ls(2,436),ls(2,439)]),cell(5,[ls(2,437),ls(2,440)])])]
 group_specs=[('police',441,443,7,261.7,274.9,True),('fire',474,476,7,380.5,393.7,True),('park',507,508,4,499.4,512.6,False),('trails',524,525,4,578.6,591.8,False),('storm-drainage',541,543,1,657.9,671.1,True)]
 for gi,(name,h,start,count,yh,yd,unithead) in enumerate(group_specs):
  hc=[linecell(2,h,1),linecell(2,h+1,2)] if unithead else [linecell(2,h,1,2)]
  rows2.append(row(f'{name}-header','group_header',(58,yh,523,yd),hc+[blank(c) for c in [3,4,5]]))
  j=start
  for k in range(count):
   label=pdata[2]['lines'][j][2]
   if label.startswith('Residential'):
    cells=[linecell(2,j,1,2)]+[linecell(2,j+c-2,c) for c in [3,4,5]];j+=4
   else:
    cells=[linecell(2,j,1),linecell(2,j+1,2)]+[linecell(2,j+c-1,c) for c in [3,4,5]];j+=5
   rows2.append(row(f'{name}-fee-{k+1}','fee',(58,yd+k*13.22,523,yd+(k+1)*13.22),cells))
  if gi<len(group_specs)-1:rows2.append(row(f'{name}-spacer','spacer',(58,yd+count*13.22,523,group_specs[gi+1][4]),[blank(1,5)]))
 table2=Table(id='fees-page-2',physical_page=2,source_sha256=SOURCE_SHA,source_image_sha256=pdata[2]['im'].sha256,column_count=5,pdf_rect_points=[58.,229.,523.,686.],column_role_notes=['Fee structure / use category','Unit (residential rows merge columns 1–2 and include heated living space in their labels)','2025 Fee','% Change','2026 Fee'],header_reference_row_ids=['fees-column-header'],native_span=region(2,'Fee Structure'),rows=rows2,visual_association_notes=['Residential rows are merged across the use and unit columns; no unprinted per-dwelling unit is supplied.','Park and Trails group labels merge the first two columns; their numeric group-header cells are blank.','Four visibly blank separator bands have no native text. The Trails separator includes the taller lower whitespace beneath its final row.','Commercial units preserve the source abbreviation 1,000 Sq. Ft of Building. Storm Drainage preserves Per Impervious Square Foot and three-decimal dollar values.'])
 rows3=[row('transportation-header','group_header',(58,80,523,93.2),[linecell(3,97,1),linecell(3,98,2)]+[blank(c) for c in [3,4,5]])]
 for k in range(7):
  if k<4:cells=[linecell(3,99+k,1,2)]
  elif k<6:cells=[linecell(3,103+(k-4)*2,1),linecell(3,104+(k-4)*2,2)]
  else:cells=[linecell(3,125,1),linecell(3,126,2)]
  if k<6:cells += [linecell(3,107+k,3),linecell(3,113+k,4),linecell(3,119+k,5)]
  else:cells += [linecell(3,127,3),linecell(3,128,4),linecell(3,129,5)]
  rows3.append(row(f'transportation-fee-{k+1}','fee',(58,93.2+k*13.22,523,93.2+(k+1)*13.22),cells))
 table3=Table(id='transportation-page-3',physical_page=3,source_sha256=SOURCE_SHA,source_image_sha256=pdata[3]['im'].sha256,column_count=5,pdf_rect_points=[58.,80.,523.,186.],column_role_notes=['Fee structure / use category','Unit (residential rows merge columns 1–2)','2025 Fee, carried from page 2 header','% Change, carried from page 2 header','2026 Fee, carried from page 2 header'],header_reference_row_ids=['fees-column-header'],native_span=region(3,'Transportation Development Fee'),rows=rows3,visual_association_notes=['The year and percentage headings are not repeated on page 3. The continuing grid aligns with the explicitly cited page 2 header.','Native text emits the first six labels, six 2025 values, six changes and six 2026 values, followed by the complete Industrial row. Cell spans preserve that native ordering while the row records express the visible associations.','Commercial units here read 1,000 Square Feet of Building; they are not silently abbreviated to match page 2.'])
 tables=[table1,table2,table3]
 crops=[]
 for name,n,rect in CLIPS:crops.append(Crop(id=name,physical_page=n,pdf_rect_points=list(map(float,rect)),file=ref(OUT/'crops'/f'{name}.png'),method='PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False',visually_checked=True))
 observations=[]
 def obs(ident,n,kind,rect,spans,finding,limit,crop_ids,imagewords=None):
  observations.append(Observation(id=ident,physical_page=n,source_sha256=SOURCE_SHA,source_image_sha256=pdata[n]['im'].sha256,kind=kind,pdf_rect_points=list(map(float,rect)),native_spans=spans,image_only_words=imagewords,finding=finding,limitation=limit,crop_ids=crop_ids,legal_effect='not_determined'))
 obs('memo-identity',1,'date_role',(50,30,565,225),[region(1,'2026 Development Impact Fee Schedule','In the 2023 adoption')],'The source identifies a Finance Department memorandum dated November 1, 2025, from City of Greeley, Colorado, concerning 2026 Development Impact Fees.','The memorandum date and subject year do not independently establish an adopted ordinance or current fees.',['p1-header'])
 obs('native-minus-a',1,'native_not_visible',(178,63,205,89),[span(1,find(1,'-A\n'),find(1,'-A\n')+3)],'The native extraction contains -A before the repeated page title. No -A is visible in the full page or direct header crop at its PDF text bounds. It remains in the exhaustive original bytes.','Do not append it to the visible title or silently remove it from the native record. Cause of the invisible text is not certified.',['p1-header'])
 obs('logo',1,'image_only',(52,65,177,143),[],'The colored logo contains the words City of, Greeley and Colorado. These logo words are recorded as image evidence, separately from native text.','This is a visual word observation, not a complete vector/logo transcription or a signature/authenticity claim.',['p1-header'],'City of; Greeley; Colorado')
 obs('adoption-methodology-claim',1,'scope_boundary',(52,239,566,309),[region(1,'In the 2023 adoption','The EAF is determined')],'The memorandum states that the six named development impact fee types and their annual adjustment methodology were adopted in 2023, and cites City of Greeley Code Chapter 4.64.055(b).','This review checks that wording. It does not verify the cited code, the adoption instrument, or the legal status of the 2026 schedule.',['p1-body'])
 obs('six-economic-indicators',1,'source_wording',(52,311,568,561),[region(1,'The EAF is determined','The 2026 EAF was calculated')],'All six listed indicators and their stated purposes are preserved, including Greeley Utility Customer Accounts, both Engineering News Records indices, assessed value and Greeley MSA Employment.','The prose expands labels used in the EAF table; these are source descriptions, not independently validated economic data. Native bullet codepoint U+F0B7 is retained although the visible mark is a round bullet.',['p1-body'])
 obs('eaf-data-period',1,'date_role',(52,563,570,620),[region(1,'The 2026 EAF was calculated','2026 EAF – Weighting')],'The source says the EAF is calculated on November 1, 2025 for fee year 2026 using year end 2024 compared with year end 2023.','Calculation date, fee year and underlying annual comparison periods remain separate. No newer source was opened.',['p1-body'])
 obs('eaf-grid-order',1,'reading_order',(52,622,541,727),[t1],'The table has six weighted indicator columns plus a resulting EAF column. The native header order interleaves words from different columns. The typed cell map restores only their visually checked associations.','The blank EAF weight cell stays blank. The printed -2.07% result and all printed weights and changes are preserved without recomputation.',['p1-eaf'])
 obs('rounding-and-average',2,'source_arithmetic',(52,61,568,117),[region(2,'For 2026, based','The Water and Sewer board')],'The source describes applying the EAF to the 2025 fee, rounding the result to zero decimals and comparing it to the 2025 fee, then says fees will decrease an average of -2.07%.','The exact decrease an average of -2.07% wording is retained. Individual printed percentages and Storm Drainage decimal values are not forced to agree with a recomputed formula.',['p2-prose'])
 obs('utility-separate-future-adoption',2,'scope_boundary',(52,120,568,161),[region(2,'The Water and Sewer board','The fee adjustment requires')],'The Water and Sewer board is described as establishing Water and Sewer Plant Investment Fees, followed by These will be adopted in December.','The statement is future-facing relative to the memo; no explicit December year is supplied. This three-page source supplies no water or sewer rates, and the statement does not prove later adoption.',['p2-prose'])
 obs('notification-effective-date',2,'date_role',(52,164,568,220),[region(2,'The fee adjustment requires','Fee Structure')],'The source describes public notification approximately 120 days before the March 1, 2026 effective date and refers to the attached fee schedule.','The approximate notification interval and stated effective date are source claims. No exact notice date, compliance finding or present applicability is inferred.',['p2-prose'])
 obs('fee-grid-units',2,'source_layout',(52,225,530,690),[table2.native_span],'All 23 page 2 fee rows are mapped to their visible group, use/size condition, printed unit and 2025/change/2026 columns. Residential conditions explicitly refer to heated living space.','No new unit is supplied for the merged residential cells. Commercial and impervious-area units remain separate. Blank group and spacer cells remain blank.',['p2-police-fire','p2-park-trails-storm'])
 obs('storm-decimals',2,'source_arithmetic',(52,654,530,691),[span(2,3598,3667)],'The Storm Drainage row prints Impervious Area, Per Impervious Square Foot, $0.315, -2.22%, and $0.308.','These printed three-decimal dollar values are retained despite the preceding general zero-decimal rounding description. This review does not resolve or repair that source-level tension.',['p2-park-trails-storm'])
 obs('transportation-column-major',3,'reading_order',(52,75,530,192),[table3.native_span],'All seven Transportation rows are mapped visually. The first six native rows are emitted by numeric column, making a plain sequential transcript misleading for row associations.','The complete original native bytes are preserved; the explicit grid is a reviewed layout mapping, not a replacement or corrected native extraction.',['p3-transportation'])
 obs('transportation-carried-headers',3,'scope_boundary',(52,75,530,192),[ls(3,97),ls(3,98)],'Page 3 begins with Transportation Development Fee and Unit. The three numeric column headings are not repeated; the table uses the continuing page 2 grid.','The header_reference_row_ids points to fees-column-header on page 2. No year text is invented as visible on page 3.',['p3-transportation'])
 obs('page-footnote-boundary',3,'source_layout',(0,0,612,792),[span(3,0,len(pdata[3]['b']))],'The third full page contains the repeated schedule title and the Transportation table, with blank space below. Across all three checked full pages, no visible footnotes or printed page-number labels were observed.','This statement is limited to these three retained pages and their renderings; it does not establish completeness of the larger fee framework or linked documents.',['p3-transportation'])
 review=Review(schema_version=1,reviewed_at=datetime.now(timezone.utc),source_id=SID,assignment_id='EB-PDF-016',status='three_page_candidate_aware_source_qa_complete_pending_parent_integration',legal_currentness='not_verified',review_mode='candidate_aware_not_blind',external_review_consulted=False,prior_exposure='Atlas prepared the packet and saw its original images, native candidate and prior intake provenance. This is candidate-aware source QA, not a blind independent transcription. No external Ebenezer EB016 report was consulted.',input_copies=copies,source=original,candidate=candidate,packet_manifest=packet,expected_pages=3,pages=pages,crops=crops,tables=tables,observations=observations,text_edits_applied=[],normalization_policy='Every original native UTF-8 byte is retained in its page file, in the exhaustive chunks and within the unchanged candidate. Table cell display text only folds whitespace between exact native spans. Words, punctuation, dollar values, percentages, grammar and units are not corrected. Cell and row rectangles are approximate PDF-point visual locators, not asserted exact ink bounds. Native reading order and visible grid order are separate.',no_arithmetic_recomputation=True,fee_row_count=30,footnotes_observed=[],provenance_limits=['The source and candidate are exact copies from the frozen EB015–017 packet. The canonical retained original was byte-equal at review time.','No network acquisition occurred in this review. The packet preserves upstream claims and actual repository intake separately; this review does not independently verify the original HTTP event.','The copied packet manifest contains other assignment references for context. Verification here intentionally checks only this source and its three images and native pages; other packet documents are outside scope.'],limits=['This is a three-page visual/native fidelity review, not an adopted-fee or current-law certification.','The source is a memorandum with schedules, not the independently checked adoption instrument. The quoted code and subsequent amendments were not opened.','No fee totals, recalculated percentages, independent economic checks or jurisdiction-wide completeness claims are produced.','Image-only logo words, non-visible native -A, table layout and native bullet encoding are disclosed separately from unchanged source wording.'])
 schema=Review.model_json_schema();payload=review.model_dump(mode='json');jsonschema.Draft202012Validator(schema).validate(payload)
 save(OUT/'SOURCE_QA.schema.json',(json.dumps(schema,indent=2,ensure_ascii=False)+'\n').encode())
 save(OUT/'SOURCE_QA.json',(json.dumps(payload,indent=2,ensure_ascii=False)+'\n').encode())
 return review

def verify(base):
 global OUT
 OUT=base.resolve()
 payload=json.loads((OUT/'SOURCE_QA.json').read_bytes());schema=json.loads((OUT/'SOURCE_QA.schema.json').read_bytes())
 jsonschema.Draft202012Validator(schema).validate(payload);review=Review.model_validate_json((OUT/'SOURCE_QA.json').read_bytes())
 if schema!=Review.model_json_schema():raise ValueError('Schema not current model')
 refs={}
 def gather(x):
  if isinstance(x,dict):
   if set(x)=={'path','sha256','size_bytes'}:refs[x['path']]=Ref(**x)
   for v in x.values():gather(v)
  elif isinstance(x,list):
   for v in x:gather(v)
 gather(payload)
 for rel,r in refs.items():
  p=OUT/rel
  if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(OUT):raise ValueError('Unsafe reference')
  b=p.read_bytes()
  if sha(b)!=r.sha256 or len(b)!=r.size_bytes:raise ValueError(f'File bytes {rel}')
 candidate=(OUT/review.candidate.path).read_bytes();pdf=pymupdf.open(OUT/review.source.path)
 if len(pdf)!=3:raise ValueError('PDF pages')
 manifest=json.loads((OUT/review.packet_manifest.path).read_bytes());doc=next(d for d in manifest['documents'] if d['source_id']==SID)
 if doc['original']['sha256']!=review.source.sha256 or doc['candidate']['sha256']!=review.candidate.sha256:raise ValueError('Manifest source/candidate')
 for p,m in zip(review.pages,doc['pages'],strict=True):
  b=p.native_text.encode();e=json.loads((OUT/p.evidence.path).read_bytes())
  if candidate[p.candidate_start_byte:p.candidate_end_byte_exclusive]!=b or (OUT/p.native_file.path).read_bytes()!=b:raise ValueError('Candidate/page bytes')
  if pdf[p.physical_page-1].get_text('text',sort=False,flags=195).encode()!=b:raise ValueError('Native reproducibility')
  if e['text'].encode()!=b or e['source_sha256']!=SOURCE_SHA or e['source_image_sha256']!=p.image.sha256:raise ValueError('Evidence source/page')
  for key,r in [('image',p.image),('evidence',p.evidence)]:
   if m[key]['sha256']!=r.sha256 or m[key]['size_bytes']!=r.size_bytes:raise ValueError('Manifest page binding')
  if m['candidate_text_offset_bytes']!=p.candidate_start_byte or m['candidate_text_end_byte_exclusive']!=p.candidate_end_byte_exclusive:raise ValueError('Manifest offsets')
  image=pymupdf.Pixmap(OUT/p.image.path)
  if image.width!=2550 or image.height!=3300:raise ValueError('Full image shape')
 for c in review.crops:
  pix=pdf[c.physical_page-1].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(c.pdf_rect_points),alpha=False)
  if pix.tobytes('png')!=(OUT/c.file.path).read_bytes():raise ValueError('Crop reproduction')
 return {'status':'passed','references_checked':len(refs),'physical_pages':3,'native_bytes':sum(len(p.native_text.encode()) for p in review.pages),'exhaustive_native_chunks':sum(len(p.chunks) for p in review.pages),'table_regions':len(review.tables),'fee_rows':review.fee_row_count,'table_rows_including_headers_spacers':sum(len(t.rows) for t in review.tables),'table_cells':sum(len(r.cells) for t in review.tables for r in t.rows),'observations':len(review.observations),'crop_rerenders':len(review.crops),'native_replay':'exact','currentness':'not_verified'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');ap.add_argument('--root',type=Path);args=ap.parse_args()
 if args.verify:print(json.dumps(verify(args.root or Path(__file__).resolve().parent),indent=2))
 else:
  build();print(json.dumps(verify(OUT),indent=2))
