"""Explicit ownership exclusions for historical local-source regeneration."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator, Mapping
from functools import cached_property
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urldefrag

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator

POLICY_PATH = Path("_CONTROL_PLANE/LOCAL_SOURCE_OWNERSHIP_CORRECTIONS.json")


class OwnershipReplacement(BaseModel):
    """One explicitly retired source identity and its observed owner."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    retired_source_id: str = Field(min_length=1)
    historical_authority_id: str = Field(min_length=1)
    observed_owner_id: str = Field(min_length=1)
    source_url: HttpUrl
    role: str = Field(min_length=1)
    current_registry_source_id: str | None
    disposition: str = Field(pattern=r"^retired_")
    historical_entry: dict[str, Any]
    evidence_location: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_history(self) -> OwnershipReplacement:
        """Require the retirement to identify the preserved historical entry."""
        for key, expected in (
            ("source_id", self.retired_source_id),
            ("authority_id", self.historical_authority_id),
        ):
            if self.historical_entry.get(key) != expected:
                raise ValueError(f"ownership correction contradicts historical {key}")
        if _url(self.historical_entry.get("url")) != _url(self.source_url):
            raise ValueError("ownership correction contradicts historical URL")
        if self.observed_owner_id == self.historical_authority_id:
            raise ValueError("ownership correction must identify a different observed owner")
        return self


class OwnershipMapping(BaseModel):
    """An explicitly affected candidate-to-permanent-unit mapping."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    review_id: str = Field(min_length=1)
    candidate_rule_unit_id: str = Field(min_length=1)
    permanent_rule_unit_id: str = Field(min_length=1)
    parent_regulation_id: str = Field(min_length=1)
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_section: str = Field(min_length=1)
    mapping_status: str = Field(min_length=1)
    mapping_reason: str = Field(min_length=1)


class OwnershipPolicy(BaseModel):
    """Validated exclusions; matching never transfers ownership or legal status."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    attribution_review: str
    legal_currentness: Literal["not_verified"]
    pipeline_enforcement: str
    replacements: tuple[OwnershipReplacement, ...] = Field(min_length=1)
    new_county_identity_source: dict[str, Any]
    affected_legacy_download_rows: int = Field(ge=0)
    affected_parent_rule_ids: tuple[str, ...]
    affected_review_ids: tuple[str, ...]
    affected_candidate_mappings: tuple[OwnershipMapping, ...]
    input_sha256: dict[str, str]
    preserved_historical_files: tuple[str, ...]
    required_followup: tuple[str, ...]
    verification_method: str
    policy_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def consistent_exclusions(self) -> OwnershipPolicy:
        """Reject duplicate identities and mappings outside the declared affected set."""
        for values in (
            [row.retired_source_id for row in self.replacements],
            self.affected_parent_rule_ids,
            self.affected_review_ids,
            [row.review_id for row in self.affected_candidate_mappings],
        ):
            if len(values) != len(set(values)) or any(not value for value in values):
                raise ValueError("ownership exclusions contain duplicate or empty identities")
        for row in self.affected_candidate_mappings:
            if row.parent_regulation_id not in self.affected_parent_rule_ids:
                raise ValueError("affected mapping has an undeclared parent")
            if row.review_id not in self.affected_review_ids:
                raise ValueError("affected mapping has an undeclared review")
        if any(not re.fullmatch(r"[a-f0-9]{64}", value) for value in self.input_sha256.values()):
            raise ValueError("ownership input hashes must be SHA-256")
        return self

    @cached_property
    def retired_source_ids(self) -> frozenset[str]:
        """Return the exact retired source identifiers."""
        return frozenset(row.retired_source_id for row in self.replacements)

    @cached_property
    def _authority_urls(self) -> frozenset[tuple[str, str]]:
        return frozenset(
            (row.historical_authority_id, _url(row.source_url)) for row in self.replacements
        )

    @cached_property
    def _entity_ids(self) -> frozenset[str]:
        return frozenset([
            *self.affected_parent_rule_ids,
            *self.affected_review_ids,
            *(row.candidate_rule_unit_id for row in self.affected_candidate_mappings),
            *(row.permanent_rule_unit_id for row in self.affected_candidate_mappings),
        ])

    def source_exclusion_reason(self, row: Mapping[str, Any]) -> str | None:
        """Return a retirement reason for an exact source ID or authority/URL pair."""
        source_id = str(row.get("source_id") or "")
        if source_id in self.retired_source_ids:
            return f"retired source ownership: {source_id}"
        authority = str(row.get("authority_id") or "")
        for key in ("url", "source_url", "requested_url", "final_url", "discovery_parent_url"):
            url = _url(row.get(key))
            if (authority, url) in self._authority_urls:
                return f"retired authority/URL attribution: {authority} {url}"
        return None

    def entity_exclusion_reason(self, row: Mapping[str, Any]) -> str | None:
        """Return a source or explicitly linked parent/review/unit exclusion reason."""
        for item in _nested_rows(row):
            reason = self._entity_reason(item)
            if reason:
                return reason
        return None

    def _entity_reason(self, row: Mapping[str, Any]) -> str | None:
        reason = self.source_exclusion_reason(row)
        if reason:
            return reason
        for key in (
            "id", "parent_rule_id", "parent_regulation_id", "review_id", "rule_unit_id",
            "candidate_rule_unit_id", "permanent_rule_unit_id",
        ):
            identity = str(row.get(key) or "").removeprefix("CONDITIONAL-")
            if identity in self._entity_ids:
                return f"affected ownership identity: {identity}"
            parent = re.sub(r"(?:-UNIT-|_RU_)\d+$", "", identity.removeprefix("COUNTY-SEM-"))
            if parent != identity and parent in self.affected_parent_rule_ids:
                return f"unit of affected ownership parent: {parent}"
        return None


def _nested_rows(row: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
    """Visit explicit source/candidate metadata without following arbitrary data or cycles."""
    pending = [(row, str(row.get("authority_id") or ""))]
    seen: set[int] = set()
    while pending:
        item, authority = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        authority = str(item.get("authority_id") or authority)
        yield {**item, "authority_id": authority}
        for key in ("candidate_rule_unit", "source", "source_metadata", "metadata"):
            child = item.get(key)
            if isinstance(child, Mapping):
                pending.append((child, authority))


def requires_ownership_policy(row: Mapping[str, Any]) -> bool:
    """Identify local pipeline inputs; this trigger never itself excludes a record."""
    for item in _nested_rows(row):
        if str(item.get("authority_level") or "").lower() in {"county", "municipal", "district"}:
            return True
        if str(item.get("authority_id") or "").startswith(
            ("CO-COUNTY-", "CO-MUNICIPAL-", "CO-DISTRICT-")
        ):
            return True
        if any(str(item.get(key) or "").startswith(("08_", "09_", "10_"))
               for key in ("layer", "layer_id")):
            return True
        if any(str(item.get(key) or "").startswith(
            ("LOCAL-", "CONDITIONAL-", "COUNTY-SEM-", "CO-COUNTY-", "CO-MUNICIPAL-", "CO-DISTRICT-")
        ) for key in (
            "id", "rule_unit_id", "parent_rule_id", "parent_regulation_id", "review_id",
            "candidate_rule_unit_id", "permanent_rule_unit_id",
        )):
            return True
        if str(item.get("source_id") or "").startswith(("county_", "municipal_", "district_")):
            return True
    return False


def _url(value: object) -> str:
    """Normalize URL syntax and discard fragments, retaining path/query distinctions."""
    if not value:
        return ""
    try:
        return urldefrag(str(HttpUrl(str(value))))[0]
    except ValueError:
        return ""


def load_ownership_policy(root: Path) -> OwnershipPolicy:
    """Load required ownership evidence before legacy collection or derived writes."""
    path = root / POLICY_PATH
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("ownership policy path must not contain symlinks")
    content = path.read_bytes()
    policy = OwnershipPolicy.model_validate_json(content)
    return policy.model_copy(update={"policy_sha256": hashlib.sha256(content).hexdigest()})
