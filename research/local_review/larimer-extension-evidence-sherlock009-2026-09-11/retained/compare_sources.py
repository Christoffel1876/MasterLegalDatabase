"""Read-only source comparison; outputs only within this audit directory."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from collections import Counter
import json, shutil, subprocess
BASE=Path('/Users/mcoors/Documents/Project Geode')
OUT=Path(__file__).parent
REPO=BASE/'MasterLegalDatabase'
PIN=BASE/'handoffs/sherlock-source-discovery-008/atlas-pinned-comparison'
ATT=OUT/'received/20260911T190213Z'
def digest(p):
    h=sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def freeze(p,rel):
    dest=OUT/'comparison-evidence'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        shutil.copyfile(p,dest);dest.chmod(0o444)
    assert digest(p)==digest(dest)
    return {'original_path':str(p),'copy_path':str(dest.relative_to(OUT)),
            'sha256':digest(dest),'size_bytes':dest.stat().st_size}
meta=json.loads((PIN/'EXPORT.json').read_text())
pin_files=[freeze(PIN/'EXPORT.json','pinned/EXPORT.json')]
for r in meta['records']:
    p=PIN/r['path'];assert digest(p)==r['sha256'] and p.stat().st_size==r['size_bytes']
    proc=subprocess.Popen(['git','cat-file','blob',meta['comparison_commit']+':'+r['path']],cwd=REPO,stdout=subprocess.PIPE)
    h=sha256();gh=sha256()
    for b in iter(lambda:proc.stdout.read(1024*1024),b''):h.update(b)
    assert proc.wait()==0 and h.hexdigest()==r['sha256']
    pin_files.append(freeze(p,'pinned/'+r['path']))
logs=json.loads((ATT/'logs/attempted_urls.json').read_text())['events']
urls={r['requested_url'] for r in logs if str(r.get('requested_url','')).startswith('https://')}
cands=json.loads((ATT/'priority_candidates_final.json').read_text())['candidates']
shas={r['sha256'] for r in cands if r.get('sha256')}
prior_sha='15933b2bbfc05894ab6f6cc49b8f8e1c4490815036f6afab9b22c7dc2cdbf10e'
def scan_manifest(p):
    counts=Counter();direct=[];parent=[];hashes=[]
    with p.open() as f:
        for n,line in enumerate(f,1):
            if not line.strip():continue
            row=json.loads(line);counts['rows']+=1
            keys=[k for k in ('source_url','requested_url','final_url','official_source_url') if row.get(k) in urls]
            linked=sorted(set(row.get('linked_urls') or []) & urls)
            small={k:row.get(k) for k in ('source_id','record_id','authority_id','status','sha256','source_url','requested_url','final_url','official_source_url','archive_path') if row.get(k) is not None}
            small['line']=n
            if keys:direct.append(dict(small,matched_fields=keys))
            if linked:parent.append(dict(small,matched_linked_urls=linked))
            if row.get('sha256') in shas|{prior_sha}:hashes.append(small)
            if row.get('final_url'):counts['populated_final_url']+=1
    return dict(counts=counts,direct_url_matches=direct,linked_parent_matches=parent,sha256_matches=hashes)
def walk_matches(obj,path='$'):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():out+=walk_matches(v,path+'.'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj):out+=walk_matches(v,f'{path}[{i}]')
    elif isinstance(obj,str) and obj in urls:out.append({'json_path':path,'url':obj})
    return out
pin_scan={}
for r in meta['records']:
    p=PIN/r['path']
    pin_scan[r['path']]=scan_manifest(p) if p.suffix=='.jsonl' else walk_matches(json.loads(p.read_text()))
current_files=[];current_scan={}
for rel in ['_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl','_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl']:
    current_files.append(freeze(REPO/rel,'current/'+rel))
    current_scan[rel]=scan_manifest(OUT/current_files[-1]['copy_path'])
source_files=[]
for r in cands[:3]:
    p=ATT/'raw'/Path(r['local_path']).name
    assert digest(p)==r['sha256']
    source_files.append((p,r['sha256'],p.stat().st_size))
size_set={x[2] for x in source_files};raw_count=0;raw_candidates=[];raw_matches=[]
for p in (REPO/'_RAW_ARCHIVE').rglob('*'):
    if p.is_symlink() or not p.is_file():continue
    raw_count+=1
    if p.stat().st_size in size_set:
        h=digest(p);raw_candidates.append({'path':str(p.relative_to(REPO)),'sha256':h,'size_bytes':p.stat().st_size})
        if h in shas:raw_matches.append(raw_candidates[-1])
prior_evidence=[]
for rel in ['logs/attempted_urls.json','priority_candidates_final.json','raw/temp_moratorium_data_centers.html']:
    prior_evidence.append(freeze(BASE/'handoffs/sherlock-source-discovery-007/20260911T182833Z'/rel,'sd007/'+rel))
prior_events=json.loads((OUT/'comparison-evidence/sd007/logs/attempted_urls.json').read_text())['events']
prior_url_rows=[r for r in prior_events if r.get('sha256')==prior_sha]
prior_pdf=BASE/'handoffs/sherlock-source-discovery-007/20260911T182833Z/raw/land_use_hearing_agenda_packet_2026-02-09.pdf'
assert digest(prior_pdf)==prior_sha
result={'compared_at':datetime.now(timezone.utc).isoformat(),'comparison_commit':meta['comparison_commit'],
 'pin_exact_git_blobs_verified':True,'target_urls':sorted(urls),'incoming_pdf_hashes':sorted(shas),
 'pinned_files':pin_files,'pinned_comparisons':pin_scan,'current_files':current_files,
 'current_comparisons':current_scan,'current_raw_regular_files_considered':raw_count,
 'current_raw_same_size_candidates':raw_candidates,'current_raw_digest_matches':raw_matches,
 'prior_evidence':prior_evidence,'prior_packet_log_rows':prior_url_rows,
 'prior_packet_bytes_verified':{'path':str(prior_pdf),'sha256':digest(prior_pdf),'size_bytes':prior_pdf.stat().st_size},
 'legal_currentness':'not_verified'}
(OUT/'comparison-facts.json').write_text(json.dumps(result,indent=2)+'\n')
for name,data in pin_scan.items():
    print('PIN',name, data.get('counts') if isinstance(data,dict) else len(data))
    if isinstance(data,dict):print('url',len(data['direct_url_matches']),'parent',len(data['linked_parent_matches']),'hash',len(data['sha256_matches']))
for name,data in current_scan.items():print('CURRENT',name,data['counts'],'url',len(data['direct_url_matches']),'parent',len(data['linked_parent_matches']),'hash',len(data['sha256_matches']))
print('rawfiles',raw_count,'size_matches',len(raw_candidates),'digest_matches',len(raw_matches))
print('prior_packet_rows',json.dumps(prior_url_rows,indent=2))
