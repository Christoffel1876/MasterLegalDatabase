"""One-time assembly of image-reviewed source text; never changes OCR or source files."""
import hashlib
import json
import math
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from models import (Acquisition, Correction, DateClaim, Manifest, Markup, Observation,
                    Page, Ref, Segment, SourceQA, Span)

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = '0688818dfd4d7726f1eb84b5b57c47580d01b094297a92d4ce88c600ccfe7eba'
RETRIEVAL_SHA = '0ad7b970736921a175de778e05629db8b9191ba2394a692d3715c0a51421c95f'

# Each replacement below was read from the complete image and exact half-page crop.
# Unchanged lines were also visually compared. OCR originals remain untouched.
EDITS = {
    2: {12: 'amendments described below; and'},
    3: {20: None, 21: None, 22: 'Chaffee County Clerk', 23: None},
    4: {
        16: '103.1 Creation of Agency.',
        18: 'charge thereof shall be known as the code '
            'official. The function of the agency shall be the',
        19: 'implementation, administration and enforcement of the provisions of this code.',
        25: '2. The Chaffee County Building Safety Department is the Code Official under this',
        26: 'code and is responsible for permit issuance, structure hardening plan review,',
        30: '3. The Fire District Having Jurisdiction shall conduct field verification and provide',
    },
    5: {
        11: 'Section 401.1 Scope',
        13: '2. One-story detached accessory, non-habitable '
            'structures, such as tool and storage sheds,',
        28: 'Attic ventilation openings located in soffits, '
            'eave overhangs, between rafters at eaves or',
        29: 'in other open overhang areas shall be '
            'specifically designed to prevent the intrusion of fire',
        30: 'embers. Gable end and dormer ventilation openings '
            'shall be located not less than 10 feet',
    },
    6: {18: 'means of a private road and the building address '
        'is not visible from the public way, a'},
    7: {
        3: 'driveways, or where immediate access is necessary for life-safety or firefighting',
        20: 'jurisdiction, if different: (Land Use Code 3.2.4.4.B.)',
    },
    8: {
        3: 'ten (10) feet in width and shall be a minimum of thirty (30) feet in length.',
        4: 'Driveway turnouts shall be comprised of such material and constructed to support',
        16: 'Where this requirement cannot be met due to documented site restrictions,',
        30: 'Exception: Where setback requirements cannot be met due to site restrictions,',
    },
    9: {
        7: 'preparation vehicles is prohibited unless approved by the fire code official.',
        18: 'The exhaust system, including hood, grease-removal devices, fans, ducts,',
        24: '506.4.3 Fuel Gas Systems',
    },
    10: {
        23: 'system(s) provided for the cooking appliance(s). The manual actuation device',
        24: 'shall be unobstructed and in view from the means of egress, located at or near a',
        25: 'means of egress from the cooking area, and at a location acceptable to the fire',
    },
    11: {
        3: 'heat or direct flame impingement can fail rapidly, creating a boiling liquid',
        13: 'accordance with NFPA 58, Liquefied Petroleum Gas Code, and the requirements',
    },
    12: {
        5: 'for fire suppression sufficient to safeguard the lives of residents and firefighters,',
        6: 'protect property, and mitigate the risk of wildfire spread. Required water supply',
        7: 'infrastructure shall be installed and operational prior to the commencement of',
        19: 'Having Jurisdiction. NFPA 1142, Standard on Water Supplies for Suburban and',
        25: 'fire protection needs of the development, subject to Fire District Having',
        29: 'under 75,000 square feet of floor area: at least one 6,000-gallon cistern.',
    },
    13: {
        1: '2. For subdivisions of five or more lots, or nonresidential developments',
        2: 'exceeding 75,000 square feet of floor area: at least one 15,000-gallon',
        3: 'cistern per 30 lots (e.g., 25 lots = one cistern, 32 lots = two cisterns), or',
        4: 'per 100,000 square feet of nonresidential floor area or fraction thereof.',
        13: 'minimum dimensions of fifty (50) feet in length by eight (8) feet in width,',
        15: 'of the access road serving the cistern, and maintained for year-round\naccess.',
        21: 'Where strict compliance with Section 508.3 is impractical due to site conditions,',
    },
    14: {
        14: 'capacity, maintaining fittings and connections in serviceable condition, and',
        22: 'and approval as part of the site plans required '
            'for a permit. The code official is authorized',
        23: 'to waive or modify the requirement for a '
            'defensible space site plan where the application',
        25: 'shall depict driveway gradient slope, turnarounds and turnouts where required,',
    },
}

# Inclusive OCR-line ranges; these partition every raw observation exactly once.
# H=heading, P=paragraph, R=recorder, E=execution label, U=uncertain handwriting, S=seal.
BLOCKS = {
    1: '1-3R 4H 5H 6-10H 11-13P 14-18P 19-23P 24-27P 28-31P 32-34P 35-36P',
    2: '1-2P 3-6P 7-8P 9P 10-12P 13-15P 16-19P 20-22P 23-24H 25-28P 29-33P',
    3: '1-3P 4-6P 7-8P 9E 10-11E 12E 13-17P 18-19P 20-21U 22E 23U 24-25S',
    4: '1H 2H 3-7P 8H 9H 10P 11H 12-13P 14H 15P 16H 17-19P 20P 21H 22-24P 25-29P 30-31P',
    5: '1-7P 8H 9-10P 11H 12H 13-18P 19P 20H 21-25P 26P 27H 28-32P',
    6: '1H 2P 3H 4-23P 24-25P 26P 27H 28-30P 31P 32P 33H',
    7: '1H 2-7P 8-10P 11H 12-13P 14H 15-16P 17-20P 21-22P 23H 24-27P 28H 29P 30-31P 32H',
    8: '1-5P 6H 7H 8-10P 11H 12-15P 16-22P 23-24P 25P 26H 27H 28-29P 30-32P',
    9: '1P 2H 3H 4-7P 8H 9P 10H 11-13P 14H 15-16P 17H 18-20P 21H 22-23P 24H 25-26P 27H 28-30P',
    10: '1-2P 3H 4-8P 9H 10-14P 15H 16-19P 20-21H 22-31P 32P 33H 34H',
    11: '1-7P 8H 9-10P 11H 12-14P 15H 16-21P 22H 23-25P 26P 27H 28H 29-31P',
    12: '1-2P 3H 4-12P 13H 14-20P 21H 22-26P 27H 28-29P',
    13: '1-4P 5H 6-10P 11H 12-15P 16H 17-19P 20H 21-26P 27-28P',
    14: '1-3P 4H 5-10P 11H 12-17P 18H 19P 20H 21-26P',
}
KINDS = dict(H='heading', P='paragraph', R='recorder_metadata', E='execution_label',
             U='handwriting_uncertain', S='seal')
# Exact lexical paragraph/heading selections that visibly bear underline.
UNDERLINED = {
    4: {1, 2, 14, 15, 16, 17},
    5: {1, 6, 8, 9, 11, 12},
    6: {5, 11},
    7: set(range(1, 16)),
    8: set(range(1, 14)) - {9},
    9: set(range(2, 19)),
    10: set(range(1, 13)) - {10},
    11: set(range(1, 14)) - {10},
    12: set(range(1, 10)),
    13: set(range(1, 11)),
    14: set(range(1, 6)),
}


def digest(data: bytes) -> str:
    """Return a SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def ref(path: Path) -> Ref:
    """Bind exact bytes below this package."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(ROOT).as_posix(), sha256=digest(data), size_bytes=len(data))


def put(path: Path, data: bytes) -> None:
    """Write a new file atomically, refusing any existing output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError(f'existing output: {path}')
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(data)
    os.replace(temporary, path)


def span(data: bytes, start: int, end: int) -> Span:
    """Bind a half-open derived-text slice."""
    return Span(start=start, end=end, sha256=digest(data[start:end]))


def mark(segment: Segment, text: str, kind: str, qualification: str = '') -> None:
    """Attach a lexical markup extent to a reviewed transcript segment."""
    assert segment.checked_text is not None
    encoded = segment.checked_text.encode()
    needle = text.encode()
    start = encoded.index(needle)
    segment.markup.append(Markup(kind=kind, start=start, end=start + len(needle),
                                 text=text, qualification=qualification or
                                 'Visible mark over these words; exact '
                                     'glyph/codepoint identity and '
                                 'punctuation-edge geometry are not certified. No '
                                     'legal-effect inference.'))


def main() -> None:
    """Assemble the complete reviewed derivative with unchanged custody and candidates."""
    source = ROOT / 'source/original.pdf'
    assert digest(source.read_bytes()) == SOURCE_SHA
    retrieval = ROOT.parent / 'ptolemy-chaffee-directed-retrieval'
    assert digest((retrieval / 'FINAL_MANIFEST.json').read_bytes()) == RETRIEVAL_SHA
    shutil.copytree(retrieval, ROOT / 'custody/retrieval')
    all_segments = []
    page_rows = []
    corrections = []
    for page in range(1, 15):
        candidate = ROOT / f'ocr/page-{page:04d}/candidate.txt'
        raw = candidate.read_bytes()
        lines = raw.decode().splitlines()
        corrected = list(lines)
        for number, value in EDITS.get(page, {}).items():
            corrections.append(Correction(page=page, line=number, raw_ocr=lines[number-1],
                checked=value, reason='Direct complete-page and exact pixel-crop comparison; '
                'handwritten identities remain uncertified.' if value is None else
                'Visible source wording/punctuation, number, or omitted characters restored '
                'only in the separate checked transcript.'))
            corrected[number-1] = value
        observed = json.loads((ROOT / f'ocr/page-{page:04d}/stdout.json').read_bytes())['lines']
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len((line + '\n').encode()))
        checked_file = b''
        segments = []
        for index, spec in enumerate(BLOCKS[page].split(), 1):
            extent, kind = spec[:-1], KINDS[spec[-1]]
            bounds = extent.split('-')
            first, last = int(bounds[0]), int(bounds[-1])
            selected = corrected[first-1:last]
            text = None if kind == 'handwriting_uncertain' else '\n'.join(selected) + '\n'
            start, end = offsets[first-1], offsets[last]
            boxes = [row['bbox'] for row in observed[first-1:last]]
            y0 = max(0, math.floor(min(1-b[1]-b[3] for b in boxes) * 3300) - 30)
            y1 = min(3300, math.ceil(max(1-b[1] for b in boxes) * 3300) + 30)
            identifier = f'CWRC-P{page:02d}-S{index:02d}'
            notes = []
            if kind == 'handwriting_uncertain':
                notes.append('OCR guesses are rejected as a transcription of identities. '
                             'Handwritten marks are present; names/authorship are not certified.')
            if kind == 'seal':
                text = 'CHAFFEE COUNTY CLERK\nSEAL\nCOLORADO\n'
                notes.append('Upper seal-ring wording is visible but omitted from OCR. '
                             'The appearance of a seal does not authenticate execution.')
            body_span = None
            if text is not None:
                value = text.encode()
                body_span = Span(start=len(checked_file), end=len(checked_file)+len(value),
                                 sha256=digest(value))
                checked_file += value + b'\n'
            crops = [f'crops/page-{page:02d}-{half}.png' for half in
                     (['top'] if y1 <= 1650 else ['bottom'] if y0 >= 1650 else ['top','bottom'])]
            segment = Segment(id=identifier, page=page, kind=kind,
                context=f'Physical page {page}, {kind.replace("_", " ")} {index}',
                ocr_line_numbers=list(range(first,last+1)), ocr_span=span(raw,start,end),
                ocr_text=raw[start:end].decode(), checked_text=text, checked_span=body_span,
                pixel_rect=(0,y0,2550,y1), image_path=f'pages/page-{page:02d}.png',
                crop_paths=crops, continuation_of=None, markup=[], notes=notes)
            if index in UNDERLINED.get(page,set()) and text:
                mark(segment, text.rstrip('\n'), 'underline')
            segments.append(segment)
        # One entire printed chair label is absent from the OCR observations.
        if page == 3:
            text = 'Gina Lucrezi, Chair\n'
            value = text.encode()
            added = Segment(id='CWRC-P03-V01', page=3, kind='execution_label',
                context='Printed chair label beneath blue signature marks',
                ocr_line_numbers=[], ocr_span=None, ocr_text='', checked_text=text,
                checked_span=Span(start=len(checked_file), end=len(checked_file)+len(value),
                                  sha256=digest(value)),
                pixel_rect=(1150,1050,2150,1450), image_path='pages/page-03.png',
                crop_paths=['crops/page-03-top.png'], continuation_of=None, markup=[],
                notes=['Printed label is partly crossed by blue signature strokes but legible. '
                       'No signature identity/authenticity conclusion. Appended in derivative '
                       'because no corresponding OCR line exists; physical position is explicit.'])
            checked_file += value + b'\n'
            segments.append(added)
        transcript = ROOT / f'transcript/page-{page:04d}.txt'
        put(transcript,checked_file)
        page_rows.append(Page(page=page, image=ref(ROOT/f'pages/page-{page:02d}.png'),
            width=2550,height=3300,native=ref(ROOT/f'native/page-{page:04d}.txt'),
            ocr_event=ref(ROOT/f'ocr/page-{page:04d}/EVENT.json'),
            ocr_stdout=ref(ROOT/f'ocr/page-{page:04d}/stdout.json'),
            ocr_stderr=ref(ROOT/f'ocr/page-{page:04d}/stderr.txt'),
            ocr_candidate=ref(candidate),checked_transcript=ref(transcript),
            ocr_line_count=len(lines),segment_ids=[s.id for s in segments],
            full_page_viewed=True,half_page_crops_viewed=True,
            footer_and_borders='Both full-width halves include all page borders and footer. '
            'No separate printed page number or footer text observed; p1 recorder page count '
            'and p3 execution/seal matter are separately retained.'))
        all_segments.extend(segments)
    heading = 'CHAFFEE COUNTY — ORDINANCE NO. 2026-02'
    for segment in all_segments:
        if segment.kind == 'heading':
            heading = ' '.join(segment.checked_text.split())
        segment.context = f'Physical page {segment.page}; source order under: {heading}'
    lookup = {s.id:s for s in all_segments}
    # Paragraph/heading continuations across physical page breaks.
    continuations = [(2,1,1,11),(3,1,2,11),(5,1,4,17),(8,1,7,15),
                     (10,1,9,18),(11,1,10,12),(12,1,11,13),(13,1,12,9),(14,1,13,10)]
    for p,s,pp,ss in continuations:
        lookup[f'CWRC-P{p:02d}-S{s:02d}'].continuation_of=f'CWRC-P{pp:02d}-S{ss:02d}'
    for sid in ['CWRC-P02-S10','CWRC-P02-S11','CWRC-P03-S02']:
        mark(lookup[sid],lookup[sid].checked_text.split('\n')[0],'underline')
    for phrase,kind in [('Exhibit A','underline'),('underline','underline'),
                        ('strikethrough','strikethrough')]:
        mark(lookup['CWRC-P03-S01'],phrase,kind)
    ordinal = lookup['CWRC-P03-S03']
    ordinal_start = ordinal.checked_text.encode().index(b'19TH') + 2
    ordinal.markup.append(Markup(kind='superscript', start=ordinal_start,
        end=ordinal_start + 2, text='TH', qualification='Visible ordinal suffix raised above 19.'))
    mark(lookup['CWRC-P04-S08'],'Chaffee County','underline')
    mark(lookup['CWRC-P04-S12'],'Chaffee County Building Safety Department','underline')
    address=lookup['CWRC-P06-S04']
    mark(address,address.checked_text[address.checked_text.index('All buildings'):].rstrip('\n'),
         'underline')
    fence=lookup['CWRC-P06-S08']
    for phrase,kind in [('materials,','underline'),('or','strikethrough'),
                        ('or fire-retardant treated wood','underline')]:
        # The struck first "or" is specifically after materials, not the earlier "code or".
        if kind=='strikethrough':
            encoded=fence.checked_text.encode();start=encoded.index(b'materials, or')+11
            fence.markup.append(Markup(kind=kind,start=start,end=start+2,text='or',
                qualification='Only this first conjunction after "materials," is struck. '
                'The later conjunction before "fire-retardant" is underlined, not struck.'))
        else:
            mark(fence,phrase,kind)
    mark(lookup['CWRC-P06-S09'],lookup['CWRC-P06-S09'].checked_text.rstrip('\n'),'strikethrough')
    appendix=lookup['CWRC-P14-S09']
    mark(appendix,appendix.checked_text[appendix.checked_text.index('Defensible site plans'):]
         .rstrip('\n'),'underline')
    observations = [
        ('O01',['CWRC-P02-S11','CWRC-P03-S01','CWRC-P04-S03'],
         'The instrument states adoption by reference of chapters 1 through 5 and Appendix A, '
         'B and C of the 2025 CWRC; pages 4–14 supply Exhibit A amendments.',
         'This packet is not the complete referenced 2025 '
             'code. Referenced material and legal effect '
         'have not been reconstructed or independently established.'),
        ('O02',['CWRC-P04-S13','CWRC-P04-S14'],
         'The source introduction says Section 102.4; its next heading says 103.4 Defined Roles '
         'of Enforcement and Approvals.', 'Both source numbers are preserved without '
             'reconciliation.'),
        ('O03',['CWRC-P06-S08','CWRC-P06-S09'],
         'The source says "8 feet way". Only the first "or" after "materials," is struck; '
         'the entire Vinyl Fencing exception sentence is struck. Materials and the final '
         'fire-retardant-treated-wood phrase bear underline.',
         'Plain OCR carries no amendment markup; the checked text also retains struck words '
         'and must be read with the explicit markup records. No live-rule inference.'),
        ('O04',['CWRC-P12-S01','CWRC-P12-S02'],
         'The source continuation reads "approval or water supply systems." The next numbered '
         'heading is 508.1.2 Purpose.', 'Neither "or" nor the numbering is silently repaired.'),
        ('O05',['CWRC-P14-S07','CWRC-P14-S08'],
         'The appendix introduction says Section B101.3; the following heading says '
         'Section 101.3.1 - Defensible Space Site Plans.',
         'The mismatch is source-owned and retained as printed.'),
        ('O06',['CWRC-P05-S09'],
         'Section 403.1.2 names City of Salida, Town of Buena Vista and Town of Poncha Springs.',
         'This is wording in a Chaffee County source, not proof of separate municipal adoption '
         'or a transfer of source ownership.'),
        ('O07',['CWRC-P12-S09','CWRC-P13-S01'],
         'The two cistern capacity items use "under 75,000" and "exceeding 75,000" square feet, '
         'respectively. Printed examples 25 lots/one cistern and 32 lots/two cisterns remain.',
         'No exactly-75,000 boundary rule, fee, or additional arithmetic is invented.'),
        ('O08',['CWRC-P13-S09','CWRC-P13-S10','CWRC-P14-S01'],
         'Alternative compliance/payment in lieu depends on written Fire District approval; '
         'the continuation expressly says payment of money alone does not constitute compliance.',
         'No dollar amount or adopted district payment program is supplied by this review.'),
        ('O09',['CWRC-P03-S04','CWRC-P03-V01','CWRC-P03-S09','CWRC-P03-S11','CWRC-P03-S12'],
         'Blue and dark handwritten execution marks and a clerk seal are visible. The printed '
         'chair label reads Gina Lucrezi, Chair. OCR omits that label and guesses handwriting.',
         'Handwriting identities and execution authenticity are not certified. No full handwritten '
         'name transcription is asserted; seal appearance is not authentication.'),
        ('O10',['CWRC-P01-S01','CWRC-P03-S02','CWRC-P03-S03','CWRC-P03-S07','CWRC-P03-S08'],
         'Recording, printed adoption/reading/publication claims, and relative effectiveness are '
         'distinct. The source says 30 days after publication as required by law.',
         'No calendar effective date is computed and no source date is promoted to verified law. '
         'Recorder fee fields are not a statement that all fees or costs are zero.'),
        ('O11',['CWRC-P09-S08','CWRC-P09-S14','CWRC-P08-S07','CWRC-P12-S05'],
         'The source explicitly cites the 2024 IFC, the 2021 IRC Section P2904, and '
         'Section 4.1.3.2 in their respective passages.',
         'References are transcribed, not resolved against unseen editions or source codes.'),
        ('O12',['CWRC-P09-S16'],
         'No terminal period is apparent after 506.4.3.4 in the Fuel Gas Systems body.',
         'A missing period is not supplied from grammar; '
             'exact character encoding is not recoverable '
         'from a scan.'),
    ]
    obs=[Observation(id=i,segment_ids=ids,statement=s,qualification=q) for i,ids,s,
        q in observations]
    dates=[
        ('6/1/2026 8:47 AM','Recorder stamp; source local time has no printed '
            'timezone',['CWRC-P01-S01']),
        ('March 4, 2008','Recital date of Fire District IGA',['CWRC-P01-S09']),
        ('July 1, 2025','Recital claim about CWRC taking effect',['CWRC-P02-S02']),
        ('April 1, 2026','Recital claim about SB25-142 local adoption deadline',['CWRC-P02-S03']),
        ('30 days after publication as required by '
            'law','Relative effective-date clause',['CWRC-P03-S02']),
        ('19TH DAY OF MAY 2026','Printed adoption statement',['CWRC-P03-S03']),
        ('May 19, 2026','Attestation meeting/adoption claim',['CWRC-P03-S07']),
        ('April 21, 2026','Attestation introduction and reading claim',['CWRC-P03-S07']),
        ('April 30, 2026','Attestation proposed-ordinance publication claim',['CWRC-P03-S07']),
        ('May 28, 2026','Attestation adopted-ordinance publication by '
            'title claim',['CWRC-P03-S08']),
    ]
    result=json.loads((ROOT/'custody/retrieval/events/A001/RESULT.json').read_bytes())
    qa=SourceQA(schema_version='chaffee-cwrc-source-qa-1',
        source_id='chaffee-cwrc-ordinance-2026-02-atlas-directed',authority_id='CO-COUNTY-CHAFFEE',
        layer_id='08_County_Authorities',source_sha=SOURCE_SHA,source=ref(source),
        prepared_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        review_status='checked_passages',
        method='Ptolemy direct full source-image reading first, then unchanged local OCR '
        'comparison and complete exact-half-page crop reading. Acquisition/title aware; '
        'not a blind test. No external reviewer reports consulted.',
        scope='All 14 full physical pages and 28 full-width half-page pixel crops were directly '
        'viewed. All printed headings, paragraphs, lists, '
            'source anomalies, dates and recorder/seal '
        'labels are transcribed; handwritten identities are explicitly unresolved. All raw OCR '
        'lines are accounted for once. This is source fidelity review, not legal interpretation.',
        native_method='PyMuPDF 1.28.2 get_text("text", flags=195, sort=False), UTF-8; '
        'all 14 native files are empty and are preserved unchanged.',
        ocr_method='On-device Apple Vision accurate en-US revision3, CPU-only; no language '
        'correction/automatic language detection; exact raw stdout and observation order retained.',
        transcription_conventions=[
            'Checked transcript is a manual visual derivative, not native text or source bytes. '
            'Line breaks generally follow the unchanged OCR observations, not certified original '
            'typesetting; the missing access line on p13 and '
                'chair label on p3 are explicit repairs.',
            'Straight quotes/apostrophes and ASCII hyphen representations inherited from OCR '
            'are retained as textual representations of scanned punctuation. Curved quote glyphs, '
            'dash lengths, ligatures, exact Unicode and font encoding are not certified.',
            'Bold/italics and indentation are visible in preserved images. Material amendment '
            'underline and strike extents are explicitly recorded; no marked words are deleted '
            'from checked text. Markup byte offsets refer only to each derived checked segment.',
            'Uncertain handwriting has null checked_text. Complete raw guesses remain available '
            'only in the rejected/qualified OCR candidate, never endorsed as signatures.',
        ],
        source_role='County ordinance bearing a recorder stamp, printed adoption/attestation '
        'claims and Exhibit A amendments; signature and legal operation not authenticated.',
        acquisition=Acquisition(source_event=ref(ROOT/'custody/retrieval/events/A001/RESULT.json'),
            frozen_retrieval_manifest=ref(ROOT/'custody/retrieval/FINAL_MANIFEST.json'),
            requested_url=result['requested_url'],final_url=result['final_url'],
            actual_started_at=result['started_at'],actual_completed_at=result['completed_at'],
            http_status=200,actual_repository_received_at=None,method='atlas_directed_public_http',
            qualification='Actual new ordinary-TLS GET, no redirect, captured in frozen retrieval '
            'packet. Earlier official-parent/Location proof remains separately qualified. '
            'Selected response headers retained; original header derivation cannot be replayed '
            'because omitted nonsecret fields were not '
                'preserved. No canonical intake in this task.'),
        pages=page_rows,segments=all_segments,observations=obs,
        date_claims=[DateClaim(value=v,role=r,segment_ids=ids,independent_legal_verification=False)
                     for v,r,ids in dates],external_reports_consulted=False,
        legal_currentness='not_verified',answer_safe=False,verified_adoption_date=None,
        verified_effective_date=None,
        limitations=[
            'Full visual judgment is a recorded reviewer action. The offline verifier checks '
            'hashes, schemas, exact candidate/derived spans, page/segment/markup coverage and '
            're-extraction; it does not independently prove that pixels mean the transcript.',
            'The incorporated 2025 CWRC, referenced NFPA/IFC/IRC, statutes, IGA, district policies '
            'and municipal instruments are not supplied or independently reviewed here.',
            'Recorded execution, adoption, publication and recording dates are source claims; '
            'legal currentness, applicability, validity, signatures and effective calendar date '
            'remain unverified. No semantic rule units, canonical intake or promotion created.',
            'The copied retrieval packet includes two other bounded action outcomes solely to '
            'preserve its exact closure; only D001 has been source-reviewed in this package.',
        ])
    put(ROOT/'SOURCE_QA.json',(qa.model_dump_json(indent=2)+'\n').encode())
    put(ROOT/'SOURCE_QA.schema.json',(json.dumps(SourceQA.model_json_schema(),
        indent=2)+'\n').encode())
    put(ROOT/'MANIFEST.schema.json',(json.dumps(Manifest.model_json_schema(),
        indent=2)+'\n').encode())
    put(ROOT/'CORRECTIONS.schema.json',(json.dumps(Correction.model_json_schema(),
        indent=2)+'\n').encode())
    put(ROOT/'CORRECTIONS.jsonl',
        ('\n'.join(c.model_dump_json() for c in corrections)+'\n').encode())
    text=['---','source_id: chaffee-cwrc-ordinance-2026-02-atlas-directed',
          'authority_id: CO-COUNTY-CHAFFEE','review_status: checked_passages',
          'legal_currentness: not_verified','answer_safe: false','---','',
          '# CWRC ordinance: complete printed-source transcription','',qa.method,'',qa.scope,'',
          'Read SOURCE_QA.json markup and uncertainty alongside these passages. Struck words '
          'remain in the text; this is not a consolidated operative code.','']
    for s in all_segments:
        text.extend([f'## {s.id} — physical page {s.page}', '',s.context,''])
        if s.continuation_of:
            text.extend([f'Continues {s.continuation_of}.',''])
        text.extend(['```text',s.checked_text.rstrip('\n') if s.checked_text else
                     '[Handwritten marks present; transcription of identity unresolved.]','```',''])
        for m in s.markup:
            text.extend([f'Visible {m.kind}: {m.text!r}.',''])
        for note in s.notes:
            text.extend([note,''])
    put(ROOT/'CHECKED_PASSAGES.md',('\n'.join(text)+'\n').encode())


if __name__ == '__main__':
    main()
