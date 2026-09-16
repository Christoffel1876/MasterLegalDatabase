"""Read-only validation of the two-source Colorado Springs custody package."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pymupdf
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict

HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(HERE))
from build_scope import Asset, PINS, Scope


class Inventory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: list[Asset]


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def read(root: Path, ref: Asset) -> bytes:
    rel = Path(ref.path)
    if rel.is_absolute() or ".." in rel.parts or rel.as_posix() != ref.path:
        raise ValueError("Noncanonical evidence path")
    path = root / rel
    if any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise ValueError("Nonordinary evidence path")
    body = path.read_bytes()
    if digest(body) != ref.sha256 or len(body) != ref.size_bytes:
        raise ValueError("Evidence bytes differ: " + ref.path)
    return body


def validate(root: Path) -> dict:
    root = root.absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("Symlink package root")
    inv = Inventory.model_validate_json((root / "FINAL_MANIFEST.json").read_bytes())
    expected = {ref.path for ref in inv.files} | {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if expected != actual or len(expected) != len(inv.files) + 2:
        raise ValueError("Closed inventory or duplicate files differ")
    for ref in inv.files:
        read(root, ref)
    if json.loads((root / "FINAL_MANIFEST.schema.json").read_bytes()) != Inventory.model_json_schema():
        raise ValueError("Inventory schema changed")
    scope_bytes = (root / "SOURCE_SCOPE.json").read_bytes()
    if digest(scope_bytes) != "d5ad6056f8b7d820dfd01d09366744dc368fe6c604811eddfb0f225616f94ef5":
        raise ValueError("Accepted source scope pin differs")
    scope = Scope.model_validate_json(scope_bytes)
    if json.loads((root / "SOURCE_SCOPE.schema.json").read_bytes()) != Scope.model_json_schema():
        raise ValueError("Source schema changed")
    if [s.source_id for s in scope.sources] != list(PINS):
        raise ValueError("Source selection changed")
    for source in scope.sources:
        pdf_bytes = read(root, source.original)
        if digest(pdf_bytes) != PINS[source.source_id]:
            raise ValueError("Source PDF pin differs")
        result = json.loads(read(root, source.result))
        reservation = json.loads(read(root, source.reservation))
        if (result["outcome"] != "complete" or result["partial_body"] is not False
                or result["http_status"] != 200 or result["body"]["sha256"] != digest(pdf_bytes)
                or result["body"]["size_bytes"] != len(pdf_bytes)
                or result["redirect_url"] is not None or reservation["hop"] != 0
                or reservation["source_id"] != source.source_id
                or reservation["url"] != source.requested_url):
            raise ValueError("Acquisition/source binding differs")
        if (source.request_started_at.isoformat().replace("+00:00", "Z") != reservation["reserved_at"]
                or source.response_finished_at.isoformat().replace("+00:00", "Z") != result["finished_at"]):
            raise ValueError("Acquisition chronology differs")
        if result["reservation_sha256"] != source.reservation.sha256:
            raise ValueError("Result/reservation hash differs")
        if result["public_headers"]["sha256"] != source.public_headers.sha256:
            raise ValueError("Response header binding differs")
        read(root, source.public_headers)
        parent = read(root, source.parent_html)
        parent_result = json.loads(read(root, source.parent_result))
        parent_reservation = json.loads(read(root, source.parent_reservation))
        if (parent_result["body"]["sha256"] != digest(parent)
                or parent_result["reservation_sha256"] != source.parent_reservation.sha256
                or parent_result["public_headers"]["sha256"] != source.parent_public_headers.sha256
                or parent_result["outcome"] != "complete" or parent_result["partial_body"]
                or parent_result["http_status"] != 200 or parent_reservation["hop"] != 0):
            raise ValueError("Parent acquisition differs")
        read(root, source.parent_public_headers)
        matches = []
        for iframe in BeautifulSoup(parent, "html.parser").find_all("iframe"):
            if iframe.get("data-src") != source.requested_url:
                continue
            arguments = [x.split("=", 1)[1] for x in urlsplit(iframe.get("src", "")).query.split("&")
                         if x.startswith("file=")]
            if len(arguments) == 1 and unquote(arguments[0]) == source.requested_url:
                matches.append(iframe)
        if len(matches) != 1:
            raise ValueError("Official parent/one-decode PDF link differs")
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            if len(pdf) != 7 or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError("PDF structure differs")
            if [p.physical_page for p in source.pages] != list(range(1, 8)):
                raise ValueError("Page coverage differs")
            for item, page in zip(source.pages, pdf, strict=True):
                if read(root, item.native) != page.get_text("text", flags=195, sort=False).encode():
                    raise ValueError("Native text differs")
                image = pymupdf.Pixmap(read(root, item.rendering))
                replay = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                if (image.width, image.height, image.samples) != (replay.width, replay.height, replay.samples):
                    raise ValueError("Page rendering differs")
    for item in scope.selected_passages:
        selected = read(root, item.native_file)[item.start_byte:item.end_byte]
        if selected != item.exact_text.encode() or digest(selected) != item.sha256:
            raise ValueError("Passage byte binding differs")
    if len(scope.native_white_text) != 8:
        raise ValueError("White-text region selection differs")
    with pymupdf.open(root / "SD014-01/original.pdf") as pdf:
        for item in scope.native_white_text:
            page = pdf[item.physical_page - 1]
            trace = next(t for t in page.get_texttrace() if t["seqno"] == item.trace_sequence)
            if ("".join(chr(c[0]) for c in trace["chars"]) != item.exact_text
                    or list(trace["bbox"]) != item.pdf_bbox or list(trace["color"]) != [1, 1, 1]
                    or trace["opacity"] != item.opacity):
                raise ValueError("PDF text trace differs")
            replay = page.get_pixmap(matrix=pymupdf.Matrix(4, 4),
                                      clip=pymupdf.Rect(item.pdf_bbox), alpha=False)
            stored = pymupdf.Pixmap(read(root, item.rendered_bbox))
            if (stored.width, stored.height, stored.samples) != (replay.width, replay.height, replay.samples):
                raise ValueError("White-region rendering differs")
            if set(replay.samples) != {255} or len(replay.samples) != item.rgb_bytes:
                raise ValueError("Checked region is not entirely white")
    for ref in inv.files:
        read(root, ref)
    return {"status": "verified_scoped_custody", "sources": 2, "pages": 14,
            "selected_passages": len(scope.selected_passages), "white_text_regions": 8,
            "complete_table_qa": False, "legal_currentness": "not_verified"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE)
    print(json.dumps(validate(parser.parse_args().root), sort_keys=True))
