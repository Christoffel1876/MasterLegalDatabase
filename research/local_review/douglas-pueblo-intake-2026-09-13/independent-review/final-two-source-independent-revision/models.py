"""Typed additive review of an exact-pinned metadata loader revision."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Check(Strict):
    command: list[str]
    started_at: AwareDatetime
    completed_at: AwareDatetime
    returncode: Literal[0]
    stdout: Ref
    stderr: Ref
    before: list[Ref]
    after: list[Ref]
    execution_directory_created: Literal[False]
    public_requests: Literal[0]
    production_writes: Literal[0]


class Review(Strict):
    schema_version: Literal[1] = 1
    reviewed_at: AwareDatetime
    reviewer: Literal['Atlas independent review worker']
    historical_transaction: Ref
    original_independent_manifest: Ref
    final_transaction: Ref
    final_preparation_manifest: Ref
    final_verifier: Ref
    final_tests: Ref
    historical_repro: str
    reproduction_scope: str
    checked_buffer_confirmation: list[str]
    read_only_check: Ref
    status: Literal['accepted_in_reviewed_scope']
    qualifications: list[str]
    public_requests: Literal[0] = 0
    production_writes: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Manifest(Strict):
    schema_version: Literal[1] = 1
    frozen_at: AwareDatetime
    files: list[Ref]
