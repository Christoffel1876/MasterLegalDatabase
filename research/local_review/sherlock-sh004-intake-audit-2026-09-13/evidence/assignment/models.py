"""Typed reporting templates for a finite public tool-action discovery assignment."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Authority = Literal["CO-COUNTY-CHAFFEE"]
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

    action_id: str = Field(pattern=r"^SHEXT004-A[0-9]{3}$")
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

    action_id: str = Field(pattern=r"^SHEXT004-A[0-9]{3}$")
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
    body_size_basis: Literal["retained_complete", "retained_partial", "no_body_observed",
                             "unknown"] = "unknown"
    observed_body_bytes: int | None = Field(default=None, ge=0)

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
        if self.body_size_basis == "no_body_observed":
            if self.observed_body_bytes != 0 or self.body_sha256 is not None:
                raise ValueError("No-body observation must be zero without a body hash")
        elif self.body_size_basis.startswith("retained_"):
            matches = [a for a in self.retained_assets if a.sha256 == self.body_sha256]
            if not matches or any(a.size_bytes != self.observed_body_bytes for a in matches):
                raise ValueError("Measured body length must match its retained asset")
        elif self.observed_body_bytes is not None:
            raise ValueError("Unknown body length must remain null")
        return self


class ActionLog(Strict):
    """Validate finite visible-tool budgets, not hidden network requests or timing claims."""

    assignment_id: Literal["SH-EXT-004"] = "SH-EXT-004"
    reservations: list[Reservation] = Field(max_length=4)
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
        if len(self.reservations) + extra_hops > 4:
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
        if sum(body_sizes) > 60_000_000:
            raise ValueError("Total retained response-body byte cap exceeded")
        if len(urls) > 4:
            raise ValueError("Distinct requested URL cap exceeded")
        for authority in ["CO-COUNTY-CHAFFEE", "CO-COUNTY-GUNNISON"]:
            charged = sum(r.authority_id == authority for r in self.reservations)
            charged += sum(len(r.visible_redirect_urls) for r in self.results
                           if by_id[r.action_id].authority_id == authority)
            if charged > 4:
                raise ValueError("Authority tool-action cap exceeded")
        if len(self.reservations) > len(self.results) + 1:
            raise ValueError("Only one unfinished public action is allowed")
        if ids and results != ids[:len(results)]:
            raise ValueError("Results must close the serial reservation prefix")
        return self
