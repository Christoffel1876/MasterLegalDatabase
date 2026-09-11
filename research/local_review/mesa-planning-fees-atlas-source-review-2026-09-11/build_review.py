"""One-time source-bound historical planning fee review builder; no network."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
import pymupdf
from review_models import *
from row_specifications import TABLES
B=Path(__file__).resolve().parent
SHA='af11318af2ce3ea5e4b1af313f348ab851a855a76418e3878d1a166c084dadb6'
def h(b):return hashlib.sha256(b).hexdigest()
def asset(p):return Asset(path=p.relative_to(B).as_posix(),sha256=h(p.read_bytes()),bytes=p.stat().st_size)
def save(p,x):
 if p.exists():raise FileExistsError(p)
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(x.model_dump_json(indent=2)+'\n');os.replace(q,p)
def make_span(n,start,text):return Span(page=n,start=start,end=start+len(text.encode()),text=text,sha256=h(text.encode()))
source=asset(B/'source/mesa-planning-fees-2017-2018.pdf');assert source.sha256==SHA
doc=pymupdf.open(B/source.path);pages=[];texts={};line_maps={};glyphs={}
for n,p in enumerate(doc,1):
 text=p.get_text('text',flags=195,sort=False);texts[n]=text;assert (B/f'native/page-{n:04d}.txt').read_bytes()==text.encode()
 rd=p.get_text('rawdict',flags=195,sort=False);off=0;ls=[];gs=[]
 for bl in rd['blocks']:
  for line in bl.get('lines',[]):
   chars=[c for sp in line['spans'] for c in sp['chars']];s=''.join(c['c'] for c in chars)+'\n';begin=off
   for c in chars:gs.append((off,off+len(c['c'].encode()),c['c'],tuple(c['bbox'])));off+=len(c['c'].encode())
   off+=1;ls.append(Line(number=len(ls)+1,bbox=line['bbox'],evidence=make_span(n,begin,s)))
 assert ''.join(l.evidence.text for l in ls)==text;line_maps[n]=ls;glyphs[n]=gs
 lp=B/f'layout/page-{n:04d}.json';save(lp,Layout(source_sha256=SHA,page=n,native_sha256=h(text.encode()),rawdict=rd));pages.append(Page(number=n,native=asset(B/f'native/page-{n:04d}.txt'),image=asset(B/f'images/page-{n:04d}.png'),layout=asset(lp),lines=ls))
def slice_lines(n,a,z):
 ls=line_maps[n];return make_span(n,ls[a-1].evidence.start,''.join(l.evidence.text for l in ls[a-1:z]))
def cell(n,col,start,text,annotation=''):
 if text is None:return Cell(column_id=col,evidence=[],native_text=None,glyph_bbox=None,annotation=annotation)
 s=make_span(n,start,text);boxes=[box for a,z,c,box in glyphs[n] if a>=s.start and z<=s.end and c.strip()]
 box=(min(x[0] for x in boxes),min(x[1] for x in boxes),max(x[2] for x in boxes),max(x[3] for x in boxes)) if boxes else None
 return Cell(column_id=col,evidence=[s],native_text=text,glyph_bbox=box,annotation=annotation)
rows=[];tables=[]
for tid,n,title,specs in TABLES:
 three=(n==1 or tid in ['P2-APPLICATIONS','P2-CONTINUATION'])
 columns=['source_item','2009_fee','2017_18_fee'] if three else ['source_item','fee_as_printed','conditions_as_printed']
 rids=[]
 for idx,(a,z,v1,v2) in enumerate(specs,1):
  ev=slice_lines(n,a,z);s=ev.text;rid=f'{tid}-R{idx:02d}';rids.append(rid)
  if three:
   j=s.rindex(v2);i=s.rindex(v1,0,j);cs=[cell(n,columns[0],ev.start,s[:i]),cell(n,columns[1],ev.start+len(s[:i].encode()),v1),cell(n,columns[2],ev.start+len(s[:j].encode()),v2)]
  elif v1 is not None:
   i=s.rindex(v1);j=i+len(v1);cs=[cell(n,columns[0],ev.start,s[:i]),cell(n,columns[1],ev.start+len(s[:i].encode()),v1),cell(n,columns[2],ev.start+len(s[:j].encode()),s[j:])]
  else:
   split=s.index('CHECKS');cs=[cell(n,columns[0],ev.start,s[:split]),cell(n,columns[1],0,None,'No amount is stated; this is not a zero fee.'),cell(n,columns[2],ev.start+len(s[:split].encode()),s[split:])]
  note='Source year columns are historical labels; not current-fee assertions.' if three else 'Fee/payer/conditions as printed in this county-published schedule; no independent adoption or currentness assertion.'
  if rid=='P1-GENERAL-R05':cs[2].annotation='Native 275.001 is visually 275.00 with superscript footnote1, not a three-decimal monetary amount.'
  if rid=='P1-ACREAGE-R08':note='Continuation of preceding 101-or-more-acre tier: Fee Plus $55.00 per25acres in2009 column; separate0.00 in2017–18 column. No extra acreage tier inferred.'
  rows.append(Row(id=rid,table_id=tid,page=n,order=idx,source_lines=(a,z),evidence=ev,cells=cs,parent_context_ids=[],annotation=note))
 tables.append(Table(id=tid,page=n,title=title,columns=columns,row_ids=rids,context_ids=[],authority_note='Published by Mesa County; named school districts/CGS/Clerk are distinct source-stated recipients or entities, not county ownership of their law.'))
contexts=[]
def context(i,n,a,z,targets,note):
 c=Context(id=i,page=n,evidence=slice_lines(n,a,z),applies_to=targets,note=note);contexts.append(c)
 for t in tables:
  if t.id in targets:t.context_ids.append(i)
 for r in rows:
  if r.id in targets:r.parent_context_ids.append(i)
context('C-YEARS',1,1,11,[t.id for t in tables if t.page==1]+['P2-APPLICATIONS','P2-CONTINUATION'],'Exhibit A; suspended2017&2018 with other-fee qualification; original2009 and2017–18 headings. Yellow highlight on latter is graphical, not a native word change.')
context('C-APPEAL',1,21,21,['P1-GENERAL-R05'],'Superscript1 requires refund when appeal upheld by Board of County Commissioners; not a zero fee.')
context('C-CONDITIONAL',1,22,22,['P1-GENERAL-R06','P1-GENERAL-R07','P1-GENERAL-R08'],'Conditional Use is parent of both employee/acreage alternatives and permit extension; preserve all or/and comparisons literally.')
context('C-MAJOR',1,36,36,['P1-MAJOR'],'Parent heading for four distinct stages.')
context('C-PUD',1,50,50,['P1-PUD'],'Literal Plan Unit Development, not silently corrected to Planned.')
context('C-ACREAGE',1,60,62,['P1-ACREAGE','P1-MAJOR-R02','P1-PUD-R02'],'Asterisk cross-reference; chart excludes AFT Majors as printed; not silently reclassified.')
context('C-ACREAGE-BASE',1,75,76,['P1-ACREAGE-R08'],'The following Fee Plus line belongs to this101-or-more tier; preserve base and additional amounts separately.')
context('C-PROPERTY',1,80,80,['P1-PROPERTY'],'Parent Property Line Adjustments.')
context('C-CONTINUATION',2,23,23,['P2-CONTINUATION'],'Continuation-fee heading; year columns continue the application table.')
context('C-POSTCARDS',2,28,33,['P2-CONTINUATION'],'Source retains one/two-asterisk patterns; Times number of postcards and adjustment wording preserved, not normalized to identical markers.')
context('C-EXTRAORDINARY',2,34,35,[t.id for t in tables if t.page==1]+['P2-APPLICATIONS','P2-CONTINUATION'],'Applicant responsibility for all extraordinary processing costs; no blanket fee waiver.')
context('C-CONTINUING',2,37,41,['P2-SCHOOL','P2-TIF','P2-COPIES','P2-PUBLICATIONS'],'Source explicitly says fees continue2017&2018; school fee unit is per residential dwelling unit. No post-period effect inferred.')
context('C-SCHOOL-EXPIRY',2,47,48,['P2-SCHOOL'],'Literal1October2020 expiration and annual review with school districts; inconsistent HTML2022 is separate.')
context('C-TIF',2,50,52,['P2-TIF'],'Collected at Planning Division; starred$1902 for single-family residence, not generalized all-use rate.')
context('C-COPIES',2,54,54,['P2-COPIES'],'Copies heading; sizes and prices retained.')
context('C-PUBLICATIONS',2,60,60,['P2-PUBLICATIONS'],'Publication prices, not regulatory filing fees.')
context('C-PRINT-PRICE',2,69,69,['P2-PUBLICATIONS'],'Printed on request at current printer’s price; source qualifier retained.')
context('C-GIS',3,1,3,['P3-GIS'],'Maps/orthophotos/other drawings, black-and-white or color; minimum per-sheet charge retained in its own row.')
context('C-IMAGERY',3,10,20,['P3-IMAGERY'],'Technical product description and two material/labor options preserved; no recalculation of minimum.')
context('C-CGS-PAYEE',3,23,26,['P3-CGS'],'Checks or money orders payable to Colorado Geological Survey; separate state agency, not school district or county planning fee.')
# Full native line accounting, including whitespace and leader lines not separately used as cells.
covered={(r.page,k) for r in rows for k in range(r.source_lines[0],r.source_lines[1]+1)}
covered|={(c.page,l.number) for c in contexts for l in line_maps[c.page] if c.evidence.start<=l.evidence.start and l.evidence.end<=c.evidence.end}
for n,ls in line_maps.items():
 for l in ls:
  if (n,l.number) not in covered:context(f'C-NATIVE-{n}-{l.number}',n,l.number,l.number,[],'Preserved source context/whitespace outside assigned rows; not discarded.')
obs=[]
def observation(i,ids,spans,finding,treatment):obs.append(Observation(id=i,related_ids=ids,evidence=spans,finding=finding,treatment=treatment))
observation('MPF-01',['C-YEARS','C-EXTRAORDINARY'],[slice_lines(1,3,11),slice_lines(2,34,35)],'The PDF labels its suspension2017&2018 and retains other-fee and extraordinary-cost qualifications.','Historical columns do not prove current zero fees or an all-fees waiver.')
observation('MPF-02',['P1-GENERAL-R05','C-APPEAL'],[slice_lines(1,19,21)],'The appeal row shows275.00 in both years. The trailing native1 is visually a raised footnote marker.','Preserve native275.001, with separate visible-footnote annotation. Refund condition remains attached.')
observation('MPF-03',['C-CONDITIONAL'],[slice_lines(1,22,29)],'Conditional-use text says fewer than200employees OR less than10acres; next row more than200employees OR10acres or more. The source does not resolve overlaps or exactly200employees by itself.','Keep literal comparisons and permit-extension parent; do not interpret precedence.')
observation('MPF-04',['C-ACREAGE-BASE','P1-ACREAGE-R08'],[slice_lines(1,75,78)],'The last acreage tier has base675.00 plus55.00per25acres in2009; the2017–18 column prints0.00 on each line.','Separate continuation line and parent; no multiplication, rounding or invented acreage bracket.')
observation('MPF-05',['C-POSTCARDS'],[slice_lines(2,24,33)],'Planning-hearing2017–18 value has no asterisk; Board-hearing value has**; postcard values have*. The quantity and adjustment note remain.','Preserve marker mismatch as source typography; no marker harmonization.')
observation('MPF-06',['C-SCHOOL-EXPIRY'],[slice_lines(2,41,48)],'PDF states1October2020 expiration; four named school districts appear as per-dwelling fee categories. Retained HTML separately states1October2022.','Leave conflict unresolved; no acquired extension/resolution and no district-law ownership promotion.')
observation('MPF-07',['P3-IMAGERY'],[slice_lines(3,10,20)],'Imagery options include10.00per sm with no minimum and customer CD media/labor; or25.00per square mile with2-square-mile/50.00minimum and county material/labor. Literal CDW is retained.','Do not blend options, repair terminology or infer present availability/pricing.')
observation('MPF-08',['P3-CGS'],[slice_lines(3,25,38)],'Four CGS review classes preserve dwelling-unit/acreage thresholds, payment with submittal and repeated warning that the eventual bill may be larger.','Treat source amounts as historical stated submittal charges, not caps; retain separate CGS payee.')
observation('MPF-09',['P3-RECORDING'],[slice_lines(3,40,40)],'Recording instruction specifies checks or money orders only payable to Mesa County Clerk and Recorder, without an amount.','Null amount remains unknown, not zero.')
# Separate HTML source claims: these do not replace PDF assertions.
parsed=json.loads((B/'custody/E001-parsed.json').read_text());ht=parsed['text'];hp=B/'custody/E001-parsed-text.txt';hp.write_text(ht)
he=json.loads((B/'custody/E001-event.json').read_text());hc=[]
for claim in ['Mesa County planning application fees have been suspended effective 2017 to present (*other fees may remain in effect).','School Land Dedication resolution expires 1 October 2022 and annual reviews will be coordinated with the School Districts.']:
 # Preserve exact spaces from retained parser, including nonbreaking spaces.
 normalized=' '.join(ht.split());assert ' '.join(claim.split()) in normalized
 if claim not in ht:
  start=ht.index('School Land Dedication resolution expires');end=ht.index('School Districts.',start)+len('School Districts.');claim=ht[start:end]
 i=ht.index(claim);hc.append(HTMLObservation(source=asset(B/'custody/E001-body.bin'),snapshot_text=asset(hp),source_url=he['requested_url'],retrieved_at=he['completed_at'],exact_claim=claim,start_byte=len(ht[:i].encode()),end_byte=len(ht[:i+len(claim)].encode()),claim_sha256=h(claim.encode()),note='Official HTML statement preserved separately from historical PDF; no resolution of temporal conflict or actual adopting instrument.'))
cs=[]
for name,n,box in [('p1-appeal-marker',1,(430,252,557,272)),('p1-acreage-addition',1,(70,628,559,662)),('p2-postcard-markers',2,(61,195,562,264)),('p2-expiration',2,(61,411,565,442))]:cs.append(Crop(id=name,page=n,clip=box,scale=4,image=asset(B/f'crops/{name}.png')))
(B/'candidate.txt').write_bytes(b''.join((B/p.native.path).read_bytes() for p in pages))
receipt=json.loads((B/'custody/E004-event.json').read_text())
r=Review(review_id='ATLAS-MESA-PLANNING-FEES-2026-09-11',authority_id='CO-COUNTY-MESA',source=source,candidate=asset(B/'candidate.txt'),source_url=receipt['requested_url'],acquired_at=receipt['completed_at'],completed_at=datetime.now(timezone.utc),engine_version='1.28.2',native_flags=195,native_sort=False,native_bytes=sum(p.native.bytes for p in pages),native_byte_changes=0,review_mode='atlas_candidate_aware_not_blind',external_assignment=None,status='all_three_pages_source_rows_and_associations_reviewed',legal_currentness='not_verified',adoption_effectiveness='not_verified',pages=pages,tables=tables,rows=rows,contexts=contexts,observations=obs,html_claims=hc,crops=cs,limits=['Three full pages and four targeted crops directly viewed; earlier directed audit had already viewed pages1–2, so this is candidate-aware internal QA.','All native bytes, including dots, spaces, symbols, source years and superscript extraction, remain unchanged. Cell/row associations are separate derived evidence.','No fee calculations, arithmetic repairs, conflict resolution, currentness/adoption/coverage promotion, canonical intake, network request or external reviewer assignment.','Source school districts, Colorado Geological Survey, county Planning Division and Clerk/Recorder remain distinct entities. County publication does not establish each entity’s current fee authority.'])
save(B/'SOURCE_REVIEW.json',r);(B/'SOURCE_REVIEW.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n')
print(json.dumps({'native_bytes':r.native_bytes,'lines':sum(len(p.lines) for p in pages),'tables':len(tables),'rows':len(rows),'cells':sum(len(r.cells) for r in rows),'contexts':len(contexts),'observations':len(obs),'html_claims':len(hc)},indent=2))
