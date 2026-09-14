"""Strict public-subset custody without private-header derivation claims."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undocumented fields and coercion in public preservation records."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Identify an unchanged file using an exact relative path, size and SHA256."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=0)


class Omission(Strict):
    """Retain custody of an excluded original without exposing its contents."""

    event_id: str = Field(pattern=r"^E\d{3}$")
    original: Asset
    retained_public_derivative: Asset
    sensitive_header_names: list[str]
    derivative_verified_locally_before_omission: Literal[True] = True
    portable_derivation_replay: Literal[False] = False


class Omissions(Strict):
    """Record all original response-header omissions, including nonsensitive originals."""

    status: Literal["public_subset_private_originals_omitted"]
    prepared_at: AwareDatetime
    original_directory_claim: str
    original_manifest: Asset
    original_payloads: Literal[716] = 716
    omitted_private_headers: list[Omission] = Field(min_length=31, max_length=31)
    locally_observed_sensitive_header_events: Literal[7] = 7
    qualification: str


class PrivacyScan(Strict):
    """Report a bounded value/field scan without disclosing removed credential values."""

    checked_at: AwareDatetime
    verbatim_files_scanned: Literal[686] = 686
    total_bytes_scanned: int = Field(ge=0)
    credential_values_checked: int = Field(ge=0)
    exact_retained_credential_value_matches: Literal[0] = 0
    sensitive_public_header_fields: Literal[0] = 0
    private_header_files_copied: Literal[0] = 0
    scope: list[str]


class Manifest(Strict):
    """Close the distributable file set and bind the preserved historical manifest."""

    status: Literal["frozen_public_preservation_source_only"]
    created_at: AwareDatetime
    original_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    copied_original_files: Literal[686] = 686
    omitted_original_files: Literal[31] = 31
    files: list[Asset]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Verification(Strict):
    """Report exactly the public checks replayed, keeping historical limits explicit."""

    status: Literal["passed_public_subset_limited_replay"]
    public_files: int
    copied_original_files: Literal[686] = 686
    omitted_private_headers: Literal[31] = 31
    events: Literal[31] = 31
    exact_requested_urls: Literal[30] = 30
    retained_response_bytes: Literal[14428668] = 14428668
    pdfs: Literal[8] = 8
    physical_native_pages_replayed: Literal[403] = 403
    saved_full_page_renders_replayed: Literal[18] = 18
    historical_viewed_page_records: Literal[14] = 14
    new_visual_page_reviews: Literal[0] = 0
    historical_legacy_rows_streamed: Literal[48390] = 48390
    priority_records: Literal[12] = 12
    checklist_rows: Literal[24] = 24
    header_derivation_replayed: Literal[False] = False
    original_size_probe_replayed: Literal[False] = False
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    limitations: list[str]
