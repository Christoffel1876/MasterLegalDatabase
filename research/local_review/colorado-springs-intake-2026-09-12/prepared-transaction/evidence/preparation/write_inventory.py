from pathlib import Path
from hashlib import sha256
import os,json
from preparation_models import Asset,Inventory
r=Path(__file__).resolve().parent
files=[Asset(path=p.relative_to(r).as_posix(),sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size) for p in sorted(r.rglob('*')) if p.is_file() and p.relative_to(r).as_posix() not in {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}]
m=Inventory(status='PREPARED_NOT_APPLIED',files=files,exclusions='FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only. Frozen review metadata may refer to external full QA packages explicitly not duplicated here.')
for name,data in [('FINAL_MANIFEST.json',m.model_dump_json(indent=2)+'\n'),('FINAL_MANIFEST.schema.json',json.dumps(Inventory.model_json_schema(),indent=2)+'\n')]:
 p=r/name
 if p.exists():
  pre=r/'_SNAPSHOTS'/sha256(p.read_bytes()).hexdigest();pre.mkdir(parents=True,exist_ok=True);(pre/name).write_bytes(p.read_bytes())
  raise ValueError('Refusing implicit inventory overwrite; snapshot preserved, regenerate intentionally')
 t=p.with_name(p.name+'.tmp');t.write_text(data);os.replace(t,p)
print(len(files),'files',sha256((r/'FINAL_MANIFEST.json').read_bytes()).hexdigest())
