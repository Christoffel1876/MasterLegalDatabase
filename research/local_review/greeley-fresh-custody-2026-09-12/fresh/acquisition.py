"""Four exact public GETs, no redirects/retries; preserve a fresh Greeley custody check."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
import argparse
import json
import subprocess

from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field
import pymupdf

BASE = Path(__file__).resolve().parent
OLD = BASE.parents[1] / "handoffs/sherlock-source-discovery-008/20260911T184800Z"
PARENT = "https://greeleyco.gov/business/construction-and-growth/building-permits-and-inspections/"
HOST = "cogy-p-001.sitecorecontenthub.cloud"
IDS = ("SD008-06", "SD008-07", "SD008-08")
PUBLIC = {"content-type", "content-length", "last-modified", "date", "etag", "cache-control", "location"}


class ExactTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    url: str
    expected_historical_sha256: str | None
    historical_reference: str


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prepared_at: datetime
    targets: list[ExactTarget] = Field(min_length=4, max_length=4)
    max_requests: Literal[4] = 4
    max_redirects: Literal[0] = 0
    max_body_per_request: Literal[2097152] = 2097152
    per_request_seconds: Literal[25] = 25
    max_execution_seconds: Literal[180] = 180
    historical_claims_unmodified: Literal[True] = True


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    requested_url: str
    started_at: datetime
    finished_at: datetime
    returncode: int | None
    http_status: int | None
    effective_url: str | None
    source_body: str
    sha256: str
    size_bytes: int
    content_type: str | None
    headers: dict[str, str]
    error_text: str
    body_complete: bool
    historical_digest_match: bool | None
    pdf_pages: int | None
    legal_currentness: Literal["not_verified"] = "not_verified"


class Reservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requested_url: str
    started_at: datetime
    redirects_allowed: Literal[0] = 0
    byte_ceiling: Literal[2097152] = 2097152
    request_seconds: Literal[25] = 25


class Summary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    receipts: list[Receipt]
    public_requests: int = Field(ge=1, le=4)
    redirects_followed: Literal[0] = 0
    canonical_writes: Literal[0] = 0
    legal_currentness: Literal["not_verified"] = "not_verified"
    limitation: str


def save(path: Path, value: BaseModel | dict) -> None:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    with path.open("x") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def targets() -> list[ExactTarget]:
    data = json.loads((OLD / "priority_candidates_final.json").read_bytes())
    html = (OLD / "raw/greeley/building_permits_and_inspections.html").read_bytes()
    soup = BeautifulSoup(html, "html.parser")
    result = [ExactTarget(source_id="GREELEY-PARENT", url=PARENT,
                          expected_historical_sha256=sha256(html).hexdigest(),
                          historical_reference="Sherlock SD008-E031 final URL; retained HTML exact hash")]
    for sid in IDS:
        candidate = next(c for c in data["candidates"] if c["id"] == sid)
        url = candidate["requested_url"]
        split = urlsplit(url)
        assert split.scheme == "https" and split.netloc == HOST
        assert split.path.startswith("/api/public/content/") and not split.fragment
        assert len([a for a in soup.find_all("a", href=True) if a["href"] == url]) == 1
        result.append(ExactTarget(source_id=sid, url=url,
                                  expected_historical_sha256=candidate["sha256"],
                                  historical_reference="Exact SD008 candidate and retained parent href; historical acquisition remains unverified"))
    return result


def acquire(target: ExactTarget, out: Path) -> Receipt:
    folder = out / target.source_id
    folder.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc)
    save(folder / "reservation.json", Reservation(requested_url=target.url, started_at=started))
    body_path = folder / "body.bin"
    # Headers are captured only in memory; cookies/authentication headers are discarded.
    command = [
        "/usr/bin/curl", "--silent", "--show-error", "--proto", "=https",
        "--connect-timeout", "10", "--max-time", "25", "--max-filesize", "2097152",
        "--user-agent", "ProjectGeode/1.0 (official-source research)",
        "--dump-header", "-", "--output", str(body_path),
        "--write-out", "\nGEODE-META\n%{http_code}\n%{url_effective}\n",
        target.url,
    ]
    try:
        process = subprocess.run(command, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as exc:
        process = subprocess.CompletedProcess(command, None, exc.stdout or b"",
            b"Wrapper subprocess timeout after 30 seconds; curl exit code unavailable. "
            + (exc.stderr or b""))
    finished = datetime.now(timezone.utc)
    if not body_path.exists():
        body_path.write_bytes(b"")
    body = body_path.read_bytes()
    assert len(body) <= 2097152
    headers_raw, marker, tail = process.stdout.rpartition(b"\nGEODE-META\n")
    fields = tail.decode("utf-8", "replace").splitlines() if marker else []
    status = int(fields[0]) if fields and fields[0].isdigit() else None
    final = fields[1] if len(fields) > 1 else None
    headers = {}
    for line in headers_raw.decode("iso-8859-1").splitlines():
        if line.startswith("HTTP/"):
            headers = {}
        elif ":" in line:
            name, value = line.split(":", 1)
            if name.lower() in PUBLIC and len(value) < 4096:
                headers[name.lower()] = value.strip()
    complete = process.returncode == 0 and status == 200 and final == target.url
    if complete and "content-length" in headers:
        complete = headers["content-length"].isdigit() and int(headers["content-length"]) == len(body)
    pages = None
    structural_error = ""
    if complete and target.source_id in IDS:
        complete = body.startswith(b"%PDF-") and b"%%EOF" in body[-1024:]
        if complete:
            try:
                with pymupdf.open(stream=body, filetype="pdf") as doc:
                    complete = not doc.is_repaired and not doc.is_encrypted and len(doc) > 0
                    if complete:
                        pages = len(doc)
                        complete = all(not page.rect.is_empty for page in doc)
            except Exception as exc:
                complete = False
                pages = None
                structural_error = " PDF parse failed: " + type(exc).__name__
    elif complete:
        complete = b"</html>" in body.lower()
    receipt = Receipt(source_id=target.source_id, requested_url=target.url,
        started_at=started, finished_at=finished, returncode=process.returncode,
        http_status=status, effective_url=final, source_body="body.bin",
        sha256=sha256(body).hexdigest(), size_bytes=len(body), content_type=headers.get("content-type"),
        headers=headers, error_text=process.stderr.decode("utf-8", "replace")[:4096] + structural_error,
        body_complete=complete,
        historical_digest_match=(sha256(body).hexdigest() == target.expected_historical_sha256)
            if complete else None, pdf_pages=pages)
    save(folder / "receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = Plan(prepared_at=datetime.now(timezone.utc), targets=targets())
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output / "plan.json", plan)
    save(args.output / "plan.schema.json", Plan.model_json_schema())
    save(args.output / "receipt.schema.json", Receipt.model_json_schema())
    save(args.output / "reservation.schema.json", Reservation.model_json_schema())
    save(args.output / "summary.schema.json", Summary.model_json_schema())
    if not args.execute:
        print("Prepared four exact public GET targets; no network requests.")
        raise SystemExit(0)
    deadline = datetime.now(timezone.utc) + timedelta(seconds=180)
    results = []
    for target in plan.targets:
        assert datetime.now(timezone.utc) < deadline
        if target.source_id != "GREELEY-PARENT":
            assert results[0].body_complete, "Fresh official parent must succeed before CDN requests"
            soup = BeautifulSoup((args.output / "GREELEY-PARENT/body.bin").read_bytes(), "html.parser")
            assert len([a for a in soup.find_all("a", href=True) if a["href"] == target.url]) == 1
        results.append(acquire(target, args.output))
    save(args.output / "summary.json", Summary(receipts=results, public_requests=len(results),
        limitation="Fresh acquisition is independent; it does not rewrite or prove earlier Sherlock transport, adoption or legal applicability."))
    print(json.dumps({"sources": [{"id": r.source_id, "status": r.http_status,
        "complete": r.body_complete, "bytes": r.size_bytes, "same_historical_bytes": r.historical_digest_match}
        for r in results]}))
