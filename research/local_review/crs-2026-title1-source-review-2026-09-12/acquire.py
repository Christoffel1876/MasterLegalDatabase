"""Acquire one explicitly observed official source with bounded ordinary HTTPS."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parent


class Ref(BaseModel):
    """An exact retained byte identity."""
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    sha256: str
    size_bytes: int


class Receipt(BaseModel):
    """Actual HTTP evidence with cookie-free public header derivatives."""
    model_config = ConfigDict(extra="forbid", strict=True)
    event_id: str
    method: Literal["GET"] = "GET"
    requested_url: str
    observed_response_url: str | None
    redirect_location: str | None
    started_at: str
    completed_at: str
    curl_exit: int
    http_status: int | None
    content_type: str | None
    tls_verification_result: int | None
    body: Ref
    headers_derivative: Ref
    header_original_sha256: str
    header_original_size_bytes: int
    redacted_header_lines: int
    original_headers_retained: Literal[False] = False
    curl_metadata: Ref
    stderr: Ref
    response_complete: bool
    automatic_redirects: Literal[False] = False
    qualification: str


def reference(path: Path) -> Ref:
    """Bind retained bytes without guessing their MIME role."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
               size_bytes=len(data))


def run(event_id: str, url: str) -> None:
    """Perform one bounded request; never automatically retry or redirect."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {"olls.info", "content.leg.colorado.gov"}:
        raise ValueError("Only observed official referral hosts are permitted")
    receipts = list((ROOT / "events").glob("E*.json")) if (ROOT / "events").exists() else []
    rows = [Receipt.model_validate_json(p.read_text()) for p in receipts]
    if len(rows) >= 8 or len({r.requested_url for r in rows} | {url}) > 4:
        raise ValueError("Action/target limit")
    remaining = 40_000_000 - sum(r.body.size_bytes for r in rows)
    if remaining <= 0:
        raise ValueError("Byte limit")
    folder = ROOT / "events" / event_id
    folder.mkdir(parents=True, exist_ok=False)
    began = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(
        ["curl", "--proto", "=https", "--connect-timeout", "15", "--max-time", "55",
         "--max-redirs", "0", "--max-filesize", str(min(remaining, 25_000_000)),
         "--silent", "--show-error", "--output", str(folder / "body.bin"),
         "--dump-header", str(folder / "private-headers.tmp"), "--write-out", "%{json}", url],
        capture_output=True, timeout=60,
    )
    ended = datetime.now(timezone.utc).isoformat()
    (folder / "curl.json").write_bytes(result.stdout)
    (folder / "stderr.txt").write_bytes(result.stderr)
    if not (folder / "body.bin").exists():
        (folder / "body.bin").write_bytes(b"")
    original = (folder / "private-headers.tmp").read_bytes()
    lines = original.splitlines(keepends=True)
    count = 0
    public = []
    for line in lines:
        name = line.split(b":", 1)[0].lower()
        if name in {b"set-cookie", b"cookie", b"authorization", b"proxy-authorization"}:
            count += 1
            public.append(name + b": [REDACTED]\r\n")
        else:
            public.append(line)
    (folder / "headers.redacted.txt").write_bytes(b"".join(public))
    (folder / "private-headers.tmp").unlink()
    meta = json.loads(result.stdout)
    status = meta.get("http_code") or None
    receipt = Receipt(
        event_id=event_id, requested_url=url,
        observed_response_url=meta.get("url_effective") if status else None,
        redirect_location=meta.get("redirect_url") or None, started_at=began, completed_at=ended,
        curl_exit=result.returncode, http_status=status, content_type=meta.get("content_type") or None,
        tls_verification_result=meta.get("ssl_verify_result") if status else None,
        body=reference(folder / "body.bin"), headers_derivative=reference(folder / "headers.redacted.txt"),
        header_original_sha256=hashlib.sha256(original).hexdigest(),
        header_original_size_bytes=len(original), redacted_header_lines=count,
        curl_metadata=reference(folder / "curl.json"), stderr=reference(folder / "stderr.txt"),
        response_complete=result.returncode == 0,
        qualification="Ordinary TLS curl; no impersonation, credentials, bypass or automatic retry. "
        "Header original hash binds bytes observed in memory; only redacted derivative retained. "
        "Response body is unchanged; acquisition does not establish current legal effect.",
    )
    (ROOT / "events" / f"{event_id}.json").write_text(receipt.model_dump_json(indent=2) + "\n")
    schema = ROOT / "Receipt.schema.json"
    if not schema.exists():
        schema.write_text(json.dumps(Receipt.model_json_schema(), indent=2) + "\n")
    sys.stdout.write(receipt.model_dump_json(indent=2) + "\n")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
