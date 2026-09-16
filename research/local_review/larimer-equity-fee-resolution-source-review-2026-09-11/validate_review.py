"""Portable, offline, read-only validation; optional Poppler replay uses temporary files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import jsonschema
import pymupdf

from review_models import Asset, Inventory, Review, SOURCE_ID, SOURCE_SHA

B = Path(__file__).resolve().parent


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ordinary(relative: str) -> Path:
    Asset(path=relative, sha256="0" * 64, size_bytes=0)
    path = B / relative
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Symlink forbidden")
    require(path.is_file(), "Missing ordinary file: " + relative)
    return path


def verify_asset(asset: Asset) -> Path:
    path = ordinary(asset.path)
    size = 0
    hashed = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            hashed.update(chunk)
    require(size == asset.size_bytes and hashed.hexdigest() == asset.sha256,
            "Asset hash/size mismatch: " + asset.path)
    return path


def content(asset: Asset) -> bytes:
    return verify_asset(asset).read_bytes()


def line(asset: Asset, number: int, expected: str) -> dict:
    require(number >= 1, "Custody row number must be one-based")
    path = verify_asset(asset)
    with path.open("rb") as handle:
        for current, raw in enumerate(handle, 1):
            if current == number:
                require(digest(raw) == expected, "Custody row byte hash mismatch")
                value = json.loads(raw)
                require(isinstance(value, dict), "Custody row must be a JSON object")
                return value
    raise ValueError("Custody row is beyond the end of the file")


def validate(rerender: bool = False) -> dict:
    inv = Inventory.model_validate_json(ordinary("MANIFEST.json").read_bytes())
    names = [a.path for a in inv.files]
    require(len(names) == len(set(names)), "Duplicate inventory entry")
    actual = set()
    for path in B.rglob("*"):
        require(not path.is_symlink(), "Symlinked package member")
        if path.is_file():
            actual.add(path.relative_to(B).as_posix())
    require(actual == set(names) | {"MANIFEST.json"}, "Uninventoried or missing files")
    for asset in inv.files:
        verify_asset(asset)
    raw = ordinary("SOURCE_QA.json").read_bytes()
    qa = Review.model_validate_json(raw)
    schema = json.loads(ordinary("SOURCE_QA.schema.json").read_bytes())
    require(schema == Review.model_json_schema(), "Exported schema drift")
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    source = content(qa.source)
    require(digest(source) == SOURCE_SHA and source.startswith(b"%PDF-")
            and source.rstrip().endswith(b"%%EOF"), "Wrong or truncated source PDF")
    with pymupdf.open(stream=source, filetype="pdf") as pdf:
        require(len(pdf) == 2 and not pdf.is_repaired and not pdf.is_encrypted,
                "PDF structure/page-count mismatch")
        for page in qa.pages:
            native = content(page.native_text)
            require(native == b"" == pdf[page.physical_page - 1].get_text(
                "text", flags=195, sort=False).encode(), "Expected empty native page")
            image = content(page.image)
            require(image[:8] == b"\x89PNG\r\n\x1a\n"
                    and struct.unpack(">II", image[16:24]) == (2550, 3300), "Page PNG dimensions")
            text = content(page.printed_body)
            for block in page.blocks:
                require(text[block.start_byte:block.end_byte] == block.text.encode(),
                        "Manual transcription slice mismatch")
    blocks = {b.id: b for p in qa.pages for b in p.blocks}
    require([b.id for b in qa.pages[0].blocks] == [
        "P1-TITLE", "P1-R1", "P1-R2", "P1-R3", "P1-R4", "P1-R5", "P1-R6-R7",
        "P1-R8", "P1-RESOLVE", "P1-ITEM1", "P1-ITEM2",
    ], "Page-one body order changed")
    require([b.id for b in qa.pages[1].blocks] == [
        *[f"P2-2{x}" for x in "abcdefgh"], "P2-ITEM3", "P2-ITEM4",
    ], "Eligibility or operative item missing/reordered")
    require(all(blocks[f"P2-2{x}"].parent_id == "P1-ITEM2" for x in "abcdefgh"),
            "Eligibility parent detached across page boundary")
    # These are source-fidelity guards, not a fee calculator or an interpretation engine.
    checks = {
        "P1-ITEM1": ["authorized", "twenty-five percent (25%)", "certain application types"],
        "P2-2a": ["as defined by the Larimer County Affordable Housing Policy"],
        "P2-2b": ["an owner", "long-term housing", "as attested through an Affidavit"],
        "P2-2d": ["registered in Larimer County", "ten (10) or fewer employees"],
        "P2-2f": ["fewer than three (3) lots"],
        "P2-2g": ["may include but are not limited to", "on a commercial site",
                   "adopted Larimer County plans or policies; and"],
        "P2-2h": ["At the discretion of the Director", "in consultation with the Board"],
        "P2-ITEM3": ["at the time of application with a planner"],
        "P2-ITEM4": ["January 2, 20243", "at the discretion of the Board",
                     "through December 31, 2027", "subject to renewal at that time"],
    }
    for ident, phrases in checks.items():
        require(all(s in blocks[ident].text for s in phrases),
                "Lost source condition or repaired anomaly: " + ident)
    require(len(qa.execution) == 5 and len(qa.observations) == 12,
            "Execution or qualification scope truncated")
    require({e.id for e in qa.execution} == {
        "EX-DATE", "EX-CHAIR", "EX-CLERK", "EX-ATTORNEY", "EX-SEAL",
    }, "Execution region identity mismatch")
    for e in qa.execution:
        require(set(e.crop_ids) <= {c.id for c in qa.crops}, "Unknown execution crop")
    c = qa.custody
    manual = line(c.manual_manifest, c.manual_line_number, c.manual_line_sha256)
    provenance = line(c.source_provenance, c.provenance_line_number, c.provenance_line_sha256)
    require(manual["record_id"] == provenance["source_id"] == qa.source_id == SOURCE_ID,
            "Custody source-ID mismatch")
    require(manual["sha256"] == provenance["canonical_original"]["sha256"]
            == provenance["received_original"]["sha256"] == SOURCE_SHA,
            "Custody/source digest mismatch")
    require(manual["size_bytes"] == provenance["canonical_original"]["size_bytes"]
            == qa.source.size_bytes, "Custody/source size mismatch")
    require(provenance["authority_id"] == qa.authority_id, "Wrong authority")
    require(manual["archive_path"] == c.canonical_archive_path
            == provenance["canonical_original"]["path"], "Historical raw path mismatch")
    require(manual["intake_id"] == provenance["intake_id"] == c.intake_id,
            "Intake identity mismatch")
    require(manual["received_at"] == provenance["repository_received_at"]
            == c.repository_received_at.isoformat().replace("+00:00", "Z"),
            "Receipt time mismatch")
    require(manual["acquisition_method"] == provenance["acquisition_method"]
            == c.acquisition_method == "received_review_package", "Acquisition relabeling")
    require(provenance["original_acquisition_at"] is c.original_acquisition_time is None
            and provenance["source_http_acquisition_verified"] is False,
            "Unknown acquisition promoted")
    for key in ["supplied_requested_url", "supplied_final_url", "supplied_time_claim",
                "supplied_method_claim", "supplied_http_status"]:
        require(provenance[key] == getattr(c, key), "Supplied provenance claim changed")
    require(manual["status"] == c.intake_status == "archived_pending_pipeline",
            "Intake status promoted")
    for crop in qa.crops:
        raw = content(crop.image)
        require(struct.unpack(">II", raw[16:24]) == (crop.width, crop.height),
                "Crop dimensions changed")
        require(crop.x + crop.width <= 2550 and crop.y + crop.height <= 3300,
                "Crop outside full source image")
    if rerender:
        version = subprocess.run(["pdftoppm", "-v"], capture_output=True, text=True, check=True)
        require("pdftoppm version 26.05.0" in version.stderr, "Recorded Poppler required")
        with tempfile.TemporaryDirectory(prefix="geode-equity-review-") as temp:
            out = Path(temp)
            subprocess.run(["pdftoppm", "-r", "300", "-png", str(B / qa.source.path),
                            str(out / "page")], check=True, capture_output=True)
            for page in qa.pages:
                require((out / f"page-{page.physical_page}.png").read_bytes()
                        == content(page.image), "Full-page render replay differs")
            for crop in qa.crops:
                subprocess.run([
                    "pdftoppm", "-f", "2", "-l", "2", "-r", "300", "-x", str(crop.x),
                    "-y", str(crop.y), "-W", str(crop.width), "-H", str(crop.height),
                    "-singlefile", "-png", str(B / qa.source.path), str(out / crop.id),
                ], check=True, capture_output=True)
                require((out / (crop.id + ".png")).read_bytes() == content(crop.image),
                        "Crop replay differs")
    return dict(passed=True, source_sha256=SOURCE_SHA, physical_pages=2,
                empty_native_pages=2, printed_body_blocks=21, execution_regions=5,
                source_observations=12, full_page_and_crop_replay=rerender,
                scope="Source image review and manual transcription; no legal certification",
                legal_currentness="not_verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerender", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(args.rerender), indent=2))
