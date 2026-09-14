from pathlib import Path
from hashlib import sha256
import json,pymupdf
from review_models import Geometry
r=Path(__file__).resolve().parent
(r/'native').mkdir(exist_ok=True)
d=pymupdf.open(r/'source/original.pdf')
for i,p in enumerate(d,1):
 raw=p.get_text('text',sort=False).encode()
 (r/f'native/page-{i:04}.txt').write_bytes(raw)
 lines=[];offset=0
 for block in p.get_text('dict',sort=False)['blocks']:
  if block['type']!=0:continue
  for line in block['lines']:
   t=''.join(s['text'] for s in line['spans'])+'\n';b=t.encode()
   assert raw[offset:offset+len(b)]==b,(i,offset,t,raw[offset:offset+len(b)])
   lines.append({'line_id':f'P{i}-L{len(lines)+1:03}','text':t,'start':offset,'end':offset+len(b),'bbox':line['bbox'],'spans':[{'text':s['text'],'bbox':s['bbox'],'font':s['font'],'flags':s['flags'],'size':s['size']} for s in line['spans']]});offset+=len(b)
 assert offset==len(raw)
 (r/f'native/page-{i:04}.geometry.json').write_text(Geometry.model_validate({'page':i,'native_sha256':sha256(raw).hexdigest(),'size_bytes':len(raw),'lines':lines}).model_dump_json(indent=2)+'\n')
 print('PAGE',i,'bytes',len(raw),'lines',len(lines))
 for l in lines:print(l['line_id'],tuple(round(v,1) for v in l['bbox']),repr(l['text']))
