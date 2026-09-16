"""Execute the explicitly authorized one-time SD008 raw-custody append."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
from jsonschema import Draft202012Validator

from geode.pipeline.manual_source_intake import (
    MANUAL_INTAKE_LEDGER_PATH,
    MANUAL_INTAKE_MANIFEST_PATH,
    MANUAL_INTAKE_REPORT_PATH,
    ManualSourceIntakeRecord,
    _blocked_queue_contains,
    _validate_reconciliation_record,
    _write_raw_artifact_once,
    reconcile_manual_source_intake,
)
from geode.utils.file_io import snapshot_existing_file

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("intake_validation", PACKAGE / "validate_intake.py")
v = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v
spec.loader.exec_module(v)
AUDIT = ROOT.parent / "handoffs/atlas-reviews/sherlock-source-discovery-008/check-2026-09-11"
DELIVERY = AUDIT / "received"
ATTEMPT = DELIVERY / "20260911T184800Z"


def asset(path: Path, *, local: bool = True) -> v.Asset:
    """Bind exact bytes, using repository-relative paths for canonical evidence."""
    return v.Asset(path=path.relative_to(ROOT).as_posix() if local else str(path),
                   sha256=v.digest(path), size_bytes=path.stat().st_size)


def write_new(path: Path, data: bytes) -> None:
    """Create a new artifact once without overwriting any prior content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def json_bytes(model: v.Strict) -> bytes:
    """Validate a strict model and its JSON Schema before returning serialized bytes."""
    text = model.model_dump_json(indent=2)
    type(model).model_validate_json(text)
    Draft202012Validator(model.model_json_schema()).validate(json.loads(text))
    return (text + "\n").encode()


if (PACKAGE / "intake-receipt.json").exists():
    raise ValueError("intake already completed; use validate_intake.py")
now = datetime.now(timezone.utc)
baseline = reconcile_manual_source_intake(ROOT, dry_run=True)
assert baseline.ledger_records_after == 35 and not baseline.added_intake_ids
assert not baseline.report_needs_update and baseline.report.archive_verification.manifest_records == 34
paths = [ROOT / p for p in [MANUAL_INTAKE_MANIFEST_PATH, MANUAL_INTAKE_LEDGER_PATH,
                            MANUAL_INTAKE_REPORT_PATH]]
before = {p: p.read_bytes() for p in paths}
for p in paths:
    assert not any(x.is_symlink() for x in (p, *p.parents))
for row in json.loads((AUDIT / "CUSTODY_RECEIPT.json").read_text())["files"]:
    for name in ["original_path", "received_path"]:
        p = Path(row[name])
        assert v.digest(p) == row["sha256"] and p.stat().st_size == row["size_bytes"]

source_specs = [
    ("SD008-01", "weld-building-fees-sd008-01", "weld/2026-bldg-fee-schedule.pdf",
     "CO-COUNTY-WELD", "08_County_Authorities", "county_fee_schedule", "SD008-B003", 5,
     [{"value": "JANUARY 2026", "role": "schedule_face_month_year", "qualification":
       "Not an independently verified adoption or effective date."},
      {"value": "Revised 012/25", "role": "literal_revision_notation", "qualification":
       "Source notation preserved exactly; not normalized into an ISO date."}]),
    ("SD008-06", "greeley-building-fees-sd008-06", "greeley/building_permit_fee_schedule.pdf",
     "CO-MUNICIPAL-GREELEY", "10_Municipal_Authorities", "municipal_building_fee_schedule",
     "SD008-E035", 1,
     [{"value": "2024", "role": "schedule_title_year", "qualification":
       "The title is not evidence that the document is legally current."},
      {"value": "Effective -2024", "role": "printed_table_header", "qualification":
       "Source label only; no exact effective day or adoption instrument verified."},
      {"value": "8/18/2026", "role": "unlabeled_footer", "qualification":
       "Role unknown; do not label adoption, publication or effectiveness."}]),
    ("SD008-07", "greeley-development-impact-fee-memo-sd008-07",
     "greeley/2026_development_impact_fee_schedule.pdf", "CO-MUNICIPAL-GREELEY",
     "10_Municipal_Authorities", "fee_adjustment_memorandum_with_schedules", "SD008-E036", 3,
     [{"value": "November 1, 2025", "role": "memorandum_date", "qualification":
       "Finance memorandum, not the cited 2023 adopting ordinance."},
      {"value": "March 1, 2026", "role": "memorandum_stated_effective_date", "qualification":
       "Page 2 statement; independent adoption and later changes not reconciled."},
      {"value": "December", "role": "prospective_water_sewer_pif_adoption", "qualification":
       "Water/Sewer PIFs are separate and stated as future adoption; not included as adopted rates."}]),
    ("SD008-08", "greeley-water-sewer-proposed-pif-notice-sd008-08",
     "greeley/2021_water_sewer_plant_investment_fees.pdf", "CO-MUNICIPAL-GREELEY",
     "10_Municipal_Authorities", "proposed_utility_fee_notice_with_schedule", "SD008-E037", 2,
     [{"value": "November 20, 2020", "role": "notice_date", "qualification":
       "Pre-adoption notice by Greeley Water and Sewer to Weld County addressees."},
      {"value": "December 16, 2020", "role": "planned_board_consideration", "qualification":
       "The notice describes future review for adoption; outcome unverified."},
      {"value": "March 1, 2021", "role": "proposed_conditional_effective_date", "qualification":
       "Page 1 expressly says assuming they are adopted; page 2 EFFECTIVE heading is subordinate "
       "to that condition."}]),
]
events = {r["event_id"]: r for r in json.loads((DELIVERY / "attempted_urls.json").read_text())["events"]}
audit = json.loads((AUDIT / "INTAKE_AUDIT.json").read_text())
source_audits = {r["priority_id"]: r for r in audit["source_checks"]}
source_paths = [ATTEMPT / "raw" / row[2] for row in source_specs]
sizes = {p.stat().st_size for p in source_paths}
sha_values = {v.digest(p) for p in source_paths}
assert len(sha_values) == 4
ordinary = 0
matching_size = 0
raw_stats = {}
for p in (ROOT / "_RAW_ARCHIVE").rglob("*"):
    assert not p.is_symlink()
    if not p.is_file():
        continue
    ordinary += 1
    raw_stats[p] = (p.stat().st_size, p.stat().st_mtime_ns)
    if p.stat().st_size in sizes:
        matching_size += 1
        assert v.digest(p) not in sha_values
assert ordinary == 538 and matching_size == 0
for p in paths[:2]:
    for line in p.open():
        row = ManualSourceIntakeRecord.model_validate_json(line)
        assert row.sha256 not in sha_values
        assert row.record_id not in {item[1] for item in source_specs}
dedupe = v.DedupeCheck(checked_at=now, ordinary_files_size_screened=ordinary,
                       matching_size_files_hashed=matching_size, symlinks_encountered=0,
                       raw_manifest_records_checked=34, ledger_records_checked=35,
                       exact_digest_matches=0, method=
                       "All ordinary raw files size screened; matching sizes require SHA256 equality")
copies = []
for origin, relative in [
    *[(AUDIT / n, "evidence/audits/" + n) for n in
      ["INTAKE_AUDIT.md", "INTAKE_AUDIT.json", "INTAKE_AUDIT.schema.json", "CUSTODY_RECEIPT.json",
       "CUSTODY_RECEIPT.schema.json", "pinned-comparison-facts.json"]],
    *[(DELIVERY / n, "evidence/supplied/" + n) for n in
      ["report-20260911T185715Z.md", "priority_candidates_final.json", "attempted_urls.json",
       "artifact_inventory.json", "backlog.json"]],
    (ATTEMPT / "derived/weld_2026_bldg_fee_extract.json",
     "evidence/supplied/weld_2026_bldg_fee_extract.json"),
    (ATTEMPT / "raw/greeley/building_permits_and_inspections.html",
     "evidence/referrals/building_permits_and_inspections.html"),
]:
    target = PACKAGE / relative
    write_new(target, origin.read_bytes())
    copies.append(v.Copy(original=asset(origin, local=False), preserved=asset(target)))
referral_path = PACKAGE / "evidence/referrals/building_permits_and_inspections.html"
anchors = v.Anchors()
anchors.feed(referral_path.read_text())
records = []
provenance = []
for priority, source_id, relative, owner, layer, role, event_id, pages, dates in source_specs:
    source = ATTEMPT / "raw" / relative
    sa = source_audits[priority]
    assert v.digest(source) == sa["primary"]["sha256"]
    with pymupdf.open(source) as pdf:
        assert len(pdf) == pages and not pdf.is_repaired and not pdf.is_encrypted
        for page in pdf:
            page.get_text()
    event = events[event_id]
    destination = (ROOT / "_RAW_ARCHIVE/manual_intake" / layer / source_id /
                   f"{now.strftime('%Y%m%dT%H%M%SZ')}_{source.name}")
    assert not destination.exists()
    reason = ("successful_version_and_final_url_unconfirmed" if owner == "CO-COUNTY-WELD"
              else "direct_host_not_in_existing_allowlist")
    note = ("Sherlock SD008 received review package; original and frozen delivery bytes rehashed. "
            "Atlas source-role/date audit retained in research/local_review/"
            "weld-greeley-intake-sherlock008-2026-09-11. No new source request by this intake. ")
    if owner == "CO-COUNTY-WELD":
        note += ("Successful requested version and final URL remain unconfirmed; supplied /v/3 is "
                 "reconstructed context only. Face JANUARY 2026 and literal Revised 012/25 do not "
                 "certify adoption/effectiveness. official_source_url is null. ")
    else:
        note += ("Exact official Greeley HTML anchor, retained curl body and response metadata "
                 "support supplied Sitecore URL; direct host is outside the existing intake "
                 "allowlist, so official_source_url is null and URL/proof stays in provenance. ")
    note += " ".join(sa["qualifications"])
    record = ManualSourceIntakeRecord(
        intake_id=f"MSI-{now.strftime('%Y%m%dT%H%M%S%fZ')}-{source_id}", record_id=source_id,
        layer_id=layer, official_source_name=("Weld County Building Inspection Division"
                 if owner == "CO-COUNTY-WELD" else "City of Greeley"),
        official_source_url=None, acquisition_method="received_review_package",
        received_from="Sherlock SD008 retained review package, independently checked by Atlas",
        reviewer_name="Atlas (Codex)", custody_note=note, original_filename=source.name,
        archive_path=destination.relative_to(ROOT).as_posix(), sha256=v.digest(source),
        size_bytes=source.stat().st_size, source_format="pdf", received_at=now,
        status="archived_pending_pipeline", blocked_queue_match=_blocked_queue_contains(ROOT, source_id),
        boundary="Byte custody only; no interpretation, adopted-status, legal-currentness, rule, "
                 "coverage or pipeline-completion promotion.",
    )
    _validate_reconciliation_record(ROOT, record)
    assert not record.blocked_queue_match
    http = None
    label = None
    if owner != "CO-COUNTY-WELD":
        original_header = ATTEMPT / "logs" / f"{event_id}.headers.txt"
        body = original_header.read_bytes()
        cleaned = b"".join(line for line in body.splitlines(keepends=True)
                           if not line.lower().startswith(b"set-cookie:"))
        derived = PACKAGE / "evidence/http" / f"{event_id}.headers-without-cookies.txt"
        write_new(derived, cleaned)
        metadata = {}
        for line in body.decode().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.lower()] = value.strip()
        http = v.HttpEvidence(
            original_header=asset(original_header, local=False),
            derived_header_without_cookies=asset(derived),
            transformation="Only Set-Cookie header lines omitted; other bytes unchanged",
            content_length=int(metadata["content-length"]), response_date=metadata["date"],
            last_modified=metadata["last-modified"],
        )
        label = next(label for url, label in anchors.links if url == event["requested_url"])
    canonical = v.Asset(path=record.archive_path, sha256=record.sha256, size_bytes=record.size_bytes)
    pr = v.SourceProvenance(
        source_id=source_id, authority_id=owner, priority_id=priority, event_id=event_id,
        source_role=role, received_original=asset(source, local=False), canonical_original=canonical,
        intake_id=record.intake_id, repository_received_at=now,
        reported_acquisition_at=(None if http is None else
            datetime.fromisoformat(event["observed_at_utc"].replace("Z", "+00:00"))),
        reported_requested_url=event["requested_url"],
        reported_final_url=event["final_url"] if http else None,
        reported_method="mac_curl" if http else "box_browser_reconstructed",
        acquisition_evidence="retained_curl_body_and_headers" if http else "reconstructed_browser",
        null_official_source_url_reason=reason,
        official_referral_url=("https://greeleyco.gov/business/construction-and-growth/"
                               "building-permits-and-inspections/" if http else None),
        official_referral_label=label, official_referral_html=asset(referral_path) if http else None,
        http_evidence=http, document_dates=[v.SourceDate(**r) for r in dates], page_count=pages,
        prior_visual_audit="evidence/audits/INTAKE_AUDIT.json#/source_checks/" +
                           str(next(i for i, r in enumerate(audit["source_checks"])
                                    if r["priority_id"] == priority)),
        prior_visual_pages=sa["inspected_physical_pages"],
        this_intake_inspection="PDF_structure_and_custody_only",
        qualifications=sa["qualifications"],
    )
    json_bytes(pr)
    records.append(record)
    provenance.append(pr)

# Final compare-before-write guard; no canonical mutation occurred above.
for p, content in before.items():
    assert p.read_bytes() == content
transaction = PACKAGE / "evidence/transaction"
for p, name in zip(paths, ["raw-manifest", "ledger", "report"], strict=True):
    write_new(transaction / (name + ".before" + p.suffix), before[p])
pre_snapshots = set((ROOT / "_SNAPSHOTS").rglob("*"))
for record, source in zip(records, source_paths, strict=True):
    _write_raw_artifact_once(ROOT / record.archive_path, source.read_bytes())
    assert v.digest(ROOT / record.archive_path) == record.sha256
raw_snapshot = snapshot_existing_file(paths[0], ROOT)
assert raw_snapshot is not None
suffix = "".join(r.model_dump_json() + "\n" for r in records).encode()
assert before[paths[0]].endswith(b"\n")
raw_tmp = paths[0].with_name(paths[0].name + ".sd008.tmp")
write_new(raw_tmp, before[paths[0]] + suffix)
assert paths[0].read_bytes() == before[paths[0]]
os.replace(raw_tmp, paths[0])
preview = reconcile_manual_source_intake(ROOT, dry_run=True)
assert preview.added_intake_ids == [r.intake_id for r in records]
assert preview.ledger_records_before == 35 and preview.ledger_records_after == 39
applied = reconcile_manual_source_intake(ROOT, dry_run=False)
repeat = reconcile_manual_source_intake(ROOT, dry_run=True)
assert not repeat.added_intake_ids and not repeat.report_needs_update
assert paths[0].read_bytes() == before[paths[0]] + suffix
assert paths[1].read_bytes() == before[paths[1]] + suffix
for p, info in raw_stats.items():
    if p != paths[0]:
        assert (p.stat().st_size, p.stat().st_mtime_ns) == info
new_snapshots = sorted(p for p in set((ROOT / "_SNAPSHOTS").rglob("*")) - pre_snapshots
                       if p.is_file())
assert len(new_snapshots) == 3
for p, name in zip(paths, ["raw-manifest", "ledger", "report"], strict=True):
    write_new(transaction / (name + ".after" + p.suffix), p.read_bytes())
write_new(PACKAGE / "intake-records.jsonl", suffix)
write_new(PACKAGE / "source-provenance.jsonl",
          "".join(p.model_dump_json() + "\n" for p in provenance).encode())
receipt = v.IntakeReceipt(
    assignment="sherlock008-received-pdf-intake", prepared_at=now, deduplication=dedupe,
    evidence_copies=copies, source_provenance=asset(PACKAGE / "source-provenance.jsonl"),
    intake_records=asset(PACKAGE / "intake-records.jsonl"),
    raw_manifest_before=asset(transaction / "raw-manifest.before.jsonl"),
    raw_manifest_after=asset(transaction / "raw-manifest.after.jsonl"),
    ledger_before=asset(transaction / "ledger.before.jsonl"),
    ledger_after=asset(transaction / "ledger.after.jsonl"),
    report_before=asset(transaction / "report.before.json"),
    report_after=asset(transaction / "report.after.json"),
    preimage_snapshots=[asset(p) for p in new_snapshots],
    new_raw_paths=[r.archive_path for r in records], baseline=baseline,
    pre_apply_dry_run=preview, applied=applied, idempotency_dry_run=repeat,
    api_usage="Existing ManualSourceIntakeRecord validation, write-once raw helper, exact-prefix "
              "raw manifest append and reconcile_manual_source_intake dry-run/apply were used. "
              "The official-only request API cannot truthfully encode received_review_package. "
              "No intake policy/allowlist or blocked queue was changed.",
    limits=["New source URLs are null in manual records; exact Greeley Sitecore source and official "
            "referral proof remain in provenance because direct host is outside the current allowlist.",
            "Weld's reconstructed /v/3 request is unconfirmed, not equivalent to a supported Greeley "
            "curl response; final URL and acquisition time remain null.",
            "Document dates retain their roles; PIF March 1, 2021 is conditional on adoption.",
            "Structural page checks do not certify all numerical cells, legal interpretation or currency.",
            "Existing missing LFS data and the one missing ledger-only EO original remain unresolved.",
            "Report, ledger and manifest writes are individually atomic/snapshotted, not a single "
            "all-files transaction; repeat reconciliation is verified idempotent."])
write_new(PACKAGE / "intake-receipt.json", json_bytes(receipt))
for name, model in [("intake-receipt", v.IntakeReceipt),
                    ("source-provenance", v.SourceProvenance),
                    ("intake-record", ManualSourceIntakeRecord)]:
    write_new(PACKAGE / (name + ".schema.json"),
              (json.dumps(model.model_json_schema(), indent=2) + "\n").encode())
print(json.dumps(v.validate_intake(ROOT), indent=2))
print("NEW RAW FILES")
for r in records:
    print(r.archive_path, r.sha256, r.size_bytes)
