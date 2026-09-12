"""Optional full-page Poppler replay; default is read-only for this package."""
import argparse,json,os,shutil,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from hashlib import sha256
from pydantic import BaseModel,ConfigDict
sys.path.insert(0,str(Path(__file__).absolute().parent))
from review_models import Asset
from validate_review import validate,digest,ordinary
class RenderReceipt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 checked_at:str
 source_sha256:str
 renderer:str
 renderer_version:str
 command_options:list[str]
 full_page_count:int
 byte_identical_images:list[Asset]
 scope:str

def run(root,binary):
 validate(root)
 before={p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
 version=subprocess.run([str(binary),'-v'],capture_output=True,text=True,check=True).stderr.strip()
 with tempfile.TemporaryDirectory(prefix='csfd-render-',dir='/private/tmp') as tmp:
  out=Path(tmp);conf=out/'fonts.xml';conf.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>/System/Library/Fonts</dir><dir>/Library/Fonts</dir><cachedir>{out}/cache</cachedir></fontconfig>')
  env=dict(os.environ,FONTCONFIG_FILE=str(conf))
  subprocess.run([str(binary),'-r','200','-png',str(root/'source/original.pdf'),str(out/'page')],env=env,check=True,capture_output=True,timeout=120)
  results=[]
  for p in range(1,8):
   actual=out/f'page-{p}.png';expected=root/f'images/page-{p}.png'
   if actual.read_bytes()!=expected.read_bytes():raise ValueError(f'Poppler page {p} bytes differ; keep renderer reproducibility separate from byte integrity')
   results.append(Asset(path=f'images/page-{p}.png',sha256=digest(actual),size_bytes=actual.stat().st_size))
 after={p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
 if before!=after:raise ValueError('package changed during render replay')
 return RenderReceipt(checked_at=datetime.now(timezone.utc).isoformat(),source_sha256=digest(root/'source/original.pdf'),renderer=str(binary),renderer_version=version,command_options=['-r','200','-png'],full_page_count=7,byte_identical_images=results,scope='All seven full-page PNG bytes reproduced in a temporary directory. This is derivation reproducibility, not legal currentness or proof of visual judgment.')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).absolute().parent);ap.add_argument('--pdftoppm',type=Path,default=Path(shutil.which('pdftoppm') or '/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'));ap.add_argument('--record',action='store_true');a=ap.parse_args();r=ordinary(a.root.absolute(),True);receipt=run(r,a.pdftoppm)
 if a.record:
  target=r/'RENDER_REPLAY.json'
  if target.exists():raise ValueError('render receipt already exists')
  target.write_text(receipt.model_dump_json(indent=2)+'\n');(r/'RENDER_REPLAY.schema.json').write_text(json.dumps(RenderReceipt.model_json_schema(),indent=2)+'\n')
 print(receipt.model_dump_json(indent=2))
