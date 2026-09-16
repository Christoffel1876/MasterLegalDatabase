"""Strict bounded acquisition and literal-source-review evidence."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

class Strict(BaseModel):
    """Reject unknown fields and implicit coercion."""
    model_config=ConfigDict(extra='forbid',strict=True)

class Asset(Strict):
    """Exact relative payload identity."""
    path: str
    sha256: str=Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int=Field(ge=0)

class Event(Strict):
    """One deliberate attempted public request; hidden transport events unmeasured."""
    sequence: int=Field(ge=1,le=8)
    requested_url: str
    returned_url: str | None
    reserved_at: AwareDatetime
    started_at: AwareDatetime
    finished_at: AwareDatetime
    status: int | None
    outcome: Literal['received','redirect','denied','failed','limit_refusal']
    body: Asset | None
    headers: dict[str,str]
    omitted_header_names: list[str]
    redirect_location: str | None
    error: str | None
    complete: bool

class Access(Strict):
    """Bounded finite request receipt, not a currentness determination."""
    recorded_at: AwareDatetime
    request_cap: Literal[8]
    distinct_target_cap: Literal[6]
    per_response_byte_cap: Literal[10485760]
    aggregate_byte_cap: Literal[20971520]
    deliberate_attempts: int
    distinct_targets: int
    retained_body_bytes: int
    tls_verification: Literal[True]
    cookies_or_authentication_used: Literal[False]
    events: list[Event]
    limitations: list[str]

class Page(Strict):
    """Complete image and unchanged machine candidates; visual wording is separate."""
    physical_page: int
    image: Asset
    native: Asset
    directly_viewed: Literal[True]
    reviewed_text: str
    observations: list[str]

class Review(Strict):
    """Literal resolution review with qualified dates and execution markings."""
    source_id: Literal['el-paso-boa-resolution-25-290-directed-lead']
    authority_id: Literal['CO-COUNTY-EL_PASO']
    reviewed_at: AwareDatetime
    reviewer: Literal['Plato']
    method: str
    source: Asset
    referring_html: Asset
    referring_href: str
    referring_anchor_text: str
    pages: list[Page]
    status: Literal['literal_source_review_pending_atlas_acceptance']
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    source_date_claims: list[str]
    limitations: list[str]

class Manifest(Strict):
    """Closed inventory excluding the manifest itself."""
    recorded_at: AwareDatetime
    status: Literal['frozen_literal_source_review_not_current_law']
    files: list[Asset]

class Match(Strict):
    """Exact matching tracked JSONL row retained as source bytes."""
    line_number: int
    matched_values: list[str]
    row_sha256: str
    raw_line: str

class Compared(Strict):
    """One pinned Git blob, streamed completely for exact equality only."""
    repository_path: str
    git_blob_oid: str
    sha256: str
    size_bytes: int
    line_count: int
    parsed_json_rows: int
    parse_errors: int
    is_lfs_pointer: bool
    matches: list[Match]

class Comparison(Strict):
    """Bounded local historical comparison, not proof of universal absence."""
    recorded_at: AwareDatetime
    repository_main_commit: str
    urls: list[str]
    acquired_pdf_sha256: str
    manifests: list[Compared]
    limitations: list[str]

class Render(Strict):
    """Actual derivative method and exact crop geometry."""
    started_at: AwareDatetime
    finished_at: AwareDatetime
    argv: list[str]
    exit_code: Literal[0]
    renderer_sha256: str
    pymupdf_version: str
    native_method: str
    native_bytes_per_page: list[int]
    crops: list[dict[str,str | int | list[int]]]

class Verification(Strict):
    """Actual bounded offline check receipt, separate from visual attestation."""
    started_at: AwareDatetime
    finished_at: AwareDatetime
    argv: list[str]
    exit_code: Literal[0]
    stdout: Asset
    stderr: Asset
    integrity_cases: list[str]
    source_review_limit: str
