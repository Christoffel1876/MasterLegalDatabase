"""Fixed Chaffee two-source custody contract; execution time is not prepared."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

SourceID = Literal[
    "chaffee-cwrc-ordinance-2026-02-atlas-directed",
    "chaffee-electric-ordinance-2026-01-atlas-directed",
]
URLS = {
    "chaffee-cwrc-ordinance-2026-02-atlas-directed": (
        "https://cms2.revize.com/revize/chaffeecounty/Documents/Departments/"
        "Building%20Department/Adopted%20Codes%20&%20Design%20Criteria/"
        "2026-02%20Ordinance%20Adopting%20the%20CWRC%20with%20Local%20"
        "Amendments_RECORDED.pdf?t=202606021136110"
    ),
    "chaffee-electric-ordinance-2026-01-atlas-directed": (
        "https://cms2.revize.com/revize/chaffeecounty/2026-01%20Ordinance%20Chaffee%20"
        "County%20Electric%20Preferred%20Amendments_RECORDED.pdf?t=202608031134050"
    ),
}


class Strict(BaseModel):
    """Reject undeclared fields and coercion."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """An exact package-relative retained file."""
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def safe(cls, value: str) -> str:
        """Forbid path aliases and escapes."""
        p = PurePosixPath(value)
        if (p.is_absolute() or any(x in ('', '.', '..') for x in value.split('/'))
                or "\\" in value or p.as_posix() != value):
            raise ValueError("unsafe asset path")
        return value


class Baseline(Strict):
    """A preserved exact canonical predecessor."""
    repository_path: str
    preserved: Asset
    records: int | None


class Provenance(Strict):
    """Observed acquisition and supplied earlier referrals remain separate."""
    source_id: SourceID
    action_id: Literal['A001', 'A002']
    target_id: Literal['CHAFFEE-D001', 'CHAFFEE-D002']
    authority_id: Literal["CO-COUNTY-CHAFFEE"]
    source: Asset
    response_body: Asset
    physical_pages: int = Field(ge=1)
    parent: Asset
    parent_url: str
    base_href: str
    original_href: str
    visible_label: str
    prior_redirect_notice: Asset
    prior_header_summary: Asset
    original_location: str
    reservation: Asset
    result: Asset
    public_headers: Asset
    curl_writeout: Asset
    requested_url: str
    final_url: str
    http_status: Literal[200]
    http_started_at: AwareDatetime
    http_completed_at: AwareDatetime
    tls_verified: Literal[True]
    redirects_followed: Literal[0]
    original_tool_command_retained: Literal[True]
    acquisition_method: Literal["manual_official_download"]
    actual_repository_received_at: None
    source_content_reviewed_in_this_intake: Literal[False]
    document_role: str
    legal_currentness: Literal["not_verified"]
    limitations: list[str]


class Template(Strict):
    """Prospective final-record values with receipt-only fields unset."""
    record_id: SourceID
    authority_id: Literal["CO-COUNTY-CHAFFEE"]
    layer_id: Literal["08_County_Authorities"]
    official_source_name: str
    official_source_url: str
    acquisition_method: Literal["manual_official_download"]
    source: Asset
    original_filename: str
    custody_note: str
    actual_repository_received_at: None
    intake_id: None
    archive_path: None

    @model_validator(mode="after")
    def identity(self) -> Template:
        """Bind filename and exact source-specific URL, not just a shared host."""
        if PurePosixPath(self.source.path).name != self.original_filename:
            raise ValueError("original_filename differs from actual incoming basename")
        if self.official_source_url != URLS[self.record_id]:
            raise ValueError("source-specific official URL differs")
        return self


class Preparation(Strict):
    """Exactly two custody records on an immutable canonical prefix."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal["PREPARED_NOT_APPLIED"]
    comparison_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    templates: list[Template] = Field(min_length=2, max_length=2)
    provenance: list[Provenance] = Field(min_length=2, max_length=2)
    baseline: list[Baseline]
    runtime_pins: dict[str, str]
    custody_subset: list[Asset]
    retrieval_plan: Asset
    retrieval_manifest: Asset
    deduplication: Asset
    legacy_guard: Asset
    raw_before: int = Field(ge=0)
    ledger_before: int = Field(ge=0)
    raw_after: int = Field(ge=2)
    ledger_after: int = Field(ge=2)
    public_requests: Literal[0]
    canonical_mutations: Literal[0]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]

    @model_validator(mode="after")
    def identities(self) -> Preparation:
        """Reject duplicated, swapped, cross-owner or divergent source records."""
        if len({t.record_id for t in self.templates}) != 2:
            raise ValueError("duplicate source IDs")
        if len({t.source.sha256 for t in self.templates}) != 2:
            raise ValueError("duplicate source digests")
        if [t.record_id for t in self.templates] != list(URLS):
            raise ValueError("selected source order differs")
        if [t.record_id for t in self.templates] != [p.source_id for p in self.provenance]:
            raise ValueError("provenance source order differs")
        for t, p in zip(self.templates, self.provenance):
            if t.source != p.source or p.requested_url != t.official_source_url:
                raise ValueError("provenance source binding differs")
            if p.final_url != p.requested_url or p.http_started_at > p.http_completed_at:
                raise ValueError("acquisition endpoint or chronology differs")
        if self.raw_after != self.raw_before + 2 or self.ledger_after != self.ledger_before + 2:
            raise ValueError("fixed two-source count differs")
        return self


class Manifest(Strict):
    """Closed preparation excludes only its own hash and later execution files."""
    schema_version: Literal[1]
    files: list[Asset]
    scope: Literal["closed_preparation_excluding_future_execution"]


class CommandResult(Strict):
    """An actual offline validation invocation."""
    label: Literal["focused_tests", "live_read_only_preflight"]
    command: list[str]
    working_directory: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    exit_code: Literal[0]
    stdout: Asset
    stderr: Asset


class Validation(Strict):
    """Evidence of preparation checks without canonical application."""
    status: Literal["passed_preparation_only"]
    completed_at: AwareDatetime
    preparation_sha256: str
    transaction_sha256: str
    results: list[CommandResult]
    test_count: int = Field(ge=60)
    combined_branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    coverage: Asset
    canonical_managed_sha256_before: dict[str, str]
    canonical_managed_sha256_after: dict[str, str]
    canonical_managed_bytes_unchanged: Literal[True]
    actual_execution_directory_created: Literal[False]
    limitations: list[str]
