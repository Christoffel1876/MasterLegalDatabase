"""Source-derived expectations frozen before examination of the new lookup adapter."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject undocumented fields and type coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Evidence(Strict):
    """A source input whose full bytes were hashed before adapter review."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Row(Strict):
    """The complete source row expected in a selected lookup result."""

    row_id: str
    physical_page: int
    group: str
    group_physical_page: int
    service: str
    fee: str
    linked_context: list[str]


class Context(Strict):
    """A complete source passage with its declared association scope."""

    context_id: str
    physical_page: int
    kind: str
    text: str
    applies_to: list[str]


class Case(Strict):
    """A source requirement; output field names are deliberately not prescribed."""

    id: str
    purpose: str
    source_id: str = "el-paso-boh-ehs-fees-sd011"
    query: str | None = None
    list_rows: bool = False
    mode: Literal["source", "current-law"] = "source"
    expected_kind: Literal["rows", "context_only", "no_match", "refused"]
    expected_exit: int
    expected_rows: list[Row]
    required_context: list[Context]
    directly_matched_context_ids: list[str]
    forbidden_context_links: dict[str, list[str]]
    prohibited_inferences: list[str]
    expected_evidence_verified: bool

    @model_validator(mode="after")
    def scope(self) -> Case:
        """Require one CLI selection and coherent row/refusal expectations."""
        if self.list_rows == (self.query is not None):
            raise ValueError("Exactly one query/list selection is required")
        if self.expected_kind in {"context_only", "no_match", "refused"} and self.expected_rows:
            raise ValueError("No synthetic fee rows for context, absence or refusal")
        return self


class Expectations(Strict):
    """A finite acceptance specification, not an execution receipt."""

    recorded_at: AwareDatetime
    status: Literal["source_expectations_frozen_before_new_adapter_review"]
    adapter_draft_read: Literal[False] = False
    adapter_executed: Literal[False] = False
    source_id: Literal["el-paso-boh-ehs-fees-sd011"]
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    issuer: Literal["El Paso County Board of Health"]
    administering_agency: Literal["El Paso County Public Health"]
    source_sha256: Literal["1b0529fb7514bcc50c0dd36c903ca361f6ab431712b4aebc48bca8e3f5373622"]
    package_repo_path: str
    inputs: list[Evidence]
    cases: list[Case]
    shared_requirements: list[str]
    custody_requirements: list[str]
    untouched_scope: list[str]


class Inventory(Strict):
    """Closed set of immutable expectation artifacts, excluding this inventory itself."""

    files: list[Evidence]
