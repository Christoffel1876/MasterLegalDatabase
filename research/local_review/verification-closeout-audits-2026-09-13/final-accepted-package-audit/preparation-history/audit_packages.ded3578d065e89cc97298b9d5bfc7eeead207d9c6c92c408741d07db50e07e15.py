"""Read-only independent acceptance and byte-custody check of three fixed packages."""
from __future__ import annotations
import ast,hashlib,importlib.util,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
from typing import Literal,Any
import jsonschema
from pydantic import BaseModel,ConfigDict,Field
HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
EXT=HERE.parent
PYTHON='/private/tmp/geode-status-venv/bin/python'
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Ref(Strict):
 path:str
 sha256:str=Field(pattern='^[a-f0-9]{64}$')
 size_bytes:int=Field(ge=0)
class Command(Strict):
 command:list[str]
 exit_code:int
 started_at:str
 completed_at:str
 stdout:Ref
 stderr:Ref
class Package(Strict):
 package:str
 root_acceptance:Ref
 original_handoff:str
 primary_manifest:Ref
 copied_files_verified:int
 reports_and_candidates:list[Ref]
 all_package_files:list[Ref]
 scope:dict[str,int]
 qualifications:list[str]
class Audit(Strict):
 status:Literal['PASS','BLOCKED']
 started_at:str
 completed_at:str
 packages:list[Package]
 validators:list[Command]
 current_raw_records:int
 current_ledger_records:int
 county_record:dict[str,Any]
 city_record:dict[str,Any]
 exact_prior_prefixes:bool
 exact_snapshots:bool
 actual_execution_receipt_matches:bool
 canonical_guards_unchanged:bool
 manifest_bound_cache_named_files:list[Ref]
 issues:list[str]
 limitations:list[str]

def stamp()->str:return datetime.now(timezone.utc).isoformat()
def safe(root:Path,name:str)->Path:
 rel=PurePosixPath(name)
 if rel.is_absolute() or '..' in rel.parts or str(rel)!=name:raise ValueError('Unsafe path')
 p=root/Path(name)
 if not p.is_file() or any(x.is_symlink() for x in [p,*p.parents]):raise ValueError('Nonordinary '+name)
 return p

def ref(root:Path,p:Path)->Ref:
 with p.open('rb') as f:d=hashlib.file_digest(f,'sha256').hexdigest()
 return Ref(path=str(p.relative_to(root)),sha256=d,size_bytes=p.stat().st_size)
def check(root:Path,r:Ref)->None:
 if ref(root,safe(root,r.path))!=r:raise ValueError('Asset differs '+r.path)
def save(name:str,raw:bytes)->Ref:
 p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():raise ValueError('Refuse overwrite '+name)
 t=p.with_name(p.name+'.tmp')
 with t.open('xb') as f:f.write(raw)
 os.replace(t,p);return ref(HERE,p)
def jlines(path:Path)->tuple[list[dict],bytes]:
 rows=[];raw=[]
 with path.open('rb') as f:
  for line in f:
   if not line.strip():raise ValueError('Blank JSONL row')
   rows.append(json.loads(line));raw.append(line)
 return rows,b''.join(raw)
def acceptance_type(builder:Path,tx:Any=None)->Any:
 """Compile only reviewed Pydantic class declarations, never the preservation builder."""
 tree=ast.parse(builder.read_bytes())
 definitions=[n for n in tree.body if isinstance(n,ast.ClassDef)]
 if not definitions or any(n.name not in {'Asset','Acceptance'} for n in definitions):
  raise ValueError('Unexpected acceptance class set')
 namespace={'BaseModel':BaseModel,'ConfigDict':ConfigDict,'Field':Field,'datetime':datetime,
            'Literal':Literal,'tx':tx,'Asset':Ref}
 exec(compile(ast.Module(body=definitions,type_ignores=[]),str(builder),'exec'),namespace)
 return namespace['Acceptance']
def main()->None:
 start=stamp();sys.path.insert(0,str(ROOT))
 from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord
 raw_path='_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
 ledger_path='_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl'
 report_path='_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json'
 guards=[raw_path,ledger_path,report_path,'_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json']
 before={p:ref(ROOT,ROOT/p) for p in guards}
 configs=[
 ('pueblo-county-intake-2026-09-13','prepared-transaction','pueblo-county-fees-intake-revision',
  '69b70f519439f905aa4cb721bee571041089c0c13771d7770a70cdc087999f1f'),
 ('eb023-equity-memo-source-qa-2026-09-13','independent-review','eb023-independent-source-review-2026-09-13',
  '7fc1136d3e233386c19b214f719de82a2448a0cb1c1d2cfc81bffbfad842d196'),
 ('eb024-bylaws-source-qa-2026-09-13','independent-review','eb024-bylaws-independent-review',
  '515205338cbdc4790b99e9c4a91ccbf35beabaf2cf2beeb8d47153a1ef1032d2')]
 packages=[];commands=[];junk=[];county=None;all_before={};tx=None
 for name,sub,original,pin in configs:
  package=ROOT/'research/local_review'/name;selected=package/sub
  original=EXT/original
  manifest=ref(selected,selected/'FINAL_MANIFEST.json')
  if manifest.sha256!=pin or ref(original,original/'FINAL_MANIFEST.json').sha256!=pin:
   raise ValueError('Pinned copy manifest mismatch '+name)
  data=json.loads((selected/'FINAL_MANIFEST.json').read_bytes())
  entries=data['files'] if isinstance(data,dict) else data
  copied=0
  for item in entries:
   item=Ref.model_validate(item);check(selected,item);check(original,item);copied+=1
   if Path(item.path).name in {'.coverage','.DS_Store'} or '__pycache__' in Path(item.path).parts:
    junk.append(ref(ROOT,selected/item.path))
  if name.startswith('pueblo-'):
   sys.path.insert(0,str(selected))
   spec=importlib.util.spec_from_file_location('reviewed_tx',selected/'transaction.py')
   tx=importlib.util.module_from_spec(spec);sys.modules[spec.name]=tx;spec.loader.exec_module(tx)
   model=acceptance_type(package/'preserve_county_applied.py',tx)
  else:model=acceptance_type(package/'accept_final_pdf_reviews.py')
  acceptance_raw=(package/'ROOT_ACCEPTANCE.json').read_bytes()
  acceptance=model.model_validate_json(acceptance_raw)
  jsonschema.validate(json.loads(acceptance_raw),json.loads((package/'ROOT_ACCEPTANCE.schema.json').read_bytes()))
  for name2 in ['ROOT_ACCEPTANCE.json','ROOT_ACCEPTANCE.schema.json']:
   save('received/'+name+'/'+name2,(package/name2).read_bytes())
  save('received/'+name+'/FINAL_MANIFEST.json',(selected/'FINAL_MANIFEST.json').read_bytes())
  if (selected/'FINAL_MANIFEST.schema.json').exists():
   save('received/'+name+'/FINAL_MANIFEST.schema.json',(selected/'FINAL_MANIFEST.schema.json').read_bytes())
  files=[ref(package,p) for p in sorted(package.rglob('*')) if p.is_file()]
  all_before[name]=files
  reports=[r for r in files if any(term in r.path.lower() for term in
            ['pass1','pass2','candidate','receipt']) and not r.path.endswith('.schema.json')]
  if name.startswith('pueblo-'):
   county=acceptance
   for item in acceptance.package_files:check(package,Ref.model_validate(item.model_dump()))
   for item in [acceptance.canonical_source,*acceptance.snapshots]:check(ROOT,Ref.model_validate(item.model_dump()))
   if acceptance.reviewed_transaction_sha256!='dcacd5e6de2cb8bc7b3e37a8dcc20b705f97c8e90747768227b4b8b8b478c5f2':
    raise ValueError('Unreviewed transaction accepted')
   scope={'physical_pages':2,'physical_rows':88,'current_raw':64,'current_ledger':65}
   command=[PYTHON,'-B',str(selected/'verify_preparation.py'),'--manifest-sha256',pin,'--repository',str(ROOT)]
  else:
   for item in [acceptance.source,acceptance.source_qa,acceptance.source_qa_schema,acceptance.independent_manifest]:
    check(package,Ref.model_validate(item.model_dump()))
   scope=acceptance.validated_scope
   if acceptance.full_pages_directly_inspected_by_atlas!=list(range(1,scope['physical_pages']+1)):
    raise ValueError('Root page scope mismatch')
   command=[PYTHON,'-B',str(selected/('validate_review.py' if name.startswith('eb023') else 'review.py'))]
  began=stamp();result=subprocess.run(command,cwd=HERE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
                capture_output=True,timeout=120)
  commands.append(Command(command=command,exit_code=result.returncode,started_at=began,completed_at=stamp(),
   stdout=save('validation/'+name+'.stdout.txt',result.stdout),stderr=save('validation/'+name+'.stderr.txt',result.stderr)))
  if result.returncode:raise ValueError('Closed verifier failed '+name+': '+result.stderr.decode()[:200])
  packages.append(Package(package=str(package.relative_to(ROOT)),root_acceptance=ref(ROOT,package/'ROOT_ACCEPTANCE.json'),
   original_handoff=str(original),primary_manifest=ref(ROOT,selected/'FINAL_MANIFEST.json'),copied_files_verified=copied,
   reports_and_candidates=reports,all_package_files=files,scope=scope,qualifications=acceptance.limitations))
 if county is None or tx is None:raise ValueError('No County acceptance')
 package=ROOT/'research/local_review/pueblo-county-intake-2026-09-13/prepared-transaction'
 intent=tx.Intent.model_validate_json((package/'execution/INTENT.json').read_bytes())
 receipt=tx.Receipt.model_validate_json((package/'execution/RECEIPT.json').read_bytes())
 if receipt!=county.actual_execution:raise ValueError('Execution/acceptance differs')
 raw_rows,raw_bytes=jlines(ROOT/raw_path);ledger_rows,ledger_bytes=jlines(ROOT/ledger_path)
 for row in raw_rows+ledger_rows:ManualSourceIntakeRecord.model_validate(row)
 if (len(raw_rows),len(ledger_rows))!=(64,65):raise ValueError('Current row counts differ')
 previous_raw=jlines(package/'execution/preimages/manual_source_intake_manifest.jsonl')[1]
 previous_ledger=jlines(package/'execution/preimages/MANUAL_SOURCE_INTAKE_LEDGER.jsonl')[1]
 record=intent.record;suffix=(record.model_dump_json()+'\n').encode()
 if raw_bytes!=previous_raw+suffix or ledger_bytes!=previous_ledger+suffix:
  raise ValueError('Exact-prefix append differs')
 for item in county.snapshots:
  snapshot=ROOT/item.path;old=package/'execution/preimages'/Path(item.path).name
  if ref(ROOT,snapshot).sha256!=ref(package,old).sha256:raise ValueError('Snapshot differs')
 if (record.acquisition_method!='received_review_package' or record.official_source_url is not None or
     record.layer_id!='08_County_Authorities' or record.status!='archived_pending_pipeline'):
  raise ValueError('County custody classification differs')
 city=next(x for x in raw_rows if x['record_id']=='pueblo-planning-fees-atlas-directed')
 if city['layer_id']!='10_Municipal_Authorities' or city['sha256']==record.sha256:
  raise ValueError('City/county mixed')
 if hashlib.sha256(raw_bytes).hexdigest()!=receipt.raw_sha256 or hashlib.sha256(ledger_bytes).hexdigest()!=receipt.ledger_sha256:
  raise ValueError('Actual receipt prefix digests differ')
 if ref(ROOT,ROOT/report_path).sha256!=receipt.report_sha256:raise ValueError('Report digest differs')
 for name,files in all_before.items():
  package=ROOT/'research/local_review'/name
  if files!=[ref(package,p) for p in sorted(package.rglob('*')) if p.is_file()]:
   raise ValueError('Package changed during read')
 unchanged=before=={p:ref(ROOT,ROOT/p) for p in guards}
 if not unchanged:raise ValueError('Canonical files changed during read')
 for name in ['INTENT.json','RECEIPT.json']:
  save('received/county-execution/'+name,(ROOT/'research/local_review/pueblo-county-intake-2026-09-13/prepared-transaction/execution'/name).read_bytes())
 audit=Audit(status='PASS',started_at=start,completed_at=stamp(),packages=packages,validators=commands,
  current_raw_records=64,current_ledger_records=65,county_record=record.model_dump(mode='json'),city_record=city,
  exact_prior_prefixes=True,exact_snapshots=True,actual_execution_receipt_matches=True,
  canonical_guards_unchanged=unchanged,manifest_bound_cache_named_files=junk,issues=[],limitations=[
   'Independent byte-custody/schema/closed-verifier audit only. No source visual judgment, full suite, HTTP, apply or repeat apply run here.',
   'Root direct-page inspection is a separately recorded acceptance claim; this audit does not authenticate prior agent timing or image-reopen chronology.',
   'The original blocked transaction remains historical, never accepted for execution. Only the revised fixed-source transaction matches actual intent/receipt.',
   'EB023 staff recommendation and conditional fees are not an adopted instrument; EB024 is a five-page bylaws source, not complete Board law.',
   'Acquisition claims, actual repository receipt and source printed dates remain distinct; all currentness and answer-safe gates stay unpromoted.',
   'Inventory regeneration and final staging are outside this audit. The historical manifest-bound .coverage must be staged with the closed County package.',
   'Copied acceptance/manifests and execution metadata are portable audit inputs; PDFs/images remain in the referenced accepted packages.'])
 raw=(audit.model_dump_json(indent=2)+'\n').encode();Audit.model_validate_json(raw)
 save('AUDIT.json',raw);save('AUDIT.schema.json',(json.dumps(Audit.model_json_schema(),indent=2)+'\n').encode())
 print(json.dumps({'status':audit.status,'packages':[(p.package,p.copied_files_verified) for p in packages],
  'current_raw':64,'current_ledger':65,'bound_cache_files':[r.path for r in junk]},indent=2))
if __name__=='__main__':main()
