"""Collect bounded, source-backed CCR verification evidence for a review proposal.

This collector inventories one complete department. It preserves evidence separately
from canonical regulation text and does not decide that an agency's rules apply to
a person or business. Any incomplete traversal fails before derived files change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import tempfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import parse_qs, quote, urljoin, urlparse
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from geode.connectors.register_daily_parser import (
    _Document,
    _Node,
    decode_register_html,
    register_html_fingerprint,
)
from geode.pipeline.register_daily import (
    MAX_SOURCE_BYTES,
    FetchResult,
    OfficialSourceClient,
    _media_suffix,
    require_sos_url,
)

LOGGER = logging.getLogger(__name__)
CATALOG_URL = "https://www.sos.state.co.us/CCR/NumericalDeptList.do"
WELCOME_URL = "https://www.sos.state.co.us/CCR/Welcome.do"
RAW_PREFIX = "_RAW_ARCHIVE/ccr/current/"
SNAPSHOT_PREFIX = "_SNAPSHOTS/ccr_current/"
VERIFICATION_PREFIX = "02_Regulations_CCR/_verification/current/"
MAX_SOURCES = 300
MAX_TOTAL_BYTES = 150_000_000
CCR_RE = re.compile(r"\b(\d{1,2})\s+CCR\s+(\d+-\d+(?:-\d+)?)\b", re.I)
DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")


class StrictModel(BaseModel):
    """Reject accidental additions to the verification evidence contract."""

    model_config = ConfigDict(extra="forbid")


class CCRSource(StrictModel):
    """Original bytes retrieved from one approved source URL."""

    url: str
    final_url: str
    path: str = Field(pattern=r"^_RAW_ARCHIVE/ccr/current/[a-f0-9]{64}\.(html|pdf|docx|doc|rtf)$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: str
    bytes: int = Field(gt=0, le=MAX_SOURCE_BYTES)
    first_retrieved_at: datetime

    @field_validator("url", "final_url")
    @classmethod
    def approved_url(cls, value: str) -> str:
        """Apply the same SOS-only allowlist to requested and redirected URLs."""

        return require_sos_url(value)

    @model_validator(mode="after")
    def content_address(self) -> CCRSource:
        """Require the archive filename to match its integrity hash."""

        if Path(self.path).stem != self.sha256:
            raise ValueError("Source archive path does not match its SHA-256")
        return self


class CCRVersion(StrictModel):
    """A version explicitly linked and labeled on the current rule page."""

    version_id: str = Field(pattern=r"^\d+$")
    effective_date: date | None = None
    filing_type: str | None = None
    adopted_date: date | None = None
    publication_date: date | None = None
    edocket_urls: list[str] = Field(default_factory=list)
    source_label: str = Field(min_length=1)
    designation: Literal["current", "future", "history", "unknown"]
    document_urls: list[str] = Field(min_length=1)

    @field_validator("document_urls", "edocket_urls")
    @classmethod
    def approved_documents(cls, value: list[str]) -> list[str]:
        """Require approved URLs for every linked document."""

        return [require_sos_url(url) for url in value]


class CCRCurrentRecord(StrictModel):
    """Evidence of source designation, distinct from a legal status determination."""

    entity_type: Literal["ccr_current_verification"] = "ccr_current_verification"
    id: str = Field(pattern=r"^\d{1,2}_CCR_\d+-\d+(?:-\d+)?$")
    ccr_citation: str
    rule_id: str = Field(pattern=r"^\d+$")
    department_id: str = Field(pattern=r"^\d+$")
    department_name: str = Field(min_length=1)
    agency_id: str = Field(pattern=r"^\d+$")
    agency_name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_page_url: str
    source_publication_cutoff: date
    observed_at: datetime
    classification: Literal["source_current", "source_repealed", "future_effective", "ambiguous"]
    classification_evidence: str = Field(min_length=1)
    selected_version_id: str | None = Field(default=None, pattern=r"^\d+$")
    effective_date: date | None = None
    repeal_date: date | None = None
    versions: list[CCRVersion]
    sources: list[CCRSource] = Field(min_length=1)
    review_required: Literal[True] = True
    boundary: str = "Source designation only; canonical CCR legal text is unchanged."

    @field_validator("source_page_url")
    @classmethod
    def approved_page(cls, value: str) -> str:
        """Validate the primary evidence URL."""

        return require_sos_url(value)


class CCRState(StrictModel):
    """Content state retained across runs; no-change checks do not rewrite it."""

    version: Literal[1] = 1
    department_id: str = Field(pattern=r"^\d+$")
    department_name: str = Field(min_length=1)
    catalog_url: str
    welcome_url: str
    agency_ids: list[str]
    rule_ids: list[str]
    source_publication_cutoff: date
    inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sources: dict[str, CCRSource]

    @field_validator("catalog_url", "welcome_url")
    @classmethod
    def approved_index(cls, value: str) -> str:
        """Validate evidence index locations."""

        return require_sos_url(value)


class CCRCurrentReport(StrictModel):
    """Run-specific evidence and completeness result, including failed checks."""

    version: Literal[1] = 1
    department_id: str
    checked_at: datetime
    status: Literal["updated", "no_change", "failed"] = "failed"
    validation_passed: bool = False
    full_department_discovery: bool = False
    department_name: str | None = None
    source_publication_cutoff: date | None = None
    agencies_checked: int = 0
    rules_checked: int = 0
    sources_checked: int = 0
    downloaded_bytes: int = 0
    classification_counts: dict[str, int] = Field(default_factory=dict)
    changed_paths: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    boundary: str = (
        "One department's publicly listed rule pages and their designated current/future "
        "documents only. Historical version links are recorded without downloading all "
        "historical documents. This does not establish statewide coverage or amend "
        "canonical CCR text. Ambiguous and repealed records require review."
    )


def _query(url: str, key: str) -> str:
    values = parse_qs(urlparse(url).query).get(key, [])
    if len(values) != 1 or not values[0]:
        raise ValueError(f"Source URL requires exactly one {key}: {url}")
    return values[0]


def _url(value: str) -> str:
    """Encode observed literal spaces without altering source query semantics."""

    return require_sos_url(quote(value, safe=":/?&=%+;,@-._~!$'()*[]"))


def _numeric(value: str) -> str:
    if not re.fullmatch(r"\d+", value):
        raise ValueError(f"Expected numeric source identifier: {value}")
    return value


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: BaseModel) -> bytes:
    return (json.dumps(value.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode()


def _target(root: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe evidence path: {name}")
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Evidence path escapes root: {name}")
    if any(item.is_symlink() for item in [target, *target.parents] if item != root.parent):
        raise ValueError(f"Evidence path contains symlink: {name}")
    return target


def _parse_html(body: bytes, content_type: str) -> _Document:
    html = decode_register_html(body, content_type)
    if not re.search(r"</html\s*>\s*(?:<script[\s\S]*?</script>\s*)?$", html, re.I):
        raise ValueError("Incomplete source HTML: missing document terminator")
    document = _Document(html)
    for anchor in document.root.nodes("a"):
        href = anchor.attrs.get("href", "")
        if re.search(r"[?&](page|offset|start|pagenum)=", href, re.I):
            raise ValueError("Unimplemented pagination on source page")
        if anchor.text().strip().casefold() in {"next", "next page", "more results"}:
            raise ValueError("Unimplemented pagination on source page")
    return document


def _links(document: _Document, base_url: str, endpoint: str) -> list[tuple[str, _Node]]:
    links = []
    for anchor in document.root.nodes("a"):
        href = anchor.attrs.get("href", "")
        if endpoint.casefold() not in href.casefold():
            continue
        url = _url(urljoin(base_url, href))
        if urlparse(url).path.rsplit("/", 1)[-1].casefold() != endpoint.casefold():
            raise ValueError(f"Unexpected source endpoint: {url}")
        links.append((url, anchor))
    return links


def _cutoff(document: _Document, checked: date) -> date:
    matches = re.findall(
        r"effective\s+on\s+or\s+before\s+(\d{1,2}/\d{1,2}/\d{4})",
        document.root.text(), re.I,
    )
    if len(set(matches)) != 1:
        raise ValueError("CCR publication cutoff is missing or ambiguous")
    cutoff = datetime.strptime(matches[0], "%m/%d/%Y").date()
    if cutoff > checked:
        raise ValueError("Source publication cutoff is later than check date")
    return cutoff


def _agencies(document: _Document, url: str, department_id: str) -> dict[str, tuple[str, str, str]]:
    agencies = {}
    for link, anchor in _links(document, url, "NumericalCCRDocList.do"):
        if _query(link, "deptID") != department_id:
            continue
        agency_id = _numeric(_query(link, "agencyID"))
        agency = _query(link, "agencyName")
        department = _query(link, "deptName")
        value = (link, agency, department)
        if agency_id in agencies and agencies[agency_id] != value:
            raise ValueError(f"Conflicting agency entries: {agency_id}")
        if not anchor.text():
            raise ValueError("Empty agency link label")
        agencies[agency_id] = value
    if not agencies or len({value[2] for value in agencies.values()}) != 1:
        raise ValueError("Department has no agencies or inconsistent source labels")
    department_label = next(iter(agencies.values()))[2]
    match = re.fullmatch(r"([\d,]+)\s+(.+)", department_label)
    if match is None:
        raise ValueError("Department label has no source numerical grouping")
    starts = [
        anchor for anchor in document.root.nodes("a")
        if anchor.attrs.get("name") in match[1].split(",")
        and _cells(_ancestor(anchor, "tr"))[-1].text() == match[2]
    ]
    if len(starts) != 1:
        raise ValueError("Missing or ambiguous department section in source catalog")
    first_row = _ancestor(starts[0], "tr")
    table = _ancestor(first_row, "table")
    expected_ids = []
    for row in table.nodes("tr"):
        if row.order <= first_row.order or _ancestor(row, "table") is not table:
            continue
        if any(anchor.attrs.get("name") for anchor in row.nodes("a")):
            break
        cells = _cells(row)
        anchors = [anchor for anchor in row.nodes("a") if anchor.attrs.get("href")]
        if len(cells) != 2 or len(anchors) != 1:
            raise ValueError("Incomplete agency row in department source section")
        target = _url(urljoin(url, anchors[0].attrs["href"]))
        if (
            urlparse(target).path != "/CCR/NumericalCCRDocList.do"
            or _query(target, "deptID") != department_id
        ):
            raise ValueError("Agency row has an unexpected endpoint or department")
        expected_ids.append(_numeric(_query(target, "agencyID")))
    if sorted(expected_ids) != sorted(agencies):
        raise ValueError("Department source rows and parsed agency identities disagree")
    return agencies


def _rules(document: _Document, url: str) -> dict[str, tuple[str, str, str]]:
    rules = {}
    tables = [
        table for table in document.root.nodes("table")
        if _headers(table) == ["ccr#", "title"]
    ]
    if len(tables) != 1:
        raise ValueError("Missing or ambiguous agency rule table")
    data_rows = [
        row for row in tables[0].nodes("tr")
        if _ancestor(row, "table") is tables[0]
        and any(cell.tag == "td" for cell in _cells(row))
    ]
    for link, anchor in _links(document, url, "DisplayRule.do"):
        if any(_query(link, key) != _query(url, key) for key in ("deptID", "agencyID")):
            raise ValueError("Rule listing belongs to another department or agency")
        if _query(link, "action").casefold() != "ruleinfo":
            raise ValueError("Unexpected rule listing action")
        rule_id = _numeric(_query(link, "ruleId"))
        citation = CCR_RE.search(anchor.text())
        if citation is None:
            raise ValueError(f"Rule listing has no CCR citation: {rule_id}")
        ccr = f"{citation[1]} CCR {citation[2]}"
        row = _ancestor(anchor, "tr")
        cells = _cells(row)
        if len(cells) != 2 or not cells[1].text():
            raise ValueError(f"Incomplete agency rule row: {rule_id}")
        values = (link, ccr, cells[1].text())
        if rule_id in rules:
            raise ValueError(f"Duplicate rule listing: {rule_id}")
        rules[rule_id] = values
    if not rules:
        raise ValueError("Agency has no verifiable rule listing")
    if len(rules) != len(data_rows):
        raise ValueError("Incomplete agency rule table: a source row was not parsed")
    return rules


def _ancestor(node: _Node, tag: str) -> _Node:
    parent = node.parent
    while parent is not None and parent.tag != tag:
        parent = parent.parent
    if parent is None:
        raise ValueError(f"Source element has no containing {tag}")
    return parent


def _cells(row: _Node) -> list[_Node]:
    return [node for node in row.nodes() if node.tag in {"td", "th"} and node.parent is row]


def _headers(table: _Node) -> list[str]:
    return [
        node.text().casefold() for node in table.nodes("th")
        if _ancestor(node, "table") is table
    ]


def _date(value: str) -> date | None:
    matches = DATE_RE.findall(value)
    if len(set(matches)) > 1:
        raise ValueError(f"Ambiguous date in source field: {value}")
    if matches:
        return datetime.strptime(matches[0], "%m/%d/%Y").date()
    if value.strip().casefold() in {"", "n/a", "imported (pdf)", "imported (docx)"}:
        return None
    raise ValueError(f"Unrecognized date field: {value}")


def _title(document: _Document) -> str:
    titles = [
        node.text() for node in document.root.nodes("p")
        if "pagehead5" in node.attrs.get("class", "").split()
    ]
    if len(titles) != 1 or not CCR_RE.match(titles[0]):
        raise ValueError("Missing or ambiguous CCR rule-page title")
    return titles[0]


def _document_link(anchor: _Node, url: str) -> tuple[str, str]:
    """Resolve the exact two observed SOS handlers without executing JavaScript."""

    handler = anchor.attrs.get("onclick", "")
    match = re.fullmatch(
        r"\s*OpenRule(Window|WordVersion)\(\s*'([0-9]+)'\s*,\s*'([^']+)'\s*\)\s*;?\s*",
        handler,
    )
    if match is None:
        raise ValueError("Unrecognized rule download handler")
    version, filename = match[2], match[3]
    if not CCR_RE.fullmatch(filename):
        raise ValueError("Unexpected rule filename in source handler")
    kind = "type=word&" if match[1] == "WordVersion" else ""
    target = (
        f"/CCR/GenerateRulePdf.do?{kind}ruleVersionId={version}&fileName={quote(filename)}"
    )
    return version, _url(urljoin(url, target))


def _versions(document: _Document, url: str) -> list[CCRVersion]:
    """Read labeled version rows, preserving effective/adopted/publication distinctions."""

    sections = []
    labels = {
        "current version": "current", "archived versions": "history",
        "future versions": "future", "future version": "future",
    }
    for node in document.root.nodes("b"):
        label = node.text().casefold()
        if label in labels:
            sections.append((node.order, labels[label]))
    if sum(label == "current" for _order, label in sections) != 1:
        raise ValueError("Missing or duplicate Current version section")
    if sum(label == "history" for _order, label in sections) != 1:
        raise ValueError("Missing or duplicate Archived versions section")
    rows = {}
    for anchor in document.root.nodes("a"):
        if "OpenRule" in anchor.attrs.get("onclick", ""):
            row = _ancestor(anchor, "tr")
            rows[row.order] = row
    for table in document.root.nodes("table"):
        headers = _headers(table)
        if len(headers) == 6 and "effective date" in headers[0]:
            for row in table.nodes("tr"):
                if _ancestor(row, "table") is table and any(
                    cell.tag == "td" for cell in _cells(row)
                ):
                    rows[row.order] = row
    if not rows:
        raise ValueError("Rule page contains no downloadable version rows")
    versions = []
    seen = set()
    expected_filename = CCR_RE.match(_title(document))[0]
    for order, row in sorted(rows.items()):
        preceding = [label for position, label in sections if position < order]
        if not preceding:
            raise ValueError("Rule download appears outside a labeled version section")
        designation = preceding[-1]
        cells = _cells(row)
        if len(cells) != 6:
            raise ValueError("Unexpected version table columns")
        table = _ancestor(row, "table")
        headers = _headers(table)
        expected = [
            "filing type", "adopted date", "colorado register publication date",
            "rulemaking details (edocket tracking #)", "download word version",
        ]
        if len(headers) != 6 or headers[1:] != expected or "effective date" not in headers[0]:
            raise ValueError("Unexpected version table headers")
        downloads = []
        version_ids = set()
        for anchor in row.nodes("a"):
            if "OpenRule" not in anchor.attrs.get("onclick", ""):
                continue
            version_id, document_url = _document_link(anchor, url)
            if _query(document_url, "fileName") != expected_filename:
                raise ValueError("Version download citation differs from rule title")
            version_ids.add(version_id)
            downloads.append(document_url)
        if len(version_ids) != 1 or len(downloads) != len(set(downloads)):
            raise ValueError("Mismatched or duplicate version download links")
        version_id = next(iter(version_ids))
        if version_id in seen:
            raise ValueError("Duplicate version identity across source rows")
        seen.add(version_id)
        pdf_anchors = cells[0].nodes("a")
        if (
            len(pdf_anchors) != 1 or "PDF" not in cells[0].text()
            or not pdf_anchors[0].attrs.get("onclick", "").startswith("OpenRuleWindow(")
        ):
            raise ValueError("Version has no source PDF link")
        effective = _date(cells[0].text())
        if cells[5].nodes("a") and _date(cells[5].text()) != effective:
            raise ValueError("PDF and Word effective dates disagree")
        edocket_urls = [
            _url(urljoin(url, anchor.attrs["href"])) for anchor in cells[4].nodes("a")
        ]
        versions.append(CCRVersion(
            version_id=version_id, effective_date=effective, filing_type=cells[1].text() or None,
            adopted_date=_date(cells[2].text()), publication_date=_date(cells[3].text()),
            edocket_urls=edocket_urls, source_label=row.text(), designation=designation,
            document_urls=downloads,
        ))
    if not any(version.designation == "current" for version in versions):
        raise ValueError("Current version section has no complete version row")
    return versions


def _classify(
    document: _Document, versions: list[CCRVersion], checked: date,
) -> tuple[str, str, CCRVersion | None]:
    """Retain explicitly labeled source status; uncertain statuses remain unknown."""

    current = [version for version in versions if version.designation == "current"]
    title = _title(document)
    if len(current) != 1:
        return "ambiguous", "Multiple source-designated current versions: " + title, None
    selected = current[0]
    repeal = re.search(r"(?:\[| - )Repealed\b([^\]]*)(?:\]|$)", title, re.I)
    if repeal:
        dates = DATE_RE.findall(repeal[0])
        if len(dates) != 1:
            return "ambiguous", repeal[0], selected
        repeal_date = datetime.strptime(dates[0], "%m/%d/%Y").date()
        status = "source_repealed" if repeal_date <= checked else "future_effective"
        return status, repeal[0], selected
    if selected.effective_date is None:
        evidence = "Current version has no stated effective date: " + selected.source_label
        return "ambiguous", evidence, selected
    status = "future_effective" if selected.effective_date > checked else "source_current"
    return status, "Current version: " + selected.source_label, selected


def _load_previous(
    root: Path, state_path: str, inventory_path: str,
) -> tuple[CCRState | None, dict[str, CCRCurrentRecord]]:
    state_file = _target(root, state_path)
    inventory_file = _target(root, inventory_path)
    if state_file.exists() != inventory_file.exists():
        raise ValueError("Prior inventory and state must both exist or both be absent")
    if not state_file.exists():
        return None, {}
    state = CCRState.model_validate_json(state_file.read_bytes())
    content = inventory_file.read_bytes()
    if _digest(content) != state.inventory_sha256:
        raise ValueError("Existing verification inventory hash mismatch")
    records = {}
    for line in content.splitlines():
        record = CCRCurrentRecord.model_validate_json(line)
        if record.rule_id in records:
            raise ValueError("Duplicate previous rule identity")
        records[record.rule_id] = record
    if sorted(records) != sorted(state.rule_ids):
        raise ValueError("Prior inventory and state identities disagree")
    for url, source in state.sources.items():
        if url != source.url:
            raise ValueError("Prior source map key disagrees with provenance URL")
        path = _target(root, source.path)
        if (
            not path.exists() or _digest(path.read_bytes()) != source.sha256
            or path.stat().st_size != source.bytes
        ):
            raise ValueError(f"Missing or corrupt prior source: {source.path}")
    for record in records.values():
        if record.department_id != state.department_id:
            raise ValueError("Prior record belongs to a different department")
        if any(state.sources.get(source.url) != source for source in record.sources):
            raise ValueError("Prior record provenance disagrees with state")
    return state, records


def _replace(target: Path, body: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(body)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _commit(root: Path, outputs: dict[str, bytes]) -> None:
    """Preserve immutable evidence, and roll back all derived writes on failure."""

    previous = {}
    applied = []
    try:
        for name, body in outputs.items():
            target = _target(root, name)
            if name.startswith((RAW_PREFIX, SNAPSHOT_PREFIX)):
                if target.exists():
                    if target.read_bytes() != body:
                        raise ValueError(f"Refusing to overwrite immutable evidence: {name}")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as handle:
                        handle.write(body)
                continue
            previous[name] = target.read_bytes() if target.exists() else None
            _replace(target, body)
            applied.append(name)
    except Exception:
        for name in reversed(applied):
            target = _target(root, name)
            if previous[name] is None:
                target.unlink(missing_ok=True)
            else:
                _replace(target, previous[name])
        raise


def collect_ccr_current(
    root: Path,
    department_id: str,
    *,
    fetch: Callable[[str], FetchResult],
    now: datetime | None = None,
    catalog_url: str = CATALOG_URL,
    welcome_url: str = WELCOME_URL,
    max_sources: int = MAX_SOURCES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> CCRCurrentReport:
    """Collect a complete department into a separately reviewable evidence package.

    A failed check does not promote any inventory or change canonical data. Raw
    files already preserved during a failed transaction remain immutable evidence.
    """

    checked_at = now or datetime.now(timezone.utc)
    report = CCRCurrentReport(department_id=department_id, checked_at=checked_at)
    try:
        _collect(
            root.resolve(), _numeric(department_id), fetch, report, catalog_url, welcome_url,
            max_sources, max_total_bytes,
        )
    except Exception as exc:
        LOGGER.exception("CCR current verification failed")
        report.errors.append(str(exc))
        report.status = "failed"
        report.validation_passed = False
        report.full_department_discovery = False
        report.changed_paths = []
    return report


def _collect(
    root: Path, department_id: str, fetch: Callable[[str], FetchResult],
    report: CCRCurrentReport, catalog_url: str, welcome_url: str,
    max_sources: int, max_total_bytes: int,
) -> None:
    if not 1 <= max_sources <= MAX_SOURCES or not 1 <= max_total_bytes <= MAX_TOTAL_BYTES:
        raise ValueError("Source limits must be positive and within the pilot hard limits")
    if report.checked_at.tzinfo is None:
        raise ValueError("Check timestamp must include timezone")
    inventory_path = f"{VERIFICATION_PREFIX}department-{department_id}.jsonl"
    state_path = f"{VERIFICATION_PREFIX}department-{department_id}-state.json"
    previous, old_records = _load_previous(root, state_path, inventory_path)
    if previous and (
        previous.department_id != department_id or previous.catalog_url != catalog_url
        or previous.welcome_url != welcome_url
    ):
        raise ValueError("Prior evidence belongs to a different collection scope")
    sources: dict[str, tuple[CCRSource, bytes]] = {}

    def collect(url: str, html: bool) -> tuple[CCRSource, _Document | None]:
        require_sos_url(url)
        if url not in sources:
            if len(sources) >= max_sources:
                raise ValueError("Source-count limit reached before full discovery")
            result = fetch(url)
            require_sos_url(result.url)
            for key in ("deptID", "agencyID", "ruleId", "ruleVersionId"):
                if key in parse_qs(urlparse(url).query):
                    if _query(result.url, key) != _query(url, key):
                        raise ValueError(f"Source redirect changed {key}: {url}")
            suffix = _media_suffix(result)
            if html != (suffix == "html"):
                raise ValueError(f"Unexpected source format at {url}")
            report.downloaded_bytes += len(result.content)
            if report.downloaded_bytes > max_total_bytes:
                raise ValueError("Total byte limit reached before full discovery")
            sha = _digest(result.content)
            artifact = CCRSource(
                url=url, final_url=result.url, path=f"{RAW_PREFIX}{sha}.{suffix}", sha256=sha,
                content_type=result.content_type, bytes=len(result.content),
                first_retrieved_at=report.checked_at,
            )
            old = previous.sources.get(url) if previous else None
            content = result.content
            if (
                old and html and old.path.endswith(".html") and old.final_url == result.url
                and old.content_type == result.content_type
            ):
                archived = _target(root, old.path).read_bytes()
                if register_html_fingerprint(archived) == register_html_fingerprint(content):
                    artifact, content = old, archived
            if (
                old and old.sha256 == sha and old.final_url == result.url
                and old.content_type == result.content_type
            ):
                artifact = old
            sources[url] = artifact, content
            report.sources_checked = len(sources)
        artifact, content = sources[url]
        document = _parse_html(content, artifact.content_type) if html else None
        return artifact, document

    _welcome_source, welcome = collect(welcome_url, True)
    as_of = report.checked_at.astimezone(ZoneInfo("America/Denver")).date()
    cutoff = _cutoff(welcome, as_of)
    if previous and cutoff < previous.source_publication_cutoff:
        raise ValueError("Source publication cutoff moved backwards")
    report.source_publication_cutoff = cutoff
    _catalog_source, catalog = collect(catalog_url, True)
    agencies = _agencies(catalog, catalog_url, department_id)
    department_name = next(iter(agencies.values()))[2]
    report.department_name = department_name
    if previous and set(previous.agency_ids) - set(agencies):
        raise ValueError("Previously inventoried agency disappeared")
    records = {}
    canonical_ids = set()
    for agency_id, (agency_url, agency_name, _department) in sorted(agencies.items()):
        _agency_source, agency = collect(agency_url, True)
        rules = _rules(agency, agency_url)
        report.agencies_checked += 1
        for rule_id, (rule_url, ccr, _listed_title) in sorted(rules.items()):
            if rule_id in records:
                raise ValueError("Rule appears in multiple agencies")
            primary, document = collect(rule_url, True)
            source_title = _title(document)
            if CCR_RE.match(source_title)[0] != ccr:
                raise ValueError("Rule-page citation differs from the agency listing")
            versions = _versions(document, rule_url)
            status, evidence, selected = _classify(document, versions, as_of)
            source_evidence = [primary]
            for version in versions:
                if version.designation in {"current", "future", "unknown"}:
                    for document_url in version.document_urls:
                        artifact, _doc = collect(document_url, False)
                        source_evidence.append(artifact)
            canonical = ccr.replace(" CCR ", "_CCR_")
            if canonical in canonical_ids:
                raise ValueError("Duplicate CCR citation across rule identities")
            canonical_ids.add(canonical)
            record = CCRCurrentRecord(
                id=canonical, ccr_citation=ccr, rule_id=rule_id, department_id=department_id,
                department_name=department_name, agency_id=agency_id, agency_name=agency_name,
                title=source_title, source_page_url=rule_url, source_publication_cutoff=cutoff,
                observed_at=report.checked_at, classification=status,
                classification_evidence=evidence, selected_version_id=(
                    selected.version_id if selected else None
                ), effective_date=selected.effective_date if selected else None,
                repeal_date=(
                    datetime.strptime(DATE_RE.search(evidence)[0], "%m/%d/%Y").date()
                    if re.match(r"(?:\[| - )Repealed\b", evidence, re.I)
                    and DATE_RE.search(evidence) else None
                ),
                versions=versions, sources=source_evidence,
            )
            old = old_records.get(rule_id)
            if old and old.id != record.id:
                raise ValueError("Previously inventoried CCR citation was reidentified")
            if old and old.model_dump(exclude={"observed_at"}) == record.model_dump(
                exclude={"observed_at"},
            ):
                record = old
            records[rule_id] = record
            report.rules_checked += 1
    if previous and set(previous.rule_ids) - set(records):
        raise ValueError("Previously inventoried rule disappeared; review required")
    inventory = b"".join(
        (records[key].model_dump_json() + "\n").encode() for key in sorted(records)
    )
    state = CCRState(
        department_id=department_id, department_name=department_name, catalog_url=catalog_url,
        welcome_url=welcome_url, agency_ids=sorted(agencies), rule_ids=sorted(records),
        source_publication_cutoff=cutoff, inventory_sha256=_digest(inventory),
        sources={key: sources[key][0] for key in sorted(sources)},
    )
    outputs = {artifact.path: content for artifact, content in sources.values()}
    outputs[inventory_path] = inventory
    outputs[state_path] = _json_bytes(state)
    changed = {}
    for name, content in outputs.items():
        target = _target(root, name)
        if not target.exists() or target.read_bytes() != content:
            if target.exists() and name.startswith(RAW_PREFIX):
                raise ValueError(f"Corrupt immutable source: {name}")
            changed[name] = content
    snapshots = {}
    for name in changed:
        target = _target(root, name)
        if target.exists() and name.startswith(VERIFICATION_PREFIX):
            prior = target.read_bytes()
            snapshots[f"{SNAPSHOT_PREFIX}{_digest(prior)}{target.suffix}"] = prior
    _commit(root, {**snapshots, **changed})
    report.changed_paths = sorted({*snapshots, *changed})
    report.classification_counts = dict(Counter(
        record.classification for record in records.values()
    ))
    report.full_department_discovery = True
    report.validation_passed = True
    report.status = "updated" if changed else "no_change"


def write_run_report(report: CCRCurrentReport, directory: Path) -> None:
    """Write run evidence outside the canonical corpus, including failure details."""

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_bytes(_json_bytes(report))
    (directory / "changes.json").write_text(json.dumps(report.changed_paths, indent=2) + "\n")
    lines = [
        "# CCR current-source verification", "", f"Result: **{report.status}**", "",
        f"Department: {report.department_name or report.department_id}",
        f"Checked: {report.checked_at.isoformat()}",
        f"Source publication cutoff: {report.source_publication_cutoff}",
        f"Agencies: {report.agencies_checked}; rules: {report.rules_checked}; "
        f"source files: {report.sources_checked}", "", report.boundary,
    ]
    if report.errors:
        lines.extend(["", "Errors:", *[f"- {error}" for error in report.errors]])
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Collect one configured department and emit a nonzero result on failure."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--department-id", required=True)
    parser.add_argument("--report-dir", type=Path, default=Path(".geode_runtime/ccr-current"))
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args(argv)
    if args.delay < 0:
        parser.error("--delay cannot be negative")
    client = OfficialSourceClient(delay=args.delay)
    try:
        report = collect_ccr_current(args.root, args.department_id, fetch=client)
    finally:
        client.close()
    write_run_report(report, args.report_dir)
    return 1 if report.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
