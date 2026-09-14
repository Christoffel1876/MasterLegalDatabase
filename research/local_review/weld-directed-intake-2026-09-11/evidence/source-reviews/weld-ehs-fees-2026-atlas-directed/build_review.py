"""Build or verify a source-bound Weld EHS fee review without editing PDF bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

BASE = Path(__file__).resolve().parent
SOURCE_SHA = '852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3'
HEADERS = {
    'WELD COUNTY DEPARTMENT OF PUBLIC HEALTH AND ENVIRONMENT',
    'ENVIRONMENTAL HEALTH SERVICES - 2026 FEE SCHEDULE',
}
GROUPS = {
    'BODY ART FACILITY SERVICES', 'CHILD CARE CENTER FEES',
    'FOOD PROTECTION SERVICES', 'INSTITUTION SERVICES', 'MISCELLANEOUS SERVICES',
    'ONSITE WASTEWATER TREATMENT SYSTEM (OWTS)', 'METHAMPHETAMINE PROGRAM SERVICES',
    'WATER QUALITY - BACTERIOLOGICAL ASSESSMENT',
    'WATER QUALITY - CHEMICAL ASSESSMENT', 'MISCELLANEOUS LABORATORY SERVICES',
    'OIL AND GAS - LABORATORY CHEMICAL ASSESSMENT',
}


class Strict(BaseModel):
    """Require explicit, correctly typed fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact relative-file identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """One exhaustive native line, including its original whitespace."""
    id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    role: Literal['blank', 'header', 'footer', 'group', 'label', 'fee', 'note']


class Page(Strict):
    """Native extraction and the directly viewed original-page image."""
    physical_page: int
    native: Asset
    image: Asset
    full_page_directly_viewed: Literal[True] = True
    header_visible: bool
    spans: list[Span]


class FeeRow(Strict):
    """Source row association, with no numeric conversion or invented fee."""
    id: str
    physical_page: int
    group_span: str
    label_spans: list[str] = Field(min_length=1)
    fee_span: str | None
    fee_cell_status: Literal['printed_text', 'visibly_blank']
    note_spans: list[str]

    @model_validator(mode='after')
    def fee_presence(self) -> FeeRow:
        """Distinguish a visible blank cell from an amount or missing extraction."""
        if (self.fee_span is None) != (self.fee_cell_status == 'visibly_blank'):
            raise ValueError('Fee cell status conflicts with its span')
        return self


class Observation(Strict):
    """A bounded direct-image observation, separate from native source text."""
    id: str
    pages: list[int]
    statement: str


class Review(Strict):
    """Complete native evidence and qualified source-row associations."""
    schema_version: Literal[1] = 1
    reviewed_at: AwareDatetime
    source: Asset
    source_id: Literal['weld-ehs-fees-2026-atlas-directed']
    review_mode: Literal['atlas_candidate_aware_direct_source_review']
    status: Literal['complete_native_source_review_with_presentation_qualifications']
    legal_currentness: Literal['not_verified'] = 'not_verified'
    adoption_date: None = None
    effective_date: None = None
    source_year_assertion: Literal['2026'] = '2026'
    pages: list[Page] = Field(min_length=3, max_length=3)
    rows: list[FeeRow]
    observations: list[Observation]
    native_bytes: Literal[7367] = 7367
    edited_source_bytes: Literal[False] = False
    numerical_corrections: Literal[False] = False
    external_review_consulted: Literal[False] = False


def asset(path: Path) -> Asset:
    """Return a hash binding for a local ordinary file."""
    data = path.read_bytes()
    return Asset(path=path.relative_to(BASE).as_posix(),
                 sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def build() -> Review:
    """Bind all original lines and manually reviewed table group associations."""
    pages: list[Page] = []
    rows: list[FeeRow] = []
    for page_num in range(1, 4):
        native = BASE / f'page-{page_num}.native.txt'
        pending: list[str] = []
        spans: list[Span] = []
        group = ''
        cursor = 0
        for index, line in enumerate(native.read_text().splitlines(keepends=True), 1):
            text = line.strip()
            ident = f'P{page_num}-L{index:03d}'
            if not text:
                role = 'blank'
            elif text in HEADERS:
                role = 'header'
            elif text == str(page_num):
                role = 'footer'
            elif text in GROUPS:
                assert not pending, pending
                role = 'group'
                group = ident
            elif text.startswith('(Review and inspection activities'):
                role = 'note'
                assert rows[-1].physical_page == page_num
                rows[-1].note_spans.append(ident)
            elif (text.startswith('Services not listed') or text.startswith('but are not limited')
                  or text.startswith('NOTE:')):
                role = 'note'
            elif (text.startswith('$') or text == 'Market Rate' or text == '3 x Stated Fee'
                  or text.startswith('Application fee of $')):
                role = 'fee'
                assert pending and group, (ident, text)
                rows.append(FeeRow(id=f'EHS-R{len(rows)+1:03d}', physical_page=page_num,
                                   group_span=group, label_spans=pending.copy(),
                                   fee_span=ident, fee_cell_status='printed_text', note_spans=[]))
                pending.clear()
            elif text.startswith('File Review Fees Per Appendix'):
                role = 'label'
                assert not pending
                rows.append(FeeRow(id=f'EHS-R{len(rows)+1:03d}', physical_page=page_num,
                                   group_span=group, label_spans=[ident], fee_span=None,
                                   fee_cell_status='visibly_blank', note_spans=[]))
            else:
                role = 'label'
                pending.append(ident)
            end = cursor + len(line.encode())
            spans.append(Span(id=ident, start=cursor, end=end, text=line, role=role))
            cursor = end
        assert not pending, pending
        pages.append(Page(physical_page=page_num, native=asset(native),
                          image=asset(BASE / f'page-{page_num}.png'),
                          header_visible=page_num == 1, spans=spans))
    observations = [
        ([1, 2, 3], 'The source identifies Weld County Department of Public Health and '
         'Environment and a 2026 Environmental Health Services fee schedule. These pages '
         'show no adoption or effective date and no adopting resolution; year is not a legal date.'),
        ([1, 2, 3], 'The two title/header lines are visible at the top of page 1, while '
         'native extraction places them near its end. The same lines are native on pages '
         '2 and 3 but not visible in their full-page renders. Preserve all extracted bytes '
         'and distinguish these visibility and ordering facts.'),
        ([1], 'The coordinator fee description ends visibly mid-word around if applicab '
         'in the checked crop, and native text ends if applicab. Do not complete the word, '
         'parenthesis or condition. The adjacent $100.00/hour fee is present.'),
        ([1], 'Body-art plan review has an application fee of $100 plus $100.00/hour. '
         'Food plan review, equipment review and HACCP caps are separate $895/$775/$620 '
         'row conditions. The zero-fee school/nonprofit/mobile categories keep their '
         'own CRS 25-4-1607(9)(a)(III) references and scopes.'),
        ([1], 'Preserve source spelling Temproary and Transportion. Do not infer an '
         'exactly-25-person education-course tier between source <25 and >25 conditions. '
         'Reciprocal Licensing/Permitting and Reciprocal Permitting remain different rows.'),
        ([2], 'File Review Fees cites Appendix 5-D, Chapter 5, Weld County Code and has '
         'a visibly blank amount cell. It is not a zero-dollar fee. Lead investigation '
         'retains a one-hour minimum, while the fax row retains $5.00+ and additional-page condition.'),
        ([2], 'The Methamphetamine decontamination permit covers up to four hours for '
         '$400.00. Its following parenthetical describes excess review/inspection time '
         'and is attached as a note to that row. The $100.00/hour rate is a separate row.'),
        ([2], 'The three-times stated-fee row is beneath the bacteriological assessment '
         'heading. Do not silently extend it to every service or to page 3 chemical fees. '
         'OWTS Loan Approval with/without Water Sample retain $248.00/$200.00; the OWTS '
         '$48.00 collection/analysis row remains distinct from bacteriological $52.50/$54.50.'),
        ([3], 'Additional Metals is one wrapped label continuing Nickel, Silver, with '
         'one $23.00 fee. The following market-rate paragraph is a separate note. '
         'Haloacetic Acids, Hexavalent Chromium and Zoonotic Testing print Market Rate; '
         'no numerical amount is supplied for them.'),
        ([3], 'The final NOTE says analyses are at the cited rates unless the amount is '
         'set by a contract approved by the Board of County Commissioners. Preserve the '
         'exception as a page-level note; no contract or replacement amount was reviewed.'),
        ([1, 3], 'The Body Art Steam spore test is $13.00 and Chemical Assessment '
         'Autoclave Spore Test is $14.00. Different labels and service groups are preserved '
         'without harmonizing amounts. Page 3 spellings Atimony, Cholrite, Phenophthalein, '
         'mosquitoe and Gasses remain source text.'),
        ([1, 2, 3], 'All complete pages and five targeted crops were directly viewed by '
         'Atlas. This is candidate-aware review of the retained source and native text, '
         'not a blind transcription or verification of subsequent legal changes. '
         'Typographic underline/superscript/spacing is not fully recreated in plain text.'),
    ]
    return Review(reviewed_at=datetime.now(timezone.utc), source=asset(BASE/'original.pdf'),
                  source_id='weld-ehs-fees-2026-atlas-directed',
                  review_mode='atlas_candidate_aware_direct_source_review',
                  status='complete_native_source_review_with_presentation_qualifications',
                  pages=pages, rows=rows,
                  observations=[Observation(id=f'EHS-O{i:02d}', pages=ps, statement=s)
                                for i, (ps, s) in enumerate(observations, 1)])


def verify(review: Review) -> dict[str, object]:
    """Check unchanged PDF/native bytes, exhaustive lines and complete row ownership."""
    assert review.source.sha256 == SOURCE_SHA
    assert asset(BASE/review.source.path) == review.source
    all_spans: dict[str, Span] = {}
    label_owners: list[str] = []
    fee_owners: list[str] = []
    groups: set[str] = set()
    geometry: dict[str, tuple[float, float, float, float]] = {}
    with pymupdf.open(BASE/review.source.path) as doc:
        assert len(doc) == 3
        for page in review.pages:
            assert asset(BASE/page.native.path) == page.native
            assert asset(BASE/page.image.path) == page.image
            raw = (BASE/page.native.path).read_bytes()
            assert doc[page.physical_page-1].get_text(
                'text', sort=False, flags=195).encode() == raw
            lines = [line for block in doc[page.physical_page-1].get_text(
                'dict', sort=False, flags=195)['blocks'] if block['type'] == 0
                     for line in block['lines']]
            assert [''.join(s['text'] for s in line['spans'])+'\n' for line in lines] == [
                span.text for span in page.spans]
            geometry.update({span.id: tuple(line['bbox'])
                             for span, line in zip(page.spans, lines)})
            cursor = 0
            for span in page.spans:
                assert span.id not in all_spans
                assert span.start == cursor and raw[span.start:span.end] == span.text.encode()
                cursor = span.end
                all_spans[span.id] = span
                if span.role == 'group':
                    groups.add(span.id)
            assert cursor == len(raw)
    assert sum(p.native.size_bytes for p in review.pages) == 7367
    for row in review.rows:
        assert row.group_span in groups
        assert all_spans[row.group_span].id.startswith(f'P{row.physical_page}-')
        label_box = geometry[row.label_spans[0]]
        preceding_groups = [g for g in groups if g.startswith(f'P{row.physical_page}-')
                            and geometry[g][1] < label_box[1]]
        assert max(preceding_groups, key=lambda g: geometry[g][1]) == row.group_span
        for ident in row.label_spans:
            assert all_spans[ident].role == 'label'
            label_owners.append(ident)
        if row.fee_span:
            assert all_spans[row.fee_span].role == 'fee'
            fee_box = geometry[row.fee_span]
            last_label_box = geometry[row.label_spans[-1]]
            assert abs((fee_box[1]+fee_box[3]-last_label_box[1]-last_label_box[3])/2) < .25
            assert fee_box[0] > last_label_box[0]
            fee_owners.append(row.fee_span)
        for ident in row.note_spans:
            assert all_spans[ident].role == 'note'
    assert len(label_owners) == len(set(label_owners))
    assert set(label_owners) == {k for k,v in all_spans.items() if v.role == 'label'}
    assert len(fee_owners) == len(set(fee_owners))
    assert set(fee_owners) == {k for k,v in all_spans.items() if v.role == 'fee'}
    assert len(groups) == 11
    assert sum(r.fee_cell_status == 'visibly_blank' for r in review.rows) == 1
    return {'status':'passed', 'pages':3, 'native_bytes':7367, 'groups':len(groups),
            'rows':len(review.rows), 'printed_fee_cells':len(fee_owners),
            'blank_fee_cells':1, 'native_lines':len(all_spans),
            'row_geometry_checked':True,
            'legal_currentness':'not_verified'}


def write_new(path: Path, text: str) -> None:
    """Write a new generated artifact atomically, refusing to overwrite."""
    assert not path.exists(), path
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(text, encoding='utf-8')
    temp.replace(path)


def main() -> None:
    """Build once or validate frozen output without writes."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        review = Review.model_validate_json((BASE/'SOURCE_QA.json').read_bytes())
        jsonschema.Draft202012Validator(json.loads(
            (BASE/'SOURCE_QA.schema.json').read_text())).validate(review.model_dump(mode='json'))
    else:
        review = build()
    result = verify(review)
    if not args.verify:
        write_new(BASE/'SOURCE_QA.json', review.model_dump_json(indent=2)+'\n')
        write_new(BASE/'SOURCE_QA.schema.json', json.dumps(Review.model_json_schema(),indent=2)+'\n')
        lines = ['---','title: Weld 2026 environmental-health fee source review',
                 'status: source_checked_pending_legal_review','legal_currentness: not_verified',
                 '---','','# Scope','',
                 f'All three source pages and five crops were directly inspected. All 7,367 '
                 f'native bytes are preserved, with {len(review.rows)} rows across eleven '
                 'service groups. One fee cell is visibly blank. Native words and amounts '
                 'are unchanged; row and note associations are separate annotations.', '',
                 '# Source qualifications','']
        lines += [f'- {o.statement}' for o in review.observations]
        lines += ['', '# Verification','',
                  'Run `PYTHONDONTWRITEBYTECODE=1 python build_review.py --verify`.',
                  'This checks native-byte identities, exhaustive line partitions, all row '
                  'label/fee ownership, group bindings and the visibly blank fee distinction. '
                  'It does not certify present legal effect or exact typography.','']
        write_new(BASE/'SOURCE_QA.md','\n'.join(lines))
    logging.warning(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
