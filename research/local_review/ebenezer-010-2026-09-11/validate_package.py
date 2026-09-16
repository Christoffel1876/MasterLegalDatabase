"""Validate the EB010 custody and byte-preserving native-text review offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from jsonschema import Draft202012Validator
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

PACKAGE = Path("research/local_review/ebenezer-010-2026-09-11")
SOURCE_ID = "larimer-development-review-fees-sd004-07"
SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Strict(BaseModel):
    """Disallow undocumented fields in generated review artifacts."""

    model_config = ConfigDict(extra="forbid")


class Asset(Strict):
    """One immutable repository file binding."""

    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)


class ReceivedCopy(Strict):
    """Exact received bytes; the original location is historical custody metadata."""

    original_path: str
    received_at: AwareDatetime
    file: Asset
    exact_copy_verified: Literal[True] = True


class HashClaim(Strict):
    """A named external hash claim checked against measured local bytes."""

    receipt_name: str
    claim_key: str
    claimed_sha256: SHA
    bound_file: Asset
    matches: Literal[True] = True

    @model_validator(mode="after")
    def matching_hash(self) -> HashClaim:
        """Require the claim and preserved file to agree."""
        if self.claimed_sha256 != self.bound_file.sha256:
            raise ValueError("external hash claim mismatch")
        return self


class ReceiptDefect(Strict):
    """A receipt summary error, separate from the full review's source claims."""

    defect_id: str
    receipt_file: Asset
    json_pointer: str
    received_text: str
    source_amount_as_printed: str
    full_report_finding_id: str
    disposition: Literal["rejected_as_fee_literal"] = "rejected_as_fee_literal"
    qualification: str


class Custody(Strict):
    """Verified delivery identity without certification of the claimed review process."""

    schema_version: Literal[1] = 1
    assignment_id: Literal["EB-PDF-010"] = "EB-PDF-010"
    source_id: Literal["larimer-development-review-fees-sd004-07"] = SOURCE_ID
    received_at: AwareDatetime
    copies: list[ReceivedCopy] = Field(min_length=4, max_length=4)
    hash_claims: list[HashClaim] = Field(min_length=23, max_length=23)
    all_embedded_hashes_resolve_to_preserved_assets: Literal[True] = True
    claimed_pass1_start: AwareDatetime
    claimed_pass1_freeze: AwareDatetime
    claimed_pass2_start: AwareDatetime
    claimed_pass2_end: AwareDatetime
    timing_and_blind_order_independently_proven: Literal[False] = False
    caption_mediation: Literal["reported_by_external_reviewer"]
    missing_referenced_support: list[str]
    receipt_defects: list[ReceiptDefect] = Field(min_length=2, max_length=2)
    limitations: list[str]


class Segment(Strict):
    """An unchanged native UTF-8 interval placed in reviewed source order."""

    segment_id: str
    name: str
    original_start_byte: int = Field(ge=0)
    original_end_byte_exclusive: int = Field(gt=0)
    text: str


class PageReview(Strict):
    """All native characters on one page, partitioned exhaustively without normalization."""

    physical_page: int = Field(ge=1, le=7)
    printed_page_label: str
    image: Asset
    image_width: Literal[2550] = 2550
    image_height: Literal[3301] = 3301
    native_evidence: Asset
    native_text_sha256: SHA
    native_text_size_bytes: int = Field(gt=0)
    candidate_start_byte: int = Field(ge=0)
    candidate_end_byte_exclusive: int = Field(gt=0)
    review_basis: Asset
    source_image_inspected_by: str
    segments_in_reviewed_order: list[Segment]
    reordered_native_text: str
    reordered_text_sha256: SHA
    association_annotations: list[str]
    source_anomalies_preserved: list[str]
    glyph_perfect_typography_certified: Literal[False] = False

    @model_validator(mode="after")
    def exhaustive_partition(self) -> PageReview:
        """Reject omission, duplication, overlap, changed bytes, or a substituted output."""
        cursor = 0
        original = bytearray()
        ids = set()
        for segment in sorted(self.segments_in_reviewed_order,
                              key=lambda value: value.original_start_byte):
            if segment.segment_id in ids or segment.original_start_byte != cursor:
                raise ValueError("native partition duplicate, gap, or overlap")
            ids.add(segment.segment_id)
            data = segment.text.encode("utf-8")
            if segment.original_end_byte_exclusive - cursor != len(data):
                raise ValueError("native UTF-8 interval length mismatch")
            original.extend(data)
            cursor = segment.original_end_byte_exclusive
        if cursor != self.native_text_size_bytes or digest(original) != self.native_text_sha256:
            raise ValueError("partition does not reconstruct the complete native page")
        reordered = "".join(s.text for s in self.segments_in_reviewed_order)
        if reordered != self.reordered_native_text:
            raise ValueError("reviewed text differs from ordered native segments")
        data = reordered.encode("utf-8")
        if digest(data) != self.reordered_text_sha256 or Counter(data) != Counter(original):
            raise ValueError("native character conservation failed")
        if self.candidate_end_byte_exclusive - self.candidate_start_byte != cursor:
            raise ValueError("candidate native interval length mismatch")
        return self


class Disposition(Strict):
    """Atlas's bounded disposition of one external report finding or receipt defect."""

    finding_id: str
    physical_pages: list[int]
    external_severity: Literal["critical", "minor", "receipt_defect"]
    disposition: Literal["accepted", "qualified", "rejected"]
    external_claim_scope: str
    source_review_basis: list[str]
    atlas_result: str
    action_in_this_package: str


class ReviewedNative(Strict):
    """Source-ordered native text and separate annotations, without legal promotion."""

    schema_version: Literal[1] = 1
    review_id: Literal["EB-PDF-010-ATLAS-NATIVE"] = "EB-PDF-010-ATLAS-NATIVE"
    source_id: Literal["larimer-development-review-fees-sd004-07"] = SOURCE_ID
    authority_id: Literal["CO-COUNTY-LARIMER"] = "CO-COUNTY-LARIMER"
    prepared_at: AwareDatetime
    status: Literal["seven_page_native_order_review_preserved"]
    source: Asset
    manual_intake: Asset
    original_intake_line: Asset
    packet_manifest: Asset
    candidate: Asset
    reviewed_text_file: Asset
    custody: Asset
    source_intake_status: Literal["archived_pending_pipeline"] = "archived_pending_pipeline"
    claimed_official_url: str
    original_acquisition_time: None = None
    source_http_acquisition_verified: Literal[False] = False
    legal_currentness: Literal["not_verified"] = "not_verified"
    legal_review: Literal["pending"] = "pending"
    semantic_rule_unit_promotion: Literal[False] = False
    coverage_promotion: Literal[False] = False
    pages: list[PageReview]
    external_finding_dispositions: list[Disposition]
    external_report_consulted_after_independent_source_reviews: Literal[True] = True
    limits: list[str]

    @model_validator(mode="after")
    def complete_page_sequence(self) -> ReviewedNative:
        """Require all seven pages and one disposition for every delivered finding."""
        if [p.physical_page for p in self.pages] != list(range(1, 8)):
            raise ValueError("review must cover exactly seven physical pages in order")
        wanted = {f"EB010-P2-{i:03}" for i in range(1, 13)} | {
            "EB010-RECEIPT-001", "EB010-RECEIPT-002"
        }
        ids = [d.finding_id for d in self.external_finding_dispositions]
        if set(ids) != wanted or len(ids) != len(wanted):
            raise ValueError("external disposition coverage incomplete or duplicated")
        return self


class EvidenceManifest(Strict):
    """Exact package inventory; its own bytes are the sole inventory exclusion."""

    schema_version: Literal[1] = 1
    assignment_id: Literal["EB-PDF-010"] = "EB-PDF-010"
    prepared_at: AwareDatetime
    source_id: Literal["larimer-development-review-fees-sd004-07"] = SOURCE_ID
    status: Literal["bounded_source_review_preserved"]
    package_path: Literal["research/local_review/ebenezer-010-2026-09-11"]
    files: list[Asset]
    source_original: Asset
    file_count: int = Field(ge=1)
    legal_currentness: Literal["not_verified"] = "not_verified"
    no_coverage_or_semantic_promotion: Literal[True] = True
    full_corpus_validation: Literal["not_run_by_this_bounded_intake"]

    @model_validator(mode="after")
    def inventory_unique(self) -> EvidenceManifest:
        """Require a complete, unique declared file count."""
        if self.file_count != len(self.files) or len({f.path for f in self.files}) != len(self.files):
            raise ValueError("manifest count or uniqueness mismatch")
        return self


class ValidationResult(Strict):
    """Machine-readable results from this offline validation invocation."""

    assignment_id: Literal["EB-PDF-010"] = "EB-PDF-010"
    status: Literal["passed"] = "passed"
    files_verified: int
    native_pages_verified: Literal[7] = 7
    exhaustive_native_partitions_verified: Literal[7] = 7
    external_hash_claims_verified: int
    external_source_findings_disposed: Literal[12] = 12
    receipt_defects_preserved_and_rejected_as_fee_literals: Literal[2] = 2
    native_replay: Literal["passed", "not_requested"]
    semantic_or_coverage_promotion: Literal[False] = False
    legal_currentness: Literal["not_verified"] = "not_verified"


def digest(data: bytes | bytearray) -> str:
    """Return the exact SHA-256 of supplied bytes."""
    return hashlib.sha256(data).hexdigest()


def checked_file(root: Path, asset: Asset) -> Path:
    """Verify a repository-relative ordinary file with no symlink traversal."""
    relative = PurePosixPath(asset.path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in asset.path:
        raise ValueError("unsafe evidence path")
    path = root.joinpath(*relative.parts)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("evidence must be an ordinary file")
    content = path.read_bytes()
    if len(content) != asset.size_bytes or digest(content) != asset.sha256:
        raise ValueError(f"evidence size/hash mismatch: {asset.path}")
    return path


def validate_package(root: Path, *, native_replay: bool = False) -> ValidationResult:
    """Verify custody, strict schemas, all page bindings, and byte-preserving reordering."""
    root = root.resolve()
    package = root / PACKAGE
    manifest = EvidenceManifest.model_validate_json((package / "evidence-manifest.json").read_bytes())
    actual = {p.relative_to(root).as_posix() for p in package.rglob("*") if p.is_file()}
    wanted = {f.path for f in manifest.files} | {(PACKAGE / "evidence-manifest.json").as_posix()}
    if actual != wanted:
        raise ValueError("package contains missing or undeclared files")
    for asset in [*manifest.files, manifest.source_original]:
        checked_file(root, asset)
    review = ReviewedNative.model_validate_json((package / "reviewed-native.json").read_bytes())
    custody = Custody.model_validate_json((package / "custody-receipt.json").read_bytes())
    for name, model in (("reviewed-native", review), ("custody-receipt", custody),
                        ("evidence-manifest", manifest)):
        schema = json.loads((package / f"{name}.schema.json").read_bytes())
        Draft202012Validator(schema).validate(model.model_dump(mode="json"))
    if review.source != manifest.source_original:
        raise ValueError("source binding differs between review and inventory")
    for name, schema_name in (
        ("packet-manifest.json", "packet-manifest.schema.json"),
        ("atlas-audits/pages1-3/ATLAS_PAGES_1_3.json",
         "atlas-audits/pages1-3/ATLAS_PAGES_1_3.schema.json"),
        ("atlas-audits/pages4-7/source-review.json", "atlas-audits/pages4-7/source-review.schema.json"),
    ):
        Draft202012Validator(json.loads((package / schema_name).read_bytes())).validate(
            json.loads((package / name).read_bytes())
        )
    for copy in custody.copies:
        checked_file(root, copy.file)
    for claim in custody.hash_claims:
        checked_file(root, claim.bound_file)
    original_receipts = {
        "PASS1_FREEZE_RECEIPT.json": json.loads((package / "reports/PASS1_FREEZE_RECEIPT.txt").read_bytes()),
        "COMPLETION_RECEIPT.json": json.loads((package / "reports/COMPLETION_RECEIPT.txt").read_bytes()),
    }
    expected_claims = {
        (name, key) for name, receipt in original_receipts.items()
        for key, value in receipt["hashes"].items()
        if isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value)
    }
    if {(c.receipt_name, c.claim_key) for c in custody.hash_claims} != expected_claims:
        raise ValueError("not every receipt hash claim has a verified binding")
    if any(r["assignment_id"] != "EB-PDF-010" or r["source_id"] != SOURCE_ID
           for r in original_receipts.values()):
        raise ValueError("external receipt identity differs")
    for claim in custody.hash_claims:
        if original_receipts[claim.receipt_name]["hashes"][claim.claim_key] != claim.claimed_sha256:
            raise ValueError("receipt hash claim was not preserved exactly")
    for defect in custody.receipt_defects:
        payload = json.loads(checked_file(root, defect.receipt_file).read_bytes())
        for part in defect.json_pointer.strip("/").split("/"):
            payload = payload[int(part)] if isinstance(payload, list) else payload[part]
        if payload != defect.received_text:
            raise ValueError("receipt defect text changed")
    candidate = checked_file(root, review.candidate).read_bytes()
    rebuilt = bytearray(candidate)
    packet = json.loads(checked_file(root, review.packet_manifest).read_bytes())
    document = next(d for d in packet["documents"] if d["source_id"] == SOURCE_ID)
    if document["original"]["sha256"] != review.source.sha256:
        raise ValueError("packet PDF binding differs")
    native_schema = json.loads((package / "native-evidence/page.schema.json").read_bytes())
    natives = []
    for page, declared in zip(review.pages, document["pages"], strict=True):
        image = checked_file(root, page.image)
        native_path = checked_file(root, page.native_evidence)
        evidence = json.loads(native_path.read_bytes())
        Draft202012Validator(native_schema).validate(evidence)
        if (evidence["source_id"] != SOURCE_ID or evidence["physical_page"] != page.physical_page
                or evidence["expected_pages"] != 7 or evidence["source_sha256"] != review.source.sha256
                or page.image.sha256 != declared["image"]["sha256"]
                or page.native_evidence.sha256 != declared["evidence"]["sha256"]
                or page.candidate_start_byte != declared["candidate_text_offset_bytes"]
                or page.candidate_end_byte_exclusive != declared["candidate_text_end_byte_exclusive"]):
            raise ValueError("page identity, image, receipt, or candidate offsets differ")
        # PNG IHDR bytes fix dimensions without requiring a Mac image library.
        data = image.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n" or int.from_bytes(data[16:20], "big") != page.image_width:
            raise ValueError("PNG signature or width mismatch")
        if int.from_bytes(data[20:24], "big") != page.image_height:
            raise ValueError("PNG height mismatch")
        native = evidence["text"].encode("utf-8")
        if (digest(native) != page.native_text_sha256 or len(native) != page.native_text_size_bytes
                or evidence["text_sha256"] != page.native_text_sha256
                or evidence["text_size_bytes"] != page.native_text_size_bytes
                or native != candidate[page.candidate_start_byte:page.candidate_end_byte_exclusive]):
            raise ValueError("native receipt or candidate slice differs")
        for segment in page.segments_in_reviewed_order:
            if native[segment.original_start_byte:segment.original_end_byte_exclusive] != segment.text.encode():
                raise ValueError("review segment is not an unchanged original interval")
        rebuilt[page.candidate_start_byte:page.candidate_end_byte_exclusive] = page.reordered_native_text.encode()
        natives.append(evidence["text"])
        checked_file(root, page.review_basis)
    if bytes(rebuilt) != checked_file(root, review.reviewed_text_file).read_bytes():
        raise ValueError("reviewed text file differs from seven exact page reorderings")
    if Counter(rebuilt) != Counter(candidate):
        raise ValueError("whole-candidate byte conservation failed")
    # Existing manual-intake custody stays pending and binds the same source bytes.
    from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord
    intake = ManualSourceIntakeRecord.model_validate_json(checked_file(root, review.manual_intake).read_bytes())
    original_line = checked_file(root, review.original_intake_line).read_bytes()
    if ManualSourceIntakeRecord.model_validate_json(original_line) != intake:
        raise ValueError("intake copy differs from preserved original line")
    if (intake.sha256 != review.source.sha256 or intake.status != "archived_pending_pipeline"
            or intake.record_id != SOURCE_ID or intake.archive_path != review.source.path
            or intake.size_bytes != review.source.size_bytes
            or intake.acquisition_method != "received_review_package"):
        raise ValueError("manual intake does not bind the pending source")
    old_manifest = (package / "packet-custody/pre-intake-manifest.jsonl").read_bytes()
    if (digest(old_manifest) != document["provenance"]["raw_intake_manifest"]["sha256"]
            or old_manifest.splitlines(keepends=True)[7] != original_line):
        raise ValueError("preserved intake line differs from frozen packet custody")
    if native_replay:
        import pymupdf
        with pymupdf.open(checked_file(root, review.source)) as pdf:
            if len(pdf) != 7:
                raise ValueError("source PDF page count mismatch")
            for number, native in enumerate(natives):
                if pdf[number].get_text("text", sort=False, flags=195) != native:
                    raise ValueError(f"native replay differs on physical page {number + 1}")
    return ValidationResult(
        files_verified=len(manifest.files) + 1,
        external_hash_claims_verified=len(custody.hash_claims),
        native_replay="passed" if native_replay else "not_requested",
    )


def main() -> None:
    """Print a strict validation result; never rewrite package files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--native-replay", action="store_true")
    args = parser.parse_args()
    print(validate_package(args.root, native_replay=args.native_replay).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
