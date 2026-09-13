from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,sys,os
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12');P=B/'extended-run/ebenezer-023-024';O=B/'extended-run/eb023024-closeout-status';D=B/'ebenezer/reviews';sys.path.insert(0,str(O));from models import *
def asset(f,base):return Asset(path=f.relative_to(base).as_posix(),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),size_bytes=f.stat().st_size)
def save(name,model):
 f=O/name;assert not f.exists();tmp=f.with_suffix('.tmp');tmp.write_text(model.model_dump_json(indent=2)+'\n');os.replace(tmp,f);(O/(name[:-5]+'.schema.json')).write_text(json.dumps(type(model).model_json_schema(),indent=2)+'\n')
manifest=json.loads((P/'MANIFEST.json').read_bytes());by={a['path']:a for a in manifest['files']};msha=asset(P/'MANIFEST.json',P).sha256
for a in manifest['files']:
 f=P/a['path'];assert not f.is_symlink();assert '..' not in Path(a['path']).parts;assert asset(f,P).model_dump()==a
for name in ['MANIFEST.json','SOURCE_ONLY_IDENTITIES.json','START_HERE.md']:
 dst=O/'packet'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(P/name,dst)
originals=[];retained=[];docs=[]
for n in [23,24]:
 d=next(D.glob(f'EB-PDF-0{n}_*'));out=O/'received'/d.name
 for f in sorted(d.rglob('*')):
  assert not f.is_symlink()
  if f.is_file():
   originals.append(asset(f,D));dest=out/f.relative_to(d);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);retained.append(asset(dest,O))
 completion=json.loads((d/'COMPLETION_RECEIPT.json').read_bytes());freeze=json.loads((d/'PASS1_FREEZE_RECEIPT.json').read_bytes());sid=completion['source_id'];checks=[]
 def check(name,expected,f,base):
  actual=asset(f,base);checks.append(Check(name=name,expected_sha256=expected,actual_sha256=actual.sha256,matches=actual.sha256==expected,evidence_path=actual.path))
 for field,name in [('pass1_frozen_sha256','PASS1_frozen.md'),('pass1_freeze_receipt_sha256','PASS1_FREEZE_RECEIPT.json'),('pass2_review_sha256','PASS2_REVIEW.md')]:check(field,completion[field],out/name,O)
 check('packet_manifest',completion['packet_manifest_sha256'],O/'packet/MANIFEST.json',O)
 check('instructions',completion['start_here_instruction_sha256'],O/'packet/START_HERE.md',O)
 check('pass1_prompt',freeze['assistance']['task_prompt_retained_sha256'],out/'prompts/PASS1_TASK_PROMPT.txt',O)
 for kind,packetkind in [('source','01-source-only'),('candidate','02-candidate-text')]:
  for f in (out/kind).iterdir():
   if f.is_file():
    relative=f'{packetkind}/{sid}/{f.name}'
    if relative in by:check(f'packet:{relative}',by[relative]['sha256'],f,O)
 check('completion_pdf_claim',completion['original_pdf_sha256'],out/'source/original.pdf',O)
 check('completion_candidate_claim',completion['candidate_actual_sha256'],out/'candidate/candidate.txt',O)
 check('completion_candidate_expected_claim',completion['candidate_expected_sha256_from_manifest'],out/'candidate/candidate.txt',O)
 for page in freeze['page_images']:check(f"freeze_page_{page['physical_page']}",page['sha256'],out/f"source/page-{page['physical_page']:04}.png",O)
 limits=['Both passes are caption-mediated assisted review; no direct pixel inspection or blind visual transcription is verified.','Consolidated Pass2 reopen report declares fresh Read/Task page representations after release. Individual per-page Read records referenced in the Pass2 report are absent from this delivery. Historical tool calls and actual ordering are not independently witnessed.','Worker packet verifier failed because jsonschema was missing. Manual-hash fallback is reported; this closeout independently hashes packet payloads and delivered source/candidate/page copies, without rerunning source QA.','Reported timestamps and file mtimes do not independently establish historical review execution or completion.','All content findings remain pending Atlas direct source verification; this receipt accepts no glyph, date, fee or layout correction.']
 if n==23:limits.append('Completion receipt says utc_freeze02:22:23Z; PASS1_FREEZE_RECEIPT says02:22:35Z. Both are before reported candidate release02:22:52Z;12-second discrepancy remains unresolved.')
 else:limits.append('PASS2_REOPEN_TASK report is present, but its original task prompt and the individual Read/crop records it references are not retained in this delivery. This limits independent reconstruction of the declared method.')
 docs.append(Document(assignment_id=completion['assignment_id'],source_id=sid,original_delivery=str(d),expected_pages=freeze['expected_pages'],worker_status=completion['status'],reported_completion_at=datetime.fromisoformat(completion['utc_completion'].replace('Z','+00:00')),reported_candidate_release_at=datetime.fromisoformat(completion['utc_candidate_release'].replace('Z','+00:00')),reported_pass1_freeze_at=datetime.fromisoformat(freeze['utc_freeze'].replace('Z','+00:00')),checks=checks,pass2_reopened_pages_claim=list(range(1,freeze['expected_pages']+1)),independent_execution_witness=False,retained_reopen_report=str((out/'pass2_reopen/PASS2_REOPEN_TASK.md').relative_to(O)),retained_individual_reopen_read_notes=[],method='caption_mediated_assisted_review',limitations=limits,content_findings_accepted_by_this_receipt=False))
 assert all(x.matches for x in checks),[(x.name,x.expected_sha256,x.actual_sha256) for x in checks if not x.matches]
r=Receipt(observed_at=datetime.now(timezone.utc),completed_worker_documents=['EB-PDF-023','EB-PDF-024'],pending_worker_documents=[],pending_atlas_verification=['EB-PDF-023','EB-PDF-024'],documents=docs,packet_manifest_sha256=msha,packet_payloads_hash_checked=len(manifest['files']),packet_payloads_copied='manifest_and_identity_metadata_only',original_files=originals,retained_files=retained,limitations=['This is a shared-folder status snapshot only. It does not claim the unavailable Grok UI was inspected or that a worker is currently running.','Prepared packet status remains historical PREPARED_NOT_DISPATCHED; actual reviewed deliveries are separately received evidence.','Complete61-file delivery copies are retained. The complete original packet is hash-checked locally but only its manifest, identities and instructions are copied; its executable verifier and unused runtime artifacts are not needed for this receipt.'],source_pages_visually_reviewed_by_this_task=0,network_requests=0)
save('STATUS_RECEIPT.json',r)
print('documents',[(x.assignment_id,len(x.checks)) for x in docs],'files',len(originals),'packetpayloads',len(manifest['files']),'msha',msha)
