"""Strict records for the bounded page-seven external-delivery audit."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject extra fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact retained file identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Audit(Strict):
    """Bounded replay results, distinct from reported methods and timestamps."""
    schema_version: Literal['page7-external-audit-1']
    audited_at: str
    scope: Literal['physical_page_7_only']
    source_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    received_files: list[Asset]
    listed_hashes: int
    listed_checksums: int
    freeze_leaf_bindings: int
    completion_hash_bindings: int
    unlisted_payloads: list[str]
    normalized_body_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    normalized_bodies_equal: Literal[True]
    findings: list[str]
    limits: list[str]


class Manifest(Strict):
    """Closed inventory of this independent packet except the manifest itself."""
    schema_version: Literal['page7-external-audit-manifest-1']
    files: list[Asset]
