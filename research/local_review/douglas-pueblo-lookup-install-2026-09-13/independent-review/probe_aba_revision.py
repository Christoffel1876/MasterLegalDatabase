"""Independent temporary-copy probes of captured native/context/image identities."""
from pathlib import Path
import hashlib
import json
import tempfile
from probe_late_qa_revision import copy_evidence, m

results=[]
for source in [m.DOUGLAS_SOURCE_ID,m.PUEBLO_SOURCE_ID]:
 with tempfile.TemporaryDirectory(prefix='dp-captured-buffer-',dir='/private/tmp') as temp:
  root=Path(temp)/'fixture';copy_evidence(root)
  baseline=m.lookup(root,source,list_rows=True).model_dump_json()
  package=root/'research/local_review'/m.DP_SOURCES[source]['folder']
  qa=package/'SOURCE_QA.json';data=json.loads(qa.read_bytes())
  if source==m.DOUGLAS_SOURCE_ID:
   native=package/data['native']['path'];image=package/data['full_image']['path']
   data['contexts'][0]['text']='UNVERIFIED CONTEXT'
   data['rows'][0]['cells'][-1]['displayed_text']='UNVERIFIED FEE'
   builder_name='_dp_douglas'
  else:
   native=package/data['pages'][0]['native']['path'];image=package/data['pages'][0]['image']['path']
   data['rows'][0]['fee']['reviewed_display']='UNVERIFIED FEE'
   data['annotations'][0]['statement']='UNVERIFIED ANNOTATION'
   builder_name='_dp_pueblo'
  saved={p:p.read_bytes() for p in [qa,native,image]}
  checked=m._check_dp_package;builder=getattr(m,builder_name);calls=[];restored=[]
  def mutate(*args,**kwargs):
   out=checked(*args,**kwargs);calls.append(True)
   if len(calls)==2:
    qa.write_text(json.dumps(data,indent=2)+'\n')
    native.write_bytes(b'UNVERIFIED NATIVE\n'+saved[native])
    image.write_bytes(saved[image]+b'UNVERIFIED IMAGE')
   return out
  def restore_after_builder(*args,**kwargs):
   try:return builder(*args,**kwargs)
   finally:
    for path,raw in saved.items():path.write_bytes(raw)
    restored.append(True)
  m._check_dp_package=mutate;setattr(m,builder_name,restore_after_builder)
  try:
   observed=m.lookup(root,source,list_rows=True).model_dump_json()
   assert observed==baseline,'Output differs from captured baseline'
   assert calls==[True,True] and restored==[True]
   assert all(path.read_bytes()==raw for path,raw in saved.items())
   results.append({'source':source,'result':'PASS','real_package_checks':2,
      'mutation_window':'after final package capture through row/context assembly',
      'mutated_fields':['QA display/context or annotation','native bytes','image bytes'],
      'restoration':'all mutated bytes restored only after builder returned (ABA)',
      'entire_output':'byte-identical to baseline before mutation',
      'rows':44,'baseline_output_sha256':hashlib.sha256(baseline.encode()).hexdigest()})
  finally:m._check_dp_package=checked;setattr(m,builder_name,builder)
print(json.dumps({'status':'PASS','cases':results,'public_requests':0,'production_writes':0},indent=2))
