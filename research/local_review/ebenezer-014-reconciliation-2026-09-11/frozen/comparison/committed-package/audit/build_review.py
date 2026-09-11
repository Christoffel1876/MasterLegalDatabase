"""Create or verify bounded candidate-aware EB014 source QA without rewriting input."""
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
SOURCE_ID = 'fort-collins-land-use-article-1-sd005-07'
SOURCE_SHA = '555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a'
SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
RECT = Annotated[list[float], Field(min_length=4, max_length=4)]
PAGE = Annotated[int, Field(ge=1, le=7)]


def sha(raw: bytes) -> str:
    """Return exact byte SHA256."""
    return hashlib.sha256(raw).hexdigest()


class StrictModel(BaseModel):
    """Disallow coercion and unspecified fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class FileRef(StrictModel):
    """A regular local file and immutable byte identity."""
    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(gt=0)]


class Span(StrictModel):
    """Exact native text plus page-relative and full-candidate byte bounds."""
    start_byte: Annotated[int, Field(ge=0)]
    end_byte_exclusive: Annotated[int, Field(gt=0)]
    candidate_start_byte: Annotated[int, Field(ge=0)]
    candidate_end_byte_exclusive: Annotated[int, Field(gt=0)]
    text: str
    sha256: SHA

    @model_validator(mode='after')
    def check(self) -> Span:
        """Validate span lengths and hash."""
        data = self.text.encode()
        if not data or sha(data) != self.sha256:
            raise ValueError('Bad span bytes')
        if self.end_byte_exclusive-self.start_byte != len(data):
            raise ValueError('Native length mismatch')
        if self.candidate_end_byte_exclusive-self.candidate_start_byte != len(data):
            raise ValueError('Candidate length mismatch')
        return self


class Chunk(StrictModel):
    """Disjoint chunk preserving exact native bytes, separate from visibility."""
    id: str
    role: Literal['layout_whitespace', 'header', 'footer', 'body', 'cover_title', 'cover_purpose']
    visibility: Literal['visible_text', 'not_visible_in_checked_render', 'layout_whitespace']
    span: Span


class PageReview(StrictModel):
    """Complete original native page with image binding and visible order."""
    physical_page: PAGE
    source_sha256: SHA
    page_role: Literal['cover', 'accessibility', 'contents', 'substantive']
    printed_page_label: str | None
    native_page_label: str | None
    image: FileRef
    native_evidence: FileRef
    original_native_file: FileRef
    native_text: str
    native_sha256: SHA
    candidate_start_byte: int
    candidate_end_byte_exclusive: int
    chunks: list[Chunk]
    visible_chunk_order: list[str]
    full_page_visually_checked: Literal[True]
    lexical_result: Literal['body_wording_matches_preserve_separate_layout_and_image_gaps']

    @model_validator(mode='after')
    def partition(self) -> PageReview:
        """Require exhaustive partition and visible-order completeness."""
        raw = self.native_text.encode()
        if sha(raw) != self.native_sha256:
            raise ValueError('Native hash mismatch')
        if self.candidate_end_byte_exclusive-self.candidate_start_byte != len(raw):
            raise ValueError('Page/candidate length mismatch')
        cursor = 0
        for chunk in self.chunks:
            s = chunk.span
            if s.start_byte != cursor or raw[s.start_byte:s.end_byte_exclusive] != s.text.encode():
                raise ValueError('Chunk gap, overlap or byte mismatch')
            if s.candidate_start_byte != self.candidate_start_byte + s.start_byte:
                raise ValueError('Chunk candidate offset mismatch')
            cursor = s.end_byte_exclusive
        if cursor != len(raw):
            raise ValueError('Incomplete native partition')
        visible = [c.id for c in self.chunks if c.visibility == 'visible_text']
        if sorted(visible) != sorted(self.visible_chunk_order):
            raise ValueError('Visible-order inventory mismatch')
        return self


class Crop(StrictModel):
    """A direct 300 dpi PDF clip used as an inspection aid."""
    id: str
    physical_page: PAGE
    pdf_rect_points: RECT
    file: FileRef
    rendering: Literal['PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False']
    visually_checked: Literal[True]


class Observation(StrictModel):
    """Checked region with native or explicitly image-only evidence."""
    id: str
    physical_page: PAGE
    source_sha256: SHA
    source_image_sha256: SHA
    kind: Literal['lexical_verified', 'source_anomaly', 'reading_order',
                  'native_not_visible', 'image_only', 'scope_boundary', 'source_layout']
    region: str
    pdf_rect_points: RECT
    native_spans: list[Span]
    image_only_words: str | None
    finding: str
    risk_or_limit: str
    crop_ids: list[str]
    legal_effect: Literal['not_determined']

    @model_validator(mode='after')
    def evidence(self) -> Observation:
        """Do not pretend image-only words have native byte offsets."""
        if self.kind != 'image_only' and not self.native_spans:
            raise ValueError('Native observation needs a byte span')
        if self.kind != 'image_only' and self.image_only_words is not None:
            raise ValueError('Image-only text in native claim')
        if self.kind == 'image_only' and self.native_spans:
            raise ValueError('Image-only claim must not invent native offsets')
        return self


class PDFLink(StrictModel):
    """PDF annotation metadata only; no link was opened."""
    id: str
    physical_page: PAGE
    source_sha256: SHA
    xref: int
    kind: Literal['uri', 'internal']
    pdf_rect_points: RECT
    uri: str | None
    destination_physical_page: PAGE | None
    destination_point: Annotated[list[float], Field(min_length=2, max_length=2)] | None
    destination_zoom: float | None
    source_method: Literal['PyMuPDF 1.28.2 Page.get_links()']
    target_opened: Literal[False]

    @model_validator(mode='after')
    def shape(self) -> PDFLink:
        """Keep URI and internal target roles separate."""
        if self.kind == 'uri':
            if self.uri is None or self.destination_physical_page is not None:
                raise ValueError('URI target shape mismatch')
        elif self.uri is not None or self.destination_physical_page is None:
            raise ValueError('Internal target shape mismatch')
        return self


class Review(StrictModel):
    """Seven-page source QA without current-law or external-review conclusions."""
    schema_version: Literal[1]
    reviewed_at: datetime
    source_id: Literal['fort-collins-land-use-article-1-sd005-07']
    assignment_id: Literal['EB-PDF-014']
    status: Literal['seven_page_candidate_aware_source_qa_complete_pending_parent_integration']
    legal_currentness: Literal['not_verified']
    review_mode: Literal['candidate_aware_not_blind']
    external_review_consulted: Literal[False]
    prior_exposure: str
    source: FileRef
    canonical_raw_source: FileRef
    packet_manifest: FileRef
    candidate: FileRef
    expected_pages: Literal[7]
    pages: list[PageReview]
    crops: list[Crop]
    observations: list[Observation]
    pdf_links: list[PDFLink]
    text_edits_applied: Annotated[list[str], Field(max_length=0)]
    preservation_policy: str
    limits: list[str]
    checks: list[str]

    @model_validator(mode='after')
    def bind(self) -> Review:
        """Require fixed source and exact page/span associations."""
        if self.source.sha256 != SOURCE_SHA or self.canonical_raw_source.sha256 != SOURCE_SHA:
            raise ValueError('Wrong source')
        pages = {p.physical_page: p for p in self.pages}
        if list(pages) != list(range(1,8)) or len(self.pages) != 7:
            raise ValueError('Incorrect seven-page inventory')
        crop_map = {c.id: c for c in self.crops}
        for p in pages.values():
            if p.source_sha256 != self.source.sha256:
                raise ValueError('Wrong page source')
        if len({o.id for o in self.observations}) != len(self.observations):
            raise ValueError('Duplicate observation IDs')
        for o in self.observations:
            p = pages[o.physical_page]
            if o.source_sha256 != self.source.sha256 or o.source_image_sha256 != p.image.sha256:
                raise ValueError('Observation source/image mismatch')
            for s in o.native_spans:
                if p.native_text.encode()[s.start_byte:s.end_byte_exclusive] != s.text.encode():
                    raise ValueError('Observation native mismatch')
                if s.candidate_start_byte != p.candidate_start_byte+s.start_byte:
                    raise ValueError('Observation candidate offset mismatch')
            for cid in o.crop_ids:
                if crop_map[cid].physical_page != o.physical_page:
                    raise ValueError('Wrong observation crop page')
        for link in self.pdf_links:
            if link.source_sha256 != self.source.sha256:
                raise ValueError('Wrong link source')
        return self


def ref(path: Path) -> FileRef:
    """Bind a non-symlink regular file."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Unsafe or absent file: {path}')
    data = path.read_bytes()
    return FileRef(path=str(path), sha256=sha(data), size_bytes=len(data))


def persist(path: Path, data: bytes) -> None:
    """Write a new file atomically without overwriting anything."""
    if path.exists():
        raise FileExistsError(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    with tmp.open('xb') as stream:
        stream.write(data)
    tmp.replace(path)


CROP_SPECS = {
    'p1-logo-title': (1, [60., 70., 400., 220.]),
    'p1-native-footer-region': (1, [35., 725., 330., 765.]),
    'p2-accessibility': (2, [75., 300., 545., 485.]),
    'p3-native-header-region': (3, [0., 10., 280., 42.]),
    'p3-native-footer-region': (3, [35., 725., 330., 765.]),
    'p4-organization-cross-references': (4, [75., 585., 565., 724.]),
    'p6-purpose-qualification': (6, [75., 151., 560., 252.]),
    'p6-inline-page-token': (6, [75., 467., 565., 530.]),
    'p7-conflict-wording': (7, [75., 336., 560., 509.]),
    'p7-severability': (7, [75., 531., 565., 620.]),
}


def collect_links(pdf: pymupdf.Document) -> list[PDFLink]:
    """Record only actual embedded annotations, without visiting their targets."""
    links: list[PDFLink] = []
    for n, page in enumerate(pdf, 1):
        for raw in page.get_links():
            if raw['kind'] not in (1,2):
                raise ValueError('Unexpected link kind')
            uri = raw.get('uri')
            links.append(PDFLink(
                id=f'PDF-P{n}-XREF-{raw["xref"]}', physical_page=n, source_sha256=SOURCE_SHA,
                xref=raw['xref'], kind='uri' if raw['kind']==2 else 'internal',
                pdf_rect_points=[float(x) for x in raw['from']], uri=uri,
                destination_physical_page=raw['page']+1 if raw['kind']==1 else None,
                destination_point=[float(x) for x in raw['to']] if raw['kind']==1 else None,
                destination_zoom=float(raw['zoom']) if raw['kind']==1 else None,
                source_method='PyMuPDF 1.28.2 Page.get_links()', target_opened=False))
    return links


def make_review() -> Review:
    """Build exact evidence bindings and separately recorded visual findings."""
    manifest = json.loads((PACKET/'manifest.json').read_bytes())
    doc = next(d for d in manifest['documents'] if d['source_id']==SOURCE_ID)
    source = ref(PACKET/doc['original']['path'])
    canonical = ref(Path(doc['provenance']['canonical_raw_pdf']['path']))
    candidate = ref(PACKET/doc['candidate']['path'])
    for actual, expected in ((source, doc['original']), (candidate, doc['candidate'])):
        if (actual.sha256,actual.size_bytes)!=(expected['sha256'],expected['size_bytes']):
            raise ValueError('Packet identity mismatch')
    if Path(source.path).read_bytes()!=Path(canonical.path).read_bytes():
        raise ValueError('Canonical source bytes differ')
    pdf = pymupdf.open(source.path)
    if len(pdf)!=7 or pdf.is_repaired or pdf.is_encrypted:
        raise ValueError('Unexpected PDF structure')
    candidate_bytes = Path(candidate.path).read_bytes()
    metadata = {p['physical_page']:p for p in doc['pages']}
    texts: dict[int,str] = {}
    pages: list[PageReview] = []

    def span(n: int, start: int, end: int) -> Span:
        raw=texts[n].encode()[start:end]
        base=metadata[n]['candidate_text_offset_bytes']
        if candidate_bytes[base+start:base+end]!=raw:
            raise ValueError('Candidate span mismatch')
        return Span(start_byte=start,end_byte_exclusive=end,
                    candidate_start_byte=base+start,candidate_end_byte_exclusive=base+end,
                    text=raw.decode(),sha256=sha(raw))

    for n,meta in metadata.items():
        image=ref(PACKET/meta['image']['path'])
        evidence=ref(PACKET/meta['evidence']['path'])
        for actual,expected in ((image,meta['image']),(evidence,meta['evidence'])):
            if (actual.sha256,actual.size_bytes)!=(expected['sha256'],expected['size_bytes']):
                raise ValueError('Page packet identity mismatch')
        e=json.loads(Path(evidence.path).read_bytes())
        text=e['text'];raw=text.encode();texts[n]=text
        if pdf[n-1].get_text('text',sort=False,flags=195)!=text:
            raise ValueError('Native extraction mismatch')
        if sha(raw)!=e['text_sha256'] or sha(raw)!=meta['text_sha256']:
            raise ValueError('Native digest mismatch')
        if len(raw)!=meta['text_size_bytes']:
            raise ValueError('Native length mismatch')
        if candidate_bytes[meta['candidate_text_offset_bytes']:meta['candidate_text_end_byte_exclusive']]!=raw:
            raise ValueError('Complete candidate page mismatch')
        native=OUT/f'page-{n:04d}.original-native.txt'
        if native.exists():
            if native.read_bytes()!=raw:raise ValueError('Preserved native mismatch')
        else:persist(native,raw)
        chunks: list[Chunk]=[]

        def chunk(label: str,role: str,visibility: str,start: int,end: int) -> str:
            cid=f'p{n}-{label}'
            chunks.append(Chunk(id=cid,role=role,visibility=visibility,span=span(n,start,end)))
            return cid

        native_label={1:'1-0',3:'1-1',4:'1-1',5:'1-2',6:'1-3',7:'1-4'}.get(n)
        if n==2:
            order=[chunk('body','body','visible_text',0,len(raw))]
        else:
            fstart=raw.index(native_label.encode())
            hstart=raw.index(b'     ARTICLE 1')
            hend=raw.index(b'\n',hstart)+1
            chunk('leading-space','layout_whitespace','layout_whitespace',0,fstart)
            footer=chunk('footer','footer','not_visible_in_checked_render' if n in (1,3) else 'visible_text',fstart,hstart)
            header=chunk('header','header','not_visible_in_checked_render' if n==3 else 'visible_text',hstart,hend)
            if n==1:
                purpose_start=raw.index(b'General Purpose  ')
                title_start=raw.index(b'ARTICLE 1 \n',purpose_start)
                chunk('body-space','layout_whitespace','layout_whitespace',hend,purpose_start)
                purpose=chunk('cover-purpose','cover_purpose','visible_text',purpose_start,title_start)
                title=chunk('cover-title','cover_title','visible_text',title_start,len(raw))
                order=[header,title,purpose]
            else:
                body=chunk('body','body','visible_text',hend,len(raw))
                order=[body] if n==3 else [header,body,footer]
        pages.append(PageReview(
            physical_page=n,source_sha256=source.sha256,
            page_role={1:'cover',2:'accessibility',3:'contents'}.get(n,'substantive'),
            printed_page_label=native_label if n>=4 else None,native_page_label=native_label,
            image=image,native_evidence=evidence,original_native_file=ref(native),
            native_text=text,native_sha256=sha(raw),
            candidate_start_byte=meta['candidate_text_offset_bytes'],
            candidate_end_byte_exclusive=meta['candidate_text_end_byte_exclusive'],
            chunks=chunks,visible_chunk_order=order,full_page_visually_checked=True,
            lexical_result='body_wording_matches_preserve_separate_layout_and_image_gaps'))

    observations: list[Observation]=[]

    def piece(n: int,exact: str,occurrence: int=0) -> Span:
        raw=texts[n].encode();needle=exact.encode();start=-1
        for _ in range(occurrence+1):start=raw.index(needle,start+1)
        return span(n,start,start+len(needle))

    def between(n: int,start: str,end: str|None) -> Span:
        raw=texts[n].encode();a=raw.index(start.encode())
        b=raw.index(end.encode(),a+len(start.encode())) if end else len(raw)
        return span(n,a,b)

    def add(n: int,kind: str,region: str,rect: list[float],spans: list[Span],
            finding: str,risk: str,crops: list[str]|None=None,image_words: str|None=None) -> None:
        observations.append(Observation(
            id=f'EB014-P{n}-O{len(observations)+1:02d}',physical_page=n,
            source_sha256=source.sha256,source_image_sha256=pages[n-1].image.sha256,
            kind=kind,region=region,pdf_rect_points=rect,native_spans=spans,
            image_only_words=image_words,finding=finding,risk_or_limit=risk,
            crop_ids=crops or [],legal_effect='not_determined'))

    add(1,'native_not_visible','Extracted cover footer',[35.,725.,330.,765.],
        [piece(1,'1-0 | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE')],
        'The native stream contains this footer. The full cover and its 300 dpi footer-region crop show no visible footer text.',
        'Retain these native bytes as not visible in the checked render; do not present 1-0 as a visible printed label or silently delete it. No claim is made about the author’s intent.', ['p1-native-footer-region'])
    add(1,'reading_order','Cover title sequence',[0.,10.,460.,430.],
        [piece(1,'ARTICLE 1 – GENERAL PURPOSE and PROVISIONS'),
         piece(1,'General Purpose  \nand Provisions'),piece(1,'ARTICLE 1 \n')],
        'Visible order is the top article banner, City logo, large ARTICLE 1, then General Purpose and Provisions. Native text places the purpose title before the large ARTICLE 1.',
        'Visible-order references are separate; original whitespace and ordering remain unchanged. Logo wording is separately image-bound.', ['p1-logo-title'])
    add(1,'image_only','City logo on cover',[60.,70.,285.,150.],[],
        'The wordmark visibly reads City of Fort Collins with a mountain/wave graphic. It is an image and is not independently represented by native logo text.',
        'This is a separate visual reading, not an insertion into the candidate, and does not certify exact font glyphs or ownership.', ['p1-logo-title'],'City of Fort Collins')
    add(2,'image_only','City logo and accessibility artwork',[30.,85.,580.,759.],[],
        'The top wordmark reads City of Fort Collins; the page also has an accessibility figure, dotted border and streetscape photograph. Those graphics are not native text.',
        'Descriptions are reviewer annotations, not source captions. No people, building identity or photograph date is inferred.', image_words='City of Fort Collins')
    add(2,'lexical_verified','Accessibility instructions and contact details',[75.,175.,545.,485.],
        [span(2,0,len(texts[2].encode()))],
        'All visible instruction text matches: 970-221-6515, V/TDD Dial 711, adacoordinator@fortcollins.gov, 970-416-4254, the reasonable-accommodation wording and fortcollins.gov/Non-Discrimination.',
        'No contact details or services were checked live. Graphic logo wording is recorded separately.', ['p2-accessibility'])
    add(2,'source_layout','Three underlined links',[75.,300.,545.,485.],
        [piece(2,'adacoordinator@fortcollins.gov'),
         piece(2,'A Request for Reasonable Accommodation'),
         piece(2,'fortcollins.gov/Non-Discrimination')],
        'Three blue underlined link labels are visible. Their actual embedded URI destinations are preserved in pdf_links separately from the displayed strings.',
        'The accommodation link’s full URI is annotation metadata, not printed wording. No target was opened.', ['p2-accessibility'])
    add(3,'native_not_visible','Contents-page extracted header and footer',[0.,10.,330.,765.],
        [piece(3,'1-1 | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE'),
         piece(3,'ARTICLE 1 – GENERAL PURPOSE and PROVISIONS')],
        'Both the recurring header and footer are present in native text but absent from the checked full contents-page render and targeted header/footer crops.',
        'The native 1-1 label here must not be confused with the visible 1-1 on physical page 4. No bytes are removed.', ['p3-native-header-region','p3-native-footer-region'])
    add(3,'lexical_verified','Contents headings and entries',[50.,65.,480.,335.],
        [between(3,'City of Fort Collins - Land Use Code',None)],
        'Visible contents text matches: Divisions 1.1–1.3, sections 1.2.1–1.2.5 and 1.3.1–1.3.3. No visible destination page numbers accompany the entries.',
        'Nine actual internal PDF link annotations are preserved; do not invent clickable targets for the final two entries or infer complete external Article coverage.')
    for n in range(4,8):
        label=pages[n-1].printed_page_label
        add(n,'reading_order','Visible banner and bottom page label',[0.,10.,335.,759.],
            [piece(n,f'{label} | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE'),
             piece(n,'ARTICLE 1 – GENERAL PURPOSE and PROVISIONS')],
            f'Physical page {n} visibly bears printed label {label} at the bottom and the article banner at the top. Native text places the footer before header and body.',
            'Keep physical page identity separate from printed labels. The exhaustive chunk references give visible order without altering extraction bytes.')
    add(4,'lexical_verified','Article and Division 1.1 titles',[50.,70.,570.,193.],
        [between(4,'ARTICLE 1\u202f','The City of Fort Collins Land Use Code')],
        'ARTICLE 1, GENERAL PURPOSE and PROVISIONS, and DIVISION 1.1 ORGANIZATION OF LAND USE CODE match the image.',
        'This is one seven-page Article 1 source, not the complete Land Use Code.')
    add(4,'lexical_verified','Seven-article inventory',[75.,195.,565.,346.],
        [between(4,'The City of Fort Collins Land Use Code','The General Purpose')],
        'The seven (7) articles and all titles match, including Article 7: Rules of Measurement and Definition in the singular.',
        'Do not replace Definition with Definitions or infer that the other articles were reviewed here.')
    add(4,'lexical_verified','Organization and cross-reference prose',[75.,352.,570.,724.],
        [between(4,'The General Purpose',None)],
        'Organization prose, Articles 2 and 4, Articles 3 and 5, Chapter 14, Article 6, Article 7, twelve-step wording and Section 6.2.2 all match. The exception for definitions specific to areas and activities of state interest in Article 6 is retained.',
        'The cited procedures and other articles were not followed or evaluated. Preserve qualifications and cited locations.', ['p4-organization-cross-references'])
    add(5,'lexical_verified','Division 1.2 and title paragraph',[50.,78.,565.,176.],
        [between(5,'DIVISION 1.2','1.2.2 PURPOSE')],
        'Division title, 1.2.1 and the four alternative code names match. The unusual line break after “known,” is present in the source and retained.',
        'Quotation shapes and narrow-space codepoints remain native bytes; exact typographic encoding is not separately certified.')
    add(5,'scope_boundary','Purpose introduction and items A–L',[50.,178.,570.,718.],
        [between(5,'1.2.2 PURPOSE',None)],
        'The purpose introduction and all twelve items A–L match, including named policy plans, climate goals, listed public services and transportation modes. M and N continue on physical page 6.',
        'Do not treat these purpose statements as a complete standalone set of binding requirements; the following qualification on page 6 is part of the source context.')
    add(6,'scope_boundary','Purpose items M and N',[75.,77.,565.,145.],
        [between(6,'(M)','The purpose statements')],
        'Items M and N continue the purpose list from page 5. M visibly has no terminal period; N ends with income levels.',
        'Preserve letter sequence and the source punctuation rather than normalizing them.')
    add(6,'lexical_verified','Purpose-statement qualification',[75.,151.,560.,252.],
        [between(6,'The purpose statements','1.2.3\u202fAUTHORITY')],
        'The complete qualification is retained: not intended as binding standards, terms, conditions, requirements or procedures, unless specifically referenced; Sections 1.2.4, 6.8.2 and 6.14.4; and only to the extent reasonably applicable in context.',
        'Do not omit the exception, contextual limit or guidance-only statement. This verifies wording, not legal applicability.', ['p6-purpose-qualification'])
    add(6,'lexical_verified','Authority section',[50.,256.,565.,335.],
        [between(6,'1.2.3\u202fAUTHORITY','1.2.4 APPLICABILITY')],
        'Authority section matches, including Article XX of the Colorado Constitution; Title 31, Article 2 of Colorado Revised Statutes; City Charter; statutory and common law.',
        'The actual external authorities were not inspected or validated in this task.')
    add(6,'lexical_verified','Applicability first paragraph',[50.,339.,565.,529.],
        [between(6,'1.2.4 APPLICABILITY','Except as hereinafter provided')],
        'Municipal-boundary scope, Article 7 definition, express exemptions, Chapter 14 landmarks example, prior approval and compliance language, and the two numbered policy/purpose qualifications match.',
        'Keep the unless/except clauses and distinction between purpose/policy guidance and applicable standards; no project-specific result is inferred.', ['p6-inline-page-token'])
    add(6,'source_anomaly','Inline - 4 - token',[75.,488.,565.,515.],
        [piece(6,'interpretation - 4 - and application')],
        'The source visibly prints “interpretation - 4 - and application” within the sentence. It is not merely a footer displaced by native reading order.',
        'Do not silently delete - 4 - as an extraction artifact or renumber this physical page.', ['p6-inline-page-token'])
    add(6,'lexical_verified','Conformance and development-review paragraphs',[75.,530.,565.,720.],
        [between(6,'Except as hereinafter provided',None)],
        'The conformance paragraph and full development-review paragraph match, including all listed building/land actions, minimum and maximum limits, overall/project/final plans, building permits, District Standards and approved final-plan review.',
        'The opening “Except as hereinafter provided” and all other applicable standards qualifications remain attached. Ongoing use continues on page 7.')
    add(7,'scope_boundary','Ongoing application and minimum standards',[50.,77.,565.,164.],
        [between(7,'This Land Use Code shall also apply','DIVISION 1.3 LEGAL')],
        'The ongoing-use paragraph continues 1.2.4; it precedes 1.2.5 MINIMUM STANDARDS. Its reasonable-and-logical-interpretation condition and the minimum-standards text match.',
        'Do not assign the ongoing-use paragraph to 1.2.5 or sever it from 1.2.4.')
    add(7,'lexical_verified','Division 1.3 and relationship to City Code',[50.,177.,565.,316.],
        [between(7,'DIVISION 1.3 LEGAL','1.3.2\u202fCONFLICT')],
        'Division and section headings and all relationship text match, including adoption-by-reference wording in Chapter 29 and incorporation of Chapter 1.',
        'These are source assertions; no adopting ordinance, effective date or amendment chain was established.')
    add(7,'lexical_verified','Conflict subsections A and B',[50.,319.,565.,510.],
        [between(7,'1.3.2\u202fCONFLICT','1.3.3\u202fSEVERABILITY')],
        'Both subsections are preserved, including Article 2/3/4 versus Article 5 language, specific-before-stringent wording, and B’s conflicts-not-addressed-in-A condition.',
        'Do not collapse the two clauses or apply their hierarchy to a factual conflict. The source’s grammatical gap is separately recorded.', ['p7-conflict-wording'])
    add(7,'source_anomaly','Missing conjunction in 1.3.2(A)',[75.,338.,565.,371.],
        [piece(7,'contained in Articles 2, 3, or 4 a standard \nor requirement in Article 5')],
        'The source visibly reads “Articles 2, 3, or 4 a standard” without a conjunction between 4 and a. The candidate matches.',
        'Do not silently insert “and,” “or,” punctuation or any other correction.', ['p7-conflict-wording'])
    add(7,'lexical_verified','Severability paragraph',[50.,513.,565.,621.],
        [between(7,'1.3.3\u202fSEVERABILITY',None)],
        'The entire severability section matches, including court or tribunal of competent jurisdiction and the remaining-provisions wording.',
        'This source statement does not independently establish validity or present legal effect.', ['p7-severability'])
    add(7,'source_anomaly','Lowercase it after sentence boundary',[75.,558.,565.,588.],
        [piece(7,'the City. it is the further intent')],
        'The source visibly uses lowercase “it” after “the City.” Native text preserves it.',
        'Do not capitalize it as an unstated editorial repair.', ['p7-severability'])

    crops=[Crop(id=cid,physical_page=n,pdf_rect_points=rect,file=ref(OUT/f'{cid}.png'),
                rendering='PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False',
                visually_checked=True) for cid,(n,rect) in CROP_SPECS.items()]
    return Review(
        schema_version=1,reviewed_at=datetime.now(timezone.utc),source_id=SOURCE_ID,
        assignment_id='EB-PDF-014',
        status='seven_page_candidate_aware_source_qa_complete_pending_parent_integration',
        legal_currentness='not_verified',review_mode='candidate_aware_not_blind',
        external_review_consulted=False,
        prior_exposure='Reviewer prepared the packet and previously viewed source images. All seven pages were now compared against unchanged native text before any external EB014 report consultation.',
        source=source,canonical_raw_source=canonical,packet_manifest=ref(PACKET/'manifest.json'),
        candidate=candidate,expected_pages=7,pages=pages,crops=crops,
        observations=observations,pdf_links=collect_links(pdf),text_edits_applied=[],
        preservation_policy='All seven native texts are preserved byte-for-byte, including non-visible extracted furniture, source anomalies, narrow spaces and original ordering. Visible order, image-only logo words, graphics and embedded link metadata are separate annotations. No corrected or consolidated candidate is substituted.',
        limits=[
            'This is candidate-aware source QA, not a blind review. No external EB014 report was read.',
            'All seven physical pages of this retained PDF were checked, but other Land Use Code articles and cited law were not reviewed.',
            'No body word or number correction was found. Image-only logo text and non-visible native furniture mean the candidate is not a complete facsimile of the visible source.',
            'Exact source Unicode codepoints, font-style inventory, watermark intent and original design intent are not certified.',
            'No visible edition/adoption/effective date was identified in these seven pages. Currency and legal effect remain unverified.',
            'PDF links are embedded annotation evidence only; no URI or other source was opened and no live target availability is claimed.',
            'Only the packet and canonical local byte identities were checked. Upstream HTTP acquisition remains received-package provenance, not a newly witnessed retrieval.',
            'This output references existing packet and canonical paths and is not a portable copy of every upstream source or receipt.'
        ],checks=[
            'Strict Pydantic and exported JSON Schema validation before record write.',
            'Fixed source SHA256, exact canonical copy equality, and frozen packet source/candidate digest and size checks.',
            'All seven image/evidence digest and size checks against the packet.',
            'Fresh PyMuPDF 1.28.2 get_text(text,sort=False,flags=195) equals every preserved native page.',
            'Every page, chunk and observation is bound to exact candidate byte offsets and hashes.',
            'Disjoint native partitions preserve every page byte, with visible order referencing only checked visible chunks.',
            'Seven full images and ten 300 dpi source crops inspected; crop bytes independently reproducible from the source.',
            'All embedded PDF links recorded from Page.get_links(), with internal destinations converted explicitly from zero-based to one-based physical pages.'
        ])


def verify_existing() -> None:
    """Revalidate exact evidence and cross-file bindings without changing output."""
    raw=(OUT/'SOURCE_QA.json').read_bytes()
    review=Review.model_validate_json(raw)
    schema=json.loads((OUT/'SOURCE_QA.schema.json').read_bytes())
    if schema!=Review.model_json_schema():raise ValueError('Schema mismatch')
    jsonschema.validate(json.loads(raw),schema)
    files=[review.source,review.canonical_raw_source,review.packet_manifest,review.candidate]
    for p in review.pages:files.extend([p.image,p.native_evidence,p.original_native_file])
    files.extend(c.file for c in review.crops)
    for f in files:
        if ref(Path(f.path))!=f:raise ValueError(f'File changed: {f.path}')
    manifest=json.loads(Path(review.packet_manifest.path).read_bytes())
    doc=next(d for d in manifest['documents'] if d['source_id']==SOURCE_ID)
    for actual,expected in ((review.source,doc['original']),(review.candidate,doc['candidate'])):
        if (actual.sha256,actual.size_bytes)!=(expected['sha256'],expected['size_bytes']):
            raise ValueError('Frozen packet source/candidate mismatch')
    if Path(review.source.path).read_bytes()!=Path(review.canonical_raw_source.path).read_bytes():
        raise ValueError('Canonical source mismatch')
    candidate=Path(review.candidate.path).read_bytes()
    pdf=pymupdf.open(review.source.path)
    for p in review.pages:
        data=p.native_text.encode()
        if candidate[p.candidate_start_byte:p.candidate_end_byte_exclusive]!=data:
            raise ValueError('Candidate page mismatch')
        if Path(p.original_native_file.path).read_bytes()!=data:
            raise ValueError('Preserved page mismatch')
        if pdf[p.physical_page-1].get_text('text',sort=False,flags=195).encode()!=data:
            raise ValueError('Fresh native mismatch')
        meta=doc['pages'][p.physical_page-1]
        if p.image.sha256!=meta['image']['sha256'] or p.native_evidence.sha256!=meta['evidence']['sha256']:
            raise ValueError('Frozen page reference mismatch')
        for c in p.chunks:
            s=c.span
            if candidate[s.candidate_start_byte:s.candidate_end_byte_exclusive]!=s.text.encode():
                raise ValueError('Candidate chunk mismatch')
    for o in review.observations:
        for s in o.native_spans:
            if candidate[s.candidate_start_byte:s.candidate_end_byte_exclusive]!=s.text.encode():
                raise ValueError('Candidate observation mismatch')
    for c in review.crops:
        data=pdf[c.physical_page-1].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),
                                             clip=pymupdf.Rect(c.pdf_rect_points),alpha=False).tobytes('png')
        if data!=Path(c.file.path).read_bytes():raise ValueError('Crop reproduction mismatch')
    if collect_links(pdf)!=review.pdf_links:raise ValueError('PDF link metadata differs')
    logging.info('Verified %d files, 7 pages, %d observations, %d native spans and %d PDF links',
                 len(files),len(review.observations),sum(len(o.native_spans) for o in review.observations),len(review.pdf_links))


def main() -> None:
    """Create once, or perform read-only verification."""
    logging.basicConfig(level=logging.INFO,format='%(message)s')
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.verify:
        verify_existing();return
    review=make_review();raw=(review.model_dump_json(indent=2)+'\n').encode()
    Review.model_validate_json(raw);schema=Review.model_json_schema()
    jsonschema.validate(json.loads(raw),schema)
    persist(OUT/'SOURCE_QA.schema.json',(json.dumps(schema,indent=2)+'\n').encode())
    persist(OUT/'SOURCE_QA.json',raw)
    verify_existing()
    logging.info('Review SHA256 %s',sha(raw))


if __name__=='__main__':
    main()
