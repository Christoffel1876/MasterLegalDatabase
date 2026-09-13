from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
import json, shutil, subprocess
import pymupdf
from pydantic import BaseModel, ConfigDict, Field
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13')
D=B/'atlas-chaffee-electric-source-qa'
class Asset(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    path:str
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)
class Event(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    kind:Literal['render','ocr']
    page:int|None
    started_at:str
    finished_at:str
    command:list[str]
    exit_code:int
    stdout:Asset
    stderr:Asset
    outputs:list[Asset]
class Receipt(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    source:Asset
    page_count:Literal[7]
    native:list[Asset]
    events:list[Event]
    status:Literal['prepared_unreviewed_images_and_native','prepared_unreviewed_ocr']
def ident(p):
    b=p.read_bytes();return Asset(path=p.relative_to(D).as_posix(),sha256=sha256(b).hexdigest(),size_bytes=len(b))
def output(p,b):
    with p.open('xb') as f:f.write(b)
    return ident(p)
import sys
if len(sys.argv)==1:
    D.mkdir();(D/'source').mkdir();(D/'native').mkdir();(D/'events').mkdir();(D/'ocr').mkdir();(D/'tools').mkdir()
    (D/'PREPARATION.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
    raw=(B/'ptolemy-chaffee-directed-retrieval/events/A002/response.body').read_bytes()
    assert sha256(raw).hexdigest()=='c0bfb6e8d4adb846fd62ec7dabbdd824286f7432be6a82b6b2d2264d4553cdf6'
    pdf=output(D/'source/original.pdf',raw); doc=pymupdf.open(stream=raw,filetype='pdf');assert len(doc)==7
    native=[output(D/f'native/page-{i+1:04}.txt',p.get_text().encode()) for i,p in enumerate(doc)]
    assert all(a.size_bytes==0 for a in native)
    cmd=['/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm','-r','300','-png',str(D/'source/original.pdf'),str(D/'source/page')]
    start=datetime.now(timezone.utc).isoformat();p=subprocess.run(cmd,capture_output=True,timeout=90);end=datetime.now(timezone.utc).isoformat()
    for i in range(1,8):(D/f'source/page-{i}.png').rename(D/f'source/page-{i:04}.png')
    ev=Event(kind='render',page=None,started_at=start,finished_at=end,command=cmd,exit_code=p.returncode,stdout=output(D/'events/render.stdout',p.stdout),stderr=output(D/'events/render.stderr',p.stderr),outputs=[ident(D/f'source/page-{i:04}.png') for i in range(1,8)])
    r=Receipt(source=pdf,page_count=7,native=native,events=[ev],status='prepared_unreviewed_images_and_native')
    (D/'PREPARATION.json').write_text(r.model_dump_json(indent=2)+'\n')
    for name in ['apple-vision-ocr','apple_vision_ocr.swift']:shutil.copy2(B/'plato-gunnison-fees-source-qa/tools'/name,D/'tools'/name)
    shutil.copy2(__file__,D/'prepare.py')
    print('Prepared7 PNGs; native empty; OCR not run.')
else:
    assert sys.argv[1:]==['--ocr']
    r=Receipt.model_validate_json((D/'PREPARATION.json').read_text()); events=[]
    for i in range(1,8):
        cmd=[str(D/'tools/apple-vision-ocr'),str(D/f'source/page-{i:04}.png')]
        start=datetime.now(timezone.utc).isoformat();p=subprocess.run(cmd,capture_output=True,timeout=45);end=datetime.now(timezone.utc).isoformat()
        out=output(D/f'ocr/page-{i:04}.json',p.stdout);err=output(D/f'ocr/page-{i:04}.stderr',p.stderr)
        if p.returncode:raise RuntimeError('OCR failed; raw streams retained')
        text='\n'.join(x['text'] for x in json.loads(p.stdout)['lines'])+'\n'
        txt=output(D/f'ocr/page-{i:04}.txt',text.encode())
        events.append(Event(kind='ocr',page=i,started_at=start,finished_at=end,command=cmd,exit_code=p.returncode,stdout=out,stderr=err,outputs=[txt]))
    r=r.model_copy(update={'events':r.events+events,'status':'prepared_unreviewed_ocr'})
    (D/'OCR_PREPARATION.json').write_text(r.model_dump_json(indent=2)+'\n')
    print('Seven unchanged machineOCR outputs retained; no source QA implied.')
