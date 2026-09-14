"""Read-only keyword lookup in one image-reviewed El Paso fee schedule."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = "el-paso-planning-fees-sd011"
PACKAGE = "research/local_review/el-paso-planning-fees-source-review-2026-09-12"
ACCEPTANCE = "docs/audits/FOUR_HOUR_RUN_2026-09-12/EL_PASO_PLANNING_QA/ACCEPTANCE.json"
ACCEPTANCE_SHA = "1f5dd98d1e2dce42abfa82bb151640a441ed465c8f7327d5bc90564a5902dc39"
PINS = {
    "FINAL_MANIFEST.json": "a0d56d11890aaaafd6fd9d143bfe7cfaa2366863c5b86e453228363cb82a891d",
    "FINAL_MANIFEST.schema.json":
        "284d1a039db9824927645b4c56e2637b0b4a9b2d80c960b07e6a518cc231acd6",
    "SOURCE_QA.json": "77416babde5e963f47a76aee0ee7dd16e54d70fcb7019f0ffc2267971df665e6",
    "REVIEWED_GRID.json": "e50428e6a2a141a640ab0f312e1b55cff33f18fc8c9ce0d8a6bbc8822ca8a37a",
    "source/original.pdf":
        "c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12",
    "validate_review.py": "7c14a66b3bbd0c4df362aef6011d59f5fff3b1080838c3e5293ce4a29106805b",
}
EXPECTED_VERIFICATION = {
    "status": "pass", "fee_rows": 104, "footnotes": 15, "general_notes": 3,
    "native_bytes": 0, "ocr_pages": 5, "explicit_unresolved_rows": ["P3-ENG-14"],
    "legal_currentness": "not_verified",
}
CURRENT_REQUEST = re.compile(
    r"\b(current(?:ly)?|today|now|latest|applicab\w*|appl(?:y|ies)|effective|"
    r"legal(?:ly)?|in force|calculate|calculation|owe|total cost)\b|"
    r"^\s*(what|how|is|are|can|may|must|do|does|should|will|would)\b|\?", re.I,
)
BOUNDARY = (
    "Source-only lookup in one 104-row reviewed scan. No fee calculation, applicability or "
    "current-law answer. A missing match does not establish absence, exemption or a zero fee."
)


class StrictModel(BaseModel):
    """Reject unrecognized fields and coercion in the research output."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(StrictModel):
    """Bind exact file bytes to a path."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Inventory(StrictModel):
    """Read the fixed package's closed file inventory before executing its verifier."""

    schema_version: Literal[1]
    files: list[Asset]
    exclusions: Literal["FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only"]


class Cell(StrictModel):
    """Preserve a manual visual cell; its offsets never describe native PDF text."""

    column: Literal["application_type", "application_fee", "project_type", "heading", "page_label"]
    text: str
    state: Literal["visible_text", "visibly_blank", "visible_text_with_clipped_unresolved_tail"]
    pixel_bbox: tuple[int, int, int, int]
    superscript_footnotes: list[int]
    transcript_start_byte: int = Field(ge=0)
    transcript_end_byte: int = Field(ge=0)
    native_start_byte: None
    native_end_byte: None

    @model_validator(mode="after")
    def validate_binding(self) -> Cell:
        """Reject impossible geometry, byte lengths, blank states or note references."""
        x0, y0, x1, y1 = self.pixel_bbox
        if not 0 <= x0 < x1 <= 2200 or not 0 <= y0 < y1 <= 1700:
            raise ValueError("Cell pixel rectangle is outside the reviewed page")
        if self.transcript_end_byte - self.transcript_start_byte != len(self.text.encode()):
            raise ValueError("Visual transcript byte length differs")
        if (self.state == "visibly_blank") != (self.text == ""):
            raise ValueError("Blank-cell state differs")
        if any(n < 1 or n > 15 for n in self.superscript_footnotes):
            raise ValueError("Unknown footnote")
        return self


class Row(StrictModel):
    """Preserve an entire reviewed row and its original relationship identifiers."""

    id: str
    physical_page: int = Field(ge=1, le=5)
    role: Literal["fee_row", "section_header", "column_headers", "title", "footnote",
                  "general_note", "page_label"]
    section_header_id: str | None
    fee_header_id: str | None
    note_id: int | None
    cells: list[Cell] = Field(min_length=1)


class EvidenceBlock(StrictModel):
    """Attach page pixels and authored transcript bytes to one complete reviewed row."""

    row: Row
    source_image: Asset
    visual_transcript: Asset
    transcription_origin: Literal["manual_visual_from_scan"] = "manual_visual_from_scan"
    offset_basis: Literal["reviewed_visual_transcript_utf8_not_pdf_native"] = (
        "reviewed_visual_transcript_utf8_not_pdf_native"
    )


class RequiredContext(StrictModel):
    """Mandatory shared context applies to every returned fee row."""

    source_headers: list[EvidenceBlock]
    table_header: EvidenceBlock
    global_footnote: EvidenceBlock
    general_notes: list[EvidenceBlock]

    @model_validator(mode="after")
    def validate_context(self) -> RequiredContext:
        """Require both source titles, column footnote one and all three General Notes."""
        if [b.row.id for b in self.source_headers] != ["P1-TITLE", "P1-DATE"]:
            raise ValueError("Source headers omitted or reordered")
        header = self.table_header.row
        if header.id != "P1-COLUMNS" or header.cells[1].superscript_footnotes != [1]:
            raise ValueError("Application Fees header footnote omitted")
        if self.global_footnote.row.id != "FN-01":
            raise ValueError("Global footnote one omitted")
        if [b.row.id for b in self.general_notes] != ["GENERAL-1", "GENERAL-2", "GENERAL-3"]:
            raise ValueError("General Notes omitted or reordered")
        return self


class FeeMatch(StrictModel):
    """Return all three cells plus exact section and row-specific footnote context."""

    fee_row: EvidenceBlock
    section_header: EvidenceBlock
    row_footnotes: list[EvidenceBlock]
    section_continues_from_prior_page: bool
    unresolved_clipped_label: bool

    @model_validator(mode="after")
    def validate_associations(self) -> FeeMatch:
        """Reject lost row, section, clipping or superscript associations."""
        row, section = self.fee_row.row, self.section_header.row
        if row.role != "fee_row" or [c.column for c in row.cells] != [
            "application_type", "application_fee", "project_type",
        ]:
            raise ValueError("Complete fee-row columns required")
        if row.section_header_id != section.id or section.role != "section_header":
            raise ValueError("Section header differs")
        if row.fee_header_id != "P1-COLUMNS":
            raise ValueError("Table header differs")
        expected = sorted({n for c in row.cells for n in c.superscript_footnotes})
        if [b.row.note_id for b in self.row_footnotes] != expected:
            raise ValueError("Row footnotes differ")
        if self.section_continues_from_prior_page != (section.physical_page < row.physical_page):
            raise ValueError("Section continuation differs")
        clipped = any(c.state == "visible_text_with_clipped_unresolved_tail" for c in row.cells)
        if self.unresolved_clipped_label != clipped:
            raise ValueError("Clipped-label uncertainty lost")
        return self


class SourceBinding(StrictModel):
    """Keep source claims, received custody and verified legal dates distinct."""

    source_id: Literal["el-paso-planning-fees-sd011"] = SOURCE_ID
    authority_id: Literal["CO-COUNTY-EL_PASO"] = "CO-COUNTY-EL_PASO"
    source_pdf: Asset
    source_review: Asset
    reviewed_grid: Asset
    package_manifest: Asset
    acceptance: Asset
    claimed_source_url: str
    claimed_final_url: str
    acquisition_method: Literal["received_review_package"]
    claimed_http_acquisition_at: str
    verified_http_acquisition_at: None
    actual_repository_received_at: str
    source_printed_date_claim: str
    verified_adoption_date: None
    verified_effective_date: None
    review_completed_at: str
    native_text_bytes: Literal[0] = 0
    fully_legible_complete_extraction: Literal[False] = False
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    limitations: list[str]
    unresolved_regions: list[str]

    @model_validator(mode="after")
    def validate_pins(self) -> SourceBinding:
        """Keep the serialized response bound to this exact accepted evidence set."""
        pairs = [(self.source_pdf, "source/original.pdf"), (self.source_review, "SOURCE_QA.json"),
                 (self.reviewed_grid, "REVIEWED_GRID.json"),
                 (self.package_manifest, "FINAL_MANIFEST.json")]
        if any(asset.sha256 != PINS[name] for asset, name in pairs):
            raise ValueError("Output source/review pin differs")
        if self.acceptance.sha256 != ACCEPTANCE_SHA:
            raise ValueError("Output acceptance pin differs")
        return self


class LookupResult(StrictModel):
    """Machine-readable, source-only results with mandatory shared notes."""

    schema_version: Literal[1] = 1
    status: Literal["matched_rows", "matched_context_only", "no_matching_row", "listed_rows"]
    mode: Literal["source"] = "source"
    source: SourceBinding
    mandatory_context: RequiredContext
    matches: list[FeeMatch] = Field(max_length=104)
    matched_context_ids: list[str]
    scope: Literal[BOUNDARY] = BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False

    @model_validator(mode="after")
    def validate_status(self) -> LookupResult:
        """Prevent duplicate rows or a misleading success/no-match label."""
        ids = [m.fee_row.row.id for m in self.matches]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate matched row")
        if bool(ids) != (self.status in {"matched_rows", "listed_rows"}):
            raise ValueError("Match status differs")
        if self.status == "listed_rows" and len(ids) != 104:
            raise ValueError("Incomplete row listing")
        if self.status == "matched_context_only" and not self.matched_context_ids:
            raise ValueError("Context-only match lacks context")
        return self


class Refusal(StrictModel):
    """Refuse legal/currentness requests without generating fee matches."""

    status: Literal["refused"] = "refused"
    reason: str
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


def _ordinary(path: Path, *, directory: bool = False) -> Path:
    path = path.expanduser().absolute()
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Unsafe path or symlink refused")
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError("Ordinary existing path required")
    return path


def _relative(root: Path, name: str) -> Path:
    rel = Path(name)
    if rel.is_absolute() or ".." in rel.parts or rel.as_posix() != name:
        raise ValueError("Noncanonical package path refused")
    return _ordinary(root / rel)


def _digest(path: Path) -> str:
    with _ordinary(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _asset(path: Path) -> Asset:
    return Asset(path=str(path), sha256=_digest(path), size_bytes=path.stat().st_size)


def _preflight(root: Path) -> Path:
    package = _ordinary(root / PACKAGE, directory=True)
    if _digest(_ordinary(root / ACCEPTANCE)) != ACCEPTANCE_SHA:
        raise ValueError("Review acceptance pin differs")
    for name, expected in PINS.items():
        if _digest(_relative(package, name)) != expected:
            raise ValueError("Pinned review artifact differs: " + name)
    inventory = Inventory.model_validate_json((package / "FINAL_MANIFEST.json").read_bytes())
    names = [ref.path for ref in inventory.files]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate package inventory path")
    expected_files = set(names) | {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}
    expected_dirs = {
        str(parent) for name in expected_files for parent in Path(name).parents
        if str(parent) != "."
    }
    actual_files, actual_dirs = set(), set()
    for path in package.rglob("*"):
        _ordinary(path, directory=path.is_dir())
        (actual_dirs if path.is_dir() else actual_files).add(path.relative_to(package).as_posix())
    # The accepted render preparation left this empty cache; Git omits empty directories.
    if actual_files != expected_files or actual_dirs - expected_dirs - {"render-cache"}:
        raise ValueError("Closed package membership differs")
    for ref in inventory.files:
        path = _relative(package, ref.path)
        if path.stat().st_size != ref.size_bytes or _digest(path) != ref.sha256:
            raise ValueError("Package file hash/size differs: " + ref.path)
    return package


def _run_verifier(package: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(package / "validate_review.py"), "--root", str(package)],
        cwd=package, env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"},
        capture_output=True, text=True, timeout=90, check=False,
    )
    if result.returncode or json.loads(result.stdout) != EXPECTED_VERIFICATION:
        raise ValueError("Pinned source-review verifier did not pass")


def _normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _matches(query: str, text: str) -> bool:
    query, text = _normalized(query), _normalized(text)
    left = r"(?<![\w.,])" if query[0].isdigit() else r"(?<!\w)"
    right = r"(?![\w.,])" if query[-1].isdigit() else r"(?!\w)"
    return re.search(left + re.escape(query) + right, text) is not None


def lookup(
    root: Path, source_id: str, query: str | None = None, *, list_rows: bool = False,
    mode: str = "source",
) -> LookupResult | Refusal:
    """Validate the fixed review, then return exact rows and complete mandatory context."""
    if source_id != SOURCE_ID:
        raise ValueError("Only the fixed El Paso planning-fee source is supported")
    if mode != "source" or (query and CURRENT_REQUEST.search(query)):
        return Refusal(reason=BOUNDARY + " Use a service keyword phrase or list rows.")
    if list_rows == (query is not None) or (query is not None and not query.strip()):
        raise ValueError("Choose a nonempty keyword phrase or list rows")
    if query is not None and len(query) > 200:
        raise ValueError("Keyword phrase exceeds 200 characters")
    root = _ordinary(Path(root), directory=True)
    package = _preflight(root)
    _run_verifier(package)
    _preflight(root)
    qa = json.loads((package / "SOURCE_QA.json").read_bytes())
    grid = json.loads((package / "REVIEWED_GRID.json").read_bytes())
    rows = [Row.model_validate_json(json.dumps(r)) for r in grid["rows"]]
    by_id = {row.id: row for row in rows}
    images = {p["physical_page"]: p["source_image"]["path"] for p in grid["pages"]}
    transcript = _asset(_relative(package, grid["transcript"]["path"]))

    def block(row: Row) -> EvidenceBlock:
        """Bind this reviewed row to the exact page image and visual transcript."""
        image = _asset(_relative(package, images[row.physical_page]))
        return EvidenceBlock(row=row, source_image=image, visual_transcript=transcript)

    context = RequiredContext(
        source_headers=[block(by_id[name]) for name in ["P1-TITLE", "P1-DATE"]],
        table_header=block(by_id["P1-COLUMNS"]), global_footnote=block(by_id["FN-01"]),
        general_notes=[block(by_id[f"GENERAL-{n}"]) for n in [1, 2, 3]],
    )
    matches = []
    for row in rows:
        if row.role != "fee_row":
            continue
        section = by_id[row.section_header_id]
        notes = [by_id[f"FN-{n:02}"] for n in sorted(
            {n for cell in row.cells for n in cell.superscript_footnotes}
        )]
        haystacks = [cell.text for r in [row, section, *notes] for cell in r.cells]
        if list_rows or any(_matches(query, text) for text in haystacks):
            matches.append(FeeMatch(
                fee_row=block(row), section_header=block(section),
                row_footnotes=[block(note) for note in notes],
                section_continues_from_prior_page=section.physical_page < row.physical_page,
                unresolved_clipped_label=row.id in grid["unresolved_row_ids"],
            ))
    shared = [*context.source_headers, context.table_header, context.global_footnote,
              *context.general_notes]
    context_ids = [] if list_rows else [
        b.row.id for b in shared if any(_matches(query, cell.text) for cell in b.row.cells)
    ]
    custody = qa["custody"]
    source = SourceBinding(
        source_pdf=_asset(package / "source/original.pdf"),
        source_review=_asset(package / "SOURCE_QA.json"),
        reviewed_grid=_asset(package / "REVIEWED_GRID.json"),
        package_manifest=_asset(package / "FINAL_MANIFEST.json"),
        acceptance=_asset(root / ACCEPTANCE),
        **{key: custody[key] for key in ["claimed_source_url", "claimed_final_url",
           "acquisition_method", "claimed_http_acquisition_at", "verified_http_acquisition_at",
           "actual_repository_received_at"]},
        source_printed_date_claim=grid["source_date_claim"],
        verified_adoption_date=None, verified_effective_date=None,
        review_completed_at=qa["completed_at"],
        limitations=[*grid["limitations"], *custody["limitations"]],
        unresolved_regions=qa["unresolved_regions"],
    )
    status = "listed_rows" if list_rows else "matched_rows" if matches else (
        "matched_context_only" if context_ids else "no_matching_row"
    )
    return LookupResult(status=status, source=source, mandatory_context=context,
                        matches=matches, matched_context_ids=context_ids)


def _escape(text: str) -> str:
    escaped = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|~$-])", r"\\\1", escaped)


def _link(label: str, path: str) -> str:
    return f"[{_escape(label)}](<{quote(path, safe='/:')}>)"


def _render_block(block: EvidenceBlock) -> str:
    row = block.row
    parts = [f"{_escape(row.id)} — physical page {row.physical_page}",
             _link("Source image", block.source_image.path)]
    for cell in row.cells:
        value = _escape(cell.text) if cell.text else "[visibly blank]"
        if cell.state == "visible_text_with_clipped_unresolved_tail":
            value += " **[clipped tail unresolved]**"
        notes = ", ".join(str(n) for n in cell.superscript_footnotes)
        parts.append(f"{_escape(cell.column)}: {value}" + (f" [footnote {notes}]" if notes else ""))
    return "\n\n".join(parts)


def render_markdown(result: LookupResult | Refusal) -> str:
    """Render readable source-only findings without echoing a user query as markup."""
    if isinstance(result, Refusal):
        return "Request refused. " + _escape(result.reason) + "\n"
    source = result.source
    lines = [BOUNDARY, "**Legal currentness: not verified. Answer safe: false.**",
             f"Status: {_escape(result.status)}; matching fee rows: {len(result.matches)}.",
             _link("Preserved source PDF", source.source_pdf.path) + " · " +
             _link("Source review", source.source_review.path) + " · " +
             _link("Official URL (received acquisition claim)", source.claimed_source_url),
             f"Source PDF SHA256: `{source.source_pdf.sha256}`",
             f"Reviewed grid SHA256: `{source.reviewed_grid.sha256}`",
             "Printed date claim: " + _escape(source.source_printed_date_claim) +
             ". Verified adoption/effective dates: unknown.",
             "Claimed HTTP time: " + source.claimed_http_acquisition_at +
             "; verified HTTP time: unknown. Repository receipt: " +
             source.actual_repository_received_at + ".",
             "**Required context for every returned row**"]
    context = result.mandatory_context
    for block in [*context.source_headers, context.table_header, context.global_footnote,
                  *context.general_notes]:
        lines.append(_render_block(block))
    for match in result.matches:
        lines.extend(["**Matched fee row**", _render_block(match.section_header),
                      _render_block(match.fee_row)])
        if match.section_continues_from_prior_page:
            lines.append("The section heading is on an earlier page of the continued table.")
        lines.extend(_render_block(note) for note in match.row_footnotes)
    if result.matched_context_ids:
        lines.append("Matched shared context: " + ", ".join(result.matched_context_ids) + ".")
    lines.append("**Source and custody limitations**")
    lines.extend(_escape(s) for s in [*source.unresolved_regions, *source.limitations])
    return "\n\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Run the fixed source lookup; refusal and evidence failures return nonzero."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-id", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query")
    group.add_argument("--list-rows", action="store_true")
    parser.add_argument("--mode", choices=["source", "current-law"], default="source")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args(argv)
    try:
        result = lookup(
            args.root, args.source_id, args.query, list_rows=args.list_rows, mode=args.mode,
        )
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.stderr.write("Scanned-fee lookup failed: " + str(error) + "\n")
        return 1
    text = (result.model_dump_json(indent=2) + "\n" if args.format == "json"
            else render_markdown(result))
    sys.stdout.write(text)
    return 2 if isinstance(result, Refusal) else 0


if __name__ == "__main__":
    raise SystemExit(main())
