"""Build or replay a five-page source-fidelity record without altering original evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pymupdf
from jsonschema import Draft202012Validator
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = "5b71fc2ba18d7a11a5c66d691b1f11526cce424cc0eb8fc07cbd37fb7e5c268a"
CANDIDATE_SHA = "5993a21f83903996a0abf22535c20ef8eb0b1f5d9e44ba48a6e38197fab6daff"
PACKET_SHA = "dbb8f0a6e6b280e5ac9b8f92877c2efb395799664ae80351c889fc62233c2e89"
CROPS = [("p3-treasurer-citations", 3, (85, 151, 542, 253)),
         ("p4-article-I", 4, (85, 418, 542, 472)),
         ("p5-final-rules", 5, (85, 400, 542, 622))]


class Strict(BaseModel):
    """Reject undeclared or loosely typed review fields."""
    model_config = ConfigDict(strict=True, extra="forbid")


class Asset(Strict):
    """An exact portable file identity."""
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def confined(cls, value: str) -> str:
        """Reject absolute, backslash or traversing file references."""
        if Path(value).is_absolute() or ".." in Path(value).parts or "\\" in value:
            raise ValueError("Unsafe evidence path")
        return value


class Line(Strict):
    """One complete nonblank native line, with genuine page-byte and geometry bindings."""
    id: str
    physical_page: int = Field(ge=1, le=5)
    native_line_number: int = Field(ge=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    bbox_pdf_points: list[float] = Field(min_length=4, max_length=4)
    paragraph_id: str


class Paragraph(Strict):
    """A visually checked heading, paragraph portion or date footer."""
    id: str
    logical_id: str
    physical_page: int = Field(ge=1, le=5)
    role: Literal["cover_text", "running_heading", "section_heading", "body", "footer"]
    section_heading: str | None
    paragraph_label: str | None
    continuation_from: str | None
    line_ids: list[str] = Field(min_length=1)
    exact_native_text: str


class Page(Strict):
    """The complete native page and its source-visible line/paragraph allocation."""
    physical_page: int = Field(ge=1, le=5)
    source_pdf_sha256: Literal[SOURCE_SHA]
    image: Asset
    native: Asset
    candidate_start: int
    candidate_end: int
    native_line_count: int
    nonblank_line_count: int
    visual_judgment: Literal["all_printed_lines_compared_to_complete_page_image"]
    lines: list[Line]
    paragraphs: list[Paragraph]


class Observation(Strict):
    """A bounded direct-source observation, not an interpretation of legal effect."""
    id: str
    pages: list[int]
    paragraph_ids: list[str]
    statement: str
    limitation: str


class Disposition(Strict):
    """One external finding assessed against the independent source reading."""
    external_id: str
    disposition: Literal["accepted_source_anomaly", "accepted_packaging_classification",
                         "resolved_by_direct_visual_review"]
    pages: list[int]
    source_evidence: str
    qualification: str


class Review(Strict):
    """Complete five-page research-only transcription and contextual source review."""
    schema_version: Literal["eb024-source-fidelity-1"]
    source_id: Literal["el-paso-boh-bylaws-sd011"]
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    prepared_at: AwareDatetime
    source: Asset
    candidate: Asset
    source_first_notes: Asset
    method: str
    full_pages_directly_viewed: list[int]
    crops_directly_viewed: list[Asset]
    extractor: Literal["PyMuPDF 1.28.2; get_text(text), flags=195, sort=False"]
    native_bytes: Literal[12640]
    native_lines: Literal[400]
    nonblank_lines: Literal[170]
    pages: list[Page] = Field(min_length=5, max_length=5)
    metadata_as_received: dict[str, str | None]
    printed_date: Literal["5/23/2012"]
    printed_date_role: Literal["unlabeled_footer_on_all_five_pages"]
    adoption_date: None
    effective_date: None
    original_acquisition_at: None
    acquisition_method: Literal["received_review_package"]
    repository_received_at_claim: Literal["2026-09-12T22:59:48.795762Z"]
    observations: list[Observation]
    external_dispositions: list[Disposition] = Field(min_length=4, max_length=4)
    limitations: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    canonical_writes: Literal[0]
    public_requests: Literal[0]


def sha(raw: bytes) -> str:
    """Digest the exact consumed byte buffer."""
    return hashlib.sha256(raw).hexdigest()


def read(root: Path, relative: str) -> bytes:
    """Read an ordinary confined evidence file, rejecting symlink ancestors."""
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Evidence path escapes")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Nonordinary evidence: " + relative)
    return path.read_bytes()


def asset(root: Path, name: str) -> Asset:
    """Create an exact file identity from an ordinary captured file."""
    raw = read(root, name)
    return Asset(path=name, sha256=sha(raw), size_bytes=len(raw))


def extract_pages(root: Path) -> tuple[list[Page], dict]:
    """Replay native lines and the manually reviewed printed section/paragraph structure."""
    raw = read(root, "source/original.pdf")
    candidate = read(root, "candidate/candidate.txt")
    if sha(raw) != SOURCE_SHA or sha(candidate) != CANDIDATE_SHA:
        raise ValueError("Fixed source/candidate identity differs")
    doc = pymupdf.open(stream=raw, filetype="pdf")
    if len(doc) != 5:
        raise ValueError("Expected five physical source pages")
    pages, assembled = [], bytearray()
    section, label, logical = None, None, "cover"
    last_body: dict[str, str] = {}
    for page_number, pdf_page in enumerate(doc, 1):
        native = pdf_page.get_text("text", flags=195, sort=False).encode()
        name = f"candidate/page-{page_number:04d}.native.txt"
        if native != read(root, name):
            raise ValueError("Original-to-native extraction differs")
        assembled.extend(f"===== PHYSICAL PDF PAGE {page_number} OF 5 (PACKAGING MARKER) =====\n".encode())
        start = len(assembled)
        assembled.extend(native)
        end = len(assembled)
        assembled.extend(f"\n===== END PHYSICAL PDF PAGE {page_number} (PACKAGING MARKER) =====\n\n".encode())
        geometry = [line for block in pdf_page.get_text("dict", flags=195, sort=False)["blocks"]
                    if "lines" in block for line in block["lines"]
                    if "".join(span["text"] for span in line["spans"]).strip()]
        lines, paragraphs = [], []
        offset, geometry_index = 0, 0
        current = None
        for number, line_raw in enumerate(native.splitlines(keepends=True), 1):
            if not line_raw.strip():
                offset += len(line_raw)
                continue
            text = line_raw.decode()
            g = geometry[geometry_index]
            geometry_index += 1
            if text.removesuffix("\n") != "".join(s["text"] for s in g["spans"]):
                raise ValueError("Native text/geometry line identity differs")
            visible = text.strip()
            new = current is None
            if visible == "5/23/2012":
                role, block_logical, new = "footer", f"footer-{page_number}", True
            elif page_number == 1:
                role, block_logical, new = "cover_text", f"cover-{geometry_index}", True
            elif visible in {"CHAPTER 1", "BYLAWS", "EL PASO COUNTY BOARD OF HEALTH"}:
                role, block_logical, new = "running_heading", f"p2-heading-{geometry_index}", True
            elif visible.startswith("SECTION 1."):
                section, label = visible, None
                logical = visible.split(":", 1)[0] + "/body"
                role, block_logical, new = "section_heading", logical + "/heading", True
            else:
                role = "body"
                match = re.match(r"^([A-I])\. ([^:]+):", visible)
                number_match = re.match(r"^([1-3])\. ", visible)
                if match:
                    label = match.group(1) + ". " + match.group(2)
                    logical = section.split(":", 1)[0] + "/" + match.group(1)
                    new = True
                elif number_match:
                    label = "C. Authority of the Board of Health / " + number_match.group(1)
                    logical = "SECTION 1.1/C/" + number_match.group(1)
                    new = True
                elif current is not None and current.role != "body":
                    new = True
                block_logical = logical
            if new:
                pid = f"P{page_number}-B{len(paragraphs) + 1:02d}"
                previous = last_body.get(block_logical) if role == "body" else None
                current = Paragraph(id=pid, logical_id=block_logical,
                    physical_page=page_number, role=role,
                    section_heading=section if role in {"body", "section_heading"} else None,
                    paragraph_label=label if role == "body" else None,
                    continuation_from=previous, line_ids=[f"P{page_number}-L{number:03d}"],
                    exact_native_text=text)
                paragraphs.append(current)
                if role == "body":
                    last_body[block_logical] = pid
            else:
                current.line_ids.append(f"P{page_number}-L{number:03d}")
                current.exact_native_text += text
            lines.append(Line(id=f"P{page_number}-L{number:03d}", physical_page=page_number,
                native_line_number=number, start=offset, end=offset + len(line_raw), text=text,
                bbox_pdf_points=[round(float(v), 6) for v in g["bbox"]],
                paragraph_id=current.id))
            offset += len(line_raw)
        if geometry_index != len(geometry):
            raise ValueError("Unassigned native geometry")
        pages.append(Page(physical_page=page_number, source_pdf_sha256=SOURCE_SHA,
            image=asset(root, f"source/page-{page_number:04d}.png"), native=asset(root, name),
            candidate_start=start, candidate_end=end, native_line_count=len(native.splitlines()),
            nonblank_line_count=len(lines),
            visual_judgment="all_printed_lines_compared_to_complete_page_image",
            lines=lines, paragraphs=paragraphs))
    if bytes(assembled) != candidate:
        raise ValueError("Candidate packaging or page order differs")
    return pages, doc.metadata


def check_review(root: Path, review: Review) -> None:
    """Verify exact source/line/context bindings; do not equate this with a visual judgment."""
    if (review.source != asset(root, "source/original.pdf")
            or review.candidate != asset(root, "candidate/candidate.txt")
            or review.source_first_notes != asset(root, "SOURCE_FIRST_NOTES.md")):
        raise ValueError("Fixed review/source identity differs")
    pages, metadata = extract_pages(root)
    if review.pages != pages or review.metadata_as_received != metadata:
        raise ValueError("Page, native, geometry or paragraph context differs")
    if review.full_pages_directly_viewed != [1, 2, 3, 4, 5]:
        raise ValueError("Incomplete recorded visual page scope")
    refs = [review.source, review.candidate, review.source_first_notes,
            *review.crops_directly_viewed]
    for ref in refs:
        if asset(root, ref.path) != ref:
            raise ValueError("Review evidence identity differs")
    ids = {p.id for page in pages for p in page.paragraphs}
    for note in review.observations:
        if not set(note.paragraph_ids) <= ids:
            raise ValueError("Observation refers to absent paragraph")
    if [d.external_id for d in review.external_dispositions] != [
            f"EB024-P2-{i:03d}" for i in range(1, 5)]:
        raise ValueError("External finding disposition incomplete")
    for page in pages:
        native = read(root, page.native.path)
        positions = set()
        for line in page.lines:
            expected = set(range(line.start, line.end))
            if positions & expected or native[line.start:line.end].decode() != line.text:
                raise ValueError("Duplicated or altered native line span")
            positions |= expected
        needed = set()
        for match in re.finditer(r"\S+", native.decode()):
            a = len(native.decode()[:match.start()].encode())
            b = len(native.decode()[:match.end()].encode())
            needed.update(range(a, b))
        if not needed <= positions:
            raise ValueError("Unbound nonwhitespace native bytes")
    if (sum(p.native.size_bytes for p in pages), sum(p.native_line_count for p in pages),
            sum(p.nonblank_line_count for p in pages)) != (12640, 400, 170):
        raise ValueError("Native extent totals differ")


def rerender(root: Path) -> None:
    """Compare all retained full PNG pixels with a fresh bounded local Poppler rendering."""
    command = shutil.which("pdftoppm")
    if command is None:
        raise ValueError("Poppler is required for --rerender")
    with tempfile.TemporaryDirectory(prefix="eb024-verify-") as temporary:
        prefix = Path(temporary) / "page"
        subprocess.run([command, "-r", "300", "-png", str(root / "source/original.pdf"),
                        str(prefix)], check=True, capture_output=True, timeout=30)
        for number in range(1, 6):
            expected = pymupdf.Pixmap(read(root, f"source/page-{number:04d}.png"))
            actual = pymupdf.Pixmap(str(prefix) + f"-{number}.png")
            if (expected.width, expected.height, expected.samples) != (
                    actual.width, actual.height, actual.samples):
                raise ValueError("Full source page pixels differ")


def verify(root: Path, render: bool = False) -> dict:
    """Validate the closed portable package and replay its structural evidence."""
    from pydantic import TypeAdapter
    manifest = TypeAdapter(list[Asset]).validate_json(read(root, "FINAL_MANIFEST.json"))
    names = {r.path for r in manifest}
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Nonordinary package member")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if len(names) != len(manifest) or actual != names | {"FINAL_MANIFEST.json"}:
        raise ValueError("Closed file inventory differs")
    for ref in manifest:
        if asset(root, ref.path) != ref:
            raise ValueError("Frozen file differs: " + ref.path)
    data = read(root, "SOURCE_QA.json")
    record = Review.model_validate_json(data)
    Draft202012Validator(json.loads(read(root, "SOURCE_QA.schema.json"))).validate(json.loads(data))
    check_review(root, record)
    if render:
        rerender(root)
    return {"status": "PASS", "source_sha256": SOURCE_SHA, "physical_pages": 5,
            "native_bytes": 12640, "native_lines": 400, "nonblank_lines": 170,
            "paragraph_portions": sum(len(p.paragraphs) for p in record.pages),
            "rerendered": render, "visual_judgment_reperformed": False,
            "legal_currentness": "not_verified", "canonical_writes": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--rerender", action="store_true")
    arguments = parser.parse_args()
    if any(p.is_symlink() for p in (arguments.root, *arguments.root.parents)):
        raise ValueError("Symlinked review root")
    sys.stdout.write(json.dumps(verify(arguments.root.resolve(), arguments.rerender), indent=2) + "\n")
