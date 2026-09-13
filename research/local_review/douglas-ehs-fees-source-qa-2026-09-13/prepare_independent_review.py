"""Record additive observations after direct image review; preserve original QA bytes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys
BASE=Path(__file__).absolute().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from independent_models import Asset,Crop,RowCheck,Review,Manifest


def ref(name:str)->Asset:
    """Bind one retained file."""
    p=BASE/name;raw=p.read_bytes()
    return Asset(path=name,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def save(name:str,value:object)->None:
    """Write only a new typed record or schema."""
    p=BASE/name
    if p.exists():raise ValueError('Refusing overwrite')
    raw=(json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode()
    t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);os.replace(t,p)


def main()->None:
    """Freeze additive review observations and source-specific model copies."""
    q=json.loads((BASE/'SOURCE_QA.json').read_bytes())
    assert ref('SOURCE_QA.json').sha256=='69f962f1caa58f9fcf90970aed1a05d7ccdbba6bb39b69f78ff0f15012896df4'
    assert ref('PASS1_frozen.json').sha256=='e9db13cf88f77d2ad9bf2c4d0d3975eb162d58eff2afc8a0e85a4911eeb76a6f'
    assert ref('original.pdf').sha256=='35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687'
    existing=[]
    for p in BASE.rglob('*'):
        rel=p.relative_to(BASE).as_posix()
        if p.is_file() and (rel in {'SOURCE_QA.json','SOURCE_QA.schema.json','PASS1_frozen.json',
            'PASS1.schema.json','original.pdf','candidate-native.txt','page-0001.png',
            'build_douglas_ehs_qa.py','freeze_douglas_ehs_visual.py','acquisition-event.json',
            'reservation.json','public.headers','initial-inspection-crop.png',
            'blank-penalty-fees-crop.png','two-authority-captions-crop.png',
            'state-caption-crop.png','state-footnote-crop.png'} or rel.startswith('_SNAPSHOTS/')):
            existing.append(ref(rel))
    for script,target,start,end in [
        ('build_douglas_ehs_qa.py','qa_models.py','class Strict','\ndef asset'),
        ('freeze_douglas_ehs_visual.py','pass_models.py','class Row','\nCOUNTY =')]:
        body=(BASE/script).read_text();classes=body[body.index(start):body.index(end)]
        text='"""Model definitions copied from the unchanged original builder, without execution logic."""\nfrom __future__ import annotations\nfrom typing import Literal\nfrom pydantic import BaseModel,ConfigDict,Field\n\n'+classes+'\n'
        with (BASE/target).open('x') as out:out.write(text)
    clips=[('initial-inspection-crop.png',[205.,479.,605.,492.],
            'Root supplied exact settings after creation in the coordination message; this review independently reproduces exact PNG bytes. No original crop timestamp was supplied.',
            'STATE-12 fee-type wording, including source Intial'),
           ('blank-penalty-fees-crop.png',[590.,514.,732.,536.],
            'Exact clip and matrix from frozen build_douglas_ehs_qa.py.',
            'STATE-16/17 unit and blank fee positions'),
           ('two-authority-captions-crop.png',[45.,79.,731.,104.],
            'Exact clip and matrix from frozen build_douglas_ehs_qa.py.',
            'County caption and column headers only; despite the filename this crop does not contain the state caption'),
           ('state-caption-crop.png',[45.,359.,731.,383.],
            'Exact clip and matrix from frozen build_douglas_ehs_qa.py.',
            'Separate state caption and column headers'),
           ('state-footnote-crop.png',[45.,532.,731.,548.],
            'Exact clip and matrix from frozen build_douglas_ehs_qa.py.',
            'Complete retail-food note with literal fee $43 of each and Increases to $55 in 2025')]
    crops=[Crop(image=ref(n),physical_page=1,displayed_pdf_clip=r,matrix_scale=4,
                renderer='PyMuPDF 1.28.2',alpha=False,settings_provenance=p,
                original_creation_timestamp=None,visual_scope=s) for n,r,p,s in clips]
    a=json.loads((BASE/'acquisition-event.json').read_bytes())
    review=Review(schema_version=1,source_id='douglas-county-ehs-fees-dcr03',
        issuer='Douglas County Health Department',source_authority_id='CO-COUNTY-DOUGLAS',
        authority_scope='issuer identity only; row citations and state/county captions remain source claims',
        completed_at=datetime.now(timezone.utc),
        review_mode='candidate-aware independent source check; not blind or a new external review',
        source=ref('original.pdf'),frozen_pass1=ref('PASS1_frozen.json'),frozen_qa=ref('SOURCE_QA.json'),
        native=ref('candidate-native.txt'),original_full_image=ref('page-0001.png'),
        independent_poppler_image=ref('independent/poppler-page-0001.png'),
        original_input_files=sorted(existing,key=lambda x:x.path),
        reviewed_rows=[RowCheck(row_id=r['row_id'],source_qa_row_index=i,
            displayed_fields={c['field']:c['displayed_text'] for c in r['cells']},
            cell_positions_reviewed=5,physical_page=1,result='supported_at_review_resolution')
            for i,r in enumerate(q['rows'])],
        checked_context_ids=[c['context_id'] for c in q['contexts']],crops=crops,
        nonblank_native_cell_lines=218,blank_fee_positions=2,total_native_lines=232,total_native_bytes=4923,
        display_normalizations=['Native U+00A0 is shown as ordinary space in displayed_text.',
            'Native U+2010 is shown as ASCII hyphen in displayed_text.',
            'Leading/trailing whitespace is trimmed only in displayed_text; original native bytes are unchanged.'],
        additional_transcription_errata=[],observations=[
            'Directly inspected the complete original full-page PNG, all five supplied crops and a separate full Poppler render; all 44 rows and 220 cell positions agree with frozen QA at review resolution.',
            'The existing STATE-12 Initial to Intial erratum is supported. Frozen pass1 remains unchanged; the source and native bytes already say Intial.',
            'STATE-16/17 fee cells are visibly blank; STATE-01 separately prints $0.00. Blank is not zero.',
            'HACCP rows retain Hourly as unit and Up to $620 as the fee text; no amount or applicability calculation is made.',
            'County row codes 25-1-508, 25-4-1607, 25-1-107 and 25-1-109, and state penalty row codes 25-4-1610 and 25-4-1611 remain literal source citations.',
            'Both effective captions visually precede their own tables although their native lines follow both footnotes.',
            'The OWTS and retail-food notes retain their exact wording and star associations. The note $23/$20/$3 distribution is not turned into an added-fee calculation.',
            'The two-authority-captions-crop filename is imprecise: its actual pixels show only the county caption/header. The state caption is a separate crop.',
            'No additional transcription erratum was identified. Exact Unicode identity and unseen legal context are not certified.'],
        source_printed_dates=['2026 Fee','Effective November 1, 2025','Effective September 1, 2025',
                              'Increases to $55 in 2025.'],
        acquisition_started_at=datetime.fromisoformat(a['started_at'].replace('Z','+00:00')),
        acquisition_completed_at=datetime.fromisoformat(a['completed_at'].replace('Z','+00:00')),
        canonical_intake_performed_by_this_task=False,legal_currentness='not_verified',answer_safe=False,
        limitations=['This is an additive candidate-aware check by an Atlas subagent, not independent-model diversity or an external blind review.',
            'Only this one physical page was reviewed; no adopting instrument, amendment chain or current-law status was established.',
            'The image wordmark is recorded as text without certifying logo geometry, typography or exact spacing.',
            'The complete acquisition event includes references/hashes for private headers and omitted transport sidecars; the public custody wrapper is a separate package. No private-header original is copied here.',
            'Rendering and native/geometry replay check retained evidence reproducibility, not legal accuracy or applicability.',
            'The source remains pending canonical intake and has no monitoring or lookup enrollment by this task.'])
    save('INDEPENDENT_REVIEW.json',review.model_dump(mode='json'))
    save('INDEPENDENT_REVIEW.schema.json',Review.model_json_schema())
    save('FINAL_MANIFEST.schema.json',Manifest.model_json_schema())


if __name__=='__main__':main()
