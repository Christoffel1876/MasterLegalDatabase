"""Offline captured-buffer counterexample, modifying only an isolated evidence copy."""
from pathlib import Path
import importlib.util
import hashlib
import json
import shutil
import socket
import sys
import tempfile

BASE=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/douglas-pueblo-lookups-revision-1')
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
assert hashlib.sha256((BASE/'proposed/research_source_lookup.py').read_bytes()).hexdigest()=='4b3f084eb9bf9a20f3e5c7b7c0c25a3b1bbbfe0de05caff9b626100808dbad6f'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('independent_dp_lookup',BASE/'proposed/research_source_lookup.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
def no_network(*args,**kwargs):raise AssertionError('Independent audit makes no network requests')
socket.getaddrinfo=no_network

def copy_evidence(destination):
 for c in m.DP_SOURCES.values():
  rel=Path('research/local_review')/c['folder'];shutil.copytree(ROOT/rel,destination/rel)
  rel=Path('docs/audits/FOUR_HOUR_RUN_2026-09-12')/c['acceptance']/'ACCEPTANCE.json';(destination/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,destination/rel)
 relatives=['execution/RECEIPT.json','execution/INTENT.json','execution/records.jsonl','evidence/preparation/source-provenance.jsonl']
 for source,c in m.DP_SOURCES.items():relatives.append('evidence/preparation/custody/'+source+'/'+c['event']+'/event.json')
 for name in relatives:
  dest=destination/m.DP_INTAKE/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/m.DP_INTAKE/name,dest)
 rel=Path('_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl');(destination/rel).parent.mkdir(parents=True,exist_ok=True)
 with (ROOT/rel).open('rb') as f,(destination/rel).open('wb') as out:
  for line in f:
   record=json.loads(line)
   if record['record_id'] in m.DP_SOURCES:
    out.write(line);dest=destination/record['archive_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/record['archive_path'],dest)

if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='lookup-late-qa-',dir='/private/tmp') as td:
  root=Path(td)/'fixture';copy_evidence(root)
  checked=m._check_dp_package;calls=[];source=m.DOUGLAS_SOURCE_ID
  path=root/'research/local_review'/m.DP_SOURCES[source]['folder']/'SOURCE_QA.json'
  expected=hashlib.sha256(path.read_bytes()).hexdigest()
  def mutate_after_check(*args,**kwargs):
   result=checked(*args,**kwargs);calls.append(True)
   if len(calls)==2:
    data=json.loads(path.read_bytes());data['rows'][0]['cells'][-1]['displayed_text']='INJECTED UNVERIFIED FEE';path.write_text(json.dumps(data,indent=2)+'\n')
   return result
  m._check_dp_package=mutate_after_check
  try:
   result=m.lookup(root,source,'INJECTED UNVERIFIED FEE')
   output={'result':'ACCEPTED','status':result.status,'evidence_verified':result.evidence_verified,'row_ids':[r.row_id for r in result.rows],'displayed_fees':[r.cells[-1].displayed_text for r in result.rows],'native_fees':[r.cells[-1].native_text for r in result.rows],'expected_review_sha256':expected,'reported_review_sha256':result.source.review.sha256,'real_package_checks':len(calls),'public_requests':0,'mutated_only_temporary_copy':True}
  except Exception as error:output={'result':'REJECTED','error':type(error).__name__+': '+str(error),'public_requests':0}
  print(json.dumps(output,indent=2))
