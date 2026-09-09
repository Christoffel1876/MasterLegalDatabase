"""Incremental, source-preserving Colorado Register refresh for review pull requests.

The pilot verifies complete issue tables in its configured date window. It never
rebuilds older corpus layers or treats a proposed rule as current regulation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import os
import re
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from geode.connectors.register_daily_parser import (
    DailyNoticeRow,
    decode_register_html,
    parse_edocket_detail,
    parse_register_index,
    parse_register_issue,
    register_html_fingerprint,
)
from geode.schemas.models import CrosswalkEntry, LayerIndexRecord, RulemakingNotice
from geode.utils.file_io import iter_jsonl

LOGGER = logging.getLogger(__name__)
LAYER = "04_Rulemaking"
INDEX = f"{LAYER}/_index.jsonl"
META = f"{LAYER}/_meta/rulemaking_notices_meta.jsonl"
DATASET = f"{LAYER}/_dataset/rulemaking_notices.jsonl"
CSV_PATH = f"{LAYER}/_dataset/rulemaking_notices.csv"
PROVENANCE = f"{LAYER}/_dataset/register_daily_sources.jsonl"
CROSSWALK = "_CROSSWALKS/rulemaking_to_regulation.jsonl"
MANIFEST = "_CONTROL_PLANE/MASTER_MANIFEST.json"
STATE = "_CONTROL_PLANE/REGISTER_REFRESH_STATE.json"
REGISTER_URL = "https://www.sos.state.co.us/CCR/RegisterHome.do"
RAW_PREFIX = "_RAW_ARCHIVE/register/daily/"
SNAPSHOT_PREFIX = "_SNAPSHOTS/register_daily/"
MAX_SOURCE_BYTES = 15_000_000
MAX_TOTAL_BYTES = 150_000_000
MAX_SOURCES = 500


class StrictModel(BaseModel):
    """Base for validated pilot records."""

    model_config = ConfigDict(extra="forbid")


def require_sos_url(value: str) -> str:
    """Limit outbound requests and redirects to public SOS CCR endpoints."""

    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"www.sos.state.co.us", "sos.state.co.us"}
        or parsed.port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path.startswith("/CCR/")
    ):
        raise ValueError(f"Unapproved source URL: {value}")
    return value


class SourceArtifact(StrictModel):
    """One immutable downloaded source and its provenance."""

    url: str
    final_url: str
    path: str = Field(
        pattern=r"^_RAW_ARCHIVE/register/daily/[a-f0-9]{64}\.(html|pdf|docx|doc|rtf)$"
    )
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: str
    retrieved_at: datetime
    bytes: int = Field(gt=0, le=MAX_SOURCE_BYTES)

    @field_validator("url", "final_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Validate both requested and final source locations."""

        return require_sos_url(value)


class SnapshotRef(StrictModel):
    """Map an immutable pre-update copy to its original derived file."""

    original_path: str
    path: str = Field(pattern=r"^_SNAPSHOTS/register_daily/[a-f0-9]{64}\.(json|jsonl|csv)$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class IssueState(StrictModel):
    """Validated scope and record identity for a previously collected issue."""

    publication_date: date
    source_sha256: str
    notice_ids: list[str]


class RefreshState(StrictModel):
    """Persistent content state; successful no-change checks do not rewrite it."""

    version: Literal[1] = 1
    since: date
    issues: dict[str, IssueState] = Field(default_factory=dict)
    sources: dict[str, SourceArtifact] = Field(default_factory=dict)
    snapshots: list[SnapshotRef] = Field(default_factory=list)


class NoticeProvenance(StrictModel):
    """Preserve table fields and all downloaded evidence for one notice."""

    notice_id: str
    publication_url: str
    row: DailyNoticeRow
    sources: list[SourceArtifact]
    resolved_ccr_evidence: str | None = None


class RefreshReport(StrictModel):
    """Per-run operational result; a failed run is never a no-change result."""

    source: Literal["colorado_register"] = "colorado_register"
    checked_at: datetime
    since: date
    status: Literal["updated", "no_change", "failed"] = "failed"
    validation_passed: bool = False
    publications_checked: int = 0
    sources_checked: int = 0
    notices_added: int = 0
    notices_updated: int = 0
    changed_paths: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    boundary: str = (
        "Pilot Register issues only; historical notices and current CCR legal status "
        "are not reverified. Linked documents are preserved as source evidence."
    )


class ManifestLayer(BaseModel):
    """Validate the fields used from the repository's existing manifest shape."""

    model_config = ConfigDict(extra="allow")
    id: str
    path: str
    record_count: int = Field(ge=0)
    known_gaps: list[str] = Field(default_factory=list)
    derived_files: list[str] = Field(default_factory=list)


class ExistingManifest(BaseModel):
    """Preserve unrelated manifest fields without substituting a different schema."""

    model_config = ConfigDict(extra="allow")
    project: dict[str, Any]
    data_layers: list[ManifestLayer]


@dataclass(frozen=True)
class FetchResult:
    """Bytes and media type returned from a verified source URL."""

    url: str
    content: bytes
    content_type: str


class OfficialSourceClient:
    """Ordinary curl HTTPS collection with trusted redirects and modest retries.

    Curl uses its standard verified TLS transport and the project's descriptive
    identity. No cookies, browser identity, or access-challenge solver are used.
    """

    def __init__(self, delay: float = 1.0) -> None:
        """Create a client with explicit timeouts and a descriptive user agent."""

        if delay < 0:
            raise ValueError("Source request delay cannot be negative")
        self.delay = delay

    def close(self) -> None:
        """Finish the client; each request already closes its temporary resources."""

    def __call__(self, url: str) -> FetchResult:
        """Download a bounded source; never bypass TLS or source access failures."""

        current = require_sos_url(url)
        for _redirect in range(4):
            for attempt in range(3):
                if self.delay:
                    time.sleep(self.delay)
                status, headers, body = self._request(current)
                if status in {429, 502, 503, 504} and attempt < 2:
                    time.sleep(min(30.0, 2.0 ** (attempt + 1)))
                    continue
                if status in {301, 302, 303, 307, 308}:
                    if not headers.get("location"):
                        raise ValueError(f"Source redirect has no Location: {current}")
                    current = require_sos_url(urljoin(current, headers["location"]))
                    break
                if not 200 <= status < 300:
                    raise ValueError(f"Source returned HTTP {status}: {current}")
                sample = body[:131072].lower()
                challenge_markers = (
                    b"cf-chl-widget", b"_cf_chl_opt", b"cf-wrapper",
                    b"<title>just a moment", b"<title>attention required",
                )
                if (headers.get("cf-mitigated", "").casefold() == "challenge"
                        or any(marker in sample for marker in challenge_markers)):
                    raise ValueError(f"Source returned an access challenge: {current}")
                if not body:
                    raise ValueError(f"Source returned an empty response: {current}")
                return FetchResult(current, body, headers.get("content-type", ""))
            else:
                raise ValueError(f"Source retry limit reached: {url}")
        raise ValueError(f"Too many redirects: {url}")

    def _request(self, url: str) -> tuple[int, dict[str, str], bytes]:
        """Issue one verified HTTPS GET without automatic redirects or curl config."""

        with tempfile.TemporaryDirectory(prefix="geode-register-http-") as directory:
            body_path = Path(directory) / "body"
            headers_path = Path(directory) / "headers"
            command = [
                "curl", "--disable", "--silent", "--show-error", "--globoff",
                "--proto", "=https", "--proto-redir", "=https",
                "--max-time", "30", "--connect-timeout", "15",
                "--max-filesize", str(MAX_SOURCE_BYTES),
                "--user-agent", "ProjectGeode/0.1 (Colorado Register research pilot)",
                "--dump-header", str(headers_path), "--output", str(body_path),
                "--write-out", "%{http_code}", "--url", url,
            ]
            try:
                result = subprocess.run(
                    command, capture_output=True, text=True, timeout=35, check=False,
                )
            except FileNotFoundError as exc:
                raise ValueError("Official source collection requires curl on PATH") from exc
            except subprocess.TimeoutExpired as exc:
                raise ValueError(f"Source request timed out: {url}") from exc
            if result.returncode == 63:
                raise ValueError(f"Source exceeds size limit: {url}")
            if result.returncode:
                raise ValueError(
                    f"Source transport failed (curl {result.returncode}): {url}; "
                    f"{result.stderr.strip()[:240]}"
                )
            if not re.fullmatch(r"\d{3}", result.stdout.strip()) or not headers_path.exists():
                raise ValueError(f"Source transport returned invalid HTTP metadata: {url}")
            if not body_path.exists() or body_path.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError(f"Source response is missing or exceeds size limit: {url}")
            status = int(result.stdout.strip())
            headers: dict[str, str] = {}
            # Proxy CONNECT and informational headers may precede the actual response.
            blocks = re.split(r"\r?\n\r?\n", headers_path.read_text(encoding="latin-1"))
            for block in blocks:
                lines = block.splitlines()
                if not lines or not lines[0].startswith("HTTP/"):
                    continue
                headers = {}
                for line in lines[1:]:
                    key, separator, value = line.partition(":")
                    if separator:
                        headers[key.strip().casefold()] = value.strip()
            return status, headers, body_path.read_bytes()


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value: BaseModel) -> bytes:
    return (json.dumps(value.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n").encode()


def _rows_bytes(rows: list[BaseModel | dict[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(
            row.model_dump(mode="json") if isinstance(row, BaseModel) else row,
            ensure_ascii=False, separators=(",", ":"),
        ) + "\n").encode()
        for row in rows
    )


def _load_rows(root: Path, name: str, schema: type[BaseModel]) -> list[dict[str, Any]]:
    path = root / name
    if not path.exists():
        return []
    result = []
    for row in iter_jsonl(path):
        schema.model_validate(row)
        result.append(row)
    return result


def _by_id(rows: list[dict[str, Any]], name: str) -> dict[str, dict[str, Any]]:
    result = {str(row["id"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate record IDs in {name}")
    return result


def _validate_existing_corpus(
    root: Path, records: dict[str, dict[str, Any]], index: dict[str, dict[str, Any]],
) -> None:
    """Refuse to rewrite or certify contradictory historical representations."""

    dataset = _by_id(_load_rows(root, DATASET, RulemakingNotice), DATASET)
    if set(dataset) != set(records):
        raise ValueError("Existing dataset and metadata IDs do not match")
    for key, row in dataset.items():
        if RulemakingNotice.model_validate(row) != RulemakingNotice.model_validate(records[key]):
            raise ValueError(f"Existing dataset and metadata values differ: {key}")
    quarters: dict[str, set[str]] = {}
    for key, row in index.items():
        name = row["path"]
        if not re.fullmatch(r"04_Rulemaking/(\d{4})/register_\1_Q[1-4]\.jsonl", name):
            raise ValueError(f"Unexpected existing quarterly path: {name}")
        quarters.setdefault(name, set()).add(key)
    for name, expected in quarters.items():
        rows = _by_id(_load_rows(root, name, RulemakingNotice), name)
        if set(rows) != expected:
            raise ValueError(f"Existing quarter and index IDs do not match: {name}")
        for key, row in rows.items():
            expected_record = RulemakingNotice.model_validate(records[key])
            if RulemakingNotice.model_validate(row) != expected_record:
                raise ValueError(f"Existing quarter and metadata values differ: {key}")
    _load_rows(root, CROSSWALK, CrosswalkEntry)


def _safe_target(root: Path, name: str) -> Path:
    target = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"Unsafe output path: {name}")
    if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
        raise ValueError(f"Output escapes project root: {name}")
    return target


def _media_suffix(result: FetchResult) -> str:
    body = result.content
    mime = result.content_type.split(";")[0].strip().casefold()
    if not body or len(body) > MAX_SOURCE_BYTES:
        raise ValueError("Empty or oversized source response")
    prefix = body[:4096].lower()
    challenge_markers = (b"access denied", b"cf-chl-", b"captcha", b"attention required")
    if any(word in prefix for word in challenge_markers):
        raise ValueError("Source returned an access challenge")
    if body.startswith(b"%PDF-"):
        return "pdf"
    if body.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                names = set(archive.namelist())
            if {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                return "docx"
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Invalid document archive at {result.url}") from exc
    if body.startswith(b"\xd0\xcf\x11\xe0"):
        return "doc"
    if body.lstrip().startswith(b"{\\rtf"):
        return "rtf"
    if b"<html" in prefix or b"<!doctype html" in prefix:
        return "html"
    raise ValueError(f"Unrecognized source format at {result.url}: {mime}")


def _row_key(record: RulemakingNotice) -> tuple[str, str, str, str]:
    return (
        record.publication_date.isoformat(), record.notice_type,
        record.ccr_rule_affected, record.edocket_tracking_number or "",
    )


def _notice(row: DailyNoticeRow, source: SourceArtifact) -> RulemakingNotice:
    if not row.ccr_rule_affected or not row.ccr_citation:
        raise ValueError(f"Unresolved CCR citation in {row.source_url}, row {row.row_number}")
    identity = "|".join([
        row.publication_date.isoformat(), row.notice_type, row.ccr_rule_affected,
        row.edocket_tracking_number or row.title,
    ])
    identifier = f"RM-{row.publication_date.year}-daily-{_digest(identity.encode())[:20]}"
    return RulemakingNotice(
        id=identifier,
        title=row.title,
        notice_type=row.notice_type,
        ccr_rule_affected=row.ccr_rule_affected,
        ccr_citation=row.ccr_citation,
        agency_code=None,
        agency=row.agency,
        summary=row.title,
        source_section_heading=row.section,
        source_row_number=row.row_number,
        source_evidence=row.source_evidence,
        notice_type_source="register_table_headers",
        hearing_date=row.hearing_date,
        effective_date=row.effective_date,
        publication_date=row.publication_date,
        edocket_tracking_number=row.edocket_tracking_number,
        edocket_url=row.edocket_url,
        subject_tags=["rulemaking"],
        source_url=row.source_url,
        source_path=source.path,
        extraction_method="register_daily_table_v1",
        field_confidence={},
        confidence={"overall": 0.0},
    )


def _index_row(notice: RulemakingNotice, now: datetime) -> LayerIndexRecord:
    year = notice.publication_date.year
    quarter = (notice.publication_date.month - 1) // 3 + 1
    return LayerIndexRecord(
        id=notice.id, layer=LAYER, entity_type=notice.entity_type,
        title=notice.title or notice.summary, citation=notice.ccr_rule_affected,
        path=f"{LAYER}/{year}/register_{year}_Q{quarter}.jsonl", meta_path=META,
        source_url=notice.source_url, source_path=notice.source_path or str(notice.source_url),
        publication_year=year, last_updated=now,
        sha256=_digest(notice.model_dump_json().encode()),
        tags=notice.subject_tags, confidence=notice.confidence.overall,
    )


def _csv_bytes(records: list[dict[str, Any]]) -> bytes:
    fields = [
        "id", "notice_type", "ccr_rule_affected", "agency_code", "publication_date",
        "hearing_date", "effective_date", "edocket_tracking_number", "source_url", "source_path",
        "source_section_heading", "source_row_number", "extraction_method", "notice_type_source",
        "summary",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: row.get(field) for field in fields} for row in records)
    return output.getvalue().encode()


def _commit_transaction(root: Path, outputs: dict[str, bytes]) -> None:
    """Apply validated derived outputs atomically per file, rolling back on error."""

    old: dict[str, bytes | None] = {}
    applied: list[str] = []
    try:
        for name, content in outputs.items():
            target = _safe_target(root, name)
            prior = target.read_bytes() if target.exists() else None
            if name.startswith((RAW_PREFIX, SNAPSHOT_PREFIX)):
                if prior is not None and prior != content:
                    raise ValueError(f"Refusing to overwrite immutable evidence: {name}")
                if prior is None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as handle:
                        handle.write(content)
                continue
            old[name] = prior
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(content)
                os.replace(temporary, target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            applied.append(name)
    except Exception:
        for name in reversed(applied):
            target = _safe_target(root, name)
            if old[name] is None:
                target.unlink(missing_ok=True)
            else:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(old[name])
                os.replace(temporary, target)
        raise


def refresh_register(
    root: Path,
    since: date,
    *,
    fetch: Callable[[str], FetchResult],
    now: datetime | None = None,
) -> RefreshReport:
    """Fetch, validate and merge a complete pilot window without replacing history.

    All fetching and semantic/schema checks finish before derived files change.
    Sources and pre-update snapshots use immutable content-addressed paths.
    """

    root = root.resolve()
    now = now or datetime.now(timezone.utc)
    report = RefreshReport(checked_at=now, since=since)
    try:
        _refresh(root, since, fetch, now, report)
    except Exception as exc:
        LOGGER.exception("Colorado Register refresh failed")
        report.status = "failed"
        report.validation_passed = False
        report.changed_paths = []
        report.notices_added = 0
        report.notices_updated = 0
        report.errors.append(str(exc))
    return report


def _refresh(
    root: Path, since: date, fetch: Callable[[str], FetchResult],
    now: datetime, report: RefreshReport,
) -> None:
    if since > now.date() or since.year < now.year - 2:
        raise ValueError("Pilot window must begin within the current or two preceding years")
    state_path = _safe_target(root, STATE)
    state = (
        RefreshState.model_validate_json(state_path.read_bytes())
        if state_path.exists() else RefreshState(since=since)
    )
    if state.since != since:
        raise ValueError("Changing the pilot window requires a separate reviewed migration")
    originals = _load_rows(root, META, RulemakingNotice)
    records = _by_id(originals, META)
    index = _by_id(_load_rows(root, INDEX, LayerIndexRecord), INDEX)
    if set(records) != set(index):
        raise ValueError("Existing rulemaking index and metadata IDs do not match")
    _validate_existing_corpus(root, records, index)
    known_keys: dict[tuple[str, str, str, str], list[str]] = {}
    for payload in originals:
        model = RulemakingNotice.model_validate(payload)
        known_keys.setdefault(_row_key(model), []).append(model.id)
    provenance = {
        row["notice_id"]: row for row in _load_rows(root, PROVENANCE, NoticeProvenance)
    }
    sources: dict[str, tuple[SourceArtifact, bytes]] = {}
    total_bytes = 0

    def collect(url: str) -> tuple[SourceArtifact, bytes]:
        nonlocal total_bytes
        require_sos_url(url)
        if url in sources:
            return sources[url]
        if len(sources) >= MAX_SOURCES:
            raise ValueError("Source limit reached; refusing an incomplete refresh")
        LOGGER.info("Checking source %d: %s", len(sources) + 1, url)
        result = fetch(url)
        require_sos_url(result.url)
        suffix = _media_suffix(result)
        total_bytes += len(result.content)
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("Total download limit reached; refusing an incomplete refresh")
        sha = _digest(result.content)
        prior = state.sources.get(url)
        if (
            prior and suffix == "html" and prior.path.endswith(".html")
            and prior.final_url == result.url and prior.content_type == result.content_type
        ):
            archived_path = _safe_target(root, prior.path)
            if archived_path.exists():
                archived = archived_path.read_bytes()
                if _digest(archived) != prior.sha256:
                    raise ValueError(f"Corrupt content-addressed source: {prior.path}")
                if register_html_fingerprint(archived) == register_html_fingerprint(result.content):
                    sources[url] = (prior, archived)
                    report.sources_checked = len(sources)
                    return prior, archived
        artifact = SourceArtifact(
            url=url, final_url=result.url, path=f"{RAW_PREFIX}{sha}.{suffix}", sha256=sha,
            content_type=result.content_type, bytes=len(result.content),
            retrieved_at=prior.retrieved_at if prior and prior.sha256 == sha else now,
        )
        sources[url] = (artifact, result.content)
        report.sources_checked = len(sources)
        return artifact, result.content

    publications = {}
    for year in range(since.year, now.year + 1):
        index_url = f"{REGISTER_URL}?pyear={year}"
        artifact, body = collect(index_url)
        if not artifact.path.endswith(".html"):
            raise ValueError("Register index was not HTML")
        for publication in parse_register_index(
            decode_register_html(body, artifact.content_type), artifact.final_url,
        ):
            published = date.fromisoformat(publication.publication_date)
            if since <= published <= now.date():
                publications[str(publication.url)] = publication
    if not publications:
        raise ValueError("No published issues in configured window; cannot verify coverage")
    if set(state.issues) - set(publications):
        raise ValueError("Previously checked issues disappeared from the listing; review required")
    changed: dict[str, RulemakingNotice] = {}
    seen_ids: set[str] = set()
    next_issues = {}
    for url, publication in sorted(publications.items(), key=lambda pair: pair[1].publication_date):
        primary, body = collect(url)
        if not primary.path.endswith(".html"):
            raise ValueError(f"Issue was not HTML: {url}")
        rows = parse_register_issue(
            decode_register_html(body, primary.content_type),
            date.fromisoformat(publication.publication_date),
            primary.final_url,
        )
        issue_ids = []
        for row in rows:
            evidence = [primary]
            detail_evidence = None
            if not row.ccr_rule_affected:
                detail_url = row.edocket_url or row.hearing_detail_url
                if not detail_url:
                    raise ValueError(
                        f"Missing citation and resolution link: {url}, row {row.row_number}"
                    )
                detail_source, detail_body = collect(detail_url)
                if not detail_source.path.endswith(".html"):
                    raise ValueError(f"CCR resolution page is not HTML: {detail_url}")
                detail = parse_edocket_detail(
                    decode_register_html(detail_body, detail_source.content_type),
                    detail_source.final_url,
                )
                if detail.tracking_number and detail.tracking_number != row.edocket_tracking_number:
                    raise ValueError(f"Docket tracking number mismatch: {detail_url}")
                row = DailyNoticeRow.model_validate({
                    **row.model_dump(), "ccr_citation": detail.ccr_citation,
                    "ccr_rule_affected": detail.ccr_rule_affected,
                })
                detail_evidence = detail.source_evidence
                evidence.append(detail_source)
            for document_url in row.document_urls:
                document, _body = collect(document_url)
                if document.path.endswith(".html"):
                    raise ValueError(f"Document link returned HTML: {document_url}")
                evidence.append(document)
            notice = _notice(row, primary)
            existing_keys = known_keys.get(_row_key(notice), [])
            if len(existing_keys) > 1:
                raise ValueError(f"Ambiguous existing notice identity: {_row_key(notice)}")
            if existing_keys:
                notice = notice.model_copy(update={"id": existing_keys[0]})
            if notice.id in seen_ids:
                raise ValueError(f"Duplicate notice identity across source rows: {notice.id}")
            seen_ids.add(notice.id)
            issue_ids.append(notice.id)
            previous = records.get(notice.id)
            if previous is None:
                report.notices_added += 1
                changed[notice.id] = notice
            elif RulemakingNotice.model_validate(previous) != notice:
                report.notices_updated += 1
                changed[notice.id] = notice
            if notice.id in changed:
                records[notice.id] = notice.model_dump(mode="json")
                index[notice.id] = _index_row(notice, now).model_dump(mode="json")
            provenance[notice.id] = NoticeProvenance(
                notice_id=notice.id, publication_url=url, row=row, sources=evidence,
                resolved_ccr_evidence=detail_evidence,
            ).model_dump(mode="json")
        old_issue = state.issues.get(url)
        if old_issue and set(old_issue.notice_ids) - set(issue_ids):
            raise ValueError(f"Previously indexed notice removed or reidentified: {url}")
        next_issues[url] = IssueState(
            publication_date=date.fromisoformat(publication.publication_date),
            source_sha256=primary.sha256, notice_ids=sorted(issue_ids),
        )
        report.publications_checked += 1
    outputs: dict[str, bytes] = {}
    for artifact, content in sources.values():
        outputs[artifact.path] = content
    outputs[PROVENANCE] = _rows_bytes([provenance[key] for key in sorted(provenance)])
    if changed:
        _prepare_corpus(root, records, index, changed, since, now, outputs)
    next_state = RefreshState(
        since=since, issues=next_issues,
        sources={url: artifact for url, (artifact, _body) in sorted(sources.items())},
        snapshots=list(state.snapshots),
    )
    outputs[STATE] = _json_bytes(next_state)
    # Keep no-change checks out of Git; evidence timestamps remain the first retrieval.
    outputs = {
        name: content for name, content in outputs.items()
        if not _safe_target(root, name).exists() or _safe_target(root, name).read_bytes() != content
    }
    snapshots = {}
    for name in list(outputs):
        if name == STATE:
            continue
        target = _safe_target(root, name)
        if name.startswith(RAW_PREFIX):
            if target.exists():
                raise ValueError(f"Corrupt content-addressed source: {name}")
            continue
        if target.exists():
            prior = target.read_bytes()
            sha = _digest(prior)
            snapshot_path = f"{SNAPSHOT_PREFIX}{sha}{target.suffix}"
            snapshots[snapshot_path] = prior
            ref = SnapshotRef(original_path=name, path=snapshot_path, sha256=sha)
            if ref not in next_state.snapshots:
                next_state.snapshots.append(ref)
    if outputs:
        outputs[STATE] = _json_bytes(next_state)
        if state_path.exists() and state_path.read_bytes() != outputs[STATE]:
            prior_state = state_path.read_bytes()
            snapshot_path = f"{SNAPSHOT_PREFIX}{_digest(prior_state)}.json"
            snapshots[snapshot_path] = prior_state
    outputs = {**snapshots, **outputs}
    _commit_transaction(root, outputs)
    report.changed_paths = sorted(outputs)
    report.validation_passed = True
    report.status = "updated" if outputs else "no_change"


def _prepare_corpus(
    root: Path, records: dict[str, dict[str, Any]], index: dict[str, dict[str, Any]],
    changed: dict[str, RulemakingNotice], since: date, now: datetime, outputs: dict[str, bytes],
) -> None:
    dataset = _by_id(_load_rows(root, DATASET, RulemakingNotice), DATASET)
    if dataset and set(dataset) != (set(records) - {key for key in changed if key not in dataset}):
        raise ValueError("Existing dataset and metadata do not cover the same historical IDs")
    all_records = [records[key] for key in sorted(records)]
    outputs[META] = _rows_bytes(all_records)
    outputs[DATASET] = _rows_bytes(all_records)
    outputs[CSV_PATH] = _csv_bytes(all_records)
    outputs[INDEX] = _rows_bytes([index[key] for key in sorted(index)])
    quarter_changes: dict[str, dict[str, RulemakingNotice]] = {}
    for notice in changed.values():
        path = _index_row(notice, now).path
        quarter_changes.setdefault(path, {})[notice.id] = notice
    for name, additions in quarter_changes.items():
        rows = _by_id(_load_rows(root, name, RulemakingNotice), name)
        rows.update({key: value.model_dump(mode="json") for key, value in additions.items()})
        outputs[name] = _rows_bytes([rows[key] for key in sorted(rows)])
    links = _load_rows(root, CROSSWALK, CrosswalkEntry)
    existing_keys = {
        (row["source_id"], row.get("target_id"), row["relationship"]): position
        for position, row in enumerate(links)
    }
    for notice in changed.values():
        key = (notice.id, notice.ccr_rule_affected, "cites")
        if key in existing_keys:
            position = existing_keys[key]
            links[position] = CrosswalkEntry.model_validate({
                **links[position], "source_evidence": notice.source_evidence,
                "data_retrieved": now.date(), "source_url": notice.source_url,
            }).model_dump(mode="json")
        else:
            links.append(CrosswalkEntry(
                source_id=notice.id, source_type="rulemaking_notice",
                target_id=notice.ccr_rule_affected, target_type="regulation_rule",
                relationship="cites", confidence=0.0,
                source_evidence=notice.source_evidence,
                data_retrieved=now.date(), source_url=notice.source_url,
            ).model_dump(mode="json"))
    outputs[CROSSWALK] = _rows_bytes(links)
    manifest_path = _safe_target(root, MANIFEST)
    manifest = ExistingManifest.model_validate_json(manifest_path.read_bytes())
    layers = [layer for layer in manifest.data_layers if layer.id == LAYER]
    if len(layers) != 1:
        raise ValueError("Manifest must identify exactly one rulemaking layer")
    layer = layers[0]
    layer.record_count = len(records)
    layer.derived_files = list(dict.fromkeys([*layer.derived_files, PROVENANCE, STATE]))
    gap = (
        f"Daily Register pilot covers issues from {since}; "
        "earlier records require separate verification."
    )
    if gap not in layer.known_gaps:
        layer.known_gaps = [*layer.known_gaps, gap]
    # Do not advance whole-layer last_checked or claim all historical sources are fresh.
    outputs[MANIFEST] = (
        json.dumps(
            manifest.model_dump(mode="json", exclude_unset=True), ensure_ascii=False, indent=2,
        )
        + "\n"
    ).encode()


def write_run_report(report: RefreshReport, directory: Path) -> None:
    """Write machine-readable status and a human-readable Actions summary."""

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_bytes(_json_bytes(report))
    (directory / "changes.json").write_text(json.dumps(report.changed_paths, indent=2) + "\n")
    lines = [
        "# Colorado Register daily check", "",
        f"- Result: **{report.status}**",
        f"- Checked at: {report.checked_at.isoformat()}",
        f"- Scope: issues published from {report.since}",
        f"- Publications checked: {report.publications_checked}",
        f"- Source files checked: {report.sources_checked}",
        f"- Notices added: {report.notices_added}",
        f"- Notices updated: {report.notices_updated}",
        f"- Validation passed: {report.validation_passed}", "",
        report.boundary,
    ]
    if report.errors:
        lines.extend(["", "## Errors", *[f"- {error}" for error in report.errors]])
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run a bounded incremental pilot and return nonzero on any incomplete check."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--since", type=date.fromisoformat, default=date(2026, 7, 1))
    parser.add_argument("--report-dir", type=Path, default=Path(".geode_runtime/register-refresh"))
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()
    if args.delay < 0:
        parser.error("--delay cannot be negative")
    logging.basicConfig(level=logging.INFO)
    client = OfficialSourceClient(args.delay)
    try:
        report = refresh_register(args.root, args.since, fetch=client)
    finally:
        client.close()
    write_run_report(report, args.report_dir)
    LOGGER.info("Register refresh %s; sources=%s", report.status, report.sources_checked)
    return 1 if report.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
