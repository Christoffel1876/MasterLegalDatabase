"""Typed reporting templates for a finite public tool-action discovery assignment."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Authority = Literal["CO-COUNTY-CHAFFEE", "CO-COUNTY-GUNNISON"]
Category = Literal["identity_service_area", "codified_rules", "adopted_changes",
    "land_use_zoning", "building_fire", "permits_licenses", "fees", "taxes",
    "health_environment", "roads_utilities", "enforcement_appeals", "policies_guidance"]


class Strict(BaseModel):
    """Reject undeclared fields and scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """An exact retained body, derivative or report."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Reservation(Strict):
    """Persist before a single public tool action; this is not a wire-request counter."""

    action_id: str = Field(pattern=r"^SHEXT003-A[0-9]{3}$")
    authority_id: Authority
    reserved_at: AwareDatetime
    tool_name: str
    action_kind: Literal["open", "download", "search", "browser_navigation", "browser_click"]
    requested_url: str | None
    search_query: str | None = None
    basis: str
    budget_checked: Literal[True]

    @model_validator(mode="after")
    def target(self) -> Reservation:
        """Require one target or one search query, never a batched public call."""
        if self.action_kind == "search":
            if self.requested_url is not None or not self.search_query:
                raise ValueError("A search reserves exactly one query")
        elif not self.requested_url or self.search_query is not None:
            raise ValueError("An open reserves exactly one requested URL")
        if self.requested_url and not self.requested_url.startswith("https://"):
            raise ValueError("Only ordinary HTTPS public targets are authorized")
        return self


class Result(Strict):
    """Record actual observations separately from the immutable reservation."""

    action_id: str = Field(pattern=r"^SHEXT003-A[0-9]{3}$")
    finished_at: AwareDatetime | None
    time_unknown_reason: str | None = None
    observed_final_url: str | None
    visible_redirect_urls: list[str]
    observed_http_status: int | None = Field(default=None, ge=100, le=599)
    outcome: Literal["response", "access_denied", "not_found", "tool_preflight_error",
                     "transport_error", "unretained_response", "unknown"]
    body_role: Literal["original_pdf", "original_html", "error_body", "browser_derivative",
                       "tool_derivative", "no_body", "unknown"]
    retained_assets: list[Asset]
    body_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    pdf_magic_checked: bool
    pdf_parse_succeeded: bool
    physical_pages: int | None = Field(default=None, ge=1)
    notes: str
    source_qa_status: Literal["not_performed"] = "not_performed"

    @model_validator(mode="after")
    def evidence(self) -> Result:
        """A parsed original PDF requires measured bytes; parsing is not complete source QA."""
        if self.finished_at is None and not self.time_unknown_reason:
            raise ValueError("Unknown timing needs a reason")
        if self.pdf_parse_succeeded and (
            self.body_role != "original_pdf" or not self.pdf_magic_checked or
            not self.body_sha256 or self.physical_pages is None
        ):
            raise ValueError("PDF structure requires actual original evidence")
        if self.body_sha256 and self.body_sha256 not in {a.sha256 for a in self.retained_assets}:
            raise ValueError("Reported body hash is not retained")
        return self


class ActionLog(Strict):
    """Validate finite visible-tool budgets, not hidden network requests or timing claims."""

    assignment_id: Literal["SH-EXT-003"] = "SH-EXT-003"
    reservations: list[Reservation] = Field(max_length=40)
    results: list[Result]
    hidden_network_requests_measured: Literal[False] = False

    @model_validator(mode="after")
    def budget(self) -> ActionLog:
        """Reject duplicate, unreserved and over-budget recorded public actions."""
        ids = [r.action_id for r in self.reservations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate reservation ID")
        results = [r.action_id for r in self.results]
        if len(results) != len(set(results)) or set(results) - set(ids):
            raise ValueError("Unreserved or duplicate result")
        # Each automatically observed hop is additionally charged; manually followed hops
        # instead receive their own reservation and must not be listed here a second time.
        by_id = {r.action_id: r for r in self.reservations}
        extra_hops = sum(len(r.visible_redirect_urls) for r in self.results)
        if len(self.reservations) + extra_hops > 40:
            raise ValueError("Visible redirect action cap exceeded")
        urls = {r.requested_url for r in self.reservations if r.requested_url}
        urls.update(url for result in self.results for url in result.visible_redirect_urls)
        body_sizes = []
        for result in self.results:
            if result.body_sha256:
                matches = [a for a in result.retained_assets if a.sha256 == result.body_sha256]
                sizes = {a.size_bytes for a in matches}
                if len(sizes) != 1:
                    raise ValueError("Conflicting byte lengths for the same body hash")
                body_sizes.append(next(iter(sizes)))
        if any(size > 20_000_000 for size in body_sizes):
            raise ValueError("Per-body byte cap exceeded")
        if sum(body_sizes) > 80_000_000:
            raise ValueError("Total retained response-body byte cap exceeded")
        if len(urls) > 30:
            raise ValueError("Distinct requested URL cap exceeded")
        for authority in ["CO-COUNTY-CHAFFEE", "CO-COUNTY-GUNNISON"]:
            charged = sum(r.authority_id == authority for r in self.reservations)
            charged += sum(len(r.visible_redirect_urls) for r in self.results
                           if by_id[r.action_id].authority_id == authority)
            if charged > 20:
                raise ValueError("Authority tool-action cap exceeded")
        if len(self.reservations) > len(self.results) + 1:
            raise ValueError("Only one unfinished public action is allowed")
        if ids and results != ids[:len(results)]:
            raise ValueError("Results must close the serial reservation prefix")
        return self


class ChecklistRow(Strict):
    """One category/authority row with explicit bounded-search status."""

    authority_id: Authority
    category: Category
    status: Literal["candidate_found", "searched_not_found", "access_blocked", "not_searched"]
    action_ids: list[str]
    candidate_ids: list[str]
    notes: str
    legal_currentness: Literal["not_verified"] = "not_verified"


class Checklist(Strict):
    """Require all24 different authority/category combinations without implying complete coverage."""

    assignment_id: Literal["SH-EXT-003"] = "SH-EXT-003"
    rows: list[ChecklistRow] = Field(min_length=24, max_length=24)

    @model_validator(mode="after")
    def combinations(self) -> Checklist:
        """Reject duplicate checklist rows."""
        if len({(r.authority_id, r.category) for r in self.rows}) != 24:
            raise ValueError("Checklist combinations differ")
        return self


class DateClaim(Strict):
    """Keep source wording and date role separate from acquisition or legal effect."""

    role: Literal["adoption", "effective", "revision", "publication", "posting", "recording",
                  "filename", "unknown"]
    printed_text: str
    evidence_location: str
    independently_verified_legal_effect: Literal[False] = False


class Priority(Strict):
    """One exact document or explicitly labeled catalog; do not bundle multiple instruments."""

    candidate_id: str = Field(pattern=r"^SHEXT003-(0[1-9]|1[0-6])$")
    authority_id: Authority
    title_as_observed: str
    requested_url: str
    observed_final_url: str | None
    role: Literal["adopted_instrument_as_stated", "proposed_instrument", "agenda_attachment",
                  "codified_text", "fee_schedule", "guidance", "form", "catalog", "unknown"]
    ownership_evidence: str
    official_referral_evidence: str
    action_ids: list[str]
    categories: list[Category]
    original_body: Asset | None
    physical_pages: int | None = Field(default=None, ge=1)
    date_claims: list[DateClaim]
    legacy_comparison: str
    remaining_gaps: list[str]
    review_status: Literal["pending_intake"] = "pending_intake"
    legal_currentness: Literal["not_verified"] = "not_verified"


class Priorities(Strict):
    """Limit the source priority queue independently of the24-category checklist."""

    assignment_id: Literal["SH-EXT-003"] = "SH-EXT-003"
    priorities: list[Priority] = Field(max_length=16)

    @model_validator(mode="after")
    def capped(self) -> Priorities:
        """Each of the two authorities receives at most eight distinct priorities."""
        ids = [p.candidate_id for p in self.priorities]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate priority ID")
        for authority in ["CO-COUNTY-CHAFFEE", "CO-COUNTY-GUNNISON"]:
            if sum(p.authority_id == authority for p in self.priorities) > 8:
                raise ValueError("Authority priority cap exceeded")
        return self


class BacklogEntry(Strict):
    """A discovered source that was not opened in this assignment."""

    authority_id: Authority
    url: str
    discovered_from: str
    reason_not_opened: str
    status: Literal["discovered_not_opened"] = "discovered_not_opened"


class Backlog(Strict):
    """Preserve deferred leads separately from attempts and collected source claims."""

    assignment_id: Literal["SH-EXT-003"] = "SH-EXT-003"
    entries: list[BacklogEntry]


class ArtifactInventory(Strict):
    """A delivery's exact retained files; independent closure verification remains Atlas work."""

    assignment_id: Literal["SH-EXT-003"] = "SH-EXT-003"
    files: list[Asset]
    status: Literal["completed_pending_atlas_verification", "partial_pending_atlas_verification"]
    legal_currentness: Literal["not_verified"] = "not_verified"

    @model_validator(mode="after")
    def unique(self) -> ArtifactInventory:
        """Disallow repeated body/report paths in the delivered inventory."""
        names = [ref.path for ref in self.files]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate artifact path")
        return self
