from pathlib import Path
from collections import Counter
from datetime import datetime
from urllib.parse import urljoin
import hashlib,json,sys
import pymupdf
from bs4 import BeautifulSoup
root=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/sherlock-sh-ext-001-atlas-audit')
r=root/'received';sys.path.insert(0,str(root/'input-protocol'))
from models import ActionLog,Reservation,Result,ArtifactInventory,Checklist,Priorities,Backlog
log=ActionLog.model_validate_json((r/'ACTION_LOG.json').read_bytes());pri=Priorities.model_validate_json((r/'PRIORITIES.json').read_bytes());backlog=Backlog.model_validate_json((r/'BACKLOG.json').read_bytes());check=Checklist.model_validate_json((r/'CHECKLIST.json').read_bytes());inv=ArtifactInventory.model_validate_json((r/'ARTIFACT_INVENTORY.json').read_bytes())
refs=set(x.path for x in inv.files);files={p.relative_to(r).as_posix() for p in r.rglob('*') if p.is_file()};bad=[]
for x in inv.files:
 p=r/x.path
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=x.sha256 or p.stat().st_size!=x.size_bytes:bad.append(x.path)
print('CLOSURE',len(refs),len(files),'unlisted',sorted(files-refs),'bad',bad)
summarybad=[];summarycount=0
for line in (r/'hash-summary-20260913T013911Z.txt').read_text().splitlines():
 h,name,size=line.split('  ');p=r/name;summarycount+=1
 if hashlib.sha256(p.read_bytes()).hexdigest()!=h or p.stat().st_size!=int(size):summarybad.append([name,h,hashlib.sha256(p.read_bytes()).hexdigest(),size,p.stat().st_size])
print('HASH_SUMMARY',summarycount,summarybad)
print('REPORT',hashlib.sha256((r/'report-SH-EXT-001-20260913T013911Z.md').read_bytes()).hexdigest())
individual=[];clock=[];bodybytes=0;unique={};aliases=[];pdfs=[];outcomes=Counter();last=None;headers=[]
for a,b in zip(log.reservations,log.results,strict=True):
 if Reservation.model_validate_json((r/'reservations'/f'{a.action_id}.json').read_bytes())!=a:individual.append(a.action_id+' reservation')
 if Result.model_validate_json((r/'results'/f'{a.action_id}.json').read_bytes())!=b:individual.append(a.action_id+' result')
 if b.finished_at<a.reserved_at or last and a.reserved_at<last:clock.append(a.action_id)
 last=b.finished_at;outcomes[(b.observed_http_status,b.body_role)]+=1
 for asset in b.retained_assets:
  p=r/asset.path
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=asset.sha256 or p.stat().st_size!=asset.size_bytes:bad.append('retainedasset:'+asset.path)
 matches=[x for x in b.retained_assets if x.sha256==b.body_sha256]
 if matches:
  bodybytes+=matches[0].size_bytes;unique[b.body_sha256]=matches[0].size_bytes
  binpath=r/'raw'/f'{a.action_id}.bin'
  if binpath.exists():aliases.append(binpath.read_bytes()==(r/matches[0].path).read_bytes())
 if b.body_role=='original_pdf':
  p=r/matches[0].path
  with pymupdf.open(p) as d:
   pdfs.append({'action':a.action_id,'sha256':b.body_sha256,'size_bytes':p.stat().st_size,'pages':len(d),'repair':d.is_repaired,'encrypted':d.is_encrypted,'metadata':d.metadata,'front_text':d[0].get_text()[:1800]})
   d[0].get_pixmap(dpi=130).save(root/f'{a.action_id}-page-1.png')
 if (r/'headers'/f'{a.action_id}.json').exists():
  h=json.loads((r/'headers'/f'{a.action_id}.json').read_bytes());hd=h['headers'];m=h['curl_meta']
  headers.append({'action':a.action_id,'status':m['http_code'],'bytes':m.get('size_download'),'content_length':hd.get('content-length'),'redirect':m.get('redirect_url'),'sensitive_names':[k for k in hd if k.lower() in {'set-cookie','authorization','proxy-authorization','cookie'}]})
print('COUNTS',len(log.reservations),len({x.requested_url for x in log.reservations}),Counter(x.authority_id for x in log.reservations),outcomes,'bodyperaction',bodybytes,'unique',sum(unique.values()),'max',max(unique.values()))
print('INDIVIDUAL',individual,'CLOCK',clock,'ALIASES',len(aliases),all(aliases),'PDFS',json.dumps(pdfs))
print('HEADERS',json.dumps(headers))
print('CHECKLIST',Counter((x.authority_id,x.status) for x in check.rows))
print('PRIORITY_DUP_URLS',[(u,n) for u,n in Counter(x.requested_url for x in pri.priorities).items() if n>1])
print('BACKLOG',json.dumps(backlog.model_dump(mode='json')))
# Source HTML matches before and after each open; no invented guesses are asserted absent.
all_links=[]
for a,b in zip(log.reservations,log.results,strict=True):
 if b.body_role not in {'original_html','browser_derivative'}:continue
 asset=next(x for x in b.retained_assets if x.sha256==b.body_sha256)
 soup=BeautifulSoup((r/asset.path).read_bytes(),'html.parser')
 for anchor in soup.find_all('a',href=True):all_links.append({'from_action':a.action_id,'href':anchor['href'],'url':urljoin(b.observed_final_url,anchor['href']),'label':' '.join(anchor.get_text(' ',strip=True).split())})
fee=[x for x in all_links if x['from_action']=='SHEXT001-A031' and 'Fee%20Schedule' in x['url']]
print('FEE_PROOF',json.dumps(fee))
print('FREMONT_DATE',[x for x in BeautifulSoup((r/'raw/SHEXT001-A025.html').read_bytes(),'html.parser').stripped_strings if '2024' in x])
for a in log.reservations:
 earlier=[x for x in all_links if x['url']==a.requested_url and x['from_action']<a.action_id]
 if int(a.action_id[-3:]) in [13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]:print('REFERRAL',a.action_id,a.requested_url,earlier[:2],a.basis)
(root/'analysis-calculations.json').write_text(json.dumps({'inventory_unlisted':sorted(files-refs),'inventory_bad':bad,'hash_summary_bad':summarybad,'individual_mismatches':individual,'timing_errors':clock,'body_bytes_per_action':bodybytes,'unique_body_bytes':sum(unique.values()),'pdfs':pdfs,'headers':headers,'fee_proof':fee,'links':all_links},indent=2)+'\n')
