"""Portable read-only verification of the frozen Douglas table and additive source check."""
from __future__ import annotations
import argparse
import hashlib
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import jsonschema
import pymupdf
from PIL import Image

sys.dont_write_bytecode=True
BASE=Path(__file__).absolute().parent
sys.path.insert(0,str(BASE))
from independent_models import Asset,Manifest,Review
from qa_models import QA
from pass_models import Transcript

SOURCE_SHA='35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687'
QA_SHA='69f962f1caa58f9fcf90970aed1a05d7ccdbba6bb39b69f78ff0f15012896df4'
PASS1_SHA='e9db13cf88f77d2ad9bf2c4d0d3975eb162d58eff2afc8a0e85a4911eeb76a6f'
FIELDS=['authority','program','fee_type','unit','fee']
IDS=[f'COUNTY-{i:02}' for i in range(1,28)]+[f'STATE-{i:02}' for i in range(1,18)]


def require(condition:bool,message:str)->None:
    """Fail closed with a concrete evidence error."""
    if not condition:raise ValueError(message)


def safe(root:Path,relative:str)->Path:
    """Reject lexical escape, symlink ancestors and nonordinary evidence files."""
    rel=Path(relative)
    require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe evidence path')
    path=root/rel
    require(not any(p.is_symlink() for p in (path,*path.parents)),'Symlink evidence path')
    require(path.is_file(),'Missing ordinary evidence file')
    return path


def content(root:Path,item)->bytes:
    """Check the exact file hash and size before interpreting it."""
    path=safe(root,item.path)
    with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    require(sha==item.sha256 and path.stat().st_size==item.size_bytes,'Evidence hash/size mismatch')
    return path.read_bytes()


def equal_box(left:list|None,right:list|None)->bool:
    """Compare the frozen native/rotated point coordinates at a tight numeric tolerance."""
    if left is None or right is None:return left==right
    return len(left)==len(right)==4 and all(abs(a-b)<0.00001 for a,b in zip(left,right))


def norm(text:str)->str:
    """Only the original display normalizations; never change candidate bytes."""
    return text.replace('\u00a0',' ').replace('\u2010','-').strip()


def validate_qa(root:Path,qa:QA,freeze:Transcript,review:Review,rerender:bool=False)->dict:
    """Replay every native row/cell/context association and all declared source geometry."""
    pdf=content(root,review.source);native=content(root,review.native)
    require(hashlib.sha256(pdf).hexdigest()==SOURCE_SHA,'Wrong PDF source')
    require(pdf.startswith(b'%PDF-') and b'%%EOF' in pdf[-1024:],'PDF framing mismatch')
    require(qa.source.model_dump()==review.source.model_dump(),'QA source binding mismatch')
    require(qa.native.model_dump()==review.native.model_dump(),'QA native binding mismatch')
    require(qa.full_image.model_dump()==review.original_full_image.model_dump(),'QA image binding mismatch')
    require(qa.pass1.model_dump()==review.frozen_pass1.model_dump(),'QA pass1 binding mismatch')
    require(freeze.source_sha256==SOURCE_SHA and freeze.image_sha256==review.original_full_image.sha256,
            'Frozen visual source identity mismatch')
    require([r.row_id for r in qa.rows]==[r.row_id for r in freeze.rows]==IDS,'Row selection mismatch')
    require([r.row_id for r in review.reviewed_rows]==IDS,'Independent row selection mismatch')
    require(len(qa.errata)==1 and not review.additional_transcription_errata,'Unexpected errata')
    error=qa.errata[0]
    require(error.row_id=='STATE-12' and error.field=='fee_type' and
            error.frozen_text=='Change of Ownership or Site Evaluation (Initial Inspection)' and
            error.image_supported_text=='Change of Ownership or Site Evaluation (Intial Inspection)',
            'Source typo/erratum mismatch')
    content(root,error.evidence)
    for image in [review.original_full_image,review.independent_poppler_image]:
        content(root,image)
        with Image.open(safe(root,image.path)) as loaded:
            require(loaded.size==(1650,1275) and loaded.format=='PNG','Full image cropped or invalid')
    with pymupdf.open(stream=pdf,filetype='pdf') as document:
        require(len(document)==1 and not document.is_repaired and not document.is_encrypted,
                'Invalid source PDF structure')
        page=document[0]
        require(page.rotation==qa.page_rotation_degrees==90 and list(page.rect)==[0,0,792,612],
                'Source rotation/page bounds mismatch')
        require(list(page.mediabox)==[0,0,612,792],'Unrotated page bounds mismatch')
        require(page.get_text('text',sort=False,flags=195).encode()==native,'Native replay mismatch')
        lines=[]
        for block in page.get_text('dict',sort=False,flags=195)['blocks']:
            for line in block.get('lines',[]):
                lines.append((''.join(span['text'] for span in line['spans']),list(line['bbox'])))
        require(len(lines)==232 and len(native)==4923,'Native completeness mismatch')
        require(('\n'.join(t for t,_ in lines)+'\n').encode()==native,'Native line serialization mismatch')
        offsets=[];cursor=0
        for text,_ in lines:
            offsets.append((cursor,cursor+len(text.encode())))
            cursor+=len((text+'\n').encode())
        used=[];blank_count=0;position=5;row_ys={}
        for index,(row,frozen,checked) in enumerate(zip(qa.rows,freeze.rows,review.reviewed_rows,strict=True)):
            require(row.table==frozen.table and row.table_caption_id==row.table.upper()+'-CAPTION',
                    'Wrong table/caption association')
            require([c.field for c in row.cells]==FIELDS,'Duplicate or reordered cell fields')
            require(checked.source_qa_row_index==index and checked.displayed_fields==
                    {c.field:c.displayed_text for c in row.cells},'Independent row binding mismatch')
            if row.row_id=='STATE-01':position+=5
            ys=[]
            for cell in row.cells:
                expected=getattr(frozen,cell.field)
                if row.row_id=='STATE-12' and cell.field=='fee_type':
                    expected=error.image_supported_text
                require(cell.displayed_text==expected,'Displayed cell/frozen transcription mismatch')
                if expected is None:
                    require(row.row_id in ['STATE-16','STATE-17'] and cell.field=='fee',
                            'Unexpected blank cell')
                    require(all(getattr(cell,name) is None for name in ['native_text','native_line',
                        'utf8_start','utf8_end','unrotated_bbox','displayed_bbox']),
                        'Blank converted to text, zero or fabricated native evidence')
                    prior=row.cells[-2].displayed_bbox
                    expected_region=[685.,prior[1]-0.5,728.,prior[3]+0.5]
                    require(equal_box(cell.blank_region,expected_region),'Wrong blank cell region')
                    region=pymupdf.Rect(expected_region)
                    require(not any(not (pymupdf.Rect(b)*page.rotation_matrix & region).is_empty
                                    for _,b in lines),'Native text overlaps declared blank fee region')
                    blank_count+=1
                    continue
                text,bbox=lines[position];start,end=offsets[position]
                require(cell.native_line==position+1 and cell.native_text==text,
                        'Wrong native line/cell association')
                require(cell.utf8_start==start and cell.utf8_end==end and
                        native[start:end].decode()==text,'Wrong UTF-8 cell offsets')
                require(norm(text)==expected and cell.blank_region is None,'Display normalization mismatch')
                rotated=list(pymupdf.Rect(bbox)*page.rotation_matrix)
                require(equal_box(cell.unrotated_bbox,bbox) and equal_box(cell.displayed_bbox,rotated),
                        'Native/display geometry mismatch')
                ys.append(rotated[1]);used.append(position+1);position+=1
            require(max(ys)-min(ys)<0.02,'Cells assigned across visual rows')
            row_ys[row.row_id]=min(ys)
            expected_note='COUNTY-OWTS-NOTE' if row.row_id in ['COUNTY-18','COUNTY-19','COUNTY-20'] else (
                'STATE-RETAIL-NOTE' if frozen.fee_type.endswith('*') else None)
            require(row.footnote_id==expected_note,'Wrong row footnote link')
        require(position==228 and len(used)==218 and blank_count==2,'Cell completeness mismatch')
        contexts={c.context_id:c for c in qa.contexts}
        context_ids=['COUNTY-OWTS-NOTE','STATE-RETAIL-NOTE','COUNTY-CAPTION','STATE-CAPTION',
                     'COUNTY-HEADERS','STATE-HEADERS','WORDMARK']
        require(list(contexts)==context_ids and len(qa.contexts)==7 and
                review.checked_context_ids==context_ids,'Context selection mismatch')
        for cid,idx,kind,scope in [
            ('COUNTY-OWTS-NOTE',228,'footnote',['COUNTY-18','COUNTY-19','COUNTY-20']),
            ('STATE-RETAIL-NOTE',229,'footnote',[f'STATE-{i:02}' for i in range(2,12)]),
            ('COUNTY-CAPTION',230,'caption',IDS[:27]),
            ('STATE-CAPTION',231,'caption',IDS[27:])]:
            ctx=contexts[cid];text,bbox=lines[idx]
            require(ctx.kind==kind and ctx.native_lines==[idx+1] and ctx.text==text and
                    ctx.applies_to==scope,'Context wording/line/scope mismatch')
            require(equal_box(ctx.unrotated_bbox,bbox) and
                    equal_box(ctx.displayed_bbox,list(pymupdf.Rect(bbox)*page.rotation_matrix)),
                    'Context geometry mismatch')
            used.append(idx+1)
        for cid,idx,scope in [('COUNTY-HEADERS',0,IDS[:27]),('STATE-HEADERS',140,IDS[27:])]:
            ctx=contexts[cid];expected=' | '.join(t for t,_ in lines[idx:idx+5])
            require(ctx.kind=='column_header' and ctx.native_lines==list(range(idx+1,idx+6)) and
                    ctx.text==expected and ctx.applies_to==scope and ctx.unrotated_bbox is None and
                    ctx.displayed_bbox is None,'Column header association mismatch')
            require(' '.join(norm(ctx.text).split())==freeze.headings[3],'Visible header wording mismatch')
            used.extend(range(idx+1,idx+6))
        wordmark=contexts['WORDMARK']
        require(wordmark.kind=='image_only_wordmark' and wordmark.text==freeze.headings[0] and
                not wordmark.native_lines and wordmark.applies_to==IDS and
                wordmark.unrotated_bbox is None and wordmark.displayed_bbox is None,
                'Wordmark/native status mismatch')
        require(norm(contexts['COUNTY-CAPTION'].text)==freeze.headings[1] and
                norm(contexts['STATE-CAPTION'].text)==freeze.headings[2],
                'County/state effective caption swap')
        require([norm(contexts[cid].text) for cid in ['COUNTY-OWTS-NOTE','STATE-RETAIL-NOTE']]
                ==freeze.footnotes,'Full footnote wording mismatch')
        require(sorted(used)==list(range(1,233)),'Unbound or duplicate native lines')
        for table,first,last in [('COUNTY','COUNTY-01','COUNTY-27'),('STATE','STATE-01','STATE-17')]:
            require(contexts[table+'-CAPTION'].displayed_bbox[3]<row_ys[first]<row_ys[last],
                    'Caption does not precede its visual table')
        for crop in review.crops:
            data=content(root,crop.image)
            pix=page.get_pixmap(matrix=pymupdf.Matrix(4,4),clip=pymupdf.Rect(crop.displayed_pdf_clip))
            require(pix.tobytes('png')==data,'Crop pixels/settings mismatch')
        require(page.get_pixmap(dpi=150,alpha=False).tobytes('png')==
                content(root,review.original_full_image),'Original full render mismatch')
    if rerender:
        executable=shutil.which('pdftoppm')
        require(executable is not None,'Poppler unavailable for requested replay')
        with tempfile.TemporaryDirectory(prefix='douglas-qa-render-') as temp:
            prefix=Path(temp)/'page'
            result=subprocess.run([executable,'-r','150','-f','1','-l','1','-singlefile','-png',
                str(safe(root,review.source.path)),str(prefix)],capture_output=True,timeout=30)
            require(result.returncode==0,'Poppler replay failed')
            require(prefix.with_suffix('.png').read_bytes()==content(root,review.independent_poppler_image),
                    'Independent Poppler render mismatch')
    acquisition=json.loads(safe(root,'acquisition-event.json').read_bytes())
    require(acquisition['event_id']=='E017' and acquisition['body']['sha256']==SOURCE_SHA and
            acquisition['body']['bytes']==len(pdf) and acquisition['curl_exit']==0 and
            acquisition['http_status']==200 and acquisition['final_url']==qa.source_url,
            'Acquisition body/source binding mismatch')
    return {'status':'verified_source_qa_pending_intake','physical_pages':1,'rows':44,'cells':220,
            'native_cell_lines':218,'blank_fee_cells':2,'native_lines':232,'native_bytes':4923,
            'original_render_replayed':True,'crops_replayed':5,'poppler_replayed':rerender,
            'legal_currentness':'not_verified','answer_safe':False}


def verify(root:Path=BASE,rerender:bool=False)->dict:
    """Verify the closed inventory, strict schemas, pinned inputs and source associations."""
    manifest=Manifest.model_validate_json(safe(root,'FINAL_MANIFEST.json').read_bytes())
    names=[a.path for a in manifest.files]
    require(names==sorted(set(names)),'Duplicate or unordered inventory')
    actual=set()
    for p in root.rglob('*'):
        require(not p.is_symlink() and (p.is_dir() or p.is_file()),'Nonordinary package member')
        if p.is_file() and p.relative_to(root).as_posix()!='FINAL_MANIFEST.json':
            actual.add(p.relative_to(root).as_posix())
    require(actual==set(names),'Closed package membership mismatch')
    indexed={a.path:a for a in manifest.files}
    for asset in manifest.files:content(root,asset)
    require(indexed['SOURCE_QA.json'].sha256==QA_SHA and
            indexed['PASS1_frozen.json'].sha256==PASS1_SHA,'Frozen QA/pass1 changed')
    qa=QA.model_validate_json(safe(root,'SOURCE_QA.json').read_bytes())
    freeze=Transcript.model_validate_json(safe(root,'PASS1_frozen.json').read_bytes())
    review=Review.model_validate_json(safe(root,'INDEPENDENT_REVIEW.json').read_bytes())
    for name,model in [('SOURCE_QA',QA),('PASS1',Transcript),
                       ('INDEPENDENT_REVIEW',Review),('FINAL_MANIFEST',Manifest)]:
        filename='PASS1_frozen.json' if name=='PASS1' else name+'.json'
        schema=json.loads(safe(root,name+'.schema.json').read_bytes())
        require(schema==model.model_json_schema(),'Schema/model mismatch')
        jsonschema.Draft202012Validator(schema).validate(json.loads(safe(root,filename).read_bytes()))
    for original in review.original_input_files:
        require(indexed.get(original.path)==original,'Original input preimage changed')
    require(review.frozen_qa==indexed['SOURCE_QA.json'] and
            review.frozen_pass1==indexed['PASS1_frozen.json'],'Independent frozen input mismatch')
    return validate_qa(root,qa,freeze,review,rerender)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rerender',action='store_true',help='Also replay independent Poppler PNG')
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(message)s')
    logging.info('%s',json.dumps(verify(rerender=args.rerender),indent=2))
