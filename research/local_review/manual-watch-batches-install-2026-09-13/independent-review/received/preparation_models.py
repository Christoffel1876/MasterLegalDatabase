"""Strict records for a prepared-only, immutable source-watch implementation handoff."""
from pathlib import PurePosixPath
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject unknown fields and implicit Python scalar conversions."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """Bind exact ordinary bytes under an explicitly supplied package/repository root."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> 'Ref':
        """Refuse absolute, traversing or normalized aliases."""
        path = PurePosixPath(self.path)
        if path.is_absolute() or '..' in path.parts or str(path) != self.path:
            raise ValueError('Unsafe evidence path')
        return self


class Design(Strict):
    """Current design decision with the earlier rejected option retained in a preimage."""
    prepared_at: AwareDatetime
    status: Literal['DESIGN_PREPARATION_NOT_INSTALLED_OR_EXECUTED']
    existing_code: list[Ref]
    pairs: dict[str, list[str]]
    source_baseline_bytes: Literal[2191486]
    source_pages: Literal[16]
    public_requests: Literal[0]
    production_writes: Literal[0]
    notes: list[str]
    implementation_decision: str


class SourceCheck(Strict):
    """A local identity/custody preflight, not a new HTTP request or legal-source review."""
    batch_id: str
    source_id: str
    authority_id: str
    baseline: Ref
    pages: int = Field(ge=1)
    exact_requested_url: str
    baseline_request_started_at: AwareDatetime | None
    baseline_recorded_http_time: AwareDatetime
    baseline_http_time_role: str
    repository_received_at: AwareDatetime
    raw_manifest_line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    legal_currentness: Literal['not_verified'] = 'not_verified'


class TestCheck(Strict):
    """One complete offline focused-test result with exact machine coverage evidence."""
    command: list[str]
    return_code: Literal[0]
    passed: Literal[205]
    branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    log: Ref
    coverage: Ref
    scope: str


class Validation(Strict):
    """Bind prepared implementation to actual local checks and unchanged existing replay."""
    schema_version: Literal[1] = 1
    checked_at: AwareDatetime
    status: Literal['PREPARED_NOT_INSTALLED_OR_EXECUTED']
    proposed_implementation: list[Ref]
    current_manual_manifest: Ref
    current_manual_records: int
    source_checks: list[SourceCheck] = Field(min_length=6, max_length=6)
    tests: TestCheck
    old_springs_inputs: list[Ref]
    old_springs_run_files: list[Ref]
    old_springs_report_status: Literal['completed']
    old_springs_readonly_replay: Literal['passed_with_transport_disabled']
    old_springs_bytes_unchanged: Literal[True]
    public_requests: Literal[0] = 0
    production_writes: Literal[0] = 0
    schedule_installed: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    limits: list[str]


class Manifest(Strict):
    """Closed preparation payloads; the manifest itself is externally hash-bound."""
    schema_version: Literal[1] = 1
    status: Literal['PREPARED_NOT_INSTALLED_OR_EXECUTED']
    files: list[Ref]
    installation_files: list[str]
    public_requests: Literal[0] = 0
    production_writes: Literal[0] = 0

    @model_validator(mode='after')
    def unique(self) -> 'Manifest':
        """Reject duplicate payloads and installation targets outside the staged subset."""
        paths = [item.path for item in self.files]
        if len(set(paths)) != len(paths):
            raise ValueError('Duplicate inventory member')
        if any('proposed/' + path not in paths for path in self.installation_files):
            raise ValueError('Missing proposed installation file')
        return self
