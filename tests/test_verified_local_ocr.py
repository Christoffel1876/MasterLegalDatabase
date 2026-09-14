"""Full-page OCR evidence, adverse inputs, and offline validation without macOS."""

from __future__ import annotations

import json
import runpy
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pymupdf
import pytest
from pydantic import ValidationError

from geode.pipeline import verified_local_ocr as ocr
from geode.pipeline.local_coverage import CATEGORIES, CoverageLedger


@pytest.fixture
def sample(tmp_path: Path) -> SimpleNamespace:
    """Use genuine PDF bytes and the complete ledger contract, without source mocks."""
    with pymupdf.open() as doc:
        for _ in range(2):
            doc.new_page(width=200, height=250)
        body = doc.tobytes()
    digest = ocr.sha256(body)
    relative = f"_RAW_ARCHIVE/local/coverage/{digest}.pdf"
    raw = tmp_path / relative
    raw.parent.mkdir(parents=True)
    raw.write_bytes(body)
    source = dict(
        source_id="scan", authority_id="CO-MUNICIPAL-GOLDEN", title="Scanned fixture",
        url="https://www.cityofgolden.gov/scan.pdf",
        final_url="https://www.cityofgolden.gov/scan.pdf",
        retrieved_at=datetime.now(timezone.utc).isoformat(), archive_path=relative,
        sha256=digest, size_bytes=len(body), media_type="pdf", kind="legal_text",
        categories=["fees"], provenance_notes="Fixture original", currentness_notes="Unknown",
        extraction_status="ocr_required", pdf_pages=2,
    )
    rows = [dict(category=category, source_ids=["scan"] if category == "fees" else [],
                 collection="legal_documents_preserved" if category == "fees" else "missing",
                 completeness="partial" if category == "fees" else "not_assessed",
                 gap="Not legally reviewed", next_action="Reconcile applicable law")
            for category in CATEGORIES]
    data = dict(
        prepared_at=source["retrieved_at"], baseline_commit="a" * 40, scope="Fixture only",
        sources=[source], directory_assessments=[], limitations=["No legal verification"],
        authorities=[dict(authority_id="CO-MUNICIPAL-GOLDEN", name="Golden", level="municipal",
                          identity_basis="Fixture identity", checklist=rows)],
    )
    value = SimpleNamespace(root=tmp_path, output=tmp_path / "derived", raw=raw,
                            ledger=tmp_path / "ledger.json", data=data, digest=digest)
    save_ledger(value)
    return value


def save_ledger(sample: SimpleNamespace) -> None:
    """Validate every fixture metadata mutation before writing it."""
    sample.ledger.write_text(CoverageLedger.model_validate(sample.data).model_dump_json())


def engine(image: Path) -> tuple[ocr.EngineInfo, list[ocr.OCRLine]]:
    """Return observations only after confirming a complete PNG was rendered."""
    assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    return (ocr.EngineInfo(version="Test OS", adapter_sha256="a" * 64),
            [ocr.OCRLine(text="Every applicant must preserve this full machine observation.",
                         confidence=0.95, bbox=(0.1, 0.1, 0.8, 0.1))])


def collect(sample: SimpleNamespace, **kwargs: object) -> ocr.CollectionSummary:
    """Exercise the actual rasterize/write/validate transaction with a deterministic engine."""
    return ocr.collect_ocr(sample.root, sample.output, sample.ledger,
                           kwargs.pop("engine", engine), dpi=150, **kwargs)


def load_manifest(sample: SimpleNamespace) -> dict:
    """Read the exact completed source receipt."""
    return json.loads((sample.output / sample.digest / "manifest.json").read_text())


def rewrite_manifest(sample: SimpleNamespace, data: dict) -> None:
    """Deliberately corrupt a receipt for adversarial tests."""
    (sample.output / sample.digest / "manifest.json").write_text(json.dumps(data))


def rewrite_page(sample: SimpleNamespace, number: int, field: str, value: object) -> None:
    """Rehash a tampered page so validation must inspect its semantics as well as bytes."""
    manifest = load_manifest(sample)
    record = manifest["pages"][number - 1]
    path = sample.output / record["path"]
    data = json.loads(path.read_text())
    data[field] = value
    body = json.dumps(data).encode()
    path.write_bytes(body)
    record.update(sha256=ocr.sha256(body), size_bytes=len(body))
    rewrite_manifest(sample, manifest)


def test_full_pages_exact_text_immutable_sources_and_offline_validation(
    sample: SimpleNamespace,
) -> None:
    before = sample.raw.read_bytes()
    text = "  full OCR text\n" * 10000 + "last observation retained  "

    def long_engine(image: Path) -> Any:
        info, lines = engine(image)
        lines[0].text = text
        return info, lines

    result = collect(sample, engine=long_engine)
    assert result.status == "fully_collected"
    assert result.expected_pages == result.page_records == 2
    assert sample.raw.read_bytes() == before
    manifest = load_manifest(sample)
    assert [p["source_page_number"] for p in manifest["pages"]] == [1, 2]
    for record in manifest["pages"]:
        page = ocr.OCRPage.model_validate_json((sample.output / record["path"]).read_bytes())
        assert page.text == text and page.status == "machine_ocr_unreviewed"
        assert page.image_width > 400 and page.image_height > 500
    shutil.rmtree(sample.output / "_renders")
    assert ocr.validate_ocr_collection(sample.root, sample.output, sample.ledger) == result
    with pytest.raises(ValueError, match="immutable"):
        collect(sample)


@pytest.mark.parametrize("change", ["missing", "length", "hash", "truncated", "count", "symlink"])
def test_bad_source_never_creates_output(sample: SimpleNamespace, change: str) -> None:
    source = sample.data["sources"][0]
    if change == "missing":
        sample.raw.unlink()
    elif change == "length":
        sample.raw.write_bytes(sample.raw.read_bytes() + b"x" * 100)
    elif change == "hash":
        body = sample.raw.read_bytes().replace(b"200", b"201")
        sample.raw.write_bytes(body)
    elif change == "truncated":
        body = sample.raw.read_bytes()[:-6]
        source.update(sha256=ocr.sha256(body), size_bytes=len(body))
        source["archive_path"] = f"_RAW_ARCHIVE/local/coverage/{source['sha256']}.pdf"
        (sample.root / source["archive_path"]).write_bytes(body)
        save_ledger(sample)
    elif change == "count":
        source["pdf_pages"] = 3
        save_ledger(sample)
    else:
        target = sample.root / "outside.pdf"
        sample.raw.rename(target)
        sample.raw.symlink_to(target)
    with pytest.raises((ValueError, RuntimeError)):
        collect(sample)
    assert not sample.output.exists()


@pytest.mark.parametrize("path", ["../out", "/tmp/escape", "missing"])
def test_read_path_confinement(sample: SimpleNamespace, path: str) -> None:
    with pytest.raises(ValueError):
        ocr._ordinary(sample.root, path)


@pytest.mark.parametrize("target", ["root", "raw", "raw_child", "symlink"])
def test_output_cannot_replace_sources_or_traverse_symlink(
    sample: SimpleNamespace, target: str,
) -> None:
    if target == "symlink":
        sample.output.symlink_to(sample.root / "elsewhere", target_is_directory=True)
    else:
        sample.output = {"root": sample.root, "raw": sample.root / "_RAW_ARCHIVE",
                         "raw_child": sample.root / "_RAW_ARCHIVE" / "derived"}[target]
    with pytest.raises(ValueError):
        collect(sample)


def test_write_new_refuses_existing_bytes(sample: SimpleNamespace) -> None:
    target = sample.root / "receipt.json"
    ocr._write_new(target, b"original")
    with pytest.raises(ValueError):
        ocr._write_new(target, b"replacement")
    assert target.read_bytes() == b"original"


@pytest.mark.parametrize("exception", [ValueError("bad engine"), OSError("missing image"),
                                      RuntimeError("render failed"),
                                      subprocess.TimeoutExpired("vision", 1)])
def test_failed_page_is_explicit_and_later_page_still_runs(
    sample: SimpleNamespace, exception: Any,
) -> None:
    seen = []

    def sometimes(image: Path) -> Any:
        seen.append(image.name)
        if len(seen) == 1:
            raise exception
        return engine(image)

    result = collect(sample, engine=sometimes)
    assert seen == ["page-0001.png", "page-0002.png"]
    assert result.status == "failed" and result.failed_pages == result.page_records == 1
    manifest = load_manifest(sample)
    assert manifest["failures"][0]["source_page_number"] == 1
    assert manifest["pages"][0]["source_page_number"] == 2
    assert ocr.validate_ocr_collection(sample.root, sample.output, sample.ledger) == result


@pytest.mark.parametrize("lines,flags,status", [
    ([], ["no_text"], "failed"),
    ([dict(text=" ", confidence=0.1, bbox=[0, 0, 1, 1])],
     ["no_text", "low_engine_confidence"], "failed"),
    ([dict(text="abc\ufffd", confidence=0.1, bbox=[0, 0, 1, 1])],
     ["sparse_text", "low_engine_confidence", "replacement_character"], "fully_collected"),
])
def test_blank_is_failed_weak_text_preserved(
    sample: SimpleNamespace, lines: Any, flags: Any, status: Any,
) -> None:
    def weak(image: Path) -> Any:
        return engine(image)[0], lines

    result = collect(sample, engine=weak)
    assert result.status == status and result.flagged_pages == 2
    page = ocr.OCRPage.model_validate_json(
        (sample.output / sample.digest / "page-0001.json").read_bytes())
    assert page.flags == flags
    assert page.text == "\n".join(line["text"] for line in lines)


@pytest.mark.parametrize("field,value", [
    ("source_page_number", 3), ("source_page_count", 3), ("source_id", "other"),
    ("source_sha256", "b" * 64), ("text", "truncated"), ("text_sha256", "b" * 64),
    ("flags", ["invented"]), ("created_at", "2026-09-10T12:00:00"),
    ("status", "verified_legal_text"), ("image_width", 0),
])
def test_page_semantics_checked_after_byte_hash(
    sample: SimpleNamespace, field: Any, value: Any,
) -> None:
    collect(sample)
    rewrite_page(sample, 1, field, value)
    with pytest.raises(ValueError):
        ocr.validate_ocr_collection(sample.root, sample.output, sample.ledger)


@pytest.mark.parametrize("change", ["size", "hash", "missing", "order", "duplicate", "path",
                                    "blank", "flag", "status", "source", "record_text"])
def test_manifest_cannot_hide_page_loss_or_identity_change(
    sample: SimpleNamespace, change: str,
) -> None:
    collect(sample)
    data = load_manifest(sample)
    if change == "size":
        data["pages"][0]["size_bytes"] += 1
    elif change == "hash":
        data["pages"][0]["sha256"] = "0" * 64
    elif change == "missing":
        data["pages"].pop()
    elif change == "order":
        data["pages"].reverse()
    elif change == "duplicate":
        data["pages"][1] = data["pages"][0]
    elif change == "path":
        data["pages"][0]["path"] = f"{sample.digest}/page-0002.json"
    elif change == "blank":
        data["blank_pages"] = [1]
    elif change == "flag":
        data["flagged_pages"] = [1]
    elif change == "status":
        data["status"] = "failed"
    elif change == "source":
        data["source_id"] = "other"
    else:
        data["pages"][0]["text_sha256"] = "0" * 64
    rewrite_manifest(sample, data)
    with pytest.raises(ValueError):
        ocr.validate_ocr_collection(sample.root, sample.output, sample.ledger)


def test_profile_cannot_change_inside_source(sample: SimpleNamespace) -> None:
    collect(sample)
    info = engine(next((sample.output / "_renders").rglob("*.png")))[0].model_dump()
    info["version"] = "different engine build"
    rewrite_page(sample, 2, "engine", info)
    with pytest.raises(ValueError, match="profile"):
        ocr.validate_ocr_collection(sample.root, sample.output, sample.ledger)


@pytest.mark.parametrize("box", [(-0.1, 0, 1, 1), (0, 0, 2, 1), (0.5, 0, 0.6, 1),
                                  (0, 0.5, 1, 0.6), (float("nan"), 0, 1, 1)])
def test_engine_boxes_are_not_clipped(box: Any) -> None:
    with pytest.raises(ValidationError):
        ocr.OCRLine(text="evidence", confidence=0.9, bbox=box)


def test_engine_settings_fixed() -> None:
    with pytest.raises(ValidationError):
        ocr.EngineInfo(version="v", adapter_sha256="a" * 64, settings={})


def test_explicit_mixed_pdf_selection_retains_every_page(sample: SimpleNamespace) -> None:
    sample.data["sources"][0]["extraction_status"] = "text_layer_present"
    save_ledger(sample)
    with pytest.raises(ValueError, match="selected PDFs"):
        collect(sample)
    result = collect(sample, source_ids=["scan"])
    assert result.expected_pages == 2 and result.status == "fully_collected"
    receipt = ocr.CollectionSelection.model_validate_json(
        (sample.output / "selection.json").read_bytes())
    assert receipt.mode == "explicit_sources" and receipt.source_ids == ["scan"]


@pytest.mark.parametrize("identities", [[], ["unknown"], ["scan", "scan"]])
def test_bad_explicit_selection(sample: SimpleNamespace, identities: Any) -> None:
    with pytest.raises(ValueError):
        collect(sample, source_ids=identities)
    assert not sample.output.exists()


@pytest.mark.parametrize("identities", [["scan", "scan"], [""], [" "]])
def test_selection_receipt_rejects_ambiguous_identity(identities: Any) -> None:
    with pytest.raises(ValueError):
        ocr.CollectionSelection(mode="explicit_sources", source_ids=identities,
                                 ledger_sha256="a" * 64)


def test_nonpdf_cannot_be_selected(sample: SimpleNamespace) -> None:
    source = sample.data["sources"][0]
    body = b"<html>fixture</html>"
    digest = ocr.sha256(body)
    source.update(sha256=digest, size_bytes=len(body), media_type="html", pdf_pages=None,
                  extraction_status="not_assessed",
                  archive_path=f"_RAW_ARCHIVE/local/coverage/{digest}.html")
    save_ledger(sample)
    with pytest.raises(ValueError):
        collect(sample, source_ids=["scan"])


def test_vision_adapter_contract_and_binary_integrity(
    sample: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = sample.root / "adapter"
    binary.write_bytes(b"executable fixture")
    instance = ocr.VisionEngine(binary, timeout=2)
    output = dict(revision=3, os_version="Actual OS build", lines=[dict(
        text="raw observed line", confidence=0.5, bbox=[0, 0, 1, 1])])
    seen = []

    def run(args: Any, **kwargs: Any) -> Any:
        seen.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(output).encode(), stderr=b"")

    monkeypatch.setattr(ocr.subprocess, "run", run)
    info, lines = instance(sample.root / "image.png")
    assert info.version == "Actual OS build" and lines[0].confidence == 0.5
    assert seen[0][1] == dict(capture_output=True, check=False, timeout=2)
    binary.write_bytes(b"modified binary")
    with pytest.raises(ValueError, match="binary changed"):
        instance(sample.root / "image.png")


@pytest.mark.parametrize("case", ["missing", "symlink", "timeout_zero", "exit", "json", "timeout"])
def test_vision_engine_failure_modes(
    sample: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, case: Any,
) -> None:
    binary = sample.root / "adapter"
    if case != "missing":
        binary.write_bytes(b"executable")
    if case == "symlink":
        link = sample.root / "link"
        link.symlink_to(binary)
        binary = link
    if case in {"missing", "symlink", "timeout_zero"}:
        with pytest.raises(ValueError):
            ocr.VisionEngine(binary, timeout=0 if case == "timeout_zero" else 1)
        return
    instance = ocr.VisionEngine(binary)

    def run(*args: Any, **kwargs: Any) -> Any:
        if case == "timeout":
            raise subprocess.TimeoutExpired("adapter", 1)
        return SimpleNamespace(returncode=1 if case == "exit" else 0,
                               stdout=b"invalid", stderr=b"engine failed")

    monkeypatch.setattr(ocr.subprocess, "run", run)
    with pytest.raises((ValueError, subprocess.TimeoutExpired)):
        instance(sample.root / "image.png")


def test_cli_collection_validation_and_failures(
    sample: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = ["--root", str(sample.root), "--output", str(sample.output),
            "--ledger", str(sample.ledger)]
    assert ocr.main(args) == 1
    monkeypatch.setattr(ocr, "VisionEngine", lambda *a: engine)
    assert ocr.main(args + ["--engine-executable", "fixture", "--dpi", "150",
                            "--source-id", "scan"]) == 0
    assert ocr.main(args + ["--validate-only"]) == 0
    (sample.output / sample.digest / "page-0001.json").unlink()
    assert ocr.main(args + ["--validate-only"]) == 1


def test_cli_returns_failure_for_blank_collection(
    sample: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ocr, "VisionEngine", lambda *a: lambda p: (engine(p)[0], []))
    assert ocr.main(["--root", str(sample.root), "--output", str(sample.output),
                     "--ledger", str(sample.ledger), "--engine-executable", "fixture"]) == 1


def test_module_entrypoint_errors_cleanly(
    sample: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["ocr", "--ledger", str(sample.ledger),
                                      "--output", str(sample.output)])
    with pytest.raises(SystemExit) as result:
        runpy.run_module(ocr.__name__, run_name="__main__")
    assert result.value.code == 1


def test_duplicate_source_hashes_fail_before_derivation(sample: SimpleNamespace) -> None:
    duplicate = dict(sample.data['sources'][0], source_id='another-scan')
    sample.data['sources'].append(duplicate)
    row = next(row for row in sample.data['authorities'][0]['checklist']
               if row['category'] == 'fees')
    row['source_ids'].append('another-scan')
    save_ledger(sample)
    with pytest.raises(ValueError, match='share PDF bytes'):
        collect(sample)
    assert not sample.output.exists()


def test_output_must_remain_in_declared_project(sample: SimpleNamespace) -> None:
    sample.output = sample.root.parent / 'escape-derived'
    with pytest.raises(ValueError, match='separate'):
        collect(sample)
    assert not sample.output.exists()


@pytest.mark.parametrize('target', ['root', 'ancestor', 'output_root', 'output_ancestor'])
def test_symlink_roots_and_ancestors_cannot_be_hidden_by_resolve(
    sample: SimpleNamespace, target: str,
) -> None:
    collect(sample)
    link = sample.root.parent / (sample.root.name + '-linked')
    link.symlink_to(sample.root, target_is_directory=True)
    if target == 'root':
        root, output = link, sample.output
    elif target == 'ancestor':
        nested = sample.root / 'nested'
        nested.mkdir()
        with pytest.raises(ValueError, match='ancestors'):
            ocr._ordinary(link / 'nested', 'missing')
        return
    elif target == 'output_root':
        other = sample.root / 'linked-output'
        other.symlink_to(sample.output, target_is_directory=True)
        root, output = sample.root, other
    else:
        root, output = sample.root, link / 'derived'
    with pytest.raises(ValueError, match='ancestors'):
        ocr.validate_ocr_collection(root, output, sample.ledger)


@pytest.mark.parametrize('change', ['missing_report', 'wrong_report', 'orphan_page'])
def test_saved_summary_and_extra_records_cannot_inflate_coverage(
    sample: SimpleNamespace, change: str,
) -> None:
    collect(sample)
    report = sample.output / 'report.json'
    if change == 'missing_report':
        report.unlink()
    elif change == 'wrong_report':
        value = json.loads(report.read_text())
        value['expected_pages'] = 3000
        report.write_text(json.dumps(value))
    else:
        (sample.output / sample.digest / 'page-9999.json').write_text('{}')
    with pytest.raises(ValueError):
        ocr.validate_ocr_collection(sample.root, sample.output, sample.ledger)
