from pathlib import Path
import json,hashlib,shutil,subprocess
from PIL import Image
import pymupdf
B=Path(__file__).parent
BASE=Path('/Users/mcoors/Documents/Project Geode')
R=BASE/'MasterLegalDatabase/research/local_review/ebenezer-013-2026-09-11'
P=BASE/'handoffs/grok-pdf-review-2026-09-11-batch-4'
S=P/'01-source-only/fort-collins-wildfire-code-sd005-05'
D=json.loads((R/'reviewed-draft.json').read_text())
for a in D['annotations']:
 print(a['id'],a['observation_id'],a['category'],repr(' '.join(x['text'] for x in a['spans'])[:105]))
B.joinpath('crops').mkdir(exist_ok=True)
# Coordinates in source PNG pixels, 2550 x 3300; crops only, no enhancement.
boxes={'p2-green':(2,(400,740,2300,1240)),'p3-title':(3,(350,695,2280,950)),'p4-habitable':(4,(560,1420,2280,1750)),'p5-code-official':(5,(360,1810,2280,2040)),'p6-exception6':(6,(560,1940,2280,2250)),'p6-materials':(6,(410,2500,2280,2940)),'p7-tree-crowns':(7,(390,560,2280,1800)),'p8-execution':(8,(275,1050,2300,2050))}
for name,(page,box) in boxes.items():Image.open(S/f'page-{page:04}.png').crop(box).save(B/'crops'/f'{name}.png')
with pymupdf.open(S/'original.pdf') as doc:
 spans=[]
 for i in [1,3,4,5,6]:
  for block in doc[i].get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for sp in line['spans']:
     if any(w.lower() in sp['text'].lower() for w in ['habitable','space.','official','Ignition-resistant','Immediate Zone','Tree crowns','____','compared','square feet']):
      spans.append({'physical_page':i+1,'text':sp['text'],'font':sp['font'],'flags':sp['flags'],'bbox':sp['bbox']})
 (B/'native-font-support.json').write_text(json.dumps(spans,indent=2)+'\n')
 print('FONT SUPPORT',json.dumps(spans,indent=2))
