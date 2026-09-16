"""Acceptance records cannot promote source fidelity to current legal authority."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class Strict(BaseModel):
    """Reject undeclared fields and implicit coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Bind one relative path to its exact bytes."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Acceptance(Strict):
    """Accept this historical source's fidelity without certifying current law."""
    source_id: Literal['el-paso-ldc-chapter-2-sd011']
    source_sha256: Literal['f3d527fd6a9da5b0043672582dda812dc9c3dfe9958d8b53eec876957ed10953']
    authority_id: Literal['CO-COUNTY-EL_PASO']
    accepted_at: AwareDatetime
    reviewer: Literal['Atlas']
    status: Literal['accepted_source_fidelity_for_metadata_only_review_join']
    source_review: Asset
    source_review_schema: Asset
    frozen_manifest: Asset
    root_reading: Asset
    scope: str
    pages_directly_inspected: list[int]
    native_candidate_changed: Literal[False]
    external_review_consulted: Literal[False]
    external_review_status: str
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    limitations: list[str]


class Inventory(Strict):
    """Enumerate every acceptance-package payload except the inventory itself."""
    files: list[Asset]
