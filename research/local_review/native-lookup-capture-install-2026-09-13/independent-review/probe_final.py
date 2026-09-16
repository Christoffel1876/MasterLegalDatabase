"""Offline reuse of frozen exploit cases against the exact prepared captured-buffer revision."""
from pathlib import Path
import importlib.util,hashlib,json,socket,sys,tempfile
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/native-lookup-captured-buffers')
R=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
EXPECTED='1f4da2ec117996c21a2676bdd82226018ecf4ad0e583297c1f52ece43d1ffe55'
code=B/'proposed/research_source_lookup.py'
assert hashlib.sha256(code.read_bytes()).hexdigest()==EXPECTED
sys.dont_write_bytecode=True

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s)
 sys.modules[name]=m;s.loader.exec_module(m);return m
m=load('independent_closeout_lookup',code)
p=load('independent_prior_probes',B/'prior-audit/probe_family.py');p.ROOT=R
socket.getaddrinfo=lambda *a,**k: (_ for _ in ()).throw(AssertionError('No network in audit'))
results=[]
with tempfile.TemporaryDirectory(prefix='lookup-closeout-',dir='/private/tmp') as td:
 root=Path(td);p.copy_fixture(m,root)
 for case in ['ehs_fee','ehs_image','springs_fee_native','weld_fee_association',
              'greeley_building_context','impact_fee','pif_fee','gj_custody','gj_fee_aba']:
  e=p.probe(m,root,case)
  assert e.status!='returned_injected_evidence',case
  assert e.source_files_restored_in_fixture
  results.append({'case':case,'status':e.status,'error':e.error,
     'verifier_calls':e.verification_calls,'checker_calls':e.checker_calls,
     'files_restored_in_fixture':e.source_files_restored_in_fixture})
normal=[]
for source in [m.SOURCE_ID,m.GREELEY_SOURCE_ID,m.WELD_SOURCE_ID,*m.GRID_SOURCES,m.SPRINGS_SOURCE_ID,m.EHS_SOURCE_ID,*m.DP_SOURCES]:
 result=m.lookup(R,source,list_rows=True)
 values={'json':result.model_dump_json(indent=2)+'\n','md':m.render_markdown(result)}
 for suffix,value in values.items():
  actual=value.replace(str(R),'__REPOSITORY__').encode()
  expected=(B/'fixtures/nine-native-sources'/(source+'.'+suffix)).read_bytes()
  assert actual==expected,(source,suffix)
  normal.append({'source_id':source,'format':suffix,'sha256':hashlib.sha256(actual).hexdigest(),'exact_fixture_equal':True})
assert hashlib.sha256(code.read_bytes()).hexdigest()==EXPECTED
print(json.dumps({'status':'PASS','script_sha256':EXPECTED,'cases':results,'normal_outputs':normal,
 'public_requests':0,'production_writes':0,
 'scope':'Replay of nine preserved historical exploit cases; no full suite or source QA.'},indent=2))
