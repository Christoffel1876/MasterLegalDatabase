"""Strict records for an explicitly authorized staged-index export verification."""
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Forbid unknown fields and implicit coercion."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Digest(Strict):
    """An exact byte identity, without claiming a file was retained."""

    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Asset(Digest):
    """One retained file relative to the receipt directory."""

    path: str


class ScanAsset(Asset):
    """One expected final-scan member."""

    tracked: bool
    ignored: bool
    basis: list[str]


class Scan(Strict):
    """The previously reviewed root scanner output contract."""

    status: Literal['prepared_exact_paths_not_staged']
    recorded_at: str
    head: str = Field(pattern=r'^[a-f0-9]{40}$')
    wrappers: int = Field(ge=0)
    new_raw_originals: Literal[6]
    files: list[ScanAsset]
    excluded_user_paths: list[str]
    qualifications: list[str]


class IndexEntry(Strict):
    """One regular, unconflicted stage-zero index member."""

    path: str
    mode: Literal['100644', '100755']
    oid: str = Field(pattern=r'^[a-f0-9]{40,64}$')


class ExportAsset(IndexEntry, Digest):
    """Exact index blob identity checked after export."""


class Command(Strict):
    """Actual process invocation and byte-stream outcomes."""

    argv: list[str]
    cwd: str
    started_at: AwareDatetime
    finished_at: AwareDatetime
    exit_code: int | None
    stdout: Digest
    stderr: Asset
    stdout_file: Asset | None
    timed_out: bool


class Receipt(Strict):
    """Actual execution only, including failed checks without inferred success."""

    schema_version: Literal['staged-export-verification-v1'] = 'staged-export-verification-v1'
    status: Literal['passed', 'failed']
    started_at: AwareDatetime
    finished_at: AwareDatetime
    repository: str
    export_directory: str
    expected_scan_sha256: str
    expected_schema_sha256: str
    index_before: Digest | None
    index_after: Digest | None
    head: str | None
    scan_members_checked: int
    exported_files: int
    exported_bytes: int
    wrappers_checked: int
    inventory_check_passed: bool
    ci_default_readiness_passed: bool
    ci_execution_requested: Literal[False] = False
    public_source_requests_requested: Literal[0] = 0
    git_mutations_requested: Literal[0] = 0
    lfs_smudge: Literal['disabled_and_never_invoked'] = 'disabled_and_never_invoked'
    commands: list[Command]
    procedure_files: list[Asset]
    failure: str | None
    qualifications: list[str]


class ExportInventory(Strict):
    """Complete index-derived exported tree inventory."""

    recorded_at: AwareDatetime
    files: list[ExportAsset]
