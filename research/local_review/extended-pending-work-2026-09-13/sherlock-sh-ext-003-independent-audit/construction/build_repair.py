from pathlib import Path
from pydantic import BaseModel,ConfigDict,Field
from typing import Literal
from bs4 import BeautifulSoup
from urllib.parse import urljoin,quote
import json,hashlib,os
class Target(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 rank:int
 authority_id:Literal['CO-COUNTY-CHAFFEE']='CO-COUNTY-CHAFFEE'
 parent_action_id:str
 parent_url:str
 parent_sha256:str=Field(pattern='^[a-f0-9]{64}$')
 parent_path:str
 base_href:str
 original_href:str
 visible_label:str
 resolved_url:str
 encoded_requested_url:str
 transformation:Literal['urljoin(first HTML base href, literal anchor href); percent-encode spaces preserving existing escapes']='urljoin(first HTML base href, literal anchor href); percent-encode spaces preserving existing escapes'
 purpose:str
 limitation:str
class Repair(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 status:Literal['PREPARED_NOT_EXECUTED']='PREPARED_NOT_EXECUTED'
 public_requests:Literal[0]=0
 targets:list[Target]=Field(min_length=4,max_length=4)
 original_failed_actions_unchanged:Literal[True]=True
 limits:list[str]
b=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run');d=b/'sherlock-sh-ext-003/deliveries/20260913T021737Z';o=b/'sherlock-sh-ext-003-independent-audit';logs=json.loads((d/'ACTION_LOG.json').read_bytes());ss={n:BeautifulSoup((d/f'raw/SHEXT003-A{n:03}.html').read_bytes(),'html.parser') for n in [1,2]}
select=[(1,1,'departments/community_planning_natural_resources/application_forms_fees.php','Planning application/fee catalog; allow later separate selection only from actually observed links.'),(2,2,'departments/building_department/applications_fees.php','Building application/fee catalog; prioritize actual schedule over footer resources.'),(3,2,'Documents/Departments/Building Department/Adopted Codes & Design Criteria/2026-02 Ordinance Adopting the CWRC with Local Amendments_RECORDED.pdf?t=202606021136110','Expressly linked wildfire-code adoption instrument; preserve visible label/filename mismatch.'),(4,2,'2026-01 Ordinance Chaffee County Electric Preferred Amendments_RECORDED.pdf?t=202608031134050','Expressly linked local electric-code amendment instrument.')]
rows=[]
for rank,n,href,purpose in select:
 soup=ss[n];a=next(a for a in soup.find_all('a',href=True) if a['href']==href);base=soup.find('base',href=True)['href'];url=urljoin(base,href)
 rows.append(Target(rank=rank,parent_action_id=f'SHEXT003-A{n:03}',parent_url=logs['reservations'][n-1]['requested_url'],parent_sha256=hashlib.sha256((d/f'raw/SHEXT003-A{n:03}.html').read_bytes()).hexdigest(),parent_path=f'received/raw/SHEXT003-A{n:03}.html',base_href=base,original_href=href,visible_label=' '.join(a.get_text(' ',strip=True).split()),resolved_url=url,encoded_requested_url=quote(url,safe=":/?#[]@!$&'()*+,;=%"),purpose=purpose,limitation='Unopened lead, not retrieved original or verified adoption/currentness; filename and anchor dates remain separate claims.'))
r=Repair(targets=rows,limits=['Exactly these four initial targets; no public requests authorized by this proposal.','Root must separately approve a finite retrieval and every redirect; no automatic crawl.','Two HTML targets may reveal later unopened links; those are not automatic follow-ups.','Preserve the original 20 Chaffee actions and failed spellings; do not relabel them successful.'])
for name,data in [('CHAFFEE_REPAIR_PROPOSAL.json',r.model_dump_json(indent=2)+'\n'),('CHAFFEE_REPAIR_PROPOSAL.schema.json',json.dumps(Repair.model_json_schema(),indent=2)+'\n')]:
 f=o/name;assert not f.exists();tmp=f.with_suffix(f.suffix+'.tmp');tmp.write_text(data);os.replace(tmp,f)
print(r.model_dump_json(indent=2))
