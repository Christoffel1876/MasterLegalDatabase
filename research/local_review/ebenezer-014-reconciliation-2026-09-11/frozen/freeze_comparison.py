"""Preserve read-only comparison inputs and verify exact external hash claims."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict,Field
import json,subprocess,shutil,jsonschema
B=Path(__file__).parent
BASE=Path('/Users/mcoors/Documents/Project Geode')
R=BASE/'MasterLegalDatabase'
REL='research/local_review/ebenezer-014-2026-09-11'
PACK=BASE/'handoffs/grok-pdf-review-2026-09-11-batch-4'
SRC=PACK/'01-source-only/fort-collins-land-use-article-1-sd005-07'
CAND=PACK/'02-candidate-text/fort-collins-land-use-article-1-sd005-07'
def hash(p):return sha256(p.read_bytes()).hexdigest()
class File(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 original_path:str
 copy_path:str
 sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 size_bytes:int=Field(ge=0)
 git_blob_match:bool|None
class Claim(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 label:str
 expected_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 actual_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 matches:bool
 actual_path:str
class Receipt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 frozen_at:datetime
 comparison_commit:str=Field(pattern=r'^[0-9a-f]{40}$')
 files:list[File]
 hash_claims:list[Claim]
 duplicate_packet_and_committed_bytes_match:bool
 original_files_unchanged:bool
 legal_currentness:str
commit=subprocess.check_output(['git','rev-parse','95155c2^{commit}'],cwd=R,text=True).strip()
files=[]
def copy(p,rel,gitrel=None):
 assert p.is_file() and not p.is_symlink() and not any(x.is_symlink() for x in p.parents)
 d=B/rel;d.parent.mkdir(parents=True,exist_ok=True)
 data=p.read_bytes()
 if not d.exists():d.write_bytes(data);d.chmod(0o444)
 assert d.read_bytes()==data
 matched=None
 if gitrel:
  body=subprocess.check_output(['git','cat-file','blob',commit+':'+gitrel],cwd=R)
  assert body==data;matched=True
 files.append(File(original_path=str(p),copy_path=rel,sha256=hash(p),size_bytes=len(data),git_blob_match=matched))
for p in sorted((R/REL).rglob('*')):
 if p.is_file():
  if '__pycache__' in p.parts:continue
  rel=str(p.relative_to(R/REL))
  copy(p,'comparison/committed-package/'+rel,REL+'/'+rel)
for p,rel in [(PACK/'manifest.json','comparison/batch4-manifest.json'),(BASE/'handoffs/EBENEZER_QUEUE_013_014_2026-09-11.md','comparison/queue-auth.md')]:copy(p,rel)
assert hash(SRC/'original.pdf')==hash(R/REL/'source/original.pdf')
assert hash(CAND/'candidate.txt')==hash(R/REL/'candidate.txt')
for i in range(1,8):
 for x,y in [(SRC/f'page-{i:04}.png',R/REL/f'images/page-{i:04}.png'),(CAND/f'native-evidence/page-{i:04}.json',R/REL/f'native-evidence/page-{i:04}.json')]:assert hash(x)==hash(y)
claims=[]
h=json.loads((B/'received/COMPLETION_RECEIPT.json').read_text())
paths={**{f'page-{i:04}.png':(h['page_images_sha256'][f'page-{i:04}.png'],SRC/f'page-{i:04}.png') for i in range(1,8)},'candidate.txt':(h['candidate_sha256'],CAND/'candidate.txt'),'PASS1_frozen.md':(h['PASS1_frozen_md_sha256'],B/'received/PASS1_frozen.md'),'PASS1_FREEZE_RECEIPT.json':(h['PASS1_FREEZE_RECEIPT_sha256'],B/'received/PASS1_FREEZE_RECEIPT.json'),'PASS2_REVIEW.md':(h['PASS2_REVIEW_md_sha256'],B/'received/PASS2_REVIEW.md'),'original.pdf':(h['original_pdf_sha256'],SRC/'original.pdf'),'packet_manifest':(h['packet_manifest_sha256'],PACK/'manifest.json'),'queue':(h['queue_sha256'],BASE/'handoffs/EBENEZER_QUEUE_013_014_2026-09-11.md')}
for k,(expected,p) in paths.items():
 claims.append(Claim(label=k,expected_sha256=expected,actual_sha256=hash(p),matches=expected==hash(p),actual_path=str(p)))
r=Receipt(frozen_at=datetime.now(timezone.utc),comparison_commit=commit,files=files,hash_claims=claims,duplicate_packet_and_committed_bytes_match=True,original_files_unchanged=True,legal_currentness='not_verified')
(B/'COMPARISON_RECEIPT.json').write_text(r.model_dump_json(indent=2)+'\n')
(B/'COMPARISON_RECEIPT.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
jsonschema.Draft202012Validator(Receipt.model_json_schema()).validate(json.loads(r.model_dump_json()))
print('Verified',len(files),'files at',commit,'and',len(claims),'claimed hashes; mismatches:',[x.label for x in claims if not x.matches])
