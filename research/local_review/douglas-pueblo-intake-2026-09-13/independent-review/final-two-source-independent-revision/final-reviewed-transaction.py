"""Guarded Douglas County / Pueblo City official-PDF intake; read-only by default."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

BASE = Path(__file__).resolve().parent
DEFAULT_ROOT = (
    BASE.parents[3]
    if BASE.name == "prepared-transaction"
    else BASE.parents[2] / "MasterLegalDatabase"
)
PREP = BASE / "evidence/preparation"
PREP_SHA = "c92aef62bbda55c29750d29ab2901b5bd6138bf8aefa8ec4a185fd83cda82fcf"
MANIFEST_SHA = "bbae26ff9ded812c81e864b313d4cfa8f2fa99c4e31191d670038ffe2f14ae4b"
RAW = "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl"
LEDGER = "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl"
REPORT = "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json"
TARGETS = (RAW, LEDGER, REPORT)
sys.dont_write_bytecode = True
RUNTIME_CODE = {
    "geode/__init__.py": (
        "01e1bd1d54b5dbfea8725799f435d6fd6307601abe866ebbd7e096e9d33cbc04"
    ),
    "geode/connectors/__init__.py": (
        "2bd1b0a5e005e8837e762359ce49d4ef12f32655d11b993b4245dceb97866027"
    ),
    "geode/connectors/archive_paths.py": (
        "b53009dafb595bce894f248d9d2c8f3cc6fba5db6d8442ec430221163ed9d83b"
    ),
    "geode/connectors/download_metadata.py": (
        "c76bd8be5936c22a9d025c6fa5849783a68815d724b8e41b728e939fd070fa6b"
    ),
    "geode/constants.py": (
        "58f2073fb806d6dd13d229a7f57444e288d4b6cabe92abc395c1ce198cf8ef64"
    ),
    "geode/pipeline/__init__.py": (
        "13207d937dac4a556cd5bd9646f2a6cd87c6adb9b2726997c0c0ea7051da3eb9"
    ),
    "geode/pipeline/manual_source_intake.py": (
        "5442b78cf16fb3b24f28a72f1c95753a444d39aaf8a906858e3fdcc9f439e0bd"
    ),
    "geode/schemas/__init__.py": (
        "02cf97899c9d6995904de627946aa4822d4ae94f7e32af5f0145eef9c383e508"
    ),
    "geode/schemas/local.py": (
        "b7c1396ac14c614620d23304af70a10e45dd83d2e51e71a88a28a16a15cf716c"
    ),
    "geode/schemas/models.py": (
        "914e719767f1a7cf7c2dc4465ac08450d1d9f2f71b3cd2e9388a78977e3773b9"
    ),
    "geode/schemas/ontology.py": (
        "b2a4e9eb203a6d898002ff93afcd0ef671a5429a5ea472e544fff2a5b8eef676"
    ),
    "geode/schemas/validators.py": (
        "8a1e279fa4979f53e9078c8204da21b0a2aba89db4a5c5d3095066d80ff4f076"
    ),
    "geode/utils/__init__.py": (
        "14522d5ce89c48bbb78f44d99287998ccc6f45124ca45031225d4e19d3107711"
    ),
    "geode/utils/file_io.py": (
        "4c68fdfe1158ad64fbd86cc91ed561244c5effe6454a34fa1138ed474ac41620"
    ),
}

APPROVED_IDENTITIES = {
    "douglas-ehs-fees-atlas-directed": (
        "CO-COUNTY-DOUGLAS",
        "08_County_Authorities",
        "https://www.douglasco.gov/documents/fee-schedule.pdf/",
    ),
    "pueblo-planning-fees-atlas-directed": (
        "CO-MUNICIPAL-PUEBLO",
        "10_Municipal_Authorities",
        "https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId=",
    ),
}


def validate_runtime_code() -> None:
    """Pin all transitive local imports before execution and again before writes."""
    for relative, expected in RUNTIME_CODE.items():
        path = DEFAULT_ROOT / relative
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Reviewed runtime is not an ordinary file")
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != expected:
            raise ValueError("Reviewed runtime changed: " + relative)

validate_runtime_code()
sys.path.insert(0, str(DEFAULT_ROOT))
from geode.pipeline.manual_source_intake import (
    ManualIntakeArchiveVerification,
    ManualSourceIntakeRecord,
    ManualSourceIntakeReport,
    _report_from_records,
    _validate_reconciliation_record,
    ManualSourceIntakeRequest,
    reconcile_manual_source_intake,
)


class Strict(BaseModel):
    """Reject unknown execution fields and scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class File(Strict):
    """One source or transaction file bound to its exact bytes."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class NewRecord(ManualSourceIntakeRecord):
    """Constrain final records to the approved source-only custody method."""

    model_config = ConfigDict(extra="forbid", strict=True)
    layer_id: Literal["08_County_Authorities", "10_Municipal_Authorities"]
    acquisition_method: Literal["manual_official_download"]
    status: Literal["archived_pending_pipeline"]
    source_format: Literal["pdf"]
    received_at: AwareDatetime
    blocked_queue_match: Literal[False]


class Change(Strict):
    """Allow only exact before/after bytes and a write-once preimage."""

    path: str
    before: File
    after: File
    snapshot: File


class Intent(Strict):
    """Persist actual application time before any repository writes."""

    schema_version: Literal[1]
    transaction_id: str
    root: str
    preparation_sha256: str
    actual_repository_received_at: AwareDatetime
    records: list[NewRecord] = Field(min_length=2, max_length=2)
    suffix: File
    changes: list[Change] = Field(min_length=3, max_length=3)
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    source_provenance_sha256: str


class Receipt(Strict):
    """Describe completed custody, preserving all acquisition and review limits."""

    schema_version: Literal[1]
    status: Literal["completed_archived_pending_pipeline"]
    completed_at: AwareDatetime
    actual_repository_received_at: AwareDatetime
    intent_sha256: str
    intent: Intent
    originals: list[File] = Field(min_length=2, max_length=2)
    raw_before: Literal[61]
    raw_after: Literal[63]
    ledger_before: Literal[62]
    ledger_after: Literal[64]
    exact_prefixes_preserved: Literal[True]
    reconciliation_added_ids: list[str]
    reconciliation_report_changed: Literal[False]
    full_corpus_validation: Literal["not_run_by_this_transaction"]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


@dataclass(frozen=True)
class Plan:
    """In-memory approved input; CLI only constructs it from the fixed frozen proof."""

    preparation_sha256: str
    source_provenance_sha256: str
    sources: tuple[dict, ...]
    templates: tuple[dict, ...]
    originals_root: Path
    before: dict[str, bytes]
    guards: tuple[File, ...]


def digest(data: bytes) -> str:
    """Return the SHA-256 of exact bytes."""
    return hashlib.sha256(data).hexdigest()


def encoded(value: BaseModel | dict) -> bytes:
    """Serialize only new typed artifacts; old JSONL bytes are never reserialized."""
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()


def ref(path: str, data: bytes) -> File:
    """Describe exact bytes without writing them."""
    return File(path=path, sha256=digest(data), size_bytes=len(data))


def safe(root: Path, relative: str = ".") -> Path:
    """Reject lexical escapes and every symlink ancestor before filesystem access."""
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Root must be an absolute path without '..'")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Relative path escapes root")
    path = root / rel
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f"Symlink path: {path}")
    return path


def destination(root: Path, relative: str) -> Path:
    """Preflight a prospective ordinary file and all existing directory ancestors."""
    path = safe(root, relative)
    if path.exists() and not path.is_file():
        raise ValueError(f"Destination is not an ordinary file: {relative}")
    for parent in path.parents:
        if parent.exists() and not parent.is_dir():
            raise ValueError(f"Destination ancestor is not a directory: {parent}")
    return path


def checked(root: Path, item: File) -> bytes:
    """Read an ordinary exact-hash file or fail closed."""
    path = safe(root, item.path)
    if not path.is_file():
        raise ValueError(f"Missing ordinary file: {item.path}")
    data = path.read_bytes()
    if digest(data) != item.sha256 or len(data) != item.size_bytes:
        raise ValueError(f"Hash/size mismatch: {item.path}")
    return data


def load_plan(root: Path) -> Plan:
    """Consume captured root-verified bytes instead of running the prior verifier.

    Root separately reviewed this frozen source evidence. Pin the manifest and all
    members here, then consume those exact buffers without rereading metadata. Final
    request/record validation and fresh source-byte checks still run before writes.
    The predecessor's embedded verifier adds no custody evidence to this preflight.
    """
    safe(root)
    captured = {}
    for name, expected in [
        ("PREPARATION.json", PREP_SHA),
        ("FINAL_MANIFEST.json", MANIFEST_SHA),
    ]:
        path = safe(PREP, name)
        if not path.is_file():
            raise ValueError("Unapproved preparation: " + name)
        content = path.read_bytes()
        if digest(content) != expected:
            raise ValueError("Unapproved preparation: " + name)
        captured[name] = content
    manifest = json.loads(captured["FINAL_MANIFEST.json"])
    expected_members = {item["path"] for item in manifest["files"]} | {
        "FINAL_MANIFEST.json",
        "FINAL_MANIFEST.schema.json",
    }
    actual_members = set()
    for path in PREP.rglob("*"):
        relative = path.relative_to(PREP).as_posix()
        safe(PREP, relative)
        if not path.is_file() and not path.is_dir():
            raise ValueError("Nonordinary preparation member")
        if path.is_file():
            actual_members.add(relative)
    if actual_members != expected_members:
        raise ValueError("Preparation membership changed")
    for item in manifest["files"]:
        file = File.model_validate(item)
        if file.path not in captured:
            captured[file.path] = checked(PREP, file)
        elif ref(file.path, captured[file.path]) != file:
            raise ValueError("Conflicting preparation file pins")
    data = json.loads(captured["PREPARATION.json"])
    before, guards = {}, []
    for baseline in data["baseline"]:
        file = File.model_validate(baseline["preserved"])
        content = captured[file.path]
        if ref(file.path, content) != file:
            raise ValueError("Baseline binding differs from captured input")
        if baseline["repository_path"] in TARGETS:
            before[baseline["repository_path"]] = content
        else:
            guards.append(ref(baseline["repository_path"], content))
    return Plan(
        PREP_SHA,
        digest(captured["source-provenance.jsonl"]),
        tuple(data["sources"]),
        tuple(data["proposed_records"]),
        PREP,
        before,
        tuple(guards),
    )


def rows(data: bytes) -> list[ManualSourceIntakeRecord]:
    """Stream records from an in-memory immutable prefix."""
    import io
    return [ManualSourceIntakeRecord.model_validate_json(line) for line in io.BytesIO(data)]


def _source_bytes(plan: Plan) -> dict[str, bytes]:
    data = {}
    if len(plan.sources) != 2 or len(plan.templates) != 2:
        raise ValueError("Exactly two approved sources required")
    for source, template in zip(plan.sources, plan.templates, strict=True):
        sid = source["proposed_record_id"]
        identity = (source["authority_id"], source["layer_id"], source["http_url"])
        if (
            sid != template["record_id"]
            or sid in data
            or identity != APPROVED_IDENTITIES.get(sid)
            or template["layer_id"] != source["layer_id"]
            or template["acquisition_method"] != "manual_official_download"
            or template["expected_sha256"] != source["original"]["sha256"]
        ):
            raise ValueError("Source/template/authority mismatch")
        request_fields = {key: template[key] for key in (
            "record_id", "layer_id", "official_source_name", "official_source_url",
            "acquisition_method", "received_from", "reviewer_name", "reviewer_email",
            "custody_note", "expected_sha256", "allow_duplicate")}
        request_fields["source_file"] = str(
            plan.originals_root / source["original"]["path"]
        )
        ManualSourceIntakeRequest.model_validate(request_fields)
        if (template["source_file"] != source["original"] or
                source["http_url"] != template["official_source_url"] or
                template["intake_id"] is not None or template["received_at"] is not None or
                template["archive_path"] is not None or
                template["status"] != "proposed_not_applied"):
            raise ValueError("Source/template custody mismatch")
        if template["original_filename"] != Path(source["original"]["path"]).name:
            raise ValueError("Original filename differs from actual incoming basename")
        data[sid] = checked(plan.originals_root, File.model_validate(source["original"]))
    return data


def _derive(plan: Plan, root: Path, when: datetime) -> tuple[Intent, dict[str, bytes], bytes]:
    stamp = when.strftime("%Y%m%dT%H%M%S%fZ")
    txid = "douglas-pueblo-final-" + stamp
    source_bytes = _source_bytes(plan)
    records = []
    for template in plan.templates:
        sid = template["record_id"]
        from geode.connectors.archive_paths import safe_archive_stem
        filename = template["original_filename"]
        archive = (
            f"_RAW_ARCHIVE/manual_intake/{template['layer_id']}/{sid}/"
            f"{when.strftime('%Y%m%dT%H%M%SZ')}_"
            f"{safe_archive_stem(Path(filename).stem)}.pdf"
        )
        records.append(NewRecord(
            intake_id=f"MSI-{stamp}-{sid}",
            record_id=sid,
            layer_id=template["layer_id"],
            official_source_name=template["official_source_name"],
            official_source_url=template["official_source_url"],
            acquisition_method="manual_official_download", received_from=template["received_from"],
            reviewer_name=template["reviewer_name"], reviewer_email=None,
            custody_note=template["custody_note"] + " Actual repository intake time is the "
            "received_at field of this record; earlier proposal timestamps remain historical.",
            original_filename=filename, archive_path=archive, sha256=digest(source_bytes[sid]),
            size_bytes=len(source_bytes[sid]), source_format="pdf", received_at=when,
            status="archived_pending_pipeline", blocked_queue_match=False,
            boundary="Direct Atlas official HTTP source evidence only; "
            "acquisition interval remains in "
            "custody_note. legal_currentness=not_verified, answer_safe=false. "
            "No rule or coverage promotion.",
        ))
    for record in records:
        _validate_reconciliation_record(root, record)
        destination(root, record.archive_path)
    suffix = b"".join((r.model_dump_json() + "\n").encode() for r in records)
    old_raw, old_ledger = rows(plan.before[RAW]), rows(plan.before[LEDGER])
    if len(old_raw) != 61 or len(old_ledger) != 62:
        raise ValueError("Expected exactly 61 raw and 62 ledger rows")
    if not all(plan.before[p].endswith(b"\n") for p in (RAW, LEDGER)):
        raise ValueError("Prefix lacks final newline")
    new_rows = [*old_ledger, *records]
    report = _report_from_records(new_rows)
    report.generated_at = when
    old_report = ManualSourceIntakeReport.model_validate_json(plan.before[REPORT])
    if old_report.archive_verification is None:
        raise ValueError("Existing archive-verification state is required")
    old = old_report.archive_verification
    report.archive_verification = ManualIntakeArchiveVerification(
        manifest_records=63, verified_intake_ids=[*old.verified_intake_ids,
                                                  *(r.intake_id for r in records)],
        ledger_only_intake_ids=old.ledger_only_intake_ids,
        missing_ledger_only_intake_ids=old.missing_ledger_only_intake_ids,
    )
    after = {RAW: plan.before[RAW] + suffix, LEDGER: plan.before[LEDGER] + suffix,
             REPORT: encoded(report)}
    changes = [Change(path=p, before=ref(p, plan.before[p]), after=ref(p, after[p]),
                      snapshot=ref(f"_SNAPSHOTS/{txid}/preimages/{p}", plan.before[p]))
               for p in TARGETS]
    intent = Intent(schema_version=1, transaction_id=txid, root=str(root),
                    preparation_sha256=plan.preparation_sha256, actual_repository_received_at=when,
                    records=records, suffix=ref("records.jsonl", suffix), changes=changes,
                    legal_currentness="not_verified", answer_safe=False,
                    source_provenance_sha256=plan.source_provenance_sha256)
    return intent, after, suffix


def _preflight(plan: Plan, root: Path, intent: Intent | None = None) -> None:
    validate_runtime_code()
    safe(root)
    snapshots = safe(root, "_SNAPSHOTS")
    if snapshots.exists() and not snapshots.is_dir():
        raise ValueError("Snapshot root is not a directory")
    sources = _source_bytes(plan)
    for guard in plan.guards:
        checked(root, guard)
    after = {}
    if intent:
        expected, after, _ = _derive(plan, root, intent.actual_repository_received_at)
        if intent != expected:
            raise ValueError("Intent differs from approved deterministic records")
        for record in intent.records:
            destination(root, record.archive_path)
        for change in intent.changes:
            destination(root, change.snapshot.path)
    else:
        # Validate the actual final-record host/layer/path rules even for a dry run,
        # before execution state or any repository destination is created.
        _derive(plan, root, datetime.now(timezone.utc))
    states = []
    for p in TARGETS:
        path = destination(root, p)
        data = path.read_bytes()
        if data == plan.before[p]:
            states.append("before")
        elif intent and data == after[p]:
            states.append("after")
        else:
            raise ValueError(f"Foreign or corrupt transaction state: {p}")
    if states not in [["before"] * 3, ["after", "before", "before"],
                      ["after", "after", "before"], ["after"] * 3]:
        raise ValueError("Unsupported publication order")
    allowed = {r.archive_path: r for r in intent.records} if intent else {}
    candidate_sizes = {len(x) for x in sources.values()}
    candidate_digests = {digest(x) for x in sources.values()}
    for folder, dirs, files in os.walk(safe(root, "_RAW_ARCHIVE"), followlinks=False):
        for name in dirs + files:
            path = Path(folder) / name
            if path.is_symlink():
                raise ValueError("Symlink in raw archive")
            if not path.is_dir() and not path.is_file():
                raise ValueError("Nonordinary member in raw archive")
        for name in files:
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            if relative in allowed:
                row = allowed[relative]
                checked(root, File(path=relative, sha256=row.sha256, size_bytes=row.size_bytes))
            elif path.is_file() and path.stat().st_size in candidate_sizes:
                if hashlib.sha256(path.read_bytes()).hexdigest() in candidate_digests:
                    raise ValueError("Duplicate source bytes outside this transaction")
            elif path.is_file() and path.stat().st_size < 200:
                raw = path.read_bytes()
                if raw.startswith(b"version https://git-lfs.github.com/spec/v1") and any(
                    h.encode() in raw for h in candidate_digests
                ):
                    raise ValueError("Matching source LFS pointer already exists")
    for row in [*rows(plan.before[RAW]), *rows(plan.before[LEDGER])]:
        if row.record_id in sources or row.sha256 in candidate_digests:
            raise ValueError("Record ID or source digest already present")
    # Also verify all existing manual originals, including disclosed ledger-only history.
    check = reconcile_manual_source_intake(root, dry_run=True)
    if states == ["before"] * 3:
        if check.added_intake_ids or check.report_needs_update:
            raise ValueError("Existing ledger/report must reconcile before this transaction")
    elif intent:
        expected_ids = [r.intake_id for r in intent.records] if states[1] == "before" else []
        if check.added_intake_ids != expected_ids:
            raise ValueError("Unexpected reconciliation additions")
        desired = ManualSourceIntakeReport.model_validate_json(after[REPORT])
        if check.report.model_dump(exclude={"generated_at"}) != desired.model_dump(
            exclude={"generated_at"}
        ):
            raise ValueError("Reconciliation differs from planned report")
    for change in intent.changes if intent else []:
        path = safe(root, change.snapshot.path)
        if path.exists():
            checked(root, change.snapshot)


def _write_once(root: Path, path: str, data: bytes, stage: Path) -> None:
    """Create a complete file atomically without replacing an existing destination."""
    target = safe(root, path)
    if target.exists():
        if not target.is_file() or target.read_bytes() != data:
            raise ValueError(f"Existing destination differs: {path}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    safe(root, path)
    stage.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="staged-", dir=stage)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        # Hard-link the independent temporary inode, not the received source inode.
        os.link(temporary, target)
    except FileExistsError:
        if target.read_bytes() != data:
            raise ValueError(f"Concurrent write collision: {path}")
    finally:
        temporary.unlink(missing_ok=True)


def _replace(root: Path, path: str, before: bytes, after: bytes) -> None:
    target = destination(root, path)
    actual = target.read_bytes()
    if actual == after:
        return
    if actual != before:
        raise ValueError("Concurrent control/manifest mutation")
    descriptor, name = tempfile.mkstemp(prefix=".douglas-pueblo-transaction-", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(after); handle.flush(); os.fsync(handle.fileno())
        safe(root, path)
        if target.read_bytes() != before:
            raise ValueError("Preimage changed immediately before replacement")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def validate_state(state: Path) -> None:
    """Reject unrelated state members and impossible orphan completion artifacts."""
    safe(state)
    if not state.exists():
        return
    if not state.is_dir():
        raise ValueError("Execution state is not a directory")
    for member in state.iterdir():
        relative = member.relative_to(state).as_posix()
        safe(state, relative)
        if relative == ".staging":
            if not member.is_dir():
                raise ValueError("State staging is not a directory")
            for staged in member.iterdir():
                if not staged.name.startswith("staged-") or not staged.is_file():
                    raise ValueError("Unrelated staging member")
                safe(state, staged.relative_to(state).as_posix())
        elif relative not in {"INTENT.json", "records.jsonl", "RECEIPT.json",
                              "transaction.lock"} or not member.is_file():
            raise ValueError("Unrelated or nonordinary file in execution state")
    if not (state / "INTENT.json").exists() and any(
        (state / p).exists() for p in ("records.jsonl", "RECEIPT.json")
    ):
        raise ValueError("Orphan suffix or receipt without intent")


def execute(
    plan: Plan, root: Path, state: Path, *, apply: bool = False,
    verify_only: bool = False, checkpoint: Callable[[str], None] | None = None,
) -> dict:
    """Apply only when explicitly selected; preserve receipt time across every replay."""
    safe(root); validate_state(state)
    checkpoint = checkpoint or (lambda _name: None)
    intent_path = destination(state, "INTENT.json")
    intent = Intent.model_validate_json(intent_path.read_bytes()) if intent_path.exists() else None
    _preflight(plan, root, intent)
    if not apply and not verify_only:
        return {"status": "dry_run_pending" if intent else "dry_run_ready", "sources": 2,
                "repository_writes": 0, "actual_repository_received_at":
                intent.actual_repository_received_at.isoformat() if intent else None,
                "legal_currentness": "not_verified"}
    if verify_only:
        if intent is None:
            raise ValueError("Transaction has not been applied")
        receipt = Receipt.model_validate_json(destination(state, "RECEIPT.json").read_bytes())
        if (receipt.intent != intent or receipt.intent_sha256 != digest(intent_path.read_bytes()) or
                receipt.actual_repository_received_at != intent.actual_repository_received_at or
                receipt.completed_at < receipt.actual_repository_received_at or
                receipt.reconciliation_added_ids):
            raise ValueError("Receipt/intent mismatch")
        for change in intent.changes:
            checked(root, change.after); checked(root, change.snapshot)
        for item in receipt.originals:
            checked(root, item)
        if receipt.originals != [File(path=r.archive_path, sha256=r.sha256, size_bytes=r.size_bytes)
                                 for r in intent.records]:
            raise ValueError("Receipt original set mismatch")
        suffix = checked(state, intent.suffix)
        for path in [RAW, LEDGER]:
            if safe(root, path).read_bytes() != plan.before[path] + suffix:
                raise ValueError("Historical prefix or exact new suffix changed")
        replay = reconcile_manual_source_intake(root, dry_run=True)
        if replay.added_intake_ids or replay.report_needs_update:
            raise ValueError("Completed transaction does not reconcile idempotently")
        return {"status": "verified_complete", "raw_records": 63, "ledger_records": 64,
                "sources": 2, "legal_currentness": "not_verified", "answer_safe": False}
    state.mkdir(parents=True, exist_ok=True)
    lock_path = destination(state, "transaction.lock")
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another transaction invocation holds the lock") from error
        validate_state(state)
        # Reload state under the lock; pre-lock observations do not authorize writes.
        intent_path = destination(state, "INTENT.json")
        intent = (
            Intent.model_validate_json(intent_path.read_bytes())
            if intent_path.exists()
            else None
        )
        _preflight(plan, root, intent)
        if intent is None:
            intent, after, suffix = _derive(plan, root, datetime.now(timezone.utc))
            _preflight(plan, root, intent)
            _write_once(state, "INTENT.json", encoded(intent), safe(state, ".staging"))
        else:
            _, after, suffix = _derive(plan, root, intent.actual_repository_received_at)
        _write_once(state, "records.jsonl", suffix, safe(state, ".staging"))
        checkpoint("intent")
        stage = safe(root, f"_SNAPSHOTS/{intent.transaction_id}/staging")
        for change in intent.changes:
            _write_once(root, change.snapshot.path, plan.before[change.path], stage)
        checkpoint("snapshots")
        for record in intent.records:
            template = next(t for t in plan.templates if t["record_id"] == record.record_id)
            content = checked(plan.originals_root, File.model_validate(template["source_file"]))
            _write_once(root, record.archive_path, content, stage)
            checkpoint("original:" + record.record_id)
        # All originals must be valid before exposing even the first manifest record.
        for record in intent.records:
            checked(
                root,
                File(
                    path=record.archive_path,
                    sha256=record.sha256,
                    size_bytes=record.size_bytes,
                ),
            )
        _replace(root, RAW, plan.before[RAW], after[RAW]); checkpoint("raw_manifest")
        _preflight(plan, root, intent)
        _replace(root, LEDGER, plan.before[LEDGER], after[LEDGER]); checkpoint("ledger")
        _replace(root, REPORT, plan.before[REPORT], after[REPORT]); checkpoint("report")
        _preflight(plan, root, intent)
        result = reconcile_manual_source_intake(root, dry_run=True)
        if result.added_intake_ids or result.report_needs_update:
            raise ValueError("Final reconciliation is not a no-op")
        receipt_path = destination(state, "RECEIPT.json")
        if not receipt_path.exists():
            receipt = Receipt(
                schema_version=1, status="completed_archived_pending_pipeline",
                completed_at=datetime.now(timezone.utc),
                actual_repository_received_at=intent.actual_repository_received_at,
                intent_sha256=digest(intent_path.read_bytes()), intent=intent,
                originals=[File(path=r.archive_path, sha256=r.sha256, size_bytes=r.size_bytes)
                           for r in intent.records], raw_before=61, raw_after=63,
                ledger_before=62, ledger_after=64, exact_prefixes_preserved=True,
                reconciliation_added_ids=[], reconciliation_report_changed=False,
                full_corpus_validation="not_run_by_this_transaction",
                legal_currentness="not_verified",
                answer_safe=False,
            )
            _write_once(state, "RECEIPT.json", encoded(receipt), safe(state, ".staging"))
        return execute(plan, root, state, verify_only=True)


def main() -> None:
    """Select read-only dry-run/verification or the explicit guarded apply operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.root.expanduser().absolute()
    if ".." in root.parts:
        parser.error("Root path cannot contain '..'")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = execute(load_plan(root), root, BASE / "execution", apply=args.apply,
                     verify_only=args.verify)
    logging.info("%s", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
