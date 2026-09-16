"""Freeze source-image observations before native extraction/comparison."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import hashlib,json
from pydantic import BaseModel,ConfigDict,Field
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Page(Strict):
 physical_page:int=Field(ge=1,le=5)
 image_path:str
 sha256:str=Field(pattern='^[a-f0-9]{64}$')
 size_bytes:int
class Receipt(Strict):
 schema_version:Literal[1]=1
 source_id:Literal['el-paso-planning-fees-sd011']
 source_sha256:Literal['c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12']
 prepared_at:str
 review_mode:Literal['source_images_first_with_prior_title_role_awareness_not_blind']
 candidate_generated:Literal[False]=False
 candidate_consulted:Literal[False]=False
 pages:list[Page]
 observations:list[str]
 legal_currentness:Literal['not_verified']='not_verified'
base=Path(__file__).absolute().parent
pages=[]
for n in range(1,6):
 p=base/f'images/page-{n}.png';b=p.read_bytes();pages.append(Page(physical_page=n,image_path=p.relative_to(base).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b)))
r=Receipt(source_id='el-paso-planning-fees-sd011',source_sha256='c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12',prepared_at=datetime.now(timezone.utc).isoformat(),review_mode='source_images_first_with_prior_title_role_awareness_not_blind',pages=pages,observations=[
'All five full landscape page images were directly viewed before generating or reading a native candidate for this source. Prior title/role knowledge is disclosed; this is not blind review.',
'Page 1 visibly prints 2026 Planning and Community Development and Fee Schedule- Effective Date May 1, 2026. This is a printed claim only; no adopted/effective/current status established.',
'The page-1 table has APPLICATION TYPE, Application Fees with superscript 1, and Project Type columns. A, B, C, D and C or D are source codes; no definitions or inferred process classes added.',
'Page 1 has Planning- Minor Applications and Engineering- Minor Applications bands. Additional sign on same property-when reviewed at the same time (no surcharge) has $89.00 and a visibly blank Project Type cell; do not inherit B silently.',
'Page 2 Planning- Major Applications continues into page 3 without a repeated section label. Areas & Activities of State Interest has TBD with superscript 13 and D; TBD is neither zero nor an unknown digit.',
'Page 3 Engineering- Major Applications continues into page 4 for Review of standalone Grading and Erosion Control Plans not associated with zoning or subdivision application and Road Disclaimer.',
'Page 3 Erosion & Sediment Quality Control Permit row is very long and reaches the right border of the application cell; potential clipped terminal wording/closing punctuation requires a later native-to-image check, not reconstruction.',
'Page 4 Other rows: Resubmittal of Applications (after 3rd Review) superscript 13 TBD; Recording Fees superscript 14 TBD; USB/flash drive superscript 15 $5.00; Research (hourly rate) $50.00. All four Project Type cells are visibly blank/shaded.',
'Page 5 contains 15 numbered footnotes and three General Notes, with blank fee/project columns. Superscript 5 is shared by Standalone Waiver and Standalone Deviation; superscript 13 occurs both for state-interest activities and resubmittals.',
'Footnote 1 says application fees include a $37.00 technology fee, not an additional $37 automatically to be added. Footnote 5 states a combined maximum of two waiver/deviation requests per land use application is included (no extra fee).',
'Footnote 4 excludes 2nd kitchens in house. Footnotes 8 and 9 distinguish final plat amendment levels. Footnote 10 includes several different percentage thresholds and all-increases PC/BoCC statement; preserve its literal addition or area phrase pending native comparison.',
'Footnote 11 says over 200 acres, more than 100 dwelling units, or including more than 10 acres developable non-residential space. Footnote 12 lists specific minor special uses. Conditions remain linked to their source rows.',
'General Note 1 gives PCD Director discretion for exceptional circumstances with non-exhaustive examples. General Note 2 has a County staff error/unnecessary-application exception to no-refund wording after a review cycle. General Note 3 preserves technical-expertise trigger, applicant costs and prior-to-formal-submittal agreement. No unconditional waiver, refund denial or fixed surcharge inferred.',
'Numeric amounts, lot/acres/cubic-feet thresholds, concurrent-review qualifications, hourly basis, repeated category labels, blank cells and source spellings are to remain strings and exact text. No arithmetic repairs or fee calculations.',
'No original HTTP acquisition was witnessed in this check. The PDF is received-package evidence; repository intake completion is not asserted.'
])
for name,b in [('VISUAL_OBSERVATIONS.json',(r.model_dump_json(indent=2)+'\n').encode()),('VISUAL_OBSERVATIONS.schema.json',(json.dumps(Receipt.model_json_schema(),indent=2)+'\n').encode())]:
 if name.endswith('OBSERVATIONS.json'):Receipt.model_validate_json(b)
 with (base/name).open('xb') as f:f.write(b)
print('Frozen',hashlib.sha256((base/'VISUAL_OBSERVATIONS.json').read_bytes()).hexdigest(),r.prepared_at)
