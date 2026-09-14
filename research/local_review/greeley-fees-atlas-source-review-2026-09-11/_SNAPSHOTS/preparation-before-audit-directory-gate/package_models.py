"""Strict portable custody and scope records for the three Greeley source reviews."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
SPECS = [
    ('EB-PDF-015', 'greeley-building-fees-sd008-06', 1, 3236,
     'fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4'),
    ('EB-PDF-016', 'greeley-development-impact-fee-memo-sd008-07', 3, 7191,
     '9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709'),
    ('EB-PDF-017', 'greeley-water-sewer-proposed-pif-notice-sd008-08', 2, 1316,
     'edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c'),
]


class Strict(BaseModel):
    """Reject undeclared fields and scalar coercion."""

    model_config = ConfigDict(extra='forbid', strict=True)


class FileRef(Strict):
    """An immutable package-local regular file."""

    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(gt=0)]

    @field_validator('path')
    @classmethod
    def confined(cls, value: str) -> str:
        """Require a normalized relative POSIX path."""
        path = PurePosixPath(value)
        if path.is_absolute() or '..' in path.parts or str(path) != value or value == '.':
            raise ValueError('A normalized package-relative path is required')
        return value


class Payload(Strict):
    """A frozen input or a newly authored packaging/verification file."""

    file: FileRef
    original_path: str | None
    role: Literal['unchanged_packet', 'unchanged_source_audit', 'package_support']


class Resolution(Strict):
    """Resolve a historical original path to frozen byte-identical evidence."""

    original_path: str
    frozen: FileRef
    basis: Literal['packet_custody_identity', 'packet_document_identity',
                   'copied_audit_input_identity']


class ScopeNote(Strict):
    """Qualified packaging summary anchored to unchanged source-review findings."""

    text: str
    audit_anchors: Annotated[list[str], Field(min_length=1)]


class Document(Strict):
    """Source and review identities; no operative rule or current-fee classification."""

    assignment_id: str
    source_id: str
    expected_physical_pages: Annotated[int, Field(ge=1, le=3)]
    original_native_bytes: Annotated[int, Field(gt=0)]
    source: FileRef
    candidate: FileRef
    audit: FileRef
    audit_schema: FileRef
    audit_directory: str
    source_role: Literal['building_fee_schedule', 'fee_adjustment_memorandum_with_schedules',
                         'proposed_utility_fee_notice_with_conditional_schedule']
    review_mode: Literal['candidate_aware_not_blind']
    external_review_status: Literal['pending_not_intaken']
    legal_currentness: Literal['not_verified']
    source_changes: Literal['none']
    scope_notes: list[ScopeNote]


class Package(Strict):
    """Complete frozen payload inventory and limited source-review scope."""

    schema_version: Literal[1]
    package_id: Literal['greeley-fees-atlas-source-review-2026-09-11']
    packaged_at: AwareDatetime
    status: Literal['atlas_source_reviews_packaged_pending_external_review']
    legal_currentness: Literal['not_verified']
    no_external_report_intake: Literal[True]
    new_network_requests: Literal[0]
    source_or_handoff_changes: Literal['none']
    documents: Annotated[list[Document], Field(min_length=3, max_length=3)]
    packet_manifest: FileRef
    payloads: list[Payload]
    historical_path_resolutions: list[Resolution]
    portability_limits: list[str]
    downstream_limits: list[str]

    @model_validator(mode='after')
    def identities(self) -> Package:
        """Pin the source set and require all identities to occur in the inventory."""
        seen = [p.file.path for p in self.payloads]
        if len(seen) != len(set(seen)):
            raise ValueError('Duplicate payload path')
        refs = {p.file.path: p.file for p in self.payloads}
        for document, expected in zip(self.documents, SPECS, strict=True):
            actual = (document.assignment_id, document.source_id,
                      document.expected_physical_pages, document.original_native_bytes,
                      document.source.sha256)
            if actual != expected:
                raise ValueError('Wrong source assignment, page count or native-byte scope')
            for ref in [document.source, document.candidate, document.audit,
                        document.audit_schema]:
                if refs.get(ref.path) != ref:
                    raise ValueError('Uninventoried document evidence')
        if refs.get(self.packet_manifest.path) != self.packet_manifest:
            raise ValueError('Uninventoried packet manifest')
        for resolution in self.historical_path_resolutions:
            if refs.get(resolution.frozen.path) != resolution.frozen:
                raise ValueError('Uninventoried custody resolution')
        originals = [r.original_path for r in self.historical_path_resolutions]
        if len(originals) != len(set(originals)):
            raise ValueError('Ambiguous historical-path resolution')
        return self


class ValidationReceipt(Strict):
    """Measured offline verification result for one package manifest."""

    schema_version: Literal[1]
    verified_at: AwareDatetime
    package: FileRef
    status: Literal['passed']
    payload_files: Annotated[int, Field(gt=0)]
    physical_pages: Literal[6]
    native_bytes: Literal[11743]
    audit_scope_checks: dict[str, int]
    schema_pairs_checked: Annotated[int, Field(gt=0)]
    historical_paths_resolved: Annotated[int, Field(gt=0)]
    full_page_rerender_performed: bool
    external_report_intake: Literal[False]
    legal_currentness: Literal['not_verified']
    checks: list[str]
