"""Read-only portable original/source-chain/native verifier and literal page search."""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit,parse_qs
sys.dont_write_bytecode = True
import pymupdf
from models import (Ref,Closure,Package,Catalog,Source,Page,Result,Reservation,
                    PriorIndexRecord,Verification,Query,Hit)
MAX_TOTAL=50_000_000
MAX_MEMBER=15_000_000

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def safe_path(value:str)->str:
    p=PurePosixPath(value)
    if p.is_absolute() or not value or '..' in p.parts or '\\' in value or str(p)!=value:
        raise ValueError('Unsafe relative member path')
    return value

def load(root:Path,pin:str)->dict[str,bytes]:
    if not re.fullmatch('[a-f0-9]{64}',pin):raise ValueError('External manifest SHA256 required')
    if any(p.is_symlink() for p in [root,*root.parents]):raise ValueError('Symlink root')
    raw=(root/'MANIFEST.json').read_bytes()
    if len(raw)>1_000_000 or sha(raw)!=pin:raise ValueError('Manifest pin mismatch')
    m=Closure.model_validate_json(raw,strict=True)
    paths=[safe_path(r.path) for r in m.files]
    if len(paths)!=len(set(paths)) or 'MANIFEST.json' in paths:raise ValueError('Duplicate/self member')
    actual=set()
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink member')
        if p.is_file():actual.add(p.relative_to(root).as_posix())
    if actual!=set(paths)|{'MANIFEST.json'}:raise ValueError('Closed membership differs')
    if sum(r.bytes for r in m.files)+len(raw)>MAX_TOTAL:raise ValueError('Package byte cap')
    out={}
    for r in m.files:
        if r.bytes>MAX_MEMBER:raise ValueError('Member byte cap')
        b=(root/r.path).read_bytes()
        if len(b)!=r.bytes or sha(b)!=r.sha256:raise ValueError('Member hash/size differs: '+r.path)
        out[r.path]=b
    return out

def rows(data:bytes,model):
    return [model.model_validate_json(line,strict=True) for line in data.splitlines() if line]
def verify(root:Path,pin:str):
    fs=load(root,pin)
    p=Package.model_validate_json(fs['PACKAGE.json'],strict=True)
    def bound(r:Ref):
        safe_path(r.path); b=fs[r.path]
        if sha(b)!=r.sha256 or len(b)!=r.bytes:raise ValueError('Record reference differs')
        return b
    cat=Catalog.model_validate_json(bound(p.catalog),strict=True)
    old=rows(bound(p.prior_index),PriorIndexRecord)
    if cat.inherited_index_path!=p.prior_index.path or cat.inherited_index_sha256!=p.prior_index.sha256 or cat.inherited_index_records!=len(old):raise ValueError('Prior index binding')
    if len(cat.rows)!=21 or len({r.citation for r in cat.rows})!=21:raise ValueError('Catalog B/D identities')
    oldcit={r.citation for r in old}
    for row in cat.rows:
        if row.inherited_index_match!=(row.citation in oldcit):raise ValueError('Inherited match differs')
    sr=rows(bound(p.source_records),Source);pg=rows(bound(p.page_records),Page)
    if {s.citation for s in sr}!={r.citation for r in cat.rows} or len(sr)!=21:raise ValueError('Exact complete 2026 B/D source-set differs')
    if len({s.original.sha256 for s in sr})!=len(sr):raise ValueError('Duplicate original bytes')
    receipts={};batch_counts=defaultdict(int);batch_bytes=defaultdict(int)
    for name,b in fs.items():
        if name.startswith('batches/') and name.endswith('/RESULT.json'):
            r=Result.model_validate_json(b,strict=True); resname=str(PurePosixPath(name).with_name('RESERVATION.json'));res=Reservation.model_validate_json(fs[resname],strict=True)
            if r.reservation_sha256!=sha(fs[resname]) or r.requested_url!=res.requested_url or r.sequence!=res.sequence:raise ValueError('Reservation binding differs')
            if r.started_at!=res.started_at or r.finished_at<r.started_at or r.finished_at.isoformat()>'2026-10-05T21:20:00+00:00':raise ValueError('Response chronology differs')
            if not r.complete_transfer or r.curl_exit!=0 or r.observed_final_url!=r.requested_url:raise ValueError('Incomplete/redirected transport claim')
            bodyname=str(PurePosixPath(name).with_name(safe_path(r.body.path)));body=fs[bodyname]
            if len(body)!=r.body.bytes or sha(body)!=r.body.sha256 or r.charged_bytes<len(body):raise ValueError('Body/charge binding differs')
            batch=name.split('/')[1];batch_counts[batch]+=1;batch_bytes[batch]+=r.charged_bytes
            receipts[name]=(r,res)
    for batch,limits in p.batch_limits.items():
        if batch_counts[batch]>limits[0] or batch_bytes[batch]>limits[1]:raise ValueError('Batch caps exceeded')
    if set(batch_counts)!=set(p.batch_limits) or sum(batch_counts.values())!=p.metered_http_requests or sum(batch_bytes.values())!=p.charged_response_bytes:raise ValueError('Request accounting differs')
    if p.batch_limits!={'new13':[35,100000000],'current8':[20,30000000]}:raise ValueError('Authorized batch ceilings differ')
    pages={}
    for x in pg:
        key=(x.citation,x.physical_page)
        if key in pages:raise ValueError('Duplicate native page')
        pages[key]=x
    expectedkeys=set();nbytes=0
    for s in sr:
        row=cat.rows[s.catalog_row_index]
        if s.citation!=row.citation or s.observed_catalog_title!=row.displayed_title or s.observed_catalog_date!=row.displayed_date or s.delegated_view_url!=row.observed_href or s.official_catalog_url!=cat.source_page:raise ValueError('Catalog row binding differs')
        fid=re.fullmatch(r'https://drive.google.com/file/d/([\w-]+)/view(?:\?usp=sharing)?',row.observed_href).group(1)
        if row.direct_download_url!=f'https://drive.google.com/uc?export=download&id={fid}':raise ValueError('Derived download route differs')
        if s.final_download_url!=f'https://drive.usercontent.google.com/download?id={fid}&export=download':raise ValueError('Final source file ID differs')
        bound(s.receipt);r,res=receipts[s.receipt.path]
        if r.http_status!=200 or r.detected_format!='pdf' or r.requested_url!=s.final_download_url or r.finished_at!=s.source_received_at:raise ValueError('Final PDF receipt differs')
        if s.original.path!=str(PurePosixPath(s.receipt.path).with_name('response.body')) or s.original.sha256!=r.body.sha256:raise ValueError('Original receipt association differs')
        batch=s.receipt.path.split('/')[1]
        parent=res.parent_evidence.split('#/safe_headers/location')[0]
        if parent==res.parent_evidence:raise ValueError('Exact observed redirect parent required')
        parname='batches/'+batch+'/'+safe_path(parent);pr,prs=receipts[parname]
        if pr.http_status not in {301,302,303,307,308} or pr.safe_headers.get('location')!=s.final_download_url:raise ValueError('Redirect source association differs')
        if pr.requested_url!=row.direct_download_url:
            # Only B002 uses the literal download association from its retained public view.
            if s.citation!='B 2026 002':raise ValueError('Unexpected alternate download route')
            viewname='batches/new13/requests/0001_B2026002-view/RESULT.json';vr,vres=receipts[viewname]
            viewbody=fs[str(PurePosixPath(viewname).with_name('response.body'))].decode('utf8')
            candidates=[json.loads('"'+v+'"') for v in re.findall(r'"(https://drive.usercontent.google.com/uc[^"\r\n]+)"',viewbody)]
            if vr.requested_url!=row.observed_href or vr.http_status!=200 or pr.requested_url not in candidates:raise ValueError('Public view download association differs')
        original=bound(s.original)
        if not original.startswith(b'%PDF-'):raise ValueError('Original PDF signature missing')
        texts=[]
        with pymupdf.open(stream=original,filetype='pdf') as doc:
            if doc.is_encrypted or doc.is_repaired or len(doc)!=s.physical_pages:raise ValueError('PDF structural/source-page mismatch')
            for num,page in enumerate(doc,1):
                key=(s.citation,num);expectedkeys.add(key);meta=pages[key]
                text=page.get_text('text',sort=False);tb=text.encode();texts.append(text)
                if meta.source_sha256!=s.original.sha256 or bound(meta.native_text)!=tb or meta.character_count!=len(text):raise ValueError('Native direct replay differs')
                nbytes+=len(tb)
        citation_found=bool(re.search(r'\s+'.join(re.escape(x) for x in s.citation.split()),'\n'.join(texts)))
        if s.native_pages!=len(texts) or s.empty_native_pages!=sum(not t.strip() for t in texts) or s.native_bytes!=sum(len(t.encode()) for t in texts) or s.citation_string_observed_in_native!=citation_found:raise ValueError('Native count/citation evidence differs')
    if set(pages)!=expectedkeys or len(sr)!=p.source_pdf_count or len(pg)!=p.physical_page_count or nbytes!=p.native_bytes:raise ValueError('Package totals differ')
    return Verification(pdf_originals=len(sr),physical_pages=len(pg),native_bytes=nbytes,metered_http_requests=p.metered_http_requests),fs,sr,pg

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['verify','query']);ap.add_argument('--root',type=Path,default=Path(__file__).parent);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--mode',choices=['citation','phrase']);ap.add_argument('--text');ap.add_argument('--limit',type=int,default=3);a=ap.parse_args()
    result,fs,sources,pages=verify(a.root,a.manifest_sha256)
    if a.command=='query':
        if a.mode is None or a.text is None or not a.text.strip() or len(a.text)>500 or not 1<=a.limit<=20:raise ValueError('Bounded mode/text/limit required')
        src={s.citation:s for s in sources};hits=[]
        for page in pages:
            text=fs[page.native_text.path].decode('utf8');match=page.citation.casefold()==a.text.casefold() if a.mode=='citation' else a.text.casefold() in text.casefold()
            if match:hits.append(Hit(citation=page.citation,physical_page=page.physical_page,original_sha256=page.source_sha256,source_url=src[page.citation].final_download_url,native_text=text))
        result=Query(mode=a.mode,text=a.text,total_matching_pages=len(hits),returned_pages=min(len(hits),a.limit),truncated=len(hits)>a.limit,hits=hits[:a.limit])
    print(result.model_dump_json(indent=2))
if __name__=='__main__':main()
