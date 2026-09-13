"""Strict immutable preparation metadata; no execution outcome is implied."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from models import Asset


class Preparation(BaseModel):
    """A finite procedure waiting for root's final scan and dispatch."""

    model_config = ConfigDict(extra='forbid', strict=True)
    status: Literal['PREPARED_NOT_EXECUTED']
    recorded_at: AwareDatetime
    files: list[Asset]
    final_scan_sha256: None
    final_scan_schema_sha256: None
    actual_exports: Literal[0]
    git_mutations: Literal[0]
    public_requests: Literal[0]
    fixture_tests_passed: Literal[23]
    limits: list[str]
    pending: list[str]


class Manifest(BaseModel):
    """Closed preparation payload inventory."""

    model_config = ConfigDict(extra='forbid', strict=True)
    recorded_at: AwareDatetime
    status: Literal['frozen_prepared_procedure_not_executed']
    files: list[Asset]
