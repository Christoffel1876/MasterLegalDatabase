"""Read-only portable verification; optional current-repository baseline check. No apply mode."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import jsonschema
import pymupdf
from bs4 import BeautifulSoup
from PIL import Image

from preparation_models import Asset, Inventory, Preparation, RecordTemplate, Source

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    """Fail validation even when Python assertions are disabled."""
    if not condition:
        raise ValueError(message)


def checked(root: Path, item: Asset) -> bytes:
    """Reject path escapes/symlinks and require the exact ordinary bytes."""
    relative = Path(item.path)
    require(bool(relative.parts) and not relative.is_absolute() and ".." not in relative.parts,
            f"Unsafe path: {item.path}")
    path = root / relative
    require(not any(p.is_symlink() for p in (path, *path.parents)), f"Symlink: {item.path}")
    require(path.is_file(), f"Missing file: {item.path}")
    data = path.read_bytes()
    require(len(data) == item.size_bytes and hashlib.sha256(data).hexdigest() == item.sha256,
            f"Changed file: {item.path}")
    return data


def validate_json(data: bytes, schema: dict) -> None:
    """Validate a retained JSON or JSONL record using its frozen schema."""
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(json.loads(data))


def validate(repo_root: Path | None = None) -> dict[str, object]:
    """Verify custody, issuer decisions and exactly the recorded twenty-page scope."""
    inventory = Inventory.model_validate_json((BASE / "FINAL_MANIFEST.json").read_bytes())
    require(json.loads((BASE / "FINAL_MANIFEST.schema.json").read_bytes()) ==
            Inventory.model_json_schema(), "Inventory schema differs")
    require(inventory.exclusions == ["FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"],
            "Unexpected inventory exclusions")
    actual = set()
    for p in BASE.rglob("*"):
        require(not p.is_symlink(), "Symlink anywhere in package")
        if p.is_file():
            actual.add(p.relative_to(BASE).as_posix())
    require(actual == {x.path for x in inventory.files} | set(inventory.exclusions),
            "Package file membership changed")
    require(len({x.path for x in inventory.files}) == len(inventory.files), "Duplicate inventory path")
    for item in inventory.files:
        checked(BASE, item)
    raw = (BASE / "PREPARATION.json").read_bytes()
    proposal = Preparation.model_validate_json(raw)
    schema = json.loads((BASE / "PREPARATION.schema.json").read_bytes())
    require(schema == Preparation.model_json_schema(), "Preparation schema differs")
    validate_json(raw, schema)
    require(proposal.audit.sha256 == proposal.audit_sha256, "Wrong pinned audit")
    audit = json.loads(checked(BASE, proposal.audit))
    validate_json(checked(BASE, proposal.audit),
                  json.loads((BASE / "inputs/audit/AUDIT.schema.json").read_bytes()))
    receipt = json.loads((BASE / "inputs/audit/CUSTODY_RECEIPT.json").read_bytes())
    require(audit["comparison_commit"] == proposal.comparison_commit, "Comparison pin differs")
    require(audit["counts"]["public_events"] == audit["counts"]["distinct_requested"] == 66,
            "Upstream event count falsely repaired")
    require(audit["public_distinct_cap_status"] == proposal.upstream_cap_status == "failed",
            "Upstream cap breach lost")
    require(audit["missing_earlier_body_digests"] == proposal.upstream_missing_body_sha256,
            "Missing upstream bodies concealed")
    candidates = audit["pdf_intake_proposals"]
    require([x["proposed_source_id"] for x in candidates] == [s.source_id for s in proposal.sources],
            "Source set differs from frozen fifteen-PDF audit")
    excluded = {s.source_id for s in proposal.sources if s.decision == "defer_issuer_layer_decision"}
    require(excluded == {"el-paso-school-district-fees-sd011",
                         "el-paso-hosted-cgs-review-guide-sd011"}, "Wrong deferred sources")
    events = {x["event_id"]: x for x in audit["events"]}
    copy_map = {c.preserved.path: c for c in proposal.custody}
    require(len(copy_map) == len(proposal.custody), "Duplicate copied input")
    for c in proposal.custody:
        require(checked(BASE, c.preserved) is not None, "Missing copied input")
        require(c.original_sha256 == c.preserved.sha256, "Exact copy changed")
        if c.method == "audited_public_header_derivative":
            require(c.preserved.path.startswith("inputs/public-headers/"), "Wrong header destination")
            header = next(h for h in audit["header_derivatives"]
                          if "inputs/" + h["derivative"]["path"] == c.preserved.path)
            require(header["derivative"]["sha256"] == c.preserved.sha256 and
                    header["original"]["sha256"] == c.excluded_raw_header_sha256,
                    "Header derivative proof mismatch")
    receipt_files = {x["frozen_path"]: x for x in receipt["files"]}
    total_native, page_count, observations = 0, 0, 0
    require(pymupdf.VersionBind == "1.28.2", "Native extraction version differs")
    for source, candidate in zip(proposal.sources, candidates, strict=True):
        source_bytes = checked(BASE, source.original)
        require(source.original.sha256 == candidate["source"]["sha256"] and
                source.original.size_bytes == candidate["source"]["size_bytes"], "PDF custody differs")
        cust = receipt_files[source.received_body_path]
        require(cust["sha256"] == source.original.sha256 and cust["size_bytes"] == len(source_bytes),
                "PDF missing from frozen received custody")
        event = events[source.event_id]
        require(event["body_matches_claim"] is True and
                event["body_sha256_claim"] == source.original.sha256 and
                event["body_size_claim"] == source.original.size_bytes, "Event/PDF body mismatch")
        require(source.requested_url_claim == event["requested_url"] == candidate["requested_url"]
                and source.final_url_claim == event["final_url_claim"] == candidate["final_url"],
                "URL claim binding differs")
        require(source.acquisition_started_at_claim.isoformat().replace("+00:00", "Z") ==
                event["started_at_claim"] and
                source.acquisition_completed_at_claim.isoformat().replace("+00:00", "Z") ==
                event["completed_at_claim"], "Claimed acquisition time altered")
        require(source.atlas_delivery_captured_at.isoformat().replace("+00:00", "Z") ==
                receipt["captured_at"], "Atlas receipt was replaced with upstream claim")
        require(source.atlas_preparation_copied_at == proposal.prepared_at and
                source.acquisition_completed_at_claim <= source.atlas_delivery_captured_at <=
                source.atlas_preparation_copied_at, "Custody chronology invalid")
        host = urlparse(source.final_url_claim).hostname
        require(host == "epc-assets.elpasoco.com", "Unreviewed final host")
        header = checked(BASE, source.public_headers)
        require(not re.search(rb"(?im)^(set-cookie|cookie|authorization|proxy-authorization)\s*:",
                              header), "Sensitive header copied")
        status_codes = [int(x) for x in re.findall(rb"(?m)^HTTP/\S+\s+(\d{3})", header)]
        locations = [x.decode().strip() for x in re.findall(rb"(?im)^location:\s*([^\r\n]+)", header)]
        destination = source.requested_url_claim
        hops = []
        for location in locations:
            destination = urljoin(destination, location); hops.append(destination)
        require(status_codes == source.observed_http_statuses == event["observed_response_statuses"]
                and hops == source.observed_redirect_destinations == event["resolved_redirect_destinations"]
                and destination == source.final_url_claim and status_codes[-1] == 200,
                "Stored HTTP chain mismatch")
        require(len(source.source_referrals) == len(candidate["source_referrals"]),
                "Missing or invented referral")
        for ref, saved in zip(source.source_referrals, candidate["source_referrals"], strict=True):
            require(ref.parent.sha256 == saved["parent"]["sha256"], "Wrong referral body")
            require(all(getattr(ref, k) == saved[k] for k in ["event_id", "parent_url", "href",
                                                            "resolved_url", "anchor_text"]),
                    "Referral claim differs")
            soup = BeautifulSoup(checked(BASE, ref.parent), "html.parser")
            base = soup.find("base", href=True)
            base_url = urljoin(ref.parent_url, base["href"]) if base else ref.parent_url
            matches = [a for a in soup.find_all("a", href=True)
                       if a["href"] == ref.href and urljoin(base_url, a["href"]) == ref.resolved_url
                       and " ".join(a.get_text(" ", strip=True).split()) == ref.anchor_text]
            require(bool(matches), "Preserved HTML lacks the claimed labeled anchor")
            require(ref.resolved_url == source.requested_url_claim, "Anchor is not the selected PDF")
        require(bool(source.source_referrals) ==
                (source.referral_basis == "preserved_official_html_anchor"), "Referral limitation lost")
        require(source.historical_matching_rows == candidate["historical_matching_rows"] and
                source.historical_source_ids == candidate["historical_source_ids"], "Legacy claims changed")
        require(source_bytes.startswith(b"%PDF-") and source_bytes.rstrip().endswith(b"%%EOF"),
                "Invalid PDF signature or tail")
        with pymupdf.open(stream=source_bytes, filetype="pdf") as pdf:
            require(len(pdf) == source.source_pages == candidate["pages"] and
                    not pdf.is_repaired and not pdf.is_encrypted, "PDF structure differs")
            native_by_page = {}
            for page in source.directly_viewed_pages:
                native = checked(BASE, page.native)
                require(pdf[page.physical_page - 1].get_text("text", flags=195, sort=False).encode()
                        == native, "Native page extraction changed")
                require(bool(native.decode().strip()) == page.native_nonwhitespace,
                        "Empty native text mislabeled")
                native_by_page[page.physical_page] = native
                checked(BASE, page.image)
                with Image.open(BASE / page.image.path) as image:
                    rect = pdf[page.physical_page - 1].rect
                    require(abs(image.width - rect.width * 2) <= 1 and
                            abs(image.height - rect.height * 2) <= 1,
                            "Image is not a full 144dpi source page")
                total_native += len(native); page_count += 1
            for observation in source.observations:
                if observation.native_anchor:
                    span = observation.native_anchor
                    require(native_by_page[observation.physical_page][span.start:span.end] ==
                            span.text.encode() and hashlib.sha256(span.text.encode()).hexdigest() ==
                            span.sha256, "Exact native anchor changed")
                observations += 1
    require(page_count == 20, "Visual extent count mismatch")
    raw_schema = json.loads((BASE / "ManualSourceIntakeRecord.schema.json").read_bytes())
    baseline_rows = {}
    for baseline in proposal.baseline:
        content = checked(BASE, baseline.preserved)
        if repo_root:
            require(checked(repo_root, Asset(path=baseline.repository_path,
                                            sha256=baseline.preserved.sha256,
                                            size_bytes=baseline.preserved.size_bytes)) == content,
                    "Current preimage changed")
        if baseline.records is not None:
            require(content.endswith(b"\n"), "Cannot append exact-prefix JSONL without terminal LF")
            rows = []
            with (BASE / baseline.preserved.path).open("rb") as stream:
                for line in stream:
                    validate_json(line, raw_schema); rows.append(json.loads(line))
            require(len(rows) == baseline.records, "Baseline count differs")
            baseline_rows[baseline.repository_path] = rows
    row_sets = list(baseline_rows.values())
    require([len(x) for x in row_sets] == [proposal.dedupe.raw_records, proposal.dedupe.ledger_records]
            == [46, 47], "Wrong baseline counts")
    ids = {s.source_id for s in proposal.sources}
    digests = {s.original.sha256 for s in proposal.sources}
    require(not any(r["record_id"] in ids or r["sha256"] in digests for rows in row_sets for r in rows),
            "Baseline has candidate collision")
    ledger = json.loads(next(checked(BASE, b.preserved) for b in proposal.baseline
                            if b.repository_path.endswith("LOCAL_COVERAGE_LEDGER.json")))
    authority = [a for a in ledger["authorities"] if a["authority_id"] == "CO-COUNTY-EL_PASO"]
    require(len(authority) == 1 and authority[0]["level"] == "county" and
            authority[0]["name"] == "El Paso County", "County identity is not explicit in baseline")
    for filename, model, expected in [
        ("source-provenance", Source, proposal.sources),
        ("proposed-records", RecordTemplate, proposal.proposed_records),
    ]:
        require(json.loads((BASE / f"{filename}.schema.json").read_bytes()) == model.model_json_schema(),
                f"Changed {filename} schema")
        with (BASE / f"{filename}.jsonl").open("rb") as stream:
            require([model.model_validate_json(line) for line in stream] == expected,
                    f"Changed {filename} rows")
    # Validate compatibility of known fields with the existing record schema, in memory only.
    # The clearly synthetic ID/time/path below are never saved as intake evidence.
    for r in proposal.proposed_records:
        probe = dict(intake_id="VALIDATION-ONLY", record_id=r.record_id, layer_id=r.layer_id,
                     official_source_name=r.official_source_name, official_source_url=r.official_source_url,
                     acquisition_method=r.acquisition_method, received_from=r.received_from,
                     reviewer_name=r.reviewer_name, reviewer_email=None, custody_note=r.custody_note,
                     original_filename="original.pdf", archive_path="VALIDATION-ONLY-NOT-A-DESTINATION",
                     sha256=r.expected_sha256, size_bytes=r.size_bytes, source_format=r.source_format,
                     received_at=proposal.prepared_at.isoformat(), status=r.intended_record_status,
                     blocked_queue_match=False, boundary="Schema probe only; never applied.")
        validate_json(json.dumps(probe).encode(), raw_schema)
    if repo_root:
        sizes = {s.original.size_bytes for s in proposal.sources}
        for folder, dirs, files in os.walk(repo_root / "_RAW_ARCHIVE", followlinks=False):
            require(not any((Path(folder) / name).is_symlink() for name in dirs + files),
                    "Raw symlink requires separate dedupe review")
            for name in files:
                p = Path(folder) / name
                if p.is_file() and p.stat().st_size in sizes:
                    require(hashlib.sha256(p.read_bytes()).hexdigest() not in digests,
                            "New raw collision; do not apply this stale proposal")
    return {"status": "prepared_not_applied", "mode": "current_baseline" if repo_root else "portable",
            "sources": 15, "proposed_county_records": 13, "deferred": sorted(excluded),
            "source_structural_pages": 351, "directly_viewed_pages": page_count,
            "native_bytes_for_viewed_pages": total_native, "bounded_observations": observations,
            "full_fee_table_reviews": 0, "raw_records_unchanged": 46, "ledger_records_unchanged": 47,
            "cap_breach_preserved": "66 distinct targets / 50 cap",
            "original_acquisition_independently_verified": False, "legal_currentness": "not_verified",
            "production_mutations": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("%s", json.dumps(validate(args.repo_root.absolute() if args.repo_root else None), indent=2))
