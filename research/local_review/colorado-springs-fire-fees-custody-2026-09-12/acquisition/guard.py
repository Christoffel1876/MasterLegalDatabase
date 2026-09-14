"""Finite serial exact-source downloader; validation is offline unless --execute is explicit."""
from __future__ import annotations

import argparse
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

from bs4 import BeautifulSoup
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

HOSTS = {'coloradosprings.gov', 'www.coloradosprings.gov'}
PUBLIC_HEADERS = {'content-type', 'content-length', 'date', 'last-modified', 'etag', 'cache-control'}
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


class PackageInventory(Strict):
    """Closed reviewed inputs, excluding only this inventory and later runtime outputs."""
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    files: list[Ref]
    exclusions: Literal['PACKAGE_INVENTORY.json and runtime/ only'] = (
        'PACKAGE_INVENTORY.json and runtime/ only'
    )

    @model_validator(mode='after')
    def unique(self) -> PackageInventory:
        """Reject ambiguous inventory members."""
        if len({item.path for item in self.files}) != len(self.files):
            raise ValueError('Duplicate package inventory path')
        return self


class PreparationReceipt(Strict):
    """Offline preparation and test results; no source acquisition or dispatch."""
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    plan: Ref
    guard: Ref
    tests: Ref
    test_log: Ref
    instructions: Ref
    parents: list[Ref]
    prior_audit: Ref
    test_exit_code: Literal[0] = 0
    tests_passed: int = Field(gt=0)
    coverage_percent: float = Field(ge=90, le=100)
    coverage_basis: Literal['statements_and_branches'] = 'statements_and_branches'
    test_method: Literal['offline injected HTTP, real socket-pair framing and mocked DNS/TLS; no public requests'] = (
        'offline injected HTTP, real socket-pair framing and mocked DNS/TLS; no public requests'
    )
    public_requests_made: Literal[0] = 0
    dispatch_at: None = None
    dispatch_receipt: None = None
    limitations: list[str]


class Target(Strict):
    """One exact PDF target corroborated by a retained iframe and its viewer argument."""
    source_id: str = Field(pattern=r'^SD014-0[1-2]$')
    parent_priority_id: str
    parent_url: str
    parent_html: Ref
    element: Literal['iframe_data_src_and_pdfjs_file']
    original_attribute: str
    viewer_src: str
    encoded_file_argument: str
    transformation: Literal['read data-src; percent-decode viewer file argument once; exact compare']
    iframe_title: str
    document_heading: str
    url: str


class Limits(Strict):
    """Hard maximums; tests or a revised reviewed plan may only narrow them."""
    requests: int = Field(default=6, ge=1, le=6)
    distinct_urls: int = Field(default=6, ge=1, le=6)
    redirects_per_source: int = Field(default=2, ge=0, le=2)
    bytes_per_source: int = Field(default=25_000_000, ge=1, le=25_000_000)
    total_bytes: int = Field(default=50_000_000, ge=1, le=50_000_000)
    request_seconds: int = Field(default=30, ge=1, le=30)


class Plan(Strict):
    """Exactly two proposed targets; preparation never dispatches them."""
    schema_version: Literal[1] = 1
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    targets: list[Target] = Field(min_length=2, max_length=2)
    limits: Limits = Field(default_factory=Limits)
    proposed_finish_by: AwareDatetime
    no_new_source_at: AwareDatetime
    hard_stop: AwareDatetime
    max_minutes_after_dispatch: Literal[30] = 30
    stop_after: Literal['SD014'] = 'SD014'
    qualifications: list[str]

    @model_validator(mode='after')
    def identities(self) -> Plan:
        """Prevent missing/duplicate IDs and unsafe initial destinations."""
        if {t.source_id for t in self.targets} != {f'SD014-0{i}' for i in range(1, 3)}:
            raise ValueError('Wrong target IDs')
        if (self.proposed_finish_by > datetime(2026, 9, 12, 23, 40, tzinfo=timezone.utc)
                or self.no_new_source_at > datetime(2026, 9, 13, 1, 25, tzinfo=timezone.utc)
                or self.hard_stop > datetime(2026, 9, 13, 1, 55, tzinfo=timezone.utc)):
            raise ValueError('Plan exceeds authorized time bounds')
        for target in self.targets:
            safe_url(target.url)
            safe_url(target.parent_url)
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
    event: int = Field(ge=1, le=6)
    source_id: str
    url: str
    hop: int = Field(ge=0, le=2)
    plan_sha256: str
    reserved_at: AwareDatetime
    deadline: AwareDatetime
    byte_allowance: int = Field(gt=0, le=25_000_000)


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
    byte_basis: Literal['retained response-body bytes; interrupted reservations charged at full allowance'] = (
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
    request_count: int = Field(ge=0, le=6)
    distinct_urls: list[str]
    charged_bytes: int = Field(ge=0, le=50_000_000)
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


def observed_url(target: Target, root: Path) -> str:
    """Bind the publisher iframe to its exactly once-decoded public PDF destination."""
    soup = BeautifulSoup(check_ref(root, target.parent_html).read_bytes(), 'html.parser')
    heads, bodies = soup.find_all('head'), soup.find_all('body')
    if len(heads) != 1 or len(bodies) != 1:
        raise ValueError('Expected one head and one body')
    headings = bodies[0].find_all('h1')
    if (len(headings) != 1 or ' '.join(headings[0].get_text(' ', strip=True).split())
            != target.document_heading):
        raise ValueError('Document heading differs')
    fields = bodies[0].select('div.field--name-field-media-document')
    if len(fields) != 1:
        raise ValueError('Expected one document media field')
    frames = fields[0].find_all('iframe')
    if len(frames) != 1 or 'pdf' not in frames[0].get('class', []):
        raise ValueError('Expected one document PDF iframe')
    frame = frames[0]
    if (frame.get('data-src') != target.original_attribute
            or frame.get('src') != target.viewer_src
            or frame.get('title') != target.iframe_title):
        raise ValueError('Observed iframe attributes differ')
    # These two observed publisher pages use exactly this relative pdf.js viewer.
    prefix = '/libraries/pdf.js/web/viewer.html?file='
    if not target.viewer_src.startswith(prefix):
        raise ValueError('Unapproved viewer route')
    encoded = target.viewer_src[len(prefix):]
    if (not encoded or any(c in encoded for c in '&+#?')
            or re.search(r'%(?![0-9a-fA-F]{2})', encoded)
            or encoded != target.encoded_file_argument):
        raise ValueError('Ambiguous or malformed viewer query')
    decoded_once = unquote(encoded, encoding='utf-8', errors='strict')
    if decoded_once != target.original_attribute or decoded_once != target.url:
        raise ValueError('Once-decoded viewer and data-src differ')
    if urlsplit(decoded_once).query or not urlsplit(decoded_once).path.endswith('.pdf'):
        raise ValueError('Expected an exact query-free PDF destination')
    return safe_url(decoded_once)


def load_plan(path: Path) -> Plan:
    """Validate both exact destinations against frozen observed parents, offline."""
    plan = Plan.model_validate_json(ordinary(path).read_bytes())
    for target in plan.targets:
        observed_url(target, path.parent)
    return plan


class Response:
    """No-redirect HTTP response backed by one verified TLS connection."""
    def __init__(self, connection, response, tls_socket):
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

    def read(self, count: int, timeout: float) -> bytes:
        """Read at most the remaining allowed body bytes within the deadline."""
        if self.response.isclosed():
            return b''
        self.socket.settimeout(timeout)
        return self.response.read1(count)

    def close(self) -> None:
        """Close both response and connection."""
        self.response.close()
        self.connection.close()


def transport(url: str, deadline: datetime, clock: Callable[[], datetime]) -> Response:
    """Resolve public IPs in a timed child, pin one address, verify TLS, and never redirect."""
    safe_url(url)
    u = urlsplit(url)
    remaining = (deadline - clock()).total_seconds()
    if remaining <= 0:
        raise TimeoutError('Deadline reached')
    script = 'import socket,json,sys;print(json.dumps(sorted({x[4][0] for x in socket.getaddrinfo(sys.argv[1],443,type=socket.SOCK_STREAM)})))'
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
    connection = http.client.HTTPSConnection(u.hostname, timeout=min(15, remaining), context=context)
    raw = socket.create_connection((addresses[0], 443), timeout=min(15, remaining))
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
        tls_socket.settimeout(min(15, (deadline - clock()).total_seconds()))
        return Response(connection, connection.getresponse(), tls_socket)
    except BaseException:
        connection.close()
        raw.close()
        raise


class Guard:
    """Single-process finite transaction: append-only reservation, response and resume."""
    def __init__(self, plan_path: Path, output: Path, clock=utcnow, fetch=transport):
        self.plan_path = plan_path
        self.plan = load_plan(plan_path)
        self.plan_sha = sha(plan_path)
        self.output = output
        self.clock = clock
        self.fetch = fetch
        self._lock_owner = None

    @contextlib.contextmanager
    def lock(self):
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

    def ledger(self):
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
            if prior and (prior[-1][1] is None or prior[-1][1].outcome != 'redirect'
                          or res.url != prior[-1][1].redirect_url or res.hop != prior[-1][0].hop + 1):
                raise ValueError('Unapproved redirect or repeated source')
            result_path = path.parent / 'result.json'
            result = Result.model_validate_json(ordinary(result_path).read_bytes()) if result_path.exists() else None
            if result:
                if result.reservation_sha256 != sha(path) or result.event != res.event:
                    raise ValueError('Result reservation binding differs')
                check_ref(self.output, result.body)
                check_ref(self.output, result.public_headers)
                if result.charged_bytes > res.byte_allowance or result.body.size_bytes > result.charged_bytes:
                    raise ValueError('Invalid byte accounting')
            events.append((res, result))
        return events

    def state(self, events) -> State:
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

    def finish(self, res: Reservation, outcome: str, status=None, partial=True,
               headers=None, redirect=None, error=None) -> Result:
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
        result = Result(event=res.event, reservation_sha256=sha(folder / 'reservation.json'),
                        finished_at=self.clock(), outcome=outcome, http_status=status,
                        body=file_ref(self.output, body), public_headers=file_ref(self.output, head),
                        partial_body=partial, content_magic=kind,
                        charged_bytes=res.byte_allowance if outcome == 'interrupted' else body.stat().st_size,
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
        if now >= run.deadline or (hop == 0 and now >= self.plan.no_new_source_at):
            raise ValueError('Deadline reached before request')
        if state.request_count >= self.plan.limits.requests:
            raise ValueError('Request budget exhausted before request')
        if url not in state.distinct_urls and len(state.distinct_urls) >= self.plan.limits.distinct_urls:
            raise ValueError('Distinct URL budget exhausted before request')
        if hop > self.plan.limits.redirects_per_source:
            raise ValueError('Redirect hop budget exhausted before request')
        prior_pairs = [(r, result) for r, result in events if r.source_id == source]
        prior = [r for r, _ in prior_pairs]
        target = next((t for t in self.plan.targets if t.source_id == source), None)
        if target is None or (not prior and (url != target.url or hop != 0)):
            raise ValueError('Unplanned initial URL refused before request')
        if prior_pairs and (prior_pairs[-1][1] is None
                            or prior_pairs[-1][1].outcome != 'redirect'
                            or prior_pairs[-1][1].redirect_url != url
                            or hop != prior_pairs[-1][0].hop + 1):
            raise ValueError('Unapproved follow-up refused before request')
        if any(r.url == url for r in prior):
            raise ValueError('Redirect cycle refused before request')
        allowance = min(self.plan.limits.total_bytes - state.charged_bytes,
                        self.plan.limits.bytes_per_source - state.source_charged_bytes.get(source, 0))
        if allowance <= 0:
            raise ValueError('Byte budget exhausted before request')
        res = Reservation(event=state.request_count + 1, source_id=source, url=url, hop=hop,
                          plan_sha256=self.plan_sha, reserved_at=now,
                          deadline=min(run.deadline, now + timedelta(seconds=self.plan.limits.request_seconds)),
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
            size = 0
            with body.open('xb') as stream:
                while size < res.byte_allowance:
                    seconds = (res.deadline - self.clock()).total_seconds()
                    if seconds <= 0:
                        raise TimeoutError('Request deadline')
                    chunk = response.read(min(65536, res.byte_allowance - size), min(15, seconds))
                    if not chunk:
                        partial = False
                        break
                    if len(chunk) > min(65536, res.byte_allowance - size):
                        raise ValueError('Transport exceeded requested read bound')
                    stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                    size += len(chunk)
                declared_length = response.headers.get('content-length')
                if declared_length is not None:
                    # A short or malformed declared body is incomplete, even if read1 returns EOF.
                    partial = partial or not declared_length.isdigit() or int(declared_length) != size
                if size == res.byte_allowance:
                    # Do not probe one extra byte. Only a known exact Content-Length proves EOF.
                    partial = declared_length != str(size)
            outcome = ('byte_limit' if size == res.byte_allowance else 'incomplete_body') if partial else (
                'complete' if 200 <= status < 300 else 'http_error')
            if status in REDIRECTS and not partial:
                if 'location' in headers:
                    outcome, redirect = 'redirect', safe_url(urljoin(res.url, headers['location']))
                else:
                    outcome, redirect = 'refused_redirect', None
        except (TimeoutError, socket.timeout, subprocess.TimeoutExpired):
            outcome, error = 'timeout', 'timeout'
        except Exception as exc:
            outcome, error = 'transport_error', type(exc).__name__
        finally:
            if response:
                response.close()
        return self.finish(res, outcome, status, partial, headers, redirect, error)

    def execute(self, dispatch_at: datetime) -> State:
        """Resume the same pinned plan; never retry a completed or interrupted source."""
        with self.lock():
            run_path = self.output / 'run.json'
            if run_path.exists():
                run = Run.model_validate_json(ordinary(run_path).read_bytes())
                if run.plan_sha256 != self.plan_sha or run.dispatch_at != dispatch_at:
                    raise ValueError('Run/dispatch/plan substitution refused')
            else:
                now = self.clock()
                deadline = min(dispatch_at + timedelta(minutes=30), self.plan.proposed_finish_by,
                               self.plan.hard_stop)
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
                        return self.state(self.ledger())  # Stop denials; no identity/route fallback.
                    if result.outcome != 'redirect':
                        break
                    url, hop = result.redirect_url, hop + 1
            return self.state(self.ledger())


def verify_frozen(root: Path) -> None:
    """Verify the published helper/plan/evidence inventory before any command."""
    data = PackageInventory.model_validate_json(ordinary(root / 'PACKAGE_INVENTORY.json').read_bytes())
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Symlink inside package/runtime')
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()
              and p.relative_to(root).parts[0] != 'runtime'
              and p.relative_to(root) != Path('PACKAGE_INVENTORY.json')}
    if actual != {item.path for item in data.files}:
        raise ValueError('Missing or unexpected frozen package file')
    for item in data.files:
        check_ref(root, item)


def main() -> None:
    """Default is offline validation; explicit execution requires the actual dispatch UTC."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--dispatch-at')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    verify_frozen(root)
    plan = load_plan(root / 'plan.json')
    if not args.execute:
        print(json.dumps({'status': 'PREPARED_NOT_DISPATCHED', 'targets': len(plan.targets),
                          'requests_made': 0, 'plan_sha256': sha(root / 'plan.json')}))
        return
    if not args.dispatch_at:
        parser.error('--execute requires actual --dispatch-at UTC')
    dispatch = datetime.fromisoformat(args.dispatch_at.replace('Z', '+00:00'))
    if dispatch.tzinfo is None:
        parser.error('Dispatch time must include UTC offset')
    try:
        state = Guard(root / 'plan.json', root / 'runtime').execute(dispatch)
        print(state.model_dump_json())
    except (ValueError, BlockingIOError) as exc:
        print(json.dumps({'status': 'stopped', 'reason': str(exc)}))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
