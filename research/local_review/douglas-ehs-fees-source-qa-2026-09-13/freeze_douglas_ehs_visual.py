"""Freeze Atlas's direct image transcription before inspecting this PDF's native text."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

BASE = Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12')
SOURCE = BASE / 'douglas-castle-rock-discovery/pdf-evidence/E017/page-0001.png'
OUT = BASE / 'douglas-ehs-source-qa'

class Row(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    row_id: str
    table: Literal['county', 'state']
    authority: str
    program: str
    fee_type: str
    unit: str
    fee: str | None

class Transcript(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal[1] = 1
    reviewer: Literal['Atlas'] = 'Atlas'
    frozen_at: str
    source_sha256: str
    image_sha256: str
    method: str
    headings: list[str]
    rows: list[Row] = Field(min_length=44, max_length=44)
    footnotes: list[str]
    limitations: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'

COUNTY = '''25-1-508|Body Art|Body Art License|Annual|$355.00
25-1-508|Body Art|Special Event Inspection|Hourly|$60.00
25-1-508|Body Art|Plan Review Application|Per Application|$100.00
25-1-508|Body Art|Environmental Health Specialist, Plan Review (per additional hour)/Change of Owner/Site Assessment/Additional Inspections|Hourly|$60.00
25-1-508|Child Care|Part Day Program Inspection (Less than 4 hours in care)|Per Routine Inspection|$175.00
25-1-508|Child Care|Full Day or 24-Hour Care Program Inspection (4 hours or more in care)|Per Routine Inspection|$240.00
25-1-508|Child Care|Plan Review Application|Per Plan Review|$100.00
25-1-508|Child Care|Environmental Health Specialist, Plan Review (per additional hour)/Change of Owner/Site Assessment/Additional Inspections|Hourly|$60.00
25-4-1607|Retail Food|Special Events License|Annual|$135.00
25-4-1607|Retail Food|Special Event Plan Review Application (2-5 vendors)|Per Event|$115.00
25-4-1607|Retail Food|Special Event Plan Review Application (5 + vendors)|Per Event|$230.00
25-1-508|Retail Food|Special Event Plan Review Late Fee|Per Late Application|$60.00
25-1-508|Retail Food|Education, 2 Hour In-Service Training|Per Training|$100.00
25-1-508|Land Use and ERRs|Environmental Health Consulting, Land Use/Environmental Record Reviews|Hourly|$60.00
25-1-508|Recreational Water|Pool / Spa / Spray Pad (by filtration system)|Annual|$180.00
25-1-508|Recreational Water|Plan Review Application|Per Plan Review|$100.00
25-1-508|Recreational Water|Environmental Health Specialist, Plan Review (per additional hour)/Change of Owner/Site Assessment/Additional Inspections|Hourly|$60.00
25-1-107|Onsite Wastewater Treatment System|New Permit**|Per Permit**|$1,060.00
25-1-107|Onsite Wastewater Treatment System|Major Repair or Expansion Permit**|Per Permit**|$695.00
25-1-107|Onsite Wastewater Treatment System|Minor Repair**|Per Permit**|$390.00
25-1-107|Onsite Wastewater Treatment System|Use Permit Application Fee|Per Permit|$65.00
25-1-107|Onsite Wastewater Treatment System|Variance Request (New/Repair Permit)|Hourly|$60.00
25-1-107|Onsite Wastewater Treatment System|New/Repair Permit Renewal|Per Permit|$55.00
25-1-107|Onsite Wastewater Treatment System|Re-Inspection|Per Inspection|$100.00
25-1-109|Onsite Wastewater Treatment System|Installers License (New/Renewal)|Annual|$40.00
25-1-109|Onsite Wastewater Treatment System|Cleaners License (New/Renewal)|Annual|$40.00
25-1-107|Onsite Wastewater Treatment System|Enforcement|Per Day|$50.00'''
STATE = '''25-4-1607|Retail Food|No Fee License (K-12 Schools, Non-profit)|Annual|$0.00
25-4-1607|Retail Food|License, Limited Food Service (Convenience, Other)*|Annual|$338.00
25-4-1607|Retail Food|Restaurant (Seating 0-100)*|Annual|$481.00
25-4-1607|Retail Food|Restaurant (Seating 101-200)*|Annual|$538.00
25-4-1607|Retail Food|Restaurant (Seating >200)*|Annual|$581.00
25-4-1607|Retail Food|Grocery Store (0-15,000 sq. ft.)*|Annual|$244.00
25-4-1607|Retail Food|Grocery Store (>15,000 sq. ft.)*|Annual|$441.00
25-4-1607|Retail Food|Grocery Store with Deli (0-15,000 sq. ft.)*|Annual|$469.00
25-4-1607|Retail Food|Grocery Store with Deli (>15,000 sq. ft.)*|Annual|$894.00
25-4-1607|Retail Food|Mobile Unit (Prepackaged, Non-TCS)*|Annual|$338.00
25-4-1607|Retail Food|Mobile Unit (Full Service)*|Annual|$481.00
25-4-1607|Retail Food|Change of Ownership or Site Evaluation (Initial Inspection)|Per Assessment|$120.00
25-4-1607|Retail Food|Plan Review Application|Per Plan Review|$155.00
25-4-1607|Retail Food|HACCP Plan, Written|Hourly|Up to $620
25-4-1607|Retail Food|HACCP Plan, Onsite Evaluation|Hourly|Up to $620
25-4-1610|Retail Food|Penalty Assessment, Late License Renewal|Per Assessment|
25-4-1611|Retail Food|Penalty Assessment, Enforcement|Per Assessment|'''

def main():
    rows=[]
    for table, text in [('county', COUNTY), ('state', STATE)]:
        for i, line in enumerate(text.splitlines(), 1):
            authority, program, fee_type, unit, fee = line.split('|')
            rows.append(Row(row_id=f'{table.upper()}-{i:02}',table=table,authority=authority,
                            program=program,fee_type=fee_type,unit=unit,fee=fee or None))
    transcript=Transcript(
        frozen_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        source_sha256='35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687',
        image_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        method='Atlas directly inspected the full supplied 1650 by 1275 page image. No native text for E017 was opened before this freeze. Prior discovery summary was known, so this is source-first row transcription, not a fully blind independent review.',
        headings=['DOUGLAS COUNTY HEALTH DEPARTMENT COLORADO',
                  'Fees Set By Douglas County Board of Health - Effective November 1, 2025',
                  'Fees Set By State Legislation - Effective September 1, 2025',
                  'Authority | Program | Environmental Health Fee Type | Unit of Activity | 2026 Fee'],
        rows=rows,
        footnotes=['**The CDPHE Water Quality Division assesses a fee of $23 for each authorized new and repair permit for OWTS. $20 is transmitted to CDPHE and $3 is retained by LPHA for administrative costs.',
                   '*The Colorado Department of Public Health and Environment assesses a fee $43 of each retail food license issued. Increases to $55 in 2025.'],
        limitations=['Exact font glyph/code points and wordmark spacing are not certified by this image transcription.',
                     'Two blank penalty fee cells are preserved as null, not zero or unknown computed fees.',
                     '2026 fee column and 2025 effective captions are separate source wording; actual adoption/currentness unverified.',
                     'No fee arithmetic, statutory interpretation, ownership-of-law or complete county coverage is certified.'])
    OUT.mkdir(exist_ok=False)
    (OUT/'PASS1_frozen.json').write_text(transcript.model_dump_json(indent=2)+'\n')
    (OUT/'PASS1.schema.json').write_text(json.dumps(Transcript.model_json_schema(),indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'sha256':hashlib.sha256((OUT/'PASS1_frozen.json').read_bytes()).hexdigest()}))

if __name__=='__main__':main()
