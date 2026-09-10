"""Validate a local-authority collection ledger without certifying current law.

Every authority has the same investigation checklist. A category may be outside
an authority's powers, but that must be investigated, not silently omitted. This
first contract deliberately has no 'complete' or 'verified current' state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import pymupdf
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from geode.utils.file_io import atomic_write_json, atomic_write_text

LOGGER = logging.getLogger(__name__)
CATEGORIES = (
    "identity_service_area", "codified_rules", "adopted_changes", "land_use_zoning",
    "building_fire", "permits_licenses", "fees", "taxes", "health_environment",
    "roads_utilities", "enforcement_appeals", "policies_guidance",
)
MAX_SOURCE_BYTES = 30_000_000
MAX_LEDGER_BYTES = 8_000_000
# These are reviewed source locations for this bounded batch, not a crawler allowlist.
OFFICIAL_HOSTS = {
    "CO-COUNTY-JEFFERSON": {"jeffco.us", "www.jeffco.us"},
    "CO-COUNTY-CLEAR_CREEK": {"clearcreekcounty.us", "www.clearcreekcounty.us"},
    "CO-MUNICIPAL-GOLDEN": {"www.cityofgolden.gov", "www.cityofgolden.net"},
    "CO-MUNICIPAL-GEORGETOWN": {"www.townofgeorgetown.us"},
    "CO-DISTRICT-DENVER_WATER": {"www.denverwater.org"},
    "CO-DISTRICT-WEST_METRO_FIRE": {"www.westmetrofire.org"},
    "directory": {"www2.census.gov", "tigerweb.geo.census.gov", "data.colorado.gov",
                  "dola.colorado.gov"},
}
DELEGATED_PREFIXES = {
    "CO-MUNICIPAL-GOLDEN": (
        "https://library.municode.com/co/golden",
        "https://cms3.revize.com/revize/goldenco/",
    ),
    "CO-MUNICIPAL-GEORGETOWN": (
        "https://library.municode.com/co/georgetown",
        "https://cms7files.revize.com/georgetownco/",
    ),
}


class LedgerModel(BaseModel):
    """Reject extra fields, blank text, and accidental unvalidated assignments."""

    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, str_min_length=1,
        validate_assignment=True,
    )


class EvidenceSource(LedgerModel):
    """One preserved source; format/hash verification is separate from legal review."""

    source_id: str
    authority_id: str | None
    title: str
    url: str
    final_url: str
    retrieved_at: datetime
    archive_path: str = Field(
        pattern=r"^_RAW_ARCHIVE/local/(coverage|research|reacquisition)/"
                r"[a-f0-9]{64}\.(pdf|html|txt|json)$"
    )
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0, le=MAX_SOURCE_BYTES, strict=True)
    media_type: Literal["pdf", "html", "txt", "json"]
    kind: Literal["directory", "catalog", "legal_text", "fee_schedule", "guidance", "form"]
    extraction_status: Literal[
        "not_assessed", "text_layer_present", "ocr_required"
    ] = "not_assessed"
    pdf_pages: int | None = Field(default=None, ge=1, strict=True)
    categories: list[str] = Field(min_length=1)
    linked_from_source_id: str | None = None
    publisher_export_manifest: str | None = Field(
        default=None,
        pattern=r"^_CONTROL_PLANE/MUNICIPAL_EXPORTS_[0-9]{4}-[0-9]{2}-[0-9]{2}\.json$",
    )
    provenance_notes: str
    currentness_notes: str
    legal_currentness: Literal["not_verified"] = "not_verified"
    legal_review: Literal["pending"] = "pending"

    @field_validator("retrieved_at")
    @classmethod
    def aware_timestamp(cls, value: datetime) -> datetime:
        """Require an actual retrieval timestamp with an explicit timezone."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Retrieval timestamp requires a timezone")
        return value

    @model_validator(mode="after")
    def source_contract(self) -> EvidenceSource:
        """Constrain source locations, archive names, and category assignments."""
        if (Path(self.archive_path).stem != self.sha256
                or Path(self.archive_path).suffix != "." + self.media_type):
            raise ValueError("Archive filename must match the digest and media type")
        if (len(set(self.categories)) != len(self.categories)
                or set(self.categories) - set(CATEGORIES)):
            raise ValueError("Source categories must be unique checklist categories")
        if self.publisher_export_manifest and (
            self.authority_id not in {"CO-MUNICIPAL-GOLDEN", "CO-MUNICIPAL-GEORGETOWN"}
            or self.kind != "legal_text" or self.media_type not in {"pdf", "json"}
            or not self.linked_from_source_id or self.url != self.final_url
        ):
            raise ValueError("Publisher exports require scoped legal content and official referral")
        for value in (self.url, self.final_url):
            parsed = urlparse(value)
            if (parsed.scheme != "https" or parsed.username or parsed.password
                    or parsed.port not in {None, 443}
                    or any(ord(char) < 32 for char in value)
                    or ".." in unquote(parsed.path).split("/")):
                raise ValueError("Evidence URLs must be ordinary HTTPS URLs")
            owner = self.authority_id or "directory"
            if self.publisher_export_manifest:
                expected = (
                    "https://mcclibrary.blob.core.usgovcloudapi.net/"
                    "publication-official-copy-pdfs/768/Final.pdf"
                    if owner == "CO-MUNICIPAL-GOLDEN" else
                    "https://library.municode.com/api/CodesContent/docIds"
                )
                if (value.split("?", 1)[0] != expected
                        or (owner == "CO-MUNICIPAL-GOLDEN" and parsed.query)
                        or parsed.fragment):
                    raise ValueError("Publisher export endpoint is outside the scoped authority")
                continue
            if parsed.hostname not in OFFICIAL_HOSTS.get(owner, set()):
                prefixes = DELEGATED_PREFIXES.get(owner, ())
                if not any(value == p.rstrip("/") or value.startswith(p.rstrip("/") + "/")
                           for p in prefixes):
                    raise ValueError("Evidence URL is outside reviewed authority locations")
                if not self.linked_from_source_id:
                    raise ValueError("Delegated sources require a preserved referring source")
        if self.authority_id is None and self.kind != "directory":
            raise ValueError("Statewide evidence must be directory evidence")
        if self.media_type != "pdf" and (self.pdf_pages is not None
                                         or self.extraction_status != "not_assessed"):
            raise ValueError("PDF page and text-layer metadata require a PDF source")
        return self


class CategoryCheck(LedgerModel):
    """A work item, never an assertion that an entire subject is legally complete."""

    category: str
    source_ids: list[str] = Field(default_factory=list)
    collection: Literal[
        "missing", "supporting_evidence_only", "legal_documents_preserved"
    ] = "missing"
    completeness: Literal["not_assessed", "partial"] = "not_assessed"
    currentness: Literal["not_verified"] = "not_verified"
    legal_review: Literal["pending"] = "pending"
    gap: str
    next_action: str


class AuthorityCoverage(LedgerModel):
    """An identified authority candidate with explicit identity and scope limitations."""

    authority_id: str = Field(pattern=r"^CO-(COUNTY|MUNICIPAL|DISTRICT)-[A-Z0-9_-]+$")
    name: str
    level: Literal["county", "municipal", "district", "public_provider"]
    identity_basis: str
    identity_source_ids: list[str] = Field(default_factory=list)
    active_government: Literal["not_verified"] = "not_verified"
    pilot: bool = False
    checklist: list[CategoryCheck]

    @model_validator(mode="after")
    def complete_checklist(self) -> AuthorityCoverage:
        """Keep every investigation category, even where applicability is unresolved."""
        categories = [row.category for row in self.checklist]
        if len(categories) != len(CATEGORIES) or set(categories) != set(CATEGORIES):
            raise ValueError("Each authority needs the entire category checklist exactly once")
        expected = "DISTRICT" if self.level == "public_provider" else self.level.upper()
        if not self.authority_id.startswith(f"CO-{expected}-"):
            raise ValueError("Authority ID and declared level disagree")
        return self


class DirectoryAssessment(LedgerModel):
    """A dated source population, distinct from today's operating authorities."""

    level: Literal["county", "municipal", "district"]
    reference_count: int | None = Field(default=None, ge=1, strict=True)
    source_ids: list[str] = Field(min_length=1)
    source_as_of: str
    findings: list[str] = Field(min_length=1)
    current_universe_verified: Literal[False] = False


class CoverageLedger(LedgerModel):
    """A bounded inventory of evidence and remaining collection work."""

    schema_version: Literal[1] = 1
    prepared_at: datetime
    baseline_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    scope: str
    directory_assessments: list[DirectoryAssessment]
    sources: list[EvidenceSource]
    authorities: list[AuthorityCoverage] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @field_validator("prepared_at")
    @classmethod
    def aware_preparation(cls, value: datetime) -> datetime:
        """Require a timezone on this inventory's preparation date."""
        return EvidenceSource.aware_timestamp(value)

    @model_validator(mode="after")
    def references(self) -> CoverageLedger:
        """Reject duplicates, orphan evidence, cross-authority links and inflated status."""
        sources = {s.source_id: s for s in self.sources}
        authorities = {a.authority_id: a for a in self.authorities}
        if len(sources) != len(self.sources) or len(authorities) != len(self.authorities):
            raise ValueError("Source and authority IDs must be unique")
        used = set()
        for source in self.sources:
            if source.authority_id is not None and source.authority_id not in authorities:
                raise ValueError("Source owner must be in the authority roster")
            parent = source.linked_from_source_id
            if parent is not None:
                if (parent not in sources or parent == source.source_id
                        or sources[parent].authority_id != source.authority_id):
                    raise ValueError("Referring source must exist and have the same owner")
                used.add(parent)
            seen = {source.source_id}
            while parent is not None:
                if parent in seen or parent not in sources:
                    raise ValueError("Source provenance cannot contain cycles or unknown parents")
                seen.add(parent)
                parent = sources[parent].linked_from_source_id
        for assessment in self.directory_assessments:
            for key in assessment.source_ids:
                if key not in sources or sources[key].kind != "directory":
                    raise ValueError("Directory assessments require directory evidence")
                used.add(key)
        for authority in self.authorities:
            for key in authority.identity_source_ids:
                if key not in sources or sources[key].kind != "directory":
                    raise ValueError("Identity references require directory evidence")
                used.add(key)
            for row in authority.checklist:
                if len(set(row.source_ids)) != len(row.source_ids):
                    raise ValueError("Category evidence IDs must not be repeated")
                for key in row.source_ids:
                    if (key not in sources or sources[key].authority_id != authority.authority_id
                            or row.category not in sources[key].categories):
                        raise ValueError("Category evidence must match its authority and subject")
                    used.add(key)
                legal = any(sources[k].kind in {"legal_text", "fee_schedule"}
                            for k in row.source_ids)
                expected = ("legal_documents_preserved" if legal else
                            "supporting_evidence_only" if row.source_ids else "missing")
                if row.collection != expected:
                    raise ValueError("Collection status must follow actual evidence types")
                if row.source_ids and row.completeness != "partial":
                    raise ValueError("Collected evidence must remain explicitly partial")
        if used != set(sources):
            raise ValueError("Every preserved source must serve an explicit checklist or directory")
        return self


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.base: str | None = None
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Collect document-base and anchor URLs without executing page code."""
        values = dict(attrs)
        href = values.get("href")
        if tag == "base" and href and self.base is None:
            self.base = href
        elif tag == "a" and href:
            self.links.append(href)


def _catalog_targets(parent: EvidenceSource, body: bytes) -> set[str]:
    """Resolve observed anchors, including a wrapper that explicitly names a city URL."""
    parser = _Links()
    parser.feed(body.decode("utf-8", errors="replace"))
    base = urljoin(parent.final_url, parser.base or "")
    targets = {unquote(urljoin(base, href)) for href in parser.links}
    for href in parser.links:
        wrapper = urlparse(urljoin(base, href))
        if (wrapper.scheme != "https" or wrapper.netloc != "www.google.com"
                or wrapper.path != "/url"):
            continue
        target = parse_qs(wrapper.query).get("q", [])
        if (len(target) == 1 and urlparse(target[0]).scheme == "https"
                and urlparse(target[0]).hostname
                in OFFICIAL_HOSTS.get(parent.authority_id or "directory", set())):
            targets.add(unquote(target[0]))
    return targets


def _validate_publisher_export(
    source: EvidenceSource, parent: EvidenceSource, root: Path, cache: dict[str, object]
) -> None:
    """Require an offline publisher proof matching this exact source and official parent."""
    from geode.pipeline.municipal_code_export import (
        MunicipalExportManifest, validate_municipal_exports,
    )

    relative = source.publisher_export_manifest
    assert relative is not None
    if relative not in cache:
        path = root / relative
        if any(part.is_symlink() for part in (path.absolute(), *path.absolute().parents)):
            raise ValueError("Publisher manifest path cannot contain symlinks")
        with path.open("rb") as stream:
            body = stream.read(MAX_LEDGER_BYTES + 1)
        if len(body) > MAX_LEDGER_BYTES:
            raise ValueError("Publisher manifest exceeds bounded read limit")
        manifest = MunicipalExportManifest.model_validate_json(body)
        validate_municipal_exports(manifest, root)
        cache[relative] = manifest
    manifest = cache[relative]
    refs = {item.source_id: item for item in manifest.sources}
    exports = [item for item in manifest.exports if item.authority_id == source.authority_id]
    if len(exports) != 1 or exports[0].content != source.source_id:
        raise ValueError("Publisher manifest does not identify this authority and content")
    export = exports[0]
    content = refs[export.content]
    referral = refs[export.official_referral]
    for actual, proof in ((source, content), (parent, referral)):
        if (actual.source_id != proof.source_id or actual.final_url != proof.url
                or actual.archive_path != proof.archive_path or actual.sha256 != proof.sha256
                or actual.size_bytes != proof.size_bytes or actual.media_type != proof.media_type
                or actual.retrieved_at != proof.retrieved_at):
            raise ValueError("Publisher proof differs from ledger source or official referral")


def validate_ledger_evidence(ledger: CoverageLedger, root: Path) -> None:
    """Check archive confinement, exact hashes, sizes, and usable source formats offline."""
    ledger = CoverageLedger.model_validate(ledger.model_dump())
    if any(path.is_symlink() for path in (root.absolute(), *root.absolute().parents)):
        raise ValueError("Evidence root and its ancestors cannot contain symlinks")
    parents = {s.linked_from_source_id for s in ledger.sources}
    contents: dict[str, bytes] = {}
    for source in ledger.sources:
        path = root
        if path.is_symlink():
            raise ValueError("Evidence root cannot be a symlink")
        for part in Path(source.archive_path).parts:
            path = path / part
            if path.is_symlink():
                raise ValueError("Evidence path cannot contain symlinks")
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing confined source file: {source.source_id}")
        with path.open("rb") as stream:
            body = stream.read(MAX_SOURCE_BYTES + 1)
        if (len(body) != source.size_bytes
                or hashlib.sha256(body).hexdigest() != source.sha256):
            raise ValueError(f"Source size/hash mismatch: {source.source_id}")
        if source.source_id in parents and source.media_type == "html":
            contents[source.source_id] = body
        if source.media_type == "pdf":
            if not body.startswith(b"%PDF-") or not body.rstrip().endswith(b"%%EOF"):
                raise ValueError("Incomplete PDF source")
            try:
                with pymupdf.open(stream=body, filetype="pdf") as doc:
                    if doc.is_encrypted or doc.is_repaired or doc.page_count < 1:
                        raise ValueError("Unreadable, repaired, encrypted, or empty PDF")
                    if source.pdf_pages is not None and source.pdf_pages != doc.page_count:
                        raise ValueError("PDF page count disagrees with the source")
                    if source.extraction_status != "not_assessed":
                        has_text = any(page.get_text().strip() for page in doc)
                        if has_text != (source.extraction_status == "text_layer_present"):
                            raise ValueError("PDF text-layer status disagrees with the source")
            except Exception as exc:
                raise ValueError(f"Invalid PDF source: {source.source_id}") from exc
        elif source.media_type == "html":
            if (not re.search(rb"<(?:!doctype\s+html|html)\b", body[:131072], re.I)
                    or not re.search(rb"</html\s*>", body, re.I)
                    or re.search(rb"<title[^>]*>\s*(access denied|just a moment)"
                                 rb"|_cf_chl_opt|cf-chl-widget", body[:131072], re.I)):
                raise ValueError("HTML is missing or is an access challenge")
            if (b"municode" in source.final_url.encode().lower()
                    and source.kind not in {"catalog", "directory"}):
                raise ValueError("Municode app shells are supporting evidence only in this batch")
        else:
            text = body.decode("utf-8-sig")
            if source.media_type == "json":
                json.loads(text)
            elif not any(c in text for c in ("|", "\t")) or len(text.splitlines()) < 2:
                raise ValueError("Directory text must be a delimited table with data rows")
    sources = {s.source_id: s for s in ledger.sources}
    publisher_cache: dict[str, object] = {}
    for source in ledger.sources:
        if source.publisher_export_manifest:
            _validate_publisher_export(source, sources[source.linked_from_source_id],
                                       root, publisher_cache)
            continue
        if all(urlparse(u).hostname in OFFICIAL_HOSTS[source.authority_id or "directory"]
               for u in (source.url, source.final_url)):
            continue
        parent = sources[source.linked_from_source_id]
        if parent.media_type != "html":
            raise ValueError("Delegated sources require an HTML referring catalog")
        if unquote(source.url) not in _catalog_targets(parent, contents[parent.source_id]):
            raise ValueError(f"Delegated source link absent from catalog: {source.source_id}")


def render_ledger_report(ledger: CoverageLedger) -> str:
    """Produce a concise report with denominator limits and each pilot's next actions."""
    counts = Counter(a.level for a in ledger.authorities)
    rows = [row for authority in ledger.authorities for row in authority.checklist]
    collections = Counter(row.collection for row in rows)
    lines = ["---", "title: Local coverage collection ledger", "status: partial",
             f"prepared_at: {ledger.prepared_at.isoformat()}", "---", "",
             "# Local coverage collection ledger", "", ledger.scope, "",
             f"Roster: {dict(sorted(counts.items()))}. Investigation items: {len(rows)}.",
             f"Preserved sources: {len(ledger.sources)}; collection states: {dict(collections)}.",
             "Legally current categories: 0. Legally reviewed categories: 0.", "",
             "Preservation is byte evidence, not a completeness or current-law certificate.", "",
             "## Directory reconciliation", ""]
    for item in ledger.directory_assessments:
        count = str(item.reference_count) if item.reference_count else "unresolved"
        lines.append(f"- {item.level}: reference count {count}; {item.source_as_of}. "
                     + " ".join(item.findings))
    for authority in ledger.authorities:
        if not authority.pilot:
            continue
        lines.extend(["", f"## {authority.name}", "", authority.identity_basis, "",
                      "| Category | Collection | Remaining work |",
                      "|---|---|---|"])
        for row in authority.checklist:
            action = (row.gap + " " + row.next_action).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {row.category} | {row.collection} | {action} |")
    lines.extend(["", "## Limits", ""] + [f"- {item}" for item in ledger.limitations])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Validate the ledger and optionally write a snapshotted JSON and Markdown report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        with args.ledger.open("rb") as stream:
            body = stream.read(MAX_LEDGER_BYTES + 1)
        if len(body) > MAX_LEDGER_BYTES:
            raise ValueError("Ledger exceeds the bounded 8 MB read limit")
        ledger = CoverageLedger.model_validate_json(body)
        validate_ledger_evidence(ledger, args.root)
        if args.output_dir:
            output = (args.root / args.output_dir).resolve()
            if not output.is_relative_to(args.root.resolve()):
                raise ValueError("Report output must remain within the project root")
            atomic_write_json(output / "local-coverage.json", ledger, args.root)
            atomic_write_text(output / "local-coverage.md", render_ledger_report(ledger), args.root)
    except (OSError, ValueError) as exc:
        LOGGER.error("Local coverage validation failed: %s", exc)
        return 1
    LOGGER.info("Validated %d authority checklists and %d sources; current law unverified",
                len(ledger.authorities), len(ledger.sources))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
