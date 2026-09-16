"""One-time construction from Plato's direct full-page and crop observations."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymupdf
from pydantic import BaseModel

from review_models import Asset, Inspection, Review, Span

ROOT = Path(__file__).resolve().parent


def digest(data: bytes) -> str:
    """Return exact-byte SHA256."""
    return hashlib.sha256(data).hexdigest()


def asset(path: str) -> dict[str, Any]:
    """Describe a local already-written payload."""
    data = (ROOT / path).read_bytes()
    return Asset(path=path, sha256=digest(data), size_bytes=len(data)).model_dump()


def write_model(path: str, model: BaseModel) -> None:
    """Validate before exclusive publication; never overwrite evidence."""
    cls = type(model)
    data = model.model_dump_json(indent=2) + '\n'
    cls.model_validate_json(data)
    with (ROOT / path).open('x') as stream:
        stream.write(data)
    with (ROOT / path.replace('.json', '.schema.json')).open('x') as stream:
        stream.write(json.dumps(cls.model_json_schema(), indent=2) + '\n')


def span(data: bytes, start: int, end: int) -> dict[str, Any]:
    """Bind one exact half-open UTF-8 span."""
    return Span(start=start, end=end, sha256=digest(data[start:end])).model_dump()


BLOCKS: list[dict[str, Any]] = []


def add(identity: str, page: int, text: str, locator: str, *,
        kind: str = 'printed_text', crops: list[str] | None = None,
        notes: list[str] | None = None, continuation: str | None = None) -> None:
    """Add observed text with explicit non-source annotations distinguished."""
    BLOCKS.append(dict(id=identity, page=page, text=text, locator=locator, kind=kind,
                       crop_paths=crops or [], notes=notes or [], continuation_of=continuation))


def stamp(page: int) -> None:
    """Preserve both recorder columns and describe undecoded graphics separately."""
    add(f'P{page}-STAMP', page,
        f'Gunnison County, CO\n9/8/2022 3:53:42 PM\n447\n687079\nPage {page} of 4\nR 0.00 D 0.00',
        'Top recorder imprint, left column followed by right column.',
        notes=['Reading order groups the two columns; the source timezone is unstated.',
               'R and D are literal stamp fields, not reviewed fee charges.'])
    add(f'P{page}-BARCODE', page,
        '[Reviewer annotation: a barcode graphic appears beneath the recorder imprint; '
        'it is not decoded as text.]', 'Barcode below top-left stamp.',
        kind='graphic_annotation', notes=['OCR pseudo-text is retained only in the raw candidate.'])


stamp(1)
add('P1-HEADER', 1, 'BOARD OF COUNTY COMMISSIONERS\n'
    'OF THE COUNTY OF GUNNISON, COLORADO\n\nRESOLUTION NO. 2022-33\n'
    'A RESOLUTION ADOPTING THE\n2021 INTERNATIONAL WILDLAND URBAN INTERFACE CODE',
    'Centered heading beneath recorder imprint.', kind='mixed_printed_and_handwritten',
    notes=['The resolution suffix 33 is handwritten; blank-rule spacing is normalized.',
           'The apparent numeric insertion is transcribed, not authenticated.'])
add('P1-RECITAL-1', 1,
    'WHEREAS, pursuant to C.R.S §38-28-201, et. seq., the Board of County Commissioners of '
    'the County of Gunnison, Colorado (herein the “Board”) previously adopted the 2015 '
    'editions of the “International Building Code”, the “International Residential Code”, '
    'the “International Mechanical Code”, the “International Fuel Gas Code”, and the '
    '“International Energy Conservation Code”; and', 'First WHEREAS paragraph.',
    crops=['crops/p1-citation.png'],
    notes=['The visible citation is §38-28-201. No substitution of a different title number.',
           'The OCR loses Mechanical Code wording and introduces isolated quote fragments.'])
add('P1-RECITAL-2', 1,
    'WHEREAS, the Board has reviewed the 2021 edition of the International Wildland Urban '
    'Interface Code (WUI Code); and', 'Second WHEREAS paragraph.',
    crops=['crops/p1-citation.png'])
add('P1-RECITAL-3', 1,
    'WHEREAS, the Board has determined that adoption of the 2015 Building Codes with certain '
    'changes, amendments and substitutions, establish minimum requirements to safeguard the '
    'public safety, health and general welfare through affordability, structural strength, '
    'means of egress, stability, sanitation, light and ventilation, energy conservation and '
    'safety to life and property from fire and other hazards attributed to the built environment '
    'and provide safety to fire fighters and emergency responders during emergency operations; '
    'and', 'Third WHEREAS paragraph.',
    notes=['Retains source 2015 wording and grammatical agreement; no edition reconciliation.'])
add('P1-RECITAL-4', 1,
    'WHEREAS, the Gunnison County Planning Commission has reviewed and certified to the Board '
    'the 2021 WUI Code with the recommended changes, amendments and substitutions; and',
    'Fourth WHEREAS paragraph.')
add('P1-RECITAL-5', 1,
    'WHEREAS, a public hearing on this matter was held by the Board on the September 6, 2022; '
    'and', 'Fifth WHEREAS paragraph.', notes=['The phrase “on the September” is in the source.'])
add('P1-RESOLVED', 1,
    'NOW THEREFORE, BE IT RESOLVED by the Board of County Commissioners of Gunnison County, '
    'Colorado that the following are hereby adopted for the unincorporated area of Gunnison '
    'County:', 'Lead-in immediately above numbered clauses.', crops=['crops/p1-numbered.png'])
add('P1-1', 1,
    '1. The International Wildland Urban Interface Code, 2021 Edition, with the amendments as '
    'set forth in Exhibit “A” attached hereto and incorporated herein.', 'Numbered clause 1.',
    crops=['crops/p1-numbered.png'])
add('P1-2', 1,
    '2. The International Wildland Urban Interface Code, 2021 Edition shall apply upon '
    'recordation of this resolution to all land use change permits classified as major or '
    'minor impact in Gunnison County.', 'Numbered clause 2.', crops=['crops/p1-numbered.png'],
    notes=['Separate recordation condition and major/minor land-use scope are retained.'])
add('P1-3', 1,
    '3. The International Wildland Urban Interface Code, 2021 Edition shall apply to all new '
    'building permit applications beginning January 1, 2023.', 'Numbered clause 3.',
    crops=['crops/p1-numbered.png'],
    notes=['This source-stated date is scoped to new building permit applications.'])
add('P1-EXECUTION', 1,
    'INTRODUCED by Commissioner Smith, seconded by Commissioner Mason and adopted on this '
    '6th day of September 2022.', 'Introduction and adoption line below numbered clauses.',
    kind='mixed_printed_and_handwritten', crops=['crops/p1-execution.png'],
    notes=['Smith, Mason, 6th and September are apparent handwritten insertions.',
           'Identity, authorship, execution authenticity and legal effect are not certified.'])

stamp(2)
add('P2-HEADER', 2, 'BOARD OF COUNTY COMMISSIONERS\n'
    'OF THE COUNTY OF GUNNISON, COLORADO', 'Heading above execution lines.',
    crops=['crops/p2-execution.png'])
for n, name in enumerate(['Jonathan Houck, Chairperson', 'Roland Mason, Commissioner',
                          'Elizabeth Smith, Commissioner'], 1):
    add(f'P2-SIGNER-{n}', 2, f'By:\n{name}', f'Printed label on execution line {n}.',
        crops=['crops/p2-execution.png'],
        notes=['Printed name and office only; adjacent signature is not transcribed as identity.'])
add('P2-ATTEST', 2, 'Attest:\nDeputy County Clerk', 'Attestation and printed office at right.',
    crops=['crops/p2-execution.png'],
    notes=['Handwriting crosses the printed office; no source deletion is inferred.'])
add('P2-HANDWRITING', 2,
    '[Reviewer annotation: the attestation handwriting appears to read “Melanie Bollig”; '
    'this is an uncertain visual reading, not an authenticated person or signature.]',
    'Handwritten attestation on the right.', kind='handwriting_annotation',
    crops=['crops/p2-execution.png'])
add('P2-SIGNATURES', 2,
    '[Reviewer annotation: three signature marks appear on the By lines and overlap some '
    'printed names. Their handwriting, identities and execution authenticity are not certified.]',
    'Three left execution lines.', kind='graphic_annotation',
    crops=['crops/p2-execution.png'])
add('P2-SEAL', 2,
    '[Reviewer annotation: a round seal graphic contains the visible words GUNNISON COUNTY, '
    'SEAL, COLORADO, with ornamental borders. This is a description, not seal authentication.]',
    'Round seal beneath right attestation.', kind='graphic_annotation',
    crops=['crops/p2-execution.png'])

stamp(3)
add('P3-HEADER', 3, 'Exhibit A\n2021 International Wildland Urban Interface Code\n'
    'Proposed Gunnison County Amendments', 'Exhibit heading below recorder stamp.',
    notes=['The source heading says Proposed; it is preserved alongside page 1 adoption wording.'])
AMENDMENTS = [
    ('402.1.1', 'Section 402.1.1 Access.',
     'Delete entire section. The current access requirements and standards throughout Gunnison '
     'County will continue to be utilized.'),
    ('402.2', 'Section 402.2 Individual structures.',
     'Delete “Section 402.2.1 and”. Current access requirements will continue to be utilized.'),
    ('402.2.1', 'Section 402.2.1 Access.',
     'Delete entire section. Current access requirements will continue to be utilized.'),
    ('403', 'Section 403 Access.',
     'Delete the following sections: 403.1 Restricted access, 403.2 Driveways, 403.2.1 Dimensions, '
     '403.2.2 Length, 403.2.3 Service limitations, 403.2.4 Turnarounds, 403.2.5 Turnouts, '
     '403.2.6 Bridges, 403.3 Fire apparatus access road, 403.7 Grade.'),
    ('404.2', 'Section 404.2 Water sources.',
     'Amend to the following and delete everything else: “The water source location shall be '
     'reviewed and approved by the code official.”'),
    ('404.6', 'Section 404.6 Fire department.', 'Delete entire section.'),
    ('502.1', 'Section 502.1 General.',
     'Amend to say the following: The fire hazard severity of building sites for building '
     'hereafter constructed, modified or relocated into wildland-urban interface areas shall '
     'be established in accordance with the Community Planning Assistance for Wildfire '
     '“Final Recommendations for Gunnison, CO 2019” report, specifically the Local-Level '
     'Wildfire Hazard data and map.'),
    ('TABLE502.1', 'Table 502.1 Fire Hazard Severity.', 'Delete table.'),
    ('502.2-A', 'Section 502.2 Fire hazard severity reduction.',
     'Amend to say the following: The fire hazard severity identified through Section 502.1 '
     'is allowed to be reduced by implementing a vegetation management plan in accordance '
     'with Appendix B.'),
    ('502.2-B', 'Section 502.2 Fire hazard severity reduction.',
     'Add the following sentence:\n\nIt is strongly encouraged that a vegetation management '
     'plan prepared by a qualified wildfire professional, including but not limited to, the '
     'Colorado State Forest Service, West Region Wildfire Council, and local fire districts.'),
    ('TABLE503.1', 'Table 503.1 Ignition-Resistant Construction.',
     'Replace “Extreme Hazard” with “Very High Hazard”. This is to ensure consistent '
     'terminology with the Community Planning Assistance for Wildfire “Final Recommendations '
     'for Gunnison, CO 2019” report.'),
    ('603.2.4', 'Section 603.2.4 Hardened zone.',
     '0-5 feet minimum from the structure shall be a hardened zone designed to prevent flames '
     'from coming in direct contact with the structure.'),
]
for n, (label, heading, body) in enumerate(AMENDMENTS, 1):
    notes = ['The section/table label is emphasized and underlined, not struck through.',
             'Printed amendment instruction retained; operative effect is not inferred.']
    if label == '502.2-B':
        notes.append('Repeated heading and incomplete grammar retained; no “be” is supplied.')
    if label == '603.2.4':
        notes.append('Continues as P4-CONTINUATION after the physical page break.')
    add(f'P3-A{n:02d}', 3, ('Add new ' if label == '603.2.4' else '') + heading + ' ' + body,
        f'Exhibit A amendment paragraph {n}, target {label}.',
        crops=['crops/p3-upper.png' if n <= 6 else 'crops/p3-lower.png'], notes=notes)

stamp(4)
add('P4-CONTINUATION', 4,
    'Use nonflammable, hard surface materials in this zone, such as rock, gravel, sand, '
    'cement, bare earth or stone/concrete pavers.', 'First body paragraph below recorder stamp.',
    crops=['crops/p4-complete-text.png'], continuation='P3-A12',
    notes=['Physical continuation of the new Section 603.2.4 paragraph on page 3.'])
add('P4-A13', 4,
    'Table 603.2 Required Defensible Space. Replace “Extreme hazard” with “Very High hazard”.',
    'Second body paragraph, Table 603.2.', crops=['crops/p4-complete-text.png'],
    notes=['Lowercase hazard is preserved; no table cells appear in this resolution.'])
add('P4-A14', 4,
    'Appendix B Vegetation Management Plan. Adopt Appendix B and add the following sentence '
    'to Section B101.1: It is strongly encouraged that a vegetation management plan prepared '
    'by a qualified wildfire professional, including but not limited to, the Colorado State '
    'Forest Service, West Region Wildfire Council, and local fire districts.',
    'Final body paragraph, Appendix B.', crops=['crops/p4-complete-text.png'],
    notes=['Incomplete source grammar retained; no “be” is inserted.'])


def main() -> None:
    """Publish checked evidence once, preserving originals and uncorrected candidate."""
    now = datetime.now(timezone.utc).isoformat()
    crops = json.loads((ROOT / 'CROPS.json').read_bytes())['crops']
    inspection = Inspection(
        reviewer='Plato', recorded_at=now,
        exposure='Packet preparer; previously viewed these four pages for render completeness. '
        'This review is candidate-aware, not blind. The current full-page and seven crop '
        'inspection preceded reading the candidate text in this review turn.',
        full_pages=[asset(f'pages/page-{n:04d}.png') for n in range(1, 5)],
        crops=[asset(c['path']) for c in crops], full_page_count=4, crop_count=7,
        chronology='Retrospective inspection receipt after direct tool display of all four '
        'full PNGs and seven exact crops. No invented per-display timestamp. Five crops were '
        'displayed again after OCR comparison to resolve wording and handwriting.',
        external_reports_consulted=False, handwriting_identities_authenticated=False)
    write_model('INSPECTION.json', inspection)
    extraction = json.loads((ROOT / 'inputs/EXTRACTION.json').read_bytes())
    candidate = (ROOT / 'inputs/candidate.txt').read_bytes()
    pages, passages = [], []
    for n in range(1, 5):
        selected = [b for b in BLOCKS if b['page'] == n]
        data = ''.join(b['text'] + '\n\n' for b in selected).encode()
        path = f'reviewed/page-{n:04d}.txt'
        with (ROOT / path).open('xb') as stream:
            stream.write(data)
        cursor = 0
        for b in selected:
            end = cursor + len((b['text'] + '\n\n').encode())
            passages.append({**b, 'image': asset(f'pages/page-{n:04d}.png'),
                             'reviewed_transcript': asset(path),
                             'reviewed_span': span(data, cursor, end)})
            cursor = end
        pix = pymupdf.Pixmap(str(ROOT / f'pages/page-{n:04d}.png'))
        ex = extraction['pages'][n - 1]
        pages.append(dict(number=n, image=asset(f'pages/page-{n:04d}.png'),
                          width=pix.width, height=pix.height,
                          native=asset(f'native/page-{n:04d}.txt'), native_spans=[],
                          native_status='empty_image_only',
                          ocr_json=asset(f'ocr/page-{n:04d}.json'),
                          ocr_text=asset(f'ocr/page-{n:04d}.txt'),
                          ocr_observation_spans=ex['observation_spans'],
                          candidate_span=span(candidate, ex['candidate_start'],
                                              ex['candidate_end']),
                          reviewed_transcript=asset(path)))
    record = json.loads((ROOT / 'inputs/canonical-record.jsonl').read_bytes())
    reservation = json.loads((ROOT / 'inputs/reservation.json').read_bytes())
    result = json.loads((ROOT / 'inputs/result.json').read_bytes())
    amendments = []
    for n, (label, heading, body) in enumerate(AMENDMENTS, 1):
        ids = [f'P3-A{n:02d}'] + (['P4-CONTINUATION'] if label == '603.2.4' else [])
        amendments.append(dict(id=f'A{n:02d}', target_literal=heading,
                               instruction_literal=body, passage_ids=ids,
                               targets_within_literal=(['403.1', '403.2', '403.2.1', '403.2.2',
                                                        '403.2.3', '403.2.4', '403.2.5',
                                                        '403.2.6', '403.3', '403.7']
                                                       if label == '403' else []),
                               qualification='Document instruction only; no underlying code '
                               'or amendment chain examined.'))
    for n, target, text in [
        (13, 'Table 603.2 Required Defensible Space.',
         'Replace “Extreme hazard” with “Very High hazard”.'),
        (14, 'Appendix B Vegetation Management Plan.',
         next(b['text'] for b in BLOCKS if b['id'] == 'P4-A14').split('. ', 1)[1])]:
        amendments.append(dict(id=f'A{n:02d}', target_literal=target,
                               instruction_literal=text, passage_ids=[f'P4-A{n}'],
                               targets_within_literal=[],
                               qualification='Document instruction only; '
                               'no operative effect inferred.'))
    discrepancies = []
    for identity, n, ids, finding in [
        ('OCR1', 1, ['P1-STAMP', 'P1-BARCODE', 'P1-RECITAL-1', 'P1-EXECUTION'],
         'Raw OCR misorders recorder fields, reads barcode noise as text, drops Code after '
         'Mechanical and fragments quotation marks, and misreads/reorders handwritten execution '
         'content. Reviewed source preserves §38-28-201 and all five named 2015 codes.'),
        ('OCR2', 2, ['P2-STAMP', 'P2-SIGNER-1', 'P2-ATTEST', 'P2-HANDWRITING', 'P2-SEAL'],
         'OCR loses recorder fields, Jonathan and initial By label, corrupts Deputy County Clerk, '
         'and guesses handwriting and seal graphics. Printed labels are recovered from images; '
         'signature identity remains uncertain.'),
        ('OCR3', 3, ['P3-STAMP', 'P3-BARCODE', 'P3-A10', 'P3-A12'],
         'OCR omits stamp 447 and retains barcode pseudo-text. Body paragraph words agree after '
         'declared whitespace/quote normalization; duplicate 502.2 and source grammar remain.'),
        ('OCR4', 4, ['P4-STAMP', 'P4-BARCODE', 'P4-CONTINUATION', 'P4-A14'],
         'OCR changes CO casing and reads barcode noise; body words agree after line joining. '
         'The continuation and repeated incomplete vegetation-plan grammar remain.')]:
        data = (ROOT / f'ocr/page-{n:04d}.txt').read_bytes()
        discrepancies.append(dict(id=identity, page=n, ocr_span=span(data, 0, len(data)),
                                  ocr_text_literal=data.decode(), reviewed_passage_ids=ids,
                                  finding=finding))
    dates = [
        dict(literal='2015', role='Prior code editions recited',
             passage_ids=['P1-RECITAL-1', 'P1-RECITAL-3'],
             qualification='Not treated as this resolution year or current adopted edition.'),
        dict(literal='2021', role='Code edition named by resolution and Exhibit A',
             passage_ids=['P1-HEADER', 'P1-1', 'P3-HEADER'],
             qualification='A source edition label, not a verification of present law.'),
        dict(literal='September 6, 2022', role='Recited public hearing date',
             passage_ids=['P1-RECITAL-5'], qualification='Source assertion only.'),
        dict(literal='6th day of September 2022', role='Apparent handwritten adoption clause',
             passage_ids=['P1-EXECUTION'], qualification='No execution authentication.'),
        dict(literal='9/8/2022 3:53:42 PM', role='Recorder imprint on all four pages',
             passage_ids=[f'P{n}-STAMP' for n in range(1, 5)],
             qualification='Timezone not printed; no separate recorder verification.'),
        dict(literal='upon recordation', role='Source-stated land-use permit applicability trigger',
             passage_ids=['P1-2'], qualification='Only major/minor-impact land use change permits '
             'are named. No conversion into an independently verified effective date.'),
        dict(literal='January 1, 2023', role='Source-stated new building application start date',
             passage_ids=['P1-3'], qualification='Distinct from the land-use recordation trigger.'),
        dict(literal='2019', role='Year in cited report title',
             passage_ids=['P3-A07', 'P3-A11'],
             qualification='Referenced report was not obtained or reviewed in this task.')]
    limits = [
        'This is complete visible text and qualified graphic/handwriting review of one four-page '
        'resolution scan, not a complete IWUIC text, amendment chain or legal-currentness review.',
        'Adoption language, Proposed exhibit heading, source dates and recorder stamp coexist. '
        'No enactment, execution authenticity, legal effect or present applicability is certified.',
        'All native extractions are empty. Byte offsets refer explicitly to unchanged machine '
        'OCR or the new reviewed transcript; they are not invented native source offsets.',
        'Reviewer observations are candidate-aware and not independently blind. No external '
        'Grok report or second language/edition source was consulted.',
        'Printed names are distinct from nearby handwritten signatures. Apparent handwritten '
        'insertions and the uncertain attestation name are not authenticated identities.',
        'Whitespace, paragraph line wraps and typographic quotation encoding are normalized; '
        'bold, underline, italic, baseline spacing and exact glyph codepoints are not certified.',
        'No actual table grid is reproduced in the source; Table 502.1, 503.1 and 603.2 are '
        'amendment instructions only. No fee amount or code table is reconstructed.',
        'The full source packet manifest is preserved for custody, but this review copies only '
        'its selected relevant assets; absent packet members are not claimed locally present.',
        'Canonical custody is received_review_package. Supplied public URL, HTTP outcome and '
        'times remain reported evidence; actual repository received_at is separate.',
        'Mechanical tests verify hashes, offsets, associations and fixed reviewed invariants. '
        'They do not independently certify visual transcription or legal interpretation.']
    review = Review.model_validate_json(json.dumps(dict(
        schema_version=1, source_id=record['record_id'], authority_id='CO-COUNTY-GUNNISON',
        layer=record['layer_id'], source=asset('inputs/original.pdf'),
        source_role='County resolution scan with recorder imprints, execution marks and Exhibit A '
        'instructions concerning the 2021 International Wildland Urban Interface Code.',
        status='complete_visible_source_fidelity_review_qualified_handwriting',
        review_kind='checked_passages', legal_currentness='not_verified', answer_safe=False,
        reviewed_at=now, method='Plato direct full-page image and exact crop inspection, then '
        'unchanged Apple Vision OCR comparison. No source edits.',
        scope='All four physical pages, all recitals, three numbered clauses, fourteen exhibit '
        'instructions, recorder fields and separately qualified execution/seal annotations.',
        normalization='UTF-8; paragraph line wraps joined; blank paragraph separator is two LF; '
        'typographic quotes represented consistently; source words, case distinctions, grammar '
        'and numerals preserved; graphic/handwriting annotations explicitly bracketed.',
        provenance=dict(acquisition_method='received_review_package',
                        official_source_url_verified=None, official_acquisition_at_verified=None,
                        supplied_requested_url=reservation['requested_url'],
                        supplied_started_at=reservation['reserved_at'],
                        supplied_finished_at=result['finished_at'],
                        supplied_times_status='reported_not_independently_verified',
                        repository_received_at=record['received_at'],
                        canonical_archive_path_claim=record['archive_path'],
                        canonical_record=asset('inputs/canonical-record.jsonl'),
                        intake_receipt=asset('inputs/INTAKE_RECEIPT.json'),
                        receipt_status='canonical_intake_record_bound_not_fresh_http_verification'),
        candidate=asset('inputs/candidate.txt'),
        packet_manifest=asset('inputs/PACKET_MANIFEST.json'),
        inspection=asset('INSPECTION.json'), pages=pages, checked_passages=passages,
        amendment_instructions=amendments, dates=dates, ocr_discrepancies=discrepancies,
        limitations=limits,
        findings=['The visible §38-28-201 citation and 2015 recitals are preserved without repair.',
                  'The two different applicability triggers remain scoped '
                  'to their printed clauses.',
                  'Duplicate Section 502.2 headings and both incomplete vegetation-plan sentences '
                  'remain intact; no word “be” or mandatory duty is silently inserted.',
                  'The hardened-zone paragraph crosses pages 3–4; all material examples remain '
                  'linked to Section 603.2.4, including literal 0-5 feet minimum.',
                  'Printed underlines mark headings. No deletion strike was identified; '
                  'instructions '
                  'using Delete or Replace are transcribed as words, not applied to other text.'],
        custody=[asset(x) for x in ['COPY_RECEIPT.json', 'CROPS.json', 'inputs/EXTRACTION.json',
                                   'inputs/INTAKE_INTENT.json', 'inputs/reservation.json',
                                   'inputs/result.json', 'inputs/RENDER_STAGE.json',
                                   'inputs/OCR_RECEIPT.json', 'inputs/CUSTODY_STAGE.json']])) )
    write_model('SOURCE_QA.json', review)
    md = ['---', 'title: Gunnison IWUIC Resolution 2022-33 — reviewed source transcript',
          'reviewer: Plato', 'status: complete_source_fidelity_review_not_current_law', '---', '',
          'Plato prepared the source packet and reviewed these images. This is candidate-aware '
          'source QA, not a blind review. Paragraph text is visually checked; bracketed graphic '
          'and handwriting annotations are reviewer descriptions. See SOURCE_QA.json for byte '
          'spans, evidence identities, date roles and qualifications.', '']
    for n in range(1, 5):
        md += [f'## Physical page {n}', '']
        for b in passages:
            if b['page'] == n:
                md += [f"### {b['id']} ({b['kind']})", '', b['text'], '']
    with (ROOT / 'REVIEWED_TRANSCRIPT.md').open('x') as stream:
        stream.write('\n'.join(md))


if __name__ == '__main__':
    main()
