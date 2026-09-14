"""Create an additive local review; never rewrite packet, candidate or source bytes."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json,shutil
import pymupdf,jsonschema
from pydantic import BaseModel,ConfigDict
from review_models import Review,FileRef
B=Path(__file__).parent
BASE=Path('/Users/mcoors/Documents/Project Geode')
PACK=BASE/'handoffs/grok-pdf-review-2026-09-11-batch-5'
SID='greeley-water-sewer-proposed-pif-notice-sd008-08'
M=json.loads((PACK/'manifest.json').read_text())
selected=next(x for x in M['sources'] if x['source_id']==SID) if 'sources' in M else next(x for x in M['documents'] if x['source_id']==SID)
class Copy(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    original_path:str
    copied_file:FileRef
class Custody(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    copied_at:datetime
    files:list[Copy]
    originals_unchanged:bool
copies=[]
def ref(rel):
    p=B/rel;return dict(path=rel,sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size)
def copy(src,rel,expected=None):
    p=B/rel;p.parent.mkdir(parents=True,exist_ok=True)
    assert src.is_file() and not src.is_symlink()
    body=src.read_bytes()
    if expected:assert sha256(body).hexdigest()==expected['sha256'] and len(body)==expected['size_bytes']
    if not p.exists():p.write_bytes(body);p.chmod(0o444)
    assert p.read_bytes()==body
    copies.append(Copy(original_path=str(src),copied_file=FileRef(**ref(rel))))
copy(PACK/'manifest.json','inputs/manifest.json')
copy(PACK/'manifest.schema.json','inputs/manifest.schema.json')
copy(PACK/selected['original']['path'],'inputs/original.pdf',selected['original'])
copy(PACK/selected['candidate']['path'],'inputs/candidate.txt',selected['candidate'])
copy(PACK/selected['page_evidence_schema']['path'],'inputs/page-evidence.schema.json',selected['page_evidence_schema'])
texts={};page_receipts={}
for p in selected['pages']:
    n=p['physical_page']
    copy(PACK/p['image']['path'],f'inputs/page-{n:04}.png',p['image'])
    copy(PACK/p['evidence']['path'],f'inputs/native-page-{n:04}.json',p['evidence'])
    r=json.loads((B/f'inputs/native-page-{n:04}.json').read_text())
    texts[n]=r['text'];page_receipts[n]=r
c=Custody(copied_at=datetime.now(timezone.utc),files=copies,originals_unchanged=True)
(B/'CUSTODY_RECEIPT.json').write_text(c.model_dump_json(indent=2)+'\n')
(B/'CUSTODY_RECEIPT.schema.json').write_text(json.dumps(Custody.model_json_schema(),indent=2)+'\n')
jsonschema.Draft202012Validator(Custody.model_json_schema()).validate(json.loads(c.model_dump_json()))
def span(n,start,end):
    data=texts[n].encode()[start:end]
    return dict(physical_page=n,start_byte=start,end_byte_exclusive=end,text=data.decode(),sha256=sha256(data).hexdigest())
def substring(n,s,occ=0):
    data=texts[n].encode();needle=s.encode();pos=-1
    for _ in range(occ+1):pos=data.index(needle,pos+1)
    return span(n,pos,pos+len(needle))
def line_span(n,value,occ=0):
    off=0;hits=[]
    for line in texts[n].splitlines(keepends=True):
        if line.strip()==value:
            leading=len(line)-len(line.lstrip())
            start=off+len(line[:leading].encode());hits.append(span(n,start,start+len(value.encode())))
        off+=len(line.encode())
    return hits[occ]
def lines_span(n,first,last,occ=0):
    a=line_span(n,first,occ);b=line_span(n,last,occ)
    return span(n,a['start_byte'],b['end_byte_exclusive'])
with pymupdf.open(B/'inputs/original.pdf') as doc:
    words=doc[1].get_text('words',sort=False)
    def cell(col,value,occ=0):
        if len(value.split())==1:
            boxes=[list(w[:4]) for w in words if w[4]==value]
        else:boxes=[list(x) for x in doc[1].search_for(value)]
        box=boxes[occ]
        return dict(column=col,display_text=value,native_span=line_span(2,value,occ),native_occurrence=occ,pdf_bbox=[float(x) for x in box],source_dollar_sign='$' if value.startswith('$') else None)
    values=[('3/4"','$11,200','$6,800'),('1"','18,700','11,400'),('1-1/2"','37,300','22,800'),('2"','59,700','36,400'),('3"','130,700','79,700'),('4"','223,900','136,700'),('6"','466,500','284,800')]
    left=[dict(row_id=f'tap-{i}',source_row=i,cells=[cell(k,v) for k,v in enumerate(row,1)]) for i,row in enumerate(values,1)]
    right=[dict(row_id='single-family-1',source_row=1,cells=[cell(1,'Single Family - 3/4"'),cell(2,'$11,200',1),cell(3,'$6,800',1)])]
    tables=[dict(table_id='tap_size',physical_page=2,source_position='left',heading_text='Plant Investment Fees (PIFs) Based on Tap Size',heading_span=lines_span(2,'Plant Investment Fees (PIFs) Based','on Tap Size'),headers=[dict(column=1,display_text='Water Tap Size',native_span=lines_span(2,'Water','Tap Size'),visibly_blank=False),dict(column=2,display_text='Water PIF',native_span=line_span(2,'Water PIF'),visibly_blank=False),dict(column=3,display_text='Sewer PIF',native_span=line_span(2,'Sewer PIF'),visibly_blank=False)],rows=left,interpretation_boundary='Seven tap-size rows on the left. The heading does not explicitly limit this table to nonresidential users; do not invent that scope.'),dict(table_id='single_family',physical_page=2,source_position='right',heading_text='Plant Investment Fees (PIFs) Single Family Residential Units',heading_span=lines_span(2,'Plant Investment Fees (PIFs) Single Family','Residential Units'),headers=[dict(column=1,display_text=None,native_span=None,visibly_blank=True),dict(column=2,display_text='Water PIF',native_span=line_span(2,'Water PIF',1),visibly_blank=False),dict(column=3,display_text='Sewer PIF',native_span=line_span(2,'Sewer PIF',1),visibly_blank=False)],rows=right,interpretation_boundary='One separate right-hand row. Do not insert it as a second row of the left table or treat it as a total. Its first column header is visibly blank.')]
pages=[]
for item in selected['pages']:
    n=item['physical_page'];data=texts[n].encode();off=0;parts=[]
    # Whole native lines partition every byte, including all spaces and blank lines.
    for line in texts[n].splitlines(keepends=True):
        end=off+len(line.encode());parts.append(span(n,off,end));off=end
    assert off==len(data)
    pages.append(dict(physical_page=n,image=ref(f'inputs/page-{n:04}.png'),native_receipt=ref(f'inputs/native-page-{n:04}.json'),native_text=texts[n],native_sha256=sha256(data).hexdigest(),native_bytes=len(data),candidate_start_byte=item['candidate_text_offset_bytes'],candidate_end_byte_exclusive=item['candidate_text_end_byte_exclusive'],partition=parts,full_image_directly_reviewed=True))
O=[]
def obs(i,ps,sp,word,qual):O.append(dict(id=f'EB017-O{i:02}',physical_pages=ps,native_spans=sp,finding=word,qualification=qual))
obs(1,[1],[line_span(1,'November 20, 2020')],'Notice date is November 20, 2020.','Printed source date, not retrieval or adoption.')
obs(2,[1],[lines_span(1,'NOTICE OF CHANGES IN PLANT INVESTMENT FEES','AND PLUMBING CONTRACTORS')],'The notice addresses Weld County homebuilders, building contractors and plumbing contractors.','Greeley issuer and Water/Sewer context remain distinct from the recipients; this is not a Weld County fee enactment.')
obs(3,[1,2],[substring(1,'December 16, 2020 board meeting.'),substring(1,'These changes will become effective on March 1, 2021, \nassuming they are adopted.'),line_span(2,'EFFECTIVE MARCH 1, 2021')],'The Board will review updated fees for adoption at its December 16, 2020 meeting. March 1, 2021 is expressly conditional on adoption.','The page 2 effective-date heading must be read with the page 1 condition; this notice does not establish adoption or current applicability.')
obs(4,[1],[substring(1,'A copy of the new plant investment fee schedule is printed on the \nreverse side of this notice.')],'The notice points to the schedule on its reverse; the delivered second page contains the two tables.','Preserve the two-page source relationship, not two unrelated fee schedules.')
obs(5,[1],[substring(1,'(350-9801)')],'The body contact number is (350-9801).','The image-only footer separately prints (970) 350-9811 and Fax (970) 350-9805. Do not silently harmonize different source numbers.')
obs(6,[1],[lines_span(1,'Erik Dial','Greeley Water and Sewer')],'Printed closing: Erik Dial / Utility Finance Manager / Greeley Water and Sewer. No handwritten signature is visible in the closing.','A printed name/title is not signature authentication.')
obs(7,[2],[tables[0]['heading_span'],tables[1]['heading_span']],'Two side-by-side tables have separate headings and header rows; the first right-hand column header is blank.','Native extraction interleaves their titles, headings and first data rows.')
obs(8,[2],[c['native_span'] for c in left[0]['cells']+right[0]['cells']+left[1]['cells']],'Native order gives the first left row, then the right Single Family row, then resumes the left table at 1-inch.','The typed table structures restore only visual row associations. No source characters are rewritten, and the right row is not appended within the left table.')
obs(9,[2],[c['native_span'] for t in tables for r in t['rows'] for c in r['cells'] if c['column']>1],'All 16 fee amounts were inspected. Dollar signs occur only on the first left row and the single-family row: four amount cells in total.','The remaining 12 amount cells have no printed dollar sign; preserve that typographic fact rather than filling symbols into a source transcription.')
obs(10,[2],[c['native_span'] for r in left for c in r['cells'] if c['column']==1],'Seven left tap labels are 3/4",1",1-1/2",2",3",4",6".','Displayed quote marks and the hyphenated fraction are retained as native characters; exact raster Unicode identity is not independently inferred.')
logo=dict(id='EB017-IMAGE-01',physical_page=1,image=ref('inputs/page-0001.png'),source_region='upper-left city logo',text_lines=['City of','Greeley','Colorado'],native_text_present=False,qualification='These words are visibly incorporated in the multicolor graphic; this list is not a claim of linear logo reading order or a new legal-authority determination.')
footer=dict(id='EB017-IMAGE-02',physical_page=1,image=ref('inputs/page-0001.png'),source_region='bottom letterhead footer and slogan',text_lines=['Water and Sewer Department • 1100 10th Street, Suite 300, Greeley, CO 80631 • (970) 350-9811 Fax (970) 350-9805','A City Achieving Community Excellence'],native_text_present=False,qualification='Complete visible wording normalized to single spaces. Round separators are represented by • for readability; their exact Unicode is not inferred. A horizontal line separates the contact line from the slogan. Body 350-9801 and footer 350-9811 remain distinct.')
data=dict(schema_version=1,assignment_id='EB-PDF-017',source_id=SID,authority_id='CO-MUNICIPAL-GREELEY',prepared_at=datetime.now(timezone.utc).isoformat(),review_mode='candidate_aware_source_review_before_external_report',external_reports_consulted=False,source_status='proposed_fee_notice_with_conditional_schedule',source_pdf=ref('inputs/original.pdf'),candidate=ref('inputs/candidate.txt'),input_custody=ref('CUSTODY_RECEIPT.json'),pages=pages,tables=tables,observations=O,image_only=[logo,footer],inspected_crops=[ref('crops/p1-footer.png'),ref('crops/p2-two-tables.png')],all_native_bytes=1316,table_data_cells=24,native_changes='none',legal_currentness='not_verified',legal_effect_verified=False,source_and_packet_changed=False,network_requests=0,limits=['Both complete PNG pages and two crops were directly viewed before generating this source QA. This is candidate-aware, not blind; no external EB017 report was consulted.','The exact PDF, candidate, images, native receipts and packet manifest are copied byte-for-byte. All trailing spaces, line wraps, native order and packaging offsets remain preserved.','Twenty-four data cells means eight labels plus 16 amount cells. Table headings and six header positions are additional structure, including one visibly blank header.','The logo/footer are image-only additions to review evidence; they are not silently inserted into the native candidate.','Source numbers and date conditions are transcribed from this notice only. No adopted fee status, present-day legal applicability, complete fee universe, inflation adjustment or computed charge is certified.'])
m=Review.model_validate_json(json.dumps(data))
(B/'SOURCE_REVIEW.json').write_text(m.model_dump_json(indent=2)+'\n')
(B/'SOURCE_REVIEW.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n')
md=['---','title: EB017 Greeley proposed water and sewer PIF notice — source QA','prepared_at: '+m.prepared_at.isoformat(),'review_mode: candidate_aware_source_review_before_external_report','external_reports_consulted: false','legal_currentness: not_verified','native_changes: none','---','','# Scope and result','','Both full pages and two diagnostic crops were directly inspected. The notice is dated November20,2020 and anticipates Board review on December16,2020. Its March1,2021 effective-date statement expressly says **assuming they are adopted**. The second-page heading alone does not establish adoption or current fees.','','The two native pages retain all1,316 bytes unchanged (797+519), with exact candidate offsets and exhaustive byte partitions. The table reconstruction binds all24 data cells to native spans and PDF coordinates, preserving separate headings and all header positions.','','# Page2 left table','','**Plant Investment Fees (PIFs) Based on Tap Size**','','| Water Tap Size | Water PIF | Sewer PIF |','|---|---:|---:|']
for r in left:md.append('| '+' | '.join(c['display_text'] for c in r['cells'])+' |')
md+=['','# Page2 right table','','**Plant Investment Fees (PIFs) Single Family Residential Units**','','| [visibly blank source header] | Water PIF | Sewer PIF |','|---|---:|---:|','| '+' | '.join(c['display_text'] for c in right[0]['cells'])+' |','','The right-hand row interrupts the native stream between the first and second left-hand rows. It remains a separate table. Dollar signs are printed only in the four cells shown with `$`; none has been added to the other12 amounts. The blank right-hand header is described here rather than invented as a source label.','','# Image-only wording and distinct contacts','','The City of Greeley / Colorado logo at the upper left and the full footer are absent from the native candidate. The footer reads:','','> '+footer['text_lines'][0],'> '+footer['text_lines'][1],'','The round separators and spacing above are a readable transcription, not an exact Unicode claim. The body says **(350-9801)**; the footer says **(970) 350-9811**, with fax **(970) 350-9805**. These distinct numbers remain as printed. Erik Dial, Utility Finance Manager, Greeley Water and Sewer is a printed closing, not an authenticated handwritten signature.','','# Source observations','']
for o in O:md+=['- **'+o['id']+'** '+o['finding']+' '+o['qualification']]
md+=['','# Validation and boundaries','','`validate_source_review.py` checks strict schema validation, copied-input hashes, PDF re-extraction, all native byte partitions and candidate slices, exact cell/header anchors, cell geometry and every row association. It performs no network or writes. Image-only wording is a scoped direct visual finding, not machine-certified OCR.','','No source, packet, candidate, repository, registry or control-plane file was edited. No external report was read and no message was sent externally. The notice’s recipients do not make it a Weld County enactment; all legal currentness remains unverified.','']
# Readability normalization affects narrative only, not native spans, cells or originals.
fix={'November20,2020':'November 20,2020','December16,2020':'December 16,2020','March1,2021':'March 1,2021','all1,316':'all 1,316','all24':'all 24','Page2':'Page 2','other12':'other 12','(970) 350':'(970) 350'}
text='\n'.join(md)
for a,z in fix.items():text=text.replace(a,z)
(B/'SOURCE_REVIEW.md').write_text(text)
print('Saved2pages,24cells,1316nativebytes,10observations,2image-only regions.')
