"""Verify the bounded Sherlock008 raw-custody intake without network or writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
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

PACKAGE = Path("research/local_review/weld-greeley-intake-sherlock008-2026-09-11")
SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Strict(BaseModel):
    """Reject unmodeled fields and type coercions in this bounded receipt."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Bind a preserved file or original delivery location to exact bytes."""

    path: str
    sha256: SHA
    size_bytes: int = Field(ge=1)


class Copy(Strict):
    """Bind an unmodified evidence copy to its original byte identity."""

    original: Asset
    preserved: Asset

    @model_validator(mode="after")
    def identical(self) -> Copy:
        """Reject any changed byte identity in an exact evidence copy."""
        if (self.original.sha256, self.original.size_bytes) != (
                self.preserved.sha256, self.preserved.size_bytes):
            raise ValueError("evidence copy identity differs")
        return self


class SourceDate(Strict):
    """Preserve literal document date text and its limited evidentiary role."""

    value: str
    role: str
    qualification: str


class HttpEvidence(Strict):
    """Retain exact non-cookie response metadata, not a new acquisition certification."""

    original_header: Asset
    derived_header_without_cookies: Asset
    transformation: Literal["Only Set-Cookie header lines omitted; other bytes unchanged"]
    status: Literal[200] = 200
    content_type: Literal["application/pdf"] = "application/pdf"
    content_length: int = Field(ge=1)
    response_date: str
    last_modified: str
    response_metadata_is_legal_date: Literal[False] = False


class SourceProvenance(Strict):
    """Separate measured PDF custody, retained source evidence and unknown legal status."""

    source_id: str
    authority_id: Literal["CO-COUNTY-WELD", "CO-MUNICIPAL-GREELEY"]
    priority_id: Literal["SD008-01", "SD008-06", "SD008-07", "SD008-08"]
    event_id: Literal["SD008-B003", "SD008-E035", "SD008-E036", "SD008-E037"]
    source_role: Literal[
        "county_fee_schedule", "municipal_building_fee_schedule",
        "fee_adjustment_memorandum_with_schedules", "proposed_utility_fee_notice_with_schedule",
    ]
    received_original: Asset
    canonical_original: Asset
    intake_id: str
    disposition: Literal["new_original_archived"] = "new_original_archived"
    repository_received_at: AwareDatetime
    acquisition_method: Literal["received_review_package"] = "received_review_package"
    reported_acquisition_at: AwareDatetime | None
    reported_requested_url: str
    reported_final_url: str | None
    reported_method: Literal["mac_curl", "box_browser_reconstructed"]
    acquisition_evidence: Literal["retained_curl_body_and_headers", "reconstructed_browser"]
    live_reacquisition_performed: Literal[False] = False
    official_source_url: None = None
    null_official_source_url_reason: Literal[
        "successful_version_and_final_url_unconfirmed", "direct_host_not_in_existing_allowlist",
    ]
    official_referral_url: str | None
    official_referral_label: str | None
    official_referral_html: Asset | None
    http_evidence: HttpEvidence | None
    document_dates: list[SourceDate]
    page_count: int = Field(ge=1)
    pdf_is_repaired: Literal[False] = False
    pdf_is_encrypted: Literal[False] = False
    prior_visual_audit: str
    prior_visual_pages: list[int]
    this_intake_inspection: Literal["PDF_structure_and_custody_only"]
    qualifications: list[str]
    status: Literal["archived_pending_pipeline"] = "archived_pending_pipeline"
    legal_currentness: Literal["not_verified"] = "not_verified"
    semantic_or_coverage_promotion: Literal[False] = False

    @model_validator(mode="after")
    def constrained_evidence(self) -> SourceProvenance:
        """Require correct owner, URL assurance, custody equality and page references."""
        expected = {
            "SD008-01": ("county_fee_schedule", 5, "SD008-B003"),
            "SD008-06": ("municipal_building_fee_schedule", 1, "SD008-E035"),
            "SD008-07": ("fee_adjustment_memorandum_with_schedules", 3, "SD008-E036"),
            "SD008-08": ("proposed_utility_fee_notice_with_schedule", 2, "SD008-E037"),
        }
        if (self.source_role, self.page_count, self.event_id) != expected[self.priority_id]:
            raise ValueError("source role/page/event does not match the reviewed source")
        if (self.received_original.sha256, self.received_original.size_bytes) != (
                self.canonical_original.sha256, self.canonical_original.size_bytes):
            raise ValueError("canonical PDF differs from received PDF")
        if any(p < 1 or p > self.page_count for p in self.prior_visual_pages):
            raise ValueError("visual audit page outside source")
        if self.priority_id == "SD008-01":
            if (self.authority_id != "CO-COUNTY-WELD" or self.reported_final_url is not None
                    or self.reported_acquisition_at is not None or self.http_evidence is not None
                    or self.official_referral_html is not None
                    or self.null_official_source_url_reason !=
                    "successful_version_and_final_url_unconfirmed"):
                raise ValueError("Weld provenance certainty was improperly promoted")
        elif (self.authority_id != "CO-MUNICIPAL-GREELEY" or self.http_evidence is None
              or self.official_referral_html is None or not self.official_referral_url
              or not self.official_referral_label or self.reported_acquisition_at is None
              or self.reported_final_url != self.reported_requested_url):
            raise ValueError("Greeley source lacks preserved direct referral/response evidence")
        return self


class DedupeCheck(Strict):
    """Record exact size screening across all current raw files and both current manifests."""

    checked_at: AwareDatetime
    ordinary_files_size_screened: Literal[538]
    matching_size_files_hashed: Literal[0]
    symlinks_encountered: Literal[0]
    raw_manifest_records_checked: Literal[34]
    ledger_records_checked: Literal[35]
    exact_digest_matches: Literal[0]
    method: Literal["All ordinary raw files size screened; matching sizes require SHA256 equality"]
    historical_digest_alone_is_available_source: Literal[False] = False


class IntakeReceipt(Strict):
    """Bind a four-original append to frozen before/after history and existing reconciliation."""

    schema_version: Literal[1] = 1
    assignment: Literal["sherlock008-received-pdf-intake"]
    prepared_at: AwareDatetime
    pdfs_checked: Literal[4] = 4
    pages_checked_structurally: Literal[11] = 11
    new_originals: Literal[4] = 4
    new_original_bytes: Literal[1091614] = 1091614
    reused_originals: Literal[0] = 0
    custody_pairs_rechecked: Literal[110] = 110
    deduplication: DedupeCheck
    evidence_copies: list[Copy]
    source_provenance: Asset
    intake_records: Asset
    raw_manifest_before: Asset
    raw_manifest_after: Asset
    ledger_before: Asset
    ledger_after: Asset
    report_before: Asset
    report_after: Asset
    preimage_snapshots: list[Asset] = Field(min_length=3, max_length=3)
    new_raw_paths: list[str] = Field(min_length=4, max_length=4)
    baseline: ManualIntakeReconciliation
    pre_apply_dry_run: ManualIntakeReconciliation
    applied: ManualIntakeReconciliation
    idempotency_dry_run: ManualIntakeReconciliation
    old_manifest_prefix_preserved: Literal[True] = True
    old_ledger_prefix_preserved: Literal[True] = True
    no_existing_source_bytes_modified: Literal[True] = True
    acquisition_method: Literal["received_review_package"] = "received_review_package"
    legal_currentness: Literal["not_verified"] = "not_verified"
    semantic_or_coverage_promotion: Literal[False] = False
    api_usage: str
    limits: list[str]

    @model_validator(mode="after")
    def transitions(self) -> IntakeReceipt:
        """Reject changed baseline history, missing-source promotion or non-idempotent append."""
        if (self.baseline.ledger_records_after, self.applied.ledger_records_before,
                self.applied.ledger_records_after) != (35, 35, 39):
            raise ValueError("unexpected ledger transition")
        av = self.applied.report.archive_verification
        prior = self.baseline.report.archive_verification
        if (av is None or prior is None or av.manifest_records != 38
                or len(av.verified_intake_ids) != 38
                or av.missing_ledger_only_intake_ids != prior.missing_ledger_only_intake_ids
                or len(av.missing_ledger_only_intake_ids) != 1):
            raise ValueError("archive/missing-history status changed unexpectedly")
        if len(self.applied.added_intake_ids) != 4:
            raise ValueError("expected four added intake identities")
        if self.idempotency_dry_run.added_intake_ids or self.idempotency_dry_run.report_needs_update:
            raise ValueError("repeat reconciliation was not a no-op")
        return self


class Anchors(HTMLParser):
    """Read ordinary HTML anchor hrefs and visible labels without script execution."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.url: str | None = None
        self.words: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start capturing an anchor with an explicit href."""
        if tag == "a":
            self.url = dict(attrs).get("href")
            self.words = []

    def handle_data(self, data: str) -> None:
        """Retain visible anchor text."""
        if self.url is not None:
            self.words.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Emit a whitespace-normalized label when its anchor ends."""
        if tag == "a" and self.url is not None:
            self.links.append((self.url, " ".join(" ".join(self.words).split())))
            self.url = None


def digest(path: Path) -> str:
    """Hash an ordinary local file using a streaming read."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked(root: Path, asset: Asset) -> Path:
    """Confine a preserved evidence path and verify its exact size and SHA256."""
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
    """Validate frozen custody, current canonical rows and preserved source evidence."""
    package = root / PACKAGE
    receipt = IntakeReceipt.model_validate_json((package / "intake-receipt.json").read_bytes())
    Draft202012Validator(json.loads((package / "intake-receipt.schema.json").read_bytes())).validate(
        receipt.model_dump(mode="json"))
    for item in receipt.evidence_copies:
        checked(root, item.preserved)
    for item in [receipt.source_provenance, receipt.intake_records, receipt.raw_manifest_before,
                 receipt.raw_manifest_after, receipt.ledger_before, receipt.ledger_after,
                 receipt.report_before, receipt.report_after, *receipt.preimage_snapshots]:
        checked(root, item)
    source_schema = json.loads((package / "source-provenance.schema.json").read_bytes())
    with checked(root, receipt.source_provenance).open() as stream:
        sources = [SourceProvenance.model_validate_json(line) for line in stream]
    with checked(root, receipt.intake_records).open() as stream:
        records = [ManualSourceIntakeRecord.model_validate_json(line) for line in stream]
    if len(sources) != 4 or len({s.canonical_original.sha256 for s in sources}) != 4:
        raise ValueError("expected four distinct canonical PDFs")
    if len(records) != 4 or [r.archive_path for r in records] != receipt.new_raw_paths:
        raise ValueError("new raw record list differs")
    suffix = "".join(r.model_dump_json() + "\n" for r in records).encode()
    for before, after in [(receipt.raw_manifest_before, receipt.raw_manifest_after),
                          (receipt.ledger_before, receipt.ledger_after)]:
        if checked(root, after).read_bytes() != checked(root, before).read_bytes() + suffix:
            raise ValueError("append changed preexisting bytes")
    snapshot_values = {(a.sha256, a.size_bytes) for a in receipt.preimage_snapshots}
    if snapshot_values != {(a.sha256, a.size_bytes) for a in
                           [receipt.raw_manifest_before, receipt.ledger_before, receipt.report_before]}:
        raise ValueError("preimage snapshots do not match all three original files")
    with (root / "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl").open() as stream:
        current = {r.intake_id: r for r in
                   (ManualSourceIntakeRecord.model_validate_json(line) for line in stream)}
    with (root / "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl").open() as stream:
        ledger = {r.intake_id: r for r in
                  (ManualSourceIntakeRecord.model_validate_json(line) for line in stream)}
    for record in records:
        _validate_reconciliation_record(root, record)
        if current.get(record.intake_id) != record or ledger.get(record.intake_id) != record:
            raise ValueError("current manifest/ledger lost or changed an intake record")
    audit = json.loads((package / "evidence/audits/INTAKE_AUDIT.json").read_bytes())
    audited_sources = {r["priority_id"]: r for r in audit["source_checks"]}
    audited_events = {r["event_id"]: r for r in audit["event_checks"]}
    for source in sources:
        prior = audited_sources[source.priority_id]
        if (prior["primary"]["sha256"] != source.canonical_original.sha256
                or prior["primary"]["size_bytes"] != source.canonical_original.size_bytes
                or prior["inspected_physical_pages"] != source.prior_visual_pages
                or prior["authority_id"] != source.authority_id):
            raise ValueError("canonical source differs from frozen independent audit")
        Draft202012Validator(source_schema).validate(source.model_dump(mode="json"))
        raw = checked(root, source.canonical_original)
        with pymupdf.open(raw) as pdf:
            if len(pdf) != source.page_count or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError("PDF structural metadata differs")
            for page in pdf:
                page.get_text()
        row = current.get(source.intake_id)
        if (row is None or row.record_id != source.source_id
                or row.archive_path != source.canonical_original.path
                or row.sha256 != source.canonical_original.sha256
                or row.official_source_url is not None or row.status != source.status
                or row.acquisition_method != "received_review_package"):
            raise ValueError("source provenance differs from canonical intake")
        if source.http_evidence:
            header = audited_events[source.event_id]["header_evidence"]
            if (header["sha256"] != source.http_evidence.original_header.sha256
                    or header["size_bytes"] != source.http_evidence.original_header.size_bytes):
                raise ValueError("original HTTP header binding differs from frozen audit")
            parser = Anchors()
            parser.feed(checked(root, source.official_referral_html).read_text())
            if (source.reported_requested_url, source.official_referral_label) not in parser.links:
                raise ValueError("exact official referral anchor is absent")
            headers = checked(root, source.http_evidence.derived_header_without_cookies).read_text()
            if re.search(r"^set-cookie:", headers, re.I | re.M):
                raise ValueError("response cookie was not excluded from derived header")
            if not re.search(r"^HTTP/\S+ 200(?:\s|$)", headers, re.M):
                raise ValueError("preserved HTTP status differs")
            for key, value in [("content-type", "application/pdf"),
                               ("content-length", str(source.canonical_original.size_bytes)),
                               ("date", source.http_evidence.response_date),
                               ("last-modified", source.http_evidence.last_modified)]:
                if not re.search(rf"^{key}: {re.escape(value)}\s*$", headers, re.M | re.I):
                    raise ValueError(f"preserved HTTP metadata differs: {key}")
    return {"status": "passed", "pdfs_verified": 4, "structural_pages": 11,
            "new_originals": 4, "reused_originals": 0, "raw_manifest_records_at_intake": 38,
            "ledger_records_at_intake": 39, "missing_ledger_only_originals": 1,
            "legal_currentness": "not_verified", "semantic_or_coverage_promotion": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(validate_intake(args.root), indent=2))
