"""Offline custody, render and literal-review closure; optional pinned Git replay."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import jsonschema
import pymupdf
from models import Access,Comparison,Manifest,Render,Review
from build_review import Links,P1,P2
ROOT=Path(__file__).resolve().parent
PDF_SHA='754e98fb7908b66e54a192cefca9817f7bb4cf2a428cf7c469d59f7cfdcdf427'
HTML_SHA='656702af12d7746320c1ef482396318b5b7e01850f805126009d8d7d9bf16345'
PDFTOPPM='/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'

def digest(raw: bytes) -> str:return sha256(raw).hexdigest()

def checked(asset,data):
    raw=data[asset.path]
    if (digest(raw),len(raw))!=(asset.sha256,asset.size_bytes):raise ValueError('Asset differs: '+asset.path)
    return raw

def typed(name,cls,data):
    item=cls.model_validate_json(data[name+'.json'])
    jsonschema.validate(item.model_dump(mode='json'),json.loads(data[name+'.schema.json']))
    return item

def leaves(v):
    if isinstance(v,dict):
        for x in v.values():yield from leaves(x)
    elif isinstance(v,list):
        for x in v:yield from leaves(x)
    elif isinstance(v,str):yield v

def content(data):
    review=typed('SOURCE_REVIEW',Review,data);access=typed('COMBINED_ACCESS',Access,data)
    render=typed('RENDER',Render,data);comparison=typed('COMPARISON',Comparison,data)
    pdf=checked(review.source,data);html=checked(review.referring_html,data)
    if digest(pdf)!=PDF_SHA or digest(html)!=HTML_SHA:raise ValueError('Wrong originals')
    if pdf!=data['curl-event-04.body'] or html!=data['curl-event-03.body']:raise ValueError('Response copy differs')
    if [e.sequence for e in access.events]!=[1,2,3,4]:raise ValueError('Attempt order differs')
    if [e.status for e in access.events]!=[None,None,200,200]:raise ValueError('Status differs')
    if [e.outcome for e in access.events]!=['failed','failed','received','received']:raise ValueError('Outcome differs')
    total=0
    for e in access.events:
        if not e.reserved_at<=e.started_at<=e.finished_at:raise ValueError('Invalid event time')
        if e.body:
            raw=checked(e.body,data);total+=len(raw)
            if len(raw)>10485760 or not e.complete:raise ValueError('Response cap/completeness differs')
        if e.redirect_location is not None:raise ValueError('Unexpected redirect')
        if any(k.lower() in {'set-cookie','cookie','authorization','proxy-authorization'} for k in e.headers):raise ValueError('Private header value retained')
    if total!=316142 or access.retained_body_bytes!=total or access.deliberate_attempts!=4 or access.distinct_targets!=2:raise ValueError('Budget accounting differs')
    if len({e.requested_url for e in access.events})!=2:raise ValueError('Distinct target count differs')
    parser=Links();parser.feed(html.decode())
    if parser.found!=[(review.referring_href,review.referring_anchor_text)]:raise ValueError('Referral differs')
    if [p.physical_page for p in review.pages]!=[1,2] or [p.reviewed_text for p in review.pages]!=[P1,P2]:raise ValueError('Literal transcript differs')
    if P1.count('WHEREAS,')!=9 or P2.count('BE IT FURTHER RESOLVED')!=5:raise ValueError('Paragraph coverage differs')
    with pymupdf.open(stream=pdf,filetype='pdf') as original:
        if original.page_count!=2:raise ValueError('PDF count differs')
        for page,physical,dims in zip(review.pages,original,[(2576,3319),(2588,3334)]):
            native=checked(page.native,data)
            if native!=b'' or physical.get_text('text',flags=195,sort=False).encode()!=native:raise ValueError('Native empty status differs')
            pix=pymupdf.Pixmap(checked(page.image,data))
            if (pix.width,pix.height)!=dims:raise ValueError('Render geometry differs')
    for crop in render.crops:
        raw=data[crop['input_path']]
        if digest(raw)!=crop['input_sha256']:raise ValueError('Crop source differs')
        pix=pymupdf.Pixmap(raw);l,t,r,b=crop['pixel_box'];s=pix.samples
        if not 0<=l<r<=pix.width or not 0<=t<b<=pix.height:raise ValueError('Invalid crop')
        part=b''.join(s[y*pix.stride+l*pix.n:y*pix.stride+r*pix.n] for y in range(t,b))
        result=pymupdf.Pixmap(pix.colorspace,r-l,b-t,part,pix.alpha).tobytes('png')
        if result!=data[crop['output_path']] or digest(result)!=crop['output_sha256']:raise ValueError('Crop pixels differ')
    if [m.parsed_json_rows for m in comparison.manifests]!=[70,48390] or any(m.matches or m.parse_errors or m.is_lfs_pointer for m in comparison.manifests):raise ValueError('Recorded historical comparison differs')
    if comparison.acquired_pdf_sha256!=PDF_SHA:raise ValueError('Compared source digest differs')
    for name,source,index in [('event-01.json','event-01.json',0),('escalated/event-01.json','escalated/event-01.json',1),('curl-event-03.json','curl-event-03.json',2),('curl-event-04.json','curl-event-04.json',3)]:
        original=json.loads(data[source]);original['sequence']=index+1
        if original!=access.events[index].model_dump(mode='json'):raise ValueError('Individual/combined receipt differs')
    return review,render,comparison

def main():
    p=argparse.ArgumentParser();p.add_argument('--unsealed',action='store_true');p.add_argument('--rerender',action='store_true');p.add_argument('--repository');args=p.parse_args()
    data={}
    for path in ROOT.rglob('*'):
        if path.is_symlink():raise ValueError('Symlink not allowed')
        if path.is_file():data[path.relative_to(ROOT).as_posix()]=path.read_bytes()
    if not args.unsealed:
        manifest=typed('FINAL_MANIFEST',Manifest,data);paths=[a.path for a in manifest.files]
        if len(paths)!=len(set(paths)) or len(paths)!=len({x.casefold() for x in paths}):raise ValueError('Aliased inventory')
        if set(data)!=set(paths)|{'FINAL_MANIFEST.json'}:raise ValueError('Closed inventory differs')
        for a in manifest.files:
            if Path(a.path).is_absolute() or '..' in Path(a.path).parts:raise ValueError('Unsafe path')
            checked(a,data)
    review,render,comparison=content(data)
    if args.rerender:
        exe=Path(PDFTOPPM)
        if digest(exe.read_bytes())!=render.renderer_sha256:raise ValueError('Renderer differs')
        with tempfile.TemporaryDirectory(prefix='plato-boa-render-') as temp:
            work=Path(temp);(work/'original.pdf').write_bytes(data['original.pdf'])
            run=subprocess.run([str(exe),'-f','1','-l','2','-r','300','-png',str(work/'original.pdf'),str(work/'page')],capture_output=True,timeout=60,check=False)
            if run.returncode:raise ValueError('Rerender failed')
            for n in [1,2]:
                if (work/f'page-{n}.png').read_bytes()!=data[f'page-{n}.png']:raise ValueError('Exact rerender differs')
    if args.repository:
        repo=Path(args.repository)
        for m in comparison.manifests:
            oid=subprocess.check_output(['git','-C',str(repo),'rev-parse',comparison.repository_main_commit+':'+m.repository_path],text=True).strip()
            if oid!=m.git_blob_oid:raise ValueError('Pinned Git blob differs')
            proc=subprocess.Popen(['git','-C',str(repo),'cat-file','blob',oid],stdout=subprocess.PIPE)
            h=sha256();size=count=0;found=[]
            for line in proc.stdout:
                h.update(line);size+=len(line);count+=1;row=json.loads(line)
                match=set(leaves(row)) & set(comparison.urls+[PDF_SHA])
                if match:found.append(count)
            if proc.wait()!=0 or h.hexdigest()!=m.sha256 or size!=m.size_bytes or count!=m.parsed_json_rows or found:raise ValueError('Historical full-stream comparison differs')
    sys.stdout.write(json.dumps({'status':'passed','pages':2,'native_bytes':[0,0],
        'deliberate_attempts':4,'distinct_urls':2,'retained_response_bytes':316142,
        'rerendered':args.rerender,'pinned_git_replayed':bool(args.repository),
        'legal_currentness':'not_verified'},indent=2)+'\n')
if __name__=='__main__':main()
