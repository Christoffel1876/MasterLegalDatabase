"""Strict records for the three-target Chaffee preservation task."""

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Reject coercion and undeclared fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class FileRef(StrictModel):
    """Exact package-relative byte identity."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        """Reject paths outside the package or ambiguous components."""
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or str(path) != value or "\\" in value:
            raise ValueError("unsafe package path")
        return value


class Target(StrictModel):
    """Observed county referral and, where present, supplied redirect proof."""

    target_id: str
    authority_id: Literal["CO-COUNTY-CHAFFEE"]
    layer_id: Literal["08"]
    parent_url: str
    parent_body: FileRef
    base_href: str
    literal_href: str
    visible_label: str
    resolved_county_url: str
    encoded_county_url: str
    prior_redirect_notice: FileRef | None
    prior_header_summary: FileRef | None
    prior_reported_status: Literal[302] | None
    raw_location: str | None
    request_url: str
    encoding_rule: Literal["urljoin first HTML base and literal href; encode spaces once"]
    evidence_limit: str
    anticipated_role: str
    legal_currentness: Literal["not_verified"]


class Plan(StrictModel):
    """Fixed targets and nonrenewable serial request limits."""

    schema_version: Literal["chaffee-directed-plan-v1"]
    prepared_at: str
    status: Literal["PREPARED_NOT_EXECUTED"]
    targets: list[Target] = Field(min_length=3, max_length=3)
    maximum_actions: Literal[3]
    maximum_distinct_urls: Literal[3]
    maximum_body_bytes: Literal[20000000]
    maximum_total_body_bytes: Literal[50000000]
    request_seconds: Literal[60]
    connect_seconds: Literal[15]
    no_start_after: Literal["2026-09-13T17:45:00Z"]
    finish_by: Literal["2026-09-13T18:00:00Z"]
    redirects: Literal[False]
    retries: Literal[0]
    request_user_agent: str
    authorization: str
    limitations: list[str]


class PlanFreeze(StrictModel):
    """Byte identities frozen before the first network request."""

    frozen_at: str
    plan: FileRef
    schema_file: FileRef
    evidence: list[FileRef]
    public_actions_before_freeze: Literal[0]


class Reservation(StrictModel):
    """Write-once reservation counting a deliberate invocation."""

    action_id: str
    target_id: str
    reserved_at: str
    plan_sha256: str
    request_url: str
    maximum_body_bytes: int = Field(gt=0, le=20000000)
    maximum_seconds: int = Field(gt=0, le=60)
    connect_seconds: Literal[15]
    prior_actions: int = Field(ge=0, le=2)
    prior_body_bytes: int = Field(ge=0, le=50000000)
    argv: list[str]
    shell_display: str
    runner: FileRef
    cwd: str
    network_permission: Literal["explicitly_authorized_narrow_escalation"]


class HeaderCustody(StrictModel):
    """Original header digest and public exact-line subset; no secret values."""

    original_sha256: str
    original_size_bytes: int
    public_subset: FileRef
    retained_field_names: list[str]
    omitted_field_names: list[str]
    omitted_line_count: int
    original_retained: Literal[False]
    limitation: str


class Attempt(StrictModel):
    """Actual local invocation and structural result, without source QA."""

    action_id: str
    target_id: str
    requested_url: str
    final_url: str | None
    location: str | None
    started_at: str
    completed_at: str
    elapsed_monotonic_seconds: float
    process_exit: int | None
    outer_timeout: bool
    http_status: int | None
    curl_reported_download_bytes: int | None
    curl_reported_redirects: int | None
    tls_verify_result: int | None
    body: FileRef
    stdout: FileRef
    stderr: FileRef
    headers: HeaderCustody
    body_complete: bool
    partial_or_unknown: bool
    cap_reached: bool
    must_stop: bool
    pdf_magic: bool
    pdf_parse_ok: bool
    pdf_pages: int | None
    parser_version: str | None
    structural_error: str | None
    disposition: str
    evidence_role: Literal["directed_original_response_custody_only"]
    reviewed_pages: Literal[0]
    answer_safe: Literal[False]
    legal_currentness: Literal["not_verified"]


class Manifest(StrictModel):
    """Closed public package inventory; final manifest excludes itself only."""

    schema_version: Literal["chaffee-directed-public-custody-v1"]
    sealed_at: str
    files: list[FileRef]
    action_count: int = Field(ge=0, le=3)
    distinct_requested_urls: int = Field(ge=0, le=3)
    retained_response_body_bytes: int = Field(ge=0, le=50000000)
    pdf_count: int = Field(ge=0, le=3)
    pdf_pages: int = Field(ge=0)
    unopened_target_ids: list[str]
    limitations: list[str]
