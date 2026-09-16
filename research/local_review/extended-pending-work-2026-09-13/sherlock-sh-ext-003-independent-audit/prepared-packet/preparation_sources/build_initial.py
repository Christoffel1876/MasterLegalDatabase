from pathlib import Path
import json,hashlib,subprocess,sys,os
from datetime import datetime,timezone
from urllib.parse import urlsplit
from pydantic import BaseModel,ConfigDict,RootModel
BASE=Path('/Users/mcoors/Documents/Project Geode')
REPO=BASE/'MasterLegalDatabase'
OLD=BASE/'handoffs/run-2026-09-12/extended-run/sherlock-sh-ext-001'
OUT=BASE/'handoffs/run-2026-09-12/extended-run/sherlock-sh-ext-003'
def put(path,data):
 path=OUT/path;path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():raise ValueError('Refuse overwrite '+str(path))
 if isinstance(data,str):data=data.encode()
 tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data);tmp.replace(path)
def jput(path,data,model=None):
 raw=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
 if model:model.model_validate_json(raw)
 put(path,raw)
replacements={'SH-EXT-001':'SH-EXT-003','SHEXT001':'SHEXT003','CO-COUNTY-PUEBLO':'CO-COUNTY-CHAFFEE','CO-COUNTY-FREMONT':'CO-COUNTY-GUNNISON'}
for file in ['models.py','validate_templates.py','verify_packet.py','test_reporting_templates.py']:
 text=(OLD/file).read_text()
 for a,b in replacements.items():text=text.replace(a,b)
 if file=='models.py':
  text=text.replace('        urls = {r.requested_url for r in self.reservations if r.requested_url}', '''        # Each automatically observed hop is additionally charged; manually followed hops
        # instead receive their own reservation and must not be listed here a second time.
        by_id = {r.action_id: r for r in self.reservations}
        extra_hops = sum(len(r.visible_redirect_urls) for r in self.results)
        if len(self.reservations) + extra_hops > 40:
            raise ValueError("Visible redirect action cap exceeded")
        urls = {r.requested_url for r in self.reservations if r.requested_url}
        urls.update(url for result in self.results for url in result.visible_redirect_urls)
        body_sizes = []
        for result in self.results:
            if result.body_sha256:
                matches = [a for a in result.retained_assets if a.sha256 == result.body_sha256]
                sizes = {a.size_bytes for a in matches}
                if len(sizes) != 1:
                    raise ValueError("Conflicting byte lengths for the same body hash")
                body_sizes.append(next(iter(sizes)))
        if any(size > 20_000_000 for size in body_sizes):
            raise ValueError("Per-body byte cap exceeded")
        if sum(body_sizes) > 80_000_000:
            raise ValueError("Total retained response-body byte cap exceeded")''')
  text=text.replace('if sum(r.authority_id == authority for r in self.reservations) > 20:', '''charged = sum(r.authority_id == authority for r in self.reservations)
            charged += sum(len(r.visible_redirect_urls) for r in self.results
                           if by_id[r.action_id].authority_id == authority)
            if charged > 20:''')
  text=text.replace('        return self\n\n\nclass ChecklistRow', '''        if ids and results != ids[:len(results)]:
            raise ValueError("Results must close the serial reservation prefix")
        return self


class ChecklistRow''')
 put(file,text)
sys.path.insert(0,str(OUT))
from models import ActionLog,ArtifactInventory,Backlog,Checklist,Priorities
from verify_packet import Asset
from typing import Any,Literal
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Input(Strict):
 repository_path:str; working:Asset;pinned:Asset;byte_equal:bool
class RegistryEntry(Strict):
 json_pointer:str;record:dict[str,Any]
class Legacy(Strict):
 edition:str;repository_path:str;full_sha256:str;full_bytes:int;full_rows:int
 selected:Asset;selected_rows:int;original_line_numbers:list[int]
 by_authority:dict[str,int];status_counts:dict[str,int]
 url_attempts:dict[str,int];source_id_attempts:dict[str,int]
 recorded_sha256s:list[str];referenced_local_paths_present:list[str]
class Comparison(Strict):
 assignment_id:Literal['SH-EXT-003'];status:Literal['PREPARED_NOT_DISPATCHED']
 captured_at:str;pinned_commit:str;observed_head:str;inputs:list[Input];legacy:list[Legacy]
 registry_entries:list[RegistryEntry];limitations:list[str]
class RawRow(RootModel[dict[str,Any]]):pass
def ref(path):
 p=OUT/path;b=p.read_bytes();return dict(path=str(path),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
inputs=[]
paths=['_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json','_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json','_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl','08_County_Authorities/_index.jsonl','_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl','_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json']
for name in paths:
 working=(REPO/name).read_bytes() if not name.endswith('.jsonl') else b''.join((REPO/name).open('rb'))
 pinned=subprocess.check_output(['git','show',head+':'+name],cwd=REPO)
 relw=Path('comparison/working_tree')/name;relp=Path('comparison/pinned_commit')/name
 put(relw,working);put(relp,pinned)
 inputs.append(dict(repository_path=name,working=ref(relw),pinned=ref(relp),byte_equal=working==pinned))
authorities={'CO-COUNTY-CHAFFEE','CO-COUNTY-GUNNISON'}
hosts={'chaffeecounty.org','www.chaffeecounty.org','search.chaffeecounty.org','gunnisoncounty.org','www.gunnisoncounty.org'}
entries=[]
def walk(x,path=''):
 if isinstance(x,dict):
  if x.get('authority_id') in authorities and 'source_id' in x:entries.append(dict(json_pointer=path,record=x))
  for k,v in x.items():walk(v,path+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
walk(json.loads((REPO/paths[0]).read_bytes()))
legacy=[]
for edition in ['pinned_commit','working_tree']:
 name='_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'
 process=None
 if edition=='pinned_commit':
  process=subprocess.Popen(['git','show',head+':'+name],cwd=REPO,stdout=subprocess.PIPE)
  stream=process.stdout
 else:stream=(REPO/name).open('rb')
 digest=hashlib.sha256();total=0;rows=0;selected=[];numbers=[];by={};statuses={};urls={};ids={};hashes=set();present=set()
 for line in stream:
  digest.update(line);total+=len(line);rows+=1
  record=RawRow.model_validate_json(line).root
  observed=[record.get(k) for k in ['source_url','requested_url','final_url','url']]
  match=record.get('authority_id') in authorities or str(record.get('source_id','')).startswith(('county_chaffee_','county_gunnison_'))
  match=match or any(isinstance(u,str) and urlsplit(u).hostname in hosts for u in observed)
  if not match:continue
  selected.append(line);numbers.append(rows)
  auth=record.get('authority_id','unknown');by[auth]=by.get(auth,0)+1
  status=record.get('status','unknown');statuses[status]=statuses.get(status,0)+1
  sid=record.get('source_id','unknown');ids[sid]=ids.get(sid,0)+1
  for u in set(u for u in observed if isinstance(u,str)):urls[u]=urls.get(u,0)+1
  sha=record.get('sha256')
  if isinstance(sha,str) and len(sha)==64:hashes.add(sha)
  raw=record.get('raw_path','').replace('\\','/')
  if '_RAW_ARCHIVE/' in raw:
   rel=Path('_RAW_ARCHIVE/'+raw.split('_RAW_ARCHIVE/',1)[1])
   if '..' not in rel.parts and (REPO/rel).is_file():present.add(str(rel))
 stream.close()
 if process and process.wait()!=0:raise ValueError('git show failed')
 rel=Path('comparison')/edition/'legacy-selected.jsonl';put(rel,b''.join(selected))
 legacy.append(dict(edition=edition,repository_path=name,full_sha256=digest.hexdigest(),full_bytes=total,full_rows=rows,selected=ref(rel),selected_rows=len(numbers),original_line_numbers=numbers,by_authority=by,status_counts=statuses,url_attempts=urls,source_id_attempts=ids,recorded_sha256s=sorted(hashes),referenced_local_paths_present=sorted(present)))
result=dict(assignment_id='SH-EXT-003',status='PREPARED_NOT_DISPATCHED',captured_at=datetime.now(timezone.utc).isoformat(),pinned_commit=head,observed_head=head,inputs=inputs,legacy=legacy,registry_entries=entries,limitations=[
'All full legacy rows were parsed before selection. Selected exact lines are historical attempts, not distinct documents or current legal coverage.',
'Exact URL equality, matching recorded digest, and availability of actual historical bytes are separate facts. A legacy digest does not verify a fresh source.',
'Full legacy streams are not distributed; their full hashes require the pinned repository to reproduce. Selected exports preserve original line bytes and line numbers.',
'Present referenced paths were checked only inside this repository after mapping the exact _RAW_ARCHIVE suffix; existence is not a recomputed historical byte match. No external Windows folders were opened.',
'No public URL was opened; old registry ownership, categories, dates and access status remain unverified leads.',
'Working and pinned manual-intake snapshots may differ; neither supersedes the other. Pointer files are unresolved metadata, not available JSONL corpora.'
])
jput('COMPARISON.json',result,Comparison);jput('COMPARISON.schema.json',Comparison.model_json_schema())
# The exact source object and registry pointer establish each authorized initial seed.
seed_ids=['county_chaffee_homepage','county_chaffee_county_codes_f34e1fe22815','county_chaffee_land_use_code','county_chaffee_continuing_resolutions_f5a90c0441da','county_gunnison_homepage','county_gunnison_building_office','county_gunnison_county_codes_8933f601f6c0','county_gunnison_land_use_resolution']
class Seed(Strict):
 source_id:str;authority_id:str;url:str;registry_json_pointer:str;priority_purpose:str
class Plan(Strict):
 assignment_id:Literal['SH-EXT-003'];status:Literal['PREPARED_NOT_DISPATCHED']
 research_cutoff:str;report_cutoff:str;seeds:list[Seed];max_actions:int;max_actions_per_county:int
 max_distinct_urls:int;max_body_bytes:int;max_total_body_bytes:int;max_pending_actions:int
 public_actions_by_preparation:Literal[0];next_assignment_authorized:Literal[False]
purposes=['Confirm county identity and discover explicitly linked fee/legal pages','Building code adoptions, amendments and short linked fee instruments','Land-use legal catalog and linked planning-fee/adoption instruments','Commissioner adopted resolutions/ordinance catalog','Confirm county identity and discover expressly linked fee/legal pages','Building Office fee/adoption links','Building Codes adoptions/local amendments','Land-use resolution catalog, planning fees and adopting instruments']
seeds=[]
for sid,purpose in zip(seed_ids,purposes):
 entry=next(e for e in entries if e['record']['source_id']==sid);r=entry['record']
 seeds.append(dict(source_id=sid,authority_id=r['authority_id'],url=r['url'],registry_json_pointer=entry['json_pointer'],priority_purpose=purpose))
plan=dict(assignment_id='SH-EXT-003',status='PREPARED_NOT_DISPATCHED',research_cutoff='2026-09-13T03:05:00Z',report_cutoff='2026-09-13T03:20:00Z',seeds=seeds,max_actions=40,max_actions_per_county=20,max_distinct_urls=30,max_body_bytes=20000000,max_total_body_bytes=80000000,max_pending_actions=1,public_actions_by_preparation=0,next_assignment_authorized=False)
jput('PLAN.json',plan,Plan);jput('PLAN.schema.json',Plan.model_json_schema())
for name,model in {'ACTION_LOG':ActionLog,'ARTIFACT_INVENTORY':ArtifactInventory,'BACKLOG':Backlog,'CHECKLIST':Checklist,'PRIORITIES':Priorities}.items():
 data=(OLD/'templates'/f'{name}.json').read_text()
 for a,b in replacements.items():data=data.replace(a,b)
 value=model.model_validate_json(data)
 jput(Path('templates')/f'{name}.json',value.model_dump(mode='json'),model)
 jput(Path('schemas')/f'{name}.schema.json',model.model_json_schema())
print(json.dumps({'head':head,'registry_entries':len(entries),'legacy':[{k:l[k] for k in ['edition','full_rows','selected_rows','by_authority','referenced_local_paths_present']} for l in legacy],'seeds':seeds},indent=2))
