"""Portable, read-only verification of El Paso's scanned planning-fee review."""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,sys
from datetime import datetime
import pymupdf,jsonschema
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE))
from review_models import Asset,Inventory,VisualTranscript,ReviewedGrid,VisualErrata,OCRComparison,SourceQA
SOURCE_SHA='c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12'
INITIAL_SHA='220ef0c72ae74e45c9a1198387b128ee576790b8d900bb9a703ff8416605d8d9'
OBSERVATIONS_SHA='5aaa66d7f1c81d498485be1ec36a40cd12799563f79de346805d26d48520c65d'
CHANGES={'P1-PLAN-20':('Interior Lot Lines:','Interior Lot Lines;'),'FN-07':('Commercial','Commerical'),'GENERAL-2':('performed','preformed')}
CROPS={
 'p3-clipped-label':(3,(138,1268,1810,1307)),
 'p5-footnotes-1-9':(5,(140,230,1765,678)),
 'p5-footnotes-10-15':(5,(140,675,1765,1052)),
 'p5-general-notes':(5,(140,1049,1765,1335)),
 'p1-lot-lines':(1,(140,1121,1762,1159)),
 'p5-footnote7':(5,(140,487,1762,529)),
 'p5-refund-note':(5,(140,1121,1762,1193)),
 'p3-fee-12145':(3,(1745,901,2054,940)),
 'p1-merger-project':(1,(1760,859,2054,898)),
}

def sha(body):return hashlib.sha256(body).hexdigest()
def ordinary(path):
 for p in (path,*path.parents):
  if p.is_symlink():raise ValueError('Symlink refused')
 if not path.is_file():raise ValueError('Ordinary file required')
def body(root,ref):
 rel=Path(ref.path)
 if rel.is_absolute() or '..' in rel.parts or rel.as_posix()!=ref.path:raise ValueError('Path escape/noncanonical path refused')
 p=root/rel;ordinary(p);b=p.read_bytes()
 if len(b)!=ref.size_bytes or sha(b)!=ref.sha256:raise ValueError('File hash/size differs: '+ref.path)
 return b
def read_model(root,name,model):
 p=root/name;ordinary(p)
 obj=model.model_validate_json(p.read_bytes())
 schema=root/name.replace('.json','.schema.json')
 if json.loads(schema.read_bytes())!=model.model_json_schema():raise ValueError('Schema differs: '+name)
 return obj

def validate(root:Path)->dict:
 root=Path(root).absolute()
 if root.is_symlink():raise ValueError('Symlink package refused')
 for p in root.rglob('*'):
  if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('Nonordinary package member')
 inv=read_model(root,'FINAL_MANIFEST.json',Inventory)
 listed={r.path for r in inv.files}|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
 if actual!=listed:raise ValueError('Closed inventory differs')
 for ref in inv.files:body(root,ref)
 if sha((root/'source/original.pdf').read_bytes())!=SOURCE_SHA:raise ValueError('Source PDF pin differs')
 if sha((root/'VISUAL_TRANSCRIPTION.json').read_bytes())!=INITIAL_SHA:raise ValueError('Initial source-first transcript pin differs')
 if sha((root/'VISUAL_OBSERVATIONS.json').read_bytes())!=OBSERVATIONS_SHA:raise ValueError('Initial observations pin differs')
 old=read_model(root,'VISUAL_TRANSCRIPTION.json',VisualTranscript)
 grid=read_model(root,'REVIEWED_GRID.json',ReviewedGrid)
 errata=read_model(root,'VISUAL_ERRATA.json',VisualErrata)
 comp=read_model(root,'OCR_CELL_COMPARISON.json',OCRComparison)
 qa=read_model(root,'SOURCE_QA.json',SourceQA)
 for ref in [old.visual_observations,old.transcript,grid.transcript,grid.initial_visual_transcript,grid.visual_errata,grid.ocr_receipt,errata.frozen_original,comp.reviewed_grid,comp.ocr_receipt,qa.source_pdf,qa.initial_visual_transcript,qa.reviewed_grid,qa.visual_errata,qa.ocr_comparison.receipt,qa.ocr_comparison.comparison,qa.custody.intake_receipt,qa.custody.source_provenance_manifest,qa.custody.source_referral_html,qa.custody.source_public_headers]:body(root,ref)
 if qa.page_coverage!=[1,2,3,4,5]:raise ValueError('Incomplete review pages')
 if [e.row_id for e in errata.entries]!=list(CHANGES):raise ValueError('Only the three declared visual errata permitted')
 for e in errata.entries:
  original=next(r for r in old.rows if r.id==e.row_id).cells[0]
  before,after=CHANGES[e.row_id]
  if e.before!=original.text or e.after!=original.text.replace(before,after):raise ValueError('Unexpected visual correction')
  body(root,e.source_crop)
 if len(grid.rows)!=len(old.rows):raise ValueError('Grid row count changed')
 expected_text=bytearray()
 for original,current in zip(old.rows,grid.rows,strict=True):
  expected=original.model_dump()
  if current.id in CHANGES:
   before,after=CHANGES[current.id];expected['cells'][0]['text']=expected['cells'][0]['text'].replace(before,after)
  for c in expected['cells']:
   c['transcript_start_byte']=len(expected_text);expected_text.extend(c['text'].encode());c['transcript_end_byte']=len(expected_text);expected_text.extend(b'\n')
  if current.model_dump()!=expected:raise ValueError('Row/column/geometry/footnote/blank association differs')
 if expected_text!=body(root,grid.transcript):raise ValueError('Reviewed visual UTF-8 bytes differ')
 for version in (old,grid):
  text=body(root,version.transcript);cursor=0
  for row in version.rows:
   for c in row.cells:
    if c.transcript_start_byte!=cursor or text[c.transcript_start_byte:c.transcript_end_byte]!=c.text.encode():raise ValueError('Transcript offset differs')
    cursor=c.transcript_end_byte+1
  if cursor!=len(text):raise ValueError('Transcript omits/truncates bytes')
  for p in version.pages:
   body(root,p.source_image);body(root,p.native_file)
 if [r.id for r in grid.rows if r.role=='fee_row' and r.cells[2].state=='visibly_blank']!=['P1-PLAN-17','P4-OTHER-01','P4-OTHER-02','P4-OTHER-03','P4-OTHER-04']:raise ValueError('Blank Project Type cells changed')
 with pymupdf.open(root/'source/original.pdf') as pdf:
  if len(pdf)!=5:raise ValueError('PDF page count differs')
  for n,page in enumerate(pdf,1):
   if (page.rect.width,page.rect.height)!=(792,612):raise ValueError('PDF geometry differs')
   if page.get_text('text',sort=False,flags=195)!='':raise ValueError('Expected empty native layer')
   if (root/f'native/page-{n:04}.txt').read_bytes()!=b'':raise ValueError('Native text was invented')
   im=pymupdf.Pixmap(str(root/f'images/page-{n}.png'))
   if (im.width,im.height)!=(2200,1700):raise ValueError('Source image dimensions differ')
 if [x.path for x in qa.native_extraction.page_files]!=[f'native/page-{n:04}.txt' for n in range(1,6)]:raise ValueError('Native page selection differs')
 for ref in qa.native_extraction.page_files:body(root,ref)
 native_expected=b''.join(f'===== PHYSICAL PDF PAGE {n} OF 5 (PACKAGING MARKER; NATIVE TEXT EMPTY) =====\n\n'.encode() for n in range(1,6))
 if body(root,qa.native_extraction.candidate_with_page_markers)!=native_expected:raise ValueError('Empty native candidate packaging differs')
 for name,(page,box) in CROPS.items():
  im=pymupdf.Pixmap(str(root/f'images/page-{page}.png'));observed=pymupdf.Pixmap(str(root/f'crops/{name}.png'));rectangle=pymupdf.IRect(box)
  if not pymupdf.IRect(im.irect).contains(rectangle):raise ValueError('Crop bounds invalid')
  replay=pymupdf.Pixmap(im.colorspace,rectangle,im.alpha);replay.copy(im,rectangle)
  if (replay.width,replay.height,replay.n,replay.samples)!=(observed.width,observed.height,observed.n,observed.samples):raise ValueError('Crop pixels differ')
 ocr_receipt=json.loads(body(root,qa.ocr_comparison.receipt))
 jsonschema.validate(ocr_receipt,json.loads((root/'OCR_COMPARISON_RECEIPT.schema.json').read_bytes()))
 if (ocr_receipt['status']!='machine_ocr_unreviewed' or len(ocr_receipt['prior_failures'])!=2 or ocr_receipt['visual_freeze_sha256']!=INITIAL_SHA):raise ValueError('OCR failure/freeze history differs')
 if sha((root/'tools/apple-vision-ocr').read_bytes())!=ocr_receipt['adapter_sha256']:raise ValueError('OCR adapter differs')
 if sha((root/'tools/apple_vision_ocr.swift').read_bytes())!=ocr_receipt['adapter_source_sha256']:raise ValueError('OCR adapter source differs')
 ocr={};engine_schema=json.loads((root/'ocr/engine-result.schema.json').read_bytes())
 for n,event in enumerate(ocr_receipt['events'],1):
  if event['page']!=n or event['exit_code']!=0 or event['status']!='machine_ocr_unreviewed':raise ValueError('OCR event coverage/status differs')
  b=(root/f'ocr/retry-authorized/page-{n:04}.stdout').read_bytes();stderr=(root/f'ocr/retry-authorized/page-{n:04}.stderr').read_bytes()
  if (sha(b),len(b),sha(stderr),len(stderr))!=(event['stdout_sha256'],event['stdout_bytes'],event['stderr_sha256'],event['stderr_bytes']):raise ValueError('OCR output differs')
  if event['image_sha256']!=sha((root/f'images/page-{n}.png').read_bytes()):raise ValueError('OCR image binding differs')
  if datetime.fromisoformat(event['started_at'])<=datetime.fromisoformat(old.frozen_at):raise ValueError('OCR must follow initial visual freeze')
  parsed=json.loads(b);jsonschema.validate(parsed,engine_schema);ocr[n]=parsed
 if set(ocr)!=set(range(1,6)):raise ValueError('Incomplete OCR pages')
 if sum(len(p['lines']) for p in ocr.values())!=qa.ocr_comparison.engine_observation_count:raise ValueError('OCR observation count differs')
 expected_pairs=[(r.id,c.column) for r in grid.rows if r.role in ['fee_row','footnote','general_note'] for c in r.cells]
 if [(r.row_id,r.column) for r in comp.cells]!=expected_pairs:raise ValueError('Incomplete/duplicate OCR cell comparison')
 for c in comp.cells:
  row=next(r for r in grid.rows if r.id==c.row_id);cell=next(x for x in row.cells if x.column==c.column);x0,y0,x1,y1=cell.pixel_bbox;selected=[]
  for i,line in enumerate(ocr[row.physical_page]['lines']):
   x,y,w,h=line['bbox'];cx=(x+w/2)*2200;cy=(1-y-h/2)*1700
   if x0<=cx<x1 and y0<=cy<y1:selected.append(i)
  text=' '.join(ocr[row.physical_page]['lines'][i]['text'] for i in selected);expected=cell.text+''.join(map(str,cell.superscript_footnotes));same=' '.join(text.split())==' '.join(expected.split())
  if c.physical_page!=row.physical_page or c.ocr_observation_indices!=selected or c.ocr_text!=text or c.visual_text_with_footnote_markers!=expected or c.equal_after_whitespace_collapse!=same:raise ValueError('OCR cell/visual comparison differs')
 if comp.final_differences!=sum(not c.equal_after_whitespace_collapse for c in comp.cells):raise ValueError('OCR disagreement count differs')
 # Stream copied JSONL provenance, never whole-file json.load.
 selected=None
 schema=json.loads((root/'custody/source-provenance.schema.json').read_bytes())
 with (root/'custody/source-provenance.jsonl').open('rb') as f:
  for number,line in enumerate(f,1):
   record=json.loads(line);jsonschema.validate(record,schema)
   if record['source_id']==qa.source_id:
    if selected is not None:raise ValueError('Duplicate source custody')
    selected=(number,line,record)
 if selected is None:raise ValueError('Missing source custody')
 number,line,p=selected
 if number!=1 or sha(line)!=qa.custody.source_provenance_line_sha256 or p['original']['sha256']!=SOURCE_SHA or p['authority_id']!=qa.authority_id:raise ValueError('Source custody binding differs')
 receipt=json.loads(body(root,qa.custody.intake_receipt));matches=[r for r in receipt['intent']['records'] if r['record_id']==qa.source_id]
 if len(matches)!=1:raise ValueError('Intake target count differs')
 r=matches[0]
 if (r['sha256']!=SOURCE_SHA or r['received_at']!=qa.custody.actual_repository_received_at or r['acquisition_method']!='received_review_package' or r['status']!='archived_pending_pipeline'):raise ValueError('Intake/custody claims differ')
 if p['requested_url_claim']!=qa.custody.claimed_source_url or p['final_url_claim']!=qa.custody.claimed_final_url or p['acquisition_started_at_claim']!=qa.custody.claimed_http_acquisition_at:raise ValueError('Claimed acquisition binding differs')
 if sha((root/'custody/SD011-E043.html').read_bytes())!=p['source_referrals'][0]['parent']['sha256'] or sha((root/'custody/SD011-E053.headers.txt').read_bytes())!=p['public_headers']['sha256']:raise ValueError('Referral/header binding differs')
 for ref in inv.files:body(root,ref)
 return {'status':'pass','fee_rows':104,'footnotes':15,'general_notes':3,'native_bytes':0,'ocr_pages':5,'explicit_unresolved_rows':['P3-ENG-14'],'legal_currentness':'not_verified'}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=HERE);args=parser.parse_args()
 print(json.dumps(validate(args.root),sort_keys=True))
