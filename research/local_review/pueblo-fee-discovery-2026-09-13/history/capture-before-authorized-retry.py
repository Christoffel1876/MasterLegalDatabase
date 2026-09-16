"""Finite public-only Pueblo source capture; ordinary verified TLS, no retries."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin, urlsplit

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).absolute().parent
DEADLINE = datetime(2026, 9, 13, 1, 5, tzinfo=timezone.utc)
HOSTS = {"www.pueblocounty.gov", "pueblocounty.gov", "county.pueblo.org",
         "www.pueblo.us", "pueblo.us"}
PUBLIC = {"content-type", "content-length", "content-encoding", "last-modified",
          "etag", "date", "location", "content-disposition"}


class Strict(BaseModel):
    """Reject undeclared evidence fields."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Bind immutable source bytes."""
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Event(Strict):
    """One request, including each redirect hop, is one counted public event."""
    event_id: str
    authority_id: Literal["CO-COUNTY-PUEBLO", "CO-MUNICIPAL-PUEBLO"]
    requested_url: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    http_status: int | None
    outcome: Literal["complete", "http_denied", "http_error", "transport_error", "partial"]
    body_complete: bool
    body: Ref
    public_headers: dict[str, str]
    redirect_to: str | None
    error_type: str | None
    tls_verified: bool | None
    transport_description: Literal["ordinary_TLS_GET_no_retry_no_cookie_or_auth"]


def save(path: Path, body: bytes) -> None:
    """Write once; never replace a previous capture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(body)


def now() -> datetime:
    """Return actual UTC time."""
    return datetime.now(timezone.utc)


def safe_url(url: str) -> str:
    """Limit destinations to the observed official authority hosts."""
    u = urlsplit(url)
    if (u.scheme != "https" or u.hostname not in HOSTS or u.username or u.password
            or u.port not in (None, 443) or u.fragment or "\\" in url
            or any(ord(c) <= 32 or ord(c) == 127 for c in url)):
        raise ValueError("Disallowed URL")
    return url


def load_transport():
    """Load the pinned unchanged prior ordinary-TLS transport with a new exact host scope."""
    path = HERE / "reference_transport.py"
    if hashlib.sha256(path.read_bytes()).hexdigest() != json.loads(
        (HERE / "TRANSPORT_PIN.json").read_bytes()
    )["sha256"]:
        raise ValueError("Transport bytes changed")
    spec = importlib.util.spec_from_file_location("pueblo_pinned_transport", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.HOSTS = HOSTS
    return module


def capture(url: str, authority: str) -> Event:
    """Capture one URL, bounded by the finite event, target, body and time budgets."""
    safe_url(url)
    old = [Event.model_validate_json(p.read_bytes()) for p in sorted(HERE.glob("events/*/event.json"))]
    reservations = sorted(HERE.glob("events/*/reservation.json"))
    if len(old) != len(reservations):
        raise ValueError("Unfinished prior reservation; no further requests")
    if len(old) >= 12 or len({x.requested_url for x in old} | {url}) > 10:
        raise ValueError("Event or distinct URL cap")
    if any(x.requested_url == url for x in old):
        raise ValueError("Repeated target is forbidden")
    if any(x.authority_id == authority and x.http_status in (401, 403) for x in old):
        raise ValueError("Authority denied access; stop this source")
    budget = min(5_000_000, 12_000_000 - sum(x.body.size_bytes for x in old))
    if budget <= 0 or now() >= DEADLINE:
        raise ValueError("Payload or deadline cap")
    event_id = f"E{len(old) + 1:03d}"
    folder = HERE / "events" / event_id
    start = now()
    deadline = min(DEADLINE, start + timedelta(seconds=30))
    save(folder / "reservation.json", json.dumps({
        "event_id": event_id, "requested_url": url, "authority_id": authority,
        "reserved_at": start.isoformat(), "request_deadline": deadline.isoformat(),
        "maximum_body_bytes": budget,
    }, indent=2).encode() + b"\n")
    chunks, status, headers, error, complete, response = [], None, {}, None, False, None
    try:
        response = load_transport().transport(url, deadline, now)
        status = response.status
        headers = {k: v for k, v in response.headers.items() if k in PUBLIC
                   and len(v) <= 4096 and not any(ord(c) < 32 for c in v)}
        size = 0
        while size < budget:
            remaining = (deadline - now()).total_seconds()
            if remaining <= 0:
                raise TimeoutError("Request deadline")
            chunk = response.read(min(65536, budget - size), remaining)
            if not chunk:
                complete = True
                break
            chunks.append(chunk)
            size += len(chunk)
        if "content-length" in headers and size != int(headers["content-length"]):
            complete = False
        if headers.get("content-encoding", "identity") not in ("", "identity"):
            complete = False
            error = "UnexpectedContentEncoding"
    except Exception as exc:
        error = type(exc).__name__
    finally:
        if response is not None:
            response.close()
    body = b"".join(chunks)
    save(folder / "body.bin", body)
    outcome = ("http_denied" if status in (401, 403) else "transport_error"
               if status is None else "partial" if not complete else "http_error"
               if status >= 400 else "complete")
    redirect = urljoin(url, headers["location"]) if status in (301, 302, 303, 307, 308) and (
        "location" in headers) else None
    record = Event(
        event_id=event_id, authority_id=authority, requested_url=url,
        started_at=start, completed_at=now(), http_status=status, outcome=outcome,
        body_complete=complete, body=Ref(path=f"events/{event_id}/body.bin",
        sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body)),
        public_headers=headers, redirect_to=redirect, error_type=error,
        tls_verified=True if status is not None else None,
        transport_description="ordinary_TLS_GET_no_retry_no_cookie_or_auth",
    )
    save(folder / "event.json", record.model_dump_json(indent=2).encode() + b"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--authority", required=True)
    args = parser.parse_args()
    result = capture(args.url, args.authority)
    sys.stdout.write(result.model_dump_json(indent=2) + "\n")
