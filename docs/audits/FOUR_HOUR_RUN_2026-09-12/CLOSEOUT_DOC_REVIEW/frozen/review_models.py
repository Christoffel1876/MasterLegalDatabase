"""Strict metadata schema for a bounded, offline documentation closeout review."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject unexpected fields and implicit conversion in Python input."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Bind the precise file version read for this documentation review."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Check(Strict):
    """Record an executed offline check or explicitly static source inspection."""

    check_id: str
    method: Literal["executed_offline", "static_read_only"]
    command_or_scope: str
    exit_code: int | None
    result: str
    limits: str


class Review(Strict):
    """Keep scoped acceptance separate from claims of overall project readiness."""

    schema_version: Literal[1] = 1
    recorded_at: AwareDatetime
    status: Literal["scoped_no_actionable_findings"] = "scoped_no_actionable_findings"
    reviewed_files: list[Ref]
    supporting_metadata: list[Ref]
    checks: list[Check]
    actionable_findings: list[str] = Field(max_length=0)
    qualifications: list[str]
    production_writes: Literal[0] = 0
    new_public_requests: Literal[0] = 0
    legal_currentness: Literal["not_verified"] = "not_verified"


class Inventory(Strict):
    """Close the new audit files without copying the complete live source packet."""

    schema_version: Literal[1] = 1
    files: list[Ref]
    scope: Literal["documentation_review_metadata"] = "documentation_review_metadata"
