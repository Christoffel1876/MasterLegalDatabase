"""Read-only source, schema, native, pixel-crop and closed-package verification."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import fitz
import jsonschema
from prepare import Asset, Inputs, ROOT
from capture_evidence import Evidence
from role_models import Manifest, Review

PINS = {
    'P04': ('3e846e6e0e112bb0e46eb77e8292604e722ec719e325050525ebaff995eebe9d',2),
    'P07': ('f8c2183427c8fe1169c6891aee288c7d63b643ae6219fd51dc86adde03e21561',2),
    'P08': ('921d5e6854a740aea608ed15bef3ea0a9c4fc8da09e29ef45e3a932ffeacfbcc',24),
}

def checked(root: Path, ref: Asset) -> bytes:
    """Capture only a safe relative asset and validate the same consumed buffer."""
    rel=Path(ref.path)
    if rel.is_absolute() or '..' in rel.parts: raise ValueError('Unsafe asset path')
    path=root/rel
    if any(p.is_symlink() for p in [path,*path.parents] if p!=root.parent):
        raise ValueError('Symlink path')
    raw=path.read_bytes()
    if (len(raw),hashlib.sha256(raw).hexdigest())!=(ref.size_bytes,ref.sha256):
        raise ValueError('Asset bytes differ: '+ref.path)
    return raw


def verify_content(root: Path, review: Review | None = None) -> dict[str,int]:
    """Replay structural associations and unchanged derivations, not human visual judgment."""
    inputs=Inputs.model_validate_json((root/'INPUTS.json').read_bytes())
    evidence=Evidence.model_validate_json((root/'EVIDENCE.json').read_bytes())
    if review is None: review=Review.model_validate_json((root/'ROLE_DECISIONS.json').read_bytes())
    checked(root,review.inputs); checked(root,review.evidence)
    for name,model in [('INPUTS',Inputs),('EVIDENCE',Evidence),('ROLE_DECISIONS',Review)]:
        schema=json.loads((root/(name+'.schema.json')).read_bytes())
        if schema!=model.model_json_schema(): raise ValueError('Schema/model differs: '+name)
        value=review.model_dump(mode='json') if name=='ROLE_DECISIONS' else json.loads((root/(name+'.json')).read_bytes())
        jsonschema.validate(value,schema)
    sources={s.priority:s for s in inputs.sources}
    if list(sources)!=list(PINS): raise ValueError('Unexpected sources')
    images={}; native={}
    for support in inputs.supporting_inputs: checked(root,support)
    for item in sources.values():
        raw=checked(root,item.source); checked(root,item.supplied_attempt)
        sha,pages=PINS[item.priority]
        if hashlib.sha256(raw).hexdigest()!=sha or item.page_count!=pages:
            raise ValueError('Wrong exact source or page count')
        attempt=json.loads(checked(root,item.supplied_attempt))
        if attempt['sha256']!=sha or attempt['authority_id']!=item.authority:
            raise ValueError('Supplied identity mismatch')
        with fitz.open(stream=raw,filetype='pdf') as pdf:
            if len(pdf)!=pages: raise ValueError('PDF page count differs')
            native[item.priority]=[p.get_text('text',flags=195,sort=False).encode() for p in pdf]
        if len(item.images)!=pages or item.native_page_bytes!=[len(x) for x in native[item.priority]]:
            raise ValueError('Render/native page coverage differs')
        for page,ref in enumerate(item.images,1): images[(item.priority,page)]=(ref,checked(root,ref))
    native_assets={}
    for n in evidence.native_pages:
        raw=checked(root,n.native)
        if raw!=native[n.priority][n.page-1]: raise ValueError('Native bytes differ')
        key=(n.priority,n.page)
        if key in native_assets: raise ValueError('Duplicate native page')
        native_assets[key]=n.native
    if set(native_assets)!=set(images): raise ValueError('Native coverage differs')
    crop_ids=set()
    for crop in evidence.crops:
        if crop.crop_id in crop_ids: raise ValueError('Duplicate crop')
        crop_ids.add(crop.crop_id)
        ref,raw=images[(crop.priority,crop.page)]
        if ref!=crop.full_image: raise ValueError('Crop page binding differs')
        full=fitz.Pixmap(raw); x0,y0,x1,y1=crop.rectangle_xyxy
        if not (0<=x0<x1<=full.width and 0<=y0<y1<=full.height and full.n==3):
            raise ValueError('Invalid crop bounds')
        pixels=b''.join(full.samples[(y*full.width+x0)*3:(y*full.width+x1)*3] for y in range(y0,y1))
        cut=fitz.Pixmap(checked(root,crop.crop))
        if cut.width!=x1-x0 or cut.height!=y1-y0 or cut.samples!=pixels:
            raise ValueError('Crop is not exact pixel subset')
        if hashlib.sha256(pixels).hexdigest()!=crop.pixel_sha256: raise ValueError('Crop pixel hash differs')
    for document in review.documents:
        source=sources[document.priority]
        if document.source!=source.source or document.authority_id!=source.authority:
            raise ValueError('Decision identity differs')
        observations={o.observation_id:o for o in document.observations}
        for page in document.pages:
            if page.image!=images[(document.priority,page.physical_page)][0]:
                raise ValueError('Decision page image differs')
        for observation in observations.values():
            if not 1<=observation.physical_page<=source.page_count: raise ValueError('Bad observation page')
            for cid in observation.crop_ids:
                crop=next(c for c in evidence.crops if c.crop_id==cid)
                if (crop.priority,crop.page)!=(document.priority,observation.physical_page):
                    raise ValueError('Observation crop association differs')
            anchor=observation.native_anchor
            if anchor is not None:
                expected=native_assets[(document.priority,observation.physical_page)]
                if anchor.asset!=expected: raise ValueError('Wrong native anchor page')
                raw=checked(root,anchor.asset)
                if not 0<=anchor.start<=anchor.end<=len(raw) or raw[anchor.start:anchor.end].decode()!=anchor.text:
                    raise ValueError('Wrong native anchor span')
                if observation.visual_text is not None and ' '.join(anchor.text.split())!=' '.join(observation.visual_text.split()):
                    raise ValueError('Selected words differ from anchor')
    p04,p07,p08=review.documents
    if p04.blank_or_incomplete_fields!=['Adopting Resolution','Effective Date','Adoption Date']:
        raise ValueError('Blank policy metadata lost')
    if p07.assessed_role!='introduced_bill_with_uncompleted_execution_fields':
        raise ValueError('Bill improperly promoted')
    expected={'P08-O04':'July 1, 2026','P08-O06':'April 1st, 2026',
              'P08-O07':'3rd day of March, 2026','P08-O08':'24th day of March, 2026'}
    if {d.observation_id:d.literal for d in p08.dates}!=expected:
        raise ValueError('Distinct source date claims lost or changed')
    return {'sources':3,'pages':28,'crops':len(crop_ids),'native_pages':len(native_assets)}


def verify_closed(root: Path) -> int:
    """Validate closed inventory and exact manifest-listed bytes."""
    raw=(root/'FINAL_MANIFEST.json').read_bytes()
    manifest=Manifest.model_validate_json(raw)
    schema=json.loads((root/'FINAL_MANIFEST.schema.json').read_bytes())
    if schema!=Manifest.model_json_schema(): raise ValueError('Manifest schema differs')
    jsonschema.validate(json.loads(raw),schema)
    expected={f.path for f in manifest.files}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if len(expected)!=len(manifest.files) or actual!=expected|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}:
        raise ValueError('Closed file inventory differs')
    if any(p.is_symlink() for p in root.rglob('*')): raise ValueError('Symlink in package')
    for ref in manifest.files: checked(root,ref)
    return len(expected)


def rerender(root: Path) -> None:
    """Reproduce all full images in a temporary directory; no package writes."""
    inputs=Inputs.model_validate_json((root/'INPUTS.json').read_bytes())
    evidence=Evidence.model_validate_json((root/'EVIDENCE.json').read_bytes())
    for ref in (evidence.renderer_wrapper,evidence.renderer_binary):
        raw=Path(ref.path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ref.sha256: raise ValueError('Render engine differs')
    with tempfile.TemporaryDirectory(prefix='plato-role-rerender-') as temp:
        tmp=Path(temp)
        for source in inputs.sources:
            pdf=tmp/(source.priority+'.pdf'); pdf.write_bytes(checked(root,source.source))
            prefix=tmp/source.priority
            subprocess.run([inputs.renderer.path,'-r','200','-png',str(pdf),str(prefix)],check=True,capture_output=True)
            generated=sorted(tmp.glob(source.priority+'-*.png'))
            if len(generated)!=source.page_count: raise ValueError('Rerender count')
            for path,ref in zip(generated,source.images,strict=True):
                if path.read_bytes()!=checked(root,ref): raise ValueError('Rerender bytes differ')


def main() -> None:
    """Run closed checks with optional exact Poppler replay."""
    parser=argparse.ArgumentParser(); parser.add_argument('--rerender',action='store_true')
    parser.add_argument('--content-only',action='store_true')
    args=parser.parse_args()
    count=None if args.content_only else verify_closed(ROOT)
    result=verify_content(ROOT)
    if args.rerender: rerender(ROOT)
    sys.stdout.write(json.dumps({'status':'passed','closed_payloads':count,
                               'rerendered':args.rerender,**result})+'\n')
if __name__=='__main__':main()
