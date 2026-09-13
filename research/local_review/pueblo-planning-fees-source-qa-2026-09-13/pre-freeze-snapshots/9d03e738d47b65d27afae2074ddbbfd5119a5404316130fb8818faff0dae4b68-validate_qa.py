"""Portable read-only source/byte/grid/custody verifier; never contacts a source URL."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
import pymupdf
from bs4 import BeautifulSoup
from qa_model import (QA, Inventory, SOURCE_SHA, PASS1_SHA, checked, derive_tables,
                      file_ref, ordinary, sha, box)

EVENT_SHA = 'abb0e0a81be60ce14de0db0240a36bd216e4a36c67461e3d4f88e81c0cd324b4'

def verify_data(root: Path, qa: QA, rerender: bool = False) -> None:
    """Replay all source text/geometry and declared qualifications, without executing builders."""
    if qa.source.path!='original.pdf' or qa.source.sha256!=SOURCE_SHA or qa.source.size_bytes!=228376:
        raise ValueError('wrong source identity')
    if qa.pass1.path!='PASS1_frozen.json' or qa.pass1.sha256!=PASS1_SHA:
        raise ValueError('frozen review identity changed')
    source=checked(root,qa.source);frozen=json.loads(checked(root,qa.pass1))
    expected_pages,expected_rows=derive_tables(root,frozen['rows'])
    if qa.pages!=expected_pages:raise ValueError('native page bytes, geometry or context mismatch')
    if qa.rows!=expected_rows:raise ValueError('physical/nested table association or display mismatch')
    if sum(p.native.size_bytes for p in qa.pages)!=qa.native_byte_count:
        raise ValueError('native byte count mismatch')
    if len({r.row_id for r in qa.rows})!=44:raise ValueError('duplicate physical rows')
    if [len(r.nested) for r in qa.rows if r.row_id in {'P1-11','P3-04'}]!=[6,11]:
        raise ValueError('nested scope mismatch')
    if {a.id for a in qa.annotations}!={'E01','E02','E03','G01','N01','C01'}:
        raise ValueError('required errata/qualification absent')
    descriptions={a.id:a for a in qa.annotations}
    for key in ['E02','E03']:
        if descriptions[key].pages!=[1,2,3,4] or 'Withdraw' not in descriptions[key].statement:
            raise ValueError('header/date omission not explicitly withdrawn')
    if ('nor site improvements' not in descriptions['E01'].statement or
            'not certified as an encoded underscore' not in descriptions['G01'].limitation):
        raise ValueError('source conditions or graphical uncertainty lost')
    for annotation in qa.annotations:
        for name in annotation.proof_paths:ordinary(root/name)
    if qa.custody_event.path!='custody/events/E005/event.json' or qa.custody_event.sha256!=EVENT_SHA:
        raise ValueError('unrecognized source custody event')
    event=json.loads(checked(root,qa.custody_event))
    if (event['authority_id']!=qa.authority_id or event['requested_url']!=qa.requested_url
            or event['http_status']!=200 or not event['body_complete'] or not event['tls_verified']
            or event['body']['sha256']!=SOURCE_SHA
            or event['started_at']!=qa.request_started_at.isoformat().replace('+00:00','Z')
            or event['completed_at']!=qa.response_finished_at.isoformat().replace('+00:00','Z')):
        raise ValueError('HTTP custody/role/time mismatch')
    for number in ['E002','E004','E005']:
        record=json.loads(ordinary(root/f'custody/events/{number}/event.json').read_bytes())
        body=ordinary(root/'custody'/record['body']['path']).read_bytes()
        if sha(body)!=record['body']['sha256'] or len(body)!=record['body']['size_bytes']:
            raise ValueError('retained HTTP body binding mismatch')
        if any(x.lower() in {'set-cookie','cookie','authorization','proxy-authorization'}
               for x in record['public_headers']):raise ValueError('private header is not distributable')
    links=json.loads((root/'custody/OFFICIAL_LINKS.json').read_bytes())
    html=(root/'custody'/links['parent_body']['path']).read_bytes()
    if sha(html)!=links['parent_body']['sha256']:raise ValueError('parent HTML hash mismatch')
    observed=[a for a in BeautifulSoup(html,'html.parser').find_all('a')
              if a.get('href')=='/DocumentCenter/View/21956/Fee-Schedule-110218-COR-LUP-FEE'
              and ' '.join(a.get_text(' ',strip=True).split())=='planning and zoning department fee schedule']
    if not observed:raise ValueError('official parent anchor absent')
    redirect=json.loads((root/'custody/events/E004/event.json').read_bytes())
    if (redirect['http_status']!=301 or redirect['requested_url']!=urljoin(links['parent_url'],observed[0]['href'])
            or redirect['redirect_to']!=qa.requested_url):raise ValueError('explicit redirect chain differs')
    with pymupdf.open(stream=source,filetype='pdf') as doc:
        for crop in qa.reproducible_crops:
            pix=doc[crop.physical_page-1].get_pixmap(matrix=pymupdf.Matrix(crop.scale,crop.scale),
                    clip=pymupdf.Rect(crop.clip),alpha=False)
            if sha(pix.samples)!=crop.pixel_sha256 or pix.tobytes('png')!=checked(root,crop.artifact):
                raise ValueError('crop pixels or source rectangle differs')
        for name,clip in [('letterhead',[0,0,612,100]),('printed_date',[490,722,555,750])]:
            values=[sha(p.get_pixmap(matrix=pymupdf.Matrix(2,2),clip=pymupdf.Rect(clip),alpha=False).samples)
                    for p in doc]
            if values!=qa.repeated_region_equality.get(name) or len(set(values))!=1:
                raise ValueError('repeated-region equality claim differs')
        rects=[box(item[1]) for drawing in doc[2].get_drawings()
               for item in drawing['items'] if item[0]=='re']
        if qa.source_graphic_bbox!=[293.84,454.96,296.9,455.74] or qa.source_graphic_bbox not in rects:
            raise ValueError('CCN source graphic changed')
        if rerender:
            for page,proof in zip(doc,qa.pages):
                if page.get_pixmap(dpi=160,alpha=False).tobytes('png')!=checked(root,proof.image):
                    raise ValueError('full source rendering mismatch')


def inventory(root: Path) -> Inventory:
    """Validate all declared files and reject paths, nonordinary entries and extra bytes."""
    values=Inventory.model_validate_json(ordinary(root/'MANIFEST.json').read_bytes())
    actual=set()
    for path in root.rglob('*'):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise ValueError('nonordinary closed-package entry')
        if path.is_file() and path.relative_to(root).as_posix()!='MANIFEST.json':
            actual.add(path.relative_to(root).as_posix())
    if actual!={f.path for f in values.files}:raise ValueError('closed inventory mismatch')
    for value in values.files:checked(root,value)
    return values


def validate(root: Path, rerender: bool = False) -> dict:
    """Read-only complete package validation; currentness remains unverified."""
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):raise ValueError('symlinked root')
    before=inventory(root)
    preserved=Inventory.model_validate_json(ordinary(root/'PRESERVED_INPUTS.json').read_bytes())
    if len(preserved.files)!=16:raise ValueError('original input count differs')
    for ref in preserved.files:checked(root,ref)
    qa=QA.model_validate_json(ordinary(root/'SOURCE_QA.json').read_bytes())
    verify_data(root,qa,rerender)
    if inventory(root)!=before:raise ValueError('package changed during verification')
    return {'status':'verified_source_qa_evidence','pages':4,'physical_rows':44,'nested_entries':43,
            'native_bytes':4923,'legal_currentness':'not_verified','public_requests':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--rerender',action='store_true')
    args=parser.parse_args()
    print(json.dumps(validate(args.root.absolute(),args.rerender),indent=2))
