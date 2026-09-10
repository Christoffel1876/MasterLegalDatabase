"""Bounded preservation of explicitly selected county documents and source catalogs.

This pilot does not repair missing historical bytes, extract obligations, or decide
legal currency. Every selected document must remain explicitly linked by its county.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import quote, unquote, urldefrag, urljoin, urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import pymupdf

from geode.connectors.register_daily_parser import _Document, decode_register_html
from geode.pipeline.register_daily import FetchResult

LOGGER = logging.getLogger(__name__)
PILOT_ID = "jefferson-clear-creek"
MAX_SOURCE_BYTES = 30_000_000
MAX_TOTAL_BYTES = 100_000_000
MAX_CATALOG_CANDIDATES = 5_000
RAW_PREFIX = "_RAW_ARCHIVE/local/reacquisition/"
SNAPSHOT_PREFIX = "_SNAPSHOTS/county_reacquisition/"
VERIFICATION_PREFIX = "08_County_Authorities/_verification/reacquisition/"
INVENTORY_PATH = f"{VERIFICATION_PREFIX}{PILOT_ID}.jsonl"
STATE_PATH = f"{VERIFICATION_PREFIX}{PILOT_ID}-state.json"
AUTHORITY_HOSTS = {
    "CO-COUNTY-JEFFERSON": frozenset({"jeffco.us", "www.jeffco.us"}),
    "CO-COUNTY-CLEAR_CREEK": frozenset({"clearcreekcounty.us", "www.clearcreekcounty.us"}),
}
AuthorityId = Literal["CO-COUNTY-JEFFERSON", "CO-COUNTY-CLEAR_CREEK"]


def normalize_url(value: str) -> str:
    """Encode observed literal spaces and remove browser-only fragments."""
    if any(ord(character) < 32 for character in value):
        raise ValueError("Source URL contains control characters")
    return quote(urldefrag(value)[0], safe=":/?&=%+;,@-._~!$'()*[]")


def require_county_url(value: str, authority_id: str | None = None) -> str:
    """Restrict requests to the correct county's HTTPS hosts and ordinary TLS port."""
    value = normalize_url(value)
    parsed = urlparse(value)
    hosts = AUTHORITY_HOSTS.get(authority_id, frozenset()) if authority_id else frozenset().union(
        *AUTHORITY_HOSTS.values())
    if (parsed.scheme != "https" or parsed.hostname not in hosts
            or parsed.port not in {None, 443} or parsed.username is not None
            or parsed.password is not None):
        raise ValueError(f"Unapproved county source URL: {value}")
    return value


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Retrieval timestamp must include a timezone")
    return value


def _label(value: str) -> str:
    return " ".join(value.split())


def _candidate_url(value: str) -> bool:
    path = unquote(urlparse(value).path).casefold()
    return bool(re.search(r"/documentcenter/(?:view|home)(?:/|$)", path)
                or re.search(r"\.(?:pdf|docx?|rtf)$", path))


class StrictModel(BaseModel):
    """Reject undeclared fields in durable pilot records."""

    model_config = ConfigDict(extra="forbid")


class CatalogSource(StrictModel):
    """A reviewed county catalog location; it does not imply complete legal coverage."""

    source_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
    authority_id: AuthorityId
    authority_name: str = Field(min_length=1)
    url: str
    title: str = Field(min_length=1)

    @model_validator(mode="after")
    def source_scope(self) -> CatalogSource:
        """Require each catalog to belong to its declared county."""
        self.url = require_county_url(self.url, self.authority_id)
        return self


class SelectedDocument(StrictModel):
    """One deliberately selected document and its exact observed catalog label."""

    source_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
    authority_id: AuthorityId
    authority_name: str = Field(min_length=1)
    url: str
    catalog_url: str
    source_label: str = Field(min_length=1)
    category: str = Field(min_length=1)

    @model_validator(mode="after")
    def source_scope(self) -> SelectedDocument:
        """Validate the county, document-candidate path, and normalized visible label."""
        self.url = require_county_url(self.url, self.authority_id)
        self.catalog_url = require_county_url(self.catalog_url, self.authority_id)
        self.source_label = _label(self.source_label)
        if not self.source_label or not _candidate_url(self.url):
            raise ValueError("Selected source requires a document-candidate URL and visible label")
        return self


class CountyPilotManifest(StrictModel):
    """Fixed, bounded selection; changes require an explicit scope migration."""

    version: Literal[1] = 1
    pilot_id: Literal["jefferson-clear-creek"] = PILOT_ID
    boundary: str = Field(min_length=1)
    catalogs: list[CatalogSource] = Field(min_length=1, max_length=4)
    documents: list[SelectedDocument] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def consistent_selection(self) -> CountyPilotManifest:
        """Reject duplicates, cross-county associations, and undeclared catalogs."""
        rows = [*self.catalogs, *self.documents]
        if len({row.source_id for row in rows}) != len(rows):
            raise ValueError("Manifest source IDs must be unique")
        if len({row.url for row in rows}) != len(rows):
            raise ValueError("Manifest source URLs must be unique")
        catalogs = {row.url: row for row in self.catalogs}
        for document in self.documents:
            catalog = catalogs.get(document.catalog_url)
            if (catalog is None or catalog.authority_id != document.authority_id
                    or catalog.authority_name != document.authority_name):
                raise ValueError("Selected document must match a declared catalog and county")
        return self


class CountySource(StrictModel):
    """Immutable original bytes and exact retrieval provenance."""

    url: str
    final_url: str
    path: str = Field(pattern=r"^_RAW_ARCHIVE/local/reacquisition/[a-f0-9]{64}\."
                     r"(html|pdf)$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: str
    bytes: int = Field(gt=0, le=MAX_SOURCE_BYTES)
    first_retrieved_at: datetime

    @field_validator("first_retrieved_at")
    @classmethod
    def timestamp(cls, value: datetime) -> datetime:
        """Require an actual timezone-aware retrieval timestamp."""
        return _aware(value)

    @model_validator(mode="after")
    def provenance(self) -> CountySource:
        """Require matching archive identity and same-county requested/final URLs."""
        require_county_url(self.url)
        authority = next(key for key, hosts in AUTHORITY_HOSTS.items()
                         if urlparse(self.url).hostname in hosts)
        require_county_url(self.final_url, authority)
        if Path(self.path).stem != self.sha256:
            raise ValueError("Original archive name differs from its SHA-256")
        return self


class CatalogCandidate(StrictModel):
    """Every direct candidate link, including unselected and external coverage gaps."""

    catalog_source_id: str
    authority_id: AuthorityId
    catalog_url: str
    url: str
    source_label: str
    href: str
    disposition: Literal["selected", "unselected", "external_or_disallowed"]


class CountyPreservationRecord(StrictModel):
    """Preserved source evidence, without an asserted legal status or obligation."""

    entity_type: Literal["county_source_preservation"] = "county_source_preservation"
    id: str
    source_id: str
    pilot_id: Literal["jefferson-clear-creek"] = PILOT_ID
    authority_id: AuthorityId
    authority_name: str
    catalog_url: str
    source_url: str
    source_label: str
    category: str
    semantic_status: Literal["source_preservation_only"] = "source_preservation_only"
    legal_status: Literal["unknown"] = "unknown"
    review_required: Literal[True] = True
    observed_at: datetime
    sources: list[CountySource] = Field(min_length=2, max_length=2)

    @field_validator("observed_at")
    @classmethod
    def timestamp(cls, value: datetime) -> datetime:
        """Require an actual timezone-aware observation timestamp."""
        return _aware(value)

    @model_validator(mode="after")
    def associations(self) -> CountyPreservationRecord:
        """Require exact identities and both catalog/document original references."""
        if self.id != f"COUNTY-REACQ-{self.source_id}":
            raise ValueError("Preservation record identity differs from source ID")
        require_county_url(self.source_url, self.authority_id)
        require_county_url(self.catalog_url, self.authority_id)
        if {source.url for source in self.sources} != {self.catalog_url, self.source_url}:
            raise ValueError("Record must preserve its catalog and selected document")
        return self


class CountyReacquisitionState(StrictModel):
    """Persistent selected-source inventory; identical rechecks do not rewrite it."""

    version: Literal[1] = 1
    pilot_id: Literal["jefferson-clear-creek"] = PILOT_ID
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    document_ids: list[str]
    sources: dict[str, CountySource]
    catalog_links: list[CatalogCandidate]


class CountyReacquisitionReport(StrictModel):
    """Run evidence that distinguishes source failure from a successful no-change check."""

    version: Literal[1] = 1
    pilot_id: Literal["jefferson-clear-creek"] = PILOT_ID
    checked_at: datetime
    status: Literal["updated", "no_change", "failed"] = "failed"
    validation_passed: bool = False
    manifest_complete: bool = False
    catalogs_checked: int = Field(default=0, ge=0)
    documents_checked: int = Field(default=0, ge=0)
    sources_checked: int = Field(default=0, ge=0)
    downloaded_bytes: int = Field(default=0, ge=0)
    changed_paths: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    boundary: str = (
        "Selected Jefferson and Clear Creek county sources only. Unselected and external "
        "catalog candidates remain coverage gaps. Preserved documents have unknown legal "
        "status and require review; canonical county data and missing historical files "
        "are unchanged."
    )


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _json_bytes(value: BaseModel) -> bytes:
    return (json.dumps(value.model_dump(mode="json"), sort_keys=True, indent=2) + "\n").encode()


def _target(root: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe preservation path: {name}")
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Preservation path escapes root: {name}")
    if any(item.is_symlink() for item in [target, *target.parents] if item != root.parent):
        raise ValueError(f"Preservation path contains a symlink: {name}")
    return target


def _suffix(result: FetchResult, maximum: int) -> str:
    body = result.content
    if not body or len(body) > maximum:
        raise ValueError("Empty source or per-source byte limit exceeded")
    if body.startswith(b"%PDF-"):
        if not body.rstrip().endswith(b"%%EOF"):
            raise ValueError("PDF is truncated or has no complete EOF marker")
        try:
            with pymupdf.open(stream=body, filetype="pdf") as document:
                if document.is_repaired or document.is_encrypted or document.page_count < 1:
                    raise ValueError("PDF is repaired, encrypted, or has no pages")
                for page_number in range(document.page_count):
                    document.load_page(page_number)
        except Exception as exc:
            raise ValueError(f"Invalid PDF structure: {exc}") from exc
        return "pdf"
    prefix = body[:131072].lower()
    if any(marker in prefix for marker in (b"access denied", b"captcha", b"_cf_chl_opt",
                                           b"<title>just a moment", b"cf-chl-widget")):
        raise ValueError("Source returned an access challenge")
    if b"<html" in prefix or b"<!doctype html" in prefix:
        return "html"
    raise ValueError("Unrecognized document format")


def _catalog_links(catalog: CatalogSource, source: CountySource, body: bytes,
                   selected: set[str]) -> list[CatalogCandidate]:
    html = decode_register_html(body, source.content_type)
    if not re.search(r"</html\s*>", html, re.I):
        raise ValueError("Catalog HTML has no complete document terminator")
    document = _Document(html)
    regions = [node for node in document.root.nodes() if node.attrs.get("id") == "page"]
    if len(regions) != 1:
        raise ValueError("Catalog requires one unique #page content region")
    headings = regions[0].nodes("h1")
    if len(headings) != 1 or _label(headings[0].text()) != _label(catalog.title):
        raise ValueError("Catalog heading does not match its declared identity")
    bases = document.root.nodes("base")
    if len(bases) > 1:
        raise ValueError("Catalog has ambiguous base URLs")
    base = urljoin(source.final_url, bases[0].attrs.get("href", "")) if bases else source.final_url
    links = {}
    for anchor in regions[0].nodes("a"):
        href = anchor.attrs.get("href", "")
        if not href:
            continue
        url = normalize_url(urljoin(base, href))
        if not _candidate_url(url):
            continue
        disposition = "selected" if url in selected else "unselected"
        try:
            require_county_url(url, catalog.authority_id)
        except ValueError:
            disposition = "external_or_disallowed"
        label = anchor.text()
        key = (url, label)
        links.setdefault(key, CatalogCandidate(
            catalog_source_id=catalog.source_id, authority_id=catalog.authority_id,
            catalog_url=catalog.url, url=url, source_label=label, href=href,
            disposition=disposition,
        ))
        if len(links) > MAX_CATALOG_CANDIDATES:
            raise ValueError("Catalog candidate limit exceeded")
    return [links[key] for key in sorted(links)]


class CountySourceClient:
    """Ordinary curl client with bounded HTTPS requests and checked same-county redirects."""

    def __init__(self, delay: float = 1.0) -> None:
        """Use a descriptive project identity, default TLS verification, and modest retries."""
        if delay < 0:
            raise ValueError("Request delay cannot be negative")
        self.delay = delay
        self.max_response_bytes = MAX_SOURCE_BYTES

    def close(self) -> None:
        """Finish the client; each request owns and closes its temporary files."""

    def __call__(self, url: str) -> FetchResult:
        """Fetch a source without browser impersonation or following external redirects."""
        current = require_county_url(url)
        authority = next(key for key, hosts in AUTHORITY_HOSTS.items()
                         if urlparse(current).hostname in hosts)
        for _redirect in range(4):
            for attempt in range(3):
                if self.delay:
                    time.sleep(self.delay)
                status, headers, body = self._request(current)
                if status in {429, 502, 503, 504} and attempt < 2:
                    time.sleep(min(8.0, 2.0 ** attempt))
                    continue
                if status in {301, 302, 303, 307, 308}:
                    if not headers.get("location"):
                        raise ValueError("County redirect is missing its Location")
                    current = require_county_url(urljoin(current, headers["location"]), authority)
                    break
                if status != 200:
                    raise ValueError(f"County source returned HTTP {status}: {current}")
                if headers.get("cf-mitigated", "").casefold() == "challenge":
                    raise ValueError("County source returned an access challenge")
                result = FetchResult(current, body, headers.get("content-type", ""))
                _suffix(result, MAX_SOURCE_BYTES)
                return result
        raise ValueError("County source redirect limit exceeded")

    def _request(self, url: str) -> tuple[int, dict[str, str], bytes]:
        """Issue one bounded GET, with automatic redirects and curl configuration disabled."""
        with tempfile.TemporaryDirectory(prefix="geode-county-http-") as directory:
            body = Path(directory) / "body"
            headers = Path(directory) / "headers"
            command = [
                "curl", "--disable", "--silent", "--show-error", "--globoff",
                "--proto", "=https", "--proto-redir", "=https", "--max-time", "45",
                "--connect-timeout", "15", "--max-filesize", str(self.max_response_bytes),
                "--user-agent", "ProjectGeode/0.1 (county source preservation pilot)",
                "--dump-header", str(headers), "--output", str(body),
                "--write-out", "%{http_code}", "--url", url,
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True,
                                        timeout=50, check=False)
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                raise ValueError(
                    "County source requires an available, responsive curl client"
                ) from exc
            if result.returncode:
                raise ValueError(f"County source transport failed (curl {result.returncode})")
            if not re.fullmatch(r"\d{3}", result.stdout.strip()) or not headers.exists():
                raise ValueError("County transport returned invalid HTTP metadata")
            if not body.exists() or body.stat().st_size > self.max_response_bytes:
                raise ValueError("County source is missing or exceeds the byte limit")
            parsed_headers = {}
            for block in re.split(r"\r?\n\r?\n", headers.read_text(encoding="latin-1")):
                lines = block.splitlines()
                if not lines or not lines[0].startswith("HTTP/"):
                    continue
                parsed_headers = {}
                for line in lines[1:]:
                    key, separator, value = line.partition(":")
                    if separator:
                        parsed_headers[key.strip().casefold()] = value.strip()
            return int(result.stdout.strip()), parsed_headers, body.read_bytes()


def _replace(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _immutable(path: Path, content: bytes) -> None:
    """Publish complete original bytes atomically without ever replacing an existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Immutable evidence differs: {path.name}")
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != content:
                raise ValueError(f"Concurrent immutable evidence differs: {path.name}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _commit(root: Path, outputs: dict[str, bytes]) -> None:
    previous = {}
    applied = []
    for name in outputs:
        _target(root, name)
    try:
        for name, content in outputs.items():
            target = _target(root, name)
            if name.startswith((RAW_PREFIX, SNAPSHOT_PREFIX)):
                _immutable(target, content)
                continue
            previous[name] = target.read_bytes() if target.exists() else None
            _replace(target, content)
            applied.append(name)
    except Exception:
        for name in reversed(applied):
            target = _target(root, name)
            if previous[name] is None:
                target.unlink(missing_ok=True)
            else:
                _replace(target, previous[name])
        raise


def _load_previous(root: Path, manifest_hash: str) -> tuple[CountyReacquisitionState | None, dict]:
    state_path, inventory_path = _target(root, STATE_PATH), _target(root, INVENTORY_PATH)
    if state_path.exists() != inventory_path.exists():
        raise ValueError("Prior state and inventory must both exist or both be absent")
    if not state_path.exists():
        return None, {}
    state = CountyReacquisitionState.model_validate_json(state_path.read_bytes())
    inventory = inventory_path.read_bytes()
    if state.manifest_sha256 != manifest_hash:
        raise ValueError("Pilot manifest changed; explicit scope migration is required")
    if _digest(inventory) != state.inventory_sha256:
        raise ValueError("Prior inventory hash differs from state")
    records = {}
    for line in inventory.splitlines():
        record = CountyPreservationRecord.model_validate_json(line)
        if record.source_id in records:
            raise ValueError("Duplicate prior preservation identity")
        records[record.source_id] = record
    if sorted(records) != state.document_ids:
        raise ValueError("Prior record identities differ from state")
    for url, source in state.sources.items():
        path = _target(root, source.path)
        if url != source.url or not path.exists():
            raise ValueError("Prior original source is missing or mismatched")
        content = path.read_bytes()
        if _digest(content) != source.sha256 or len(content) != source.bytes:
            raise ValueError("Prior original source bytes are corrupt")
    for record in records.values():
        if any(state.sources.get(source.url) != source for source in record.sources):
            raise ValueError("Prior record provenance differs from state")
    return state, records


def collect_county_reacquisition(
    root: Path, manifest: CountyPilotManifest, *, fetch: Callable[[str], FetchResult],
    now: datetime | None = None, max_total_bytes: int = MAX_TOTAL_BYTES,
    max_source_bytes: int = MAX_SOURCE_BYTES,
) -> CountyReacquisitionReport:
    """Collect the complete selected manifest, failing before any derived promotion on gaps."""
    report = CountyReacquisitionReport(checked_at=now or datetime.now(timezone.utc))
    try:
        _aware(report.checked_at)
        manifest = CountyPilotManifest.model_validate(manifest.model_dump())
        if (not 1 <= max_total_bytes <= MAX_TOTAL_BYTES
                or not 1 <= max_source_bytes <= MAX_SOURCE_BYTES):
            raise ValueError("Pilot limits must be positive and within the hard bounds")
        _collect(root.resolve(), manifest, fetch, report, max_total_bytes, max_source_bytes)
    except Exception as exc:
        LOGGER.exception("County source preservation failed")
        report.status = "failed"
        report.errors.append(str(exc))
        report.validation_passed = report.manifest_complete = False
        report.changed_paths = []
    return report


def _collect(root: Path, manifest: CountyPilotManifest, fetch: Callable[[str], FetchResult],
             report: CountyReacquisitionReport, max_total: int, max_source: int) -> None:
    manifest_hash = _digest(_json_bytes(manifest))
    previous, old_records = _load_previous(root, manifest_hash)
    sources: dict[str, tuple[CountySource, bytes]] = {}

    def collect(url: str, authority_id: str, html: bool) -> CountySource:
        require_county_url(url, authority_id)
        if url not in sources:
            remaining = max_total - report.downloaded_bytes
            if remaining <= 0:
                raise ValueError("Total byte limit exhausted before requesting the next source")
            if isinstance(fetch, CountySourceClient):
                fetch.max_response_bytes = min(max_source, remaining)
            result = fetch(url)
            report.downloaded_bytes += len(result.content)
            if report.downloaded_bytes > max_total:
                raise ValueError("Total byte limit exceeded before manifest completion")
            require_county_url(result.url, authority_id)
            suffix = _suffix(result, max_source)
            if html != (suffix == "html"):
                raise ValueError(f"Unexpected source format: {url}")
            sha = _digest(result.content)
            artifact = CountySource(
                url=url, final_url=result.url, path=f"{RAW_PREFIX}{sha}.{suffix}", sha256=sha,
                content_type=result.content_type, bytes=len(result.content),
                first_retrieved_at=report.checked_at,
            )
            old = previous.sources.get(url) if previous else None
            if old and old.model_dump(exclude={"first_retrieved_at"}) == artifact.model_dump(
                    exclude={"first_retrieved_at"}):
                artifact = old
            sources[url] = artifact, result.content
            report.sources_checked = len(sources)
        return sources[url][0]

    links = []
    for catalog in manifest.catalogs:
        source = collect(catalog.url, catalog.authority_id, True)
        selected = {doc.url for doc in manifest.documents if doc.catalog_url == catalog.url}
        candidates = _catalog_links(catalog, source, sources[catalog.url][1], selected)
        pairs = {(candidate.url, candidate.source_label) for candidate in candidates}
        for document in manifest.documents:
            if (document.catalog_url == catalog.url
                    and (document.url, document.source_label) not in pairs):
                raise ValueError(
                    f"Selected document link or label disappeared: {document.source_id}"
                )
        links.extend(candidates)
        report.catalogs_checked += 1
    records = {}
    for document in manifest.documents:
        original = collect(document.url, document.authority_id, False)
        record = CountyPreservationRecord(
            id=f"COUNTY-REACQ-{document.source_id}", source_id=document.source_id,
            authority_id=document.authority_id, authority_name=document.authority_name,
            catalog_url=document.catalog_url, source_url=document.url,
            source_label=document.source_label, category=document.category,
            observed_at=report.checked_at,
            sources=[sources[document.catalog_url][0], original],
        )
        old = old_records.get(document.source_id)
        if (old and old.model_dump(exclude={"observed_at"})
                == record.model_dump(exclude={"observed_at"})):
            record = old
        records[document.source_id] = record
        report.documents_checked += 1
    if previous and set(previous.document_ids) != set(records):
        raise ValueError("Selected preservation identities changed")
    inventory = b"".join(
        (records[key].model_dump_json() + "\n").encode() for key in sorted(records)
    )
    state = CountyReacquisitionState(
        manifest_sha256=manifest_hash, inventory_sha256=_digest(inventory),
        document_ids=sorted(records), sources={key: sources[key][0] for key in sorted(sources)},
        catalog_links=sorted(
            links, key=lambda link: (link.catalog_source_id, link.url, link.source_label)
        ),
    )
    outputs = {source.path: content for source, content in sources.values()}
    outputs[INVENTORY_PATH], outputs[STATE_PATH] = inventory, _json_bytes(state)
    changed, snapshots = {}, {}
    for name, content in outputs.items():
        target = _target(root, name)
        if not target.exists() or target.read_bytes() != content:
            if target.exists() and name.startswith(RAW_PREFIX):
                raise ValueError("Refusing to replace corrupt immutable evidence")
            changed[name] = content
            if target.exists() and name.startswith(VERIFICATION_PREFIX):
                prior = target.read_bytes()
                snapshot = f"{SNAPSHOT_PREFIX}{_digest(prior)}{target.suffix}"
                snapshot_target = _target(root, snapshot)
                if snapshot_target.exists():
                    if snapshot_target.read_bytes() != prior:
                        raise ValueError("Existing immutable snapshot is corrupt")
                else:
                    snapshots[snapshot] = prior
    _commit(root, {**snapshots, **changed})
    report.changed_paths = sorted({*snapshots, *changed})
    report.validation_passed = report.manifest_complete = True
    report.status = "updated" if changed else "no_change"


def write_run_report(report: CountyReacquisitionReport, directory: Path) -> None:
    """Atomically retain validated JSON, changes, and a source-preservation summary."""
    report = CountyReacquisitionReport.model_validate(report.model_dump())
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    lines = ["# County source preservation", "", f"Result: **{report.status}**", "",
             f"Checked: {report.checked_at.isoformat()}",
             f"Catalogs: {report.catalogs_checked}; documents: {report.documents_checked}; "
             f"source URLs: {report.sources_checked}", "", report.boundary]
    if report.errors:
        lines.extend(["", "Errors:", *[f"- {error}" for error in report.errors]])
    values = {"report.json": _json_bytes(report),
              "changes.json": (json.dumps(report.changed_paths, indent=2) + "\n").encode(),
              "summary.md": ("\n".join(lines) + "\n").encode()}
    for name, content in values.items():
        target = _target(directory, name)
        if target.exists() and target.read_bytes() != content:
            old = target.read_bytes()
            snapshot = _target(directory, f"_SNAPSHOTS/{_digest(old)}{target.suffix}")
            _immutable(snapshot, old)
        _replace(target, content)


def main(argv: list[str] | None = None) -> int:
    """Run the fixed county preservation pilot; failures emit reports and a nonzero result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args(argv)
    if args.delay < 0:
        parser.error("--delay cannot be negative")
    root, report_dir = args.root.resolve(), args.report_dir.resolve()
    if any(report_dir.is_relative_to(root / name) for name in (
        "08_County_Authorities", "_RAW_ARCHIVE", "_CONTROL_PLANE", "_SNAPSHOTS", ".git",
    )):
        parser.error("Reports must be outside corpus and control-plane directories")
    report = CountyReacquisitionReport(checked_at=datetime.now(timezone.utc))
    client = CountySourceClient(args.delay)
    try:
        path = args.manifest if args.manifest.is_absolute() else root / args.manifest
        if path.stat().st_size > 1_000_000:
            raise ValueError("Pilot manifest exceeds the bounded read limit")
        manifest = CountyPilotManifest.model_validate_json(path.read_bytes())
        report = collect_county_reacquisition(root, manifest, fetch=client)
    except Exception as exc:
        report.errors.append(str(exc))
    finally:
        client.close()
    write_run_report(report, report_dir)
    return 1 if report.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
