#!/usr/bin/env python3
"""Read-only, offline integrity/reproduction gate; does not certify legal effect."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import jsonschema
import pymupdf

from review_models import Asset, Inventory, Review, Span

SOURCE_SHA = "8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ordinary(root: Path, relative: str) -> Path:
    Asset(path=relative, sha256="0" * 64, size_bytes=0)
    path = root.absolute() / relative
    for current in [path, *path.parents]:
        require(not current.is_symlink(), f"symlink is forbidden: {current}")
    require(path.is_file(), f"missing ordinary file: {relative}")
    return path


def read_asset(root, asset):
    if isinstance(asset, dict):
        asset = Asset.model_validate(asset)
    data = ordinary(root, asset.path).read_bytes()
    require(len(data) == asset.size_bytes, f"size mismatch: {asset.path}")
    require(digest(data) == asset.sha256, f"hash mismatch: {asset.path}")
    return data


def checked_json(root, path, schema):
    value = json.loads(ordinary(root, path).read_bytes())
    specification = json.loads(ordinary(root, schema).read_bytes())
    jsonschema.Draft202012Validator(specification).validate(value)
    return value


def all_spans(value):
    if isinstance(value, dict):
        if set(value) == {"physical_page", "start_byte", "end_byte_exclusive", "exact_text", "sha256"}:
            yield Span.model_validate(value)
        else:
            for child in value.values():
                yield from all_spans(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_spans(child)


def validate_content(review, native, layouts):
    require(review.source.sha256 == SOURCE_SHA, "unexpected source identity")
    require(len(review.rows) == 107 and len(review.tables) == 19, "incomplete row/table accounting")
    require(len(review.contexts) == 18 and len(review.observations) == 13, "incomplete context/observation accounting")
    for span in all_spans(review.model_dump()):
        data = native[span.physical_page]
        require(data[span.start_byte:span.end_byte_exclusive] == span.exact_text.encode(), "native span mismatch")
    for page in review.pages:
        n = page.physical_page
        require(page.source_sha256 == SOURCE_SHA, "page source identity mismatch")
        chunks = page.lines
        require([c.line_1based for c in chunks] == list(range(1, len(chunks) + 1)), "line order mismatch")
        offset = 0
        for chunk in chunks:
            require(chunk.span.physical_page == n and chunk.span.start_byte == offset, "line partition gap or overlap")
            require(chunk.classification == ("native_text" if chunk.span.exact_text.strip() else "native_whitespace"), "line classification mismatch")
            offset = chunk.span.end_byte_exclusive
        require(offset == len(native[n]), "line partition truncation")
        require(b"".join(c.span.exact_text.encode() for c in chunks) == native[n], "native partition changed")
    require(sum(map(len, native.values())) == review.native_bytes, "native byte total mismatch")
    # Every nonblank native line is represented by source-row, heading or context evidence.
    semantic_spans = []
    for row in review.rows:
        semantic_spans += row.source_evidence
    for table in review.tables:
        semantic_spans += table.title
        for col in table.columns:
            semantic_spans += col.evidence
            if col.label_origin == "exact_native":
                require(col.label == " ".join("".join(s.exact_text for s in col.evidence).split()), "column label changed")
    for context in review.contexts:
        semantic_spans += context.evidence
    for page in review.pages:
        for line in page.lines:
            if line.classification == "native_whitespace":
                continue
            span = line.span
            require(any(s.physical_page == page.physical_page and s.start_byte <= span.start_byte
                        and s.end_byte_exclusive >= span.end_byte_exclusive for s in semantic_spans),
                    f"unaccounted native line: page {page.physical_page}, line {line.line_1based}")
    rows = {r.row_id: r for r in review.rows}
    tables = {t.table_id: t for t in review.tables}
    required_contexts = {
        "P1-MANUFACTURED-R05": {"P1-ENGINEERED"},
        "P1-PLAN-REVIEW-R01": {"P1-MAJOR"},
        "P1-PLAN-REVIEW-R02": {"P1-MINOR"},
        "P2-DRAINAGE-R01": {"P2-DRAINAGE-NOTE"},
        "P3-INVESTIGATION-R01": {"P3-INVESTIGATION-NOTE"},
        "P4-MATRIX-R21": {"P4-OIL-GAS"},
        "P5-DRAINAGE-R01": {"P5-DRAINAGE-NOTE"},
    }
    for i in range(1, 6):
        required_contexts[f"P2-ELECTRICAL-AREA-R{i:02d}"] = {"P2-RESIDENTIAL-SCOPE"}
        required_contexts[f"P2-ELECTRICAL-VALUE-R{i:02d}"] = {"P2-OTHER-ELECTRICAL"}
    for i in range(1, 4):
        required_contexts[f"P4-NOTE-RATES-R{i:02d}"] = {"P4-GARAGE-PARENT"}
    for rid, expected in required_contexts.items():
        row = rows[rid]
        require(expected <= set(row.context_ids) | set(tables[row.table_id].context_ids), "lost condition/footnote association")
    matrix = [r for r in review.rows if r.table_id == "P4-MATRIX"]
    columns = ["IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IV", "VA", "VB"]
    require([c.column_id for c in tables["P4-MATRIX"].columns] == ["label", *columns], "matrix column order changed")
    found_np = {(r.row_order, c.column_id) for r in matrix for c in r.cells[1:] if c.display_text == "N.P."}
    require(found_np == {(12, "VB"), (16, "IIIB"), (16, "VB"), (17, "IIIB"), (17, "VB")}, "N.P. association mismatch")
    require(sum(len(r.cells) - 1 for r in matrix) == 252, "matrix cell count mismatch")
    # Compare each matrix cell to native source geometry, not just nine-item lists.
    geometry = []
    for block in layouts[4]["get_text_dict"]["blocks"]:
        for line in block.get("lines", []):
            geometry.append(("".join(s["text"] for s in line["spans"]) + "\n", line["bbox"]))
    require("".join(t for t, _ in geometry).encode() == native[4], "layout/native line correspondence differs")
    page4 = review.pages[3]
    offset_to_box = {line.span.start_byte: geometry[i][1] for i, line in enumerate(page4.lines)}
    centers = []
    for col in tables["P4-MATRIX"].columns[1:]:
        box = offset_to_box[col.evidence[0].start_byte]
        centers.append((box[0] + box[2]) / 2)
    for row in matrix:
        label_box = offset_to_box[row.cells[0].evidence[0].start_byte]
        last_label_span = row.cells[0].evidence[-1]
        label_end_line = max((l for l in page4.lines if l.span.start_byte < last_label_span.end_byte_exclusive),
                             key=lambda l: l.line_1based)
        label_bottom = offset_to_box[label_end_line.span.start_byte][3]
        for j, cell in enumerate(row.cells[1:]):
            require(len(cell.evidence) == 1, "matrix value requires a single original line")
            box = offset_to_box[cell.evidence[0].start_byte]
            center = (box[0] + box[2]) / 2
            left = (centers[j-1] + centers[j]) / 2 if j else 170
            right = (centers[j] + centers[j+1]) / 2 if j < 8 else 612
            require(left < center < right, "matrix value escapes visible column")
            require(label_box[1] - 1 <= box[1] <= label_bottom, "matrix value escapes visible row")
    return sum(1 for _ in all_spans(review.model_dump()))


def negative_checks(review, native, layouts):
    """In-memory tamper checks; neither source nor package files are changed."""
    original = review.model_dump(mode="json")
    cases = []
    def add(name, change):
        value = copy.deepcopy(original)
        change(value)
        cases.append((name, value))
    add("missing_page", lambda d: d["pages"].pop())
    add("duplicate_page", lambda d: d["pages"][1].update(physical_page=1))
    add("future_legal_promotion", lambda d: d.update(legal_currentness="verified"))
    add("changed_source_digest", lambda d: d["source"].update(sha256="0" * 64))
    add("native_partition_gap", lambda d: d["pages"][0]["lines"].pop(0))
    add("changed_rate_text", lambda d: d["rows"][0]["cells"][1].update(display_text="$25"))
    add("duplicate_row_identity", lambda d: d["rows"][1].update(row_id=d["rows"][0]["row_id"]))
    add("reversed_row_order", lambda d: d["rows"][0].update(row_order=2))
    add("lost_foundation_condition", lambda d: next(r for r in d["rows"] if r["row_id"] == "P1-MANUFACTURED-R05").update(context_ids=[]))
    def wrong_matrix_column(d):
        row = next(r for r in d["rows"] if r["row_id"] == "P4-MATRIX-R01")
        row["cells"][1]["evidence"], row["cells"][2]["evidence"] = row["cells"][2]["evidence"], row["cells"][1]["evidence"]
        row["cells"][1]["display_text"], row["cells"][2]["display_text"] = row["cells"][2]["display_text"], row["cells"][1]["display_text"]
    add("correct_bytes_wrong_matrix_column", wrong_matrix_column)
    rejected = []
    for name, value in cases:
        try:
            changed = Review.model_validate_json(json.dumps(value))
            validate_content(changed, native, layouts)
        except (ValueError, KeyError):
            rejected.append(name)
        else:
            raise ValueError(f"negative check accepted invalid evidence: {name}")
    return rejected


def validate(root: Path):
    inventory = Inventory.model_validate_json(ordinary(root, "evidence-manifest.json").read_bytes())
    recorded = {a.path for a in inventory.files}
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"symlink forbidden: {path}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == recorded | {"evidence-manifest.json"}, "inventory omission or extra file")
    for asset in inventory.files:
        read_asset(root, asset)
    review = Review.model_validate_json(ordinary(root, "SOURCE_REVIEW.json").read_bytes())
    checked_json(root, "SOURCE_REVIEW.json", "SOURCE_REVIEW.schema.json")
    prep = checked_json(root, "PREPARATION.json", "PREPARATION.schema.json")
    crops = checked_json(root, "CROPS.json", "CROPS.schema.json")
    for asset in [review.source, review.candidate, review.preparation, review.crop_manifest]:
        read_asset(root, asset)
    require(prep["source"] == review.source.model_dump(), "preparation source changed")
    require(prep["candidate"] == review.candidate.model_dump(), "candidate preparation changed")
    require(prep["source_review_mode"] == review.review_mode and prep["external_assignment"] is None, "review identity/order overclaim")
    source = read_asset(root, review.source)
    require(source.startswith(b"%PDF-") and source.rstrip().endswith(b"%%EOF"), "invalid PDF boundaries")
    require(pymupdf.VersionBind == "1.28.2", "reproduction requires PyMuPDF 1.28.2; byte validation and rendering are distinct")
    document = pymupdf.open(stream=source, filetype="pdf")
    require(not document.is_repaired and not document.is_encrypted and len(document) == 5, "PDF structural mismatch")
    native = {}; layouts = {}; candidate_parts = []
    for page in review.pages:
        n = page.physical_page
        retained = read_asset(root, page.native)
        require(document[n-1].get_text("text", sort=False, flags=195).encode() == retained, "native extraction not reproducible")
        native[n] = retained
        layout = json.loads(read_asset(root, page.layout))
        require(layout["source_sha256"] == SOURCE_SHA and layout["physical_page"] == n and layout["native_sha256"] == page.native.sha256, "layout binding mismatch")
        require(layout["get_text_dict"] == json.loads(json.dumps(document[n-1].get_text("dict", sort=False, flags=195))), "layout reproduction differs")
        layouts[n] = layout
        png = document[n-1].get_pixmap(matrix=pymupdf.Matrix(300/72, 300/72), alpha=False).tobytes("png")
        require(png == read_asset(root, page.image), "page PNG reproduction differs")
        pp = prep["pages"][n-1]
        require(pp["native"] == page.native.model_dump() and pp["image"] == page.image.model_dump()
                and pp["layout"] == page.layout.model_dump(), "prepared page binding mismatch")
        candidate_parts.append(f"===== PHYSICAL PAGE {n:04d} =====\n".encode() + retained + b"\n")
        candidate = read_asset(root, review.candidate)
        require(candidate[pp["candidate_start_byte"]:pp["candidate_end_byte_exclusive"]] == retained, "candidate slice binding differs")
    require(b"".join(candidate_parts) == read_asset(root, review.candidate), "candidate separators or bytes changed")
    crop_ids = []
    for crop in crops["crops"]:
        crop_ids.append(crop["crop_id"])
        require(crop["source_sha256"] == SOURCE_SHA and crop["engine"] == "PyMuPDF 1.28.2", "crop source/engine mismatch")
        n = crop["physical_page"]
        rectangle = pymupdf.Rect(crop["pdf_clip_points"])
        require(document[n-1].rect.contains(rectangle) and not rectangle.is_empty, "crop escapes source page")
        pix = document[n-1].get_pixmap(matrix=pymupdf.Matrix(300/72, 300/72), clip=rectangle, alpha=False)
        require(pix.width == crop["width"] and pix.height == crop["height"], "crop dimensions differ")
        require(pix.tobytes("png") == read_asset(root, {k: crop[k] for k in ("path", "sha256", "size_bytes")}), "crop reproduction differs")
    require(len(crop_ids) == len(set(crop_ids)) == 10, "crop inventory incomplete")
    for page in review.pages:
        require(page.viewed_crop_ids == [c["crop_id"] for c in crops["crops"] if c["physical_page"] == page.physical_page], "viewed-crop page binding differs")
    for row in review.rows:
        require(set(row.crop_ids) <= set(review.pages[row.physical_page-1].viewed_crop_ids), "row cites wrong-page crop")
    spans = validate_content(review, native, layouts)
    rejections = negative_checks(review, native, layouts)
    # Preserve chain of custody without opening external historical paths.
    manual = read_asset(root, prep["original_manual_manifest"])
    manual_lines = manual.splitlines(keepends=True)
    require(len(manual_lines) == 38 and prep["manual_manifest_line"] == 35, "frozen manual manifest differs")
    selected_line = manual_lines[34]
    require(digest(selected_line) == prep["manual_record_line_sha256"], "selected intake line digest differs")
    record = json.loads(selected_line)
    require(record == prep["selected_manual_record"] and record["record_id"] == review.source_id, "manual intake identity differs")
    require(record["sha256"] == SOURCE_SHA and record["size_bytes"] == len(source), "manual source digest/size differs")
    require(record["acquisition_method"] == "received_review_package" and record["status"] == "archived_pending_pipeline"
            and record["official_source_url"] is None, "custody/currentness was promoted")
    require(record["received_at"] == review.received_at.isoformat().replace("+00:00", "Z"), "receipt time changed")
    intake_schema = json.loads(ordinary(root, "custody/intake-record.schema.json").read_bytes())
    for line in manual_lines:
        jsonschema.Draft202012Validator(intake_schema).validate(json.loads(line))
    for asset in prep["custody_files"]:
        read_asset(root, asset)
    checked_json(root, "custody/intake-receipt.json", "custody/intake-receipt.schema.json")
    checked_json(root, "custody/sd008-CUSTODY_RECEIPT.json", "custody/sd008-CUSTODY_RECEIPT.schema.json")
    audit = checked_json(root, "custody/sd008-INTAKE_AUDIT.json", "custody/sd008-INTAKE_AUDIT.schema.json")
    selected = [s for s in audit["source_checks"] if s["priority_id"] == "SD008-01"]
    require(len(selected) == 1 and selected[0]["primary"]["sha256"] == SOURCE_SHA
            and selected[0]["primary"]["size_bytes"] == len(source), "SD008 source custody mismatch")
    provenance_schema = json.loads(ordinary(root, "custody/source-provenance.schema.json").read_bytes())
    records = [json.loads(line) for line in ordinary(root, "custody/source-provenance.jsonl").read_bytes().splitlines()]
    for value in records:
        jsonschema.Draft202012Validator(provenance_schema).validate(value)
    records = [v for v in records if v["source_id"] == review.source_id]
    require(len(records) == 1, "unique source provenance required")
    provenance = records[0]
    require(provenance["canonical_original"]["sha256"] == SOURCE_SHA and provenance["canonical_original"]["path"] == record["archive_path"], "canonical provenance mismatch")
    require(provenance["reported_requested_url"] == review.supplied_url_claim and provenance["reported_final_url"] is None
            and provenance["reported_acquisition_at"] is None and provenance["official_source_url"] is None
            and provenance["legal_currentness"] == "not_verified" and provenance["semantic_or_coverage_promotion"] is False,
            "supplied acquisition/currentness qualifications differ")
    return {"validation_passed": True, "source_sha256": SOURCE_SHA, "physical_pages": 5,
            "reproduced_full_page_images": 5, "reproduced_crops": 10,
            "native_bytes": 14311, "native_changes": 0, "native_lines": 567,
            "fee_and_value_rows": 107, "tables": 19, "valuation_matrix_cells": 252,
            "all_value_cells_including_referrals_and_percentages": 331,
            "contexts": 18, "observations": 13, "replayed_native_spans": spans,
            "in_memory_negative_checks_rejected": rejections,
            "inventory_files_including_manifest": len(inventory.files) + 1,
            "legal_currentness": "not_verified", "external_assignment": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parent)
    args = parser.parse_args()
    print(json.dumps(validate(args.root.absolute()), indent=2))
