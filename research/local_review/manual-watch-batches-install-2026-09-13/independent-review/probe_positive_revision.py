"""Local positive controls for the revised replay checks."""
from pathlib import Path
import tempfile,json
from probe_replay_revision import w,fixtures,no_network

def run():
 results=[]
 for narrow in [False,True]:
  with tempfile.TemporaryDirectory(prefix='watch-positive-',dir='/private/tmp') as td:
   root=fixtures.packet.__wrapped__(Path(td));path=root/w.SELECTION
   if narrow:
    raw=json.loads(path.read_bytes());raw['limits']['request_seconds']=3;raw['max_run_seconds']=20
    path.write_text(w.Plan.model_validate_json(json.dumps(raw)).model_dump_json())
   plan=w.load_plan(path);output=root/w.RUNTIME/'positive';calls=[]
   responses=[fixtures.Response(b'',302,{'location':plan.targets[0].url+'?fixture=1'}),fixtures.Response((root/plan.targets[0].baseline.path).read_bytes()),fixtures.Response((root/plan.targets[1].baseline.path).read_bytes())]
   def fetch(url,*args):calls.append(url);return responses.pop(0)
   report=w.run_watch(path,output,fixtures.NOW,w.g.sha(path),clock=lambda:fixtures.NOW,fetch=fetch)
   assert report.status=='completed' and [o.status for o in report.observations]==['unchanged','unchanged'] and len(calls)==3
   assert w.verify_run(path,output)==report
   frozen={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
   # Final-seal recovery never fetches and preserves existing event bodies.
   (output/'RUN_MANIFEST.json').unlink()
   repeated=w.run_watch(path,output,fixtures.NOW,w.g.sha(path),clock=lambda:fixtures.NOW,fetch=no_network)
   assert repeated==report
   assert frozen=={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
   other=root/w.SELECTIONS['western-fees-v1']
   try:w.run_watch(other,output,fixtures.NOW,w.g.sha(other),clock=lambda:fixtures.NOW,fetch=no_network)
   except ValueError:pass
   else:raise AssertionError('Cross-batch replay accepted')
   assert frozen=={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
   results.append({'narrower_limits':narrow,'same_host_redirect':'completed_three_fixture_calls','two_sources':'unchanged_exact_bytes','final_seal_recovery':'byte_identical_no_fetch','cross_batch':'rejected_no_change','public_requests':0})
 return results
if __name__=='__main__':print(json.dumps(run(),indent=2))
