"""Read-only verification of the five-page Weld ordinance source review."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
from typing import Literal
import jsonschema
import pymupdf
from review_models import Review, Custody, Manifest, Strict, Asset
B=Path(__file__).resolve().parent

class ValidationResult(Strict):
    validated_at: datetime
    status: Literal['passed']
    review: Asset
    source_pdf_bytes: Literal[125953]
    source_pages: Literal[5]
    native_bytes: Literal[9284]
    page_observations: Literal[18]
    stated_date_records: Literal[11]
    images_bound: Literal[8]
    crops_reproduced: Literal[11]
    selected_custody_files: Literal[6]
    original_paths_checked: bool
    candidate_or_source_changed: Literal[False]
    legal_currentness: Literal['not_verified']
    checks: list[str]

def check(root:Path,asset:Asset)->bytes:
    """Return only the exact ordinary-file bytes named by a confined asset."""
    p=root/asset.path
    assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),asset.path
    raw=p.read_bytes()
    assert len(raw)==asset.size_bytes and sha256(raw).hexdigest()==asset.sha256,asset.path
    return raw

def load(name:str,model:type[Strict])->Strict:
    """Validate strict data and exported schema without rewriting either."""
    raw=(B/(name+'.json')).read_bytes()
    schema=json.loads((B/(name+'.schema.json')).read_bytes())
    assert schema==model.model_json_schema()
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    return model.model_validate_json(raw)

def validate(check_originals:bool=False)->ValidationResult:
    """Check local byte custody, full native text, source observations and images."""
    r=load('SOURCE_QA',Review)
    custody=load('CUSTODY_RECEIPT',Custody)
    assert r.source.sha256=='2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0'
    assert r.source.size_bytes==125953 and pymupdf.VersionBind=='1.28.2'
    check(B,r.source)
    assert len(custody.files)==6
    for f in custody.files:
        raw=check(B,f.local)
        if check_originals:
            p=Path(f.original_path)
            assert not any(x.is_symlink() for x in (p,*p.parents))
            assert p.read_bytes()==raw
    acquisition=json.loads(check(B,r.acquisition_receipt))
    jsonschema.Draft202012Validator(json.loads((B/'inputs/ACCESS_RECEIPT.schema.json').read_bytes())).validate(acquisition)
    event=next(x for x in acquisition['attempts'] if x['event_id']=='ATLAS-WELD-03')
    assert event['retained_original']['sha256']==r.source.sha256
    assert event['response_body']['sha256']==r.source.sha256
    assert event['retained_original']['size_bytes']==r.source.size_bytes
    assert event['target_url']==event['final_url']==r.source_url
    assert event['http_status']==200 and event['curl_exit_code']==0
    assert event['finished_at']=='2026-09-11T19:49:18.706875Z'
    for key,path in [('stdout_metadata','curl-metadata.json'),('stderr','curl-stderr.txt'),('response_headers','response-headers.bin')]:
        row=event[key]
        check(B,Asset(path='inputs/'+path,sha256=row['sha256'],size_bytes=row['size_bytes']))
    assert {o.id for o in r.observations}=={f'W26-O{i:02}' for i in range(1,19)}
    assert len(r.stated_dates)==11
    assert [(d.role,d.stated_date) for d in r.stated_dates]==[
        ('publication','2026-01-14'),('first_reading','2026-01-26'),
        ('publication','2026-01-30'),('second_reading','2026-02-09'),
        ('publication','2026-02-13'),('final_reading_rescheduled_to','2026-02-25'),
        ('continued_to','2026-04-06'),('publication','2026-04-10'),
        ('effective_as_stated','2026-04-15'),('adoption_as_stated','2026-04-06'),
        ('historical_ordinance_2000_1_adoption_recital','2000-12-28')]
    with pymupdf.open(B/r.source.path) as pdf:
        assert len(pdf)==5 and not pdf.is_encrypted and not pdf.is_repaired
        assert not any(page.get_links() for page in pdf)
        for p in r.pages:
            raw=pdf[p.physical_page-1].get_text('text',sort=False,flags=195).encode()
            assert raw==p.native_text.encode()==check(B,p.native_file)
            check(B,p.primary_image)
            assert '2026-0765 \nORD2026-01 \n' in p.native_text
            if p.secondary_image:
                check(B,p.secondary_image)
                with pymupdf.open(B/r.source.path) as fresh:
                    expected=fresh[p.physical_page-1].get_pixmap(matrix=pymupdf.Matrix(150/72,150/72),alpha=False).tobytes('png')
                assert expected==(B/p.secondary_image.path).read_bytes()
        assert len(r.crops)==11
        for c in r.crops:
            raw=check(B,c.file)
            if c.method=='pymupdf_300dpi_pdf_clip':
                expected=pdf[c.physical_page-1].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(c.rect),alpha=False).tobytes('png')
                assert expected==raw,c.id
            else:
                original=pymupdf.Pixmap(B/r.pages[c.physical_page-1].primary_image.path)
                crop=pymupdf.Pixmap(B/c.file.path)
                left,top,right,bottom=c.rect
                assert original.n==crop.n==3 and crop.width==right-left and crop.height==bottom-top
                pixels=original.samples
                expected=b''.join(pixels[y*original.stride+left*3:y*original.stride+right*3] for y in range(top,bottom))
                assert expected==crop.samples,c.id
    p2=r.pages[1].native_text;p3=r.pages[2].native_text;p5=r.pages[4].native_text
    assert 'I. though T. - No change.' in p2
    assert 'mitigation may be required sufficient' in p3
    votes=p5[p5.index('Scott K. James'):p5.index('Approved as to Form:')]
    assert votes.count(': Aye')==r.printed_vote_aye==4 and votes.count(': Nay')==r.printed_vote_nay==1
    assert 'Scott K. James, Chair: Nay' in votes
    assert 'Esther E. Gesick, Clerk to the Board' in p5
    if (B/'FINAL_MANIFEST.json').exists():
        final=load('FINAL_MANIFEST',Manifest)
        actual={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file() and p.name not in ['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'] and '__pycache__' not in p.parts}
        assert {x.path for x in final.files}==actual
        for f in final.files:check(B,f)
    p=B/'SOURCE_QA.json'
    return ValidationResult(validated_at=datetime.now(timezone.utc),status='passed',review=Asset(path=p.name,sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size),source_pdf_bytes=125953,source_pages=5,native_bytes=9284,page_observations=18,stated_date_records=11,images_bound=8,crops_reproduced=11,selected_custody_files=6,original_paths_checked=check_originals,candidate_or_source_changed=False,legal_currentness='not_verified',checks=['Strict Pydantic and JSON Schema; fixed source identity and complete five-page native coverage','Six exact selected custody files and source-response identity from frozen access receipt','Fresh native re-extraction equals all 9284 saved bytes; 18 image-bound observations and eleven date spans','Eight full-page images hash-bound; three additional full-page renders and all eleven crops reproduced','Printed four-Aye/one-Nay tally, distinct rescheduled/continued/adopted/effective roles and source anomalies retained','Complete frozen file inventory when present; no independent legal-currentness or execution claim'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-originals',action='store_true')
    print(validate(parser.parse_args().check_originals).model_dump_json(indent=2))
