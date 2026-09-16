"""Strict offline preparation records; these do not certify public source availability."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from models import Asset


class Strict(BaseModel):
    """Reject unknown preparation fields and scalar coercion."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Input(Strict):
    """Bind separate working and pinned source metadata bytes."""

    repository_path: str
    working: Asset
    pinned: Asset
    byte_equal: bool


class RegistryEntry(Strict):
    """Preserve the registry object unchanged with its original JSON pointer."""

    json_pointer: str
    record: dict[str, Any]


class Legacy(Strict):
    """Summarize a fully parsed original stream and bind its exact selected lines."""

    edition: str
    repository_path: str
    full_sha256: str
    full_bytes: int
    full_rows: int
    selected: Asset
    selected_rows: int
    original_line_numbers: list[int]
    by_authority: dict[str, int]
    status_counts: dict[str, int]
    url_attempts: dict[str, int]
    source_id_attempts: dict[str, int]
    recorded_sha256s: list[str]
    referenced_local_paths_present: list[str]


class Comparison(Strict):
    """The captured comparison is historical metadata, not a fresh source check."""

    assignment_id: Literal['SH-EXT-003']
    status: Literal['PREPARED_NOT_DISPATCHED']
    captured_at: str
    pinned_commit: str
    observed_head: str
    inputs: list[Input]
    legacy: list[Legacy]
    registry_entries: list[RegistryEntry]
    limitations: list[str]


class Seed(Strict):
    """An exact recorded initial URL; category/title are unverified discovery context."""

    source_id: str
    authority_id: str
    url: str
    registry_json_pointer: str
    priority_purpose: str


class Plan(Strict):
    """A finite proposal that only a separate root dispatch can activate."""

    assignment_id: Literal['SH-EXT-003']
    status: Literal['PREPARED_NOT_DISPATCHED']
    research_cutoff: str
    report_cutoff: str
    seeds: list[Seed]
    max_actions: int
    max_actions_per_county: int
    max_distinct_urls: int
    max_body_bytes: int
    max_total_body_bytes: int
    max_pending_actions: int
    public_actions_by_preparation: Literal[0]
    next_assignment_authorized: Literal[False]
