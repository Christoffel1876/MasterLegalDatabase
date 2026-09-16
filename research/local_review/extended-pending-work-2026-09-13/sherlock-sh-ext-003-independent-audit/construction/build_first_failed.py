from pathlib import Path
from datetime import datetime,timezone
import sys,os,json,hashlib,re,subprocess,shutil
from urllib.parse import urljoin,unquote
from bs4 import BeautifulSoup
import pymupdf
B=Path('/Users/mcoors/Documents/Project Geode'); E=B/'handoffs/run-2026-09-12/extended-run'; P=E/'sherlock-sh-ext-003'; D=P/'deliveries/20260913T021737Z'; O=E/'sherlock-sh-ext-003-independent-audit'; R=B/'MasterLegalDatabase'
sys.path.insert(0,str(O));from audit_models import *
def sha(b):return hashlib.sha256(b).hexdigest()
def asset(p,base=O):
 with p.open('rb') as h:s=hashlib.file_digest(h,'sha256').hexdigest()
 return Asset(path=p.relative_to(base).as_posix(),sha256=s,size_bytes=p.stat().st_size)
def write(name,model):
 f=O/name;assert not f.exists(),name;f.parent.mkdir(parents=True,exist_ok=True)
 tmp=f.with_suffix(f.suffix+'.tmp');tmp.write_text(model.model_dump_json(indent=2)+'\n');os.replace(tmp,f)
 sf=O/(name.rsplit('.',1)[0]+'.schema.json');sf.write_text(json.dumps(type(model).model_json_schema(),indent=2)+'\n')
def copy(src,dst):
 assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
now=datetime.now(timezone.utc); inv=json.loads((D/'ARTIFACT_INVENTORY.json').read_bytes()); expected={x['path']:x for x in inv['files']};items=[]
for f in sorted(D.rglob('*')):
 assert not f.is_symlink()
 if not f.is_file():continue
 rel=f.relative_to(D).as_posix();raw=f.read_bytes();a=asset(f,D)
 if rel in expected:assert a.model_dump()==expected[rel]
 lines=raw.splitlines(keepends=True);redacted=[]
 for n,line in enumerate(lines,1):
  if re.match(rb'(?i)^set-cookie\s*:',line):
   redacted.append(n);lines[n-1]=b'Set-Cookie: [REDACTED]\r\n' if line.endswith(b'\r\n') else b'Set-Cookie: [REDACTED]\n'
 dst=O/'received'/rel;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();dst.write_bytes(b''.join(lines) if redacted else raw)
 items.append(CustodyItem(original=a,retained=asset(dst),mode='set_cookie_redacted' if redacted else 'exact',redacted_lines=redacted))
write('CUSTODY_RECEIPT.json',Custody(captured_at=now,original_delivery=str(D),supplied_inventory_entries=len(expected),supplied_inventory_mismatches=[],unlisted_original_files=sorted({x.original.path for x in items}-set(expected)),items=items,scope='All 346 delivery files hashed locally. Four raw curl logs have explicit public Set-Cookie-redacted derivatives; original hashes verified at capture, not recomputable from derivatives. No originals changed.'))
pm=json.loads((P/'FINAL_MANIFEST.json').read_bytes());assert sha((P/'FINAL_MANIFEST.json').read_bytes())=='47363aa29ca229e5b20f60dca1e9abca401e09c9a3fb4fd9f312bed9a621a4ce'
for a in pm['files']:
 f=P/a['path'];assert asset(f,P).model_dump()==a;copy(f,O/'prepared-packet'/a['path'])
copy(P/'FINAL_MANIFEST.json',O/'prepared-packet/FINAL_MANIFEST.json')
# Stream the current full legacy file, then independently stream the pinned Git blob.
legacy_path=R/'_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl';copy(legacy_path,O/'comparison/full-legacy.jsonl'); full=O/'comparison/full-legacy.jsonl'
log=json.loads((D/'ACTION_LOG.json').read_bytes()); reservations=log['reservations'];results=log['results']; urls={x['requested_url'] for x in reservations};hs={x['body_sha256'] for x in results if x['body_sha256']};matches=[]
with full.open('rb') as h:
 for n,raw in enumerate(h,1):
  row=json.loads(raw);reason=[]
  if row.get('requested_url') in urls:reason.append('requested_url_exact')
  if row.get('source_url') in urls:reason.append('source_url_parent_context')
  if row.get('sha256') in hs:reason.append('body_digest')
  if reason:
   rawpath=row.get('raw_path');mapped=None;state='not_checked';available=None
   if 'body_digest' in reason and rawpath and '/_RAW_ARCHIVE/' in rawpath.replace('\\','/'):
    suffix='_RAW_ARCHIVE/'+rawpath.replace('\\','/').split('/_RAW_ARCHIVE/',1)[1];mapped=suffix;f=R/suffix
    if not f.exists():state='missing'
    elif f.is_symlink() or not f.is_file():state='nonordinary'
    else:state='ordinary_present';available=asset(f,R).sha256
   matches.append(Match(line=n,raw_line_sha256=sha(raw),source_id=row['source_id'],requested_url=row.get('requested_url'),source_url=row.get('source_url'),recorded_sha256=row.get('sha256'),recorded_raw_path=rawpath,reasons=reason,mapped_repository_path=mapped,mapped_path_state=state,available_sha256=available))
count=n;pin='2f2b450d8ecb3eff5258598d7be27189bc5e4cff';proc=subprocess.Popen(['git','show',pin+':_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'],cwd=R,stdout=subprocess.PIPE);digest=hashlib.sha256();pn=0
for raw in proc.stdout:json.loads(raw);digest.update(raw);pn+=1
assert proc.wait()==0;assert digest.hexdigest()==asset(full).sha256 and pn==count
legacy=Legacy(current_commit_observed=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),pinned_commit=pin,stream=asset(full),pinned_stream_sha256=digest.hexdigest(),current_rows=count,pinned_rows=pn,identical_streams=True,matching_rows=matches,comparison_scope='All 48,390 rows of current and pinned legacy metadata; exact requested URL, exact source URL parent-context, and all received nonempty body digests. One identical complete stream retained for both verified hashes.',limitations=['Historical recorded digests are metadata comparisons, not fresh original-byte comparisons.','Only the eight digest-matched historic raw paths were checked for local presence; no global raw/LFS absence claim.','A historic filename ending .html does not prove HTML content; two received PDFs match such digests.'])
write('LEGACY_COMPARISON.json',legacy)
# Bind current canonical manual records without mutating them.
manual=R/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl';copy(manual,O/'comparison/current-manual.jsonl');manual_rows=[]
with manual.open('rb') as h:
 for row in h:manual_rows.append(json.loads(row))
referrals=[]
for idx in list(range(9,25))+[26,27,28]:
 r=reservations[idx-1];parent=2 if 9<=idx<=14 else 1 if 15<=idx<=20 else 4 if 21<=idx<=24 else 6
 fp=D/f'raw/SHEXT003-A{parent:03}.html';soup=BeautifulSoup(fp.read_bytes(),'html.parser');pu=reservations[parent-1]['requested_url'];base=soup.find('base',href=True);base=base['href'] if base else None
 anchors=soup.find_all('a',href=True)
 if idx>=26:
  a=next(a for a in anchors if urljoin(base or pu,a['href'])==r['requested_url'])
 else:
  a=next(a for a in anchors if urljoin(pu,a['href'])==r['requested_url'])
 resolved=urljoin(base or pu,a['href'])
 referrals.append(Referral(action_id=r['action_id'],parent_action_id=f'SHEXT003-A{parent:03}',parent=asset(O/'received'/fp.relative_to(D)),parent_url=pu,original_href=a['href'],html_base_href=base,visible_label=' '.join(a.get_text(' ',strip=True).split()),resolved_url=resolved,attempted_url=r['requested_url'],exact_browser_resolution_match=resolved==r['requested_url']))
observations={26:['First page names Board of County Commissioners of the County of Gunnison, Colorado, Resolution No. 25-24 and a resolution establishing a schedule of building permit fees.','Source first page states the attached Exhibit A fee schedule is adopted and says it shall not be effective unless and until a copy is recorded. This is source wording, not a legal-effect determination.','Hand-filled adoption line visually reads 17th June, 2025; signature mark is present without identity authentication. Recorder stamp reads 6/18/2025 10:46:06 AM, reception702424, Page1of3. Remaining pages not visually reviewed.'],27:['First page names the Gunnison county board, Resolution No.23-22, and adoption of listed 2021 building codes, Colorado model electric-ready/solar-ready code and IWUIC amendments.','Recorder stamp visibly reads11/14/2023 8:13:55 AM, reception694082, Page1of16. No full16-page amendment/execution review.'],28:['First page names Gunnison county board, Resolution No.2022-33, adopting2021 International Wildland Urban Interface Code.','First page distinguishes recordation and new building-permit applications beginning January1,2023; unincorporated-area language and Exhibit A incorporation are visible. No operative/currentness conclusion.','Recorder stamp visibly reads9/8/2022 3:53:42 PM, reception687079, Page1of4; handwritten adoption date appears6th September2022. No signer identity determination.']}
pdfs=[]
for n in [26,27,28]:
 f=O/f'received/raw/SHEXT003-A{n:03}.pdf';body=f.read_bytes();doc=pymupdf.open(stream=body,filetype='pdf');r=reservations[n-1]
 pdfs.append(PDF(action_id=r['action_id'],source=asset(f),authority_id='CO-COUNTY-GUNNISON',physical_pages=len(doc),is_repaired=doc.is_repaired,encrypted=doc.is_encrypted,terminal_eof=body.rstrip().endswith(b'%%EOF'),first_page_image=asset(O/f'visual/A{n:03}-page1.png'),render_command=['pdftoppm','-f','1','-singlefile','-r','120','-png',f'received/raw/SHEXT003-A{n:03}.pdf',f'visual/A{n:03}-page1'],reviewed_pages=[1],role_observations=observations[n],historical_digest_lines=[m.line for m in matches if m.recorded_sha256==sha(body)],historical_exact_request_lines=[m.line for m in matches if m.requested_url==r['requested_url']],canonical_manual_digest_lines=[i for i,x in enumerate(manual_rows,1) if sha(body) in [x.get('sha256'),x.get('content_sha256'),x.get('file_sha256')]],limitations=['Received from Sherlock delivery; supplied HTTP200 and local tool timing claims not independently witnessed by Atlas.','First-page role review only; complete legal text, all attachments, supersession and legal currentness remain unverified.']))
# Check original records close their exact serial prefix and each retained-body binding.
for i,(r,z) in enumerate(zip(reservations,results)):
 assert r['action_id']==z['action_id'];assert json.loads((D/f"reservations/{r['action_id']}.json").read_bytes())==r
 assert json.loads((D/f"results/{r['action_id']}.json").read_bytes())==z
 for a in z['retained_assets']:assert asset(D/a['path'],D).model_dump()==a
 assert datetime.fromisoformat(z['finished_at'].replace('Z','+00:00'))>=datetime.fromisoformat(r['reserved_at'].replace('Z','+00:00'))
 if i:assert datetime.fromisoformat(r['reserved_at'].replace('Z','+00:00'))>=datetime.fromisoformat(results[i-1]['finished_at'].replace('Z','+00:00'))
reject=next(f for f in (O/'received/logs').glob('budget_reserve*') if b'Distinct requested URL cap exceeded' in f.read_bytes());nextinput=O/'received/inputs/reserve_SHEXT003-A031.json'
if not nextinput.exists():nextinput=next(f for f in (O/'received/inputs').iterdir() if 'A031' in f.name)
stale=json.loads((D/'logs/final_status.json').read_bytes());print('STALE',stale)
budget=Budget(actions=30,distinct_urls=len(urls),chaffee_actions=20,gunnison_actions=10,accepted_body_bytes=sum(z['observed_body_bytes'] for z in results),maximum_body_bytes=max(z['observed_body_bytes'] for z in results),response_bodies=sum(bool(z['body_sha256']) for z in results),no_body_results=sum(not z['body_sha256'] for z in results),first_reservation=reservations[0]['reserved_at'],last_result=results[-1]['finished_at'],serial_nonoverlap=True,pending_actions=0,actual_reservation31=False,rejected_next_input=asset(nextinput),rejected_next_log=asset(reject),stale_status_actions=24,command_log_actions=24,hidden_wire_requests_measured=False)
findings=[Finding(finding_id='F01',severity='correction',statement='Ten Chaffee follow-ups ignored the retained HTML base href and therefore attempted different URLs from their observed anchors. A009-A014 andA021-A024 remain failed/misdirected attempts; no source absence inference.',evidence=['REFERRALS in AUDIT.json','received/raw/SHEXT003-A002.html','received/raw/SHEXT003-A004.html']),Finding(finding_id='F02',severity='correction',statement='Unencoded spaces caused curl3 preflight failures. Shared holiday/legal-policy/footer resources exhausted the20-action Chaffee budget before high-value fee/adoption links. Four unopened, properly base-resolved priorities are additive only.',evidence=['CHAFFEE_REPAIR_PROPOSAL.json','received/ACTION_LOG.json']),Finding(finding_id='F03',severity='correction',statement='Full historical metadata has exact requested URL and digest matches for A026 andA027, four records each. The worker sample-based no_exact_url_match strings must not be treated as global absence. A028 exact requested history is reported separately.',evidence=['LEGACY_COMPARISON.json','received/PRIORITIES.json']),Finding(finding_id='F04',severity='qualification',statement='All343 supplied inventory bindings match;346 total delivery files are preserved. Four raw curl logs contain12 Set-Cookie lines; only explicitly redacted public derivatives are copied, with original hashes retained.',evidence=['CUSTODY_RECEIPT.json']),Finding(finding_id='F05',severity='qualification',statement='Actual30 reservations/results close serially with30 distinct URLs,20 Chaffee/10 Gunnison and1,600,233 retained bodybytes. A031 input exists but reservation was refused. final_status.json is stale24-action status; tool_sequence.jsonl records only the first24 command sequences.',evidence=['received/ACTION_LOG.json','received/logs/final_status.json','received/logs/tool_sequence.jsonl',asset(reject).path]),Finding(finding_id='F06',severity='qualification',statement='Supplied curl command logs for first24 use a Chrome-like User-Agent; they are not browser observations. No -k, -L or retry flag appears in those24 recorded commands. Remaining6 lack equivalent command records in tool_sequence. Source transport/times remain supplied claims; hidden network requests unmeasured.',evidence=['received/logs/tool_sequence.jsonl','received/headers/SHEXT003-A026.json']),Finding(finding_id='F07',severity='gap',statement='Gunnison LUR3157 only yielded redirect shells. Retained Location points to Amended-March-5-2026 but that destination was not opened. A029 privacy-policy redirect is not a building code. No actual LUR PDF or Chaffee PDF recovered.',evidence=['received/headers/SHEXT003-A025.json','received/headers/SHEXT003-A029.json','received/headers/SHEXT003-A030.json'])]
a=Audit(assignment_id='SH-EXT-003',prepared_packet_manifest_sha256=sha((P/'FINAL_MANIFEST.json').read_bytes()),actual_dispatch_claim='Parent Atlas reports actual dispatch02:15:13Z, acknowledgement observed02:15:48Z; worker claims start02:15:50Z. Audit verifies files, not the historical UI.',worker_timing_claims_independently_witnessed=False,measured_local_audit_at=now,budget=budget,referrals=referrals,pdfs=pdfs,findings=findings,legal_currentness='not_verified',public_requests_by_audit=0,source_review_scope='first physical page of each of three PDFs; 3 of 23 pages')
write('AUDIT.json',a)
print('BUILT',len(items),len(matches),[(p.action_id,p.historical_exact_request_lines,p.historical_digest_lines) for p in pdfs])
