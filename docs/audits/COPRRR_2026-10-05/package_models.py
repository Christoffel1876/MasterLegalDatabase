"""Strict models for a portable supplementary source and native-page package."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    """Reject unknown fields and coercion."""

    model_config = ConfigDict(strict=True, extra="forbid")


class Asset(Strict):
    """Hash-bound relative package member."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def portable_path(cls, value: str) -> str:
        """Require a clean package-relative path."""
        if value.startswith("/") or "\\" in value or any(
            part in ("", ".", "..") for part in value.split("/")
        ):
            raise ValueError("unsafe package path")
        return value


class Page(Strict):
    """One physical source page; native extraction has not been legally reviewed."""

    citation: str
    source_id: str
    original_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    physical_page: int = Field(ge=1)
    pdf_page_label: str
    native_text: Asset
    native_text_empty_after_strip: bool
    original_page_width_points: float = Field(gt=0)
    original_page_height_points: float = Field(gt=0)
    extraction_status: Literal["native_text_unreviewed"] = "native_text_unreviewed"
    ocr_used: Literal[False] = False
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Source(Strict):
    """Fresh original acquired from an official archive's delegated public link."""

    source_id: str
    title_observed_on_official_archive: str
    official_parent_url: str
    observed_public_view_url: str
    requested_public_download_url: str
    final_response_url: str
    acquired_at: str
    original: Asset
    page_count: int = Field(gt=0)
    empty_native_pages: list[int]
    native_text_bytes: int = Field(ge=0)
    acquisition_receipts: list[Asset]
    historical_record_id: str
    historical_index_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    historical_index_sha256_basis: Literal["summary_utf8"] = "summary_utf8"
    historical_original_sha256: None = None
    historical_original_comparison: Literal[
        "not_possible_no_historical_original_hash_or_body"
    ] = "not_possible_no_historical_original_hash_or_body"
    format_verified: Literal["pdf_opened_without_repair_or_encryption"]
    extraction_method: str
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class MissingOriginal(Strict):
    """Existing baseline identity and its observed local source-path availability."""

    record_id: str
    source_path: str
    expected_sha256: str
    expected_sha256_basis: Literal["summary_utf8", "original_pdf_bytes"]
    materialized_at_existing_path: bool
    matches_expected_sha256: bool | None


class Observation(Strict):
    """Explicitly transcribed browser evidence, never represented as raw HTTP."""

    url: str
    observation: str
    observed_links: list[str]
    evidence_kind: Literal["browser_visible_dom_transcription"] = "browser_visible_dom_transcription"
    raw_wire_capture_available: Literal[False] = False


class Gap(Strict):
    """Machine-readable unresolved source or coverage finding."""

    gap_id: str
    source_url: str | None
    existing_record_id: str | None
    state: str
    evidence_paths: list[str]
    explanation: str
    original_acquired: Literal[False] = False


class Provenance(Strict):
    """Package-level scope, browser findings, and retained gaps."""

    recorded_at: str
    root_run_sha256: str
    root_supplement_sha256: str
    collection_request_count: int = Field(le=45)
    collection_charged_bytes: int = Field(le=100000000)
    collection_body_cap_bytes: Literal[15000000] = 15000000
    browser_successful_navigation_count: int = Field(le=10)
    browser_policy_refused_navigation_count: int
    browser_resource_bytes: Literal["unmetered_separate"] = "unmetered_separate"
    baseline_index: Asset
    baseline_original_availability: list[MissingOriginal]
    browser_observations: list[Observation]
    gaps: list[Gap]
    native_extraction_limitations: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Manifest(Strict):
    """Closed set of portable package members except this manifest itself."""

    schema_version: Literal["supplementary-source-native-package-1"]
    created_at: str
    original_count: int
    native_page_count: int
    original_bytes: int
    native_text_bytes: int
    assets: list[Asset]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Verification(Strict):
    """Offline package verification and negative citation checks."""

    verified_at: str
    manifest_sha256: str
    manifest_member_count: int
    original_count: int
    native_page_count: int
    original_bytes: int
    native_text_bytes: int
    verified_request_count: int
    verified_charged_bytes: int
    exact_citation_cases: int
    negative_citation_cases: int
    hash_mismatch_cases: int
    unsafe_path_cases: int
    all_page_text_reextractions_identical: Literal[True] = True
    all_pdf_structures_verified: Literal[True] = True
    all_manifest_members_verified: Literal[True] = True
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
