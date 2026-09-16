"""One-time additive independent audit construction from preserved evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from audit_models import Asset, Audit, Crop, Finding, Fragment, GapProof, Inspection, Row, Span
from verify_audit import ROOT, TABLES, capture, validate_review


def asset(path: str) -> Asset:
    """Bind a local ordinary file by exact bytes."""
    data = (ROOT / path).read_bytes()
    return Asset(path=path, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def write_model(path: str, model: BaseModel) -> None:
    """Validate typed JSON before exclusive publication."""
    data = model.model_dump_json(indent=2) + '\n'
    type(model).model_validate_json(data)
    with (ROOT / path).open('x') as stream:
        stream.write(data)
    with (ROOT / path.replace('.json', '.schema.json')).open('x') as stream:
        stream.write(json.dumps(type(model).model_json_schema(), indent=2) + '\n')


def byte_span(data: bytes, start: int, end: int) -> Span:
    """Bind one exact marked-up transcript span."""
    part = data[start:end]
    return Span(start=start, end=end, text=part.decode(), sha256=hashlib.sha256(part).hexdigest())


def grid(table: str, block: dict[str, Any], text: bytes) -> Fragment:
    """Preserve all cells and classify the source's merged group headers separately."""
    rows = []
    cursor = block['transcript_span']['start']
    for line in block['transcript_span']['text'].encode().splitlines(keepends=True):
        if line.startswith(b'|') and not line.startswith(b'| ---'):
            cells, begin = [], 1
            for chunk in line.split(b'|')[1:-1]:
                trimmed = chunk.strip()
                start = cursor + begin + len(chunk) - len(chunk.lstrip())
                cells.append(byte_span(text, start, start + len(trimmed)))
                begin += len(chunk) + 1
            kind = ('header' if not rows else 'merged_heading_with_editorial_placeholder'
                    if any('[editorial: merged heading' in c.text for c in cells) else 'data')
            rows.append(Row(kind=kind, cells=cells))
        cursor += len(line)
    return Fragment(table_id=table, block_id=block['id'], page=block['page'], rows=rows)


def main() -> None:
    """Record completed direct-image observations and audited corrected draft."""
    now = datetime.now(timezone.utc).isoformat()
    files = capture(ROOT)
    try:
        validate_review(files, 'draft/SOURCE_QA.json', 'draft/TRANSCRIPT.md',
                        'draft/SOURCE_QA.schema.json')
    except ValueError as error:
        if str(error) != 'Uncovered terminal paragraph':
            raise
    else:
        raise ValueError('Historical defect unexpectedly disappeared')
    original = json.loads(files['draft/SOURCE_QA.json'])
    old_text = files['draft/TRANSCRIPT.md']
    end = original['blocks'][-1]['transcript_span']['end']
    proof = GapProof(checked_at=now, original_review=asset('draft/SOURCE_QA.json'),
                     original_transcript=asset('draft/TRANSCRIPT.md'),
                     last_recorded_block_end=end, transcript_bytes=len(old_text),
                     unrepresented_suffix=byte_span(old_text, end, len(old_text)),
                     observed_error='Uncovered terminal paragraph',
                     disposition='repaired_only_in_separate_root_revision')
    write_model('ORIGINAL_GAP_PROOF.json', proof)
    crop = Crop(source_image=asset('draft/source/page-0007.png'),
                xyxy=(1100, 1430, 1830, 1540), crop=asset('crops/p7-printed-chair.png'),
                method='exact_RGB_pixel_slice_no_resampling')
    inspection = Inspection(
        reviewer='Plato', recorded_at=now,
        method='Direct inspection of all seven full 300 dpi source PNGs and the nine supplied '
        'exact crops, followed by comparison with the complete root transcript and markup. '
        'A tenth, narrowly framed crop was created and directly inspected for the printed '
        'chair surname. This receipt records completed inspections retrospectively; it does '
        'not invent individual tool-display times. Candidate-aware, same model family as Atlas; '
        'no external Grok report or new source consulted.',
        full_pages=[asset(f'draft/source/page-{n:04d}.png') for n in range(1, 8)],
        supplied_crops=[asset('draft/' + c['path']) for c in
                        json.loads(files['draft/CROPS.json'])['items']],
        supplemental_crops=[crop],
        uncertainty='Tiny terminal punctuation markup extents, obscured printed surname c/f, '
        'handwritten identity and seal authenticity remain qualified. No legal effect inferred.')
    write_model('INSPECTION.json', inspection)
    validate_review(files, 'revision/SOURCE_QA.json', 'revision/TRANSCRIPT.md',
                    'revision/SOURCE_QA.schema.json')
    qa = json.loads(files['revision/SOURCE_QA.json'])
    text = files['revision/TRANSCRIPT.md']
    blocks = {b['id']: b for b in qa['blocks']}
    fragments = [grid(table, blocks[b], text) for table, entry in TABLES.items() for b in entry[0]]
    findings = [
        Finding(id='PLATO-A002-01', classification='structural_omission',
                original_evidence=[asset('draft/SOURCE_QA.json'), asset('draft/TRANSCRIPT.md'),
                                   asset('ORIGINAL_GAP_PROOF.json')],
                description='The initial record had 97 blocks; its last block ended at byte '
                '16138 of a 16266-byte transcript. The trailing seal annotation was present '
                'in the transcript but omitted by the paragraph parser because it ended in '
                'one LF. This was a structured coverage omission, not missing source text.',
                disposition='Root supplied a separate revision with 98 blocks, including the '
                'terminal seal annotation. The original seventy-file draft remains unchanged.'),
        Finding(id='PLATO-A002-02', classification='qualified_printed_glyph',
                original_evidence=[asset('draft/source/page-0007.png'),
                                   asset('crops/p7-printed-chair.png'),
                                   asset('draft/TRANSCRIPT.md')],
                description='The third surname character in the printed chair line is crossed '
                'by the blue signature. The initial confident f is not sufficiently supported '
                'by those visible pixels; c/f remains uncertain in this source image.',
                disposition='Root independently viewed the exact crop and changed only a new '
                'revision to Gina Lu[editorial: obscured character, c/f uncertain]rezi, Chair. '
                'No alternate public spelling was looked up and no signature identity certified.'),
        Finding(id='PLATO-A002-03', classification='confirmed_scope',
                original_evidence=[asset('revision/SOURCE_QA.json'),
                                   asset('revision/TRANSCRIPT.md'), asset('INSPECTION.json')],
                description='The remaining printed paragraphs, twenty-two amendment headings, '
                '85 visible underline/strike/superscript spans, seven logical tables, eight '
                'fragments and twelve data rows agree with the reviewed source images within '
                'the declared typography limits. All six cross-page associations are preserved.',
                disposition='Accepted for scoped source-fidelity research review, pending '
                'root integration; no present-law, enactment-chain or execution certification.')]
    audit = Audit(
        schema_version=1, reviewer='Plato', recorded_at=now,
        status='accepted_scoped_revision_pending_root_integration',
        source_id='chaffee-electric-ordinance-2026-01-atlas-directed',
        authority_id='CO-COUNTY-CHAFFEE', source=asset('draft/source/original.pdf'),
        original_review=asset('draft/SOURCE_QA.json'),
        original_transcript=asset('draft/TRANSCRIPT.md'),
        selected_review=asset('revision/SOURCE_QA.json'),
        selected_schema=asset('revision/SOURCE_QA.schema.json'),
        selected_transcript=asset('revision/TRANSCRIPT.md'),
        copy_receipt=asset('COPY_RECEIPT.json'), revision_receipt=asset('REVISION_RECEIPT.json'),
        inspection=asset('INSPECTION.json'), original_draft_files_preserved=70,
        full_pages_inspected=7, supplied_crops_inspected=9, additional_crops_inspected=1,
        logical_tables=7, physical_fragments=8, data_rows=12, table_fragments=fragments,
        findings=findings, limitations=[
            'Plato is an independent agent review within the same model family as Atlas, not '
            'an independent model-family or blind external validation.',
            'Root revision retains original source, full PNGs, nine crops, native files and '
            'all 14190 OCR bytes. Initial failed paragraph coverage and prior spelling remain '
            'historical evidence, not silently overwritten.',
            'Only source-visible markup is encoded. Tiny terminal punctuation extents and '
            'bold/italic styling are not exhaustively certified.',
            'Table R/I superscript b has no local definition; a different table footnote is '
            'not borrowed. Identical replacement numerals remain duplicated with strike/underline.',
            'Commercial water-heater exception lacks the multiple-units condition present '
            'in residential exceptions; the 208/240-volt and 40-amp exception remains intact.',
            'The source says Table R406.4 in the paragraph and displays Table R406.5. Its '
            'duplicate 2.2 numbering and and or wording are preserved without correction.',
            'Recorder stamp and attested publication/adoption statements remain source claims. '
            'The 30-day clause is not converted to a computed effective date; no legal currentness '
            'or execution authenticity is asserted.',
            'Received retrieval evidence is a selected HTTP subset. Original nonpublic header '
            'bytes were not retained upstream; omitted values cannot be replayed. Their deletion '
            'and field filtering are retained receipt claims, not an independently replayed '
            'procedure.',
            'No public request, OCR rerun, canonical intake, inventory change or source-packet '
            'modification occurred in this audit. Historical pre-intake/null fields are not '
            'updated to imply a later canonical action.',
            'Mechanical checks validate captured hashes, spans, markup, table and paragraph '
            'coverage; they are not independent visual perception or legal interpretation.'],
        legal_currentness='not_verified', answer_safe=False, external_bot_reports_consulted=False)
    write_model('AUDIT.json', audit)


if __name__ == '__main__':
    main()
