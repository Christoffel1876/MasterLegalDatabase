"""Offline visual excerpts must bind actual source bytes and strict machine-OCR pages."""

from __future__ import annotations

import hashlib
import json
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import pytest
from pydantic import ValidationError

from geode.pipeline import local_text_review as review
from geode.pipeline import verified_local_ocr as ocr
from geode.pipeline.local_coverage import CATEGORIES, CoverageLedger
from geode.pipeline.verified_local_ocr import (
    EngineInfo,
    OCRLine,
    OCRPage,
    RenderingInfo,
    page_flags,
)

NOW = datetime(2026, 9, 10, 19, 0, tzinfo=timezone.utc)
Package = tuple[Path, dict, dict, dict]
OWNER = "CO-MUNICIPAL-GOLDEN"
TEXT = "The fee shall become effective immediately upon adoption."


def digest(body: bytes) -> str:
    """Return the exact fixture-byte digest."""
    return hashlib.sha256(body).hexdigest()


def save_page(root: Path, page_data: dict) -> tuple[str, str]:
    """Validate the real OCR schema before writing a fixture page."""
    page = OCRPage.model_validate(page_data)
    relative = (f"_DERIVED/local_ocr/fixture-batch/{page.source_sha256}/"
                f"page-{page.source_page_number:04d}.json")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    body = page.model_dump_json(indent=2).encode()
    path.write_bytes(body)
    return relative, digest(body)


def save_ledger(root: Path, data: dict) -> None:
    """Store a complete validated ledger, including all authority checklist rows."""
    ledger = CoverageLedger.model_validate(data)
    path = root / "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ledger.model_dump_json(indent=2))


def save_collection(root: Path, ledger: dict, page: dict, *, blank_second: bool = False) -> None:
    """Account for both fixture pages with immutable-format selection/manifest/summary receipts."""
    output = root / "_DERIVED/local_ocr/fixture-batch"
    source = ledger["sources"][0]
    second_lines = [] if blank_second else [OCRLine(
        text="Separate second page with its complete fixture text",
        confidence=0.91, bbox=(0.1, 0.7, 0.8, 0.1),
    )]
    second_text = "\n".join(line.text for line in second_lines)
    second = dict(page, source_page_number=2, lines=second_lines, text=second_text,
                  text_sha256=digest(second_text.encode()), flags=page_flags(second_lines))
    records = []
    for data in (page, second):
        relative, hashed = save_page(root, data)
        body = (root / relative).read_bytes()
        records.append(ocr.PageFile(
            source_page_number=data["source_page_number"],
            path=Path(relative).relative_to(output.relative_to(root)).as_posix(),
            sha256=hashed, size_bytes=len(body), text_sha256=data["text_sha256"],
        ))
    manifest = ocr.OCRManifest(
        source_id=source["source_id"], source_path=source["archive_path"],
        source_sha256=source["sha256"], source_size_bytes=source["size_bytes"],
        source_page_count=2, status="failed" if blank_second else "fully_collected",
        pages=records, failures=[], blank_pages=[2] if blank_second else [],
        flagged_pages=[2] if blank_second else [],
    )
    selection = ocr.CollectionSelection(
        mode="explicit_sources", source_ids=[source["source_id"]],
        ledger_sha256=digest((root / "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json").read_bytes()),
    )
    summary = ocr.CollectionSummary(
        source_count=1, expected_pages=2, page_records=2, failed_pages=0,
        blank_pages=int(blank_second), flagged_pages=int(blank_second),
        fully_collected_sources=int(not blank_second), failed_sources=int(blank_second),
        status=manifest.status,
    )
    for relative, model in [("selection.json", selection), ("report.json", summary),
                            (f"{source['sha256']}/manifest.json", manifest)]:
        (output / relative).write_text(model.model_dump_json())


@pytest.fixture
def package(tmp_path: Path) -> tuple[Path, dict, dict, dict]:
    """Preserve a real two-page PDF and a genuine minimal OCRPage schema fixture."""
    root = tmp_path.resolve()
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), TEXT)
        document.new_page().insert_text((72, 72), "Separate second page")
        original = document.tobytes()
    source_hash = digest(original)
    relative = f"_RAW_ARCHIVE/local/coverage/{source_hash}.pdf"
    original_path = root / relative
    original_path.parent.mkdir(parents=True)
    original_path.write_bytes(original)
    source = dict(
        source_id="golden-fee", authority_id=OWNER, title="Fixture fee resolution",
        url="https://www.cityofgolden.gov/fee.pdf",
        final_url="https://www.cityofgolden.gov/fee.pdf", retrieved_at=NOW,
        archive_path=relative, sha256=source_hash, size_bytes=len(original),
        media_type="pdf", kind="legal_text", pdf_pages=2,
        extraction_status="text_layer_present", categories=["fees"],
        provenance_notes="Exact fixture source", currentness_notes="Not reconciled",
    )
    rows = [dict(
        category=category, source_ids=["golden-fee"] if category == "fees" else [],
        collection="legal_documents_preserved" if category == "fees" else "missing",
        completeness="partial" if category == "fees" else "not_assessed",
        gap="Later changes remain uncollected", next_action="Reconcile adopting sources",
    ) for category in CATEGORIES]
    ledger = dict(
        prepared_at=NOW, baseline_commit="a" * 40, scope="One fixture source only",
        directory_assessments=[], sources=[source], authorities=[dict(
            authority_id=OWNER, name="Golden", level="municipal", pilot=True,
            identity_basis="Fixture authority", identity_source_ids=[], checklist=rows,
        )], limitations=["No legal-currentness certification"],
    )
    save_ledger(root, ledger)
    lines = [OCRLine(text=TEXT, confidence=0.91, bbox=(0.1, 0.7, 0.8, 0.1))]
    page = OCRPage(
        source_id=source["source_id"], source_sha256=source_hash,
        source_page_number=1, source_page_count=2, text=TEXT,
        text_sha256=digest(TEXT.encode()), lines=lines,
        engine=EngineInfo(version="fixture macOS", adapter_sha256="b" * 64),
        rendering=RenderingInfo(version="fixture renderer", dpi=200),
        image_sha256="c" * 64, image_width=1700, image_height=2200,
        flags=page_flags(lines), created_at=NOW,
    ).model_dump()
    save_collection(root, ledger, page)
    page_path, page_hash = save_page(root, page)
    excerpt = dict(
        excerpt_id="fee-effective", source_id=source["source_id"],
        source_sha256=source_hash, physical_page=1, ocr_page_path=page_path,
        ocr_page_sha256=page_hash, topic="effective_date", raw_ocr_excerpt=TEXT,
        visually_checked_transcription=TEXT, correction_notes=[],
        source_context="Operative effective-date sentence; other text unreviewed",
    )
    data = dict(
        review_id="fixture-excerpts", prepared_at=NOW, excerpts=[excerpt],
        limits=["Only the specified sentence was visually checked"],
    )
    return root, data, ledger, page


def validate(data: dict, root: Path) -> review.ExcerptReview:
    """Exercise the actual review model and source validator together."""
    model = review.ExcerptReview.model_validate(data)
    review.validate_excerpt_review(model, root)
    return model


def test_real_pdf_ledger_and_ocr_page_pass_without_broadening_review(package: Package) -> None:
    root, data, _, _ = package
    model = validate(data, root)
    assert model.unreviewed_text_status == "machine_ocr_unreviewed"
    assert model.excerpts[0].review_scope == "specified_excerpt_only"
    assert model.excerpts[0].legal_currentness == "not_verified"


def test_normalized_equivalence_preserves_nfkc_and_whitespace(package: Package) -> None:
    root, data, _, _ = package
    data["excerpts"][0]["raw_ocr_excerpt"] = "The  fee\nshall become effective immediately"
    data["excerpts"][0]["visually_checked_transcription"] = (
        "Ｔｈｅ fee shall become effective immediately"
    )
    validate(data, root)


def test_corrected_visual_transcription_requires_explicit_notes(package: Package) -> None:
    root, data, _, _ = package
    excerpt = data["excerpts"][0]
    excerpt["visually_checked_transcription"] = "The fee takes effect on adoption."
    with pytest.raises(ValidationError, match="correction notes"):
        review.ExcerptReview.model_validate(data)
    excerpt["correction_notes"] = ["Fixture correction compared with the source image"]
    validate(data, root)


@pytest.mark.parametrize("field,value", [
    ("review_scope", "entire_document"), ("legal_currentness", "verified_current"),
    ("legal_review", "approved"), ("review_method", "automatic_full_review"),
    ("raw_ocr_excerpt", " "), ("visually_checked_transcription", "\n"),
    ("source_context", ""), ("correction_notes", [" "]),
    ("physical_page", True), ("physical_page", 0), ("physical_page", "1"),
    ("topic", "whole_document"), ("unexpected", "claim"),
])
def test_excerpt_contract_rejects_false_claims_and_empty_text(
    package: Package, field: str, value: object,
) -> None:
    _, data, _, _ = package
    data["excerpts"][0][field] = value
    with pytest.raises(ValidationError):
        review.ExcerptReview.model_validate(data)


@pytest.mark.parametrize("field,value", [
    ("prepared_at", datetime(2026, 9, 10)), ("limits", []),
    ("unreviewed_text_status", "reviewed"), ("schema_version", 2),
    ("ledger_path", "alternate-ledger.json"), ("excerpts", []),
])
def test_review_contract_rejects_ambiguous_time_scope_and_empty_packages(
    package: Package, field: str, value: object,
) -> None:
    _, data, _, _ = package
    data[field] = value
    with pytest.raises(ValidationError):
        review.ExcerptReview.model_validate(data)


def test_duplicate_ids_and_oversized_review_count_rejected(package: Package) -> None:
    _, data, _, _ = package
    data["excerpts"] *= 2
    with pytest.raises(ValidationError, match="unique"):
        review.ExcerptReview.model_validate(data)
    data["excerpts"] *= 101
    with pytest.raises(ValidationError):
        review.ExcerptReview.model_validate(data)


@pytest.mark.parametrize("mutation", ["hash_directory", "page_filename", "traversal", "absolute"])
def test_review_path_is_bound_to_source_and_page(package: Package, mutation: str) -> None:
    _, data, _, _ = package
    excerpt = data["excerpts"][0]
    if mutation == "hash_directory":
        excerpt["source_sha256"] = "f" * 64
    elif mutation == "page_filename":
        excerpt["physical_page"] = 2
    elif mutation == "traversal":
        excerpt["ocr_page_path"] = "../" + excerpt["ocr_page_path"]
    else:
        excerpt["ocr_page_path"] = "/" + excerpt["ocr_page_path"]
    with pytest.raises(ValidationError):
        review.ExcerptReview.model_validate(data)


@pytest.mark.parametrize("mutation", ["unknown_source", "wrong_hash", "out_of_bounds"])
def test_excerpt_must_bind_existing_preserved_source(package: Package, mutation: str) -> None:
    root, data, _, _ = package
    excerpt = data["excerpts"][0]
    if mutation == "unknown_source":
        excerpt["source_id"] = "missing"
    elif mutation == "wrong_hash":
        excerpt["source_sha256"] = "f" * 64
        excerpt["ocr_page_path"] = f"_DERIVED/local_ocr/fixture-batch/{'f' * 64}/page-0001.json"
    else:
        excerpt["physical_page"] = 3
        excerpt["ocr_page_path"] = excerpt["ocr_page_path"].replace("0001", "0003")
    with pytest.raises(ValueError, match="preserved PDF"):
        validate(data, root)


@pytest.mark.parametrize("mutation", ["source_id", "source_hash", "page_number", "page_count"])
def test_real_ocr_page_must_bind_same_source_and_page(package: Package, mutation: str) -> None:
    root, data, _, page = package
    if mutation == "source_id":
        page["source_id"] = "foreign-source"
    elif mutation == "source_hash":
        page["source_sha256"] = "f" * 64
    elif mutation == "page_number":
        page["source_page_number"] = 2
    else:
        page["source_page_count"] = 3
    # Keep the review's named file, so a valid foreign page cannot be substituted there.
    body = OCRPage.model_validate(page).model_dump_json().encode()
    excerpt = data["excerpts"][0]
    (root / excerpt["ocr_page_path"]).write_bytes(body)
    excerpt["ocr_page_sha256"] = digest(body)
    with pytest.raises(ValueError, match="different source or physical page"):
        validate(data, root)


def test_page_hash_fails_before_schema_is_trusted(package: Package) -> None:
    root, data, _, _ = package
    path = root / data["excerpts"][0]["ocr_page_path"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate(data, root)


def test_raw_excerpt_must_exist_even_when_visual_corrections_are_recorded(package: Package) -> None:
    root, data, _, _ = package
    excerpt = data["excerpts"][0]
    excerpt["raw_ocr_excerpt"] = "invented raw OCR sentence"
    excerpt["correction_notes"] = ["A correction note does not supply missing OCR evidence"]
    with pytest.raises(ValueError, match="absent"):
        validate(data, root)


def test_invalid_real_ocr_schema_cannot_be_hidden_behind_matching_file_hash(
    package: Package,
) -> None:
    root, data, _, page = package
    page["text_sha256"] = "f" * 64
    body = json.dumps(page, default=str).encode()
    excerpt = data["excerpts"][0]
    (root / excerpt["ocr_page_path"]).write_bytes(body)
    excerpt["ocr_page_sha256"] = digest(body)
    with pytest.raises(ValidationError, match="text hash mismatch"):
        validate(data, root)


def test_wrong_authority_ownership_is_rejected_by_preserved_ledger(package: Package) -> None:
    root, data, ledger, _ = package
    ledger["sources"][0]["authority_id"] = "CO-MUNICIPAL-GEORGETOWN"
    path = root / "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json"
    path.write_text(json.dumps(ledger, default=str))
    with pytest.raises(ValidationError):
        validate(data, root)


def test_source_original_corruption_is_not_just_a_metadata_check(package: Package) -> None:
    root, data, ledger, _ = package
    (root / ledger["sources"][0]["archive_path"]).write_bytes(b"not the original")
    with pytest.raises(ValueError):
        validate(data, root)


@pytest.mark.parametrize("target", ["page", "page_ancestor", "ledger", "source"])
def test_symlinked_evidence_is_rejected(package: Package, target: str) -> None:
    root, data, ledger, _ = package
    paths = {
        "page": root / data["excerpts"][0]["ocr_page_path"],
        "page_ancestor": (root / data["excerpts"][0]["ocr_page_path"]).parent,
        "ledger": root / "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json",
        "source": root / ledger["sources"][0]["archive_path"],
    }
    selected = paths[target]
    real = selected.with_name(selected.name + "-real")
    selected.rename(real)
    selected.symlink_to(real, target_is_directory=real.is_dir())
    with pytest.raises(ValueError, match="symlink"):
        validate(data, root)


def test_post_validation_object_mutation_is_revalidated(package: Package) -> None:
    root, data, _, _ = package
    model = review.ExcerptReview.model_validate(data)
    object.__setattr__(model.excerpts[0], "review_scope", "entire_document")
    with pytest.raises(ValidationError):
        review.validate_excerpt_review(model, root)


@pytest.mark.parametrize("kind", ["missing", "directory", "empty", "oversize", "escape"])
def test_bounded_reads_reject_nonfiles_empty_oversize_and_escape(tmp_path: Path, kind: str) -> None:
    root = (tmp_path / "root").resolve()
    root.mkdir()
    path = root / "evidence"
    if kind == "directory":
        path.mkdir()
    elif kind == "empty":
        path.write_bytes(b"")
    elif kind == "oversize":
        path.write_bytes(b"123456")
    elif kind == "escape":
        path = tmp_path / "outside"
        path.write_bytes(b"123")
    relative = "../outside" if kind == "escape" else "evidence"
    with pytest.raises(ValueError):
        review._confined_bytes(root, relative, 5)


def test_bounded_read_accepts_exact_limit(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "page").write_bytes(b"12345")
    assert review._confined_bytes(root, "page", 5) == b"12345"


def test_page_size_limit_is_used_during_validation(
    package: Package, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, data, _, _ = package
    monkeypatch.setattr(review, "MAX_PAGE_BYTES", 10)
    with pytest.raises(ValueError, match="read limit"):
        validate(data, root)


def write_review(root: Path, data: dict) -> Path:
    """Create a valid review input for actual CLI validation."""
    path = root / "review.json"
    path.write_text(review.ExcerptReview.model_validate(data).model_dump_json())
    return path


def test_cli_valid_relative_and_absolute_inputs(
    package: Package, caplog: pytest.LogCaptureFixture,
) -> None:
    root, data, _, _ = package
    path = write_review(root, data)
    assert review.main(["--root", str(root), "--review", "review.json"]) == 0
    assert review.main(["--root", str(root), "--review", str(path)]) == 0


@pytest.mark.parametrize("kind", ["missing", "malformed", "outside", "symlink", "ancestor"])
def test_cli_rejects_invalid_or_symlinked_review_inputs(
    package: Package, kind: str, caplog: pytest.LogCaptureFixture,
) -> None:
    root, data, _, _ = package
    path = write_review(root, data)
    if kind == "missing":
        path.unlink()
    elif kind == "malformed":
        path.write_text("{invalid")
    elif kind == "outside":
        path = root.parent / "outside-review.json"
        path.write_text(review.ExcerptReview.model_validate(data).model_dump_json())
    elif kind == "symlink":
        actual = root / "actual-review.json"
        path.rename(actual)
        path.symlink_to(actual)
    else:
        linked_root = root.parent / "linked-root"
        linked_root.symlink_to(root, target_is_directory=True)
        root = linked_root
        path = root / "review.json"
    assert review.main(["--root", str(root), "--review", str(path)]) == 1
    assert "validation failed" in caplog.text


def test_cli_review_read_limit_is_applied_before_parsing(
    package: Package, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, data, _, _ = package
    path = write_review(root, data)
    monkeypatch.setattr(review, "MAX_REVIEW_BYTES", 10)
    assert review.main(["--root", str(root), "--review", str(path)]) == 1


def test_module_entrypoint_exits_successfully_for_valid_offline_package(
    package: Package, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, data, _, _ = package
    path = write_review(root, data)
    monkeypatch.setattr(
        sys, "argv", ["local_text_review", "--root", str(root), "--review", str(path)],
    )
    with pytest.raises(SystemExit) as outcome:
        runpy.run_module("geode.pipeline.local_text_review", run_name="__main__", alter_sys=True)
    assert outcome.value.code == 0


@pytest.mark.parametrize("slug", ["../escape", "Uppercase", "nested/path", ".", "bad space"])
def test_collection_slug_rejects_escape_and_unreviewed_path_shapes(
    package: Package, slug: str,
) -> None:
    _, data, _, _ = package
    data["excerpts"][0]["ocr_page_path"] = data["excerpts"][0]["ocr_page_path"].replace(
        "fixture-batch", slug,
    )
    with pytest.raises(ValidationError):
        review.ExcerptReview.model_validate(data)


@pytest.mark.parametrize("page_number", [10000, 100000])
def test_schema_allows_five_and_six_digit_physical_pages(
    package: Package, page_number: int,
) -> None:
    _, data, _, _ = package
    excerpt = data["excerpts"][0]
    excerpt["physical_page"] = page_number
    excerpt["ocr_page_path"] = excerpt["ocr_page_path"].replace("0001", str(page_number))
    model = review.ExcerptReview.model_validate(data)
    assert model.excerpts[0].physical_page == page_number


@pytest.mark.parametrize("media", ["html", "pdf_without_page_count"])
def test_non_pdf_or_unmeasured_source_cannot_support_physical_page_review(
    package: Package, media: str,
) -> None:
    root, data, ledger, _ = package
    source = ledger["sources"][0]
    if media == "html":
        body = b"<html><body>Fee catalog, not a PDF</body></html>"
        source.update(
            sha256=digest(body), size_bytes=len(body), media_type="html",
            extraction_status="not_assessed", pdf_pages=None,
            archive_path=f"_RAW_ARCHIVE/local/coverage/{digest(body)}.html",
        )
        (root / source["archive_path"]).write_bytes(body)
        excerpt = data["excerpts"][0]
        excerpt["source_sha256"] = source["sha256"]
        excerpt["ocr_page_path"] = (
            f"_DERIVED/local_ocr/fixture-batch/{source['sha256']}/page-0001.json"
        )
    else:
        source["pdf_pages"] = None
    save_ledger(root, ledger)
    with pytest.raises(ValueError, match="preserved PDF"):
        validate(data, root)


def test_validated_collection_is_reused_for_multiple_excerpts(
    package: Package, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, data, _, _ = package
    calls = []
    actual = ocr.validate_ocr_collection

    def counting(project: Path, output: Path, ledger_path: Path) -> ocr.CollectionSummary:
        calls.append(output)
        return actual(project, output, ledger_path)

    monkeypatch.setattr(ocr, "validate_ocr_collection", counting)
    data["excerpts"].append(dict(data["excerpts"][0], excerpt_id="same-page-other-excerpt"))
    validate(data, root)
    assert calls == [root / "_DERIVED/local_ocr/fixture-batch"]


@pytest.mark.parametrize("missing", ["selection.json", "report.json", "manifest.json"])
def test_standalone_page_cannot_bypass_required_collection_receipts(
    package: Package, missing: str,
) -> None:
    root, data, ledger, _ = package
    collection = root / "_DERIVED/local_ocr/fixture-batch"
    target = collection / (ledger["sources"][0]["sha256"] if missing == "manifest.json" else "")
    (target / missing).unlink()
    with pytest.raises(ValueError):
        validate(data, root)


def test_unrelated_corrupt_page_invalidates_collection_but_does_not_silently_drop_it(
    package: Package,
) -> None:
    root, data, ledger, _ = package
    path = (root / "_DERIVED/local_ocr/fixture-batch" / ledger["sources"][0]["sha256"]
            / "page-0002.json")
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash or length"):
        validate(data, root)


def test_orphan_collection_slug_cannot_bypass_manifest_membership(package: Package) -> None:
    root, data, _, _ = package
    excerpt = data["excerpts"][0]
    original = root / excerpt["ocr_page_path"]
    excerpt["ocr_page_path"] = excerpt["ocr_page_path"].replace("fixture-batch", "orphan-batch")
    orphan = root / excerpt["ocr_page_path"]
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(original.read_bytes())
    with pytest.raises(ValueError, match="selection"):
        validate(data, root)


def test_known_blank_elsewhere_preserves_failed_status_but_allows_nonblank_excerpt(
    package: Package,
) -> None:
    root, data, ledger, page = package
    save_collection(root, ledger, page, blank_second=True)
    output = root / "_DERIVED/local_ocr/fixture-batch"
    summary = ocr.validate_ocr_collection(
        root, output, root / "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json",
    )
    assert summary.status == "failed" and summary.blank_pages == 1
    checked = validate(data, root)
    assert checked.unreviewed_text_status == "machine_ocr_unreviewed"
    assert checked.excerpts[0].review_scope == "specified_excerpt_only"
