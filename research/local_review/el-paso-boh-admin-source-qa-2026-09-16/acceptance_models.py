"""Acceptance records cannot promote source fidelity to current legal authority."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Acceptance(Strict):
    source_id: Literal['el-paso-boh-admin-regulations-sd011']
    source_sha256: Literal['64d72ce1f7783dcf7fb5a3f6956e8ba4845c4839318613a1dee09d99716625d7']
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
    files: list[Asset]
