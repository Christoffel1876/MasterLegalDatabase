"""Independent offline acceptance contract for a prepared manual-source CI proposal."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Refuse undeclared or coerced evidence fields."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact ordinary-file identity in this closed packet."""

    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Check(Strict):
    """One bounded expectation and its separately recorded result."""

    id: str
    expected: str
    outcome: Literal['pending', 'pass', 'fail', 'not_executed']
    evidence: list[str]


class Finding(Strict):
    """Material issue or explicit residual limitation, with a reproducible anchor."""

    id: str
    severity: Literal['blocker', 'qualification', 'no_issue']
    statement: str
    evidence: list[str]


class Audit(Strict):
    """Preparation review only; never a live HTTP execution or installation receipt."""

    schema_version: Literal['1.0']
    stage: Literal['expectations_before_draft', 'frozen_independent_review']
    created_at: str
    inputs: list[Asset]
    checks: list[Check]
    findings: list[Finding]
    public_requests: Literal[0]
    canonical_changes: Literal[False]
    scheduled_or_installed_by_audit: Literal[False]
    legal_currentness: Literal['not_verified']
    limitations: list[str]


class Inventory(Strict):
    """Every retained payload; the outer manifest is the sole unlisted file."""

    status: Literal['frozen_offline_review_prepared_only']
    files: list[Asset]


class Baseline(Strict):
    """Selected local baseline identity and read-only Git storage observations."""

    source_id: str
    repository_path: str
    sha256: str
    size_bytes: int
    tracked: bool
    git_filter: str
    begins_pdf_magic: bool


class BaselineProbe(Strict):
    """Storage check does not reverify legal content or unselected corpus availability."""

    recorded_at: str
    rows: list[Baseline] = Field(min_length=8, max_length=8)
    public_requests: Literal[0]
    limitation: str


class ExecutionCheck(Strict):
    """Actual local sparse-corpus readiness; no watched publisher invocation."""

    checked_at: str
    temporary_root: str
    immutable_inputs_checked: Literal[88]
    manual_record_count: int
    manual_manifest_sha256: str
    actual_processes: Literal[4]
    execution_switch_present: Literal[False]
    source_runtime_created: Literal[False]
    summary: Asset
    status: Literal['ready']
    public_requests: Literal[0]
    limitations: list[str]
