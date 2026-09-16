"""Bounded, offline regressions for source and derived evidence bindings."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from review_models import Review
from verify_review import validate_content

ROOT = Path(__file__).resolve().parent


def review() -> Review:
    """Load a fresh typed review without changing files."""
    return Review.model_validate_json((ROOT / 'SOURCE_QA.json').read_bytes())


def test_actual_content() -> None:
    """All retained source and transcript bindings replay."""
    validate_content(ROOT, review())


@pytest.mark.parametrize('case', range(8))
def test_reject_changed_evidence(case: int) -> None:
    """Eight distinct evidence substitutions cannot pass structural verification."""
    item = review()
    if case == 0:
        item.source.sha256 = '0' * 64
    elif case == 1:
        item.pages[0].native.size_bytes = 1
    elif case == 2:
        item.pages[2].ocr_observation_spans[0].end += 1
    elif case == 3:
        item.blocks[0].transcript_span.start += 1
    elif case == 4:
        item.fees[0].amount_literal = '0.7%'
    elif case == 5:
        item.fees[2].block_id = 'P3-MECH'
    elif case == 6:
        item.fees[0].conditions_block_ids.remove('P1-CONDITION')
    else:
        item.dates[-1].literal = '6/19/2025 10:46:06 AM'
    with pytest.raises((AssertionError, ValueError)):
        validate_content(ROOT, item)


def test_reject_currentness_promotion() -> None:
    """Reviewed source text cannot be relabeled current or answer-safe."""
    data = json.loads((ROOT / 'SOURCE_QA.json').read_bytes())
    data['legal_currentness'] = 'current'
    data['answer_safe'] = True
    with pytest.raises(ValidationError):
        Review.model_validate_json(json.dumps(data))
