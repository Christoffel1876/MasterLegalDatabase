"""One local focused test receipt, written only after tests finish."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,sys,hashlib,json,os
HERE=Path(__file__).absolute().parent;sys.path.insert(0,str(HERE))
from review_models import TamperResults
cmd=[sys.executable,'-B','-m','pytest','-p','no:cacheprovider','-q',str(HERE/'test_review.py')]
run=subprocess.run(cmd,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),cwd=HERE.parent,timeout=90)
print(run.stdout.decode());print(run.stderr.decode())
if run.returncode:raise SystemExit(run.returncode)
assert b'28 passed' in run.stdout
with (HERE/'focused-tests.log').open('xb') as f:f.write(run.stdout+run.stderr)
r=TamperResults(prepared_at=datetime.now(timezone.utc).isoformat(),command=cmd,tests_passed=28,tests_failed=0,receipt_scope='Offline integrity/refusal tests, not independent visual correctness.',stdout_sha256=hashlib.sha256(run.stdout+run.stderr).hexdigest())
b=(r.model_dump_json(indent=2)+'\n').encode();TamperResults.model_validate_json(b)
with (HERE/'TEST_RECEIPT.json').open('xb') as f:f.write(b)
with (HERE/'TEST_RECEIPT.schema.json').open('xb') as f:f.write((json.dumps(TamperResults.model_json_schema(),indent=2)+'\n').encode())
