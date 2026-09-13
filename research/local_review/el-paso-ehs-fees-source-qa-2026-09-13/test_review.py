"""Small offline corruption checks for the complete English EHS evidence package."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from review_models import CompleteReview, Ref
from validate_review import HERE, checked, validate_data


@pytest.fixture
def review() -> CompleteReview:
    """Load the unchanged complete review; tests mutate only in-memory copies."""
    return CompleteReview.model_validate_json((HERE / 'SOURCE_QA.json').read_bytes())


def test_actual_complete_source(review: CompleteReview) -> None:
    """All 65 rows, complete source grid and 102 exact spans replay from the original PDF."""
    validate_data(HERE, review)
    assert len(review.bindings) == 102 and len(review.contexts) == 37


@pytest.mark.parametrize('change', [
    'fee', 'group', 'carried_page', 'note', 'definition_link', 'routine_inference',
    'same_value_wrong_span', 'candidate_offset', 'merged_null', 'approval_claim', 'source_hash',
])
def test_corruptions_refused(review: CompleteReview, change: str) -> None:
    """Structural and semantic tampering must fail even if outer hashes were regenerated."""
    data: dict[str, Any] = copy.deepcopy(review.model_dump(mode='json'))
    if change == 'fee':
        data['rows'][0]['fee'] = '$166.00 per six months'
    elif change == 'group':
        data['rows'][28]['group'] = 'Retail Food Establishment (RFE)'
    elif change == 'carried_page':
        data['rows'][28]['group_physical_page'] = 3
    elif change == 'note':
        note = next(c for c in data['contexts'] if c['context_id'] == 'OTHER2')
        note['text'] = 'Fees will be assessed for complaint investigations.'
    elif change == 'definition_link':
        data['rows'][19]['linked_context'].remove('STAR')
    elif change == 'routine_inference':
        data['rows'][18]['linked_context'].append('CHILD1')
    elif change == 'same_value_wrong_span':
        # R010 and R013 both print $190.00; identical text cannot justify the wrong row location.
        data['bindings'][9]['spans'][1] = copy.deepcopy(data['bindings'][12]['spans'][1])
    elif change == 'candidate_offset':
        data['pages'][0]['candidate_start'] += 1
    elif change == 'merged_null':
        data['tables'][0]['rows'][0]['cells'][1] = ''
    elif change == 'approval_claim':
        data['source_approval_claim'] = 'October 25, 2024'
    else:
        data['source']['sha256'] = '0' * 64
    with pytest.raises(ValueError):
        validate_data(HERE, CompleteReview.model_validate_json(__import__('json').dumps(data)))


@pytest.mark.parametrize('path', ['../source/original.pdf', '/tmp/original.pdf'])
def test_escaping_refs_refused(path: str) -> None:
    """Evidence paths cannot leave the portable package."""
    with pytest.raises(ValueError, match='Unsafe'):
        checked(HERE, Ref(path=path, sha256='0' * 64, size_bytes=0))


def test_currentness_promotion_refused(review: CompleteReview) -> None:
    """The review schema cannot certify a source as current law."""
    data = review.model_dump(mode='json')
    data['legal_currentness'] = 'verified_current'
    with pytest.raises(ValueError):
        CompleteReview.model_validate_json(__import__('json').dumps(data))
