"""Build and verify bounded Atlas source QA without legal-effect promotion."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Literal
import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

BASE=Path(__file__).resolve().parent
SHA='79795d6650664c33808b3877e97b04fd31a84ab1a6bda8ab658c3153cbbe3993'
URL='https://www.gjcity.org/DocumentCenter/View/15790/2024-IFC-Adoption-Ordinance-No-5269'
class Strict(BaseModel):
    """Reject fields not declared in the research contract."""
    model_config=ConfigDict(extra='forbid')
class Asset(Strict):
    """Identify exact local evidence bytes."""
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)
class Span(Strict):
    """Preserve one exhaustive, unchanged native line and its byte offsets."""
    id:str
    start:int=Field(ge=0)
    end:int=Field(gt=0)
    text:str
class Page(Strict):
    """Bind an inspected full page to original embedded text and a render."""
    physical_page:int=Field(ge=1,le=29)
    native:Asset
    image:Asset
    native_spans:list[Span]
    full_page_directly_viewed:Literal[True]=True
    review_scope:Literal['structure_and_selected_language_not_character_certification']
    topic_map:str
class Ref(Strict):
    """Bind an annotation to an exact page-byte range, including imperfect OCR."""
    physical_page:int=Field(ge=1,le=29)
    start:int=Field(ge=0)
    end:int=Field(gt=0)
    native_excerpt:str
    excerpt_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
class Note(Strict):
    """A source observation rather than an extracted enforceable rule."""
    id:str
    kind:Literal['date_conflict','adoption_scope','source_anomaly','exceptions',
                 'fee_reference','section_map','graphic','signature','limitation']
    statement:str
    references:list[Ref]=Field(min_length=1)
    visual_reading:str|None=None
    legal_currentness:Literal['not_verified']='not_verified'
class Heading(Strict):
    """A literal native navigation candidate, not a complete legal-unit index."""
    span_id:str
    physical_page:int
    text:str
class Review(Strict):
    """Preserve all pages while explicitly withholding legal/currentness conclusions."""
    schema_version:Literal[1]=1
    source_id:Literal['grand-junction-ordinance5269']
    reviewed_at:AwareDatetime
    reviewer:Literal['Atlas']='Atlas'
    mode:Literal['candidate_aware_direct_source_review']
    source:Asset
    access_receipt:Asset
    official_url:str
    native_extractor:Literal['PyMuPDF 1.28.2, text, flags=195, sort=False']
    render_method:Literal['Poppler pdftoppm, full pages, 120 dpi PNG']
    source_metadata:dict
    native_bytes:Literal[68078]
    source_pages:Literal[29]
    visually_viewed_pages:list[int]=Field(min_length=29,max_length=29)
    pages:list[Page]=Field(min_length=29,max_length=29)
    heading_candidates:list[Heading]
    annotations:list[Note]
    legal_currentness:Literal['not_verified']='not_verified'
    effective_date:None=None
    effective_date_status:Literal['conflicting_source_statements_unresolved']
    semantic_rule_units_created:Literal[False]=False
    native_text_edited:Literal[False]=False
    word_level_transcription_certified:Literal[False]=False
    all_graphic_dimensions_certified:Literal[False]=False
    scope_limits:list[str]
    @model_validator(mode='after')
    def identities(self) -> Review:
        """Require each physical page exactly once and unambiguous annotation IDs."""
        if [p.physical_page for p in self.pages]!=list(range(1,30)):
            raise ValueError('missing, duplicated or reordered page')
        if self.visually_viewed_pages!=list(range(1,30)):
            raise ValueError('visual coverage mismatch')
        ids=[x.id for x in self.annotations]
        if len(ids)!=len(set(ids)):raise ValueError('duplicate annotation ID')
        return self
class Manifest(Strict):
    """Inventory the immutable package without self-reference."""
    schema_version:Literal[1]=1
    files:list[Asset]
    excluded:list[str]
def asset(path:Path) -> Asset:
    """Return exact file identity."""
    b=path.read_bytes()
    return Asset(path=str(path.relative_to(BASE)),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
def new(path:Path,text:str) -> None:
    """Write a new validated record atomically without overwriting evidence."""
    if path.exists():raise FileExistsError(path)
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(path)
def ref(page:int,start:str|None=None,end:str|None=None) -> Ref:
    """Locate an exact substring range; a null start explicitly binds the whole page."""
    b=(BASE/f'page-{page:02d}.native.txt').read_bytes()
    if start is None:a,z=0,len(b)
    else:
        needle=start.encode();a=b.index(needle)
        if b.find(needle,a+1)!=-1:raise ValueError(('ambiguous anchor',page,start))
        if end is None:z=a+len(needle)
        else:z=b.index(end.encode(),a)+len(end.encode())
    excerpt=b[a:z]
    return Ref(physical_page=page,start=a,end=z,native_excerpt=excerpt.decode(),excerpt_sha256=hashlib.sha256(excerpt).hexdigest())
TOPICS=[
'City title and recitals; 15.44.010 adoption by reference and selected appendices; beginning15.44.020 enforcement.',
'15.44.020 continuation;15.44.030 city definitions/delegation;15.44.040 amendments;105.1.7 permit fees;105.5 selective deletion list begins.',
'105.5 retained-list continuation and other review processes;105.5.51 operational tents;105.6.22 mobile-stage exception;105.6.25 construction tents and continuing exceptions.',
'Continuation of tent exceptions;105.5.30 LP-gas operational permit and R-3 exception;105.6.16 construction permit;105.5.18 fuel-generator exception;112.1 appeals board;202 mobile-stage definition begins.',
'202 definitions continue: mobile stage, bonfire, fire pit, household waste, nonattainment, open burning, permanent fire pit/fireplace.',
'202 recreational fire, salvage and vegetative-material definitions;203.9.5 R-5 occupancy;304.1.3 vegetation removal with dwelling exceptions and preserved other laws.',
'307 outdoor burning replacement begins;307.1 general permit/code conditions;weather/fire-watch prohibition and two exceptions;household-waste list begins.',
'Waste list continues;salvage prohibition;owner permission;burn restrictions;307.2 permit requirement and no-permit categories;state/local approvals;extinguishment discretion.',
'307.4 bonfire,recreational,portable/nonportable/permanent fire distances;general/agricultural burning and parcel/daily limits begin.',
'307.4.6 items2–12 seasonal,timing,attendance,materials and air-control conditions;307.4.7 case-by-case prescribed burns.',
'307.5 attendance/equipment;307.6 twelve no-permit categories begins, with regulatory qualifications.',
'307.6 list completion;307.7 cost recovery and penalties;308.1.4.1 egress devices;308.1.6.3 sky-lantern prohibition;311.1.1 abandoned premises;311.3 additions begin.',
'311.3 enforcement,notice,assessment,collection and penalties;311.5 placarding authority.',
'322.1.1.1 micromobility egress;401.2 conditional emergency plans;503.1 access;503.2.3.1 surface;503.2.4 turning modeling;503.2.5 dead-end exception begins.',
'Dead-end exception completes;503.2.9 loop-lane ten standards;503.2.10 shared-driveway heading begins.',
'Shared-driveway eight standards;511/511.1 RV/mobile/manufactured housing hydrants and access.',
'901.3.1 conditional small-system permit exception;903 sprinkler/system amendments;907 false-alarm additions with970-number anomaly;intentional misuse clause begins.',
'False-alarm conditions,fee resolution and30-day stabilization;1103.1 existing-building exception;3103.2 tent approval and exceptions begin.',
'Tent exceptions complete;3405 outdoor tires replacement and eight resulting subsections;6101.2 LP-gas permits/application begins.',
'LP application continuation;6101.3 documents;6101.4 prohibitions and exceptions including incomplete sentence;6105.1 approved equipment;NFPA855 edition replacement begins.',
'NFPA855-23 replacement completes;B103.4 alternative fire-flow methods;C102.2 looped water supply and exceptions1–4 begin.',
'C102.2 exceptions4–6 continue;C102.3 hydrant installation;D102.1 access/surface approval;D102.2 private driveway definition begins.',
'Driveway width discretion;D103.1 turnaround replacement and graphic;D103.2 grade rule and approval exception.',
'D103.4.1 sprinkler-provision-exception table;D103.4.2 intermediate turnaround authority;D103.6 andD103.6.1 signs.',
'D103.6.2–.4 signs;D105.1 sprinkler exception;D107.1 andD107.2 access conditions;AppendixO103.4 valet-trash sprinkler condition.',
'15.44.050 new permit categories with hearing opportunity;15.44.060 flammable liquids zones;15.44.070 LP-gas zones;15.44.080 explosives heading.',
'Explosives prohibition/safeguards continuation;printed15.44.90 appeals and fee;15.44.100 penalties;unamended IFC adoption,conflict repeal,September1 effective clause;public hearing/copy-on-file statements.',
'Copy inspection availability continuation;June18 introduction andJuly16 second reading;printed president/city-clerk roles,signature marks and seal.',
'Clerk certification;June18 introduction,July16 adoption/hearing,July21 certification;publicationJune21/July19;August18 effective statement;signature mark and seal.'
]
def build() -> Review:
    """Build source-bound structure and observations after direct full-page inspection."""
    pages=[];headings=[]
    for n in range(1,30):
        spans=[];pos=0
        for i,line in enumerate((BASE/f'page-{n:02d}.native.txt').read_text().splitlines(True),1):
            span=Span(id=f'P{n:02d}-L{i:03d}',start=pos,end=pos+len(line.encode()),text=line)
            spans.append(span);pos=span.end
            if re.match(r'^(?:Section |15\.44\.|Chapter |Appendix |Figure |TABLE |MISCELLANEOUS|PUBLIC HEARING)',line):
                headings.append(Heading(span_id=span.id,physical_page=n,text=line))
        pages.append(Page(physical_page=n,native=asset(BASE/f'page-{n:02d}.native.txt'),image=asset(BASE/f'page-{n:02d}.png'),native_spans=spans,review_scope='structure_and_selected_language_not_character_certification',topic_map=TOPICS[n-1]))
    notes=[]
    def note(kind:str,statement:str,refs:list[Ref],visual:str|None=None) -> None:
        notes.append(Note(id=f'GJO-{len(notes)+1:03d}',kind=kind,statement=statement,references=refs,visual_reading=visual))
    note('date_conflict','Lead finding: two incompatible explicit effective-date statements appear in the same source. Page27 body states September1,2025; page29 certification states August18,2025. Neither is selected as controlling. Earlier three-page discovery did not inspect page27 and remains a frozen, narrower observation.',
         [ref(27,'The adopted ordinance shall be effective as of September 1 ,2025.'),ref(29,'Effective: August 18, 2025')],
         'Page27: The adopted ordinance shall be effective as of September 1, 2025. Page29: Effective: August 18, 2025. Spacing here is a visual reading; native byte spacing is preserved in references.')
    note('adoption_scope','Title and15.44.010 adopt2024 IFC by reference with listed Appendices B,C,D,E,F,G,H,I,N,O, subject to local deletions/modifications. Page27 adopts unamended IFC sections as published and repeals conflicting instruments with its stated exception. This29-page instrument does not contain the entire referenced model code.',[ref(1),ref(27,'All sections of the 2024 IFC','except as otherwise provided herein.')])
    note('adoption_scope','The ordinance identifies city jurisdiction;15.44.030 defines jurisdiction as City of Grand Junction and city officers/designees. No county or separate rural-fire-district adoption is inferred.',[ref(1),ref(2,'15.44.030 Definitions.','15.44.040 Amendments to the International Fire Code.')])
    note('fee_reference','105.1.7 says permit rates and fees shall be adopted by City Council resolution. This is a reference to adopting fee authority, not a complete fee schedule or confirmation of a separately published fee PDF.',[ref(2,'105.1.7 Permit Fees.','resolution.')])
    note('exceptions','105.5 deletes operational-permit subsections with an explicit retained list extending from page2 to page3. The following paragraph says absence of a required operational permit does not absolve other-code compliance and allows other city administrative review. Preserve the entire list and continuation; do not summarize as abolition of permits.',[ref(2,'105.5 Required operational permits.'),ref(2,'its entirety with the exception of','105.5.40 (Outdoor'),ref(3)])
    note('source_anomaly','The retained operational list visibly repeats105.5.39 for Mobile food preparation vehicles and Organic coatings, with105.5.36 Open Burning between. Preserve this numbering as source text; do not silently renumber. Embedded text also has OCR-like punctuation/letter errors.',[ref(2,'woodworking plants,105.5,32','105.5.40 (Outdoor')])
    note('exceptions','105.5.51 and105.6.25 have2400-square-foot baseline tent thresholds, recreational/funeral exceptions, special-use400-square-foot language and mobile stages. The construction-tent exception paragraph itself says operational permit; this source wording is not rewritten. The corresponding3103.2 approval provision spans pages18–19.',[ref(3),ref(4,'square feet.','Section 105.5.30'),ref(18),ref(19,'structures and tents','Exception 4: Mobile Stages.')])
    note('exceptions','LP-gas operational and construction permit provisions distinguish120-gallon thresholds and the operational R-3 container exception.105.5.18 adds a specific fuel-generator-storage exception. These are separate conditions; no generalized exemption is generated.',[ref(4)])
    note('section_map','Definitions on pages4–6 carry substantive size/material/location qualifications. Section304.1.3 vegetation removal includes dwelling exceptions while preserving additional federal,state and county laws. They remain attached to the full native pages.',[ref(4),ref(5),ref(6)])
    note('exceptions','307 burning provisions contain prohibitions and conditional exceptions: hazardous weather/red-flag rules, household-waste and salvage prohibitions, owner permission, permit/no-permit categories,other-agency approvals and extinguishment authority. The exception lists are not converted to unconditional permissions.',[ref(7),ref(8)])
    note('exceptions','307.4 distance and fuel-size requirements differ among bonfires,recreational fires,portable/nonportable and permanent fire pits. General/agricultural burning has parcel,daily,seasonal,time-of-day,attendance/material and air-quality qualifications continuing to page10.',[ref(9),ref(10)])
    note('source_anomaly','The vegetative-material definition discusses small dry-leaf piles, while307.4.6 item9 uses a prohibition sentence containing a parenthetical three-cubic-foot leaf volume. Both are retained; this source review does not reconcile their legal relationship.',[ref(6),ref(10)])
    note('exceptions','307.4.7 uses case-by-case may-be-allowed prescribed burns with advance permit and permit-compliance conditions.307.5 requires attendance/equipment;307.6 lists12 no-permit categories with its own continuing qualifications, not a waiver of all burning regulations.',[ref(10),ref(11),ref(12)])
    note('fee_reference','307.7 cost recovery ties to violation/out-of-control fire conditions,actual city costs,an administrative penalty by Council resolution and possible manager minimums. Its20-day payment,possible20-percent collection charge and8-percent annual interest language is preserved without a combined calculation.',[ref(12,'307.7 Cost Recovery Fee.','recover or collect any amounts owing.')])
    note('section_map','308 egress-device and sky-lantern prohibitions;311 abandoned-premises,notice/abatement/collection and placarding;322 micromobility egress prohibition remain distinct. The311 notice periods and assessments do not become generalized fee rules.',[ref(12),ref(13),ref(14)])
    note('fee_reference','311.3 states60-day work notice,actual costs plus10percent administration,20-day assessment payment and a separate10percent collection penalty under its own conditions. These are not the307.7 percentages and are not merged.',[ref(13)])
    note('exceptions','401.2 begins Where required and retains on-site plans/official request review.503 access/surface/turning provisions include approvals and a sprinkler-conditioned dead-end exception continuing on page15.',[ref(14),ref(15)])
    note('section_map','Loop lanes have ten listed standards; shared driveways have eight,including parking,access,width/length and approval qualifications.511 addresses hydrants/access for named RV/mobile/manufactured housing facilities,with official authority to reduce distance under distinct hazards.',[ref(15),ref(16)])
    note('exceptions','901.3.1 states20 sprinkler heads or less/5 alarm devices or less will not require a permit when approved via a scope-of-work letter review and guidance compliance. This review does not resolve how that clause relates to separate modification-review fees.',[ref(17,'901.3.1 Relocations','and provided by the GJFD.')])
    note('source_anomaly','The false-alarm amendment instruction lists907.6.6.4, but the following visible body heading is970.6.6.4. The body also prints multifunction where malfunction might be expected. Neither anomaly is silently repaired.',[ref(17,'Section 907.6.6. Add','location of the alarm.')])
    note('fee_reference','False-alarm clauses continue across17–18 and distinguish malfunction,improper use,unexplained activation,quarter/year thresholds,and30-day new-system stabilization.907.6.6.4.3 refers to a fee schedule established by Council resolution and filed with Clerk; no actual fee amount is supplied there.',[ref(17),ref(18,'the improper use','before charges will accrue for false alarms.')])
    note('exceptions','1103.1 exception3 conditions specified existing-building interventions on consultation between fire and chief building officials and their stated unsafe/hazardous assessment; no unconditional retrofit directive is inferred.',[ref(18,'Section 1103.1 Required construction.','emergency responders.')])
    note('source_anomaly','The tire-storage directive says delete3405.1 through3405.7, while the replacement visibly includes3405.8 as well. Preserve all eight resulting subsection bodies and the unchanged directive.',[ref(19,'Section 3405 Outdoor Storage.','Section 3405.8.')])
    note('exceptions','6101.4 LP-gas/natural-gas and ancillary-installation prohibitions have separate explicit exceptions;6101.3 document requirements and6105.1 approved-equipment conditions remain separate.',[ref(19),ref(20)])
    note('source_anomaly','The ancillary LP-gas exception visibly ends its technical-report sentence at prior to the equipment before the next section heading. No missing verb/object or intended legal requirement is invented.',[ref(20,'A technical','Section 6105.1 Nonapproved equipment.')],
         'The printed text ends: prior to the equipment. No terminal period is visible at that cutoff.')
    note('section_map','Chapter80 replaces the stated NFPA855-20 reference with855-23. AppendixB103.4 describes an alternative with not-more-than-two-lots and other factual/approval conditions,including recorded memorandum. It is not automatic relief.',[ref(20,'Chapter 80 Referenced Standards'),ref(20,'855-20'),ref(21)])
    note('exceptions','C102.2 looped-water requirements have six numbered exceptions spanning21–22,including distinct residential,multifamily,commercial-size,sprinkler,length/future-connection and impracticability conditions. May-allow/may-require and written-findings terms remain unnormalized.',[ref(21),ref(22)])
    note('section_map','D102 access/private-driveway provisions retain surface approval,150-foot trigger,12-foot baseline and discretion to increase width. D103.1 replaces the turnaround figure and references TEDS; those external standards are not independently collected here.',[ref(22),ref(23)])
    note('graphic','FigureD103.1 contains five turnaround layouts with red/black dimension annotations. The embedded text is badly garbled and loses geometry; it is not a verified numerical figure transcription. The visible90-foot and80-foot cul-de-sac layouts and120-foot hammerhead/alternatives remain image evidence. Red labels are not interpreted as legislative strikeouts.',[ref(23,'Figure D103.1. Add New Figure','Section D103.2.')])
    note('source_anomaly','D103.2 states8percent maximum grade and4percent turnaround grade,followed by an exception reading Grades steeper than10percent as approved by the fire code official. Preserve this exact contrast and approval qualification; no implied range or corrected threshold is supplied.',[ref(23,'D103.2 Grade.','1. Grades steeper than 10 percent as approved by the fire code official.')])
    note('graphic','TableD103.4.1 is expressly a FIRE SPRINKLER PROVISION EXCEPTION. Native extraction reads columns out of order. Visually its0–300 row has20-foot width/None Required;301–500 and501–750 rows each have20-foot width and the same listed turnaround alternatives. The Over750 entry spans the first two columns and has Special Approval Required; no independent width is inferred.',[ref(24,'TABLE D103.4.1','For Sl: 1 foot= 304.8mm')],
         '301–500 and501–750:120-foot Hammerhead,60-foot "Y" or90-foot diameter cul-de-sac in accordance with Figure D103.1. This is a scoped visual association, not an automated fee/rule unit. Native first-row Hannmerhead spelling is preserved separately.')
    note('exceptions','D103.4.2 intermediate turnaround authority andD103.6 signs vary by width/location/official requirement. D105 andD107 sprinkler/access exceptions retain all approval and system conditions. AppendixO valet-trash service is limited to sprinkler-equipped buildings as stated.',[ref(24),ref(25)])
    note('exceptions','15.44.050 requires an opportunity to be heard before specified new permit categories;15.44.060–.080 zoning/storage provisions contain official safety/approval exceptions. The explosives restriction shall not prohibit specified safeguarded storage. Do not flatten these into absolute bans.',[ref(26),ref(27,'Storage of explosives','designee.')])
    note('fee_reference','The printed15.44.90 Appeals clause describes a written appeal and Council-resolution fee within30days,with its own section109 reference. This is preserved alongside112.1 Board-of-Appeals language,without reconciling the numbering.15.44.100 separately references GJMC1.04.090 penalties.',[ref(27,'15.44.90 Appeals.','adopted in this chapter.'),ref(4,'Section 112.1. Amend','Chapter 2')])
    note('signature','Pages28–29 show signature marks and city seals. Page28 prints Cody Kennedy,President of the Council,and City Clerk; page29 prints Deputy City Clerk. Marks are not authenticated identities. Native text on page29 garbles the printed deputy-clerk label,so it is not a reliable signature transcript.',[ref(28),ref(29)],
         'Printed page29 role: Deputy City Clerk. The source-native line remains ^&ep\'uty Cit^feff; no handwritten name is certified.')
    note('adoption_scope','IntroductionJune18,2025 and second reading/adoptionJuly16,2025 are stated on28–29. Page27 schedules a July16 hearing at5:30PM; certification is July21,with publicationJune21 andJuly19. These distinct event dates do not resolve the conflicting effective clauses.',[ref(27,'A public hearing','C.R.S.'),ref(28),ref(29)])
    note('limitation','All29 complete120-dpi page images were directly viewed. This is candidate-aware,with prior discovery1/28/29 readings known. No visible operative-body strikethrough was identified; textual delete/replace directives and red graphic dimensions are not themselves evidence of a tracked-change comparison. Every embedded native byte is preserved without full character-level certification.',[ref(1),ref(23),ref(27),ref(29)])
    with pymupdf.open(BASE/'original.pdf') as doc:metadata=doc.metadata
    return Review(source_id='grand-junction-ordinance5269',reviewed_at=datetime.now(timezone.utc),
        mode='candidate_aware_direct_source_review',source=asset(BASE/'original.pdf'),
        access_receipt=asset(BASE/'access-event.json'),official_url=URL,
        native_extractor='PyMuPDF 1.28.2, text, flags=195, sort=False',
        render_method='Poppler pdftoppm, full pages, 120 dpi PNG',source_metadata=metadata,
        native_bytes=68078,source_pages=29,visually_viewed_pages=list(range(1,30)),pages=pages,
        heading_candidates=headings,annotations=notes,
        effective_date_status='conflicting_source_statements_unresolved',
        scope_limits=['No network access or source-file editing in this task.',
          'All pages visually reviewed for structure and selected language,not every character or figure dimension certified.',
          'Full original embedded text is preserved,including OCR-like errors; it is not a corrected transcription.',
          'Native heading candidates are navigation aids,not an exhaustive semantic rule inventory.',
          'No external model-code volume,TEDS,fee resolution,newer amendment or currentness chain was retrieved.',
          'No legal-effect resolution,canonical ledger change,semantic rule-unit creation or signature authentication.'])

def verify(review:Review) -> dict:
    """Verify source hashes,full native byte coverage and every annotation reference."""
    if not __debug__:raise RuntimeError('run without -O')
    assert review.source.sha256==SHA and review.official_url==URL
    for a in [review.source,review.access_receipt]:assert asset(BASE/a.path)==a
    event=json.loads((BASE/review.access_receipt.path).read_text())
    assert event['body_sha256']==SHA and event['http_status']==200
    assert event['requested_url']==event['final_url']==URL
    byte_total=0;line_total=0;allspans={}
    with pymupdf.open(BASE/review.source.path) as doc:
        assert len(doc)==29 and not doc.is_repaired and not doc.is_encrypted
        assert doc.metadata==review.source_metadata
        for page in review.pages:
            assert asset(BASE/page.native.path)==page.native and asset(BASE/page.image.path)==page.image
            raw=(BASE/page.native.path).read_bytes()
            assert doc[page.physical_page-1].get_text('text',flags=195,sort=False).encode()==raw
            pos=0
            for i,s in enumerate(page.native_spans,1):
                assert s.id==f'P{page.physical_page:02d}-L{i:03d}'
                assert s.start==pos and raw[s.start:s.end]==s.text.encode()
                pos=s.end;allspans[s.id]=(page.physical_page,s.text)
            assert pos==len(raw)
            assert b''.join(s.text.encode() for s in page.native_spans)==raw
            byte_total+=len(raw);line_total+=len(page.native_spans)
            assert (BASE/page.image.path).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert byte_total==review.native_bytes==68078
    for h in review.heading_candidates:assert allspans[h.span_id]==(h.physical_page,h.text)
    for note in review.annotations:
        for r in note.references:
            raw=(BASE/f'page-{r.physical_page:02d}.native.txt').read_bytes()[r.start:r.end]
            assert raw==r.native_excerpt.encode()
            assert hashlib.sha256(raw).hexdigest()==r.excerpt_sha256
    lead=review.annotations[0]
    assert lead.kind=='date_conflict' and len(lead.references)==2
    assert lead.references[0].physical_page==27 and 'September 1 ,2025' in lead.references[0].native_excerpt
    assert lead.references[1].physical_page==29 and 'August 18, 2025' in lead.references[1].native_excerpt
    assert review.effective_date is None
    return {'passed':True,'pages':29,'native_bytes':byte_total,'native_lines':line_total,
      'full_pages_viewed':len(review.visually_viewed_pages),'annotation_count':len(review.annotations),
      'native_heading_candidates':len(review.heading_candidates),
      'effective_date_status':review.effective_date_status,'legal_currentness':'not_verified'}

def main() -> None:
    """Build once or verify the frozen package without any network access."""
    ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    if args.verify:
        manifest=Manifest.model_validate_json((BASE/'MANIFEST.json').read_text())
        actual={str(p.relative_to(BASE)) for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        assert actual-set(manifest.excluded)=={a.path for a in manifest.files}
        for a in manifest.files:
            p=BASE/a.path
            assert not Path(a.path).is_absolute() and '..' not in Path(a.path).parts
            assert not any(x.is_symlink() for x in [p,*p.parents] if x==BASE or BASE in x.parents)
            assert asset(p)==a
        review=Review.model_validate_json((BASE/'SOURCE_QA.json').read_text())
        jsonschema.validate(review.model_dump(mode='json'),json.loads((BASE/'SOURCE_QA.schema.json').read_text()))
    else:
        review=build();new(BASE/'SOURCE_QA.json',review.model_dump_json(indent=2)+'\n')
        new(BASE/'SOURCE_QA.schema.json',json.dumps(Review.model_json_schema(),indent=2)+'\n')
    logging.warning(json.dumps(verify(review),indent=2))
if __name__=='__main__':main()
