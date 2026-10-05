"""Freeze the reviewer-authored findings from actual full-page and crop inspection."""
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

from prepare import ROOT, Inputs, asset
from capture_evidence import Evidence
from role_models import NativeAnchor, Observation, DateClaim, PageReview, RoleDecision, Review


def main() -> None:
    """Write only a new validated role decision; never edit source or native buffers."""
    if (ROOT/'ROLE_DECISIONS.json').exists(): raise ValueError('Review already frozen')
    inputs=Inputs.model_validate_json((ROOT/'INPUTS.json').read_bytes())
    evidence=Evidence.model_validate_json((ROOT/'EVIDENCE.json').read_bytes())
    sources={s.priority:s for s in inputs.sources}
    natives={(n.priority,n.page):n.native for n in evidence.native_pages}

    def obs(identity: str, priority: str, page: int, locator: str, kind: str,
            quote: str | None, finding: str, crops: list[str]) -> Observation:
        """Bind selected printed words to exact unchanged native bytes when present."""
        anchor=None
        if quote is not None:
            ref=natives[(priority,page)]; raw=(ROOT/ref.path).read_bytes(); text=raw.decode()
            pattern=r'\s+'.join(re.escape(x) for x in quote.split())
            m=re.search(pattern,text)
            if m:
                start=len(text[:m.start()].encode()); end=len(text[:m.end()].encode())
                anchor=NativeAnchor(asset=ref,start=start,end=end,text=raw[start:end].decode())
        return Observation(observation_id=identity,physical_page=page,locator=locator,
            kind=kind,visual_text=quote,finding=finding,crop_ids=crops,native_anchor=anchor)

    def date(literal: str, role: str, identity: str, scope: str) -> DateClaim:
        """Keep source assertions and their unresolved scope separate."""
        return DateClaim(literal=literal,role=role,observation_id=identity,scope=scope,
                         independently_verified=False,operative_date_certified=False)

    def pages(priority: str, notes: list[str]) -> list[PageReview]:
        """Record the actual complete page-image role scan, not full transcription."""
        out=[]
        for n,note in enumerate(notes,1):
            printed=str(n-2) if priority=='P08' and n>=3 else (str(n) if n==2 else None)
            out.append(PageReview(physical_page=n,printed_page=printed,
                image=sources[priority].images[n-1],directly_viewed=True,
                role_scan_note=note,complete_text_fidelity_checked=False))
        return out

    common=dict(legal_currentness='not_verified',legal_effect_certified=False,
                complete_text_fidelity_checked=False,intake_or_rule_promotion_authorized=False)
    p04=RoleDecision(priority='P04',action_id='SHDISC002-A010',
        authority_id='CO-COUNTY-JEFFERSON',source=sources['P04'].source,
        title_as_printed='Jefferson County Building Code',
        assessed_role='policy_with_uncompleted_adoption_metadata',
        role_reason='A regulatory-policy form contains adoption/effect language but leaves its adopting resolution and adoption/effective header dates empty. This copy does not substantiate completed adoption; its URL includes Draft--FINAL, which is not itself legal-status evidence.',
        pages=pages('P04',[
            'Policy identity, blank adoption metadata and Section A adoption language; no signature or execution block.',
            'Code-list continuation, incorporation, June 30 effect/supersession, unincorporated-county scope and severability; no execution block.']),
        observations=[
            obs('P04-O01','P04',1,'Header policy title/number/type','document_identity',
                'Type of Policy: Regulatory','Part 3 Regulations, Chapter 8 Property, Section 4; county policy custodian is Building Safety.',['P04-header']),
            obs('P04-O02','P04',1,'Header Adopting Resolution / Effective Date / Adoption Date','blank_field',
                None,'All three fields have no entered value. Administrative Revision Date instead says Not applicable.',['P04-header']),
            obs('P04-O03','P04',1,'A. Adoption, paragraph 1','printed_claim',
                'effective June 30, 2026:','Internal clause asserts adoption of listed codes effective June 30, 2026; preserve separately from blank metadata.',['P04-header']),
            obs('P04-O04','P04',2,'A.2','printed_claim',
                'The full texts of the Jefferson County Building Codes identified above are hereby adopted and incorporated as if fully set out at length herein.',
                'Incorporation/adoption words are present but not proof of a completed adopting act.',['P04-effect']),
            obs('P04-O05','P04',2,'A.3','printed_claim',
                'This Policy and the Jefferson County Building Codes adopted herein shall take effect June 30, 2026 and shall supersede and replace the existing building code Policy and all previously-adopted versions of such codes and building code supplements as of such date.',
                'Source-stated effect and supersession, not an independently verified operative date.',['P04-effect']),
            obs('P04-O06','P04',2,'A.4','scope',
                'The Jefferson County Building Codes shall apply to all unincorporated areas of Jefferson County.',
                'County scope is explicitly unincorporated areas; do not transfer to Arvada.',['P04-effect']),
        ],
        dates=[date('June 30, 2026','source_stated_effective_date_unverified','P04-O03','A.1 listed building codes'),
               date('June 30, 2026','source_stated_effective_date_unverified','P04-O05','A.3 policy, codes and supersession')],
        blank_or_incomplete_fields=['Adopting Resolution','Effective Date','Adoption Date'],
        execution_evidence_in_copy='No signature, completed adopting resolution identifier, or execution block observed on either physical page.',
        unverified_external_dependencies=['Completed adopting resolution and approved policy version; referenced code supplements and fee documents are not contained in this two-page policy.'],**common)

    p07=RoleDecision(priority='P07',action_id='SHDISC002-A023',
        authority_id='CO-MUNICIPAL-ARVADA',source=sources['P07'].source,
        title_as_printed='COUNCIL BILL NO. 26-028',
        assessed_role='introduced_bill_with_uncompleted_execution_fields',
        role_reason='The source announces a hearing and records introduction/initial publication, while the ordinance number, adoption month, execution lines and second publication date remain uncompleted. Do not classify the retained copy as a completed adopted ordinance.',
        pages=pages('P07',[
            'Hearing notice, bill number, blank ordinance number, residential-zoning table, severability, conditional effect and printed introduction date.',
            'Adoption template with blank month; blank Mayor, City Clerk and City Attorney approval lines; first printed publication date and blank second line.']),
        observations=[
            obs('P07-O01','P07',1,'Top identifiers','document_identity','COUNCIL BILL NO. 26-028',
                'The following ORDINANCE NO. has no number entered.',['P07-header-hearing']),
            obs('P07-O02','P07',1,'Boxed hearing notice','printed_claim',
                'A public hearing on this Council Bill will be held by the Arvada City Council on Tuesday, October 6 at 6:15pm at 8101 Ralston Road in the Council Chambers.',
                'Notice is prospective wording. The box itself does not print a year; the document elsewhere prints 2026.',['P07-header-hearing']),
            obs('P07-O03','P07',1,'Section 1','scope',
                'Table 3-1-2-2 of the Arvada City Code is hereby repealed and enacted to read as follows:',
                'Proposed ordinance concerns residential land use by zoning district. The table is visible; its cells are outside this role-only review.',[]),
            obs('P07-O04','P07',1,'Section 3','printed_claim',
                'This ordinance shall be effective five (5) days after publication following final passage.',
                'Conditional formula; no calendar effect date is calculated.',['P07-introduction']),
            obs('P07-O05','P07',1,'Introduction line','printed_claim',
                'INTRODUCED, READ, AND ORDERED PUBLISHED this 15th day of September, 2026.',
                'Printed introduction assertion only.',['P07-introduction']),
            obs('P07-O06','P07',2,'Top adoption template','blank_field',None,
                'Printed PASSED, ADOPTED AND APPROVED this 6th day of [blank], 2026. Month remains blank; do not fill October from the hearing notice. Underscore length is not certified.',['P07-execution']),
            obs('P07-O07','P07',2,'Execution and approval lines','execution',None,
                'All lines are blank: Lauren Simpson, Mayor; ATTEST City Clerk; APPROVED AS TO FORM Rachel A. Morris, City Attorney, By. Printed names are not signatures.',['P07-execution']),
            obs('P07-O08','P07',2,'Publication Dates','printed_claim','September 15, 2026',
                'First publication date printed; second publication-date line blank.',['P07-execution']),
        ],
        dates=[date('Tuesday, October 6 at 6:15pm','source_stated_hearing_date_unverified','P07-O02','Hearing notice; year not printed in this box'),
               date('15th day of September, 2026','source_stated_introduction_date_unverified','P07-O05','Introduction/order to publish'),
               date('September 15, 2026','source_stated_publication_date_unverified','P07-O08','First of two publication-date lines'),
               date('five (5) days after publication following final passage','source_stated_conditional_effect_unverified','P07-O04','Section 3; triggering events not independently verified')],
        blank_or_incomplete_fields=['Ordinance number','Month in this 6th day of [blank], 2026','Mayor signature','City Clerk signature','City Attorney By signature','Second publication date'],
        execution_evidence_in_copy='Execution template is present but unfilled; no signatures or seal observed.',
        unverified_external_dependencies=['Final passage/adoption instrument, completed ordinance identifier, executed/certified copy and final publication evidence.'],**common)

    notes=[
        'City-branded cover labels Wildfire Resiliency Code; lower title misspells Arvada as Aravda.',
        'Table of contents; no adoption or execution certification.',
        'Ordinance-form heading, incomplete Council Bill 26- and blank ordinance number; Section 1 enactment language and definitions.',
        'Definitions continued; no document execution or revision metadata.',
        'Definitions and material-test criteria continued; no execution metadata.',
        'Definitions continued; no execution or revision metadata.',
        'Definitions, Article II scope and general requirements; no completed ordinance identity.',
        'Existing-condition scope and Section 106-10(c) July 1, 2026 code/permit timing claim; no execution metadata.',
        'Applicability, other laws and referenced standards; no execution metadata.',
        'Applicability and exemptions; duplicate (f) labels visible, not corrected; no execution metadata.',
        'Code compliance agency names city Building Safety Division and Fire Protection Districts; duties begin.',
        'Alternative materials, methods and approval criteria; no execution metadata.',
        'Duties, modifications, permits and entry; no execution metadata.',
        'Official records and permit process; no execution metadata.',
        'Fees by reference, inspections, enforcement and appeals; Article III starts; no execution metadata.',
        'Mapping/designations and Article IV structure hardening; no completed adoption instrument.',
        'Class 1 hardening requirements; no execution or revision metadata.',
        'Class 1 hardening continued with exceptions; no execution metadata.',
        'Deck/door provisions and Class 2 hardening start; no execution metadata.',
        'Class 2 hardening and Article V site-area requirements with exceptions; no execution metadata.',
        'Class 1 site-area and ignition-zone provisions; no execution metadata.',
        'Retaining walls, fencing, signage and Class 2 requirements start; no execution metadata.',
        'Class 2 site-area requirements continued; no execution metadata.',
        'Final site-area clauses, severability, April 1st effect, March 3 introduction and March 24 adoption claims; document ends without signature or certification block.',
    ]
    p08=RoleDecision(priority='P08',action_id='SHDISC002-A026',
        authority_id='CO-MUNICIPAL-ARVADA',source=sources['P08'].source,
        title_as_printed='Wildfire Resiliency Code; Chapter 106, Aravda City Code',
        assessed_role='ordinance_form_code_with_printed_adoption_claim',
        role_reason='The final page expressly prints a March 24, 2026 adoption assertion, so it must not be erased by calling the entire source merely an unsigned proposal. However identifiers are incomplete, no execution/certification appears, and two clauses separately print April 1 and July 1 effect language. Actual adoption, operative scope and currentness remain unresolved.',
        pages=pages('P08',notes),
        observations=[
            obs('P08-O01','P08',1,'Cover title and lower banner','document_identity',
                'Chapter 106, Aravda City Code','The printed misspelling Aravda is retained. Cover native extraction is empty; this observation is image-based.',['P08-cover-title']),
            obs('P08-O02','P08',3,'Top identifiers','blank_field','COUNCIL BILL NO. 26-',
                'Bill identifier stops after 26-; ORDINANCE NO. has no entered number.',['P08-identifiers']),
            obs('P08-O03','P08',3,'Section 1','printed_claim',
                'Chapter 106, Arvada Wildfire Resiliency Code, is hereby enacted and shall read as follows:',
                'Enactment words appear in an ordinance-form document; they do not alone verify completed adoption.',['P08-identifiers']),
            obs('P08-O04','P08',8,'Printed page 6, Section 106-10(c)','printed_claim',
                'Date effective. This code shall become effective on July 1, 2026, and shall apply to permits applied for on or after July 1, 2026. Applications for permits made prior to July 1, 2026, shall be governed by the terms of the codes and regulations in effect at the time of application.',
                'Preserve both the date and earlier-permit qualification; distinguish the code/permit clause from the final ordinance clause.',['P08-code-date']),
            obs('P08-O05','P08',11,'Printed page 9, Section 106-12(a)-(b)','scope',
                'The Arvada Building Safety Division and the Fire Protection Districts within Arvada are hereby designated as the code compliance agencies',
                'City-issued document names municipal and fire-district administration roles. This is not a county or standalone fire-district enactment.',['P08-agencies']),
            obs('P08-O06','P08',24,'Printed page 22, Section 3','printed_claim',
                'This ordinance shall be effective on April 1st, 2026.',
                'A separate ordinance-effect assertion. Relationship to July 1 code/permit clause is not resolved; do not collapse into a single verified date.',['P08-ending']),
            obs('P08-O07','P08',24,'Introduction line','printed_claim',
                'INTRODUCED, READ, AND ORDERED PUBLISHED this 3rd day of March, 2026.',
                'Printed source assertion only; no publication event independently verified.',['P08-ending']),
            obs('P08-O08','P08',24,'Final adoption line','printed_claim',
                'PASSED, ADOPTED AND APPROVED this 24th day of March, 2026.',
                'Printed adoption claim is present and retained; no signature/authentication or complete adopting identifier accompanies it in this copy.',['P08-ending']),
            obs('P08-O09','P08',24,'Document ending and all-page role scan','execution',None,
                'The retained 24-page copy ends after the adoption statement and printed page 22. No signature, attestation, completed ordinance number or certification block was observed anywhere in the copy.',['P08-ending']),
        ],
        dates=[date('July 1, 2026','source_stated_effective_date_unverified','P08-O04','Section 106-10(c) code and permit applicability, with earlier-permit qualification'),
               date('April 1st, 2026','source_stated_effective_date_unverified','P08-O06','Final ordinance Section 3'),
               date('3rd day of March, 2026','source_stated_introduction_date_unverified','P08-O07','Introduction/order to publish'),
               date('24th day of March, 2026','source_stated_adoption_date_unverified','P08-O08','Printed passed/adopted/approved statement')],
        blank_or_incomplete_fields=['Council Bill number after 26-','Ordinance number'],
        execution_evidence_in_copy='Printed adoption assertion is present; no execution signatures, attestation or certification block observed on all 24 pages.',
        unverified_external_dependencies=['Complete adopting ordinance identifier and executed/certified record; publication/adoption evidence; resolution of April 1 ordinance versus July 1 code/permit clauses; subsequent revisions and current codification.'],**common)
    review=Review(schema_version=1,reviewer='Plato',recorded_at=datetime.now(timezone.utc).isoformat(),
        status='complete_bounded_document_role_review',inputs=asset(ROOT/'INPUTS.json'),
        evidence=asset(ROOT/'EVIDENCE.json'),custody='received_review_package',
        original_http_and_timing_verified=False,
        source_exposure='Prior Ptolemy custody audit, including first-page native excerpts and tentative role cautions, read before images; task identity cues supplied by Atlas. Same Codex family, not blind. All 28 full images and ten crops then directly inspected by this reviewer.',
        visual_method='Poppler 200 dpi complete physical pages viewed with view_image; exact pixel crops inspected. Full-page display resized by tool. Native byte lengths checked during preflight; unchanged native text consulted only after full-page role scan. No OCR or full text fidelity review.',
        directly_viewed_full_pages=28,directly_viewed_crops=10,candidate_corrections_performed=False,
        public_requests=0,documents=[p04,p07,p08],limitations=[
            'Received-package custody only. Supplied HTTP status, URLs and times remain claims; this reviewer made no public request.',
            'Role review scans every physical page for identity/date/approval/execution/revision evidence, not every substantive word, table cell or requirement.',
            'No completed amendment/adoption/publication chain or legal-currentness determination; no canonical intake, rule, lookup or coverage promotion.',
            'Selected quotations normalize whitespace and superscript placement for readability; image evidence governs blank-field geometry and visual formatting.',
            'Absence findings concern this exact retained copy only, not the existence of executed instruments elsewhere.',
            'Unchanged native buffers are retained as unreviewed extraction context; empty cover extraction is not a blank source page.',
        ])
    (ROOT/'ROLE_DECISIONS.schema.json').write_text(json.dumps(Review.model_json_schema(),indent=2)+'\n')
    (ROOT/'ROLE_DECISIONS.json').write_text(review.model_dump_json(indent=2)+'\n')
    sys.stdout.write(f'Validated {len(review.documents)} document roles, 28 page observations and 10 crops.\n')
if __name__=='__main__':main()
