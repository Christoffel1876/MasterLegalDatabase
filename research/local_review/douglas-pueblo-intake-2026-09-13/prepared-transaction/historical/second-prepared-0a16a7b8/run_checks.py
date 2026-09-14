"""Run only isolated fixture tests and read-only real preparation checks."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import os,subprocess,sys,json,hashlib
from pydantic import BaseModel,ConfigDict
BASE=Path(__file__).resolve().parent
class Attempt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 command:list[str];cwd:str;started_at:str;completed_at:str;returncode:int;stdout_sha256:str;stderr_sha256:str;production_writes:Literal[0];public_requests:Literal[0]
def run(name,args):
 dest=BASE/'validation'/name;dest.mkdir(parents=True,exist_ok=False)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',COVERAGE_FILE='/private/tmp/final-two-source-intake.coverage')
 start=datetime.now(timezone.utc).isoformat();p=subprocess.run(args,cwd=BASE,env=env,capture_output=True,timeout=120)
 (dest/'stdout.txt').write_bytes(p.stdout);(dest/'stderr.txt').write_bytes(p.stderr)
 record=Attempt(command=args,cwd=str(BASE),started_at=start,completed_at=datetime.now(timezone.utc).isoformat(),returncode=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest(),production_writes=0,public_requests=0)
 (dest/'ATTEMPT.json').write_text(record.model_dump_json(indent=2)+'\n')
 (dest/'ATTEMPT.schema.json').write_text(json.dumps(Attempt.model_json_schema(),indent=2)+'\n')
 print(name,p.returncode,p.stdout.decode()[-1700:],p.stderr.decode()[-1000:])
 if p.returncode:raise SystemExit(p.returncode)
run('final-focused',[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','test_transaction.py','--cov=transaction','--cov-branch','--cov-report=term-missing','--cov-report=json:validation/final-focused/coverage.json'])
run('actual-read-only',[sys.executable,'-B','validate_preparation.py','--live'])
run('actual-cli-dry-run',[sys.executable,'-B','transaction.py','--dry-run'])
