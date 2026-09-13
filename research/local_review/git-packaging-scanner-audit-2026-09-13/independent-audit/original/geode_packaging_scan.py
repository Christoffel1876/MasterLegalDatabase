"""Read-only explicit packaging scan of this session's approved repository evidence."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
import argparse, json, subprocess
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
dst=B/'atlas-final-packaging'/args.name;dst.mkdir(parents=True,exist_ok=False)
(dst/'SCAN.schema.json').write_text(json.dumps(Scan.model_json_schema(),indent=2)+'\n')
tracked={p.decode() for p in git('ls-files','-z').split(b'\0') if p}
selected:dict[str,set[str]]={}
def add(rel:str,basis:str)->None:
 p=Path(rel)
 if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe path')
 if rel in ['docs/audits/PROJECT_STATUS_2026-09-09.md','geode/schemas/models 2.py']:raise ValueError('user path')
 selected.setdefault(rel,set()).add(basis)
wrappers=0
for inv in sorted((R/'research/local_review').glob('*/INVENTORY.json')):
 if inv.relative_to(R).as_posix().casefold() in {x.casefold() for x in tracked}:continue
 root=inv.parent;obj=json.loads(inv.read_bytes());jsonschema.validate(obj,json.loads((root/'INVENTORY.schema.json').read_bytes()))
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
  add(p.relative_to(R).as_posix(),'closed wrapper '+root.name)
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
 if any(p.is_symlink() for p in root.rglob('*')) or actual != expected|{'INVENTORY.json'}:raise ValueError('wrapper closure '+str(root))
 add(inv.relative_to(R).as_posix(),'closed wrapper inventory');wrappers+=1
# Previously independently reviewed exact ignored candidates retain their published hashes.
prior=json.loads((B/'ptolemy-inventory69-packaging-audit/NEEDED_FORCE_ADD.json').read_bytes())
for a in prior['files']:
 if hashasset(R/a['path'])!=(a['sha256'],a['size_bytes']):raise ValueError('prior packaging member changed')
 add(a['path'],'independent packaging audit pin')
manifest='_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
old=git('show','HEAD:'+manifest);now=(R/manifest).read_bytes()
if not now.startswith(old):raise ValueError('raw manifest not exact append')
new=[json.loads(line) for line in now[len(old):].splitlines()]
if len(new)!=6:raise ValueError('expected six new originals')
for a in new:
 if hashasset(R/a['archive_path'])!=(a['sha256'],a['size_bytes']):raise ValueError('new original differs')
 add(a['archive_path'],'new raw original exact appended manifest')
# Actual fee-intake snapshot was taken after the earlier packaging audit.
for root in [R/'_SNAPSHOTS/CHAFFEE-20260913T170209370066Z']:
 for p in root.rglob('*'):
  if p.is_file():add(p.relative_to(R).as_posix(),'actual fee-intake preimage snapshot')
# Inventory snapshots/installation records belong to the reviewed maintained package.
prefix='research/local_review/manual-source-review-inventory-2026-09-11/'
for b in git('ls-files','--others','--exclude-standard','-z','--',prefix).split(b'\0'):
 if b:add(b.decode(),'reviewed inventory installation and preimages')
allowed={'_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json',manifest,'geode/constants.py','geode/pipeline/manual_review_inventory.py','geode/schemas/validators.py',prefix+'README.md',prefix+'inventory.json',prefix+'join-plan.json','tests/test_manual_review_inventory.py'}
for b in git('diff','--name-only','-z','HEAD','--').split(b'\0'):
 if b:
  rel=b.decode()
  if rel not in allowed:raise ValueError('unreviewed maintained change '+rel)
  add(rel,'reviewed maintained change')
add('tests/test_chaffee_source_path.py','reviewed publisher-path regression tests')
# CI files are included only when the root installation receipt explicitly exists.
ci=R/'research/local_review/manual-watch-ci-integration-2026-09-13/INSTALLATION.json'
if ci.exists():
 d=json.loads(ci.read_bytes())
 for a in d['installed_files']:
  if hashasset(R/a['path'])!=(a['sha256'],a['size_bytes']):raise ValueError('installed CI differs')
  add(a['path'],'root-reviewed CI installation')
paths=sorted(selected)
cp=subprocess.run(['git','check-ignore','--no-index','--stdin','-z'],cwd=R,input=b'\0'.join(p.encode() for p in paths)+b'\0',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if cp.returncode not in [0,1]:raise ValueError('check-ignore failed')
ignored={b.decode() for b in cp.stdout.split(b'\0') if b}
assets=[]
for rel in paths:
 h,n=hashasset(R/rel)
 if n>50_000_000:raise ValueError('oversized review payload '+rel)
 assets.append(Asset(path=rel,sha256=h,size_bytes=n,tracked=rel in tracked,ignored=rel in ignored,basis=sorted(selected[rel])))
scan=Scan(status='prepared_exact_paths_not_staged',recorded_at=datetime.now(timezone.utc).isoformat(),head=git('rev-parse','HEAD').decode().strip(),wrappers=wrappers,new_raw_originals=len(new),files=assets,excluded_user_paths=['docs/audits/PROJECT_STATUS_2026-09-09.md','geode/schemas/models 2.py'],qualifications=['Closed root wrapper inventories authenticate exact bytes, not correctness of every historical claim or every failed historical test.','The one SH004 hash-bound .pyc remains non-executed historical evidence; unbound caches are excluded.','Paths and hashes are this scan snapshot, not proof of later staging or remote publication.'])
(dst/'SCAN.json').write_text(scan.model_dump_json(indent=2)+'\n')
(dst/'paths.nul').write_bytes(b'\0'.join(p.encode() for p in paths)+b'\0')
(dst/'force-add.nul').write_bytes(b'\0'.join(a.path.encode() for a in assets if a.ignored and not a.tracked)+b'\0')
print(json.dumps({'wrappers':wrappers,'files':len(assets),'bytes':sum(a.size_bytes for a in assets),'ignored_untracked':sum(a.ignored and not a.tracked for a in assets),'new_originals':len(new),'scan_sha256':hashasset(dst/'SCAN.json')[0]},indent=2))
