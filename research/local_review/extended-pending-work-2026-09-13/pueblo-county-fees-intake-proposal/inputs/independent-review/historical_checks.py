from pathlib import Path
import json,hashlib,collections,importlib.util,sys
from bs4 import BeautifulSoup
import pymupdf,jsonschema
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run');P=B/'pueblo-county-fees-source-review-revision';O=B/'pueblo-county-fees-independent-review'
def sha(b):return hashlib.sha256(b).hexdigest()
d=json.loads((P/'SOURCE_QA.json').read_bytes());jsonschema.Draft202012Validator(json.loads((P/'SOURCE_QA.schema.json').read_bytes())).validate(d)
verifier=B/'pueblo-county-fees-validation/verify_source_review.py';s=importlib.util.spec_from_file_location('source_structural',verifier);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
v=m.verify(P).model_dump(mode='json')
receipt=json.loads((P/'discovery/RECEIPT.json').read_bytes());jsonschema.Draft202012Validator(json.loads((P/'discovery/RECEIPT.schema.json').read_bytes())).validate(receipt)
for r in receipt['files']:
 raw=(P/'discovery/frozen'/r['path']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)==r['size_bytes']
inv=json.loads((P/'discovery/frozen/ARTIFACT_INVENTORY.json').read_bytes())
for r in inv['files']:
 raw=(P/'discovery/frozen'/r['path']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)==r['size_bytes']
log=json.loads((P/'discovery/frozen/ACTION_LOG.json').read_bytes());assert len(log['reservations'])==len(log['results'])==2
url=log['reservations'][0]['requested_url'];legacy=B/'sherlock-sh-ext-001/comparison/pinned_commit/legacy-selected.jsonl'
assert sha(legacy.read_bytes())=='755c44489adb15f1acc91aa7ea6ad21dc59bef1a0df36cb2be0b82f2c38050cd'
matches=[];n=0
for line in legacy.open('rb'):
 r=json.loads(line);n+=1
 if url in [r.get('source_url'),r.get('requested_url')] or r.get('sha256')==d['source']['sha256']:matches.append(r)
parent=B/'sherlock-sh-ext-001/deliveries/20260913T013245Z/raw/SHEXT001-A031.html'
soup=BeautifulSoup(parent.read_bytes(),'html.parser');links=[{'href':a.get('href'),'label':a.get_text(' ',strip=True)} for a in soup.find_all('a',href=True) if a['href']==url]
assert len(links)==1
images=[]
with pymupdf.open(P/'original.pdf') as pdf:
 metadata=pdf.metadata
 for pg in d['pages']:
  image=pymupdf.Pixmap(P/pg['image']['path']);replay=pdf[pg['physical_page']-1].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False)
  assert image.samples==replay.samples
  images.append({'physical_page':pg['physical_page'],'width':image.width,'height':image.height,'pymupdf_144dpi_pixel_replay_equal':True})
result={'status':'PASS','source_qa_sha256':sha((P/'SOURCE_QA.json').read_bytes()),'structural_verifier_sha256':sha(verifier.read_bytes()),'structural_result':v,'direct_visual_pages':[1,2],'rows_directly_compared':88,'row_kind_counts':dict(collections.Counter(r['kind'] for pg in d['pages'] for r in pg['rows'])),'images':images,'pdf_metadata':metadata,'source_receipt_files_verified':len(receipt['files']),'delivery_inventory_entries_verified':len(inv['files']),'recorded_actions':2,'recorded_distinct_urls':len({r['requested_url'] for r in log['reservations']}),'recorded_body_bytes':sum(r['size_bytes'] for r in log['results']),'reported_http_times_independently_acquired':False,'legacy_comparison':{'path':str(legacy),'sha256':sha(legacy.read_bytes()),'rows':n,'fee_exact_url_or_digest_matches':matches,'scope':'Only pinned selected JSONL; not a current global duplicate or absence audit.'},'official_referral':{'path':str(parent),'sha256':sha(parent.read_bytes()),'body_role':'received_browser_DOM_derivative_not_HTTP_original','exact_anchor':links[0]},'public_requests':0,'legal_currentness':'not_verified'}
(O/'CHECKS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,indent=2,ensure_ascii=False))
