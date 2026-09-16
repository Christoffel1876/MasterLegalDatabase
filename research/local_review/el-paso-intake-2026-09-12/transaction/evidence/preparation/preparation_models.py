"""Strict, non-operative records for the bounded El Paso custody proposal."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Strict(BaseModel):
    """Reject unknown fields and implicit scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Bind one exact ordinary file relative to this package."""

    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)


class Copy(Strict):
    """Record a copied input without certifying its upstream acquisition."""

    original_path: str
    original_sha256: SHA
    preserved: Asset
    method: Literal["exact_copy", "audited_public_header_derivative"]
    excluded_raw_header_sha256: SHA | None = None


class Page(Strict):
    """Bind a fully viewed page image and its uncorrected native extraction."""

    physical_page: int = Field(ge=1)
    image: Asset
    native: Asset
    native_nonwhitespace: bool
    view_scope: Literal["full_page_for_title_issuer_role_and_selected_date_context"]
    numeric_table_certification: Literal[False]


class Span(Strict):
    """Locate an exact UTF-8 substring; this is not corrected native text."""

    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str
    sha256: SHA


class Observation(Strict):
    """Record bounded image-supported wording and extraction limitations."""

    observation_id: str
    physical_page: int = Field(ge=1)
    region: str
    visible_text: str
    native_anchor: Span | None
    conclusion: str
    uncertainty: str
    legal_currentness: Literal["not_verified"]


class DateClaim(Strict):
    """Keep a source-stated date separate from legal effect or collection time."""

    value: str
    role: Literal[
        "source_stated_effective", "source_stated_approval", "recording_stamp",
        "unlabeled_cover_date", "source_stated_execution", "document_footer_date",
    ]
    observation_id: str
    independently_verified: Literal[False]


class Referral(Strict):
    """Keep the exact preserved public HTML anchor and audited response context."""

    event_id: str
    parent_url: str
    parent: Asset
    href: str
    resolved_url: str
    anchor_text: str


class Source(Strict):
    """Propose or defer ownership using direct document evidence."""

    source_id: str
    decision: Literal["propose_county_intake", "defer_issuer_layer_decision"]
    authority_id: Literal["CO-COUNTY-EL_PASO"] | None
    layer_id: Literal["08_County_Authorities"] | None
    issuer_as_shown: str
    issuer_kind: Literal[
        "county_department", "county_board_of_commissioners", "county_board_of_health",
        "unresolved_school_fee_issuer", "colorado_geological_survey",
    ]
    document_role: str
    title_for_intake: str
    language: Literal["en", "es"]
    original: Asset
    received_body_path: str
    source_pages: int = Field(ge=1)
    event_id: str
    requested_url_claim: str
    final_url_claim: str
    acquisition_started_at_claim: AwareDatetime
    acquisition_completed_at_claim: AwareDatetime
    upstream_acquisition_independently_verified: Literal[False]
    verified_http_acquired_at: None
    atlas_delivery_captured_at: AwareDatetime
    atlas_preparation_copied_at: AwareDatetime
    actual_repository_received_at: None
    public_headers: Asset
    observed_http_statuses: list[int]
    observed_redirect_destinations: list[str]
    source_referrals: list[Referral]
    referral_basis: Literal["preserved_official_html_anchor", "inherited_url_no_fresh_anchor"]
    historical_matching_rows: int = Field(ge=0)
    historical_source_ids: list[str]
    directly_viewed_pages: list[Page] = Field(min_length=1)
    observations: list[Observation] = Field(min_length=1)
    date_claims: list[DateClaim]
    verified_adoption_date: None
    verified_effective_date: None
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    translation_equivalence_verified: Literal[False]
    full_text_reviewed: Literal[False]
    qualifications: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def ownership_and_extent(self) -> Source:
        """Prevent an excluded issuer or unchecked page from entering county intake."""
        included = self.decision == "propose_county_intake"
        if included != (self.authority_id is not None and self.layer_id is not None):
            raise ValueError("Decision and explicit county identity disagree")
        if included == self.issuer_kind.startswith(("unresolved_", "colorado_")):
            raise ValueError("Excluded issuer cannot become county authority")
        pages = [p.physical_page for p in self.directly_viewed_pages]
        if pages != sorted(set(pages)) or pages[0] != 1 or max(pages) > self.source_pages:
            raise ValueError("Invalid direct visual page scope")
        obs = [o.observation_id for o in self.observations]
        if len(set(obs)) != len(obs):
            raise ValueError("Duplicate observation identity")
        if any(o.physical_page not in pages for o in self.observations):
            raise ValueError("Observation exceeds visual scope")
        if any(d.observation_id not in obs for d in self.date_claims):
            raise ValueError("Date lacks a checked source observation")
        return self


class RecordTemplate(Strict):
    """Hold only known final-record fields; execution fields must remain null."""

    record_id: str
    layer_id: Literal["08_County_Authorities"]
    official_source_name: str
    official_source_url: str
    acquisition_method: Literal["received_review_package"]
    received_from: str
    reviewer_name: str
    reviewer_email: None
    custody_note: str
    source_file: Asset
    expected_sha256: SHA
    source_format: Literal["pdf"]
    size_bytes: int = Field(ge=1)
    allow_duplicate: Literal[False]
    intake_id: None
    archive_path: None
    received_at: None
    status: Literal["proposed_not_applied"]
    intended_record_status: Literal["archived_pending_pipeline"]
    legal_currentness: Literal["not_verified"]


class Baseline(Strict):
    """Bind a repository preimage without changing or reserializing it."""

    repository_path: str
    preserved: Asset
    records: int | None = Field(ge=0)


class Dedupe(Strict):
    """Record exact existing manual rows and a bounded ordinary-raw-file screen."""

    checked_at: AwareDatetime
    raw_records: int = Field(ge=0)
    ledger_records: int = Field(ge=0)
    ordinary_raw_files_screened: int = Field(ge=0)
    symlinks_skipped: list[str]
    candidate_size_files_hashed: list[Asset]
    source_id_matches: list[str]
    raw_manifest_digest_matches: list[str]
    ledger_digest_matches: list[str]
    ordinary_raw_digest_matches: list[str]
    boundary: str


class Preparation(Strict):
    """Fixed fifteen-source review and thirteen-source unexecuted proposal."""

    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal["prepared_not_applied"]
    apply_available: Literal[False]
    audit: Asset
    audit_sha256: Literal["a6e5befb2cd424a6a0c9f072075bab3abd1f78849495b91b4ca0194064d377f0"]
    comparison_commit: Literal["0a3ba27aaf5358141efb5af2c33c3a6b9043d099"]
    baseline: list[Baseline]
    dedupe: Dedupe
    sources: list[Source] = Field(min_length=15, max_length=15)
    proposed_records: list[RecordTemplate] = Field(min_length=13, max_length=13)
    custody: list[Copy]
    source_structural_pages: Literal[351]
    directly_viewed_pages: Literal[20]
    full_numeric_table_reviews: Literal[0]
    public_events_during_preparation: Literal[0]
    upstream_public_events: Literal[66]
    upstream_distinct_targets: Literal[66]
    upstream_distinct_target_cap: Literal[50]
    upstream_cap_status: Literal["failed"]
    upstream_missing_body_sha256: list[SHA] = Field(min_length=2, max_length=2)
    original_acquisition_certified: Literal[False]
    legal_currentness: Literal["not_verified"]
    production_mutations: Literal[0]
    limitations: list[str]

    @model_validator(mode="after")
    def fixed_join(self) -> Preparation:
        """Require exact one-to-one proposed records and independently bounded review scope."""
        ids = [s.source_id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate source ID")
        proposed = [s for s in self.sources if s.decision == "propose_county_intake"]
        if [s.source_id for s in proposed] != [r.record_id for r in self.proposed_records]:
            raise ValueError("Proposal records do not match source decisions")
        for s, r in zip(proposed, self.proposed_records, strict=True):
            if (r.expected_sha256 != s.original.sha256 or r.source_file != s.original
                    or r.official_source_name != s.title_for_intake
                    or r.official_source_url != s.requested_url_claim
                    or r.size_bytes != s.original.size_bytes):
                raise ValueError("Intake template loses identity, bytes, title or URL")
        if sum(len(s.directly_viewed_pages) for s in self.sources) != 20:
            raise ValueError("Visual page count differs from actual recorded scope")
        if sum(s.source_pages for s in self.sources) != 351:
            raise ValueError("Structural page count changed")
        return self


class Inventory(Strict):
    """Close this handoff package without adding repository or legal claims."""

    schema_version: Literal[1]
    frozen_at: AwareDatetime
    files: list[Asset]
    exclusions: Literal["FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"] | list[str]
