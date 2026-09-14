"""One-time derived review builder after Atlas direct source inspection; never fetches."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json,pymupdf
from review_models import *
D=Path(__file__).resolve().parent

def asset(p):
    raw=p.read_bytes();return Asset(path=p.relative_to(D).as_posix(),sha256=sha256(raw).hexdigest(),size_bytes=len(raw))
def span(path,start,end):
    raw=(D/path).read_bytes()[start:end]
    return Span(path=path,start=start,end=end,text=raw.decode(),sha256=sha256(raw).hexdigest())
if (D/'SOURCE_QA.json').exists():raise ValueError('Refuse review rewrite')
(D/'SOURCE_QA.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n')
lines={};used={};native=[]
for p in [1,2]:
    path=f'native/page-{p}.txt';raw=(D/path).read_bytes();offset=0;lines[p]=[]
    for n,line in enumerate(raw.splitlines(keepends=True),1):
        s=span(path,offset,offset+len(line));lines[p].append(s);native.append((p,n,s));offset+=len(line)
    assert offset==len(raw)
def consume(p,text,who):
    target=' '.join(text.split());ll=lines[p]
    for start,x in enumerate(ll):
        if (p,start) in used or not x.text.strip():continue
        for count in range(1,4):
            run=ll[start:start+count]
            if len(run)!=count or any((p,start+j) in used for j in range(count)):break
            joined=' '.join(' '.join(x.text.split()) for x in run)
            join_hyphen=joined.replace('10- 401','10-401')
            if target in [joined,join_hyphen]:
                for j in range(count):used[p,start+j]=who
                return run
    raise ValueError('Cannot bind '+who+': '+text)
rows=[]
for i,line in enumerate((D/'rows-reviewed.txt').read_text().splitlines(),1):
    p,g,label,fee=line.split('|');p=int(p);rid=f'R{i:02d}'
    la=consume(p,label,rid);fe=consume(p,fee,rid)
    assert len(fe)==1
    notes=['N03']
    if rid=='R38':notes.append('N01')
    if rid=='R41':notes.append('N02')
    if rid in ['R48','R49']:notes.append('H01')
    rows.append(Row(id=rid,page=p,group_id=g,application=label,fee=fee,application_native=la,fee_native=fe[0],related_note_ids=notes))
def rs(g):return [r.id for r in rows if r.group_id==g]
groupdefs=[('G01','STANDARD APPLICATIONS','LAND USE/DEVELOPMENT APPLICATIONS',1),('G02','PLANNED DEVELOPMENT AND REZONING','LAND USE/DEVELOPMENT APPLICATIONS',1),('G03','SIGNS','LAND USE/DEVELOPMENT APPLICATIONS',1),('G04','SPECIAL EVENTS','LAND USE/DEVELOPMENT APPLICATIONS',1),('G05','SUBDIVISION EXEMPTIONS','LAND DIVISION APPLICATIONS',1),('G06','SUBDIVISIONS','LAND DIVISION APPLICATIONS',2),('G07','VARIANCES AND APPEALS',None,2),('G08','SHORT-TERM RENTALS',None,2),('G09','ACTIVITIES AND AREAS OF STATE INTEREST (1041 REGULATIONS)',None,2),('G10','HOURLY RATES',None,2)]
groups=[];passages=[]
for g,h,parent,p in groupdefs:
    groups.append(Group(id=g,heading=h,parent_heading=parent,pages=sorted({r.page for r in rows if r.group_id==g}),row_ids=rs(g),heading_native=consume(p,h,g)[0],column_headings=None if g=='G10' else ('Application Type','Fee'),heading_on_page2=p==2))
    if g!='G10':
        for title in ['Application Type','Fee']:
            cid=g+'-'+title.replace(' ','-')
            passages.append(Passage(id=cid,page=p,kind='column_heading',text=title,native=consume(p,title,cid),applies_to_rows=rs(g)))
for p in [1,2]:
    for j,(kind,text) in enumerate([('header','CHAFFEE COUNTY'),('header','PLANNING AND ZONING DEPARTMENT'),('footer','Updated December 2024')]):
        cid=f'P{p}-M{j}'
        passages.append(Passage(id=cid,page=p,kind=kind,text=text,native=consume(p,text,cid),applies_to_rows=[]))
for i,text in enumerate(['Chaffee County Fee Schedule','Planning and Zoning','Effective January 1, 2025']):
    cid=f'T{i}';passages.append(Passage(id=cid,page=1,kind='title',text=text,native=consume(1,text,cid),applies_to_rows=[]))
for i,text in enumerate(['LAND USE/DEVELOPMENT APPLICATIONS','LAND DIVISION APPLICATIONS']):
    cid=f'PARENT{i}';rr=[r.id for r in rows if next(g for g in groups if g.id==r.group_id).parent_heading==text]
    passages.append(Passage(id=cid,page=1,kind='parent_heading',text=text,native=consume(1,text,cid),applies_to_rows=rr))
notes=[('N01','note','*If applicant is successful on appeal, appeal fee will be refunded.',['R38']),('N02','note','*License Fee is required in addition to Application Review Fee and is required prior to license being issued.',['R41']),('H01','hourly_condition','For non-standard development reviews, the Planning Director may allow an application to be reviewed at an hourly rate. Special requests of the County’s GIS Coordinator, including outside party requests, shall be billed hourly.',['R48','R49']),('N03','note','Pursuant to Section 5.2.5.5 of the Chaffee County Land Use Code, the County may require escrow of additional amounts to pay referral agencies and/or outside consultants for application review. Such fees are in addition to this schedule and shall be levied based on the individual application.',[r.id for r in rows])]
for cid,kind,text,rr in notes:passages.append(Passage(id=cid,page=2,kind=kind,text=text,native=consume(2,text,cid),applies_to_rows=rr))
for p,n,s in native:
    if s.text.strip() and (p,n-1) not in used:raise ValueError('Unassociated text: '+s.text)
rects=[(1,'logo',[130,45,475,310]),(1,'title',[820,135,1820,630]),(1,'development',[130,680,2410,1860]),(1,'divisions',[130,2450,2420,3160]),(2,'continuation',[130,340,2410,1040]),(2,'appeal-rental',[130,1090,2410,1810]),(2,'1041',[130,1810,2410,2450]),(2,'hourly-notes',[130,2490,2410,3200])]
(D/'crops').mkdir();cropdata=[]
for p,name,r in rects:
    pix=pymupdf.Pixmap(str(D/f'pages/page-{p}.png'));rect=pymupdf.IRect(r);c=pymupdf.Pixmap(pix.colorspace,rect,pix.alpha);c.copy(pix,rect)
    dest=D/f'crops/p{p}-{name}.png';dest.write_bytes(c.tobytes('png'));cropdata.append(dict(page=p,rect=r,source=asset(D/f'pages/page-{p}.png').model_dump(),crop=asset(dest).model_dump()))
(D/'CROPS.json').write_text(json.dumps(cropdata,indent=2)+'\n')
qa=Review(source_id='chaffee-planning-application-fees-atlas-directed',authority_id='CO-COUNTY-CHAFFEE',source=asset(D/'source/original.pdf'),reviewed_at=datetime.now(timezone.utc).isoformat(),reviewer='Atlas',status='complete_source_fidelity_pending_independent_review',review_kind='checked_tables',legal_currentness='not_verified',answer_safe=False,method='Atlas directly inspected both full300dpi source images, then compared every visible table row and full page context to unchanged native text. Eight exact crops generated for targeted confirmation; their inspection is recorded in a separate subsequent receipt. This is candidate-aware source QA, not a blind or current-law review.',source_pages=[asset(D/f'pages/page-{p}.png') for p in [1,2]],native_pages=[asset(D/f'native/page-{p}.txt') for p in [1,2]],native_lines=[NativeLine(page=p,line=n,span=s,associated_with=used.get((p,n-1))) for p,n,s in native],groups=groups,rows=rows,passages=passages,graphics=[Graphic(page=p,observation='Colored county emblem with visible COLORADO / CHAFFEE / COUNTY / EST. 1879 and mountain/sun motif; logo words omitted from native text.',identity_or_authenticity_verified=False) for p in [1,2]],inspected_full_pages=(1,2),crops=[asset(D/x['crop']['path']) for x in cropdata],source_date_claims=['Effective January 1, 2025 appears beneath the page1 title.','Updated December 2024 is printed at the bottom of each page; native extraction floats both footers near the head.'],verified_effective_date=None,limitations=['Exactly49 physical fee rows in10 logical categories; subdivision exemptions span both pages, with no repeated heading before the first four page2 rows. Category hierarchy is visual layout, not a legal applicability determination.','All displayed amounts and fee expressions remain literal. The planned-development expression and 1,000 SF comm. space is not rewritten as a per-unit formula or calculated.','The source provides less-than and greater-than2,500 foot-marked exploration categories; exactly2,500 is not supplied. No threshold gap is repaired.','Appeal refund and rental-license-in-addition notes remain scoped to their marked rows. The final escrow paragraph remains a schedule-wide qualification, not a computed fee.','Native extraction preserves the body and amounts but omits the colored logo and reorders Updated footers. Typographic whitespace and line wrapping are normalized; exact Unicode glyph identity is not certified by pixels.','Printed effective/update dates are source assertions, not verified legal currentness. No adopting resolution, amendment chain, application-specific answer or fee calculation was checked.','Two new observed publicGET/receipt chains are distinct from supplied historical referrals. This review predates canonical intake of this PDF; provenance is retained separately without inventing a received_at.','Tests and hashes check structure and reproducibility, not perfect visual transcription or independent-model-family certification.'],custody=[asset(D/x) for x in ['PREPARATION.json','PREPARATION.schema.json','EXTRACTION.json','EXTRACTION.schema.json','CROPS.json','rows-reviewed.txt']])
(D/'SOURCE_QA.json').write_text(qa.model_dump_json(indent=2)+'\n')
text=['# Chaffee County planning fee schedule — complete scoped review','', 'Source date statements and all limitations are in SOURCE_QA.json. This is source text, not a fee calculation or current-law answer.','']
for g in groups:
    text.extend(['## '+g.heading,'','| Physical page | Application type | Printed fee |','|---|---|---|'])
    for r in rows:
        if r.group_id==g.id:text.append(f'| {r.page} | {r.application} | {r.fee} |')
    text.append('')
for p in passages:
    if p.kind not in ['column_heading','parent_heading']:text.extend([f'[{p.id}; physical page{p.page}; {p.kind}] '+p.text,''])
(D/'CHECKED_TABLES.md').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(rows=len(rows),groups=len(groups),native_lines=len(native),native_bytes=sum(x.size_bytes for x in qa.native_pages),review_sha256=asset(D/'SOURCE_QA.json').sha256)))
