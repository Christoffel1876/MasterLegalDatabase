"""Bind a frozen Atlas image transcription to immutable native text and visible table geometry."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Literal
import pymupdf
from pydantic import BaseModel, ConfigDict, Field

BASE=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12')
OUT=BASE/'douglas-ehs-source-qa'
DISC=BASE/'douglas-castle-rock-discovery'

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)

class Asset(Strict):
    path:str
    sha256:str
    size_bytes:int

class Cell(Strict):
    field:str
    displayed_text:str|None
    native_text:str|None
    native_line:int|None
    utf8_start:int|None
    utf8_end:int|None
    unrotated_bbox:list[float]|None
    displayed_bbox:list[float]|None
    blank_region:list[float]|None

class Row(Strict):
    row_id:str
    table:Literal['county','state']
    table_caption_id:str
    footnote_id:str|None
    cells:list[Cell]=Field(min_length=5,max_length=5)

class Context(Strict):
    context_id:str
    kind:Literal['caption','footnote','column_header','image_only_wordmark']
    text:str
    native_lines:list[int]
    unrotated_bbox:list[float]|None
    displayed_bbox:list[float]|None
    applies_to:list[str]

class Erratum(Strict):
    row_id:str
    field:str
    frozen_text:str
    image_supported_text:str
    evidence:Asset
    explanation:str

class QA(Strict):
    schema_version:Literal[1]=1
    source_id:Literal['douglas-county-ehs-fees-dcr03']='douglas-county-ehs-fees-dcr03'
    reviewer:Literal['Atlas']='Atlas'
    completed_at:str
    source:Asset
    source_url:str
    physical_pages:Literal[1]=1
    page_rotation_degrees:Literal[90]=90
    native:Asset
    full_image:Asset
    pass1:Asset
    rows:list[Row]=Field(min_length=44,max_length=44)
    contexts:list[Context]
    errata:list[Erratum]
    observations:list[str]
    limitations:list[str]
    review_status:Literal['source_checked_pending_intake']='source_checked_pending_intake'
    legal_currentness:Literal['not_verified']='not_verified'
    answer_safe:Literal[False]=False

def asset(path):
    data=path.read_bytes()
    return Asset(path=path.relative_to(OUT).as_posix(),sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))

def norm(text):
    return text.replace('\u00a0',' ').replace('\u2010','-').strip()

def main():
    assert not (OUT/'SOURCE_QA.json').exists()
    freeze=json.loads((OUT/'PASS1_frozen.json').read_bytes())
    assert asset(OUT/'PASS1_frozen.json').sha256=='e9db13cf88f77d2ad9bf2c4d0d3975eb162d58eff2afc8a0e85a4911eeb76a6f'
    for src,dst in [(DISC/'events/E017/body.bin','original.pdf'),
                    (DISC/'events/E017/event.json','acquisition-event.json'),
                    (DISC/'events/E017/public.headers','public.headers'),
                    (DISC/'events/E017/reservation.json','reservation.json'),
                    (DISC/'pdf-evidence/E017/page-0001.native.txt','candidate-native.txt'),
                    (DISC/'pdf-evidence/E017/page-0001.png','page-0001.png'),
                    (BASE/'freeze_douglas_ehs_visual.py','freeze_douglas_ehs_visual.py')]:
        shutil.copy2(src,OUT/dst)
    doc=pymupdf.open(OUT/'original.pdf');page=doc[0]
    native=(OUT/'candidate-native.txt').read_bytes()
    assert page.get_text('text',sort=False,flags=195).encode()==native
    lines=[]
    for block in page.get_text('dict',sort=False,flags=195)['blocks']:
        for line in block.get('lines',[]):
            text=''.join(s['text'] for s in line['spans'])
            lines.append((text,list(line['bbox'])))
    assert ('\n'.join(t for t,_ in lines)+'\n').encode()==native
    offsets=[];position=0
    for text,_ in lines:
        offsets.append((position,position+len(text.encode())))
        position+=len((text+'\n').encode())
    pos=5;rows=[]
    for frozen in freeze['rows']:
        if frozen['row_id']=='STATE-01':pos+=5
        cells=[]
        for field in ['authority','program','fee_type','unit','fee']:
            expected=frozen[field]
            if frozen['row_id']=='STATE-12' and field=='fee_type':
                expected=expected.replace('Initial','Intial')
            if expected is None:
                previous=cells[-1]['displayed_bbox']
                region=[685.0,previous[1]-0.5,728.0,previous[3]+0.5]
                # Native line boxes are unrotated; inspect the exact displayed blank fee region.
                assert not any(pymupdf.Rect(b)*page.rotation_matrix & pymupdf.Rect(region)
                               for _,b in lines)
                cells.append(dict(field=field,displayed_text=None,native_text=None,native_line=None,
                                  utf8_start=None,utf8_end=None,unrotated_bbox=None,
                                  displayed_bbox=None,blank_region=region))
            else:
                text,bbox=lines[pos]
                assert norm(text)==expected,(frozen['row_id'],field,text,expected)
                rotated=list(pymupdf.Rect(bbox)*page.rotation_matrix)
                start,end=offsets[pos]
                cells.append(dict(field=field,displayed_text=expected,native_text=text,
                                  native_line=pos+1,utf8_start=start,utf8_end=end,
                                  unrotated_bbox=bbox,displayed_bbox=rotated,blank_region=None))
                pos+=1
        ys=[c['displayed_bbox'][1] for c in cells if c['displayed_bbox']]
        assert max(ys)-min(ys)<0.02
        row_id=frozen['row_id']
        footnote='COUNTY-OWTS-NOTE' if row_id in ['COUNTY-18','COUNTY-19','COUNTY-20'] else (
            'STATE-RETAIL-NOTE' if frozen['fee_type'].endswith('*') else None)
        rows.append(Row(row_id=row_id,table=frozen['table'],table_caption_id=frozen['table'].upper()+'-CAPTION',footnote_id=footnote,cells=cells))
    assert pos==len(lines)-4
    contexts=[]
    for cid,kind,index,applies in [
        ('COUNTY-OWTS-NOTE','footnote',pos,['COUNTY-18','COUNTY-19','COUNTY-20']),
        ('STATE-RETAIL-NOTE','footnote',pos+1,[r.row_id for r in rows if r.footnote_id=='STATE-RETAIL-NOTE']),
        ('COUNTY-CAPTION','caption',pos+2,[r.row_id for r in rows if r.table=='county']),
        ('STATE-CAPTION','caption',pos+3,[r.row_id for r in rows if r.table=='state'])]:
        text,bbox=lines[index]
        contexts.append(Context(context_id=cid,kind=kind,text=text,native_lines=[index+1],
                                unrotated_bbox=bbox,displayed_bbox=list(pymupdf.Rect(bbox)*page.rotation_matrix),applies_to=applies))
    for table,index in [('county',0),('state',140)]:
        # First table is five column headings plus 27 complete five-cell rows.
        text=' | '.join(t for t,_ in lines[index:index+5])
        assert norm(text).startswith('Authority | Program')
        contexts.append(Context(context_id=table.upper()+'-HEADERS',kind='column_header',text=text,
                                native_lines=list(range(index+1,index+6)),unrotated_bbox=None,
                                displayed_bbox=None,applies_to=[r.row_id for r in rows if r.table==table]))
    contexts.append(Context(context_id='WORDMARK',kind='image_only_wordmark',text=freeze['headings'][0],
                            native_lines=[],unrotated_bbox=None,displayed_bbox=None,applies_to=[r.row_id for r in rows]))
    for name,clip in [('blank-penalty-fees-crop.png',[590,514,732,536]),
                      ('two-authority-captions-crop.png',[45,79,731,104]),
                      ('state-caption-crop.png',[45,359,731,383]),
                      ('state-footnote-crop.png',[45,532,731,548])]:
        page.get_pixmap(matrix=pymupdf.Matrix(4,4),clip=pymupdf.Rect(clip)).save(OUT/name)
    qa=QA(completed_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
          source=asset(OUT/'original.pdf'),source_url='https://www.douglasco.gov/documents/fee-schedule.pdf/',
          native=asset(OUT/'candidate-native.txt'),full_image=asset(OUT/'page-0001.png'),
          pass1=asset(OUT/'PASS1_frozen.json'),rows=rows,contexts=contexts,
          errata=[Erratum(row_id='STATE-12',field='fee_type',
                         frozen_text='Change of Ownership or Site Evaluation (Initial Inspection)',
                         image_supported_text='Change of Ownership or Site Evaluation (Intial Inspection)',
                         evidence=asset(OUT/'initial-inspection-crop.png'),
                         explanation='Direct 4x crop confirms source prints Intial. Frozen pass1 is unchanged; native extraction reproduces source typo faithfully.')],
          observations=['Native extraction places both green authority/effective-date captions after both tables and both footnotes; their visual table associations are restored explicitly.',
                        'Native wordmark is absent; image-only publisher wordmark retained as context.',
                        '218 nonblank native cell lines match visual transcription after explicit NBSP-to-space and U+2010-to-hyphen display normalization, with one preserved pass1 erratum.',
                        'Two penalty fee cells are visibly blank, with no native line bounding boxes in their displayed fee regions. Blank is not zero.',
                        'Source has 2026 fee columns but November 1, 2025 county caption and September 1, 2025 state caption.',
                        'The retail food footnote says fee $43 of each and Increases to $55 in 2025. These awkward/source-date statements are preserved.',
                        'Footnote-star linkage and complete notes are retained; the OWTS note describes a $23 assessment with $20/$3 distribution without making an additional-fee calculation.'],
          limitations=['Atlas source-first visual pass knew the discovery summary; not a fully blind independent review and no Grok review occurred.',
                       'All 44 rows and their 220 displayed cell positions reviewed on one physical page; exact Unicode glyph identity from visual appearance not certified.',
                       'Geometric/native reproducibility validates associations, not adoption or current legal effect.',
                       'This source is not canonically intaken, enrolled in daily monitoring or exposed through the production lookup.',
                       'Acquisition event refers to locally retained private headers; this QA package carries the public derivative only. Public custody wrapper separately records original omission.'])
    (OUT/'SOURCE_QA.json').write_text(qa.model_dump_json(indent=2)+'\n')
    (OUT/'SOURCE_QA.schema.json').write_text(json.dumps(QA.model_json_schema(),indent=2)+'\n')
    shutil.copy2(__file__,OUT/'build_douglas_ehs_qa.py')
    print(json.dumps({'rows':len(rows),'native_lines':len(lines),'source_qa_sha256':asset(OUT/'SOURCE_QA.json').sha256}))

if __name__=='__main__':main()
