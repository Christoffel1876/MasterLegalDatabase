"""Validate sampled local-fee findings against preserved pages and scoped excerpt reviews.

This package reconciles source evidence. It cannot certify a complete fee schedule,
current law, total project cost, or the legal applicability of a published amount.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import pymupdf
from pydantic import Field, field_validator, model_validator

from geode.pipeline.local_coverage import CoverageLedger, LedgerModel, validate_ledger_evidence
from geode.pipeline.local_text_review import (
    ExcerptReview,
    _confined_bytes,
    _normalized,
    validate_excerpt_review,
)

LOGGER = logging.getLogger(__name__)
MAX_PACKAGE_BYTES = 5_000_000
MAX_REVIEW_BYTES = 2_000_000
DIGEST = r"^[a-f0-9]{64}$"


class FeeCitation(LedgerModel):
    """One exact page passage; a scanned passage requires a separately checked excerpt."""

    source_id: str
    source_sha256: str = Field(pattern=DIGEST)
    physical_page: int = Field(ge=1, strict=True)
    printed_page: str | None = None
    section: str
    excerpt: str
    method: Literal["native_text", "checked_ocr_excerpt"]
    checked_review_path: str | None = Field(
        default=None, pattern=r"^research/fees/[a-z0-9][a-z0-9_-]*\.json$"
    )
    checked_review_sha256: str | None = Field(default=None, pattern=DIGEST)
    checked_excerpt_id: str | None = None

    @model_validator(mode="after")
    def review_binding(self) -> FeeCitation:
        """Keep scanned reviews explicit and forbid misleading unused review metadata."""
        fields = (self.checked_review_path, self.checked_review_sha256, self.checked_excerpt_id)
        if self.method == "checked_ocr_excerpt" and not all(fields):
            raise ValueError("Scanned fee passages require a hashed checked-excerpt review")
        if self.method == "native_text" and any(value is not None for value in fields):
            raise ValueError("Native page-text citations cannot carry unused review metadata")
        return self


class FeeObservation(LedgerModel):
    """A sampled finding with conditions, never a complete price or legal opinion."""

    observation_id: str
    authority_id: str
    classification: Literal[
        "published_fee_entry", "adopting_text", "source_version", "source_conflict"
    ]
    statement: str
    conditions: list[str] = Field(min_length=1)
    evidence: list[FeeCitation] = Field(min_length=1, max_length=10)
    legal_currentness: Literal["not_verified"] = "not_verified"
    legal_review: Literal["pending"] = "pending"


class FeeOpenItem(LedgerModel):
    """An unresolved adoption, amendment, or source conflict, retained as open work."""

    item_id: str
    authority_id: str
    issue: str
    source_ids: list[str] = Field(min_length=1)
    next_action: str
    observed_urls: list[str] = Field(default_factory=list, max_length=100)
    status: Literal["open"] = "open"

    @field_validator("observed_urls")
    @classmethod
    def ordinary_links(cls, values: list[str]) -> list[str]:
        """Continuation links are ordinary HTTPS references, not network instructions."""
        for value in values:
            parsed = urlparse(value)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                    or parsed.password or parsed.port not in {None, 443}
                    or any(ord(char) < 32 for char in value)):
                raise ValueError("Continuation references must be ordinary HTTPS links")
        return values


class FeeReconciliation(LedgerModel):
    """Durable findings reuse the authority ledger's preserved source records."""

    schema_version: Literal[1] = 1
    study_id: str
    prepared_at: datetime
    ledger_path: Literal["_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json"] = (
        "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json"
    )
    scope: str
    observations: list[FeeObservation] = Field(min_length=1, max_length=200)
    open_chain: list[FeeOpenItem] = Field(min_length=1, max_length=100)
    limitations: list[str] = Field(min_length=1)
    coverage: Literal["sampled_findings_only"] = "sampled_findings_only"
    legal_currentness: Literal["not_verified"] = "not_verified"
    legal_review: Literal["pending"] = "pending"

    @field_validator("prepared_at")
    @classmethod
    def aware_timestamp(cls, value: datetime) -> datetime:
        """Preserve an unambiguous preparation time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Fee reconciliation timestamp requires a timezone")
        return value

    @model_validator(mode="after")
    def unique_identifiers(self) -> FeeReconciliation:
        """Avoid ambiguous observation and remaining-work references."""
        for identifiers in ([row.observation_id for row in self.observations],
                            [row.item_id for row in self.open_chain]):
            if len(identifiers) != len(set(identifiers)):
                raise ValueError("Fee observation and open-item IDs must be unique")
        return self


def validate_fee_reconciliation(package: FeeReconciliation, root: Path) -> None:
    """Verify source/page/owner hashes and excerpts without certifying legal currency."""
    package = FeeReconciliation.model_validate(package.model_dump())
    ledger = CoverageLedger.model_validate_json(
        _confined_bytes(root, package.ledger_path, 8_000_000)
    )
    validate_ledger_evidence(ledger, root)
    sources = {source.source_id: source for source in ledger.sources}
    owners = {authority.authority_id for authority in ledger.authorities}
    reviews: dict[str, tuple[str, ExcerptReview]] = {}
    page_text: dict[tuple[str, int], str] = {}
    for observation in package.observations:
        if observation.authority_id not in owners:
            raise ValueError("Fee observation authority is absent from the ledger")
        for citation in observation.evidence:
            source = sources.get(citation.source_id)
            if (source is None or source.authority_id != observation.authority_id
                    or source.sha256 != citation.source_sha256 or source.media_type != "pdf"
                    or source.pdf_pages is None or citation.physical_page > source.pdf_pages):
                raise ValueError(
                    "Fee citation must bind its owner's preserved PDF and physical page"
                )
            if citation.method == "native_text":
                key = (source.source_id, citation.physical_page)
                if key not in page_text:
                    with pymupdf.open(root / source.archive_path) as document:
                        page_text[key] = _normalized(
                            document[citation.physical_page - 1].get_text()
                        )
                if _normalized(citation.excerpt) not in page_text[key]:
                    raise ValueError("Fee excerpt is absent from the preserved source-page text")
                continue
            path = citation.checked_review_path
            if path not in reviews:
                body = _confined_bytes(root, path, MAX_REVIEW_BYTES)
                checked = ExcerptReview.model_validate_json(body)
                validate_excerpt_review(checked, root)
                reviews[path] = (hashlib.sha256(body).hexdigest(), checked)
            review_hash, checked = reviews[path]
            if review_hash != citation.checked_review_sha256:
                raise ValueError("Checked fee-excerpt review hash mismatch")
            excerpt = next((item for item in checked.excerpts
                            if item.excerpt_id == citation.checked_excerpt_id), None)
            if (excerpt is None or excerpt.source_id != source.source_id
                    or excerpt.source_sha256 != source.sha256
                    or excerpt.physical_page != citation.physical_page
                    or _normalized(excerpt.visually_checked_transcription)
                    != _normalized(citation.excerpt)):
                raise ValueError("Fee citation differs from its specified checked source excerpt")
    for item in package.open_chain:
        if item.authority_id not in owners:
            raise ValueError("Open fee-chain authority is absent from the ledger")
        if (len(item.source_ids) != len(set(item.source_ids))
                or any(sid not in sources or sources[sid].authority_id != item.authority_id
                       for sid in item.source_ids)):
            raise ValueError("Open fee-chain sources must belong to the stated authority")


def main(argv: list[str] | None = None) -> int:
    """Validate a durable reconciliation offline without changing its evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--study", type=Path, required=True)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        relative = (args.root / args.study).absolute().relative_to(
            args.root.absolute()
        ).as_posix()
        package = FeeReconciliation.model_validate_json(
            _confined_bytes(args.root, relative, MAX_PACKAGE_BYTES)
        )
        validate_fee_reconciliation(package, args.root)
    except (OSError, ValueError) as exc:
        LOGGER.error("Fee reconciliation validation failed: %s", exc)
        return 1
    LOGGER.info("Validated %d sampled fee findings and %d open chains; legal review remains pending",
                len(package.observations), len(package.open_chain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
