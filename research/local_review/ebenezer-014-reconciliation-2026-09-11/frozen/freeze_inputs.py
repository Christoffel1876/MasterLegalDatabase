from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict,Field
import json,shutil,jsonschema
B=Path(__file__).parent
BASE=Path('/Users/mcoors/Documents/Project Geode')
EXT=BASE/'handoffs/ebenezer-reviews/EB-PDF-014_fort-collins-land-use-article-1-sd005-07_20260911T192225Z'
class File(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 original_path:str
 received_path:str
 sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 size_bytes:int=Field(ge=0)
class Receipt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 frozen_at:datetime
 files:list[File]=Field(min_length=4,max_length=4)
 original_files_unchanged:bool
files=[]
for p in sorted(EXT.iterdir()):
 assert p.is_file() and not p.is_symlink()
 d=B/'received'/p.name;d.parent.mkdir(parents=True,exist_ok=True)
 data=p.read_bytes()
 if not d.exists():d.write_bytes(data);d.chmod(0o444)
 assert d.read_bytes()==data
 files.append(File(original_path=str(p),received_path=str(d.resolve()),sha256=sha256(data).hexdigest(),size_bytes=len(data)))
r=Receipt(frozen_at=datetime.now(timezone.utc),files=files,original_files_unchanged=True)
(B/'CUSTODY_RECEIPT.json').write_text(r.model_dump_json(indent=2)+'\n')
(B/'CUSTODY_RECEIPT.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
jsonschema.Draft202012Validator(Receipt.model_json_schema()).validate(json.loads(r.model_dump_json()))
print(r.model_dump_json(indent=2))
