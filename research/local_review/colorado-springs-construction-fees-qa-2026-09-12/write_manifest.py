from pathlib import Path
from hashlib import sha256
import json,shutil
from review_models import Inventory,Asset
r=Path(__file__).resolve().parent
p=r/'FINAL_MANIFEST.json'
if p.exists():
 pre=r/'preparation-preimages'/sha256(p.read_bytes()).hexdigest();pre.mkdir(parents=True,exist_ok=True)
 if not (pre/p.name).exists():shutil.copyfile(p,pre/p.name)
files=[]
for p in sorted(r.rglob('*')):
 if p.is_file() and p.relative_to(r).as_posix() not in {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}:
  files.append(Asset(path=p.relative_to(r).as_posix(),sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size))
files.sort(key=lambda a:a.path)
m=Inventory(schema_version='1.0',status='frozen_source_qa_pending_root_independent_acceptance',source_sha256='e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a',files=files,excluded_paths='FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only; all other ordinary package files are included.')
(r/'FINAL_MANIFEST.json').write_text(m.model_dump_json(indent=2)+'\n')
(r/'FINAL_MANIFEST.schema.json').write_text(json.dumps(Inventory.model_json_schema(),indent=2)+'\n')
print(len(files),'included files',sha256((r/'FINAL_MANIFEST.json').read_bytes()).hexdigest())
