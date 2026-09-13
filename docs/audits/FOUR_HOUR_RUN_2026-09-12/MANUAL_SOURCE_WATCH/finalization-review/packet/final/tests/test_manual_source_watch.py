"""Offline fixtures for fixed-source byte watching; never make public requests."""
from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pymupdf
import pytest

from geode.pipeline import manual_source_watch as w

SOURCE = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 13, 0, 10, tzinfo=timezone.utc)


class Response:
    """Controlled finite body with HTTP fields and optional interrupted read."""
    def __init__(self, body: bytes, status: int = 200,
                 headers: dict[str, str] | None = None, fail: bool = False) -> None:
        """Configure one finite in-memory response without a network socket."""
        self.body, self.status, self.offset = body, status, 0
        self.headers = headers if headers is not None else {
            'content-type': 'application/pdf', 'content-length': str(len(body))}
        self.fail = fail
        self.closed = False

    def read(self, count: int, timeout: float) -> bytes:
        """Honor byte bounds; an injected interruption follows one short chunk."""
        if self.fail and self.offset:
            raise KeyboardInterrupt()
        limit = min(count, 64) if self.fail else count
        block = self.body[self.offset:self.offset + limit]
        self.offset += len(block)
        return block

    def close(self) -> None:
        """Record closure even when body reading fails."""
        self.closed = True


@pytest.fixture
def packet(tmp_path: Path) -> Path:
    """Copy exact canonical inputs and selected raw lines into a tiny temporary repository."""
    root = tmp_path / 'packet'
    selection = json.loads((SOURCE / w.SELECTION).read_bytes())
    copied: set[str] = set()

    def copy(relative: str) -> None:
        """Preserve immutable bytes without executing research scripts."""
        if relative in copied:
            return
        source = SOURCE / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.add(relative)

    copy(w.SELECTION.as_posix())
    for field in ['custody_scope', 'custody_schema', 'intake_acceptance', 'intake_receipt']:
        copy(selection[field]['path'])
    for target in selection['targets']:
        copy(target['baseline']['path'])
    scope_path = Path(selection['custody_scope']['path'])
    scope = json.loads((SOURCE / scope_path).read_bytes())
    for source in scope['sources']:
        for field in ['result', 'reservation', 'parent_html']:
            copy((scope_path.parent / source[field]['path']).as_posix())
    for ref in selection['prior_live'].values():
        copy(ref['path'])
    prior = Path(selection['prior_live']['run_manifest']['path'])
    for ref in json.loads((SOURCE / prior).read_bytes())['files']:
        copy((prior.parent / ref['path']).as_posix())
    selected = {t['canonical_source_id'] for t in selection['targets']}
    raw = []
    with (SOURCE / w.MANUAL_MANIFEST).open('rb') as handle:
        for line in handle:
            if json.loads(line)['record_id'] in selected:
                raw.append(line)
    output = root / w.MANUAL_MANIFEST
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b''.join(raw))
    return root


def bodies(root: Path) -> list[bytes]:
    """Use both actual frozen originals for equality fixtures."""
    targets = json.loads((root / w.SELECTION).read_bytes())['targets']
    return [(root / t['baseline']['path']).read_bytes() for t in targets]


def changed_pdf() -> bytes:
    """Generate a distinct valid PDF fixture without modifying source originals."""
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Offline changed source fixture')
        return pdf.tobytes()


def run(root: Path, items: list[Any], name: str = 'fixture',
        clock: Any = lambda: NOW) -> tuple[Any, list[str]]:
    """Inject every HTTP outcome and verify reservation-before-transport ordering."""
    calls: list[str] = []
    output = root / w.RUNTIME / name

    def fetch(url: str, deadline: datetime, now: Any) -> Any:
        """A local response sequence, never a real transport."""
        records = sorted(output.glob('events/*/reservation.json'))
        assert len(records) == len(calls) + 1
        calls.append(url)
        value = items.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value

    result = w.run_watch(root / w.SELECTION, output, NOW,
                         w.g.sha(root / w.SELECTION), clock=clock, fetch=fetch)
    return result, calls


def reseal(root: Path, kind: str = 'run') -> None:
    """Reseal only temporary tamper fixtures to exercise semantic checks."""
    name = 'RUN_MANIFEST.json'
    (root / name).unlink()
    w.seal(root, kind)


def change_plan(root: Path, update: Any) -> None:
    """Write a schema-validated temporary plan with deliberately narrowed bounds."""
    path = root / w.SELECTION
    data = json.loads(path.read_bytes())
    update(data)
    model = w.Plan.model_validate_json(json.dumps(data))
    path.write_text(model.model_dump_json())


def test_actual_baselines_and_portable_context(packet: Path) -> None:
    """Two exact complete PDFs retain their issuer, source dates and unknown currentness."""
    result, calls = run(packet, [Response(b) for b in bodies(packet)])
    assert len(calls) == 2 and result.status == 'completed'
    assert result.mode == 'offline_fixture' and result.clock_basis == 'injected_fixture_clock'
    assert [o.status for o in result.observations] == ['unchanged', 'unchanged']
    assert all(o.valid_pdf_pages == 7 and o.bytes_equal_to_baseline for o in result.observations)
    assert all(o.legal_currentness == 'not_verified' for o in result.observations)
    assert '2015' in ' '.join(result.observations[0].source_context)
    assert 'PPRBD' in ' '.join(result.observations[1].source_context)
    assert w.verify_run(packet / w.SELECTION, packet / w.RUNTIME / 'fixture') == result
    assert not result.baseline_updated and not result.scheduler_installed


def test_changed_valid_pdf_requires_review(packet: Path) -> None:
    """Different valid bytes do not alter the original expected hash or legal status."""
    old = bodies(packet)
    result, _ = run(packet, [Response(changed_pdf()), Response(old[1])])
    first = result.observations[0]
    assert first.status == 'changed' and first.review_needed and first.valid_pdf_pages == 1
    assert not first.bytes_equal_to_baseline and first.inferred_legal_change is None
    assert first.baseline.sha256 == hashlib.sha256(old[0]).hexdigest()
    assert bodies(packet) == old


@pytest.mark.parametrize('status', [401, 403, 407])
def test_denial_stops_batch_without_retry(packet: Path, status: int) -> None:
    """Publisher denials stop before source two and preserve the actual response body."""
    result, calls = run(packet, [Response(b'<html>denied</html>', status)])
    assert len(calls) == 1 and result.status == 'stopped'
    assert [o.status for o in result.observations] == ['access_denied', 'not_checked']
    assert result.observations[1].response_body is None
    assert w.verify_run(packet / w.SELECTION, packet / w.RUNTIME / 'fixture') == result


@pytest.mark.parametrize('status', [404, 410])
def test_missing_is_not_repeal_or_unchanged(packet: Path, status: int) -> None:
    """A missing source may coexist with an unchanged second source."""
    result, calls = run(packet, [Response(b'missing', status), Response(bodies(packet)[1])])
    assert len(calls) == 2
    assert result.observations[0].status == 'not_found'
    assert result.observations[0].inferred_legal_change is None
    assert result.observations[1].status == 'unchanged'


@pytest.mark.parametrize('error', [TimeoutError(), OSError(), ValueError('fixture')])
def test_transport_failure_retains_completed_other_source(packet: Path, error: Exception) -> None:
    """A transport failure produces no false publisher denial or byte comparison."""
    result, calls = run(packet, [Response(bodies(packet)[0]), error])
    assert len(calls) == 2
    assert result.observations[0].status == 'unchanged'
    assert result.observations[1].status == 'transport_error'
    assert result.observations[1].http_status is None
    assert result.observations[1].bytes_equal_to_baseline is None


@pytest.mark.parametrize('body,headers', [
    (b'<html>viewer</html>', {'content-type': 'text/html', 'content-length': '19'}),
    (b'%PDF-1.7\ncorrupt\n%%EOF', {'content-type': 'application/pdf', 'content-length': '22'}),
    (b'', {'content-type': 'application/pdf', 'content-length': '0'}),
])
def test_incomplete_and_nonpdf_never_changed(packet: Path, body: bytes,
                                            headers: dict[str, str]) -> None:
    """Framing and format failures cannot become changed legal documents."""
    result, _ = run(packet, [Response(body, headers=headers), Response(bodies(packet)[1])])
    assert result.observations[0].status == 'invalid_response'
    assert result.observations[0].bytes_equal_to_baseline is None


@pytest.mark.parametrize('content_type', ['text/html', 'application/octet-stream', ''])
def test_pdf_magic_does_not_override_changed_media_type(packet: Path, content_type: str) -> None:
    """Even exact old PDF bytes need the expected declared response type."""
    data = bodies(packet)
    headers = {'content-type': content_type, 'content-length': str(len(data[0]))}
    result, _ = run(packet, [Response(data[0], headers=headers), Response(data[1])])
    assert result.observations[0].status == 'invalid_response'


def test_truncation_with_known_length(packet: Path) -> None:
    """A short HTTP body retains bytes but cannot claim exact equality."""
    data = bodies(packet)
    response = Response(data[0][:-100], headers={
        'content-type': 'application/pdf', 'content-length': str(len(data[0]))})
    result, _ = run(packet, [response, Response(data[1])])
    assert result.observations[0].status == 'invalid_response'
    assert result.observations[0].response_body.size_bytes == len(data[0]) - 100


def test_same_host_redirect_counted(packet: Path) -> None:
    """One observed same-host hop costs an additional request and retains the old body."""
    data = bodies(packet)
    redirect = Response(b'', 302, {
        'location': '/system/files/redirected.pdf', 'content-length': '0'})
    result, calls = run(packet, [redirect, Response(data[0]), Response(data[1])])
    assert len(calls) == 3 and result.state.request_count == 3
    assert result.observations[0].status == 'unchanged'
    assert result.observations[0].events == [1, 2]
    assert result.observations[0].response_url.endswith('/redirected.pdf')


@pytest.mark.parametrize('location', [
    'https://www.coloradosprings.gov/moved.pdf', 'https://example.org/other.pdf',
    'http://coloradosprings.gov/insecure.pdf', 'https://coloradosprings.gov/login',
])
def test_redirect_destination_refused(packet: Path, location: str) -> None:
    """No host, TLS or authentication fallback is requested."""
    redirect = Response(b'', 302, {'location': location, 'content-length': '0'})
    result, calls = run(packet, [redirect, Response(bodies(packet)[1])])
    assert len(calls) <= 2 and location not in calls
    assert result.observations[0].status == 'refused'


def test_redirect_budget_stops_without_losing_first_hop(packet: Path) -> None:
    """Two offered redirects exceed the single-hop limit before a third request."""
    replies = [Response(b'', 301, {'location': '/a.pdf', 'content-length': '0'}),
               Response(b'', 301, {'location': '/b.pdf', 'content-length': '0'})]
    result, calls = run(packet, replies)
    assert len(calls) == 2 and result.observations[0].events == [1, 2]
    assert result.observations[0].status == 'refused'
    assert result.observations[1].status == 'not_checked'


@pytest.mark.parametrize('key', ['requests', 'distinct_urls'])
def test_request_budget_refuses_before_second_source(packet: Path, key: str) -> None:
    """A narrowed budget preserves source one and records source two as unattempted."""
    change_plan(packet, lambda p: p['limits'].update({key: 1}))
    result, calls = run(packet, [Response(bodies(packet)[0])])
    assert len(calls) == 1 and result.status == 'stopped'
    assert result.observations[1].status == 'not_checked'


def test_byte_budget_retains_bounded_prefix(packet: Path) -> None:
    """No over-read is needed to classify an unknown-length body at its cap."""
    change_plan(packet, lambda p: p['limits'].update(bytes_per_source=128, total_bytes=128))
    result, calls = run(packet, [Response(bodies(packet)[0])])
    assert len(calls) == 1 and result.state.charged_bytes == 128
    assert result.observations[0].response_body.size_bytes == 128
    assert result.observations[0].status == 'refused'


def test_interrupt_retains_partial_body_and_never_retries(packet: Path) -> None:
    """Controlled interruption preserves the exact partial response under one reservation."""
    result, calls = run(packet, [Response(bodies(packet)[0], fail=True)])
    assert len(calls) == 1 and result.observations[0].status == 'transport_error'
    assert result.observations[0].response_body.size_bytes == 64
    assert result.observations[1].status == 'not_checked'
    assert result.state.charged_bytes == 2_000_000


def test_existing_report_replay_makes_no_requests(packet: Path) -> None:
    """Repeated reading reuses the immutable report and cannot refetch a completed attempt."""
    first, _ = run(packet, [Response(x) for x in bodies(packet)])
    second, calls = run(packet, [])
    assert first == second and not calls
    with pytest.raises(ValueError, match='dispatch differs'):
        w.run_watch(packet / w.SELECTION, packet / w.RUNTIME / 'fixture',
                    NOW + timedelta(seconds=1),
                    w.g.sha(packet / w.SELECTION), fetch=lambda *a: pytest.fail('network'))


@pytest.mark.parametrize('field,value', [
    ('url', 'https://coloradosprings.gov/other.pdf'),
    ('canonical_source_id', 'wrong-owner'),
    ('authority_id', 'CO-COUNTY-EL_PASO'),
])
def test_source_substitution_refused(packet: Path, field: str, value: str) -> None:
    """Source identity, jurisdiction and initial URL cannot be silently reassigned."""
    raw = json.loads((packet / w.SELECTION).read_bytes())
    raw['targets'][0][field] = value
    with pytest.raises(ValueError):
        w.Plan.model_validate_json(json.dumps(raw))


def test_baseline_tamper_refused_before_transport(packet: Path) -> None:
    """Hash custody is checked before any request reservation exists."""
    p = packet / json.loads((packet / w.SELECTION).read_bytes())['targets'][0]['baseline']['path']
    p.write_bytes(p.read_bytes() + b'changed')
    with pytest.raises(ValueError):
        run(packet, [])
    assert not (packet / w.RUNTIME).exists()


def test_reviewed_digest_required_before_request(packet: Path) -> None:
    """The supplied review digest must be the precise checked plan bytes."""
    with pytest.raises(ValueError, match='reviewed plan digest'):
        w.run_watch(packet / w.SELECTION, packet / w.RUNTIME / 'test', NOW, '0' * 64,
                    fetch=lambda *a: pytest.fail('network'))
    assert not (packet / w.RUNTIME).exists()


@pytest.mark.parametrize('name', ['../escape', '/tmp/escape', '.', 'nested/path', 'bad name'])
def test_output_confinement(packet: Path, name: str) -> None:
    """The CLI/API cannot write a canonical repository or arbitrary destination."""
    with pytest.raises(ValueError):
        w.check_output(packet, packet / w.RUNTIME / name)


def test_symlinked_output_ancestor(packet: Path, tmp_path: Path) -> None:
    """An apparently local run cannot be routed elsewhere through a symlink."""
    (packet / w.RUNTIME).parent.mkdir(parents=True)
    (packet / w.RUNTIME).symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink'):
        run(packet, [])


def test_failed_report_write_preserves_prior_source_evidence(
        packet: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed final receipt write never removes successfully saved source bodies."""
    original = w.g.save_model

    def fail(path: Path, record: Any) -> None:
        """Inject failure at the report only."""
        if path.name == 'report.json':
            raise OSError('fixture disk full')
        original(path, record)

    monkeypatch.setattr(w.g, 'save_model', fail)
    with pytest.raises(OSError):
        run(packet, [Response(x) for x in bodies(packet)])
    assert len(list((packet / w.RUNTIME / 'fixture/events').glob('*/body.bin'))) == 2
    monkeypatch.setattr(w.g, 'save_model', original)
    result, calls = run(packet, [])
    assert not calls and result.status == 'completed'


def test_resealed_report_status_tamper_refused(packet: Path) -> None:
    """Even a newly hashed report must reproduce classification from the captured body."""
    run(packet, [Response(x) for x in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    path = output / 'report.json'
    record = json.loads(path.read_bytes())
    record['observations'][0]['status'] = 'changed'
    model = w.Report.model_validate_json(json.dumps(record))
    path.write_text(model.model_dump_json())
    reseal(output)
    with pytest.raises(ValueError, match='classification mismatch'):
        w.verify_run(packet / w.SELECTION, output)


def test_body_tamper_and_unlisted_file_refused(packet: Path) -> None:
    """Body edits and unrelated files cannot be concealed by a successful old report."""
    run(packet, [Response(x) for x in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    extra = output / 'unexpected.txt'
    extra.write_text('extra')
    with pytest.raises(ValueError, match='inventory differs'):
        w.verify_run(packet / w.SELECTION, output)
    extra.unlink()
    body = output / 'events/0001/body.bin'
    body.write_bytes(b'altered')
    with pytest.raises(ValueError):
        w.verify_run(packet / w.SELECTION, output)


@pytest.mark.parametrize('status', [204, 304, 429, 500])
def test_non200_never_equal(packet: Path, status: int) -> None:
    """No unsolicited cache or error status substitutes for verified PDF bytes."""
    result, _ = run(packet, [Response(b'', status), Response(bodies(packet)[1])])
    assert result.observations[0].status == 'transport_error'
    assert result.observations[0].bytes_equal_to_baseline is None


@pytest.mark.parametrize('change', ['order', 'path', 'scope', 'date'])
def test_plan_identity_or_custody_date_mismatch(packet: Path, change: str) -> None:
    """Logical identity and original HTTP time bindings are explicit, not filename guesses."""
    data = json.loads((packet / w.SELECTION).read_bytes())
    if change == 'order':
        data['targets'].reverse()
    elif change == 'path':
        data['targets'][0]['baseline']['path'] = 'other.pdf'
    elif change == 'scope':
        data['custody_scope']['sha256'] = '0' * 64
    else:
        data['targets'][0]['baseline_request_started_at'] = '2026-01-01T00:00:00Z'
    if change != 'date':
        with pytest.raises(ValueError):
            w.Plan.model_validate_json(json.dumps(data))
    else:
        model = w.Plan.model_validate_json(json.dumps(data))
        (packet / w.SELECTION).write_text(model.model_dump_json())
        with pytest.raises(ValueError, match='HTTP/source binding'):
            w.load_plan(packet / w.SELECTION)


@pytest.mark.parametrize('offset', [-301, 1])
def test_expired_or_future_dispatch_refused_before_write(packet: Path, offset: int) -> None:
    """Invalid invocation times cannot create misleading HTTP attempts."""
    with pytest.raises(ValueError, match='dispatch time'):
        w.run_watch(packet / w.SELECTION, packet / w.RUNTIME / 'time',
                    NOW + timedelta(seconds=offset), w.g.sha(packet / w.SELECTION),
                    clock=lambda: NOW, fetch=lambda *a: pytest.fail('network'))
    assert not (packet / w.RUNTIME).exists()


def test_naive_dispatch_refused_before_write(packet: Path) -> None:
    """Timezone omission is refused, not silently interpreted as local time."""
    with pytest.raises(ValueError, match='timezone aware'):
        w.run_watch(packet / w.SELECTION, packet / w.RUNTIME / 'time', NOW.replace(tzinfo=None),
                    w.g.sha(packet / w.SELECTION), clock=lambda: NOW,
                    fetch=lambda *a: pytest.fail('network'))
    assert not (packet / w.RUNTIME).exists()


def test_more_than100_page_pdf_refused() -> None:
    """A tiny but excessive-page document is not admitted as an ordinary changed fee schedule."""
    with pymupdf.open() as pdf:
        for _ in range(101):
            pdf.new_page()
        data = pdf.tobytes()
    with pytest.raises(ValueError, match='page limit'):
        w.pdf_pages(data)


def test_encrypted_pdf_refused() -> None:
    """Password-protected source bytes are preserved but not certified as readable PDFs."""
    with pymupdf.open() as pdf:
        pdf.new_page()
        data = pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                          owner_pw='fixture-owner', user_pw='fixture-user')
    with pytest.raises(ValueError, match='structure'):
        w.pdf_pages(data)


@pytest.mark.parametrize('field,value', [
    ('implementation_sha256', '0' * 64), ('mode', 'live_http'),
    ('generated_at', '2020-01-01T00:00:00Z'), ('status', 'stopped'),
])
def test_resealed_report_metadata_refused(packet: Path, field: str, value: str) -> None:
    """Clock, implementation, execution mode and completeness are bound to retained receipts."""
    run(packet, [Response(x) for x in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    path = output / 'report.json'
    data = json.loads(path.read_bytes())
    data[field] = value
    path.write_text(w.Report.model_validate_json(json.dumps(data)).model_dump_json())
    reseal(output)
    with pytest.raises(ValueError):
        w.verify_run(packet / w.SELECTION, output)


def test_seal_failure_recovers_without_fetch(packet: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A durable report with a missing final inventory can be sealed after semantic replay."""
    original = w.seal
    monkeypatch.setattr(w, 'seal', lambda *args: (_ for _ in ()).throw(OSError('seal failure')))
    with pytest.raises(OSError, match='seal failure'):
        run(packet, [Response(b) for b in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    assert (output / 'report.json').exists() and not (output / 'RUN_MANIFEST.json').exists()
    monkeypatch.setattr(w, 'seal', original)
    result, calls = run(packet, [])
    assert not calls and w.verify_run(packet / w.SELECTION, output) == result


def test_unsealed_unknown_payload_is_not_blessed(packet: Path) -> None:
    """Recovering a lost seal must not silently inventory unrelated data."""
    run(packet, [Response(b) for b in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    (output / 'RUN_MANIFEST.json').unlink()
    (output / 'unknown.bin').write_bytes(b'not an event')
    with pytest.raises(ValueError, match='Unexpected'):
        run(packet, [])
    assert not (output / 'RUN_MANIFEST.json').exists()


def test_deadline_between_preflight_and_execute_is_verifiable(packet: Path) -> None:
    """Elapsed initialization creates a zero-request stopped receipt with a valid run clock."""
    ticks = iter([NOW, NOW + timedelta(seconds=301), NOW + timedelta(seconds=302)])
    result, calls = run(packet, [], clock=lambda: next(ticks))
    assert not calls and result.status == 'stopped' and result.state.request_count == 0
    assert w.verify_run(packet / w.SELECTION, packet / w.RUNTIME / 'fixture') == result


def test_late_complete_cannot_prove_equality(packet: Path) -> None:
    """Even resealed complete evidence cannot certify success beyond its reserved deadline."""
    run(packet, [Response(b) for b in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    result_path = output / 'events/0001/result.json'
    result = w.g.Result.model_validate_json(result_path.read_bytes())
    result = result.model_copy(update={'finished_at': NOW + timedelta(seconds=31)})
    result_path.write_text(result.model_dump_json())
    pairs = w.WatchGuard(packet / w.SELECTION, output).ledger()
    obs = w.observation(w.load_plan(packet / w.SELECTION).targets[0], pairs, output)
    assert obs.status == 'transport_error' and obs.bytes_equal_to_baseline is None
    report_path = output / 'report.json'
    report = w.Report.model_validate_json(report_path.read_bytes())
    report_path.write_text(report.model_copy(update={
        'generated_at': NOW + timedelta(seconds=32)}).model_dump_json())
    reseal(output)
    with pytest.raises(ValueError, match='deadline'):
        w.verify_run(packet / w.SELECTION, output)


@pytest.mark.parametrize('delay_ms', [1, 2])
def test_deadline_during_result_finalization_seals_and_replays(
        packet: Path, monkeypatch: pytest.MonkeyPatch, delay_ms: int) -> None:
    """Exact/late finalization deadlines retain bytes but never produce invalid complete records."""
    current = NOW
    crossed = False
    original_sha = w.g.sha

    class AlmostInTime(Response):
        """Finish actual fixture reading just before the declared request deadline."""
        def close(self) -> None:
            nonlocal current
            super().close()
            current = NOW + timedelta(seconds=29.999)

    def delayed_sha(path: Path) -> str:
        """Simulate the reservation-hash I/O crossing the deadline in finish(), once."""
        nonlocal current, crossed
        value = original_sha(path)
        caller = inspect.currentframe().f_back.f_code.co_name
        if path.name == 'reservation.json' and caller == 'finish' and not crossed:
            current += timedelta(milliseconds=delay_ms)
            crossed = True
        return value

    monkeypatch.setattr(w.g, 'sha', delayed_sha)
    originals = bodies(packet)
    report, calls = run(packet, [AlmostInTime(originals[0]), Response(originals[1])],
                        clock=lambda: current)
    output = packet / w.RUNTIME / 'fixture'
    event = w.g.Result.model_validate_json((output / 'events/0001/result.json').read_bytes())
    assert crossed and len(calls) == 2
    assert event.finished_at == NOW + timedelta(seconds=29.999, milliseconds=delay_ms)
    assert event.outcome == 'timeout' and event.partial_body
    assert event.error_type == 'deadline_during_result_finalization'
    assert (output / event.body.path).read_bytes() == originals[0]
    assert report.status == 'stopped' and report.observations[0].status == 'transport_error'
    assert report.observations[0].bytes_equal_to_baseline is None
    assert report.observations[1].status == 'unchanged'
    assert w.verify_run(packet / w.SELECTION, output) == report
    replay, more_calls = run(packet, [], clock=lambda: current)
    assert replay == report and not more_calls


def append_unrelated(root: Path, missing: bool = False) -> None:
    """Add a distinct validated intake record without changing the selected originals."""
    path = root / w.MANUAL_MANIFEST
    with path.open('rb') as handle:
        row = w.ManualSourceIntakeRecord.model_validate_json(next(handle))
    data = row.model_dump(mode='json')
    data.update(record_id='unselected-fixture', intake_id='MSI-unselected-fixture')
    if missing:
        data['archive_path'] = '_RAW_ARCHIVE/manual_intake/missing.pdf'
    model = w.ManualSourceIntakeRecord.model_validate_json(json.dumps(data))
    with path.open('ab') as handle:
        handle.write(model.model_dump_json().encode() + b'\n')


def test_append_does_not_break_runtime_preimage(
        packet: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A report-write interruption resumes against its exact old source-manifest snapshot."""
    original = w.g.save_model

    def fail(path: Path, record: Any) -> None:
        """Fail only the terminal report."""
        if path.name == 'report.json':
            raise OSError('report failure')
        original(path, record)

    monkeypatch.setattr(w.g, 'save_model', fail)
    with pytest.raises(OSError):
        run(packet, [Response(b) for b in bodies(packet)])
    snapshot = packet / w.RUNTIME / 'fixture/inputs/manual_manifest.jsonl'
    before = snapshot.read_bytes()
    append_unrelated(packet)
    monkeypatch.setattr(w.g, 'save_model', original)
    result, calls = run(packet, [], clock=lambda: NOW + timedelta(seconds=400))
    assert not calls and result.status == 'completed' and snapshot.read_bytes() == before


def test_readiness_counts_dynamic_unavailable_records(packet: Path) -> None:
    """Preserved, available, configured and historical live checks remain distinct."""
    append_unrelated(packet, missing=True)
    result = w.readiness(packet)
    assert result.manual_pdf_records == 3 and result.locally_hash_verified_pdf_originals == 2
    assert result.configured_sources == 2 and result.unselected_manual_pdf_records == 1
    assert result.accepted_prior_finite_live_source_checks == 2
    assert result.unavailable_or_mismatch[0].record_id == 'unselected-fixture'
    assert result.recurring_deployment == 'not_deployed_by_this_feature'
    assert not result.fixed_urls_find_new_editions_elsewhere


def test_cli_readiness_and_execute_requirements(packet: Path, capsys: Any) -> None:
    """Default CLI is offline, and incomplete explicit execution is refused."""
    assert w.main(['--root', str(packet)]) == 0
    assert json.loads(capsys.readouterr().out)['configured_sources'] == 2
    assert w.main(['--root', str(packet), '--execute']) == 2
    assert 'Execution requires' in capsys.readouterr().err


def test_cli_reuses_retained_dispatch(packet: Path, monkeypatch: pytest.MonkeyPatch,
                                      capsys: Any) -> None:
    """CLI replay uses the original dispatch without changing it to today's clock."""
    report, _ = run(packet, [Response(b) for b in bodies(packet)])
    calls = []

    def replay(plan: Path, output: Path, dispatch: datetime, digest: str) -> Any:
        """Verify the exact retained dispatch passed by CLI without a transport."""
        calls.append(dispatch)
        assert dispatch == NOW and digest == w.g.sha(plan)
        return w.verify_run(plan, output)

    monkeypatch.setattr(w, 'run_watch', replay)
    arguments = ['--root', str(packet), '--execute', '--run-name', 'fixture',
                 '--reviewed-selection-sha256', w.g.sha(packet / w.SELECTION)]
    assert w.main(arguments) == 0 and calls == [NOW]
    assert json.loads(capsys.readouterr().out)['dispatch_at'] == report.model_dump(mode='json')[
        'dispatch_at']
    assert w.main(['--root', str(packet), '--verify-run', 'fixture']) == 0
    capsys.readouterr()


@pytest.mark.parametrize('name', ['selection_snapshot', 'manual_manifest_snapshot',
                                'transport_sha256'])
def test_runtime_receipt_substitutions_refused(packet: Path, name: str) -> None:
    """Resealed invocation metadata must preserve the selected inputs and helper identity."""
    run(packet, [Response(b) for b in bodies(packet)])
    output = packet / w.RUNTIME / 'fixture'
    path = output / 'INVOCATION.json'
    data = json.loads(path.read_bytes())
    if name.endswith('snapshot'):
        data[name]['path'] = 'other.json'
    else:
        data[name] = '0' * 64
    path.write_text(w.Invocation.model_validate_json(json.dumps(data)).model_dump_json())
    report_path = output / 'report.json'
    report = w.Report.model_validate_json(report_path.read_bytes())
    report_path.write_text(report.model_copy(update={
        'invocation': w.g.file_ref(output, path)}).model_dump_json())
    reseal(output)
    with pytest.raises(ValueError):
        w.verify_run(packet / w.SELECTION, output)


@pytest.mark.parametrize('payload', [b'\n', b'', b'{"bad": true}\n'])
def test_bad_manual_manifest_refused(packet: Path, payload: bytes) -> None:
    """Blank, empty or invalid intake streams cannot produce readiness."""
    (packet / w.MANUAL_MANIFEST).write_bytes(payload)
    with pytest.raises(ValueError):
        w.manual_records(packet)


def test_duplicate_manifest_and_external_schema_refused(packet: Path) -> None:
    """Ambiguous source rows and declarative remote schema references are rejected offline."""
    path = packet / w.MANUAL_MANIFEST
    with path.open('rb') as handle:
        first = next(handle)
    with path.open('ab') as handle:
        handle.write(first)
    with pytest.raises(ValueError, match='Duplicate'):
        w.manual_records(packet)
    with pytest.raises(ValueError, match='External'):
        w.schema_check(b'{}', b'{"allOf":[{"$ref":"https://example.com/schema"}]}')


def test_unique_inventory_and_config_location(packet: Path) -> None:
    """Duplicate inventory paths and alternate config locations have no admitted identity."""
    ref = w.g.file_ref(packet, packet / w.SELECTION)
    with pytest.raises(ValueError, match='Duplicate'):
        w.FileInventory(kind='run', files=[ref, ref])
    wrong = packet / 'other.json'
    shutil.copyfile(packet / w.SELECTION, wrong)
    with pytest.raises(ValueError, match='Selection must'):
        w.repository_root(wrong)


@pytest.mark.parametrize('key', ['custody_schema', 'prior_live'])
def test_fixed_custody_anchor_replacement_refused(packet: Path, key: str) -> None:
    """A locally rehashed alternate custody schema or historical run is not accepted."""
    data = json.loads((packet / w.SELECTION).read_bytes())
    if key == 'prior_live':
        data[key]['report']['sha256'] = '0' * 64
    else:
        data[key]['sha256'] = '0' * 64
    with pytest.raises(ValueError):
        w.Plan.model_validate_json(json.dumps(data))
