"""Adversarial source-binding tests; mutations stay in temporary copied fixtures."""
from __future__ import annotations
import copy
import hashlib
import json
import shutil
from pathlib import Path

import pymupdf
import pytest
import validate_eb025 as check
from audit_models import Asset, Manifest

ROOT = Path(__file__).absolute().parent


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "copy"
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "validation"))
    data = json.loads((root / "received/SOURCE_QA.json").read_bytes())
    return root, data


def reseal(root):
    schema = root / "FINAL_MANIFEST.schema.json"
    schema.write_text(json.dumps(Manifest.model_json_schema(), indent=2) + "\n")
    assets = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != root / "FINAL_MANIFEST.json":
            raw = path.read_bytes()
            assets.append(Asset(path=path.relative_to(root).as_posix(),
                                sha256=check.digest(raw), size_bytes=len(raw)))
    m = Manifest(status="FROZEN_INDEPENDENT_STRUCTURAL_VALIDATOR", files=assets)
    (root / "FINAL_MANIFEST.json").write_text(m.model_dump_json(indent=2) + "\n")


def row(data, identity):
    return next(r for r in data["rows"] if r["row_id"] == identity)


def passage(data, identity):
    return next(p for p in data["passages"] if p["id"] == identity)


def set_span(span, raw, start, end):
    span.update(start_byte=start, end_byte=end, text=raw[start:end].decode(),
                sha256=check.digest(raw[start:end]))


def test_actual_complete_structural_result(fixture):
    root, data = fixture
    result = check.check_review_payload(root, data)
    assert result.physical_rows == 75 and result.fee_rows == 65
    assert result.native_spans_checked == 168 and result.crop_pixel_replays == 15
    assert result.visibly_blank_cells_as_recorded == 1 and result.merged_placeholder_cells == 8
    assert result.visually_certified_footer_year is None
    assert result.new_visual_review_pages == 0 and not result.answer_safe


@pytest.mark.parametrize("kind", ["fee", "label", "row_page", "row_id", "category", "geometry",
                                  "blank_zero", "blank_merged", "merged_value", "span_columns",
                                  "native_page", "native_offset", "native_hash", "native_text"])
def test_table_and_native_binding_mutations(fixture, kind):
    root, data = fixture
    selected = row(data, "p2-t1-r04")
    if kind == "fee": selected["cells"][1]["text"] = "$166.00 por seis meses"
    elif kind == "label": selected["cells"][0]["text"] = "Different source service"
    elif kind == "row_page": selected["physical_page"] = 3
    elif kind == "row_id": selected["row_id"] = "p2-t1-r99"
    elif kind == "category": selected["category_source_row"] = "p2-t1-r13"
    elif kind == "geometry": selected["cells"][1]["bbox"][0] += 1.0
    elif kind == "span_columns": selected["cells"][1]["span_columns"] = 2
    elif kind in {"blank_zero", "blank_merged"}:
        c = row(data, "p4-t1-r01")["cells"][1]
        c["text"] = "$0.00" if kind == "blank_zero" else None
        c["representation"] = ("visible_text_native_whitespace_preserved_separately"
                               if kind == "blank_zero" else "merged_into_left")
    elif kind == "merged_value": row(data, "p2-t1-r01")["cells"][1]["text"] = "0"
    else:
        span = selected["cells"][1]["native_span"]
        if kind == "native_page": span["page"] = 3
        elif kind == "native_offset": span["start_byte"] += 1
        elif kind == "native_hash": span["sha256"] = "0" * 64
        else: span["text"] = "$166"
    with pytest.raises(ValueError): check.check_review_payload(root, data)


def test_same_valid_amount_from_wrong_occurrence_refused(fixture):
    root, data = fixture
    selected = row(data, "p2-t1-r11")["cells"][1]
    earlier = row(data, "p2-t1-r07")["cells"][1]
    assert selected["text"] == earlier["text"]
    selected["native_span"] = copy.deepcopy(earlier["native_span"])
    with pytest.raises(ValueError, match="occurrence/ordering"):
        check.check_review_payload(root, data)


@pytest.mark.parametrize("kind", ["footnote", "context", "license", "owts", "duplicate", "missing"])
def test_referential_links_refused(fixture, kind):
    root, data = fixture
    if kind == "footnote": data["links"][-1]["source_rows"] = ["p3-t1-r02"]
    elif kind == "context": data["links"][2]["source_rows"].pop()
    elif kind == "license": data["links"][0]["source_rows"] = ["p3-t2-r30"]
    elif kind == "owts": data["links"][1]["source_rows"].pop()
    elif kind == "duplicate": data["links"][-1]["id"] = data["links"][-2]["id"]
    else: data["links"].pop()
    with pytest.raises(ValueError, match="link"):
        check.check_review_payload(root, data)


@pytest.mark.parametrize("kind", ["exception_cut", "footer_one_word", "tail_cut", "wrong_role"])
def test_complete_passage_boundaries(fixture, kind):
    root, data = fixture
    identity = {"exception_cut": "definition-6", "footer_one_word": "footer-1",
                "tail_cut": "footer-tail-6", "wrong_role": "definition-7"}[kind]
    p = passage(data, identity)
    raw = (root / f"received/inputs/page-{p['span']['page']:04}.native.txt").read_bytes()
    if kind == "exception_cut":
        end = raw.index("con la excepción".encode(), p["span"]["start_byte"])
        set_span(p["span"], raw, p["span"]["start_byte"], end)
    elif kind == "footer_one_word":
        set_span(p["span"], raw, p["span"]["start_byte"], p["span"]["start_byte"] + 8)
    elif kind == "tail_cut":
        set_span(p["span"], raw, p["span"]["start_byte"], p["span"]["end_byte"] - 1)
    else:
        p["role"] = "general_fee_notes"
    with pytest.raises(ValueError, match="complete context/footer"):
        check.check_review_payload(root, data)


def test_actual_historical_one_word_footer_draft_rejected(fixture):
    root, _ = fixture
    p = root / "received/preparation-history/before-complete-footer-spans/SOURCE_QA.json"
    older = json.loads(p.read_bytes())
    with pytest.raises(ValueError, match="complete context/footer"):
        check.check_review_payload(root, older)


@pytest.mark.parametrize("field,value", [("legal_currentness", "verified"), ("answer_safe", True),
                                        ("translation_equivalence_verified", True),
                                        ("external_reports_consulted", True),
                                        ("language", "English"), ("source_modified", True)])
def test_scope_promotions_refused(fixture, field, value):
    root, data = fixture; data[field] = value
    with pytest.raises(ValueError): check.check_review_payload(root, data)


@pytest.mark.parametrize("kind", ["year", "readable", "missing", "wrong_page", "wrong_crop"])
def test_six_footer_qualifications(fixture, kind):
    root, data = fixture
    if kind == "year": data["footer_evidence"][0]["visually_certified_year"] = 2023
    elif kind == "readable": data["footer_evidence"][0]["full_tail_visually_readable"] = True
    elif kind == "missing": data["footer_evidence"].pop()
    elif kind == "wrong_page": data["footer_evidence"][0]["page"] = 5
    else: data["footer_evidence"][0]["exact_pixel_crop"] = "crops/page-0005-footer-left.png"
    with pytest.raises(ValueError): check.check_review_payload(root, data)


@pytest.mark.parametrize("kind", ["source", "candidate", "native", "page_image"])
def test_altered_artifact_with_updated_local_digest(fixture, kind):
    root, data = fixture
    target = {"source": data["source"], "candidate": data["candidate"],
              "native": data["pages"][1]["native"], "page_image": data["pages"][0]["png"]}[kind]
    path = root / "received" / target["path"]
    if kind == "page_image":
        original = root / "received/inputs/page-0005.png"
        replacement = original.read_bytes()
    else:
        replacement = path.read_bytes() + b"changed"
    path.write_bytes(replacement)
    target.update(sha256=check.digest(replacement), size_bytes=len(replacement))
    with pytest.raises(ValueError): check.check_review_payload(root, data)


@pytest.mark.parametrize("kind", ["pixel", "out_of_bounds", "page", "crop_sha", "missing"])
def test_crop_proof_mutations(fixture, kind):
    root, data = fixture
    crop = data["crops"][0]
    metadata_path = root / "received/CROP_PREPARATION.json"
    metadata = json.loads(metadata_path.read_bytes())
    m = next(x for x in metadata if x["path"] == crop["asset"]["path"])
    if kind == "pixel":
        path = root / "received" / crop["asset"]["path"]
        pixmap = pymupdf.Pixmap(str(path)); pixmap.set_pixel(0, 0, (0, 0, 0))
        raw = pixmap.tobytes("png"); path.write_bytes(raw)
        crop["asset"].update(sha256=check.digest(raw), size_bytes=len(raw))
        m.update(sha256=check.digest(raw), size_bytes=len(raw))
        metadata_path.write_text(json.dumps(metadata))
    elif kind == "out_of_bounds":
        crop["box_pixels"] = [0, 0, 0, 5]; m["box_pixels"] = crop["box_pixels"]
        metadata_path.write_text(json.dumps(metadata))
    elif kind == "page": crop["source_page"] = 5
    elif kind == "crop_sha": crop["source_sha256"] = "0" * 64
    else: data["crops"].pop()
    with pytest.raises(ValueError, match="crop"):
        check.check_review_payload(root, data)


def test_wrong_native_extraction_settings(fixture):
    root, data = fixture
    path = root / ("packet-evidence/02-candidate-text/" + check.SID + "/EXTRACTION.json")
    value = json.loads(path.read_bytes()); value["method"] = "flags=0 sort=True"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="settings"):
        check.check_review_payload(root, data)


def test_closed_portable_wrapper(fixture):
    root, _ = fixture; reseal(root)
    result = check.verify(root)
    assert result["status"] == "passed_structural_source_bindings_only"
    assert result["full_page_png_replays"] == 0
    (root / "unlisted.txt").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="membership"): check.verify(root)


def test_closed_hash_detects_changed_proof(fixture):
    root, _ = fixture; reseal(root)
    p = root / "received/inputs/candidate.txt"; p.write_bytes(p.read_bytes() + b"x")
    with pytest.raises(ValueError, match="hash/size"): check.verify(root)


def test_schema_mutation_refused(fixture):
    root, _ = fixture; reseal(root)
    path = root / "FINAL_MANIFEST.schema.json"; data = json.loads(path.read_bytes())
    data["properties"]["status"] = {"type": "string"}; path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="schema differs"): check.verify(root)


def test_path_escape_and_symlink_refusal(fixture, tmp_path):
    root, data = fixture
    for name in ["../outside", "/absolute", "a\\b", "a//b"]:
        with pytest.raises(ValueError, match="unsafe"): check.ordinary(root, name)
    p = root / "received/inputs/original.pdf"
    outside = tmp_path / "same.pdf"; p.rename(outside); p.symlink_to(outside)
    with pytest.raises(ValueError, match="linked"): check.check_review_payload(root, data)


def test_poppler_unavailable_refusal(fixture, monkeypatch):
    root, _ = fixture; monkeypatch.setattr(check.shutil, "which", lambda _: None)
    with pytest.raises(ValueError, match="unavailable"): check.rerender_pages(root)


def test_poppler_identity_refusal(fixture, monkeypatch, tmp_path):
    root, _ = fixture; executable = tmp_path / "fake"; executable.write_bytes(b"not renderer")
    monkeypatch.setattr(check.shutil, "which", lambda _: str(executable))
    with pytest.raises(ValueError, match="identity differs"): check.rerender_pages(root)
