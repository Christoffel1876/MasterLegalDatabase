"""Record local test execution; performs no source request or canonical write."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,os,hashlib
from typing import Literal
from pydantic import BaseModel,ConfigDict,AwareDatetime
BASE=Path(__file__).absolute().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from models import Asset


class Check(BaseModel):
    """Bind the exact bounded local verification invocation and results."""
    model_config=ConfigDict(extra='forbid',strict=True)
    status:Literal['passed']
    started_at:AwareDatetime
    completed_at:AwareDatetime
    command:list[str]
    cwd:str
    returncode:Literal[0]
    tests_passed:Literal[10]
    stdout:Asset
    stderr:Asset
    scope:Literal['offline custody/tamper checks; no new visual review or HTTP request']


def main()->None:
    """Run only this package's ten focused tests and retain exact output bytes."""
    command=[sys.executable,'-B','-m','pytest',str(BASE/'test_preservation.py'),'-q',
             '-p','no:cacheprovider','--basetemp=/private/tmp/greeley-fresh-preservation-tests']
    start=datetime.now(timezone.utc)
    result=subprocess.run(command,cwd='/private/tmp',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
                          capture_output=True,timeout=90)
    end=datetime.now(timezone.utc)
    refs=[]
    for label,data in [('stdout',result.stdout),('stderr',result.stderr)]:
        name='CHECKS.'+label+'.txt';path=BASE/name
        with path.open('xb') as out:out.write(data)
        refs.append(Asset(path=name,sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data)))
    assert result.returncode==0,result.stdout.decode()+result.stderr.decode()
    assert b'10 passed' in result.stdout
    check=Check(status='passed',started_at=start,completed_at=end,command=command,
                cwd='/private/tmp',returncode=0,tests_passed=10,stdout=refs[0],stderr=refs[1],
                scope='offline custody/tamper checks; no new visual review or HTTP request')
    for name,value in [('CHECKS.json',check.model_dump(mode='json')),
                       ('CHECKS.schema.json',Check.model_json_schema())]:
        with (BASE/name).open('x') as out:out.write(json.dumps(value,indent=2)+'\n')


if __name__=='__main__':main()
