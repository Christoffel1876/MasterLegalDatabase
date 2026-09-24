"""Retrieve three observed AgendaSuite links with bounded, recorded public HTTP actions."""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent / "atlas-chain-downloads"
URLS = {
    "resolution-22-401": "https://www.agendasuite.org/iip/elpaso/file/getfile/33301",
    "resolution-25-291": "https://www.agendasuite.org/iip/elpaso/file/getfile/50986",
    "resolution-26-8": "https://www.agendasuite.org/iip/elpaso/file/getfile/52035",
}


class Receipt(BaseModel):
    """Actual transport observations, with catalog identity still awaiting PDF inspection."""

    model_config = ConfigDict(extra="forbid")
    requested_url: str
    started_at: str
    completed_at: str
    argv: list[str]
    returncode: int
    http_status: int | None
    content_type: str | None
    redirect_url: str | None
    body_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    body_size_bytes: int = Field(ge=0, le=10_000_000)
    pdf_pages: int | None
    scope: str


def now() -> str:
    """Return the actual host UTC timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> None:
    """Run one serial attempt per observed URL; do not follow redirects or retry."""
    ROOT.mkdir(exist_ok=False)
    for name, url in URLS.items():
        directory = ROOT / name
        directory.mkdir()
        body = directory / "response.bin"
        headers = directory / "headers.txt"
        argv = ["curl", "--silent", "--show-error", "--connect-timeout", "15",
                "--max-time", "45", "--max-filesize", "10000000", "--proto", "=https",
                "--dump-header", str(headers), "--output", str(body),
                "--write-out", "%{json}", url]
        started = now()
        result = subprocess.run(argv, capture_output=True, check=False)
        completed = now()
        (directory / "curl.stderr").write_bytes(result.stderr)
        (directory / "curl.stdout.json").write_bytes(result.stdout)
        details = json.loads(result.stdout) if result.stdout.strip() else {}
        payload = body.read_bytes() if body.exists() else b""
        if not body.exists():
            body.write_bytes(b"")
        pages = None
        if details.get("response_code") == 200 and payload.startswith(b"%PDF-"):
            pages = len(pymupdf.open(stream=payload, filetype="pdf"))
        record = Receipt(
            requested_url=url, started_at=started, completed_at=completed, argv=argv,
            returncode=result.returncode, http_status=details.get("response_code"),
            content_type=details.get("content_type"), redirect_url=details.get("redirect_url"),
            body_sha256=hashlib.sha256(payload).hexdigest(), body_size_bytes=len(payload),
            pdf_pages=pages,
            scope="Observed link from received Sherlock A019 catalog evidence. Actual Atlas "
                  "HTTP transport recorded here; PDF document role/currentness not yet verified.",
        )
        (directory / "RECEIPT.json").write_text(record.model_dump_json(indent=2) + "\n")
        logging.info("%s HTTP%s bytes=%s PDFpages=%s", name, record.http_status,
                     record.body_size_bytes, pages)
    (ROOT / "RECEIPT.schema.json").write_text(
        json.dumps(Receipt.model_json_schema(), indent=2) + "\n"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
