from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
import hashlib, json, subprocess
from pydantic import BaseModel, ConfigDict, Field
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-fees-source-qa')
class Line(BaseModel):
    model_config=ConfigDict(extra='forbid', strict=True)
    text:str
    confidence:float=Field(ge=0,le=1)
    bbox:tuple[float,float,float,float]
class Output(BaseModel):
    model_config=ConfigDict(extra='forbid', strict=True)
    revision:Literal[3]
    os_version:str
    lines:list[Line]
class Event(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    page:int
    command:list[str]
    started_at:str
    finished_at:str
    exit_code:int
    image_sha256:str
    stdout_sha256:str
    stderr_sha256:str
class Receipt(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    status:str
    method:str
    binary_sha256:str
    events:list[Event]
D=B/'ocr-escalated';D.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
events=[]
for n in range(1,4):
    image=B/f'pages/page-{n:04}.png';cmd=[str(B/'tools/apple-vision-ocr'),str(image)]
    start=datetime.now(timezone.utc).isoformat();p=subprocess.run(cmd,capture_output=True,timeout=45)
    for suffix,data in [('json',p.stdout),('stderr',p.stderr)]:
        with (D/f'page-{n:04}.{suffix}').open('xb') as f:f.write(data)
    events.append(Event(page=n,command=cmd,started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode,image_sha256=sha(image.read_bytes()),stdout_sha256=sha(p.stdout),stderr_sha256=sha(p.stderr)))
    if p.returncode:break
    o=Output.model_validate_json(p.stdout)
    with (D/f'page-{n:04}.txt').open('xb') as f:f.write(('\n'.join(x.text for x in o.lines)+'\n').encode())
r=Receipt(status='machine_ocr_unreviewed' if not p.returncode else 'failed',method='Same existing local Apple Vision executable, environmental retry outside sandbox; raw engine observation order preserved; no text corrections',binary_sha256=sha((B/'tools/apple-vision-ocr').read_bytes()),events=events)
for name,data in [('RECEIPT.json',r.model_dump_json(indent=2)),('RECEIPT.schema.json',json.dumps(Receipt.model_json_schema(),indent=2)),('OCR.schema.json',json.dumps(Output.model_json_schema(),indent=2))]:
    with (D/name).open('x') as f:f.write(data+'\n')
print(r.status, len(events))
