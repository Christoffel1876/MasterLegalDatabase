"""Prepared fixed three-source intake; no network, generic append or mutating reconciliation."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import urljoin

import pymupdf
from bs4 import BeautifulSoup
from pydantic import AwareDatetime, ConfigDict, Field
from models import Asset, Preparation, SourceID, Strict

BASE = Path(__file__).absolute().parent
RUNTIME_ROOT = Path("/Users/mcoors/Documents/Project Geode/statewide-hour-2026-09-23")
PLAN_SHA = "16be7d7fd5c3dd9585c3d8c55b7101b1e4d3d9e5b51cf600f816a97f93f13dc4"
RAW = "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl"
LEDGER = "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl"
REPORT = "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json"
SELECTED = {'custer-right-to-ranch-farm-resolution-98-14-shstate03': ('5afc51d162a5472b999ce5bf308ff9a93810015bcbea7c7e710cec864932605a', 12688, 4), 'delta-land-use-adoption-resolution-2021-r-001-shstate03': ('43aa136adb355681cd8dc4ac2c5437ab74ee7cc5c52050dcfc29f6d6d90dd0ba', 181916, 3), 'delta-land-use-code-2024-label-shstate03': ('d5a6e7a8f8c3e6ba6e29ce97ede237e591e963a33eb2bbaee03b5b5c9d8c429b', 2340999, 234)}

sys.dont_write_bytecode = True


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ordinary(root: Path, name: str, missing: bool = False) -> Path:
    """Reject escape, aliases, links and nonordinary ancestors before access."""
    relative = Path(name)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in name
            or relative.as_posix() != name):
        raise ValueError("unsafe path")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or any(
            p.exists() and not p.is_dir() for p in path.parents):
        raise ValueError("symlink or nonordinary ancestor")
    if path.exists() and not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("not an ordinary file: " + name)
    if not missing and not path.is_file():
        raise ValueError("missing ordinary file: " + name)
    return path


def capture(root: Path, asset: Asset) -> bytes:
    raw = ordinary(root, asset.path).read_bytes()
    if len(raw) != asset.size_bytes or digest(raw) != asset.sha256:
        raise ValueError("input changed: " + asset.path)
    return raw


def load_plan(base: Path = BASE) -> Preparation:
    """Parse only the exact checked preparation buffer; pin runtime before import/use."""
    raw = ordinary(base, "PREPARATION.json").read_bytes()
    if digest(raw) != PLAN_SHA:
        raise ValueError("preparation pin differs")
    plan = Preparation.model_validate_json(raw)
    for path, expected in plan.runtime_pins.items():
        if digest(ordinary(RUNTIME_ROOT, path).read_bytes()) != expected:
            raise ValueError("reviewed runtime changed: " + path)
    return plan


load_plan()
sys.path.insert(0, str(RUNTIME_ROOT))
from geode.pipeline import manual_source_intake as mi


class NewRecord(mi.ManualSourceIntakeRecord):
    """Validated final custody only; timestamp is created during eventual apply."""
    model_config = ConfigDict(extra="forbid", strict=True)
    record_id: SourceID
    layer_id: Literal["08_County_Authorities"]
    official_source_url: None
    acquisition_method: Literal["received_review_package"]
    source_format: Literal["pdf"]
    status: Literal["archived_pending_pipeline"]
    blocked_queue_match: Literal[False]
    received_at: AwareDatetime


class Intent(Strict):
    preparation_sha256: str
    actual_repository_received_at: AwareDatetime
    records: list[NewRecord] = Field(min_length=3, max_length=3)
    expected_report: mi.ManualSourceIntakeReport


class Receipt(Strict):
    status: Literal["completed_archived_pending_pipeline"]
    preparation_sha256: str
    intent_sha256: str
    actual_repository_received_at: AwareDatetime
    raw_sha256: str
    ledger_sha256: str
    report_sha256: str
    raw_records: int
    ledger_records: int
    source_id_to_sha256: dict[str, str]
    canonical_archive_paths: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


def record_for(template, timestamp: datetime) -> NewRecord:
    stamp = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    name = template.original_filename
    identity = template.record_id
    return NewRecord(
        intake_id=f"MSI-{stamp}-{identity}", record_id=identity, layer_id=template.layer_id,
        official_source_name=template.official_source_name, official_source_url=None,
        acquisition_method="received_review_package", received_from="Sherlock SH-STATE-20260923-03 delivery",
        reviewer_name="Atlas", reviewer_email=None, custody_note=template.custody_note,
        original_filename=name,
        archive_path=f"_RAW_ARCHIVE/manual_intake/{template.layer_id}/{identity}/{stamp}_{name}",
        sha256=template.source.sha256, size_bytes=template.source.size_bytes, source_format="pdf",
        received_at=timestamp, status="archived_pending_pipeline", blocked_queue_match=False,
        boundary="Received byte custody only; full-source review, acquisition authentication, "
                 "adoption, legal currentness and structured-rule promotion remain unverified.",
    )


def read_rows(raw: bytes):
    with io.BytesIO(raw) as handle:
        return [mi.ManualSourceIntakeRecord.model_validate_json(line) for line in handle]


def expected_report(plan, originals, records, timestamp):
    """Derive from the captured ledger plus exactly the selected records, never live additions."""
    previous = mi.ManualSourceIntakeReport.model_validate_json(originals[REPORT])
    verified = previous.archive_verification
    if verified is None or verified.manifest_records != plan.raw_before:
        raise ValueError("missing baseline verification")
    report = mi._report_from_records([*read_rows(originals[LEDGER]), *records])
    report.generated_at = timestamp
    report.archive_verification = mi.ManualIntakeArchiveVerification(
        manifest_records=plan.raw_after,
        verified_intake_ids=[*verified.verified_intake_ids, *[r.intake_id for r in records]],
        ledger_only_intake_ids=verified.ledger_only_intake_ids,
        missing_ledger_only_intake_ids=verified.missing_ledger_only_intake_ids,
        boundary=verified.boundary,
    )
    return mi.ManualSourceIntakeReport.model_validate_json(report.model_dump_json())


def report_bytes(intent):
    return (intent.expected_report.model_dump_json(indent=2) + "\n").encode()


def atomic_once(path: Path, raw: bytes):
    """Create exact immutable bytes; refuse an existing different destination."""
    ordinary(path.parent, path.name, missing=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("immutable conflict: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".county-intake-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        ordinary(path.parent, path.name, missing=True)
        os.link(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def atomic_replace(path: Path, before: bytes, after: bytes):
    """Replace only an exact recognized predecessor; no reserialization of old JSONL."""
    ordinary(path.parent, path.name)
    if path.read_bytes() != before:
        raise ValueError("prefix changed before replacement")
    fd, temp = tempfile.mkstemp(prefix=".county-intake-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(after)
            handle.flush()
            os.fsync(handle.fileno())
        ordinary(path.parent, path.name)
        if path.read_bytes() != before:
            raise ValueError("prefix changed during replacement")
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def baseline_verified(root, original, plan):
    """Validate all baseline identities/body hashes and the unchanged missing-history report."""
    raw_rows, ledger_rows = read_rows(original[RAW]), read_rows(original[LEDGER])
    if (len(raw_rows), len(ledger_rows)) != (plan.raw_before, plan.ledger_before):
        raise ValueError("baseline counts differ")
    known = {}
    for label, rows in (("raw", raw_rows), ("ledger", ledger_rows)):
        seen = set()
        for row in rows:
            mi._validate_reconciliation_record(root, row)
            if row.intake_id in seen:
                raise ValueError("duplicate baseline intake ID")
            seen.add(row.intake_id)
            if row.record_id in SELECTED or row.sha256 in {v[0] for v in SELECTED.values()}:
                raise ValueError("selected source already present in baseline")
            if row.intake_id in known and known[row.intake_id] != row:
                raise ValueError("baseline raw/ledger identity conflict")
            known[row.intake_id] = row
    raw_ids = {row.intake_id for row in raw_rows}
    ledger_ids = {row.intake_id for row in ledger_rows}
    if not raw_ids <= ledger_ids:
        raise ValueError("baseline has unrelated unreconciled raw rows")
    verified, missing, ledger_only = [], [], []
    for row in ledger_rows:
        path = mi._validate_reconciliation_record(root, row)
        if row.intake_id not in raw_ids:
            ledger_only.append(row.intake_id)
        if not path.exists():
            if row.intake_id in raw_ids:
                raise ValueError("baseline raw source is missing")
            missing.append(row.intake_id)
        else:
            ordinary(root, row.archive_path)
            with path.open("rb") as handle:
                sha = hashlib.file_digest(handle, "sha256").hexdigest()
            if path.stat().st_size != row.size_bytes or sha != row.sha256:
                raise ValueError("baseline raw source changed")
            verified.append(row.intake_id)
    previous = mi.ManualSourceIntakeReport.model_validate_json(original[REPORT])
    calculated = mi._report_from_records(ledger_rows)
    calculated.archive_verification = mi.ManualIntakeArchiveVerification(
        manifest_records=len(raw_rows), verified_intake_ids=verified,
        ledger_only_intake_ids=ledger_only, missing_ledger_only_intake_ids=missing,
    )
    if calculated.model_dump(exclude={"generated_at"}) != previous.model_dump(
            exclude={"generated_at"}):
        raise ValueError("baseline report differs from captured records and available originals")


def check_custody(base, plan):
    """Consume only captured checked buffers, preserving reported/source distinctions."""
    buffers = {a.path: capture(base, a) for a in plan.custody_subset}
    recommendation = json.loads(buffers[plan.recommendation.path])
    source_bytes = []
    for template, provenance in zip(plan.templates, plan.provenance):
        required = SELECTED[template.record_id]
        raw = buffers[template.source.path]
        if (digest(raw), len(raw), provenance.physical_pages) != required:
            raise ValueError("selected source identity differs")
        if Path(template.source.path).name != template.original_filename:
            raise ValueError("incoming filename differs")
        if not raw.startswith(b"%PDF-") or not raw.rstrip().endswith(b"%%EOF"):
            raise ValueError("selected PDF framing differs")
        with pymupdf.open(stream=raw, filetype="pdf") as doc:
            if doc.page_count != required[2] or doc.is_repaired or doc.is_encrypted:
                raise ValueError("selected PDF structure differs")
        matches = [(item, source) for item in recommendation["items"]
                   for source in item["sources"] if source["source_id"] == provenance.action_id]
        if len(matches) != 1:
            raise ValueError("source recommendation is not unique")
        item, source = matches[0]
        if (item["authority_id"] != template.authority_id
                or source["declared_sha256"] != template.source.sha256
                or source["url"] != provenance.requested_url_reported):
            raise ValueError("audited source/authority/scope differs")
        reservation = json.loads(buffers[provenance.reservation.path])
        result = json.loads(buffers[provenance.result.path])
        if (reservation["action_id"] != provenance.action_id
                or result["action_id"] != provenance.action_id
                or reservation["authority_id"] != template.authority_id
                or reservation["requested_url"] != provenance.requested_url_reported
                or result["body"]["sha256"] != digest(raw)
                or result["body"]["size_bytes"] != len(raw)
                or result["body"]["path"] != "bodies/" + template.original_filename
                or result["http_status"] != 200 or result["exit_code"] != 0
                or result["body_role"] != "original_pdf"
                or result["body_size_basis"] != "complete"
                or result["automatic_redirect_urls"] != []
                or result["physical_pages"] != provenance.originally_reported_pages
                or result["observed_final_url"] != provenance.final_url_reported
                or provenance.final_url_reported != provenance.requested_url_reported
                or datetime.fromisoformat(reservation["reserved_at"].replace("Z", "+00:00"))
                != provenance.reported_reserved_at
                or datetime.fromisoformat(result["finished_at"].replace("Z", "+00:00"))
                != provenance.reported_finished_at):
            raise ValueError("reported transport binding differs")
        parent = buffers[provenance.parent.path]
        if provenance.referral_kind == "retained_html_anchor":
            soup = BeautifulSoup(parent, "html.parser")
            if (soup.find("base") is not None
                    or provenance.original_href not in [a.get("href") for a in soup.select("a[href]")]
                    or urljoin(provenance.parent_url, provenance.original_href)
                    != provenance.requested_url_reported
                    or reservation["evidence"]["sha256"] != digest(parent)):
                raise ValueError("parent referral differs")
        elif provenance.referral_kind == "retained_location_claim":
            preceding = json.loads(parent)
            if (preceding["action_id"] != reservation["referring_action_id"]
                    or preceding["http_status"] not in [301, 302, 303, 307, 308]
                    or reservation["basis"] != "retained_location"
                    or reservation["exact_observed_href_or_location"]
                    != provenance.requested_url_reported):
                raise ValueError("reported redirect referral differs")
        else:
            seeds = json.loads(parent)
            seeds = seeds["seeds"]
            selected = [s for s in seeds if s["seed_id"] == reservation["seed_id"]]
            if (len(selected) != 1 or selected[0]["url"] != provenance.requested_url_reported
                    or selected[0]["authority_id"] != template.authority_id):
                raise ValueError("seed referral differs")
        source_bytes.append(raw)
    if [t.record_id for t in plan.templates] != list(SELECTED):
        raise ValueError("selected source order differs")
    return source_bytes


def preflight(root, base, plan, intent):
    """Recognize only reviewed prefixes and monotone original/raw/ledger/report states."""
    sources = check_custody(base, plan)
    legacy = ordinary(root, plan.legacy_guard.path)
    with legacy.open("rb") as handle:
        legacy_sha = hashlib.file_digest(handle, "sha256").hexdigest()
    if (legacy.stat().st_size != plan.legacy_guard.size_bytes
            or legacy_sha != plan.legacy_guard.sha256):
        raise ValueError("full legacy comparison baseline changed")
    original = {item.repository_path: capture(base, item.preserved) for item in plan.baseline}
    current = {name: ordinary(root, name).read_bytes() for name in original}
    baseline_verified(root, original, plan)
    ordinary(root, "_SNAPSHOTS/.preflight", missing=True)
    for name in original.keys() - {RAW, LEDGER, REPORT}:
        if current[name] != original[name]:
            raise ValueError("guard changed: " + name)
    for template in plan.templates:
        if mi._blocked_queue_contains(root, template.record_id):
            raise ValueError("unexpected blocked-queue match")
    suffix = b""
    existing = []
    if intent is not None:
        if (intent.preparation_sha256 != PLAN_SHA
                or [r.record_id for r in intent.records] != list(SELECTED)):
            raise ValueError("intent identity differs")
        for template, record, source in zip(plan.templates, intent.records, sources):
            if record != record_for(template, intent.actual_repository_received_at):
                raise ValueError("intent record differs")
            dest = mi._validate_reconciliation_record(root, record)
            ordinary(root, record.archive_path, missing=True)
            if dest.exists() and dest.read_bytes() != source:
                raise ValueError("source destination conflict")
            existing.append(dest.exists())
        if existing != sorted(existing, reverse=True):
            raise ValueError("unrecognized original write order")
        if intent.expected_report != expected_report(
                plan, original, intent.records, intent.actual_repository_received_at):
            raise ValueError("intent report differs from captured reviewed records")
        suffix = b"".join((record.model_dump_json() + "\n").encode() for record in intent.records)
    phases = []
    for name in [RAW, LEDGER]:
        if not original[name].endswith(b"\n"):
            raise ValueError("historical JSONL lacks final newline")
        if current[name] == original[name]:
            phases.append(0)
        elif intent and current[name] == original[name] + suffix:
            phases.append(1)
        else:
            raise ValueError("unrecognized canonical prefix/state: " + name)
    if current[REPORT] == original[REPORT]:
        phases.append(0)
    elif intent and current[REPORT] == report_bytes(intent):
        phases.append(1)
    else:
        raise ValueError("unrecognized changed report")
    if phases not in [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]]:
        raise ValueError("unrecognized canonical phase order")
    if any(phases) and existing != [True, True, True]:
        raise ValueError("canonical metadata ahead of complete originals")
    # Exact-size scan includes all canonical raw files and rejects untracked duplicate bodies.
    allowed = {r.archive_path for r in intent.records} if intent else set()
    sizes = {v[1] for v in SELECTED.values()}
    hashes = {v[0] for v in SELECTED.values()}
    for top, dirs, files in os.walk(root / "_RAW_ARCHIVE", followlinks=False):
        for name in dirs + files:
            p = Path(top) / name
            if p.is_symlink():
                raise ValueError("linked raw archive entry")
        for name in files:
            p = Path(top) / name
            if not stat.S_ISREG(p.stat().st_mode):
                raise ValueError("nonordinary raw archive entry")
            if p.stat().st_size in sizes and p.relative_to(root).as_posix() not in allowed:
                if digest(p.read_bytes()) in hashes:
                    raise ValueError("selected source already exists elsewhere in raw archive")
    return {"original": original, "current": current, "suffix": suffix, "sources": sources,
            "phase": phases, "originals_present": existing}


def execution_paths(base, plan):
    execution = base / "execution"
    allowed = {"LOCK", "INTENT.json", "RECEIPT.json"}
    allowed.update("preimages/" + Path(item.repository_path).name for item in plan.baseline)
    if execution.exists():
        for top, dirs, files in os.walk(execution, followlinks=False):
            for name in dirs:
                path = Path(top) / name
                if path.is_symlink() or path.relative_to(execution).as_posix() != "preimages":
                    raise ValueError("unrecognized execution directory")
            for name in files:
                path = Path(top) / name
                ordinary(execution, path.relative_to(execution).as_posix())
                if path.relative_to(execution).as_posix() not in allowed:
                    raise ValueError("unrecognized execution file")
    ordinary(execution, "INTENT.json", missing=True)
    return execution


def receipt_for(plan, intent, state, intent_raw):
    return Receipt(
        status="completed_archived_pending_pipeline", preparation_sha256=PLAN_SHA,
        intent_sha256=digest(intent_raw),
        actual_repository_received_at=intent.actual_repository_received_at,
        raw_sha256=digest(state["current"][RAW]), ledger_sha256=digest(state["current"][LEDGER]),
        report_sha256=digest(state["current"][REPORT]), raw_records=plan.raw_after,
        ledger_records=plan.ledger_after,
        source_id_to_sha256={k: v[0] for k, v in SELECTED.items()},
        canonical_archive_paths=[r.archive_path for r in intent.records],
        legal_currentness="not_verified", answer_safe=False,
    )


def run(root: Path, *, apply=False, verify=False, base: Path = BASE,
        fault: Callable[[str], None] = lambda _: None):
    """Read-only by default; explicit apply is separate from preparing this packet."""
    if apply and verify:
        raise ValueError("select one execution mode")
    root = root.expanduser().absolute()
    plan = load_plan(base)
    execution = execution_paths(base, plan)
    intent_path = ordinary(execution, "INTENT.json", missing=True)
    intent = Intent.model_validate_json(intent_path.read_bytes()) if intent_path.exists() else None
    state = preflight(root, base, plan, intent)
    if not apply and not verify:
        return {"status": "dry_run", "raw_before": plan.raw_before, "raw_after": plan.raw_after,
                "ledger_before": plan.ledger_before, "ledger_after": plan.ledger_after,
                "actual_repository_received_at": None if intent is None else
                intent.actual_repository_received_at.isoformat(), "canonical_mutations": 0,
                "source_bytes": sum(len(raw) for raw in state["sources"]),
                "legal_currentness": "not_verified"}
    if verify and intent is None:
        raise ValueError("no completed execution to verify")
    if apply:
        ordinary(execution, "LOCK", missing=True)
        execution.mkdir(parents=True, exist_ok=True)
        with (execution / "LOCK").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if intent_path.exists():
                intent = Intent.model_validate_json(intent_path.read_bytes())
            else:
                timestamp = datetime.now(timezone.utc)
                records = [record_for(t, timestamp) for t in plan.templates]
                candidate = Intent(
                    preparation_sha256=PLAN_SHA, actual_repository_received_at=timestamp,
                    records=records,
                    expected_report=expected_report(plan, state["original"], records, timestamp),
                )
                preflight(root, base, plan, candidate)
                atomic_once(intent_path, candidate.model_dump_json(indent=2).encode() + b"\n")
                intent = candidate
            state = preflight(root, base, plan, intent)
            for name, raw in state["original"].items():
                atomic_once(execution / "preimages" / Path(name).name, raw)
            stamp = intent.actual_repository_received_at.strftime("%Y%m%dT%H%M%S%fZ")
            snapshot_name = "CUSTER-DELTA-" + stamp
            for name in [RAW, LEDGER, REPORT]:
                atomic_once(root / "_SNAPSHOTS" / snapshot_name / name, state["original"][name])
            fault("intent")
            for index, record in enumerate(intent.records):
                state = preflight(root, base, plan, intent)
                destination = ordinary(root, record.archive_path, missing=True)
                atomic_once(destination, state["sources"][index])
                fault("original_" + str(index + 1))
            for name, stage in [(RAW, "raw"), (LEDGER, "ledger"), (REPORT, "reconciled")]:
                state = preflight(root, base, plan, intent)
                after = (report_bytes(intent) if name == REPORT
                         else state["original"][name] + state["suffix"])
                if state["current"][name] == state["original"][name]:
                    atomic_replace(root / name, state["original"][name], after)
                fault(stage)
            state = preflight(root, base, plan, intent)
            if state["phase"] != [1, 1, 1]:
                raise ValueError("incomplete transaction")
            receipt = receipt_for(plan, intent, state, intent_path.read_bytes())
            encoded_receipt = receipt.model_dump_json(indent=2).encode() + b"\n"
            atomic_once(execution / "RECEIPT.json", encoded_receipt)
    receipt = Receipt.model_validate_json(ordinary(execution, "RECEIPT.json").read_bytes())
    state = preflight(root, base, plan, intent)
    expected = receipt_for(plan, intent, state, intent_path.read_bytes())
    if state["phase"] != [1, 1, 1] or receipt != expected:
        raise ValueError("completed receipt/state differs")
    for item in plan.baseline:
        saved = ordinary(execution, "preimages/" + Path(item.repository_path).name)
        if saved.read_bytes() != state[
                "original"][item.repository_path]:
            raise ValueError("execution preimage differs")
    snapshot_name = "CUSTER-DELTA-" + intent.actual_repository_received_at.strftime("%Y%m%dT%H%M%S%fZ")
    for name in [RAW, LEDGER, REPORT]:
        saved = ordinary(root, "_SNAPSHOTS/" + snapshot_name + "/" + name)
        if saved.read_bytes() != state["original"][name]:
            raise ValueError("repository snapshot differs")
    return receipt.model_dump(mode="json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=RUNTIME_ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args.root, apply=args.apply, verify=args.verify)
    except (ValueError, OSError) as error:
        sys.stderr.write(str(error) + "\n")
        raise SystemExit(1)
    print(json.dumps(result, indent=2))
