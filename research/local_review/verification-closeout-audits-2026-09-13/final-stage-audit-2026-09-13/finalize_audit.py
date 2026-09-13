"""Close a preliminary staging audit; never stage or edit repository content."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import hashlib,json,os,subprocess
from pydantic import BaseModel,ConfigDict,Field
HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
class Ref(Strict):
 path:str
 sha256:str=Field(pattern='^[a-f0-9]{64}$')
 size_bytes:int=Field(ge=0)
class Finding(Strict):
 path:str
 line:int
 classification:str
 basis:str
class Review(Strict):
 status:Literal['PRELIMINARY_REVIEW_COMPLETE_FINAL_REFRESH_REQUIRED']
 observed_at:str
 scanned_files:int
 scanned_selected_bytes:int
 candidates:int
 normal_pathspecs:int
 force_add_pathspecs:int
 findings:list[Finding]
 detected_actual_secret_values:int
 final_gates:list[str]
 omitted_scope:list[str]
class Manifest(Strict):
 status:Literal['PREPARED_NOT_STAGED_NOT_EXECUTED']
 files:list[Ref]
 public_requests:Literal[0]=0
 archive_executions:Literal[0]=0
 canonical_mutations:Literal[0]=0

def save(name:str,raw:bytes)->None:
 p=HERE/name
 if p.exists():raise ValueError('Refuse overwrite '+name)
 temp=p.with_suffix(p.suffix+'.tmp')
 with temp.open('xb') as f:f.write(raw)
 os.replace(temp,p)
def ref(p:Path)->Ref:
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return Ref(path=str(p.relative_to(HERE)),sha256=h,size_bytes=p.stat().st_size)
def main()->None:
 a=json.loads((HERE/'STAGING_AUDIT.json').read_bytes())
 findings=[]
 for x in a['secret_scan']:
  if x['classification'].startswith('explicit'):
   cls='redacted header, no cookie value retained'
   basis='Public curl-log line explicitly contains a redaction marker; originals excluded by its frozen custody audit.'
  elif x['kind']=='authorization':
   cls='Python type annotation, not an HTTP header'
   basis='Exact line declares authorization: Asset or authorization: g.Ref in a Pydantic model.'
  else:
   cls='Legacy archive filename substring, not a credential'
   basis='Match occurs inside local_path source_page filename at legacy row7861; surrounding JSON declares an archived HTML artifact, not a token field. No token-shaped value is copied here.'
  findings.append(Finding(path=x['path'],line=x['line'],classification=cls,basis=basis))
 force=sum(1 for x in a['candidates'] if x['ignored_rule'] and not x['tracked'])
 review=Review(status='PRELIMINARY_REVIEW_COMPLETE_FINAL_REFRESH_REQUIRED',
  observed_at=datetime.now(timezone.utc).isoformat(),scanned_files=len(a['candidates']),
  scanned_selected_bytes=sum(x['size_bytes'] for x in a['candidates']),candidates=len(a['candidates']),
  normal_pathspecs=len(a['candidates'])-force,force_add_pathspecs=force,findings=findings,
  detected_actual_secret_values=0,final_gates=[
   'Initial Git status capture precedes the completed County intake. Re-capture all status and package paths before staging; this is not the final release list.',
   'At scan time the live raw/ledger were64/65 while inventory remained63/24/39. Finish the explicit inventory update before the final archive smoke check.',
   'Add final County transaction, EB023/024, full-test logs and final acceptance artifacts only after their owners freeze them; they may be absent from this initial path list.',
   'Recompute selected file hashes after all concurrent writers freeze. Reject any mismatch rather than silently refreshing this historical manifest.',
   'Review94 explicitly ignored paths before force-add, including3 new canonical PDFs and19 current/exact-preimage snapshots; ordinary add would omit them.',
   'Keep both named user-owned files excluded. Do not use git add -A or a directory-wide forced add.',
   'Run the prepared19-check clean archive harness only against the reviewed commit exported outside the original workspace, supplying final inventory counts.',
   'Confirm final tracked evidence includes all closed-package payloads and full-tests.log. Git status alone omits ignored PDF/log inputs.'],
  omitted_scope=[
   'No secret values detected among selected text-like artifacts under the specified header/token patterns; this is not a universal credential scan.',
   'Binary document/image contents were not OCRed or visually re-reviewed for private information.',
   'Older untracked snapshots not selected by current-session names or exact HEAD preimage digest are listed separately; no broad historical force-add.',
   'No staging, commit, clean-export execution, source request, scheduling or production mutation performed.'])
 raw=(review.model_dump_json(indent=2)+'\n').encode();Review.model_validate_json(raw)
 save('REVIEW.json',raw);save('REVIEW.schema.json',(json.dumps(Review.model_json_schema(),indent=2)+'\n').encode())
 save('git-status.final-observation.nul',subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT))
 print(review.model_dump_json(indent=2))
if __name__=='__main__':main()
