"""Offline reproduction of a deadline crossed while finalizing a complete event."""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import sys
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

BASE = Path('/Users/mcoors/Documents/Project Geode')
ROOT = BASE / 'MasterLegalDatabase'
HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('watch_review_fixtures',
                                             ROOT / 'tests/test_manual_source_watch.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
from geode.pipeline import manual_source_watch as w


class Clock:
    """Advance only at the explicitly simulated finalization I/O boundary."""
    def __init__(self) -> None:
        self.value = fixtures.NOW
        self.crossed = False

    def __call__(self):
        return self.value


root = fixtures.packet.__wrapped__(HERE / 'fixture')
clock = Clock()
calls = []
body = fixtures.bodies(root)


class FirstResponse(fixtures.Response):
    """The full first body finishes one millisecond before its request deadline."""
    def close(self) -> None:
        super().close()
        clock.value = fixtures.NOW + timedelta(seconds=29.999)


responses = [FirstResponse(body[0]), fixtures.Response(body[1])]
original_sha = w.g.sha


def delayed_sha(path: Path) -> str:
    """Simulate two milliseconds of ordinary reservation hashing/finalization I/O."""
    value = original_sha(path)
    caller = inspect.currentframe().f_back.f_code.co_name
    if path.name == 'reservation.json' and caller == 'finish' and not clock.crossed:
        clock.value += timedelta(milliseconds=2)
        clock.crossed = True
    return value


def fetch(url, deadline, now):
    """Return only local fixture bodies; no public socket can be opened."""
    calls.append(url)
    return responses.pop(0)


output = root / w.RUNTIME / 'finalization-boundary'
error = None
with patch.object(w.g, 'sha', delayed_sha):
    try:
        w.run_watch(root / w.SELECTION, output, fixtures.NOW,
                    original_sha(root / w.SELECTION), clock=clock, fetch=fetch)
    except ValueError as exc:
        error = str(exc)
report = json.loads((output / 'report.json').read_bytes())
event = json.loads((output / 'events/0001/result.json').read_bytes())
reservation = json.loads((output / 'events/0001/reservation.json').read_bytes())
assert error == 'Complete response exceeds declared request deadline', error
assert event['outcome'] == 'complete' and report['observations'][0]['status'] == 'transport_error'
assert report['observations'][0]['bytes_equal_to_baseline'] is None
assert not (output / 'RUN_MANIFEST.json').exists()
before = len(calls)
try:
    w.run_watch(root / w.SELECTION, output, fixtures.NOW,
                original_sha(root / w.SELECTION), clock=clock, fetch=fetch)
except ValueError as exc:
    replay_error = str(exc)
else:
    replay_error = None
assert len(calls) == before and replay_error == error
result = {
    'case': 'deadline_crossed_during_finish_reservation_hash',
    'production_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(w.__file__), Path(w.g.__file__)]},
    'fixture_public_requests': 0, 'injected_response_count': len(calls),
    'request_deadline': reservation['deadline'], 'event_finished_at': event['finished_at'],
    'event_outcome': event['outcome'], 'report_status': report['status'],
    'first_observation_status': report['observations'][0]['status'],
    'first_observation_equality': report['observations'][0]['bytes_equal_to_baseline'],
    'final_seal_present': False, 'initial_exception': error, 'replay_exception': replay_error,
    'classification': 'safe refusal, but ordinary timing boundary leaves unverifiable final report',
    'scope': 'offline injected clock and response; no production edits or public requests',
}
(HERE / 'REPRODUCTION.json').write_text(json.dumps(result, indent=2) + '\n')
sys.stdout.write(json.dumps(result, indent=2) + '\n')
