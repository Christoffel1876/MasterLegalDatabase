"""Build this handoff once; never invoke production intake or write repository data."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from preparation_models import Asset, Copy, Dedupe, Preparation, RecordTemplate, Source
from source_notes import NOTES

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2] / "MasterLegalDatabase"
AUDIT_ROOT = BASE.parent / "sherlock011-atlas-audit"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO))
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord


def asset(path: Path, root: Path = BASE) -> dict[str, str | int]:
    """Hash exact bytes under a named evidence root."""
    data = path.read_bytes()
    return Asset(path=path.relative_to(root).as_posix(),
                 sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data)).model_dump()


def save(path: Path, data: bytes) -> None:
    """Create new output atomically and refuse to alter a different existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refuse overwrite: {path}")
        return
    temp = path.with_name(path.name + ".tmp")
    with temp.open("xb") as handle:
        handle.write(data)
    os.replace(temp, path)


def encoded(value: object) -> bytes:
    """Encode readable deterministic JSON."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build() -> Preparation:
    """Freeze current custody and known record fields without executing intake."""
    if (BASE / "PREPARATION.json").exists():
        raise ValueError("Preparation exists; verification is read-only")
    now = datetime.now(timezone.utc).isoformat()
    audit = json.loads((BASE / "inputs/audit/AUDIT.json").read_bytes())
    copies: dict[str, Copy] = {}

    def copy(original: Path, relative: str, *, raw_header_sha: str | None = None) -> dict:
        """Preserve a checked input or an already audited public-header derivative."""
        data = original.read_bytes()
        save(BASE / relative, data)
        item = Copy(original_path=str(original), original_sha256=hashlib.sha256(data).hexdigest(),
                    preserved=Asset.model_validate(asset(BASE / relative)),
                    method="audited_public_header_derivative" if raw_header_sha else "exact_copy",
                    excluded_raw_header_sha256=raw_header_sha)
        copies[relative] = item
        return item.preserved.model_dump()

    for p in sorted((BASE / "inputs/audit").iterdir()):
        copy(AUDIT_ROOT / p.name, p.relative_to(BASE).as_posix())
    baseline = []
    current_paths = [
        "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl",
        "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl",
        "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json",
        "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_POLICY.json",
        "_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json",
        "geode/pipeline/manual_source_intake.py", "AGENTS.md",
    ]
    all_rows: dict[str, list[ManualSourceIntakeRecord]] = {}
    for name in current_paths:
        frozen = copy(REPO / name, "inputs/current/" + name)
        rows = None
        if name.endswith(".jsonl"):
            parsed = []
            with (BASE / frozen["path"]).open("rb") as handle:
                for line in handle:
                    parsed.append(ManualSourceIntakeRecord.model_validate_json(line))
            all_rows[name] = parsed
            rows = len(parsed)
        baseline.append({"repository_path": name, "preserved": frozen, "records": rows})
    for name in [
        "research/local_review/weld-directed-intake-2026-09-11/validate_preparation.py",
        "research/local_review/weld-directed-intake-2026-09-11/README.md",
        "research/local_review/mesa-grand-junction-directed-intake-2026-09-11/INTAKE_RECEIPT.json",
        "research/local_review/mesa-grand-junction-directed-intake-2026-09-11/validate_intake.py",
        "research/local_review/weld-greeley-intake-sherlock008-2026-09-11/README.md",
        "research/local_review/weld-greeley-intake-sherlock008-2026-09-11/validate_intake.py",
    ]:
        copy(REPO / name, "inputs/precedent/" + name)
    save(BASE / "ManualSourceIntakeRecord.schema.json", encoded(
        ManualSourceIntakeRecord.model_json_schema()))
    proposals = audit["pdf_intake_proposals"]
    events = {e["event_id"]: e for e in audit["events"]}
    headers = {Path(h["derivative"]["path"]).name: h for h in audit["header_derivatives"]}
    sources = []
    records = []
    for candidate in proposals:
        sid = candidate["proposed_source_id"]
        notes = NOTES[sid]
        original = copy(AUDIT_ROOT / candidate["source"]["path"],
                        f"sources/{sid}/original.pdf")
        event = events[candidate["event_id"]]
        h = headers[candidate["event_id"] + ".headers.txt"]
        public = copy(AUDIT_ROOT / h["derivative"]["path"],
                      "inputs/" + h["derivative"]["path"],
                      raw_header_sha=h["original"]["sha256"])
        refs = []
        for r in candidate["source_referrals"]:
            p = copy(AUDIT_ROOT / r["parent"]["path"],
                     "inputs/referrals/" + r["event_id"] + ".html")
            refs.append({k: r[k] for k in ["event_id", "parent_url", "href", "resolved_url",
                                          "anchor_text"]} | {"parent": p})
            h2 = headers[r["event_id"] + ".headers.txt"]
            copy(AUDIT_ROOT / h2["derivative"]["path"], "inputs/" + h2["derivative"]["path"],
                 raw_header_sha=h2["original"]["sha256"])
        pages = sorted({x[0] for x in notes["observations"]})
        page_records = []
        for page in pages:
            image = next((BASE / "images").glob(f"{sid}-{page:0{len(str(candidate['pages']))}}.png"))
            native = BASE / "native" / f"{sid}-p{page:03}.txt"
            page_records.append({"physical_page": page, "image": asset(image),
                                 "native": asset(native),
                                 "native_nonwhitespace": bool(native.read_text().strip()),
                                 "view_scope": "full_page_for_title_issuer_role_and_selected_date_context",
                                 "numeric_table_certification": False})
        observations, dates = [], []
        for i, (page, region, visible, anchor, conclusion, uncertainty, date, role) in enumerate(
            notes["observations"], 1
        ):
            raw = (BASE / "native" / f"{sid}-p{page:03}.txt").read_bytes()
            span = None
            if anchor:
                needle = anchor.encode()
                start = raw.find(needle)
                if start < 0:
                    raise ValueError(f"Missing uncorrected native anchor: {sid}: {anchor!r}")
                span = {"start": start, "end": start + len(needle), "text": anchor,
                        "sha256": hashlib.sha256(needle).hexdigest()}
            oid = f"{sid}-O{i:02}"
            observations.append({"observation_id": oid, "physical_page": page, "region": region,
                                 "visible_text": visible, "native_anchor": span,
                                 "conclusion": conclusion, "uncertainty": uncertainty,
                                 "legal_currentness": "not_verified"})
            if date:
                dates.append({"value": date, "role": role, "observation_id": oid,
                              "independently_verified": False})
        included = notes["kind"] not in {"unresolved_school_fee_issuer", "colorado_geological_survey"}
        source = dict(
            source_id=sid, decision="propose_county_intake" if included else "defer_issuer_layer_decision",
            authority_id="CO-COUNTY-EL_PASO" if included else None,
            layer_id="08_County_Authorities" if included else None,
            issuer_as_shown=notes["issuer"], issuer_kind=notes["kind"], document_role=notes["role"],
            title_for_intake=notes["title"], language="es" if "spanish" in sid else "en",
            original=original, received_body_path=candidate["source"]["path"],
            source_pages=candidate["pages"], event_id=event["event_id"],
            requested_url_claim=event["requested_url"], final_url_claim=event["final_url_claim"],
            acquisition_started_at_claim=event["started_at_claim"],
            acquisition_completed_at_claim=event["completed_at_claim"],
            upstream_acquisition_independently_verified=False, verified_http_acquired_at=None,
            atlas_delivery_captured_at=candidate["custody_captured_at"],
            atlas_preparation_copied_at=now, actual_repository_received_at=None,
            public_headers=public, observed_http_statuses=event["observed_response_statuses"],
            observed_redirect_destinations=event["resolved_redirect_destinations"],
            source_referrals=refs, referral_basis="preserved_official_html_anchor" if refs else
            "inherited_url_no_fresh_anchor", historical_matching_rows=candidate["historical_matching_rows"],
            historical_source_ids=candidate["historical_source_ids"], directly_viewed_pages=page_records,
            observations=observations, date_claims=dates, verified_adoption_date=None,
            verified_effective_date=None, legal_currentness="not_verified", answer_safe=False,
            translation_equivalence_verified=False, full_text_reviewed=False,
            qualifications=notes["qualifications"],
        )
        sources.append(Source.model_validate_json(encoded(source)))
        if included:
            custody_note = (
                "Received through Sherlock source-discovery-011, not a direct Atlas HTTP acquisition. "
                f"Delivered event {event['event_id']} claims download from {event['requested_url']} "
                f"ending at {event['final_url_claim']} on {event['completed_at_claim']}; these times "
                "and original-download provenance are not independently witnessed. Exact retained "
                f"PDF digest is {original['sha256']}. Atlas delivery custody captured at "
                f"{candidate['custody_captured_at']}; actual repository receipt time remains unset. "
                f"Issuer: {notes['issuer']}. Role: {notes['role']}. "
                + " ".join(notes["qualifications"]) + " Source-only title/role review; no legal "
                "currentness, complete extraction, translation equivalence or answer-safety promotion. "
                "The source-discovery batch exceeded its distinct-target cap (66/50) and lost two "
                "earlier non-PDF bodies; these custody failures remain disclosed, not repaired by intake."
            )
            record = dict(record_id=sid, layer_id="08_County_Authorities",
                          official_source_name=notes["title"],
                          official_source_url=event["requested_url"],
                          acquisition_method="received_review_package", received_from="Sherlock",
                          reviewer_name="Atlas / Ptolemy", reviewer_email=None, custody_note=custody_note,
                          source_file=original, expected_sha256=original["sha256"], source_format="pdf",
                          size_bytes=original["size_bytes"], allow_duplicate=False, intake_id=None,
                          archive_path=None, received_at=None, status="proposed_not_applied",
                          intended_record_status="archived_pending_pipeline", legal_currentness="not_verified")
            records.append(RecordTemplate.model_validate_json(encoded(record)))
    raw_rows, ledger_rows = [all_rows[n] for n in current_paths[:2]]
    ids = {s.source_id for s in sources}
    digests = {s.original.sha256 for s in sources}
    sizes = {s.original.size_bytes for s in sources}
    screened = 0
    same_size, skipped, raw_matches = [], [], []
    for folder, dirs, files in os.walk(REPO / "_RAW_ARCHIVE", followlinks=False):
        for name in list(dirs):
            p = Path(folder) / name
            if p.is_symlink():
                skipped.append(str(p.relative_to(REPO))); dirs.remove(name)
        for name in files:
            p = Path(folder) / name
            if p.is_symlink():
                skipped.append(str(p.relative_to(REPO))); continue
            if not p.is_file():
                continue
            screened += 1
            if p.stat().st_size in sizes:
                a = asset(p, REPO); same_size.append(a)
                if a["sha256"] in digests:
                    raw_matches.append(a["path"])
    dedupe = dict(checked_at=now, raw_records=len(raw_rows), ledger_records=len(ledger_rows),
                  ordinary_raw_files_screened=screened, symlinks_skipped=sorted(skipped),
                  candidate_size_files_hashed=sorted(same_size, key=lambda x: x["path"]),
                  source_id_matches=sorted({r.record_id for r in raw_rows + ledger_rows if r.record_id in ids}),
                  raw_manifest_digest_matches=[r.intake_id for r in raw_rows if r.sha256 in digests],
                  ledger_digest_matches=[r.intake_id for r in ledger_rows if r.sha256 in digests],
                  ordinary_raw_digest_matches=sorted(raw_matches),
                  boundary="Current manual streams and ordinary raw files only; no former Windows host "
                  "or unavailable LFS bytes were opened. Absence here is not universal absence. "
                  "Repeat this screen against the then-current repository before any authorized apply.")
    dedupe = Dedupe.model_validate_json(encoded(dedupe))
    if any([dedupe.source_id_matches, dedupe.raw_manifest_digest_matches,
            dedupe.ledger_digest_matches, dedupe.ordinary_raw_digest_matches]):
        raise ValueError("Potential duplicate requires explicit reconciliation, not append")
    for b in baseline:
        if (REPO / b["repository_path"]).read_bytes() != (BASE / b["preserved"]["path"]).read_bytes():
            raise ValueError("Baseline changed during preparation")
    proposal = Preparation.model_validate_json(encoded(dict(
        schema_version=1, prepared_at=now, status="prepared_not_applied", apply_available=False,
        audit=asset(BASE / "inputs/audit/AUDIT.json"), audit_sha256=asset(BASE / "inputs/audit/AUDIT.json")["sha256"],
        comparison_commit=audit["comparison_commit"], baseline=baseline, dedupe=dedupe.model_dump(mode="json"),
        sources=[s.model_dump(mode="json") for s in sources],
        proposed_records=[r.model_dump(mode="json") for r in records],
        custody=[x.model_dump(mode="json") for x in copies.values()], source_structural_pages=351,
        directly_viewed_pages=20, full_numeric_table_reviews=0, public_events_during_preparation=0,
        upstream_public_events=66, upstream_distinct_targets=66, upstream_distinct_target_cap=50,
        upstream_cap_status="failed", upstream_missing_body_sha256=audit["missing_earlier_body_digests"],
        original_acquisition_certified=False, legal_currentness="not_verified", production_mutations=0,
        limitations=[
            "All 15 first pages and five additional source-role/date pages were viewed; this is not a 351-page legal review.",
            "Only 13 proposed county/Board of Health records; school-fee issuer and CGS layer remain unresolved.",
            "Four exact PDF hashes match inherited historical claims; former original bytes were not opened.",
            "All 15 retained PDF bodies match their delivered event hashes; the two missing earlier bodies are other events.",
            "No request API was invoked: its official-only acquisition enum cannot truthfully express received_review_package.",
            "Record templates intentionally lack intake IDs, archive destinations and actual receipt times until authorized execution.",
            "Upstream cap/body-path failures and incomplete browser activity assurance remain inherited from the frozen audit.",
            "Only audited public header derivatives are copied. Original private headers and all six cookie-bearing files remain outside this package.",
            "Current-law answers, rule units, registry changes and coverage promotion are outside this preparation.",
        ],
    )))
    save(BASE / "PREPARATION.json", encoded(proposal.model_dump(mode="json")))
    save(BASE / "PREPARATION.schema.json", encoded(Preparation.model_json_schema()))
    save(BASE / "proposed-records.jsonl", b"".join((r.model_dump_json() + "\n").encode() for r in records))
    save(BASE / "proposed-records.schema.json", encoded(RecordTemplate.model_json_schema()))
    save(BASE / "source-provenance.jsonl", b"".join((s.model_dump_json() + "\n").encode() for s in sources))
    save(BASE / "source-provenance.schema.json", encoded(Source.model_json_schema()))
    return proposal


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = build()
    logging.info("Prepared %s PDFs / %s proposed records; no repository writes", len(result.sources),
                 len(result.proposed_records))
