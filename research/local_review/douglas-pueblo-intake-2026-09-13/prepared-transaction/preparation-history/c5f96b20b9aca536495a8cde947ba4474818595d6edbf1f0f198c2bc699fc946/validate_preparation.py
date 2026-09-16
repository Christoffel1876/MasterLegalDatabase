"""Read-only custody/schema verification; --live adds canonical transaction dry-run."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from urllib.parse import urljoin
import pymupdf
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from preparation_models import Preparation, Source, Template, Asset

def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def read(path:Path)->bytes:
 if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():raise ValueError('Nonordinary evidence')
 return path.read_bytes()
def check(base:Path,ref:Asset)->bytes:
 p=Path(ref.path)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Evidence escape')
 b=read(base/p)
 if digest(b)!=ref.sha256 or len(b)!=ref.size_bytes:raise ValueError('Evidence SHA/size mismatch')
 return b

def verify(base:Path=BASE)->dict:
 prep=base/'evidence/preparation'
 data=Preparation.model_validate_json(read(prep/'PREPARATION.json'))
 manifest=json.loads(read(prep/'FINAL_MANIFEST.json'))
 expected={x['path'] for x in manifest['files']}|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}
 actual=set()
 for p in prep.rglob('*'):
  if any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('Symlink member')
  if not p.is_file() and not p.is_dir():raise ValueError('Special member')
  if p.is_file():actual.add(p.relative_to(prep).as_posix())
 if expected!=actual:raise ValueError('Closed preparation membership differs')
 for a in manifest['files']:check(prep,Asset.model_validate(a))
 with (prep/'source-provenance.jsonl').open('rb') as f:source_rows=[Source.model_validate_json(row) for row in f]
 with (prep/'proposed-records.jsonl').open('rb') as f:templates=[Template.model_validate_json(row) for row in f]
 if source_rows!=data.sources or templates!=data.proposed_records:raise ValueError('JSONL differs from prepared records')
 identities={'douglas-ehs-fees-atlas-directed':('CO-COUNTY-DOUGLAS','08_County_Authorities',1),'pueblo-planning-fees-atlas-directed':('CO-MUNICIPAL-PUEBLO','10_Municipal_Authorities',4)}
 if len(data.sources)!=2 or [x.proposed_record_id for x in data.sources]!=list(identities):raise ValueError('Selected source IDs changed')
 for source,t in zip(data.sources,data.proposed_records,strict=True):
  if (source.authority_id,source.layer_id,source.physical_pages)!=identities[source.proposed_record_id]:raise ValueError('Identity/layer mismatch')
  body=check(prep,source.original)
  with pymupdf.open(stream=body,filetype='pdf') as pdf:
   if len(pdf)!=source.physical_pages or pdf.is_repaired or pdf.is_encrypted:raise ValueError('PDF structure differs')
  if source.response_completed_at<source.request_started_at:raise ValueError('Acquisition interval reversed')
  for a in source.evidence:check(prep,a)
  selected=[a for a in BeautifulSoup(check(prep,source.referral_parent_body),'html.parser').find_all('a',href=True) if ' '.join(a.get_text(' ',strip=True).split())==source.referral_label and a['href']==source.referral_href]
  if len(selected)!=1 or urljoin(source.referral_parent_url,source.referral_href)!=source.referral_selected_url:raise ValueError('Official parent anchor mismatch')
  events=[json.loads(check(prep,a)) for a in source.evidence if a.path.endswith('/event.json')]
  final=[x for x in events if x.get('body',{}).get('sha256')==source.original.sha256]
  if len(final)!=1:raise ValueError('Ambiguous final response')
  event=final[0]
  if event['http_status']!=200 or event.get('final_url',event['requested_url'])!=source.http_url:raise ValueError('HTTP identity mismatch')
  if event['started_at'].replace('Z','+00:00')!=source.request_started_at.isoformat() or event['completed_at'].replace('Z','+00:00')!=source.response_completed_at.isoformat():raise ValueError('HTTP acquisition timing mismatch')
  if event.get('body_complete',event.get('curl_exit')==0) is not True:raise ValueError('Incomplete response')
  selected_url=source.referral_selected_url
  for ref in source.redirect_events:
   redirect=json.loads(check(prep,ref))
   if redirect['requested_url']!=selected_url or redirect['http_status']!=301:raise ValueError('Redirect mismatch')
   selected_url=redirect['redirect_to']
  if selected_url!=source.http_url:raise ValueError('Referral does not reach selected body URL')
  if t.record_id!=source.proposed_record_id or t.layer_id!=source.layer_id or t.source_file!=source.original or t.expected_sha256!=source.original.sha256 or t.official_source_url!=source.http_url:raise ValueError('Proposed record/source mismatch')
  qa=json.loads(check(prep,next(a for a in source.evidence if a.path.endswith('/SOURCE_QA.json'))))
  if qa['source']['sha256']!=source.original.sha256:raise ValueError('Accepted QA source mismatch')
 for baseline in data.baseline:
  b=check(prep,baseline.preserved)
  if baseline.records is not None:
   import io
   count=sum(1 for _ in io.BytesIO(b))
   if count!=baseline.records or not b.endswith(b'\n'):raise ValueError('Exact prefix row shape differs')
 return {'status':'verified_prepared_not_applied','sources':2,'pages':5,'source_bytes':sum(s.original.size_bytes for s in data.sources),'raw_before':61,'ledger_before':62,'proposed_raw_after':63,'proposed_ledger_after':64,'actual_repository_received_at':None,'legal_currentness':'not_verified','public_requests':0}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--live',action='store_true');p.add_argument('--root',type=Path);a=p.parse_args();result=verify()
 if a.live:
  import transaction as tx
  root=a.root.absolute() if a.root else tx.DEFAULT_ROOT
  result['live_dry_run']=tx.execute(tx.load_plan(root),root,BASE/'execution')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
