"""Read-only structural replay for one fixed Spanish source; no new visual/legal judgment."""
from __future__ import annotations
import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
import math
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import jsonschema
import pymupdf
from audit_models import Asset, CheckResult, Custody, Manifest, RunResult
from review_models import Review

HERE = Path(__file__).absolute().parent
SOURCE_SHA = "fd162c37442dc99097a272d9ebbf74fbfd063f2dc2f2226fdeb8b93a53849ec9"
QA_SHA = "2372e6bde1fa544c56dbaed1a808a7389bf943006f8d2d4c65dd5fa10a8ad46f"
SID = "el-paso-boh-ehs-fees-spanish-sd011"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary(root, name):
    part = Path(name)
    require(not part.is_absolute() and ".." not in part.parts and "\\" not in name
            and part.as_posix() == name, "unsafe evidence path")
    path = root / part
    require(not any(p.is_symlink() for p in (path, *path.parents)), "linked evidence")
    require(stat.S_ISREG(path.stat().st_mode), "nonordinary evidence")
    return path


def asset(root, item):
    raw = ordinary(root, item.path).read_bytes()
    require(len(raw) == item.size_bytes and digest(raw) == item.sha256,
            "asset hash/size differs: " + item.path)
    return raw


def typed(root, name, model):
    raw = ordinary(root, name + ".json").read_bytes()
    schema = json.loads(ordinary(root, name + ".schema.json").read_bytes())
    require(schema == model.model_json_schema(), "schema differs: " + name)
    jsonschema.validate(json.loads(raw), schema)
    return model.model_validate_json(raw)


def span_bytes(span, native, expected_page=None):
    require(span.page in native, "span page outside fixed source")
    require(expected_page is None or span.page == expected_page, "span on wrong physical page")
    raw = native[span.page]
    require(0 <= span.start_byte < span.end_byte <= len(raw), "span bounds invalid")
    selected = raw[span.start_byte:span.end_byte]
    require(selected.decode("utf-8") == span.text and digest(selected) == span.sha256,
            "native byte span/text/hash differs")
    return selected


def match_cell(raw, value, cursor):
    """Find the exact sequential native occurrence, allowing only whitespace separation."""
    text = raw.decode("utf-8")
    start_char = len(raw[:cursor].decode("utf-8"))
    expression = r"\s*".join(re.escape(ch) for ch in value if not ch.isspace())
    match = re.search(expression, text[start_char:])
    require(match is not None, "table cell absent from native page")
    start = start_char + match.start()
    end = start_char + match.end()
    return len(text[:start].encode()), len(text[:end].encode())


def bounds(raw, start, end=None):
    begin = raw.index(start.encode())
    finish = raw.index(end.encode(), begin) if end is not None else begin + len(start.encode())
    return begin, finish


def passage_contract(native):
    """Bound complete fixed-source contexts, including all exceptions and page transitions."""
    items = {
        "cover": (1, "cover_and_agency", "REGULACIONES", "Aprobado"),
        "chapter-and-section-a": (2, "governing_section_context", "CAPÍTULO 3",
                                  "2024 TARIFAS PROGRAMADAS"),
        "asterisk-note": (4, "table_footnote", "* Incluye una reinspección.", None),
        "section-b": (4, "penalty_exception_context", "B.  La falta", "Definiciones"),
        "definitions-headings": (4, "definitions_heading", "Definiciones", "(1) Una"),
        "definition-1": (4, "rfe_definition", "(1) Una evaluación", "(2) "),
        "definition-2": (4, "rfe_definition", "(2) Una inspección", "(3) "),
        "definition-3": (4, "rfe_definition", "(3) Un documento", "(4) "),
        "definition-4": (4, "rfe_definition", "(4) Un proceso", "Sistemas de tratamiento"),
        "owts-definitions-heading": (4, "definitions_heading", "Sistemas de tratamiento",
                                     "(5) Reparación"),
        "definition-5": (4, "owts_definition", "(5) Reparación", "(6) Reparación"),
        "definition-6": (4, "owts_definition", "(6) Reparación", "Aprobado"),
        "definition-7": (5, "owts_definition", "(7) Reinspección", "Cuido de niños:"),
        "childcare-definitions": (5, "childcare_definitions", "Cuido de niños:", "Aprobado"),
        "other-notes": (6, "general_fee_notes", "Otras notas:", "Aprobado"),
    }
    expected = {}
    for identity, (page, role, first, last) in items.items():
        expected[identity] = (page, role, *bounds(native[page], first, last))
    for page, raw in native.items():
        start = raw.index(b"Aprobado")
        expected[f"footer-{page}"] = (
            page, "partially_obscured_footer", start, raw.index(b"\n", start))
        start, end = bounds(raw, "d\n2023")
        expected[f"footer-tail-{page}"] = (
            page, "native_text_without_complete_visual_support", start, end)
    return expected


def link_contract(rows):
    fee_ids = [r.row_id for r in rows if r.role == "fee"]
    owts = "p2-t1-r25"
    contracts = {
        "license-page-continuation": (
            "continuation", ["p3-t2-r30", "p4-t1-r01"], []),
        "owts-category-continuation": (
            "continuation", [owts] + [r.row_id for r in rows if r.category_source_row == owts], []),
        "governing-context": (
            "section_context", fee_ids, ["chapter-and-section-a", "section-b", "other-notes"]),
    }
    for marker, target in [("*", "asterisk-note")] + [
            (f"({n})", f"definition-{n}") for n in range(1, 8)]:
        source_ids = [r.row_id for r in rows if marker in (r.cells[0].text or "")]
        require(bool(source_ids), "fixed source footnote marker missing")
        contracts["footnote-" + target] = ("footnote", source_ids, [target])
    return contracts


def check_review_payload(package, payload):
    """Semantic bindings beneath the outer seal, separately exercisable with adversarial records."""
    root = package / "received"
    review = Review.model_validate_json(json.dumps(payload))
    schema = json.loads(ordinary(root, "SOURCE_QA.schema.json").read_bytes())
    require(schema == Review.model_json_schema(), "root review schema/model mismatch")
    jsonschema.validate(payload, schema)
    source = asset(root, review.source)
    require(review.source.sha256 == SOURCE_SHA and len(source) == 252997,
            "wrong fixed source PDF")
    require(source.startswith(b"%PDF-") and source.rstrip().endswith(b"%%EOF"), "PDF framing")
    require(pymupdf.VersionBind == "1.28.2", "PyMuPDF version differs from extraction/table contract")
    packet = package / "packet-evidence"
    manifest = json.loads(ordinary(packet, "MANIFEST.json").read_bytes())
    packet_pins = {a["path"]: a for a in manifest["files"]}
    extraction = json.loads(ordinary(packet, "02-candidate-text/" + SID + "/EXTRACTION.json")
                            .read_bytes())
    require(extraction["method"] == "PyMuPDF 1.28.2 Page.get_text(text, flags=195, sort=False)"
            and extraction["normalization"] == "none; physical-page markers are packaging"
            and extraction["source_sha256"] == SOURCE_SHA, "native extraction settings differ")
    native, image_raw, images = {}, {}, {}
    reconstructed = b""
    with pymupdf.open(stream=source, filetype="pdf") as document:
        require(document.page_count == 6 and not document.is_repaired and not document.is_encrypted,
                "source PDF structural state differs")
        for page in review.pages:
            number = page.page
            require(page.native.path == f"inputs/page-{number:04}.native.txt"
                    and page.png.path == f"inputs/page-{number:04}.png", "page asset order differs")
            raw = asset(root, page.native)
            require(raw == document[number - 1].get_text("text", flags=195, sort=False).encode(),
                    "native text not reproducible from source")
            require(page.text.encode() == raw, "page text differs from unchanged native")
            native[number] = raw
            image_raw[number] = asset(root, page.png)
            images[number] = pymupdf.Pixmap(image_raw[number])
            require((images[number].width, images[number].height, images[number].n)
                    == (2550, 3300, 3), "full page image dimensions/channels differ")
            require(list(document[number - 1].rect) == [0.0, 0.0, 612.0, 792.0],
                    "PDF page geometry differs")
            for item, subdirectory in [(page.png, "01-source-only"),
                                       (page.native, "02-candidate-text")]:
                pin = packet_pins[f"{subdirectory}/{SID}/{Path(item.path).name}"]
                require(item.sha256 == pin["sha256"] and item.size_bytes == pin["size_bytes"],
                        "page/candidate packet identity differs")
            reconstructed += f"===== PHYSICAL PDF PAGE {number} OF 6 (PACKAGING MARKER) =====\n".encode()
            begin = len(reconstructed)
            reconstructed += raw
            extracted = extraction["pages"][number - 1]
            require(extracted["physical_page"] == number
                    and (extracted["candidate_start"], extracted["candidate_end"])
                    == (begin, len(reconstructed)), "candidate page offsets differ")
            reconstructed += f"\n===== END PHYSICAL PDF PAGE {number} (PACKAGING MARKER) =====\n\n".encode()
        require(asset(root, review.candidate) == reconstructed, "candidate markers/content differ")
        require(sum(map(len, native.values())) == review.native_bytes == 10216
                and len(reconstructed) == review.candidate_bytes == 10894, "native/candidate counts differ")
        expected_rows, category = [], None
        blank_count = merged_count = span_count = table_count = 0
        for page in range(1, 7):
            cursor = 0
            # The library may print a one-time optional-layout advisory. Keep CLI JSON clean.
            with redirect_stdout(io.StringIO()):
                tables = document[page - 1].find_tables().tables
            for table_index, table in enumerate(tables, 1):
                table_count += 1
                values = table.extract()
                for row_index, (cells, geometry) in enumerate(zip(values, table.rows), 1):
                    identity = f"p{page}-t{table_index}-r{row_index:02}"
                    row = review.rows[len(expected_rows)]
                    require((row.row_id, row.physical_page, row.physical_table, row.physical_row)
                            == (identity, page, table_index, row_index), "physical row mapping differs")
                    require(len(cells) == 2 and len(row.cells) == 2, "physical column count differs")
                    role = "fee"
                    if page == 2 and row_index == 1:
                        role = "title"
                    elif page == 2 and row_index == 2:
                        role = "column_headers"
                    elif cells[1] is None:
                        role = "category"
                    elif (page, table_index, row_index) == (4, 1, 1):
                        role = "continuation"
                    require(row.role == role, "row fee/category/continuation role differs")
                    if role == "category":
                        category = identity
                    expected_category = category if role in {"fee", "continuation"} else None
                    require(row.category_source_row == expected_category, "category association differs")
                    for column, (value, box, cell) in enumerate(zip(cells, geometry.cells, row.cells), 1):
                        require(cell.column == column and cell.text == value, "PDF table cell text differs")
                        require(cell.span_columns == (2 if column == 1 and cells[1] is None else 1),
                                "merged column span differs")
                        if box is None:
                            require(cell.bbox is None, "merged cell geometry differs")
                        else:
                            require(cell.bbox is not None and len(cell.bbox) == 4
                                    and all(math.isfinite(v) for v in cell.bbox)
                                    and all(abs(a - b) <= 1e-6 for a, b in zip(box, cell.bbox)),
                                    "PDF cell geometry differs")
                        representation = ("merged_into_left" if value is None else
                                          "visibly_blank" if value == "" else
                                          "visible_text_native_whitespace_preserved_separately")
                        require(cell.representation == representation, "blank/merged/text role differs")
                        if value is None or value == "":
                            require(cell.native_span is None, "blank/merged cell acquired native text")
                            blank_count += int(value == "")
                            merged_count += int(value is None)
                        else:
                            require(cell.native_span is not None, "text cell lacks native span")
                            span_bytes(cell.native_span, native, page)
                            start, end = match_cell(native[page], value, cursor)
                            require((cell.native_span.start_byte, cell.native_span.end_byte)
                                    == (start, end), "cell native occurrence/ordering differs")
                            cursor = end
                            span_count += 1
                    expected_rows.append(identity)
        require(len(expected_rows) == 75 and table_count == 5, "physical table completeness differs")
    contract = passage_contract(native)
    require(len(review.passages) == len(contract) == 27
            and {p.id for p in review.passages} == set(contract), "passage identity coverage differs")
    for passage in review.passages:
        page, role, start, end = contract[passage.id]
        span_bytes(passage.span, native, page)
        require((passage.role, passage.span.start_byte, passage.span.end_byte) == (role, start, end),
                "complete context/footer passage bounds differ: " + passage.id)
        span_count += 1
    links = link_contract(review.rows)
    require(len(review.links) == len(links) == 11
            and {link.id for link in review.links} == set(links), "link identity coverage differs")
    for link in review.links:
        require((link.kind, link.source_rows, link.target_passages) == links[link.id],
                "footnote/category/continuation link differs: " + link.id)
    crop_preparation = json.loads(ordinary(root, "CROP_PREPARATION.json").read_bytes())
    crop_metadata = {c["path"]: c for c in crop_preparation}
    require(len(review.crops) == len(crop_metadata) == 15
            and {c.asset.path for c in review.crops} == set(crop_metadata), "crop coverage differs")
    crop_pages = {}
    for crop in review.crops:
        claimed = crop_metadata[crop.asset.path]
        require(crop.source_page in native and len(crop.box_pixels) == 4, "crop source page/bounds")
        require((crop.source_page, crop.source_sha256, crop.box_pixels, crop.method,
                 crop.asset.sha256, crop.asset.size_bytes) ==
                (claimed["physical_page"], claimed["source_sha256"], claimed["box_pixels"],
                 claimed["method"], claimed["sha256"], claimed["size_bytes"]), "crop metadata differs")
        source_image = images[crop.source_page]
        require(crop.source_sha256 == digest(image_raw[crop.source_page]), "crop parent hash differs")
        x0, y0, x1, y1 = crop.box_pixels
        require(0 <= x0 < x1 <= source_image.width and 0 <= y0 < y1 <= source_image.height,
                "crop outside complete page image")
        rectangle = pymupdf.IRect(crop.box_pixels)
        replay = pymupdf.Pixmap(source_image.colorspace, rectangle, source_image.alpha)
        replay.copy(source_image, rectangle)
        retained = asset(root, crop.asset)
        pixels = pymupdf.Pixmap(retained)
        require((pixels.width, pixels.height, pixels.n) == (x1 - x0, y1 - y0, source_image.n)
                and pixels.samples == replay.samples, "crop pixel replay differs")
        require(digest(replay.tobytes("png")) == crop.asset.sha256, "crop PNG byte replay differs")
        crop_pages[crop.asset.path] = crop.source_page
    require([f.page for f in review.footer_evidence] == list(range(1, 7)), "six footer records required")
    for footer in review.footer_evidence:
        require(footer.first_line_passage == f"footer-{footer.page}"
                and footer.native_tail_passage == f"footer-tail-{footer.page}"
                and crop_pages.get(footer.exact_pixel_crop) == footer.page,
                "footer passage/crop binding differs")
        require(footer.visually_certified_year is None and not footer.full_tail_visually_readable,
                "unsupported footer year promotion")
    return CheckResult(
        status="passed_structural_source_bindings_only", source_sha256=SOURCE_SHA, source_pages=6,
        native_bytes=10216, candidate_bytes=10894, physical_table_fragments=5,
        physical_rows=75, fee_rows=65, native_spans_checked=span_count,
        visibly_blank_cells_as_recorded=blank_count, merged_placeholder_cells=merged_count,
        passage_bindings=27, link_bindings=11, crop_pixel_replays=15,
        footer_limitations_preserved=6, visually_certified_footer_year=None,
        new_visual_review_pages=0, legal_currentness="not_verified", answer_safe=False,
        translation_equivalence_verified=False, external_reports_consulted=False,
    )


def rerender_pages(package):
    """Replay original Poppler settings into stdout; no image files or root bytes are written."""
    render = json.loads(ordinary(package, "packet-evidence/04-verification/render-events/" +
                                 SID + "/RENDER.json").read_bytes())
    executable = shutil.which("pdftoppm")
    require(executable is not None, "Poppler executable unavailable")
    with open(executable, "rb") as handle:
        require(hashlib.file_digest(handle, "sha256").hexdigest() == render["renderer_sha256"],
                "Poppler executable identity differs")
    pdf = ordinary(package, "received/inputs/original.pdf")
    for page in range(1, 7):
        result = subprocess.run([executable, "-r", "300", "-f", str(page), "-l", str(page),
                                 "-singlefile", "-png", str(pdf)],
                                capture_output=True, check=False, timeout=60)
        require(result.returncode == 0, "Poppler page replay failed")
        original = ordinary(package, f"received/inputs/page-{page:04}.png").read_bytes()
        require(result.stdout == original, "Poppler full-page PNG replay differs")
    return 6


def verify(package=HERE, rerender=False):
    """Closed portable verification; source claims and agent observations remain scoped."""
    manifest = typed(package, "FINAL_MANIFEST", Manifest)
    expected = {a.path for a in manifest.files} | {"FINAL_MANIFEST.json"}
    actual = set()
    for top, dirs, files in os.walk(package, followlinks=False):
        for name in dirs + files:
            require(not (Path(top) / name).is_symlink(), "linked package member")
        for name in files:
            path = Path(top) / name
            require(stat.S_ISREG(path.stat().st_mode), "nonordinary package member")
            actual.add(path.relative_to(package).as_posix())
    require(len(expected) == len(manifest.files) + 1 and actual == expected,
            "closed package membership differs")
    for item in manifest.files:
        asset(package, item)
    custody = typed(package, "CUSTODY", Custody)
    require(custody.source_review_sha256 == QA_SHA, "review custody identity differs")
    for item in custody.items:
        asset(package, item.retained)
    review_raw = ordinary(package, "received/SOURCE_QA.json").read_bytes()
    require(digest(review_raw) == QA_SHA, "source QA pin differs")
    require(ordinary(package, "review_models.py").read_bytes()
            == ordinary(package, "received/models.py").read_bytes(), "root models copy differs")
    packet_raw = ordinary(package, "packet-evidence/MANIFEST.json").read_bytes()
    require(digest(packet_raw) == custody.packet_manifest_sha256, "packet manifest pin differs")
    pins = {a["path"]: a for a in json.loads(packet_raw)["files"]}
    for item in custody.items:
        if item.retained.path.startswith("packet-evidence/"):
            name = item.retained.path.removeprefix("packet-evidence/")
            if name not in {"MANIFEST.json", "MANIFEST.schema.json"}:
                require(item.retained.sha256 == pins[name]["sha256"]
                        and item.retained.size_bytes == pins[name]["size_bytes"],
                        "selected packet metadata pin differs")
    canonical = ordinary(package, "packet-evidence/03-custody/" + SID + "/canonical-record.jsonl")
    with canonical.open("rb") as stream:
        record_rows = [json.loads(line) for line in stream]
    require(len(record_rows) == 1 and record_rows[0]["record_id"] == SID
            and record_rows[0]["sha256"] == SOURCE_SHA, "retained canonical custody row differs")
    result = check_review_payload(package, json.loads(review_raw))
    output = result.model_dump(mode="json")
    output["full_page_png_replays"] = rerender_pages(package) if rerender else 0
    output["public_requests"] = 0
    return RunResult.model_validate(output).model_dump(mode="json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerender", action="store_true", help="Replay six complete Poppler PNGs")
    args = parser.parse_args()
    print(json.dumps(verify(rerender=args.rerender), indent=2))
