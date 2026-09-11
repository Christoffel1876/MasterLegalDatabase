"""Read-only combined custody check for the two distinct recovery attempts."""
from pathlib import Path
from datetime import datetime
from typing import Literal
import hashlib,json,sys
import jsonschema
from pydantic import BaseModel,ConfigDict,Field
from recover_catalog import Receipt,Start
B=Path(__file__).resolve().parent
class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Asset(Strict):
 path:str
 sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
 bytes:int=Field(ge=0)
class FinalReceipt(Strict):
 completed_at:datetime
 source_oid:str
 expected_bytes:int
 configured_repository:Literal['Christoffel1876/MasterLegalDatabase']
 first_attempt:Asset
 retry_attempt:Asset
 first_attempt_result:Literal['transport_failed_without_http_response']
 retry_result:Literal['batch_http_200_exact_object_error_404']
 returned_error_message:Literal['Object does not exist on the server']
 object_bytes_downloaded:Literal[0]
 source_catalog_replaced:Literal[False]
 prior_files_unchanged:list[Asset]
 tls_method:Literal['installed_certifi_ca_bundle_with_verification_enabled']
 object_absence_scope:str
 limitations:list[str]
class Inventory(Strict):
 files:list[Asset]
 excluded_self:Literal['FINAL_RECOVERY_MANIFEST.json']

def sha(b):return hashlib.sha256(b).hexdigest()
def read(a):
 p=B/a.path
 assert not Path(a.path).is_absolute() and '..' not in Path(a.path).parts
 assert all(not q.is_symlink() for q in [p,*p.parents])
 b=p.read_bytes();assert len(b)==a.bytes and sha(b)==a.sha256;return b

def validate():
 inv=Inventory.model_validate_json((B/'FINAL_RECOVERY_MANIFEST.json').read_bytes())
 assert {p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()}=={a.path for a in inv.files}|{inv.excluded_self}
 for a in inv.files:read(a)
 final=FinalReceipt.model_validate_json((B/'FINAL_RECOVERY_RECEIPT.json').read_bytes())
 jsonschema.Draft202012Validator(json.loads((B/'FINAL_RECOVERY_RECEIPT.schema.json').read_text())).validate(final.model_dump(mode='json'))
 first=Receipt.model_validate_json(read(final.first_attempt));second=Receipt.model_validate_json(read(final.retry_attempt))
 assert first.outcome=='attempt_failed' and first.failure_class=='URLError' and first.batch_http_status is None
 assert second.outcome=='exact_object_unavailable' and second.batch_http_status==200 and second.object_error_code==404
 assert second.object_oid==final.source_oid and second.object_error_message==final.returned_error_message
 assert not second.download_action_present and second.download_bytes==0 and second.download_path is None
 assert second.object_size==final.expected_bytes
 for a in final.prior_files_unchanged:read(a)
 for folder,receipt in [(B,first),(B/'certifi-retry',second)]:
  start=Start.model_validate_json((folder/'ATTEMPT_STARTED.json').read_bytes());assert start==receipt.started
  pointer=(folder/'retrieval-catalog.pointer.txt').read_bytes()
  assert sha(pointer)==start.pointer_sha256 and len(pointer)==start.pointer_bytes
  assert pointer==f'version https://git-lfs.github.com/spec/v1\noid sha256:{final.source_oid}\nsize {final.expected_bytes}\n'.encode()
  jsonschema.Draft202012Validator(json.loads((folder/'RECOVERY_RECEIPT.schema.json').read_text())).validate(receipt.model_dump(mode='json'))
 sys.stdout.write('PASS: original ten files unchanged; first no-HTTP failure and verified-TLS retry with exact-object404 are separately bound; zero bytes downloaded and no catalog replacement.\n')
if __name__=='__main__':validate()
