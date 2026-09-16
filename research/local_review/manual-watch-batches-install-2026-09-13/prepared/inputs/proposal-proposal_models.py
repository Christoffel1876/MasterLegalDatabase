"""Strict models for an offline enrollment proposal; no acquisition or activation code."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, model_validator


class Strict(BaseModel):
    """Reject unknown fields and implicit Python type conversion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Bind a repository-relative metadata file or a declared archived original."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Evidence(Strict):
    """Identify an exact metadata document and, optionally, a zero-based JSONL row."""

    artifact: Ref
    jsonl_row: int | None = Field(default=None, ge=0)
    pointers: list[str]
    scope: str


class Candidate(Strict):
    """Preserve custody, review limits and the proposed exact watch target separately."""

    rank: int = Field(ge=1, le=6)
    record_id: str
    intake_id: str
    authority_id: str
    layer_id: str
    title: str
    baseline: Ref
    baseline_pages: int = Field(ge=1)
    raw_manifest_zero_based_row: int = Field(ge=0)
    raw_manifest_exact_line_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    historical_raw_url: str | None
    historical_acquisition_method: str
    historical_reported_acquisition: dict[str, JsonValue]
    repository_received_at: AwareDatetime
    proposed_url: str
    retained_final_url: str
    http_started_at: AwareDatetime | None
    http_finished_at: AwareDatetime
    http_time_role: str
    recorded_http_status: Literal[200]
    recorded_redirects: Literal[0]
    official_link_basis: str
    official_parent_url: str | None
    official_parent_label: str | None
    authority_evidence: Evidence
    custody_evidence: Evidence
    referral_evidence: list[Evidence]
    review_evidence: Evidence
    review_schema: Ref
    mapped_review_kind: str
    mapped_scope_fields: dict[str, JsonValue]
    recorded_source_roles: dict[str, JsonValue]
    review_limitations: list[str]
    proposal_reason: str
    enrollment_conditions: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    status: Literal["PREPARED_NOT_ACTIVATED"] = "PREPARED_NOT_ACTIVATED"


class Remaining(Strict):
    """Classify one unselected record without claiming a new complete evidence audit."""

    record_id: str
    authority_id: str
    inventory_zero_based_row: int = Field(ge=0)
    baseline: Ref
    review_mapped: bool
    verified_http_mapped: bool
    disposition: Literal[
        "proposed", "verified_custody_deferred", "reviewed_missing_mapped_http",
        "metadata_only_missing_mapped_http",
    ]
    reason: str


class Budget(Strict):
    """Recommend finite limits; this is not a runnable watch configuration."""

    baseline_bytes: int
    baseline_pages: int
    suggested_sub_batches: list[list[str]]
    each_sub_batch_baseline_bytes: list[int]
    maximum_sources_per_sub_batch: Literal[2] = 2
    request_events_per_sub_batch: Literal[4] = 4
    distinct_urls_per_sub_batch: Literal[4] = 4
    same_host_redirects_per_source: Literal[1] = 1
    bytes_per_response_ceiling: Literal[2000000] = 2000000
    total_response_bytes_per_sub_batch: Literal[4000000] = 4000000
    seconds_per_request: Literal[30] = 30
    seconds_per_invocation: Literal[300] = 300
    retries: Literal[0] = 0
    reasoning: str


class Proposal(Strict):
    """Bind six proposals and all 59 unselected inventory dispositions."""

    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    status: Literal["PREPARED_NOT_ACTIVATED"] = "PREPARED_NOT_ACTIVATED"
    input_pins: dict[str, Ref]
    metadata_evidence_pins: list[Ref]
    currently_selected: list[str] = Field(min_length=2, max_length=2)
    inventory_records: Literal[61] = 61
    inventory_mapped_reviews: Literal[21] = 21
    unselected_records: Literal[59] = 59
    candidates: list[Candidate] = Field(min_length=6, max_length=6)
    remaining: list[Remaining] = Field(min_length=59, max_length=59)
    partition_counts: dict[str, int]
    budget: Budget
    activation_gates: list[str]
    edition_discovery_gap: list[str]
    inspection_scope: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    public_requests: Literal[0] = 0
    production_writes: Literal[0] = 0

    @model_validator(mode="after")
    def coherent(self) -> "Proposal":
        """Reject duplicated, omitted or inconsistent source and budget claims."""
        ids = [x.record_id for x in self.candidates]
        remaining = [x.record_id for x in self.remaining]
        if len(set(ids)) != 6 or len(set(remaining)) != 59:
            raise ValueError("Duplicate source identity")
        if set(ids) & set(self.currently_selected):
            raise ValueError("Proposals must be additional sources")
        counts = {key: sum(x.disposition == key for x in self.remaining)
                  for key in self.partition_counts}
        if counts != self.partition_counts or sum(counts.values()) != 59:
            raise ValueError("Unselected partition mismatch")
        if set(ids) != {x.record_id for x in self.remaining if x.disposition == "proposed"}:
            raise ValueError("Proposed partition mismatch")
        if self.budget.baseline_bytes != sum(x.baseline.size_bytes for x in self.candidates):
            raise ValueError("Baseline bytes mismatch")
        if self.budget.baseline_pages != sum(x.baseline_pages for x in self.candidates):
            raise ValueError("Baseline pages mismatch")
        groups = self.budget.suggested_sub_batches
        if sorted(sum(groups, [])) != sorted(ids) or any(len(x) != 2 for x in groups):
            raise ValueError("Sub-batch membership mismatch")
        by_id = {x.record_id: x.baseline.size_bytes for x in self.candidates}
        if [sum(by_id[x] for x in group) for group in groups] != (
            self.budget.each_sub_batch_baseline_bytes
        ):
            raise ValueError("Sub-batch bytes mismatch")
        return self


class FinalManifest(Strict):
    """Close the proposal's local metadata payloads without claiming original PDF custody."""

    schema_version: Literal[1] = 1
    status: Literal["PREPARED_NOT_ACTIVATED"] = "PREPARED_NOT_ACTIVATED"
    files: list[Ref]
    scope: Literal["offline_planning_metadata_only"] = "offline_planning_metadata_only"
    legal_currentness: Literal["not_verified"] = "not_verified"

    @model_validator(mode="after")
    def unique(self) -> "FinalManifest":
        """Reject repeated payload names."""
        if len({x.path for x in self.files}) != len(self.files):
            raise ValueError("Repeated manifest path")
        return self
