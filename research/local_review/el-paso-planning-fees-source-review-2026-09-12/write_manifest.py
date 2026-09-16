"""Write a typed closed inventory, preserving prior draft inventory preimages."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
HERE=Path(__file__).absolute().parent;sys.path.insert(0,str(HERE))
from review_models import Asset,Inventory
old=HERE/'FINAL_MANIFEST.json'
if old.exists():
 p=HERE/'preparation-preimages'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');p.mkdir(parents=True)
 with (p/'FINAL_MANIFEST.json').open('xb') as f:f.write(old.read_bytes())
files=[]
for p in sorted(HERE.rglob('*')):
 if p.is_file() and p not in [old,HERE/'FINAL_MANIFEST.schema.json']:
  b=p.read_bytes();files.append(Asset(path=p.relative_to(HERE).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b)))
r=Inventory(files=files,exclusions='FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only');b=(r.model_dump_json(indent=2)+'\n').encode();Inventory.model_validate_json(b);old.write_bytes(b)
schema=(json.dumps(Inventory.model_json_schema(),indent=2)+'\n').encode()
sp=HERE/'FINAL_MANIFEST.schema.json'
if sp.exists():assert sp.read_bytes()==schema
else:sp.write_bytes(schema)
print(hashlib.sha256(b).hexdigest(),len(files)+2,'files')
