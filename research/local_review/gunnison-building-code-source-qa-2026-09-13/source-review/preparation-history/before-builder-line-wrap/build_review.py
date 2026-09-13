"""Encode source-image observations; this builder does not establish visual correctness."""
from datetime import datetime, timezone
import hashlib
import json
import re
import pymupdf
from models import Association, Block, Custody, Marking, Note, Page, Review, Span
from crop_tools import Crops
from prepare import ROOT, asset, write


TEXTS = {n: (ROOT / f'transcripts/page-{n:04}.txt').read_bytes() for n in range(1, 17)}
CROPS = Crops.model_validate_json((ROOT / 'CROPS.json').read_bytes())
CROP_MAP = {c.id: c.image for c in CROPS.crops}


def span(number: int, exact: str, start: int | None = None) -> Span:
    """Bind exact UTF-8 bytes in the reviewed transcript, never invented native offsets."""
    raw = exact.encode()
    offset = TEXTS[number].index(raw) if start is None else start
    assert TEXTS[number][offset:offset + len(raw)] == raw
    return Span(page=number, start=offset, end=offset + len(raw), text=exact,
                sha256=hashlib.sha256(raw).hexdigest())


def blocks(number: int) -> list[Block]:
    """Partition every reviewed byte into contextual source blocks."""
    raw = TEXTS[number]
    text = raw.decode()
    starts = {0, raw.index(b'Gunnison County, CO\n')}
    pattern = (r'(?m)^(?:Section |R108\.4\.[12] |Appendix |Table |WHEREAS|'
               r'NOW THEREFORE|INTRODUCED|ATTEST:|MAJOR RENOVATION|MAJOR ADDITION)')
    for match in re.finditer(pattern, text):
        starts.add(len(text[:match.start()].encode()))
    if number == 2:
        for match in re.finditer(r'(?m)^[1-8]\.\s', text):
            starts.add(len(text[:match.start()].encode()))
    if number in [3, 5, 9, 10, 11, 12, 13, 14, 15, 16]:
        starts.add(len(raw) - len(f'{number}\n'.encode()))
    positions = sorted(starts) + [len(raw)]
    result = []
    pix = pymupdf.Pixmap(str(ROOT / f'pages/page-{number:02}.png'))
    for i, (left, right) in enumerate(zip(positions, positions[1:]), 1):
        content = raw[left:right].decode()
        role = ('recording_stamp' if content.startswith('Gunnison County, CO\n')
                else 'printed_pagination' if content == f'{number}\n' else 'body')
        result.append(Block(id=f'P{number:02}B{i:02}', role=role,
                            span=span(number, content, left),
                            pixel_box=[0, 0, pix.width, pix.height], continuation_of=None))
    return result


NOTES = {
    1: [('date_role', 'The resolution heading prints 23- followed by handwritten 22. '
         'Its numbered title and cited code editions are source claims, not verified current law.',
         'RESOLUTION NO: 23-22', None),
        ('date_role', 'The lower recording stamp reads November 14, 2023 at 8:13:55 AM; '
         'this is distinct from the hearing/adoption wording and effective-date clause.',
         '11/14/2023 8:13:55 AM', 'p1-number-stamp')],
    2: [('exception_scope', 'Keep the unincorporated-area limitation and the item 8 immediate-effect '
         'exception with the January 1, 2024 clause. These are transcribed source assertions, '
         'not an independent legal-effect determination.',
         'unincorporated area of Gunnison County effective January 1, 2024, except for item 8\n'
         'below which shall be effective immediately:', None),
        ('layout', 'Items 1–8 refer to Appendix A–H, while the following pages are headed '
         'ATTACHMENT A–H. Both source terms are retained.', 'in Appendix "A"', None),
        ('execution', 'Handwritten fill readings are Puckett Daniels, Smith, 7th, and November. '
         'These are visual readings of filled blanks, not authentication of people or signatures. '
         'The printed 2023 remains separate. Printed-body transcript omits the handwriting, '
         'which is retained in markings and this crop.', 'INTRODUCED by Commissioner',
         'p2-execution'),
        ('transcription_correction', 'OCR dropped item labels 3 and 5 and fragmented quotation '
         'punctuation. Direct image review restores the visible list labels and wording.',
         '3. The "International Mechanical Code"', None)],
    3: [('execution', 'Three signature-like marks and a circular county seal are visible. '
         'Printed commissioner and clerk labels are transcribed; handwritten signature identities '
         'are not inferred from the labels. Barcode remains a graphic, not decoded text.',
         'Elizabeth Smith, Commissioner', 'p3-execution')],
    4: [('layout', 'Three visibly struck spans remain in the transcript and are explicitly marked: '
         'International Private Sewage Disposal Code; private sewage disposal systems; 120. '
         'The replacement text is retained beside them; no clean enacted text is synthesized.',
         'International Private Sewage Disposal Code', 'p4-strikes'),
        ('exception_scope', 'The accessory-structure item retains siting compliance with Articles '
         '11 and 13. The agricultural item retains the non-residential definition, agricultural '
         'operation condition, and county approval before construction.',
         'Section 105.2 Work exempt from permit:', 'p4-strikes')],
    5: [('source_anomaly', 'The related-fees heading is Section 109.5, with Section 109.2.1 and '
         'Section 108.2.1.1 beneath it. Their differing source numbers are not repaired. '
         'Punctuation after Plan review fees is retained as a semicolon from the scan.',
         'Section 109.2.1 Plan review fees;', 'p5-fees'),
        ('exception_scope', 'The 65%, residential 30%, and ERI 22% bases remain within complete '
         'clauses; additional-review hours and independent-review costs are not collapsed into '
         'a single amount. Refund authorization retains both alternatives, the 80% maximum, '
         'no-work condition and original-permittee written request within 180 days.',
         'Section 109.6 Refunds:', 'p5-fees')],
    6: [('source_anomaly', 'The heading is Section 105.5.1 without an R prefix. The scan prints '
         '$75.0 per hour in R108.4.1, while page 5 prints $75.00; no numerical repair is made.',
         '$75.0 per\nhour', 'p6-75-0'),
        ('exception_scope', 'Keep the 0.0075 valuation basis and $55 minimum, greater-than-5,000 '
         'valuation condition, 30%/22% plan-review distinction and full non-refundable $250 '
         'application-credit/12-month forfeiture clause. No fee calculation is performed.',
         'R108.4.2 Application fee:', 'p6-75-0')],
    7: [('table', 'Table R301.2 is presented as labeled prose rather than a ruled grid. '
         'Its design criteria and subheadings are explicitly associated and continue on page 8. '
         'Keep BF-days-100year, 37.2F and all units as printed; do not repair conversions.',
         'Table R301.2 Climatic and Geographic Design Criteria:', 'p7-criteria'),
        ('source_anomaly', 'Refund item 2 is visibly numbered 2 without a following period; '
         'the OCR omitted the number. Both refund conditions remain with the limitation sentence.',
         '2 Not more than 80 percent', None)],
    8: [('table', 'The first seven entries continue Manual J Design Criteria from page 7. '
         '65 and 50 in HDD65/CDD50 are visually subscripted; plain text retains the digits '
         'with a separate marking.', 'HDD65/CDD50: 9.03', 'p8-continuation'),
        ('source_anomaly', 'The source prints 40°F (4.8°C). This is retained without calculating '
         'a conversion or substituting a different temperature.', '40°F\n(4.8°C)',
         'p8-temperature'),
        ('exception_scope', 'Preserve deletion directions for the townhouse section and first '
         'sentence of the dwelling section, the 3,600-square-foot gross-floor-area clause '
         'including utility areas and garages, and the greater-than-5,000 exception separately.',
         'Section R313.1 Townhome automatic sprinkler systems:', None)],
    9: [('layout', 'The five Appendix inclusion directions do not reproduce those underlying '
         'appendices. This sixteen-page source review does not claim review of the referenced '
         'code books or appendices.', 'Appendix AF Passive Radon Gas Controls:', None)],
    10: [('exception_scope', 'The mechanical permit valuation basis and $55 minimum are separate '
          'from the 65% plan-review fee, which is qualified by where plan review is needed. '
          'Both separately numbered appeals provisions are retained.',
          'Section 109.2 Schedule of permit fees:', None)],
    11: [('exception_scope', 'Keep the exact deletion scopes: exceptions 3 and 4; items 8 and '
          '10; all subsections of 621 followed by the replacement prohibition.',
          'Section 303.3 Prohibited locations:', None),
         ('transcription_correction', 'OCR merged and corrupted the final replacement heading '
          'and body. Direct full-page review restores the following and Unvented room heaters '
          'wording; the original OCR remains unchanged.', 'the following:\nUnvented room heaters',
          None)],
    12: [('exception_scope', 'The commissioning exception retains less than 480,000 Btu/h '
          '(140.7kW) cooling OR 600,000 Btu/h (175.8 kW) combined capacities. The R401.2 '
          'Exception #2 continues on page 13; it must not stop at Gross Floor.',
          'Section C408.2 Mechanical systems and service water-heating systems',
          'p12-exception'),
         ('source_anomaly', 'Temperature wording is again 40°F (4.8°C); keep the source values '
          'and the water-detected condition.', '40°F\n(4.8°C)', None)],
    13: [('exception_scope', 'The opening line completes page 12 Exception #2: Area shall comply '
          'with Section R401.2.5 and R401.2.3. It is not an independent new paragraph rule.',
          'Area shall comply with Section R401.2.5 and R401.2.3.', 'p13-continuation'),
         ('source_anomaly', 'The source has lowercase developed under R406.1, unlike uppercase '
          'Developed under page 8 N1106.1. Preserve both and the differing section numbers.',
          'developed per ANSI/RESNET/ICC 301.', None)],
    14: [('transcription_correction', 'The engine omitted the entire five-line appeals '
          'replacement paragraph. It is visibly present and has been transcribed from the '
          'full page and exact crop; missing OCR text is not missing source text.',
          'The Gunnison County Board of Appeals', 'p14-omitted-body')],
    15: [('exception_scope', 'The disaster and cost-differential-waiver amendments only replace '
          'the jurisdiction name; they do not supply the underlying waiver language. '
          'Renovation and addition definitions retain their distinct work-area/added-area bases '
          'and exceeds 50 percent wording.', 'Section 202 General Definitions:', None)],
    16: [('exception_scope', 'Preserve all three exceptions and the complete incidental-work '
          'and code-required-work qualifications in exception 2. Exception 3 retains the '
          'existing-exterior-materials condition. The final deletion is specifically Section '
          '602.1 General as labeled, not a synthesized deletion of every sprinkler provision.',
          'Section 101.5 Additions or alterations:', 'p16-exceptions'),
         ('transcription_correction', 'OCR corrupted the final appeals sentence and omitted '
          'of this code. Direct source reading restores those visible words.',
          'or determinations made by the code official', None)],
}


def main() -> None:
    """Assemble strict page, association, annotation and custody records."""
    page_blocks = {n: blocks(n) for n in range(1, 17)}
    for n, previous, needle in [(8, 7, 'Table R301.2'), (13, 12, 'Section R401.2')]:
        parent = next(b for b in page_blocks[previous] if b.span.text.startswith(needle))
        page_blocks[n][0].continuation_of = parent.id
    pages = []
    for n in range(1, 17):
        notes = []
        for i, (kind, statement, exact, crop) in enumerate(NOTES[n], 1):
            s = span(n, exact)
            notes.append(Note(id=f'P{n:02}N{i:02}', kind=kind, statement=statement,
                              transcript_start=s.start, transcript_end=s.end,
                              exact_transcript=s.text, crop=CROP_MAP.get(crop)))
        pix = pymupdf.Pixmap(str(ROOT / f'pages/page-{n:02}.png'))
        pages.append(Page(number=n, image=asset(ROOT / f'pages/page-{n:02}.png'),
                          native=asset(ROOT / f'native/page-{n:04}.txt'), native_byte_count=0,
                          ocr=asset(ROOT / f'ocr/page-{n:04}.json'),
                          ocr_text=asset(ROOT / f'ocr/page-{n:04}.txt'),
                          transcript=asset(ROOT / f'transcripts/page-{n:04}.txt'),
                          image_width=pix.width, image_height=pix.height,
                          full_image_viewed=True, review_method=
                          'candidate_aware_direct_image_source_qa', notes=notes,
                          blocks=page_blocks[n]))
    associations = []
    parent = 'Table R301.2 Climatic and Geographic Design Criteria'
    for n in [7, 8]:
        text = TEXTS[n].decode()
        left = text.index('Ground Snow Load:') if n == 7 else 0
        right = text.index('Gunnison County, CO') if n == 7 else text.index('Section R302.5.1')
        lines = text[left:right].splitlines(keepends=True)
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.startswith(('Wind Design:', 'Subject to Damage from:',
                                'Manual J Design Criteria:')):
                parent = line.strip().rstrip(':')
                index += 1
                continue
            if ':' not in line:
                raise ValueError('Unbound design-criteria continuation')
            exact = line
            if line.startswith('Ground Snow Load:'):
                while not lines[index + 1].startswith('Wind Design:'):
                    index += 1
                    exact += lines[index]
            label, value = exact.rstrip('\n').split(':', 1)
            if label in ['Seismic Design Category', 'Ice Barrier Underlayment Required',
                         'Flood Hazards', 'Air Freezing Index', 'Mean Annual Temp']:
                parent = 'Table R301.2 Climatic and Geographic Design Criteria'
            s = span(n, exact)
            context = [b.id for b in page_blocks[n]
                       if b.span.start <= s.start < b.span.end]
            if n == 8:
                context.append(page_blocks[n][0].continuation_of)
            associations.append(Association(id=f'DESIGN-{len(associations) + 1:02}',
                                            label=label, value=value.strip(), span=s,
                                            parent_heading=parent, context_block_ids=context))
            index += 1
    markings = []
    for i, exact in enumerate(['International Private Sewage Disposal Code',
                               'private sewage disposal systems', '120'], 1):
        markings.append(Marking(id=f'STRIKE-{i}', kind='struck', page=4, span=span(4, exact),
                                statement='Visible strike line; retain the underlying text '
                                'without treating it as unmarked operative wording.',
                                pixel_box=[145, 205, 1160, 760], identity_verified=False))
    for n in range(1, 17):
        markings.append(Marking(id=f'BARCODE-{n:02}', kind='barcode_presence', page=n,
                                span=None, statement='Recording barcode visible; not decoded.',
                                pixel_box=[0, 0, pages[n - 1].image_width,
                                           pages[n - 1].image_height], identity_verified=False))
    markings.extend([
        Marking(id='HAND-NUMBER', kind='handwritten_fill', page=1,
                span=span(1, '22'), statement='Handwritten suffix reads 22 after printed 23-.',
                pixel_box=[690, 130, 840, 175], identity_verified=False),
        Marking(id='HAND-EXECUTION', kind='handwritten_fill', page=2, span=None,
                statement='Visible filled blanks read Puckett Daniels; Smith; 7th; November. '
                'No identity or execution authentication is implied.',
                pixel_box=[145, 1170, 1145, 1260], identity_verified=False),
        Marking(id='SIGNATURE-P2', kind='signature_presence', page=2, span=None,
                statement='Signature-like mark overlaps the printed Jonathan Houck, Chairperson '
                'label; the mark itself is not transcribed as an authenticated name.',
                pixel_box=[145, 1340, 1145, 1475], identity_verified=False),
        Marking(id='SIGNATURES-P3', kind='signature_presence', page=3, span=None,
                statement='Three signature-like marks above/beside commissioner and clerk labels; '
                'no inferred identities or dates.', pixel_box=[145, 55, 1160, 530],
                identity_verified=False),
        Marking(id='SEAL-P3', kind='seal_presence', page=3, span=None,
                statement='Circular GUNNISON COUNTY / SEAL / COLORADO mark visible; '
                'authenticity not established.', pixel_box=[490, 325, 745, 580],
                identity_verified=False),
        Marking(id='SUBSCRIPT-P8', kind='subscript', page=8,
                span=span(8, 'HDD65/CDD50'), statement='65 and 50 appear as subscripts; '
                'plain-text digits retained with this graphical qualification.',
                pixel_box=[180, 65, 500, 115], identity_verified=False),
    ])
    review = Review(schema_version='1.0', source=asset(ROOT / 'original.pdf'),
                    source_id='gunnison-building-code-resolution-2023-22-sh-ext-003',
                    authority_id='CO-COUNTY-GUNNISON', page_count=16, native_total_bytes=0,
                    source_currentness='not_verified', answer_safe=False,
                    external_reports_consulted=False,
                    review_method='candidate_aware_direct_image_source_qa',
                    legal_adoption_verified=False, signature_identity_verified=False,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    custody=Custody.model_validate_json((ROOT / 'CUSTODY.json').read_bytes()),
                    pages=pages, associations=associations, markings=markings,
                    limitations=[
                        'All sixteen full Poppler page images were directly viewed, then all '
                        'thirteen retained crops. This is candidate-aware Atlas/Popper source QA, '
                        'not blind review, external review or demonstrated model diversity.',
                        'No external reviewer reports were consulted. Initial full-image viewing '
                        'preceded reading generated OCR, but no frozen independent transcript '
                        'preceded OCR comparison; no stronger process-independence claim is made.',
                        'All sixteen native text outputs are empty. Reviewed offsets refer only '
                        'to separately authored UTF-8 transcript bytes, never to nonexistent '
                        'native text. OCR is uncorrected and preserved separately.',
                        'Reviewed transcript normalizes font, underline, italics, quotation-glyph '
                        'encoding and soft line layout. It is not a glyph-perfect facsimile. '
                        'All substantive printed wording, visible numbers and amendment '
                        'instructions are retained. Strikes, handwriting and graphics are '
                        'qualified separately, and source images govern ambiguity.',
                        'Block pixel boxes deliberately contain the full physical page. They '
                        'are not word-level or precise line coordinates. Exact crops and raw '
                        'OCR normalized boxes provide separately labeled region evidence.',
                        'Signature marks, barcodes and decorative seal geometry are retained '
                        'visually, not decoded or authenticated. Partially obscured underlying '
                        'pagination is not reconstructed.',
                        'Review covers the sixteen-page resolution and its attached amendment '
                        'pages only, not the incorporated international codes, referenced '
                        'appendices, later amendments, repeal, adoption authentication or '
                        'current legal effect.',
                        'No arithmetic, fee calculation, source typo repair, statutory '
                        'interpretation, RuleUnit promotion or answer-safe status is performed.',
                    ])
    write(ROOT / 'SOURCE_QA.json', (review.model_dump_json(indent=2) + '\n').encode())
    schema = json.dumps(Review.model_json_schema(), indent=2) + '\n'
    temporary = ROOT / 'SOURCE_QA.schema.json.tmp'
    temporary.write_text(schema)
    temporary.replace(ROOT / 'SOURCE_QA.schema.json')
    lines = ['---', 'title: Gunnison Resolution 23-22 source review',
             'status: source_review_only', 'source_currentness: not_verified',
             'answer_safe: false', 'external_reports_consulted: false', '---', '',
             '# Source review', '',
             'All 16 physical pages were directly inspected. Native text is empty on every '
             'page. The complete reviewed printed-body transcript below remains separate '
             'from the unchanged OCR and graphical/handwriting annotations.', '',
             'The custody receipt is September 13, 2026 repository receipt of a Sherlock '
             'package. Original HTTP acquisition is not independently verified. Source '
             'adoption, recording and effective-date statements have distinct roles; none '
             'certifies present legal status.', '', '## Limitations', '']
    lines.extend('- ' + limit for limit in review.limitations)
    for page in pages:
        lines.extend(['', f'## Physical page {page.number}', '', '```text',
                      TEXTS[page.number].decode().rstrip(), '```', '',
                      '### Image-supported annotations', ''])
        lines.extend(f'- {note.id}: {note.statement}' for note in page.notes)
    lines.extend(['', '## Design criteria associations', '',
                  'The 27 entries remain with their source parent headings and full byte spans. '
                  'Page 8 continues the Manual J list from page 7.', ''])
    for item in associations:
        lines.append(f'- {item.id}, p{item.span.page}, {item.parent_heading}: '
                     f'{item.label}: {item.value}')
    write(ROOT / 'SOURCE_QA.md', ('\n'.join(lines) + '\n').encode())


if __name__ == '__main__':
    main()
