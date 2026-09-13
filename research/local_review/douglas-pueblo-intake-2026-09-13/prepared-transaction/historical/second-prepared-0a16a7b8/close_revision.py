"""Seal the root-requested revision after preserving the complete earlier packet."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import json,hashlib,os,sys
from pydantic import BaseModel,ConfigDict
BASE=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(BASE))
from package_models import File,Inventory,Validation
class Revision(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 reviewed_at:str;status:Literal['PREPARED_NOT_APPLIED'];prior_manifest:File;prior_file_count:Literal[100];prior_all_files_unchanged:Literal[True];source_preparation_unchanged:Literal[True];transaction:File;tests:File;changes:list[str];canonical_writes:Literal[0]
def ref(p):
 b=p.read_bytes();return File(path=p.relative_to(BASE).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
def enc(v):return (json.dumps(v.model_dump(mode='json') if hasattr(v,'model_dump') else v,indent=2)+'\n').encode()
def replace(name,data):
 p=BASE/name
 if p.exists():
  before=p.read_bytes();history=BASE/'preparation-history'/hashlib.sha256(before).hexdigest();history.mkdir(parents=True,exist_ok=True)
  saved=history/p.name
  if saved.exists():assert saved.read_bytes()==before
  else:saved.write_bytes(before)
 tmp=p.with_name('.'+p.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,p)
prior=BASE/'historical/first-prepared-9a12c339';m=json.loads((prior/'FINAL_MANIFEST.json').read_bytes())
assert hashlib.sha256((prior/'FINAL_MANIFEST.json').read_bytes()).hexdigest()=='9a12c339721adb98f7c952081437a1958a45f74c66e39f5f705ba089ae11fe52'
for f in m['files']:
 b=(prior/f['path']).read_bytes();assert len(b)==f['size_bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
for p in (BASE/'evidence/preparation').rglob('*'):
 if p.is_file():assert p.read_bytes()==(prior/p.relative_to(BASE)).read_bytes()
assert not (BASE/'execution').exists()
revision=Revision(reviewed_at=datetime.now(timezone.utc).isoformat(),status='PREPARED_NOT_APPLIED',prior_manifest=ref(prior/'FINAL_MANIFEST.json'),prior_file_count=100,prior_all_files_unchanged=True,source_preparation_unchanged=True,transaction=ref(BASE/'transaction.py'),tests=ref(BASE/'test_transaction.py'),changes=['Format all transaction lines to at most100 characters; name fixed source identity map and format runtime pins.','Remove unused predecessor VERIFIER_SHA and explain direct frozen-manifest checking.','Consume only the exact PREPARATION, manifest, provenance and baseline buffers that passed verification; no unchecked metadata reread.','Keep fresh source-byte verification before writes; regression rejects source mutation after metadata capture.','61 focused tests and actual canonical read-only preflight passed; unchanged source bytes and original61/62prefixes.'],canonical_writes=0)
replace('REVISION.json',enc(revision));replace('REVISION.schema.json',enc(Revision.model_json_schema()))
old=json.loads((prior/'VALIDATION.json').read_bytes());cov=json.loads((BASE/'validation/revised-focused/coverage.json').read_bytes())
old.update(checked_at=datetime.now(timezone.utc).isoformat(),tests_passed=61,branch_inclusive_coverage_percent=float(cov['totals']['percent_covered']),transaction=ref(BASE/'transaction.py').model_dump(),tests=ref(BASE/'test_transaction.py').model_dump(),command_receipts=[ref(BASE/'validation'/name/'ATTEMPT.json').model_dump() for name in ['revised-focused','revised-read-only','revised-cli-dry-run']])
old['qualifications']+=['Root requested readability cleanup and captured-metadata reread repair; previous100-file packet preserved byte-exact in historical/first-prepared-9a12c339.']
record=Validation.model_validate_json(json.dumps(old));replace('VALIDATION.json',enc(record));replace('VALIDATION.schema.json',enc(Validation.model_json_schema()))
# Snapshot current outer inventories before computing the new closed inventory.
for name in ['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json']:
 p=BASE/name;b=p.read_bytes();h=BASE/'preparation-history'/hashlib.sha256(b).hexdigest();h.mkdir(parents=True,exist_ok=True);(h/name).write_bytes(b)
files=[]
for p in sorted(BASE.rglob('*')):
 if p.is_symlink():raise ValueError('Symlink package member')
 if p.is_file() and p.name not in [] and p.relative_to(BASE).as_posix() not in {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}:files.append(ref(p))
manifest=Inventory(schema_version=1,status='PREPARED_NOT_APPLIED',prepared_at=datetime.now(timezone.utc),files=files,mutable_execution_directory='execution',execution_directory_present_at_freeze=False,sources=2,physical_pages=5,original_bytes=377549,legal_currentness='not_verified',preparation_canonical_writes=0,public_requests=0)
# Preimages already exist; direct atomic replacement must not add new files after enumeration.
for name,data in [('FINAL_MANIFEST.json',enc(manifest)),('FINAL_MANIFEST.schema.json',enc(Inventory.model_json_schema()))]:
 p=BASE/name;t=p.with_name('.'+p.name+'.tmp');t.write_bytes(data);os.replace(t,p)
print('FROZEN',len(files)+2,'files',sum(x.size_bytes for x in files)+(BASE/'FINAL_MANIFEST.json').stat().st_size+(BASE/'FINAL_MANIFEST.schema.json').stat().st_size,'bytes')
for name in ['FINAL_MANIFEST.json','VALIDATION.json','REVISION.json','transaction.py','test_transaction.py','validate_package.py','evidence/preparation/PREPARATION.json','evidence/preparation/source-provenance.jsonl']:print(name,ref(BASE/name).sha256)
