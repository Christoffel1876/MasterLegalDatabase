from pathlib import Path
from datetime import datetime,timezone
import subprocess,sys,os,json,hashlib
r=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/ptolemy-chaffee-fee-intake-preparation')
sys.path.insert(0,str(r));from models import Preparation,CommandResult,Validation,Asset
plan=Preparation.model_validate_json((r/'PREPARATION.json').read_bytes());repo=r.parents[2]/'MasterLegalDatabase'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return Asset(path=p.relative_to(r).as_posix(),sha256=sha(p),size_bytes=p.stat().st_size)
before={b.repository_path:sha(repo/b.repository_path) for b in plan.baseline}
results=[]
commands=[('focused_tests',[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','test_transaction.py','--cov=transaction','--cov=models','--cov-branch','--cov-report=term-missing','--cov-report=json:'+str(r/'validation/final-coverage.json')]),('live_read_only_preflight',[sys.executable,'-B',str(r/'transaction.py'),'--dry-run','--root',str(repo)])]
for label,argv in commands:
 start=datetime.now(timezone.utc);env=os.environ.copy();env['COVERAGE_FILE']='/private/tmp/chaffee-fee-final.coverage'
 result=subprocess.run(argv,cwd=r,capture_output=True,env=env,timeout=180)
 end=datetime.now(timezone.utc)
 out=r/f'validation/{label}.stdout';err=r/f'validation/{label}.stderr';out.write_bytes(result.stdout);err.write_bytes(result.stderr)
 if result.returncode:sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr);raise SystemExit(result.returncode)
 results.append(CommandResult(label=label,command=argv,working_directory=str(r),started_at=start,completed_at=end,exit_code=0,stdout=ref(out),stderr=ref(err)))
after={b.repository_path:sha(repo/b.repository_path) for b in plan.baseline}
assert before==after and not(r/'execution').exists()
coverage=json.loads((r/'validation/final-coverage.json').read_bytes())
import re
count=int(re.search(rb'(\d+) passed', (r/'validation/focused_tests.stdout').read_bytes()).group(1))
record=Validation(status='passed_preparation_only',completed_at=datetime.now(timezone.utc),preparation_sha256=sha(r/'PREPARATION.json'),transaction_sha256=sha(r/'transaction.py'),results=results,test_count=count,combined_branch_inclusive_coverage_percent=coverage['totals']['percent_covered'],coverage=ref(r/'validation/final-coverage.json'),canonical_managed_sha256_before=before,canonical_managed_sha256_after=after,canonical_managed_bytes_unchanged=True,actual_execution_directory_created=False,limitations=['Temporary-fixture process interruption/replay only, not filesystem power-loss durability.','No network, source review or canonical application performed.','Original parent acquisition remains supplied historical evidence; actual redirect/PDF process times are separately observed.'])
(r/'VALIDATION.json').write_text(record.model_dump_json(indent=2)+'\n');(r/'VALIDATION.schema.json').write_text(json.dumps(Validation.model_json_schema(),indent=2)+'\n')
print(count,coverage['totals']['percent_covered'])
