from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-fees-source-qa')
sys.path.insert(0,str(B))
from review_models import Asset, Span, Block, Fee, Page, Review, DateStatement
sha=lambda b:hashlib.sha256(b).hexdigest()
def asset(p):
 b=(B/p).read_bytes();return Asset(path=p,sha256=sha(b),size_bytes=len(b))
def write(p,b):
 with (B/p).open('xb') as f:f.write(b)
def span(b,s=0):return Span(start=s,end=s+len(b),sha256=sha(b))
rows=[]
def add(i,p,k,box,t,*notes):rows.append((i,p,k,box,t,list(notes)))
P='printed_text';H='handwriting_annotation';G='graphic_annotation'
add('P1-HEADER',1,P,(330,180,2230,520),'BOARD OF COUNTY COMMISSIONERS\nOF THE COUNTY OF GUNNISON, COLORADO\nRESOLUTION NO: 25-24\nA RESOLUTION ESTABLISHING A SCHEDULE OF BUILDING PERMIT FEES','The final 24 is handwritten. Line layout retained only at headings; font styling is represented by the image.')
add('P1-R1',1,P,(320,540,2260,730),'WHEREAS, pursuant to the International Building Code and the International Residential Code the Board is authorized to set and amend the Community Development Department’s fees for building permits; and')
add('P1-R2',1,P,(320,750,2260,1220),'WHEREAS, Community Development staff has provided the Board of County Commissioners an analysis of the current fee schedule, Appendix AL, that identified a regressive fee percentage per increased project valuation and recommended the establishment of a flat percentage of the total project valuation to ensure that building permit fees are equitable for all project valuation amounts and cover the cost of application review and building inspections and recommended and increase of application deposits collected at the time of submittal in memos dated March 14, 2025 and May 22, 2025, both titled “Building Permit Fees”; and','Literal source wording “recommended and increase of” retained.')
add('P1-R3',1,P,(320,1250,2260,1440),'WHEREAS, Community Development staff experiences an increase in demand for review and inspection resources for larger valuation projects that is not recovered by use of the Appendix AL Permit Fee schedule; and')
add('P1-R4',1,P,(320,1470,2260,1730),'WHEREAS, the Board wishes to establish a schedule of permit fees in accordance with the International Building Code and the International Residential Code that can be adjusted from time to time to cover the cost of the development review and inspection program and that is clear and accessible to the citizens of Gunnison County.')
add('P1-ADOPTION',1,P,(320,1750,2260,1940),'NOW, THEREFORE, BE IT RESOLVED by the Board of County Commissioners of Gunnison County, Colorado that the Community Development Department Building Permit Fee Schedule is hereby adopted and attached as Exhibit A hereto.')
add('P1-CONDITION',1,P,(320,1970,2260,2150),'THIS RESOLUTION AND THE APPROVAL GRANTED HEREBY SHALL NOT BE EFFECTIVE UNLESS AND UNTIL A COPY IS RECORDED IN THE Office of the Clerk and Recorder of Gunnison County.')
add('P1-EXECUTION',1,P,(300,2210,2260,2370),'INTRODUCED by Commissioner Houck, seconded by Commissioner Puckett Daniels, and adopted on this 17th day of June, 2025.','Houck, Puckett Daniels, 17th and June are visually read handwritten insertions; identity and execution authenticity are not certified. The superscript th is represented as ordinary characters; blank-line lengths are not reproduced.')
add('P1-SIGN-LABEL',1,P,(320,2450,2260,2750),'BOARD OF COUNTY COMMISSIONERS\nOF GUNNISON COUNTY, COLORADO\nLaura Puckett-Daniels, Chairperson')
add('P1-SIGN',1,G,(320,2570,2250,2740),'A handwritten signature mark is visible above and overlapping the printed Laura Puckett-Daniels label.','This is a graphic observation, not a transcription or authenticated signer identity.')
add('P1-NUM',1,P,(1190,2870,1330,2950),'1')
add('P1-STAMP',1,P,(820,2940,2200,3250),'Gunnison County, CO\n6/18/2025 10:46:06 AM\n447\n702424\nPage 1 of 3\nR 0.00 D [fee:doc]','Two-column stamp ordered left column then right column; barcode preserved in image, not decoded.')
add('P2-LABEL1',2,P,(320,170,2260,330),'Jonathan Houck, Commissioner')
add('P2-SIGN',2,G,(330,30,2230,350),'A handwritten signature mark is visible above and overlapping the printed Jonathan Houck label.','No authenticated signer identity.')
add('P2-ABSENT',2,H,(380,320,920,440),'(Absent)','Handwritten annotation above the Elizabeth Smith signature line.')
add('P2-LABEL2',2,P,(320,390,2260,510),'Elizabeth Smith, Commissioner')
add('P2-ATTEST',2,P,(320,570,2230,1020),'ATTEST:\nGunnison County Clerk','A handwritten line crosses the printed word Gunnison. Printed wording remains transcribed; no substitution inferred.')
add('P2-HAND',2,H,(330,760,1050,1100),'Holly\nDeputy','Apparent handwriting reading only; no surname, office authority or identity authentication inferred.')
add('P2-SEAL',2,G,(920,610,1460,1200),'Circular seal visibly contains GUNNISON COUNTY, SEAL and COLORADO.','Seal graphics and dots retained as pixels; no authenticity claim.')
add('P2-STAMP',2,P,(850,1230,2270,1470),'Gunnison County, CO\n6/18/2025 10:46:06 AM\n447\n702424\nPage 2 of 3\nR 0.00 D [fee:doc]','Two-column stamp ordered left then right; barcode not decoded.')
add('P2-NUM',2,P,(1180,2850,1350,3010),'2','Most of this physical page is blank; all visible text regions are represented.')
add('P3-HEADER',3,P,(320,180,2320,360),'ATTACHMENT A\nGunnison County Building Permit Fees','The source uses ATTACHMENT A here and Exhibit A on page 1.')
add('P3-GENERAL',3,P,(320,395,2280,470),'0.9% flat fee (based on valuation; includes plan review).')
add('P3-MIN',3,P,(480,470,2280,540),'• A minimum fee of $300 is applied to all permits.','This bullet is visually under the 0.9% paragraph. Its wording is preserved without reconciling it with the separate mechanical minimum.')
add('P3-DEPOSIT',3,P,(480,540,2340,990),'• A non-refundable application deposit of $1,000 for new residential and commercial structures and $200 for all other types including utility and accessory structures, repairs, alterations and additions to existing structures is due at the time of application submittal and is to be applied to the building permit fee at the time of issuance. The application deposit will be forfeited if the permit is not issued.')
add('P3-MODEL',3,P,(320,1040,2280,1190),'0.7% flat fee (based on valuation, includes plan review) for permits that utilize model home plans provided by Gunnison County.')
add('P3-REVIEW',3,P,(320,1250,2360,1590),'Additional plan review required by changes or revisions to the plans shall be charged a fee of $150.00 and review time beyond two hours shall be assessed at a rate of $100.00 per hour. If an independent plan review is required by the Building Official, the actual cost of such review along with administrative costs assessed at a rate of $75.00 per hour will be charged.')
add('P3-VALUATION',3,P,(320,1640,2360,2310),'Project valuations shall reflect the total value of work, including labor and materials, for which the permit is being issued. For residential structures greater than 5,000 square feet it is the applicant’s responsibility to provide the project valuation according to Section R108 of the International Residential Code and Section 109 of the International Building Code. For structures less than 5,000 square feet the applicant may provide the project valuation or project valuations may be established according to the Building Valuation Data schedule as set forth in the most recent issue, at the time of the issuance of the building permit, or the Building Safety Journal, published by the International Code Council with a regional multiplier of 2.8.','Literal “or the Building Safety Journal” retained. Greater than and less than are not replaced by inclusive thresholds; exactly 5,000 is not supplied.')
add('P3-MECH-HEADER',3,P,(320,2330,2280,2430),'Mechanical only permits (includes solid-fuel burning devices)')
add('P3-MECH',3,P,(320,2460,2280,2550),'0.75% flat fee (based on project valuation)')
add('P3-MECH-MIN',3,P,(480,2540,2340,2630),'• A minimum fee of $55.00 is applied to all mechanical permits.')
add('P3-MECH-REVIEW',3,P,(480,2620,2360,2770),'• Plan review fee, if plan review is needed, is 65% of the total mechanical permit fee.')
add('P3-NUM',3,P,(1200,2870,1350,2970),'3')
add('P3-STAMP',3,P,(930,2940,2480,3250),'Gunnison County, CO\n6/18/2025 10:46:06 AM\n447\n702424\nPage 3 of 3\nR 0.00 D [fee:doc]','Two-column stamp ordered left then right; barcode not decoded.')
(B/'reviewed').mkdir()
blocks=[];pages=[]
for n in range(1,4):
 selected=[x for x in rows if x[1]==n]; b=b''.join((x[4]+'\n').encode() for x in selected)
 name=f'reviewed/page-{n:04}.txt';write(name,b); pos=0
 for i,p,k,box,t,notes in selected:
  data=(t+'\n').encode();blocks.append(Block(id=i,page=p,kind=k,image=asset(f'pages/page-{p:04}.png'),region_xyxy=box,text=t,transcript=asset(name),transcript_span=span(data,pos),notes=notes));pos+=len(data)
 o=json.loads((B/f'ocr-escalated/page-{n:04}.json').read_bytes());s=[];pos=0
 for line in o['lines']:
  data=(line['text']+'\n').encode();s.append(span(data,pos));pos+=len(data)
 pages.append(Page(number=n,image=asset(f'pages/page-{n:04}.png'),native=asset(f'native/page-{n:04}.txt'),native_spans=[],native_status='empty_image_only',ocr_json=asset(f'ocr-escalated/page-{n:04}.json'),ocr_text=asset(f'ocr-escalated/page-{n:04}.txt'),ocr_observation_spans=s,reviewed_transcript=asset(name),width=2550,height=3300))
byid={x.id:x for x in blocks};fees=[]
for bid,amount,label,sub,extra in [
 ('P3-GENERAL','0.9%','flat fee','general',[]),
 ('P3-MIN','$300','minimum fee','general',['P3-GENERAL']),
 ('P3-DEPOSIT','$1,000','new residential and commercial structures','general',['P3-GENERAL']),
 ('P3-DEPOSIT','$200','all other types','general',['P3-GENERAL']),
 ('P3-MODEL','0.7%','model home plans provided by Gunnison County','model home',[]),
 ('P3-REVIEW','$150.00','Additional plan review required by changes or revisions','additional review',[]),
 ('P3-REVIEW','$100.00','review time beyond two hours','additional review',[]),
 ('P3-REVIEW','actual cost','independent plan review','independent review',[]),
 ('P3-REVIEW','$75.00','administrative costs','independent review',[]),
 ('P3-MECH','0.75%','flat fee','mechanical',['P3-MECH-HEADER']),
 ('P3-MECH-MIN','$55.00','minimum fee','mechanical',['P3-MECH-HEADER','P3-MECH']),
 ('P3-MECH-REVIEW','65%','Plan review fee','mechanical',['P3-MECH-HEADER','P3-MECH'])]:
 t=byid[bid].text.encode();amt=amount.encode();start=t.index(amt)
 fees.append(Fee(id=f'F{len(fees)+1:02}',block_id=bid,amount_literal=amount,amount_in_block=span(amt,start),label_literal=label,conditions_block_ids=[bid,*extra,'P3-VALUATION','P1-CONDITION'],subsection=sub,notes=['Full clause is authoritative for source transcription; this component is a reviewer decomposition, not a separate printed table row or fee calculation.']))
r=Review(schema_version=1,source_id='gunnison-building-fees-resolution-2025-24-sh-ext-003',authority_id='CO-COUNTY-GUNNISON',layer='08_County_Authorities',source=asset('inputs/original.pdf'),source_role='County building permit fee resolution with attached prose and bullet fee schedule',status='complete_visible_source_fidelity_review_qualified_handwriting',legal_currentness='not_verified',answer_safe=False,reviewed_at=datetime.now(timezone.utc).isoformat(),method='Candidate-aware Atlas review. All three fresh 300 dpi Poppler full pages were inspected before fresh native extraction and OCR. Prior recommendation first-page role checks were known. No external transcription or other edition was consulted. Six targeted crops inspected after full pages. Native extraction flags=195, sort=False yielded zero bytes on every page. Apple Vision raw outputs remain unchanged; visual transcript normalizes whitespace and uses Unicode typographic punctuation without certifying original code points. Printed text, handwriting and graphic annotations are explicitly separated.',official_acquisition_at_verified=None,supplied_requested_url=json.loads((B/'inputs/reservation.json').read_bytes())['requested_url'],supplied_acquisition_interval=('2026-09-13T02:18:53.906067Z','2026-09-13T02:18:54.606000Z'),supplied_time_status='reported_not_independently_verified',source_bytes_intake_status_at_review='received_package_canonical_intake_not_asserted',pages=pages,blocks=blocks,fees=fees,dates=[DateStatement(literal='March 14, 2025',role='Referenced staff memo date',block_ids=['P1-R2'],qualification='Referenced memo not part of this review.'),DateStatement(literal='May 22, 2025',role='Referenced staff memo date',block_ids=['P1-R2'],qualification='Referenced memo not part of this review.'),DateStatement(literal='17th day of June, 2025',role='Source-stated adoption date with handwritten day and month',block_ids=['P1-EXECUTION'],qualification='Visual reading, not authenticated execution or current applicability.'),DateStatement(literal='6/18/2025 10:46:06 AM',role='Visible recorder stamp time',block_ids=['P1-STAMP','P2-STAMP','P3-STAMP'],qualification='No timezone stated. Image of stamp is not independent recorder-system verification; conditional effectiveness is not converted into an asserted effective date.')],limitations=['Only this three-page received PDF was reviewed; no current-law, subsequent-amendment, supersession or cross-version check.','Original acquisition time and HTTP event history are supplied claims; exact retained bytes and local rendering/OCR timings are independently hash-bound.','Signatures, seal and handwritten insertions are visual observations only; no identity, authenticity or wet-execution certification.','No native text exists to bind substantive source-native offsets. All native spans are empty. Reviewed transcript offsets and OCR observation offsets are distinct derived evidence.','Page 3 is a prose and bullet schedule. Twelve fee components are a review decomposition, not twelve physical table rows or twelve legal obligations.','Source says Exhibit A on page 1 and ATTACHMENT A on page 3. This anomaly is retained.','All minimum/deposit/model-plan/mechanical clauses retain source hierarchy. No inferred reconciliation of the general all-permits minimum with the mechanical subsection.','The valuation text addresses residential structures greater than 5,000 and structures less than 5,000 square feet. Exactly 5,000 and missing qualifiers are not filled in.','No fee arithmetic or combined total is produced. Percent bases, per-hour units, non-refundable deposit, forfeiture and plan-review conditions remain attached.','Barcodes, signature curves, seal ornamentation, exact underlining, fonts and source code points are not transcribed as textual evidence. Original pixels remain available.'],findings=['All visible printed prose, headings, four fee bullets, signature labels, handwritten textual insertions, three page numbers and recorder stamp fields are represented.','OCR agrees with the twelve numeric/actual-cost fee components; major OCR errors concern execution handwriting, signature artifacts, seal and recorder marks. The untouched OCR is not promoted as reviewed text.','OCR page 3 loses or changes the two mechanical bullet markers and lowercases Council; source visual transcript restores those visible features.','The page 1 wording recommended and increase of and page 3 wording or the Building Safety Journal are source anomalies retained, not OCR corrections.','The page 2 word Gunnison has a visible crossing mark; its printed label remains preserved and the handwritten Deputy is recorded separately.'],custody=[asset('inputs/'+p.name) for p in sorted((B/'inputs').iterdir())])
data=(r.model_dump_json(indent=2)+'\n').encode();Review.model_validate_json(data);write('SOURCE_QA.json',data);write('SOURCE_QA.schema.json',(json.dumps(Review.model_json_schema(),indent=2)+'\n').encode())
md=['---','status: complete_visible_source_fidelity_review_qualified_handwriting','legal_currentness: not_verified','---','# Gunnison Resolution 25-24 source review','',r.method,'','## Reviewed visible text','']
for block in blocks:md.extend([f'### {block.id} — physical page {block.page} ({block.kind})','',block.text,'',*['Note: '+x+'\n' for x in block.notes]])
md.extend(['## Limits','',*['- '+x for x in r.limitations]])
write('REVIEWED_TRANSCRIPT.md',('\n'.join(md)+'\n').encode())
print(len(blocks),'blocks',len(fees),'fee components')
