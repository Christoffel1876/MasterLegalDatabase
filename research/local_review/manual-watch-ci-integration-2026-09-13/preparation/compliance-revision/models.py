"""Strict additive revision custody; importing performs no work."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Ref(BaseModel):
    """Bind one exact ordinary file."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Change(BaseModel):
    """Describe one of the two permitted file changes."""
    model_config = ConfigDict(extra='forbid', strict=True)
    install_path: str
    before: Ref
    after: Ref
    scope: Literal['annotations_only', 'yaml_frontmatter_only']


class Receipt(BaseModel):
    """Preserve predecessor and exact two-file revision boundaries."""
    model_config = ConfigDict(extra='forbid', strict=True)
    status: Literal['PREPARED_ADDITIVE_COMPLIANCE_REVISION']
    prepared_at: str
    predecessor_manifest: Ref
    changes: list[Change] = Field(min_length=2, max_length=2)
    ast_equivalence: Ref
    focused_test: Ref
    focused_tests_passed: Literal[44]
    predecessor_payloads_unchanged: Literal[154]
    runner_changed: Literal[False]
    workflow_changed: Literal[False]
    source_configs_changed: Literal[False]
    installed_or_deployed: Literal[False]
    source_requests: Literal[0]
    limitations: list[str]


class Manifest(BaseModel):
    """Closed inventory of this additive revision only."""
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['manual_watch_ci_compliance_revision']
    prepared_at: str
    files: list[Ref]
