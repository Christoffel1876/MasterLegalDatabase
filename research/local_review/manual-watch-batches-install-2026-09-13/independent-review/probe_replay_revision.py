"""Offline replay counterexample using temporary copies and explicit fixture clocks."""
from pathlib import Path
from datetime import timedelta
import importlib.util
import hashlib
import json
import socket
import sys
import tempfile

BASE=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/manual-watch-expansion-revision')
assert hashlib.sha256((BASE/'FINAL_MANIFEST.json').read_bytes()).hexdigest() == 'ef2d664301fa00935100307628ec5ac0317bfd622480dc79c0d92ce44b8b159f', 'Frozen input package changed; do not treat as same reproduction'
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from load_proposed import load
w=load()
sys.path.insert(0,str(BASE/'proposed/tests'))
import test_manual_source_watch_batches as fixtures

def no_network(*args,**kwargs):raise AssertionError('No public network in independent fixture')
socket.getaddrinfo=no_network
w.g.transport=no_network

def put(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def ref(root,path):return w.g.file_ref(root,path).model_dump(mode='json')

def run_case(kind):
 with tempfile.TemporaryDirectory(prefix='watch-replay-audit-',dir='/private/tmp') as td:
  root=fixtures.packet.__wrapped__(Path(td));path=root/w.SELECTION
  plan=w.load_plan(path);output=root/w.RUNTIME/'independent-fixture'
  clock=lambda:fixtures.NOW
  calls=[]
  samehost=plan.targets[0].url+'?observed-fixture-redirect=1'
  responses=[fixtures.Response(b'',302,{'location':samehost}), fixtures.Response((root/plan.targets[0].baseline.path).read_bytes()),fixtures.Response((root/plan.targets[1].baseline.path).read_bytes())]
  def fetch(url,*args):calls.append(url);return responses.pop(0)
  report=w.run_watch(path,output,fixtures.NOW,w.g.sha(path),clock=clock,fetch=fetch)
  assert report.status=='completed' and len(calls)==3
  original=w.verify_run(path,output)
  event1=output/'events/0001';event2=output/'events/0002'
  if kind=='cross_host_redirect':
   foreign=plan.targets[1].url+'?forged-cross-authority=1'
   head=json.loads((event1/'public-headers.json').read_bytes());head['headers']['location']=foreign;put(event1/'public-headers.json',head)
   result=json.loads((event1/'result.json').read_bytes());result['redirect_url']=foreign;result['public_headers']=ref(output,event1/'public-headers.json');put(event1/'result.json',result)
   reservation=json.loads((event2/'reservation.json').read_bytes());reservation['url']=foreign;put(event2/'reservation.json',reservation)
   head=json.loads((event2/'public-headers.json').read_bytes());head['request_url']=foreign;put(event2/'public-headers.json',head)
   result=json.loads((event2/'result.json').read_bytes());result['reservation_sha256']=w.g.sha(event2/'reservation.json');result['public_headers']=ref(output,event2/'public-headers.json');put(event2/'result.json',result)
  elif kind=='request_deadline_extension':
   reservation=json.loads((event2/'reservation.json').read_bytes());reservation['deadline']=(fixtures.NOW+timedelta(seconds=200)).isoformat();put(event2/'reservation.json',reservation)
   result=json.loads((event2/'result.json').read_bytes());result['reservation_sha256']=w.g.sha(event2/'reservation.json');result['finished_at']=(fixtures.NOW+timedelta(seconds=70)).isoformat();put(event2/'result.json',result)
   event3=output/'events/0003'
   reservation=json.loads((event3/'reservation.json').read_bytes());reservation['reserved_at']=(fixtures.NOW+timedelta(seconds=70)).isoformat();reservation['deadline']=(fixtures.NOW+timedelta(seconds=100)).isoformat();put(event3/'reservation.json',reservation)
   result=json.loads((event3/'result.json').read_bytes());result['reservation_sha256']=w.g.sha(event3/'reservation.json');result['finished_at']=(fixtures.NOW+timedelta(seconds=70)).isoformat();put(event3/'result.json',result)
  elif kind=='redirect_limit_narrowing':
   raise NotImplementedError
  # Rebuild only observations and accounting from edited fixture events; no fetch is possible.
  guard=w.WatchGuard(path,output,clock=clock,fetch=no_network)
  pairs=[(w.g.Reservation.model_validate_json(p.read_bytes()), w.g.Result.model_validate_json((p.parent/'result.json').read_bytes())) for p in sorted(output.glob('events/*/reservation.json'))];edited=json.loads((output/'report.json').read_bytes())
  edited['observations']=[w.observation(t,pairs,output).model_dump(mode='json') for t in guard.plan.targets]
  edited['state']=guard.state(pairs).model_dump(mode='json')
  if kind=='request_deadline_extension':edited['generated_at']=(fixtures.NOW+timedelta(seconds=70)).isoformat()
  put(output/'report.json',edited)
  (output/'RUN_MANIFEST.json').unlink();w.seal(output,'run')
  try:
   checked=w.verify_run(path,output)
   return {'case':kind,'result':'ACCEPTED','status':checked.status,'responses':[o.response_url for o in checked.observations], 'public_requests':0,'clock_basis':'injected fixture, dispatch 2026-09-13T00:10:00Z; deadline case alters event/report times to +70 seconds','original_event_count':len(calls),'changed_fixture_only':True}
  except Exception as error:
   return {'case':kind,'result':'REJECTED','error':type(error).__name__+': '+str(error),'public_requests':0}

if __name__=='__main__':
 print(json.dumps([run_case(x) for x in ['cross_host_redirect','request_deadline_extension']],indent=2))
