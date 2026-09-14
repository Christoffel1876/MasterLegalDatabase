"""Reproduce the additive source/native comparison from an already frozen visual first pass."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review_models import Binding, CompleteReview, Context, FirstPass, GridRow, Page, Ref, Row
from review_models import Span, Table


def ref(path: Path) -> Ref:
    """Hash one existing immutable member."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(HERE).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
               size_bytes=len(data))


def normalized(text: str) -> str:
    """Normalize whitespace only; retain amounts, punctuation, spelling and codepoints."""
    return ' '.join(text.split())


def find_span(raw: bytes, text: str, after: int = 0) -> Span:
    """Bind a whitespace-normalized phrase to exact native UTF-8 byte offsets."""
    decoded = raw.decode('utf-8')
    tokens = list(re.finditer(r'\S+', decoded))
    words = [m.group() for m in tokens]
    wanted = text.split()
    matches = []
    for i in range(len(words) - len(wanted) + 1):
        if words[i:i + len(wanted)] != wanted:
            continue
        start = len(decoded[:tokens[i].start()].encode())
        end = len(decoded[:tokens[i + len(wanted) - 1].end()].encode())
        if start >= after:
            matches.append((start, end))
    if not matches:
        raise ValueError('Missing exact native phrase: ' + text)
    start, end = matches[0]
    data = raw[start:end]
    return Span(start=start, end=end, sha256=hashlib.sha256(data).hexdigest(),
                text=data.decode('utf-8'))


def derive() -> dict[str, Any]:
    """Derive all row and context bindings without modifying first-pass or source bytes."""
    first = FirstPass.model_validate_json((HERE / 'PASS1.json').read_bytes())
    extraction = json.loads((HERE / 'NATIVE_EXTRACTION.json').read_bytes())
    raw = {i: (HERE / 'native' / f'page-{i:04d}.txt').read_bytes() for i in range(1, 6)}
    rows, tables, bindings = [], [], []
    index = 0
    with pymupdf.open(HERE / 'source/original.pdf') as pdf:
        for page_number in [2, 3, 4]:
            tables_found = pdf[page_number - 1].find_tables().tables
            if len(tables_found) != 1:
                raise ValueError('Expected one complete physical grid')
            table = tables_found[0]
            cells = table.extract()
            grid = []
            after = 0
            for n, pair in enumerate(cells):
                row_id = None
                if pair[1] is not None and pair != ['Service', 'Fee']:
                    old = first.rows[index]
                    if old.physical_page != page_number:
                        raise ValueError('First-pass row page differs')
                    service, fee = pair
                    service_span = find_span(raw[page_number], service, after)
                    fee_span = find_span(raw[page_number], fee, service_span.end)
                    if raw[page_number][service_span.end:fee_span.start].strip():
                        raise ValueError('Intervening source content breaks fee association')
                    after = fee_span.end
                    row_id = old.row_id
                    # Preserve stacked event alternatives as actual line breaks, not source slashes.
                    final_fee = ('\n'.join(line.strip() for line in fee.splitlines())
                                 if row_id in {'R057', 'R058'} else normalized(fee))
                    row = old.model_copy(update={'service': normalized(service), 'fee': final_fee})
                    if row_id == 'R019':
                        row = row.model_copy(update={
                            'linked_context': [x for x in row.linked_context if x != 'CHILD1']})
                    rows.append(row)
                    equal = (normalized(old.service) == normalized(service) and
                             normalized(old.fee) == normalized(fee))
                    bindings.append(Binding(identity=row_id, physical_page=page_number,
                        spans=[service_span, fee_span], normalized_equal=equal,
                        note=('Visual row/column association verified; original native spans retained. '
                              'See additive errata for any first-pass presentation difference.')))
                    index += 1
                grid.append(GridRow(cells=pair, cell_rectangles=[
                    list(cell) if cell is not None else None for cell in table.rows[n].cells],
                    fee_row_id=row_id))
            tables.append(Table(physical_page=page_number, rectangle=list(table.bbox), rows=grid,
                carried_group_from_prior_page=(
                    'Onsite Wastewater Treatment Systems (OWTS)' if page_number == 3 else None)))
    if index != 65:
        raise ValueError('Complete fee row count differs')
    contexts = []
    for old in first.contexts:
        text = old.text.replace('Service | Fee', 'Service\nFee')
        context = old.model_copy(update={'text': text})
        if context.context_id == 'CHILD1':
            context = context.model_copy(update={
                'applies_to': [x for x in context.applies_to if x != 'R019']})
        contexts.append(context)
        span = find_span(raw[context.physical_page], text)
        bindings.append(Binding(identity=context.context_id, physical_page=context.physical_page,
            spans=[span], normalized_equal=normalized(old.text) == normalized(text),
            note='Source context retained; no scope, precedence or legal-effect inference.'))
    return {'pages': [Page.model_validate(p) for p in extraction['pages']], 'rows': rows,
            'contexts': contexts, 'bindings': bindings, 'tables': tables}


def build() -> CompleteReview:
    """Create one new additive record after the immutable source-first freeze."""
    data = derive()
    return CompleteReview(completed_at=datetime.now(timezone.utc),
        status='source_visual_and_native_compared_pending_root_review',
        first_pass=ref(HERE / 'PASS1.json'), source=ref(HERE / 'source/original.pdf'),
        candidate=ref(HERE / 'candidate.txt'), extraction_method='PyMuPDF get_text text',
        extraction_version=pymupdf.VersionBind, extraction_flags=195, extraction_sort=False,
        **data, native_bytes_preserved=8060, source_fee_rows=65, source_groups=7,
        source_table_grid_rows=74,
        geometry_method='PyMuPDF Page.find_tables default line strategy; 1 table on pages 2–4',
        errata=[
            'R032: first-pass Review-Additional joined a visual line wrap. Final display retains '
            'the whitespace-normalized native Review- Additional; exact original cell is preserved.',
            'R045: first-pass Inspections – Year-Round inserted a space after the en dash. '
            'Native/source cell reads Inspections –Year-Round; final display preserves that spacing.',
            'R057 and R058: first-pass slashes were explicit packaging between stacked event '
            'amounts. Final fee strings use source line breaks; no slash is attributed to the PDF.',
            'COLS: first-pass Service | Fee was column packaging. Final context uses a line break '
            'and the complete two-cell grid separately retains the source column relationship.',
            'R019: removed the first-pass implicit link to Routine inspections because the row '
            'label says Residential / Day Treatment Inspection without Routine. The complete '
            'Childcare definitions remain in context; no inspection-type inference is made.',
        ], limitations=[
            'All five physical pages were read visually before native access; this is an Atlas '
            'source-first review, not a blind independent human review or authenticated event log.',
            'Original source text and all 8060 native UTF-8 bytes are unchanged. Whitespace is '
            'normalized in display fields; exact page and cell text is separately retained.',
            'Seven named service groups contain 65 service/fee rows. One fee cell cites a statute '
            'rather than a dollar amount; no amount is supplied for that reference.',
            'The asterisk attaches Includes one reinspection to OWTS New Permit. Numbered '
            'definitions (1)–(7) retain their explicit row references and all exception wording.',
            'All fees are on a per-visit fee basis is preserved alongside explicit two-year, '
            'six-month, hourly, per-person and year-specific cells. No precedence is inferred.',
            'Failure-to-pay paragraph B preserves except as otherwise provided by Section 2; '
            'this five-page source does not resolve that reference.',
            'The closing quotation mark after Inspection in definition (7), 2024/2025 amounts, '
            'missing for in $298.00 1 Event, and unequal numeric formatting are preserved.',
            'Approval October 25, 2023 and effective January 1, 2024 are printed source claims, '
            'not independently verified enactment, complete amendment chain or current law.',
            'The separate Spanish source was not opened; translation equivalence is not reviewed.',
            'Canonical record preserves received-review-package custody. Claimed original HTTP '
            'acquisition and Sherlock batch-cap failures are not cured by this source-text review.',
        ], issuer='El Paso County Board of Health', administering_agency='El Paso County Public Health',
        source_approval_claim='October 25, 2023', source_effective_claim='January 1, 2024',
        legal_currentness='not_verified', translation_equivalence='not_reviewed')


if __name__ == '__main__':
    destination = HERE / 'SOURCE_QA.json'
    if destination.exists():
        raise SystemExit('Refuse overwrite; use validate_review.py for read-only replay')
    result = build()
    destination.write_text(result.model_dump_json(indent=2) + '\n')
    (HERE / 'SOURCE_QA.schema.json').write_text(json.dumps(
        CompleteReview.model_json_schema(), indent=2) + '\n')
    sys.stdout.write(f'{len(result.rows)} rows, {len(result.contexts)} contexts, '
                     f'{len(result.bindings)} bindings\n')
