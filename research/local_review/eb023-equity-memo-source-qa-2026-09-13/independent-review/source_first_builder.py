from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

OUT=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/eb023-independent-source-review-2026-09-13')
SRC=OUT.parent/'ebenezer-023-024/01-source-only/larimer-equity-fee-memo-sd007-05'
assert not OUT.exists();(OUT/'source').mkdir(parents=True)
class Asset(BaseModel):
 model_config=ConfigDict(strict=True,extra='forbid')
 path:str;sha256:str=Field(pattern=r'^[0-9a-f]{64}$');size_bytes:int
class Block(BaseModel):
 model_config=ConfigDict(strict=True,extra='forbid')
 id:str;page:int;kind:Literal['masthead','metadata','heading','paragraph','bullet','table_header','table_fragment','footnote','attachment','page_number','graphic_note'];text:str;association:str|None=None
class FirstReview(BaseModel):
 model_config=ConfigDict(strict=True,extra='forbid')
 source_id:str;review_phase:Literal['source_images_before_current_phase_ocr_comparison'];frozen_at:str;assets:list[Asset];blocks:list[Block];scope_notes:list[str];legal_currentness:Literal['not_verified'];complete_four_pages:Literal[True]
assets=[]
for name in ['original.pdf',*[f'page-{n:04d}.png' for n in range(1,5)]]:
 raw=(SRC/name).read_bytes();ref=Asset(path='source/'+name,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw));Asset.model_validate_json(ref.model_dump_json());(OUT/ref.path).write_bytes(raw);assets.append(ref)
assert assets[0].sha256=='9b8ba4e32fee82e5d632b53a7da19ad626438ef130b750e73e09b591fc9e7b14'
blocks=[]
def add(id,page,kind,text,association=None): blocks.append(Block(id=id,page=page,kind=kind,text=text,association=association))
add('P1-MASTHEAD',1,'masthead','LARIMER COUNTY | COMMUNITY DEVELOPMENT\nP.O. Box 1190, Fort Collins, Colorado 80522-1190')
add('P1-TO',1,'metadata','To: Board of County Commissioners')
add('P1-FROM',1,'metadata','From: Rebecca Everette, Community Development Director')
add('P1-DATE',1,'metadata','Date: Admin Matters, December 19, 2023')
add('P1-RE',1,'heading','Re: Planning and Engineering Development Review Fee Implementation (January 2, 2024) and Revised Resolution Declaring Equity Fee Reduction to Achieve Community Benefits')
add('P1-H1',1,'heading','Purpose')
add('P1-P1',1,'paragraph','At the November 20, 2023 work session, the Board of County Commissioners provided direction on the full implementation of new Planning and Engineering Development Review Fees, scheduled to take effect in January 2024. Staff has revised the development review fee schedule and the Equity Fee Reduction resolution based on that guidance. The revisions include several adjustments to simplify the fee structure, streamline the administration of fees, and improve customer service. New fees have also been added for Special Event Permits and Larimer County Sheriff’s Office Wildfire Review.')
add('P1-P2',1,'paragraph','Staff recommend adoption of the new Fee Schedule effective January 2, 2024 (Attachment A) and the Revised Equity Fee Resolution (Attachment B) at the Administrative Matters meeting on December 19, 2023.')
add('P1-H2',1,'heading','Background')
add('P1-P3',1,'paragraph','In 2022, following a Fee Study conducted by Ayres Associates, the Board of County Commissioners approved new Planning and Engineering Development Review Fees. The goals of the fee study were to evaluate the full “cost of service” for various types of planning and engineering applications. At full implementation, the new fees aim to recoup overall (about 90%) service cost on most Planning and Engineering application types.')
add('P1-P4',1,'paragraph','In January 2023, the first 50% of the fee increases took effect. In some specific instances, fee amounts decreased to accurately account for staff time or to incentivize certain project types that provide a community service (e.g., zoning verifications). The second 50% of the fee changes are scheduled to take effect in January 2024. In addition to approving a new fee schedule, the Board of County Commissioners also adopted a resolution that allows for fee reductions for certain application types that support community goals.')
add('P1-P5',1,'paragraph','Following the 50% implementation in 2023, staff identified several challenges and opportunities for improvement, including:', 'CHALLENGES')
add('P1-GRAPHIC',1,'graphic_note','Blue rules and a green mountain logo with the visible words LARIMER COUNTY. No printed page number is visible on physical page 1.')
add('P2-GRAPHIC',2,'graphic_note','Green mountain logo with the visible words LARIMER COUNTY and blue rule at top.')
add('P2-B1',2,'bullet','The new fee structure created many new fee categories, which did not easily align to the County’s existing accounting structures and Energov system.','CHALLENGES')
add('P2-B2',2,'bullet','Some of the fee categories are duplicative or overlapping, which has created confusion for customers and made it difficult for staff to consistently interpret and administer.','CHALLENGES')
add('P2-B3',2,'bullet','Some fee amounts are very close to one another (e.g., $5 to $10 difference) for similar services, which introduces unnecessary complexity.','CHALLENGES')
add('P2-B4',2,'bullet','The “equity fee reduction” option has been beneficial for several projects. However, the resolution, as written, does not account for all situations where such a fee reduction could be beneficial.','CHALLENGES')
add('P2-H1',2,'heading','Recommended Changes to Fee Schedule')
add('P2-P1',2,'paragraph','Implementation of the full (100%) fee amounts is scheduled to take effect January 2, 2024. To simplify implementation and improve the customer experience, staff recommend several minor adjustments to the fee schedule. Recommendations include:','FEE_RECOMMENDATIONS')
add('P2-B5',2,'bullet','Combine fee categories that are very similar in nature. In the case where the fees may differ slightly, use averaging or cost recovery data to determine the most appropriate fee amount.','FEE_RECOMMENDATIONS')
add('P2-B6',2,'bullet','Round fees up or down to the nearest $5 increment to simplify customer communication and understanding.','FEE_RECOMMENDATIONS')
add('P2-B7',2,'bullet','Eliminate fees that are duplicative or unnecessary.','FEE_RECOMMENDATIONS')
add('P2-B8',2,'bullet','Add the Consumer Price Index (CPI) factor at the same time building permit fees are adjusted in July 2024 (rather than January).','FEE_RECOMMENDATIONS')
add('P2-B9',2,'bullet','Reorganize fee structure to improve the ease of use.','FEE_RECOMMENDATIONS')
add('P2-P2',2,'paragraph','At the November 20 work session, staff proposed a change to absorb the cost of meeting publication and notification letters into each fee category, rather than calculating those fees on a project-by-project basis. While generally supported by the Commissioners, additional review and analysis is needed to implement this change, so it will be reconsidered at a future date.')
add('P2-H2',2,'heading','Recommended Changes to Equity Fee Resolution')
add('P2-P3',2,'paragraph','The Equity Fee Resolution establishes a lower fee for certain small-scale projects. Additionally, it includes some discretion to consider projects that might fit the Comprehensive Plan or other plan goals and that the Director could discuss with the Board of County Commissioners to allow for a reduced fee. The Resolution is set to expire on December 31, 2023.')
add('P2-P4',2,'paragraph','The following application types are currently eligible for reduced fees:','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P2-B10',2,'bullet','Accessory Living Areas that an owner is building to make available for long-term housing, as attested through an Affidavit or Extended Family Dwellings;','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P2-B11',2,'bullet','Childcare facilities;','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P2-PAGE',2,'page_number','2')
add('P3-GRAPHIC',3,'graphic_note','Green mountain logo with the visible words LARIMER COUNTY and blue rule at top.')
add('P3-B1',3,'bullet','Small businesses registered in Larimer County with three (3) or fewer employees doing site plan or tenant finish;','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P3-B2',3,'bullet','Subdivisions with fewer than three (3) lots;','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P3-B3',3,'bullet','Minor modifications or site upgrades to achieve Comprehensive Plan or Climate and Sustainability Plan goals. These may include but are not limited to installation of lighting to achieve dark sky lighting goals, water efficiency landscaping improvements, renewable energy infrastructure installations on a commercial site, or local food related agricultural projects; and','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P3-B4',3,'bullet','At the discretion of the Director or by the Director in consultation with the Board of County Commissioners, other projects that may achieve Comprehensive Plan, Climate and Sustainability Plan goals, or other Larimer County Strategic Plan objectives.','EXISTING_ELIGIBILITY_AS_MEMO_STATES')
add('P3-P1',3,'paragraph','Staff recommends extending the Equity Fee Reduction Resolution for 4 more years (to 2027), with the following adjustments:','EQUITY_RECOMMENDATIONS')
add('P3-B5',3,'bullet','For the small business category, broaden the language to increase the maximum number of employees (from 3 to 10) and the types of development applications that qualify (any application type)','EQUITY_RECOMMENDATIONS')
add('P3-B6',3,'bullet','Add a category for affordable housing projects','EQUITY_RECOMMENDATIONS')
add('P3-B7',3,'bullet','Add a category for accessory uses on agricultural properties','EQUITY_RECOMMENDATIONS')
add('P3-B8',3,'bullet','Remove the equity fee option for Extended Family Dwellings, which are already subject to a lower fee than similar project types','EQUITY_RECOMMENDATIONS')
add('P3-H1',3,'heading','Special Event Permit Fees')
add('P3-P2',3,'paragraph','Based on feedback from the Board of County Commissioners at the December 4, 2023 work session, a new fee structure is proposed for special event permits, with tiered fees based on the scale and impact of the event, as follows:','SPECIAL_EVENT_PROPOSAL')
add('P3-T-H',3,'table_header','Event Type | Fee | Event includes at least one of the following characteristics:','SPECIAL_EVENT_TABLE')
add('P3-T1-LABEL',3,'table_fragment','Tier 1 (up to 500 people)','TIER1/event_type')
add('P3-T1-FEE',3,'table_fragment','$200\n$100 (non-profit or community group)\n$25 DNR fee*','TIER1/fee')
add('P3-T1-C1',3,'table_fragment','Max. attendance of up to 500 people','TIER1/characteristics/1')
add('P3-T1-C2',3,'table_fragment','Minor impacts to roadways, adjacent property owners, and adjacent neighborhoods','TIER1/characteristics/2')
add('P3-T1-C3',3,'table_fragment','Minor transportation impacts','TIER1/characteristics/3')
add('P3-T1-C4',3,'table_fragment','Generally, does not require Larimer County Sheriff’s Office or Department of Natural Resources staffing beyond normal operations','TIER1/characteristics/4')
add('P3-T2-LABEL',3,'table_fragment','Tier 2 (up to 1500 people)','TIER2/event_type')
add('P3-T2-FEE',3,'table_fragment','$500\n$250 (non-profit or community group)','TIER2/fee/part1')
add('P3-T2-C1',3,'table_fragment','Max. attendance of up to 1,500 people','TIER2/characteristics/1')
add('P3-T2-C2',3,'table_fragment','Moderate impacts to roadways, adjacent property owners, and adjacent neighborhoods','TIER2/characteristics/2')
add('P3-PAGE',3,'page_number','3')
add('P4-GRAPHIC',4,'graphic_note','Green mountain logo with the visible words LARIMER COUNTY and blue rule at top.')
add('P4-T2-LABEL',4,'table_fragment','','TIER2/event_type/blank_continuation_cell')
add('P4-T2-FEE',4,'table_fragment','$100 DNR fee*','TIER2/fee/part2')
add('P4-T2-C3',4,'table_fragment','Moderate transportation impacts (e.g., removal of parking, off-site parking and circulation plan, requires a traffic impact study)','TIER2/characteristics/3')
add('P4-T2-C4',4,'table_fragment','Requires limited to moderate Larimer County Sheriff’s Office or Department of Natural Resources staffing beyond normal operations','TIER2/characteristics/4')
add('P4-T3-LABEL',4,'table_fragment','Tier 3 (>1500 people)','TIER3/event_type')
add('P4-T3-FEE',4,'table_fragment','$1000\n$500 (non-profit or community group)\n$250 DNR fee*','TIER3/fee')
add('P4-T3-C1',4,'table_fragment','Attendance estimated to be greater than 1,500 people','TIER3/characteristics/1')
add('P4-T3-C2',4,'table_fragment','Moderate to severe impacts to roadways, adjacent property owners, and adjacent neighborhoods','TIER3/characteristics/2')
add('P4-T3-C3',4,'table_fragment','Moderate to severe transportation impacts (e.g., removal of parking, off-site parking and circulation plan, requires a traffic impact study, major mitigation measures required, major impacts to transit)','TIER3/characteristics/3')
add('P4-T3-C4',4,'table_fragment','Requires significant Larimer County Sheriff’s Office or Department of Natural Resources staffing, including moderate to major support in the venue','TIER3/characteristics/4')
add('P4-TR-LABEL',4,'table_fragment','Full Road Closure','ROAD/event_type')
add('P4-TR-FEE',4,'table_fragment','$500','ROAD/fee')
add('P4-TR-C1',4,'table_fragment','Full closure of at least one roadway, in addition to permit fee','ROAD/characteristics/1')
add('P4-TR-C2',4,'table_fragment','Does not include block party closures','ROAD/characteristics/2')
add('P4-FN1',4,'footnote','*Department of Natural Resources Fee: Applies to events on or adjacent to lands owned or managed by the Larimer County Department of Natural Resources. Additional fees for event staffing will be negotiated on a case-by-case basis, per Department of Natural Resources policy.','TIER1,TIER2,TIER3/DNR_fee')
add('P4-H1',4,'heading','Sheriff’s Office Wildfire Review Fee')
add('P4-P1',4,'paragraph','On December 11, 2023, the Board provided direction on new wildfire review fees for development projects within the jurisdiction of the Larimer County Sheriff’s Office. The Planning and Engineering Development Review Fee Schedule has been updated to include those fees as proposed.')
add('P4-H2',4,'heading','Next Steps')
add('P4-P2',4,'paragraph','If adopted, staff will communicate the fee adjustments to customers and implement the new fee schedule beginning January 2, 2024.')
add('P4-P3',4,'paragraph','Staff recommends a follow-up review of the development review fee schedule every five years to re-evaluate the County’s service cost recovery goal and make necessary adjustments. Accordingly, the next major fee study would occur in 2027.')
add('P4-GRAPHIC2',4,'graphic_note','Thin colored horizontal scan marks cross the lower part of the first line of the follow-up review paragraph and continue into the right margin. Wording remains visible; this is not treated as a strike-through instruction.')
add('P4-H3',4,'heading','Attachments')
add('P4-A1',4,'attachment','Attachment A: Proposed New Fee Schedules for January, 2 2024 (100% implementation)')
add('P4-A2',4,'attachment','Attachment B: Revised Resolution Declaring Equity Fee Reduction for Planning and Engineering and Development Review Fees for Certain Application Types that Achieve Community Benefits')
add('P4-PAGE',4,'page_number','4')
review=FirstReview(source_id='larimer-equity-fee-memo-sd007-05',review_phase='source_images_before_current_phase_ocr_comparison',frozen_at=datetime.now(timezone.utc).isoformat(),assets=assets,blocks=blocks,scope_notes=[
 'All four complete 300dpi source PNGs were directly viewed at approximately 04:40 UTC on September 13, 2026, before current-phase candidate/OCR or root-note consultation. Display tool resized them from2550x3300 to1376x1780; full-resolution source PNGs are preserved.',
 'This is not blind QA: I prepared the packet previously and know the parent/reviewer concerns. Current-phase text was transcribed from the source images before candidate comparison.',
 'Whitespace and line wrapping are normalized; spelling, visible punctuation, amounts, qualifiers and source anomalies are preserved as observed. Exact font glyph codepoints, incidental raster specks and decorative geometry are not certified.',
 'There are four logical special-event rows, five physical row fragments: Tier2 spans physical pages3 and4. The blank p4 event-type continuation cell does not create a new unnamed tier.',
 'All prose, headings, bullets, table wording, notes, attachments and visible page numbers are represented. Decorative logos/rules are described separately.',
 'This is a staff memo recommending adoption; Attachment A/B are referenced but not contained in these four pages. No executed resolution, adoption or current legal effect is inferred.',
],legal_currentness='not_verified',complete_four_pages=True)
raw=review.model_dump_json(indent=2)+'\n';FirstReview.model_validate_json(raw)
(OUT/'SOURCE_FIRST.json').write_text(raw);(OUT/'SOURCE_FIRST.schema.json').write_text(json.dumps(FirstReview.model_json_schema(),indent=2)+'\n')
shutil.copyfile(__file__,OUT/'source_first_builder.py')
print('blocks',len(blocks),'sha',hashlib.sha256(raw.encode()).hexdigest(),review.frozen_at)
