"""Typed, read-only expectations and intake review records for two preserved PDFs."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unknown fields and implicit Python coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Pin an evidence file's exact bytes."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Source(Strict):
    """Keep source ownership, transport and accepted review scope distinct."""

    canonical_id: str
    historical_review_id: str
    authority_id: str
    layer_id: str
    source: Ref
    page_count: int
    parent_url: str
    parent_anchor_label: str
    parent: Ref
    observed_href: str
    initial_pdf_url: str
    final_pdf_url: str
    redirect_count: int
    acquisition_started_at: AwareDatetime
    acquisition_finished_at: AwareDatetime
    events: list[Ref]
    accepted_review: Ref
    accepted_schema: Ref
    acceptance: Ref
    full_images_directly_viewed: list[Ref]
    expected_review_kind: Literal["checked_tables"] = "checked_tables"
    review_scope: list[str]
    required_qualifications: list[str]
    actual_repository_received_at: None = None
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Comparison(Strict):
    """Record an exact equality search without claiming global novelty."""

    input_file: Ref
    rows_read: int | None
    exact_matches: list[str]


class Expectations(Strict):
    """Freeze independent expectations before opening another agent's preparation."""

    schema_version: Literal[1] = 1
    frozen_at: AwareDatetime
    preparation_read_before_freeze: Literal[False] = False
    sources: list[Source] = Field(min_length=2, max_length=2)
    exact_compared_values: list[str]
    comparisons: list[Comparison]
    validator_results: list[str]
    limitations: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"


class FinalReview(Strict):
    """Record the later preparation comparison without rewriting the frozen expectations."""

    schema_version: Literal[1] = 1
    completed_at: AwareDatetime
    expectations: Ref
    preparation_files: list[Ref]
    status: Literal["no_blocker_in_reviewed_scope", "changes_required", "preparation_not_ready"]
    checks: list[str]
    actionable_findings: list[str]
    required_qualifications: list[str]
    no_production_write: Literal[True] = True
    no_public_request: Literal[True] = True
    legal_currentness: Literal["not_verified"] = "not_verified"


class ReadOnlyCheck(Strict):
    """Keep the exact command, timestamps and unchanged-file observations."""

    command: list[str]
    cwd: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    returncode: Literal[0]
    before: list[Ref]
    after: list[Ref]
    monitored_files_unchanged: Literal[True]
    execution_directory_created: Literal[False]
    public_requests: Literal[0]
    production_writes: Literal[0]


class Manifest(Strict):
    """Close this independent review to a fixed set of ordinary payload files."""

    schema_version: Literal[1] = 1
    frozen_at: AwareDatetime
    files: list[Ref]
    legal_currentness: Literal["not_verified"] = "not_verified"
