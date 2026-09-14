"""One-time assembly of manually checked source wording; refuses replacement."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from review_models import Asset, Review

B = Path(__file__).resolve().parent


def asset(name):
    p = B / name
    raw = p.read_bytes()
    return Asset(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)).model_dump()


def put(name, raw):
    p = B / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        f.write(raw)


p1 = [
    ("P1-TITLE", "title", "REVISED RESOLUTION DECLARING EQUITY FEE REDUCTION\nFOR PLANNING AND ENGINEERING DEVELOPMENT REVIEW FEES FOR CERTAIN\nAPPLICATION TYPES THAT ACHIEVE COMMUNITY BENEFITS", (280, 300, 2290, 540)),
    ("P1-R1", "recital", "WHEREAS, the Larimer County Land Use Code contains the review processes and standards for different development types; and", (270, 645, 2280, 780)),
    ("P1-R2", "recital", "WHEREAS, Larimer County charges a combined Planning and Engineering Development Review fee to applicants at the time of a development review application as outlined in a Fee Schedule; and", (270, 805, 2280, 1005)),
    ("P1-R3", "recital", "WHEREAS, in 2022, after a thorough study of the time it takes to do development review and assessing comparable services and costs in other communities, Larimer County adopted a new Planning and Engineering Development Review Fee Schedule that took effect on January 3, 2023; and", (270, 1030, 2280, 1300)),
    ("P1-R4", "recital", "WHEREAS, for many application types, the application costs have increased and may be harder to bear for certain smaller projects that may be providing a community benefit as noted below; and", (270, 1330, 2280, 1545)),
    ("P1-R5", "recital", "WHEREAS, Larimer County's Comprehensive Plan, Strategic Plan Objectives, and Climate and Sustainability Plan define community goals related to affordable and attainable workforce housing and different housing types, affordable and accessible childcare facilities, energy efficiency and water conservation, and supporting small business startups; and", (265, 1560, 2290, 1840)),
    ("P1-R6-R7", "recital", "WHEREAS, the Board of County Commissioners recognizes that certain applicants and application types should be eligible for a reduction in the development fees to achieve greater equity between smaller and larger applications and to achieve such goals that benefit the community; and WHEREAS, the Board of County Commissioners may delegate authority to the Planning Director (Community Development Director) to reduce fees for certain development application types to achieve County goals; and", (260, 1855, 2290, 2270)),
    ("P1-R8", "recital", "WHEREAS, in 2022, Larimer County approved a resolution allowing for fee reductions for Planning and Engineering Development Review fees for certain application types that achieve community benefits.", (260, 2295, 2290, 2500)),
    ("P1-RESOLVE", "resolution_lead", "NOW THEREFORE, BE IT RESOLVED BY THE BOARD OF COUNTY COMMISSIONERS OF LARIMER COUNTY, COLORADO, that:", (260, 2515, 2290, 2680)),
    ("P1-ITEM1", "operative", "1. The Planning Director is hereby authorized to reduce development fees as published on the Fee Schedule by twenty-five percent (25%) for certain application types as outlined in this resolution.", (330, 2690, 2290, 2890)),
    ("P1-ITEM2", "operative", "2. Planning process application types that are eligible for reduced fees include:", (330, 2950, 2290, 3050)),
]
p2 = [
    ("P2-2a", "eligibility", "a. Affordable housing projects, as defined by the Larimer County Affordable Housing Policy;", (500, 320, 2290, 460)),
    ("P2-2b", "eligibility", "b. Accessory Living Areas that an owner is building to make available for long-term housing, as attested through an Affidavit;", (500, 460, 2290, 590)),
    ("P2-2c", "eligibility", "c. Childcare facilities;", (500, 590, 2290, 660)),
    ("P2-2d", "eligibility", "d. Small businesses registered in Larimer County with ten (10) or fewer employees;", (500, 650, 2290, 725)),
    ("P2-2e", "eligibility", "e. Accessory uses on agricultural properties;", (500, 720, 2290, 790)),
    ("P2-2f", "eligibility", "f. Subdivisions with fewer than three (3) lots;", (500, 785, 2290, 860)),
    ("P2-2g", "eligibility", "g. Minor modifications or site upgrades to achieve Comprehensive Plan or Climate and Sustainability Plan goals. These may include but are not limited to installation of lighting to achieve dark sky lighting goals, water efficiency landscaping improvements, renewable energy infrastructure installations on a commercial site, local food related agricultural projects, or other community benefits as described in adopted Larimer County plans or policies; and", (500, 850, 2290, 1250)),
    ("P2-2h", "eligibility", "h. At the discretion of the Director or by the Director in consultation with the Board of County Commissioners, other projects that may achieve Comprehensive Plan, Climate and Sustainability Plan goals, or other Larimer County Strategic Plan objectives.", (500, 1250, 2290, 1510)),
    ("P2-ITEM3", "operative", "3. Applicant must request the fee reduction at the time of application with a planner.", (350, 1510, 2290, 1590)),
    ("P2-ITEM4", "operative", "4. This resolution is effective as of January 2, 20243 and shall remain in effect, at the discretion of the Board of County Commissioners, through December 31, 2027, subject to renewal at that time.", (350, 1570, 2290, 1795)),
]

pages = []
for number, rows in [(1, p1), (2, p2)]:
    blocks = []
    content = b""
    for idx, (ident, role, text, rect) in enumerate(rows):
        text += "\n" if idx == len(rows) - 1 else "\n\n"
        raw = text.encode("utf-8")
        blocks.append(dict(
            id=ident, physical_page=number, role=role, text=text,
            start_byte=len(content), end_byte=len(content) + len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            byte_basis="manual_page_transcription_utf8_not_native_source_text",
            region_px=rect, region_precision="approximate_locator_in_full_300dpi_image",
            parent_id="P1-ITEM2" if role == "eligibility" else None,
        ))
        content += raw
    body = f"text/page-{number:04d}-printed-body.txt"
    native = f"native/page-{number:04d}.txt"
    put(body, content)
    put(native, b"")
    pages.append(dict(
        physical_page=number, image=asset(f"images/page-{number}.png"),
        native_text=asset(native), native_bytes=0, printed_body=asset(body),
        width_px=2550, height_px=3300, full_page_directly_viewed=True, blocks=blocks,
    ))

crops = [dict(id=name, physical_page=2, image=asset(f"crops/{name}.png"),
              x=x, y=y, width=w, height=h, dpi=300, directly_viewed=True)
         for name, x, y, w, h in [
             ("date-and-clause4", 280, 1570, 1980, 340),
             ("execution", 80, 1800, 2250, 1270),
             ("eligibility", 490, 290, 1810, 1240),
         ]]

execution = [
    dict(id="EX-DATE", physical_page=2, region_px=[270, 1770, 2290, 1900],
         printed_fragments=["Passed and adopted this", "day of", ", 2023, in Larimer County, Colorado."],
         observation="Blue handwriting fills the day and month spaces on the printed passage/adoption line. The printed year is 2023.",
         handwriting_reading="The day reads 19th and the month reads December.",
         qualification="A visual reading of the filled line, not an authenticated adoption date or proof of legal execution. Handwritten date remains separate from the defective printed effective-year statement.",
         crop_ids=["date-and-clause4", "execution"]),
    dict(id="EX-CHAIR", physical_page=2, region_px=[1230, 1900, 2280, 2310],
         printed_fragments=["BOARD OF COMMISSIONERS OF", "LARIMER COUNTY, COLORADO", "Chair"],
         observation="A blue cursive signature mark crosses the line above Chair. The first printed line here omits COUNTY; the body elsewhere says Board of County Commissioners.",
         handwriting_reading=None,
         qualification="No person's name, capacity, authority or signature authenticity is certified from the mark or office label.",
         crop_ids=["execution"]),
    dict(id="EX-CLERK", physical_page=2, region_px=[85, 2320, 1180, 2665],
         printed_fragments=["ATTEST:", "County Clerk"],
         observation="A blue cursive signature mark is present above the County Clerk line; blue handwriting to the left of the printed label reads Deputy.",
         handwriting_reading="Deputy (role annotation only).",
         qualification="Signature identity, authority and authenticity are not determined; the handwritten role word is not a typed addition to the original body.",
         crop_ids=["execution"]),
    dict(id="EX-ATTORNEY", physical_page=2, region_px=[85, 2640, 1100, 3030],
         printed_fragments=["APPROVED AS TO FORM:", "County Attorney"],
         observation="A blue signature mark appears on the form-approval line. A short blue annotation immediately left of County Attorney resembles Asst.",
         handwriting_reading="Tentative role abbreviation Asst; exact ending/punctuation not certified.",
         qualification="No signature-name transcription or legal approval/authenticity determination is made.",
         crop_ids=["execution"]),
    dict(id="EX-SEAL", physical_page=2, region_px=[570, 1830, 1210, 2410],
         printed_fragments=["LARIMER COUNTY CLERK", "SEAL", "COLORADO"],
         observation="A large black circular seal impression/image with the stated words is visible. Dotted circular decoration surrounds the words.",
         handwriting_reading=None,
         qualification="Seal presence and visible words are recorded, not seal authenticity or exact ornamental typography.",
         crop_ids=["execution"]),
]

def obs(ident, kind, blocks, statement, limitation, ex=()):
    return dict(id=ident, kind=kind, block_ids=blocks, execution_ids=list(ex),
                statement=statement, limitation=limitation)

observations = [
    obs("EQ-01", "scope", ["P1-TITLE", "P1-R6-R7", "P1-RESOLVE"],
        "The source identifies Larimer County, its Board of County Commissioners, and delegated Planning Director (Community Development Director) authority for planning and engineering development-review fee reductions.",
        "County source context is distinct from municipal or district authority; no independent legal-authority adjudication is made."),
    obs("EQ-02", "condition", ["P1-ITEM1", "P1-ITEM2", "P2-2a", "P2-2h", "P2-ITEM3"],
        "Item 1 authorizes the Planning Director to reduce Fee Schedule development fees by twenty-five percent (25%) for the application types outlined. Eligibility and an application-time request remain attached to that percentage.",
        "Not a universal reduction, applicant entitlement, calculated charge, full fee-schedule adoption or permission to omit other conditions."),
    obs("EQ-03", "condition", ["P2-2a", "P2-2b", "P2-2c", "P2-2d", "P2-2e", "P2-2f"],
        "The first six eligibility items retain the Affordable Housing Policy definition, owner/long-term-housing/Affidavit qualification, childcare, county registration and ten-or-fewer employees, agricultural accessory uses, and subdivisions with fewer than three lots.",
        "The policy, Affidavit form and any application definitions are not appended or independently reviewed. Fewer than three is not silently changed to three or fewer."),
    obs("EQ-04", "condition", ["P2-2g"],
        "Item g addresses minor modifications/site upgrades toward named plans; its examples expressly are not limited to the listed lighting, water, renewable-energy, agricultural and other community benefits.",
        "Retain the commercial-site phrase within the renewable-energy example and the adopted-plans/policies reference; do not manufacture additional eligibility tests."),
    obs("EQ-05", "condition", ["P2-2h"],
        "Item h separately preserves Director discretion or Director consultation with the Board for other projects achieving the named plan goals/objectives.",
        "Do not convert the discretionary category into a universally mandatory reduction."),
    obs("EQ-06", "condition", ["P2-ITEM3"],
        "Applicant must request the reduction at the time of application with a planner.",
        "No additional request deadline or retroactive eligibility rule is supplied by this review."),
    obs("EQ-07", "source_defect", ["P2-ITEM4"],
        "Item 4 visibly prints January 2, 20243. The five-digit year is retained exactly as source wording.",
        "Do not silently replace it with 2024, infer a corrected effective date from the filename or reconcile it using an unreviewed memo."),
    obs("EQ-08", "date", ["P2-ITEM4"],
        "The printed duration is through December 31, 2027, at the Board's discretion and subject to renewal at that time.",
        "This is source-stated text, not a finding that the resolution remains operative today or that a renewal occurred."),
    obs("EQ-09", "date", ["P1-R3", "P1-R8"],
        "Recitals separately state a 2022 fee-schedule adoption, January 3, 2023 effect for that schedule, and a prior 2022 fee-reduction resolution.",
        "Those underlying instruments and the complete fee schedule are not included or independently verified; recital dates are not this instrument's authenticated adoption date."),
    obs("EQ-10", "execution", [],
        "The final execution area visibly has a filled day/month line, printed year 2023, three blue signature marks, office labels and a circular seal.",
        "Completed-looking execution is only a visual description. Identity, wet signatures, signer authority, authenticity, official recording and legal effect remain unverified.",
        ["EX-DATE", "EX-CHAIR", "EX-CLERK", "EX-ATTORNEY", "EX-SEAL"]),
    obs("EQ-11", "dependency", ["P1-R1", "P1-R2", "P1-R5", "P1-R8", "P1-ITEM1", "P2-2a", "P2-2g", "P2-2h"],
        "The two supplied pages refer to the Land Use Code, Fee Schedule, Affordable Housing Policy, named plans/policies and prior resolution. No appended attachment or visible Attachment A reference appears in this PDF.",
        "This is an absence observation within these two pages only. No unavailable Attachment A, incorporated schedule, external definition or cross-document fee chain is reconstructed."),
    obs("EQ-12", "scope", ["P1-TITLE", "P2-ITEM4"],
        "Both full pages and three targeted source crops were directly inspected. The source has zero extracted native-text bytes on both pages; the body here is a new manual transcription from the images.",
        "This is Atlas candidate-aware source QA with prior intake metadata available, not a blind external pass or a claim that native OCR existed. No source bytes are altered."),
]

manual_lines = (B / "custody/manual-manifest.jsonl").read_bytes().splitlines(keepends=True)
provenance_lines = (B / "custody/source-provenance.jsonl").read_bytes().splitlines(keepends=True)
m = json.loads(manual_lines[32]); p = json.loads(provenance_lines[5])
assert m["record_id"] == p["source_id"] == "larimer-equity-fee-resolution-sd007-04"
review = Review.model_validate_json(json.dumps(dict(
    review_id="ATLAS-LARIMER-EQUITY-RESOLUTION-2026-09-11-SESSION2",
    source_id=m["record_id"], authority_id=p["authority_id"],
    authority_basis="Exact retained source/custody assignment plus visible county and Board names; not independent verification of legal authority.",
    source=asset("original.pdf"), source_unchanged=True, expected_physical_pages=2,
    review_mode="atlas_candidate_aware_source_qa_not_blind",
    prior_exposure="The reviewer read the source's existing inventory and SD007 provenance qualifications before viewing the two pages. No external reviewer report was consulted; native extraction is empty.",
    external_reports_consulted=False, status="printed_body_transcribed_execution_observations_qualified",
    reviewed_at=datetime.now(timezone.utc).isoformat(),
    transcription_convention="Preserve all visible printed body wording, capitalization, numbers, punctuation and paragraph/item order. Visual line wraps are joined with spaces except the three-line title; paragraph separators are added consistently. An ordinary apostrophe represents the visible possessive mark. Exact Unicode, whitespace, font, underline, microtypography and handwritten signatures are not certified. Execution printed fragments and handwritten/graphic observations are separate. UTF-8 offsets bind these manual transcription files, not the empty PDF native extraction.",
    native_extractor="PyMuPDF 1.28.2 text flags=195 sort=False",
    rendering_engine="Poppler pdftoppm 26.05.0", rendering_dpi=300,
    pages=pages, crops=crops, execution=execution, observations=observations,
    custody=dict(
        manual_manifest=asset("custody/manual-manifest.jsonl"), manual_line_number=33,
        manual_line_sha256=hashlib.sha256(manual_lines[32]).hexdigest(),
        source_provenance=asset("custody/source-provenance.jsonl"), provenance_line_number=6,
        provenance_line_sha256=hashlib.sha256(provenance_lines[5]).hexdigest(),
        canonical_archive_path=m["archive_path"], intake_id=m["intake_id"],
        repository_received_at=m["received_at"], acquisition_method=m["acquisition_method"],
        supplied_requested_url=p["supplied_requested_url"], supplied_final_url=p["supplied_final_url"],
        supplied_time_claim=p["supplied_time_claim"], supplied_method_claim=p["supplied_method_claim"],
        supplied_http_status=p["supplied_http_status"], source_http_acquisition_verified=False,
        intake_status=m["status"], copied_at="2026-09-11T21:17:56.710036Z",
        limitation="Source bytes were copied from the existing canonical archive without a network request. HTTP status, routes and approximate browser/mtime timing remain supplied upstream claims. Original HTTP acquisition time is unknown. Whole frozen custody files contain other records for historical integrity only; this package verifies/reviews only the selected source and lines. Historical external paths are informational and are never opened by the portable validator.",
    ),
    attachments_present=False, attachment_a_reference_observed=False, signature_marks_observed=3,
    execution_area_completed_as_visual_observation=True, adopted_status_verified=False,
    legal_currentness="not_verified", semantic_or_coverage_promotion=False,
    limitations=[
        "Complete printed body on both supplied pages is manually transcribed; execution/signature/graphic areas are separately qualified, not a full diplomatic handwritten transcription.",
        "The original is a two-page scanned PDF with empty native text. The manual body is a derived source-reading artifact; byte checks cannot independently prove that a human read each word correctly.",
        "The title underline, blue ink, signatures and black seal remain visible in unchanged source renders. No exact graphical/Unicode certification or reconstruction is supplied.",
        "The source defect 20243, all eight eligibility categories, Director/Board discretion, application-time request and renewal qualification remain intact.",
        "No original acquisition replay, missing attachment, complete fee schedule, cited policy/plan, prior adopting instrument, amendment chain, legal-currentness, fee calculation or geographic-coverage claim is included.",
        "This is an internal Atlas review, not an Ebenezer assignment, external blind review, signer authentication or semantic RuleUnit promotion. Raw archive and all existing repository/control records remain unchanged.",
    ],
)))
put("SOURCE_QA.json", (review.model_dump_json(indent=2) + "\n").encode())
put("SOURCE_QA.schema.json", (json.dumps(Review.model_json_schema(), indent=2) + "\n").encode())
print("Validated source QA:", len(review.pages), "pages;", sum(len(x.blocks) for x in review.pages), "body blocks;")
