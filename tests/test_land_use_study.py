"""Research evidence must retain exact source identity, pages, and uncertainty."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import pytest
from pydantic import ValidationError

from geode.pipeline import land_use_study as research

NOW = datetime(2026, 9, 10, 17, tzinfo=timezone.utc)
QUOTE = "Applicants must submit a final plan."


def make_pdf(*, encrypted: bool = False) -> bytes:
    """Generate real two-page evidence with distinct source statements."""
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), QUOTE)
        document.new_page().insert_text((72, 72), "The review fee is $100.")
        return document.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256 if encrypted else pymupdf.PDF_ENCRYPT_NONE,
            owner_pw="owner" if encrypted else None, user_pw="reader" if encrypted else None,
        )


def write_source(root: Path, body: bytes, **updates: object) -> research.StudySource:
    """Create a hash-named fixture and matching source metadata."""
    digest = hashlib.sha256(body).hexdigest()
    suffix = updates.pop("suffix", "pdf")
    name = f"_RAW_ARCHIVE/local/research/{digest}.{suffix}"
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return research.StudySource(
        source_id="jefferson-zoning", county="Jefferson", title="County zoning source",
        url="https://www.jeffco.us/DocumentCenter/View/1828", archive_path=name,
        sha256=digest, retrieved_at=NOW, document_kind="zoning_text",
        currentness_notes="Edition remains under substantive review.", **updates,
    )


def study(source: research.StudySource) -> research.LandUseStudy:
    """Assemble a bounded, explicitly provisional observation."""
    return research.LandUseStudy(
        study_id="land-use-pilot", scenario="One scoped application process.",
        scope_boundary="Selected passages only, not a complete permit checklist.",
        prepared_at=NOW, baseline_commit="a" * 40, sources=[source],
        observations=[research.Observation(
            id="JEFF-001", county="Jefferson", stage="submission", actor="Applicants",
            statement="Applicants submit a final plan.", modality="mandatory",
            citations=[research.Citation(source_id=source.source_id, pdf_page=1,
                                         printed_page="6-1", section="6.A", excerpt=QUOTE)],
        )], open_questions=["Check later amendments and applicability."],
    )


@pytest.fixture
def valid(tmp_path: Path) -> research.LandUseStudy:
    """Create a valid study whose source exists only in the temporary fixture corpus."""
    return study(write_source(tmp_path, make_pdf()))


def test_valid_study_preserves_research_flags_and_does_not_write(
    tmp_path: Path, valid: research.LandUseStudy,
) -> None:
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert research.validate_study_evidence(valid, tmp_path) is None
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    rebuilt = research.LandUseStudy.model_validate_json(valid.model_dump_json())
    assert rebuilt == valid
    assert rebuilt.observations[0].research_only is True
    assert rebuilt.observations[0].legal_currentness == "not_fully_reconciled"
    assert rebuilt.sources[0].currentness_status == "unknown"


def test_exact_excerpt_only_normalizes_unicode_compatibility_and_whitespace(
    tmp_path: Path, valid: research.LandUseStudy,
) -> None:
    citation = valid.observations[0].citations[0]
    citation.excerpt = "Ａｐｐｌｉｃａｎｔｓ\u00a0must\n\t submit  a final plan."
    valid.observations[0].citations.append(citation.model_copy())
    research.validate_study_evidence(valid, tmp_path)


@pytest.mark.parametrize("updates,error", [
    ({"excerpt": "Applicants may submit a final plan."}, "Exact excerpt absent"),
    ({"excerpt": "applicants must submit a final plan."}, "Exact excerpt absent"),
    ({"pdf_page": 2}, "Exact excerpt absent"),
    ({"pdf_page": 3}, "page does not exist"),
])
def test_wrong_quote_or_page_is_rejected(
    tmp_path: Path, valid: research.LandUseStudy, updates: dict, error: str,
) -> None:
    valid.observations[0].citations[0] = valid.observations[0].citations[0].model_copy(
        update=updates
    )
    with pytest.raises(ValueError, match=error):
        research.validate_study_evidence(valid, tmp_path)


@pytest.mark.parametrize("mutation", ["duplicate_source", "duplicate_observation", "missing_source",
                                      "wrong_county", "conditional_without_conditions"])
def test_cross_record_identity_and_condition_failures(
    valid: research.LandUseStudy, mutation: str,
) -> None:
    data = valid.model_dump()
    if mutation == "duplicate_source":
        data["sources"] *= 2
    elif mutation == "duplicate_observation":
        data["observations"] *= 2
    elif mutation == "missing_source":
        data["observations"][0]["citations"][0]["source_id"] = "absent"
    elif mutation == "wrong_county":
        data["observations"][0]["county"] = "Clear Creek"
    else:
        data["observations"][0]["modality"] = "conditional"
    with pytest.raises(ValidationError):
        research.LandUseStudy.model_validate(data)


def test_conditional_and_second_county_sources_remain_distinct(
    tmp_path: Path, valid: research.LandUseStudy,
) -> None:
    source = valid.sources[0].model_copy(update={
        "source_id": "clear-creek-zoning", "county": "Clear Creek",
        "url": "https://www.clearcreekcounty.us/DocumentCenter/View/927",
    })
    observation = valid.observations[0].model_copy(deep=True, update={
        "id": "CLEAR-001", "county": "Clear Creek", "modality": "conditional",
        "conditions": ["When this application process applies."],
    })
    observation.citations[0].source_id = source.source_id
    valid.sources.append(source)
    valid.observations.append(observation)
    research.validate_study_evidence(valid, tmp_path)


@pytest.mark.parametrize("updates", [
    {"research_only": False}, {"legal_currentness": "current"}, {"complete": True},
    {"conditions": ["  "]}, {"statement": " "}, {"citations": []},
])
def test_observation_rejects_certainty_unknown_fields_and_empty_evidence(
    valid: research.LandUseStudy, updates: dict,
) -> None:
    with pytest.raises(ValidationError):
        research.Observation.model_validate({**valid.observations[0].model_dump(), **updates})


@pytest.mark.parametrize("updates", [
    {"sha256": "0" * 64}, {"retrieved_at": "2026-09-10"},
    {"currentness_status": "legally_current"}, {"currentness_notes": " "},
    {"currentness_status": "edition_and_catalog_consistent"},
    {"archive_path": "/tmp/source.pdf"}, {"archive_path": "_RAW_ARCHIVE/../source.pdf"},
    {"url": "https://external.example/file.pdf"}, {"url": "http://www.jeffco.us/a.pdf"},
    {"url": "https://user@www.jeffco.us/a.pdf"}, {"url": "https://www.jeffco.us:444/a.pdf"},
    {"url": "https://www.clearcreekcounty.us/a.pdf"},
    {"url": "https://www.jef\nfco.us/a.pdf"},
])
def test_source_rejects_false_provenance_and_currentness(
    valid: research.LandUseStudy, updates: dict,
) -> None:
    with pytest.raises(ValidationError):
        research.StudySource.model_validate({**valid.sources[0].model_dump(), **updates})


def test_identified_edition_requires_but_does_not_certify_version_statement(
    tmp_path: Path, valid: research.LandUseStudy,
) -> None:
    valid.sources[0].currentness_status = "edition_identified_unreconciled"
    valid.sources[0].version_statement = "Source cover says edition published March 10, 2026."
    research.validate_study_evidence(valid, tmp_path)
    assert valid.observations[0].legal_currentness == "not_fully_reconciled"


@pytest.mark.parametrize("updates", [
    {"prepared_at": "2026-09-10"}, {"baseline_commit": "main"}, {"sources": []},
    {"observations": []}, {"scenario": " "}, {"complete_coverage": True},
])
def test_study_rejects_invalid_identity_and_scope(
    valid: research.LandUseStudy, updates: dict,
) -> None:
    with pytest.raises(ValidationError):
        research.LandUseStudy.model_validate({**valid.model_dump(), **updates})


def test_study_bounds_and_pdf_page_minimum(valid: research.LandUseStudy) -> None:
    for field, count in [("sources", 31), ("observations", 101)]:
        data = valid.model_dump()
        data[field] *= count
        with pytest.raises(ValidationError):
            research.LandUseStudy.model_validate(data)
    for page in (0, True, "1"):
        with pytest.raises(ValidationError):
            research.Citation.model_validate({
                **valid.observations[0].citations[0].model_dump(), "pdf_page": page,
            })


@pytest.mark.parametrize("mutation", ["missing", "directory", "corrupt", "empty", "oversized"])
def test_missing_or_corrupt_original_fails(
    tmp_path: Path, valid: research.LandUseStudy, mutation: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / valid.sources[0].archive_path
    if mutation in {"missing", "directory"}:
        path.unlink()
        if mutation == "directory":
            path.mkdir()
    elif mutation == "corrupt":
        path.write_bytes(path.read_bytes() + b"tampered")
    elif mutation == "empty":
        path.write_bytes(b"")
    else:
        monkeypatch.setattr(research, "MAX_SOURCE_BYTES", 1)
    with pytest.raises(ValueError):
        research.validate_study_evidence(valid, tmp_path)


@pytest.mark.parametrize("location", ["root", "directory", "file"])
def test_symlinks_cannot_substitute_evidence(
    tmp_path: Path, valid: research.LandUseStudy, location: str,
) -> None:
    root = tmp_path
    target = tmp_path / valid.sources[0].archive_path
    if location == "root":
        root = tmp_path / "linked-root"
        root.symlink_to(tmp_path, target_is_directory=True)
    else:
        original = target if location == "file" else target.parent
        moved = original.with_name("real-original")
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=location == "directory")
    with pytest.raises(ValueError, match="symlink"):
        research.validate_study_evidence(valid, root)


@pytest.mark.parametrize("kind", ["truncated", "header_only", "encrypted", "repaired",
                                  "no_pages", "lfs_pointer"])
def test_pdf_structure_is_verified_even_with_a_matching_hash(tmp_path: Path, kind: str) -> None:
    bodies = {
        "truncated": make_pdf()[:128], "header_only": b"%PDF-1.7\n%%EOF\n",
        "encrypted": make_pdf(encrypted=True),
        "repaired": re.sub(rb"startxref\s+\d+", b"startxref\n0", make_pdf()),
        "no_pages": make_pdf().replace(b"/Count 2", b"/Count 0"),
        "lfs_pointer": b"version https://git-lfs.github.com/spec/v1\n",
    }
    payload = study(write_source(tmp_path, bodies[kind]))
    with pytest.raises(ValueError):
        research.validate_study_evidence(payload, tmp_path)


def test_uncited_html_catalog_is_verified_but_cannot_satisfy_pdf_citation(
    tmp_path: Path, valid: research.LandUseStudy,
) -> None:
    catalog = write_source(tmp_path, b"<!doctype html><html><body>Catalog</body></html>",
                           suffix="html")
    catalog.source_id = "catalog"
    catalog.document_kind = "catalog"
    valid.sources.append(catalog)
    research.validate_study_evidence(valid, tmp_path)
    valid.observations[0].citations[0].source_id = "catalog"
    with pytest.raises(ValueError, match="PDF sources"):
        research.validate_study_evidence(valid, tmp_path)


@pytest.mark.parametrize("body", [
    b"<html>Truncated", b"ordinary text</html>",
    b"<html><title>Access Denied</title></html>",
    b"<html><title>Just a moment...</title><body>challenge</body></html>",
    b"<html><script>var _cf_chl_opt = {};</script></html>",
])
def test_non_html_bytes_cannot_be_catalog_evidence(
    tmp_path: Path, valid: research.LandUseStudy, body: bytes,
) -> None:
    source = write_source(tmp_path, body, suffix="html")
    source.source_id = "bad-catalog"
    valid.sources.append(source)
    with pytest.raises(ValueError, match="ordinary HTML"):
        research.validate_study_evidence(valid, tmp_path)


def test_cli_logs_validated_counts_and_fails_for_bad_inputs_without_writing(
    tmp_path: Path, valid: research.LandUseStudy, monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = tmp_path / "study.json"
    path.write_text(valid.model_dump_json())
    monkeypatch.chdir(tmp_path)
    args = ["--study", str(path)]
    with caplog.at_level(logging.INFO):
        assert research.main(args) == 0
    assert "Validated 1 sources and 1 research observations" in caplog.text
    assert research.main([*args, "--root", str(tmp_path / "missing")]) == 1
    path.write_text("invalid json")
    assert research.main(args) == 1
    path.write_bytes(b" " * 2_000_001)
    assert research.main(args) == 1
    path.unlink()
    assert research.main(args) == 1
    assert not path.exists()
