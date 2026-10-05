"""Create exact pixel-slice evidence and unchanged native buffers after visual inspection."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Literal

import fitz
from PIL import Image
from pydantic import BaseModel, ConfigDict
from prepare import Asset, Inputs, ROOT, POPPLER, asset

class Crop(BaseModel):
    """Unaltered rectangular pixel subset of a bound full-page render."""
    model_config = ConfigDict(extra='forbid', strict=True)
    crop_id: str
    priority: str
    page: int
    full_image: Asset
    rectangle_xyxy: list[int]
    crop: Asset
    pixel_sha256: str

class NativePage(BaseModel):
    """Untouched extraction for context; not a complete checked transcription."""
    model_config = ConfigDict(extra='forbid', strict=True)
    priority: str
    page: int
    native: Asset

class Evidence(BaseModel):
    """Actual locally generated evidence and known rendering implementation."""
    model_config = ConfigDict(extra='forbid', strict=True)
    generated_at: str
    native_method: Literal['PyMuPDF get_text(text), flags=195, sort=False; UTF-8 unchanged']
    native_version: str
    all_full_page_images_directly_viewed_before_native_read: Literal[True]
    native_length_only_preflight_before_visuals: Literal[True]
    full_image_display: Literal['view_image; 1700x2200 originals displayed at 1376x1780; crops separate']
    renderer_wrapper: Asset
    renderer_binary: Asset
    renderer_version: str
    crops: list[Crop]
    native_pages: list[NativePage]

def main() -> None:
    """Capture only new local supporting derivatives."""
    if (ROOT/'EVIDENCE.json').exists(): raise ValueError('Already captured')
    inp=Inputs.model_validate_json((ROOT/'INPUTS.json').read_bytes())
    crops=[]; natives=[]
    recipes=[
        ('P04-header','P04',1,[160,120,1600,900]),
        ('P04-effect','P04',2,[170,1100,1600,1500]),
        ('P07-header-hearing','P07',1,[90,90,1400,350]),
        ('P07-introduction','P07',1,[170,1790,1580,2050]),
        ('P07-execution','P07',2,[160,150,1510,1450]),
        ('P08-identifiers','P08',3,[180,130,1550,670]),
        ('P08-code-date','P08',8,[180,720,1600,950]),
        ('P08-agencies','P08',11,[180,140,1600,480]),
        ('P08-ending','P08',24,[160,1460,1580,2050]),
        ('P08-cover-title','P08',1,[65,1880,1650,2140]),
    ]
    (ROOT/'crops').mkdir()
    for identity,priority,page,rect in recipes:
        src=next(x for x in inp.sources if x.priority==priority)
        ref=src.images[page-1]; image=Image.open(ROOT/ref.path)
        crop=image.crop(tuple(rect)); path=ROOT/'crops'/f'{identity}.png'; crop.save(path)
        crops.append(Crop(crop_id=identity,priority=priority,page=page,full_image=ref,
            rectangle_xyxy=rect,crop=asset(path),pixel_sha256=hashlib.sha256(crop.tobytes()).hexdigest()))
    for source in inp.sources:
        directory=ROOT/'native'/source.priority; directory.mkdir(parents=True)
        with fitz.open(ROOT/source.source.path) as pdf:
            for n,page in enumerate(pdf,1):
                path=directory/f'page-{n:02}.txt'
                path.write_bytes(page.get_text('text',flags=195,sort=False).encode('utf-8'))
                natives.append(NativePage(priority=source.priority,page=n,native=asset(path)))
    import subprocess
    binary=POPPLER.parent/'../../native/poppler/bin/pdftoppm'; binary=binary.resolve()
    v=subprocess.run([str(POPPLER),'-v'],capture_output=True,text=True,check=True)
    r=Asset(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),size_bytes=binary.stat().st_size)
    data=Evidence(generated_at=datetime.now(timezone.utc).isoformat(),
        native_method='PyMuPDF get_text(text), flags=195, sort=False; UTF-8 unchanged',
        native_version=fitz.VersionBind,all_full_page_images_directly_viewed_before_native_read=True,
        native_length_only_preflight_before_visuals=True,
        full_image_display='view_image; 1700x2200 originals displayed at 1376x1780; crops separate',
        renderer_wrapper=inp.renderer,renderer_binary=r,renderer_version=(v.stdout+v.stderr).strip(),
        crops=crops,native_pages=natives)
    (ROOT/'EVIDENCE.schema.json').write_text(json.dumps(Evidence.model_json_schema(),indent=2)+'\n')
    (ROOT/'EVIDENCE.json').write_text(data.model_dump_json(indent=2)+'\n')
    sys.stdout.write(f'Captured {len(crops)} crops and {len(natives)} unchanged native pages.\n')
if __name__=='__main__':main()
