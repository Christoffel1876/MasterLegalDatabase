"""Resealed forensic counterexamples: replay must enforce the same limits as reservation."""
from datetime import timedelta
import json
from pathlib import Path
from typing import Any

import pytest
from geode.pipeline import manual_source_watch_batches as w
from tests.test_manual_source_watch_batches import NOW, Response, packet


def put(path: Path, data: Any) -> None:
    """Write deliberately altered test metadata, never a production source or saved run."""
    path.write_text(json.dumps(data, indent=2) + '\n')


def ref(root: Path, path: Path) -> dict:
    """Rehash altered test evidence to exercise semantics rather than the outer hash gate."""
    return w.g.file_ref(root, path).model_dump(mode='json')


def run_redirect(root: Path, request_seconds: int = 30,
                 run_seconds: int = 300) -> tuple[Path, Path, w.Plan]:
    """Create one valid same-host redirected response plus the second selected source."""
    path = root / w.SELECTION
    data = json.loads(path.read_bytes())
    data['limits']['request_seconds'] = request_seconds
    data['max_run_seconds'] = run_seconds
    plan = w.Plan.model_validate_json(json.dumps(data))
    put(path, plan.model_dump(mode='json'))
    output = root / w.RUNTIME / 'replay-policy'
    location = plan.targets[0].url + '?observed-fixture-redirect=1'
    responses = [Response(b'', 302, {'location': location}),
                 Response((root / plan.targets[0].baseline.path).read_bytes()),
                 Response((root / plan.targets[1].baseline.path).read_bytes())]
    report = w.run_watch(path, output, NOW, w.g.sha(path), clock=lambda: NOW,
                         fetch=lambda *args: responses.pop(0))
    assert report.status == 'completed' and report.state.request_count == 3
    assert w.verify_run(path, output) == report
    return path, output, plan


def unchecked_test_pairs(output: Path) -> list:
    """Reconstruct deliberately forged fixture data without the real ledger's policy gates."""
    pairs = []
    for path in sorted(output.glob('events/*/reservation.json')):
        pairs.append((w.g.Reservation.model_validate_json(path.read_bytes()),
                      w.g.Result.model_validate_json((path.parent / 'result.json').read_bytes())))
    return pairs


def reseal_fixture(path: Path, output: Path, end_seconds: int = 0) -> None:
    """Make a self-consistent forged report so only the missing policy rule detects it."""
    guard = w.WatchGuard(path, output, fetch=lambda *args: pytest.fail('No network'))
    pairs = unchecked_test_pairs(output)
    record = json.loads((output / 'report.json').read_bytes())
    record['observations'] = [w.observation(t, pairs, output).model_dump(mode='json')
                              for t in guard.plan.targets]
    record['state'] = guard.state(pairs).model_dump(mode='json')
    record['generated_at'] = (NOW + timedelta(seconds=end_seconds)).isoformat()
    put(output / 'report.json', record)
    (output / 'RUN_MANIFEST.json').unlink()
    w.seal(output, 'run')


def test_resealed_allowed_other_host_is_not_original_source(packet: Path) -> None:
    """An approved Weld host must not masquerade as the redirected Arapahoe source."""
    path, output, plan = run_redirect(packet)
    first, second = output / 'events/0001', output / 'events/0002'
    foreign = plan.targets[1].url + '?forged-cross-authority=1'
    headers = json.loads((first / 'public-headers.json').read_bytes())
    headers['headers']['location'] = foreign
    put(first / 'public-headers.json', headers)
    result = json.loads((first / 'result.json').read_bytes())
    result.update(redirect_url=foreign, public_headers=ref(output, first / 'public-headers.json'))
    put(first / 'result.json', result)
    reservation = json.loads((second / 'reservation.json').read_bytes())
    reservation['url'] = foreign
    put(second / 'reservation.json', reservation)
    headers = json.loads((second / 'public-headers.json').read_bytes())
    headers['request_url'] = foreign
    put(second / 'public-headers.json', headers)
    result = json.loads((second / 'result.json').read_bytes())
    result.update(reservation_sha256=w.g.sha(second / 'reservation.json'),
                  public_headers=ref(output, second / 'public-headers.json'))
    put(second / 'result.json', result)
    reseal_fixture(path, output)
    with pytest.raises(ValueError, match='original source hostname'):
        w.verify_run(path, output)


@pytest.mark.parametrize('forged_seconds', [200, 29])
def test_resealed_request_deadline_must_match_reserved_budget(
        packet: Path, forged_seconds: int) -> None:
    """A longer 200-second or altered shorter deadline is not the declared 30-second policy."""
    path, output, _ = run_redirect(packet)
    second = output / 'events/0002'
    reservation = json.loads((second / 'reservation.json').read_bytes())
    reservation['deadline'] = (NOW + timedelta(seconds=forged_seconds)).isoformat()
    put(second / 'reservation.json', reservation)
    result = json.loads((second / 'result.json').read_bytes())
    result['reservation_sha256'] = w.g.sha(second / 'reservation.json')
    # In the late case all later event/report times agree, and +70 remains within the run.
    end = 70 if forged_seconds == 200 else 0
    result['finished_at'] = (NOW + timedelta(seconds=end)).isoformat()
    put(second / 'result.json', result)
    if end:
        third = output / 'events/0003'
        reservation = json.loads((third / 'reservation.json').read_bytes())
        reservation['reserved_at'] = (NOW + timedelta(seconds=end)).isoformat()
        reservation['deadline'] = (NOW + timedelta(seconds=end + 30)).isoformat()
        put(third / 'reservation.json', reservation)
        result = json.loads((third / 'result.json').read_bytes())
        result['reservation_sha256'] = w.g.sha(third / 'reservation.json')
        result['finished_at'] = (NOW + timedelta(seconds=end)).isoformat()
        put(third / 'result.json', result)
    reseal_fixture(path, output, end)
    with pytest.raises(ValueError, match='selected request limit'):
        w.verify_run(path, output)


@pytest.mark.parametrize('request_seconds,run_seconds', [(5, 300), (30, 3)])
def test_narrowed_limits_and_valid_same_host_redirect_still_replay(
        packet: Path, request_seconds: int, run_seconds: int) -> None:
    """The gate admits actual reservations capped by either request or total run time."""
    path, output, _ = run_redirect(packet, request_seconds, run_seconds)
    for reservation, _ in w.WatchGuard(path, output).ledger():
        assert reservation.deadline == NOW + timedelta(seconds=min(request_seconds, run_seconds))
    assert w.verify_run(path, output).status == 'completed'


def test_ledger_respects_narrowed_redirect_policy(packet: Path) -> None:
    """The replay ledger enforces a stricter selected hop bound, not just its schema ceiling."""
    path, output, plan = run_redirect(packet)
    guard = w.WatchGuard(path, output)
    guard.plan = plan.model_copy(update={'limits': plan.limits.model_copy(
        update={'redirects_per_source': 0})})
    with pytest.raises(ValueError, match='selected redirect limit'):
        guard.ledger()
