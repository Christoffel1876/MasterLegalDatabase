"""Packaging and privacy records for unresolved Arapahoe resolution evidence."""
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    """Reject undeclared fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """An exact ordinary package-relative file binding."""
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

    @field_validator('path')
    @classmethod
    def local_path(cls, value: str) -> str:
        """Reject paths outside the selected package."""
        p = PurePosixPath(value)
        if not value or p.is_absolute() or '..' in p.parts or '\\' in value:
            raise ValueError('ordinary relative path required')
        if str(p) != value:
            raise ValueError('normalized relative path required')
        return value


class Redaction(Strict):
    """One omitted original and its explicitly marked distributable derivative."""
    excluded_original: Asset
    derivative: Asset
    reason: Literal['Set-Cookie session value excluded from distribution']
    transformation: str
    original_checked_against_handoff_before_packaging: Literal[True]
    original_digest_recomputed_by_portable_validator: Literal[False]
    sensitive_lines_replaced: Literal[1]
    original_retained_in_handoff: Literal[True]


class Status(Strict):
    """Research-only status without closing the missing legal-instrument chain."""
    package_id: Literal['arapahoe-resolution26-224-evidence-2026-09-11']
    packaged_at: datetime
    historical_handoff: str
    frozen_handoff_inventory: Asset
    frozen_audit: Asset
    handoff_files_total: Literal[36]
    exact_handoff_files_included: Literal[35]
    exact_handoff_bytes_included: Literal[1513543]
    redactions: list[Redaction] = Field(min_length=1, max_length=1)
    source_attachment_sha256: Literal[
        '8f1e94f6332fc9c36ee479f4673e2f85a533b2b777f29cbfc9757c2adcd41e6c'
    ]
    source_attachment_pages: Literal[2]
    original_access_events_counted: Literal[8]
    original_distinct_targets: Literal[6]
    new_public_access_events: Literal[0]
    scope: Literal['preserve_completed_bounded_source_review_only']
    item_metadata: Literal['26-403: Passed; final action 9/8/2026']
    item_metadata_qualification: str
    attachment_status: Literal['unnumbered_unfilled_resolution_attachment']
    numbered_executed_resolution_26_224_confirmed: Literal[False]
    adoption_date: None
    effective_date: None
    legal_currentness: Literal['not_verified']
    raw_manifest_or_ledger_intake: Literal[False]
    semantic_or_coverage_promotion: Literal[False]
    external_assignment: None
    privacy_check: list[str]
    limits: list[str]


class Inventory(Strict):
    """Complete file inventory except for the inventory's own bytes."""
    package_id: Literal['arapahoe-resolution26-224-evidence-2026-09-11']
    files: list[Asset]
    excluded_self: Literal['evidence-manifest.json']
