"""Validate the frozen EB013 pages 5–8 source review without writes or network."""
from __future__ import annotations
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
from typing import Annotated,Literal
import pymupdf
from jsonschema import Draft202012Validator
from pydantic import AwareDatetime,BaseModel,ConfigDict,Field,model_validator
B=Path('/Users/mcoors/Documents/Project Geode')
P=B/'handoffs/grok-pdf-review-2026-09-11-batch-4'
SID='fort-collins-wildfire-code-sd005-05'
O=B/'handoffs/atlas-reviews'/SID/'pre-review-2026-09-11/pages5-8'
SHA=Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Asset(Strict):
    path:str
    sha256:SHA
    size_bytes:int=Field(gt=0)
class Crop(Strict):
    asset:Asset
    source_image:Asset
    physical_page:int=Field(ge=5,le=8)
    pixel_box:tuple[int,int,int,int]
    method:Literal['Pillow crop of original PNG; no rescaling or annotation']
    inspected:Literal[True]=True
class Mark(Strict):
    kind:Literal['strikethrough','yellow_highlight','blank_field','draft_label','source_anomaly','page_continuation','typography']
    native_text:str
    original_start_byte:int=Field(ge=0)
    original_end_byte_exclusive:int=Field(gt=0)
    observation:str
class Observation(Strict):
    id:str
    physical_page:int=Field(ge=5,le=8)
    section:str
    region_description:str
    original_start_byte:int=Field(ge=0)
    original_end_byte_exclusive:int=Field(gt=0)
    native_text:str
    native_text_sha256:SHA
    wording_comparison:Literal['no_word_or_numeric_discrepancy_identified']
    graphical_annotations:list[Mark]
    association_risks:list[str]
class PageReview(Strict):
    physical_page:int=Field(ge=5,le=8)
    printed_page_label:str
    source_image:Asset
    image_width:Literal[2550]=2550
    image_height:Literal[3300]=3300
    native_evidence:Asset
    candidate_start_byte:int=Field(ge=0)
    candidate_end_byte_exclusive:int=Field(gt=0)
    native_text:str
    native_text_sha256:SHA
    native_text_size_bytes:int=Field(gt=0)
    full_image_inspected:Literal[True]=True
    diagnostic_crops:list[str]
    observations_in_native_order:list[Observation]
    visual_reading_order_ids:list[str]
    @model_validator(mode='after')
    def exact_partition(self)->PageReview:
        raw=self.native_text.encode();cursor=0;ids=[]
        assert hashlib.sha256(raw).hexdigest()==self.native_text_sha256
        assert len(raw)==self.native_text_size_bytes
        assert self.candidate_end_byte_exclusive-self.candidate_start_byte==len(raw)
        for obs in self.observations_in_native_order:
            assert obs.physical_page==self.physical_page
            assert obs.original_start_byte==cursor
            end=obs.original_end_byte_exclusive
            assert raw[cursor:end]==obs.native_text.encode()
            assert hashlib.sha256(obs.native_text.encode()).hexdigest()==obs.native_text_sha256
            for mark in obs.graphical_annotations:
                assert cursor<=mark.original_start_byte<mark.original_end_byte_exclusive<=end
                assert raw[mark.original_start_byte:mark.original_end_byte_exclusive]==mark.native_text.encode()
            cursor=end;ids.append(obs.id)
        assert cursor==len(raw)
        assert len(set(ids))==len(ids) and sorted(ids)==sorted(self.visual_reading_order_ids)
        return self
class Review(Strict):
    schema_version:Literal[1]=1
    assignment_id:Literal['EB-PDF-013']='EB-PDF-013'
    source_id:Literal['fort-collins-wildfire-code-sd005-05']=SID
    reviewer:Literal['Atlas / Codex independent source QA (recover_county)']
    prepared_at:AwareDatetime
    review_mode:Literal['candidate_aware_visual_QA']='candidate_aware_visual_QA'
    external_ebenezer_reports_consulted:Literal[False]=False
    blind_review_claim:Literal[False]=False
    reviewed_physical_pages:tuple[Literal[5],Literal[6],Literal[7],Literal[8]]
    source:Asset
    canonical_source:Asset
    packet_manifest:Asset
    candidate:Asset
    native_method:Literal['PyMuPDF 1.28.2 Page.get_text("text", sort=False, flags=195)']
    original_status:Literal['archived_pending_pipeline']='archived_pending_pipeline'
    candidate_status_unchanged:Literal['machine_native_text_unreviewed']='machine_native_text_unreviewed'
    source_visibly_draft:Literal[True]=True
    source_or_candidate_modified:Literal[False]=False
    legal_currentness:Literal['not_verified']='not_verified'
    adoption_or_effectiveness_certified:Literal[False]=False
    semantic_or_coverage_promotion:Literal[False]=False
    pages:list[PageReview]=Field(min_length=4,max_length=4)
    crops:list[Crop]
    findings:list[str]
    limits:list[str]
    @model_validator(mode='after')
    def page_scope(self)->Review:
        assert [p.physical_page for p in self.pages]==[5,6,7,8]
        assert self.source.sha256==self.canonical_source.sha256
        assert self.source.size_bytes==self.canonical_source.size_bytes
        return self

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def asset(p:Path)->Asset:return Asset(path=str(p),sha256=sha(p.read_bytes()),size_bytes=p.stat().st_size)
def checked(a:Asset)->bytes:
    p=Path(a.path);assert not any(x.is_symlink() for x in (p,*p.parents));b=p.read_bytes();assert len(b)==a.size_bytes and sha(b)==a.sha256;return b


def validate_review(path: Path) -> dict[str, object]:
    """Check exact native partitions, source hashes, receipts and original-pixel crops."""
    review=Review.model_validate_json(path.read_bytes())
    schema=json.loads(path.with_suffix('.schema.json').read_bytes())
    Draft202012Validator(schema).validate(review.model_dump(mode='json'))
    checked(review.canonical_source)
    raw=checked(review.source)
    candidate=checked(review.candidate)
    packet=json.loads(checked(review.packet_manifest))
    document=next(d for d in packet['documents'] if d['source_id']==review.source_id)
    if document['original']['sha256']!=review.source.sha256:
        raise ValueError('packet source binding differs')
    with pymupdf.open(stream=raw,filetype='pdf') as pdf:
        if len(pdf)!=8:
            raise ValueError('source page count differs')
        for page in review.pages:
            image=checked(page.source_image)
            evidence=json.loads(checked(page.native_evidence))
            declared=document['pages'][page.physical_page-1]
            if (page.source_image.sha256!=declared['image']['sha256']
                or page.native_evidence.sha256!=declared['evidence']['sha256']
                or evidence['source_sha256']!=review.source.sha256
                or evidence['source_image_sha256']!=page.source_image.sha256
                or evidence['text']!=page.native_text
                or evidence['physical_page']!=page.physical_page):
                raise ValueError('page identity or native receipt differs')
            if candidate[page.candidate_start_byte:page.candidate_end_byte_exclusive]!=page.native_text.encode():
                raise ValueError('native candidate interval differs')
            if pdf[page.physical_page-1].get_text('text',sort=False,flags=195)!=page.native_text:
                raise ValueError('native replay differs')
    for crop in review.crops:
        checked(crop.source_image);checked(crop.asset)
        source_pix=pymupdf.Pixmap(crop.source_image.path)
        crop_pix=pymupdf.Pixmap(crop.asset.path)
        x0,y0,x1,y1=crop.pixel_box
        if not (0<=x0<x1<=source_pix.width and 0<=y0<y1<=source_pix.height):
            raise ValueError('crop bounds exceed source image')
        if (crop_pix.width,crop_pix.height,crop_pix.n)!=(x1-x0,y1-y0,source_pix.n):
            raise ValueError('crop pixel dimensions differ')
        original=source_pix.samples_mv
        expected=b''.join(original[y*source_pix.stride+x0*source_pix.n:y*source_pix.stride+x1*source_pix.n] for y in range(y0,y1))
        if expected!=crop_pix.samples:
            raise ValueError('crop pixels do not equal original page region')
    return {'status':'passed','physical_pages':[5,6,7,8],
            'native_bytes':sum(p.native_text_size_bytes for p in review.pages),
            'observations':sum(len(p.observations_in_native_order) for p in review.pages),
            'crops_verified':len(review.crops),'external_reports_consulted':False,
            'legal_currentness':'not_verified','source_or_candidate_modified':False}


if __name__=='__main__':
    print(json.dumps(validate_review(Path(__file__).with_name('SOURCE_REVIEW.json')),indent=2))
