"""Validate the bounded Sherlock007 received-package intake without changing data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import pymupdf
from jsonschema import Draft202012Validator
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from geode.pipeline.manual_source_intake import (
    ManualIntakeReconciliation,
    ManualSourceIntakeRecord,
    _validate_reconciliation_record,
)

PACKAGE = Path("research/local_review/larimer-intake-sherlock007-2026-09-11")
SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Strict(BaseModel):
    """Reject unmodeled fields in generated custody evidence."""

    model_config = ConfigDict(extra="forbid")


class Asset(Strict):
    """A byte-bound repository file or historical delivery location."""

    path: str
    sha256: SHA
    size_bytes: int = Field(ge=1)


class PreservedEvidence(Strict):
    """An immutable copy of an earlier audit or supplied provenance artifact."""

    original: Asset
    preserved: Asset

    @model_validator(mode="after")
    def exact_copy(self) -> PreservedEvidence:
        """Require equal original and preserved byte identities."""
        if (self.original.sha256, self.original.size_bytes) != (
            self.preserved.sha256, self.preserved.size_bytes):
            raise ValueError("preserved evidence differs from original")
        return self


class SourceProvenance(Strict):
    """Measured bytes and qualified supplied source claims for one delivered PDF."""

    source_id: str
    authority_id: Literal["CO-COUNTY-LARIMER"] = "CO-COUNTY-LARIMER"
    priority_id: str
    event_id: str
    source_role: Literal[
        "fee_schedule", "fee_increase_memo", "recorded_initial_moratorium_resolution",
        "signed_equity_reduction_instrument", "staff_recommendation_memo",
        "meeting_packet_with_unsigned_extension_draft", "incidental_building_amendments",
        "incidental_wildfire_code",
    ]
    received_original: Asset
    canonical_original: Asset
    intake_id: str
    disposition: Literal["new_original_archived", "existing_original_reused"]
    repository_received_at: AwareDatetime
    delivery_rechecked_at: AwareDatetime
    original_acquisition_at: None = None
    acquisition_method: Literal["received_review_package"] = "received_review_package"
    supplied_requested_url: str
    supplied_final_url: str
    supplied_http_status: Literal[200] = 200
    supplied_time_claim: str
    supplied_method_claim: Literal["browser_GET"] = "browser_GET"
    source_http_acquisition_verified: Literal[False] = False
    official_source_url: str | None
    official_url_allowlist_accepted: bool
    referral_context: str
    referral_evidence: list[Asset]
    source_audit_pointer: str
    source_audit_inspected_physical_pages: list[int]
    inspected_by_this_intake: Literal["PDF_structure_only"] = "PDF_structure_only"
    page_count: int = Field(ge=1)
    pdf_is_repaired: Literal[False] = False
    pdf_is_encrypted: Literal[False] = False
    source_qualifications: list[str]
    status: Literal["archived_pending_pipeline"] = "archived_pending_pipeline"
    legal_currentness: Literal["not_verified"] = "not_verified"
    semantic_or_coverage_promotion: Literal[False] = False

    @model_validator(mode="after")
    def exact_identity(self) -> SourceProvenance:
        """Keep byte identity, URL qualification, and page bounds explicit."""
        if (self.received_original.sha256, self.received_original.size_bytes) != (
                self.canonical_original.sha256, self.canonical_original.size_bytes):
            raise ValueError("received and canonical bytes differ")
        if any(p < 1 or p > self.page_count for p in self.source_audit_inspected_physical_pages):
            raise ValueError("source-audit page out of bounds")
        if not self.official_url_allowlist_accepted and self.official_source_url is not None:
            raise ValueError("unapproved source URL must remain a qualified claim")
        return self


class DedupeCheck(Strict):
    """Exact size-screened SHA comparison across the complete local raw archive."""

    scope: Literal["all ordinary files under repository _RAW_ARCHIVE"]
    checked_at: AwareDatetime
    ordinary_files_size_screened: int = Field(ge=1)
    matching_size_files_hashed: int = Field(ge=0)
    matching_size_bytes_hashed: int = Field(ge=0)
    symlinks_encountered: Literal[0] = 0
    method: Literal["size excludes byte equality; every matching-size file SHA256 verified"]
    new_pdf_digests: list[SHA] = Field(min_length=3, max_length=3)
    reused_pdf_digests: list[SHA] = Field(min_length=6, max_length=6)
    limit: str


class IntakeReceipt(Strict):
    """A three-original intake with six exact-byte reuses and unchanged prior custody."""

    schema_version: Literal[1] = 1
    assignment: Literal["sherlock007-received-pdf-intake"]
    prepared_at: AwareDatetime
    source_authority_id: Literal["CO-COUNTY-LARIMER"]
    layer_id: Literal["08_County_Authorities"]
    pdfs_checked: Literal[9] = 9
    pages_checked_structurally: Literal[345] = 345
    new_originals: Literal[3] = 3
    new_original_pages: Literal[200] = 200
    new_original_bytes: Literal[31000893] = 31000893
    reused_originals: Literal[6] = 6
    custody_pairs_rechecked: Literal[87] = 87
    deduplication: DedupeCheck
    evidence_copies: list[PreservedEvidence]
    source_provenance: Asset
    intake_records: Asset
    raw_manifest_before: Asset
    raw_manifest_after: Asset
    ledger_before: Asset
    ledger_after: Asset
    report_before: Asset
    report_after: Asset
    preimage_snapshots: list[Asset]
    batch4_frozen_manifest: Asset
    batch4_preimage_rechecked: Literal[True] = True
    new_raw_paths: list[str] = Field(min_length=3, max_length=3)
    baseline: ManualIntakeReconciliation
    pre_apply_dry_run: ManualIntakeReconciliation
    applied: ManualIntakeReconciliation
    idempotency_dry_run: ManualIntakeReconciliation
    no_existing_raw_bytes_changed: Literal[True] = True
    old_manifest_prefix_preserved: Literal[True] = True
    old_ledger_prefix_preserved: Literal[True] = True
    original_acquisition_at: None = None
    acquisition_method: Literal["received_review_package"]
    legal_currentness: Literal["not_verified"] = "not_verified"
    semantic_or_coverage_promotion: Literal[False] = False
    api_usage: str
    limits: list[str]

    @model_validator(mode="after")
    def count_transition(self) -> IntakeReceipt:
        """Reject changed baseline history or an unexpected reconciliation result."""
        if (self.baseline.ledger_records_after, self.applied.ledger_records_before,
                self.applied.ledger_records_after) != (32, 32, 35):
            raise ValueError("unexpected ledger transition")
        if len(self.applied.added_intake_ids) != 3:
            raise ValueError("intake must add exactly three validated records")
        av = self.applied.report.archive_verification
        if (av is None or av.manifest_records != 34 or len(av.verified_intake_ids) != 34
                or len(av.missing_ledger_only_intake_ids) != 1):
            raise ValueError("archive availability or ledger-only gap changed unexpectedly")
        if self.idempotency_dry_run.added_intake_ids or self.idempotency_dry_run.report_needs_update:
            raise ValueError("reconciliation was not idempotent")
        return self


def digest(path: Path) -> str:
    """Hash an ordinary local file without loading it all into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked(root: Path, asset: Asset) -> Path:
    """Verify a repository-relative evidence path, size and SHA-256."""
    relative = PurePosixPath(asset.path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in asset.path:
        raise ValueError("unsafe repository evidence path")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("evidence is not an ordinary file")
    if path.stat().st_size != asset.size_bytes or digest(path) != asset.sha256:
        raise ValueError(f"evidence bytes differ: {asset.path}")
    return path


def validate_intake(root: Path) -> dict[str, object]:
    """Verify the frozen transaction and current raw records without network or writes."""
    package = root / PACKAGE
    receipt = IntakeReceipt.model_validate_json((package / "intake-receipt.json").read_bytes())
    schema = json.loads((package / "intake-receipt.schema.json").read_bytes())
    Draft202012Validator(schema).validate(receipt.model_dump(mode="json"))
    for binding in receipt.evidence_copies:
        checked(root, binding.preserved)
    for asset in [receipt.source_provenance, receipt.intake_records, receipt.raw_manifest_before,
                  receipt.raw_manifest_after, receipt.ledger_before, receipt.ledger_after,
                  receipt.report_before, receipt.report_after, *receipt.preimage_snapshots]:
        checked(root, asset)
    with checked(root, receipt.source_provenance).open() as stream:
        sources = [SourceProvenance.model_validate_json(line) for line in stream]
    with checked(root, receipt.intake_records).open() as stream:
        new_rows = [ManualSourceIntakeRecord.model_validate_json(line) for line in stream]
    if len(sources) != 9 or len({s.canonical_original.sha256 for s in sources}) != 9:
        raise ValueError("must bind exactly nine distinct PDFs")
    if len(new_rows) != 3 or [r.archive_path for r in new_rows] != receipt.new_raw_paths:
        raise ValueError("new raw intake list mismatch")
    before = checked(root, receipt.raw_manifest_before).read_bytes()
    after = checked(root, receipt.raw_manifest_after).read_bytes()
    old_ledger = checked(root, receipt.ledger_before).read_bytes()
    new_ledger = checked(root, receipt.ledger_after).read_bytes()
    suffix = "".join(r.model_dump_json() + "\n" for r in new_rows).encode()
    if after != before + suffix or new_ledger != old_ledger + suffix:
        raise ValueError("intake changed preexisting manifest or ledger bytes")
    with (root / "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl").open() as stream:
        current = [ManualSourceIntakeRecord.model_validate_json(line) for line in stream]
    indexed = {r.intake_id: r for r in current}
    for record in new_rows:
        _validate_reconciliation_record(root, record)
        if indexed.get(record.intake_id) != record:
            raise ValueError("current manifest has lost or changed the received intake")
    for source in sources:
        raw = checked(root, source.canonical_original)
        with pymupdf.open(raw) as pdf:
            if len(pdf) != source.page_count or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError("PDF structural metadata differs")
        row = indexed.get(source.intake_id)
        if (row is None or row.sha256 != source.canonical_original.sha256
                or row.archive_path != source.canonical_original.path
                or row.record_id != source.source_id or row.status != "archived_pending_pipeline"):
            raise ValueError("source provenance differs from pending canonical intake")
    return {"status": "passed", "pdfs_verified": 9, "new_originals": 3,
            "reused_originals": 6, "raw_manifest_records_at_intake": 34,
            "ledger_records_at_intake": 35, "missing_ledger_only_originals": 1,
            "legal_currentness": "not_verified", "semantic_or_coverage_promotion": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(validate_intake(args.root), indent=2))
