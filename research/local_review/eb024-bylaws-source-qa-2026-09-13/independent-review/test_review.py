"""Meaningful offline refusal checks for the complete five-page source review."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from review import ROOT, Review, asset, check_review


@pytest.fixture
def original() -> Review:
    """Load the actual fixed-source review without editing it."""
    return Review.model_validate_json((ROOT / "SOURCE_QA.json").read_bytes())


def test_complete_review(original: Review) -> None:
    """The intact source carries every native line and the real page continuation."""
    check_review(ROOT, original)
    assert len([line for page in original.pages for line in page.lines]) == 170
    assert original.pages[4].paragraphs[0].continuation_from == "P4-B09"


def test_unrelated_source_identity_refused(original: Review) -> None:
    """A real unrelated file cannot be presented as the PDF with otherwise valid page evidence."""
    record = original.model_copy(deep=True)
    record.source = asset(ROOT, "SOURCE_FIRST_NOTES.md")
    with pytest.raises(ValueError, match="Fixed review/source identity differs"):
        check_review(ROOT, record)


@pytest.mark.parametrize("kind", ["word", "range", "geometry", "paragraph", "continuation", "footer"])
def test_modified_review_refused(original: Review, kind: str) -> None:
    """Reject changed wording, coordinates, ownership of text or missing physical-page context."""
    record = original.model_copy(deep=True)
    if kind == "word":
        record.pages[2].lines[0].text = "Unsupported replacement\n"
    elif kind == "range":
        record.pages[2].lines[0].start += 1
    elif kind == "geometry":
        record.pages[2].lines[0].bbox_pdf_points[0] += 20
    elif kind == "paragraph":
        record.pages[2].paragraphs[1].section_heading = "SECTION 1.3: MEETINGS"
    elif kind == "continuation":
        record.pages[4].paragraphs[0].continuation_from = None
    else:
        record.pages[4].lines.pop()
        record.pages[4].paragraphs.pop()
    with pytest.raises(ValueError, match="Page, native, geometry or paragraph context differs"):
        check_review(ROOT, record)


@pytest.mark.parametrize("kind", ["pdf", "native", "png", "symlink"])
def test_changed_source_fixture_refused(tmp_path: Path, original: Review, kind: str) -> None:
    """Real temporary file alterations cannot acquire a verified source-review result."""
    fixture = tmp_path / "fixture"
    for name in ["source", "candidate", "crops"]:
        shutil.copytree(ROOT / name, fixture / name)
    shutil.copyfile(ROOT / "SOURCE_FIRST_NOTES.md", fixture / "SOURCE_FIRST_NOTES.md")
    if kind == "pdf":
        target = fixture / "source/original.pdf"
        target.write_bytes(target.read_bytes() + b"\n% altered source\n")
    elif kind == "native":
        target = fixture / "candidate/page-0003.native.txt"
        target.write_bytes(target.read_bytes().replace(b"11-10.5-10 1", b"11-10.5-101"))
    elif kind == "png":
        target = fixture / "source/page-0005.png"
        target.write_bytes((fixture / "source/page-0004.png").read_bytes())
    else:
        target = fixture / "candidate/page-0003.native.txt"
        target.unlink()
        target.symlink_to(ROOT / "candidate/page-0003.native.txt")
    with pytest.raises(ValueError):
        check_review(fixture, original)


@pytest.mark.parametrize("field,value", [("legal_currentness", "verified"),
                                          ("answer_safe", True),
                                          ("authority_id", "CO-MUNICIPAL-PUEBLO"),
                                          ("unrecognized", "extra")])
def test_false_promotions_and_schema_extras_refused(field: str, value: object) -> None:
    """Reject a source review silently promoted or reassigned to another authority."""
    record = json.loads((ROOT / "SOURCE_QA.json").read_bytes())
    record[field] = value
    with pytest.raises(ValidationError):
        Review.model_validate_json(json.dumps(record))
