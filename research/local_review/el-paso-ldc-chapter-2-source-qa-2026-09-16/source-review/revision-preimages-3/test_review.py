"""Meaningful in-memory integrity failures; no historical source or packet changes."""
import json
from pathlib import Path
from typing import Callable

import pytest
from pydantic import ValidationError

from review_models import Review
from verify_review import ROOT, load, verify_content


@pytest.fixture(scope='module')
def evidence() -> tuple[Review, dict[str, bytes]]:
    """Capture the proposal once, excluding no substantive source bytes."""
    data=load(ROOT,sealed=False)
    return Review.model_validate_json(data['SOURCE_QA.json']),data


def altered(review: Review, ident: str, change: Callable) -> Review:
    """Return a mutable deep copy for one controlled malformed passage."""
    result=review.model_copy(deep=True)
    change(next(p for p in result.checked_passages if p.id==ident))
    return result


def test_complete_source(evidence: tuple) -> None:
    """All seven pages and every native byte validate."""
    result=verify_content(*evidence)
    assert result=={'pages':7,'passages':119,'native_lines':302,'native_bytes':16366,
                   'candidate_bytes':16520,'cross_page_links':5,'crops':7}


def test_exception_not_cannot_be_removed(evidence: tuple) -> None:
    """Losing a prohibition is rejected instead of becoming reviewed text."""
    review,data=evidence
    changed=altered(review,'2.2.3B-intro',lambda p:setattr(p,'text',p.text.replace('may not','may')))
    with pytest.raises(ValueError,match='wording silently changed'):
        verify_content(changed,data)


def test_source_double_period_not_repaired(evidence: tuple) -> None:
    """A grammatical cleanup cannot masquerade as source fidelity."""
    review,data=evidence
    changed=altered(review,'2.2.3A-text',lambda p:setattr(p,'text',p.text.replace('public..','public.')))
    with pytest.raises(ValueError,match='wording silently changed'):
        verify_content(changed,data)


def test_cross_page_parent_cannot_change(evidence: tuple) -> None:
    """The page-six body must remain attached to its page-five heading."""
    review,data=evidence
    changed=altered(review,'2.2.3B.3-text',lambda p:setattr(p,'parent_id','2.2.4'))
    with pytest.raises(ValueError,match='parent association'):
        verify_content(changed,data)


def test_cross_page_link_cannot_be_dropped(evidence: tuple) -> None:
    """A page break does not terminate a heading or paragraph association."""
    review,data=evidence;changed=review.model_copy(deep=True)
    changed.structural_links.pop()
    with pytest.raises(ValueError,match='Cross-page continuation'):
        verify_content(changed,data)


def test_footer_native_order_not_visual_order(evidence: tuple) -> None:
    """A caller cannot represent the native prefix as the checked visual order."""
    review,data=evidence;changed=review.model_copy(deep=True)
    changed.pages[0].visual_order=changed.pages[0].checked_passage_ids[:]
    with pytest.raises(ValueError,match='Visual footer/body order'):
        verify_content(changed,data)


def test_native_line_cannot_be_omitted(evidence: tuple) -> None:
    """Omitted native evidence is caught even when text fields remain unchanged."""
    review,data=evidence;changed=review.model_copy(deep=True)
    changed.pages[1].native_lines.pop()
    with pytest.raises(ValueError,match='Native line coverage'):
        verify_content(changed,data)


@pytest.mark.parametrize('path',['inputs/original.pdf','native/page-0004.txt','pages/page-0007.png'])
def test_changed_input_refused(evidence: tuple, path: str) -> None:
    """PDF, native and render inputs must match the pinned original packet."""
    review,data=evidence;changed=dict(data);changed[path]=changed[path]+b'x'
    with pytest.raises(ValueError,match='differs'):
        verify_content(review,changed)


def test_date_role_not_promoted(evidence: tuple) -> None:
    """A printed date cannot become a verified operative date."""
    review,_=evidence;raw=review.model_dump(mode='json')
    raw['dates'][0]['operative_date_certified']=True
    with pytest.raises(ValidationError):
        Review.model_validate_json(json.dumps(raw))
    raw=review.model_dump(mode='json');raw['answer_safe']=True
    with pytest.raises(ValidationError):
        Review.model_validate_json(json.dumps(raw))


def test_url_claim_cannot_be_silently_unified(evidence: tuple) -> None:
    """The received requested/final URL difference survives the review."""
    review,data=evidence;changed=review.model_copy(deep=True)
    changed.provenance.supplied_final_url=changed.provenance.supplied_url
    with pytest.raises(ValueError,match='URL/referral'):
        verify_content(changed,data)


def test_unknown_payload_rejected_after_seal(tmp_path: Path, evidence: tuple) -> None:
    """Closed inventory refuses an extra file even if all listed assets are exact."""
    from datetime import datetime,timezone
    from hashlib import sha256
    from review_models import Manifest
    _,data=evidence
    # Tiny fixture exercises closure independently of large images and content checks.
    fixture={'one.txt':b'one','FINAL_MANIFEST.schema.json':json.dumps(Manifest.model_json_schema()).encode()}
    for name,raw in fixture.items(): (tmp_path/name).write_bytes(raw)
    model=Manifest.model_validate_json(json.dumps({'schema_version':1,
        'status':'frozen_source_fidelity_review_not_current_law',
        'created_at':datetime.now(timezone.utc).isoformat(),'files':[
            {'path':name,'sha256':sha256(raw).hexdigest(),'size_bytes':len(raw)} for name,raw in fixture.items()]}))
    (tmp_path/'FINAL_MANIFEST.json').write_text(model.model_dump_json())
    assert set(load(tmp_path))==set(fixture)|{'FINAL_MANIFEST.json'}
    (tmp_path/'unexpected.txt').write_text('unbound')
    with pytest.raises(ValueError,match='Closed inventory'):
        load(tmp_path)


def test_printed_heading_period_preserved(evidence: tuple) -> None:
    """The canonical ID omits punctuation while the printed label retains it."""
    review,data=evidence
    changed=altered(review,'2.2.3',lambda p:setattr(p,'label_as_printed','2.2.3'))
    with pytest.raises(ValueError,match='numbering/parent association'):
        verify_content(changed,data)
