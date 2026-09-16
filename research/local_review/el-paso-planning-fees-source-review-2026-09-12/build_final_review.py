"""Additive post-OCR reconciliation; leaves the source-first draft unchanged."""
from pathlib import Path
import sys,json,hashlib,copy
from datetime import datetime,timezone
HERE=Path(__file__).absolute().parent;sys.path.insert(0,str(HERE))
from review_models import *
import pymupdf

def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,b):
 p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def asset(name):
 b=(HERE/name).read_bytes();return Asset(path=name,sha256=sha(b),size_bytes=len(b))
def save(name,obj):
 b=(obj.model_dump_json(indent=2)+'\n').encode();type(obj).model_validate_json(b);write(name,b);write(name.replace('.json','.schema.json'),(json.dumps(type(obj).model_json_schema(),indent=2)+'\n').encode())
original=VisualTranscript.model_validate_json((HERE/'VISUAL_TRANSCRIPTION.json').read_bytes())
assert sha((HERE/'VISUAL_TRANSCRIPTION.json').read_bytes())=='220ef0c72ae74e45c9a1198387b128ee576790b8d900bb9a703ff8416605d8d9'
changes=[('P1-PLAN-20','Interior Lot Lines:','Interior Lot Lines;','p1-lot-lines',1,(140,1121,1762,1159)),('FN-07','Commercial','Commerical','p5-footnote7',5,(140,487,1762,529)),('GENERAL-2','performed','preformed','p5-refund-note',5,(140,1121,1762,1193))]
errata=[]
for i,(id,before,after,crop,page,box) in enumerate(changes,1):
 c=next(r for r in original.rows if r.id==id).cells[0]
 assert c.text.count(before)==1
 errata.append(Erratum(id=f'VE-{i:02}',row_id=id,column='application_type',before=c.text,after=c.text.replace(before,after),source_crop=asset(f'crops/{crop}.png'),source_page=page,pixel_bbox=box,basis='After comparison with separately generated OCR, the original source-image crop was directly inspected. This corrects the initial manual visual draft to the visible source; OCR and original draft remain unchanged.'))
e=VisualErrata(frozen_original=asset('VISUAL_TRANSCRIPTION.json'),prepared_at=datetime.now(timezone.utc).isoformat(),entries=errata);save('VISUAL_ERRATA.json',e)
data=original.model_dump();data['review_mode']='candidate_aware_visual_grid_after_separate_ocr_comparison';data['ocr_consulted_at_freeze']=True;data['frozen_at']=datetime.now(timezone.utc).isoformat();data['initial_visual_transcript']=asset('VISUAL_TRANSCRIPTION.json');data['visual_errata']=asset('VISUAL_ERRATA.json');data['ocr_receipt']=asset('OCR_COMPARISON_RECEIPT.json')
text=bytearray()
for r in data['rows']:
 for c in r['cells']:
  match=next((x for x in errata if x.row_id==r['id'] and x.column==c['column']),None)
  if match:c['text']=match.after
  c['transcript_start_byte']=len(text);text.extend(c['text'].encode());c['transcript_end_byte']=len(text);text.extend(b'\n')
write('REVIEWED_TRANSCRIPTION.txt',bytes(text));data['transcript']=asset('REVIEWED_TRANSCRIPTION.txt')
data['limitations']=[x for x in data['limitations'] if not x.startswith('No OCR candidate') and not x.startswith('Canonical intake completion')]+['The original image-first draft is retained unchanged. This separate reviewed grid incorporates exactly the three image-confirmed errata after consulting uncorrected OCR. It does not replace the historical freeze sequence or claim blind review.','Separate actual repository intake receipt is now retained as custody evidence. Archived-pending-pipeline receipt is not verified HTTP acquisition, adoption or legal currentness.']
grid=ReviewedGrid.model_validate(data);save('REVIEWED_GRID.json',grid)
ocr={n:json.loads((HERE/f'ocr/retry-authorized/page-{n:04}.stdout').read_bytes()) for n in range(1,6)}
comp=[]
for r in grid.rows:
 if r.role not in ['fee_row','footnote','general_note']:continue
 for c in r.cells:
  x0,y0,x1,y1=c.pixel_bbox;found=[]
  for i,l in enumerate(ocr[r.physical_page]['lines']):
   x,y,w,h=l['bbox'];cx=(x+w/2)*2200;cy=(1-y-h/2)*1700
   if x0<=cx<x1 and y0<=cy<y1:found.append((i,l['text']))
  observed=' '.join(t for i,t in found);expected=c.text+''.join(map(str,c.superscript_footnotes));same=' '.join(expected.split())==' '.join(observed.split())
  kind='comparison_agreement_not_proof' if same else 'ocr_omitted_visible_project_code' if c.column=='project_type' and not observed else 'ocr_fee_punctuation_error' if c.column=='application_fee' else 'ocr_superscript_misread_or_omitted' if c.superscript_footnotes else 'source_spacing_or_line_wrap_preserved'
  comp.append(OCRCell(row_id=r.id,physical_page=r.physical_page,column=c.column,ocr_observation_indices=[i for i,t in found],ocr_text=observed,visual_text_with_footnote_markers=expected,equal_after_whitespace_collapse=same,disposition=kind))
comparison=OCRComparison(status='uncorrected_ocr_compared_to_image_reviewed_grid',reviewed_grid=asset('REVIEWED_GRID.json'),ocr_receipt=asset('OCR_COMPARISON_RECEIPT.json'),method='observation_bbox_center_in_recorded_cell_then_engine_order; comparison only',cells=comp,final_differences=sum(not x.equal_after_whitespace_collapse for x in comp),confidence_interpretation='Engine scores are not verification or a probability of legal accuracy.');save('OCR_CELL_COMPARISON.json',comparison)
# Exact custody copies; line-by-line JSONL processing.
prep=HERE.parent/'el-paso-intake-preparation';tx=HERE.parent/'el-paso-intake-transaction'
for name,p in [('custody/source-provenance.jsonl',prep/'source-provenance.jsonl'),('custody/source-provenance.schema.json',prep/'source-provenance.schema.json'),('custody/intake-RECEIPT.json',tx/'execution/RECEIPT.json'),('custody/SD011-E043.html',prep/'inputs/referrals/SD011-E043.html'),('custody/SD011-E053.headers.txt',prep/'inputs/public-headers/SD011-E053.headers.txt')]:
 b=p.read_bytes();write(name,b);assert p.read_bytes()==b
selected=None
with (HERE/'custody/source-provenance.jsonl').open('rb') as f:
 for n,line in enumerate(f,1):
  obj=json.loads(line)
  if obj['source_id']=='el-paso-planning-fees-sd011':assert n==1;selected=(line,obj)
line,prov=selected
receipt=json.loads((HERE/'custody/intake-RECEIPT.json').read_bytes());records=receipt['intent']['records'];record=next(x for x in records if x['record_id']=='el-paso-planning-fees-sd011')
assert record['sha256']==SOURCE_SHA and record['acquisition_method']=='received_review_package'
assert (HERE/'source/original.pdf').read_bytes()==(HERE.parents[2]/'MasterLegalDatabase'/record['archive_path']).read_bytes()
for key in ['authorization:','cookie:','set-cookie:','proxy-authorization:']:
 assert key not in (HERE/'custody/SD011-E053.headers.txt').read_text().lower()
nativecandidate=b''.join(f'===== PHYSICAL PDF PAGE {n} OF 5 (PACKAGING MARKER; NATIVE TEXT EMPTY) =====\n\n'.encode() for n in range(1,6));write('native/candidate.txt',nativecandidate)
q=SourceQA(source_pdf=asset('source/original.pdf'),initial_visual_transcript=asset('VISUAL_TRANSCRIPTION.json'),reviewed_grid=asset('REVIEWED_GRID.json'),visual_errata=asset('VISUAL_ERRATA.json'),completed_at=datetime.now(timezone.utc).isoformat(),status='five_pages_source_reviewed_with_explicit_unresolved_clipped_tail',page_coverage=[1,2,3,4,5],native_extraction=NativeSummary(version=pymupdf.VersionBind,method='Page.get_text("text", sort=False, flags=195)',page_files=[asset(f'native/page-{n:04}.txt') for n in range(1,6)],candidate_with_page_markers=asset('native/candidate.txt')),ocr_comparison=OCRSummary(status='machine_ocr_unreviewed_preserved_with_separate_visual_comparison',receipt=asset('OCR_COMPARISON_RECEIPT.json'),comparison=asset('OCR_CELL_COMPARISON.json'),actual_os_version=ocr[1]['os_version'],engine_observation_count=sum(len(o['lines']) for o in ocr.values())),custody=Custody(acquisition_method='received_review_package',received_from='Sherlock',claimed_source_url=prov['requested_url_claim'],claimed_final_url=prov['final_url_claim'],claimed_http_acquisition_at=prov['acquisition_started_at_claim'],actual_repository_received_at=record['received_at'],intake_status=record['status'],intake_receipt=asset('custody/intake-RECEIPT.json'),source_provenance_manifest=asset('custody/source-provenance.jsonl'),source_provenance_line_sha256=sha(line),source_referral_html=asset('custody/SD011-E043.html'),source_public_headers=asset('custody/SD011-E053.headers.txt'),limitations=['The original SD011 HTTP times/statuses are supplied claims; this review made no source request. Successful local custody/byte checks do not retrospectively authenticate the transfer.','The SD011 batch exceeded the distinct-target cap (66/50) and lost two earlier non-PDF bodies; retained PDF custody does not repair those failures.','The source-provenance draft predates actual intake; its null received time and one-page review scope remain historical. The separate transaction receipt supplies actual repository receipt, not legal review.']),observations=[
'Every one of the five full page images was directly inspected before OCR. All 104 fee rows, three table columns, 15 footnotes, three General Notes, section continuations and page labels are represented. One clipped row tail remains unresolved, so no fully legible complete extraction is claimed.',
'The original native text is empty on all pages. Visual UTF-8 offsets belong only to the separately authored transcripts. Native offsets are null; no source text layer was manufactured.',
'Three initial visual-draft mistakes were corrected additively after direct crop checks: a semicolon after Interior Lot Lines; source Commerical in footnote 7; source preformed in General Note 2. Frozen draft and uncorrected OCR remain unchanged.',
'The application-fee column footnote says fees include a $37.00 technology fee. No additional charge is calculated. Footnote 5 preserves the combined maximum of two waiver/deviation requests per land-use application included without extra fee.',
'Five fee-row project-type cells are visibly blank: P1-PLAN-17 and the four Other rows on page 4. Blank columns beside all footnotes/General Notes are also retained. TBD is literal for state-interest activities, resubmittal and recording fees; it is not zero.',
'Project-type letters A/B/C/D and C or D remain source codes, without inferred meanings. Planning-Major continues from page 2 to 3; Engineering-Major from page 3 to 4.',
'The full footnotes retain excluded second kitchens, final-plat level conditions, hearings may be required, distinct percentage thresholds, sketch-plan acreage/unit conditions and the minor-special-use list. The literal addition or area phrase in footnote 10 is not repaired.',
'The three General Notes preserve Director discretion, the County-staff-error exception to refund wording, and technical-review/expert costs paid by the applicant with extent/nature established prior to formal submittal. No unconditional waiver, fixed surcharge or legal interpretation is produced.',
'Apple Vision comparison retains its machine output unmodified. A source fee $12,145.00 was recognized as $12.145.00; several source superscripts and three visible project codes were misread/omitted. Engine confidence does not establish source correctness.',
'May 1, 2026 is the source-printed effective-date claim. No adopting instrument or amendment/currentness chain was examined; no verified adoption or effective date is assigned.'
],unresolved_regions=['P3-ENG-14 application-type cell: visible wording ends at submittal against the cell border; an invisible continuation or closing parenthesis cannot be reconstructed. OCR reading agrees only with the visible portion and does not close this gap.','Exact Unicode/spacing/typographic appearance cannot be determined solely from pixel shapes. Line wraps are joined in visual transcription, raised footnote numbers are separate references, and the logo is retained as image artwork rather than transcribed legal text.'])
save('SOURCE_QA.json',q)
md=['---','title: "El Paso planning fees — five-page source review"','source_id: "el-paso-planning-fees-sd011"','authority_id: "CO-COUNTY-EL_PASO"','status: "source_reviewed_with_unresolved_clipped_tail"','legal_currentness: "not_verified"','---','',
'All five full page images were directly inspected. The package records **104 fee rows, 15 footnotes and three General Notes** with page-pixel bounds. The source has **zero native text bytes on every page**; visual transcript offsets are explicitly separate. This is source-first review with prior title/role knowledge, followed by disclosed OCR comparison—not a blind review.','',
'One page-3 label is clipped at its right cell edge. Its visible text is retained through “submittal”; no invisible ending or closing parenthesis is supplied. This prevents a claim of completely legible extraction.','',
'`VISUAL_TRANSCRIPTION.json` preserves the initial image-first draft. `REVIEWED_GRID.json` is the final grid after three image-confirmed additive corrections: “Lines;” rather than “Lines:”, source “Commerical”, and source “preformed”. `VISUAL_ERRATA.json` binds those changes to original image crops. OCR outputs remain uncorrected; the source $12,145.00 comma was misread by OCR as a period.','',
'The source banner says **Fee Schedule- Effective Date May 1, 2026**. This is a printed claim, not an independently verified effective/adoption date. The actual repository receipt at **2026-09-12T22:59:48.795762Z** is received-review-package custody. The earlier claimed HTTP time remains unverified.','',
'Rows below collapse source line wraps and separate raised footnote markers. “(blank)” denotes an observed blank cell; it does not mean zero or inherit a preceding project code. IDs and table organization are review metadata, not additional source wording. No fees are calculated.','']
for page in range(1,5):
 md += [f'## Physical page {page}','','| Review row | Application type | Application fee | Project type | Footnote markers |','|---|---|---|---|---|']
 for row in grid.rows:
  if row.physical_page==page and row.role=='fee_row':
   c=row.cells;label=c[0].text+(' [clipped tail unresolved]' if c[0].state.endswith('unresolved_tail') else '')
   md.append('| '+' | '.join([row.id,label,c[1].text,c[2].text or '(blank)',', '.join(map(str,c[0].superscript_footnotes))])+' |')
 md.append('')
md+=['## Physical page 5 — complete notes','']
for row in grid.rows:
 if row.role in ['footnote','general_note']:md += [row.cells[0].text,'']
md += ['## Verification','',
'Run `validate_review.py` with Python, Pydantic 2, PyMuPDF and jsonschema from any working directory. It is read-only and makes no network requests or OCR calls. It verifies the closed inventory, source PDF/page count and empty native text, all image/cell/pixel/UTF-8 bindings, the exact three-change reconciliation, footnote and blank-cell preservation, OCR receipts/comparison and separate custody. Hash verification does not replace visual judgment. Pin the final manifest hash outside this folder.','',
'The supplied two early local OCR failures remain documented; the single authorized retry succeeded on all five pages. Nothing in the source PDF, raw archive, canonical ledger, source packet or earlier frozen reports was changed by this review.']
write('SOURCE_QA.md',('\n'.join(md)+'\n').encode())
print('Final grid',asset('REVIEWED_GRID.json').sha256,'QA',asset('SOURCE_QA.json').sha256,'remaining OCR differences',comparison.final_differences)
