"""Offline negative fixtures for complete paragraph and marked table evidence."""
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

import pytest

from verify_audit import ROOT, capture, validate_audit, validate_review

QA = 'revision/SOURCE_QA.json'
TEXT = 'revision/TRANSCRIPT.md'
SCHEMA = 'revision/SOURCE_QA.schema.json'


@pytest.fixture(scope='module')
def baseline() -> dict[str, bytes]:
    """Capture the immutable audit fixture once."""
    return capture(ROOT)


def checked(files: dict[str, bytes]) -> dict[str, int]:
    """Run the exact selected review validator without manifest resealing."""
    return validate_review(files, QA, TEXT, SCHEMA)


def update_qa(files: dict[str, bytes],
              change: Callable[[dict[str, Any]], None]) -> dict[str, bytes]:
    """Change one typed record without modifying any source artifact."""
    result = files.copy()
    qa = json.loads(result[QA])
    change(qa)
    result[QA] = json.dumps(qa).encode()
    return result


def rewrite(files: dict[str, bytes], before: str, after: str) -> dict[str, bytes]:
    """Rebind all offsets after deliberately falsifying a reviewed source literal."""
    result = files.copy()
    text = result[TEXT].decode().replace(before, after).encode()
    require_change = text != result[TEXT]
    assert require_change
    qa = json.loads(result[QA])
    qa['transcript'].update(sha256=hashlib.sha256(text).hexdigest(), size_bytes=len(text))
    headings = list(re.finditer(rb'^# Physical page ([1-7])\n', text, re.M))
    blocks, marks = [], []
    def binding(start: int, end: int) -> dict[str, Any]:
        """Bind the deliberately edited local transcript bytes."""
        part = text[start:end]
        return dict(start=start, end=end, text=part.decode(),
                    sha256=hashlib.sha256(part).hexdigest())
    for index, page in enumerate(qa['pages']):
        start = headings[index].end()
        end = headings[index + 1].start() if index < 6 else len(text)
        page['transcript_span'] = binding(start, end)
        # Parse full paragraphs including a last line terminated by exactly one LF.
        for n, match in enumerate(re.finditer(rb'\S.*?(?=\n\n|\n?\Z)',
                                              text[start:end], re.S), 1):
            a, b = start + match.start(), start + match.end()
            literal = text[a:b].decode()
            kind = ('table_fragment' if literal.startswith('|') else
                    'editorial_graphic_note' if literal.startswith('[editorial:') else
                    'printed_context')
            blocks.append(dict(id=f"p{page['number']}-b{n:02d}", page=page['number'],
                               kind=kind, transcript_span=binding(a, b), image=page['image']))
        for match in re.finditer(rb'<(u|s|sup)>(.*?)</\1>', text[start:end], re.S):
            marks.append(dict(page=page['number'],
                              kind={'u': 'underline', 's': 'strikethrough',
                                    'sup': 'superscript'}[match[1].decode()],
                              transcript_span=binding(start + match.start(2),
                                                      start + match.end(2)),
                              meaning='visible_typography_only_not_operative_status'))
    qa['blocks'], qa['marks'] = blocks, marks
    result[TEXT], result[QA] = text, json.dumps(qa).encode()
    return result


def test_revised_complete_audit(baseline: dict[str, bytes]) -> None:
    """All copied/revised identities, cell spans and image recipes pass."""
    result = validate_audit(baseline)
    assert result['blocks'] == 98 and result['marks'] == 85
    assert result['data_rows'] == 12 and result['ocr_bytes'] == 14190


def test_initial_failure_preserved(baseline: dict[str, bytes]) -> None:
    """The original missing terminal paragraph remains reproducible evidence."""
    with pytest.raises(ValueError, match='Uncovered terminal paragraph'):
        validate_review(baseline, 'draft/SOURCE_QA.json', 'draft/TRANSCRIPT.md',
                        'draft/SOURCE_QA.schema.json')


def test_drop_terminal_seal_rejected(baseline: dict[str, bytes]) -> None:
    """Final-seal coverage is not excused by complete page span coverage."""
    changed = update_qa(baseline, lambda q: q['blocks'].pop())
    with pytest.raises(ValueError, match='Uncovered terminal paragraph'):
        checked(changed)


def test_drop_strike_record_rejected(baseline: dict[str, bytes]) -> None:
    """Visible strike tags require exact typed markup records."""
    def change(qa: dict[str, Any]) -> None:
        """Remove one struck wording observation."""
        qa['marks'] = [m for m in qa['marks'] if m['transcript_span']['text'] !=
                       'shall not be equipped with continuously burning pilot ignition systems']
    with pytest.raises(ValueError, match='Markup spans'):
        checked(update_qa(baseline, change))


@pytest.mark.parametrize(('before', 'after'), [
    ('<s>9</s> <u>9</u>', '<s>9</s> <u>8</u>'),
    ('<s>1</s> <u>3</u>', '<s>1</s> <u>9</u>'),
    ('Water heating equipment</u>', 'Water heating equipment location</u>'),
    ('| 6 | 54 | <u>50</u> |', '| 6 | 50 | <u>54</u> |'),
])
def test_resealed_cell_misassociation_rejected(baseline: dict[str, bytes], before: str,
                                              after: str) -> None:
    """Typed, resealed local strings cannot swap the reviewed values or row labels."""
    with pytest.raises(ValueError, match='Source data-cell associations'):
        checked(rewrite(baseline, before, after))


@pytest.mark.parametrize(('before', 'after'), [
    ('not including any capacity used for compliance with Section C406 of this code',
     'including capacity used for compliance with Section C406 of this code'),
    ('that serves multiple dwelling units or sleeping units', ''),
    ('208/240-volt', '240-volt'),
    ('minimum capacity of 40 amps', 'capacity of 20 amps'),
    ('continuous raceways and or conductors', 'continuous raceways and conductors'),
    ('indicated in Table R406.4', 'indicated in Table R406.5'),
])
def test_resealed_exception_or_source_repair_rejected(baseline: dict[str, bytes], before: str,
                                                      after: str) -> None:
    """Do not lose exceptions, electrical ratings or source-specific anomalies."""
    with pytest.raises(ValueError, match='Checked qualifier'):
        checked(rewrite(baseline, before, after))


def test_identical_numeric_tables_keep_captions(baseline: dict[str, bytes]) -> None:
    """The R/I and Other fragments cannot exchange their distinct heading contexts."""
    def change(qa: dict[str, Any]) -> None:
        """Swap fragments which happen to show identical numeric strings."""
        qa['tables'][0]['fragment_block_ids'], qa['tables'][2]['fragment_block_ids'] = (
            qa['tables'][2]['fragment_block_ids'], qa['tables'][0]['fragment_block_ids'])
    with pytest.raises(ValueError, match='Table association'):
        checked(update_qa(baseline, change))


def test_crosspage_table_link_rejected(baseline: dict[str, bytes]) -> None:
    """Page 4 Envelope rows cannot be detached or attached to a different table."""
    def change(qa: dict[str, Any]) -> None:
        """Point page 3 Envelope fragment at residential prose."""
        qa['links'][2]['to_block_id'] = 'p4-b02'
    with pytest.raises(ValueError, match='Cross-page link'):
        checked(update_qa(baseline, change))


def test_date_promotion_rejected(baseline: dict[str, bytes]) -> None:
    """A source-stated 30-day clause cannot become a verified computed date."""
    changed = update_qa(baseline, lambda q: q.update(effective_date='2026-06-27'))
    with pytest.raises(ValueError):
        checked(changed)


def test_native_ocr_confusion_rejected(baseline: dict[str, bytes]) -> None:
    """Empty native files cannot acquire source spans from the OCR transcript."""
    def change(qa: dict[str, Any]) -> None:
        """Mislabel reviewed text as native extraction."""
        qa['pages'][0]['native_spans'] = [qa['pages'][0]['transcript_span']]
    with pytest.raises(ValueError):
        checked(update_qa(baseline, change))


def test_changed_original_rejected(baseline: dict[str, bytes]) -> None:
    """Original PDF bytes must match both copied draft and HTTP identity."""
    changed = baseline.copy()
    changed['draft/source/original.pdf'] += b'corruption'
    with pytest.raises(ValueError, match='Changed asset'):
        checked(changed)


def test_wrong_retrieval_date_rejected(baseline: dict[str, bytes]) -> None:
    """Source-stated recorder time cannot replace actual observed GET time."""
    changed = update_qa(baseline, lambda q: q.update(observed_get_completed_at='2026-06-01'))
    with pytest.raises(ValueError, match='HTTP source or timing'):
        checked(changed)


def test_bad_cell_span_rejected(baseline: dict[str, bytes]) -> None:
    """Audit cells require exact offsets in the selected transcript."""
    altered = baseline.copy()
    audit = json.loads(altered['AUDIT.json'])
    audit['table_fragments'][0]['rows'][1]['cells'][1]['start'] += 1
    altered['AUDIT.json'] = json.dumps(audit).encode()
    with pytest.raises(ValueError, match='Text span mismatch'):
        validate_audit(altered)


def test_symbolic_link_refused(tmp_path: Path) -> None:
    """Capture cannot escape through a file link."""
    (tmp_path / 'link').symlink_to(ROOT / 'draft/source/original.pdf')
    with pytest.raises(ValueError, match='Symlink'):
        capture(tmp_path)


def test_captured_buffer_is_consumed(tmp_path: Path) -> None:
    """A later filesystem replacement is not returned as verified original bytes."""
    from verify_audit import read
    target = tmp_path / 'payload'
    target.write_bytes(b'original')
    files = capture(tmp_path)
    target.write_bytes(b'replacement')
    assert read(files, dict(path='payload', sha256=hashlib.sha256(b'original').hexdigest(),
                            size_bytes=8)) == b'original'
