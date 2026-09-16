"""Reproduce full Poppler page images into temporary files, never alter inputs."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import argparse,hashlib,json,os,subprocess,tempfile
from pydantic import BaseModel,ConfigDict
HERE=Path(__file__).absolute().parent
DEFAULT=Path('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm')
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class ImageResult(Strict):
 physical_page:int
 image_path:str
 expected_sha256:str
 reproduced_sha256:str
 size_bytes:int
 exact_match:Literal[True]=True
class RenderReplay(Strict):
 input_source_path:Literal['source/original.pdf']='source/original.pdf'
 input_source_sha256:Literal['c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12']
 started_at:str
 completed_at:str
 engine:Literal['Poppler pdftoppm']='Poppler pdftoppm'
 executable_sha256:str
 version_output:str
 arguments:Literal['-r 200 -png source/original.pdf temporary/page']='-r 200 -png source/original.pdf temporary/page'
 images:list[ImageResult]
 source_bytes_unchanged:Literal[True]=True
 scope:Literal['full five displayed physical pages; exact output bytes compared']='full five displayed physical pages; exact output bytes compared'
def sha(b):return hashlib.sha256(b).hexdigest()
def replay(root:Path,poppler:Path):
 source=root/'source/original.pdf';original=source.read_bytes();start=datetime.now(timezone.utc).isoformat();exe=poppler.read_bytes()
 version=subprocess.run([str(poppler),'-v'],capture_output=True,check=True,timeout=10)
 with tempfile.TemporaryDirectory(prefix='el-paso-render-check-') as temporary:
  tmp=Path(temporary);cfg=tmp/'fonts.conf';cfg.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>/System/Library/Fonts</dir><dir>/Library/Fonts</dir><cachedir>{tmp}/cache</cachedir></fontconfig>')
  env=dict(os.environ,FONTCONFIG_FILE=str(cfg))
  subprocess.run([str(poppler),'-r','200','-png',str(source),str(tmp/'page')],capture_output=True,check=True,timeout=45,env=env)
  results=[]
  for n in range(1,6):
   a=(root/f'images/page-{n}.png').read_bytes();b=(tmp/f'page-{n}.png').read_bytes()
   if a!=b:raise ValueError('Rendered image mismatch on page '+str(n))
   results.append(ImageResult(physical_page=n,image_path=f'images/page-{n}.png',expected_sha256=sha(a),reproduced_sha256=sha(b),size_bytes=len(a)))
 if source.read_bytes()!=original or poppler.read_bytes()!=exe:raise ValueError('Source/renderer changed during replay')
 return RenderReplay(input_source_sha256=sha(original),started_at=start,completed_at=datetime.now(timezone.utc).isoformat(),executable_sha256=sha(exe),version_output=(version.stdout+version.stderr).decode(),images=results)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=HERE);p.add_argument('--poppler',type=Path,default=DEFAULT);p.add_argument('--record',action='store_true');a=p.parse_args();r=replay(a.root,a.poppler)
 if a.record:
  b=(r.model_dump_json(indent=2)+'\n').encode();RenderReplay.model_validate_json(b)
  with (a.root/'RENDER_REPLAY.json').open('xb') as f:f.write(b)
  with (a.root/'RENDER_REPLAY.schema.json').open('xb') as f:f.write((json.dumps(RenderReplay.model_json_schema(),indent=2)+'\n').encode())
 print('PASS: all five full Poppler page images reproduced byte-identically.')
