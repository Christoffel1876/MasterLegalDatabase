from pathlib import Path
import subprocess,json,hashlib
from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
OUT=ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/EL_PASO_EHS_LOOKUP/root-cli'
OUT.mkdir()
class Event(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 query:str
 exit_code:int
 status:str
 row_ids:list[str]
 context_ids:list[str]
 output_file:str
 sha256:str
for i,(query,expected,rows,code) in enumerate([
 ('Section 2','matched_context_only',[],0),
 ('211.50','matched',['R031'],0),
 ('OWTS New Permit','matched',['R020'],0),
 ('complaint investigations','matched_context_only',[],0),
 ('current fee','refused_current_law',[],2),
]):
 args=['/private/tmp/geode-status-venv/bin/python','-B',str(ROOT/'scripts/research_source_lookup.py'),'--root',str(ROOT),'--source-id','el-paso-boh-ehs-fees-sd011','--query',query,'--format','json']
 p=subprocess.run(args,cwd='/private/tmp',capture_output=True,timeout=50)
 assert p.returncode==code,(query,p.stderr)
 data=json.loads(p.stdout)
 assert data['status']==expected and [r['row_id'] for r in data['rows']]==rows
 assert data['legal_currentness']=='not_verified' and not data['answer_safe']
 if code==0:
  assert len(data['context'])==37
  b=next(c for c in data['context'] if c['context_id']=='B')
  assert 'Section 2,' in b['native']['text'] and '$100 per day' in b['native']['text']
 else:assert data['source'] is None and not data['context']
 output=f'{i+1:02d}.json';(OUT/output).write_bytes(p.stdout)
 event=Event(query=query,exit_code=p.returncode,status=data['status'],row_ids=rows,context_ids=data['matched_context_ids'],output_file=output,sha256=hashlib.sha256(p.stdout).hexdigest())
 (OUT/f'{i+1:02d}.receipt.json').write_text(event.model_dump_json(indent=2)+'\n')
 print(event.model_dump_json())
(OUT/'receipt.schema.json').write_text(json.dumps(Event.model_json_schema(),indent=2)+'\n')
