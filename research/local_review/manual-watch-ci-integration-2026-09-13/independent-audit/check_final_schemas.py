from pathlib import Path
import hashlib, importlib.util, json, sys
p=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/popper-manual-watch-ci-public-audit')
f=p/'final';script=f/'scripts/manual_source_watch_ci.py'
assert hashlib.sha256(script.read_bytes()).hexdigest()=='09fc26756c7432af64c65b48ad8b08080c0cf1d5353456b587062386c65135df'
spec=importlib.util.spec_from_file_location('final87_schema_export',script)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
for cls,name in [(m.Plan,'manual_source_watch_ci.schema.json'),(m.Summary,'manual_source_watch_ci-summary.schema.json'),(m.ProcessReceipt,'manual_source_watch_ci-process.schema.json'),(m.ProgressSnapshot,'manual_source_watch_ci-progress.schema.json')]:
 assert cls.model_json_schema()==json.loads((f/'config'/name).read_bytes()),name
summary=m.Summary.model_validate_json((p/'actual-readiness/summary.json').read_bytes())
assert summary.status=='ready' and not summary.execution_requested and len(summary.pairs)==4
for path in (p/'actual-readiness').glob('*.process.json'):
 r=m.ProcessReceipt.model_validate_json(path.read_bytes());assert r.exit_code==0 and not r.retried
assert len(list((p/'actual-readiness').glob('*.process.json')))==4
assert hashlib.sha256((f/'.github/workflows/manual-source-watch-daily.yml').read_bytes()).hexdigest()=='b2a7eabf2dcb5e627ddf22033bbde74af75fe738581737cd38e6b28599bd4b0e'
print('Four final schema exports exact; four actual read-only subprocess receipts typed and exit0; unchanged reviewed workflow digest exact.')
print('These local schema/process checks do not certify Linux execution, scheduler activation or source access.')
