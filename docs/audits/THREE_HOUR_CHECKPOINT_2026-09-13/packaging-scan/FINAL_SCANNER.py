"""Read-only explicit packaging scan of this session's approved repository evidence."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
import argparse, io, json, subprocess
import jsonschema
from pydantic import BaseModel, ConfigDict, Field
R=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13')
class Asset(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 path:str
 sha256:str=Field(pattern='^[a-f0-9]{64}$')
 size_bytes:int=Field(ge=0)
 tracked:bool
 ignored:bool
 basis:list[str]
class Scan(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 status:Literal['prepared_exact_paths_not_staged']
 recorded_at:str
 head:str
 wrappers:int
 new_raw_originals:int
 files:list[Asset]
 excluded_user_paths:list[str]
 qualifications:list[str]
def git(*args:str,input:bytes|None=None)->bytes:
 return subprocess.run(['git',*args],cwd=R,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout

def hashasset(p:Path)->tuple[str,int]:
 if p.is_symlink() or not p.is_file():raise ValueError('non-regular '+str(p))
 b=p.read_bytes();return sha256(b).hexdigest(),len(b)
parser=argparse.ArgumentParser();parser.add_argument('name');args=parser.parse_args()
if not args.name.replace('-','').isalnum():raise ValueError('unsafe scan name')
dst=B/'plato-final-packaging-scan'/'runs'/args.name;dst.mkdir(parents=True,exist_ok=False)
(dst/'SCAN.schema.json').write_text(json.dumps(Scan.model_json_schema(),indent=2)+'\n')
tracked={p.decode() for p in git('ls-files','-z').split(b'\0') if p}
selected:dict[str,set[str]]={}
expected_identities:dict[str,tuple[str,int]]={}
BASELINE_HEAD='512684a65ae3c4eb51509b23520cfe41823ca0b9'
if git('rev-parse','HEAD').decode().strip()!=BASELINE_HEAD:raise ValueError('reviewed HEAD changed')
def add(rel:str,basis:str,expected:tuple[str,int])->None:
 p=Path(rel)
 if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe path')
 if p.name.casefold() in {'project_status_2026-09-09.md','models 2.py'}:raise ValueError('excluded user basename')
 if any(name.casefold()==rel.casefold() and name!=rel for name in selected):
  raise ValueError('case-aliased packaging member '+rel)
 if rel in expected_identities and expected_identities[rel]!=expected:
  raise ValueError('conflicting expected identity '+rel)
 if hashasset(R/rel)!=expected:raise ValueError('selected identity drift '+rel)
 expected_identities[rel]=expected
 selected.setdefault(rel,set()).add(basis)

def bound_json(rel:str)->dict:
 if rel not in expected_identities:raise ValueError('unbound metadata '+rel)
 p=R/rel;raw=p.read_bytes()
 if (sha256(raw).hexdigest(),len(raw))!=expected_identities[rel]:
  raise ValueError('metadata identity drift '+rel)
 return json.loads(raw)

approval_raw=(B/'plato-final-packaging-scan/APPROVALS.json').read_bytes()
if sha256(approval_raw).hexdigest()!='fc7d09f3e641eea23937df2d9662cb96e202690840f363390d9026922cf5503f':raise ValueError('approved wrapper set changed')
approval=json.loads(approval_raw)
approved_wrappers={a['path']:(a['sha256'],a['size_bytes']) for a in approval['wrappers']}
if len(approved_wrappers)!=21:raise ValueError('expected exactly twenty-one approved wrappers')
observed_wrappers=set()
wrappers=0
for inv in sorted((R/'research/local_review').glob('*/INVENTORY.json')):
 if inv.relative_to(R).as_posix().casefold() in {x.casefold() for x in tracked}:continue
 wrapper_rel=inv.relative_to(R).as_posix()
 if wrapper_rel not in approved_wrappers:raise ValueError('wrapper not explicitly reviewed '+wrapper_rel)
 observed_wrappers.add(wrapper_rel)
 root=inv.parent;inv_raw=inv.read_bytes()
 if (sha256(inv_raw).hexdigest(),len(inv_raw))!=approved_wrappers[wrapper_rel]:raise ValueError('approved wrapper inventory differs')
 obj=json.loads(inv_raw);jsonschema.validate(obj,json.loads((root/'INVENTORY.schema.json').read_bytes()))
 expected=set()
 for a in obj['files']:
  rel=a['path']
  prefix=root.relative_to(R).as_posix()+'/'
  if rel.startswith(prefix):rel=rel[len(prefix):]
  p=root/rel
  if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('unsafe wrapper path')
  if rel in expected:raise ValueError('duplicate wrapper member')
  expected.add(rel)
  if hashasset(p)!=(a['sha256'],a['size_bytes']):raise ValueError('wrapper hash '+str(p))
  add(p.relative_to(R).as_posix(),'closed wrapper '+root.name,(a['sha256'],a['size_bytes']))
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
 if any(p.is_symlink() for p in root.rglob('*')) or actual != expected|{'INVENTORY.json'}:raise ValueError('wrapper closure '+str(root))
 add(inv.relative_to(R).as_posix(),'closed wrapper inventory',(sha256(inv_raw).hexdigest(),len(inv_raw)));wrappers+=1
if observed_wrappers!=set(approved_wrappers):raise ValueError('approved wrapper absent')
# Previously independently reviewed exact ignored candidates retain their published hashes.
prior_raw=(B/'ptolemy-inventory69-packaging-audit/NEEDED_FORCE_ADD.json').read_bytes()
if sha256(prior_raw).hexdigest()!='94ce696f540b45cfa2aa5fb6fc792adce5422b971fc7f4960b3fa013852284c0':
 raise ValueError('independent ignored-payload proposal changed')
prior=json.loads(prior_raw)
for a in prior['files']:
 if hashasset(R/a['path'])!=(a['sha256'],a['size_bytes']):raise ValueError('prior packaging member changed')
 add(a['path'],'independent packaging audit pin',(a['sha256'],a['size_bytes']))
manifest='_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
old=git('show',BASELINE_HEAD+':'+manifest);now=(R/manifest).read_bytes()
if not now.startswith(old):raise ValueError('raw manifest not exact append')
if not old.endswith(b'\n'):raise ValueError('historical manifest missing newline')
with io.BytesIO(now[len(old):]) as stream:new=[json.loads(line) for line in stream]
APPROVED_RAW = {'gunnison-building-fees-resolution-2025-24-sh-ext-003': ('_RAW_ARCHIVE/manual_intake/08_County_Authorities/gunnison-building-fees-resolution-2025-24-sh-ext-003/20260913T155735577123Z_SHEXT003-A026.pdf', '53bd127e25d331ab0086fb09c5e1485d52dc46a96235d84476ef17a989022bab', 126763), 'gunnison-building-code-resolution-2023-22-sh-ext-003': ('_RAW_ARCHIVE/manual_intake/08_County_Authorities/gunnison-building-code-resolution-2023-22-sh-ext-003/20260913T155735577123Z_SHEXT003-A027.pdf', '41dc3a6c962039878f4b49212c07e289a8658903dd63a9980e68ecdee9cc9b7b', 682037), 'gunnison-iwuic-resolution-2022-33-sh-ext-003': ('_RAW_ARCHIVE/manual_intake/08_County_Authorities/gunnison-iwuic-resolution-2022-33-sh-ext-003/20260913T155735577123Z_SHEXT003-A028.pdf', '0b2dc2e2bdff25b849b29de9285e993d7a353a9209cffbccad2ebc79c7f7b99d', 114843), 'chaffee-cwrc-ordinance-2026-02-atlas-directed': ('_RAW_ARCHIVE/manual_intake/08_County_Authorities/chaffee-cwrc-ordinance-2026-02-atlas-directed/20260913T164404840983Z_original.pdf', '0688818dfd4d7726f1eb84b5b57c47580d01b094297a92d4ce88c600ccfe7eba', 1146747), 'chaffee-electric-ordinance-2026-01-atlas-directed': ('_RAW_ARCHIVE/manual_intake/08_County_Authorities/chaffee-electric-ordinance-2026-01-atlas-directed/20260913T164404840983Z_original.pdf', 'c0bfb6e8d4adb846fd62ec7dabbdd824286f7432be6a82b6b2d2264d4553cdf6', 529100), 'chaffee-planning-application-fees-atlas-directed': ('_RAW_ARCHIVE/manual_intake/08_County_Authorities/chaffee-planning-application-fees-atlas-directed/20260913T170209370066Z_original.pdf', '8c6b6176f8617a43c4f4eb422f5c9c7287ffba8f2daee4af803c6831d2682205', 206144)}
if len({a['record_id'] for a in new})!=6 or {a['record_id'] for a in new}!=set(APPROVED_RAW):
 raise ValueError('selected raw source IDs differ')
for a in new:
 if (a['archive_path'],a['sha256'],a['size_bytes'])!=APPROVED_RAW[a['record_id']]:
  raise ValueError('selected raw source identity differs')
if len(new)!=6:raise ValueError('expected six new originals')
for a in new:
 if hashasset(R/a['archive_path'])!=(a['sha256'],a['size_bytes']):raise ValueError('new original differs')
 add(a['archive_path'],'new raw original exact appended manifest',(a['sha256'],a['size_bytes']))
# Bind snapshot contents to previously reviewed custody, not a directory crawl.
fee='research/local_review/chaffee-planning-fees-intake-2026-09-13/prepared-transaction/'
fee_plan=bound_json(fee+'PREPARATION.json')
if expected_identities[fee+'PREPARATION.json'][0]!='a25b2071c9275af9b7299edf198b96870a79ba5ac8e0c412f6b8647774d683ca':
 raise ValueError('fee preparation changed')
fee_snapshot='_SNAPSHOTS/CHAFFEE-20260913T170209370066Z/'
for a in fee_plan['baseline']:
 if a['repository_path'] in {manifest,'_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json'}:
  pin=a['preserved'];add(fee_snapshot+a['repository_path'],'actual fee-intake preimage snapshot',(pin['sha256'],pin['size_bytes']))
prefix='research/local_review/manual-source-review-inventory-2026-09-11/'
ordinary_raw=(B/'ptolemy-inventory69-packaging-audit/UNTRACKED_ORDINARY.json').read_bytes()
if sha256(ordinary_raw).hexdigest()!='caadb14d9eb61a67a1e81afa78265fd627aec626ffce464dcc30c8cff14ed7fe':
 raise ValueError('independent ordinary-payload proposal changed')
for a in json.loads(ordinary_raw)['files']:
 if a['path'].startswith(prefix):
  add(a['path'],'previous independent inventory packaging pin',(a['sha256'],a['size_bytes']))
installed='research/local_review/manual-inventory-final-fee-code-integration-2026-09-13/'
receipt=bound_json(installed+'execution/RECEIPT.json')
receipt_schema=bound_json(installed+'execution/RECEIPT.schema.json')
jsonschema.validate(receipt,receipt_schema)
if expected_identities[installed+'execution/RECEIPT.json'][0]!='dbc0aa616f217dca664cfbbc587d22d3ae2f5cb57289c99188391b74a8bd6cde':
 raise ValueError('final inventory installation differs')
for a in receipt['targets']:
 pin=a['after'];add(a['repository_path'],'root-reviewed final inventory installation',(pin['sha256'],pin['size_bytes']))
preimage=bound_json(installed+'preparation/PREIMAGE_RECEIPT.json')
jsonschema.validate(preimage,bound_json(installed+'preparation/PREIMAGE_RECEIPT.schema.json'))
for a in preimage['files']:
 add(receipt['snapshot_directory']+'/'+Path(a['repository_path']).name,'final inventory exact preimage',(a['sha256'],a['size_bytes']))
unknown_inventory=[]
for item in git('ls-files','--others','--exclude-standard','-z','--',prefix).split(b'\0'):
 if item and item.decode() not in selected:unknown_inventory.append(item.decode())
if unknown_inventory:raise ValueError('unbound inventory files require review: '+repr(unknown_inventory))
# A future CI installation must itself be bound by its closed wrapper and exact schema.
ci_files=set()
ci='research/local_review/manual-watch-ci-integration-2026-09-13/INSTALLATION.json'
if not (R/ci).is_file():raise ValueError('reviewed CI installation absent')
if (R/ci).exists():
 for pin in [approval['installation'],approval['installation_schema']]:
  if expected_identities.get(pin['path'])!=(pin['sha256'],pin['size_bytes']):raise ValueError('final CI receipt/schema pin differs')
 d=bound_json(ci);ci_schema=bound_json(ci.removesuffix('.json')+'.schema.json')
 jsonschema.validate(d,ci_schema)
 for a in d['installed_files']:
  if a['path'] in ci_files:raise ValueError('duplicate CI installed path')
  ci_files.add(a['path'])
  add(a['path'],'root-reviewed CI installation',(a['sha256'],a['size_bytes']))
allowed={'_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json',manifest,'geode/constants.py','geode/pipeline/manual_review_inventory.py','geode/schemas/validators.py',prefix+'README.md',prefix+'inventory.json',prefix+'join-plan.json','tests/test_manual_review_inventory.py'}
for b in git('diff','--name-only','-z','HEAD','--').split(b'\0'):
 if b:
  rel=b.decode()
  if rel not in allowed|ci_files:raise ValueError('unreviewed maintained change '+rel)
  add(rel,'explicit maintained change snapshot',expected_identities.get(rel,hashasset(R/rel)))
add('tests/test_chaffee_source_path.py','reviewed publisher-path regression tests',('01088333afd68e8b9fe9d61156725cc0505bb7e9c59a7296c90a54d9d1248f6e',(R/'tests/test_chaffee_source_path.py').stat().st_size))
paths=sorted(selected)
cp=subprocess.run(['git','check-ignore','--no-index','--stdin','-z'],cwd=R,input=b'\0'.join(p.encode() for p in paths)+b'\0',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if cp.returncode not in [0,1]:raise ValueError('check-ignore failed')
ignored={b.decode() for b in cp.stdout.split(b'\0') if b}
assets=[]
for rel in paths:
 h,n=hashasset(R/rel)
 if (h,n)!=expected_identities[rel]:raise ValueError('final identity drift '+rel)
 if n>50_000_000:raise ValueError('oversized review payload '+rel)
 assets.append(Asset(path=rel,sha256=h,size_bytes=n,tracked=rel in tracked,ignored=rel in ignored,basis=sorted(selected[rel])))
if git('rev-parse','HEAD').decode().strip()!=BASELINE_HEAD:raise ValueError('HEAD changed during scan')
scan=Scan(status='prepared_exact_paths_not_staged',recorded_at=datetime.now(timezone.utc).isoformat(),head=git('rev-parse','HEAD').decode().strip(),wrappers=wrappers,new_raw_originals=len(new),files=assets,excluded_user_paths=['docs/audits/PROJECT_STATUS_2026-09-09.md','geode/schemas/models 2.py'],qualifications=['Closed root wrapper inventories authenticate exact bytes, not correctness of every historical claim or every failed historical test.','The one SH004 hash-bound .pyc remains non-executed historical evidence; unbound caches are excluded.','Paths and hashes are this scan snapshot, not proof of later staging or remote publication.'])
(dst/'SCAN.json').write_text(scan.model_dump_json(indent=2)+'\n')
(dst/'paths.nul').write_bytes(b'\0'.join(p.encode() for p in paths)+b'\0')
(dst/'force-add.nul').write_bytes(b'\0'.join(a.path.encode() for a in assets if a.ignored and not a.tracked)+b'\0')
print(json.dumps({'wrappers':wrappers,'files':len(assets),'bytes':sum(a.size_bytes for a in assets),'ignored_untracked':sum(a.ignored and not a.tracked for a in assets),'new_originals':len(new),'scan_sha256':hashasset(dst/'SCAN.json')[0]},indent=2))
