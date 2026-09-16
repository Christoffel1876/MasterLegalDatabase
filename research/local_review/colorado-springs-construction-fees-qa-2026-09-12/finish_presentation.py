from pathlib import Path
import json,pymupdf,shutil
from hashlib import sha256
from review_models import QA,Crop
r=Path(__file__).resolve().parent
p=r/'CROPS.json';pre=r/'preparation-preimages'/sha256(p.read_bytes()).hexdigest();pre.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,pre/p.name)
src=r/'images/page-2.png';im=pymupdf.Pixmap(str(src));b=[185,1130,1545,1290];box=pymupdf.IRect(b);c=pymupdf.Pixmap(im.colorspace,box,im.alpha);c.copy(im,box);c.set_origin(0,0);out=r/'crops/p2-a4-actual.png';c.save(str(out))
crops=json.loads(p.read_text());crops.append(Crop(path='crops/p2-a4-actual.png',page=2,pixel_bbox=b,parent_sha256=sha256(src.read_bytes()).hexdigest(),sha256=sha256(out.read_bytes()).hexdigest()).model_dump());p.write_text(json.dumps(crops,indent=2)+'\n')
q=QA.model_validate_json((r/'SOURCE_QA.json').read_text())
s=['---','title: Colorado Springs Construction Services fee schedule source QA','review_type: Atlas source-first image and native-association review','source_id: SD014-02','authority_id: CO-MUNICIPAL-COLORADO_SPRINGS','legal_currentness: not_verified','---','','Seven physical pages and all 128 fee rows were directly reviewed. All 14,423 native UTF-8 bytes remain unchanged; 410 native lines are bound to page geometry and original-image pixels. This readable view collapses only surrounding layout whitespace and uses line breaks within cells. SOURCE_QA.json and native files preserve exact characters and byte offsets.','','The City fire department is the issuer. The PPRBD collection role remains in its complete definition below. “Effective 07/01/2026” is a printed claim, not independently established legal currentness or adoption.','','Every fee row links the complete global plan-review note, implementation statement, other-schedule reference, and technology-fee row. The linked table notes and definitions must accompany any source-only reuse; links retain qualifications without deciding applicability.','']
for t in q.tables:
 heading=next(b for b in q.blocks if b.block_id==t.heading_block_id).parts[0].exact_native_text.strip();s+=['## '+heading,'',f"Physical pages: {', '.join(map(str,t.page_order))}. Column roles below are visually observed; the source does not print separate description/fee column headings.",'','| Record | Page | Source description | Fee as printed |','|---|---:|---|---|']
 for x in q.fee_rows:
  if x.table_id!=t.table_id:continue
  def fmt(v):return '<br>'.join(z.strip() for z in v.strip().splitlines()).replace('|','\\|')
  s.append(f'| {x.row_id} | {x.physical_page} | {fmt(x.label.exact_native_text)} | {fmt(x.fee_as_printed.exact_native_text)} |')
 s.append('')
s+=['## Complete notes, definitions and qualifications','']
for b in q.blocks:
 if b.kind not in {'definition','table_note','general_note','implementation','other_schedule_reference','printed_date'}:continue
 s += ['### '+b.block_id,'']
 for part in b.parts:s += [f'Physical page {part.page}; native lines {", ".join(part.line_ids)}.','','```text',part.exact_native_text.rstrip('\n'),'```','']
 for n in b.notes:s += [n,'']
s+=['## Source anomalies and limits','']
for x in q.source_anomalies+q.limits:s+=['- '+x]
s+=['','The initial source-first observations are preserved verbatim as working notes. They abbreviate labels and values and are not a substitute for this complete byte-bound grid. No native corrections were made. Twelve retained crops include the originally mispositioned A-4 crop and the subsequent correctly positioned crop; neither was overwritten.','']
(r/'SOURCE_QA.md').write_text('\n'.join(s))
