"""Typed receipt for bounded preparation, rendering inspection and integrity checks."""
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict


class Strict(BaseModel):
    """Reject unrecognized receipt fields and implicit scalar coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Case(Strict):
    """Record the actual rejection reached by a temporary tamper probe."""
    case: str
    result: Literal['rejected']
    reason: str


class Check(Strict):
    """Record the earlier exact packet verification result before receipt sealing."""
    status: Literal['verified_prepared_not_dispatched']
    documents: Literal[2]
    physical_pages: Literal[5]
    native_bytes: Literal[9846]
    images_dpi: Literal[300]
    payloads: int
    manifest_sha256: str
    public_requests: Literal[0]
    source_fidelity_review_performed_by_validator: Literal[False]
    legal_currentness: Literal['not_verified']


class Validation(Strict):
    """Retain exact command output and honest rendering/fixture limits."""
    started_at: AwareDatetime
    completed_at: AwareDatetime
    initial_manifest_sha256: str
    status: Literal['passed']
    portable_cli_exit: Literal[0]
    portable_stdout: str
    portable_stderr: str
    tamper_checks: list[Case]
    packet_check: Check
    all_five_full_images_directly_viewed_for_render_completeness: Literal[True]
    review_scope: str
    initial_local_setup_failures: list[str]
    source_or_repository_writes: Literal[0]
    public_requests: Literal[0]
