from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
from pydantic import BaseModel,ConfigDict,Field
BASE=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run')
source=BASE/'sherlock-sh-ext-002/deliveries/20260913T015719Z'
prior=BASE/'sherlock-sh-ext-001-atlas-audit'
out=BASE/'sherlock-sh-ext-002-independent-audit'
class Asset(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 source_path:str;preserved_path:str;sha256:str=Field(pattern=r'^[a-f0-9]{64}$');size_bytes:int
class Custody(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 captured_at:str;delivery_original_path:str;assets:list[Asset];inventory_listed_payloads:int
 inventory_claims_verified:bool;unlisted_delivery_files:list[str];public_requests:int
assets=[]
def save(src,dst):
 if any(p.is_symlink() for p in [src,*src.parents]):raise ValueError('Symlink')
 raw=src.read_bytes();target=out/dst;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():raise ValueError('Duplicate preservation')
 tmp=target.with_name(target.name+'.tmp');tmp.write_bytes(raw);tmp.replace(target)
 if target.read_bytes()!=raw:raise ValueError('Copy differs')
 assets.append(Asset(source_path=str(src),preserved_path=str(dst),sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw)))
inv=json.loads((source/'ARTIFACT_INVENTORY.json').read_bytes());listed={a['path']:a for a in inv['files']}
for p in sorted(source.rglob('*')):
 if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('Nonordinary delivery')
 if not p.is_file():continue
 rel=p.relative_to(source).as_posix();raw=p.read_bytes()
 if rel in listed:
  a=listed[rel]
  if hashlib.sha256(raw).hexdigest()!=a['sha256'] or len(raw)!=a['size_bytes']:raise ValueError('Original inventory mismatch')
 save(p,Path('received')/rel)
for name in ['START_HERE.md']:
 save(BASE/'sherlock-sh-ext-002'/name,Path('authorization')/name)
for name in ['DIRECTED_PROPOSAL.json','DIRECTED_PROPOSAL.schema.json','FINAL_MANIFEST.json','AUDIT.json','CUSTODY_RECEIPT.json','REPORT.md','received/raw/SHEXT001-A031.html','received/results/SHEXT001-A031.json','received/reservations/SHEXT001-A031.json','received/headers/SHEXT001-A031.json']:
 if not(prior/name).is_file():print('MISSING optional parent',name);continue
 save(prior/name,Path('parent-audit')/name)
# Preserve the exact selected stream used by Sherlock; no source bytes are substituted.
save(BASE/'sherlock-sh-ext-001/comparison/pinned_commit/legacy-selected.jsonl',Path('comparison/prior-selected-1415.jsonl'))
now=datetime.now(timezone.utc).isoformat()
receipt=Custody(captured_at=now,delivery_original_path=str(source),assets=assets,inventory_listed_payloads=len(listed),inventory_claims_verified=True,unlisted_delivery_files=sorted({p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}-set(listed)),public_requests=0)
for name,value in [('CUSTODY_RECEIPT.json',receipt.model_dump(mode='json')),('CUSTODY_RECEIPT.schema.json',Custody.model_json_schema())]:
 raw=json.dumps(value,indent=2)+'\n'
 if name=='CUSTODY_RECEIPT.json':Custody.model_validate_json(raw)
 path=out/name;tmp=path.with_suffix('.tmp');tmp.write_text(raw);tmp.replace(path)
print('captured_at',now,'assets',len(assets),'delivery',len(listed)+len(receipt.unlisted_delivery_files))
