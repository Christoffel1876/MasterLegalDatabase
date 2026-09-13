"""Prepare, never apply, two exact municipal manual-intake requests."""
from __future__ import annotations
import hashlib,json,os,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
import pymupdf
from preparation_models import *
BASE=Path('/Users/mcoors/Documents/Project Geode');REPO=BASE/'MasterLegalDatabase'
sys.path.insert(0,str(REPO))
from geode.pipeline.manual_source_intake import ManualSourceIntakeRequest,ManualSourceIntakeRecord,archive_manual_source,reconcile_manual_source_intake,_validate_reconciliation_record
from geode.schemas.validators import require_official_source_url
from geode.connectors.archive_paths import safe_archive_stem
r=Path(__file__).resolve().parent
review=BASE/'handoffs/run-2026-09-12/colorado-springs-fire-fees-source-review'
modern=REPO/'research/local_review/colorado-springs-construction-fees-qa-2026-09-12'
now=datetime.now(timezone.utc)
COPIES=[]
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ordinary(p):
    if any(x.is_symlink() for x in [p,*p.parents]):raise ValueError('symlink: '+str(p))
    if not p.is_file():raise ValueError('not ordinary file: '+str(p))
    return p

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()==data:return
        raise ValueError('Refusing to overwrite preparation file: '+str(path))
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def asset(rel):
    p=ordinary(r/rel);return Asset(path=rel,sha256=digest(p),size_bytes=p.stat().st_size)
def copy(src,rel,kind):
    ordinary(src);atomic(r/rel,src.read_bytes());a=asset(rel)
    assert a.sha256==digest(src)
    COPIES.append(Copy(original_path=src.relative_to(BASE).as_posix(),preserved=a,kind=kind));return a
def save(rel,model):atomic(r/rel,(model.model_dump_json(indent=2)+'\n').encode())
def schema(rel,model):atomic(r/rel,(json.dumps(model.model_json_schema(),indent=2)+'\n').encode())
def records(path):
    with ordinary(path).open('r',encoding='utf-8') as f:
        return [ManualSourceIntakeRecord.model_validate_json(line) for line in f if line.strip()]
rawrel='_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
ledgerrel='_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl'
reportrel='_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json'
baseline=[]
for rel in [rawrel,ledgerrel,reportrel,'_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_POLICY.json','_CONTROL_PLANE/BLOCKED_DOWNLOAD_QUEUE.json']:
    a=copy(REPO/rel,'inputs/current/'+rel,'baseline');baseline.append(Baseline(repository_path=rel,preserved=a,records=len(records(REPO/rel)) if rel.endswith('.jsonl') else None))
for rel in ['AGENTS.md','geode/pipeline/manual_source_intake.py','geode/schemas/validators.py','geode/constants.py','geode/connectors/archive_paths.py','geode/utils/file_io.py']:
    copy(REPO/rel,'inputs/current/'+rel,'code_reference')
for name in ['SOURCE_SCOPE.json','SOURCE_SCOPE.schema.json','FINAL_MANIFEST.json','README.md']:
    copy(review/name,'inputs/review-scope/'+name,'review_metadata')
for name in ['SOURCE_QA.json','SOURCE_QA.schema.json','FINAL_MANIFEST.json']:
    copy(modern/name,'inputs/modern-qa/'+name,'review_metadata')
for name in ['ACCEPTANCE.json','ACCEPTANCE.schema.json']:
    copy(REPO/'docs/audits/FOUR_HOUR_RUN_2026-09-12/COLORADO_SPRINGS_CONSTRUCTION_QA'/name,'inputs/modern-qa/'+name,'review_metadata')
copy(BASE/'handoffs/run-2026-09-12/el-paso-intake-transaction/execution/RECEIPT.json','inputs/el-paso-lessons/completed-transaction-receipt.json','review_metadata')
copy(BASE/'handoffs/run-2026-09-12/el-paso-intake-transaction/README.md','inputs/el-paso-lessons/README.md','review_metadata')
copy(review/'acquisition/plan.json','inputs/acquisition-plan.json','http_receipt')
copy(review/'acquisition/LINK_PROVENANCE.json','inputs/LINK_PROVENANCE.json','http_receipt')
scope=json.loads((review/'SOURCE_SCOPE.json').read_text());plan=json.loads((review/'acquisition/plan.json').read_text())
ids=['colorado-springs-code-services-fees-2015-atlas-directed','colorado-springs-construction-fees-atlas-directed']
expected=['555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56','e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a']
sources=[];templates=[];requests=[];previews=[]
for index,(sid,rid,sha) in enumerate(zip(['SD014-01','SD014-02'],ids,expected,strict=True)):
    srcmeta=next(x for x in scope['sources'] if x['source_id']==sid);target=next(x for x in plan['targets'] if x['source_id']==sid)
    filename='feeschedule_codeservices_final_2015.pdf' if index==0 else '2026 Fee Schedule Construction Services.pdf'
    original=copy(review/sid/'original.pdf',f'sources/{sid}/{filename}','source')
    assert original.sha256==sha and original.size_bytes==[162682,258393][index]
    with pymupdf.open(r/original.path) as pdf:assert len(pdf)==7 and not pdf.is_repaired and not pdf.is_encrypted
    acq={}
    for name in ['reservation.json','result.json','public-headers.json','parent_html.bin','parent_reservation.json','parent_result.json','parent_public_headers.json']:
        acq[name]=copy(review/'acquisition'/sid/name,f'inputs/acquisition/{sid}/{name}','parent_html' if name=='parent_html.bin' else 'http_receipt')
    copy(review/sid/'page-0001.png',f'inputs/identity/{sid}-page-1.png','identity_image')
    reservation=json.loads((r/acq['reservation.json'].path).read_text());result=json.loads((r/acq['result.json'].path).read_text())
    assert result['reservation_sha256']==acq['reservation.json'].sha256 and result['body']['sha256']==sha and result['body']['size_bytes']==original.size_bytes
    assert result['outcome']=='complete' and result['http_status']==200 and not result['partial_body'] and result['redirect_url'] is None
    assert result['public_headers']['sha256']==acq['public-headers.json'].sha256
    url=require_official_source_url(reservation['url']);assert url==target['url'] and urlsplit(url).netloc=='coloradosprings.gov'
    parent=json.loads((r/acq['parent_reservation.json'].path).read_text());parentresult=json.loads((r/acq['parent_result.json'].path).read_text())
    assert parentresult['body']['sha256']==acq['parent_html.bin'].sha256 and parentresult['reservation_sha256']==acq['parent_reservation.json'].sha256 and parentresult['public_headers']['sha256']==acq['parent_public_headers.json'].sha256
    soup=BeautifulSoup((r/acq['parent_html.bin'].path).read_bytes(),'html.parser');iframes=[x for x in soup.find_all('iframe') if x.get('data-src')==url];assert len(iframes)==1
    iframe=iframes[0];viewer=iframe['src'];query=urlsplit(viewer).query;fields=[p.split('=',1)[1] for p in query.split('&') if p.startswith('file=')];assert len(fields)==1 and unquote(fields[0])==url
    referral=Referral(parent_url=parent['url'],parent_html=acq['parent_html.bin'],original_data_src=iframe['data-src'],original_viewer_src=viewer,encoded_file_argument=fields[0],resolved_url=url,transformation='Read data-src; decode the pdf.js file argument exactly once; require both to equal the exact requested PDF URL.',parent_reservation=acq['parent_reservation.json'],parent_result=acq['parent_result.json'],parent_public_headers=acq['parent_public_headers.json'])
    if index==0:
        title='Colorado Springs Fire Department — 2015 Fee Schedule - Code Services'
        role='Code Services fee schedule as received; visible 2015 title, enactment/current status not established'
        dates='2015';date_role='Visible title year; not an independently verified effective or adoption date'
        extent='Root source-scope review inspected all seven pages for structure and selected context; full numeric table/row QA is not complete. This preparation independently viewed page 1 for municipal issuer and title only.'
        quals=['Native white-on-white page-1 numbers and the 2015 Proposed changes strings on pages 2–6 are not visible in the checked white source regions; neither visible title nor hidden native strings establishes enactment or operative status.','Definition headings and body order require layout review; no complete extraction or numeric table certification.','The modern construction schedule references a Code Services Fee Schedule without an edition; no supersession or exact cross-document edition linkage has been established.']
        qa=asset('inputs/review-scope/SOURCE_SCOPE.json')
    else:
        title='Colorado Springs Fire Department — Construction Services Fee Schedule'
        role='Construction Services fee schedule as received'
        dates='Effective 07/01/2026';date_role='Source-printed effective-date claim only; adopting instrument not verified'
        extent='Accepted Atlas seven-page source QA binds 128 fee rows, nine tables, thirteen definitions, three in-table notes and 14,423 native bytes. This is extraction/association review, not adoption/currentness or answer-safety promotion.'
        quals=['City fire department is the municipal issuer; the complete definition identifies PPRBD as the collector of construction plan-check fees through its portal, with conditional deduction at CSFD plan approval. PPRBD is not substituted as the source owner.','Implementation assesses fees upon the plan approval date. High-pile storage and hazardous-material fees point to another Code Services schedule without specifying its edition. Full context remains linked in the accepted QA.','Preserve the contents/actual definitions page mismatch and all native source anomalies. No fee calculation or legal effective-date verification.']
        qa=asset('inputs/modern-qa/SOURCE_QA.json')
    note=f"Direct ordinary Atlas HTTPS acquisition from {url}, request reserved {reservation['reserved_at']}, complete HTTP 200 response finished {result['finished_at']}, no redirects; original response digest {sha}. This is not a Sherlock received-package claim. Source role: {role}. Source date: {dates}; {date_role}. {extent} {' '.join(quals)} Actual repository receipt is not yet assigned in this proposal; execution must set received_at once to its actual intake UTC time and preserve this acquisition interval separately."
    template=RecordTemplate(record_id=rid,layer_id='10_Municipal_Authorities',authority_id='CO-MUNICIPAL-COLORADO_SPRINGS',official_source_name=title,official_source_url=url,acquisition_method='manual_official_download',received_from='Atlas; direct ordinary public HTTPS response from the City of Colorado Springs',reviewer_name='Atlas',reviewer_email=None,custody_note=note,source_file=original,original_filename=filename,expected_sha256=sha,size_bytes=original.size_bytes,source_format='pdf',allow_duplicate=False,intake_id=None,archive_path=None,received_at=None,status='proposed_not_applied',intended_record_status='archived_pending_pipeline',archive_path_template=f'_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/{rid}/{{ACTUAL_INTAKE_UTC_YYYYMMDDTHHMMSSZ}}_{safe_archive_stem(Path(filename).stem)}.pdf',legal_currentness='not_verified')
    req=ManualSourceIntakeRequest(record_id=rid,layer_id=template.layer_id,source_file=str(r/original.path),official_source_name=title,official_source_url=url,acquisition_method='manual_official_download',received_from=template.received_from,reviewer_name='Atlas',reviewer_email=None,custody_note=note,expected_sha256=sha,allow_duplicate=False)
    preview=archive_manual_source(REPO,req,dry_run=True,timestamp=now);ManualSourceIntakeRecord.model_validate(preview);_validate_reconciliation_record(REPO,preview)
    assert preview.status=='dry_run_pending_archive' and not preview.blocked_queue_match
    requests.append(req);previews.append(preview);templates.append(template)
    sources.append(Source(source_id=sid,proposed_record_id=rid,authority_id=template.authority_id,layer_id=template.layer_id,issuer='Colorado Springs Fire Department, City of Colorado Springs',document_role=role,original=original,original_received_body_path=f'handoffs/run-2026-09-12/sd014-fire-fee-pdfs/runtime/events/{index+1:04}/body.bin',page_count=7,http_url=url,request_started_at=datetime.fromisoformat(reservation['reserved_at'].replace('Z','+00:00')),response_completed_at=datetime.fromisoformat(result['finished_at'].replace('Z','+00:00')),http_status=200,redirect_count=0,complete_response=True,acquisition_method='manual_official_download',response_receipts=[acq[n] for n in ['reservation.json','result.json','public-headers.json']],referral=referral,source_printed_date_claim=dates,date_role=date_role,verified_adoption_date=None,verified_effective_date=None,actual_future_repository_received_at=None,source_qa_scope=extent,source_qa_metadata=qa,legal_currentness='not_verified',answer_safe=False,qualifications=quals))
# Global byte-identity screen, independent of the generic same-record-only duplicate check.
rawrows=records(REPO/rawrel);ledgerrows=records(REPO/ledgerrel);sizes={s.original.size_bytes for s in sources};digests={s.original.sha256 for s in sources}
count=0;symlinks=[];hashed=[];matches=[];lfsmatches=[]
for base,dirs,files in os.walk(REPO/'_RAW_ARCHIVE',followlinks=False):
    for name in dirs+files:
        p=Path(base)/name
        if p.is_symlink():symlinks.append(p.relative_to(REPO).as_posix())
    for name in files:
        p=Path(base)/name
        if p.is_symlink() or not p.is_file():continue
        count+=1;size=p.stat().st_size
        if size in sizes:
            h=digest(p);hashed.append(Asset(path=p.relative_to(REPO).as_posix(),sha256=h,size_bytes=size))
            if h in digests:matches.append(p.relative_to(REPO).as_posix())
        elif size<200:
            raw=p.read_bytes()
            if raw.startswith(b'version https://git-lfs.github.com/spec/v1') and any(h.encode() in raw for h in digests):lfsmatches.append(p.relative_to(REPO).as_posix())
patterns=expected+[s.http_url for s in sources]+ids;pattern_counts={p:0 for p in patterns};metadata=[]
for rel in ['_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl','_CONTROL_PLANE/RAW_SOURCE_HASH_MANIFEST.json','_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json','_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json','_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json']:
    p=ordinary(REPO/rel);metadata.append(Asset(path=rel,sha256=digest(p),size_bytes=p.stat().st_size));tail=b'';encoded=[p.encode() for p in patterns];keep=max(map(len,encoded))-1
    with p.open('rb') as f:
        while chunk:=f.read(1024*1024):
            combined=tail+chunk
            for pat in patterns:pattern_counts[pat]+=combined.count(pat.encode())-tail.count(pat.encode())
            tail=combined[-keep:]
ded=Dedupe(observed_at=now,ordinary_raw_files_screened=count,symlink_paths=symlinks,same_size_files_hashed=hashed,matching_raw_files=matches,matching_lfs_pointers=lfsmatches,matching_raw_manifest_records=[x.record_id for x in rawrows if x.sha256 in digests],matching_ledger_records=[x.record_id for x in ledgerrows if x.sha256 in digests],proposed_id_collisions=[x.record_id for x in rawrows+ledgerrows if x.record_id in ids],metadata_search_inputs=metadata,exact_metadata_pattern_counts=pattern_counts,limitation='Global ordinary _RAW_ARCHIVE files screened by exact candidate byte size then SHA-256; small LFS pointers checked for candidate OIDs. Five named current metadata files searched for exact URLs, hashes and proposed IDs. No fuzzy URL/history/currentness inference; unavailable original bytes cannot be compared. Metadata inputs are repository-relative hash references, not all duplicated in this package.')
assert not symlinks and not matches and not lfsmatches and not ded.matching_raw_manifest_records and not ded.matching_ledger_records and not ded.proposed_id_collisions and not any(pattern_counts.values())
recon=reconcile_manual_source_intake(REPO,dry_run=True);assert not recon.added_intake_ids and not recon.report_needs_update
save('BASELINE_RECONCILIATION.json',recon)
for b in baseline:assert digest(REPO/b.repository_path)==b.preserved.sha256
for name,rows,model in [('proposed-records',templates,RecordTemplate),('requests',requests,ManualSourceIntakeRequest),('dry-run-previews',previews,ManualSourceIntakeRecord),('source-provenance',sources,Source)]:
    for row in rows:model.model_validate(row)
    atomic(r/f'{name}.jsonl',(''.join(row.model_dump_json()+'\n' for row in rows)).encode());schema(name+'.schema.json',model)
preflight=[
 'Root approval of these exact two source IDs and this frozen preparation; no source or registry/currentness expansion.',
 'Freeze exact current raw-manifest, manual-ledger and report bytes plus policy/blocked-queue/code hashes. Refuse any change from this baseline and serialize against other intake writers.',
 'Validate every source SHA, byte size, PDF page count, public HTTP receipt and observed official iframe referral. Re-run both ManualSourceIntakeRequest and final ManualSourceIntakeRecord validation, and the actual strict host and layer/path/aware-time checks before any raw write.',
 'Re-run global raw-byte and LFS-OID dedupe plus source-ID/digest/path collision checks. Generic duplicate rejection only checks the same record_id and digest and is insufficient alone.',
 'Run reconcile_manual_source_intake(root,dry_run=True) before mutation; require current 59 originals/60 ledger rows, no additions/report drift, and preserve the existing missing EO row.',
 'Do not copy dry-run preview timestamps, intake IDs, archive paths or dry_run status into the real manifest. Set one actual UTC intake time at execution, freeze an intent, construct two final archived_pending_pipeline records and an exact JSONL suffix, and persist that same intent for any resume.',
 'Snapshot all three exact preimages before writes. Preflight all destinations and ancestors as ordinary, non-symlink paths. Stage independent source-byte copies; never replace an existing original. Verify both new originals before any manifest publication.',
 'Avoid the generic apply helper: its raw-manifest helper reserializes existing rows and its multi-file writes are not a resumable transaction. Use a separately reviewed exact-prefix, non-overwriting transaction preserving before+suffix bytes, stage order, intent and interrupted states, as learned from El Paso.',
 'Validate both final rows against actual reconciliation host/path rules before mutation; the El Paso interruption arose because initial record parsing was weaker than reconciliation validation.',
 'After the two original files and exact manifest suffix, append the same validated suffix to the ledger and write the typed reconciled report. Require 61 verified originals, 62 ledger records, unchanged historical prefixes and unchanged missing EO history; rerun dry-run reconciliation and require no additions/report changes.',
 'Preserve execution receipt with actual time, source hashes, snapshots and final manifest/ledger/report hashes. Run appropriate repository schema checks afterward and retain their actual result; no legal-rule, coverage, source-registry or lookup-currentness promotion is included.'
]
prep=Preparation(schema_version='1.0',status='PREPARED_NOT_APPLIED',prepared_at=now,actual_repository_received_at=None,repository_mutations=0,public_requests=0,sources=sources,proposed_records=templates,current_raw_records=len(rawrows),current_ledger_records=len(ledgerrows),current_verified_originals=len(recon.report.archive_verification.verified_intake_ids),preserved_missing_ledger_only_ids=recon.report.archive_verification.missing_ledger_only_intake_ids,expected_raw_records_after_two_new_intakes=61,expected_ledger_records_after_two_new_intakes=62,expected_verified_originals_after_two_new_intakes=61,baseline=baseline,copies=COPIES,dedupe=ded,host_validation='Both exact official URLs accepted by current require_official_source_url; no policy change.',request_schema_validation='Two real ManualSourceIntakeRequest instances validated; two archive_manual_source(dry_run=True) previews validated as ManualSourceIntakeRecord. Preview receipt times are preparation-only, never final intake times.',reconciliation=asset('BASELINE_RECONCILIATION.json'),required_preflight=preflight,warnings=['Preparation only. All actual future repository receipt fields remain null in canonical append templates. Preview records are deliberately dry_run_pending_archive and cannot be reconciled as archived records.','Source-date claims, observed HTTP acquisition intervals and future repository intake time are distinct. The 2015 PDF has not received complete numeric table QA; the modern full QA remains source extraction review, not legal effect.','Review metadata is copied exactly but its full image/native/code dependencies are retained in the separate frozen source QA packages, not duplicated here.','Do not call these two PDFs newly adopted laws, substitute PPRBD for the municipal issuer, claim supersession between editions, or treat all 62 ledger rows as available originals.'])
save('PREPARATION.json',prep);schema('PREPARATION.schema.json',Preparation)
print('READY',len(sources),'sources',sum(s.original.size_bytes for s in sources),'bytes',digest(r/'PREPARATION.json'))
