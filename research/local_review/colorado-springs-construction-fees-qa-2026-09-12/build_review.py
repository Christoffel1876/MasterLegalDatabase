from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from collections import Counter
import json,math,shutil,pymupdf
from review_models import *
from row_map import *
r=Path(__file__).resolve().parent

def asset(path):
 p=r/path;return Asset(path=path,sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size)
def save(path,model):
 p=r/path
 if p.exists():
  pre=r/'preparation-preimages'/sha256(p.read_bytes()).hexdigest();pre.mkdir(parents=True,exist_ok=True)
  if not (pre/p.name).exists():shutil.copyfile(p,pre/p.name)
 p.write_text(model.model_dump_json(indent=2)+'\n')
def pixel(b):return [math.floor(b[0]*200/72),math.floor(b[1]*200/72),math.ceil(b[2]*200/72),math.ceil(b[3]*200/72)]
geom={p:Geometry.model_validate_json((r/f'native/page-{p:04}.geometry.json').read_text()) for p in range(1,8)}
used=Counter()
def part(p,nums):
 ls=[geom[p].lines[i-1] for i in nums]
 for l in ls:used[l.line_id]+=1
 return dict(line_ids=[l.line_id for l in ls],exact_native_text=''.join(l.text for l in ls),native_ranges=[[l.start,l.end] for l in ls],pdf_bboxes=[l.bbox for l in ls],pixel_bboxes=[pixel(l.bbox) for l in ls])
rows=[];counts=Counter()
for p,t,left,right in ROWS:
 counts[p,t]+=1;rid=f'P{p}-{t.upper()}-{counts[p,t]:02}'
 notes,defs=linked_context(p,t,left)
 rows.append(FeeRow(row_id=rid,table_id=t,physical_page=p,label=Cell(role='label',**part(p,left)),fee_as_printed=Cell(role='fee_as_printed',**part(p,right)),global_context_ids=GLOBAL,table_context_ids=notes,definition_ids=defs,context_rule='Return the complete global context, linked table notes and definitions with this source row; conditions remain source wording, not an applicability decision.'))
blocks=[]
for bid,(kind,parts) in CONTEXT.items():
 notes=[]
 if bid=='CONTENTS':notes=['The printed contents says Definitions/Explanations Page 5; the actual heading is physical page 6. Preserve both.']
 if bid=='DEF-REINSPECTION':notes=['One definition continues from physical page 6 onto page 7. Both parts must travel together.']
 if bid=='PRINTED-EFFECTIVE-DATE':notes=['Printed effective-date claim only; neither adoption nor current applicability has been independently verified.']
 blocks.append(Block(block_id=bid,kind=kind,parts=[BlockPart(page=p,**part(p,list(range(a,b+1)))) for p,a,b in parts],notes=notes))
for t,(p,l) in TABLES.items():blocks.append(Block(block_id=f'HEADING-{t.upper()}',kind='heading',parts=[BlockPart(page=p,**part(p,[l]))],notes=[]))
for p,g in geom.items():
 for i,l in enumerate(g.lines,1):
  if not used[l.line_id]:
   kind='native_whitespace' if not l.text.strip() else 'footer'
   assert kind=='native_whitespace' or l.text.strip()==str(p),(p,l)
   blocks.append(Block(block_id=f'UNASSIGNED-{l.line_id}',kind=kind,parts=[BlockPart(page=p,**part(p,[i]))],notes=['Native whitespace has no additional visible fee wording.'] if kind=='native_whitespace' else []))
assert set(used.values())=={1};assert sum(used.values())==sum(len(g.lines) for g in geom.values())
plan=r.parent/'sd014-fire-fee-pdfs/plan.json'
shutil.copyfile(plan,r/'custody/plan.json')
pages=[]
for p,g in geom.items():
 im=pymupdf.Pixmap(str(r/f'images/page-{p}.png'))
 pages.append(Page(physical_page=p,source_rect_points=[0.,0.,612.,792.],image=asset(f'images/page-{p}.png'),image_dimensions=[im.width,im.height],native=asset(f'native/page-{p:04}.txt'),geometry=asset(f'native/page-{p:04}.geometry.json'),native_line_count=len(g.lines),direct_full_image_viewed=True))
qa=QA(schema_version='1.0',source_id='SD014-02',authority_id='CO-MUNICIPAL-COLORADO_SPRINGS',issuer='Colorado Springs Fire Department, Division of the Fire Marshal',collector_qualification='The City fire department issues this schedule. The complete Construction Plan Check Fee definition identifies Pikes Peak Regional Building Department (PPRBD) as the collector through its plan portal; this does not reassign the issuing authority. Accela submission is separately described for the fire-system plan-check fee.',source=asset('source/original.pdf'),source_sha256='e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a',page_count=7,source_status='fee_schedule_as_received',legal_currentness='not_verified',adoption_verification='not_verified',effective_date_verification='printed_claim_only',printed_effective_date='07/01/2026',review_method='Atlas source-first direct image QA followed by native comparison; title and role known, not blind',reviewed_at=datetime.now(timezone.utc).isoformat(),source_first_observations=asset('VISUAL_OBSERVATIONS.json'),source_first_observations_sha256='e382da7c1be63d5b7b26be5f0d43d35b1fe55a4486346377fe8895cfbfdbbc97',provenance=Provenance(method='Atlas direct ordinary HTTPS GET retained complete response',request_started_at='2026-09-12T23:10:46.676197Z',response_finished_at='2026-09-12T23:10:47.380038Z',official_url='https://coloradosprings.gov/system/files/2026-07/2026%20Fee%20Schedule%20Construction%20Services.pdf',http_status=200,redirect_count=0,event=2,receipts=[asset(f'custody/{n}') for n in ['reservation.json','result.json','public-headers.json','body.bin','plan.json']],header_dates_are_legal_dates=False),native_engine='PyMuPDF 1.28.2 get_text(text, sort=False); UTF-8 unchanged per physical page',native_byte_basis='Zero-based half-open UTF-8 offsets in the named unchanged physical-page native file; PDF bboxes in points, crop bboxes in 200 dpi original-image pixels.',native_byte_count=sum(g.size_bytes for g in geom.values()),pages=pages,tables=[Table(table_id=t,heading_block_id=f'HEADING-{t.upper()}',page_order=sorted({x.physical_page for x in rows if x.table_id==t}),row_ids=[x.row_id for x in rows if x.table_id==t],column_roles='Unlabeled left description and right fee columns; roles are visual associations, not invented printed column headings.') for t in TABLES],fee_rows=rows,blocks=blocks,all_native_lines_assigned_once=True,all_context_must_accompany_fee_rows=True,comparison_findings=[
 'All seven full Poppler page images were directly inspected before extracting native text. All 128 fee rows were then compared against unchanged native label/fee cells. Eleven targeted crops were inspected; an additional corrected A-4 crop replaces no prior crop.',
 'No material native word, fee-value or row-association correction was needed. Native whitespace and line breaks remain exact; normalized text in the Markdown is a reading view only.',
 'Every native line, including printed footer numbers and non-visible whitespace runs, is assigned once. The two cover logos remain graphical image evidence; no extra text has been inferred from them.',
 'Native linear order places footer numbers near the start of each page and alternates description/fee cells. The structured grid preserves separate columns and full multiline labels, amounts and definitions.',
 'All source-context records remain available. Every fee row requires the complete global plan-review note, implementation statement, other-schedule reference and all-permit technology row. Related table notes and definitions are linked as source context, without declaring their legal applicability.'
],source_anomalies=[
 'Contents directs Definitions/Explanations to Page 5; the heading and definitions start on physical page 6.',
 'Construction continues from page 2 through all of page 3 and the first two rows of page 4. Miscellaneous permits continue from page 4 to page 5. Re-Inspection continues from page 6 to page 7.',
 'High-rise and performance-based rows print 0.04/sq. ft. without a dollar sign. The performance-based description and definition independently retain the $2,000 minimum; no currency symbol or arithmetic is supplied.',
 'The additional-100 sprinkler-head row prints $336.00, whereas several other sprinkler rows print $344.00. Values remain unchanged.',
 'Source preserves R2 without a hyphen for the additional 50 dwelling/sleeping-unit row, sq. Ft capitalization in the final storage row, a space in 50, 000 in the A-4 tier, and the plans is marked grammar in Limited Review.',
 'The descriptions retain 50,000 + / 10,001 + and other original tier boundaries, even where adjacent intervals appear unusual. No boundary, arithmetic, classification or label repair is made.',
 'No numbered footnote markers are present. Three complete in-table NOTE paragraphs and thirteen complete definition records supply conditions and exceptions. Rate expressions 1.5x Review Fee, 2x Permit Fee and IRS Standard Mileage Rate remain text.'
],limits=[
 'This is a source extraction and visual association review of one seven-page municipal schedule, not a legal-currentness, adoption or authority-of-enactment determination.',
 'Effective 07/01/2026 is a printed source claim. HTTP retrieval time and Last-Modified/Date headers are custody or server metadata, not independently verified legal effective dates.',
 'The PPRBD collection clause does not establish that PPRBD issued the municipal schedule or that this package covers all regional building fees.',
 'No fee calculation, outside IRS lookup, applicability determination, cross-document supersession or Code Services schedule review occurred in this package.',
 'Global/context links preserve all conditions for a future source-only reader; they do not silently assert that every linked condition applies to every row.',
 'External review is not represented. The method is Atlas source-first direct-image review followed by native comparison, with prior title/role knowledge; it is not a fully blind independent transcription.'
])
save('SOURCE_QA.json',qa)
(r/'SOURCE_QA.schema.json').write_text(json.dumps(QA.model_json_schema(),indent=2)+'\n')
for cls,name in [(Geometry,'NATIVE_GEOMETRY'),(Crop,'CROP')]: (r/f'{name}.schema.json').write_text(json.dumps(cls.model_json_schema(),indent=2)+'\n')
print('fee rows',len(rows),'native bytes',qa.native_byte_count,'lines',sum(len(g.lines) for g in geom.values()),'blocks',len(blocks),'tables',[(t.table_id,len(t.row_ids)) for t in qa.tables])
