"""Build a finite evidence audit from existing response bytes only; no network."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess
import pymupdf
from audit_models import *
from capture import Event, save
B=Path(__file__).resolve().parent
R=B.parents[2]/'MasterLegalDatabase'
SEED=B.parent/'mesa-grand-junction-discovery-2026-09-11'
TASK='atlas-mesa-grand-junction-directed-gaps-2026-09-11'
def h(v):return hashlib.sha256(v).hexdigest()
def f(p):
    b=p.read_bytes();return File(path=p.relative_to(B).as_posix(),sha256=h(b),bytes=len(b))
def copy_new(src,dst):
    b=src.read_bytes()
    if dst.exists():
        if dst.read_bytes()!=b:raise ValueError('input changed')
    else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    return f(dst)
for eid in ['E009','E010','E011','E013']:
    for name in ['event.json','parsed.json','body.bin','curl-metadata.json']:
        src=SEED/'events'/eid/name
        if src.exists():copy_new(src,B/'inputs'/f'{eid}-{name}')
E={p.parent.name:Event.model_validate_json(p.read_text()) for p in sorted((B/'events').glob('*/event.json'))}
# Freeze the contemporaneous small raw-manifest comparison; never change its original.
manual=R/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
mf=copy_new(manual,B/'inputs/manual-source-intake-manifest.jsonl')
manual_rows=[json.loads(x) for x in (B/mf.path).read_text().splitlines()]
legacy_path=R/'_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'
legacy_bytes=legacy_path.stat().st_size
legacy_hash=hashlib.sha256(); matches=[];counts={e:{'exact_requested_url':0,'parent_source_url':0,'equal_digest':0} for e in E}
cache={}
with legacy_path.open('rb') as stream:
    for n,line in enumerate(stream,1):
        legacy_hash.update(line);row=json.loads(line); why=[]
        for eid,e in E.items():
            for mode,yes in [('exact_requested_url',row.get('requested_url')==e.requested_url),('parent_source_url',row.get('source_url')==e.requested_url),('equal_digest',row.get('sha256')==e.body_sha256)]:
                if yes:counts[eid][mode]+=1;why.append(f'{eid}:{mode}')
        if not why:continue
        raw=row.get('raw_path');ref=None;availability='no repository-local archive reference';actual=None
        if raw and '_RAW_ARCHIVE/' in raw.replace('\\','/'):
            ref='_RAW_ARCHIVE/'+raw.replace('\\','/').split('_RAW_ARCHIVE/',1)[1]
            if ref not in cache:
                p=R/ref
                if '..' in Path(ref).parts or p.is_symlink():res=('unsafe reference not opened',None)
                elif not p.is_file():res=('missing from current checkout',None)
                else:
                    b=p.read_bytes()
                    if b.startswith(b'version https://git-lfs.github.com/spec/v1\n'):res=('Git LFS pointer, not original bytes',h(b))
                    else:res=('ordinary local bytes verified',h(b))
                cache[ref]=res
            availability,actual=cache[ref]
        matches.append(HistoricalRow(line=n,line_sha256=h(line),line_utf8=line.decode(),row=row,matches=why,archive_reference=ref,local_availability=availability,local_recomputed_sha256=actual))
commit=json.loads((B/'inputs/INPUTS.json').read_text())['commit']
pinned=subprocess.run(['git','-C',str(R),'show',f'{commit}:_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'],capture_output=True,check=True).stdout
legacy=Legacy(input_file=File(path='_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl',sha256=legacy_hash.hexdigest(),bytes=legacy_bytes),compared_commit=commit,commit_hash_matched=h(pinned)==legacy_hash.hexdigest(),total_lines=n,matched_rows=matches,counts_by_event=counts,manual_snapshot=mf,manual_rows=len(manual_rows),manual_digest_matches={eid:sum(e.body_sha256 in row.values() for row in manual_rows) for eid,e in E.items()},note='Exact URL histories and recorded digest matches are separate. A historical manifest digest match is not historical-byte equality unless the corresponding ordinary local file was independently rehashed. Referenced old full manifest is not copied; exact matched original lines and its measured hash are retained. No global corpus novelty, law change, freshness or completeness is established.')
viewed={'E003':[1,4,5],'E004':[1,2],'E007':[1,3,5]}
roles={'E003':'City ordinance and certification as stated, with explicit future effective date; redlines retained','E004':'County planning fee exhibit labeled 2017 & 2018; historical schedule linked by current page','E007':'County Building Department Exhibit A fee schedule; catalog labels adopted, adopting instrument not included'}
limits={'E003':['Source states first reading 2026-08-05, adoption/second reading 2026-09-02, certification 2026-09-08, publications 2026-08-08 and 2026-09-05, effective 2026-10-05.','The stated effective date is after receipt; no current operative-law or subsequent-amendment determination.'], 'E004':['PDF heading states 2017 & 2018, whereas referring page states suspension effective 2017 to present and labels a 2017–2019 table.','School-dedication expiration: PDF page2 states 1 October 2020; HTML states 1 October 2022. No resolution or extension was acquired.'], 'E007':['URL filename includes 2024 and directory includes 2026-04; neither establishes legal adoption or effect.','No adoption/effective date observed on selected pages1,3,5. PDF references 2003 IBC valuation data with a limited-values-only qualification on page5.']}
pdfs=[]
for eid in viewed:
    p=pymupdf.open(B/E[eid].body_path);d=B/'pdf-review'/eid;np=[]
    for i,page in enumerate(p,1):
        out=d/f'native-{i:04d}.txt';out.write_bytes(page.get_text('text',flags=pymupdf.TEXTFLAGS_TEXT,sort=False).encode())
        image=d/f'page-{i:04d}.png'
        limit=None
        if eid=='E003' and i==2:limit='Native text empty; page not visually reviewed. This is an extraction gap, not a blank-page claim.'
        if eid=='E003' and i==3:limit='Native text appears corrupted/linearized; page not visually reviewed. No substantive text reliance.'
        if i not in viewed[eid] and limit is None:limit='Not visually reviewed; native bytes and any render are preservation only.'
        np.append(NativePage(page=i,native=f(out),image=f(image) if image.exists() else None,visually_viewed=i in viewed[eid],limitation=limit))
    pdfs.append(PDF(event_id=eid,source=f(B/E[eid].body_path),pages=len(p),repaired=p.is_repaired,encrypted=p.is_encrypted,engine='PyMuPDF',version=pymupdf.VersionBind,flags=pymupdf.TEXTFLAGS_TEXT,metadata=p.metadata,native_pages=np,role=roles[eid],date_limits=limits[eid]))
# Bind exact UTF8 source slices, keeping graphical observations separate from native text.
obs=[]
def add(eid,page,topic,statement,start,end=None):
    if page:
        path=B/f'pdf-review/{eid}/native-{page:04d}.txt';s=path.read_text()
    else:
        path=B/f'events/{eid}/parsed-text.txt';parsed=json.loads((B/f'events/{eid}/parsed.json').read_text());s=parsed['text']
        if not path.exists():path.write_text(s)
    begin=s.index(start);finish=s.index(end,begin)+len(end) if end else begin+len(start)
    excerpt=s[begin:finish];byte_start=len(s[:begin].encode());blob=excerpt.encode()
    obs.append(Observation(id=f'MGD-{len(obs)+1:02d}',event_id=eid,physical_page=page,topic=topic,statement=statement,evidence=[Slice(file=f(path),start=byte_start,end=byte_start+len(blob),excerpt=excerpt,excerpt_sha256=h(blob))],scope='selected_source_region' if page else 'official_html_statement'))
add('E001',None,'planning_catalog_temporal_scope','Official HTML states planning application fees suspended effective 2017 to present, retaining other-fee qualification; this is a webpage statement, not an acquired adopting instrument.','Mesa County planning application fees','(*other fees may remain in effect).')
add('E001',None,'planning_catalog_expiration','HTML states school-dedication resolution expiration 1 October 2022. It differs from linked PDF page2 (2020); neither date is silently corrected.','School Land Dedication resolution expires','School Districts.')
add('E002',None,'shared_administration','County department describes services in the county, De Beque, Collbran, Palisade and Grand Junction. This does not assign municipal ordinances to the county or establish district application.','Our department performs inspections','City of Grand Junction.')
add('E005',None,'unavailable_adopting_instrument','The official page says county ordinance adopting and amending building codes cannot be posted, citing HB21-1110. No contact was made; underlying ordinance/amendments remain uncollected.','In compliance with HB21-1110','970-244-1631')
add('E005',None,'future_code_statement','The webpage states 2026 NEC and 2024 Colorado Plumbing and Fuel Gas Code will be effective January 1, 2027; this is future source-stated timing, not independently verified adoption.','The 2026 NEC','January 1,2027.')
add('E004',1,'planning_pdf_edition','Visible heading identifies Exhibit A and 2017 & 2018 suspension with other-fee qualification; yellow marking highlights the 2017–18 fee column. No current schedule certification.','Mesa County Planning','2017 & 2018 \n \nTYPE OF APPLICATION')
add('E004',1,'planning_appeal_exception','Historical exhibit lists appeals at 275.00 in both fee columns, with a refund if the Board of County Commissioners upholds the appeal. Other rows showing zero are not a blanket statement that all development charges are waived.','Appeals of Administrative Decisions','fee will be refunded to appellant.')
add('E004',2,'planning_pdf_expiration','Visible page2 says school-dedication resolution expires 1 October 2020. Listed district names identify recipients/categories in this county schedule, not acquired district legal instruments.','School Land Dedication resolution expires','Districts.')
add('E004',2,'planning_extraordinary_costs','Visible page2 preserves applicant responsibility for extraordinary development-processing costs and a separate 2017 & 2018 continuing-fees section. Amounts are historical source evidence only.','Payment of all extraordinary costs','THE FOLLOWING FEES WILL CONTINUE TO BE COLLECTED IN 2017 & 2018')
add('E007',1,'building_fee_discretion','Selected fee table states commercial review maximum50%, residential review maximum15% with department discretion, residential submittal maximum$250 non-refundable and credited on issuance, and additional departmental third-party review maximum20%. Conditions and private reviewer costs remain in source; this is not a complete fee transcription.','Plan Review Fees in addition to','Maximum 20% of the Value of \nthe Calculated Permit Fee as \ndetermined to be appropriate \nby the Building Department')
add('E007',3,'building_fee_source_anomalies','Visible Table2 requires rounding fees up to the next dollar. Preserve the source printed $500,00.01 lower bound and the note word coast; no arithmetic repair or correction to $500,000.01 is made.','“Total Valuation” is the actual coast','The Total Valuation for remodels is the actual labor and material cost of the project.')
add('E007',5,'limited_2003_valuation_reference','Page5 note6 restricts 2003 IBC reference to listed valuation values; definitions/other requirements use the version adopted by the department. Do not mistake this schedule for adoption of the entire2003 IBC.','The values in this table are from','Department.')
add('E003',1,'city_ordinance_scope','Visible title identifies City of Grand Junction Ordinance5340, amending Title21 concerning significant-tree preservation. It is city evidence; the displayed strike/underline convention requires separate graphical review of amendments.','CITY OF GRAND JUNCTION','PRESERVATION OF SIGNIFICANT TREES')
add('E003',4,'city_redline_and_adoption','Page4 visibly strikes §21.07.100 heading and (g) text, and the mature trees words in §21.09.060(a)(1). Unstruck surrounding conditions remain. Page4 states first reading August5 and second-reading adoption September2,2026. Signature marks, printed labels and seal are visible; no identity/authenticity determination.','INTRODUCED','pamphlet form.\nATTEST:')
add('E003',5,'city_certification_dates','Page5 states certification September8,2026; publication August8 and September5; effective October5,2026. The latter is after this September11 receipt. Do not treat source adoption and effectiveness as the same date. Signature mark is not authenticated.','IN WITNESS WHEREOF','Effective: October 5, 2026')
basis=[]
for eid,parent,label in [('E001','inputs/E010-parsed.json','Fees'),('E002','inputs/E013-parsed.json',None),('E004','events/E001/parsed.json','Application Fees Schedule (2017 & 2018)'),('E005','events/E002/parsed.json','Adopted Codes and Regulations'),('E006','events/E002/parsed.json','Permit and Plan Review Fees'),('E007','events/E006/parsed.json','Adopted Fee Schedule (PDF)')]:
    links=json.loads((B/parent).read_text())['links'];ls=[x for x in links if x['url']==E[eid].requested_url and (label is None or x['label']==label)]
    if not ls:raise ValueError(f'missing observed link {eid}')
    basis.append(LinkBasis(event_id=eid,source_file=parent,source_kind='parsed_anchor',exact_url=E[eid].requested_url,exact_label=ls[0]['label']))
basis.append(LinkBasis(event_id='E003',source_file='inputs/E011-curl-metadata.json',source_kind='curl_redirect',exact_url=E['E003'].requested_url,exact_label=None))
sensitive=[str(p.relative_to(B)) for p in (B/'events').glob('*/headers.txt') if any(x.lower().startswith((b'set-cookie:',b'authorization:',b'proxy-authorization:')) for x in p.read_bytes().splitlines())]
a=Audit(task_id=TASK,prepared_at=datetime.now(timezone.utc),public_stop_at=max(e.completed_at for e in E.values()),public_event_count=len(E),distinct_requested_urls=len({e.requested_url for e in E.values()}),response_bytes=sum(e.body_bytes for e in E.values()),acquired_pdf_bytes=sum(p.source.bytes for p in pdfs),source_ownership={eid:'CO-MUNICIPAL-GRAND_JUNCTION' if eid=='E003' else 'CO-COUNTY-MESA' for eid in E},basis=basis,pdfs=pdfs,observations=obs,legacy=legacy,unopened=['Mesa county adopting/amending building ordinance: official page states unavailable; no phone/email contact attempted.','Exact model-code provider/state rule links and wiring/foundation guidance in E005 parsed.json remain unopened; not silently adopted or assigned to municipalities.','Mesa supplemental fee resolutions, school-dedication extensions and later fee schedules remain uncollected.','GJ5340 physical pages2–3 were not visually reviewed and have deficient native text; complete graphical/redline extraction and later amendment chain remain unverified.','GJ code publisher consolidation and fire-fee work are outside this task; no overlapping public requests.'],limitations=['Seven explicit user-visible curl invocations, seven distinct URLs, all HTTP200. No automatic retry/redirect, bypass, auth or hidden route. Any DNS/TLS internals are not extra separately observed public events.','All HTTP response bodies and headers preserved exactly. Local headers may contain a Set-Cookie value; listed sensitive headers require explicit derivative redaction before distribution.','13 structural PDF pages preserved; only8 full pages visually inspected: E0031/4/5, E0041/2, E0071/3/5. Three additional saved renders are not claimed viewed.','No full transcription, complete numeric verification, legal/currentness/coverage promotion, canonical intake, repository change, bot message or scheduler action.','Historical HTML digest changes are not evidence of changes in law. Uploaded path dates, PDF metadata and receipt times are not enactment dates.'],distribution_header_sensitive_paths=sensitive)
save(B/'ACCESS_AUDIT.json',a)
(B/'ACCESS_AUDIT.schema.json').write_text(json.dumps(Audit.model_json_schema(),indent=2)+'\n')
print(json.dumps({'events':len(E),'bytes':a.response_bytes,'pdf_bytes':a.acquired_pdf_bytes,'pages':sum(p.pages for p in pdfs),'observations':len(obs),'legacy_counts':counts,'matched_legacy_rows':len(matches),'manual_rows':len(manual_rows),'manual_matches':legacy.manual_digest_matches,'sensitive_header_paths':sensitive},indent=2))
