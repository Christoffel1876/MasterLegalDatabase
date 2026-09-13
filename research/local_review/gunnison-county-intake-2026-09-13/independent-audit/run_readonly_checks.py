from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import hashlib,json,subprocess
from pydantic import BaseModel,ConfigDict
P=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/popper-gunnison-intake-preparation')
A=P.parent/'plato-gunnison-intake-audit';R=P.parents[2]/'MasterLegalDatabase'
# The repository is a sibling of handoffs, not a child of this run.
R=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
class Event(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 name:str;command:list[str];started_at:str;finished_at:str;exit_code:int
 stdout_path:str;stdout_sha256:str;stderr_path:str;stderr_sha256:str
class Result(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 status:Literal['passed'];events:list[Event];managed_before:dict[str,str]
 managed_after:dict[str,str];execution_directory_present:Literal[False]
sha=lambda b:hashlib.sha256(b).hexdigest()
pins=json.loads((P/'VALIDATION.json').read_bytes())['canonical_managed_sha256_before']
def managed():return {p:sha((R/p).read_bytes()) for p in pins}
before=managed();events=[]
for name,args in [('seal',['validate_preparation.py']),('live-preflight',['transaction.py','--dry-run','--root',str(R)])]:
 cmd=['/private/tmp/geode-status-venv/bin/python','-B',str(P/args[0]),*args[1:]]
 start=datetime.now(timezone.utc).isoformat();s=subprocess.run(cmd,capture_output=True,timeout=120)
 for kind,data in [('stdout',s.stdout),('stderr',s.stderr)]:
  with (A/f'{name}.{kind}.txt').open('xb') as f:f.write(data)
 events.append(Event(name=name,command=cmd,started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),exit_code=s.returncode,stdout_path=f'{name}.stdout.txt',stdout_sha256=sha(s.stdout),stderr_path=f'{name}.stderr.txt',stderr_sha256=sha(s.stderr)))
 assert s.returncode==0,s.stderr
assert managed()==before and not (P/'execution').exists()
r=Result(status='passed',events=events,managed_before=before,managed_after=managed(),execution_directory_present=False)
for name,data in [('READ_ONLY_CHECKS.json',r.model_dump_json(indent=2)),('READ_ONLY_CHECKS.schema.json',json.dumps(Result.model_json_schema(),indent=2))]:
 with (A/name).open('x') as f:f.write(data+'\n')
print('read-only checks passed; seven canonical managed files unchanged')
