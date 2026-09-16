#!/usr/bin/env python3
"""Read-only offline source QA replay. Never calls a network tool or modifies this package."""
from __future__ import annotations
import argparse,json,math,os,stat,sys
from collections import Counter
from hashlib import sha256
from pathlib import Path,PurePosixPath
import pymupdf,jsonschema
sys.path.insert(0,str(Path(__file__).absolute().parent))
from review_models import Asset,QA,Geometry,Crop,Inventory,Reservation,HTTPResult,Headers,ValidationResult
from row_map import ROWS,TABLES,CONTEXT,GLOBAL,linked_context
SOURCE='e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a'
FIRST='e382da7c1be63d5b7b26be5f0d43d35b1fe55a4486346377fe8895cfbfdbbc97'
def require(value,message):
 if not value:raise ValueError(message)
def ordinary(path:Path,directory=False):
 for parent in [path,*path.parents]:require(not parent.is_symlink(),f'symlink refused: {parent.name}')
 mode=path.stat().st_mode
 require(stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode),'not an ordinary path')
 return path
def safe(root:Path,rel:str):
 p=PurePosixPath(rel)
 require(rel and not p.is_absolute() and '..' not in p.parts and '.' not in p.parts and p.as_posix()==rel and '\\' not in rel,'unsafe path')
 return ordinary(root/rel)
def digest(path):
 h=sha256()
 with path.open('rb') as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:
  require(k not in d,'duplicate JSON key');d[k]=v
 return d
def load(path):return json.loads(path.read_text(),object_pairs_hook=unique)
def check_asset(root,a):
 p=safe(root,a.path);require(p.stat().st_size==a.size_bytes and digest(p)==a.sha256,'asset hash/size mismatch: '+a.path);return p
def pixels(b):return [math.floor(b[0]*200/72),math.floor(b[1]*200/72),math.ceil(b[2]*200/72),math.ceil(b[3]*200/72)]
def validate(root:Path,closed=True):
 root=ordinary(root.absolute(),True)
 require(pymupdf.VersionBind=='1.28.2','native replay requires recorded PyMuPDF 1.28.2')
 inv=Inventory.model_validate(load(safe(root,'FINAL_MANIFEST.json')))
 if closed:
  actual=set()
  for base,dirs,files in os.walk(root,followlinks=False):
   for n in dirs:ordinary(Path(base)/n,True)
   for n in files:
    p=ordinary(Path(base)/n);actual.add(p.relative_to(root).as_posix())
  require(actual=={x.path for x in inv.files}|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'},'closed file inventory mismatch')
 for a in inv.files:check_asset(root,a)
 require(load(safe(root,'FINAL_MANIFEST.schema.json'))==Inventory.model_json_schema(),'manifest schema differs')
 require(load(safe(root,'SOURCE_QA.schema.json'))==QA.model_json_schema(),'QA schema differs')
 q=QA.model_validate(load(safe(root,'SOURCE_QA.json')))
 require(q.source.path=='source/original.pdf' and q.source.size_bytes==258393,'source location/size')
 source=check_asset(root,q.source);require(digest(source)==SOURCE,'source changed')
 require(q.source_first_observations.path=='VISUAL_OBSERVATIONS.json','source-first path')
 first=check_asset(root,q.source_first_observations);require(digest(first)==FIRST,'source-first freeze changed')
 jsonschema.validate(load(first),load(safe(root,'VISUAL_OBSERVATIONS.schema.json')))
 with pymupdf.open(source) as doc:
  require(len(doc)==7 and not doc.is_repaired and not doc.is_encrypted,'invalid source PDF structure')
  require([p.physical_page for p in q.pages]==list(range(1,8)),'page order/scope')
  lines={};used=Counter();native_count=0
  for p in q.pages:
   n=p.physical_page;page=doc[n-1]
   require(p.source_rect_points==list(page.rect)==[0.,0.,612.,792.],'page geometry')
   require(p.native.path==f'native/page-{n:04}.txt' and p.geometry.path==f'native/page-{n:04}.geometry.json' and p.image.path==f'images/page-{n}.png','page evidence identity')
   raw=check_asset(root,p.native).read_bytes();require(raw==page.get_text('text',sort=False).encode(),'native extraction mismatch')
   g=Geometry.model_validate(load(check_asset(root,p.geometry)))
   require(g.page==n and g.native_sha256==digest(root/p.native.path) and g.size_bytes==len(raw),'native geometry binding')
   native_count+=len(raw);expected=[];off=0
   for b in page.get_text('dict',sort=False)['blocks']:
    if b['type']!=0:continue
    for l in b['lines']:
     t=''.join(s['text'] for s in l['spans'])+'\n';end=off+len(t.encode());require(raw[off:end]==t.encode(),'native reconstruction')
     expected.append({'line_id':f'P{n}-L{len(expected)+1:03}','text':t,'start':off,'end':end,'bbox':list(l['bbox']),'spans':[{'text':s['text'],'bbox':list(s['bbox']),'font':s['font'],'flags':s['flags'],'size':s['size']} for s in l['spans']]});off=end
   require([l.model_dump() for l in g.lines]==expected and off==len(raw),'native geometry or byte bounds changed')
   require(p.native_line_count==len(expected),'line count mismatch')
   im=pymupdf.Pixmap(str(check_asset(root,p.image)));require(p.image_dimensions==[im.width,im.height]==[1700,2200],'image dimensions')
   require(load(first)['images'][p.image.path]==p.image.sha256,'initial source image binding changed')
   for l in g.lines:lines[l.line_id]=l
  require(native_count==q.native_byte_count==14423 and len(lines)==410,'full native scope changed')
 def check_part(part,ids):
  require(part.line_ids==ids,'source line associations changed')
  ls=[lines[x] for x in ids]
  require(part.exact_native_text==''.join(l.text for l in ls),'native wording changed')
  require(part.native_ranges==[[l.start,l.end] for l in ls],'native byte offsets changed')
  require(part.pdf_bboxes==[l.bbox for l in ls] and part.pixel_bboxes==[pixels(l.bbox) for l in ls],'geometry/pixel binding changed')
  for l in ls:used[l.line_id]+=1
 counts=Counter()
 for row,(p,t,ll,rr) in zip(q.fee_rows,ROWS,strict=True):
  counts[p,t]+=1
  require(row.row_id==f'P{p}-{t.upper()}-{counts[p,t]:02}' and row.table_id==t and row.physical_page==p,'fee row order/identity changed')
  require(row.label.role=='label' and row.fee_as_printed.role=='fee_as_printed','column role swapped')
  check_part(row.label,[f'P{p}-L{x:03}' for x in ll]);check_part(row.fee_as_printed,[f'P{p}-L{x:03}' for x in rr])
  require(row.global_context_ids==GLOBAL,'missing global qualifications')
  notes,defs=linked_context(p,t,ll);require(row.table_context_ids==notes and row.definition_ids==defs,'missing linked note or definition')
 blocks={b.block_id:b for b in q.blocks};require(len(blocks)==len(q.blocks),'duplicate block')
 expected_ids=set(CONTEXT)|{f'HEADING-{t.upper()}' for t in TABLES}
 for bid,(kind,parts) in CONTEXT.items():
  require(bid in blocks,'missing context');b=blocks[bid]
  require(b.kind==kind and len(b.parts)==len(parts),'context kind/continuation changed')
  for part,(p,a,z) in zip(b.parts,parts,strict=True):
   require(part.page==p,'context page changed');check_part(part,[f'P{p}-L{x:03}' for x in range(a,z+1)])
 for t,(p,n) in TABLES.items():
  b=blocks[f'HEADING-{t.upper()}'];require(b.kind=='heading' and len(b.parts)==1 and b.parts[0].page==p,'table heading changed');check_part(b.parts[0],[f'P{p}-L{n:03}'])
 for lid,l in lines.items():
  if used[lid]:continue
  bid='UNASSIGNED-'+lid;expected_ids.add(bid);require(bid in blocks,'missing footer/whitespace');b=blocks[bid];p=int(lid[1:lid.index('-')]);kind='native_whitespace' if not l.text.strip() else 'footer'
  require(b.kind==kind and len(b.parts)==1 and b.parts[0].page==p,'footer/whitespace class changed');check_part(b.parts[0],[lid])
 require(set(blocks)==expected_ids and set(used)==set(lines) and set(used.values())=={1},'native lines not partitioned exactly once')
 require([t.table_id for t in q.tables]==list(TABLES),'table order changed')
 for t in q.tables:
  require(t.heading_block_id==f'HEADING-{t.table_id.upper()}' and t.row_ids==[x.row_id for x in q.fee_rows if x.table_id==t.table_id] and t.page_order==sorted({x.physical_page for x in q.fee_rows if x.table_id==t.table_id}),'table row/page continuation changed')
 known=set(blocks)|{x.row_id for x in q.fee_rows}
 require(all(set(x.global_context_ids+x.table_context_ids+x.definition_ids)<=known for x in q.fee_rows),'dangling context')
 require(len([b for b in q.blocks if b.kind=='definition'])==13 and len([b for b in q.blocks if b.kind=='table_note'])==3,'context scope changed')
 crops=[Crop.model_validate(x) for x in load(safe(root,'CROPS.json'))];require(len(crops)==12 and len({c.path for c in crops})==12,'crop scope')
 for c in crops:
  parent=q.pages[c.page-1];require(c.parent_sha256==parent.image.sha256,'crop parent mismatch');im=pymupdf.Pixmap(str(root/parent.image.path));box=pymupdf.IRect(c.pixel_bbox)
  require(pymupdf.IRect(im.irect).contains(box) and not box.is_empty,'crop bounds');out=pymupdf.Pixmap(im.colorspace,box,im.alpha);out.copy(im,box);out.set_origin(0,0)
  raw=safe(root,c.path).read_bytes();require(sha256(raw).hexdigest()==c.sha256 and raw==out.tobytes('png'),'crop reproduction mismatch')
 # Exact response provenance; parent plan paths are retained claims and never opened.
 for a in q.provenance.receipts:check_asset(root,a)
 require([a.path for a in q.provenance.receipts]==['custody/reservation.json','custody/result.json','custody/public-headers.json','custody/body.bin','custody/plan.json'],'custody scope')
 res=Reservation.model_validate(load(root/'custody/reservation.json'));result=HTTPResult.model_validate(load(root/'custody/result.json'));headers=Headers.model_validate(load(root/'custody/public-headers.json'));plan=load(root/'custody/plan.json')
 require(result.reservation_sha256==digest(root/'custody/reservation.json') and res.plan_sha256==digest(root/'custody/plan.json'),'reservation/plan digest')
 require(res.reserved_at==q.provenance.request_started_at and result.finished_at==q.provenance.response_finished_at,'acquisition timing changed')
 require(res.url==headers.request_url==q.provenance.official_url and [x for x in plan['targets'] if x['source_id']=='SD014-02'][0]['url']==res.url,'source URL identity changed')
 require(result.body.path=='events/0002/body.bin' and result.body.sha256==digest(root/'custody/body.bin')==SOURCE and result.body.size_bytes==258393,'response/source mismatch')
 require(result.public_headers.path=='events/0002/public-headers.json' and result.public_headers.sha256==digest(root/'custody/public-headers.json') and result.public_headers.size_bytes==(root/'custody/public-headers.json').stat().st_size,'headers hash/size')
 require(set(headers.headers)=={'content-length','content-type','last-modified','date','cache-control'} and headers.headers['content-length']=='258393' and headers.headers['content-type']=='application/pdf' and not headers.rejected_fields,'public header policy')
 return ValidationResult(status='validated_source_qa_no_currentness_promotion',source_sha256=SOURCE,physical_pages=7,fee_rows=128,tables=9,definition_records=13,table_notes=3,native_bytes=14423,native_lines=410,crops=12,files_verified=len(inv.files),legal_currentness='not_verified')
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).absolute().parent);a=p.parse_args()
 try:print(validate(a.root).model_dump_json(indent=2))
 except (OSError,ValueError,KeyError,TypeError,IndexError) as e:raise SystemExit('Validation failed: '+str(e))
if __name__=='__main__':main()
