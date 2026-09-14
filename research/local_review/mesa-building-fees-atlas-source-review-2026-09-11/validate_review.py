"""Read-only byte, full-page, cell-grid and condition-association validator."""
from __future__ import annotations
from pathlib import Path
import copy,hashlib,json,sys
import pymupdf
import jsonschema
from review_models import Asset,Inventory,Review,Layout,Preparation,Span
B=Path(__file__).resolve().parent
SHA='421aa92efa159b484a091f1ade3589f6abb8a060bb880ec0c0a09e0472e4b9e7'
def require(ok,msg):
    if not ok:raise ValueError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def ordinary(rel):
    Asset(path=rel,sha256='0'*64,bytes=0)
    p=B/rel
    for q in [p,*p.parents]:require(not q.is_symlink(),'symlink not allowed')
    require(p.is_file(),'missing ordinary file '+rel);return p

def data(a):
    b=ordinary(a.path).read_bytes();require(len(b)==a.bytes and digest(b)==a.sha256,'file identity mismatch '+a.path);return b

def each_span(x):
    if isinstance(x,dict):
        if set(x)=={'physical_page','start','end','exact_text','sha256'}:yield Span.model_validate(x)
        else:
            for v in x.values():yield from each_span(v)
    elif isinstance(x,list):
        for v in x:yield from each_span(v)

def validate_content(r,doc,native,layouts):
    require(r.source.sha256==SHA,'wrong source')
    require(len(r.tables)==7 and [len(t.rows) for t in r.tables]==[6,8,14,5,9,19,11],'table/row truncation')
    require(sum(x.kind=='body' for t in r.tables for x in t.rows)==64,'body row accounting')
    require(len(r.contexts)==11 and len(r.observations)==11,'missing context or source qualification')
    for s in each_span(r.model_dump()):require(native[s.physical_page][s.start:s.end]==s.exact_text.encode(),'native span mismatch')
    for p in r.pages:
        off=0
        geometric=[]
        for block in layouts[p.physical_page]['blocks']:
            for line in block.get('lines',[]):geometric.append((''.join(s['text'] for s in line['spans'])+'\n',tuple(line['bbox'])))
        require(len(geometric)==len(p.lines),'native line omission')
        for i,line in enumerate(p.lines):
            require(line.line==i+1 and line.span.start==off and line.span.physical_page==p.physical_page,'native line ordering')
            require((line.span.exact_text,line.bbox)==geometric[i],'line text or geometry mismatch')
            off=line.span.end
        require(off==len(native[p.physical_page]),'native page truncation')
    # Re-detect the PDF border grid, and bind each cell to actual source row/column geometry.
    for n in range(1,6):
        found=doc[n-1].find_tables().tables;recorded=[t for t in r.tables if t.physical_page==n]
        require(len(found)==len(recorded),'table omission')
        for ti,(raw,t) in enumerate(zip(found,recorded),1):
            require(t.id==f'P{n}-T{ti}','table identity')
            require(raw.extract()==t.extracted_matrix,'table matrix changed')
            original={(ri,ci):tuple(box) for ri,row in enumerate(raw.rows) for ci,box in enumerate(row.cells) if box is not None}
            require(len(original)==len(t.cells),'cell missing')
            for c in t.cells:
                require(original[(c.anchor_row,c.anchor_column)]==c.bbox,'wrong physical cell')
                require(c.id==f'{t.id}-R{c.anchor_row:02d}C{c.anchor_column:02d}','cell identity')
                require(c.geometric_extraction==(t.extracted_matrix[c.anchor_row][c.anchor_column] or ''),'cell text changed')
                evidence=[]
                for line in r.pages[n-1].lines:
                    x0,y0,x1,y1=line.bbox;cx=(x0+x1)/2;cy=(y0+y1)/2
                    if c.bbox[0]-.1<=cx<=c.bbox[2]+.1 and c.bbox[1]-.1<=cy<=c.bbox[3]+.1:evidence.append(line.span)
                require(c.native_evidence==evidence,'cell native evidence escaped its source position')
                require(t.x_grid[c.anchor_column]==c.bbox[0] and t.x_grid[c.anchor_column+c.column_span]==c.bbox[2],'x grid binding')
                require(t.y_grid[c.anchor_row]==c.bbox[1] and t.y_grid[c.anchor_row+c.row_span]==c.bbox[3],'y grid binding')
            cs={c.id:c for c in t.cells}
            for row in t.rows:
                require(row.id==f'{t.id}-R{row.row_index:02d}','row identity')
                if row.fee_number_as_printed is not None:require(row.fee_number_as_printed==cs[row.cell_ids[0]].geometric_extraction,'lost merged fee parent')
    # Every nonblank native line must occur in cell evidence or context; no silent dropped notes.
    accounted=[s for t in r.tables for c in t.cells for s in c.native_evidence]+[s for c in r.contexts for s in c.evidence]
    for p in r.pages:
        for l in p.lines:
            if l.span.exact_text.strip():require(any(s.physical_page==p.physical_page and s.start<=l.span.start and s.end>=l.span.end for s in accounted),'unaccounted native line')
    ts={t.id:t for t in r.tables}
    required={'P1-T1':{'P1-PARENT'},'P2-T2':{'P3-FOOTNOTES'},'P3-T1':{'P3-FOOTNOTES'},'P3-T2':{'P3-ROUNDING','P3-VALUATION'},'P4-T1':{'P3-VALUATION','P5-VALUATION'},'P5-T1':{'P3-VALUATION','P5-VALUATION'}}
    for tid,ids in required.items():require(ids<=set(ts[tid].qualification_ids),'lost footnote/condition')
    require('P1-DISCRETION' in ts['P1-T1'].rows[2].qualification_ids,'lost commercial maximum condition')
    require(len(ts['P3-T2'].rows[1:])==8,'valuation tier count')
    matrix=[t for t in r.tables if t.physical_page in (4,5)]
    require(all(t.column_meanings==['Group','IA','IB','IIA','IIB','IIIA','IIIB','IV','VA','VB'] for t in matrix),'matrix column order')
    require(sum(len(t.rows)-2 for t in matrix)==26,'matrix body count')
    actual_np={(t.id,ri,ci) for t in matrix for ri,row in enumerate(t.extracted_matrix) for ci,v in enumerate(row) if v=='NP'}
    require(actual_np=={('P4-T1',13,9),('P4-T1',17,6),('P4-T1',17,9)},'wrong NP associations')
    require(ts['P4-T1'].extracted_matrix[4][6]=='99.751','nightclub value changed')
    require(ts['P5-T1'].extracted_matrix[2][0]=='1-4 Institutional, day\ncare facilities','source label changed')
    require(ts['P3-T2'].extracted_matrix[7][0]=='$500,00.01 to $1,000,000','source tier repaired')
    require(data(r.candidate)==b''.join(native[p] for p in range(1,6)),'candidate order or bytes changed')

def validate():
    inv=Inventory.model_validate_json(ordinary('evidence-manifest.json').read_bytes())
    actual={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()}
    require(actual=={a.path for a in inv.files}|{'evidence-manifest.json'},'inventory omission or extra')
    for a in inv.files:data(a)
    r=Review.model_validate_json(ordinary('SOURCE_REVIEW.json').read_bytes())
    schema=json.loads(ordinary('SOURCE_REVIEW.schema.json').read_text());require(schema==Review.model_json_schema(),'schema drift');jsonschema.Draft202012Validator(schema).validate(r.model_dump(mode='json'))
    prep=Preparation.model_validate_json(ordinary('PREPARATION.json').read_bytes());require(prep.source==r.source,'preparation source')
    for a in prep.custody_files:data(a)
    receipt=json.loads(ordinary('custody/E007-event.json').read_bytes());metrics=json.loads(ordinary('custody/E007-curl-metadata.json').read_bytes());require(receipt['body_sha256']==SHA and receipt['body_bytes']==r.source.bytes,'original response binding');require(receipt['requested_url']==r.source_url and receipt['final_url']==r.final_url,'URL binding');require(receipt['completed_at']==r.acquired_at.isoformat().replace('+00:00','Z'),'receipt time');require(metrics['ssl_verify_result']==0 and metrics['num_redirects']==0 and metrics['http_code']==200,'TLS/HTTP/redirect');links=json.loads(ordinary('custody/E006-parsed.json').read_text())['links'];require({'url':r.source_url,'label':'Adopted Fee Schedule (PDF)'} in links,'official referral')
    source=data(r.source);require(source.startswith(b'%PDF-') and source.rstrip().endswith(b'%%EOF'),'PDF boundary');doc=pymupdf.open(stream=source,filetype='pdf');require(len(doc)==5 and not doc.is_repaired and not doc.is_encrypted,'PDF structure');require(pymupdf.VersionBind==r.engine_version,'recorded engine required for exact reproduction')
    native={};layouts={}
    for p in r.pages:
        n=p.physical_page;native[n]=data(p.native);require(doc[n-1].get_text('text',flags=195,sort=False).encode()==native[n],'native extraction replay');lay=Layout.model_validate_json(data(p.layout));require(lay.source_sha256==SHA and lay.page==n and lay.native_sha256==p.native.sha256,'layout bindings');layouts[n]=lay.text_dict;require(json.loads(json.dumps(doc[n-1].get_text('dict',flags=195,sort=False)))==lay.text_dict,'layout replay');require(doc[n-1].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).tobytes('png')==data(p.image),'image replay')
    for c in r.crops:require(doc[c.physical_page-1].get_pixmap(matrix=pymupdf.Matrix(c.scale,c.scale),clip=pymupdf.Rect(c.clip),alpha=False).tobytes('png')==data(c.image),'crop replay')
    validate_content(r,doc,native,layouts)
    # Focused in-memory tampering checks; no synthetic legal examples or source mutation.
    changes=[]
    def negative(label,change):
        value=r.model_dump(mode='json');change(value)
        try:modified=Review.model_validate_json(json.dumps(value));validate_content(modified,doc,native,layouts)
        except (ValueError,KeyError,IndexError):changes.append(label)
        else:raise ValueError('bad evidence accepted: '+label)
    negative('missing_page',lambda x:x['pages'].pop())
    negative('missing_tier',lambda x:x['tables'][4]['rows'].pop())
    negative('wrong_matrix_column',lambda x:x['tables'][5]['column_meanings'].reverse())
    negative('changed_native_amount',lambda x:x['tables'][5]['cells'][0]['native_evidence'][0].update(exact_text='changed'))
    negative('lost_rounding',lambda x:x['tables'][4].update(qualification_ids=[]))
    negative('lost_parent_fee_number',lambda x:x['tables'][1]['rows'][6].update(fee_number_as_printed='7'))
    negative('changed_source',lambda x:x['source'].update(sha256='0'*64))
    negative('currentness_promotion',lambda x:x.update(legal_currentness='verified'))
    sys.stdout.write(json.dumps({'passed':True,'source_sha256':SHA,'pages':5,'native_bytes':r.native_bytes,'native_changes':0,'tables':7,'body_rows':64,'valuation_tiers':8,'matrix_rows':26,'matrix_value_cells':234,'physical_cells':396,'grid_positions':423,'native_lines':540,'contexts':11,'observations':11,'negative_checks_rejected':changes,'status':'source association review; no legal-currentness or adoption certification'},indent=2)+'\n')
if __name__=='__main__':validate()
