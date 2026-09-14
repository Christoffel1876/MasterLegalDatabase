"""Typed additive diagnosis of a preserved, partially completed custody transaction."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Reject extra fields and scalar coercions."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """Bind local retained bytes without certifying upstream acquisition."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Anchor(Strict):
    """Record one exact anchor destination in an already approved official parent."""
    parent_url: str
    parent_html: Ref
    href: str
    label: str
    resolved_url: str


class HostRow(Strict):
    """Separate approved host identity from source-date and original-custody certainty."""
    source_id: str
    authority_id: Literal['CO-COUNTY-EL_PASO']
    url: str
    host: str
    old_policy_accepted: bool
    new_policy_accepted: Literal[True]
    old_error: str | None
    anchors: list[Anchor]
    referral_limitation: str
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    legal_currentness: Literal['not_verified']


class StateFile(Strict):
    """Bind the interrupted bytes to the original intent's exact before/after state."""
    repository_path: str
    preserved: Ref
    position: Literal['before', 'after']
    original_intent_expected_sha256: str


class Diagnosis(Strict):
    """Record the actual failure and reviewed repair proposal without claiming recovery ran."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal['recovery_prepared_not_executed']
    original_transaction: Ref
    original_intent: Ref
    original_actual_repository_received_at: AwareDatetime
    old_constants: Ref
    approved_constants: Ref
    old_constants_snapshot_repository_path: str
    exact_added_host: Literal['epc-assets.elpasoco.com']
    removed_hosts: list[str] = Field(max_length=0)
    before_raw_records: Literal[46]
    before_ledger_records: Literal[47]
    interrupted_raw_records: Literal[59]
    interrupted_ledger_records: Literal[47]
    archived_new_originals: Literal[13]
    state_files: list[StateFile] = Field(min_length=3, max_length=3)
    host_matrix: list[HostRow] = Field(min_length=13, max_length=13)
    old_policy_rejections: Literal[9]
    cause: str
    correction: str
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]

    @model_validator(mode='after')
    def exact_scope(self) -> Diagnosis:
        """Prevent a wider exception or a falsely complete transaction claim."""
        if len({r.source_id for r in self.host_matrix}) != 13:
            raise ValueError('Duplicate source')
        if sum(not r.old_policy_accepted for r in self.host_matrix) != 9:
            raise ValueError('Expected exact nine previously rejected sources')
        if [s.position for s in self.state_files] != ['after', 'before', 'before']:
            raise ValueError('Interrupted state differs')
        if any(not r.anchors for r in self.host_matrix if not r.old_policy_accepted):
            raise ValueError('Asset-host exception lacks exact official referral')
        return self


class Inventory(Strict):
    """Closed frozen recovery preparation, excluding this inventory and test fixtures only."""
    status: Literal['recovery_prepared_not_executed']
    files: list[Ref]
    exclusions: Literal['PACKAGE_INVENTORY.json and _test_runs/ only']
