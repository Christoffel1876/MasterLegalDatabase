"""Prepare six exact local source bindings only; no enrollment or HTTP execution."""
from pathlib import Path
import ast,hashlib,io,json,sys,shutil
from datetime import datetime,timezone
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
import pymupdf
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]/'MasterLegalDatabase'
PROPOSAL=BASE.parents[1]/'manual-watch-next-selection'
sys.dont_write_bytecode=True;sys.path.insert(0,str(PROPOSAL));sys.path.insert(0,str(ROOT))
from proposal_models import Proposal,Candidate
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord
class File(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 path:str;sha256:str;size_bytes:int
class Check(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 record_id:str;authority_id:str;baseline:File;actual_pdf_pages:int;exact_raw_line_sha256:str;observed_raw_manifest:File;metadata_files_verified:list[File]
class Catalog(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 schema_version:Literal[1];catalog_version:Literal['2026-09-13-v1'];prepared_at:str;status:Literal['PREPARED_NOT_INSTALLED'];sources:list[Candidate]=Field(min_length=6,max_length=6);public_requests:Literal[0];legal_currentness:Literal['not_verified']
def sha(b):return hashlib.sha256(b).hexdigest()
def file(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return File(path=p.relative_to(ROOT).as_posix(),sha256=h,size_bytes=p.stat().st_size)
def checked(ref):
 p=ROOT/ref.path
 if any(x.is_symlink() for x in (p,*p.parents)) or not p.is_file():raise ValueError('Nonordinary input')
 data=p.read_bytes()
 if len(data)!=ref.size_bytes or sha(data)!=ref.sha256:raise ValueError('Input identity differs: '+ref.path)
 return data
proposal=Proposal.model_validate_json((PROPOSAL/'PROPOSAL.json').read_bytes())
manifest=ROOT/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl';manifest_ref=file(manifest);rows={};hashes={}
with manifest.open('rb') as handle:
 for line in handle:
  row=ManualSourceIntakeRecord.model_validate_json(line);rows[row.record_id]=row;hashes[row.record_id]=sha(line)
assert file(manifest)==manifest_ref
checks=[]
for source in proposal.candidates:
 row=rows[source.record_id]
 assert (row.sha256,row.archive_path,row.size_bytes,row.layer_id,row.received_at,row.official_source_url,row.acquisition_method)==(source.baseline.sha256,source.baseline.path,source.baseline.size_bytes,source.layer_id,source.repository_received_at,source.historical_raw_url,source.historical_acquisition_method)
 assert hashes[source.record_id]==source.raw_manifest_exact_line_sha256
 body=checked(source.baseline)
 with pymupdf.open(stream=body,filetype='pdf') as pdf:
  assert len(pdf)==source.baseline_pages and not pdf.is_repaired and not pdf.is_encrypted
  assert body.startswith(b'%PDF-') and body.rstrip().endswith(b'%%EOF')
 evidence=[source.authority_evidence.artifact,source.custody_evidence.artifact,source.review_evidence.artifact,source.review_schema,*[e.artifact for e in source.referral_evidence]]
 seen={}
 for ref in evidence:checked(ref);seen[ref.path]=File(**ref.model_dump())
 checks.append(Check(record_id=source.record_id,authority_id=source.authority_id,baseline=File(**source.baseline.model_dump()),actual_pdf_pages=source.baseline_pages,exact_raw_line_sha256=hashes[source.record_id],observed_raw_manifest=manifest_ref,metadata_files_verified=list(seen.values())))
catalog=Catalog(schema_version=1,catalog_version='2026-09-13-v1',prepared_at=datetime.now(timezone.utc).isoformat(),status='PREPARED_NOT_INSTALLED',sources=proposal.candidates,public_requests=0,legal_currentness='not_verified')
out=BASE/'proposed/config';out.mkdir(parents=True,exist_ok=True)
(out/'manual_source_watch_sources_v1.json').write_text(catalog.model_dump_json(indent=2)+'\n');(out/'manual_source_watch_sources_v1.schema.json').write_text(json.dumps(Catalog.model_json_schema(),indent=2)+'\n')
(BASE/'BASELINE_CHECKS.jsonl').write_bytes(b''.join((c.model_dump_json()+'\n').encode() for c in checks));(BASE/'BASELINE_CHECK.schema.json').write_text(json.dumps(Check.model_json_schema(),indent=2)+'\n')
print('Verified6localPDFs',sum(x.baseline.size_bytes for x in checks),'bytes',sum(x.actual_pdf_pages for x in checks),'pages; no extraction/visual review/noHTTP')
print('Catalog SHA',sha((out/'manual_source_watch_sources_v1.json').read_bytes()))
