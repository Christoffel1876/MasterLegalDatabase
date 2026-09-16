"""One authorized transport-context retry of local Apple Vision; no network."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import hashlib,json,subprocess
from pydantic import BaseModel,ConfigDict,Field
HERE=Path(__file__).absolute().parent
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Line(Strict):
 text:str
 confidence:float=Field(ge=0,le=1)
 bbox:tuple[float,float,float,float]
class Result(Strict):
 revision:Literal[3]
 os_version:str
 lines:list[Line]
class Event(Strict):
 page:int
 image_sha256:str
 command:list[str]
 started_at:str
 completed_at:str
 stdout_sha256:str
 stdout_bytes:int
 stderr_sha256:str
 stderr_bytes:int
 exit_code:int
 status:Literal['machine_ocr_unreviewed','failed']
class Receipt(Strict):
 status:Literal['machine_ocr_unreviewed','failed']
 engine:Literal['Apple Vision']='Apple Vision'
 revision:Literal[3]=3
 adapter_sha256:str
 adapter_source_sha256:str
 visual_freeze_sha256:str
 execution_context:Literal['explicitly_authorized_exec_require_escalated_once']
 settings:dict
 events:list[Event]
 prior_failures:list[dict]
 reason_no_retry_after_failure:Literal['stop on first error in this authorized retry']='stop on first error in this authorized retry'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
 with p.open('xb') as f:f.write(b)
exe=HERE/'tools/apple-vision-ocr';adapter=exe.read_bytes();visual=(HERE/'VISUAL_TRANSCRIPTION.json').read_bytes()
assert sha(visual)=='220ef0c72ae74e45c9a1198387b128ee576790b8d900bb9a703ff8416605d8d9'
out=HERE/'ocr/retry-authorized';out.mkdir()
events=[];failed=False
for n in range(1,6):
 image=HERE/f'images/page-{n}.png';cmd=[str(exe),str(image)];start=datetime.now(timezone.utc).isoformat()
 p=subprocess.run(cmd,capture_output=True,timeout=45,check=False)
 if p.returncode==0:Result.model_validate_json(p.stdout)
 write(out/f'page-{n:04}.stdout',p.stdout);write(out/f'page-{n:04}.stderr',p.stderr)
 events.append(Event(page=n,image_sha256=sha(image.read_bytes()),command=cmd,started_at=start,completed_at=datetime.now(timezone.utc).isoformat(),stdout_sha256=sha(p.stdout),stdout_bytes=len(p.stdout),stderr_sha256=sha(p.stderr),stderr_bytes=len(p.stderr),exit_code=p.returncode,status='machine_ocr_unreviewed' if p.returncode==0 else 'failed'))
 print('page',n,'exit',p.returncode,'bytes',len(p.stdout),flush=True)
 if p.returncode!=0:failed=True;break
assert sha(exe.read_bytes())==sha(adapter) and (HERE/'VISUAL_TRANSCRIPTION.json').read_bytes()==visual
r=Receipt(status='failed' if failed else 'machine_ocr_unreviewed',adapter_sha256=sha(adapter),adapter_source_sha256=sha((HERE/'tools/apple_vision_ocr.swift').read_bytes()),visual_freeze_sha256=sha(visual),execution_context='explicitly_authorized_exec_require_escalated_once',settings={'recognition_level':'accurate','recognition_languages':['en-US'],'uses_language_correction':False,'automatically_detects_language':False,'minimum_text_height':0,'uses_cpu_only':True,'reading_order':'engine_observation_order','bounding_box_origin':'bottom_left'},events=events,prior_failures=[{'attempt':'initial run_ocr_comparison.py page 1','exit_code':1,'captured_error':'CalledProcessError','original_stdout_stderr_retained':False,'time':'not retained','limitation':'The initial subprocess exception displayed exit 1; its captured streams were not saved before that script stopped.'},{'attempt':'direct diagnostic invocation of same binary and image page 1','exit_code':1,'tool_merged_output':'nilError','separate_streams_retained':False,'time':'not retained','limitation':'Tool output recorded nilError. No OCR text was returned.'}])
b=(r.model_dump_json(indent=2)+'\n').encode();Receipt.model_validate_json(b);write(HERE/'OCR_COMPARISON_RECEIPT.json',b);write(HERE/'OCR_COMPARISON_RECEIPT.schema.json',(json.dumps(Receipt.model_json_schema(),indent=2)+'\n').encode());write(HERE/'ocr/engine-result.schema.json',(json.dumps(Result.model_json_schema(),indent=2)+'\n').encode())
