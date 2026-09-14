from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Literal
import hashlib, json, subprocess, os
from pydantic import BaseModel, ConfigDict
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-fees-source-qa')
S=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-planning-fees-source-review/tools')
class Record(BaseModel):
    model_config=ConfigDict(extra='forbid')
    status: Literal['machine_ocr_unreviewed','local_ocr_failed']
    engine: str
    binary_sha256: str
    swift_sha256: str
    events: list[dict[str, Any]]
(B/'ocr').mkdir(); (B/'tools').mkdir()
for name in ['apple-vision-ocr','apple_vision_ocr.swift']:
    with (B/'tools'/name).open('xb') as f: f.write((S/name).read_bytes())
(B/'tools/apple-vision-ocr').chmod(0o700)
sha=lambda b:hashlib.sha256(b).hexdigest()
events=[]
for n in range(1,4):
    image=B/f'pages/page-{n:04}.png'; cmd=[str(B/'tools/apple-vision-ocr'),str(image)]
    start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(cmd,capture_output=True,timeout=45)
    for suffix, data in [('stdout',result.stdout),('stderr',result.stderr)]:
        with (B/f'ocr/page-{n:04}.{suffix}').open('xb') as f:f.write(data)
    events.append(dict(page=n,command=cmd,started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,image_sha256=sha(image.read_bytes()),stdout_sha256=sha(result.stdout),stderr_sha256=sha(result.stderr)))
    if result.returncode:break
r=Record(status='local_ocr_failed' if result.returncode else 'machine_ocr_unreviewed',engine='Apple Vision revision 3; accurate en-US; language correction false; CPU only; raw observation order',binary_sha256=sha((B/'tools/apple-vision-ocr').read_bytes()),swift_sha256=sha((B/'tools/apple_vision_ocr.swift').read_bytes()),events=events)
for name,data in [('OCR_RECEIPT.json',r.model_dump_json(indent=2)),('OCR_RECEIPT.schema.json',json.dumps(Record.model_json_schema(),indent=2))]:
    with (B/name).open('x') as f:f.write(data+'\n')
print(r.status, len(events))
