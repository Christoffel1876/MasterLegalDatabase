"""One-time focused validation run recorder; never called by the read-only validator."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import subprocess,os,json,shutil
from review_models import TestReceipt,Asset
r=Path(__file__).resolve().parent
cmd=['/private/tmp/geode-status-venv/bin/python','-B','-m','pytest',str(r/'test_review.py'),'-q','-p','no:cacheprovider']
result=subprocess.run(cmd,cwd='/private/tmp',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
for name in ['focused-tests.log','TEST_RECEIPT.json','TEST_RECEIPT.schema.json']:
 p=r/name
 if p.exists():
  pre=r/'preparation-preimages'/sha256(p.read_bytes()).hexdigest();pre.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,pre/name)
log=r/'focused-tests.log';log.write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr)
if result.returncode:raise SystemExit(result.returncode)
receipt=TestReceipt(run_at=datetime.now(timezone.utc).isoformat(),command=cmd,exit_code=0,log=Asset(path='focused-tests.log',sha256=sha256(log.read_bytes()).hexdigest(),size_bytes=log.stat().st_size),coverage_note='Focused offline semantic mutation tests; no claim that tests establish source accuracy or legal currentness.')
(r/'TEST_RECEIPT.json').write_text(receipt.model_dump_json(indent=2)+'\n');(r/'TEST_RECEIPT.schema.json').write_text(json.dumps(TestReceipt.model_json_schema(),indent=2)+'\n')
