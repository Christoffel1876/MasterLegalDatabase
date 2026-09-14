"""Strict public-custody records; historical omissions remain explicit."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Ref(BaseModel):
    """An exact retained file identity."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Omission(BaseModel):
    """Record an excluded historical member without carrying its contents."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)
    reason: Literal['unrelated_untracked_user_owned_file']


class PublicReceipt(BaseModel):
    """Bind the current operational proposal and limited historical preservation."""
    model_config = ConfigDict(extra='forbid', strict=True)
    status: Literal['PREPARED_ONLY_PUBLIC_SUBSET_AND_87_PIN_REVISION']
    prepared_at: str
    predecessor_manifest: Ref
    original_payload_count: Literal[154]
    retained_original_payload_count: Literal[153]
    omitted: list[Omission] = Field(min_length=1, max_length=1)
    install_files: list[Ref]
    final_immutable_pin_count: Literal[87]
    all_final_pins_git_tracked: Literal[True]
    focused_tests_passed: Literal[44]
    sparse_readiness_passed: Literal[True]
    unrelated_user_file_original_unchanged: Literal[True]
    unrelated_user_file_contents_present: Literal[False]
    source_requests: Literal[0]
    installed_or_deployed: Literal[False]
    limitations: list[str]


class Manifest(BaseModel):
    """Close only the actual public payload tree."""
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['manual_watch_ci_publishable_revision']
    prepared_at: str
    files: list[Ref]
