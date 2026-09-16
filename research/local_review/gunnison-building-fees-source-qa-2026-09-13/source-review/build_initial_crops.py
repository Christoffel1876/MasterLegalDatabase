from pathlib import Path
from pydantic import BaseModel, ConfigDict
import fitz, hashlib, json
B=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-fees-source-qa')
class Crop(BaseModel):
    model_config=ConfigDict(extra='forbid')
    path: str
    image_path: str
    image_sha256: str
    rectangle: tuple[int,int,int,int]
    sha256: str
class Crops(BaseModel):
    model_config=ConfigDict(extra='forbid')
    method:str
    crops:list[Crop]
rows=[]
for n,name,box in [(1,'p1-execution',(200,2150,2450,3290)),(2,'p2-signatures',(200,40,2370,1500)),(3,'p3-top',(180,220,2390,1590)),(3,'p3-bottom',(180,1450,2390,2950))]:
    ip=B/f'pages/page-{n:04}.png'; p=fitz.Pixmap(str(ip));x0,y0,x1,y1=box
    samples=b''.join(p.samples[y*p.stride+x0*p.n:y*p.stride+x1*p.n] for y in range(y0,y1))
    out=B/f'crops/{name}.png';fitz.Pixmap(fitz.csRGB,x1-x0,y1-y0,samples,False).save(out)
    rows.append(Crop(path=str(out.relative_to(B)),image_path=str(ip.relative_to(B)),image_sha256=hashlib.sha256(ip.read_bytes()).hexdigest(),rectangle=box,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
r=Crops(method='Exact RGB pixel rectangle from full 300 dpi Poppler PNG; top-left origin',crops=rows)
for name,data in [('CROPS.json',r.model_dump_json(indent=2)),('CROPS.schema.json',json.dumps(Crops.model_json_schema(),indent=2))]:
    with (B/name).open('x') as f:f.write(data+'\n')
