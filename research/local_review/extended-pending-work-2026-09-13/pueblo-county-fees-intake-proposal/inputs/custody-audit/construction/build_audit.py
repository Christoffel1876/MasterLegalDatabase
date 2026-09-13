from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,unquote
import json,hashlib,sys,subprocess,os
import pymupdf
from bs4 import BeautifulSoup
from pydantic import RootModel
from typing import Any
BASE=Path('/Users/mcoors/Documents/Project Geode');REPO=BASE/'MasterLegalDatabase'
OUT=BASE/'handoffs/run-2026-09-12/extended-run/sherlock-sh-ext-002-independent-audit'
sys.path.insert(0,str(OUT));sys.path.insert(0,str(REPO))
from audit_models import Asset,Event,Referral,LegacyComparison,CurrentIntakeComparison,Finding,Audit,IntakeRecommendation
from geode.schemas.validators import require_official_source_url
from geode.constants import ALL_LAYERS
class RawRecord(RootModel[dict[str,Any]]):pass
def put(name,raw):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():raise ValueError('Refuse overwrite '+str(p))
 if isinstance(raw,str):raw=raw.encode()
 tmp=p.with_name(p.name+'.tmp');tmp.write_bytes(raw);tmp.replace(p)
def ref(name):
 p=OUT/name;raw=p.read_bytes();return Asset(path=str(name),sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
def save_model(name,value):
 raw=value.model_dump_json(indent=2)+'\n';type(value).model_validate_json(raw);put(name,raw)
 put(Path(name).with_suffix('.schema.json'),json.dumps(type(value).model_json_schema(),indent=2)+'\n')
now=datetime.now(timezone.utc)
log=json.loads((OUT/'received/ACTION_LOG.json').read_bytes())
proposal=json.loads((OUT/'parent-audit/DIRECTED_PROPOSAL.json').read_bytes())
activation=json.loads((OUT/'received/ACTIVATION.json').read_bytes())
assert ref('authorization/START_HERE.md').sha256==activation['start_here_sha256']
assert ref('parent-audit/DIRECTED_PROPOSAL.json').sha256==activation['directed_proposal_sha256']
assert ref('parent-audit/FINAL_MANIFEST.json').sha256==activation['audit_manifest_sha256']
events=[]
for r,result,target in zip(log['reservations'],log['results'],proposal['targets']):
 action=r['action_id'];assert r==json.loads((OUT/f'received/reservations/{action}.json').read_bytes());assert result==json.loads((OUT/f'received/results/{action}.json').read_bytes())
 assert r['requested_url']==result['observed_final_url']==target['url']
 header=json.loads((OUT/f'received/headers/{action}.json').read_bytes())
 assert header['requested_url']==target['url']==header['curl_meta']['final_url']
 assert int(header['curl_meta']['http_code'])==result['observed_http_status']
 ext='pdf' if action.endswith('001') else 'html'
 raw=(OUT/f'received/raw/{action}.{ext}').read_bytes();duplicate=(OUT/f'received/raw/{action}.bin').read_bytes();assert raw==duplicate
 assert len(raw)==result['size_bytes']==int(header['curl_meta']['size_download'])
 assert hashlib.sha256(raw).hexdigest()==result['body_sha256']
 if 'content-length' in header['headers']:assert int(header['headers']['content-length'])==len(raw)
 assert not result['visible_redirect_urls']
 page_count=encrypted=repaired=eof=None;title=None
 if ext=='pdf':
  assert raw.startswith(b'%PDF-')
  with pymupdf.open(stream=raw,filetype='pdf') as doc:page_count=doc.page_count;encrypted=bool(doc.is_encrypted);repaired=bool(doc.is_repaired)
  eof=raw.rstrip().endswith(b'%%EOF');assert page_count==2 and not encrypted and not repaired and eof
 else:
  soup=BeautifulSoup(raw,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else None
 private=[k for k in header['headers'] if k.lower() in {'set-cookie','cookie','authorization','proxy-authorization','x-api-key'}]
 assert not private
 notes=['Transport observations are supplied worker records; no original curl command or complete wire transcript is retained.','The .bin and typed-extension files are the same received response bytes, not two downloads.']
 if ext=='html':notes.append('HTTP403 is consistent with retained Just a moment challenge HTML; this is not a successful commissioner catalog or legal source.')
 e=dict(action_id=action,authority_id=r['authority_id'],requested_url=r['requested_url'],reported_final_url=result['observed_final_url'],reported_reserved_at=r['reserved_at'],reported_finished_at=result['finished_at'],reported_http_status=result['observed_http_status'],reported_visible_redirects=result['visible_redirect_urls'],retained_role='received_pdf' if ext=='pdf' else 'received_access_denial_html',body=ref(f'received/raw/{action}.{ext}').model_dump(),byte_identical_duplicate=ref(f'received/raw/{action}.bin').model_dump(),reservation=ref(f'received/reservations/{action}.json').model_dump(),result=ref(f'received/results/{action}.json').model_dump(),headers=ref(f'received/headers/{action}.json').model_dump(),structural_pdf_pages=page_count,pdf_encrypted=encrypted,pdf_repaired=repaired,terminal_pdf_eof_present=eof,html_title=title,observed_header_names=sorted(header['headers']),private_header_names_detected=private,headers_and_result_byte_counts_match=True,notes=notes)
 events.append(Event.model_validate_json(json.dumps(e)))
assert events[0].reported_reserved_at<=events[0].reported_finished_at<=events[1].reported_reserved_at<=events[1].reported_finished_at
assert events[-1].reported_finished_at<datetime(2026,9,13,2,15,tzinfo=timezone.utc)
assert sum(e.body.size_bytes for e in events)==81082
referrals=[]
for target in proposal['targets']:
 name='parent-audit/'+target['parent']['path'];asset=ref(name);assert asset.sha256==target['parent']['sha256'] and asset.size_bytes==target['parent']['size_bytes']
 soup=BeautifulSoup((OUT/name).read_bytes(),'html.parser')
 anchors=[a for a in soup.find_all('a',href=True) if a['href']==target['exact_href'] and ' '.join(a.get_text(' ',strip=True).split())==target['exact_label']]
 assert len(anchors)==1 and urljoin(target['parent_url'],target['exact_href'])==target['url']
 referrals.append(Referral(authority_id='CO-COUNTY-PUEBLO',parent_url=target['parent_url'],parent=asset,parent_role='retained_browser_rendered_dom',parent_title=soup.title.get_text(' ',strip=True),parent_h1=[h.get_text(' ',strip=True) for h in soup.find_all('h1')],exact_href=target['exact_href'],exact_label=target['exact_label'],resolved_url=target['url'],anchor_match_count=1,target_role='fee_schedule_link' if '.pdf' in target['url'] else 'commissioner_catalog_lead',limitations=['A031 was a retained browser-rendered DOM after an earlier source denial, under that earlier assignment. It is not an original HTTP response body.','The county attribution is based on the official parent identity/department/URL chain; no issuer wording or adoption on the PDF face is certified here.']))
urls=[e.requested_url for e in events];digests=[e.body.sha256 for e in events];sid='pueblo-county-planning-fees-sh-ext-002'
commit='2f2b450d8ecb3eff5258598d7be27189bc5e4cff';legacy=[]
for edition in ['pinned_commit','working_tree']:
 proc=None;name='_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'
 if edition=='pinned_commit':
  proc=subprocess.Popen(['git','show',commit+':'+name],cwd=REPO,stdout=subprocess.PIPE);handle=proc.stdout
 else:handle=(REPO/name).open('rb')
 h=hashlib.sha256();size=0;n=0;matched=[];numbers=[];urlmatches=shamatches=decoded=idmatches=0
 for n,line in enumerate(handle,1):
  h.update(line);size+=len(line);r=RawRecord.model_validate_json(line).root
  fields=[r.get(k) for k in ['source_url','requested_url','final_url','url']]
  um=any(u in urls for u in fields if isinstance(u,str));sm=str(r.get('sha256','')).lower() in digests
  dm=any(unquote(u) in {unquote(x) for x in urls} for u in fields if isinstance(u,str));im=r.get('source_id')==sid
  urlmatches+=um;shamatches+=sm;decoded+=dm;idmatches+=im
  if um or sm or dm or im:matched.append(line);numbers.append(n)
 handle.close()
 if proc:assert proc.wait()==0
 relative=f'comparison/{edition}/matching-original-lines.jsonl';put(relative,b''.join(matched))
 legacy.append(LegacyComparison(edition=edition,pinned_commit=commit if proc else None,repository_path=name,full_file_sha256=h.hexdigest(),full_file_bytes=size,full_rows=n,compared_urls=urls,compared_sha256s=digests,exact_url_field_matches=urlmatches,digest_matches=shamatches,decoded_url_matches=decoded,proposed_id_matches=idmatches,matching_original_lines=ref(relative),original_line_numbers=numbers,full_stream_included=False,actual_historical_original_bytes_compared=False,limitations=['Every full JSONL row was parsed before matching. Match fields were source_url,requested_url,final_url,url and sha256; decoded URL comparison only percent-decodes, without hostname equivalence or inferred redirects.','No exact metadata match does not prove global novelty, absence of unrecorded originals, or a legal change. Matching metadata would not establish historical byte availability.','Full streams are not copied; portable audit verification cannot independently reproduce their full-stream hashes without the pinned repository or exact captured input.']))
manual=[]
for name in ['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl']:
 rawlines=[];n=sha_count=url_count=id_count=0
 with (REPO/name).open('rb') as f:
  for n,line in enumerate(f,1):
   r=RawRecord.model_validate_json(line).root;rawlines.append(line)
   sha_count+=r.get('sha256')==events[0].body.sha256;url_count+=r.get('official_source_url')==urls[0];id_count+=r.get('record_id')==sid
 rel='comparison/current-intake/'+Path(name).name;put(rel,b''.join(rawlines))
 manual.append(CurrentIntakeComparison(repository_path=name,file=ref(rel),rows=n,sha256_matches=sha_count,exact_url_matches=url_count,proposed_id_matches=id_count,proposed_source_id=sid,captured_at=now))
assert all(x.full_rows==48390 and x.exact_url_field_matches==x.digest_matches==x.decoded_url_matches==x.proposed_id_matches==0 for x in legacy)
assert all(x.sha256_matches==x.exact_url_matches==x.proposed_id_matches==0 for x in manual)
findings=[
Finding(finding_id='C01',disposition='verified',statement='All25 delivered inventory entries match exact size and SHA. The27-file delivery additionally contains the inventory itself and hash-summary. Two .bin files duplicate the corresponding PDF/error body, leaving two distinct responses.',evidence=['received/ARTIFACT_INVENTORY.json','CUSTODY_RECEIPT.json'],limits=['An internally matching inventory establishes retained byte identity, not authenticity of all acquisition claims.']),
Finding(finding_id='C02',disposition='verified',statement='Both requested URLs exactly match the authorized proposal and retained A031 anchors, including the fee filename percent encoding. A031 title identifies Pueblo County; authority is CO-COUNTY-PUEBLO, separate from City of Pueblo.',evidence=['authorization/START_HERE.md','parent-audit/DIRECTED_PROPOSAL.json','parent-audit/received/raw/SHEXT001-A031.html'],limits=['A031 is a retained browser-rendered DOM, not original HTTP bytes. No adopting instrument is established by its label.']),
Finding(finding_id='C03',disposition='qualified',statement='The two recorded reservations/results are serial, report75214+5868=81082 response bytes, and finish before02:15. Retained complete PDF length matches content-length and supplied curl size. The audit captured all delivery bytes at02:20:59, before the02:25 report deadline.',evidence=['received/ACTION_LOG.json','received/headers/SHEXT002-A001.json','received/logs/collector_state.json','CUSTODY_RECEIPT.json'],limits=['Original source acquisition times, TLS verification, unchanged user agent and reserve-before-public-call execution are reported, not independently proved. Hidden wire requests are unmeasured.']),
Finding(finding_id='C04',disposition='qualified',statement='Commissioner target is a received403 challenge/error body, not a catalog success. No later action or retry is recorded; final collector_state.stop is null while report and result notes declare source-stopped.',evidence=['received/results/SHEXT002-A002.json','received/raw/SHEXT002-A002.html','received/logs/collector_state.json','received/report.md'],limits=['The null stop flag is not an affirmative machine stop receipt; the bounded two-action log and explicit report support only the recorded stop.']),
Finding(finding_id='C05',disposition='verified',statement='Independent full pinned/current48,390-row legacy comparisons found zero exact requested/final/source URL or recorded digest matches for either received response; percent-decoded URL comparison is also zero.',evidence=['comparison/pinned_commit/matching-original-lines.jsonl','comparison/working_tree/matching-original-lines.jsonl','received/derived/historical_comparison.json'],limits=['This strengthens the earlier selected1,415-row no-match only within the full legacy metadata file. It is not global original-byte absence or a legal/version-change finding.']),
Finding(finding_id='C06',disposition='qualified',statement='The worker discloses caption-mediated review of both pages. This audit performs structural PDF/image metadata checks only and makes no fee-table, source-face issuer, signature, date or exhaustive visual-review finding.',evidence=['received/derived/SHEXT002-A001_visual_caption_mediated.json','received/derived/SHEXT002-A001_rasters.json'],limits=['Raster dimensions alone do not independently establish rendered-image provenance without complete settings; separate root/Ptolemy source QA remains separate.']),
Finding(finding_id='C07',disposition='intake_eligible_with_conditions',statement='One received fee PDF is suitable for a guarded preservation-only intake proposal as received_review_package. Current63-row manual manifest and64-row ledger contain no exact fee digest, official URL or proposed source ID match.',evidence=[x.file.path for x in manual],limits=['Actual future receipt time and canonical archive path must be created by the approved intake transaction. No original acquisition time or manual_official_download method should be invented.'])]
custody=json.loads((OUT/'CUSTODY_RECEIPT.json').read_bytes());captured=datetime.fromisoformat(custody['captured_at']);assert captured<datetime(2026,9,13,2,25,tzinfo=timezone.utc)
audit=Audit(assignment_id='SH-EXT-002',status='custody_verified_with_qualifications_pending_intake',audited_at=now,delivery_captured_at=captured,authorization=ref('authorization/START_HERE.md'),directed_proposal=ref('parent-audit/DIRECTED_PROPOSAL.json'),parent_manifest=ref('parent-audit/FINAL_MANIFEST.json'),events=events,referrals=referrals,legacy=legacy,current_intake=manual,findings=findings,inventory_listed_files=25,inventory_claims_verified=True,actual_delivery_files=27,unlisted_delivery_files=custody['unlisted_delivery_files'],independent_distinct_response_bodies=2,retained_response_body_bytes=81082,declared_actions=2,declared_distinct_urls=2,declared_visible_redirects=0,recorded_serial_order_consistent=True,reported_research_completed_before_cutoff=True,delivery_bytes_captured_before_report_cutoff=True,hidden_network_requests_measured=False,transport_command_retained=False,independent_source_visual_pages=0,legal_currentness='not_verified',answer_safe=False,public_requests_by_auditor=0,canonical_intakes_by_auditor=0)
save_model('AUDIT.json',audit)
assert require_official_source_url(urls[0])==urls[0] and '08_County_Authorities' in ALL_LAYERS
recommendation=IntakeRecommendation(status='proposed_not_applied',source_id=sid,authority_id='CO-COUNTY-PUEBLO',layer_id='08_County_Authorities',incoming_source=events[0].body,original_filename='SHEXT002-A001.pdf',official_source_url=urls[0],official_source_name='Pueblo County planning fee schedule; official parent label: Fee Schedule Adopted 5.8.25 - Revised (2).pdf',acquisition_method='received_review_package',actual_future_received_at=None,archive_path=None,original_acquisition_time=None,reported_acquisition_interval=[str(events[0].reported_reserved_at),str(events[0].reported_finished_at)],required_final_status='archived_pending_pipeline',expected_canonical_pdf_count=1,legal_currentness='not_verified',prerequisites=['Root reviews this independent custody audit and the separately owned complete source QA.','A separately reviewed transaction checks exact current raw/ledger prefixes and duplicate source IDs/hashes immediately before any write.','Use actual eventual repository receipt time. Preserve reported curl times as supplied claims, not verified acquisition timestamps.','Use the existing typed manual-record received_review_package pattern and validation/reconciliation; the generic ManualSourceIntakeRequest CLI enum does not admit that method. Do not change the enum or relabel the method to fit it.','Keep original_filename equal to the actual incoming basename; copy exact bytes write-once and preserve atomic manifest/ledger snapshots.'],exclusions=['Do not intake the403 HTML, either duplicate.bin file, derived text, rasters, or parent DOM as a second canonical fee original.','No adoption or effective date is proved by the filename5.8.25 or Last-Modified header.','No legal-currentness, answer-safe, complete-county or monitoring promotion.'])
save_model('INTAKE_RECOMMENDATION.json',recommendation)
print(json.dumps({'audit_sha':ref('AUDIT.json').sha256,'legacy':[(x.edition,x.full_rows,x.full_file_sha256,x.digest_matches,x.exact_url_field_matches) for x in legacy],'intake':[(x.rows,x.sha256_matches,x.exact_url_matches,x.proposed_id_matches) for x in manual],'source_id':sid},indent=2))
