"""One-time assembly of Atlas's manually reviewed transcript and source relationships."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json,re,shutil
from review_models import Asset,Span,Block,Mark,Page,Table,Link,DateClaim,Review
B=Path(__file__).resolve().parent
def asset(p):
    p=Path(p);raw=p.read_bytes();return Asset(path=p.relative_to(B).as_posix(),sha256=sha256(raw).hexdigest(),size_bytes=len(raw))
raw=(B/'TRANSCRIPT.md').read_bytes();text=raw.decode()
def span(a,b):
    x=raw[a:b];return Span(start=a,end=b,text=x.decode(),sha256=sha256(x).hexdigest())
matches=list(re.finditer(rb'^# Physical page ([1-7])\n',raw,re.M));assert len(matches)==7
blocks=[];pages=[];marks=[]
for index,m in enumerate(matches):
    n=int(m[1]);start=m.end();end=matches[index+1].start() if index<6 else len(raw)
    page=Page(number=n,image=asset(B/f'source/page-{n:04}.png'),native=asset(B/f'native/page-{n:04}.txt'),native_spans=[],ocr_json=asset(B/f'ocr/page-{n:04}.json'),ocr_text=asset(B/f'ocr/page-{n:04}.txt'),transcript_span=span(start,end));pages.append(page)
    for k,bm in enumerate(re.finditer(rb'\S(?:.*?\S)?(?=\n\n|\n?\Z)',raw[start:end],re.S),1):
        s=span(start+bm.start(),start+bm.end());kind='table_fragment' if s.text.startswith('|') else 'editorial_graphic_note' if s.text.startswith('[editorial:') else 'printed_context'
        blocks.append(Block(id=f'p{n}-b{k:02}',page=n,kind=kind,transcript_span=s,image=page.image))
    for mm in re.finditer(rb'<(u|s|sup)>(.*?)</\1>',raw[start:end],re.S):
        marks.append(Mark(page=n,kind={'u':'underline','s':'strikethrough','sup':'superscript'}[mm[1].decode()],transcript_span=span(start+mm.start(2),start+mm.end(2))))
def find(s,page=None):
    found=[b for b in blocks if s in b.transcript_span.text and (page is None or b.page==page)]
    assert len(found)==1,(s,len(found));return found[0].id
tables=[
Table(id='C406.1(2)',title='Additional energy efficiency credits for Group R and I occupancies',pages=[2,3],fragment_block_ids=[],context_block_ids=[find('8. TABLE',2),find('TABLE C406.1(2)\n',2)],physical_data_rows=2,qualifiers=['Climate Zone6B; fossil row visibly struck9 followed by underlined9; heat-pump row struck5 followed by underlined9.','Both rows carry superscript b; no definition for this first table b appears in the seven-page excerpt. Do not borrow another table footnote.']),
Table(id='C406.1(3)',title='Additional energy efficiency credits for Group E occupancies',pages=[3],fragment_block_ids=[find('water heater <sup>a</sup>',3)],context_block_ids=[find('9. TABLE',3),find('TABLE C406.1(3)\n',3),find('a. For schools',3)],physical_data_rows=2,qualifiers=['Climate Zone6B; fossil struck3/underlined3; heat-pump struck1/underlined3.','Both a markers link only to For schools with showers or full-service kitchens.']),
Table(id='C406.1(5)',title='Additional energy efficiency credits for other occupancies',pages=[3],fragment_block_ids=[],context_block_ids=[find('10. TABLE',3),find('OTHER<sup>a</sup>',3),find('a. Other occupancies',3)],physical_data_rows=2,qualifiers=['Climate Zone6B; fossil struck9/underlined9; heat-pump struck5/underlined9.','Title marker a excludes Groups B,E,I,M,R; both row markers b reference Section406.7.1 as printed.']),
Table(id='C407.2',title='Requirements for total building performance',pages=[3,4],fragment_block_ids=[find('Thermal envelope certificate',3),find('Slabs-on-grade',4)],context_block_ids=[find('11. TABLE',3),find('TABLE C407.2\n',3)],physical_data_rows=3,qualifiers=['Envelope is a merged heading, not a legal data row. The two unheaded page4 rows continue the page3 table.']),
Table(id='R405.2',title='Requirements for total building performance',pages=[6],fragment_block_ids=[find('Water heating equipment location</u>',6)],context_block_ids=[find('20. Table',6),find('TABLE R405.2 REQUIREMENTS',6)],physical_data_rows=1,qualifiers=['Mechanical is a merged heading. R403.5.4 associates with Water heating equipment location.']),
Table(id='R406.2',title='Requirements for energy rating index',pages=[6],fragment_block_ids=[find('Water heating equipment</u>',6)],context_block_ids=[find('21. Table',6),find('TABLE R406.2 REQUIREMENTS',6)],physical_data_rows=1,qualifiers=['Mechanical is a merged heading. Source title is Water heating equipment, without location.']),
Table(id='R406.5',title='Maximum energy rating index',pages=[7],fragment_block_ids=[find('| 6 | 54 |',7)],context_block_ids=[find('TABLE R406.5 MAXIMUM',7),find('R406.5 ERI-based compliance.',7)],physical_data_rows=1,qualifiers=['Climate zone6, all-electric54, mixed-fuel underlined50.','The preceding paragraph visibly references TableR406.4, while the displayed table is R406.5; preserve source difference.'])]
# Two visually identical b-marked fragments belong to distinct caption contexts.
bfragments=[b for b in blocks if b.page==3 and b.kind=='table_fragment' and 'water heater <sup>b</sup>' in b.transcript_span.text]
assert len(bfragments)==2
tables[0].fragment_block_ids=[bfragments[0].id];tables[2].fragment_block_ids=[bfragments[1].id]
links=[]
for i,a,p,b,q,reason in [
('c401','3. Section C401.2.2',1,'C401.2.2 ASHRAE 90.1.',2,'The amendment introduction on page1 continues with its body on page2.'),
('table-ri','TABLE C406.1(2)\n',2,'water heater <sup>b</sup>',3,'The page2 R/I caption belongs to the first page3 table; not GroupE.'),
('envelope','Thermal envelope certificate',3,'Slabs-on-grade',4,'The Envelope table continues across pages3/4.'),
('r401','2.4.',4,'3. For buildings',5,'Residential R401.2.5 item3 and certificate condition continue onto page5.'),
('r404','19. A new Section',5,'R404.4 Additional electric infrastructure.',6,'The heading on page5 introduces page6 requirements and their exceptions.'),
('eri','22. Section R406.5',6,'R406.5 ERI-based compliance.',7,'The ERI amendment heading continues into page7 text/table.')]:
    target=bfragments[0].id if i=='table-ri' else find(b,q)
    links.append(Link(id=i,kind='cross_page_continuation',from_block_id=find(a,p),to_block_id=target,reason=reason))
dates=[DateClaim(literal=s,role=role,block_ids=[find(anchor,p)]) for s,role,anchor,p in [
('6/1/2026 8:47 AM','recorder stamp; no timezone supplied','Reception #508292',1),
('19th DAY OF MAY, 2026','printed adoption claim; th superscript','ADOPTED BY',7),
('April 21, 2026','attested proposed-ordinance introduction and reading','The above is a true',7),
('April 30, 2026','attested publication of proposed ordinance','The above is a true',7),
('May 28, 2026','attested publication by title of adopted ordinance','Adopted Ordinance Published',7),
('30 days after publication as required by law','conditional effective-date clause, not a computed verified date','SECTION 3. EFFECTIVE DATE',7)]]
custody=B/'retrieval-evidence';custody.mkdir(exist_ok=True)
up=B.parent/'ptolemy-chaffee-directed-retrieval'
for name in ['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json','REPORT.md','PLAN.json','PLAN.schema.json','events/A002/RESULT.json','events/A002/RESERVATION.json','events/A002/stdout.writeout.json','events/A002/public-response.headers','events/A002/stderr.txt']:
    dst=custody/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(up/name,dst)
record=Review(source_id='chaffee-electric-ordinance-2026-01-atlas-directed',authority_id='CO-COUNTY-CHAFFEE',reviewed_at=datetime.now(timezone.utc).isoformat(),source=asset(B/'source/original.pdf'),transcript=asset(B/'TRANSCRIPT.md'),method='Atlas direct inspection of all7 full300dpi Poppler source images and9 exact source crops, then full printed-text transcription with explicit underlined/struck/superscript markup and qualified graphic notes. Unchanged on-device Apple Vision OCR observations compared separately; source has no native text. Later revised after Plato independently identified a missing final annotation block and an obscured printed-name character. This is not a blind or independent-model-family review.',full_pages=list(range(1,8)),focused_crops=[asset(p) for p in sorted((B/'crops').glob('*.png'))],pages=pages,blocks=blocks,marks=marks,tables=tables,links=links,dates=dates,observed_get_completed_at='2026-09-13T16:09:47.762418Z',acquisition_evidence=[asset(p) for p in sorted(custody.rglob('*')) if p.is_file()],ocr_bytes=sum(p.ocr_text.size_bytes for p in pages),observations=[
'All seven native text files are empty. OCR is a machine observation and is never substituted for native text.',
'OCR drops or merges visible underlining and strikethrough. Gas-lighting language, energy requirements and six numeric credit cells require explicit markup preservation.',
'The first and third fossil-water-heater cells visibly replace9 with9; the school fossil cell replaces3 with3. These are source observations, not OCR repairs or new calculations.',
'OCR corrupts table values into92, $2,13 and52, omits most of item10, omits enumerators2/3 and8/9, damages the C406.1 text, and drops the page6 Exceptions heading and final multiple-units condition. The reviewed transcript restores these from images.',
'OCR garbles the final attestation publication line and omits the printed chair-name/title line; the third surname character remains obscured; no OCR signature tokens are accepted as names.',
'Preserved source anomalies include item1.1 followed by2.2 under R401.2.5(1), mixed fuel versus mixed-fuel, R406.5 paragraph reference to TableR406.4, and C406.1(5) note Section406.7.1 without C.',
'Source water-heater exceptions differ: commercial >300,000Btu/h has no multiple-unit qualifier, residential includes it. Preserve each full exception with its own section.',
'The leading p3 table has superscript b but no local b definition in this seven-page excerpt; no missing base-code text is invented.',
'Only page1 has the visible recorder header; no printed footer page numerals are observed. The final printed date clause has no terminal period.'],limitations=[
'Full reviewed scope is printed words, numeric/table associations, visible amendment markup and qualified graphics. Paragraph wrapping, table pipes, physical-page headings and editorial bracket notes are transcription packaging, not printed source text. Bold and italic typeface are not exhaustively encoded; the source images remain authoritative.',
'Underline/strike extents around tiny terminal punctuation can be visually imprecise at scan resolution. No exact Unicode typography or byte identity of source typeface is claimed. Inline tags identify observed markings, not legal operative status.',
'The handwritten clerk name between Lori Mitchell by and Chief Deputy is unresolved. Blue chair signature identity is not certified; printed name is separate. Seal presence does not authenticate execution.',
'The recorder date, adoption and publication statements are visible source claims; no external publication proof, amendment chain, legal effective date or currentness check occurred. No computation converts the30-day clause into a verified effective_date.',
'Twenty-two numbered amendment instructions, seven logical tables, eight physical table fragments and twelve data rows are scoped document counts, not statewide coverage or independent regulatory burdens.',
'The initial source review predates canonical intake. GET completion is the new observed retrieval event, not historical publication/adoption or future repository receipt.',
'The retrieval evidence subset preserves exact A002 records plus frozen parent metadata; it does not contain all files named in the full upstream manifest. Full upstream packet is separate.',
'The initial transcription used only this source and OCR. This revision incorporates two source-based findings from Plato’s independent Codex task; no Grok report or other legal source was consulted. The printed chair surname has an obscured third character; do not assert c or f. This is not a guarantee of perfect transcription.'])
(B/'SOURCE_QA.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n')
(B/'SOURCE_QA.json').write_text(record.model_dump_json(indent=2)+'\n')
print('Draft assembled:',len(blocks),'blocks',len(marks),'marks',len(tables),'tables',record.ocr_bytes,'OCR bytes')
