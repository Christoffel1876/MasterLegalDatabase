"""Validate and record candidate-aware source QA for four fixed EB013 pages."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Annotated, Literal

import jsonschema
import pymupdf
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path('/Users/mcoors/Documents/Project Geode')
PACKET = ROOT / 'handoffs/grok-pdf-review-2026-09-11-batch-4'
OUT = Path(__file__).resolve().parent
SOURCE_ID = 'fort-collins-wildfire-code-sd005-05'
SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


def sha(data: bytes) -> str:
    """Return an exact byte SHA256."""
    return hashlib.sha256(data).hexdigest()


class StrictModel(BaseModel):
    """Reject extra fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class FileRef(StrictModel):
    """An immutable file identity; paths are absolute local custody references."""
    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(ge=1)]


class ByteSpan(StrictModel):
    """An exact page-native span bound to the corresponding candidate bytes."""
    start_byte: Annotated[int, Field(ge=0)]
    end_byte_exclusive: Annotated[int, Field(gt=0)]
    candidate_start_byte: Annotated[int, Field(ge=0)]
    candidate_end_byte_exclusive: Annotated[int, Field(gt=0)]
    exact_native_text: str
    sha256: SHA

    @model_validator(mode='after')
    def verify(self) -> ByteSpan:
        """Check lengths and hashes before persistence."""
        raw = self.exact_native_text.encode('utf-8')
        if self.end_byte_exclusive - self.start_byte != len(raw):
            raise ValueError('Native span length mismatch')
        if self.candidate_end_byte_exclusive - self.candidate_start_byte != len(raw):
            raise ValueError('Candidate span length mismatch')
        if not raw or sha(raw) != self.sha256:
            raise ValueError('Span content hash mismatch')
        return self


class Crop(StrictModel):
    """A directly rendered inspection aid, not a replacement source image."""
    id: str
    physical_page: Annotated[int, Field(ge=1, le=4)]
    pdf_rect_points: Annotated[list[float], Field(min_length=4, max_length=4)]
    file: FileRef
    rendering: Literal['PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False']
    visually_inspected: Literal[True]


class Chunk(StrictModel):
    """Exhaustive native chunk; display order references do not rewrite it."""
    id: str
    role: Literal['header', 'footer', 'body']
    span: ByteSpan


class Page(StrictModel):
    """Full native page and its immutable image/evidence binding."""
    physical_page: Annotated[int, Field(ge=1, le=4)]
    source_sha256: SHA
    image: FileRef
    native_evidence: FileRef
    original_native_file: FileRef
    original_native_text: str
    original_native_sha256: SHA
    candidate_start_byte: int
    candidate_end_byte_exclusive: int
    native_chunks: list[Chunk]
    suggested_visual_order: list[str]
    full_image_visually_inspected: Literal[True]
    lexical_result: Literal['no_word_or_number_correction_identified']
    native_reextraction_matches: Literal[True]

    @model_validator(mode='after')
    def partition(self) -> Page:
        """Require complete disjoint native-byte preservation."""
        data = self.original_native_text.encode('utf-8')
        if sha(data) != self.original_native_sha256:
            raise ValueError('Page content mismatch')
        cursor = 0
        for chunk in self.native_chunks:
            span = chunk.span
            if span.start_byte != cursor:
                raise ValueError('Native gap or overlap')
            if data[span.start_byte:span.end_byte_exclusive] != span.exact_native_text.encode():
                raise ValueError('Chunk text mismatch')
            if span.candidate_start_byte != self.candidate_start_byte + span.start_byte:
                raise ValueError('Candidate offset mismatch')
            cursor = span.end_byte_exclusive
        if cursor != len(data):
            raise ValueError('Native partition incomplete')
        ids = [c.id for c in self.native_chunks]
        if sorted(ids) != sorted(self.suggested_visual_order):
            raise ValueError('Visual order must reference every original chunk once')
        return self


class Observation(StrictModel):
    """Source wording and separate physical marks without legal-effect inference."""
    id: str
    physical_page: Annotated[int, Field(ge=1, le=4)]
    kind: Literal['lexical_verified', 'source_marking', 'source_anomaly',
                  'reading_order', 'scope_boundary']
    region: str
    pdf_rect_points: Annotated[list[float], Field(min_length=4, max_length=4)]
    spans: Annotated[list[ByteSpan], Field(min_length=1)]
    finding: str
    risk_or_limit: str
    crop_ids: list[str]
    legal_effect: Literal['not_determined']


class Review(StrictModel):
    """A bounded candidate-aware source review, not a legal consolidation."""
    schema_version: Literal[1]
    reviewed_at: datetime
    source_id: Literal['fort-collins-wildfire-code-sd005-05']
    assignment_id: Literal['EB-PDF-013']
    status: Literal['pages_1_4_candidate_aware_source_qa_complete_pending_parent_integration']
    legal_currentness: Literal['not_verified']
    review_mode: Literal['candidate_aware_not_blind']
    external_review_consulted: Literal[False]
    prior_source_exposure: str
    source: FileRef
    packet_manifest: FileRef
    candidate: FileRef
    source_page_count: Literal[8]
    reviewed_pages: list[Page]
    crops: list[Crop]
    observations: list[Observation]
    text_corrections: Annotated[list[str], Field(max_length=0)]
    preservation_policy: str
    limits: list[str]
    verification_checks: list[str]

    @model_validator(mode='after')
    def bind(self) -> Review:
        """Require observations to cite this fixed page inventory and source."""
        pages = {p.physical_page: p for p in self.reviewed_pages}
        if list(pages) != [1, 2, 3, 4]:
            raise ValueError('Only pages 1-4, exactly once and ordered')
        ids = [o.id for o in self.observations]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate observation ID')
        crops = {c.id: c for c in self.crops}
        for p in pages.values():
            if p.source_sha256 != self.source.sha256:
                raise ValueError('Page/source mismatch')
        for o in self.observations:
            p = pages[o.physical_page]
            raw = p.original_native_text.encode()
            for s in o.spans:
                if raw[s.start_byte:s.end_byte_exclusive] != s.exact_native_text.encode():
                    raise ValueError('Observation source-byte mismatch')
                if s.candidate_start_byte != p.candidate_start_byte + s.start_byte:
                    raise ValueError('Observation candidate-byte mismatch')
            for crop_id in o.crop_ids:
                if crops[crop_id].physical_page != o.physical_page:
                    raise ValueError('Observation/crop page mismatch')
        return self


def ref(path: Path) -> FileRef:
    """Read a regular non-symlink file and bind its exact bytes."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Unsafe or absent path: {path}')
    raw = path.read_bytes()
    return FileRef(path=str(path), sha256=sha(raw), size_bytes=len(raw))


def persist(path: Path, raw: bytes) -> None:
    """Create new output atomically; never overwrite a prior record."""
    if path.exists():
        raise FileExistsError(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('xb') as stream:
        stream.write(raw)
    tmp.replace(path)


CROP_SPECS = {
    'p1-citations-duplicate-c': (1, [65., 188., 550., 406.]),
    'p2-notices-blanks': (2, [65., 190., 550., 294.]),
    'p2-authority-publication': (2, [65., 477., 550., 680.]),
    'p3-title-replacement': (3, [65., 180., 550., 226.]),
    'p3-historic-modifications': (3, [85., 261., 550., 348.]),
    'p3-exception-deletion': (3, [65., 360., 550., 555.]),
    'p4-thresholds': (4, [100., 70., 550., 277.]),
    'p4-exemption-tail': (4, [100., 292., 550., 445.]),
    'p4-old-section-103': (4, [65., 452., 550., 706.]),
}


def make_review() -> Review:
    """Bind checked observations to untouched machine text and source images."""
    manifest = json.loads((PACKET / 'manifest.json').read_bytes())
    doc = next(d for d in manifest['documents'] if d['source_id'] == SOURCE_ID)
    source = ref(PACKET / doc['original']['path'])
    candidate = ref(PACKET / doc['candidate']['path'])
    candidate_bytes = Path(candidate.path).read_bytes()
    pdf = pymupdf.open(source.path)
    if len(pdf) != 8 or pdf.is_repaired or pdf.is_encrypted:
        raise ValueError('Unexpected PDF structure')
    page_metadata = {p['physical_page']: p for p in doc['pages'][:4]}
    texts: dict[int, str] = {}
    pages: list[Page] = []

    def span(n: int, start: int, end: int) -> ByteSpan:
        raw = texts[n].encode()[start:end]
        offset = page_metadata[n]['candidate_text_offset_bytes']
        if candidate_bytes[offset+start:offset+end] != raw:
            raise ValueError('Candidate substring mismatch')
        return ByteSpan(start_byte=start, end_byte_exclusive=end,
                        candidate_start_byte=offset+start,
                        candidate_end_byte_exclusive=offset+end,
                        exact_native_text=raw.decode(), sha256=sha(raw))

    for n, meta in page_metadata.items():
        evidence_ref = ref(PACKET / meta['evidence']['path'])
        image_ref = ref(PACKET / meta['image']['path'])
        if evidence_ref.sha256 != meta['evidence']['sha256']:
            raise ValueError('Packet evidence hash mismatch')
        if image_ref.sha256 != meta['image']['sha256']:
            raise ValueError('Packet image hash mismatch')
        evidence = json.loads(Path(evidence_ref.path).read_bytes())
        text = evidence['text']
        texts[n] = text
        raw = text.encode()
        if pdf[n-1].get_text('text', sort=False, flags=195) != text:
            raise ValueError('Fresh native extraction differs')
        if sha(raw) != evidence['text_sha256'] or sha(raw) != meta['text_sha256']:
            raise ValueError('Native hash mismatch')
        native_path = OUT / f'page-{n:04d}.original-native.txt'
        if native_path.exists():
            if native_path.read_bytes() != raw:
                raise ValueError('Preserved native byte mismatch')
        else:
            persist(native_path, raw)
        footer_start = raw.index(f'- {n} -'.encode())
        footer_end = footer_start + len(f'- {n} - \n \n'.encode())
        chunks = [Chunk(id=f'p{n}-header', role='header', span=span(n, 0, footer_start)),
                  Chunk(id=f'p{n}-footer', role='footer', span=span(n, footer_start, footer_end)),
                  Chunk(id=f'p{n}-body', role='body', span=span(n, footer_end, len(raw)))]
        pages.append(Page(physical_page=n, source_sha256=source.sha256,
                          image=image_ref, native_evidence=evidence_ref,
                          original_native_file=ref(native_path), original_native_text=text,
                          original_native_sha256=sha(raw),
                          candidate_start_byte=meta['candidate_text_offset_bytes'],
                          candidate_end_byte_exclusive=meta['candidate_text_end_byte_exclusive'],
                          native_chunks=chunks,
                          suggested_visual_order=[f'p{n}-header', f'p{n}-body', f'p{n}-footer'],
                          full_image_visually_inspected=True,
                          lexical_result='no_word_or_number_correction_identified',
                          native_reextraction_matches=True))

    observations: list[Observation] = []

    def piece(n: int, exact: str, occurrence: int = 0) -> ByteSpan:
        raw = texts[n].encode(); needle = exact.encode(); cursor = -1
        for _ in range(occurrence + 1):
            cursor = raw.index(needle, cursor + 1)
        return span(n, cursor, cursor + len(needle))

    def between(n: int, start: str, end: str | None, occurrence: int = 0) -> ByteSpan:
        raw = texts[n].encode(); cursor = -1
        for _ in range(occurrence + 1):
            cursor = raw.index(start.encode(), cursor + 1)
        limit = raw.index(end.encode(), cursor + len(start.encode())) if end else len(raw)
        return span(n, cursor, limit)

    def add(n: int, kind: str, region: str, rect: list[float], spans: list[ByteSpan],
            finding: str, risk: str, crops: list[str] | None = None) -> None:
        observations.append(Observation(
            id=f'EB013-P{n}-O{len(observations)+1:02d}', physical_page=n, kind=kind,
            region=region, pdf_rect_points=rect, spans=spans, finding=finding,
            risk_or_limit=risk, crop_ids=crops or [], legal_effect='not_determined'))

    for n in range(1, 5):
        add(n, 'source_marking', 'Two-line draft header', [160., 30., 455., 67.],
            [piece(n, 'DRAFT FOR DISCUSSION ONLY - \nSUBJECT TO FURTHER REVIEW AND REVISION')],
            'Both draft-warning lines are fully visible and faithfully present in native text.',
            'This source is visibly marked as a draft. No adopted or current effect follows.')
        add(n, 'reading_order', 'Footer precedes body in native extraction', [285., 727., 325., 749.],
            [piece(n, f'- {n} -')],
            'The printed page label is visually at the bottom, but its native bytes occur before the body. The page partition preserves it and provides header/body/footer display references.',
            'Do not treat the footer token as body text or silently rewrite the original byte sequence.')

    add(1, 'source_anomaly', 'Ordinance title', [70., 70., 545., 145.],
        [between(1, 'ORDINANCE NO.', 'A. \n')],
        'Title visibly retains ORDINANCE NO. XXX, 2025, Chapter 5, 2025 Colorado Wildfire Resiliency Code, and appendices with amendments.',
        'XXX is an unresolved placeholder, not an ordinance identifier. The year in the title does not establish adoption.')
    add(1, 'lexical_verified', 'Recitals A and B', [65., 150., 550., 253.],
        [between(1, 'A. \n', 'C. \n')],
        'A and B match. B prints July 1, 2025, Colorado Revised Statutes 24-33.5-1236(2), and the exact unusual wording “8 Code of Regulations Colorado 1507-39(3)”.',
        'Preserve source citation wording; do not silently normalize it or independently certify the recital.', ['p1-citations-duplicate-c'])
    add(1, 'source_anomaly', 'Two consecutive C recitals', [65., 263., 550., 405.],
        [between(1, 'C. \n', 'D. \n')],
        'Two consecutive recitals are both labeled C. The second prints 24-33.5-1237(2)(a), Senate Bill 25-142, and within nine months of Board adoption. Native text agrees.',
        'Do not relabel the second C or calculate a date; these are source claims.', ['p1-citations-duplicate-c'])
    add(1, 'lexical_verified', 'Recitals D through H', [65., 413., 550., 709.],
        [between(1, 'D. \n', None)],
        'D through H match, including Chapters 1, 2, 3, and 5 of the 2024 International Wildland Urban Interface Code and all ten named 2024 construction codes. Italic source terms remain ordinary characters in native text.',
        'Concurrent-adoption and public-interest statements are recitals in this draft, not verified external events. No exhaustive font-style annotation is claimed.')
    add(2, 'lexical_verified', 'Recital I notice intervals', [65., 82., 550., 182.],
        [between(2, 'I. \n', 'J. \n')],
        'Article II, Section 7, publication twice, at least eight (8) days and at least fifteen (15) days are present exactly as printed.',
        'Do not substitute a single interval or claim the notice conditions have been met.')
    add(2, 'source_marking', 'J and K publication blanks', [65., 190., 550., 294.],
        [between(2, 'J. \n', 'In light of')],
        'J has two green-filled underlined blank date areas, each followed by 2025. K has one green-filled underlined blank date area followed by 2025; Exhibit A is underlined. Native underscores represent the blank baselines.',
        'No dates can be supplied. Exact rendered underline glyph counts and opaque-fill mechanics are not certified; native underscore counts are preserved.', ['p2-notices-blanks'])
    add(2, 'lexical_verified', 'Enacting clause and new Article IX', [65., 304., 550., 479.],
        [between(2, 'In light of', 'Pursuant to the power')],
        'Enacting clause, Section 1, CHAPTER 5, Article IX. Wildfire Resiliency Standards, and Sec. 5-370 match. The source Section 1 wording is “Chapter 5 of the City of Fort Collins”.',
        'Do not insert “Code” into the source wording. Enacting syntax alone does not establish enactment.')
    add(2, 'lexical_verified', 'Section 5-370 text', [65., 477., 550., 680.],
        [between(2, 'Pursuant to the power', None)],
        '31-16-202, Charter Article II Section 7, June 1, 2025 publication wording, all property/buildings/structures, the amendment exception, and all articles and appendices are retained.',
        'June 1 publication is distinct from the July 1 adoption recital on page 1. Neither event is independently verified here.', ['p2-authority-publication'])
    add(2, 'source_marking', 'Yellow outline around Article IX and Section 5-370', [52., 419., 568., 721.],
        [between(2, 'Article IX.', None)],
        'A yellow rectangular outline surrounds the Article IX heading, Section 5-370 heading and body; CHAPTER 5 is above the outline.',
        'The outline is a visible source annotation, not a text token or proof of adopted effect.')
    add(3, 'lexical_verified', 'Section 5-371 heading and introductory cross-reference', [65., 70., 550., 141.],
        [between(3, 'Sec. 5-371.', '1. \n')],
        'Heading and reference to § 5-370 agree, including the section symbol.',
        'This page starts local amendment instructions within the same visibly draft document.')
    add(3, 'source_marking', '101.1 jurisdiction replacement', [65., 153., 550., 226.],
        [between(3, '1. \nSection 101.1', '2. \nSection 102.9')],
        'The source strikes [NAME OF JURISDICTION] and highlights “the City of Fort Collins” in yellow immediately after it. Both texts survive in the candidate, including its “]the” adjacency.',
        'Do not delete the struck words or add a separating space in the original. A clean consolidated sentence would lose draft markup unless separately represented.', ['p3-title-replacement'])
    add(3, 'source_marking', '102.9 variance/modification pairs', [85., 261., 550., 348.],
        [piece(3, 'variance', 0), piece(3, 'modification', 0),
         piece(3, 'variance', 1), piece(3, 'modification', 1)],
        'Both occurrences of variance are struck through; both immediately following occurrences of modification have yellow highlighting.',
        'The native “variance modification” pairs are faithful character inventory but must not be read as an unmarked compound term.', ['p3-historic-modifications'])
    add(3, 'lexical_verified', '102.9 substantive text and exception designations', [85., 261., 550., 474.],
        [between(3, '102.9. Historic Structures.', '3. \nSection 102.9.1')],
        'Repair/rehabilitation/contributing-structure conditions, continued historic designation, minimum necessary wording, and exception with all three designations match.',
        'The negative exception wording “do not meet one or more” is preserved without interpretation; markup on variance/modification is handled separately.', ['p3-historic-modifications', 'p3-exception-deletion'])
    add(3, 'source_marking', 'Deletion instruction and struck 102.9.1 paragraph', [65., 486., 550., 555.],
        [between(3, '3. \nSection 102.9.1', '4. \nSection 102.10')],
        'The deletion instruction is unstruck. The following full 102.9.1 heading and paragraph are visibly struck through, ending “consists of the spirit and intent of this code.” Native text preserves both.',
        'Do not read the struck exemption paragraph as a surviving exemption, and do not silently remove it from source evidence.', ['p3-exception-deletion'])
    add(3, 'scope_boundary', '102.10 introduction and first list item', [65., 565., 550., 685.],
        [between(3, '4. \nSection 102.10', None)],
        'The amended-heading instruction, no-authorization-for-violations caveat, compliance-not-required introduction and item 1 (interior alterations) match. Items 2–10 follow on page 4.',
        'Do not sever list items from the introductory caveat or confuse amendment number 4 with exemption item numbers.')
    add(3, 'source_marking', 'Yellow page-body outline', [50., 65., 563., 727.],
        [span(3, pages[2].native_chunks[2].span.start_byte, len(texts[3].encode()))],
        'A yellow rectangular outline surrounds this page’s body, excluding the draft header and printed footer.',
        'This annotation is separate from individual yellow highlighted text and has no inferred legal effect.')
    add(4, 'lexical_verified', '102.10 items 2–5 numerical conditions', [105., 70., 550., 277.],
        [between(4, '2. \nAdditions', '6. \nPainting')],
        'Item 2 uses not more than 500 square feet; items 3 and 4 use less than 25 percent. All three compare conditions to April 1, 2026 using city and county records. Item 5 separately uses less than twenty-five percent and lacks that dated comparison phrase.',
        'Do not collapse items 3–5 or silently add the dated condition to item 5. Roof covering and attachment language remains distinct from exterior walls.', ['p4-thresholds'])
    for number, start, end in [
        (2, 'compared to the condition of the structure on April 1, 2026, as \ndetermined based on city and county records', '.'),
        (3, 'compared to the condition of the exterior walls on \nApril 1, 2026, as determined based on city and county records', '.'),
        (4, 'compared to the condition of the exterior roof covering on April 1, 2026, as \ndetermined based on city and county records', '.'),
    ]:
        add(4, 'source_marking', f'Item {number} yellow comparison clause',
            [140., 70., 550., 238.], [piece(4, start)],
            f'The dated comparison clause in item {number} has yellow highlighting. All its original words are retained.',
            'Highlighting does not establish an effective date or adopted addition.', ['p4-thresholds'])
    add(4, 'lexical_verified', '102.10 items 6–10', [105., 277., 550., 445.],
        [between(4, '6. \nPainting', '5. \nSECTION 103')],
        'Items 6–10 match: maintenance; one-story nonhabitable accessory uses with area not exceeding 120 square feet and separation greater than or equal to 10 feet; Group U including Agricultural Structures more than 50 feet from occupiable or habitable space; fences more than 8 feet; and thirty-five acre parcel with only one residential structure that does not abut a residential or commercial area.',
        'Preserve each inequality, both area/distance conditions, Group U qualifier, and non-abutment condition. No applicability is decided.', ['p4-exemption-tail'])
    add(4, 'scope_boundary', 'Amendment 5 follows exemption item 10', [65., 452., 550., 486.],
        [between(4, '5. \nSECTION 103', 'SECTION 103—CODE COMPLIANCE AGENCY \n103.1')],
        'The outer amendment number 5 resumes after the ten-item exemption list; the instruction says Section 103 is deleted in its entirety and replaced with the following.',
        'Do not renumber this outer 5 as exemption item 11 or merge the two numbering levels.', ['p4-old-section-103'])
    add(4, 'source_marking', 'Entire old Section 103 block struck', [85., 499., 550., 666.],
        [between(4, 'SECTION 103—CODE COMPLIANCE AGENCY \n103.1', '\n \nSECTION 103—CODE COMPLIANCE AGENCY')],
        'The first standalone Section 103 heading and its full 103.1 Creation, 103.2 Appointment and 103.3 Deputies text are visibly struck through, including [INSERT NAME OF DEPARTMENT]. All remain in native text.',
        'An unmarked reading would misrepresent this draft’s presentation. No department name is supplied; no silent removal or consolidation is authorized.', ['p4-old-section-103'])
    add(4, 'source_marking', 'Repeated yellow Section 103 heading', [85., 679., 550., 696.],
        [piece(4, 'SECTION 103—CODE COMPLIANCE AGENCY', 2)],
        'The second standalone Section 103 heading at the bottom is unstruck and yellow-highlighted. It follows the struck old block.',
        'Only this replacement heading appears on page 4; its following content is outside this four-page QA scope. Do not deduplicate it against the struck heading.', ['p4-old-section-103'])
    add(4, 'source_marking', 'Yellow page-body outline', [50., 65., 563., 727.],
        [span(4, pages[3].native_chunks[2].span.start_byte, len(texts[4].encode()))],
        'A yellow rectangular outline surrounds the body, excluding the draft header and footer.',
        'The outline is separate from text highlights and does not establish adoption.')

    crop_records = [Crop(id=label, physical_page=n, pdf_rect_points=rect,
                         file=ref(OUT / f'{label}.png'),
                         rendering='PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False',
                         visually_inspected=True)
                    for label, (n, rect) in CROP_SPECS.items()]
    return Review(
        schema_version=1, reviewed_at=datetime.now(timezone.utc), source_id=SOURCE_ID,
        assignment_id='EB-PDF-013',
        status='pages_1_4_candidate_aware_source_qa_complete_pending_parent_integration',
        legal_currentness='not_verified', review_mode='candidate_aware_not_blind',
        external_review_consulted=False,
        prior_source_exposure='Reviewer prepared this packet and previously viewed its source images. This task compared pages 1–4 with the unchanged native candidate before reading any external EB013 report.',
        source=source, packet_manifest=ref(PACKET / 'manifest.json'), candidate=candidate,
        source_page_count=8, reviewed_pages=pages, crops=crop_records,
        observations=observations, text_corrections=[],
        preservation_policy='All native UTF-8 bytes for pages 1–4 are preserved unchanged, including whitespace, footer placement, struck wording, repeated labels and placeholders. Byte-bound observations and display-order references are separate; no consolidated or operative text is produced.',
        limits=[
            'Only physical pages 1–4 were checked in this task; no eight-page completeness claim.',
            'No external EB013 report was consulted. This is candidate-aware QA, not a blind transcription.',
            'No lexical correction was identified. This does not certify exact visible Unicode codepoints, individual underline-glyph counts or a complete font-style inventory.',
            'Yellow highlights/outlines, green blank fields and strikethroughs are physical source observations; their adopted effect is not inferred.',
            'Source dates and citations are preserved as printed and have not been checked against external law, amendment history or current official sources.',
            'Original acquisition metadata remains the packet’s received-package provenance. This review performed no HTTP requests.',
            'Absolute custody paths bind existing local packet files; the review is not a standalone bundle of every original and upstream receipt.'
        ],
        verification_checks=[
            'Source and candidate match the frozen packet SHA256 and sizes.',
            'All four page image and native-evidence SHA256 values match the packet.',
            'PyMuPDF 1.28.2 get_text(text, sort=False, flags=195) exactly reproduces all four native texts.',
            'Every native page byte matches its packet candidate offset range.',
            'Three disjoint native chunks per page cover every byte exactly once; display-order references contain every chunk exactly once.',
            'Every observation span matches page-native and full candidate bytes, with independent span SHA256.',
            'All four complete images and nine 300 dpi source crops were visually inspected.',
            'Strict Pydantic validation and exported JSON Schema validation pass before record write.'
        ])


def verify_existing() -> None:
    """Validate the frozen review and exact byte bindings without mutation."""
    raw = (OUT / 'SOURCE_QA.json').read_bytes()
    review = Review.model_validate_json(raw)
    schema = json.loads((OUT / 'SOURCE_QA.schema.json').read_bytes())
    if schema != Review.model_json_schema():
        raise ValueError('Schema differs from strict model')
    jsonschema.validate(json.loads(raw), schema)
    files = [review.source, review.packet_manifest, review.candidate]
    for p in review.reviewed_pages:
        files.extend([p.image, p.native_evidence, p.original_native_file])
    files.extend(c.file for c in review.crops)
    for f in files:
        if ref(Path(f.path)) != f:
            raise ValueError(f'File hash mismatch: {f.path}')
    candidate = Path(review.candidate.path).read_bytes()
    source = pymupdf.open(review.source.path)
    for p in review.reviewed_pages:
        data = p.original_native_text.encode()
        if candidate[p.candidate_start_byte:p.candidate_end_byte_exclusive] != data:
            raise ValueError('Whole-page candidate mismatch')
        if Path(p.original_native_file.path).read_bytes() != data:
            raise ValueError('Preserved native file mismatch')
        if source[p.physical_page-1].get_text('text', sort=False, flags=195).encode() != data:
            raise ValueError('Native reextraction mismatch')
    logging.info('Verified %d files, %d pages and %d observations',
                 len(files), len(review.reviewed_pages), len(review.observations))


def main() -> None:
    """Create once or revalidate the fixed review."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify_existing()
        return
    review = make_review()
    raw = (review.model_dump_json(indent=2) + '\n').encode()
    Review.model_validate_json(raw)
    schema = Review.model_json_schema()
    jsonschema.validate(json.loads(raw), schema)
    persist(OUT / 'SOURCE_QA.schema.json', (json.dumps(schema, indent=2)+'\n').encode())
    persist(OUT / 'SOURCE_QA.json', raw)
    verify_existing()
    logging.info('Review SHA256 %s', sha(raw))


if __name__ == '__main__':
    main()
