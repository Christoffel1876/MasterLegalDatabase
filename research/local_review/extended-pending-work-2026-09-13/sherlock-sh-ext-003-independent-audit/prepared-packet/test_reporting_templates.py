"""Offline synthetic checks of the reporting budgets; no public actions or source acquisition."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models import ActionLog, Reservation, Result


def reservation(number: int, authority: str | None = None) -> Reservation:
    """Create a clearly synthetic reservation for counter validation only."""
    return Reservation(action_id=f"SHEXT003-A{number:03}",
        authority_id=authority or ("CO-COUNTY-CHAFFEE" if number % 2 else "CO-COUNTY-GUNNISON"),
        reserved_at=datetime(2026, 9, 13, 2, tzinfo=timezone.utc), tool_name="synthetic_test",
        action_kind="open", requested_url=f"https://example.invalid/{number}",
        basis="Offline fixture; never opened", budget_checked=True)


def result(number: int) -> Result:
    """Pair a synthetic result with a reservation without claiming source bytes."""
    return Result(action_id=f"SHEXT003-A{number:03}", finished_at=None,
        time_unknown_reason="Synthetic test only", observed_final_url=None,
        visible_redirect_urls=[], outcome="tool_preflight_error", body_role="no_body",
        retained_assets=[], pdf_magic_checked=False, pdf_parse_succeeded=False,
        physical_pages=None, notes="No public request occurred",
        body_size_basis="no_body_observed", observed_body_bytes=0)


def test_valid_recorded_budget() -> None:
    """One pending action and a completed prior action are allowed."""
    log = ActionLog(reservations=[reservation(1), reservation(2)], results=[result(1)])
    assert not log.hidden_network_requests_measured


@pytest.mark.parametrize("case", ["total", "authority", "distinct", "duplicate", "unreserved",
                                  "multiple_pending"])
def test_counter_refusals(case: str) -> None:
    """Reject over-cap, duplicate and unreserved reporting states."""
    if case == "total":
        values = [reservation(i) for i in range(1, 42)]
    elif case == "authority":
        values = [reservation(i, "CO-COUNTY-CHAFFEE") for i in range(1, 22)]
    elif case == "distinct":
        values = [reservation(i) for i in range(1, 32)]
    elif case == "duplicate":
        values = [reservation(1), reservation(1)]
    else:
        values = [reservation(1), reservation(2)]
    results = [result(i) for i in range(1, len(values) + 1)]
    if case == "unreserved":
        results = [result(3)]
    elif case == "multiple_pending":
        results = []
    with pytest.raises(ValueError):
        ActionLog(reservations=values, results=results)


def test_parser_claim_requires_actual_pdf_evidence() -> None:
    """A PDF-suffixed name or successful-looking tool note cannot fabricate an original."""
    data = result(1).model_dump(mode="json")
    data.update(pdf_parse_succeeded=True, physical_pages=1)
    with pytest.raises(ValueError):
        Result.model_validate_json(__import__("json").dumps(data))


@pytest.mark.parametrize('updates',[
 {'action_kind':'search','requested_url':'https://example.invalid','search_query':'one'},
 {'action_kind':'search','requested_url':None,'search_query':None},
 {'requested_url':None}, {'requested_url':'http://example.invalid'}])
def test_invalid_reservation_target(updates):
    data=reservation(1).model_dump(mode='json');data.update(updates)
    with pytest.raises(ValueError):
        Reservation.model_validate_json(__import__('json').dumps(data))


@pytest.mark.parametrize('updates',[
 {'time_unknown_reason':None}, {'body_sha256':'a'*64},
 {'body_size_basis':'no_body_observed','observed_body_bytes':1},
 {'body_size_basis':'retained_partial','observed_body_bytes':1},
 {'body_size_basis':'unknown','observed_body_bytes':1}])
def test_invalid_result_measurement(updates):
    data=result(1).model_dump(mode='json');data.update(updates)
    with pytest.raises(ValueError):
        Result.model_validate_json(__import__('json').dumps(data))


def test_valid_search_and_complete_body():
    import json
    data=reservation(1).model_dump(mode='json')
    data.update(action_kind='search',requested_url=None,search_query='county fee official')
    assert Reservation.model_validate_json(json.dumps(data)).search_query
    data=result(1).model_dump(mode='json')
    data.update(body_size_basis='retained_complete', observed_body_bytes=10,
                body_sha256='a'*64, retained_assets=[
                    {'path':'body', 'sha256':'a'*64, 'size_bytes':10}])
    assert Result.model_validate_json(json.dumps(data)).observed_body_bytes==10


def test_checklist_and_inventory_duplicates():
    import json
    from pathlib import Path
    from models import Checklist,ArtifactInventory
    data=json.loads((Path(__file__).parent/'templates/CHECKLIST.json').read_bytes())
    assert len(Checklist.model_validate_json(json.dumps(data)).rows)==24
    data['rows'][1]=data['rows'][0]
    with pytest.raises(ValueError,match='combinations'):
        Checklist.model_validate_json(json.dumps(data))
    data={'assignment_id':'SH-EXT-003','files':[{'path':'x','sha256':'a'*64,'size_bytes':1}]*2,
          'status':'partial_pending_atlas_verification','legal_currentness':'not_verified'}
    with pytest.raises(ValueError,match='Duplicate'):
        ArtifactInventory.model_validate_json(json.dumps(data))


def test_priority_caps_and_duplicates():
    import json
    from models import Priorities
    row={'candidate_id':'SHEXT003-01','authority_id':'CO-COUNTY-CHAFFEE',
         'title_as_observed':'Synthetic','requested_url':'https://example.invalid',
         'observed_final_url':None,'role':'unknown','ownership_evidence':'Synthetic',
         'official_referral_evidence':'Synthetic','action_ids':[],'categories':['fees'],
         'original_body':None,'physical_pages':None,'date_claims':[],
         'legacy_comparison':'Synthetic','remaining_gaps':['Not a source claim']}
    assert len(Priorities.model_validate_json(json.dumps({'priorities':[row]})).priorities)==1
    with pytest.raises(ValueError,match='Duplicate'):
        Priorities.model_validate_json(json.dumps({'priorities':[row,row]}))
    rows=[dict(row,candidate_id=f'SHEXT003-{i:02}') for i in range(1,10)]
    with pytest.raises(ValueError,match='Authority priority'):
        Priorities.model_validate_json(json.dumps({'priorities':rows}))
