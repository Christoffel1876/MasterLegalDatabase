from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from typing import Literal
import json,shutil,sys,re
import pymupdf
from pydantic import BaseModel,ConfigDict,Field
B=Path('/Users/mcoors/Documents/Project Geode');P=B/'handoffs/run-2026-09-13/atlas-eb025-source-qa';packet=B/'handoffs/run-2026-09-13/ebenezer-preparation';sid='el-paso-boh-ehs-fees-spanish-sd011'
model='''from pydantic import BaseModel,ConfigDict,Field,model_validator
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
'''
(P/'models.py').write_text(model);sys.path.insert(0,str(P));from models import Asset,Span,Page,Cell,Row,Passage,Link,Crop,Review
inputs=P/'inputs';inputs.mkdir(exist_ok=True)
def copy(src,dest):
 data=src.read_bytes();target=inputs/dest
 if target.exists():assert target.read_bytes()==data
 else:target.write_bytes(data)
 return target
def asset(path):
 data=path.read_bytes();return Asset(path=str(path.relative_to(P)),sha256=sha256(data).hexdigest(),size_bytes=len(data))
original=copy(packet/'01-source-only'/sid/'original.pdf','original.pdf');candidate=copy(packet/'02-candidate-text'/sid/'candidate.txt','candidate.txt')
assert sha256(original.read_bytes()).hexdigest()=='fd162c37442dc99097a272d9ebbf74fbfd063f2dc2f2226fdeb8b93a53849ec9'
for n in range(1,7):
 copy(packet/'01-source-only'/sid/f'page-{n:04}.png',f'page-{n:04}.png');copy(packet/'02-candidate-text'/sid/f'page-{n:04}.native.txt',f'page-{n:04}.native.txt')
texts={n:(inputs/f'page-{n:04}.native.txt').read_text() for n in range(1,7)}
def span(n,start,end):
 text=texts[n][start:end];return Span(page=n,start_byte=len(texts[n][:start].encode()),end_byte=len(texts[n][:end].encode()),text=text,sha256=sha256(text.encode()).hexdigest())
def literal(n,s,end=None,begin=0):
 i=texts[n].index(s,begin);j=texts[n].index(end,i) if end else i+len(s);return span(n,i,j)
def match_cell(n,value,cursor):
 if not value:return None,cursor
 pattern=r'\s*'.join(re.escape(x) for x in value if not x.isspace());m=re.search(pattern,texts[n][cursor:]);assert m,(n,value,cursor)
 i=cursor+m.start();j=cursor+m.end();return span(n,i,j),j
rows=[];category=None
with pymupdf.open(original) as doc:
 assert len(doc)==6
 for n in range(1,7):assert doc[n-1].get_text('text',flags=195,sort=False)==texts[n]
 for n in [2,3,4]:
  cursor=0
  for tnum,tab in enumerate(doc[n-1].find_tables().tables,1):
   extracted=tab.extract()
   for rnum,(values,geometry) in enumerate(zip(extracted,tab.rows),1):
    rid=f'p{n}-t{tnum}-r{rnum:02}'
    role='fee'
    if n==2 and rnum==1:role='title'
    elif n==2 and rnum==2:role='column_headers'
    elif values[1] is None:role='category'
    elif n==4 and tnum==1 and rnum==1:role='continuation'
    if role=='category':category=rid
    cells=[]
    for col,(value,box) in enumerate(zip(values,geometry.cells),1):
     ref,cursor=match_cell(n,value,cursor)
     cells.append(Cell(column=col,span_columns=2 if col==1 and values[1] is None else 1,bbox=list(box) if box else None,representation='merged_into_left' if value is None else 'visibly_blank' if value=='' else 'visible_text_native_whitespace_preserved_separately',text=value,native_span=ref))
    rows.append(Row(row_id=rid,physical_page=n,physical_table=tnum,physical_row=rnum,role=role,category_source_row=category if role in ['fee','continuation'] else None,cells=cells))
passages=[]
def add(id,role,sp,note):passages.append(Passage(id=id,role=role,span=sp,visual_note=note))
add('cover','cover_and_agency',literal(1,'REGULACIONES','Aprobado'),'All substantive cover and contact lines directly read; visible agency word is Publica without an accent. Underlines are graphic formatting, not added text.')
add('chapter-and-section-a','governing_section_context',literal(2,'CAPÍTULO 3','2024 TARIFAS PROGRAMADAS'),'Image shows A. A partir as a continuous clause; native splits A p / artir. Preserve byte fragment but do not treat the split as a source misspelling. Stated 1 de enero de 2024 remains a source claim, not independently verified currentness.')
add('asterisk-note','table_footnote',literal(4,'* Incluye una reinspección.'),'Asterisk refers to OWTS Permiso nuevo*.')
add('section-b','penalty_exception_context',literal(4,'B.  La falta','Definiciones'),'Entire paragraph includes salvo que se disponga lo contrario en la Sección 2, no más de $100 por día and until fully paid. No applicability or arithmetic determination.')
add('definitions-headings','definitions_heading',literal(4,'Definiciones','(1) Una'),'Heading scope retained.')
for n in range(1,5):
 start=f'({n}) '+{1:'Una evaluación',2:'Una inspección',3:'Un documento',4:'Un proceso'}[n]
 end=f'({n+1}) ' if n<4 else 'Sistemas de tratamiento'
 add(f'definition-{n}','rfe_definition',literal(4,start,end),'Native wording and punctuation preserved; definition4 has a period after control before para mantener, also visible in source.')
add('owts-definitions-heading','definitions_heading',literal(4,'Sistemas de tratamiento','(5) Reparación'),'Separate OWTS heading.')
add('definition-5','owts_definition',literal(4,'(5) Reparación','(6) Reparación'),'Complete major-repair definition.')
add('definition-6','owts_definition',literal(4,'(6) Reparación','Aprobado'),'Includes the exception for deflectores del tanque y líneas colapsadas; no shortened paraphrase substitutes for it.')
add('definition-7','owts_definition',literal(5,'(7) Reinspección','Cuido de niños:'),'Continues the numbered definitions on the following physical page; preserves dangling closing quotation mark and all qualifying text.')
add('childcare-definitions','childcare_definitions',literal(5,'Cuido de niños:','Aprobado'),'Image crop confirms Cuido de niños (not Cuidado); all four inspection descriptions read including cada dos años, a solicitud and a discreción terms.')
add('other-notes','general_fee_notes',literal(6,'Otras notas:','Aprobado'),'All three notes preserved: per-visit basis; no charges for complaint/communicable-disease investigation visits; collection/payment language.')
for n in range(1,7):add(f'footer-{n}','partially_obscured_footer',literal(n,'Aprobado',None),'Native includes the complete first footer line. A separate following native d /2023 exists but rendered line is mostly obscured; no fully readable year or reconstructed de2023 is certified from pixels.')
for n in range(1,7):add(f'footer-tail-{n}','native_text_without_complete_visual_support',literal(n,'d\n2023'),'Exact native characters preserved as extraction evidence; source pixels expose only partial upper marks. Do not treat as a fully read date or silently delete from native.')
links=[Link(id='license-page-continuation',source_rows=['p3-t2-r30','p4-t1-r01'],target_passages=[],kind='continuation',note='Page3 service Licencia de establecimiento minorista continues with de alimentos on page4. The page4 fee cell is blank; the Per Section25-4-1607 C.R.S. value remains on page3. No second license fee invented.'),Link(id='owts-category-continuation',source_rows=['p2-t1-r25','p2-t1-r26']+[r.row_id for r in rows if r.physical_page==3 and r.category_source_row=='p2-t1-r25'],target_passages=[],kind='continuation',note='The OWTS category starts onpage2 and continues through the nextpage/table fragment without repeating its header. Preserve separate physical regions.'),Link(id='governing-context',source_rows=[r.row_id for r in rows if r.role=='fee'],target_passages=['chapter-and-section-a','section-b','other-notes'],kind='section_context',note='Full source context travels with extracted fee rows; no applicability decision.')]
for marker,ids,definition in [('*',['p2-t1-r26'],'asterisk-note'),('(1)',['p3-t2-r25'],'definition-1'),('(2)',['p3-t2-r26','p3-t2-r27'],'definition-2'),('(3)',['p4-t1-r04'],'definition-3'),('(4)',['p4-t1-r05'],'definition-4'),('(5)',['p3-t1-r02'],'definition-5'),('(6)',['p3-t1-r03'],'definition-6'),('(7)',['p3-t2-r05'],'definition-7')]:links.append(Link(id='footnote-'+definition,source_rows=ids,target_passages=[definition],kind='footnote',note='Printed marker '+marker+' is retained with its source-defined explanation.'))
crops=[]
for c in json.loads((P/'CROP_PREPARATION.json').read_text()):crops.append(Crop(asset=asset(P/c['path']),source_page=c['physical_page'],source_sha256=c['source_sha256'],box_pixels=c['box_pixels'],method=c['method']))
review=Review(prepared_at=datetime.now(timezone.utc).isoformat(),source=asset(original),candidate=asset(candidate),pages=[Page(page=n,png=asset(inputs/f'page-{n:04}.png'),native=asset(inputs/f'page-{n:04}.native.txt'),text=texts[n],limits='Full page and footer crop directly inspected; footer-tail clipping is separately qualified. Exact glyph code points and all graphic details are not visually certified.') for n in range(1,7)],rows=rows,passages=passages,links=links,crops=crops,native_bytes=sum(len(x.encode()) for x in texts.values()),candidate_bytes=candidate.stat().st_size,full_pages_directly_viewed=list(range(1,7)),method='Atlas direct image review of all six complete Poppler source PNGs at displayed1376x1780 (original2550x3300), followed by exact source-pixel crops and candidate-aware native/table comparison. No Ebenezer report, English version or prior source correction consulted. Table boundaries came from PyMuPDF detection and were checked against complete source images; every65fee-row service/value association was read. Native text, line breaks and Unicode are immutable, with visually qualified derivative mappings.',observations=[
'Five physical table fragments contain75physicalrows and65fee rows, including the statutory-reference row. Merged title/category cells and one visibly blank continuation fee cell remain explicit.',
'All visible schedule amounts and bases agree with native text; table association and heading/footnote context must accompany values. No fee arithmetic performed.',
'Source mixes Spanish with in2024, in2025, per hour, Per Section, 1 Event and for Multiple Events. These are not translated or repaired.',
'OWTS first-property row has $211.50 in2024 ($368 in2025), while Additional OWTS prints $281.00 in2024 only. No additional2025value is supplied.',
'Native A p /artir split does not reflect the visually continuous A partir clause. Source p5 heading is Cuido de niños, while p2 category is Cuidado de los Niños. Cover agency text is Publica without accent; other paragraphs print Pública.',
'All six footer first lines are present in inspected source crops. Native tails d/newline2023 survive behind visible clipping; do not infer a fully legible approval year from these bytes. Source prefix25deoctubre and body1deenerode2024 remain different date claims.',
'Footnote(7) begins onpage5; RFElicense service continues acrosspages3/4. No missing paragraph is reconstructed from another language or edition.'
],limitations=['This is Spanish source fidelity only, not translation equivalence or assessment of legal authority of a translation.','The received source and historical acquisition metadata remain separate from current official retrieval; no public request made.','All source/candidate bytes unchanged. Leading native blank lines, soft hyphens and footer tails remain present; derivative display text does not certify Unicode typography.','No currentness/adoption/application conclusion. Rendered footer tail is partially obscured; a complete year is not visually certified.','No external review chronology or tool internals authenticated. This is not a blind transcription.'])
(P/'SOURCE_QA.json').write_text(review.model_dump_json(indent=2)+'\n');(P/'SOURCE_QA.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n');(P/'build_source_qa.py').write_bytes(Path(__file__).read_bytes())
print('DRAFT',review.native_bytes,'native bytes',len(rows),'table rows',sum(r.role=='fee' for r in rows),'fee rows',len(passages),'passages',len(crops),'crops')
