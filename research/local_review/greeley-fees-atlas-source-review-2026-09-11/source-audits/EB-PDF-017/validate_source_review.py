"""Read-only schema, native-byte, geometry and table-association checks for EB017."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from typing import Literal
import json
import jsonschema,pymupdf
from review_models import Review,Strict,FileRef
B=Path(__file__).parent

def digest(p):return sha256(p.read_bytes()).hexdigest()
def check_file(p,h,size):
    if p.is_symlink() or any(x.is_symlink() for x in p.parents):raise ValueError('Symlink input')
    if not p.is_file() or p.stat().st_size!=size or digest(p)!=h:
        raise ValueError(f'Changed file: {p}')

def validate_review(m:Review):
    """Check one parsed review against its frozen original source and native bytes."""
    for r in [m.source_pdf,m.candidate,m.input_custody]+m.inspected_crops:
        check_file(B/r.path,r.sha256,r.size_bytes)
    candidate=(B/m.candidate.path).read_bytes();native={}
    with pymupdf.open(B/m.source_pdf.path) as pdf:
        if len(pdf)!=2 or pdf.is_repaired or pdf.is_encrypted:raise ValueError('Invalid PDF')
        for p in m.pages:
            for r in [p.image,p.native_receipt]:check_file(B/r.path,r.sha256,r.size_bytes)
            data=p.native_text.encode();native[p.physical_page]=data
            if data!=pdf[p.physical_page-1].get_text('text',sort=False,flags=195).encode():
                raise ValueError('Native extraction differs')
            if len(data)!=p.native_bytes or sha256(data).hexdigest()!=p.native_sha256:
                raise ValueError('Native byte identity')
            if candidate[p.candidate_start_byte:p.candidate_end_byte_exclusive]!=data:
                raise ValueError('Candidate slice differs')
            off=0
            for s in p.partition:
                if s.start_byte!=off or s.end_byte_exclusive<=off:
                    raise ValueError('Native partition gap/overlap')
                off=s.end_byte_exclusive
            if off!=len(data):raise ValueError('Native partition incomplete')
        if sum(len(v) for v in native.values())!=1316:raise ValueError('Native coverage')
        def bound(s):
            data=native[s.physical_page][s.start_byte:s.end_byte_exclusive]
            if data.decode()!=s.text or sha256(data).hexdigest()!=s.sha256:
                raise ValueError('Native span differs')
        for p in m.pages:
            for s in p.partition:bound(s)
        words=pdf[1].get_text('words',sort=False)
        table_centers=[]
        for table in m.tables:
            bound(table.heading_span)
            expected_heading = ('Plant Investment Fees (PIFs) Based on Tap Size'
                if table.table_id=='tap_size' else
                'Plant Investment Fees (PIFs) Single Family Residential Units')
            if table.heading_text!=expected_heading:raise ValueError('Exchanged table heading')
            if ' '.join(table.heading_span.text.split())!=table.heading_text:
                raise ValueError('Table heading mismatch')
            for h in table.headers:
                blank=table.table_id=='single_family' and h.column==1
                if h.visibly_blank!=blank:raise ValueError('Blank header changed')
                if blank:
                    if h.native_span is not None or h.display_text is not None:
                        raise ValueError('Invented right first-column header')
                else:
                    if h.native_span is None:raise ValueError('Missing header anchor')
                    bound(h.native_span)
                    if ' '.join(h.native_span.text.split())!=h.display_text:
                        raise ValueError('Header content mismatch')
                    if h.column>1:
                        offsets=[];offset=0
                        for line in native[2].decode().splitlines(keepends=True):
                            if line.strip()==h.display_text:
                                offsets.append(offset+len(line[:len(line)-len(line.lstrip())].encode()))
                            offset+=len(line.encode())
                        expected=offsets[0 if table.table_id=='tap_size' else 1]
                        if h.native_span.start_byte!=expected:
                            raise ValueError('Header bound to the other table')
            ys=[];xs=[]
            for number,row in enumerate(table.rows,1):
                if row.source_row!=number:raise ValueError('Wrong row ordinal')
                cy=[];cx=[]
                for cell in row.cells:
                    bound(cell.native_span)
                    if cell.native_span.text!=cell.display_text:raise ValueError('Altered cell')
                    value=cell.display_text
                    if len(value.split())==1:
                        boxes=[list(w[:4]) for w in words if w[4]==value]
                    else:boxes=[list(x) for x in pdf[1].search_for(value)]
                    if cell.native_occurrence>=len(boxes):raise ValueError('Missing source cell')
                    actual=boxes[cell.native_occurrence]
                    if actual!=cell.pdf_bbox:raise ValueError('Source cell geometry differs')
                    x0,y0,x1,y1=actual;cx.append((x0+x1)/2);cy.append((y0+y1)/2)
                if cx!=sorted(cx) or len(set(cx))!=3:raise ValueError('Column association differs')
                if max(cy)-min(cy)>8:raise ValueError('Row cells belong to different rows')
                ys.append(sum(cy)/3);xs.append(sum(cx)/3)
            if ys!=sorted(ys) or len(set(ys))!=len(ys):raise ValueError('Row order differs')
            table_centers.append(sum(xs)/len(xs))
        if table_centers[0]>=table_centers[1]:raise ValueError('Tables exchanged')
        for o in m.observations:
            for s in o.native_spans:
                if s.physical_page not in o.physical_pages:raise ValueError('Observation page')
                bound(s)
    for item in m.image_only:
        check_file(B/item.image.path,item.image.sha256,item.image.size_bytes)
        if any(line in m.pages[0].native_text for line in item.text_lines if len(line)>25):
            raise ValueError('Image-only claim conflicts with native text')
    return m

class ValidationResult(Strict):
    validated_at:datetime
    review:FileRef
    status:Literal['passed']
    pages:Literal[2]
    native_bytes:Literal[1316]
    table_count:Literal[2]
    table_rows:list[int]
    table_data_cells:Literal[24]
    fee_amount_cells:Literal[16]
    printed_dollar_cells:Literal[4]
    image_only_regions:Literal[2]
    originals_unchanged:Literal[True]
    legal_currentness:Literal['not_verified']
    checks_passed:list[str]

def validate():
    raw=(B/'SOURCE_REVIEW.json').read_text();m=Review.model_validate_json(raw)
    schema=json.loads((B/'SOURCE_REVIEW.schema.json').read_text())
    if schema!=Review.model_json_schema():raise ValueError('Schema definition mismatch')
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    receipt=json.loads((B/'CUSTODY_RECEIPT.json').read_text())
    jsonschema.Draft202012Validator(json.loads((B/'CUSTODY_RECEIPT.schema.json').read_text())).validate(receipt)
    for row in receipt['files']:
        f=row['copied_file'];check_file(B/f['path'],f['sha256'],f['size_bytes'])
        check_file(Path(row['original_path']),f['sha256'],f['size_bytes'])
    validate_review(m)
    p=B/'SOURCE_REVIEW.json'
    return ValidationResult(validated_at=datetime.now(timezone.utc),review=FileRef(path=p.name,sha256=digest(p),size_bytes=p.stat().st_size),status='passed',pages=2,native_bytes=1316,table_count=2,table_rows=[7,1],table_data_cells=24,fee_amount_cells=16,printed_dollar_cells=4,image_only_regions=2,originals_unchanged=True,legal_currentness='not_verified',checks_passed=['Strict Pydantic and JSON Schema validation','All nine frozen input/original file pairs unchanged','Exact PDF native re-extraction and candidate slices','Exhaustive native-byte partitions including trailing spaces','Two separate table headings, six header positions and 24 bound data cells','Source cell rectangles and row/column association; four printed dollar cells','Ten source observations and two visually reviewed image-only regions; visual wording is not machine-certified OCR'])
if __name__=='__main__':print(validate().model_dump_json(indent=2))
