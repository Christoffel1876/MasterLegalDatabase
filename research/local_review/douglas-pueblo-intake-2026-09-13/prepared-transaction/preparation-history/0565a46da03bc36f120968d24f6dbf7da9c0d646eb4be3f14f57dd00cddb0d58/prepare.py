"""Prepare local immutable inputs only. Never apply this transaction."""
import ast, hashlib, json, os, re, shutil, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime
import pymupdf
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]/'MasterLegalDatabase'
OLD=BASE.parent/'colorado-springs-intake-transaction'
sys.path.insert(0,str(ROOT))
from geode.pipeline.manual_source_intake import ManualSourceIntakeRequest, ManualSourceIntakeRecord, reconcile_manual_source_intake
class Strict(BaseModel): model_config=ConfigDict(extra='forbid',strict=True)
class Asset(Strict):
 path:str;sha256:str=Field(pattern=r'^[a-f0-9]{64}$');size_bytes:int=Field(ge=0)
class Source(Strict):
 source_id:str;proposed_record_id:str;authority_id:str;layer_id:Literal['08_County_Authorities','10_Municipal_Authorities'];original:Asset;http_url:str;request_started_at:AwareDatetime;response_completed_at:AwareDatetime;http_status:Literal[200];physical_pages:int;issuer:str;source_date_claims:list[str];legal_currentness:Literal['not_verified'];actual_repository_received_at:None;review_scope:str;qualifications:list[str];evidence:list[Asset]
class Template(Strict):
 record_id:str;layer_id:str;official_source_name:str;official_source_url:str;acquisition_method:Literal['manual_official_download'];received_from:str;reviewer_name:str;reviewer_email:None;custody_note:str;expected_sha256:str;allow_duplicate:Literal[False];source_file:Asset;original_filename:str;intake_id:None;archive_path:None;received_at:None;status:Literal['proposed_not_applied']
class Baseline(Strict): repository_path:str;preserved:Asset;records:int|None
class Preparation(Strict):
 schema_version:Literal[1];status:Literal['PREPARED_NOT_APPLIED'];prepared_at:AwareDatetime;canonical_mutations:Literal[0];public_requests:Literal[0];sources:list[Source];proposed_records:list[Template];baseline:list[Baseline];raw_before:Literal[61];raw_after:Literal[63];ledger_before:Literal[62];ledger_after:Literal[64];missing_ledger_only_ids:list[str];duplicate_check:str;legacy_id_check:str
class Manifest(Strict): schema_version:Literal[1];files:list[Asset]
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x.model_dump(mode='json') if isinstance(x,BaseModel) else x,indent=2,ensure_ascii=False)+'\n').encode()
def put(path,data):
 p=BASE/path;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==data,path
 else:
  with p.open('xb') as f:f.write(data)
 return Asset(path=path,sha256=sha(data),size_bytes=len(data))
def cp(src,dst):return put(dst,src.read_bytes())
PREP=BASE/'evidence/preparation';PREP.mkdir(parents=True,exist_ok=True)
def cpe(src,dst):
 a=cp(src,'evidence/preparation/'+dst);return a.model_copy(update={'path':dst})
ids=['douglas-ehs-fees-atlas-directed','pueblo-planning-fees-atlas-directed']
configs=[dict(sid='douglas-county-ehs-fees-dcr03',id=ids[0],authority='CO-COUNTY-DOUGLAS',layer='08_County_Authorities',qa='douglas-ehs-fees-source-qa-2026-09-13',discovery='douglas-castle-rock-discovery-2026-09-12/frozen',event='E017',parent='E012',pages=1,name='Douglas County Health Department environmental health fee schedule',dates=['2026 Fee columns','Fees Set By Douglas County Board of Health - Effective November 1, 2025','Fees Set By State Legislation - Effective September 1, 2025'],scope='44 rows /220 displayed cells,218 nonblank native cell lines and2 blank fee cells; one full physical page; Atlas candidate-aware review, not blind or independent-model diversity.',accept='DOUGLAS_EHS_SOURCE_QA'),dict(sid='city-pueblo-planning-fees',id=ids[1],authority='CO-MUNICIPAL-PUEBLO',layer='10_Municipal_Authorities',qa='pueblo-planning-fees-source-qa-2026-09-13',discovery='pueblo-fee-discovery-2026-09-13',event='E005',parent='E002',pages=4,name='City of Pueblo Planning and Community Development application fee schedule',dates=['2-13-26 printed on all4 physical pages'],scope='44 physical application rows and nested category/fee associations over4 pages. Atlas candidate-aware QA; source-first header/date and nor errata preserved additively.',accept='PUEBLO_SOURCE_QA')]
sources=[];templates=[]
for c in configs:
 q=ROOT/'research/local_review'/c['qa'];d=ROOT/'research/local_review'/c['discovery'];ev=json.loads((d/'events'/c['event']/'event.json').read_bytes());body=d/'events'/c['event']/'body.bin';b=body.read_bytes();assert b== (q/'original.pdf').read_bytes();assert sha(b)==ev['body']['sha256'];assert len(b)==ev['body'].get('size_bytes',ev['body'].get('bytes'))
 with pymupdf.open(stream=b,filetype='pdf') as pdf:assert len(pdf)==c['pages'] and not pdf.is_repaired and not pdf.is_encrypted
 original=cpe(body,'sources/'+c['id']+'/original.pdf'); evidence=[]
 for event in [c['parent'],c['event']]+(['E004'] if c['id']==ids[1] else []):
  for name in ['event.json','reservation.json','public.headers','curl-metadata.txt','stderr.txt']:
   p=d/'events'/event/name
   if p.is_file():evidence.append(cpe(p,'custody/'+c['id']+'/'+event+'/'+name))
  if event!=c['event']:evidence.append(cpe(d/'events'/event/'body.bin','custody/'+c['id']+'/'+event+'/body.bin'))
 for name in ['SOURCE_QA.json','README.md','MANIFEST.json','INDEPENDENT_REVIEW.json','ERRATA.json']:
  if (q/name).is_file():evidence.append(cpe(q/name,'review/'+c['id']+'/'+name))
 evidence.append(cpe(ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12'/c['accept']/'ACCEPTANCE.json','review/'+c['id']+'/ROOT_ACCEPTANCE.json'))
 if (d/'OFFICIAL_LINKS.json').is_file():evidence.append(cpe(d/'OFFICIAL_LINKS.json','custody/'+c['id']+'/OFFICIAL_LINKS.json'))
 quals=['Source printed dates are separate from acquisition and future repository receipt; adoption and legal currentness are not verified.','Existing review artifacts are dated evidence; this intake does not create RuleUnits, enable answers, calculate fees, or enroll monitoring.']
 if c['id']==ids[0]:quals+=['County issuer; county-set and state-legislation captions are literal source claims, not separately acquired state laws. Blank fees are not zero.']
 else:quals+=['City issuer only; no Pueblo County scope. Exact received final URL follows retained E004301 from official parent selected link.']
 src=Source(source_id=c['sid'],proposed_record_id=c['id'],authority_id=c['authority'],layer_id=c['layer'],original=original,http_url=ev.get('final_url',ev['requested_url']),request_started_at=datetime.fromisoformat(ev['started_at'].replace('Z','+00:00')),response_completed_at=datetime.fromisoformat(ev['completed_at'].replace('Z','+00:00')),http_status=200,physical_pages=c['pages'],issuer=c['name'],source_date_claims=c['dates'],legal_currentness='not_verified',actual_repository_received_at=None,review_scope=c['scope'],qualifications=quals,evidence=evidence)
 note=f"Authority {c['authority']}; directly recorded Atlas ordinary verified-TLS public HTTP acquisition {ev['started_at']} through {ev['completed_at']}, status200, exact PDF SHA256{sha(b)}. Earlier HTTP acquisition is not the future repository received_at. Source printed claims: {'; '.join(c['dates'])}. {' '.join(quals)} Evidence: handoffs/run-2026-09-12/final-two-source-intake/evidence/preparation/custody/{c['id']}/."
 t=Template(record_id=c['id'],layer_id=c['layer'],official_source_name=c['name'],official_source_url=src.http_url,acquisition_method='manual_official_download',received_from='Atlas recorded official public HTTP response',reviewer_name='Atlas',reviewer_email=None,custody_note=note,expected_sha256=sha(b),allow_duplicate=False,source_file=original,original_filename=('douglas_environmental_health_fee_schedule.pdf' if c['id']==ids[0] else 'pueblo_planning_fee_schedule_2-13-26.pdf'),intake_id=None,archive_path=None,received_at=None,status='proposed_not_applied')
 fields={k:getattr(t,k) for k in ['record_id','layer_id','official_source_name','official_source_url','acquisition_method','received_from','reviewer_name','reviewer_email','custody_note','expected_sha256','allow_duplicate']};fields['source_file']=str(PREP/original.path);ManualSourceIntakeRequest.model_validate(fields)
 sources.append(src);templates.append(t)
paths=['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_POLICY.json','_CONTROL_PLANE/BLOCKED_DOWNLOAD_QUEUE.json'];baseline=[]
for path in paths:
 n=None
 if path.endswith('.jsonl'):
  with (ROOT/path).open('rb') as f:
   rows=[ManualSourceIntakeRecord.model_validate_json(line) for line in f]
  n=len(rows);assert n==(61 if path.startswith('_RAW') else 62)
  assert not any(r.record_id in ids or r.sha256 in [s.original.sha256 for s in sources] for r in rows)
 baseline.append(Baseline(repository_path=path,preserved=cpe(ROOT/path,'baseline/'+path),records=n))
# Scope legacy ID scan to control/legacy source registries and source manifests, not raw PDF contents.
legacy=[]
for path in list((ROOT/'_CONTROL_PLANE').glob('*SOURCE*'))+list((ROOT/'_RAW_ARCHIVE/local').glob('**/*manifest*.json*')):
 if path.is_file() and path.stat().st_size<20_000_000:
  with path.open('rb') as f:
   for line in f:
    if any(i.encode() in line for i in ids):legacy.append(str(path.relative_to(ROOT)))
assert not legacy,legacy
check=reconcile_manual_source_intake(ROOT,dry_run=True);assert not check.added_intake_ids and not check.report_needs_update
prep=Preparation(schema_version=1,status='PREPARED_NOT_APPLIED',prepared_at=datetime.now(timezone.utc),canonical_mutations=0,public_requests=0,sources=sources,proposed_records=templates,baseline=baseline,raw_before=61,raw_after=63,ledger_before=62,ledger_after=64,missing_ledger_only_ids=check.report.archive_verification.missing_ledger_only_intake_ids,duplicate_check='Current raw/ledger ID and SHA check passed; transaction preflight scans all raw files by candidate byte lengths and LFS OIDs.',legacy_id_check='No proposed ID in current control source files or local source manifests scanned; no arbitrary rename/reclassification of historic records.')
cpe_data=lambda name,data:put('evidence/preparation/'+name,data)
cpe_data('PREPARATION.json',enc(prep));cpe_data('PREPARATION.schema.json',enc(Preparation.model_json_schema()));cpe_data('proposed-records.jsonl',b''.join((t.model_dump_json()+'\n').encode() for t in templates));cpe_data('source-provenance.jsonl',b''.join((s.model_dump_json()+'\n').encode() for s in sources))
manifest=Manifest(schema_version=1,files=[Asset(path=p.relative_to(PREP).as_posix(),sha256=sha(p.read_bytes()),size_bytes=p.stat().st_size) for p in sorted(PREP.rglob('*')) if p.is_file()]);cpe_data('FINAL_MANIFEST.json',enc(manifest));cpe_data('FINAL_MANIFEST.schema.json',enc(Manifest.model_json_schema()))
# Preserve the exact reviewed implementation and tests before adapting only this new copy.
cp(OLD/'transaction.py','reference/transaction.py');cp(OLD/'test_transaction.py','reference/test_transaction.py')
code=(OLD/'transaction.py').read_text();code=code.replace('Guarded Colorado Springs official-PDF transaction','Guarded Douglas County / Pueblo City official-PDF transaction')
code=re.sub(r'PREP_SHA = "[a-f0-9]+"','PREP_SHA = "'+sha((PREP/'PREPARATION.json').read_bytes())+'"',code);code=re.sub(r'MANIFEST_SHA = "[a-f0-9]+"','MANIFEST_SHA = "'+sha((PREP/'FINAL_MANIFEST.json').read_bytes())+'"',code)
start=code.index('def load_plan(');end=code.index('\ndef rows(',start)
loader='''def load_plan(root: Path) -> Plan:
    """Verify the exact closed prepared inputs before any possible write."""
    safe(root)
    for name, expected in [("PREPARATION.json", PREP_SHA), ("FINAL_MANIFEST.json", MANIFEST_SHA)]:
        p=safe(PREP,name)
        if not p.is_file() or digest(p.read_bytes())!=expected:raise ValueError("Unapproved preparation: "+name)
    manifest=json.loads((PREP/"FINAL_MANIFEST.json").read_bytes())
    expected={x["path"] for x in manifest["files"]}|{"FINAL_MANIFEST.json","FINAL_MANIFEST.schema.json"}
    actual=set()
    for p in PREP.rglob("*"):
        safe(PREP,p.relative_to(PREP).as_posix())
        if not p.is_file() and not p.is_dir():raise ValueError("Nonordinary preparation member")
        if p.is_file():actual.add(p.relative_to(PREP).as_posix())
    if actual!=expected:raise ValueError("Preparation membership changed")
    for item in manifest["files"]:checked(PREP,File.model_validate(item))
    data=json.loads((PREP/"PREPARATION.json").read_bytes());before={};guards=[]
    for b in data["baseline"]:
        content=checked(PREP,File.model_validate(b["preserved"]))
        if b["repository_path"] in TARGETS:before[b["repository_path"]]=content
        else:guards.append(ref(b["repository_path"],content))
    return Plan(PREP_SHA,digest((PREP/"source-provenance.jsonl").read_bytes()),tuple(data["sources"]),tuple(data["proposed_records"]),PREP,before,tuple(guards))

'''
code=code[:start]+loader+code[end:]
code=code.replace('layer_id: Literal["10_Municipal_Authorities"]','layer_id: Literal["08_County_Authorities", "10_Municipal_Authorities"]')
code=code.replace('source["authority_id"] != "CO-MUNICIPAL-COLORADO_SPRINGS" or\n                source["layer_id"] != "10_Municipal_Authorities" or\n                template["layer_id"] != "10_Municipal_Authorities" or','(source["authority_id"], source["layer_id"]) not in {("CO-COUNTY-DOUGLAS", "08_County_Authorities"), ("CO-MUNICIPAL-PUEBLO", "10_Municipal_Authorities")} or\n                template["layer_id"] != source["layer_id"] or')
code=code.replace('f"_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/{sid}/"','f"_RAW_ARCHIVE/manual_intake/{template[\'layer_id\']}/{sid}/"').replace('record_id=sid, layer_id="10_Municipal_Authorities"','record_id=sid, layer_id=template["layer_id"]')
# Substitute numeric baseline literals in code, without changing hash strings.
for old,new in [(62,64),(61,63),(60,62),(59,61)]:code=re.sub(r'(?<![a-zA-Z0-9])'+str(old)+r'(?![a-zA-Z0-9])',str(new),code)
code=code.replace('colorado-springs-sd014-','douglas-pueblo-final-').replace('.colorado-springs-transaction-','.douglas-pueblo-transaction-')
# Pin current source modules: no production changes are made.
module=ast.parse(code);pins=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUNTIME_CODE' for t in n.targets));newpins={k:sha((ROOT/k).read_bytes()) for k in pins};a=code.index('RUNTIME_CODE = ');b=code.index('\ndef validate_runtime_code',a);code=code[:a]+'RUNTIME_CODE = '+repr(newpins)+'\n'+code[b:]
put('transaction.py',code.encode())
tests=(OLD/'test_transaction.py').read_text()
for old,new in [(62,64),(61,63),(60,62),(59,61)]:tests=re.sub(r'(?<![a-zA-Z0-9])'+str(old)+r'(?![a-zA-Z0-9])',str(new),tests)
tests=tests.replace('CO-MUNICIPAL-COLORADO_SPRINGS','CO-MUNICIPAL-PUEBLO').replace('coloradosprings.gov','www.pueblo.us').replace('colorado-springs-code-services-fees-2015-atlas-directed',ids[0]).replace('colorado-springs-construction-fees-atlas-directed',ids[1]);put('test_transaction.py',tests.encode())
print('PREPARED',prep.prepared_at,'two exact PDFs',sum(s.original.size_bytes for s in sources),'bytes')
