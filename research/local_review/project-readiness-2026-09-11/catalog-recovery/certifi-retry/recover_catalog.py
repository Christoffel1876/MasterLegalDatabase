"""One exact LFS recovery attempt; credentials and action URLs stay in memory."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,os,re,ssl,subprocess,sys,time
import certifi
from urllib.request import Request,build_opener,HTTPSHandler,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
B=Path(__file__).resolve().parent
R=B.parents[3]/'MasterLegalDatabase'
OID='e12d942b4c8098281d86a8e0db7a76b22512a8a75d050ff590a8e876c7b840b4'
SIZE=225796201
ENDPOINT='https://github.com/Christoffel1876/MasterLegalDatabase.git/info/lfs/objects/batch'
class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Start(Strict):
 started_at:datetime
 repository:str
 operation:Literal['download']='download'
 oid:str
 expected_bytes:int
 pointer_sha256:str
 pointer_bytes:int
 local_lfs_object_present:bool
 check_deadline:datetime
 download_deadline:datetime
 credentials:str='Existing gh authentication read in memory only; not retained or printed.'
class Receipt(Strict):
 started:Start
 completed_at:datetime
 outcome:str
 batch_http_status:int | None=None
 batch_response_sha256:str | None=None
 batch_response_bytes:int | None=None
 batch_response_original_retained:Literal[False]=False
 batch_headers:dict[str,str]={}
 object_oid:str | None=None
 object_size:int | None=None
 object_error_code:int | None=None
 object_error_message:str | None=None
 download_action_present:bool=False
 action_url_retained:Literal[False]=False
 download_http_status:int | None=None
 download_bytes:int=0
 download_sha256:str | None=None
 download_path:str | None=None
 exact_oid_and_size_verified:bool=False
 jsonl_lines:int | None=None
 jsonl_object_rows:int | None=None
 jsonl_syntax_errors:int | None=None
 schema_valid_rows:int | None=None
 schema_invalid_rows:int | None=None
 schema_error_locations:list[dict]=[]
 schema_name:str | None=None
 schema_module_sha256:str | None=None
 failure_class:str | None=None
 sanitized_error:str | None=None
 limitations:list[str]
def save(p:Path,obj:BaseModel)->None:
 if p.exists():raise FileExistsError(p)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(obj.model_dump_json(indent=2)+'\n');os.replace(tmp,p)
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def request(req,timeout=30):
 try:return opener.open(req,timeout=timeout)
 except HTTPError as e:return e

def main()->None:
 global opener
 now=datetime.now(timezone.utc)
 check_end=datetime(2026,9,11,20,50,tzinfo=timezone.utc);download_end=datetime(2026,9,11,21,0,tzinfo=timezone.utc)
 if now>=check_end:raise ValueError('public check deadline passed')
 if (B/'ATTEMPT_STARTED.json').exists():raise ValueError('one-attempt guard: prior attempt exists')
 raw=subprocess.run(['git','-C',str(R),'remote','get-url','origin'],capture_output=True,text=True,check=True).stdout.strip()
 need_origin=raw in ['https://github.com/Christoffel1876/MasterLegalDatabase.git','https://github.com/Christoffel1876/MasterLegalDatabase','git@github.com:Christoffel1876/MasterLegalDatabase.git']
 if not need_origin:raise ValueError('configured origin mismatch')
 pointer=(R/'_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl').read_bytes()
 expected=f'version https://git-lfs.github.com/spec/v1\noid sha256:{OID}\nsize {SIZE}\n'.encode()
 if pointer!=expected:raise ValueError('exact pointer changed')
 local=R/f'.git/lfs/objects/{OID[:2]}/{OID[2:4]}/{OID}'
 s=Start(started_at=now,repository='Christoffel1876/MasterLegalDatabase',oid=OID,expected_bytes=SIZE,pointer_sha256=sha(pointer),pointer_bytes=len(pointer),local_lfs_object_present=local.is_file(),check_deadline=check_end,download_deadline=download_end)
 (B/'retrieval-catalog.pointer.txt').write_bytes(pointer);save(B/'ATTEMPT_STARTED.json',s)
 rec=Receipt(started=s,completed_at=now,outcome='pending',limitations=['One explicitly authorized transport-repair retry of the exact object, using installed certifi CA trust with verification enabled. Prior no-HTTP transport-failure receipt remains unchanged. No alternate repository, credential output, install, Git mutation or catalog replacement.','Original batch/action response is not retained because it may contain signed download credentials; only its hash, length and allowlisted metadata are recorded.','Recovered bytes, if available, remain in this handoff pending root decision. JSONL/schema validation does not certify freshness, ownership release eligibility, answer safety or legal currentness.'])
 token=None
 try:
  auth=subprocess.run(['/usr/local/bin/gh','auth','token','--hostname','github.com'],capture_output=True,text=True)
  if auth.returncode or not auth.stdout.strip():raise RuntimeError('existing gh credential unavailable')
  token=auth.stdout.strip()
  opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  headers={'Accept':'application/vnd.git-lfs+json','Content-Type':'application/vnd.git-lfs+json','Authorization':'Basic '+base64.b64encode(('x-access-token:'+token).encode()).decode(),'User-Agent':'Project Geode exact-object recovery'}
  payload=json.dumps({'operation':'download','transfers':['basic'],'objects':[{'oid':OID,'size':SIZE}]}).encode()
  req=Request(ENDPOINT,data=payload,headers=headers,method='POST')
  with request(req) as resp:
   rec.batch_http_status=resp.status
   body=resp.read(1048577)
   rec.batch_response_bytes=len(body);rec.batch_response_sha256=sha(body)
   rec.batch_headers={k:v for k,v in resp.headers.items() if k.lower() in ['date','content-type','content-length','x-github-request-id','retry-after']}
  if len(body)>1048576:raise RuntimeError('batch response exceeds bounded metadata size')
  if rec.batch_http_status!=200:
   rec.outcome='batch_unavailable';rec.sanitized_error='Non-success HTTP response; no retry was made.';return
  obj=json.loads(body)
  objects=obj.get('objects',[])
  if len(objects)!=1 or objects[0].get('oid')!=OID:raise RuntimeError('batch exact-object identity mismatch')
  item=objects[0];rec.object_oid=item['oid'];rec.object_size=item.get('size')
  error=item.get('error')
  if error:
   rec.object_error_code=error.get('code')
   msg=str(error.get('message',''))
   known=['Object does not exist on the server','Object does not exist on the server.','Object does not exist','Not Found','Repository not found']
   rec.object_error_message=msg if msg in known else 'Server reports object unavailable; untrusted message not retained.'
   rec.outcome='exact_object_unavailable';return
  action=item.get('actions',{}).get('download');rec.download_action_present=bool(action)
  if not action:rec.outcome='no_download_action';return
  if item.get('size')!=SIZE:raise RuntimeError('advertised size mismatch')
  from urllib.parse import urlparse
  url=action.get('href');u=urlparse(url)
  if u.scheme!='https' or u.username or u.password:raise RuntimeError('download action is not ordinary verified HTTPS')
  if datetime.now(timezone.utc)>=download_end:raise RuntimeError('download deadline reached before starting')
  action_headers=action.get('header',{})
  if not isinstance(action_headers,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in action_headers.items()):raise RuntimeError('invalid action header shape')
  # Do not forward the GitHub credential to the action host. Only scoped server-provided headers.
  dreq=Request(url,headers={'User-Agent':'Project Geode exact-object recovery',**action_headers},method='GET')
  partial=B/'retrieval-catalog.jsonl.partial';dig=hashlib.sha256();total=0
  sys.stdout.write('Exact LFS object is available; starting one bounded download.\n');sys.stdout.flush()
  with request(dreq,timeout=30) as resp:
   rec.download_http_status=resp.status
   if resp.status!=200:rec.outcome='download_non_success';return
   with partial.open('xb') as out:
    while True:
     if datetime.now(timezone.utc)>=download_end:raise TimeoutError('download hard deadline')
     block=resp.read(min(1024*1024,SIZE-total+1))
     if not block:break
     out.write(block);dig.update(block);total+=len(block);rec.download_bytes=total
     if total>SIZE:raise RuntimeError('download larger than expected object')
  rec.download_sha256=dig.hexdigest();rec.download_path=partial.name
  if total!=SIZE or dig.hexdigest()!=OID:rec.outcome='download_integrity_mismatch';return
  destination=B/f'{OID}.jsonl';os.replace(partial,destination);rec.download_path=destination.name;rec.exact_oid_and_size_verified=True
  # Stream syntax and current record-schema validation without invoking any production pipeline.
  sys.path.insert(0,str(R));from geode.pipeline.retrieval_catalog import RetrievalCatalogRecord
  rec.schema_name='geode.pipeline.retrieval_catalog.RetrievalCatalogRecord'
  rec.schema_module_sha256=sha((R/'geode/pipeline/retrieval_catalog.py').read_bytes())
  lines=objects=bad=valid=invalid=0;locations=[]
  with destination.open('rb') as stream:
   for lines,line in enumerate(stream,1):
    try:
     val=json.loads(line)
     if not isinstance(val,dict):raise ValueError('non-object JSONL row')
     objects+=1
    except (ValueError,UnicodeError):bad+=1;continue
    try:RetrievalCatalogRecord.model_validate(val);valid+=1
    except Exception as e:
     invalid+=1
     if len(locations)<20:locations.append({'line':lines,'error_class':type(e).__name__})
  rec.jsonl_lines=lines;rec.jsonl_object_rows=objects;rec.jsonl_syntax_errors=bad;rec.schema_valid_rows=valid;rec.schema_invalid_rows=invalid;rec.schema_error_locations=locations
  rec.outcome='download_complete_validated' if not bad and not invalid else 'download_complete_validation_errors'
 except Exception as exc:
  rec.failure_class=type(exc).__name__
  # Do not serialize exception strings: libraries may include auth or signed URLs.
  rec.sanitized_error='Attempt stopped on an exception; exception message intentionally not retained.'
  rec.outcome='attempt_failed'
  partial=B/'retrieval-catalog.jsonl.partial'
  if partial.exists():
   dig=hashlib.sha256();total=0
   with partial.open('rb') as p:
    for chunk in iter(lambda:p.read(1024*1024),b''):dig.update(chunk);total+=len(chunk)
   rec.download_bytes=total;rec.download_sha256=dig.hexdigest();rec.download_path=partial.name
 finally:
  token=None
  rec.completed_at=datetime.now(timezone.utc);save(B/'RECOVERY_RECEIPT.json',rec)
  (B/'RECOVERY_RECEIPT.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
  sys.stdout.write(json.dumps({'outcome':rec.outcome,'batch_http_status':rec.batch_http_status,'object_error_code':rec.object_error_code,'object_error_message':rec.object_error_message,'download_action_present':rec.download_action_present,'download_bytes':rec.download_bytes,'exact_sha_size_verified':rec.exact_oid_and_size_verified,'jsonl_rows':rec.jsonl_object_rows,'failure_class':rec.failure_class},indent=2)+'\n')
if __name__=='__main__':main()
