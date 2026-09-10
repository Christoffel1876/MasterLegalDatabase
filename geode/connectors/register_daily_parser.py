"""Strict, column-aware source parsing for the Colorado Register daily pilot.

This deliberately does not use the historical bulk extractor: an AG opinion
date is not an effective date, and a proposal without a CCR number is retained
for resolution against its explicitly linked hearing detail.
"""

from __future__ import annotations

import codecs
import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from geode.connectors.register_scraper import RegisterPublication

_SOS_HOSTS = frozenset({"www.sos.state.co.us", "www.coloradosos.gov", "coloradosos.gov"})
_CCR = re.compile(r"\b\d{1,2}\s+CCR\s+\d+-\d+(?:-\d+)?\b", re.IGNORECASE)
_TRACKING = re.compile(r"^\d{4}-\d{5}$")
_DATE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")
_VOID = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
})
_SECTIONS = {
    "notices of proposed rulemaking": "proposed",
    "notice of proposed rulemaking": "proposed",
    "permanent rules adopted": "adopted",
    "emergency rules adopted": "emergency",
    "terminated rulemaking": "terminated",
}
_SKIP_SECTIONS = frozenset({
    "non-rulemaking public notices and other miscellaneous rulemaking notices",
    "nonrulemaking public notices and other miscellaneous rulemaking notices",
    "calendar of hearings",
})
# Exact passive wrapper observed on SOS Register pages on 2026-09-09. Match only
# its changing ray/timestamp values; a different or extended script stays visible.
_PASSIVE_CF_SCRIPT = (
    b"<script>(function(){function c(){var b=a.contentDocument||"
    b"(a.contentWindow&&a.contentWindow.document);if(b){var d=b.createElement('script');"
    b'd.innerHTML="window.__CF$cv$params={r:\'__GEODE_RAY__\',t:\'__GEODE_TIME__\'};'
    b"var a=document.createElement('script');"
    b"a.src='/cdn-cgi/challenge-platform/scripts/jsd/main.js';"
    b"document.getElementsByTagName('head')[0].appendChild(a);\";"
    b"b.getElementsByTagName('head')[0].appendChild(d)}}if(document.body){"
    b"var a=document.createElement('iframe');a.height=1;a.width=1;"
    b"a.style.position='absolute';a.style.top=0;a.style.left=0;a.style.border='none';"
    b"a.style.visibility='hidden';document.body.appendChild(a);"
    b"if('loading'!==document.readyState)c();else if(window.addEventListener)"
    b"document.addEventListener('DOMContentLoaded',c);"
    b"else{var e=document.onreadystatechange||function(){};"
    b"document.onreadystatechange=function(b){e(b);'loading'!==document.readyState&&"
    b"(document.onreadystatechange=e,c())}}}})();</script>"
)
_PASSIVE_CF_RE = re.compile(
    re.escape(_PASSIVE_CF_SCRIPT)
    .replace(b"__GEODE_RAY__", rb"[a-f0-9]{16,32}")
    .replace(b"__GEODE_TIME__", rb"[A-Za-z0-9+/=]{4,64}")
)


def register_html_fingerprint(body: bytes) -> str:
    """Hash source bytes except the exact known passive Cloudflare injection.

    Raw evidence remains unchanged. Legal text, links, whitespace, and all other
    scripts remain significant; this is a comparison fingerprint, not an archive
    integrity hash. A changed wrapper is conservatively treated as a change.
    """

    return hashlib.sha256(_PASSIVE_CF_RE.sub(b"", body)).hexdigest()


def decode_register_html(body: bytes, content_type: str) -> str:
    """Decode official HTML strictly, preserving its original punctuation.

    BOM takes precedence over HTTP charset, which takes precedence over an early
    HTML meta declaration. Undeclared English-language HTML uses valid UTF-8 when
    possible, otherwise the HTML Windows-1252 fallback. ISO-8859-1/ASCII labels
    follow the HTML Windows-1252 mapping. Unknown labels and malformed declared
    encodings fail; raw archive bytes are never changed or decoded with replacement.

    See https://html.spec.whatwg.org/multipage/parsing.html#determining-the-character-encoding
    """

    if body.startswith(codecs.BOM_UTF8):
        return body.decode("utf-8-sig")
    if body.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        raise RegisterParseError("UTF-32 is not a supported HTML encoding")
    if body.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return body.decode("utf-16")
    declared = _content_charset(content_type)
    if declared is not None:
        return body.decode(_html_codec(declared))
    # Latin-1 is used solely as a lossless byte view of ASCII markup, not to
    # decode the legal source text. HTML declarations must be in the first 1024 bytes.
    prefix = _Document(body[:1024].decode("latin-1"))
    labels: list[str] = []
    for node in prefix.root.nodes("meta"):
        if "charset" in node.attrs:
            labels.append(node.attrs["charset"])
        elif node.attrs.get("http-equiv", "").casefold() == "content-type":
            label = _content_charset(node.attrs.get("content", ""))
            if label is not None:
                labels.append(label)
    if labels:
        encodings = {_html_codec(label, from_meta=True) for label in labels}
        if len(encodings) != 1:
            raise RegisterParseError("Conflicting HTML meta character encodings")
        return body.decode(encodings.pop())
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        mime = content_type.split(";", 1)[0].strip().casefold()
        html_markup = re.search(rb"<!doctype\s+html\b|<html\b", body[:1024], re.I)
        if mime == "application/xhtml+xml" or (mime != "text/html" and not html_markup):
            raise RegisterParseError("Undeclared non-HTML source is not valid UTF-8")
        return body.decode("windows-1252")


def _content_charset(content_type: str) -> str | None:
    matches = re.findall(
        r"(?:^|;)\s*charset\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^;\s]*))",
        content_type, re.IGNORECASE,
    )
    labels = {next((value for value in group if value), "").strip().casefold()
              for group in matches}
    if len(labels) > 1:
        raise RegisterParseError("Conflicting HTTP character encodings")
    return next(iter(labels), None)


def _html_codec(label: str, *, from_meta: bool = False) -> str:
    normalized = label.strip().casefold().replace("_", "-")
    if normalized in {"utf-8", "utf8", "unicode-1-1-utf-8"}:
        return "utf-8"
    if normalized in {
        "windows-1252", "cp1252", "x-cp1252", "iso-8859-1", "iso8859-1", "iso88591",
        "iso-8859-1:1987", "iso-ir-100", "latin1", "latin-1", "l1", "ibm819", "cp819",
        "csisolatin1", "ascii", "us-ascii", "ansi-x3.4-1968",
    }:
        return "windows-1252"
    if normalized in {"utf-16", "utf-16le", "utf-16be"}:
        return "utf-8" if from_meta else ("utf-16-le" if normalized == "utf-16" else normalized)
    raise RegisterParseError(f"Unknown or unsupported HTML encoding: {label!r}")


class RegisterParseError(ValueError):
    """Source structure or a material field cannot be interpreted safely."""


def official_sos_url(value: str) -> str:
    """Validate an SOS URL and encode literal spaces without changing its meaning.

    The September 10, 2026 issue links a DOCX filename containing a space. Curl
    requires its percent-encoded representation; existing escapes and query
    delimiters must remain untouched. The original source HTML is archived as-is.
    """

    parsed = urlparse(value)
    if (parsed.scheme != "https" or parsed.hostname not in _SOS_HOSTS
            or parsed.username or parsed.password or parsed.port not in {None, 443}):
        raise RegisterParseError(f"Expected an HTTPS Colorado SOS source URL: {value}")
    return value.replace(" ", "%20")


class DailyNoticeRow(BaseModel):
    """A source row, including unresolved proposals and source-specific dates."""

    model_config = ConfigDict(extra="forbid")

    notice_type: str
    department: str = Field(min_length=1)
    agency: str = Field(min_length=1)
    title: str = Field(min_length=1)
    ccr_citation: str | None = None
    ccr_rule_affected: str | None = None
    edocket_tracking_number: str | None = None
    edocket_url: str | None = None
    hearing_detail_url: str | None = None
    opinion_url: str | None = None
    document_urls: list[str] = Field(default_factory=list)
    hearing_date: date | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    termination_date: date | None = None
    publication_date: date
    section: str
    row_number: int = Field(ge=1)
    source_evidence: str = Field(min_length=1)
    source_url: str

    @field_validator("source_url", "edocket_url", "hearing_detail_url", "opinion_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        """Require official source links."""

        return official_sos_url(value) if value is not None else None

    @field_validator("document_urls")
    @classmethod
    def validate_documents(cls, values: list[str]) -> list[str]:
        """Require official document links."""

        return [official_sos_url(value) for value in values]


class DailyEdocketDetail(BaseModel):
    """Labeled CCR and tracking fields on an eDocket or hearing detail page."""

    model_config = ConfigDict(extra="forbid")

    ccr_citation: str
    ccr_rule_affected: str
    tracking_number: str
    title: str | None = None
    hearing_date: date | None = None
    effective_date: date | None = None
    document_urls: list[str] = Field(default_factory=list)
    source_evidence: str
    source_url: str

    @field_validator("source_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Require an official detail URL."""

        return official_sos_url(value)

    @field_validator("document_urls")
    @classmethod
    def validate_documents(cls, values: list[str]) -> list[str]:
        """Require official document URLs."""

        return [official_sos_url(value) for value in values]


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    order: int
    parent: _Node | None = field(default=None, repr=False)
    children: list[_Node | str] = field(default_factory=list)

    def text(self) -> str:
        if self.tag in {"script", "style"}:
            return ""
        return _clean(" ".join(c if isinstance(c, str) else c.text() for c in self.children))

    def nodes(self, tag: str | None = None) -> list[_Node]:
        result: list[_Node] = []
        for child in self.children:
            if isinstance(child, _Node):
                if tag is None or child.tag == tag:
                    result.append(child)
                result.extend(child.nodes(tag))
        return result


class _Document(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root", {}, 0)
        self.stack = [self.root]
        self.counter = 0
        self.feed(html)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.counter += 1
        node = _Node(tag, {key: value or "" for key, value in attrs}, self.counter, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def parse_register_index(html: str, index_url: str) -> list[RegisterPublication]:
    """Discover dated HTML issues from an official Register index, failing closed."""

    official_sos_url(index_url)
    doc = _checked_document(html, "colorado register")
    requested_year = parse_qs(urlparse(index_url).query).get("pyear", [])
    issues: dict[date, RegisterPublication] = {}
    for link in doc.root.nodes("a"):
        href = link.attrs.get("href", "")
        url = urljoin(index_url, href)
        if urlparse(url).path.casefold() != "/ccr/registercontents.do":
            continue
        official_sos_url(url)
        values = parse_qs(urlparse(url).query).get("publicationDay", [])
        if len(values) != 1:
            raise RegisterParseError("Issue link is missing its unique publicationDay")
        try:
            published = datetime.strptime(values[0], "%m/%d/%Y").date()
        except ValueError as exc:
            raise RegisterParseError(f"Invalid Register publication date: {values[0]}") from exc
        if requested_year and requested_year != [str(published.year)]:
            raise RegisterParseError("Register index returned a different publication year")
        candidate = RegisterPublication(
            title=f"Colorado Register {published.isoformat()}",
            publication_date=published.isoformat(), url=url,
        )
        if published in issues and str(issues[published].url) != str(candidate.url):
            raise RegisterParseError(f"Conflicting issue links for {published}")
        issues[published] = candidate
    if not issues:
        raise RegisterParseError("Register index has no dated HTML publication links")
    return [issues[day] for day in sorted(issues)]


def parse_register_issue(
    html: str, publication_date: date, source_url: str,
) -> list[DailyNoticeRow]:
    """Read rulemaking table columns exactly; retain unresolved proposal rows."""

    official_sos_url(source_url)
    doc = _checked_document(html, "colorado register")
    _check_publication_date(doc, publication_date, source_url)
    headings = _headings(doc)
    rows: list[DailyNoticeRow] = []
    known_tables = 0
    for table in doc.root.nodes("table"):
        table_rows = _table_rows(table)
        header_rows = [row for row in table_rows if any(c.tag == "th" for c in _cells(row))]
        if not header_rows:
            continue
        if len(header_rows) != 1:
            raise RegisterParseError("Register table has ambiguous header rows")
        headers = [_clean(cell.text()).casefold() for cell in _cells(header_rows[0])]
        section = _section_before(table, headings)
        section_key = section.casefold()
        if section_key in _SKIP_SECTIONS:
            continue
        notice_type = _SECTIONS.get(section_key)
        if notice_type is None:
            if any("rule" in header or "agency" in header for header in headers):
                raise RegisterParseError(f"Unrecognized rule table section: {section!r}")
            continue
        expected = _expected_headers(notice_type)
        if headers != expected:
            raise RegisterParseError(f"Unexpected columns in {section}: {headers}")
        known_tables += 1
        for table_row in table_rows:
            if table_row is header_rows[0]:
                continue
            cells = _cells(table_row)
            if not cells:
                continue
            if len(cells) != len(headers):
                raise RegisterParseError(
                    f"Malformed row in {section}: expected {len(headers)} cells"
                )
            by_header = dict(zip(headers, cells))
            if not any(cell.text() for cell in cells):
                raise RegisterParseError(f"Unexpected empty data row in {section}")
            title_header = {"proposed": "proposed rules", "terminated": "ccr #"}.get(
                notice_type, "rules adopted",
            )
            title = by_header[title_header].text()
            ccr = _single_ccr(title, required=notice_type != "proposed")
            tracking, edocket, hearing, opinion = _tracking_links(table_row, html, source_url)
            if notice_type == "proposed" and not tracking:
                raise RegisterParseError("Proposed row has no traceable tracking identifier")
            evidence = " | ".join(
                f"{header}: {cell.text()}" for header, cell in zip(headers, cells)
            )
            rows.append(DailyNoticeRow(
                notice_type=notice_type,
                department=by_header["department"].text(),
                agency=by_header["agency"].text(),
                title=title,
                ccr_citation=ccr,
                ccr_rule_affected=ccr.replace(" ", "_") if ccr else None,
                edocket_tracking_number=tracking, edocket_url=edocket,
                hearing_detail_url=hearing, opinion_url=opinion,
                document_urls=_document_links(table_row, source_url),
                hearing_date=_column_date(by_header, "hearing"),
                effective_date=_column_date(by_header, "effective date"),
                expiration_date=_column_date(by_header, "expiration date"),
                termination_date=_column_date(by_header, "termination date"),
                publication_date=publication_date, section=section,
                row_number=len(rows) + 1, source_evidence=evidence, source_url=source_url,
            ))
    if not known_tables:
        raise RegisterParseError("Register issue has no recognized rulemaking tables")
    # Explicit empty tables with recognized columns are valid; a missing table is not.
    return rows


def parse_edocket_detail(html: str, source_url: str) -> DailyEdocketDetail:
    """Resolve CCR only from labeled fields on an official hearing/eDocket page."""

    official_sos_url(source_url)
    doc = _checked_document(html)
    labeled: dict[str, str] = {}
    evidence: list[str] = []
    for table in doc.root.nodes("table"):
        for row in _table_rows(table):
            cells = _cells(row)
            if len(cells) != 2:
                continue
            label = cells[0].text().rstrip(":").casefold()
            if label not in {"ccr number", "tracking number", "rule title", "effective date"}:
                continue
            value = cells[1].text()
            if label in labeled and labeled[label] != value:
                raise RegisterParseError(f"Conflicting detail field: {label}")
            labeled[label] = value
            evidence.append(f"{cells[0].text()}: {value}")
    ccr = _single_ccr(labeled.get("ccr number", ""), required=True)
    tracking = labeled.get("tracking number", "")
    if not _TRACKING.fullmatch(tracking):
        raise RegisterParseError("Detail has no valid labeled Tracking Number")
    query = parse_qs(urlparse(source_url).query)
    requested = query.get("trackingNum", query.get("trackingNumber", []))
    if requested and requested != [tracking]:
        raise RegisterParseError("Detail tracking number differs from requested source")
    assert ccr is not None
    return DailyEdocketDetail(
        ccr_citation=ccr, ccr_rule_affected=ccr.replace(" ", "_"),
        tracking_number=tracking, title=labeled.get("rule title"),
        effective_date=(
            _parse_date(labeled["effective date"]) if labeled.get("effective date") else None
        ),
        document_urls=_document_links(doc.root, source_url),
        source_evidence=" | ".join(evidence), source_url=source_url,
    )


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _checked_document(html: str, required: str | None = None) -> _Document:
    lowered = html.casefold()
    markers = ("access denied", "cf-wrapper", "attention required", "enable cookies")
    if any(marker in lowered for marker in markers):
        raise RegisterParseError("Source returned an access challenge")
    doc = _Document(html)
    if not doc.root.text() or (required and required not in doc.root.text().casefold()):
        raise RegisterParseError("Unexpected or empty source page")
    return doc


def _check_publication_date(doc: _Document, published: date, source_url: str) -> None:
    requested = parse_qs(urlparse(source_url).query).get("publicationDay", [])
    if requested and (len(requested) != 1 or _parse_date(requested[0]) != published):
        raise RegisterParseError("Issue publication date differs from requested source")
    for node in doc.root.nodes("p"):
        match = re.match(r"([A-Za-z]+ \d{1,2}, \d{4})\s*-\s*Volume\b", node.text())
        if match:
            try:
                stated = datetime.strptime(match.group(1), "%B %d, %Y").date()
            except ValueError as exc:
                raise RegisterParseError("Invalid issue publication heading") from exc
            if stated != published:
                raise RegisterParseError("Issue publication heading differs from requested source")


def _headings(doc: _Document) -> list[tuple[int, str]]:
    return [(node.order, node.text()) for node in doc.root.nodes()
            if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}
            or (node.tag in {"p", "div"} and "pagehead" in node.attrs.get("class", ""))]


def _section_before(table: _Node, headings: list[tuple[int, str]]) -> str:
    eligible = [text for order, text in headings if order < table.order]
    return eligible[-1] if eligible else ""


def _table_rows(table: _Node) -> list[_Node]:
    rows: list[_Node] = []
    for row in table.nodes("tr"):
        ancestor = row.parent
        while ancestor is not None and ancestor.tag != "table":
            ancestor = ancestor.parent
        if ancestor is table:
            rows.append(row)
    return rows


def _cells(row: _Node) -> list[_Node]:
    return [node for node in row.children if isinstance(node, _Node) and node.tag in {"td", "th"}]


def _expected_headers(notice_type: str) -> list[str]:
    if notice_type == "proposed":
        return ["department", "agency", "proposed rules", "hearing"]
    if notice_type == "terminated":
        return [
            "department", "agency", "ccr #", "tracking #", "termination date",
            "reason for termination",
        ]
    if notice_type == "emergency":
        return [
            "department", "agency", "rules adopted", "justification", "ag opinion",
            "effective date", "expiration date",
        ]
    return ["department", "agency", "rules adopted", "ag opinion", "effective date"]


def _column_date(cells: dict[str, _Node], column: str) -> date | None:
    if column not in cells:
        return None
    text = cells[column].text()
    return _parse_date(text) if text else None


def _parse_date(text: str) -> date:
    matches = _DATE.findall(text)
    if len(matches) != 1:
        raise RegisterParseError(f"Expected one explicit source date: {text!r}")
    try:
        return datetime.strptime(matches[0], "%m/%d/%Y").date()
    except ValueError as exc:
        raise RegisterParseError(f"Invalid source date: {text!r}") from exc


def _single_ccr(text: str, *, required: bool) -> str | None:
    matches = sorted({_clean(match.group()).upper() for match in _CCR.finditer(text)})
    if len(matches) > 1 or (required and not matches):
        raise RegisterParseError(f"Expected one explicit CCR citation: {text!r}")
    return matches[0] if matches else None


def _document_links(node: _Node, source_url: str) -> list[str]:
    links: set[str] = set()
    for anchor in node.nodes("a"):
        href = anchor.attrs.get("href", "")
        if re.search(r"\.(?:pdf|docx?|rtf|txt)(?:\?|$)", href, re.IGNORECASE):
            links.add(official_sos_url(urljoin(source_url, href)))
    return sorted(links)


def _tracking_links(
    row: _Node, html: str, source_url: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    tracking: set[str] = set()
    edocket = hearing = opinion = None
    for anchor in row.nodes("a"):
        href = anchor.attrs.get("href", "")
        parsed = urlparse(urljoin(source_url, href))
        if parsed.path.casefold() == "/ccr/edocketdetails.do":
            values = parse_qs(parsed.query).get("trackingNum", [])
            if len(values) != 1:
                raise RegisterParseError("eDocket link missing tracking number")
            tracking.add(values[0])
            edocket = official_sos_url(urljoin(source_url, href))
        click = anchor.attrs.get("onclick", "")
        for function, prefix in (
            ("OpenDetailsWindow", "/CCR/DisplayHearingDetails.do?trackingNumber="),
            ("DisplayOpinion", "/CCR/Opinion.do?forview=true&trackingNum="),
        ):
            match = re.fullmatch(rf"\s*{function}\(['\"](\d{{4}}-\d{{5}})['\"]\)\s*;?\s*", click)
            if match:
                # Follow only the URL template actually declared by this source page.
                template = rf"window\.open\(\s*['\"]{re.escape(prefix)}['\"]\s*\+"
                if not re.search(template, html):
                    raise RegisterParseError(f"Source does not declare the {function} URL template")
                tracking.add(match.group(1))
                url = official_sos_url(urljoin(source_url, prefix + match.group(1)))
                if function == "OpenDetailsWindow":
                    hearing = url
                else:
                    opinion = url
    if len(tracking) > 1 or any(not _TRACKING.fullmatch(value) for value in tracking):
        raise RegisterParseError("Conflicting or invalid row tracking numbers")
    return next(iter(tracking), None), edocket, hearing, opinion
