"""Offline failure/budget/resume tests; every HTTP transport is injected or mocked."""
import hashlib
import http.client
import socket
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from geode.pipeline import manual_watch_http as g

NOW = datetime(2026, 9, 12, 22, 0, tzinfo=timezone.utc)


class FakeResponse:
    def __init__(self, body=b'ok', status=200, headers=None, interrupt=False, timeout=False):
        self.body, self.status = body, status
        self.headers = headers if headers is not None else {'content-length': str(len(body))}
        self.offset = 0
        self.interrupt, self.timeout = interrupt, timeout
        self.reads = []
        self.closed = False

    def read(self, count, timeout):
        self.reads.append(count)
        if self.offset and self.interrupt:
            raise KeyboardInterrupt()
        if self.offset and self.timeout:
            raise TimeoutError()
        n = min(count, 2) if self.interrupt or self.timeout else count
        result = self.body[self.offset:self.offset + n]
        self.offset += len(result)
        return result

    def close(self):
        self.closed = True


def package(tmp_path, limits=None, urls=None):
    """Create an explicit two-source plan with no discovery dependencies."""
    root = tmp_path / 'packet'
    root.mkdir()
    urls = urls or [f'https://coloradosprings.gov/{n}.pdf' for n in range(2)]
    plan = g.Plan(
        targets=[g.Target(source_id=f'SD014-0{n}', url=url) for n, url in enumerate(urls, 1)],
        limits=g.Limits(**(limits or {})),
    )
    path = root / 'plan.json'
    g.save_model(path, plan)
    return path, tmp_path / 'output'


def execute(path, output, responses, clock=lambda: NOW):
    calls = []
    def fetch(url, deadline, now):
        # Every invocation must already have its durable reservation.
        reservations = sorted(output.glob('events/*/reservation.json'))
        assert len(reservations) == len(calls) + 1
        saved = g.Reservation.model_validate_json(reservations[-1].read_bytes())
        assert saved.url == url and saved.plan_sha256 == g.sha(path)
        calls.append(url)
        response = responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response
    instance = g.Guard(path, output, clock=clock, fetch=fetch)
    return instance, calls


def test_two_sources_same_filename_immutable(tmp_path):
    path, output = package(tmp_path, urls=[f'https://coloradosprings.gov/{n}/same.pdf' for n in range(2)])
    guard, calls = execute(path, output, [FakeResponse(bytes([n])) for n in range(2)])
    state = guard.execute(NOW)
    assert state.request_count == 2 and len(calls) == 2
    before = {str(p): p.read_bytes() for p in output.glob('events/*/*')}
    assert len(list(output.glob('events/*/body.bin'))) == 2
    guard.execute(NOW)
    assert len(calls) == 2
    assert all(Path(p).read_bytes() == b for p, b in before.items())
    with pytest.raises(FileExistsError):
        g.immutable(output / 'events/0001/body.bin', b'overwrite')
    assert (output / 'events/0001/body.bin').read_bytes() == b'\x00'


def test_request_budget_refuses_before_next_transport(tmp_path):
    path, output = package(tmp_path, {'requests': 1})
    guard, calls = execute(path, output, [FakeResponse()])
    with pytest.raises(ValueError, match='Request budget'):
        guard.execute(NOW)
    assert len(calls) == 1 and len(guard.ledger()) == 1


@pytest.mark.parametrize('duplicate', ['source_id', 'url'])
def test_duplicate_selection_refused_before_network(tmp_path, duplicate):
    """Duplicate identity or URL cannot masquerade as two monitored sources."""
    path, _ = package(tmp_path)
    data = json.loads(path.read_bytes())
    data['targets'][1][duplicate] = data['targets'][0][duplicate]
    with pytest.raises(ValueError, match='distinct'):
        g.Plan.model_validate_json(json.dumps(data))


def test_distinct_budget_refuses_before_second_url(tmp_path):
    path, output = package(tmp_path, {'distinct_urls': 1})
    guard, calls = execute(path, output, [FakeResponse()])
    with pytest.raises(ValueError, match='Distinct URL budget'):
        guard.execute(NOW)
    assert len(calls) == 1


def test_redirect_hop_budget_reserved_per_hop(tmp_path):
    path, output = package(tmp_path, {'redirects_per_source': 1})
    responses = [FakeResponse(b'', 302, {'location': '/redirect1'}),
                 FakeResponse(b'', 302, {'location': '/redirect2'})]
    guard, calls = execute(path, output, responses)
    with pytest.raises(ValueError, match='hop budget'):
        guard.execute(NOW)
    assert len(calls) == 2
    assert [r.hop for r, _ in guard.ledger()] == [0, 1]


def test_redirect_request_budget(tmp_path):
    path, output = package(tmp_path, {'requests': 1})
    guard, calls = execute(path, output, [FakeResponse(b'', 302, {'location': '/redirect'})])
    with pytest.raises(ValueError, match='Request budget'):
        guard.execute(NOW)
    assert len(calls) == 1


@pytest.mark.parametrize('url', [
    'http://coloradosprings.gov/a', 'https://evil.example/a', 'https://u:p@coloradosprings.gov/a',
    'https://127.0.0.1/a', 'https://localhost/a', 'https://coloradosprings.gov:8443/a',
    'https://coloradosprings.gov/a#x', 'https://coloradosprings.gov/login',
    'https://coloradosprings.gov/%6cogin', 'https://coloradosprings.gov/a?access_token=secret',
    'https://coloradosprings.gov/a\\b', 'https://coloradosprings.gov/%0d%0aevil',
    'https://coloradosprings.gov/privacy', 'https://coloradosprings.gov/styles.css',
])
def test_unsafe_url_refused_before_network(url):
    with pytest.raises(ValueError):
        g.safe_url(url)


def test_unsafe_redirect_and_public_header_filter(tmp_path):
    path, output = package(tmp_path)
    guard, calls = execute(path, output, [FakeResponse(b'blocked', 302, {
        'location': 'https://u:secret@evil.example/', 'set-cookie': 'secret',
        'authorization': 'secret', 'www-authenticate': 'secret', 'content-type': 'text/html'
    })] + [FakeResponse() for _ in range(1)])
    guard.execute(NOW)
    res = guard.ledger()[0][1]
    assert res.outcome == 'refused_redirect' and res.redirect_url is None
    assert len(calls) == 2
    headers = json.loads((output / res.public_headers.path).read_bytes())
    assert headers == {'headers': {'content-type': 'text/html'}, 'rejected_fields': ['location'],
                       'request_url': 'https://coloradosprings.gov/0.pdf'}
    assert b'secret' not in (output / res.public_headers.path).read_bytes()


def test_redirect_cycle_not_refetched(tmp_path):
    path, output = package(tmp_path)
    guard, calls = execute(path, output, [FakeResponse(b'', 302, {'location': '/0.pdf'})])
    with pytest.raises(ValueError, match='cycle'):
        guard.execute(NOW)
    assert len(calls) == 1


def test_per_source_sizecap_retains_partial_without_probe(tmp_path):
    path, output = package(tmp_path, {'bytes_per_source': 5, 'total_bytes': 20})
    responses = [FakeResponse(b'1234567890') for _ in range(2)]
    originals = list(responses)
    guard, calls = execute(path, output, responses)
    state = guard.execute(NOW)
    assert state.charged_bytes == 10 and len(calls) == 2
    for res, result in guard.ledger():
        assert result.partial_body and result.outcome == 'byte_limit'
        assert (output / result.body.path).read_bytes() == b'12345'
    assert all(r.reads == [5] for r in originals)


def test_total_sizecap_stops_before_new_source(tmp_path):
    path, output = package(tmp_path, {'total_bytes': 8})
    guard, calls = execute(path, output, [FakeResponse(b'0123456789')])
    with pytest.raises(ValueError, match='Byte budget'):
        guard.execute(NOW)
    result = guard.ledger()[0][1]
    assert len(calls) == 1 and result.body.size_bytes == 8 and result.partial_body


def test_known_exact_length_cap_is_complete(tmp_path):
    path, output = package(tmp_path, {'bytes_per_source': 2})
    guard, _ = execute(path, output, [FakeResponse(b'ok') for _ in range(2)])
    guard.execute(NOW)
    assert all(not result.partial_body for _, result in guard.ledger())


def test_unknown_length_at_cap_is_conservatively_partial(tmp_path):
    path, output = package(tmp_path, {'bytes_per_source': 2})
    guard, _ = execute(path, output, [FakeResponse(b'ok', headers={}) for _ in range(2)])
    guard.execute(NOW)
    assert all(result.partial_body for _, result in guard.ledger())


def test_timeout_preserves_partial_bytes(tmp_path):
    path, output = package(tmp_path)
    guard, _ = execute(path, output, [FakeResponse(b'abcdef', timeout=True)] + [FakeResponse() for _ in range(1)])
    guard.execute(NOW)
    result = guard.ledger()[0][1]
    assert result.outcome == 'timeout' and result.partial_body and result.charged_bytes == 2
    assert (output / result.body.path).read_bytes() == b'ab'


def test_interruption_after_reservation_resume_does_not_retry(tmp_path):
    path, output = package(tmp_path, {'bytes_per_source': 5, 'total_bytes': 20})
    guard, calls = execute(path, output, [FakeResponse(b'abcdef', interrupt=True)])
    with pytest.raises(KeyboardInterrupt):
        guard.execute(NOW)
    assert len(calls) == 1 and guard.ledger()[0][1] is None
    next_calls = []
    resumed = g.Guard(path, output, clock=lambda: NOW, fetch=lambda u, d, c: next_calls.append(u) or FakeResponse(b'x'))
    state = resumed.execute(NOW)
    result = resumed.ledger()[0][1]
    assert result.outcome == 'interrupted' and result.charged_bytes == 5
    assert result.body.size_bytes == 2 and result.partial_body
    assert len(next_calls) == 1 and state.charged_bytes == 6
    assert 'https://coloradosprings.gov/0.pdf' not in next_calls


def test_interruption_before_body_still_consumes_reservation(tmp_path):
    path, output = package(tmp_path, {'bytes_per_source': 3, 'total_bytes': 20})
    guard, _ = execute(path, output, [KeyboardInterrupt()])
    with pytest.raises(KeyboardInterrupt):
        guard.execute(NOW)
    resumed = g.Guard(path, output, clock=lambda: NOW, fetch=lambda *args: FakeResponse())
    resumed.execute(NOW)
    result = resumed.ledger()[0][1]
    assert result.body.size_bytes == 0 and result.charged_bytes == 3


def test_plan_substitution_refused_before_fetch(tmp_path):
    path, output = package(tmp_path)
    guard, calls = execute(path, output, [FakeResponse() for _ in range(2)])
    guard.execute(NOW)
    data = json.loads(path.read_bytes());data['max_run_seconds'] = 299;path.write_text(json.dumps(data))
    changed = g.Guard(path, output, clock=lambda: NOW, fetch=lambda *args: pytest.fail('network attempted'))
    with pytest.raises(ValueError, match='substitution'):
        changed.execute(NOW)
    assert len(calls) == 2


def test_denial_stops_and_resume_does_not_continue(tmp_path):
    path, output = package(tmp_path)
    guard, calls = execute(path, output, [FakeResponse(b'denied', 403)])
    guard.execute(NOW);guard.execute(NOW)
    assert len(calls) == 1 and guard.ledger()[0][1].http_status == 403


def test_lock_prevents_second_process_transaction(tmp_path):
    path, output = package(tmp_path)
    first = g.Guard(path, output);second = g.Guard(path, output)
    with first.lock():
        with pytest.raises(BlockingIOError):
            with second.lock():
                pytest.fail('second lock acquired')


def test_expired_or_future_dispatch_no_request(tmp_path):
    path, output = package(tmp_path)
    guard = g.Guard(path, output, clock=lambda: NOW, fetch=lambda *args: pytest.fail('HTTP'))
    for dispatch in (NOW + timedelta(seconds=1), NOW - timedelta(minutes=31)):
        with pytest.raises(ValueError, match='dispatch'):
            guard.execute(dispatch)
    assert not list(output.glob('events/*'))


def test_partial_metadata_transaction_refuses_resume(tmp_path):
    path, output = package(tmp_path);output.mkdir();(output/'incomplete.tmp').write_text('{')
    guard = g.Guard(path, output, clock=lambda: NOW, fetch=lambda *args: pytest.fail('HTTP'))
    with pytest.raises(ValueError, match='Incomplete metadata'):
        guard.execute(NOW)






def test_nonpublic_dns_refused_before_connect(monkeypatch):
    monkeypatch.setattr(g.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=b'["127.0.0.1"]'))
    monkeypatch.setattr(g.socket,'create_connection',lambda *a,**k:pytest.fail('connected'))
    with pytest.raises(ValueError,match='Nonpublic'):
        g.transport('https://coloradosprings.gov/x.pdf',NOW+timedelta(seconds=30),lambda:NOW)




def test_source_and_result_tamper_refused(tmp_path):
    path,output=package(tmp_path);guard,_=execute(path,output,[FakeResponse() for _ in range(2)]);guard.execute(NOW)
    (output/'events/0001/body.bin').write_bytes(b'bad')
    with pytest.raises(ValueError,match='Evidence hash'):guard.execute(NOW)


def test_symlink_input_and_output_refused(tmp_path):
    path,output=package(tmp_path);link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(ValueError):g.Guard(link, output)
    output.symlink_to(path.parent,target_is_directory=True)
    with pytest.raises(ValueError):g.Guard(path,output).execute(NOW)


def test_production_transport_pins_public_ip_and_verifies_named_tls(monkeypatch):
    calls=[]
    class Sock:
        def settimeout(self,t):calls.append(('timeout',t))
        def close(self):calls.append(('socket-close',))
    sock=Sock()
    class HTTP:
        status=200
        def getheaders(self):return [('Content-Type','application/pdf'),('Set-Cookie','not-retained')]
        def isclosed(self):return False
        def read1(self,n):return b'%PDF-'[:n]
        def close(self):calls.append(('response-close',))
    class Conn:
        def __init__(self,host,**kwargs):self.sock=None;calls.append(('host',host,kwargs))
        def request(self,method,path,headers):calls.append(('request',method,path,headers))
        def getresponse(self):return HTTP()
        def close(self):calls.append(('connection-close',))
    class Context:
        def wrap_socket(self,raw,server_hostname):
            assert raw is sock;calls.append(('sni',server_hostname));return sock
    monkeypatch.setattr(g.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=b'["8.8.8.8"]'))
    monkeypatch.setattr(g.socket,'create_connection',lambda address,**kw:calls.append(('connect',address)) or sock)
    monkeypatch.setattr(g.ssl,'create_default_context',lambda **kw:calls.append(('tls-context',kw)) or Context())
    monkeypatch.setattr(g.http.client,'HTTPSConnection',Conn)
    response=g.transport('https://coloradosprings.gov/file.pdf?a=1',NOW+timedelta(seconds=30),lambda:NOW)
    assert response.read(3,2)==b'%PD';response.close()
    assert ('connect',('8.8.8.8',443)) in calls
    assert ('sni','coloradosprings.gov') in calls
    request=next(c for c in calls if c[0]=='request')
    assert request[1:3]==('GET','/file.pdf?a=1')
    assert not {'Authorization','Cookie'} & set(request[3])
    assert ('timeout',2) in calls


def test_production_tls_failure_closes_socket(monkeypatch):
    closed=[]
    class Sock:
        def settimeout(self,n):pass
        def close(self):closed.append(True)
    class Context:
        verify_mode = g.ssl.CERT_REQUIRED
        check_hostname = True
        def wrap_socket(self,*a,**k):raise g.ssl.SSLError('fixture')
    monkeypatch.setattr(g.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=b'["8.8.8.8"]'))
    monkeypatch.setattr(g.socket,'create_connection',lambda *a,**k:Sock())
    monkeypatch.setattr(g.ssl,'create_default_context',lambda **k:Context())
    with pytest.raises(g.ssl.SSLError):g.transport('https://coloradosprings.gov/a',NOW+timedelta(seconds=5),lambda:NOW)
    assert closed


def test_transport_expired_before_dns(monkeypatch):
    monkeypatch.setattr(g.subprocess,'run',lambda *a,**k:pytest.fail('DNS started'))
    with pytest.raises(TimeoutError):g.transport('https://coloradosprings.gov/a',NOW,lambda:NOW)


def test_duplicate_location_response_refused():
    response=SimpleNamespace(status=302,getheaders=lambda:[('Location','/a'),('Location','/b')])
    with pytest.raises(ValueError,match='Ambiguous'):g.Response(None,response,None)


def test_nonpublic_headers_and_control_values_refused():
    for headers in [{'set-cookie':'secret'},{'date':'a\r\nb'},{'location':'https://evil.example/'}]:
        with pytest.raises(ValueError):g.HeaderRecord(headers=headers)


def test_transport_failure_retains_empty_event(tmp_path):
    path,output=package(tmp_path);guard,_=execute(path,output,[RuntimeError('not exposed')]+[FakeResponse() for _ in range(1)])
    guard.execute(NOW);result=guard.ledger()[0][1]
    assert result.outcome=='transport_error' and result.error_type=='RuntimeError' and result.body.size_bytes==0






def test_invalid_plan_identity_time_and_ref():
    for value in ['/absolute','../escape','./alias']:
        with pytest.raises(ValueError):g.Ref(path=value,sha256='0'*64,size_bytes=0)






def test_unplanned_direct_reservation_refused(tmp_path):
    path,output=package(tmp_path);guard=g.Guard(path,output,clock=lambda:NOW)
    run=g.Run(plan_sha256=g.sha(path),dispatch_at=NOW,initialized_at=NOW,deadline=NOW+timedelta(minutes=30))
    with guard.lock():
        with pytest.raises(ValueError,match='Unplanned'):
            guard.reserve('SD014-01','https://coloradosprings.gov/not-planned.pdf',0,run)
    assert not list(output.glob('events/*'))


def test_request_without_committed_reservation_cannot_fetch(tmp_path):
    path,output=package(tmp_path);guard=g.Guard(path,output,clock=lambda:NOW,fetch=lambda *a:pytest.fail('HTTP'))
    res=g.Reservation(event=1,source_id='SD014-01',url='https://coloradosprings.gov/0.pdf',hop=0,
        plan_sha256=g.sha(path),reserved_at=NOW,deadline=NOW+timedelta(seconds=30),byte_allowance=100)
    with guard.lock():
        with pytest.raises(ValueError,match='durable reservation'):guard.request(res)


def test_reservation_expired_before_transport_is_recorded(tmp_path):
    path,output=package(tmp_path);clock=[NOW];guard=g.Guard(path,output,clock=lambda:clock[0],fetch=lambda *a:pytest.fail('HTTP'))
    run=g.Run(plan_sha256=g.sha(path),dispatch_at=NOW,initialized_at=NOW,deadline=NOW+timedelta(minutes=30))
    with guard.lock():
        res=guard.reserve('SD014-01','https://coloradosprings.gov/0.pdf',0,run)
        clock[0]=NOW+timedelta(seconds=31);result=guard.request(res)
    assert result.outcome=='hard_stop' and result.body.size_bytes==0


def test_default_one_redirect_stops_before_third_request(tmp_path):
    """A second redirect is recorded but its destination is never requested."""
    path, output = package(tmp_path)
    responses = [FakeResponse(b'', 302, {'location': f'/hop{n}'}) for n in range(1, 3)]
    instance, calls = execute(path, output, responses)
    with pytest.raises(ValueError, match='hop budget'):
        instance.execute(NOW)
    assert len(calls) == 2
    assert [r.hop for r, _ in instance.ledger()] == [0, 1]
    with pytest.raises(ValueError):
        g.Limits(redirects_per_source=2)


def test_short_content_length_is_preserved_as_partial(tmp_path):
    path, output = package(tmp_path)
    instance, calls = execute(path, output, [FakeResponse(b'%PDF-short', headers={
        'content-length': '100'})] + [FakeResponse() for _ in range(1)])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.partial_body and result.outcome == 'incomplete_body'
    assert result.body.size_bytes == 10 and result.charged_bytes == 10
    assert result.content_magic == 'pdf' and len(calls) == 2


def wire_response(wire):
    """Create real HTTPResponse framing using only a local AF_UNIX socket pair."""
    reader, writer = socket.socketpair()
    writer.sendall(wire)
    writer.close()
    response = http.client.HTTPResponse(reader)
    response.begin()
    wrapped = g.Response(SimpleNamespace(close=lambda: None), response, reader)
    reader.close()  # Same socket-owner close used for Connection: close responses.
    return wrapped


@pytest.mark.parametrize('headers,body,expected', [
    (b'Content-Length: 4\r\n', b'test', b'test'),
    (b'Content-Length: 0\r\n', b'', b''),
    (b'Content-Length: 8\r\n', b'test', b'test'),
    (b'Transfer-Encoding: chunked\r\n', b'4\r\nWiki\r\n5\r\npedia\r\n0\r\n\r\n', b'Wikipedia'),
    (b'Transfer-Encoding: chunked\r\n', b'0\r\n\r\n', b''),
    (b'', b'eof-delimited', b'eof-delimited'),
])
def test_real_framing_never_sets_timeout_on_closed_response(headers, body, expected):
    wrapped = wire_response(b'HTTP/1.1 200 OK\r\nConnection: close\r\n' + headers + b'\r\n' + body)
    pieces = []
    while True:
        piece = wrapped.read(65536, 1)
        if not piece:
            break
        pieces.append(piece)
    assert b''.join(pieces) == expected
    assert wrapped.response.isclosed() and wrapped.socket.fileno() == -1
    assert wrapped.read(65536, 1) == b''  # A second EOF read must also be harmless.
    wrapped.close()


@pytest.mark.parametrize('headers,body,outcome,partial,retained', [
    (b'Content-Length: 4\r\n', b'test', 'complete', False, b'test'),
    (b'Content-Length: 0\r\n', b'', 'complete', False, b''),
    (b'Content-Length: 8\r\n', b'test', 'incomplete_body', True, b'test'),
    (b'Transfer-Encoding: chunked\r\n', b'4\r\nWiki\r\n0\r\n\r\n', 'complete', False, b'Wiki'),
    (b'Transfer-Encoding: chunked\r\n', b'4\r\nWiki\r\n', 'transport_error', True, b'Wiki'),
    (b'', b'eof-delimited', 'complete', False, b'eof-delimited'),
])
def test_real_framing_full_guard_accounting(tmp_path, headers, body, outcome, partial, retained):
    path, output = package(tmp_path)
    response = wire_response(b'HTTP/1.1 200 OK\r\nConnection: close\r\n' + headers + b'\r\n' + body)
    instance, calls = execute(path, output, [response, FakeResponse()])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.outcome == outcome and result.partial_body is partial
    assert result.charged_bytes == len(retained)
    assert (output / result.body.path).read_bytes() == retained
    instance.execute(NOW)
    assert len(calls) == 2  # Neither successful nor partial sources are retried.


def test_real_response_cap_and_safe_location_preserved_without_following(tmp_path):
    path, output = package(tmp_path, {'bytes_per_source': 3})
    response = wire_response(b'HTTP/1.1 302 Found\r\nConnection: close\r\n'
                             b'Content-Length: 9\r\nLocation: /safe.pdf\r\n\r\nabcdefghi')
    instance, calls = execute(path, output, [response, FakeResponse()])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.outcome == 'byte_limit' and result.partial_body
    assert result.redirect_url is None and result.charged_bytes == 3
    record = g.HeaderRecord.model_validate_json((output / result.public_headers.path).read_bytes())
    assert record.headers['location'] == '/safe.pdf'
    assert record.request_url == 'https://coloradosprings.gov/0.pdf'
    assert len(calls) == 2 and 'https://coloradosprings.gov/safe.pdf' not in calls


def test_safe_routing_header_is_durable_before_interrupted_body(tmp_path):
    path, output = package(tmp_path)
    response = FakeResponse(b'abcdef', 302, {'location': '/safe.pdf'}, interrupt=True)
    instance, _ = execute(path, output, [response])
    with pytest.raises(KeyboardInterrupt):
        instance.execute(NOW)
    saved = g.HeaderRecord.model_validate_json(
        (output / 'events/0001/public-headers.json').read_bytes())
    assert saved.headers['location'] == '/safe.pdf'
    assert saved.request_url == 'https://coloradosprings.gov/0.pdf'
    assert (output / 'events/0001/body.bin').read_bytes() == b'ab'
    resumed = g.Guard(path, output, clock=lambda: NOW, fetch=lambda *a: FakeResponse())
    resumed.execute(NOW)
    result = resumed.ledger()[0][1]
    assert result.outcome == 'interrupted' and result.redirect_url is None
    assert result.charged_bytes == 2_000_000


def test_unsafe_routing_value_is_rejected_even_when_body_is_partial(tmp_path):
    path, output = package(tmp_path)
    response = FakeResponse(b'abcd', 302, {'location': 'https://u:secret@evil.example/'}, timeout=True)
    instance, calls = execute(path, output, [response, FakeResponse()])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    saved = (output / result.public_headers.path).read_bytes()
    assert result.partial_body and result.redirect_url is None and b'secret' not in saved
    assert json.loads(saved) == {'headers': {}, 'rejected_fields': ['location'],
                                'request_url': 'https://coloradosprings.gov/0.pdf'}
    assert len(calls) == 2


@pytest.mark.parametrize('code', [401, 403, 407])
def test_real_denial_stops_entire_run_and_resume(tmp_path, code):
    path, output = package(tmp_path)
    response = wire_response(f'HTTP/1.1 {code} Denied\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'.encode())
    instance, calls = execute(path, output, [response])
    instance.execute(NOW)
    instance.execute(NOW)
    assert len(calls) == 1 and instance.ledger()[0][1].http_status == code


def test_real_redirect_reserved_before_request_and_header_retained(tmp_path):
    path, output = package(tmp_path)
    response = wire_response(b'HTTP/1.1 301 Moved\r\nContent-Length: 0\r\n'
                             b'Connection: close\r\nLocation: /safe.pdf\r\n\r\n')
    instance, calls = execute(path, output, [response, FakeResponse(b'%PDF-test'), FakeResponse()])
    state = instance.execute(NOW)
    assert state.request_count == 3
    assert calls[1] == 'https://coloradosprings.gov/safe.pdf'
    first = instance.ledger()[0][1]
    assert first.outcome == 'redirect' and first.redirect_url == calls[1]
    assert not first.partial_body


def test_two_target_four_request_and_four_mb_hard_maxima(tmp_path):
    """Selection cannot silently expand its reviewed resource budgets."""
    path, _ = package(tmp_path)
    plan = g.Plan.model_validate_json(path.read_bytes())
    assert plan.limits.requests == 4
    assert plan.limits.total_bytes == 4_000_000
    for narrowed in ({'requests': 5}, {'distinct_urls': 5}, {'total_bytes': 4_000_001},
                     {'bytes_per_source': 2_000_001}, {'request_seconds': 31}):
        with pytest.raises(ValueError):
            g.Limits(**narrowed)
    data = json.loads(path.read_bytes())
    data['targets'].append(data['targets'][0])
    with pytest.raises(ValueError):
        g.Plan.model_validate_json(json.dumps(data))


def test_header_rejection_state_cannot_contradict_saved_value():
    for headers, rejected in [({'date': 'x'}, ['date']), ({}, ['location', 'location'])]:
        with pytest.raises(ValueError, match='Contradictory'):
            g.HeaderRecord(headers=headers, rejected_fields=rejected)






def test_allowed_host_change_is_not_followed(tmp_path):
    """An allowed www host still differs from the selected source's exact host."""
    path, output = package(tmp_path)
    instance, calls = execute(path, output, [FakeResponse(b'', 302, {
        'location': 'https://www.coloradosprings.gov/moved.pdf'})])
    with pytest.raises(ValueError, match='Unplanned'):
        instance.execute(NOW)
    assert calls == ['https://coloradosprings.gov/0.pdf']
    assert len(instance.ledger()) == 1


def test_elapsed_run_deadline_stops_second_source(tmp_path):
    """Completion of the first source cannot give the next source a fresh run budget."""
    path, output = package(tmp_path)
    clock = [NOW]
    calls = []

    class LastSecondResponse(FakeResponse):
        def close(self):
            super().close()
            clock[0] = NOW + timedelta(seconds=300)

    def fetch(url, deadline, now):
        calls.append(url)
        return LastSecondResponse()

    instance = g.Guard(path, output, clock=lambda: clock[0], fetch=fetch)
    with pytest.raises(ValueError, match='Deadline'):
        instance.execute(NOW)
    assert len(calls) == 1
    assert instance.ledger()[0][1].outcome == 'timeout'
    assert instance.ledger()[0][1].partial_body
    assert not (output / 'events/0002').exists()


def test_plan_changed_between_reservation_and_transport_is_refused(tmp_path):
    """The immutable plan digest is checked again immediately before transport."""
    path, output = package(tmp_path)
    instance = g.Guard(path, output, clock=lambda: NOW,
                       fetch=lambda *args: pytest.fail('network attempted'))
    run = g.Run(plan_sha256=g.sha(path), dispatch_at=NOW, initialized_at=NOW,
                deadline=NOW + timedelta(seconds=300))
    with instance.lock():
        reservation = instance.reserve('SD014-01', 'https://coloradosprings.gov/0.pdf', 0, run)
        path.write_bytes(path.read_bytes() + b'\n')
        with pytest.raises(ValueError, match='Plan changed before transport'):
            instance.request(reservation)
    assert not (output / 'events/0001/body.bin').exists()


def test_stalled_body_read_retains_bytes_and_classifies_timeout(tmp_path):
    """An elapsed request deadline does not turn a partial body into an unchanged PDF."""
    path, output = package(tmp_path)
    clock = [NOW]

    class StalledResponse(FakeResponse):
        def read(self, count, timeout):
            clock[0] = NOW + timedelta(seconds=31)
            return b'ab'

    responses = [StalledResponse(b'abcdef'), FakeResponse()]
    instance, calls = execute(path, output, responses, clock=lambda: clock[0])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.outcome == 'timeout' and result.partial_body
    assert result.charged_bytes == 2 and result.error_type == 'timeout'
    assert (output / result.body.path).read_bytes() == b'ab'
    assert len(calls) == 2


@pytest.mark.parametrize('field,value,message', [
    ('event', 2, 'sequence'),
    ('source_id', 'unknown', 'Unplanned'),
    ('url', 'https://coloradosprings.gov/other.pdf', 'Unplanned'),
])
def test_tampered_initial_reservation_refused(tmp_path, field, value, message):
    """A saved reservation must still refer to its original selected request."""
    path, output = package(tmp_path)
    instance, _ = execute(path, output, [FakeResponse(), FakeResponse()])
    instance.execute(NOW)
    saved = output / 'events/0001/reservation.json'
    data = json.loads(saved.read_bytes())
    data[field] = value
    saved.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=message):
        instance.ledger()


def test_tampered_result_reservation_binding_refused(tmp_path):
    """A validly shaped result cannot claim another reserved event."""
    path, output = package(tmp_path)
    instance, _ = execute(path, output, [FakeResponse(), FakeResponse()])
    instance.execute(NOW)
    saved = output / 'events/0001/result.json'
    data = json.loads(saved.read_bytes())
    data['reservation_sha256'] = '0' * 64
    saved.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Result reservation binding'):
        instance.ledger()


def test_overlong_transport_chunk_is_not_written(tmp_path):
    """A faulty injected transport cannot write beyond the pre-reserved byte capacity."""
    path, output = package(tmp_path, {'bytes_per_source': 2})

    class OversizedResponse(FakeResponse):
        def read(self, count, timeout):
            return b'not bounded'

    instance, _ = execute(path, output, [OversizedResponse(), FakeResponse()])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.outcome == 'transport_error' and result.error_type == 'ValueError'
    assert result.body.size_bytes == 0 and result.partial_body


def test_elapsed_dns_deadline_prevents_connection(monkeypatch):
    """DNS consuming the remaining deadline must prevent a new socket connection."""
    clock = [NOW]

    def resolve(*args, **kwargs):
        clock[0] = NOW + timedelta(seconds=30)
        return SimpleNamespace(stdout=b'["8.8.8.8"]')

    monkeypatch.setattr(g.subprocess, 'run', resolve)
    monkeypatch.setattr(g.socket, 'create_connection', lambda *a, **k: pytest.fail('connected'))
    with pytest.raises(TimeoutError, match='Deadline'):
        g.transport('https://coloradosprings.gov/a.pdf', NOW + timedelta(seconds=30),
                    lambda: clock[0])


def test_real_conflicting_length_rules_refused_before_body_read(tmp_path):
    """Chunked bytes cannot use a shorter Content-Length to masquerade as complete."""
    path, output = package(tmp_path, {'bytes_per_source': 4})
    calls = []
    wire = (b'HTTP/1.1 200 OK\r\nConnection: close\r\nTransfer-Encoding: chunked\r\n'
            b'Content-Length: 4\r\n\r\n8\r\nabcdefgh\r\n0\r\n\r\n')

    def fetch(url, deadline, now):
        calls.append(url)
        if len(calls) == 1:
            return wire_response(wire)
        return FakeResponse()

    instance = g.Guard(path, output, clock=lambda: NOW, fetch=fetch)
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.outcome == 'transport_error' and result.error_type == 'ValueError'
    assert result.partial_body and result.body.size_bytes == 0
    assert result.content_magic == 'empty'
    instance.execute(NOW)
    assert len(calls) == 2


def test_injected_conflicting_length_rules_are_also_refused(tmp_path):
    """Custom transports must honor the same framing boundary as the real transport."""
    path, output = package(tmp_path, {'bytes_per_source': 4})
    response = FakeResponse(b'abcdefgh', headers={
        'transfer-encoding': 'chunked', 'content-length': '4'})
    instance, calls = execute(path, output, [response, FakeResponse()])
    instance.execute(NOW)
    result = instance.ledger()[0][1]
    assert result.outcome == 'transport_error' and result.partial_body
    assert result.body.size_bytes == 0 and response.reads == [] and response.closed
    assert len(calls) == 2
