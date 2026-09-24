"""Strict session-only freshness evidence, with no legal promotion."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unknown fields and coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Pin(Strict):
    """Exact artifact identity; a web derivative is not a source original."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Event(Strict):
    """Deliberate web-tool action and observed representation limits."""

    event_id: str
    operation: Literal["open", "click"]
    requested_url: str
    reported_final_url: str
    interval_start: str
    interval_end: str
    interval_role: Literal["tool_batch_wall_clock_not_http_timing"]
    representation: Literal["web_tool_parsed_page"]
    evidence: Pin
    original_http_status: None = None
    original_source_sha256: None = None
    source_original_retained: Literal[False] = False


class Candidate(Strict):
    """A bounded research lead, distinct from an admitted legal record."""

    candidate_id: str
    source_owner: str
    source_url: str
    possible_layer: str
    discovered_date: str
    change_type: Literal["new", "amended", "repealed", "corrected", "unknown"]
    reason_for_review: str
    status: Literal["needs_validation", "queued", "processed", "rejected", "duplicate"]
    confidence: float = Field(ge=0, le=1)
    confidence_scope: Literal["catalog_identity_only_not_legal_effect"]
    authority_id: str
    observed_label: str
    event_ids: list[str]
    adoption_date: None = None
    effective_date: None = None
    original_sha256: None = None
    document_url: None = None
    local_comparison: str
    next_step: str
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Queue(Strict):
    """Nonactivated handoff-only candidate proposal."""

    schema_version: Literal[1] = 1
    canonical_queue_changed: Literal[False] = False
    activated: Literal[False] = False
    candidates: list[Candidate]


class Comparison(Strict):
    """Recount over explicitly pinned tracked metadata, not raw bodies."""

    input: Pin
    row_count: int = Field(ge=0)
    representation: Literal["jsonl_records", "json_document", "lfs_pointer"]
    matches: dict[str, list[str]]
    qualification: str


class Report(Strict):
    """Session freshness report implementing the repository policy contract."""

    schema_version: Literal[1] = 1
    report_id: str
    session_date: str
    prepared_at: str
    baseline_commit: str
    search_completed: Literal[True] = True
    sources_checked: list[Event]
    candidates: list[Candidate]
    controls: list[Pin]
    comparisons: list[Comparison]
    public_action_count: int = Field(ge=0, le=10)
    public_action_limit: Literal[10] = 10
    findings: list[str]
    unchecked_scope: list[str]
    limitations: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    canonical_changed: Literal[False] = False


class Manifest(Strict):
    """Closed inventory excluding only this self-referential manifest."""

    schema_version: Literal[1] = 1
    excluded: list[str]
    files: list[Pin]
