"""Version 2 bounded HTTP custody for six explicitly approved additional sources."""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Literal
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

# Version 1 remains unchanged for existing Springs saved-run replay.
# This transport policy is necessary, not sufficient: the adapter pins each exact URL.
HOSTS = {
    'files.arapahoeco.gov', 'www.weld.gov', 'www.gjcity.org', 'www.mesacounty.us',
    'cogy-p-001.sitecorecontenthub.cloud',
}
PUBLIC_HEADERS = {
    'content-type', 'content-length', 'date', 'last-modified', 'etag', 'cache-control'}
REDIRECTS = {301, 302, 303, 307, 308}


class Strict(BaseModel):
    """Reject extra fields and scalar coercions."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """Immutable confined local evidence identity."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> Ref:
        """Reject external and ambiguous file references."""
        p = Path(self.path)
        if p.is_absolute() or '..' in p.parts or str(p) != self.path:
            raise ValueError('Unconfined evidence path')
        return self


class Target(Strict):
    """One explicit HTTPS source; the caller separately binds its canonical custody."""
    source_id: str = Field(min_length=1, max_length=160)
    url: str


class Limits(Strict):
    """Hard maximums; tests or a revised reviewed plan may only narrow them."""
    requests: int = Field(default=4, ge=1, le=4)
    distinct_urls: int = Field(default=4, ge=1, le=4)
    redirects_per_source: int = Field(default=1, ge=0, le=1)
    bytes_per_source: int = Field(default=2_000_000, ge=1, le=2_000_000)
    total_bytes: int = Field(default=4_000_000, ge=1, le=4_000_000)
    request_seconds: int = Field(default=30, ge=1, le=30)


class Plan(Strict):
    """Two explicit targets and elapsed limits; no schedule or historical date wrapper."""
    targets: list[Target] = Field(min_length=2, max_length=2)
    limits: Limits = Field(default_factory=Limits)
    max_run_seconds: int = Field(default=300, ge=1, le=300)

    @model_validator(mode='after')
    def unique(self) -> Plan:
        """Refuse ambiguous identities and unsafe source destinations."""
        if len({t.source_id for t in self.targets}) != 2:
            raise ValueError('Two distinct source identities required')
        if len({t.url for t in self.targets}) != 2:
            raise ValueError('Two distinct source URLs required')
        for target in self.targets:
            safe_url(target.url)
        return self


class Run(Strict):
    """Immutable local execution receipt; dispatch time is supplied, not independently proved."""
    plan_sha256: str
    dispatch_at: AwareDatetime
    initialized_at: AwareDatetime
    deadline: AwareDatetime
    dispatch_time_basis: Literal['supplied_by_operator_not_independently_proved'] = (
        'supplied_by_operator_not_independently_proved'
    )


class Reservation(Strict):
    """Durable request and maximum body-byte capacity reserved before any HTTP attempt."""
    event: int = Field(ge=1, le=4)
    source_id: str
    url: str
    hop: int = Field(ge=0, le=1)
    plan_sha256: str
    reserved_at: AwareDatetime
    deadline: AwareDatetime
    byte_allowance: int = Field(gt=0, le=2_000_000)


class Result(Strict):
    """Immutable event result, including exact retained partial bytes and accounting."""
    event: int
    reservation_sha256: str
    finished_at: AwareDatetime
    outcome: Literal['complete', 'http_error', 'redirect', 'refused_redirect', 'byte_limit',
                     'incomplete_body', 'timeout', 'transport_error', 'interrupted', 'hard_stop']
    http_status: int | None
    body: Ref
    public_headers: Ref
    partial_body: bool
    content_magic: Literal['pdf', 'html', 'empty', 'other']
    charged_bytes: int = Field(ge=0)
    redirect_url: str | None
    error_type: str | None
    byte_basis: Literal[
        'retained response-body bytes; interrupted reservations charged at full allowance'] = (
        'retained response-body bytes; interrupted reservations charged at full allowance'
    )
    legal_currentness: Literal['not_verified'] = 'not_verified'

    @model_validator(mode='after')
    def accounting(self) -> Result:
        """Require retained bytes to be covered by the conservative charge."""
        if self.body.size_bytes > self.charged_bytes:
            raise ValueError('Retained body exceeds charged budget')
        return self


class HeaderRecord(Strict):
    """Only selected public response fields; no cookie/authentication values."""
    headers: dict[str, str]
    rejected_fields: list[str] = Field(default_factory=list)
    request_url: str | None = None

    @model_validator(mode='after')
    def public(self) -> HeaderRecord:
        """Reject unexpected fields, line folding and unsafe redirect destinations."""
        if (set(self.headers) | set(self.rejected_fields)) - (PUBLIC_HEADERS | {'location'}):
            raise ValueError('Nonpublic header refused')
        if (len(self.rejected_fields) != len(set(self.rejected_fields))
                or set(self.headers) & set(self.rejected_fields)):
            raise ValueError('Contradictory header retention state')
        for value in self.headers.values():
            if len(value) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise ValueError('Unsafe header value')
        if self.request_url is not None:
            safe_url(self.request_url)
        if 'location' in self.headers:
            safe_url(urljoin(self.request_url or '', self.headers['location']))
        return self


def capture_public_headers(raw: dict[str, str], requested_url: str) -> HeaderRecord:
    """Keep selected safe headers before body reads; unsafe values are never persisted."""
    headers, rejected = {}, []
    for key, value in raw.items():
        if key not in PUBLIC_HEADERS | {'location'}:
            continue
        try:
            if key == 'location':
                if not value or any(ord(c) <= 32 or ord(c) == 127 for c in value):
                    raise ValueError('Unsafe Location value')
                safe_url(urljoin(requested_url, value))
            HeaderRecord(headers={key: value}, request_url=requested_url)
            headers[key] = value
        except (ValueError, TypeError):
            rejected.append(key)
    return HeaderRecord(headers=headers, rejected_fields=sorted(set(rejected)),
                        request_url=requested_url)


class State(Strict):
    """Reconstructed validated accounting; immutable event files are authoritative."""
    request_count: int = Field(ge=0, le=4)
    distinct_urls: list[str]
    charged_bytes: int = Field(ge=0, le=4_000_000)
    source_charged_bytes: dict[str, int]


def utcnow() -> datetime:
    """Read actual UTC time."""
    return datetime.now(timezone.utc)


def safe_url(url: str) -> str:
    """Refuse credentials, auth routes, non-HTTPS, other hosts and ambiguous URL syntax."""
    if any(ord(c) <= 32 or ord(c) == 127 for c in url) or '\\' in url:
        raise ValueError('Unsafe URL syntax')
    u = urlsplit(url)
    if (u.scheme != 'https' or u.hostname not in HOSTS or u.username is not None
            or u.password is not None or u.port not in (None, 443) or u.fragment):
        raise ValueError('Disallowed URL destination')
    decoded = unquote(u.path)
    if any(ord(c) < 32 or ord(c) == 127 for c in decoded):
        raise ValueError('Encoded control character refused')
    path = decoded.lower().split('/')
    if (any(p in {'login', 'signin', 'oauth', 'authorize', 'sso', 'privacy', 'privacy-policy',
                  'privacy-statement', 'cookie-policy'} for p in path)
            or decoded.lower().endswith(('.css', '.js', '.ico', '.woff', '.woff2'))):
        raise ValueError('Authentication route refused')
    if {k.lower() for k in parse_qs(u.query)} & {
        'token', 'access_token', 'id_token', 'password', 'authorization', 'auth', 'signature'
    }:
        raise ValueError('Authentication query refused')
    return url


def ordinary(path: Path) -> Path:
    """Reject symlinks and nonordinary files."""
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise ValueError('Unsafe local file')
    return path


def sha(path: Path) -> str:
    """Compute a bounded-memory file hash."""
    with ordinary(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def file_ref(root: Path, path: Path) -> Ref:
    """Bind exact ordinary bytes under their local relative name."""
    return Ref(path=str(path.relative_to(root)), sha256=sha(path), size_bytes=path.stat().st_size)


def check_ref(root: Path, ref: Ref) -> Path:
    """Check a confined file before using it."""
    p = root / ref.path
    if file_ref(root, p) != ref:
        raise ValueError('Evidence hash/size differs')
    return p


def sync_dir(path: Path) -> None:
    """Durably commit a directory entry on supported local filesystems."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def immutable(path: Path, data: bytes) -> None:
    """Create bytes once, with no replacement of any existing target or partial temp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Unsafe output path')
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)  # Exclusive atomic publication: never replaces an existing event.
    temporary.unlink()
    sync_dir(path.parent)


def save_model(path: Path, record: Strict) -> None:
    """Validate a record before every durable state or receipt write."""
    body = (record.model_dump_json(indent=2) + '\n').encode()
    type(record).model_validate_json(body)
    immutable(path, body)


def interrupt_socket(sock: socket.socket) -> socket.socket:
    """Keep an independent descriptor able to stop a Connection: close response."""
    # Test doubles do not own OS descriptors. Real TLS sockets cannot use SSLSocket.dup().
    if not isinstance(sock, socket.socket):
        return sock
    return socket.socket(fileno=os.dup(sock.fileno()))


@contextlib.contextmanager
def socket_deadline(sock: socket.socket, seconds: float) -> Iterator[None]:
    """Bound a complete parser operation, including its internal repeated socket reads."""
    if seconds <= 0:
        raise TimeoutError('Socket operation deadline')
    expired = threading.Event()
    end = time.monotonic() + seconds

    def stop() -> None:
        """Interrupt this one socket when its absolute operation budget expires."""
        expired.set()
        with contextlib.suppress(OSError):
            sock.shutdown(socket.SHUT_RDWR)

    timer = threading.Timer(seconds, stop)
    timer.name = 'geode-watch-deadline'
    timer.daemon = True
    timer.start()
    try:
        try:
            yield
        except BaseException:
            if expired.is_set():
                raise TimeoutError('Socket operation deadline') from None
            raise
    finally:
        timer.cancel()
        timer.join()
    if expired.is_set() or time.monotonic() >= end:
        raise TimeoutError('Socket operation deadline')


class Response:
    """No-redirect HTTP response backed by one verified TLS connection."""
    def __init__(self, connection: http.client.HTTPSConnection,
                 response: http.client.HTTPResponse, tls_socket: socket.socket,
                 deadline_socket: socket.socket | None = None) -> None:
        """Capture one verified connection and its independent shutdown handle."""
        self.connection = connection
        self.response = response
        self.socket = tls_socket
        self.status = response.status
        self.headers = {}
        for key, value in response.getheaders():
            key = key.lower()
            if key in self.headers and key in {'location', 'content-length'}:
                raise ValueError('Ambiguous routing/framing headers')
            self.headers[key] = value
        validate_framing(self.headers)
        self.deadline_socket = (deadline_socket if deadline_socket is not None else
                                interrupt_socket(tls_socket))

    def read(self, count: int, timeout: float) -> bytes:
        """Read at most the remaining allowed body bytes within the deadline."""
        if self.response.isclosed():
            return b''
        with socket_deadline(self.deadline_socket, timeout):
            self.socket.settimeout(timeout)
            return self.response.read1(count)

    def close(self) -> None:
        """Close both response and connection."""
        try:
            self.response.close()
        finally:
            try:
                self.connection.close()
            finally:
                if self.deadline_socket is not self.socket:
                    self.deadline_socket.close()


def validate_framing(headers: dict[str, str]) -> None:
    """Reject competing HTTP length rules before a capped body can appear complete."""
    if 'transfer-encoding' in headers and 'content-length' in headers:
        raise ValueError('Ambiguous Transfer-Encoding and Content-Length')


def transport(url: str, deadline: datetime, clock: Callable[[], datetime]) -> Response:
    """Resolve public IPs in a timed child, pin one address, verify TLS, and never redirect."""
    safe_url(url)
    u = urlsplit(url)
    remaining = (deadline - clock()).total_seconds()
    if remaining <= 0:
        raise TimeoutError('Deadline reached')
    script = ('import socket,json,sys;print(json.dumps(sorted({x[4][0] for x in '
              'socket.getaddrinfo(sys.argv[1],443,type=socket.SOCK_STREAM)})))')
    result = subprocess.run([sys.executable, '-I', '-c', script, u.hostname],
                            capture_output=True, check=True, timeout=min(5, remaining))
    addresses = json.loads(result.stdout)
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError('Nonpublic DNS address refused')
    remaining = (deadline - clock()).total_seconds()
    if remaining <= 0:
        raise TimeoutError('Deadline reached')
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    connection = http.client.HTTPSConnection(
        u.hostname, timeout=min(15, remaining), context=context)
    raw = socket.create_connection((addresses[0], 443), timeout=min(15, remaining))
    deadline_socket = None
    try:
        raw.settimeout(max(0.001, min(15, (deadline - clock()).total_seconds())))
        connection.sock = context.wrap_socket(raw, server_hostname=u.hostname)
        if clock() >= deadline:
            raise TimeoutError('TLS deadline')
        connection.sock.settimeout(min(15, (deadline - clock()).total_seconds()))
        connection.request('GET', u.path + ('?' + u.query if u.query else ''), headers={
            'Host': u.hostname, 'User-Agent': 'ProjectGeode-SourceReview/1.0',
            'Accept': 'application/pdf,text/html;q=0.8,*/*;q=0.1', 'Accept-Encoding': 'identity',
            'Connection': 'close'})
        if clock() >= deadline:
            raise TimeoutError('Header deadline')
        tls_socket = connection.sock
        seconds = min(15, (deadline - clock()).total_seconds())
        tls_socket.settimeout(seconds)
        deadline_socket = interrupt_socket(tls_socket)
        with socket_deadline(deadline_socket, seconds):
            response = connection.getresponse()
        if clock() >= deadline:
            raise TimeoutError('Header deadline')
        return Response(connection, response, tls_socket, deadline_socket)
    except BaseException:
        connection.close()
        raw.close()
        if deadline_socket is not None and deadline_socket is not raw:
            deadline_socket.close()
        raise


class Guard:
    """Single-process finite transaction: append-only reservation, response and resume."""
    def __init__(self, plan_path: Path, output: Path,
                 clock: Callable[[], datetime] = utcnow,
                 fetch: Callable[..., Any] = transport, plan: Plan | None = None) -> None:
        """Bind one explicit selection and injectable clock/transport before reservation."""
        self.plan_path = plan_path
        self.plan = plan or Plan.model_validate_json(ordinary(plan_path).read_bytes())
        self.plan_sha = sha(plan_path)
        self.output = output
        self.clock = clock
        self.fetch = fetch
        self._lock_owner = None

    @contextlib.contextmanager
    def lock(self) -> Iterator[None]:
        """Hold the exclusive nonblocking OS lock for the whole execution/resume."""
        if self.output.is_symlink() or any(p.is_symlink() for p in self.output.parents):
            raise ValueError('Unsafe output root')
        self.output.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.output / '.guard.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_owner = os.getpid()
            yield
        finally:
            self._lock_owner = None
            os.close(fd)

    def ledger(self) -> list[tuple[Reservation, Result | None]]:
        """Reconstruct limits from immutable reservations, refusing tampering or gaps."""
        if list(self.output.rglob('*.tmp')):
            raise ValueError('Incomplete metadata transaction; manual review required')
        events = []
        for path in sorted(self.output.glob('events/*/reservation.json')):
            res = Reservation.model_validate_json(ordinary(path).read_bytes())
            if res.event != len(events) + 1 or path.parent.name != f'{res.event:04d}':
                raise ValueError('Reservation sequence changed')
            if res.plan_sha256 != self.plan_sha:
                raise ValueError('Plan substitution refused')
            safe_url(res.url)
            target = next((t for t in self.plan.targets if t.source_id == res.source_id), None)
            prior = [item for item in events if item[0].source_id == res.source_id]
            if target is None or (not prior and (res.url != target.url or res.hop != 0)):
                raise ValueError('Unplanned initial URL')
            if urlsplit(res.url).hostname != urlsplit(target.url).hostname:
                raise ValueError('Reservation changed the original source hostname')
            if res.hop > self.plan.limits.redirects_per_source:
                raise ValueError('Reservation exceeds the selected redirect limit')
            if prior and (prior[-1][1] is None or prior[-1][1].outcome != 'redirect'
                          or res.url != prior[-1][1].redirect_url
                          or res.hop != prior[-1][0].hop + 1):
                raise ValueError('Unapproved redirect or repeated source')
            result_path = path.parent / 'result.json'
            result = (Result.model_validate_json(ordinary(result_path).read_bytes())
                      if result_path.exists() else None)
            if result:
                if result.reservation_sha256 != sha(path) or result.event != res.event:
                    raise ValueError('Result reservation binding differs')
                check_ref(self.output, result.body)
                check_ref(self.output, result.public_headers)
                if (result.charged_bytes > res.byte_allowance or
                        result.body.size_bytes > result.charged_bytes):
                    raise ValueError('Invalid byte accounting')
            events.append((res, result))
        return events

    def state(self, events: list[tuple[Reservation, Result | None]]) -> State:
        """Charge an unfinished reservation fully until a durable result exists."""
        charges = {}
        for res, result in events:
            charges[res.source_id] = charges.get(res.source_id, 0) + (
                result.charged_bytes if result else res.byte_allowance)
        state = State(request_count=len(events), distinct_urls=sorted({r.url for r, _ in events}),
                      charged_bytes=sum(charges.values()), source_charged_bytes=charges)
        if (state.request_count > self.plan.limits.requests
                or len(state.distinct_urls) > self.plan.limits.distinct_urls
                or state.charged_bytes > self.plan.limits.total_bytes
                or any(n > self.plan.limits.bytes_per_source for n in charges.values())):
            raise ValueError('Ledger already exceeds plan budget')
        return state

    def finish(self, res: Reservation, outcome: str, status: int | None = None,
               partial: bool = True, headers: dict[str, str] | None = None,
               redirect: str | None = None, error: str | None = None) -> Result:
        """Persist sanitized headers and exact body evidence once, without replacing bytes."""
        folder = self.output / 'events' / f'{res.event:04d}'
        body = folder / 'body.bin'
        if not body.exists():
            immutable(body, b'')
        head = folder / 'public-headers.json'
        if not head.exists():
            save_model(head, HeaderRecord(headers=headers or {}))
        else:
            HeaderRecord.model_validate_json(ordinary(head).read_bytes())
        with ordinary(body).open('rb') as stream:
            magic = stream.read(512).lstrip()
        kind = 'pdf' if magic.startswith(b'%PDF-') else ('html' if b'<html' in magic.lower()
                or b'<!doctype html' in magic.lower() else ('empty' if not magic else 'other'))
        reservation_sha = sha(folder / 'reservation.json')
        body_ref = file_ref(self.output, body)
        headers_ref = file_ref(self.output, head)
        finished_at = self.clock()
        if outcome == 'complete' and finished_at >= res.deadline:
            outcome, partial, redirect = 'timeout', True, None
            error = 'deadline_during_result_finalization'
        result = Result(event=res.event, reservation_sha256=reservation_sha,
                        finished_at=finished_at, outcome=outcome, http_status=status,
                        body=body_ref, public_headers=headers_ref,
                        partial_body=partial, content_magic=kind,
                        charged_bytes=(res.byte_allowance if outcome == 'interrupted'
                                       else body.stat().st_size),
                        redirect_url=redirect, error_type=error)
        save_model(folder / 'result.json', result)
        return result

    def reserve(self, source: str, url: str, hop: int, run: Run) -> Reservation:
        """Enforce every budget and reserve durably before the transport is invoked."""
        if self._lock_owner != os.getpid():
            raise ValueError('Exclusive process lock required')
        if sha(self.plan_path) != self.plan_sha:
            raise ValueError('Plan changed during run')
        safe_url(url)
        events = self.ledger()
        state = self.state(events)
        now = self.clock()
        if now >= run.deadline:
            raise ValueError('Deadline reached before request')
        if state.request_count >= self.plan.limits.requests:
            raise ValueError('Request budget exhausted before request')
        if (url not in state.distinct_urls and
                len(state.distinct_urls) >= self.plan.limits.distinct_urls):
            raise ValueError('Distinct URL budget exhausted before request')
        if hop > self.plan.limits.redirects_per_source:
            raise ValueError('Redirect hop budget exhausted before request')
        prior_pairs = [(r, result) for r, result in events if r.source_id == source]
        prior = [r for r, _ in prior_pairs]
        target = next((t for t in self.plan.targets if t.source_id == source), None)
        if (target is None or urlsplit(url).hostname != urlsplit(target.url).hostname
                or (not prior and (url != target.url or hop != 0))):
            raise ValueError('Unplanned initial URL refused before request')
        if prior_pairs and (prior_pairs[-1][1] is None
                            or prior_pairs[-1][1].outcome != 'redirect'
                            or prior_pairs[-1][1].redirect_url != url
                            or hop != prior_pairs[-1][0].hop + 1):
            raise ValueError('Unapproved follow-up refused before request')
        if any(r.url == url for r in prior):
            raise ValueError('Redirect cycle refused before request')
        allowance = min(self.plan.limits.total_bytes - state.charged_bytes,
                        self.plan.limits.bytes_per_source
                        - state.source_charged_bytes.get(source, 0))
        if allowance <= 0:
            raise ValueError('Byte budget exhausted before request')
        res = Reservation(event=state.request_count + 1, source_id=source, url=url, hop=hop,
                          plan_sha256=self.plan_sha, reserved_at=now,
                          deadline=min(run.deadline, now + timedelta(
                              seconds=self.plan.limits.request_seconds)),
                          byte_allowance=allowance)
        save_model(self.output / 'events' / f'{res.event:04d}' / 'reservation.json', res)
        return res

    def request(self, res: Reservation) -> Result:
        """Make one request, retaining partial bytes while never following redirects itself."""
        if self._lock_owner != os.getpid():
            raise ValueError('Exclusive process lock required')
        if sha(self.plan_path) != self.plan_sha:
            raise ValueError('Plan changed before transport')
        ledger = self.ledger()
        if not ledger or ledger[-1] != (res, None):
            raise ValueError('No matching uncompleted durable reservation')
        self.state(ledger)
        if self.clock() >= res.deadline:
            return self.finish(res, 'hard_stop', error='deadline_before_transport')
        response = None
        status = None
        headers = {}
        partial = True
        outcome = 'transport_error'
        redirect = None
        error = None
        body = self.output / 'events' / f'{res.event:04d}' / 'body.bin'
        try:
            response = self.fetch(res.url, res.deadline, self.clock)
            status = response.status
            selected_headers = capture_public_headers(response.headers, res.url)
            headers = selected_headers.headers
            save_model(body.parent / 'public-headers.json', selected_headers)
            validate_framing(response.headers)
            size = 0
            with body.open('xb') as stream:
                while size < res.byte_allowance:
                    seconds = (res.deadline - self.clock()).total_seconds()
                    if seconds <= 0:
                        raise TimeoutError('Request deadline')
                    chunk = response.read(min(65536, res.byte_allowance - size), min(15, seconds))
                    if len(chunk) > min(65536, res.byte_allowance - size):
                        raise ValueError('Transport exceeded requested read bound')
                    if chunk:
                        stream.write(chunk)
                        stream.flush()
                        os.fsync(stream.fileno())
                        size += len(chunk)
                    if self.clock() >= res.deadline:
                        raise TimeoutError('Request deadline after read')
                    if not chunk:
                        partial = False
                        break
                declared_length = response.headers.get('content-length')
                if declared_length is not None:
                    # A short or malformed declared body is incomplete, even if read1 returns EOF.
                    partial = (partial or not declared_length.isdigit()
                               or int(declared_length) != size)
                if size == res.byte_allowance:
                    # Do not probe one extra byte. Only a known exact Content-Length proves EOF.
                    partial = declared_length != str(size)
            outcome = ('byte_limit' if size == res.byte_allowance else
                       'incomplete_body') if partial else (
                'complete' if 200 <= status < 300 else 'http_error')
            if status in REDIRECTS and not partial:
                if 'location' in headers:
                    outcome, redirect = 'redirect', safe_url(urljoin(res.url, headers['location']))
                else:
                    outcome, redirect = 'refused_redirect', None
        except (TimeoutError, socket.timeout, subprocess.TimeoutExpired):
            outcome, error, partial = 'timeout', 'timeout', True
        except Exception as exc:
            outcome, error = 'transport_error', type(exc).__name__
        finally:
            if response:
                response.close()
        if self.clock() >= res.deadline:
            outcome, error, partial, redirect = 'timeout', 'timeout', True, None
        return self.finish(res, outcome, status, partial, headers, redirect, error)

    def execute(self, dispatch_at: datetime) -> State:
        """Resume the same pinned plan; never retry a completed or interrupted source."""
        with self.lock():
            run_path = self.output / 'run.json'
            if run_path.exists():
                run = Run.model_validate_json(ordinary(run_path).read_bytes())
                if (run.plan_sha256 != self.plan_sha or run.dispatch_at != dispatch_at
                        or run.deadline != dispatch_at + timedelta(
                            seconds=self.plan.max_run_seconds)):
                    raise ValueError('Run/dispatch/plan substitution refused')
            else:
                now = self.clock()
                deadline = dispatch_at + timedelta(seconds=self.plan.max_run_seconds)
                if dispatch_at > now or now >= deadline:
                    raise ValueError('Invalid/expired dispatch time')
                run = Run(plan_sha256=self.plan_sha, dispatch_at=dispatch_at,
                          initialized_at=now, deadline=deadline)
                save_model(run_path, run)
            for res, result in self.ledger():
                if result is None:
                    self.finish(res, 'interrupted', error='prior_process_ended_without_result')
            if any(result and result.http_status in {401, 403, 407}
                   for _, result in self.ledger()):
                return self.state(self.ledger())
            for target in self.plan.targets:
                history = [pair for pair in self.ledger() if pair[0].source_id == target.source_id]
                if history and history[-1][1].outcome != 'redirect':
                    continue
                url = history[-1][1].redirect_url if history else target.url
                hop = history[-1][0].hop + 1 if history else 0
                while True:
                    res = self.reserve(target.source_id, url, hop, run)
                    result = self.request(res)
                    if result.http_status in {401, 403, 407}:
                        # Stop denials; no identity or route fallback.
                        return self.state(self.ledger())
                    if result.outcome != 'redirect':
                        break
                    url, hop = result.redirect_url, hop + 1
            return self.state(self.ledger())
