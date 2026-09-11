"""Build five-page source QA without altering acquisition or repository records."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import jsonschema
from review_models import Asset, Span, Page, Observation, SourceDate, Crop, Review, Custody, CustodyRow
B=Path(__file__).parent
A=B.parents[1]/'weld-directed-access-2026-09-11/authorized-http-retry'

def ref(path):
    p=B/path
    return Asset(path=path,sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size)

def save(name,record):
    schema=type(record).model_json_schema()
    raw=record.model_dump_json(indent=2)+'\n'
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    for suffix,body in [('.json',raw),('.schema.json',json.dumps(schema,indent=2)+'\n')]:
        p=B/(name+suffix);assert not p.exists();t=p.with_name(p.name+'.tmp')
        t.write_text(body);t.replace(p)

copy_pairs=[(A/'ATLAS-WELD-03/ord26-01.3rd-adopted.pdf','inputs/original.pdf'),
    (A/'ACCESS_RECEIPT.json','inputs/ACCESS_RECEIPT.json'),
    (A/'ACCESS_RECEIPT.schema.json','inputs/ACCESS_RECEIPT.schema.json'),
    (A/'ATLAS-WELD-03/response-headers.bin','inputs/response-headers.bin'),
    (A/'ATLAS-WELD-03/curl-metadata.json','inputs/curl-metadata.json'),
    (A/'ATLAS-WELD-03/curl-stderr.txt','inputs/curl-stderr.txt')]
custody=[]
for src,name in copy_pairs:
    assert src.is_file() and not any(p.is_symlink() for p in (src,*src.parents))
    p=B/name
    if not p.exists():
        t=p.with_name(p.name+'.tmp');t.write_bytes(src.read_bytes());t.replace(p);p.chmod(0o444)
    assert p.read_bytes()==src.read_bytes()
    custody.append(CustodyRow(original_path=str(src.resolve()),local=ref(name)))
assert (A/'ATLAS-WELD-03/response-body.bin').read_bytes()==(B/'inputs/original.pdf').read_bytes()
save('CUSTODY_RECEIPT',Custody(copied_at=datetime.now(timezone.utc),files=custody,original_files_unchanged=True,source_response_body_identical_to_pdf=True,scope='Selected ATLAS-WELD-03 exact PDF and acquisition evidence copies. The full two-response access receipt is retained as context; this review does not inspect the EHS PDF or independently re-perform acquisition.'))
P=[]
for n in range(1,6):
    txt=(B/f'native/page-{n:04}.txt').read_text()
    P.append(Page(physical_page=n,primary_image=ref(f'images/page-{n}.png'),primary_rendering='Poppler pdftoppm 26.05.0, 150 dpi, PNG',secondary_image=ref(f'images/pymupdf-page-{n}.png') if n in [2,3,5] else None,secondary_rendering='PyMuPDF 1.28.2; Matrix(150/72,150/72); alpha=False' if n in [2,3,5] else None,native_file=ref(f'native/page-{n:04}.txt'),native_text=txt,native_sha256=sha256(txt.encode()).hexdigest(),printed_header=f'Final Reading / Page {n}' if n>1 else None,primary_footer_visible=True,secondary_footer_visible=True if n in [2,3,5] else None,full_page_visually_checked=True))

def span(n,start,end=None):
    raw=P[n-1].native_text.encode();a=raw.index(start.encode())
    z=raw.index(end.encode(),a) if end else a+len(start.encode())
    content=raw[a:z]
    return Span(start_byte=a,end_byte_exclusive=z,text=content.decode(),sha256=sha256(content).hexdigest())
O=[]
def observe(n,kind,region,start,end,finding,limits):
    O.append(Observation(id=f'W26-O{len(O)+1:02}',physical_page=n,kind=kind,region=region,native_span=span(n,start,end) if start else None,source_image=P[n-1].primary_image,finding=finding,limits=limits,changes_native_text=False,legal_currentness='not_verified'))
observe(1,'source_role','Title, issuer, recitals and enacting instruction','Weld County Code Ordinance 2026-01','Chapter 23 \nZoning',
    'Title is Weld County Code Ordinance 2026-01. It names the Board of County Commissioners of the County of Weld, State of Colorado, and says Chapter 23 Zoning is repealed and re-enacted, with amendments. The recital references adoption of Ordinance 2000-1 on December 28, 2000.',
    'This is a county instrument. The historical recital is not the adoption date of 2026-01. Selected amendments and no-change placeholders do not reproduce the complete Chapter 23 or establish current consolidated law.')
observe(1,'wording','Definitions instruction and data-center definition','Amend Sec. 23-1-90.','ARTICLE II - Procedures',
    'The source instructs changing italicized terms throughout the definitions section to non-italics, then defines DATA CENTER. It states no limitation on peak electrical load and separately describes backup power systems with total generation capacity of less than fifty (50) megawatts; other definitions remain unchanged.',
    'Preserve the separation of peak electrical load from backup generation capacity. The bracketed source instruction is not an instruction to modify this preserved original or silently restyle existing code.')
observe(2,'wording','Site-plan application and supporting documents','Amend Sec. 23-2-160.','U. A statement',
    'The passage retains the preapplication conference, supporting-document context, item F evidence of water under C.R.S. 29-20-301 et seq., item H electricity-provider will-serve letter, and all stated no-change ranges.',
    'Do not infer the contents of omitted no-change items. The source typo though is retained separately, not repaired.')
observe(2,'wording','Site-plan compatibility and noise standard','U. A statement','Division 4 - Uses',
    'Item U retains compatibility with surrounding existing/future DEVELOPMENT and plan/agreement references, preconstruction location/layout/design qualifications, and once-operational conformance. Item 1 adds a sixty-five decibels (65 dB(C)) C-scale limit at any point on the subject property boundary, in addition to the referenced dB(A) limits.',
    'Preserve C weighting, the measurement boundary and the existing dB(A) context. Referenced Chapter 14, Article IX and Section 14-9-40 were not independently inspected.')
observe(2,'wording','Special-review design standards','Amend Sec. 23-2-240.',None,
    'The design-standard amendment retains application compliance and continued compliance if approved, followed by water compliance under C.R.S. 29-20-301 et seq. The remainder-of-section no-change instruction continues at the top of page 3.',
    'Keep the page-3 no-change line attached to this preceding section. This is not the full design-standard section.')
# Extend the preceding span through the page end, preserving all bytes in that passage.
O[-1].native_span=span(2,'Amend Sec. 23-2-240.',None)
raw=P[1].native_text.encode();a=raw.index(b'Amend Sec. 23-2-240.')
O[-1].native_span=Span(start_byte=a,end_byte_exclusive=len(raw),text=raw[a:].decode(),sha256=sha256(raw[a:]).hexdigest())
observe(3,'wording','Special-review operational noise','Amend Sec. 23-2-250.','Amend Sec. 23-2-260.',
    'The operation-standard amendment includes preconstruction/design scope and once-operational conformance, Chapter 14/Article IX and Section 14-9-40 dB(A) context, plus the same sixty-five decibels (65 dB(C)) property-boundary limit.',
    'The line wrap inside 14-9-40 is preserved. Do not conflate site-plan and special-review application routes.')
observe(3,'wording','Special-review supporting documents','Amend Sec. 23-2-260.','ARTICLE III - Zone',
    'Item E retains water proof, unchanged items, a noise mitigation plan that may be required sufficient to demonstrate compliance, and new item 7 requiring the electricity-provider will-serve letter.',
    'May be required must not be rewritten as universally mandatory. Preserve all no-change/insert-new instructions and the letter condition serving the property area.')
observe(4,'wording','I-1 amendment','Amend Sec. 23-3-310.','Amend Sec. 23-3-320.',
    'I-1 Light Industrial adds DATA CENTERS as new F.5 under Uses by Special Review, with permit approval under Article II, Division 4.',
    'Preserve unchanged preceding items and renumber instruction. Do not recast this as an unconditional use permission.')
observe(4,'wording','I-2 amendment','Amend Sec. 23-3-320.','Amend Sec. 23-3-330.',
    'I-2 Medium Industrial adds DATA CENTERS as new C.9 subject to Site Plan Review, approval and recording under Article II, Division 3. Preserve the exact screening clause: Any USE conducted outside of an ENCLOSED BUILDING shall be SCREENED from adjacent PUBLIC RIGHTS-OF-WAY and ADJACENT LOTS in any Zone District other than I-3.',
    'Keep the complete source screening and district qualifier. No application to a particular site is inferred.')
observe(4,'wording','I-3 amendment','Amend Sec. 23-3-330.',None,
    'I-3 Heavy Industrial adds DATA CENTERS as new C.12 subject to Site Plan Review, approval and recording under Article II, Division 3.',
    'All unchanged ranges and renumber/no-other-changes language remain present. The other district provisions are not supplied here.')
raw=P[3].native_text.encode();a=raw.index(b'Amend Sec. 23-3-330.')
O[-1].native_span=Span(start_byte=a,end_byte_exclusive=len(raw),text=raw[a:].decode(),sha256=sha256(raw[a:]).hexdigest())
observe(5,'wording','Municode supplementation direction','Be it further ordained by the Board that','Be it further ordained by the Board, if',
    'The Clerk is directed to arrange for Municode to supplement the Weld County Code with these amendments and resolve specified capitalization, grammar, numbering and placement inconsistencies.',
    'This instruction does not prove supplementation has occurred and does not authorize silent editorial changes to the retained source.')
observe(5,'wording','Severability','Be it further ordained by the Board, if','Publication: January',
    'The complete severability wording is retained, including the remaining-portions and would-have-enacted clauses.',
    'A source severability statement is not an independent finding of legal validity.')
observe(5,'source_role','Printed reading/publication/effective timeline','Publication: January','The Board of County Commissioners',
    'Nine printed timeline lines distinguish publication, first and second readings, a rescheduled final reading, continuation, later publication and effectiveness. Effective is printed April 15, 2026.',
    'Dates are claims printed in this instrument. The publication issues and independent proceedings were not inspected; February 25 is a rescheduled date, not the stated final adoption date.')
observe(5,'source_role','Adoption statement and vote','The Board of County Commissioners','Approved as to Form:',
    'The source states adoption on the 6th day of April, A.D., 2026. Printed votes are Scott K. James, Chair: Nay; Jason S. Maxey, Pro-Tem: Aye; Perry L. Buck: Aye; Lynette Peppler: Aye; Kevin D. Ross: Aye. The printed tally is four Aye and one Nay.',
    'This supports an adopted-amendment role as stated by the source, not independent validation of meeting minutes, execution, subsequent amendments or currentness.')
observe(5,'wording','Printed form approval and attestation','Approved as to Form:',None,
    'Printed labels read Approved as to Form: Bruce Barker, County Attorney; Attest: Esther E. Gesick, Clerk to the Board. No handwritten signatures or initials are observed in the five-page copy.',
    'Typed names and a seal graphic do not certify wet-signature identity, a digital signature, execution formalities or authenticity beyond the retained source copy.')
raw=P[4].native_text.encode();a=raw.index(b'Approved as to Form:')
O[-1].native_span=Span(start_byte=a,end_byte_exclusive=len(raw),text=raw[a:].decode(),sha256=sha256(raw[a:]).hexdigest())
observe(5,'image_only','County seal graphic',None,None,
    'A circular seal graphic beside the vote/attestation area visibly contains WELD, COUNTY and 1861. Its image lettering is absent from native extraction.',
    'Record this as image-only evidence; no native offsets are invented. The seal graphic is not a recorder stamp, proof of wet execution or verified authentication.')
observe(2,'source_anomaly','No-change range typo','I. though T. - No change.',None,
    'The visible source and native text both read I. though T. - No change., with though rather than through.',
    'Preserve the source anomaly. Do not fill the unchanged range from inference or silently repair spelling.')
observe(1,'rendering_limit','Recurring document identifiers and native order','2026-0765 \nORD2026-01 \n',None,
    'The recurring lower-right identifiers are 2026-0765 and ORD2026-01. Native extraction places them before the body (after Final Reading/Page on pages 2-5), although they are visibly footers on all five pages.',
    'These are identifiers, not printed dates or proof of recording. Retain the source order in native bytes and record visible location separately. No substantive footer content is missing.')
dates=[]
for role,date,line in [
 ('publication','2026-01-14','Publication: January 14, 2026'),
 ('first_reading','2026-01-26','First Reading: January 26, 2026'),
 ('publication','2026-01-30','Publication: January 30, 2026, in the Greeley Tribune'),
 ('second_reading','2026-02-09','Second Reading: February 9, 2026'),
 ('publication','2026-02-13','Publication: February 13, 2026, in the Greeley Tribune'),
 ('final_reading_rescheduled_to','2026-02-25','Final Reading Rescheduled to: February 25, 2026'),
 ('continued_to','2026-04-06','Continued to: April 6, 2026'),
 ('publication','2026-04-10','Publication: April 10, 2026, in the Greeley Tribune'),
 ('effective_as_stated','2026-04-15','Effective: April 15, 2026'),
 ('adoption_as_stated','2026-04-06','the 6th day of April, A.D., 2026:')]:
    dates.append(SourceDate(role=role,stated_date=date,physical_page=5,span=span(5,line),legal_event_independently_verified=False))
dates.append(SourceDate(role='historical_ordinance_2000_1_adoption_recital',stated_date='2000-12-28',physical_page=1,span=span(1,'on December 28, 2000, adopted Weld \nCounty Code Ordinance 2000-1'),legal_event_independently_verified=False))
C=[]
for name,n,rect in [('p1-definition',1,[70,540,560,650]),('p2-noise-and-typo',2,[65,290,560,560]),('p3-supporting-documents',3,[65,320,560,650]),('p5-dates-vote',5,[65,315,560,590]),('p5-seal-attest',5,[65,515,560,760])]+[(f'p{n}-native-footer',n,[445,720,560,760]) for n in [2,3,5]]:
    C.append(Crop(id=name,physical_page=n,file=ref('crops/'+name+'.png'),method='pymupdf_300dpi_pdf_clip',rect=rect,inspected=True))
for n in [2,3,5]:C.append(Crop(id=f'p{n}-poppler-footer',physical_page=n,file=ref(f'crops/p{n}-poppler-footer.png'),method='pillow_primary_png_crop',rect=[925,1490,1190,1610],inspected=True))
R=Review(schema_version=1,reviewed_at=datetime.now(timezone.utc),source_id='weld-ordinance26-01',authority_id='CO-COUNTY-WELD',source=ref('inputs/original.pdf'),source_role='adopted_amendment_instrument_as_stated_in_source',document_scope='Five-page final-reading ordinance with selected Chapter 23 Zoning amendments and explicit no-change/renumber instructions; not a complete consolidated Chapter 23.',review_mode='candidate_aware_direct_source_qa_not_blind',external_reports_consulted=False,source_retrieval_performed_by_this_reviewer=False,source_url='https://www.weld.gov/files/sharedassets/public/v/3/departments/planning-and-zoning/documents/long-range/code-changes/ord26-01.3rd-adopted.pdf',acquisition_receipt=ref('inputs/ACCESS_RECEIPT.json'),expected_pages=5,native_bytes=9284,native_extraction='PyMuPDF 1.28.2; get_text(text, sort=False, flags=195)',pages=P,observations=O,stated_dates=dates,crops=C,source_adoption_date='2026-04-06',source_effective_date='2026-04-15',printed_vote_aye=4,printed_vote_nay=1,handwritten_signatures_observed=False,seal_graphic_observed=True,complete_consolidated_chapter=False,missing_native_word_correction_identified=False,source_changed=False,network_requests=0,repository_changes=False,legal_currentness='not_verified',limits=[
 'Candidate-aware Atlas direct source QA, not an external Ebenezer or Sherlock assignment and not a blind review. Five complete Poppler pages, three additional complete PyMuPDF page renders and eleven crops were inspected.',
 'All 9284 native UTF-8 bytes are retained unchanged across five separately hashed native files. No substantive word or number correction was identified. Native text does not encode the seal image or visual reading order.',
 'No strike-through, colored revision highlighting or handwritten insertions were observed. Bold amendment headings, uppercase defined terms, source editing instructions, no-change ranges and renumber language remain intact; an exhaustive font-style inventory and exact visual Unicode are not certified.',
 'Adoption, publication and effectiveness dates are explicitly source-stated. No publication copy, independent minutes, wet execution, cryptographic signature, full code consolidation or later amendment chain was checked. Currentness remains not_verified.',
 'The exact PDF equals the received HTTP response body and claimed historical digest. This reviewer made no network requests and did not independently repeat acquisition or inspect a historical original. The parent access audit owns the DNS/HTTP attempt history and official URL evidence.',
 'The full access receipt includes a second EHS source only as custody context. Only this five-page ordinance PDF was inspected. No repository intake, source registry, queue, corpus, legal-currentness or semantic coverage record was changed.'
])
save('SOURCE_QA',R)
text=['---','title: "Weld Ordinance 2026-01 - five-page source QA"',f'reviewed_at: "{R.reviewed_at.isoformat()}"','source_id: "weld-ordinance26-01"','status: "source_qa_complete_pending_parent_intake"','review_mode: "candidate_aware_direct_source_qa_not_blind"','legal_currentness: "not_verified"','---','','# Source result','','The five-page copy presents **Weld County Code Ordinance 2026-01** as adopted on **April 6, 2026**, with four printed Aye votes and one Nay, and states **Effective: April 15, 2026**. Its title and enacting clause repeal and re-enact Chapter 23 Zoning with amendments. The actual five pages supply selected amendments and no-change instructions, not the full consolidated zoning chapter.','','All five full source pages were directly inspected, with three additional full-page renders and eleven crops. All **9,284 native UTF-8 bytes** are preserved unchanged in five page-bound files. This is candidate-aware Atlas source QA, not an external reviewer assignment. No substantive native word or number correction was identified.','','## Source roles and dates','','| Source role | Stated date | Physical page |','|---|---|---|']
for d in dates:text.append(f'| {d.role} | {d.stated_date} | {d.physical_page} |')
text+=['','Dates remain source assertions: publication notices and independent proceedings were not checked. February 25 is a rescheduled final-reading date; April 6 is both the stated continuation and adoption date. The December 28, 2000 recital concerns Ordinance 2000-1. The footer 2026-0765 is an identifier, not a legal date.','','## Checked regions','','| ID | Page | Direct-source finding | Limit |','|---|---|---|']
for o in O:text.append(f'| {o.id} | {o.physical_page} | {o.finding} | {o.limits} |')
text+=['','## Execution and preservation limits','','The final page prints the five commissioners and their votes; Bruce Barker, County Attorney beneath Approved as to Form; Esther E. Gesick, Clerk to the Board beneath Attest; and a county seal graphic. No handwritten signature is visible. Typed names and seal imagery are not authentication of execution.','','The source typo **I. though T. - No change.** is preserved. The noise-plan clause remains **may be required**. The definition distinguishes no peak-electrical-load limit from backup generation capacity **less than fifty (50) megawatts**. The noise provisions retain **65 dB(C)**, existing dB(A) context and the subject-property-boundary measurement point. The I-1 special-review route remains distinct from I-2/I-3 site-plan-review routes.','','The source tells the Clerk to arrange for Municode supplementation and specified editorial reconciliation; that is not evidence the supplementation has occurred or permission to alter this preserved copy. No current-law consolidation or completeness claim is made.','','## Custody and verification','','Source SHA256: `'+R.source.sha256+'`; '+str(R.source.size_bytes)+' bytes. The copied access receipt records ordinary-TLS HTTP 200 on the exact URL, without redirect, completed 2026-09-11T19:49:18.706875Z. The access audit, not this source-reading task, owns that retrieval.','','The read-only verifier checks strict models and schemas, source/custody hashes, all native re-extractions, observation/date spans, full-page image bindings, expected image inventories and retained native/visual footer identities. PNG crops remain bound to their exact source and recorded generation methods. No original is modified.','','```sh','PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python validate_source_review.py','```','','## Scope limits','']+['- '+x for x in R.limits]+['']
(B/'SOURCE_QA.md').write_text('\n'.join(text))
print('Prepared',len(P),'pages',len(O),'observations',len(dates),'dates',len(C),'crops')
