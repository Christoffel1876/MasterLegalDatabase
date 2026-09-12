"""Controlled manual source intake for blocked official documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from geode.connectors.archive_paths import safe_archive_stem
from geode.connectors.download_metadata import source_format_from_extension
from geode.constants import ALL_LAYERS, CONTROL_PLANE_DIR, RAW_ARCHIVE_DIR
from geode.schemas.validators import require_official_source_url
from geode.utils.file_io import atomic_write_json, atomic_write_text, iter_jsonl, relative_path

MANUAL_INTAKE_ARCHIVE_ROOT = Path(RAW_ARCHIVE_DIR) / "manual_intake"
MANUAL_INTAKE_MANIFEST_PATH = MANUAL_INTAKE_ARCHIVE_ROOT / "manual_source_intake_manifest.jsonl"
MANUAL_INTAKE_LEDGER_PATH = Path(CONTROL_PLANE_DIR) / "MANUAL_SOURCE_INTAKE_LEDGER.jsonl"
MANUAL_INTAKE_REPORT_PATH = Path(CONTROL_PLANE_DIR) / "MANUAL_SOURCE_INTAKE_REPORT.json"
MANUAL_INTAKE_POLICY_PATH = Path(CONTROL_PLANE_DIR) / "MANUAL_SOURCE_INTAKE_POLICY.json"
BLOCKED_DOWNLOAD_QUEUE_PATH = Path(CONTROL_PLANE_DIR) / "BLOCKED_DOWNLOAD_QUEUE.json"

ACQUISITION_METHODS = (
    "official_email",
    "state_archives_request",
    "manual_official_download",
    "public_records_request",
    "other_official_transfer",
)


class ManualSourceIntakeRequest(BaseModel):
    """Request to preserve one official source artifact received outside automation."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(min_length=1)
    layer_id: str
    source_file: str
    official_source_name: str = Field(min_length=1)
    official_source_url: str | None = None
    acquisition_method: Literal[
        "official_email",
        "state_archives_request",
        "manual_official_download",
        "public_records_request",
        "other_official_transfer",
    ]
    received_from: str = Field(min_length=1)
    reviewer_name: str = Field(min_length=1)
    reviewer_email: str | None = None
    custody_note: str = Field(min_length=10)
    expected_sha256: str | None = None
    allow_duplicate: bool = False

    @field_validator("layer_id")
    @classmethod
    def _valid_layer(cls, value: str) -> str:
        """Require a known Geode layer."""

        if value not in ALL_LAYERS:
            raise ValueError(f"unknown layer_id: {value}")
        return value

    @field_validator("record_id")
    @classmethod
    def _safe_record_id(cls, value: str) -> str:
        """Reject path-like record identifiers."""

        if "/" in value or "\\" in value or value.strip() in {"", ".", ".."}:
            raise ValueError("record_id must be an identifier, not a path")
        return value

    @field_validator("official_source_url")
    @classmethod
    def _official_url(cls, value: str | None) -> str | None:
        """Validate official URLs when a URL is available."""

        if value is None or not value.strip():
            return None
        return require_official_source_url(value.strip())

    @field_validator("expected_sha256")
    @classmethod
    def _valid_sha(cls, value: str | None) -> str | None:
        """Validate optional expected SHA-256."""

        if value is None or not value.strip():
            return None
        cleaned = value.strip().lower()
        if len(cleaned) != 64 or any(char not in "0123456789abcdef" for char in cleaned):
            raise ValueError("expected_sha256 must be a 64-character hex digest")
        return cleaned


class ManualSourceIntakeRecord(BaseModel):
    """Durable record for one archived manual source artifact."""

    model_config = ConfigDict(extra="forbid")

    intake_id: str
    record_id: str
    layer_id: str
    official_source_name: str
    official_source_url: str | None = None
    acquisition_method: str
    received_from: str
    reviewer_name: str
    reviewer_email: str | None = None
    custody_note: str
    original_filename: str
    archive_path: str
    sha256: str
    size_bytes: int = Field(ge=1)
    source_format: str
    received_at: datetime
    status: str
    blocked_queue_match: bool
    boundary: str


class ManualSourceIntakeReport(BaseModel):
    """Summary of manual source intake state."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    ledger_path: str
    archive_manifest_path: str
    records: int = Field(ge=0)
    pending_pipeline_use: int = Field(ge=0)
    layers: dict[str, int] = Field(default_factory=dict)
    latest_record_id: str | None = None
    acquisition_methods: dict[str, int] = Field(default_factory=dict)
    archive_verification: ManualIntakeArchiveVerification | None = None
    boundary: str


class ManualIntakeArchiveVerification(BaseModel):
    """Distinguish verified archive bytes from retained ledger-only history."""

    model_config = ConfigDict(extra="forbid")

    manifest_records: int = Field(ge=0)
    verified_intake_ids: list[str]
    ledger_only_intake_ids: list[str]
    missing_ledger_only_intake_ids: list[str]
    boundary: str = (
        "Hash and size verification establishes local byte identity only. "
        "Ledger-only history may lack a local original; custody, acquisition claims, "
        "pipeline status, and legal currentness are not promoted."
    )


class ManualIntakeReconciliation(BaseModel):
    """Validated preview or result of reconciling the archive into the ledger."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["dry_run", "updated", "no_change"]
    added_intake_ids: list[str]
    ledger_records_before: int = Field(ge=0)
    ledger_records_after: int = Field(ge=0)
    report_needs_update: bool
    report: ManualSourceIntakeReport


def _reconciliation_path(root: Path, relative: Path) -> Path:
    """Reject path escapes and symlink components, including ancestors of root."""

    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe reconciliation path: {relative}")
    path = root / relative
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"symlink in reconciliation path: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"reconciliation path is not a file: {path}")
    return path


def _validate_reconciliation_record(root: Path, row: ManualSourceIntakeRecord) -> Path:
    """Validate an existing record without reclassifying its acquisition method."""

    for value in (row.intake_id, row.record_id):
        if not value.strip() or "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("invalid reconciliation record identifier")
    if row.layer_id not in ALL_LAYERS:
        raise ValueError(f"unknown layer_id: {row.layer_id}")
    if len(row.sha256) != 64 or any(c not in "0123456789abcdef" for c in row.sha256):
        raise ValueError("invalid reconciliation SHA-256")
    if row.received_at.tzinfo is None or row.received_at.utcoffset() is None:
        raise ValueError("reconciliation received_at must be timezone-aware")
    if row.official_source_url:
        require_official_source_url(row.official_source_url)
    path = PurePosixPath(row.archive_path)
    expected_parent = MANUAL_INTAKE_ARCHIVE_ROOT / row.layer_id / safe_archive_stem(row.record_id)
    if (
        path.as_posix() != row.archive_path
        or "\\" in row.archive_path
        or ":" in row.archive_path
        or path.parent != PurePosixPath(expected_parent.as_posix())
    ):
        raise ValueError(f"invalid manual archive path: {row.archive_path}")
    return _reconciliation_path(root, Path(row.archive_path))


def reconcile_manual_source_intake(
    root: Path, *, dry_run: bool = True
) -> ManualIntakeReconciliation:
    """Append missing validated archive records and repair the derived report.

    Incoming records must be pending and have matching local source bytes. Existing
    ledger-only history is retained, with missing originals disclosed separately.
    All identity/custody conflicts fail before writes. Ledger and report writes are
    separately atomic and snapshotted; rerunning repairs an interrupted report write.
    This never writes the raw manifest, sources, or blocked-download queue.
    """

    root = root.absolute()
    paths = [
        _reconciliation_path(root, path)
        for path in (
            MANUAL_INTAKE_MANIFEST_PATH,
            MANUAL_INTAKE_LEDGER_PATH,
            MANUAL_INTAKE_REPORT_PATH,
        )
    ]
    manifest_path, ledger_path, report_path = paths
    if not manifest_path.is_file():
        raise ValueError("manual archive manifest is missing")
    before = {path: path.read_bytes() if path.exists() else None for path in paths}
    manifest = _read_records(manifest_path)
    ledger = _read_records(ledger_path)
    by_identity: dict[tuple[str, ...], ManualSourceIntakeRecord] = {}
    by_id: dict[str, ManualSourceIntakeRecord] = {}
    added: list[ManualSourceIntakeRecord] = []
    for label, rows in (("ledger", ledger), ("manifest", manifest)):
        seen: set[str] = set()
        for row in rows:
            _validate_reconciliation_record(root, row)
            if row.intake_id in seen:
                raise ValueError(f"duplicate intake_id in {label}: {row.intake_id}")
            seen.add(row.intake_id)
            if label == "manifest" and row.status != "archived_pending_pipeline":
                raise ValueError(
                    f"manifest record is not archived_pending_pipeline: {row.intake_id}"
                )
            keys = (
                ("intake_id", row.intake_id),
                ("archive_path", row.archive_path),
                ("record_digest", row.record_id, row.sha256),
            )
            for key in keys:
                prior = by_identity.get(key)
                if prior is not None and prior != row:
                    raise ValueError(f"conflicting manual intake {key[0]}: {key[1:]}")
                by_identity[key] = row
            if row.intake_id not in by_id:
                by_id[row.intake_id] = row
                if label == "manifest":
                    added.append(row)

    manifest_ids = {row.intake_id for row in manifest}
    verified: list[str] = []
    missing: list[str] = []
    ledger_only = [row.intake_id for row in ledger if row.intake_id not in manifest_ids]
    for row in by_id.values():
        path = _validate_reconciliation_record(root, row)
        if not path.exists():
            if row.intake_id in manifest_ids:
                raise ValueError(f"manifest source is missing: {row.archive_path}")
            missing.append(row.intake_id)
            continue
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if path.stat().st_size != row.size_bytes or digest != row.sha256:
            raise ValueError(f"archive hash or size mismatch: {row.archive_path}")
        verified.append(row.intake_id)

    report = _report_from_records([*ledger, *added])
    report.archive_verification = ManualIntakeArchiveVerification(
        manifest_records=len(manifest),
        verified_intake_ids=verified,
        ledger_only_intake_ids=ledger_only,
        missing_ledger_only_intake_ids=missing,
    )
    current_report = (
        ManualSourceIntakeReport.model_validate_json(before[report_path])
        if before[report_path] is not None
        else None
    )
    report_changed = current_report is None or current_report.model_dump(
        exclude={"generated_at"}
    ) != report.model_dump(exclude={"generated_at"})
    if not report_changed:
        report = current_report
    result = ManualIntakeReconciliation(
        status="dry_run" if dry_run else "updated" if added or report_changed else "no_change",
        added_intake_ids=[row.intake_id for row in added],
        ledger_records_before=len(ledger),
        ledger_records_after=len(ledger) + len(added),
        report_needs_update=report_changed,
        report=report,
    )
    for path, data in before.items():
        _reconciliation_path(root, path.relative_to(root))
        if (path.read_bytes() if path.exists() else None) != data:
            raise ValueError(f"manual intake input changed during reconciliation: {path}")
    if dry_run or result.status == "no_change":
        return result
    snapshots = root / "_SNAPSHOTS"
    if any(path.is_symlink() for path in (snapshots, *snapshots.parents)):
        raise ValueError("symlink in reconciliation snapshot path")
    # Preserve existing ledger bytes, including historical custody wording.
    if added:
        prefix = (before[ledger_path] or b"").decode("utf-8")
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        content = prefix + "".join(row.model_dump_json() + "\n" for row in added)
        atomic_write_text(ledger_path, content, root)
    if report_changed:
        atomic_write_json(report_path, report, root)
    return result


def archive_manual_source(
    root: Path,
    request: ManualSourceIntakeRequest | dict[str, Any],
    *,
    dry_run: bool = False,
    timestamp: datetime | None = None,
) -> ManualSourceIntakeRecord:
    """Validate and optionally archive one manually received official source file."""

    resolved_root = root.resolve()
    intake_request = ManualSourceIntakeRequest.model_validate(request)
    source_path = Path(intake_request.source_file).expanduser().resolve()
    _validate_source_file(source_path, resolved_root)
    content = source_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if intake_request.expected_sha256 and digest != intake_request.expected_sha256:
        raise ValueError("source file SHA-256 does not match expected_sha256")
    if not intake_request.allow_duplicate:
        _reject_duplicate_digest(resolved_root, intake_request.record_id, digest)

    received_at = timestamp or datetime.now(timezone.utc)
    archive_path = _manual_archive_path(resolved_root, intake_request, source_path, received_at)
    record = ManualSourceIntakeRecord(
        intake_id=f"MSI-{received_at.strftime('%Y%m%dT%H%M%S%fZ')}-{safe_archive_stem(intake_request.record_id)}",
        record_id=intake_request.record_id,
        layer_id=intake_request.layer_id,
        official_source_name=intake_request.official_source_name,
        official_source_url=intake_request.official_source_url,
        acquisition_method=intake_request.acquisition_method,
        received_from=intake_request.received_from,
        reviewer_name=intake_request.reviewer_name,
        reviewer_email=intake_request.reviewer_email,
        custody_note=intake_request.custody_note,
        original_filename=source_path.name,
        archive_path=relative_path(archive_path, resolved_root),
        sha256=digest,
        size_bytes=len(content),
        source_format=source_format_from_extension(source_path.suffix),
        received_at=received_at,
        status="archived_pending_pipeline" if not dry_run else "dry_run_pending_archive",
        blocked_queue_match=_blocked_queue_contains(resolved_root, intake_request.record_id),
        boundary=(
            "Manual intake preserves official source evidence for later pipeline use. "
            "It does not by itself certify, interpret, or structure the legal record."
        ),
    )
    if dry_run:
        return record

    _write_raw_artifact_once(archive_path, content)
    _append_jsonl_raw(resolved_root / MANUAL_INTAKE_MANIFEST_PATH, record)
    _append_jsonl_control(resolved_root / MANUAL_INTAKE_LEDGER_PATH, record, resolved_root)
    _update_blocked_download_queue(resolved_root, record)
    write_manual_source_intake_report(resolved_root)
    return record


def write_manual_source_intake_policy(root: Path) -> dict[str, Any]:
    """Write the manual source intake policy artifact."""

    resolved_root = root.resolve()
    policy = manual_source_intake_policy()
    atomic_write_json(resolved_root / MANUAL_INTAKE_POLICY_PATH, policy, resolved_root)
    return policy


def manual_source_intake_policy() -> dict[str, Any]:
    """Return the manual source intake policy."""

    return {
        "policy_id": "MANUAL_SOURCE_INTAKE",
        "status": "active",
        "purpose": (
            "Preserve official source artifacts that cannot be collected by automated "
            "downloaders, without weakening raw-source custody rules."
        ),
        "allowed_use": [
            "Blocked official downloads such as EO-2019-007.",
            "Official files received from a source owner, State Archives, or a public-records response.",
            "Manual official downloads when automated access is blocked but a human can retrieve the file.",
        ],
        "not_allowed": [
            "Unofficial replacement files.",
            "Edited, OCR-corrected, summarized, or reformatted copies as raw source evidence.",
            "Overwriting an existing raw archive artifact.",
            "Using manual intake as proof of legal correctness without later validation.",
        ],
        "required_metadata": [
            "record_id",
            "layer_id",
            "official_source_name",
            "acquisition_method",
            "received_from",
            "reviewer_name",
            "custody_note",
            "sha256",
        ],
        "output_artifacts": [
            MANUAL_INTAKE_MANIFEST_PATH.as_posix(),
            MANUAL_INTAKE_LEDGER_PATH.as_posix(),
            MANUAL_INTAKE_REPORT_PATH.as_posix(),
        ],
        "boundary": (
            "Manual intake archives evidence only. A separate connector or pipeline rebuild "
            "must use the artifact, validate output, and refresh source-to-output audits."
        ),
    }


def build_manual_source_intake_report(root: Path) -> ManualSourceIntakeReport:
    """Build the manual source intake report from the control ledger."""

    resolved_root = root.resolve()
    rows = list(_read_records(resolved_root / MANUAL_INTAKE_LEDGER_PATH))
    return _report_from_records(rows)


def _report_from_records(rows: list[ManualSourceIntakeRecord]) -> ManualSourceIntakeReport:
    """Summarize custody records without asserting their acquisition is verified."""

    layers: dict[str, int] = {}
    methods: dict[str, int] = {}
    for row in rows:
        layers[row.layer_id] = layers.get(row.layer_id, 0) + 1
        methods[row.acquisition_method] = methods.get(row.acquisition_method, 0) + 1
    latest = rows[-1].record_id if rows else None
    return ManualSourceIntakeReport(
        generated_at=datetime.now(timezone.utc),
        ledger_path=MANUAL_INTAKE_LEDGER_PATH.as_posix(),
        archive_manifest_path=MANUAL_INTAKE_MANIFEST_PATH.as_posix(),
        records=len(rows),
        pending_pipeline_use=sum(1 for row in rows if row.status == "archived_pending_pipeline"),
        layers=dict(sorted(layers.items())),
        latest_record_id=latest,
        acquisition_methods=dict(sorted(methods.items())),
        boundary=(
            "This report summarizes manual intake custody records, including received review "
            "packages. Acquisition methods and source claims are preserved as recorded; counts "
            "do not verify official delivery, local availability, legal currentness, or "
            "completion of a structured-layer rebuild."
        ),
    )


def write_manual_source_intake_report(root: Path) -> ManualSourceIntakeReport:
    """Write the manual source intake report."""

    resolved_root = root.resolve()
    report = build_manual_source_intake_report(resolved_root)
    atomic_write_json(resolved_root / MANUAL_INTAKE_REPORT_PATH, report, resolved_root)
    return report


def _validate_source_file(source_path: Path, root: Path) -> None:
    """Validate the submitted source file before archiving."""

    if not source_path.exists() or not source_path.is_file():
        raise ValueError(f"source file does not exist: {source_path}")
    if source_path.stat().st_size <= 0:
        raise ValueError("source file is empty")
    raw_root = (root / RAW_ARCHIVE_DIR).resolve()
    if source_path == raw_root or source_path.is_relative_to(raw_root):
        raise ValueError("manual intake source_file must not already be inside _RAW_ARCHIVE")


def _manual_archive_path(
    root: Path,
    request: ManualSourceIntakeRequest,
    source_path: Path,
    received_at: datetime,
) -> Path:
    """Return the write-once archive path for a manual artifact."""

    stamp = received_at.strftime("%Y%m%dT%H%M%SZ")
    stem = safe_archive_stem(source_path.stem)
    suffix = source_path.suffix.lower() or ".source"
    return (
        root
        / MANUAL_INTAKE_ARCHIVE_ROOT
        / request.layer_id
        / safe_archive_stem(request.record_id)
        / f"{stamp}_{stem}{suffix}"
    )


def _write_raw_artifact_once(target: Path, content: bytes) -> None:
    """Write a raw manual artifact without overwriting any existing file."""

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise FileExistsError(f"manual intake destination already exists: {target}") from exc


def _append_jsonl_raw(target: Path, record: ManualSourceIntakeRecord) -> None:
    """Append to a raw-archive manifest while preserving JSONL validity."""

    existing_lines: list[str] = []
    if target.exists():
        for payload in iter_jsonl(target):
            existing_lines.append(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    existing_lines.append(record.model_dump_json(exclude_none=False))
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_name(f"{target.name}.tmp")
    try:
        tmp_path.write_text("\n".join(existing_lines) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _append_jsonl_control(target: Path, record: ManualSourceIntakeRecord, root: Path) -> None:
    """Append to the control-plane manual intake ledger."""

    from geode.utils.file_io import append_jsonl_record_atomic

    append_jsonl_record_atomic(target, record, root)


def _reject_duplicate_digest(root: Path, record_id: str, digest: str) -> None:
    """Reject repeated intake of the same file for the same record."""

    for row in _read_records(root / MANUAL_INTAKE_LEDGER_PATH):
        if row.record_id == record_id and row.sha256 == digest:
            raise ValueError(f"manual source already archived for {record_id} with this SHA-256")


def _blocked_queue_contains(root: Path, record_id: str) -> bool:
    """Return whether the blocked-download queue includes a record."""

    queue = _read_json(root / BLOCKED_DOWNLOAD_QUEUE_PATH)
    rows = queue.get("items", [])
    return any(isinstance(row, dict) and row.get("record_id") == record_id for row in rows)


def _update_blocked_download_queue(root: Path, record: ManualSourceIntakeRecord) -> None:
    """Annotate a matching blocked-download item after manual intake."""

    path = root / BLOCKED_DOWNLOAD_QUEUE_PATH
    queue = _read_json(path)
    rows = queue.get("items", [])
    if not isinstance(rows, list):
        return
    changed = False
    for row in rows:
        if not isinstance(row, dict) or row.get("record_id") != record.record_id:
            continue
        row["status"] = "manual_source_archived_pending_pipeline"
        row["manual_intake_archive_path"] = record.archive_path
        row["manual_intake_sha256"] = record.sha256
        row["manual_intake_ledger_path"] = MANUAL_INTAKE_LEDGER_PATH.as_posix()
        row["next_action"] = (
            "Run the layer-specific pipeline rebuild and source-to-output audit using "
            "the manually archived official artifact."
        )
        changed = True
    if changed:
        queue["generated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write_json(path, queue, root)


def _read_records(path: Path) -> list[ManualSourceIntakeRecord]:
    """Read manual intake records from JSONL if the file exists."""

    if not path.exists():
        return []
    return [ManualSourceIntakeRecord.model_validate(row) for row in iter_jsonl(path)]


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object, returning an empty object if absent."""

    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _build_request_from_args(args: argparse.Namespace) -> ManualSourceIntakeRequest:
    """Build a manual intake request from CLI arguments."""

    missing = [
        name
        for name in (
            "source_file",
            "record_id",
            "layer_id",
            "official_source_name",
            "acquisition_method",
            "received_from",
            "reviewer_name",
            "custody_note",
        )
        if not getattr(args, name)
    ]
    if missing:
        raise ValueError(f"missing required intake arguments: {', '.join(missing)}")
    return ManualSourceIntakeRequest(
        record_id=args.record_id,
        layer_id=args.layer_id,
        source_file=args.source_file,
        official_source_name=args.official_source_name,
        official_source_url=args.official_source_url,
        acquisition_method=args.acquisition_method,
        received_from=args.received_from,
        reviewer_name=args.reviewer_name,
        reviewer_email=args.reviewer_email,
        custody_note=args.custody_note,
        expected_sha256=args.expected_sha256,
        allow_duplicate=args.allow_duplicate,
    )


def main() -> None:
    """Run manual source intake from the command line."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--write-policy", action="store_true")
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--source-file")
    parser.add_argument("--record-id")
    parser.add_argument("--layer-id")
    parser.add_argument("--official-source-name")
    parser.add_argument("--official-source-url")
    parser.add_argument("--acquisition-method", choices=ACQUISITION_METHODS)
    parser.add_argument("--received-from")
    parser.add_argument("--reviewer-name")
    parser.add_argument("--reviewer-email")
    parser.add_argument("--custody-note")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--allow-duplicate", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    output: dict[str, Any] = {}
    if args.reconcile:
        if args.write_policy or args.source_file or args.record_id:
            parser.error("--reconcile cannot be combined with policy writing or a new intake")
        result = reconcile_manual_source_intake(root, dry_run=not args.apply)
        output["reconciliation"] = result.model_dump(mode="json")
    elif args.write_policy:
        output["policy"] = write_manual_source_intake_policy(root)
        output["report"] = write_manual_source_intake_report(root).model_dump(mode="json")
    else:
        request = _build_request_from_args(args)
        record = archive_manual_source(root, request, dry_run=not args.apply)
        output["record"] = record.model_dump(mode="json")
        if args.apply:
            output["report"] = build_manual_source_intake_report(root).model_dump(mode="json")

    if args.json:
        print(json.dumps(output, indent=2))
        return
    if "reconciliation" in output:
        result = output["reconciliation"]
        print(
            f"Manual intake reconciliation {result['status']}: "
            f"{len(result['added_intake_ids'])} additions, "
            f"{result['ledger_records_after']} ledger records"
        )
    elif "record" in output:
        status = output["record"]["status"]
        archive_path = output["record"]["archive_path"]
        print(f"Manual source intake {status}: {archive_path}")
    else:
        print(f"Manual source intake policy written: {MANUAL_INTAKE_POLICY_PATH.as_posix()}")


if __name__ == "__main__":
    main()
