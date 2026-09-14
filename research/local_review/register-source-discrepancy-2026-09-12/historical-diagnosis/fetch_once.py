"""One authorized bounded official GET chain; never rerun this capture."""

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
URL = (
    "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026"
    "&Volume=49&yearPublishNumber=15&Month=8&Year=2026"
)


class Event(BaseModel):
    """One actual HTTP request or local transport failure."""

    model_config = ConfigDict(extra="forbid")
    number: int = Field(ge=1, le=3)
    requested_url: str
    started_at: datetime
    finished_at: datetime
    curl_exit: int
    http_status: int | None
    content_type: str | None
    location: str | None
    header_path: str
    header_sha256: str
    body_path: str
    body_sha256: str
    body_bytes: int = Field(ge=0, le=5_000_000)
    stderr_path: str
    sensitive_header_names: list[str]


class Capture(BaseModel):
    """Typed bounded network capture, without a legal-effect conclusion."""

    model_config = ConfigDict(extra="forbid")
    initial_url: str
    tls_verification: str = "curl default CA/hostname verification; no insecure flags"
    cookies_sent: bool = False
    retries: int = 0
    limits: str = "30 seconds total; 5 MB/body; at most 2 same-authority HTTPS redirects"
    status: str
    events: list[Event] = Field(min_length=1, max_length=3)


def main() -> None:
    """Capture exact output/header bytes, enforcing bounds before each redirect."""

    directory = HERE / "fresh"
    directory.mkdir(exist_ok=False)
    began = time.monotonic()
    url = URL
    events = []
    outcome = "not_completed"
    for number in range(1, 4):
        remaining = 30 - (time.monotonic() - began)
        if remaining <= 0:
            outcome = "total_time_limit"
            break
        headers = directory / f"event-{number:02d}.headers"
        body = directory / f"event-{number:02d}.body"
        errors = directory / f"event-{number:02d}.stderr"
        started = datetime.now(timezone.utc)
        command = ["/usr/bin/curl", "--silent", "--show-error", "--proto", "=https",
                   "--max-time", str(remaining), "--max-filesize", "5000000",
                   "--dump-header", str(headers), "--output", str(body), url]
        result = subprocess.run(command, capture_output=True, timeout=remaining + 1)
        finished = datetime.now(timezone.utc)
        errors.write_bytes(result.stderr)
        if not headers.exists():
            headers.write_bytes(b"")
        if not body.exists():
            body.write_bytes(b"")
        raw_headers = headers.read_bytes()
        fields = {}
        status = None
        for line in raw_headers.decode("iso-8859-1").splitlines():
            if line.startswith("HTTP/"):
                status = int(line.split()[1])
                fields = {}
            elif ":" in line:
                key, value = line.split(":", 1)
                fields[key.lower()] = value.strip()
        data = body.read_bytes()
        sensitive = sorted(set(fields) & {
            "set-cookie", "cookie", "authorization", "proxy-authorization",
            "www-authenticate", "proxy-authenticate",
        })
        events.append(Event(
            number=number, requested_url=url, started_at=started, finished_at=finished,
            curl_exit=result.returncode, http_status=status,
            content_type=fields.get("content-type"), location=fields.get("location"),
            header_path=headers.relative_to(HERE).as_posix(),
            header_sha256=hashlib.sha256(raw_headers).hexdigest(),
            body_path=body.relative_to(HERE).as_posix(),
            body_sha256=hashlib.sha256(data).hexdigest(), body_bytes=len(data),
            stderr_path=errors.relative_to(HERE).as_posix(), sensitive_header_names=sensitive,
        ))
        if result.returncode:
            outcome = "transport_or_local_error"
            break
        if status == 200:
            outcome = "http_200_received"
            break
        if status not in {301, 302, 303, 307, 308}:
            outcome = "http_denial_or_other_nonredirect"
            break
        candidate = urljoin(url, fields.get("location", ""))
        parsed = urlparse(candidate)
        if (not fields.get("location") or parsed.scheme != "https"
                or parsed.netloc != urlparse(URL).netloc or parsed.username is not None):
            outcome = "redirect_rejected"
            break
        if number == 3:
            outcome = "redirect_limit"
            break
        url = candidate
    capture = Capture(initial_url=URL, status=outcome, events=events)
    (HERE / "FETCH_RECEIPT.json").write_text(capture.model_dump_json(indent=2) + "\n")
    (HERE / "FETCH_RECEIPT.schema.json").write_text(
        json.dumps(Capture.model_json_schema(), indent=2) + "\n"
    )
    sys.stdout.write(capture.model_dump_json() + "\n")


if __name__ == "__main__":
    main()
