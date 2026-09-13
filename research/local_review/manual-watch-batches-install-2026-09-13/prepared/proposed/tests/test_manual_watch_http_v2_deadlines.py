"""Absolute parser deadlines using only local socket pairs and injected responses."""
from __future__ import annotations

import contextlib
import http.client
import socket
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from geode.pipeline import manual_watch_http_v2 as g


def timers() -> set[int | None]:
    """Identify deadline workers so each operation proves it leaves none behind."""
    return {t.ident for t in threading.enumerate() if t.name == 'geode-watch-deadline'}


@contextlib.contextmanager
def trickle_response(prefix: bytes, lines: list[bytes], delay: float):
    """Serve explicit HTTP bytes through an AF_UNIX pair, never a network socket."""
    reader, writer = socket.socketpair()
    stopped = threading.Event()

    def send() -> None:
        try:
            writer.sendall(prefix)
            for line in lines:
                if stopped.wait(delay):
                    break
                writer.sendall(line)
        except OSError:
            pass  # The watchdog intentionally shuts down the receiver.
        finally:
            writer.close()

    thread = threading.Thread(target=send)
    thread.start()
    try:
        yield reader
    finally:
        stopped.set()
        reader.close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def test_expired_socket_operation_has_no_worker() -> None:
    """No operation or timer starts when no budget remains."""
    before = timers()
    with pytest.raises(TimeoutError, match='deadline'):
        with g.socket_deadline(None, 0):
            pytest.fail('entered expired operation')
    assert timers() == before


@pytest.mark.parametrize('error', [ValueError('fixture'), KeyboardInterrupt()])
def test_timer_cancelled_when_operation_raises(error: BaseException) -> None:
    """Exception propagation must cancel and join the independent watchdog."""
    reader, writer = socket.socketpair()
    before = timers()
    try:
        with pytest.raises(type(error)):
            with g.socket_deadline(reader, 10):
                raise error
        assert timers() == before
        writer.sendall(b'x')
        assert reader.recv(1) == b'x'
    finally:
        reader.close()
        writer.close()


def test_success_has_no_late_shutdown() -> None:
    """A cancelled timer cannot later terminate a reused socket."""
    reader, writer = socket.socketpair()
    before = timers()
    try:
        with g.socket_deadline(reader, .05):
            writer.sendall(b'a')
            assert reader.recv(1) == b'a'
        time.sleep(.07)
        writer.sendall(b'b')
        assert reader.recv(1) == b'b'
        assert timers() == before
    finally:
        reader.close()
        writer.close()


def test_deadline_closes_blocked_read_and_joins_worker() -> None:
    """A socket that never returns is interrupted without waiting for a peer EOF."""
    reader, writer = socket.socketpair()
    before = timers()
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            with g.socket_deadline(reader, .08):
                reader.recv(1)
        assert time.monotonic() - start < .8
        assert timers() == before
    finally:
        reader.close()
        writer.close()


def test_closed_socket_shutdown_error_is_bounded() -> None:
    """A concurrent close does not turn watchdog cleanup into a leaking thread."""
    reader, writer = socket.socketpair()
    reader.close()
    writer.close()
    before = timers()
    with pytest.raises(TimeoutError):
        with g.socket_deadline(reader, .02):
            time.sleep(.04)
    assert timers() == before


def test_real_chunk_trailers_obey_total_read_deadline() -> None:
    """read1 may parse many lines; each arriving line cannot refresh the total budget."""
    prefix = (b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n'
              b'4\r\nbody\r\n0\r\n')
    with trickle_response(prefix, [b'X-Trailer: value\r\n'] * 20 + [b'\r\n'], .03) as reader:
        raw = http.client.HTTPResponse(reader)
        raw.begin()
        response = g.Response(SimpleNamespace(close=lambda: None), raw, reader)
        duplicate = response.deadline_socket
        reader.close()  # Response's file object stays open after Connection: close.
        try:
            assert response.read(4, .5) == b'body'
            start = time.monotonic()
            with pytest.raises(TimeoutError):
                response.read(4, .12)
            assert time.monotonic() - start < .8
            assert not timers()
        finally:
            response.close()
        assert duplicate.fileno() == -1


def test_real_slow_response_headers_obey_transport_deadline(monkeypatch) -> None:
    """Actual HTTPResponse header parsing is stopped across repeated short lines."""
    prefix = b'HTTP/1.1 200 OK\r\n'
    with trickle_response(prefix, [b'X-Header: value\r\n'] * 20 + [b'\r\n'], .03) as reader:
        monkeypatch.setattr(g.subprocess, 'run', lambda *a, **k:
                            SimpleNamespace(stdout=b'["8.8.8.8"]'))
        monkeypatch.setattr(g.socket, 'create_connection', lambda *a, **k: reader)
        monkeypatch.setattr(g.ssl, 'create_default_context', lambda **k:
                            SimpleNamespace(wrap_socket=lambda sock, **kwargs: sock))
        before = timers()
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            g.transport('https://www.gjcity.org/a.pdf',
                        g.utcnow() + timedelta(seconds=.12), g.utcnow)
        assert time.monotonic() - start < .8
        assert reader.fileno() == -1
        assert timers() == before


@pytest.mark.parametrize('late_chunk', [b'abcd', b''])
def test_late_injected_return_is_never_complete(tmp_path: Path, late_chunk: bytes) -> None:
    """Even an injected transport that ignores time cannot certify late bytes or EOF."""
    now = datetime(2026, 9, 13, tzinfo=timezone.utc)
    clock = [now]
    plan = g.Plan(targets=[g.Target(source_id=f's{n}',
                  url=f'https://www.gjcity.org/{n}.pdf') for n in range(2)],
                  limits=g.Limits(bytes_per_source=4))
    path = tmp_path / 'plan.json'
    g.save_model(path, plan)

    def read(count: int, timeout: float) -> bytes:
        clock[0] = now + timedelta(seconds=31)
        return late_chunk

    response = SimpleNamespace(status=200, headers={'content-length': str(len(late_chunk))},
                               read=read, close=lambda: None)
    guard = g.Guard(path, tmp_path / 'run', clock=lambda: clock[0], fetch=lambda *a: response)
    run = g.Run(plan_sha256=g.sha(path), dispatch_at=now, initialized_at=now,
                deadline=now + timedelta(minutes=5))
    with guard.lock():
        reservation = guard.reserve('s0', plan.targets[0].url, 0, run)
        result = guard.request(reservation)
    assert result.outcome == 'timeout' and result.partial_body
    assert (guard.output / result.body.path).read_bytes() == late_chunk
    assert result.charged_bytes == len(late_chunk)
    assert not timers()


def test_response_close_releases_watch_descriptor_even_on_error() -> None:
    """A failed response close still releases the additional interrupt descriptor."""
    reader, writer = socket.socketpair()
    raw = SimpleNamespace(status=200, getheaders=lambda: [],
                          close=lambda: (_ for _ in ()).throw(OSError('fixture')))
    closed = []
    response = g.Response(SimpleNamespace(close=lambda: closed.append(True)), raw, reader)
    try:
        with pytest.raises(OSError):
            response.close()
        assert closed == [True]
        assert response.deadline_socket.fileno() == -1
    finally:
        reader.close()
        writer.close()
