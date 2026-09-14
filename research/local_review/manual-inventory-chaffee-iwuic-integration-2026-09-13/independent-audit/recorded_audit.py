from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,io,json,os,re,subprocess,sys
from typing import Literal
import jsonschema
from pydantic import BaseModel,ConfigDict,Field
BASE=Path('/Users/mcoors/Documents/Project Geode');REPO=BASE/'MasterLegalDatabase';P=BASE/'handoffs/run-2026-09-13/plato-inventory-69-33-integration';OUT=BASE/'handoffs/run-2026-09-13/ptolemy-inventory69-packaging-audit';OUT.mkdir(exist_ok=False)
class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
class Ref(Strict):
 path:str
 sha256:str=Field(pattern='^[0-9a-f]{64}$')
 size_bytes:int=Field(ge=0)
class File(Ref):
 tracked:bool
 ignored:bool
 ignore_rule:str|None
 lfs_filter:str|None
 issues:list[str]
class InventoryReview(Strict):
 recorded_at:str
 inputs:list[Ref]
 exact_installed_targets:int
 sources:int
 mapped:int
 unmapped:int
 new_schema_entries:dict[str,str]
 ast_otherwise_identical:Literal[True]
 unchanged_authority_joins:int
 unchanged_review_joins:int
 old_row_changes:dict[str,list[str]]
 new_review_proofs:list[dict]
 all_source_currentness_unverified:Literal[True]
 all_source_answer_safe_false:Literal[True]
 unchanged_legacy_ledger:Ref
 notes:list[str]
class Packaging(Strict):
 recorded_at:str
 git_head:str
 selection_rule:str
 roots:list[str]
 files:list[File]
 missing_references:list[str]
 protected_private_candidates:list[str]
 soft_limit_bytes:int
 hard_limit_bytes:int
 limits:list[str]
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p,root=BASE):
 b=p.read_bytes();return Ref(path=p.relative_to(root).as_posix(),sha256=sha(b),size_bytes=len(b))
def put(name,obj):
 if isinstance(obj,BaseModel):body=obj.model_dump_json(indent=2)
 else:body=json.dumps(obj,indent=2)
 (OUT/name).write_text(body+'\n')
def git(args,data=None):
 env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
 out=subprocess.run(['git',*args],cwd=REPO,input=data,capture_output=True,env=env,check=False)
 if out.returncode not in (0,1):raise RuntimeError(out.stderr.decode())
 return out.stdout
inputs=[]
for path in [P/'FINAL_MANIFEST.json',P/'execution/FINAL_MANIFEST.json',P/'PREPARATION.json',P/'execution/RECEIPT.json']:
 inputs.append(ref(path))
for folder in [P,P/'execution']:
 manifest=json.loads((folder/'FINAL_MANIFEST.json').read_bytes())
 jsonschema.validate(manifest,json.loads((folder/'FINAL_MANIFEST.schema.json').read_bytes()))
 for item in manifest['files']:
  got=ref(folder/item['path'],folder)
  assert (got.sha256,got.size_bytes)==(item['sha256'],item['size_bytes']),item
plan=json.loads((P/'PREPARATION.json').read_bytes());receipt=json.loads((P/'execution/RECEIPT.json').read_bytes())
assert receipt['preparation_sha256']==sha((P/'PREPARATION.json').read_bytes())
for t in plan['targets']:
 raw=(REPO/t['repository_path']).read_bytes();prop=(P/t['after']['path']).read_bytes()
 assert raw==prop and sha(raw)==t['after']['sha256'];inputs.append(ref(REPO/t['repository_path']))
oldcode=ast.parse((P/'preimages/manual_review_inventory.py').read_text());newcode=ast.parse((REPO/'geode/pipeline/manual_review_inventory.py').read_text())
def allowed(tree):
 return next(n for n in tree.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=='ALLOWED_REVIEW_SCHEMAS')
oldnode=allowed(oldcode);newnode=allowed(newcode);od=ast.literal_eval(oldnode.value);nd=ast.literal_eval(newnode.value);extra={k:v for k,v in nd.items() if k not in od};assert len(extra)==3
assert all(nd[k]==v for k,v in od.items());newnode.value=copy.deepcopy(oldnode.value);assert ast.dump(oldcode)==ast.dump(newcode)
invpath=REPO/'research/local_review/manual-source-review-inventory-2026-09-11';oldinv=json.loads((P/'preimages/inventory.json').read_bytes());newinv=json.loads((invpath/'inventory.json').read_bytes());oldplan=json.loads((P/'preimages/join-plan.json').read_bytes());newplan=json.loads((invpath/'join-plan.json').read_bytes())
assert newplan['authorities'][:67]==oldplan['authorities'] and len(oldplan['authorities'])==67
assert newplan['reviews'][:30]==oldplan['reviews'] and len(oldplan['reviews'])==30
assert len(newplan['authorities'])==69 and len(newplan['reviews'])==33
oldrows={r['record_id']:r for r in oldinv['sources']};newrows={r['record_id']:r for r in newinv['sources']};changes={}
for sid,row in oldrows.items():
 changed=[k for k in row if row[k]!=newrows[sid].get(k)]
 if changed:changes[sid]=changed
assert changes=={'gunnison-iwuic-resolution-2022-33-sh-ext-003':['reviews','review_status']},changes
assert len(newrows)==69 and newinv['rows_with_review']==33 and newinv['rows_without_review']==36
assert all(r['legal_currentness']=='not_verified' and r['answer_safe'] is False for r in newrows.values())
for key in ['legal_currentness','answer_safe','coverage_promotion','unchanged_legacy_ledger']:assert newinv[key]==oldinv[key]
proofs=[]
for selected in plan['reviews']:
 sid=selected['source_id'];row=newrows[sid]
 assert row['authority_id']==selected['authority_id'] and row['source']['sha256']==selected['source_sha256']
 for key in ['acceptance','acceptance_schema','review','review_schema']:
  got=ref(REPO/selected[key]['path'],REPO);assert got.model_dump()==selected[key];inputs.append(ref(REPO/selected[key]['path']))
 source=(REPO/row['source']['path']).read_bytes();assert sha(source)==row['source']['sha256'] and len(source)==row['source']['size_bytes']
 qa=json.loads((REPO/selected['review']['path']).read_bytes());schema=json.loads((REPO/selected['review_schema']['path']).read_bytes());jsonschema.validate(qa,schema)
 acceptance=json.loads((REPO/selected['acceptance']['path']).read_bytes());jsonschema.validate(acceptance,json.loads((REPO/selected['acceptance_schema']['path']).read_bytes()))
 assert selected['review_schema']['sha256'] in extra and extra[selected['review_schema']['sha256']]=='checked_passages'
 match=row['reviews'][0];assert match['artifact']==selected['review'] and match['schema_artifact']==selected['review_schema']
 assert match['answer_safe'] is False and match['legal_currentness']=='not_verified'
 assert row['intake_received_at']!=row['verified_http_acquired_at']
 if 'gunnison' in sid:assert row['verified_http_acquired_at'] is None and row['official_source_url'] is None
 else:
  assert row['intake_received_at']=='2026-09-13T16:44:04.840983Z'
  event=row['verified_http_evidence']['document']['artifact'];eventraw=(REPO/event['path']).read_bytes();assert sha(eventraw)==event['sha256'];eventdata=json.loads(eventraw)
  assert eventdata['completed_at']==row['verified_http_acquired_at'] and eventdata['body']['sha256']==row['source']['sha256'] and eventdata['http_status']==200
 proofs.append({'source_id':sid,'authority_id':row['authority_id'],'source':row['source'],'review':match['artifact'],'schema':match['schema_artifact'],'review_kind':match['review_kind'],'intake_received_at':row['intake_received_at'],'verified_http_acquired_at':row['verified_http_acquired_at'],'scope_pointers':list(match['scope_fields']),'preserved_limitations':match['limitations']})
audit=InventoryReview(recorded_at=datetime.now(timezone.utc).isoformat(),inputs=inputs,exact_installed_targets=6,sources=69,mapped=33,unmapped=36,new_schema_entries=extra,ast_otherwise_identical=True,unchanged_authority_joins=67,unchanged_review_joins=30,old_row_changes=changes,new_review_proofs=proofs,all_source_currentness_unverified=True,all_source_answer_safe_false=True,unchanged_legacy_ledger=Ref(**newinv['unchanged_legacy_ledger']),notes=['This is independent metadata/custody review, not a new visual judgment of source pages.','All previous source rows are unchanged except the explicitly listed IWUIC review fields.','Gunnison reported acquisition remains unverified; Chaffee observed GET times remain separate from later intake.','Historical pending-review or pre-intake qualifiers inside accepted source QA remain historical and are not overwritten.'])
put('INVENTORY_REVIEW.json',audit);put('INVENTORY_REVIEW.schema.json',InventoryReview.model_json_schema())
# Scope all date-named September13 accepted research roots plus existing inventory snapshots,
# all September13 raw receipts, and date-labelled root snapshots (including earlier tracked ones).
roots=[p for p in (REPO/'research/local_review').iterdir() if p.is_dir() and p.name.endswith('2026-09-13')]
roots.append(invpath)
roots += [p for p in (REPO/'_SNAPSHOTS').iterdir() if p.is_dir() and ('2026-09-13' in p.name or '20260913' in p.name)]
paths=set(p for root in roots for p in root.rglob('*') if p.is_file() or p.is_symlink())
with (REPO/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl').open('rb') as handle:
 for line in handle:
  row=json.loads(line)
  if row['received_at'].startswith('2026-09-13'):paths.add(REPO/row['archive_path'])
for name in ['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json']:
 paths.add(REPO/name)
tracked=set(git(['ls-files','-z']).decode().split('\0'));names=sorted(p.relative_to(REPO).as_posix() for p in paths)
payload=('\0'.join(names)+'\0').encode();ignored=git(['check-ignore','-v','-z','--stdin'],payload).decode().split('\0');ignore={}
for i in range(0,len(ignored)-1,4):
 rulefile,line,pattern,name=ignored[i:i+4];ignore[name]=f'{rulefile}:{line}:{pattern}'
attrs=git(['check-attr','-z','filter','--stdin'],payload).decode().split('\0');filters={}
for i in range(0,len(attrs)-1,3):
 name,attr,val=attrs[i:i+3];filters[name]=None if val=='unspecified' else val
files=[];private=[];missing=[]
for name in names:
 path=REPO/name;issues=[]
 if path.is_symlink():issues.append('symlink_do_not_stage_without_review');body=b''
 elif not path.is_file():missing.append(name);continue
 else:body=path.read_bytes()
 if len(body)>=100_000_000:issues.append('at_or_above_100MB')
 elif len(body)>=50_000_000:issues.append('at_or_above_50MB')
 if any(part in {'__pycache__','.pytest_cache','.ruff_cache','.mypy_cache','.DS_Store','node_modules'} for part in path.parts) or path.name in {'.coverage'} or path.suffix in {'.pyc','.pyo'}:
  issues.append('cache_or_generated_tool_state_review_before_staging')
 if path.name in {'private.headers','transient-private.headers','.env','API_KEYS.json'}:
  issues.append('private_named_payload_review_before_staging');private.append(name)
 if path.suffix.lower() in {'.headers','.txt','.log','.json','.jsonl','.html'} and len(body)<40_000_000:
  # Record only paths/counts, never secret-looking values.
  if re.search(rb'(?im)^\s*(?:set-cookie|authorization|proxy-authorization|cookie)\s*:',body):
   issues.append('header_secret_field_present_review_without_echoing_values');private.append(name)
  if re.search(rb'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----',body):
   issues.append('private_key_marker');private.append(name)
 files.append(File(path=name,sha256=sha(body),size_bytes=len(body),tracked=name in tracked,ignored=name in ignore,ignore_rule=ignore.get(name),lfs_filter=filters.get(name),issues=issues))
# Locate declared missing package members for relevant date-root top-level manifests.
for root in roots:
 for mn in ['MANIFEST.json','FINAL_MANIFEST.json']:
  manifest=root/mn
  if not manifest.is_file():continue
  try:data=json.loads(manifest.read_bytes())
  except (ValueError,OSError):continue
  entries=data.get('files',[])
  if not isinstance(entries,list):continue
  for item in entries:
   if not isinstance(item,dict) or not isinstance(item.get('path'),str):continue
   rel=Path(item['path'])
   if rel.is_absolute() or '..' in rel.parts:continue
   target=root/rel
   if not target.exists():missing.append(target.relative_to(REPO).as_posix())
pack=Packaging(recorded_at=datetime.now(timezone.utc).isoformat(),git_head=git(['rev-parse','HEAD']).decode().strip(),selection_rule='All research/local_review top-level directories ending2026-09-13, current manual inventory tree, all September13 date-labelled root snapshots, all current manual originals received September13, and three live manual-intake metadata files. This includes earlier tracked overnight packages; force-add candidates exclude already tracked paths.',roots=[p.relative_to(REPO).as_posix() for p in roots],files=files,missing_references=sorted(set(missing)),protected_private_candidates=sorted(set(private)),soft_limit_bytes=50_000_000,hard_limit_bytes=100_000_000,limits=['No staging, commit, network or canonical edits.','The file list is a preparation-time snapshot, not automatic authorization to stage future additions.','Text marker checks are bounded privacy screening, not a comprehensive credential audit; no values are reproduced.','Missing declared references are assessed only for top-level files-list manifests; some portable wrappers use other inventory shapes.','Git index tracking/ignore/filter status is recorded separately from ordinary working-tree source hashes.','Intentional immutable historical test evidence may include caches; its original package closure must not be silently broken. Review or explicitly preserve/exclude the complete package.'])
put('PACKAGING.json',pack);put('PACKAGING.schema.json',Packaging.model_json_schema())
needed=[f for f in files if f.ignored and not f.tracked and not f.issues]
put('NEEDED_FORCE_ADD.json',{'prepared_at':pack.recorded_at,'status':'proposal_only_no_staging','files':[f.model_dump() for f in needed]})
(OUT/'needed-force-add.nul').write_bytes(('\0'.join(f.path for f in needed)+'\0').encode())
put('REVIEW_BEFORE_STAGE.json',{'files':[f.model_dump() for f in files if f.issues]})
put('UNTRACKED_ORDINARY.json',{'files':[f.model_dump() for f in files if not f.ignored and not f.tracked and not f.issues]})
put('SUMMARY.json',{'files':len(files),'total_bytes':sum(f.size_bytes for f in files),'tracked':sum(f.tracked for f in files),'ignored_untracked_safe':len(needed),'ignored_safe_bytes':sum(f.size_bytes for f in needed),'ordinary_untracked_safe':sum(not f.ignored and not f.tracked and not f.issues for f in files),'flagged':sum(bool(f.issues) for f in files),'missing':len(set(missing)),'private_candidates':len(set(private)),'max_file_bytes':max(f.size_bytes for f in files)})
print((OUT/'SUMMARY.json').read_text())
