"""Strict, portable evidence for a later recorded acquisition of existing source bytes."""
from __future__ import annotations
from typing import Literal
from pathlib import PurePosixPath
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    """Forbid extra fields and scalar coercion."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """One package-relative ordinary file."""
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator('path')
    @classmethod
    def confined(cls, value: str) -> str:
        """Reject path escapes before any file access."""
        if PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts:
            raise ValueError('Unsafe package path')
        return value


class Copy(Strict):
    """Retain the origin label separately from an unchanged copied asset."""
    original_path: str
    copied: Asset
    copy_method: Literal['unchanged_exact_bytes'] = 'unchanged_exact_bytes'


class Line(Strict):
    """Bind selected raw UTF-8 JSONL bytes, including the original line ending."""
    original_repository_path: str
    original_whole_file_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    original_whole_file_size_bytes: int = Field(gt=0)
    original_zero_based_row: int = Field(ge=0)
    selected_document: Asset
    selected_zero_based_row: int = Field(ge=0)
    exact_line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    exact_line_size_bytes: int = Field(gt=0)


class Anchor(Strict):
    """Bind the precise fresh HTML anchor without claiming a rendered label."""
    parent: Asset
    parent_url: str
    href: str
    exact_source_start_byte: int = Field(ge=0)
    exact_source_end_byte: int = Field(gt=0)
    exact_anchor_html: str
    anchor_html_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    normalized_dom_text: str
    occurrence_count: Literal[1]
    label_scope: Literal['DOM text including icon-label strings; not a new visual webpage review']


class ArchivedMatch(Strict):
    """Existing sources were compared to the retained fresh body, not reacquired again."""
    repository_path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(gt=0)
    byte_comparison: Literal['same_exact_bytes']
    represented_by: Asset


class Source(Strict):
    """Separate a new HTTP custody event from an earlier canonical intake record."""
    event_id: str
    record_id: str
    authority_id: Literal['CO-MUNICIPAL-GREELEY']
    layer_id: Literal['10_Municipal_Authorities']
    body: Asset
    reservation: Asset
    receipt: Asset
    pages: int = Field(gt=0)
    anchor: Anchor
    archived_source: ArchivedMatch
    prior_qa_original: ArchivedMatch
    canonical_record: Line
    prior_provenance: Line
    prior_qa: Asset
    prior_qa_schema: Asset
    prior_qa_source_sha_pointer: str
    source_role: str
    prior_repository_received_at: AwareDatetime
    prior_acquisition_method: Literal['received_review_package']
    prior_official_source_url: None
    qualifications: list[str] = Field(min_length=3)
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]


class Scan(Strict):
    """Describe what was actually scanned, without certifying absence of all secrets."""
    public_header_names: list[str]
    header_dictionary_count: Literal[8]
    rejected_header_keys_found: list[str]
    credential_patterns: list[str]
    scanned_text_assets: list[str]
    credential_pattern_match_count: Literal[0]
    receipt_error_texts_empty: Literal[True]
    raw_response_headers_available: Literal[False]
    original_header_exclusions: list[str]
    limitations: list[str]
    redactions_performed_in_this_package: Literal[0]


class Preservation(Strict):
    """Qualified offline preservation of four recorded complete GET results."""
    schema_version: Literal[1]
    status: Literal['public_custody_preserved_no_canonical_change']
    preserved_at: AwareDatetime
    original_copies: list[Copy]
    acquisition_script: Asset
    sources: list[Source] = Field(min_length=3,max_length=3)
    fresh_parent: Asset
    historical_parent: Asset
    parent_byte_identity: Literal['same_exact_bytes']
    privacy_scan: Scan
    recorded_public_gets: Literal[4]
    recorded_redirects: Literal[0]
    requests_by_this_preservation: Literal[0]
    canonical_writes: Literal[0]
    total_pdf_pages: Literal[6]
    total_pdf_bytes: Literal[877639]
    full_source_qa_replayed: Literal[False]
    old_acquisition_claims_changed: Literal[False]
    legal_currentness: Literal['not_verified']
    limitations: list[str]


class Document(Strict):
    """HttpBinding-compatible package-relative document location."""
    artifact: Asset
    jsonl_row: int | None = Field(default=None,ge=0)


class HttpBinding(Strict):
    """Exact existing inventory contract, with package-relative paths awaiting integration."""
    document: Document
    sha_pointer: str
    status_pointer: str
    time_pointer: str


class HttpCandidate(Strict):
    """Propose an additive fresh-event reference; not an inventory mutation."""
    record_id: str
    verified_http: HttpBinding
    path_basis: Literal['package-relative; prefix with actual destination if later integrated']
    time_role: Literal['recorded response completion, not original acquisition or repository intake']
    integration_status: Literal['not_applied']


class Manifest(Strict):
    """Closed inventory of all distributable evidence, excluding only its own JSON."""
    schema_version: Literal[1]
    status: Literal['public_custody_preserved_no_canonical_change']
    prepared_at: AwareDatetime
    files: list[Asset]
    self_excluded: Literal['FINAL_MANIFEST.json']
    legal_currentness: Literal['not_verified']
