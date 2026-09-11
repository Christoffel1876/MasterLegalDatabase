"""Portable read-only native, glyph, column, condition and custody validation."""
from pathlib import Path
from html.parser import HTMLParser
from html import unescape
import hashlib,json,sys
import pymupdf,jsonschema
from review_models import *
from row_specifications import TABLES
B=Path(__file__).resolve().parent
SHA='af11318af2ce3ea5e4b1af313f348ab851a855a76418e3878d1a166c084dadb6'
def need(ok,note):
 if not ok:raise ValueError(note)
def h(b):return hashlib.sha256(b).hexdigest()
def file(rel):
 Asset(path=rel,sha256='0'*64,bytes=0);p=B/rel
 for q in [p,*p.parents]:need(not q.is_symlink(),'symlink reference')
 need(p.is_file(),'missing file '+rel);return p

def read(a):
 b=file(a.path).read_bytes();need(len(b)==a.bytes and h(b)==a.sha256,'file mismatch '+a.path);return b

def spans(x):
 if isinstance(x,dict):
  if set(x)=={'page','start','end','text','sha256'}:yield Span.model_validate(x)
  else:
   for y in x.values():yield from spans(y)
 elif isinstance(x,list):
  for y in x:yield from spans(y)

def box_for(s,glyphs):
 boxes=[b for a,z,c,b in glyphs[s.page] if a>=s.start and z<=s.end and c.strip()]
 return (min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)) if boxes else None

def content(r,native,glyphs):
 need(r.source.sha256==SHA,'wrong source');need(len(r.rows)==77 and len(r.tables)==17,'row/table truncation');need(len(r.contexts)==30 and len(r.observations)==9,'context/observation truncation')
 for s in spans(r.model_dump()):need(native[s.page][s.start:s.end]==s.text.encode(),'native span mismatch')
 for p in r.pages:
  off=0
  for i,l in enumerate(p.lines,1):
   need(l.number==i and l.evidence.page==p.number and l.evidence.start==off,'line sequence/gap');off=l.evidence.end
  need(off==len(native[p.number]),'native page truncation')
 need(r.native_bytes==13127 and read(r.candidate)==b''.join(native[n] for n in [1,2,3]),'candidate native bytes')
 ts={t.id:t for t in r.tables};rs={x.id:x for x in r.rows};contexts={c.id:c for c in r.contexts}
 for tid,n,title,defs in TABLES:
  t=ts[tid];need(t.page==n and t.title==title,'table ownership/label');need(t.row_ids==[f'{tid}-R{i:02d}' for i in range(1,len(defs)+1)],'table row list')
  three=n==1 or tid in ['P2-APPLICATIONS','P2-CONTINUATION'];cols=['source_item','2009_fee','2017_18_fee'] if three else ['source_item','fee_as_printed','conditions_as_printed'];need(t.columns==cols,'historical columns changed')
  for idx,(a,z,v1,v2) in enumerate(defs,1):
   row=rs[f'{tid}-R{idx:02d}'];need(row.source_lines==(a,z) and row.order==idx,'row source line mapping');ls=r.pages[n-1].lines;expected=''.join(l.evidence.text for l in ls[a-1:z]);need(row.evidence.start==ls[a-1].evidence.start and row.evidence.text==expected,'wrong source row');s=expected
   if three:
    j=s.rindex(v2);i=s.rindex(v1,0,j);defs2=[(0,s[:i]),(i,v1),(j,v2)]
   elif v1 is not None:
    i=s.rindex(v1);j=i+len(v1);defs2=[(0,s[:i]),(i,v1),(j,s[j:])]
   else:
    i=s.index('CHECKS');defs2=[(0,s[:i]),(0,None),(i,s[i:])]
   for c,(at,value) in zip(row.cells,defs2):
    need(c.native_text==value,'column value/condition changed')
    if value is None:need(c.glyph_bbox is None and not c.evidence,'invented absent fee')
    else:
     need(len(c.evidence)==1,'unexpected cell partition');e=c.evidence[0];need(e.start==row.evidence.start+len(s[:at].encode()) and e.text==value,'cell moved to different occurrence');need(c.glyph_bbox==box_for(e,glyphs),'cell glyph geometry')
   if three:
    left=row.cells[1].glyph_bbox;right=row.cells[2].glyph_bbox
    need(left is not None and right is not None and left[2]<=right[0]+.5,'reversed fee columns')
    need(max(left[1],right[1])<=min(left[3],right[3]),'fee values not on corresponding visual row')
 # Check every original nonblank line belongs to a row or context.
 evidence=[x.evidence for x in r.rows]+[x.evidence for x in r.contexts]
 for p in r.pages:
  for l in p.lines:
   if l.evidence.text.strip():need(any(s.page==p.number and s.start<=l.evidence.start and s.end>=l.evidence.end for s in evidence),'unaccounted source line')
 required_rows={'P1-GENERAL-R05':{'C-APPEAL'},'P1-GENERAL-R06':{'C-CONDITIONAL'},'P1-GENERAL-R07':{'C-CONDITIONAL'},'P1-GENERAL-R08':{'C-CONDITIONAL'},'P1-MAJOR-R02':{'C-ACREAGE'},'P1-PUD-R02':{'C-ACREAGE'},'P1-ACREAGE-R08':{'C-ACREAGE-BASE'}}
 for rid,ids in required_rows.items():need(ids<=set(rs[rid].parent_context_ids),'lost parent/refund/acreage condition')
 required_tables={'P2-CONTINUATION':{'C-YEARS','C-POSTCARDS','C-EXTRAORDINARY'},'P2-SCHOOL':{'C-CONTINUING','C-SCHOOL-EXPIRY'},'P2-TIF':{'C-TIF','C-CONTINUING'},'P2-PUBLICATIONS':{'C-PRINT-PRICE'},'P3-IMAGERY':{'C-IMAGERY'},'P3-CGS':{'C-CGS-PAYEE'}}
 for tid,ids in required_tables.items():need(ids<=set(ts[tid].context_ids),'lost table condition/payee')
 for tid,n,_,_ in TABLES:
  if n==1:need({'C-YEARS','C-EXTRAORDINARY'}<=set(ts[tid].context_ids),'waiver qualification lost')
 for rid in ts['P3-CGS'].row_ids:
  need('Paid with the submittal' in rs[rid].cells[0].native_text and 'When CGS bills applicant the fee may be larger' in rs[rid].cells[2].native_text,'lost CGS payment/uncapped-bill qualifier')
 need('1 October 2020' in contexts['C-SCHOOL-EXPIRY'].evidence.text,'PDF date changed');need(rs['P3-RECORDING-R01'].cells[1].native_text is None,'unknown recording fee became zero')
 # The appeal marker is graphically raised; native275.001 is never silently parsed as money.
 e=rs['P1-GENERAL-R05'].cells[2].evidence[0];gs=[(a,z,c,b) for a,z,c,b in glyphs[1] if a>=e.start and z<=e.end];need(''.join(c for _,_,c,_ in gs)=='275.001','appeal marker lost');need(gs[-1][3][1]<gs[-2][3][1],'superscript marker geometry missing')

class HTMLText(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.parts=[];self.links=[]
 def handle_starttag(self,t,a):
  if t in ['script','style']:self.skip+=1
  if t=='a':self.links.extend(v for k,v in a if k=='href' and v)
 def handle_endtag(self,t):
  if t in ['script','style']:self.skip=max(0,self.skip-1)
 def handle_data(self,s):
  if not self.skip:self.parts.append(s)

def validate():
 inv=Inventory.model_validate_json(file('evidence-manifest.json').read_bytes());actual={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()};need(actual=={a.path for a in inv.files}|{'evidence-manifest.json'},'inventory omission/extra')
 for a in inv.files:read(a)
 r=Review.model_validate_json(file('SOURCE_REVIEW.json').read_bytes());schema=json.loads(file('SOURCE_REVIEW.schema.json').read_text());need(schema==Review.model_json_schema(),'schema drift');jsonschema.Draft202012Validator(schema).validate(r.model_dump(mode='json'))
 source=read(r.source);need(source.startswith(b'%PDF-') and source.rstrip().endswith(b'%%EOF'),'PDF boundaries');d=pymupdf.open(stream=source,filetype='pdf');need(len(d)==3 and not d.is_repaired and not d.is_encrypted,'PDF structure');need(pymupdf.VersionBind==r.engine_version,'exact renderer version required');native={};glyphs={}
 for p in r.pages:
  n=p.number;native[n]=read(p.native);need(d[n-1].get_text('text',flags=195,sort=False).encode()==native[n],'native reproduction');lay=Layout.model_validate_json(read(p.layout));need(lay.source_sha256==SHA and lay.page==n and lay.native_sha256==p.native.sha256,'layout identity');rd=d[n-1].get_text('rawdict',flags=195,sort=False);need(json.loads(json.dumps(rd))==lay.rawdict,'rawdict reproduction');gs=[];off=0;ls=[]
  for bl in rd['blocks']:
   for line in bl.get('lines',[]):
    chars=[c for sp in line['spans'] for c in sp['chars']];txt=''.join(c['c'] for c in chars)+'\n';ls.append((txt,tuple(line['bbox'])))
    for c in chars:gs.append((off,off+len(c['c'].encode()),c['c'],tuple(c['bbox'])));off+=len(c['c'].encode())
    off+=1
  glyphs[n]=gs;need([(l.evidence.text,l.bbox) for l in p.lines]==ls,'native line geometry');need(d[n-1].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).tobytes('png')==read(p.image),'full PNG reproduction')
 for c in r.crops:need(d[c.page-1].get_pixmap(matrix=pymupdf.Matrix(c.scale,c.scale),clip=pymupdf.Rect(c.clip),alpha=False).tobytes('png')==read(c.image),'crop reproduction')
 ev=json.loads(file('custody/E004-event.json').read_text());m=json.loads(file('custody/E004-curl-metadata.json').read_text());need(ev['requested_url']==r.source_url and ev['body_sha256']==SHA and ev['body_bytes']==r.source.bytes,'source response binding');need(ev['completed_at']==r.acquired_at.isoformat().replace('+00:00','Z'),'source receipt clock');need(m['http_code']==200 and m['ssl_verify_result']==0 and m['num_redirects']==0,'HTTP/TLS/redirect evidence')
 he=json.loads(file('custody/E001-event.json').read_text());hp=HTMLText();hp.feed(file('custody/E001-body.bin').read_text());visible=' '.join(' '.join(hp.parts).split());need(r.source_url in hp.links or r.source_url.removeprefix('https://www.mesacounty.us') in hp.links,'missing official PDF link')
 for claim in r.html_claims:
  body=read(claim.source);text=read(claim.snapshot_text);need(h(body)==he['body_sha256'] and claim.source_url==he['requested_url'],'HTML source binding');need(text[claim.start_byte:claim.end_byte]==claim.exact_claim.encode() and h(claim.exact_claim.encode())==claim.claim_sha256,'HTML claim bytes');need(' '.join(claim.exact_claim.split()) in visible,'claim not in retained HTML text')
 need(any('1 October 2022' in c.exact_claim for c in r.html_claims),'separate HTML expiration lost');content(r,native,glyphs)
 rejected=[]
 def negative(name,change):
  v=r.model_dump(mode='json');change(v)
  try:rr=Review.model_validate_json(json.dumps(v));content(rr,native,glyphs)
  except (ValueError,KeyError,IndexError):rejected.append(name)
  else:raise ValueError('tamper accepted '+name)
 negative('missing_page',lambda x:x['pages'].pop())
 negative('missing_fee_row',lambda x:x['rows'].pop())
 negative('swapped_year_columns',lambda x:x['tables'][0]['columns'].reverse())
 negative('lost_appeal_refund',lambda x:x['rows'][4].update(parent_context_ids=[]))
 negative('lost_extraordinary_costs',lambda x:x['tables'][0].update(context_ids=[]))
 negative('source_expiration_corrected',lambda x:next(c for c in x['contexts'] if c['id']=='C-SCHOOL-EXPIRY')['evidence'].update(text='expires2022'))
 negative('unknown_recording_fee_zero',lambda x:x['rows'][-1]['cells'][1].update(native_text='0.00'))
 negative('legal_currentness_promoted',lambda x:x.update(legal_currentness='verified'))
 sys.stdout.write(json.dumps({'passed':True,'source_sha256':SHA,'pages':3,'native_bytes':13127,'native_byte_changes':0,'source_lines':201,'tables':17,'source_rows':77,'cells':231,'contexts':30,'observations':9,'html_claims':2,'negative_checks_rejected':rejected,'scope':'source byte/geometry/association review only; legal currentness and unresolved2020/2022 conflict unchanged'},indent=2)+'\n')
if __name__=='__main__':validate()
