"""Hash every selected staged blob before permitting the local checkpoint commit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from pydantic import BaseModel,ConfigDict
BASE=Path('/Users/mcoors/Documents/Project Geode');ROOT=BASE/'MasterLegalDatabase'
RUN=BASE/'handoffs/run-2026-09-12'
class Receipt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 checked_at:str
 status:str
 prepared_record_sha256:str
 selected_files:int
 staged_changed_files:int
 selected_stored_bytes:int
 all_index_blobs_match:bool
 index_changed_paths_within_selection:bool
 untracked_user_files_excluded:bool
 head_before_commit:str
p=ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/FINAL_RUN_CHECKPOINT/PREPARATION.json'
prep=json.loads(p.read_bytes())
expected={r['path']:(r['sha256'],r['size_bytes']) for r in prep['files']}
for name in ['PREPARATION.json','PREPARATION.schema.json']:
 q=p.parent/name;raw=q.read_bytes();expected[q.relative_to(ROOT).as_posix()]=(hashlib.sha256(raw).hexdigest(),len(raw))
selected={x.decode() for x in (RUN/'final-checkpoint-pathspec.nul').read_bytes().split(b'\0') if x}
assert set(expected)==selected
changed={x.decode() for x in subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0') if x}
assert changed<=selected
index={}
for row in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
 if not row:continue
 meta,path=row.split(b'\t',1);mode,oid,stage=meta.decode().split()
 if path.decode() in selected:
  assert stage=='0' and mode in ['100644','100755'];index[path.decode()]=oid
assert set(index)==selected
process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
for name in sorted(selected):
 process.stdin.write((index[name]+'\n').encode());process.stdin.flush()
 header=process.stdout.readline().decode().split();assert header[1]=='blob'
 length=int(header[2]);assert length==expected[name][1],name
 remaining=length;digest=hashlib.sha256()
 while remaining:
  chunk=process.stdout.read(min(remaining,1024*1024));assert chunk;digest.update(chunk);remaining-=len(chunk)
 assert process.stdout.read(1)==b'\n'
 assert digest.hexdigest()==expected[name][0],name
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected[name][0],name
process.stdin.close();assert process.wait()==0
assert not {'docs/audits/PROJECT_STATUS_2026-09-09.md','geode/schemas/models 2.py'} & selected
receipt=Receipt(checked_at=datetime.now(timezone.utc).isoformat(),status='passed_before_local_commit',prepared_record_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),selected_files=len(selected),staged_changed_files=len(changed),selected_stored_bytes=sum(v[1] for v in expected.values()),all_index_blobs_match=True,index_changed_paths_within_selection=True,untracked_user_files_excluded=True,head_before_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip())
for name,value in [('FINAL_INDEX_VERIFICATION.schema.json',Receipt.model_json_schema()),('FINAL_INDEX_VERIFICATION.json',receipt.model_dump())]:
 dest=RUN/name;assert not dest.exists();dest.write_text(json.dumps(value,indent=2)+'\n')
print(receipt.model_dump_json())
