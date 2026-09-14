"""Read-only portable byte, paragraph, geometry and image replay for the EB026 review."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

from review_models import FileRef, Manifest, Review, SOURCE_ID, SOURCE_SHA, Validation


def require(condition: bool, message: str) -> None:
    """Refuse evidence mismatches without depending on interpreter assertions."""
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    """Hash one captured buffer."""
    return hashlib.sha256(raw).hexdigest()


def ordinary(path: Path) -> None:
    """Reject symlink ancestors before reading an ordinary file."""
    for item in [path, *path.parents]:
        require(not item.is_symlink(), f"Symlink path: {item}")
    require(stat.S_ISREG(path.stat().st_mode), f"Not an ordinary file: {path}")


def safe(root: Path, relative: str) -> Path:
    """Constrain an inventory member to its lexical package root."""
    value = Path(relative)
    require(not value.is_absolute() and relative == value.as_posix(), "Invalid member path")
    require(bool(value.parts) and all(p not in {"", ".", ".."} for p in value.parts),
            "Unsafe member path")
    path = root / value
    ordinary(path)
    return path


def capture(root: Path) -> dict[str, bytes]:
    """Capture each closed member once, verifying its hash before any interpretation."""
    root = root.absolute()
    ordinary(root / "FINAL_MANIFEST.json")
    manifest_bytes = (root / "FINAL_MANIFEST.json").read_bytes()
    manifest = Manifest.model_validate_json(manifest_bytes)
    names = [f.path for f in manifest.files]
    require(len(names) == len(set(names)), "Duplicate inventory path")
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Symlink member")
        if path.is_file() and path != root / "FINAL_MANIFEST.json":
            actual.add(path.relative_to(root).as_posix())
    require(actual == set(names), "Closed file membership differs")
    buffers = {"FINAL_MANIFEST.json": manifest_bytes}
    for item in manifest.files:
        data = safe(root, item.path).read_bytes()
        require(len(data) == item.size_bytes and sha(data) == item.sha256,
                f"Inventory identity differs: {item.path}")
        buffers[item.path] = data
    require(json.loads(buffers["FINAL_MANIFEST.schema.json"]) == Manifest.model_json_schema(),
            "Manifest schema differs")
    return buffers


def bound(buffers: dict[str, bytes], ref: FileRef) -> bytes:
    """Return only a captured file whose complete identity matches the reference."""
    require(ref.path in buffers, f"Uncaptured reference: {ref.path}")
    raw = buffers[ref.path]
    require(len(raw) == ref.size_bytes and sha(raw) == ref.sha256,
            f"Bound file differs: {ref.path}")
    return raw


def verify_buffers(buffers: dict[str, bytes], rerender: bool = False) -> Validation:
    """Replay exact native text, complete context partition, source geometry and viewed crops."""
    require(json.loads(buffers["SOURCE_QA.schema.json"]) == Review.model_json_schema(),
            "QA schema differs")
    qa = Review.model_validate_json(buffers["SOURCE_QA.json"])
    original = bound(buffers, qa.source)
    require(sha(original) == SOURCE_SHA and len(original) == 64434, "Wrong source PDF")
    require(qa.source_id == SOURCE_ID, "Wrong source identity")
    candidate = bound(buffers, qa.candidate)
    require(sha(candidate) == "14b5a44fae0cfd68a13e07a34aed34f992fc0cee4e1f6a624d0c35697436bcd7",
            "Wrong unchanged candidate")
    packet = bound(buffers, qa.packet_manifest)
    require(sha(packet) == qa.packet_manifest_sha256, "Original packet manifest differs")
    members = {f["path"]: f for f in json.loads(packet)["files"]}
    for name, raw in buffers.items():
        if name.startswith("inputs/") and name[7:] not in {"MANIFEST.json", "MANIFEST.schema.json"}:
            require(name[7:] in members, "Input missing from original packet manifest")
            member = members[name[7:]]
            require(member["sha256"] == sha(raw) and member["size_bytes"] == len(raw),
                    "Original packet input mismatch")
    record_lines = list(io.BytesIO(bound(buffers, qa.canonical_record)))
    require(len(record_lines) == 1, "Expected one exact selected canonical row")
    record = json.loads(record_lines[0])
    custody = json.loads(bound(buffers, qa.custody))
    require(record["source_id"] == SOURCE_ID and record["sha256"] == SOURCE_SHA,
            "Canonical source identity differs")
    require(custody["source_id"] == SOURCE_ID and
            custody["authority_id"] == qa.authority_id and
            custody["repository_received_at"] == qa.received_at and
            custody["acquisition_method"] == qa.acquisition_method and
            custody["original_http_acquisition_at"] is None, "Custody roles differ")
    require(record["received_at"] == qa.received_at and
            record["acquisition_method"] == qa.acquisition_method and
            record["archived_path"] == custody["canonical_archive_path"], "Canonical custody differs")
    total_native = line_count = cursor = 0
    segments = {}
    doc = pymupdf.open(stream=original, filetype="pdf")
    require(len(doc) == 6 and not doc.is_repaired and not doc.is_encrypted, "PDF structure differs")
    for page, actual_page in zip(qa.pages, doc):
        n = page.physical_page
        raw = bound(buffers, page.native)
        require(raw == actual_page.get_text("text", flags=195, sort=False).encode(),
                f"Native extraction differs on page{n}")
        image = bound(buffers, page.image)
        require(image[:8] == b"\x89PNG\r\n\x1a\n" and
                struct.unpack(">II", image[16:24]) == (2550, 3300), "Full image dimensions differ")
        marker = f"===== PHYSICAL PDF PAGE {n} OF 6 (PACKAGING MARKER) =====\n".encode()
        closing = f"\n===== END PHYSICAL PDF PAGE {n} (PACKAGING MARKER) =====\n\n".encode()
        require(candidate[cursor:cursor + len(marker)] == marker, "Candidate marker mismatch")
        cursor += len(marker)
        require(page.candidate_native_start == cursor and
                page.candidate_native_end == cursor + len(raw), "Candidate native offsets differ")
        require(candidate[cursor:cursor + len(raw)] == raw, "Candidate body mismatch")
        cursor += len(raw)
        require(candidate[cursor:cursor + len(closing)] == closing, "Candidate ending mismatch")
        cursor += len(closing)
        geometry = [l for b in actual_page.get_text("dict", flags=195, sort=False)["blocks"]
                    if b["type"] == 0 for l in b["lines"]]
        native_lines = raw.splitlines(keepends=True)
        require(len(geometry) == len(native_lines) == len(page.lines), "Missing/extra native line")
        offset = 0
        for i, (line, text, geom) in enumerate(zip(page.lines, native_lines, geometry), 1):
            require(line.id == f"P{n:02}-L{i:03}" and line.physical_page == n and
                    line.line_number == i, "Line identity mismatch")
            require(line.byte_start == offset and line.byte_end == offset + len(text),
                    "Line byte range mismatch")
            require(line.candidate_byte_start == page.candidate_native_start + offset and
                    line.candidate_byte_end == page.candidate_native_start + offset + len(text),
                    "Line candidate byte range mismatch")
            require(line.text.encode() == text and line.sha256 == sha(text), "Line text mismatch")
            require(line.bbox_pdf_points == list(geom["bbox"]) and
                    text.decode() == "".join(s["text"] for s in geom["spans"]) + "\n",
                    "Line PDF geometry mismatch")
            offset += len(text)
        require(offset == len(raw), "Native bytes not completely covered")
        offset = first = 0
        for i, segment in enumerate(page.segments, 1):
            require(segment.id == f"P{n:02}-S{i:02}" and segment.physical_page == n,
                    "Segment identity mismatch")
            require(segment.first_line == first + 1 and segment.last_line >= segment.first_line,
                    "Segment line partition mismatch")
            member_lines = page.lines[segment.first_line - 1:segment.last_line]
            require(bool(member_lines) and segment.byte_start == offset and
                    segment.byte_end == member_lines[-1].byte_end, "Segment byte partition mismatch")
            text = raw[segment.byte_start:segment.byte_end]
            require(segment.text.encode() == text and segment.sha256 == sha(text),
                    "Segment wording mismatch")
            require(segment.line_ids == [l.id for l in member_lines], "Segment line binding differs")
            require((not segment.text.strip()) == (segment.kind == "extraction_whitespace"),
                    "Whitespace/visible segment classification differs")
            require(segment.visual_disposition == ("native_whitespace_only" if not text.strip()
                    else "wording_matches_visible_source"), "Visual disposition mismatch")
            segments[segment.id] = segment
            offset, first = segment.byte_end, segment.last_line
        require(offset == len(raw) and first == len(page.lines), "Dropped native paragraph text")
        total_native += len(raw)
        line_count += len(page.lines)
    require(cursor == len(candidate) and total_native == 13558 and line_count == 180,
            "Overall source coverage differs")
    require(sum(bool(l.text.strip()) for p in qa.pages for l in p.lines) == 178,
            "Nonwhitespace line count differs")
    expected_links = {("P02-S15", "P03-S01"), ("P03-S09", "P04-S01"), ("P05-S12", "P06-S01")}
    require({(s.id, s.continues_to) for s in segments.values() if s.continues_to} == expected_links and
            {(s.continues_from, s.id) for s in segments.values() if s.continues_from} == expected_links,
            "Cross-page paragraph continuation differs")
    crop_ids = {c.id for c in qa.crops}
    require(len(crop_ids) == 15, "Duplicate crop identity")
    for crop in qa.crops:
        expected = bound(buffers, crop.image)
        if crop.method == "pdf_clip_pymupdf":
            require(crop.coordinate_unit == "pdf_points", "Crop unit mismatch")
            pix = doc[crop.physical_page - 1].get_pixmap(
                matrix=pymupdf.Matrix(300 / 72, 300 / 72), clip=pymupdf.Rect(crop.rectangle),
                alpha=False)
        else:
            require(crop.coordinate_unit == "source_png_pixels" and
                    crop.rectangle == [0, 2850, 2550, 3300], "Footer crop bounds differ")
            source_pix = pymupdf.Pixmap(bound(buffers, qa.pages[crop.physical_page - 1].image))
            rect = pymupdf.IRect(crop.rectangle)
            pix = pymupdf.Pixmap(source_pix.colorspace, rect, False)
            pix.copy(source_pix, rect)
        require(pix.tobytes("png") == expected, "Crop replay differs")
    for observation in qa.observations:
        require(set(observation.segment_ids) <= set(segments), "Unknown observation paragraph")
        require(set(observation.crop_ids) <= crop_ids, "Unknown observation crop")
        texts = [segments[s].text for s in observation.segment_ids]
        require(all(any(anchor in text for text in texts) for anchor in observation.literal_anchors),
                "Observation source anchor differs")
    if rerender:
        replay_poppler(buffers, qa, original)
    doc.close()
    return Validation(status="passed", physical_pages=6, native_bytes=13558, native_lines=180,
                      paragraph_segments=len(segments), crop_replays=15,
                      full_page_render_replays=6 if rerender else 0,
                      legal_currentness="not_verified", visual_judgment_automatically_certified=False)


def replay_poppler(buffers: dict[str, bytes], qa: Review, original: bytes) -> None:
    """Optionally replay the six full pages using the recorded local Poppler binary."""
    receipt = json.loads(buffers[f"inputs/04-verification/render-events/{SOURCE_ID}/RENDER.json"])
    renderer = Path(receipt["renderer_path"])
    require(renderer.is_file() and sha(renderer.read_bytes()) == receipt["renderer_sha256"],
            "Recorded renderer unavailable or changed; plain verification remains portable")
    with tempfile.TemporaryDirectory(prefix="eb026-render-") as folder:
        root = Path(folder)
        (root / "original.pdf").write_bytes(original)
        (root / "fontconfig.xml").write_bytes(buffers["inputs/04-verification/fontconfig.xml"])
        env = dict(os.environ, FONTCONFIG_FILE=str(root / "fontconfig.xml"))
        result = subprocess.run([str(renderer), "-r", "300", "-png", str(root / "original.pdf"),
                                 str(root / "page")], capture_output=True, timeout=30, env=env)
        require(result.returncode == 0, "Poppler replay failed")
        rendered = sorted(root.glob("page-*.png"))
        require(len(rendered) == 6, "Poppler page count differs")
        for file, page in zip(rendered, qa.pages):
            require(file.read_bytes() == bound(buffers, page.image), "Full-page replay differs")


def main() -> None:
    """Verify a copied package without opening any historical source or external report path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parent)
    parser.add_argument("--rerender", action="store_true")
    args = parser.parse_args()
    value = verify_buffers(capture(args.root), args.rerender)
    sys.stdout.write(value.model_dump_json(indent=2) + "\n")


if __name__ == "__main__":
    main()
