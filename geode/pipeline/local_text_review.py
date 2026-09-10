"""Bind bounded visual excerpt checks to preserved sources and machine OCR pages.

An excerpt check records what an assistant compared with a rendered source page.
It does not certify every character on that page, an entire document, legal force,
currentness, or completeness. Unchecked OCR text remains machine-generated text.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from geode.pipeline.local_coverage import CoverageLedger, LedgerModel, validate_ledger_evidence

LOGGER = logging.getLogger(__name__)
MAX_REVIEW_BYTES = 2_000_000
MAX_PAGE_BYTES = 4_000_000


def _normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


class CheckedExcerpt(LedgerModel):
    """One source-page passage, with explicit OCR corrections and limited review scope."""

    excerpt_id: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_page: int = Field(ge=1, strict=True)
    ocr_page_path: str = Field(
        pattern=r"^_DERIVED/local_ocr/[a-z0-9][a-z0-9_-]*/"
                r"[a-f0-9]{64}/page-[0-9]{4,6}\.json$"
    )
    ocr_page_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    topic: Literal["adoption", "effective_date", "repeal", "scope", "fee", "exception"]
    raw_ocr_excerpt: str
    visually_checked_transcription: str
    correction_notes: list[str] = Field(default_factory=list)
    source_context: str
    review_method: Literal["assistant_compared_source_page_image"] = (
        "assistant_compared_source_page_image"
    )
    review_scope: Literal["specified_excerpt_only"] = "specified_excerpt_only"
    legal_currentness: Literal["not_verified"] = "not_verified"
    legal_review: Literal["pending"] = "pending"

    @model_validator(mode="after")
    def explicit_corrections(self) -> CheckedExcerpt:
        """Require a reason for every passage whose visual transcription differs from OCR."""
        if (_normalized(self.raw_ocr_excerpt) != _normalized(self.visually_checked_transcription)
                and not self.correction_notes):
            raise ValueError("Changed OCR transcription requires explicit correction notes")
        if (Path(self.ocr_page_path).parent.name != self.source_sha256
                or Path(self.ocr_page_path).stem != f"page-{self.physical_page:04d}"):
            raise ValueError("OCR evidence path must match the declared source and physical page")
        return self


class ExcerptReview(LedgerModel):
    """An immutable, scoped set of excerpt checks, never a whole-document approval."""

    schema_version: Literal[1] = 1
    review_id: str
    prepared_at: datetime
    ledger_path: Literal["_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json"] = (
        "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json"
    )
    excerpts: list[CheckedExcerpt] = Field(min_length=1, max_length=200)
    limits: list[str] = Field(min_length=1)
    unreviewed_text_status: Literal["machine_ocr_unreviewed"] = "machine_ocr_unreviewed"

    @field_validator("prepared_at")
    @classmethod
    def aware_preparation(cls, value: datetime) -> datetime:
        """Require an unambiguous review timestamp."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Review timestamp requires a timezone")
        return value

    @model_validator(mode="after")
    def unique_ids(self) -> ExcerptReview:
        """Reject ambiguous duplicate excerpt identifiers."""
        if len({row.excerpt_id for row in self.excerpts}) != len(self.excerpts):
            raise ValueError("Excerpt IDs must be unique")
        return self


def _confined_bytes(root: Path, relative: str, maximum: int) -> bytes:
    path = root / relative
    if any(part.is_symlink() for part in (path.absolute(), *path.absolute().parents)):
        raise ValueError("Evidence paths and their ancestors cannot contain symlinks")
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Evidence must be an ordinary file within the project root")
    with path.open("rb") as stream:
        body = stream.read(maximum + 1)
    if not body or len(body) > maximum:
        raise ValueError("Evidence file is empty or exceeds its read limit")
    return body


def validate_excerpt_review(review: ExcerptReview, root: Path) -> None:
    """Verify excerpt/source/page references without claiming to automate visual review."""
    from geode.pipeline.verified_local_ocr import (
        CollectionSelection, OCRManifest, OCRPage, validate_ocr_collection,
    )

    review = ExcerptReview.model_validate(review.model_dump())
    ledger = CoverageLedger.model_validate_json(
        _confined_bytes(root, review.ledger_path, 8_000_000)
    )
    validate_ledger_evidence(ledger, root)
    sources = {source.source_id: source for source in ledger.sources}
    collections: dict[str, CollectionSelection] = {}
    manifests: dict[tuple[str, str], OCRManifest] = {}
    for excerpt in review.excerpts:
        source = sources.get(excerpt.source_id)
        if (source is None or source.sha256 != excerpt.source_sha256
                or source.media_type != "pdf" or source.pdf_pages is None
                or excerpt.physical_page > source.pdf_pages):
            raise ValueError("Excerpt must identify a preserved PDF and an existing physical page")
        body = _confined_bytes(root, excerpt.ocr_page_path, MAX_PAGE_BYTES)
        if hashlib.sha256(body).hexdigest() != excerpt.ocr_page_sha256:
            raise ValueError("OCR page evidence hash mismatch")
        page = OCRPage.model_validate_json(body)
        if (page.source_id != source.source_id or page.source_sha256 != source.sha256
                or page.source_page_number != excerpt.physical_page
                or page.source_page_count != source.pdf_pages):
            raise ValueError("OCR page identifies a different source or physical page")
        if _normalized(excerpt.raw_ocr_excerpt) not in _normalized(page.text):
            raise ValueError("Claimed OCR excerpt is absent from the preserved page text")
        collection = Path(excerpt.ocr_page_path).parent.parent.as_posix()
        if collection not in collections:
            # Integrity validation preserves failed/blank status; it is not legal approval.
            validate_ocr_collection(root, root / collection, root / review.ledger_path)
            collections[collection] = CollectionSelection.model_validate_json(
                _confined_bytes(root, f"{collection}/selection.json", MAX_REVIEW_BYTES)
            )
        if source.source_id not in collections[collection].source_ids:
            raise ValueError("Cited OCR source is absent from the collection selection")
        key = (collection, source.sha256)
        if key not in manifests:
            manifests[key] = OCRManifest.model_validate_json(_confined_bytes(
                root, f"{collection}/{source.sha256}/manifest.json", MAX_PAGE_BYTES,
            ))
        if not any(
            record.source_page_number == excerpt.physical_page
            and f"{collection}/{record.path}" == excerpt.ocr_page_path
            and record.sha256 == excerpt.ocr_page_sha256
            for record in manifests[key].pages
        ):
            raise ValueError("Cited OCR page is absent from its collection manifest")


def main(argv: list[str] | None = None) -> int:
    """Validate a review package offline without changing source or review records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--review", type=Path, required=True)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        relative = (args.root / args.review).absolute().relative_to(
            args.root.absolute()
        ).as_posix()
        review = ExcerptReview.model_validate_json(
            _confined_bytes(args.root, relative, MAX_REVIEW_BYTES)
        )
        validate_excerpt_review(review, args.root)
    except (OSError, ValueError) as exc:
        LOGGER.error("Excerpt review validation failed: %s", exc)
        return 1
    LOGGER.info("Validated %d bounded excerpt checks; whole-document review remains pending",
                len(review.excerpts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
