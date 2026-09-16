"""Adapted bounded serial capture; no automatic redirects, retries or recursive crawl."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
HOSTS = {'www.douglas.co.us', 'www.douglasco.gov', 'publicnotices.douglas.co.us', 'www.crgov.com', 'ecode360.com', 'library.municode.com'}
STOP = datetime(2026, 9, 13, 0, 5, tzinfo=timezone.utc)
SENSITIVE = {b'set-cookie', b'cookie', b'authorization', b'proxy-authorization',
             b'www-authenticate', b'proxy-authenticate'}


class Strict(BaseModel):
    """Validate evidence before writes."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """An exact retained local file."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int = Field(ge=0)


class Reservation(Strict):
    """One budget slot reserved before any public request."""
    event_id: str
    url: str
    basis: str
    reserved_at: AwareDatetime
    maximum_seconds: int
    maximum_bytes: int


class Event(Strict):
    """An observed response or transport failure, never inferred HTTP success."""
    event_id: str
    requested_url: str
    basis: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    curl_exit: int
    http_status: int | None
    final_url: str | None
    content_type: str | None
    redirect_location: str | None
    body: Ref
    private_headers: Ref
    public_headers: Ref
    removed_header_names: list[str]
    metadata: Ref
    stderr: Ref
    outcome: str
    legal_currentness: str = 'not_verified'


class Link(Strict):
    """An exact discovered anchor, not an automatically opened target."""
    url: str
    label: str
    href: str


class Parsed(Strict):
    """Derived readable HTML text and observed anchors bound to the original."""
    event_id: str
    source: Ref
    encoding: str
    title: str
    text: str
    links: list[Link]


def sha(data: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(data).hexdigest()


def ref(path: Path) -> Ref:
    """Identify one retained local original or derivative."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(HERE).as_posix(), sha256=sha(data), bytes=len(data))


def write(path: Path, data: bytes) -> None:
    """Create new ordinary evidence atomically without overwriting."""
    assert not path.exists() and not path.is_symlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('xb') as handle:
        handle.write(data)
    tmp.replace(path)


def save(path: Path, model: Strict) -> None:
    """Preserve a schema-validated record."""
    write(path, model.model_dump_json(indent=2).encode() + b'\n')


def capture(url: str, basis: str) -> None:
    """Open exactly one verified-TLS official URL and retain its response."""
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname not in HOSTS or parts.username
            or parts.password or parts.port not in (None, 443) or parts.fragment):
        raise ValueError('Only exact authorized public HTTPS destinations')
    if any(ord(c) <= 32 for c in url) or '\\' in url:
        raise ValueError('Unsafe URL')
    reservations = sorted((HERE / 'events').glob('E*/reservation.json'))
    prior = [Reservation.model_validate_json(p.read_bytes()) for p in reservations]
    events = []
    for item, path in zip(prior, reservations):
        result = path.parent / 'event.json'
        if not result.exists():
            raise ValueError('Unresolved earlier attempt; stop rather than undercount')
        events.append(Event.model_validate_json(result.read_bytes()))
    if (len(prior) >= 50 or len({x.url for x in prior} | {url}) > 35
            or sum(x.body.bytes for x in events) >= 75_000_000):
        raise ValueError('Public budget exhausted')
    now = datetime.now(timezone.utc)
    if now >= STOP:
        raise ValueError('Public cutoff reached')
    repeated = [e for e in events if e.requested_url == url]
    if repeated and not (len(repeated) == 1 and repeated[0].curl_exit == 6):
        raise ValueError('No repeat except one documented DNS-route retry')
    number = len(prior) + 1
    directory = HERE / 'events' / f'E{number:03d}'
    directory.mkdir(parents=True)
    reservation = Reservation(event_id=f'E{number:03d}', url=url, basis=basis,
                              reserved_at=now, maximum_seconds=30, maximum_bytes=20_000_000)
    save(directory / 'reservation.json', reservation)
    result = subprocess.run([
        'curl', '-q', '--silent', '--show-error', '--proto', '=https', '--retry', '0',
        '--max-redirs', '0', '--connect-timeout', '10', '--max-time', '30',
        '--max-filesize', str(min(20_000_000, 75_000_000 - sum(e.body.bytes for e in events))),
        '--user-agent', 'Project Geode public-source research',
        '--dump-header', str(directory / 'private.headers'),
        '--output', str(directory / 'body.bin'),
        '--write-out', '%{http_code}\n%{url_effective}\n%{content_type}\n', url,
    ], capture_output=True, timeout=35)
    completed = datetime.now(timezone.utc)
    write(directory / 'curl-metadata.txt', result.stdout)
    write(directory / 'stderr.txt', result.stderr)
    for name in ['body.bin', 'private.headers']:
        if not (directory / name).exists():
            write(directory / name, b'')
    fields = result.stdout.decode('utf-8', errors='replace').splitlines()
    status = int(fields[0]) if fields and fields[0].isdigit() and int(fields[0]) else None
    final = fields[1] if len(fields) > 1 else None
    content = fields[2] if len(fields) > 2 else None
    headers = (directory / 'private.headers').read_bytes()
    kept, removed, dropping = [], set(), False
    location = None
    for line in headers.splitlines(keepends=True):
        if line.startswith((b' ', b'\t')):
            if not dropping:
                kept.append(line)
            continue
        key = line.split(b':', 1)[0].strip().lower()
        dropping = key in SENSITIVE
        if dropping:
            removed.add(key.decode('ascii'))
        else:
            kept.append(line)
        if key == b'location':
            location = urljoin(url, line.split(b':', 1)[1].strip().decode('latin-1'))
    write(directory / 'public.headers', b''.join(kept))
    event = Event(
        event_id=reservation.event_id, requested_url=url, basis=basis, started_at=now,
        completed_at=completed, curl_exit=result.returncode, http_status=status,
        final_url=final, content_type=content, redirect_location=location,
        body=ref(directory / 'body.bin'), private_headers=ref(directory / 'private.headers'),
        public_headers=ref(directory / 'public.headers'), removed_header_names=sorted(removed),
        metadata=ref(directory / 'curl-metadata.txt'), stderr=ref(directory / 'stderr.txt'),
        outcome='http_response' if status is not None else 'transport_failure',
    )
    save(directory / 'event.json', event)
    if status == 200 and result.returncode == 0 and 'html' in (content or ''):
        match = re.search(r'charset=([^;\s]+)', content or '', re.I)
        encoding = match[1] if match else 'utf-8'
        soup = BeautifulSoup((directory / 'body.bin').read_bytes().decode(encoding), 'html.parser')
        links = [Link(url=urljoin(final or url, a['href']), label=a.get_text(' ', strip=True),
                      href=a['href']) for a in soup.find_all('a', href=True)]
        title = soup.title.get_text(' ', strip=True) if soup.title else ''
        for item in soup(['script', 'style']):
            item.decompose()
        parsed = Parsed(event_id=event.event_id, source=event.body, encoding=encoding,
                        title=title, text=soup.get_text('\n', strip=True), links=links)
        save(directory / 'parsed.json', parsed)
    sys.stdout.write(json.dumps({
        'event_id': event.event_id, 'status': status, 'curl_exit': result.returncode,
        'bytes': event.body.bytes, 'sha256': event.body.sha256, 'content_type': content,
        'redirect': location,
    }) + '\n')


if __name__ == '__main__':
    capture(sys.argv[1], sys.argv[2])
