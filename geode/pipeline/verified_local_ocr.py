"""Complete-page machine OCR with immutable source and derived-byte verification.

These receipts verify provenance and page coverage, never legal accuracy. Apple
Vision runs only during extraction; offline validation needs no macOS service.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

import pymupdf
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from geode.pipeline.local_coverage import CoverageLedger, EvidenceSource

LOGGER = logging.getLogger(__name__)
DIGEST = r"^[a-f0-9]{64}$"
ENGINE_SETTINGS = {
    "recognition_level": "accurate", "recognition_languages": ["en-US"],
    "uses_language_correction": False, "automatically_detects_language": False,
    "minimum_text_height": 0, "uses_cpu_only": True,
    "bounding_box_origin": "bottom_left", "reading_order": "engine_observation_order",
}
PRIORITY = [
    "cc-building-r26-19", "georgetown-2026-ordinance-3-original",
    "georgetown-2026-ordinance-4-original", "georgetown-2026-ordinance-5-original",
    "georgetown-2026-fees-original", "west-metro-2024-adoption", "cc-ordinance-16803",
]


def sha256(body: bytes) -> str:
    """Hash exact bytes without text normalization."""
    return hashlib.sha256(body).hexdigest()


class OCRModel(BaseModel):
    """Strict metadata; preserve OCR strings exactly, including whitespace."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class OCRLine(OCRModel):
    """One engine observation in its original order and normalized image bounds."""

    text: str
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    bbox: tuple[float, float, float, float]

    @field_validator("bbox")
    @classmethod
    def bounds(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        """Reject invalid boxes instead of silently clipping engine output."""
        if (any(not 0 <= item <= 1 for item in value)
                or value[0] + value[2] > 1.000001 or value[1] + value[3] > 1.000001):
            raise ValueError("OCR bounding box is outside the page")
        return value


class EngineInfo(OCRModel):
    """Actual engine revision, OS version, adapter bytes and recognition settings."""

    name: Literal["Apple Vision"] = "Apple Vision"
    version: str = Field(min_length=1)
    revision: Literal[3] = 3
    adapter_sha256: str = Field(pattern=DIGEST)
    settings: dict = Field(default_factory=lambda: dict(ENGINE_SETTINGS))

    @field_validator("settings")
    @classmethod
    def exact_settings(cls, value: dict) -> dict:
        """Keep the adapter's fixed settings explicit and verifiable."""
        if value != ENGINE_SETTINGS:
            raise ValueError("Unexpected OCR engine settings")
        return value


class EngineResult(OCRModel):
    """Validated output from the one-image native adapter."""

    revision: Literal[3]
    os_version: str = Field(min_length=1)
    lines: list[OCRLine]


class RenderingInfo(OCRModel):
    """Rasterization settings, distinct from cross-platform reproducibility."""

    engine: Literal["PyMuPDF"] = "PyMuPDF"
    version: str = Field(min_length=1)
    dpi: int = Field(ge=150, le=600, strict=True)
    colorspace: Literal["RGB"] = "RGB"
    scope: Literal["entire_displayed_pdf_page"] = "entire_displayed_pdf_page"


def page_flags(lines: list[OCRLine]) -> list[str]:
    """Return triage signals; high confidence is not proof of accurate text."""
    text = "\n".join(line.text for line in lines)
    flags = []
    if not text.strip():
        flags.append("no_text")
    elif sum(character.isalnum() for character in text) < 30:
        flags.append("sparse_text")
    if any(line.confidence < 0.8 for line in lines):
        flags.append("low_engine_confidence")
    if "\ufffd" in text:
        flags.append("replacement_character")
    return flags


class OCRPage(OCRModel):
    """One full physical page's uncorrected machine recognition and provenance."""

    schema_version: Literal[1] = 1
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=DIGEST)
    source_page_number: int = Field(ge=1, strict=True)
    source_page_count: int = Field(ge=1, strict=True)
    status: Literal["machine_ocr_unreviewed"] = "machine_ocr_unreviewed"
    text: str
    text_sha256: str = Field(pattern=DIGEST)
    lines: list[OCRLine]
    engine: EngineInfo
    rendering: RenderingInfo
    image_sha256: str = Field(pattern=DIGEST)
    image_width: int = Field(gt=0, strict=True)
    image_height: int = Field(gt=0, strict=True)
    flags: list[str]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Require timezone-aware derivation time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("OCR timestamp requires a timezone")
        return value

    @model_validator(mode="after")
    def integrity(self) -> OCRPage:
        """Bind text, flags and physical page bounds without asserting correctness."""
        if self.source_page_number > self.source_page_count:
            raise ValueError("OCR page exceeds source page count")
        if self.text != "\n".join(line.text for line in self.lines):
            raise ValueError("OCR text differs from complete engine observations")
        if sha256(self.text.encode("utf-8")) != self.text_sha256:
            raise ValueError("OCR text hash mismatch")
        if self.flags != page_flags(self.lines):
            raise ValueError("OCR triage flags do not match page observations")
        return self


class PageFile(OCRModel):
    """Exact derived page-file identity in source order."""

    source_page_number: int = Field(ge=1, strict=True)
    path: str = Field(pattern=r"^[a-f0-9]{64}/page-[0-9]{4,6}\.json$")
    sha256: str = Field(pattern=DIGEST)
    size_bytes: int = Field(gt=0, strict=True)
    text_sha256: str = Field(pattern=DIGEST)


class PageFailure(OCRModel):
    """An explicit failed page, never silently omitted from coverage."""

    source_page_number: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=1)


class OCRManifest(OCRModel):
    """All source pages accounted for, with blank recognition still unresolved."""

    schema_version: Literal[1] = 1
    source_id: str
    source_path: str
    source_sha256: str = Field(pattern=DIGEST)
    source_size_bytes: int = Field(gt=0, strict=True)
    source_page_count: int = Field(ge=1, strict=True)
    status: Literal["fully_collected", "failed"]
    pages: list[PageFile]
    failures: list[PageFailure]
    blank_pages: list[int]
    flagged_pages: list[int]
    boundary: Literal["Machine OCR only; legal accuracy and currency remain unreviewed."] = (
        "Machine OCR only; legal accuracy and currency remain unreviewed."
    )

    @model_validator(mode="after")
    def coverage(self) -> OCRManifest:
        """Reject missing, duplicate, unordered pages and optimistic completion."""
        numbers = [page.source_page_number for page in self.pages]
        failed = [page.source_page_number for page in self.failures]
        if numbers != sorted(set(numbers)) or failed != sorted(set(failed)):
            raise ValueError("OCR manifest pages must be unique and ordered")
        if sorted(numbers + failed) != list(range(1, self.source_page_count + 1)):
            raise ValueError("OCR manifest does not account for every source page")
        if any(p.path != f"{self.source_sha256}/page-{p.source_page_number:04d}.json"
               for p in self.pages):
            raise ValueError("OCR page path does not match source and page")
        if (self.blank_pages != sorted(set(self.blank_pages))
                or self.flagged_pages != sorted(set(self.flagged_pages))
                or set(self.blank_pages) - set(self.flagged_pages)
                or set(self.flagged_pages) - set(numbers)):
            raise ValueError("OCR flagged/blank page references are inconsistent")
        expected = "failed" if self.failures or self.blank_pages else "fully_collected"
        if self.status != expected:
            raise ValueError("OCR completion status conceals failed or blank pages")
        return self


class CollectionSelection(OCRModel):
    """Exact whole-source scope, retained when the live ledger later grows."""

    schema_version: Literal[1] = 1
    mode: Literal["all_ledger_scans_at_collection", "explicit_sources"]
    source_ids: list[str] = Field(min_length=1)
    ledger_sha256: str = Field(pattern=DIGEST)

    @field_validator("source_ids")
    @classmethod
    def unique_ids(cls, value: list[str]) -> list[str]:
        """Reject duplicated or empty source selections."""
        if len(value) != len(set(value)) or any(not item.strip() for item in value):
            raise ValueError("OCR selection requires unique nonempty source IDs")
        return value


class CollectionSummary(OCRModel):
    """Machine collection totals, with no legal or full-page accuracy assertion."""

    source_count: int
    expected_pages: int
    page_records: int
    failed_pages: int
    blank_pages: int
    flagged_pages: int
    fully_collected_sources: int
    failed_sources: int
    status: Literal["fully_collected", "failed"]


def _root_without_symlinks(path: Path) -> Path:
    absolute = path.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ValueError("Evidence roots and all ancestors must be free of symlinks")
    return absolute.resolve()


def _ordinary(root: Path, relative: str) -> Path:
    root = _root_without_symlinks(root)
    path = root / relative
    if (Path(relative).is_absolute() or ".." in Path(relative).parts
            or not path.resolve().is_relative_to(root.resolve())):
        raise ValueError("Evidence path escapes its declared root")
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError("Evidence symlinks are not permitted")
        cursor = cursor.parent
    if not path.is_file():
        raise ValueError(f"Evidence file is missing: {relative}")
    return path


def _source_body(root: Path, source: EvidenceSource) -> bytes:
    path = _ordinary(root, source.archive_path)
    with path.open("rb") as stream:
        body = stream.read(source.size_bytes + 1)
    if (len(body) != source.size_bytes or sha256(body) != source.sha256
            or not body.startswith(b"%PDF-") or not body.rstrip().endswith(b"%%EOF")):
        raise ValueError(f"Source PDF identity or completeness failed: {source.source_id}")
    with pymupdf.open(stream=body, filetype="pdf") as document:
        if (document.is_repaired or document.is_encrypted
                or document.page_count != source.pdf_pages or not document.page_count):
            raise ValueError(f"Source PDF structure/page count failed: {source.source_id}")
    return body


def _write_new(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"Refusing to overwrite derived evidence: {path.name}")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(body)
    temporary.replace(path)


def _json_bytes(model: OCRModel) -> bytes:
    return (model.model_dump_json(indent=2) + "\n").encode("utf-8")


class VisionEngine:
    """Call the compiled one-page Apple Vision adapter with a hard timeout."""

    def __init__(self, executable: Path, timeout: float = 60) -> None:
        """Bind the adapter's actual binary bytes and a positive timeout."""
        if timeout <= 0 or not executable.is_file() or executable.is_symlink():
            raise ValueError("OCR requires an ordinary adapter binary and positive timeout")
        self.executable = executable.resolve()
        self.adapter_sha256 = sha256(executable.read_bytes())
        self.timeout = timeout

    def __call__(self, image_path: Path) -> tuple[EngineInfo, list[OCRLine]]:
        """Preserve every observation; never truncate output or remove weak text."""
        if sha256(self.executable.read_bytes()) != self.adapter_sha256:
            raise ValueError("OCR adapter binary changed during the run")
        result = subprocess.run(
            [str(self.executable), str(image_path)], capture_output=True,
            check=False, timeout=self.timeout,
        )
        if result.returncode:
            raise ValueError(f"OCR engine exited {result.returncode}: "
                             f"{result.stderr.decode('utf-8', errors='replace')}")
        value = EngineResult.model_validate_json(result.stdout)
        return EngineInfo(version=value.os_version, adapter_sha256=self.adapter_sha256), value.lines


def _validate_manifest(root: Path, output: Path, source: EvidenceSource) -> OCRManifest:
    path = _ordinary(output, f"{source.sha256}/manifest.json")
    manifest = OCRManifest.model_validate_json(path.read_bytes())
    if (manifest.source_id != source.source_id or manifest.source_path != source.archive_path
            or manifest.source_sha256 != source.sha256
            or manifest.source_size_bytes != source.size_bytes
            or manifest.source_page_count != source.pdf_pages):
        raise ValueError("OCR manifest source identity differs from the ledger")
    flagged, blank = [], []
    profile = None
    for record in manifest.pages:
        body = _ordinary(output, record.path).read_bytes()
        if len(body) != record.size_bytes or sha256(body) != record.sha256:
            raise ValueError("OCR page-file hash or length mismatch")
        page = OCRPage.model_validate_json(body)
        if (page.source_id != source.source_id or page.source_sha256 != source.sha256
                or page.source_page_number != record.source_page_number
                or page.source_page_count != source.pdf_pages
                or page.text_sha256 != record.text_sha256):
            raise ValueError("OCR page identity differs from its manifest")
        current = (page.engine.model_dump(), page.rendering.model_dump())
        if profile is not None and current != profile:
            raise ValueError("OCR engine/rendering profile changed between source pages")
        profile = current
        if page.flags:
            flagged.append(page.source_page_number)
        if "no_text" in page.flags:
            blank.append(page.source_page_number)
    if flagged != manifest.flagged_pages or blank != manifest.blank_pages:
        raise ValueError("OCR manifest flags differ from actual page records")
    return manifest


def _sources(
    ledger_path: Path, source_ids: list[str] | None = None,
) -> list[EvidenceSource]:
    ledger = CoverageLedger.model_validate_json(ledger_path.read_bytes())
    if source_ids is None:
        sources = [s for s in ledger.sources if s.extraction_status == "ocr_required"]
    else:
        by_id = {source.source_id: source for source in ledger.sources}
        if len(source_ids) != len(set(source_ids)) or set(source_ids) - set(by_id):
            raise ValueError("OCR selection contains duplicate or unknown source IDs")
        sources = [by_id[identity] for identity in source_ids]
    if len({source.sha256 for source in sources}) != len(sources):
        raise ValueError("Selected source IDs share PDF bytes; select one identity per original")
    if not sources or any(s.media_type != "pdf" or not s.pdf_pages for s in sources):
        raise ValueError("Ledger must identify selected PDFs with exact page counts")
    return sorted(sources, key=lambda s: (
        PRIORITY.index(s.source_id) if s.source_id in PRIORITY else len(PRIORITY), s.source_id))


def _validated_summary(
    root: Path, output: Path, ledger_path: Path, *, require_report: bool,
) -> CollectionSummary:
    """Verify complete source/page coverage and exact bytes offline, without rerendering.

    A successful validation may describe an explicitly failed collection. Callers
    must check `status`; blank recognition is never certified fully collected.
    """
    root, output = _root_without_symlinks(root), _root_without_symlinks(output)
    manifests = []
    selection = CollectionSelection.model_validate_json(
        _ordinary(output, "selection.json").read_bytes())
    for source in _sources(ledger_path, selection.source_ids):
        _source_body(root, source)
        manifests.append(_validate_manifest(root, output, source))
    expected = {"selection.json"}
    if require_report:
        expected.add("report.json")
    for manifest in manifests:
        expected.add(f"{manifest.source_sha256}/manifest.json")
        expected.update(page.path for page in manifest.pages)
    actual = {str(path.relative_to(output)) for path in output.rglob("*.json")}
    if actual != expected:
        raise ValueError("OCR collection JSON files differ from declared complete receipts")
    failed = sum(m.status == "failed" for m in manifests)
    summary = CollectionSummary(
        source_count=len(manifests), expected_pages=sum(m.source_page_count for m in manifests),
        page_records=sum(len(m.pages) for m in manifests),
        failed_pages=sum(len(m.failures) for m in manifests),
        blank_pages=sum(len(m.blank_pages) for m in manifests),
        flagged_pages=sum(len(m.flagged_pages) for m in manifests),
        fully_collected_sources=len(manifests) - failed, failed_sources=failed,
        status="failed" if failed else "fully_collected",
    )
    if require_report:
        saved = CollectionSummary.model_validate_json(_ordinary(output, "report.json").read_bytes())
        if saved != summary:
            raise ValueError("OCR saved report differs from verified source/page totals")
    return summary


def validate_ocr_collection(root: Path, output: Path, ledger_path: Path) -> CollectionSummary:
    """Verify selected source/page bytes, coverage and summary offline, without rerendering.

    Integrity validation can return status ``failed`` for explicitly blank or failed
    pages. It never certifies those collections as fully collected or legally correct.
    """
    return _validated_summary(root, output, ledger_path, require_report=True)


def collect_ocr(
    root: Path, output: Path, ledger_path: Path,
    engine: Callable[[Path], tuple[EngineInfo, list[OCRLine]]], *, dpi: int = 300,
    source_ids: list[str] | None = None,
) -> CollectionSummary:
    """Recognize every ledger scan page, preserving failures and immutable page receipts."""
    root, output = _root_without_symlinks(root), _root_without_symlinks(output)
    raw = root / "_RAW_ARCHIVE"
    if (not output.is_relative_to(root) or output == root
            or output == raw or raw in output.parents):
        raise ValueError("OCR output must be separate from originals and the repository root")
    rendering = RenderingInfo(version=pymupdf.VersionBind, dpi=dpi)
    sources = _sources(ledger_path, source_ids)
    if output.exists():
        raise ValueError("Use a new output directory; prior OCR evidence is immutable")
    for source in sources:
        _source_body(root, source)
    selection = CollectionSelection(
        mode="explicit_sources" if source_ids is not None else "all_ledger_scans_at_collection",
        source_ids=[source.source_id for source in sources],
        ledger_sha256=sha256(ledger_path.read_bytes()),
    )
    _write_new(output / "selection.json", _json_bytes(selection))
    for source in sources:
        pages, failures, blank, flagged = [], [], [], []
        with pymupdf.open(stream=_source_body(root, source), filetype="pdf") as document:
            for number, pdf_page in enumerate(document, start=1):
                try:
                    pixmap = pdf_page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                    image_body = pixmap.tobytes("png")
                    image_path = output / "_renders" / source.sha256 / f"page-{number:04d}.png"
                    _write_new(image_path, image_body)
                    info, lines = engine(image_path)
                    lines = [OCRLine.model_validate(line) for line in lines]
                    text = "\n".join(line.text for line in lines)
                    page = OCRPage(
                        source_id=source.source_id, source_sha256=source.sha256,
                        source_page_number=number, source_page_count=document.page_count,
                        text=text, text_sha256=sha256(text.encode("utf-8")), lines=lines,
                        engine=info, rendering=rendering, image_sha256=sha256(image_body),
                        image_width=pixmap.width, image_height=pixmap.height,
                        flags=page_flags(lines), created_at=datetime.now(timezone.utc),
                    )
                    body = _json_bytes(page)
                    relative = f"{source.sha256}/page-{number:04d}.json"
                    _write_new(output / relative, body)
                    pages.append(PageFile(source_page_number=number, path=relative,
                                          sha256=sha256(body), size_bytes=len(body),
                                          text_sha256=page.text_sha256))
                    if page.flags:
                        flagged.append(number)
                    if "no_text" in page.flags:
                        blank.append(number)
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    failures.append(PageFailure(source_page_number=number, reason=str(exc)))
                LOGGER.info("OCR %s page %d/%d", source.source_id, number, document.page_count)
        manifest = OCRManifest(
            source_id=source.source_id, source_path=source.archive_path,
            source_sha256=source.sha256, source_size_bytes=source.size_bytes,
            source_page_count=source.pdf_pages,
            status="failed" if failures or blank else "fully_collected",
            pages=pages, failures=failures, blank_pages=blank, flagged_pages=flagged,
        )
        _write_new(output / source.sha256 / "manifest.json", _json_bytes(manifest))
    summary = _validated_summary(root, output, ledger_path, require_report=False)
    _write_new(output / "report.json", _json_bytes(summary))
    return summary


def main(argv: list[str] | None = None) -> int:
    """Collect or validate unreviewed OCR without editing raw sources or the ledger."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-executable", type=Path)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--source-id", action="append", dest="source_ids",
                        help="Select whole PDF sources explicitly; repeat for each ID")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        if args.validate_only:
            summary = validate_ocr_collection(args.root, args.output, args.ledger)
        else:
            if args.engine_executable is None:
                raise ValueError("Extraction requires --engine-executable")
            summary = collect_ocr(args.root, args.output, args.ledger,
                                  VisionEngine(args.engine_executable, args.timeout),
                                  dpi=args.dpi, source_ids=args.source_ids)
    except (OSError, ValueError, RuntimeError) as exc:
        LOGGER.error("OCR evidence failed: %s", exc)
        return 1
    LOGGER.info("OCR collection: %s", summary.model_dump_json())
    return 0 if summary.status == "fully_collected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
