"""Offline proof and native-text extraction for two explicitly scoped municipal exports.

An intact publisher edition is not a certification of current law. Later ordinances,
incorporated codes, maps, and applicability still require substantive review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import tempfile
import unicodedata
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator, Literal
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import pymupdf
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LOGGER = logging.getLogger(__name__)
LIBRARY = "https://library.municode.com"
STORAGE = "https://mcclibrary.blob.core.usgovcloudapi.net"
MAX_SOURCE_BYTES = 50_000_000
PUBLIC_ENDPOINTS = {
    "clients": "Clients/stateAbbr: stateAbbr",
    "publications": "ClientContent/{ClientID}",
    "latest_job": "Jobs/latest/{ProductID}",
    "toc": "codesToc: productId, jobId",
    "pdf": "PublicationPdfDownload/{publicationId}",
    "print": "CodesContent/docIds: productId, jobId, docIds, showChanges",
}
PROFILES = {
    "CO-MUNICIPAL-GOLDEN": ("Golden", 2384, 15366, 768, "www.cityofgolden.gov"),
    "CO-MUNICIPAL-GEORGETOWN": (
        "Georgetown", 19056, 18162, 4206, "www.townofgeorgetown.us"
    ),
}
Authority = Literal["CO-MUNICIPAL-GOLDEN", "CO-MUNICIPAL-GEORGETOWN"]
Digest = str


class ExportModel(BaseModel):
    """Strict, immutable evidence metadata without implicit legal conclusions."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceRef(ExportModel):
    """A hash-bound original, or explicitly redacted publisher URL response."""

    source_id: str = Field(min_length=1)
    url: str
    archive_path: str
    sha256: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0, le=MAX_SOURCE_BYTES, strict=True)
    retrieved_at: datetime
    media_type: Literal["html", "json", "pdf", "js", "png"]
    representation: Literal[
        "original", "signed_url_redacted", "public_client_endpoint_summary"
    ] = "original"
    request_query_redacted: bool = False

    @field_validator("retrieved_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        """Keep actual retrieval instants timezone-aware."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Retrieval timestamp requires a timezone")
        return value

    @model_validator(mode="after")
    def safe_identity(self) -> SourceRef:
        """Reject non-content-addressed paths and non-public URL forms."""
        path = Path(self.archive_path)
        parsed = urlsplit(self.url)
        if (path.is_absolute() or ".." in path.parts or path.stem != self.sha256
                or path.suffix != "." + self.media_type):
            raise ValueError("Archive path must be relative and content-addressed")
        if (parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment
                or parsed.port not in {None, 443}
                or ".." in unquote(parsed.path).split("/")
                or any(ord(char) < 32 for char in self.url)
                or any(key.lower() in {"sig", "se", "sp", "sv"}
                       for key in parse_qs(parsed.query))):
            raise ValueError("Source URL must be public HTTPS without signed query tokens")
        return self


class EditionExcerpt(ExportModel):
    """A physical-page excerpt connecting the downloaded PDF to its edition."""

    page: int = Field(ge=1, strict=True)
    excerpt: str = Field(min_length=1)


class EndpointInspection(ExportModel):
    """Derived endpoint inspection; the excluded vendor script hash is not recomputed."""

    schema_version: Literal[1] = 1
    script_url: str
    original_response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    endpoint_bindings: dict[str, str]
    original_script_preserved_in_durable_corpus: Literal[False] = False
    original_script_hash_recomputed_offline: Literal[False] = False


class MunicipalExport(ExportModel):
    """One complete publisher export with explicit unresolved current-law limitations."""

    authority_id: Authority
    official_referral: str
    publications: str
    latest_job: str
    toc: str
    content: str
    download_response: str | None = None
    images: list[str] = Field(default_factory=list, max_length=30)
    job_id: int = Field(gt=0, strict=True)
    expected_units: int = Field(gt=0, le=10_000, strict=True)
    edition_statement: str = Field(min_length=1)
    pdf_edition_excerpts: list[EditionExcerpt] = Field(default_factory=list)
    legal_currentness: Literal["not_reconciled"] = "not_reconciled"
    review_required: Literal[True] = True
    limitations: list[str] = Field(min_length=1)


class MunicipalExportManifest(ExportModel):
    """A bounded proof chain for Golden and Georgetown, not a general crawler policy."""

    schema_version: Literal[1] = 1
    sources: list[SourceRef] = Field(min_length=1, max_length=40)
    clients: str
    library_shell: str
    library_script: str
    exports: list[MunicipalExport] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def references(self) -> MunicipalExportManifest:
        """Require unique identities and every explicitly referenced source."""
        ids = {source.source_id for source in self.sources}
        if len(ids) != len(self.sources):
            raise ValueError("Duplicate source IDs")
        if len({item.authority_id for item in self.exports}) != len(self.exports):
            raise ValueError("Duplicate authority export")
        required = {self.clients, self.library_shell, self.library_script}
        for item in self.exports:
            required.update([item.official_referral, item.publications, item.latest_job,
                             item.toc, item.content, *item.images])
            if item.download_response:
                required.add(item.download_response)
        if required != ids:
            raise ValueError("Manifest sources must exactly match referenced sources")
        return self


class ExtractedText(ExportModel):
    """Native text retains source page/node location without interpreting legal duties."""

    authority_id: Authority
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ordinal: int = Field(ge=1, strict=True)
    kind: Literal["pdf_page", "publisher_node"]
    page: int | None = Field(default=None, ge=1, strict=True)
    node_id: str | None = None
    title: str | None = None
    text: str
    image_urls: list[str] = Field(default_factory=list)
    extraction: Literal["pymupdf_native", "html_text"]
    research_only: Literal[True] = True
    review_required: Literal[True] = True
    legal_currentness: Literal["not_reconciled"] = "not_reconciled"

    @model_validator(mode="after")
    def location(self) -> ExtractedText:
        """A record must cite exactly one physical page or one publisher node."""
        if self.kind == "pdf_page":
            if self.page != self.ordinal or self.node_id or self.extraction != "pymupdf_native":
                raise ValueError("PDF text needs its exact physical page")
        elif self.page is not None or not self.node_id or self.extraction != "html_text":
            raise ValueError("Publisher text needs its exact node")
        return self


class ExportValidation(ExportModel):
    """Counts describe preserved exports, never complete or currently effective law."""

    authority_id: Authority
    source_id: str
    source_sha256: str
    units: int
    top_level_nodes: int
    images_referenced: int
    images_preserved: int
    missing_images: list[str]
    edition_statement: str
    legal_currentness: Literal["not_reconciled"] = "not_reconciled"
    review_required: Literal[True] = True
    signed_response_original_hash_recomputed: bool | None = None
    client_implementation_original_hash_recomputed: Literal[False] = False


class _HTML(HTMLParser):
    def __init__(self, body: str) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.images: list[str] = []
        self.bases: list[str] = []
        self.parts: list[str] = []
        self.hidden = 0
        self.feed(body)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for target, key, collection in [("a", "href", self.links),
                                        ("script", "src", self.scripts),
                                        ("img", "src", self.images),
                                        ("base", "href", self.bases)]:
            if tag == target and values.get(key):
                collection.append(str(values[key]))
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "div", "li", "td", "th", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def _normal(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Publisher text metadata must be a string")
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _read(root: Path, source: SourceRef) -> bytes:
    path = root.absolute() / source.archive_path
    if any(parent.is_symlink() for parent in [path, *path.parents]):
        raise ValueError("Evidence path contains a symlink")
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Missing ordinary evidence file")
    with path.open("rb") as stream:
        body = stream.read(MAX_SOURCE_BYTES + 1)
    if len(body) != source.size_bytes or hashlib.sha256(body).hexdigest() != source.sha256:
        raise ValueError("Source size/hash mismatch")
    return body


def _confined(root: Path, path: Path) -> Path:
    absolute = path.absolute()
    if (".." in absolute.parts
            or any(parent.is_symlink() for parent in [absolute, *absolute.parents])
            or not absolute.resolve().is_relative_to(root.resolve())):
        raise ValueError("Path must be inside the evidence root without symlinks or traversal")
    return absolute


def _at(source: SourceRef, url: str, media: str) -> None:
    if source.url != url or source.media_type != media:
        raise ValueError(f"Unexpected source endpoint or format: {source.source_id}")


def _html_links(source: SourceRef, body: bytes, scripts: bool = False) -> list[str]:
    if not re.search(rb"<html\b", body[:131072], re.I) or not re.search(
            rb"</html\s*>\s*$", body, re.I):
        raise ValueError("Referring evidence must be complete HTML")
    parsed = _HTML(body.decode("utf-8"))
    if len(parsed.bases) > 1:
        raise ValueError("Ambiguous HTML base")
    base = urljoin(source.url, parsed.bases[0]) if parsed.bases else source.url
    if urlsplit(base).netloc != urlsplit(source.url).netloc:
        raise ValueError("HTML base changes source authority")
    return [urlsplit(urljoin(base, value))._replace(fragment="").geturl()
            for value in (parsed.scripts if scripts else parsed.links)]


def _print_chunks(body: bytes, roots: list[dict[str, Any]], units: int) -> list[dict[str, Any]]:
    chunks = json.loads(body)
    if not isinstance(chunks, list) or len(chunks) != units:
        raise ValueError("Publisher print has wrong chunk count")
    required = {"Id", "Title", "Content", "Footnotes", "DocOrderId", "NodeDepth"}
    for chunk in chunks:
        if not isinstance(chunk, dict) or not required <= chunk.keys():
            raise ValueError("Malformed publisher chunk")
        if (not isinstance(chunk["Id"], str) or not chunk["Id"]
                or not isinstance(chunk["Title"], str)
                or not isinstance(chunk["Content"], str)
                or not isinstance(chunk["Footnotes"], (str, type(None)))
                or type(chunk["DocOrderId"]) is not int
                or type(chunk["NodeDepth"]) is not int or chunk["NodeDepth"] < 1):
            raise ValueError("Invalid publisher chunk identity or content")
    if (len({chunk["Id"] for chunk in chunks}) != units
            or [chunk["DocOrderId"] for chunk in chunks] != list(range(1, units + 1))):
        raise ValueError("Publisher chunks must have unique IDs and complete ordered ordinals")
    top = [(c["Id"], c["Title"], c["DocOrderId"]) for c in chunks if c["NodeDepth"] == 1]
    expected = [(r["Id"], r["Heading"], r["DocOrderId"]) for r in roots]
    if top != expected or not roots or roots[-1]["DocOrderId"] != units:
        raise ValueError("Publisher print does not match the full table of contents")
    return chunks


def validate_municipal_exports(
    manifest: MunicipalExportManifest, root: Path,
) -> list[ExportValidation]:
    """Verify bounded original bytes and publisher identity chains entirely offline."""
    manifest = MunicipalExportManifest.model_validate(manifest.model_dump())
    sources = {s.source_id: s for s in manifest.sources}
    if sum(s.size_bytes for s in manifest.sources) > 100_000_000:
        raise ValueError("Export manifest exceeds 100 MB")
    for source in manifest.sources:
        _read(root, source)
        is_download = any(source.source_id == item.download_response for item in manifest.exports)
        is_signed_pdf = any(source.source_id == item.content
                            and item.authority_id == "CO-MUNICIPAL-GOLDEN"
                            for item in manifest.exports)
        representation = ("signed_url_redacted" if is_download else
                          "public_client_endpoint_summary" if source.source_id ==
                          manifest.library_script else "original")
        if (source.representation != representation
                or source.request_query_redacted != is_signed_pdf):
            raise ValueError("Redaction metadata does not match the source's exact role")
    clients_source = sources[manifest.clients]
    _at(clients_source, LIBRARY + "/api/Clients/stateAbbr?stateAbbr=co", "json")
    clients = json.loads(_read(root, clients_source))
    shell, script = sources[manifest.library_shell], sources[manifest.library_script]
    _at(shell, LIBRARY + "/co/golden/codes/municipal_code", "html")
    if script.url not in _html_links(shell, _read(root, shell), scripts=True):
        raise ValueError("Publisher shell does not refer to preserved public client")
    inspection = EndpointInspection.model_validate_json(_read(root, script))
    if (urlsplit(script.url).netloc != "library.municode.com" or script.media_type != "json"
            or urlsplit(script.url).path != "/dist/js/all/all.min.js"
            or inspection.script_url != script.url
            or inspection.endpoint_bindings != PUBLIC_ENDPOINTS):
        raise ValueError("Invalid derived public endpoint inspection evidence")
    results = []
    for item in manifest.exports:
        name, client_id, product_id, publication_id, official_host = PROFILES[item.authority_id]
        matching = [c for c in clients if c.get("ClientID") == client_id]
        if (len(matching) != 1 or matching[0].get("ClientName") != name
                or matching[0].get("State", {}).get("StateAbbreviation") != "CO"):
            raise ValueError("Colorado client identity does not match municipality")
        official = sources[item.official_referral]
        public_code = f"{LIBRARY}/co/{name.lower()}/codes/municipal_code"
        if (urlsplit(official.url).netloc != official_host or official.media_type != "html"
                or public_code not in _html_links(official, _read(root, official))):
            raise ValueError("Official municipality does not refer to its publisher code")
        publication, job_source = sources[item.publications], sources[item.latest_job]
        _at(publication, f"{LIBRARY}/api/ClientContent/{client_id}", "json")
        products = json.loads(_read(root, publication)).get("codes", [])
        products = [p for p in products if p.get("productId") == product_id]
        if (len(products) != 1 or products[0].get("publicationId") != publication_id
                or products[0].get("productName") != "Municipal Code"):
            raise ValueError("Client publication/product binding is invalid")
        _at(job_source, f"{LIBRARY}/api/Jobs/latest/{product_id}", "json")
        job = json.loads(_read(root, job_source))
        if (job.get("ProductId") != product_id or job.get("Id") != item.job_id
                or job.get("IsLatest") is not True
                or _normal(item.edition_statement) not in _normal(job.get("BannerText", ""))):
            raise ValueError("Latest-job identity or edition statement mismatch")
        toc_source = sources[item.toc]
        _at(toc_source, f"{LIBRARY}/api/codesToc?productId={product_id}&jobId={item.job_id}",
            "json")
        toc = json.loads(_read(root, toc_source))
        roots = toc.get("Children", [])
        if (toc.get("Id") != str(product_id) or not roots
                or len({r["Id"] for r in roots}) != len(roots)
                or any(r.get("ParentId") != str(product_id) or r.get("NodeDepth") != 1
                       for r in roots)):
            raise ValueError("TOC root identity mismatch")
        content = sources[item.content]
        image_urls: set[str] = set()
        redacted = None
        if name == "Golden":
            stable = f"{STORAGE}/publication-official-copy-pdfs/{publication_id}/Final.pdf"
            _at(content, stable, "pdf")
            if (not item.download_response or products[0].get("hasPdf") is not True
                    or products[0].get("hasPdfDownloadEnabled") is not True or item.images
                    or not item.pdf_edition_excerpts or not content.request_query_redacted):
                raise ValueError("Golden export lacks enabled download/edition proof")
            download = sources[item.download_response]
            _at(download, f"{LIBRARY}/api/PublicationPdfDownload/{publication_id}", "json")
            proof = json.loads(_read(root, download))
            if (download.representation != "signed_url_redacted"
                    or proof.get("stable_download_url") != stable
                    or proof.get("signed_query_redacted") is not True
                    or not re.fullmatch(r"[a-f0-9]{64}",
                                        proof.get("original_response_sha256", ""))):
                raise ValueError("Invalid explicitly redacted publisher response")
            redacted = False
            body = _read(root, content)
            if not body.startswith(b"%PDF-") or not body.rstrip().endswith(b"%%EOF"):
                raise ValueError("Truncated publisher PDF")
            with pymupdf.open(stream=body, filetype="pdf") as pdf:
                if pdf.is_repaired or pdf.is_encrypted or pdf.page_count != item.expected_units:
                    raise ValueError("Invalid PDF page count or integrity")
                pages = [page.get_text() for page in pdf]
                heading_text = re.sub(r"[^a-z0-9]", "", "".join(pages).lower())
                if any(re.sub(r"[^a-z0-9]", "", r["Heading"].lower()) not in heading_text
                       for r in roots):
                    raise ValueError("A top-level publisher heading is absent from the PDF")
                for excerpt in item.pdf_edition_excerpts:
                    if (excerpt.page > pdf.page_count or _normal(excerpt.excerpt) not in
                            _normal(pages[excerpt.page - 1])):
                        raise ValueError("PDF edition excerpt absent from cited page")
        else:
            if item.download_response or item.pdf_edition_excerpts:
                raise ValueError("Georgetown uses public print, not a disabled PDF export")
            parsed = urlsplit(content.url)
            query = parse_qs(parsed.query)
            if (parsed.scheme + "://" + parsed.netloc + parsed.path !=
                    LIBRARY + "/api/CodesContent/docIds" or content.media_type != "json"
                    or query != {"productId": [str(product_id)], "jobId": [str(item.job_id)],
                                 "docIds": [r["Id"] for r in roots], "showChanges": ["false"]}):
                raise ValueError("Print query must select every TOC root without changes")
            chunks = _print_chunks(_read(root, content), roots, item.expected_units)
            for chunk in chunks:
                image_urls.update(_HTML(chunk["Content"] + (chunk["Footnotes"] or "")).images)
        image_sources = [sources[key] for key in item.images]
        if len({s.url for s in image_sources}) != len(image_sources):
            raise ValueError("Duplicate image references")
        for source in image_sources:
            prefix = f"{STORAGE}/codecontent/{product_id}/{item.job_id}/"
            if (source.url not in image_urls or not source.url.startswith(prefix)
                    or source.media_type != "png"):
                raise ValueError("Image is not explicitly linked to this publication/job")
            body = _read(root, source)
            if not body.startswith(b"\x89PNG\r\n\x1a\n") or not body.endswith(b"IEND\xaeB`\x82"):
                raise ValueError("Truncated PNG dependency")
            pymupdf.Pixmap(body)
        results.append(ExportValidation(
            authority_id=item.authority_id, source_id=content.source_id,
            source_sha256=content.sha256, units=item.expected_units, top_level_nodes=len(roots),
            images_referenced=len(image_urls), images_preserved=len(image_sources),
            missing_images=sorted(image_urls - {source.url for source in image_sources}),
            edition_statement=item.edition_statement,
            signed_response_original_hash_recomputed=redacted,
        ))
    return results


def iter_export_text(
    manifest: MunicipalExportManifest, root: Path,
) -> Iterator[ExtractedText]:
    """Validate first, then yield page/node text with immutable source provenance."""
    validate_municipal_exports(manifest, root)
    sources = {source.source_id: source for source in manifest.sources}
    for item in manifest.exports:
        source = sources[item.content]
        common = dict(authority_id=item.authority_id, source_id=source.source_id,
                      source_sha256=source.sha256)
        if source.media_type == "pdf":
            with pymupdf.open(stream=_read(root, source), filetype="pdf") as pdf:
                for number, page in enumerate(pdf, 1):
                    yield ExtractedText(**common, ordinal=number, kind="pdf_page", page=number,
                                        text=page.get_text(), extraction="pymupdf_native")
        else:
            for chunk in json.loads(_read(root, source)):
                html = _HTML(chunk["Content"] + (chunk["Footnotes"] or ""))
                yield ExtractedText(
                    **common, ordinal=chunk["DocOrderId"], kind="publisher_node",
                    node_id=chunk["Id"], title=chunk["Title"], text="".join(html.parts).strip(),
                    image_urls=list(dict.fromkeys(html.images)), extraction="html_text",
                )


def write_export_text(manifest: MunicipalExportManifest, root: Path, output: Path) -> int:
    """Atomically create a new text directory; refuse any existing destination."""
    output = _confined(root, output)
    if output.resolve().is_relative_to(root.resolve() / "_RAW_ARCHIVE"):
        raise ValueError("Derived text must never be written inside the raw archive")
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("Output must be a new directory inside an existing parent")
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary) / "text"
        stage.mkdir()
        count = 0
        with (stage / "text.jsonl").open("w", encoding="utf-8") as stream:
            for record in iter_export_text(manifest, root):
                stream.write(record.model_dump_json() + "\n")
                count += 1
        os.replace(stage, output)
    return count


def validate_saved_export_text(
    manifest: MunicipalExportManifest, root: Path, text_path: Path,
) -> int:
    """Stream saved typed text against regeneration, rejecting omissions or modifications."""
    text_path = _confined(root, text_path)
    count = 0
    with text_path.open("r", encoding="utf-8") as stream:
        for expected in iter_export_text(manifest, root):
            line = stream.readline(2_000_001)
            if not line or len(line) > 2_000_000:
                raise ValueError("Missing or oversized saved text record")
            actual = ExtractedText.model_validate_json(line)
            if actual != expected:
                raise ValueError("Saved text differs from its exact source regeneration")
            count += 1
        if stream.read(1):
            raise ValueError("Saved text contains extra records or trailing data")
    return count


def main(argv: list[str] | None = None) -> int:
    """Validate exports offline and optionally create a new research-text directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    outputs = parser.add_mutually_exclusive_group()
    outputs.add_argument("--output", type=Path)
    outputs.add_argument("--text", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        with _confined(args.root, args.manifest).open("rb") as stream:
            body = stream.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Manifest exceeds 2 MB")
        manifest = MunicipalExportManifest.model_validate_json(body)
        results = validate_municipal_exports(manifest, args.root)
        if args.output:
            write_export_text(manifest, args.root, args.output)
        if args.text:
            validate_saved_export_text(manifest, args.root, args.text)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        LOGGER.error("Municipal export validation failed: %s", exc)
        return 1
    LOGGER.info("Validated %d publisher exports; %d physical pages/nodes; legal review pending",
                len(results), sum(item.units for item in results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
