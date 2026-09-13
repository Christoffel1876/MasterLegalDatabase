"""Offline fixtures for fixed-source byte watching; never make public requests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pymupdf
import pytest

SOURCE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('watch_under_test', SOURCE / 'watch.py')
w = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = w
spec.loader.exec_module(w)
NOW = datetime(2026, 9, 13, 0, 10, tzinfo=timezone.utc)


class Response:
    """Controlled finite body with HTTP fields and optional interrupted read."""
    def __init__(self, body: bytes, status: int = 200,
                 headers: dict[str, str] | None = None, fail: bool = False) -> None:
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
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copy only exact required inputs into a temporary standalone handoff."""
    root = tmp_path / 'packet'
    root.mkdir()
    for name in ['watch.py', 'sd014_guard.py', 'WATCH_PLAN.json']:
        shutil.copyfile(SOURCE / name, root / name)
    shutil.copytree(SOURCE / 'evidence', root / 'evidence')
    monkeypatch.setattr(w, 'HERE', root)
    return root


def bodies(root: Path) -> list[bytes]:
    """Use both actual frozen originals for equality fixtures."""
    return [(root / f'evidence/custody/SD014-0{i}/original.pdf').read_bytes() for i in [1, 2]]


def changed_pdf() -> bytes:
    """Generate a distinct valid PDF fixture without modifying source originals."""
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'Offline changed source fixture')
        return pdf.tobytes()


def run(root: Path, items: list[Any], name: str = 'fixture',
        clock: Any = lambda: NOW) -> tuple[Any, list[str]]:
    """Inject every HTTP outcome and verify reservation-before-transport ordering."""
    calls: list[str] = []
    output = root / 'runs' / name

    def fetch(url: str, deadline: datetime, now: Any) -> Any:
        """A local response sequence, never a real transport."""
        records = sorted(output.glob('events/*/reservation.json'))
        assert len(records) == len(calls) + 1
        calls.append(url)
        value = items.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value

    result = w.run_watch(root / 'WATCH_PLAN.json', output, NOW,
                         w.g.sha(root / 'WATCH_PLAN.json'), clock=clock, fetch=fetch)
    return result, calls


def reseal(root: Path, kind: str = 'run') -> None:
    """Reseal only temporary tamper fixtures to exercise semantic checks."""
    name = 'RUN_MANIFEST.json' if kind == 'run' else 'PACKAGE_MANIFEST.json'
    (root / name).unlink()
    w.seal(root, kind)


def change_plan(root: Path, update: Any) -> None:
    """Write a schema-validated temporary plan with deliberately narrowed bounds."""
    path = root / 'WATCH_PLAN.json'
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
    assert w.verify_run(packet / 'WATCH_PLAN.json', packet / 'runs/fixture') == result
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
    assert w.verify_run(packet / 'WATCH_PLAN.json', packet / 'runs/fixture') == result


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
    redirect = Response(b'', 302, {'location': '/system/files/redirected.pdf', 'content-length': '0'})
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
        w.run_watch(packet / 'WATCH_PLAN.json', packet / 'runs/fixture', NOW + timedelta(seconds=1),
                    w.g.sha(packet / 'WATCH_PLAN.json'), fetch=lambda *a: pytest.fail('network'))


@pytest.mark.parametrize('field,value', [
    ('url', 'https://coloradosprings.gov/other.pdf'),
    ('canonical_source_id', 'wrong-owner'),
    ('authority_id', 'CO-COUNTY-EL_PASO'),
])
def test_source_substitution_refused(packet: Path, field: str, value: str) -> None:
    """Source identity, jurisdiction and initial URL cannot be silently reassigned."""
    raw = json.loads((packet / 'WATCH_PLAN.json').read_bytes())
    raw['targets'][0][field] = value
    with pytest.raises(ValueError):
        w.Plan.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize('field', ['hard_stop', 'no_new_source_at', 'proposed_finish_by'])
def test_time_bound_expansion_refused(packet: Path, field: str) -> None:
    """This prototype is not an indefinite authorization for future recurring runs."""
    raw = json.loads((packet / 'WATCH_PLAN.json').read_bytes())
    raw[field] = '2027-01-01T00:00:00Z'
    with pytest.raises(ValueError):
        w.Plan.model_validate_json(json.dumps(raw))


def test_baseline_tamper_refused_before_transport(packet: Path) -> None:
    """Hash custody is checked before any request reservation exists."""
    p = packet / 'evidence/custody/SD014-01/original.pdf'
    p.write_bytes(p.read_bytes() + b'changed')
    with pytest.raises(ValueError):
        run(packet, [])
    assert not (packet / 'runs').exists()


def test_reviewed_digest_required_before_request(packet: Path) -> None:
    """The supplied review digest must be the precise checked plan bytes."""
    with pytest.raises(ValueError, match='reviewed plan digest'):
        w.run_watch(packet / 'WATCH_PLAN.json', packet / 'runs/test', NOW, '0' * 64,
                    fetch=lambda *a: pytest.fail('network'))
    assert not (packet / 'runs').exists()


@pytest.mark.parametrize('name', ['../escape', '/tmp/escape', '.', 'nested/path', 'bad name'])
def test_output_confinement(packet: Path, name: str) -> None:
    """The CLI/API cannot write a canonical repository or arbitrary destination."""
    with pytest.raises(ValueError):
        w.check_output(packet, packet / 'runs' / name)


def test_symlinked_output_ancestor(packet: Path, tmp_path: Path) -> None:
    """An apparently local run cannot be routed elsewhere through a symlink."""
    (packet / 'runs').symlink_to(tmp_path, target_is_directory=True)
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
    assert len(list((packet / 'runs/fixture/events').glob('*/body.bin'))) == 2
    monkeypatch.setattr(w.g, 'save_model', original)
    result, calls = run(packet, [])
    assert not calls and result.status == 'completed'


def test_resealed_report_status_tamper_refused(packet: Path) -> None:
    """Even a newly hashed report must reproduce classification from the captured body."""
    run(packet, [Response(x) for x in bodies(packet)])
    output = packet / 'runs/fixture'
    path = output / 'report.json'
    record = json.loads(path.read_bytes())
    record['observations'][0]['status'] = 'changed'
    model = w.Report.model_validate_json(json.dumps(record))
    path.write_text(model.model_dump_json())
    reseal(output)
    with pytest.raises(ValueError, match='classification mismatch'):
        w.verify_run(packet / 'WATCH_PLAN.json', output)


def test_body_tamper_and_unlisted_file_refused(packet: Path) -> None:
    """Body edits and unrelated files cannot be concealed by a successful old report."""
    run(packet, [Response(x) for x in bodies(packet)])
    output = packet / 'runs/fixture'
    extra = output / 'unexpected.txt'
    extra.write_text('extra')
    with pytest.raises(ValueError, match='inventory differs'):
        w.verify_run(packet / 'WATCH_PLAN.json', output)
    extra.unlink()
    body = output / 'events/0001/body.bin'
    body.write_bytes(b'altered')
    with pytest.raises(ValueError):
        w.verify_run(packet / 'WATCH_PLAN.json', output)


def test_default_cli_is_offline(packet: Path, monkeypatch: pytest.MonkeyPatch,
                                capsys: pytest.CaptureFixture[str]) -> None:
    """A default command validates the plan and cannot make a public request."""
    w.seal(packet, 'prototype')
    monkeypatch.setattr(sys, 'argv', ['watch.py'])
    monkeypatch.setattr(w.g, 'transport', lambda *a: pytest.fail('network'))
    assert w.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output['status'] == 'PREPARED_NOT_DISPATCHED' and output['public_requests_made'] == 0


@pytest.mark.parametrize('argv', [
    ['--execute'], ['--execute', '--verify-run', 'a'],
    ['--execute', '--run-name', 'a', '--dispatch-at', '2026-09-13T00:10:00',
     '--reviewed-plan-sha256', '0' * 64],
])
def test_cli_missing_or_conflicting_execution_fields(
        packet: Path, monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> None:
    """Missing reviewed input or timezone data fails before transport."""
    w.seal(packet, 'prototype')
    monkeypatch.setattr(sys, 'argv', ['watch.py'] + argv)
    monkeypatch.setattr(w.g, 'transport', lambda *a: pytest.fail('network'))
    assert w.main() == 2


@pytest.mark.parametrize('status', [204, 304, 429, 500])
def test_non200_never_equal(packet: Path, status: int) -> None:
    """No unsolicited cache or error status substitutes for verified PDF bytes."""
    result, _ = run(packet, [Response(b'', status), Response(bodies(packet)[1])])
    assert result.observations[0].status == 'transport_error'
    assert result.observations[0].bytes_equal_to_baseline is None


@pytest.mark.parametrize('change', ['order', 'path', 'scope', 'date'])
def test_plan_identity_or_custody_date_mismatch(packet: Path, change: str) -> None:
    """Logical identity and original HTTP time bindings are explicit, not filename guesses."""
    data = json.loads((packet / 'WATCH_PLAN.json').read_bytes())
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
        (packet / 'WATCH_PLAN.json').write_text(model.model_dump_json())
        with pytest.raises(ValueError, match='date binding'):
            w.load_plan(packet / 'WATCH_PLAN.json')


@pytest.mark.parametrize('offset', [-301, 1])
def test_expired_or_future_dispatch_refused_before_write(packet: Path, offset: int) -> None:
    """Invalid invocation times cannot create misleading HTTP attempts."""
    with pytest.raises(ValueError, match='dispatch time'):
        w.run_watch(packet / 'WATCH_PLAN.json', packet / 'runs/time',
                    NOW + timedelta(seconds=offset), w.g.sha(packet / 'WATCH_PLAN.json'),
                    clock=lambda: NOW, fetch=lambda *a: pytest.fail('network'))
    assert not (packet / 'runs').exists()


def test_naive_dispatch_refused_before_write(packet: Path) -> None:
    """Timezone omission is refused, not silently interpreted as local time."""
    with pytest.raises(ValueError, match='timezone aware'):
        w.run_watch(packet / 'WATCH_PLAN.json', packet / 'runs/time', NOW.replace(tzinfo=None),
                    w.g.sha(packet / 'WATCH_PLAN.json'), clock=lambda: NOW,
                    fetch=lambda *a: pytest.fail('network'))
    assert not (packet / 'runs').exists()


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
    output = packet / 'runs/fixture'
    path = output / 'report.json'
    data = json.loads(path.read_bytes())
    data[field] = value
    path.write_text(w.Report.model_validate_json(json.dumps(data)).model_dump_json())
    reseal(output)
    with pytest.raises(ValueError):
        w.verify_run(packet / 'WATCH_PLAN.json', output)


def test_duplicate_inventory_and_wrong_kind_refused(packet: Path) -> None:
    """Closed inventories cannot alias assets or mislabel a run as preparation."""
    ref = w.g.file_ref(packet, packet / 'watch.py')
    with pytest.raises(ValueError, match='Duplicate'):
        w.FileInventory(kind='run', files=[ref, ref])
    w.seal(packet, 'prototype')
    inventory = packet / 'PACKAGE_MANIFEST.json'
    data = json.loads(inventory.read_bytes())
    data['kind'] = 'run'
    inventory.write_text(w.FileInventory.model_validate_json(json.dumps(data)).model_dump_json())
    with pytest.raises(ValueError, match='Wrong inventory'):
        w.verify_inventory(packet, 'prototype')


def test_symlink_inside_inventory_refused(packet: Path) -> None:
    """A copied packet cannot follow an unlisted linked file while hashing."""
    (packet / 'linked.pdf').symlink_to(packet / 'evidence/custody/SD014-01/original.pdf')
    with pytest.raises(ValueError, match='Symlink'):
        w.seal(packet, 'prototype')
    (packet / 'linked.pdf').unlink()
    w.seal(packet, 'prototype')
    (packet / 'linked.pdf').symlink_to(packet / 'evidence/custody/SD014-01/original.pdf')
    with pytest.raises(ValueError, match='Symlink'):
        w.verify_inventory(packet, 'prototype')


def test_unexpected_custody_file_refused(packet: Path) -> None:
    """The selected evidence subset may not silently grow beyond original custody records."""
    (packet / 'evidence/custody/extra.json').write_text('{}')
    with pytest.raises(ValueError, match='Unbound custody'):
        w.load_plan(packet / 'WATCH_PLAN.json')


def test_cli_verifies_offline_result(packet: Path, monkeypatch: pytest.MonkeyPatch,
                                    capsys: pytest.CaptureFixture[str]) -> None:
    """A read-only CLI result validates existing reports without replaying HTTP."""
    run(packet, [Response(x) for x in bodies(packet)])
    w.seal(packet, 'prototype')
    monkeypatch.setattr(sys, 'argv', ['watch.py', '--verify-run', 'fixture'])
    monkeypatch.setattr(w.g, 'transport', lambda *a: pytest.fail('network'))
    assert w.main() == 0
    assert json.loads(capsys.readouterr().out)['mode'] == 'offline_fixture'


def test_cli_execute_boundary_stays_mocked(packet: Path, monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    """Exercise dispatch argument plumbing without permitting a real transport."""
    report, _ = run(packet, [Response(x) for x in bodies(packet)])
    w.seal(packet, 'prototype')
    calls = []

    def fake_run(*args: Any) -> Any:
        """Record the exact dispatch arguments and return a previous fixture result."""
        calls.append(args)
        return report

    monkeypatch.setattr(w, 'run_watch', fake_run)
    monkeypatch.setattr(sys, 'argv', ['watch.py', '--execute', '--run-name', 'new',
        '--dispatch-at', NOW.isoformat(), '--reviewed-plan-sha256', w.g.sha(packet / 'WATCH_PLAN.json')])
    assert w.main() == 0 and len(calls) == 1
    assert json.loads(capsys.readouterr().out)['mode'] == 'offline_fixture'
