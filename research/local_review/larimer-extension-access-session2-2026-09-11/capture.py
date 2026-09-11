"""Bounded ordinary HTTPS receipt capture; never follows redirects or retries."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

BASE = Path(__file__).resolve().parent
HOSTS = {"records.larimer.org", "www.larimer.gov", "larimercoco.portal.civicclerk.com"}

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

class Event(Strict):
    schema_version: Literal[1] = 1
    event_id: str
    requested_url: str
    basis: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    tool: Literal["curl_direct_https"] = "curl_direct_https"
    tls_verification: Literal["default_verified_no_override"] = "default_verified_no_override"
    redirects_followed: Literal[0] = 0
    retry_count: Literal[0] = 0
    curl_exit: int
    http_status: int | None
    final_url: str | None
    content_type: str | None
    outcome: Literal["publisher_http_response", "transport_failure_no_http_response"]
    assets: list[Asset]
    legal_currentness: Literal["not_verified"] = "not_verified"

def asset(path: Path) -> Asset:
    body = path.read_bytes()
    return Asset(path=path.relative_to(BASE).as_posix(),
                 sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_id")
    parser.add_argument("url")
    parser.add_argument("basis")
    args = parser.parse_args()
    u = urlsplit(args.url)
    if u.scheme != "https" or u.hostname not in HOSTS or u.username or u.password:
        raise ValueError("Only explicitly observed official public HTTPS hosts allowed")
    if datetime.now(timezone.utc).isoformat() >= "2026-09-11T21:30:00+00:00":
        raise ValueError("Public access deadline reached")
    existing = list((BASE / "events").glob("*/event.json"))
    if len(existing) >= 12:
        raise ValueError("Event cap reached")
    urls = {json.loads(p.read_text())["requested_url"] for p in existing}
    if args.url not in urls and len(urls) >= 8:
        raise ValueError("Distinct URL cap reached")
    folder = BASE / "events" / args.event_id
    folder.mkdir(parents=True, exist_ok=False)
    start = datetime.now(timezone.utc)
    result = subprocess.run([
        "curl", "--silent", "--show-error", "--connect-timeout", "15", "--max-time", "30",
        "--max-filesize", "20000000", "--proto", "=https", "--max-redirs", "0",
        "--output", str(folder / "body.bin"), "--dump-header", str(folder / "headers.txt"),
        "--write-out", "%{json}", args.url,
    ], capture_output=True, timeout=40)
    end = datetime.now(timezone.utc)
    (folder / "curl-metadata.json").write_bytes(result.stdout)
    (folder / "stderr.txt").write_bytes(result.stderr)
    meta = json.loads(result.stdout)
    code = int(meta.get("http_code", 0)) or None
    record = Event(
        event_id=args.event_id, requested_url=args.url, basis=args.basis,
        started_at=start, completed_at=end, curl_exit=result.returncode, http_status=code,
        final_url=meta.get("url_effective"), content_type=meta.get("content_type") or None,
        outcome="publisher_http_response" if code else "transport_failure_no_http_response",
        assets=[asset(p) for p in sorted(folder.iterdir())],
    )
    Event.model_validate_json(record.model_dump_json())
    (folder / "event.json").write_text(record.model_dump_json(indent=2)+"\n")
    print(record.model_dump_json())

if __name__ == "__main__":
    main()
