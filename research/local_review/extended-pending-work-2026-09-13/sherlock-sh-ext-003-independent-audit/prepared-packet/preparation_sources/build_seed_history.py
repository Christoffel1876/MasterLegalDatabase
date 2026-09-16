from pathlib import Path
from typing import Any
import json,hashlib,sys,os,shutil
from pydantic import BaseModel,ConfigDict
p=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/sherlock-sh-ext-003')
sys.path.insert(0,str(p))
def write_new(name,data):
 path=p/name;path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():raise ValueError('Exists '+str(path))
 if isinstance(data,str):data=data.encode()
 tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data);tmp.replace(path)
def replace_preserved(name,text):
 path=p/name;write_new(Path('preparation-preimages/formatting')/name,path.read_bytes())
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(text);tmp.replace(path)
for name in ['models.py','test_reporting_templates.py','test_budget.py']:
 s=(p/name).read_text()
 s=s.replace('Require all24 different authority/category combinations without implying complete coverage.','Require all 24 authority/category combinations without claiming complete coverage.')
 s=s.replace("    data.update(body_size_basis='retained_complete',observed_body_bytes=10,\n                body_sha256='a'*64,retained_assets=[{'path':'body','sha256':'a'*64,'size_bytes':10}])", "    data.update(body_size_basis='retained_complete', observed_body_bytes=10,\n                body_sha256='a'*64, retained_assets=[\n                    {'path':'body', 'sha256':'a'*64, 'size_bytes':10}])")
 s=s.replace("    observed = result(1).model_copy(update={'visible_redirect_urls':['https://example.invalid/hop']})", "    observed = result(1).model_copy(update={\n        'visible_redirect_urls':['https://example.invalid/hop']})")
 s=s.replace("    unknown = result(1).model_copy(update={'body_size_basis':'unknown','observed_body_bytes':None})", "    unknown = result(1).model_copy(update={\n        'body_size_basis':'unknown', 'observed_body_bytes':None})")
 if s!=(p/name).read_text():replace_preserved(name,s)
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Direct(Strict):
 original_line_number:int;source_id:str;status:str;recorded_sha256:str|None
 source_url:str|None;requested_url:str;final_url:str|None
class History(Strict):
 source_id:str;authority_id:str;exact_seed_url:str;source_id_rows:int
 any_url_field_rows:int;source_url_parent_rows:int;requested_url_rows:int;final_url_rows:int
 requested_url_records:list[Direct]
class Histories(Strict):
 assignment_id:str;edition:str;selected_export_sha256:str;rows:list[History];limitations:list[str]
plan=json.loads((p/'PLAN.json').read_bytes());comparison=json.loads((p/'COMPARISON.json').read_bytes())
legacy=next(x for x in comparison['legacy'] if x['edition']=='working_tree')
rows=[]
with (p/legacy['selected']['path']).open('rb') as f:
 for number,line in zip(legacy['original_line_numbers'],f):rows.append((number,json.loads(line)))
result=[]
for seed in plan['seeds']:
 url=seed['url'];direct=[]
 for n,r in rows:
  if r.get('requested_url')==url:
   direct.append(dict(original_line_number=n,source_id=r.get('source_id','unknown'),status=r.get('status','unknown'),recorded_sha256=r.get('sha256'),source_url=r.get('source_url'),requested_url=url,final_url=r.get('final_url')))
 result.append(dict(source_id=seed['source_id'],authority_id=seed['authority_id'],exact_seed_url=url,source_id_rows=sum(r.get('source_id')==seed['source_id'] for _,r in rows),any_url_field_rows=sum(url in [r.get(k) for k in ['source_url','requested_url','final_url','url']] for _,r in rows),source_url_parent_rows=sum(r.get('source_url')==url for _,r in rows),requested_url_rows=len(direct),final_url_rows=sum(r.get('final_url')==url for _,r in rows),requested_url_records=direct))
data=Histories(assignment_id='SH-EXT-003',edition='working_tree',selected_export_sha256=legacy['selected']['sha256'],rows=result,limitations=['COMPARISON.url_attempts counts presence in any of four URL fields, including source_url parent context. It is not the count of direct requests to that endpoint.','Only requested_url_records here bind that exact historical request URL to its recorded digest. A digest remains an inherited record claim; bytes were not present at the recorded paths.','Pinned and working selected exports have identical bytes at capture, but retain both editions and their hashes.'])
write_new('SEED_HISTORY.json',data.model_dump_json(indent=2)+'\n');write_new('SEED_HISTORY.schema.json',json.dumps(Histories.model_json_schema(),indent=2)+'\n')
write_new('preparation_sources/build_initial.py',Path('/private/tmp/build-sh-ext003.py').read_bytes())
# Preserve the copied reusable predecessor code independently of these additive adaptations.
old=p.parent/'sherlock-sh-ext-001'
for name in ['models.py','validate_templates.py','test_reporting_templates.py','verify_packet.py']:
 write_new(Path('preparation_sources/sh-ext-001')/name,(old/name).read_bytes())
print(json.dumps([{k:r[k] for k in ['source_id','source_id_rows','any_url_field_rows','requested_url_rows']} for r in result],indent=2))
