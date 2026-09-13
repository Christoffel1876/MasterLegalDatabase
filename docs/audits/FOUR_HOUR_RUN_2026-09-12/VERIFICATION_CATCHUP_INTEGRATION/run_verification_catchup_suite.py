"""Record the final installed suite with stable code/test hashes before and after."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from typing import Literal
from pydantic import BaseModel, ConfigDict

ROOT = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
OUT = ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/VERIFICATION_CATCHUP_INTEGRATION'
PYTHON = '/private/tmp/geode-status-venv/bin/python'

class Run(BaseModel):
    """Observed suite outcome and the exact code/test snapshot it exercised."""
    model_config=ConfigDict(extra='forbid',strict=True)
    started_at: datetime
    finished_at: datetime | None=None
    command: list[str]
    status: Literal['running','passed','failed','code_changed_during_run']
    code_test_hashes: dict[str,str]
    changed_during_run: list[str]=[]
    exit_code: int | None=None
    log_sha256: str | None=None
    coverage_sha256: str | None=None

def pins() -> dict[str,str]:
    paths=sorted([p for prefix in ['geode','tests','scripts'] for p in (ROOT/prefix).rglob('*.py') if '__pycache__' not in p.parts])
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def save(path:Path,raw:bytes) -> None:
    if path.exists():raise ValueError('Existing execution result')
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('xb') as handle:handle.write(raw)
    os.replace(tmp,path)

def main() -> None:
    from importlib import import_module
    sys.path.insert(0,str(ROOT))
    inventory=import_module('geode.pipeline.manual_review_inventory')
    inventory.check_inventory(ROOT,inventory.build_inventory(ROOT))
    measured=json.loads((ROOT/inventory.PACKAGE/'inventory.json').read_bytes())
    if (len(measured['sources']),measured['rows_with_review'],measured['rows_without_review'])!=(64,27,37):
        raise ValueError('Final approved inventory is not installed')
    before=pins();OUT.mkdir()
    cmd=[PYTHON,'-B','-m','pytest','tests/','-q','-p','no:cacheprovider',
         '--basetemp=/private/tmp/geode-verification-catchup-integration','--cov=geode',
         '--cov=scripts.research_source_lookup','--cov-branch',
         '--cov-report=json:'+str(OUT/'coverage.json'),'--cov-report=term-missing']
    begin=Run(started_at=datetime.now(timezone.utc),command=cmd,status='running',code_test_hashes=before)
    save(OUT/'RUN.schema.json',(json.dumps(Run.model_json_schema(),indent=2)+'\n').encode())
    save(OUT/'START.json',(begin.model_dump_json(indent=2)+'\n').encode())
    save(OUT/Path(__file__).name,Path(__file__).read_bytes())
    with (OUT/'pytest.log').open('xb') as log:
        result=subprocess.run(cmd,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',
            'COVERAGE_FILE':'/private/tmp/geode-verification-catchup-integration.coverage'},stdout=log,stderr=subprocess.STDOUT)
    after=pins();changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
    raw=(OUT/'pytest.log').read_bytes();coverage=OUT/'coverage.json'
    final=Run(started_at=begin.started_at,finished_at=datetime.now(timezone.utc),command=cmd,
        status='code_changed_during_run' if changed else ('passed' if result.returncode==0 else 'failed'),
        code_test_hashes=before,changed_during_run=changed,exit_code=result.returncode,
        log_sha256=hashlib.sha256(raw).hexdigest(),
        coverage_sha256=hashlib.sha256(coverage.read_bytes()).hexdigest() if coverage.exists() else None)
    save(OUT/'RESULT.json',(final.model_dump_json(indent=2)+'\n').encode())
    print(final.model_dump_json(indent=2,exclude={'code_test_hashes'}))
    print(raw.decode(errors='replace')[-1800:])
    raise SystemExit(0 if final.status=='passed' else 1)

if __name__=='__main__': main()
