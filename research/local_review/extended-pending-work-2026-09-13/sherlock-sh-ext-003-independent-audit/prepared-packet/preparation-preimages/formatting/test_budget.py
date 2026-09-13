"""Local-only finite accounting tests; no HTTP transport is imported or invoked."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib

import pytest
from pydantic import ValidationError

from budget import CUTOFF, complete, counters, load_log, reserve, save_new
from models import ActionLog, Asset, Result
from test_reporting_templates import reservation, result

NOW = datetime(2026, 9, 13, 2, tzinfo=timezone.utc)


def test_reserve_complete_and_serial_resume(tmp_path: Path) -> None:
    """An interrupted reservation blocks a second action until its observed result is saved."""
    first = reserve(tmp_path, reservation(1), NOW)
    assert first.pending_action == 'SHEXT003-A001'
    with pytest.raises(ValueError, match='unfinished|no immutable'):
        reserve(tmp_path, reservation(2), NOW)
    assert complete(tmp_path, result(1), NOW).can_reserve
    assert reserve(tmp_path, reservation(2), NOW).reserved_actions == 2
    assert load_log(tmp_path).reservations[0] == reservation(1)


def test_denied_endpoint_refused_before_reservation(tmp_path: Path) -> None:
    """Changing the tool does not authorize an exact denied endpoint retry."""
    reserve(tmp_path, reservation(1), NOW)
    denied = result(1).model_copy(update={'outcome':'access_denied'})
    complete(tmp_path, denied, NOW)
    retry = reservation(2).model_copy(update={'requested_url':reservation(1).requested_url})
    with pytest.raises(ValueError, match='Denied'):
        reserve(tmp_path, retry, NOW)
    assert len(load_log(tmp_path).reservations) == 1


@pytest.mark.parametrize('count', [0, 1])
def test_cutoff_refused(tmp_path: Path, count: int) -> None:
    """No new action at or after the fixed research cutoff, including an empty run."""
    if count:
        reserve(tmp_path, reservation(1), NOW)
        complete(tmp_path, result(1), NOW)
    value = reservation(count + 1).model_copy(update={'reserved_at':CUTOFF})
    with pytest.raises(ValueError, match='cutoff'):
        reserve(tmp_path, value, CUTOFF)


def test_duplicate_url_is_still_an_action() -> None:
    """Repeated retrievals cost separate actions while distinct URLs count once."""
    first, second = reservation(1), reservation(2)
    second = second.model_copy(update={'requested_url':first.requested_url})
    state = counters(ActionLog(reservations=[first,second],results=[result(1),result(2)]),NOW)
    assert state.reserved_actions == 2 and state.distinct_urls == 1


def test_automatic_visible_redirects_charged() -> None:
    """Known automatic hops cost actions and distinct URLs beyond their initial tool action."""
    observed = result(1).model_copy(update={'visible_redirect_urls':['https://example.invalid/hop']})
    state = counters(ActionLog(reservations=[reservation(1)],results=[observed]),NOW)
    assert state.charged_visible_actions == 2 and state.distinct_urls == 2
    over = observed.model_copy(update={'visible_redirect_urls':[
        f'https://example.invalid/hop/{i}' for i in range(20)]})
    with pytest.raises(ValueError, match='Authority'):
        ActionLog(reservations=[reservation(1)],results=[over])


def test_unknown_body_accounting_blocks_continuation(tmp_path: Path) -> None:
    """Unknown bytes remain unknown and stop further collection rather than being counted as zero."""
    reserve(tmp_path,reservation(1),NOW)
    unknown = result(1).model_copy(update={'body_size_basis':'unknown','observed_body_bytes':None})
    assert not complete(tmp_path,unknown,NOW).can_reserve
    with pytest.raises(ValueError, match='Unknown'):
        reserve(tmp_path,reservation(2),NOW)


def test_partial_body_hash_checked_and_retained(tmp_path: Path) -> None:
    """Preserve measured partial bytes and stop; a changed retained body is refused."""
    raw = b'partial response'
    (tmp_path/'body.bin').write_bytes(raw)
    asset = Asset(path='body.bin',sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
    value = result(1).model_copy(update={'retained_assets':[asset],'body_sha256':asset.sha256,
        'body_size_basis':'retained_partial','observed_body_bytes':len(raw)})
    reserve(tmp_path,reservation(1),NOW)
    (tmp_path/'body.bin').write_bytes(b'changed')
    with pytest.raises(ValueError, match='bytes differ'):
        complete(tmp_path,value,NOW)
    (tmp_path/'body.bin').write_bytes(raw)
    state=complete(tmp_path,value,NOW)
    assert state.retained_body_bytes==len(raw) and not state.can_reserve


def test_immutable_result_and_path_safety(tmp_path: Path) -> None:
    """Earlier records survive duplicate publication and symlinked local state is refused."""
    path=tmp_path/'record.json'
    save_new(path,result(1));before=path.read_bytes()
    with pytest.raises(FileExistsError):save_new(path,result(2))
    assert path.read_bytes()==before
    (tmp_path/'linked').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError,match='Symlink'):
        load_log(tmp_path/'linked')


@pytest.mark.parametrize('size,count',[(20_000_001,1),(20_000_000,5)])
def test_byte_budget_refuses_complete_log(size: int,count: int) -> None:
    """Both per-body and aggregate retained-body limits include every repeated response."""
    records=[]
    for i in range(1,count+1):
        asset=Asset(path=f'{i}.pdf',sha256='a'*64,size_bytes=size)
        records.append(result(i).model_copy(update={'retained_assets':[asset],
            'body_sha256':asset.sha256,'body_size_basis':'retained_complete',
            'observed_body_bytes':size}))
    with pytest.raises(ValueError,match='byte cap'):
        ActionLog(reservations=[reservation(i) for i in range(1,count+1)],results=records)


def test_only_serial_prefix_can_be_completed() -> None:
    """Closing action2 before action1 cannot launder an unfinished action."""
    with pytest.raises(ValueError,match='prefix'):
        ActionLog(reservations=[reservation(1),reservation(2)],results=[result(2)])


def test_cli_roundtrip(tmp_path,monkeypatch,capsys):
    import budget
    class Clock:
        @staticmethod
        def now(tz):return NOW
    monkeypatch.setattr(budget,'datetime',Clock)
    source=tmp_path/'input.json'
    for operation,value in [('reserve',reservation(1)),('complete',result(1))]:
        source.write_text(value.model_dump_json())
        monkeypatch.setattr('sys.argv',['budget',operation,'--delivery',str(tmp_path/'run'),
                                       '--input',str(source)])
        assert budget.main()==0
    monkeypatch.setattr('sys.argv',['budget','status','--delivery',str(tmp_path/'run')])
    assert budget.main()==0
    assert 'public_requests_by_helper' in capsys.readouterr().out


@pytest.mark.parametrize('operation',['reserve','complete'])
def test_cli_missing_input(tmp_path,monkeypatch,operation):
    import budget
    monkeypatch.setattr('sys.argv',['budget',operation,'--delivery',str(tmp_path)])
    with pytest.raises(ValueError,match='Provide'):budget.main()


def test_bad_serial_clock_result_and_path(tmp_path):
    with pytest.raises(ValueError,match='serial prefix'):reserve(tmp_path,reservation(2),NOW)
    with pytest.raises(ValueError,match='actual local'):
        reserve(tmp_path,reservation(1),NOW+timedelta(seconds=1))
    with pytest.raises(ValueError,match='single pending'):complete(tmp_path,result(1),NOW)
    reserve(tmp_path,reservation(1),NOW)
    with pytest.raises(ValueError,match='does not close'):complete(tmp_path,result(2),NOW)
    asset=Asset(path='../secret',sha256='a'*64,size_bytes=1)
    value=result(1).model_copy(update={'retained_assets':[asset]})
    with pytest.raises(ValueError,match='Unsafe'):complete(tmp_path,value,NOW)


def test_exact_exhausted_caps():
    reservations=[];results=[]
    for i in range(1,41):
        reservations.append(reservation(i).model_copy(
            update={'requested_url':'https://example.invalid/x'}))
        asset=Asset(path=f'{i}.pdf',sha256='a'*64,size_bytes=2_000_000)
        results.append(result(i).model_copy(update={'retained_assets':[asset],
            'body_sha256':asset.sha256,'body_size_basis':'retained_complete',
            'observed_body_bytes':2_000_000}))
    state=counters(ActionLog(reservations=reservations,results=results),NOW)
    assert not state.can_reserve and len(state.stop_reasons)==2
