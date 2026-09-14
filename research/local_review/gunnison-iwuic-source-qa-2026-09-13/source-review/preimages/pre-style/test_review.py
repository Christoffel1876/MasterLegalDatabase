"""Meaningful offline tamper and association checks; no visual/legal certification."""
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from review_models import Asset, Review
from verify_review import ROOT, capture, validate_content


@pytest.fixture(scope='module')
def baseline() -> dict[str, bytes]:
    """Capture immutable input buffers once for independent negative fixtures."""
    return capture(ROOT)


def rewrite(files: dict[str, bytes], mutation: Callable[[dict[str, Any]], None]) -> dict[str, bytes]:
    """Reseal transcript identities after a deliberately wrong semantic edit."""
    result = files.copy()
    qa = json.loads(result['SOURCE_QA.json'])
    mutation(qa)
    for page in qa['pages']:
        blocks = [p for p in qa['checked_passages'] if p['page'] == page['number']]
        data = ''.join(p['text'] + '\n\n' for p in blocks).encode()
        ref = page['reviewed_transcript']
        ref.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        result[ref['path']] = data
        pos = 0
        for block in blocks:
            part = (block['text'] + '\n\n').encode()
            block['reviewed_transcript'] = copy.deepcopy(ref)
            block['reviewed_span'] = dict(start=pos, end=pos + len(part),
                                           sha256=hashlib.sha256(part).hexdigest())
            pos += len(part)
    result['SOURCE_QA.json'] = json.dumps(qa).encode()
    return result


def passage(qa: dict[str, Any], identity: str) -> dict[str, Any]:
    """Find one exact reviewed passage in a fixture."""
    return next(x for x in qa['checked_passages'] if x['id'] == identity)


def test_complete_baseline(baseline: dict[str, bytes]) -> None:
    """All source/OCR/transcript bytes and cross-page instructions are accounted for."""
    assert validate_content(baseline) == dict(pages=4, crops=7, passages=43, amendments=14,
                                             ocr_bytes=5734, candidate_bytes=6186,
                                             reviewed_bytes=6692)


@pytest.mark.parametrize(('identity', 'before', 'after'), [
    ('P1-RECITAL-1', '§38-28-201', '§30-28-201'),
    ('P1-RECITAL-3', '2015', '2021'),
    ('P1-2', 'major or minor impact', 'all classifications'),
    ('P1-3', 'January 1, 2023', 'September 8, 2022'),
    ('P3-HEADER', 'Proposed ', ''),
    ('P3-A10', 'plan prepared', 'plan be prepared'),
    ('P3-A12', '0-5 feet minimum', '5 feet'),
    ('P4-CONTINUATION', 'bare earth or ', ''),
    ('P4-A14', 'plan prepared', 'plan be prepared'),
])
def test_resealed_source_changes_rejected(baseline: dict[str, bytes], identity: str,
                                          before: str, after: str) -> None:
    """Even resealed local transcripts cannot silently repair checked source anomalies."""
    def mutate(qa: dict[str, Any]) -> None:
        """Change a checked literal without touching original source evidence."""
        p = passage(qa, identity)
        p['text'] = p['text'].replace(before, after)
    with pytest.raises(ValueError):
        validate_content(rewrite(baseline, mutate))


def test_duplicate_heading_not_deduplicated(baseline: dict[str, bytes]) -> None:
    """A repeated source number is not an accidental duplicate to remove."""
    def mutate(qa: dict[str, Any]) -> None:
        """Remove the second 502.2 instruction."""
        qa['checked_passages'] = [x for x in qa['checked_passages'] if x['id'] != 'P3-A10']
    with pytest.raises(ValueError, match='Passage count'):
        validate_content(rewrite(baseline, mutate))


def test_cross_page_link_required(baseline: dict[str, bytes]) -> None:
    """Page 4 materials stay attached to page 3 hardened-zone provision."""
    def mutate(qa: dict[str, Any]) -> None:
        """Detach the continuation while retaining every word."""
        passage(qa, 'P4-CONTINUATION')['continuation_of'] = None
    with pytest.raises(ValueError, match='continuation'):
        validate_content(rewrite(baseline, mutate))


def test_section403_targets_complete(baseline: dict[str, bytes]) -> None:
    """Enumerated deletion target associations cannot drop one subsection."""
    def mutate(qa: dict[str, Any]) -> None:
        """Drop only 403.2.6 from structured associations."""
        qa['amendment_instructions'][3]['targets_within_literal'].remove('403.2.6')
    with pytest.raises(ValueError, match='enumeration'):
        validate_content(rewrite(baseline, mutate))


def test_instruction_wrong_page_rejected(baseline: dict[str, bytes]) -> None:
    """Table and section instructions must point to their own literal text."""
    def mutate(qa: dict[str, Any]) -> None:
        """Attach water-source instruction to fire-department passage."""
        qa['amendment_instructions'][4]['passage_ids'] = ['P3-A06']
    with pytest.raises(ValueError, match='association'):
        validate_content(rewrite(baseline, mutate))


def test_handwriting_cannot_be_printed(baseline: dict[str, bytes]) -> None:
    """Handwritten execution insertions retain their qualified classification."""
    def mutate(qa: dict[str, Any]) -> None:
        """Misclassify the introduction line."""
        passage(qa, 'P1-EXECUTION')['kind'] = 'printed_text'
    with pytest.raises(ValueError, match='Handwritten'):
        validate_content(rewrite(baseline, mutate))


def test_current_law_rejected(baseline: dict[str, bytes]) -> None:
    """Source-fidelity review cannot be promoted by a status-field edit."""
    qa = json.loads(baseline['SOURCE_QA.json'])
    qa['answer_safe'] = True
    with pytest.raises(ValueError):
        Review.model_validate_json(json.dumps(qa))


def test_candidate_changes_rejected(baseline: dict[str, bytes]) -> None:
    """The uncorrected machine candidate remains byte-exact."""
    altered = baseline.copy()
    altered['inputs/candidate.txt'] = altered['inputs/candidate.txt'].replace(b'leth', b'6th')
    with pytest.raises(ValueError, match='Asset mismatch'):
        validate_content(altered)


def test_native_offsets_not_invented(baseline: dict[str, bytes]) -> None:
    """Zero-byte native extraction never gains an OCR span under its name."""
    def mutate(qa: dict[str, Any]) -> None:
        """Invent one nominal native span."""
        qa['pages'][0]['native_spans'] = [dict(start=0, end=0,
            sha256=hashlib.sha256(b'').hexdigest())]
    with pytest.raises(ValueError, match='Native text'):
        validate_content(rewrite(baseline, mutate))


def test_wrong_receipt_time_rejected(baseline: dict[str, bytes]) -> None:
    """Supplier acquisition time cannot replace actual repository received_at."""
    def mutate(qa: dict[str, Any]) -> None:
        """Move reported acquisition time into the canonical custody field."""
        qa['provenance']['repository_received_at'] = qa['provenance']['supplied_started_at']
    with pytest.raises(ValueError, match='Repository intake'):
        validate_content(rewrite(baseline, mutate))


def test_image_corruption_rejected(baseline: dict[str, bytes]) -> None:
    """A changed PNG cannot keep its source-review identity."""
    altered = baseline.copy()
    altered['pages/page-0003.png'] += b'changed'
    with pytest.raises(ValueError, match='Asset mismatch'):
        validate_content(altered)


def test_ocr_offset_rejected(baseline: dict[str, bytes]) -> None:
    """Every original OCR observation stays at its unchanged byte location."""
    def mutate(qa: dict[str, Any]) -> None:
        """Shift one observation by one byte."""
        qa['pages'][2]['ocr_observation_spans'][0]['start'] = 1
    with pytest.raises(ValueError, match='OCR gap'):
        validate_content(rewrite(baseline, mutate))


def test_symbolic_link_rejected(tmp_path: Path) -> None:
    """Local provenance cannot follow an arbitrary file link."""
    root = tmp_path / 'review'
    root.mkdir()
    (root / 'linked').symlink_to(ROOT / 'inputs/original.pdf')
    with pytest.raises(ValueError, match='Symlink'):
        capture(root)


def test_captured_bytes_survive_late_disk_mutation(tmp_path: Path) -> None:
    """A consumed buffer does not silently reread later replacement bytes."""
    root = tmp_path / 'review'
    root.mkdir()
    path = root / 'example.txt'
    path.write_bytes(b'original')
    files = capture(root)
    path.write_bytes(b'late injection')
    from verify_review import get
    ref = Asset(path='example.txt', sha256=hashlib.sha256(b'original').hexdigest(), size_bytes=8)
    assert get(files, ref) == b'original'
