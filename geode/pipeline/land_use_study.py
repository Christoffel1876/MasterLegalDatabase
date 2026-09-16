"""Research-only land-use observations with offline, page-exact source verification.

Evidence validation establishes byte provenance and excerpt presence. It does not
establish legal currency, completeness, applicability, or the truth of a paraphrase.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import pymupdf
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

County = Literal["Jefferson", "Clear Creek"]
COUNTY_HOSTS = {
    "Jefferson": {"jeffco.us", "www.jeffco.us"},
    "Clear Creek": {"clearcreekcounty.us", "www.clearcreekcounty.us"},
}
MAX_SOURCE_BYTES = 30_000_000
LOGGER = logging.getLogger(__name__)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Evidence timestamps must include a timezone")
    return value


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


class StudyModel(BaseModel):
    """Reject undeclared fields and empty strings throughout the research contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)


class StudySource(StudyModel):
    """One preserved county original, without a claim of fully reconciled current law."""

    source_id: str
    county: County
    title: str
    url: str
    archive_path: str = Field(
        pattern=r"^_RAW_ARCHIVE/local/(research|reacquisition)/[a-f0-9]{64}\.(pdf|html)$"
    )
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    retrieved_at: datetime
    document_kind: Literal[
        "zoning_text", "fee_schedule", "policy", "process_guide", "catalog", "other"
    ]
    version_statement: str | None = None
    currentness_status: Literal[
        "edition_identified_unreconciled", "edition_and_catalog_consistent", "unknown"
    ] = "unknown"
    currentness_notes: str

    @field_validator("retrieved_at")
    @classmethod
    def aware_retrieval(cls, value: datetime) -> datetime:
        """Require timezone-aware retrieval evidence."""
        return _aware(value)

    @model_validator(mode="after")
    def provenance(self) -> StudySource:
        """Match the archive digest and declared county's official HTTPS location."""
        parsed = urlparse(self.url)
        if (parsed.scheme != "https" or parsed.hostname not in COUNTY_HOSTS[self.county]
                or parsed.username is not None or parsed.password is not None
                or parsed.port not in {None, 443} or any(ord(char) < 32 for char in self.url)):
            raise ValueError("Study source URL must belong to its declared county")
        if Path(self.archive_path).stem != self.sha256:
            raise ValueError("Source archive filename must match its SHA-256")
        if self.currentness_status != "unknown" and self.version_statement is None:
            raise ValueError("An identified edition requires a source version statement")
        return self


class Citation(StudyModel):
    """An exact excerpt on one physical PDF page; printed labels remain separate."""

    source_id: str
    pdf_page: int = Field(ge=1, strict=True)
    printed_page: str | None = None
    section: str
    excerpt: str


class Observation(StudyModel):
    """A scoped research statement that retains conditions and review limitations."""

    id: str
    county: County
    stage: Literal["presubmission", "submission", "review", "hearing", "decision", "fees", "scope"]
    actor: str
    statement: str
    modality: Literal["mandatory", "optional", "conditional", "agency_discretion", "informational"]
    conditions: list[str] = Field(default_factory=list)
    fee_text: str | None = None
    timing_text: str | None = None
    citations: list[Citation] = Field(min_length=1)
    research_only: Literal[True] = True
    legal_currentness: Literal["not_fully_reconciled"] = "not_fully_reconciled"

    @model_validator(mode="after")
    def explicit_conditions(self) -> Observation:
        """Conditional observations must retain at least one stated condition."""
        if self.modality == "conditional" and not self.conditions:
            raise ValueError("Conditional observation requires explicit conditions")
        return self


class LandUseStudy(StudyModel):
    """A bounded comparison of researched passages, not a complete compliance answer."""

    study_id: str
    scenario: str
    scope_boundary: str
    prepared_at: datetime
    baseline_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    sources: list[StudySource] = Field(min_length=1, max_length=30)
    observations: list[Observation] = Field(min_length=1, max_length=100)
    open_questions: list[str] = Field(default_factory=list)

    @field_validator("prepared_at")
    @classmethod
    def aware_preparation(cls, value: datetime) -> datetime:
        """Require a timezone-aware preparation timestamp."""
        return _aware(value)

    @model_validator(mode="after")
    def references(self) -> LandUseStudy:
        """Reject duplicate identities, undeclared sources, and cross-county citations."""
        sources = {source.source_id: source for source in self.sources}
        if len(sources) != len(self.sources):
            raise ValueError("Study source IDs must be unique")
        if len({item.id for item in self.observations}) != len(self.observations):
            raise ValueError("Observation IDs must be unique")
        for observation in self.observations:
            for citation in observation.citations:
                source = sources.get(citation.source_id)
                if source is None or source.county != observation.county:
                    raise ValueError("Citation must reference a declared source in the same county")
                if not source.archive_path.endswith(".pdf"):
                    raise ValueError("Page citations require PDF sources")
        return self


def _source_bytes(root: Path, source: StudySource) -> bytes:
    path = root
    if path.is_symlink():
        raise ValueError("Evidence root must not be a symlink")
    for part in Path(source.archive_path).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Evidence path must not contain symlinks")
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Source is not an ordinary file inside the root: {source.source_id}")
    with path.open("rb") as stream:
        body = stream.read(MAX_SOURCE_BYTES + 1)
    if not body or len(body) > MAX_SOURCE_BYTES:
        raise ValueError("Evidence original is empty or exceeds the 30 MB source limit")
    if hashlib.sha256(body).hexdigest() != source.sha256:
        raise ValueError(f"Source hash mismatch: {source.source_id}")
    return body


def validate_study_evidence(study: LandUseStudy, root: Path) -> None:
    """Verify every original and cited PDF excerpt without writes or network requests.

    Raises:
        ValueError: The schema, source identity, bytes, PDF, or exact page excerpt fails.
    """
    study = LandUseStudy.model_validate(study.model_dump())
    for source in study.sources:
        body = _source_bytes(root, source)
        if source.archive_path.endswith(".html"):
            if (not re.search(rb"<(?:!doctype\s+html|html)\b", body[:131072], re.I)
                    or not re.search(rb"</html\s*>\s*$", body, re.I)
                    or re.search(rb"<title[^>]*>\s*(access denied|just a moment)"
                                 rb"|_cf_chl_opt|cf-chl-widget", body[:131072], re.I)):
                raise ValueError(f"Source is not complete ordinary HTML: {source.source_id}")
            continue
        if not body.startswith(b"%PDF-") or not body.rstrip().endswith(b"%%EOF"):
            raise ValueError(f"Source is not a complete PDF: {source.source_id}")
        try:
            with pymupdf.open(stream=body, filetype="pdf") as document:
                if document.is_repaired or document.is_encrypted or document.page_count < 1:
                    raise ValueError("PDF is repaired, encrypted, or has no pages")
                pages = {}
                for observation in study.observations:
                    for citation in observation.citations:
                        if citation.source_id != source.source_id:
                            continue
                        if citation.pdf_page > document.page_count:
                            raise ValueError(f"PDF citation page does not exist: {observation.id}")
                        if citation.pdf_page not in pages:
                            pages[citation.pdf_page] = _normalized(
                                document.load_page(citation.pdf_page - 1).get_text()
                            )
                        if _normalized(citation.excerpt) not in pages[citation.pdf_page]:
                            raise ValueError(
                                f"Exact excerpt absent from PDF page: {observation.id}"
                            )
        except Exception as exc:
            raise ValueError(f"Invalid PDF evidence for {source.source_id}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    """Validate an archived research study offline, logging counts without writing data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        with args.study.open("rb") as stream:
            body = stream.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Study JSON exceeds the 2 MB bounded read limit")
        study = LandUseStudy.model_validate_json(body)
        validate_study_evidence(study, args.root)
    except (OSError, ValueError) as exc:
        LOGGER.error("Study evidence validation failed: %s", exc)
        return 1
    LOGGER.info("Validated %d sources and %d research observations",
                len(study.sources), len(study.observations))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
