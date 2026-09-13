"""Seal the incoming-basename correction; preserve both prior complete packets."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import json,hashlib,os,sys
from pydantic import BaseModel,ConfigDict
BASE=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(BASE))
from package_models import File,Inventory,Validation
class Revision(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 checked_at:str;status:Literal['PREPARED_NOT_APPLIED'];prior_manifest:File;prior_file_count:Literal[228];prior_all_files_unchanged:Literal[True];source_and_custody_bytes_unchanged:Literal[True];source_provenance_unchanged:Literal[True];changed_preparation_members:list[str];incoming_basename:Literal['original.pdf'];publisher_filename_inferred:Literal[False];transaction:File;tests:File;canonical_writes:Literal[0];legal_currentness:Literal['not_verified']
def ref(p):
 b=p.read_bytes();return File(path=p.relative_to(BASE).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
def enc(v):return (json.dumps(v.model_dump(mode='json') if hasattr(v,'model_dump') else v,indent=2)+'\n').encode()
def replace(name,data):
 p=BASE/name
 if p.exists():
  old=p.read_bytes();s=BASE/'preparation-history'/hashlib.sha256(old).hexdigest();s.mkdir(parents=True,exist_ok=True);q=s/p.name
  if q.exists():assert q.read_bytes()==old
  else:q.write_bytes(old)
 t=p.with_name('.'+p.name+'.tmp');t.write_bytes(data);os.replace(t,p)
prior=BASE/'historical/second-prepared-0a16a7b8';m=json.loads((prior/'FINAL_MANIFEST.json').read_bytes())
assert hashlib.sha256((prior/'FINAL_MANIFEST.json').read_bytes()).hexdigest()=='0a16a7b835b6d38bf348df267fe04bb055cd50ddae2984412ce3ad1b2821f40f'
for f in m['files']:
 b=(prior/f['path']).read_bytes();assert len(b)==f['size_bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
changed=[]
for p in (BASE/'evidence/preparation').rglob('*'):
 if p.is_file() and p.read_bytes()!=(prior/p.relative_to(BASE)).read_bytes():changed.append(p.relative_to(BASE/'evidence/preparation').as_posix())
assert set(changed)=={'PREPARATION.json','proposed-records.jsonl','FINAL_MANIFEST.json'}
assert not (BASE/'execution').exists()
revision=Revision(checked_at=datetime.now(timezone.utc).isoformat(),status='PREPARED_NOT_APPLIED',prior_manifest=ref(prior/'FINAL_MANIFEST.json'),prior_file_count=228,prior_all_files_unchanged=True,source_and_custody_bytes_unchanged=True,source_provenance_unchanged=True,changed_preparation_members=sorted(changed),incoming_basename='original.pdf',publisher_filename_inferred=False,transaction=ref(BASE/'transaction.py'),tests=ref(BASE/'test_transaction.py'),canonical_writes=0,legal_currentness='not_verified')
replace('REVISION.json',enc(revision));replace('REVISION.schema.json',enc(Revision.model_json_schema()))
old=json.loads((BASE/'VALIDATION.json').read_bytes());cov=json.loads((BASE/'validation/filename-focused/coverage.json').read_bytes())
old.update(checked_at=datetime.now(timezone.utc).isoformat(),tests_passed=62,branch_inclusive_coverage_percent=float(cov['totals']['percent_covered']),transaction=ref(BASE/'transaction.py').model_dump(),tests=ref(BASE/'test_transaction.py').model_dump(),preparation=ref(BASE/'evidence/preparation/PREPARATION.json').model_dump(),command_receipts=[ref(BASE/'validation'/name/'ATTEMPT.json').model_dump() for name in ['filename-focused','filename-read-only','filename-cli-dry-run']])
old['qualifications']+=['Root requested original_filename equal the actual incoming basename original.pdf for both; descriptive labels stay in official_source_name and HTTP Content-Disposition remains unchanged. Prior228-file revision is preserved exactly.']
record=Validation.model_validate_json(json.dumps(old));replace('VALIDATION.json',enc(record));replace('VALIDATION.schema.json',enc(Validation.model_json_schema()))
for name in ['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json']:
 p=BASE/name;raw=p.read_bytes();s=BASE/'preparation-history'/hashlib.sha256(raw).hexdigest();s.mkdir(exist_ok=True);q=s/name
 if q.exists():assert q.read_bytes()==raw
 else:q.write_bytes(raw)
files=[ref(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p.relative_to(BASE).as_posix() not in {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}]
manifest=Inventory(schema_version=1,status='PREPARED_NOT_APPLIED',prepared_at=datetime.now(timezone.utc),files=files,mutable_execution_directory='execution',execution_directory_present_at_freeze=False,sources=2,physical_pages=5,original_bytes=377549,legal_currentness='not_verified',preparation_canonical_writes=0,public_requests=0)
for name,data in [('FINAL_MANIFEST.json',enc(manifest)),('FINAL_MANIFEST.schema.json',enc(Inventory.model_json_schema()))]:
 p=BASE/name;t=p.with_name('.'+p.name+'.tmp');t.write_bytes(data);os.replace(t,p)
print('FROZEN',len(files)+2,'files',sum(x.size_bytes for x in files)+(BASE/'FINAL_MANIFEST.json').stat().st_size+(BASE/'FINAL_MANIFEST.schema.json').stat().st_size,'bytes')
for name in ['FINAL_MANIFEST.json','VALIDATION.json','REVISION.json','transaction.py','test_transaction.py','validate_preparation.py','evidence/preparation/PREPARATION.json','evidence/preparation/source-provenance.jsonl']:print(name,ref(BASE/name).sha256)
