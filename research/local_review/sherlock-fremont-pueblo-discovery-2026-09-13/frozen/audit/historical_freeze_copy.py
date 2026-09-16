from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
from typing import Literal
from pydantic import BaseModel,ConfigDict,AwareDatetime,Field
class Ref(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 path:str;sha256:str=Field(pattern=r'^[a-f0-9]{64}$');size_bytes:int
class Receipt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 captured_at:AwareDatetime;source_root:str;frozen_root:str;files:list[Ref];public_requests:Literal[0];source_membership_unchanged:Literal[True];scope_note:str
base=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run')
source=base/'sherlock-sh-ext-001/deliveries/20260913T013245Z'
out=base/'sherlock-sh-ext-001-atlas-audit'
def inventory(root):
 refs=[]
 for p in sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix()):
  if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('nonordinary')
  if p.is_file():refs.append(Ref(path=p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size))
 return refs
before=inventory(source);shutil.copytree(source,out/'received');after=inventory(source)
assert before==after==inventory(out/'received')
receipt=Receipt(captured_at=datetime.now(timezone.utc),source_root=str(source),frozen_root=str(out/'received'),files=before,public_requests=0,source_membership_unchanged=True,scope_note='Exact current received tree, including separate reconciliation-R1 subfolder. This audit evaluates initial discovery; R1 is retained separately without rewriting initial records.')
(out/'CUSTODY_RECEIPT.json').write_text(receipt.model_dump_json(indent=2)+'\n')
(out/'CUSTODY_RECEIPT.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
print(len(before),sum(r.size_bytes for r in before),hashlib.sha256((out/'CUSTODY_RECEIPT.json').read_bytes()).hexdigest())
for name in ['models.py','validate_templates.py','INSTRUCTIONS.md','FINAL_MANIFEST.json','COMPARISON.json']:
 p=base/'sherlock-sh-ext-001'/name;target=out/'input-protocol'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
shutil.copytree(base/'sherlock-sh-ext-001/schemas',out/'input-protocol/schemas')
