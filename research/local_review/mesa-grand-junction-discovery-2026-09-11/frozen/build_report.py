"""Build the finite report from retained evidence, without public requests."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from audit_models import Report, Priority, Basis, Legacy, Cell, VisualScope, Summary, Strict
from capture import save, Event
from pydantic import Field

B=Path(__file__).resolve().parent
R=B.parents[2]/'MasterLegalDatabase'
TASK='atlas-mesa-grand-junction-discovery-2026-09-11'
def read(path: Path) -> dict:
    """Read one bounded JSON artifact."""
    return json.loads(path.read_text(encoding='utf-8'))
def rows(x: object):
    """Yield registry records recursively without inventing missing IDs."""
    if isinstance(x,dict):
        if 'source_id' in x: yield x
        for v in x.values(): yield from rows(v)
    elif isinstance(x,list):
        for v in x: yield from rows(v)
events={p.parent.name:Event.model_validate_json(p.read_text())
        for p in sorted((B/'events').glob('*/event.json'))}
registry=[]
for name in ['LOCAL_SOURCE_REGISTRY.json','MUNICIPAL_SOURCE_REGISTRY.json']:
    registry.extend(read(B/'inputs'/f'{name}.relevant.json')['rows'])
registry=list(rows(registry))
P=[]
def priority(i: int, auth: str, cats: list[str], title: str, url: str, role: str,
             status: str, eid: str | None, parent: str, label: str,
             notes: list[str], gaps: list[str], redirect: str | None=None) -> None:
    """Assemble a single-resource lead from a retained exact anchor."""
    rids=sorted({x['source_id'] for x in registry if x.get('url')==url})
    P.append(dict(priority_id=f'ATLAS-MG-{i:02d}',authority_id=auth,categories=cats,
        title=title,url=url,role=role,acquisition_status=status,source_event_id=eid,
        unfollowed_redirect_url=redirect,basis=[Basis(event_id=parent,
            input_source_ids=rids,label=label,
            note='Exact anchor preserved in this event HTML; no inference of legal currency.').model_dump()],
        existing_registry_source_ids=rids,date_and_scope_notes=notes,gaps=gaps))
def anchor(eid: str, label: str) -> str:
    """Select one observed exact label, failing on ambiguous matching URLs."""
    links=read(B/'events'/eid/'parsed.json')['links']
    urls={x['url'] for x in links if x['label']==label}
    if len(urls)!=1: raise ValueError((eid,label,urls))
    return urls.pop()
M='CO-COUNTY-MESA';G='CO-MUNICIPAL-GRAND_JUNCTION'
priority(1,M,['land_use_zoning'],'Mesa County 2020 Land Development Code, amended April 23, 2024',
 events['E012'].requested_url,'consolidated_code_text_edition_identified',
 'source_preserved','E012','E006','Land Development Code - 2020 (Amended 04-23-24, PDF)',
 ['219 physical PDF pages; cover and first two contents pages visually checked.',
  'Cover states January 14, 2020 and six amendment dates ending April 23, 2024.',
  'Catalog labels this code Current while separately listing proposed 2026 revisions.',
  'E002 explicitly describes these land-use rules as governing unincorporated Mesa County.'],
 ['Later adopted instruments and maps were not reconciled; 219 pages does not certify completeness.',
  'Native bytes preserved for every page; substantive text, tables and cross-references not fully reviewed.'])
priority(2,M,['fees'],'Mesa County Planning Fees page',
 anchor('E010','Fees'),'fee_catalog_or_schedule_unopened','linked_unopened',None,'E010','Fees',
 ['Only the official referring Applications and Fees page was opened.',
  'No fee amounts, schedule edition, adoption authority or effectiveness were verified.'],
 ['Open the exact Fees link and preserve each adopted schedule and amendment; target cap reached.'])
label=next(x['label'] for x in read(B/'events/E013/parsed.json')['links']
           if x['label'].startswith('Building Department Performs'))
priority(3,M,['building_fire'],'Mesa County Building Department',
 anchor('E013',label),'building_department_catalog_unopened','linked_unopened',None,'E013',label,
 ['Official parent says the department serves Mesa County, De Beque, Collbran, Palisade and Grand Junction.',
  'Shared administration does not transfer city ordinance ownership to the county.'],
 ['County adoption resolutions, amendments, adopted editions, fire-district boundaries and fees uncollected.'])
label='PRO2026-0092 Mesa County 2020 Land Development Code - Hearings Planning Commission October 15, 2026 and Board of Commissioners November 17, 2026'
priority(4,M,['adopted_changes'],label,anchor('E006',label),'future_hearing_notice_unopened',
 'linked_unopened',None,'E006',label,
 ['E006 heading: Hearing Dates - Revision 09-03-26.',
  'October 15 and November 17, 2026 are announced hearing dates, not adoption/effective dates.',
  'July 24, 2026 draft and additions/deletions PDFs are separately linked under Updates.'],
 ['Notice PDF unopened; proposal text, hearing occurrence, final action and subsequent instruments unverified.'])
priority(5,G,['land_use_zoning'],'Grand Junction municipal code publisher entry',
 anchor('E009','Municipal Code'),'authorized_publisher_code_entry_unopened','linked_unopened',
 None,'E009','Municipal Code',
 ['Exact official city HTML referral identifies ecode360.com/GR4464.',
  'Existing registry zoning ID municipal_grand_junction_zoning points to https://ecode360.com/45346067; that specific title URL was not freshly opened.',
  'Registry pre-2023 zoning PDF remains historical and was not substituted for current code.'],
 ['Publisher text, Title 21 scope, supplement cutoff and post-cutoff amendments not collected or reconciled.'])
priority(6,G,['building_fire'],'Grand Junction Ordinance 5269: 2024 IFC adoption and amendments',
 events['E007'].requested_url,'adoption_and_local_amendment_instrument_as_stated',
 'source_preserved','E007','E004','City Ordinance Number 5269 (PDF)',
 ['29 physical pages; full pages 1, 28 and 29 visually checked, not all amendment provisions.',
  'Page1 adopts specified 2024 IFC appendices with exceptions/amendments to GJMC15.44; controlling within city limits as stated.',
  'Page28 states introduction June18,2025 and second reading July16,2025; visible signature marks and seal, identities not authenticated.',
  'Page29 states publication June21 and July19,2025, certification July21,2025, and Effective: August18,2025.',
  'The source title and operative clauses are adoption evidence despite proposed wording retained in an earlier recital.'],
 ['Later amendments/current law not reconciled; building Ordinance5268 only recorded in registry and unopened.',
  'City fire service page also discusses Grand Junction Rural Fire Protection District; do not assign the city ordinance to that separate district.'])
priority(7,G,['fees'],'Grand Junction Fire Prevention Service Fees',
 events['E008'].requested_url,'fire_prevention_fee_schedule','source_preserved','E008',
 'E004','Fire Prevention Bureau Fees (PDF)',
 ['Both physical pages viewed; schedule has new-building, tenant-finish, fire-alarm, sprinkler and miscellaneous fee groups.',
  'No printed edition, adoption date or effective date was observed on either page; PDF metadata dates are not legal dates.',
  'Native extraction puts group headers after fee rows; exact row-to-group table transcription is still pending.',
  'The same catalog also links a different older Fees endpoint (DocumentCenter/View/563), unopened and unreconciled.'],
 ['Not a complete city development fee schedule; planning, impact and other fees were not collected.',
  'Adopting authority, later revisions, district application and all numeric associations require review.'])
label=next(x['label'] for x in read(B/'events/E009/parsed.json')['links']
           if x['label'].startswith('Ordinance No. 5340'))
priority(8,G,['adopted_changes','land_use_zoning'],'Grand Junction Ordinance 5340: significant-tree preservation amendments',
 events['E011'].requested_url,'adopted_instrument_catalog_assertion_only','redirect_only','E011',
 'E009',label,
 ['Official E009 catalog places this instrument under Ordinances Adopted in the Last 30 Days.',
  'Catalog describes amendments to Sections21.07.040 and21.09.060(a)(1); no exact passage/date verified in PDF.',
  'Requested document URL returned301; destination recorded but not followed because the12-target cap was reached.'],
 ['Actual instrument bytes, signatures, adoption/effective dates and code integration remain unverified.'],
 'https://www.gjcity.org/DocumentCenter/View/18335/Ordinance-No-5340?bidId=')
# Full historical manifest comparison is streamed, including records outside the two selected authorities.
legacy_path=R/'_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'
comparisons={p['priority_id']:{'requested':[],'parent':[],'equal':[]} for p in P}
h=hashlib.sha256(); line_count=0
with legacy_path.open('rb') as stream:
 for line in stream:
  h.update(line);line_count+=1;row=json.loads(line)
  for p in P:
   c=comparisons[p['priority_id']]
   if row.get('requested_url')==p['url']: c['requested'].append(row)
   if row.get('source_url')==p['url']: c['parent'].append(row)
   e=events.get(p['source_event_id']);digest=e.body_sha256 if e and e.http_status==200 else None
   if digest and row.get('sha256')==digest: c['equal'].append(row)
for p in P:
 c=comparisons[p['priority_id']]
 p['legacy']=Legacy(requested_url_matches=len(c['requested']),
    parent_source_url_matches=len(c['parent']),
    requested_match_source_ids=sorted({x['source_id'] for x in c['requested']}),
    parent_match_source_ids=sorted({x['source_id'] for x in c['parent']}),
    known_digests_at_requested_url=sorted({x['sha256'] for x in c['requested'] if x.get('sha256')}),
    preserved_digest_equal_records=len(c['equal']),
    preserved_digest_equal_source_ids=sorted({x['source_id'] for x in c['equal']}),
    interpretation='Exact historical URL/hash comparison only; repeated attempts and aliases are not extra documents. No match does not prove new legal content.').model_dump()
class Compare(Strict):
    input_sha256:str; input_lines:int; generated_at:datetime; priorities:list[Priority]
    manual_manifest_path:str; manual_manifest_sha256:str; manual_manifest_rows:int
    manual_pdf_digest_matches:dict[str,int]
manual=R/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl';mh=hashlib.sha256();n=0
manual_matches={e:0 for e in ['E007','E008','E012']}
with manual.open('rb') as stream:
 for line in stream:
  mh.update(line);n+=1;row=json.loads(line)
  for e in manual_matches:
   if events[e].body_sha256 in row.values():manual_matches[e]+=1
save(B/'LEGACY_COMPARISON.json',Compare(input_sha256=h.hexdigest(),input_lines=line_count,
 generated_at=datetime.now(timezone.utc),priorities=[Priority.model_validate(p) for p in P],
 manual_manifest_path=str(manual.relative_to(R)),manual_manifest_sha256=mh.hexdigest(),
 manual_manifest_rows=n,manual_pdf_digest_matches=manual_matches))
checklist=[]
def cell(a: str,c: str,ids: list[int],es: list[str],status: str,gap: str) -> None:
    """Add one of the eight explicitly scoped discovery cells."""
    checklist.append(Cell(authority_id=a,category=c,priority_ids=[f'ATLAS-MG-{i:02d}' for i in ids],
                          supporting_event_ids=es,status=status,gap=gap))
cell(M,'land_use_zoning',[1],['E002','E006'],'preserved_partial','219-page identified edition preserved; subsequent adoption chain and maps not reconciled.')
cell(M,'building_fire',[3],['E013'],'catalog_and_leads_only','Shared county/city administration identified; actual county adoption/amendment/fire instruments uncollected.')
cell(M,'fees',[2],['E010'],'catalog_and_leads_only','Fee endpoint found but unopened; application guidance is not an adopted fee schedule.')
cell(M,'adopted_changes',[4],['E006'],'catalog_and_leads_only','Future hearing and proposed-draft leads only; no 2026 final county adoption verified.')
cell(G,'land_use_zoning',[5,8],['E009'],'catalog_and_leads_only','Authorized code entry unopened; recent tree amendment PDF remains redirect-only.')
cell(G,'building_fire',[6],['E004','E005'],'preserved_partial','City fire adoption preserved; building ordinance, subsequent amendments and rural district instruments unreconciled.')
cell(G,'fees',[7],['E004'],'preserved_partial','Two-page fire fee schedule preserved; edition, adoption, alternate linked fee PDF and broader development fees unresolved.')
cell(G,'adopted_changes',[8,6],['E009'],'preserved_partial','5269 source adoption dates inspected;5340 catalog-stage assertion only; rolling30-day catalog is not full history.')
scopes=[]
for e,pgs,scope,obs in [
 ('E007',[1,28,29],'Title, jurisdiction/adoption clauses and concluding adoption/certification dates only; 26 remaining pages not visually reviewed.',
  ['2024 IFC adoption and city amendments, not model-code reproduction or county ordinance.',
   'Introduction2025-06-18; second reading2025-07-16; published2025-06-21 and2025-07-19; certification2025-07-21; stated effective2025-08-18.',
   'Visible signature marks and seal; no signature identity or authenticity claim.']),
 ('E008',[1,2],'Both full pages viewed for schedule identity, groups, date absence and extraction ordering; no full numeric transcription certification.',
  ['Fire Prevention Service Fees and Continued headings; grouped fee table, including plan reviews and miscellaneous permits.',
   'Group headers occur after numeric rows in native extraction; table geometry must be retained in any later transcription.',
   'No printed edition/adoption/effective date observed; PDF metadata timestamp is not an adoption date.']),
 ('E012',[1,2,3],'Cover and first two contents pages only; 216 remaining pages not visually reviewed.',
  ['Cover identifies2020 code, January14,2020, amendments through April23,2024.',
   'Visible contents include zoning/development procedures, districts, use regulations and development standards.',
   '219 structural pages and complete native extraction do not certify legal or textual completeness.'])]:
 st=read(B/'pdf-inspection'/e/'STRUCTURE.json')
 scopes.append(VisualScope(event_id=e,source_pages=st['pages'],full_pages_viewed=pgs,
   render_paths=[f'pdf-inspection/{e}/view-{p:04d}.png' for p in pgs],scope=scope,observations=obs))
s=Summary(public_events=len(events),distinct_requested_urls=len({e.requested_url for e in events.values()}),
 http_200=sum(e.http_status==200 for e in events.values()),http_301=sum(e.http_status==301 for e in events.values()),
 transport_failures=sum(e.http_status is None for e in events.values()),
 response_body_bytes=sum(e.body_bytes for e in events.values()),
 accepted_200_bytes=sum(e.body_bytes for e in events.values() if e.http_status==200),
 pdf_count=3,pdf_structural_pages=sum(x.source_pages for x in scopes),
 full_pages_visually_checked=sum(len(x.full_pages_viewed) for x in scopes),priority_count=len(P),checklist_rows=8)
report=Report(task_id=TASK,prepared_at=datetime.now(timezone.utc),
 stop_at=max(e.completed_at for e in events.values()),input_commit=read(B/'INPUTS.json')['commit'],
 initial_observed_commit='69a33703a9fecb5119816ae02d4ba32d40753a55',
 input_commit_note='HEAD advanced during parallel root work. All four input hashes were checked against f160dec2792a2efbcbfee8d37fd3c72477e83cb1 and matched. Neither branch nor files were changed by this task.',
 scope='Atlas-only finite discovery: Mesa County and City of Grand Junction, four categories each. No Sherlock assignment, external contact, source promotion or repository modification.',
 summary=s,priorities=P,checklist=checklist,pdf_review=scopes,
 findings=[
  'Both authority snapshots have12 missing recovery-ledger cells, not_assessed completeness and not_verified currentness; dated2025 Census identity evidence is not current operating-status certification.',
  'Pinned registries contain21 Mesa source IDs and9 Grand Junction source IDs. Historical manifest has724 Mesa records/21 IDs/67 requested URLs and10 city records/8 IDs/9 requested URLs; repeated attempts and category aliases do not measure collection completeness.',
  'Mesa county-municipal ownership must remain separate: its Building Department describes services for Grand Junction and three towns; county land-use catalog expressly addresses unincorporated areas.',
  'Grand Junction fire webpage includes services for its Rural Fire Protection District. This does not independently adopt the city ordinance for that district.',
  'Mesa catalog identifies a2024-amended code separately from2026 proposed revisions and future hearings; July24 draft revision and September3 hearing-date revision are not enactment dates.',
  'Grand Junction ordinance catalog mixes proposed measures and last30days adoptions; only its explicit subsection label supports the5340 adoption-stage assertion.',
  'City development guidance warns forms referencing2018 IFC are being updated; do not infer all linked guidance reflects the2024 adoption.',
  'Fresh Mesa LDC digest equals41 historical manifest records across aliases. HTML digest differences alone do not establish changes in law.',
  'No public searches, browser sessions, hidden APIs, authentication, spoofing or automatic retries/redirects were used. E001 was a DNS transport failure; E002 was one exact ordinary-TLS retry. All remaining attempts are explicit logged requests.'],
 explicit_unopened_gaps=[
  'Mesa Fees and Building Department links (priorities02/03) were discovered but never requested.',
  'Mesa hearing notice and both proposed revision PDFs were linked, not downloaded; hearing outcomes not checked.',
  'Grand Junction eCode360 entry and registered Title21 URL were not requested; official referral only.',
  'Grand Junction5340 explicit redirect destination was recorded but not followed; body retained is redirect HTML, not the ordinance PDF.',
  'Grand Junction Ordinance5268 building adoption PDF is a recorded registry lead, not collected here.',
  'Alternate Grand Junction fee endpoint /DocumentCenter/View/563/Fire-Prevention-Bureau-Fees-PDF is linked but unopened; do not assume equal fees.',
  'Stage1 fire-restrictions banner was observed on county pages; no sheriff instrument or authority/jurisdiction reconciliation was performed.'],
 limitations=[
  'Public collection stopped at12 distinct targets and13 events before20:25UTC; no follow-on work authorized by this package.',
  'Three PDFs have genuine HTTP200 response bytes; only8 of250 physical pages were visually reviewed. Native extraction is preserved for all250, without full transcription/currentness certification.',
  'No source was added to raw archive, manual ledger, registry or recovery coverage. No Git mutation or bot dispatch occurred.',
  'Six city response-header files contain server Set-Cookie fields. They remain local custody; any distributable copy must use separately hashed redacted derivatives while retaining original hashes.',
  'Absent historical/manual matches mean only no match in the compared files. Missing raw evidence, repeated histories and later amendments remain unresolved.',
  'This report is discovery and preservation evidence, not legal advice, an exhaustive source inventory or a current-law certification.'])
save(B/'REPORT.json',report)
for cls,name in [(Report,'REPORT.schema.json'),(Compare,'LEGACY_COMPARISON.schema.json')]:
 path=B/name;path.write_text(json.dumps(cls.model_json_schema(),indent=2)+'\n',encoding='utf-8')
print(report.model_dump_json(indent=2))
