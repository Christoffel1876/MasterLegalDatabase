"""Run the already available local OCR binary only after the visual freeze."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,os,sys
from typing import Literal
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
 exit_code:Literal[0]
class Receipt(Strict):
 schema_version:Literal[1]=1
 status:Literal['machine_ocr_unreviewed']='machine_ocr_unreviewed'
 engine:Literal['Apple Vision']='Apple Vision'
 revision:Literal[3]=3
 adapter_path:str
 adapter_sha256:str
 adapter_source_sha256:str
 visual_freeze_sha256:str
 settings:dict
 events:list[Event]
 generations_unchanged:Literal[True]=True
base=HERE.parents[2]/'MasterLegalDatabase'
binary=base/'.geode_runtime/ocr-code-fees-2026-09-10/apple-vision-ocr'
swift=base/'scripts/apple_vision_ocr.swift'
assert (HERE/'VISUAL_TRANSCRIPTION.json').is_file()
(HERE/'ocr').mkdir();(HERE/'tools').mkdir()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
 with p.open('xb') as f:f.write(b)
exe=HERE/'tools/apple-vision-ocr';b=binary.read_bytes();write(exe,b);exe.chmod(0o700);write(HERE/'tools/apple_vision_ocr.swift',swift.read_bytes())
events=[]
for n in range(1,6):
 image=HERE/f'images/page-{n}.png';start=datetime.now(timezone.utc).isoformat();cmd=[str(exe),str(image)]
 run=subprocess.run(cmd,capture_output=True,timeout=45,check=True)
 Result.model_validate_json(run.stdout)
 write(HERE/f'ocr/page-{n:04}.json',run.stdout)
 write(HERE/f'ocr/page-{n:04}.stderr.txt',run.stderr)
 events.append(Event(page=n,image_sha256=sha(image.read_bytes()),command=cmd,started_at=start,completed_at=datetime.now(timezone.utc).isoformat(),stdout_sha256=sha(run.stdout),stdout_bytes=len(run.stdout),stderr_sha256=sha(run.stderr),exit_code=0))
assert sha(exe.read_bytes())==sha(b)
r=Receipt(adapter_path='tools/apple-vision-ocr',adapter_sha256=sha(b),adapter_source_sha256=sha(swift.read_bytes()),visual_freeze_sha256=sha((HERE/'VISUAL_TRANSCRIPTION.json').read_bytes()),settings={'recognition_level':'accurate','recognition_languages':['en-US'],'uses_language_correction':False,'automatically_detects_language':False,'minimum_text_height':0,'uses_cpu_only':True,'reading_order':'engine_observation_order','bounding_box_origin':'bottom_left'},events=events)
rj=(r.model_dump_json(indent=2)+'\n').encode();Receipt.model_validate_json(rj);write(HERE/'OCR_COMPARISON_RECEIPT.json',rj);write(HERE/'OCR_COMPARISON_RECEIPT.schema.json',(json.dumps(Receipt.model_json_schema(),indent=2)+'\n').encode());write(HERE/'ocr/engine-result.schema.json',(json.dumps(Result.model_json_schema(),indent=2)+'\n').encode())
print('OCR complete',len(events),'pages; output remains uncorrected.')
