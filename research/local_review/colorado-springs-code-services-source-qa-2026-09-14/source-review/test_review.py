"""Source-derived association expectations and independent corruption cases."""
import copy
import json
import pytest
from pydantic import ValidationError
from review_models import QA
from verify_review import ROOT, captured_inputs, validate_content, verify, verify_crops


@pytest.fixture(scope='module')
def evidence() -> tuple[QA, dict[str, bytes]]:
    """Capture this review once for in-memory negative cases."""
    qa=QA.model_validate_json((ROOT/'SOURCE_QA.json').read_bytes())
    return qa,captured_inputs(qa)


def test_full_verification() -> None:
    """All source bytes, geometry, white text and exact pixel crops replay."""
    assert verify(False)['fee_associations']==197


@pytest.mark.parametrize('identity,amounts',[
    ('R2-025',['$296']),('R2-026',['$506']),('R2-029',['$1,050']),
    ('R3-006',['$1,928']),('R3-025',['1.5 x original plan review fee']),
    ('R4-018',['$774']),('R5-001',['$164','$494']),('R5-017',['$246','$370']),
    ('R5-033',['n/a','$1,936']),('R5-044',['no charge','no charge']),
    ('R5-049',['$14','$14']),('R5-051',['n/a','n/a']),
    ('R6-011',['n/c']),('R6-019',['$264']),('R6-020',['$132']),
    ('R6-033',['$272']),('R6-034',['$60']),('R6-035',['$304']),('R6-036',['$93']),
])
def test_visible_fee_values(evidence: tuple[QA,dict[str,bytes]],identity: str,
                            amounts: list[str]) -> None:
    """Keep source-visible values and their distinct columns literal."""
    qa,_=evidence
    by={line.id:line for line in qa.lines}
    row=next(row for row in qa.rows if row.id==identity)
    assert [' '.join(by[i].text.strip() for i in c) for c in row.fee_refs]==amounts


def test_nested_and_definition_associations(evidence: tuple[QA,dict[str,bytes]]) -> None:
    """Retain parent labels, page-7 displaced body and nonnumeric conditions."""
    qa,_=evidence
    rows={r.id:r for r in qa.rows}; paragraphs={p.id:p for p in qa.paragraphs}
    by={line.id:line.text for line in qa.lines}
    assert 'P2-L053' in rows['R2-026'].group_refs
    assert 'P5-L133' in rows['R5-035'].group_refs
    assert 'P5-L139' in rows['R5-037'].group_refs
    assert 'P6-L077' in rows['R6-033'].group_refs
    assert paragraphs['D10'].body_refs[0]=='P7-L030'
    assert paragraphs['D6'].body_refs[0]=='P7-L038'
    assert 'C5-207' in rows['R5-044'].context_refs
    assert 'C5-208' in rows['R5-038'].context_refs
    assert 'C3-83' in rows['R3-029'].context_refs
    assert 'No charge if closed within' in ''.join(by[i] for i in rows['R4-CLOSEOUT'].label_refs)


@pytest.mark.parametrize('change',[
    'drop_row','swap_columns','same_amount_wrong_row','drop_parent','drop_exception',
    'wrong_definition','native_change','white_visible','offset_change','crop_change',
    'currentness','adoption',
])
def test_reject_corruption(evidence: tuple[QA,dict[str,bytes]],change: str) -> None:
    """Reject substantive source association, scope and byte corruption."""
    qa,buffers=evidence
    data=copy.deepcopy(qa.model_dump())
    if change=='drop_row':data['rows'].pop()
    elif change=='swap_columns':data['rows'][107]['fee_refs'].reverse()
    elif change=='same_amount_wrong_row':data['rows'][0]['fee_refs']=[['P2-L007']]
    elif change=='drop_parent':data['rows'][25]['group_refs']=[]
    elif change=='drop_exception':data['rows'][-1]['label_refs']=['P4-L091']
    elif change=='wrong_definition':data['paragraphs'][-1]['body_refs']=['P7-L038']
    elif change=='native_change':data['lines'][0]['text']='999\n'
    elif change=='white_visible':data['lines'][0]['visibility']='visible'
    elif change=='offset_change':data['lines'][0]['start']=1
    elif change=='crop_change':data['crops'][0]['pixel_box'][0]+=1
    elif change=='currentness':data['legal_currentness']='verified'
    elif change=='adoption':data['adoption_date']='2015-01-01'
    with pytest.raises((AssertionError,ValidationError)):
        altered=QA.model_validate(data)
        validate_content(altered,buffers)
        verify_crops(altered,buffers)
