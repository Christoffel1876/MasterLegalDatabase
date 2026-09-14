"""Freeze Atlas's direct four-page reading before consulting native text."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import hashlib,json
from pydantic import BaseModel,ConfigDict,Field
ROOT=Path(__file__).parent
class Row(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 row_id:str
 physical_page:int=Field(ge=1,le=4)
 application:str
 fee:str
class Pass1(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 source_sha256:Literal['0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b']
 frozen_at:str
 method:str
 source_header:str
 date_claims:list[str]
 rows:list[Row]
 uncertainties:list[str]
 visual_notes:list[str]
 legal_currentness:Literal['not_verified']='not_verified'
 answer_safe:Literal[False]=False
DATA={
1:[
('Accessory Dwelling Unit','$50'),
('Accessory Structure (one, two, or three-family residence)','$50'),
('Administrative Determination','$150'),
('Annexation','$500 + $5 for each acre over 10 acres'),
('Annexation Agreement Amendment','$500'),
('Appeal of Administrative Determination','$600'),
('Awning Over Right of Way','$25'),
('Certificate of Appropriateness:\n- Residential (historic landmark)\n- Non-residential (historic landmark)','$75\n$150'),
('Certificate of Economic Hardship (related to Certificate of Appropriateness)','$75'),
('Certificate of Zoning, or Legal Nonconforming Lot, Structure, or Use','$50'),
('Commercial Site Plan','- Landscape Verification: $0 1st Visit, $150 2nd Visit, $300 3rd Visit or More\n- Large-Scale Development: $1,000 ≤ 100,000 sf, $1,500 >100,000 sf\n- Lighting Plan Review: $50\n- Site Plan Review: $300\n- Tenant Finish or Exterior Remodel (without addition that increases building footprint or site improvements): $50\n- Interior Only Remodel (without addition that increases building footprint or site improvements): $50'),
('Continuation of Public Hearing','$50'),
('Demolition (structures not designated as a historic landmark)\n- Non-residential structure\n- Residential Structure','- $150\n- $25'),
],
2:[
('Demolition Permit Review (designated as a historic landmark)','$150'),
('Extension of Recordation Deadline','$40'),
('HARP Development Plan Review','$150'),
('Limited Use Permit','$500'),
('Marijuana Certificate of Location (cannabis)','$500'),
('Marijuana (Retail or Medical) Conditional Use Permit or Renewal (cannabis)','- New Permit: $5,000 (medical center, retail store, retail or medical cultivation facility, retail or medical infused product manufacturing, and retail or medical testing facility)\n- Renewal: $2,500'),
('Master Sign Plan','$150'),
('Metropolitan District Service Plan Review','- $500, plus hourly rate for legal review of the service plan'),
('Nomination of Historic District','$200'),
('Nomination of Historic Landmark','$150'),
('Overall Development Plan','$500 + $5 For each acre over 10 acres\n(Note: waived if required as part of an annexation)'),
('Planned Unit Development, Development Guide/Plan Amendment','$500'),
('Planned Unit Development, Site Plan Review or Major Revision','- $500 1st 50,000 sf\n- $500 Each additional 50,000 sf'),
('Planned Unit Development, Site Plan Review, Minor Revision','- $250 Dimensional\n- $100 Landscape\n- $150 Location\n- $200 Parking'),
],
3:[
('Public Notice Fees','- $2 Postcard for each address\n- $5 HPC Poster\n- $5 PZ poster\n- $3 ZBA poster\n- Legal advertisement calculation based on number of cases per meeting.\n- $25 per public notice required for annexation'),
('Rearrangement of Property Boundaries','$200'),
('Residential, New Construction or Addition (one- or two-family residence)','$50'),
('Rezoning\n- A-1\n- A-2\n- A-3\n- A-4\n- R-1, R-2, R-2U, R-3, R-4, R-5, R-6 & R-8\n- R-7\n- O-1, B-1, B-2, B-3, B-4, BP, I-1, I-2, I-3\n- H-B, HARP1, HARP2, HARP3\n- CCN, RCN\n- S-1, S-2, S-3, S-4, S-5\n- MPCD, PUD','- $100 + $1.00 per acre\n- $100 + $4 per acre\n- $100 + $18 per acre\n- $100 + $35 per acre\n- $150 + $75 1st acre + $20 each additional acre\n- $150 + $150 1st acre + $40 each additional acre\n- $150 + $125 1st acre + $30 each additional acre\n- $90 + $125 1st acre + $30 each additional acre\n- $150_+ $125 1st acre + $30 each additional acre\n- $90 + $25 1st acre + $10 each additional acre\n- $500 base fee + $50 per acre'),
('Sign Plan Review','$95'),
('Special Area Plan','$100 + $25 per Lot'),
('Special Exception','$500'),
('Special Use Permit (Use by Review)','$500'),
('Specially Requested Hearing (ZBA)','$1,000'),
('Specially Requested Hearing (HPC)','$150'),
('Student Housing, Site Plan or Major Revision','$500 (1st 50,000 sf) + $500 (each additional 50,000 sf)'),
('Student Housing, Minor Revision','$100'),
('Subdivision','- $100 + $160 per Lot (≤10), $105 Plus per Lot (≥11)\n- $100 Deferred Filing+ $50 per lot'),
('Swimming Pool','$50'),
],
4:[
('Vacation (of street, alley, or other public way)','- $250 Alley (if not included with Road Vacation)\n- $175 Easement\n- $325 Road\n(Note: fees per plat)'),
('Variance','- $750 Non-Residential\n- $250 Residential'),
('Wireless Communication Facilities, (Tower or Antenna,) New or Modification','$500'),
]}
rows=[Row(row_id=f'P{page}-{i:02d}',physical_page=page,application=a,fee=b) for page,items in DATA.items() for i,(a,b) in enumerate(items,1)]
assert len(rows)==44
r=Pass1(source_sha256=hashlib.sha256((ROOT/'original.pdf').read_bytes()).hexdigest(),frozen_at=datetime.now(timezone.utc).isoformat(),method='Atlas direct full-page PNG inspection at160dpi on all4 pages, source-first before native extraction. Acquisition metadata and4-page structure known; not an external blind reviewer.',source_header='city of PUEBLO colorado | Planning & Community Development | 101 W Riverwalk | Pueblo, Colorado 81003 | Tel 719-553-2259 | www.pueblo.us | FEE SCHEDULE',date_claims=['2-13-26 printed in bottom-right footer on physical pages1 and4; no explicit effective/adoption date label seen.'],rows=rows,uncertainties=['P3-04 CCN, RCN fee has a visible low mark between $150 and +; transcribed as underscore provisionally pending crop.','Exact Unicode bullets, superscript encodings and typography are not certified from pixels.'],visual_notes=['Applications/Fees column headers repeat on pages1,2 and4; page3 starts Public Notice Fees without a header row.','Page4 repeats the letterhead; pages2 and3 begin directly with the continuation table.','No printed page numbers seen. No signatures, seals, adopting ordinance or resolution cited in the visible document.','Each record is one physical application row; nested bullet lists are preserved within the two associated cells. Rezoning has11 paired subcategories; Certificate of Appropriateness and Demolition have2 paired categories each.','Visual soft line wraps are joined; bullets normalized to ASCII hyphen plus space; superscript st/nd/rd flattened. Capitalization, awkward punctuation, monetary strings and explicit qualifications are retained.','The city site may expose an old link slug for different current bytes; neither URL slug nor Content-Disposition filename establishes legal currentness.'])
body=(r.model_dump_json(indent=2)+'\n').encode();Pass1.model_validate_json(body)
with (ROOT/'PASS1_frozen.json').open('xb') as f:f.write(body)
with (ROOT/'PASS1.schema.json').open('x') as f:f.write(json.dumps(Pass1.model_json_schema(),indent=2)+'\n')
print(json.dumps({'rows':len(rows),'sha256':hashlib.sha256(body).hexdigest(),'frozen_at':r.frozen_at}))
