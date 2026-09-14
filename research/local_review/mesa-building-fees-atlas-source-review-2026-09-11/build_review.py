"""Assemble the Atlas source review from the already preserved five-page PDF."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
import pymupdf
from review_models import *
B=Path(__file__).resolve().parent
SOURCE_SHA='421aa92efa159b484a091f1ade3589f6abb8a060bb880ec0c0a09e0472e4b9e7'
def sha(b):return hashlib.sha256(b).hexdigest()
def asset(p):
    b=p.read_bytes();return Asset(path=p.relative_to(B).as_posix(),sha256=sha(b),bytes=len(b))
def save(p,m):
    if p.exists():raise FileExistsError(p)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(m.model_dump_json(indent=2)+'\n');os.replace(tmp,p)
def span(n,start,text):return Span(physical_page=n,start=start,end=start+len(text.encode()),exact_text=text,sha256=sha(text.encode()))
source=asset(B/'source/mesa-building-fees-exhibit-a.pdf');assert source.sha256==SOURCE_SHA
receipt=json.loads((B/'custody/E007-event.json').read_text())
start=datetime.now(timezone.utc)
prep=Preparation(source=source,prepared_at=start,source_url=receipt['requested_url'],acquired_at=receipt['completed_at'],custody_files=[asset(p) for p in sorted((B/'custody').iterdir())],mode='candidate_aware_internal_review',note='Exact source bytes/response custody preserved before this review. Source first partly viewed in prior directed-gap audit; this is candidate-aware full five-page QA, not blind or external verification. Retained earlier audit describes its earlier narrower scope and is not rewritten.')
save(B/'PREPARATION.json',prep)
doc=pymupdf.open(B/source.path);pages=[];tables=[];contexts=[];outside={};text_by_page={}
header_counts=[[1],[1,1],[0,1],[2],[2]]
titles=[['Table 1A- Mesa County Building Department Fees'],['Fees Related to Administration/Inspections','Project Specific Permit Fees'],['Project Specific Permit Fees (continued from physical page 2)','Table 2- Mesa County Permit Fee Schedule'],['Table 3A- Building Valuation Data'],['Table 3A- Building Valuation Data (continued)']]
for n,page in enumerate(doc,1):
    text=page.get_text('text',flags=195,sort=False);text_by_page[n]=text
    assert (B/f'native/page-{n:04d}.txt').read_bytes()==text.encode()
    layout=page.get_text('dict',flags=195,sort=False);lines=[];offset=0
    for block in layout['blocks']:
        for line in block.get('lines',[]):
            line_text=''.join(s['text'] for s in line['spans'])+'\n'
            lines.append(NativeLine(line=len(lines)+1,bbox=line['bbox'],span=span(n,offset,line_text)));offset+=len(line_text.encode())
    assert ''.join(x.span.exact_text for x in lines)==text
    lp=B/f'layout/page-{n:04d}.json';save(lp,Layout(source_sha256=SOURCE_SHA,page=n,native_sha256=sha(text.encode()),text_dict=layout))
    pages.append(Page(physical_page=n,native=asset(B/f'native/page-{n:04d}.txt'),image=asset(B/f'images/page-{n:04d}.png'),layout=asset(lp),lines=lines))
    covered=set();found=page.find_tables()
    for ti,t in enumerate(found.tables,1):
        tid=f'P{n}-T{ti}';matrix=t.extract()
        def cuts(axis):
            vals=sorted(v for box in t.cells for v in [box[axis],box[axis+2]])
            merged=[]
            for v in vals:
                if not merged or abs(v-merged[-1])>.01:merged.append(v)
            return merged
        xs=cuts(0);ys=cuts(1);assert len(xs)==t.col_count+1 and len(ys)==t.row_count+1
        cells=[]
        for ri,row in enumerate(t.rows):
            for ci,box in enumerate(row.cells):
                if box is None:continue
                r0=min(range(len(ys)),key=lambda k:abs(ys[k]-box[1]));r1=min(range(len(ys)),key=lambda k:abs(ys[k]-box[3]));c0=min(range(len(xs)),key=lambda k:abs(xs[k]-box[0]));c1=min(range(len(xs)),key=lambda k:abs(xs[k]-box[2]));assert ri==r0 and ci==c0
                evidence=[]
                for line in lines:
                    x0,y0,x1,y1=line.bbox;cx=(x0+x1)/2;cy=(y0+y1)/2
                    if box[0]-.1<=cx<=box[2]+.1 and box[1]-.1<=cy<=box[3]+.1:
                        evidence.append(line.span);covered.add(line.line)
                cells.append(Cell(id=f'{tid}-R{ri:02d}C{ci:02d}',anchor_row=ri,anchor_column=ci,row_span=r1-r0,column_span=c1-c0,bbox=box,geometric_extraction=matrix[ri][ci] or '',native_evidence=evidence,blank=not bool(matrix[ri][ci])))
        rs=[]
        for ri,row in enumerate(matrix):
            ids=[]
            for ci in range(t.col_count):
                cs=[c for c in cells if c.anchor_row<=ri<c.anchor_row+c.row_span and c.anchor_column<=ci<c.anchor_column+c.column_span];assert len(cs)==1
                ids.append(cs[0].id)
            fee=None
            if (n<=2 or n==3 and ti==1) and ri>=header_counts[n-1][ti-1]:
                fee=next(c.geometric_extraction for c in cells if c.id==ids[0])
            rs.append(Row(id=f'{tid}-R{ri:02d}',row_index=ri,kind='header' if ri<header_counts[n-1][ti-1] else 'body',cell_ids=ids,fee_number_as_printed=fee,qualification_ids=[],annotation='Merged cell references preserve the printed parent fee number/description; repeated references are not duplicate charges.' if len(set(ids))!=len(ids) or any(c.anchor_row<ri for c in cells if c.id in ids) else ''))
        columns=(['Fee #','Fee Description: label or merged description','Fee Description: condition','Fee Value'] if n==1 else ['Fee #','Fee Description','Fee Value'] if n==2 or n==3 and ti==1 else ['Total Valuation','Permit Fee'] if n==3 else ['Group','IA','IB','IIA','IIB','IIIA','IIIB','IV','VA','VB'])
        tables.append(Table(id=tid,physical_page=n,title=titles[n-1][ti-1],title_status='continued_table_structural_label' if n==3 and ti==1 else 'visible_source_title',x_grid=xs,y_grid=ys,extracted_matrix=matrix,cells=cells,rows=rs,column_meanings=columns,qualification_ids=[]))
    outside[n]=[line.span for line in lines if line.line not in covered]
# Context retains every original line outside cell geometry, with explicit useful associations.
for n,spans in outside.items():
    contexts.append(Context(id=f'P{n}-OUTSIDE',physical_page=n,kind='unclassified_native_context',evidence=spans,applies_to=[t.id for t in tables if t.physical_page==n],annotation='All native text outside table cell geometry, including headings, displaced native table-number fragments and notes. Exact order is retained; individual conditions are additionally bound below.'))
def excerpt(n,begin,end):
    s=text_by_page[n];i=s.index(begin);j=s.index(end,i)+len(end);return span(n,len(s[:i].encode()),s[i:j])
def ctx(i,n,kind,begin,end,targets,note):
    c=Context(id=i,physical_page=n,kind=kind,evidence=[excerpt(n,begin,end)],applies_to=targets,annotation=note);contexts.append(c)
    for t in tables:
        if t.id in targets:t.qualification_ids.append(i)
        for r in t.rows:
            if r.id in targets:r.qualification_ids.append(i)
ctx('P1-PARENT',1,'condition','Applies to any project','fees may also apply.',['P1-T1'],'Printed fee1 parent applies across all four additional subrows. Separately listed project fees supersede this permit fee; reinspection/additional plan review may apply.')
ctx('P1-DISCRETION',1,'condition','Plan Review Fees in addition to','by the Building Department \n',['P1-T1-R02'],'First occurrence binds commercial maximum50% and department determination; all remaining maxima and their conditions remain in corresponding row cells.')
ctx('P3-FOOTNOTES',3,'footnote','(1) \n','“Total Valuation” is determined by Table 3A and 3B.',['P2-T2','P3-T1'],'References (1) and (2) must retain their separate valuation definitions; literal coast is not changed. Table3B is referenced but no separate 3B heading is present in received five pages.')
ctx('P3-ROUNDING',3,'condition','(All Permit Fees Rounded up','next dollar)',['P3-T2'],'Applies to every one of the eight printed valuation tiers. No fee computation or arithmetic validation performed.')
ctx('P3-VALUATION',3,'valuation_note','Notes: \n1. To determine','the actual labor and material cost of the project.',['P3-T2','P4-T1','P5-T1'],'Both full notes retained: new/addition multipliers and outside dimensions, versus remodel labor/material cost. Source references 3A and 3B; missing3B not synthesized.')
ctx('P5-VALUATION',5,'valuation_note','Notes: \n1.','Department.',['P4-T1','P5-T1'],'All six notes apply to the continued valuation table: garages Utility; unfinished basements$15/sq.ft.; shell-only20% deduction; NP not permitted; complete unfinished residential basements$40/sq.ft.; limited2003values-only reference.')
# Attach exact source parent qualifications to subgroup rows whose label is vertically merged.
for t in tables:
 for r in t.rows:
  if r.kind=='body' and r.fee_number_as_printed in ['6','14','16','19']:
   r.annotation+=' Printed merged parent number '+r.fee_number_as_printed+' remains associated with every subordinate row; no unprinted equality case is supplied.'
(B/'candidate.txt').write_bytes(b''.join((B/p.native.path).read_bytes() for p in pages))
crops=[]
for name,n,box in [('p5-first-rows',5,(165,98,565,177)),('p4-nightclub',4,(70,172,563,224)),('p3-upper-tiers',3,(70,520,542,615))]:
 crops.append(Crop(id=name,physical_page=n,clip=box,scale=4.0,image=asset(B/f'crops/{name}.png')))
obs=[]
def ob(kind,pgs,ids,ev,statement,treatment):obs.append(Observation(id=f'MBF-{len(obs)+1:02d}',kind=kind,physical_pages=pgs,related_ids=ids,evidence=ev,statement=statement,treatment=treatment))
ob('association',[1],['P1-T1'],[excerpt(1,'Applies to any project','review. \nMaximum 20% of the Value of \nthe Calculated Permit Fee as \ndetermined to be appropriate \nby the Building Department')],'Fee1 is a merged parent with a base Table2 referral and four subrows. Commercial50%, residential15%, third-party20% are maxima with department determination; residential$250 is a maximum non-refundable submittal charge credited at issuance. Third-party private costs are negotiated/charged directly between parties.','Retain all parent, actor, contingency and credit wording; do not treat maxima as fixed charges or blend third-party private costs into the departmental20%.')
ob('association',[2],['P2-T1'],[excerpt(2,'Inspections outside','per hour per person \nProject Specific Permit Fees')],'Fee2 is$60/hour/person with2-hour minimum;3 is$50/hour/person;4 distinguishes first$50 versus$100 for addition reinspection on same violation;5 is conditional on staff and additional to fee4;6 splits expired-TCO inspection$250 versus pre-expiry extension$100;7 is$75/hour/person.','Preserve literal addition wording and all units/conditions. Dollar superscripts/spaces remain exact in native evidence.')
ob('scope_limit',[2,3],['P2-T2-R10','P2-T2-R11','P3-T1-R00','P3-T1-R02'],[excerpt(2,'Under $2,000 Valuation','Table 2 (1) \n17'),excerpt(3,'Less than 400 sq. ft.','Table 2 \n20')],'Fee16 says Under and Over$2,000; fee19 says Less than and Over400sq.ft. The exact equality cases are not specified in these rows.','Do not invent a fee for the equality cases or repair boundaries.')
ob('source_anomaly',[3],['P3-FOOTNOTES','P3-T2-R07'],[excerpt(3,'“Total Valuation” is the actual coast','materials.'),excerpt(3,'$500,00.01 to $1,000,000','$1,000,000 \n')],'Literal coast and $500,00.01 are visible source text, not extraction corrections.','Preserve unchanged; no numeric/arithmetic repair.')
ob('scope_limit',[3,4,5],['P3-VALUATION','P4-T1','P5-T1'],[excerpt(3,'“Total Valuation” is determined by Table 3A and 3B.','“Total Valuation” is determined by Table 3A and 3B.'),excerpt(5,'Table 3A- Building Valuation Data (continued)','Table 3A- Building Valuation Data (continued)')],'Notes refer to Table3A and3B, while received source pages4–5 both visibly identify Table3A (second is continued). No separately labeled3B table is present in the five-page source.','Do not rename the continuation3B or manufacture missing data.')
ob('source_anomaly',[4],['P4-T1-R04'],[excerpt(4,'99.751','99.751')],'Nightclubs/IIIB visibly reads99.751 with three decimal places; crop confirms all digits on baseline.','Preserve99.751; do not round or reinterpret the final1 as a footnote.')
ob('source_anomaly',[4,5],['P4-T1-R14','P5-T1-R02'],[excerpt(4,'H234 High Hazard','H234 High Hazard'),excerpt(5,'1-4 Institutional, day','care facilities')],'Source group labels are H234 and 1-4 Institutional, day care facilities.','Preserve original labels; no expansion to H-2/3/4 or I-4.')
ob('association',[4,5],['P4-T1','P5-T1'],[excerpt(5,'N.P. = Not Permitted','N.P. = Not Permitted')],'Matrix has26body rows and9construction columns. Three printed NP cells: H-1/VB and I-2/IIIB,VB. Other values, including page4 I-3/IIIB112.98 and VB98.94, are numeric in this source.','Do not import NP positions or rates from another county schedule. Full matrix associations retained.')
ob('association',[5],['P5-VALUATION'],[excerpt(5,'Private Garages','Department.')],'All six valuation notes preserved, including the2003 IBC values-only qualification and adopted-version rule for other requirements/definitions.','No inference that this exhibit adopts the2003 IBC generally; no arithmetic or current-law conclusion.')
ob('reading_order',[1,2],['P1-OUTSIDE','P2-OUTSIDE'],[excerpt(1,'1A','1A'),excerpt(2,'1A','1A')],'Native Table1A fragments occur separately from the visual title, and superscript decimal/reference typography can produce spaces. All native bytes are kept in their original order; cell association is a separate geometrical derivation.','No native cleanup; visible titles in the readable tables are reviewer-associated labels, with exact source fragments retained.')
ob('date_role',[1,2,3,4,5],['P1-OUTSIDE'],[excerpt(1,'EXHIBIT A','MESA COUNTY BUILDING DEPARTMENT FEE SCHEDULE')],'No printed adoption/effective date is visible in the five-page schedule. Filename2024, directory2026-04 and PDF metadata are not enactment dates; catalog Adopted Fee Schedule is a referral label.','Adoption/effectiveness and legal currentness remain not_verified.')
review=Review(review_id='ATLAS-MESA-BUILDING-FEES-2026-09-11',authority_id='CO-COUNTY-MESA',source=source,candidate=asset(B/'candidate.txt'),acquired_at=receipt['completed_at'],source_url=receipt['requested_url'],final_url=receipt['final_url'],prepared_at=start,completed_at=datetime.now(timezone.utc),review_mode='atlas_candidate_aware_not_blind',external_assignment=None,status='source_text_and_table_associations_reviewed',legal_currentness='not_verified',adoption_effectiveness='not_verified',engine='PyMuPDF',engine_version='1.28.2',native_flags=195,native_sort=False,render_scale=2.0,native_bytes=sum(p.native.bytes for p in pages),native_byte_changes=0,pages=pages,tables=tables,contexts=contexts,crops=crops,observations=obs,limits=['All five full pages and three focused crops directly viewed; candidate-aware Atlas source QA, not independent external blind review.','No new source request, legal interpretation, fee computation, numeric correction, rule-unit/coverage/currentness promotion or canonical intake.','Geometric cell strings are separate derived extraction, while original native UTF8 bytes and all source glyph positions are retained unchanged. Superscripts/spacing are not a native-text correction.','All physical tables retained, including eight valuation tiers and26valuation rows; absent referenced Table3B is unresolved.','Raw PDF and prior custody files are unchanged. Fresh typed records are research evidence only; no assertion of authenticity of enactment.'])
save(B/'SOURCE_REVIEW.json',review)
(B/'SOURCE_REVIEW.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n')
(B/'PREPARATION.schema.json').write_text(json.dumps(Preparation.model_json_schema(),indent=2)+'\n')
print(json.dumps({'native_bytes':review.native_bytes,'tables':len(tables),'body_rows':sum(r.kind=='body' for t in tables for r in t.rows),'all_rows':sum(len(t.rows) for t in tables),'grid_slots':sum(len(r.cell_ids) for t in tables for r in t.rows),'physical_cells':sum(len(t.cells) for t in tables),'native_lines':sum(len(p.lines) for p in pages),'contexts':len(contexts),'observations':len(obs)},indent=2))
