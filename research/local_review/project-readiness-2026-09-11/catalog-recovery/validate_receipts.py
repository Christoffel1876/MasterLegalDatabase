"""Read-only verification of the sanitized, unsuccessful recovery attempt."""
from pathlib import Path
import hashlib,json,sys
import jsonschema
from pydantic import BaseModel,ConfigDict,Field
from recover_catalog import Receipt,Start
B=Path(__file__).resolve().parent
class File(BaseModel):
 model_config=ConfigDict(extra='forbid')
 path:str
 sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
 bytes:int=Field(ge=0)
class Inventory(BaseModel):
 model_config=ConfigDict(extra='forbid')
 files:list[File]
 excluded_self:str

def validate():
 inv=Inventory.model_validate_json((B/'evidence-manifest.json').read_bytes())
 expected={f.path for f in inv.files}|{inv.excluded_self}
 actual={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()}
 assert actual==expected
 for f in inv.files:
  p=B/f.path
  assert not Path(f.path).is_absolute() and '..' not in Path(f.path).parts
  assert all(not q.is_symlink() for q in [p,*p.parents])
  b=p.read_bytes();assert len(b)==f.bytes and hashlib.sha256(b).hexdigest()==f.sha256
 start=Start.model_validate_json((B/'ATTEMPT_STARTED.json').read_bytes())
 receipt=Receipt.model_validate_json((B/'RECOVERY_RECEIPT.json').read_bytes())
 assert receipt.started==start
 pointer=(B/'retrieval-catalog.pointer.txt').read_bytes()
 assert len(pointer)==start.pointer_bytes and hashlib.sha256(pointer).hexdigest()==start.pointer_sha256
 assert pointer==f'version https://git-lfs.github.com/spec/v1\noid sha256:{start.oid}\nsize {start.expected_bytes}\n'.encode()
 for name in ['RECOVERY_RECEIPT','LOCAL_TLS_DIAGNOSTICS']:
  jsonschema.Draft202012Validator(json.loads((B/f'{name}.schema.json').read_text())).validate(json.loads((B/f'{name}.json').read_text()))
 assert receipt.outcome=='attempt_failed' and receipt.failure_class=='URLError'
 assert receipt.batch_http_status is None and receipt.download_bytes==0 and not receipt.exact_oid_and_size_verified
 assert receipt.download_path is None and receipt.jsonl_lines is None
 sys.stdout.write('PASS: exact pointer, typed sanitized records and inventory verified; transport failure, no HTTP result or recovered object.\n')
if __name__=='__main__':validate()
