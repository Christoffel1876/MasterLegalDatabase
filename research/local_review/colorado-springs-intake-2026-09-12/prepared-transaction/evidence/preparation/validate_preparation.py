"""Read-only portable proposal validation; optional live preflight never applies intake."""
from __future__ import annotations
import argparse,hashlib,json,os,stat,sys
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit,unquote
import jsonschema,pymupdf
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).absolute().parent))
from preparation_models import Preparation,RecordTemplate,Source,Inventory,Asset
EXPECTED=[('SD014-01','colorado-springs-code-services-fees-2015-atlas-directed','555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56',162682),('SD014-02','colorado-springs-construction-fees-atlas-directed','e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a',258393)]
def require(ok,message):
    if not ok:raise ValueError(message)
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ordinary(path,directory=False):
    require(not any(p.is_symlink() for p in [path,*path.parents]),'symlink refused')
    require(stat.S_ISDIR(path.stat().st_mode) if directory else stat.S_ISREG(path.stat().st_mode),'nonordinary path');return path
def path(root,relative):
    p=PurePosixPath(relative);require(not p.is_absolute() and '..' not in p.parts and p.as_posix()==relative and '\\' not in relative,'unsafe relative path');return ordinary(root/relative)
def check(root,a):
    p=path(root,a.path);require(p.stat().st_size==a.size_bytes and digest(p)==a.sha256,'hash or size mismatch: '+a.path);return p
def pairs(items):
    d={}
    for k,v in items:require(k not in d,'duplicate JSON key');d[k]=v
    return d
def load(p):return json.loads(p.read_text(),object_pairs_hook=pairs)
def jsonlines(p,schema):
    rows=[]
    with p.open('r',encoding='utf-8') as f:
        for line in f:
            require(bool(line.strip()),'blank JSONL line');v=json.loads(line,object_pairs_hook=pairs);jsonschema.validate(v,schema);rows.append(v)
    return rows
def validate(root,repo=None):
    root=ordinary(root.absolute(),True)
    inv=Inventory.model_validate_json(path(root,'FINAL_MANIFEST.json').read_text())
    actual=set()
    for base,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:ordinary(Path(base)/name,True)
        for name in files:actual.add(ordinary(Path(base)/name).relative_to(root).as_posix())
    require(actual=={a.path for a in inv.files}|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'},'closed inventory mismatch')
    for a in inv.files:check(root,a)
    require(load(path(root,'FINAL_MANIFEST.schema.json'))==Inventory.model_json_schema(),'manifest schema changed')
    prep=Preparation.model_validate_json(path(root,'PREPARATION.json').read_text())
    require(load(path(root,'PREPARATION.schema.json'))==Preparation.model_json_schema(),'preparation schema changed')
    proposed=jsonlines(path(root,'proposed-records.jsonl'),RecordTemplate.model_json_schema())
    source_rows=jsonlines(path(root,'source-provenance.jsonl'),Source.model_json_schema())
    require(proposed==[x.model_dump(mode='json') for x in prep.proposed_records],'proposal JSONL mismatch')
    require(source_rows==[x.model_dump(mode='json') for x in prep.sources],'source JSONL mismatch')
    requests=jsonlines(path(root,'requests.jsonl'),load(path(root,'requests.schema.json')))
    previews=jsonlines(path(root,'dry-run-previews.jsonl'),load(path(root,'dry-run-previews.schema.json')))
    require(len(requests)==len(previews)==2,'request scope changed')
    for c in prep.copies:check(root,c.preserved)
    plan=load(path(root,'inputs/acquisition-plan.json'))
    for source,template,req,preview,(sid,rid,sha,size) in zip(prep.sources,prep.proposed_records,requests,previews,EXPECTED,strict=True):
        require(source.source_id==sid and source.proposed_record_id==rid and template.record_id==rid,'source identity changed')
        p=check(root,source.original);require(digest(p)==sha and p.stat().st_size==size,'exact original changed')
        with pymupdf.open(p) as pdf:require(len(pdf)==7 and not pdf.is_repaired and not pdf.is_encrypted,'PDF structure changed')
        target=next(t for t in plan['targets'] if t['source_id']==sid)
        require(source.http_url==target['url'] and urlsplit(source.http_url).scheme=='https' and urlsplit(source.http_url).netloc=='coloradosprings.gov','official target identity')
        acq={Path(a.path).name:check(root,a) for a in source.response_receipts}
        reservation=load(acq['reservation.json']);result=load(acq['result.json']);headers=load(acq['public-headers.json'])
        require(result['reservation_sha256']==digest(acq['reservation.json']) and reservation['plan_sha256']==digest(path(root,'inputs/acquisition-plan.json')),'HTTP reservation binding')
        require(result['http_status']==200 and result['outcome']=='complete' and result['partial_body'] is False and result['redirect_url'] is None,'HTTP outcome changed')
        require(result['body']['sha256']==sha and result['body']['size_bytes']==size and result['content_magic']=='pdf','HTTP source bytes mismatch')
        require(reservation['url']==headers['request_url']==source.http_url,'HTTP URL mismatch')
        require(result['public_headers']['sha256']==digest(acq['public-headers.json']),'public-header binding')
        require(set(headers['headers'])<=set(['content-type','content-length','last-modified','date','cache-control','location']),'private header field')
        require(source.request_started_at.isoformat().replace('+00:00','Z')==reservation['reserved_at'] and source.response_completed_at.isoformat().replace('+00:00','Z')==result['finished_at'],'acquisition times changed')
        ref=source.referral;html=check(root,ref.parent_html);pr=load(check(root,ref.parent_reservation));ps=load(check(root,ref.parent_result));ph=check(root,ref.parent_public_headers)
        require(pr['url']==ref.parent_url==target['parent_url'],'parent URL mismatch')
        require(ps['body']['sha256']==digest(html) and ps['body']['size_bytes']==html.stat().st_size and ps['reservation_sha256']==ref.parent_reservation.sha256 and ps['public_headers']['sha256']==digest(ph),'parent receipt binding')
        require(ps['http_status']==200 and ps['outcome']=='complete' and ps['partial_body'] is False and ps['redirect_url'] is None,'parent completion changed')
        soup=BeautifulSoup(html.read_bytes(),'html.parser');frames=[x for x in soup.find_all('iframe') if x.get('data-src')==ref.original_data_src];require(len(frames)==1,'observed iframe missing')
        frame=frames[0];require(frame['src']==ref.original_viewer_src,'viewer attribute mismatch');encoded=[v.split('=',1)[1] for v in urlsplit(frame['src']).query.split('&') if v.startswith('file=')];require(len(encoded)==1 and encoded[0]==ref.encoded_file_argument and unquote(encoded[0])==ref.original_data_src==ref.resolved_url==source.http_url,'single-decode referral mismatch')
        require(req['record_id']==rid and req['layer_id']=='10_Municipal_Authorities' and req['expected_sha256']==sha and req['official_source_url']==source.http_url and req['acquisition_method']=='manual_official_download' and req['allow_duplicate'] is False,'request identity/provenance mismatch')
        require(Path(req['source_file']).name==template.original_filename and req['custody_note']==template.custody_note,'request custody mismatch')
        require(preview['record_id']==rid and preview['sha256']==sha and preview['size_bytes']==size and preview['status']=='dry_run_pending_archive' and preview['blocked_queue_match'] is False,'preview not dry run')
        require(preview['received_at']==prep.prepared_at.isoformat().replace('+00:00','Z'),'preview time must be preparation time')
        require(template.archive_path is None and template.intake_id is None and template.received_at is None,'future intake time invented')
    recon=load(check(root,prep.reconciliation));require(not recon['added_intake_ids'] and not recon['report_needs_update'],'baseline reconciliation drift')
    require(recon['report']['archive_verification']['missing_ledger_only_intake_ids']==prep.preserved_missing_ledger_only_ids==['MSI-20260707T221329208329Z-EO-2019-007'],'missing historical EO changed')
    for b in prep.baseline:
        p=check(root,b.preserved)
        if b.records is not None:require(len(jsonlines(p,load(path(root,'dry-run-previews.schema.json'))))==b.records,'baseline row count mismatch')
    require(not prep.dedupe.matching_raw_files and not prep.dedupe.matching_lfs_pointers and not prep.dedupe.matching_raw_manifest_records and not prep.dedupe.matching_ledger_records and not prep.dedupe.proposed_id_collisions and not any(prep.dedupe.exact_metadata_pattern_counts.values()),'recorded dedupe did not clear')
    if repo is not None:
        repo=ordinary(repo.absolute(),True)
        for b in prep.baseline:require(digest(path(repo,b.repository_path))==b.preserved.sha256,'current baseline changed: '+b.repository_path)
        for c in prep.copies:
            if c.kind=='code_reference':
                rel=c.original_path.removeprefix('MasterLegalDatabase/');require(digest(path(repo,rel))==c.preserved.sha256,'current validation code changed')
        for a in prep.dedupe.metadata_search_inputs:require(digest(path(repo,a.path))==a.sha256,'current metadata search input changed')
        sys.path.insert(0,str(repo))
        from geode.pipeline.manual_source_intake import ManualSourceIntakeRequest,ManualSourceIntakeRecord,archive_manual_source,reconcile_manual_source_intake,_validate_reconciliation_record
        from geode.schemas.validators import require_official_source_url
        for request,source in zip(requests,prep.sources,strict=True):
            request=dict(request,source_file=str(root/source.original.path));req=ManualSourceIntakeRequest.model_validate(request);require_official_source_url(req.official_source_url)
            preview=archive_manual_source(repo,req,dry_run=True,timestamp=prep.prepared_at);ManualSourceIntakeRecord.model_validate(preview);_validate_reconciliation_record(repo,preview)
        live=reconcile_manual_source_intake(repo,dry_run=True)
        require(not live.added_intake_ids and not live.report_needs_update and live.ledger_records_before==60 and live.report.archive_verification.manifest_records==59,'live reconciliation mismatch')
        sizes={s.original.size_bytes for s in prep.sources};hashes={s.original.sha256 for s in prep.sources}
        for base,dirs,files in os.walk(repo/'_RAW_ARCHIVE',followlinks=False):
            for n in dirs+files:require(not (Path(base)/n).is_symlink(),'raw symlink introduced')
            for n in files:
                p=ordinary(Path(base)/n)
                if p.stat().st_size in sizes:require(digest(p) not in hashes,'new canonical duplicate bytes')
                elif p.stat().st_size<200:
                    raw=p.read_bytes();require(not(raw.startswith(b'version https://git-lfs.github.com/spec/v1') and any(h.encode() in raw for h in hashes)),'new matching LFS pointer')
    return {'status':'validated_preparation_not_applied','sources':2,'pdf_pages':14,'source_bytes':421075,'municipal_layer':'10_Municipal_Authorities','raw_before':59,'ledger_before':60,'expected_raw_after':61,'expected_ledger_after':62,'current_repository_preflight':repo is not None,'canonical_writes':0,'actual_repository_received_at':None,'legal_currentness':'not_verified'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).absolute().parent);ap.add_argument('--repo',type=Path);a=ap.parse_args()
    print(json.dumps(validate(a.root,a.repo),indent=2))
