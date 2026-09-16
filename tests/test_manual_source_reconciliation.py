"""Tests for conservative reconciliation of existing manual archive custody."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geode.pipeline import manual_source_intake as intake


def _record(root: Path, name: str, *, available: bool = True) -> intake.ManualSourceIntakeRecord:
    """Create a minimal source and its independently supplied custody record."""

    body = f"immutable received source {name}".encode()
    archive_path = intake.MANUAL_INTAKE_ARCHIVE_ROOT / "08_County_Authorities" / name / "file.pdf"
    if available:
        path = root / archive_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return intake.ManualSourceIntakeRecord(
        intake_id=f"MSI-{name}",
        record_id=name,
        layer_id="08_County_Authorities",
        official_source_name="Supplied county source",
        official_source_url="https://www.larimer.gov/building/fees",
        acquisition_method="received_review_package",
        received_from="Package reviewer",
        reviewer_name="Custody reviewer",
        custody_note="Original acquisition unknown; supplied log time is not receipt time.",
        original_filename="file.pdf",
        archive_path=archive_path.as_posix(),
        sha256=hashlib.sha256(body).hexdigest(),
        size_bytes=len(body),
        source_format="pdf",
        received_at=datetime(2026, 9, 11, 17, 13, tzinfo=timezone.utc),
        status="archived_pending_pipeline",
        blocked_queue_match=False,
        boundary="Received bytes only; legal currentness and pipeline use remain unverified.",
    )


def _write(root: Path, path: Path, rows: list[intake.ManualSourceIntakeRecord]) -> None:
    """Write test custody fixtures; production code must not rewrite the manifest."""

    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(row.model_dump_json() + "\n" for row in rows))


def _inventory(root: Path) -> dict[str, bytes]:
    """Capture files to prove dry-run and rejection paths are read-only."""

    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_reconcile_preserves_custody_and_missing_ledger_history(tmp_path: Path) -> None:
    """Append missing records while retaining and disclosing unavailable older history."""

    old = _record(tmp_path, "old", available=False)
    known = _record(tmp_path, "known")
    new = _record(tmp_path, "new")
    _write(tmp_path, intake.MANUAL_INTAKE_LEDGER_PATH, [old, known])
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [known, new])
    intake.write_manual_source_intake_report(tmp_path)
    queue = tmp_path / intake.BLOCKED_DOWNLOAD_QUEUE_PATH
    queue.write_text('{"items":[{"record_id":"new","status":"blocked"}]}\n')
    before = _inventory(tmp_path)

    preview = intake.reconcile_manual_source_intake(tmp_path)
    assert preview.status == "dry_run"
    assert preview.added_intake_ids == [new.intake_id]
    assert _inventory(tmp_path) == before
    result = intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert result.status == "updated"
    assert result.ledger_records_before == 2 and result.ledger_records_after == 3
    assert result.report.pending_pipeline_use == 3
    assert result.report.acquisition_methods == {"received_review_package": 3}
    evidence = result.report.archive_verification
    assert evidence.manifest_records == 2
    assert evidence.verified_intake_ids == [known.intake_id, new.intake_id]
    assert evidence.ledger_only_intake_ids == [old.intake_id]
    assert evidence.missing_ledger_only_intake_ids == [old.intake_id]
    ledger = (tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH).read_bytes()
    assert ledger.startswith(before[str(intake.MANUAL_INTAKE_LEDGER_PATH)])
    assert intake._read_records(tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH) == [old, known, new]
    for rel, body in before.items():
        controls = (intake.MANUAL_INTAKE_LEDGER_PATH, intake.MANUAL_INTAKE_REPORT_PATH)
        if rel not in map(str, controls):
            assert (tmp_path / rel).read_bytes() == body
    snapshots = list((tmp_path / "_SNAPSHOTS").rglob("MANUAL_SOURCE_INTAKE*"))
    assert sorted(p.read_bytes() for p in snapshots) == sorted(
        before[str(p)] for p in (intake.MANUAL_INTAKE_LEDGER_PATH, intake.MANUAL_INTAKE_REPORT_PATH)
    )
    applied = _inventory(tmp_path)
    second = intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert second.status == "no_change" and second.added_intake_ids == []
    assert second.report.generated_at == result.report.generated_at
    assert _inventory(tmp_path) == applied


@pytest.mark.parametrize(
    "change",
    [
        {"sha256": "0" * 64},
        {"archive_path": "_RAW_ARCHIVE/manual_intake/08_County_Authorities/a/other.pdf"},
        {"custody_note": "Unjustified replacement custody statement"},
        {"acquisition_method": "manual_official_download"},
        {"received_at": "2026-09-11T18:00:00Z"},
        {"intake_id": "MSI-alternate"},
    ],
)
def test_reconcile_rejects_conflicting_identity_before_writes(tmp_path: Path, change: dict) -> None:
    """Same identity/path/digest cannot silently acquire conflicting metadata."""

    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_LEDGER_PATH, [row])
    updated = intake.ManualSourceIntakeRecord.model_validate(row.model_dump() | change)
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [updated])
    before = _inventory(tmp_path)
    with pytest.raises(ValueError, match="conflicting manual intake"):
        intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("manifest", [True, False])
def test_duplicate_rows_rejected(tmp_path: Path, manifest: bool) -> None:
    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [row, row] if manifest else [row])
    _write(tmp_path, intake.MANUAL_INTAKE_LEDGER_PATH, [row] if manifest else [row, row])
    with pytest.raises(ValueError, match="duplicate intake_id"):
        intake.reconcile_manual_source_intake(tmp_path)


@pytest.mark.parametrize("damage", ["missing", "hash", "size"])
def test_incoming_raw_must_match_before_any_write(tmp_path: Path, damage: str) -> None:
    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [row])
    raw = tmp_path / row.archive_path
    if damage == "missing":
        raw.unlink()
    elif damage == "hash":
        raw.write_bytes(b"x" * row.size_bytes)
    else:
        raw.write_bytes(raw.read_bytes() + b"changed")
    before = _inventory(tmp_path)
    with pytest.raises(ValueError, match="missing|hash or size mismatch"):
        intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"record_id": "../escape"}, "identifier"),
        ({"layer_id": "unknown"}, "unknown layer"),
        ({"sha256": "NOT-A-HASH"}, "SHA-256"),
        ({"received_at": "2026-09-11T17:13:00"}, "timezone-aware"),
        ({"status": "dry_run_pending_archive"}, "not archived_pending_pipeline"),
        ({"archive_path": "../outside.pdf"}, "invalid manual archive path"),
        ({"archive_path": "/tmp/outside.pdf"}, "invalid manual archive path"),
        ({"official_source_url": "https://example.com/fake.pdf"}, "unauthorized"),
    ],
)
def test_invalid_manifest_record_is_refused(tmp_path: Path, change: dict, message: str) -> None:
    row = _record(tmp_path, "a")
    _write(
        tmp_path,
        intake.MANUAL_INTAKE_MANIFEST_PATH,
        [intake.ManualSourceIntakeRecord.model_validate(row.model_dump() | change)],
    )
    with pytest.raises(ValueError, match=message):
        intake.reconcile_manual_source_intake(tmp_path)


@pytest.mark.parametrize("target", ["raw", "manifest", "ledger", "report", "snapshots", "root"])
def test_symlinks_refused(tmp_path: Path, target: str) -> None:
    root = tmp_path / "repo"
    row = _record(root, "a")
    _write(root, intake.MANUAL_INTAKE_MANIFEST_PATH, [row])
    _write(root, intake.MANUAL_INTAKE_LEDGER_PATH, [])
    external = tmp_path / "external"
    if target == "root":
        external.symlink_to(root, target_is_directory=True)
        root = external
    elif target == "snapshots":
        external.mkdir()
        (root / "_SNAPSHOTS").symlink_to(external, target_is_directory=True)
    else:
        paths = {"raw": Path(row.archive_path), "manifest": intake.MANUAL_INTAKE_MANIFEST_PATH,
                 "ledger": intake.MANUAL_INTAKE_LEDGER_PATH,
                 "report": intake.MANUAL_INTAKE_REPORT_PATH}
        p = root / paths[target]
        if p.exists():
            p.rename(external)
        else:
            external.write_text("{}")
        p.symlink_to(external)
    with pytest.raises(ValueError, match="symlink"):
        intake.reconcile_manual_source_intake(root, dry_run=False)


def test_report_failure_is_repairable_without_duplicate_or_raw_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [row])
    writer = intake.atomic_write_json

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("report write interrupted")

    monkeypatch.setattr(intake, "atomic_write_json", fail)
    with pytest.raises(OSError, match="interrupted"):
        intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    ledger = (tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH).read_bytes()
    monkeypatch.setattr(intake, "atomic_write_json", writer)
    recovered = intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert recovered.status == "updated" and recovered.added_intake_ids == []
    assert (tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH).read_bytes() == ledger
    assert recovered.report.records == 1


def test_input_race_refused_even_on_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [row])
    original = intake._report_from_records

    def race(rows: list[intake.ManualSourceIntakeRecord]) -> intake.ManualSourceIntakeReport:
        _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [])
        return original(rows)

    monkeypatch.setattr(intake, "_report_from_records", race)
    with pytest.raises(ValueError, match="input changed"):
        intake.reconcile_manual_source_intake(tmp_path)
    assert not (tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH).exists()


def test_cli_reconcile_default_dry_run_and_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [row])
    args = ["manual-intake", "--root", str(tmp_path), "--reconcile"]
    monkeypatch.setattr(sys, "argv", [*args, "--json"])
    intake.main()
    assert json.loads(capsys.readouterr().out)["reconciliation"]["status"] == "dry_run"
    assert not (tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH).exists()
    monkeypatch.setattr(sys, "argv", [*args, "--apply"])
    intake.main()
    assert "updated: 1 additions, 1 ledger records" in capsys.readouterr().out


def test_cli_rejects_mixed_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["manual-intake", "--reconcile", "--write-policy"])
    with pytest.raises(SystemExit):
        intake.main()


def test_missing_manifest_and_nonfile_inputs_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manifest is missing"):
        intake.reconcile_manual_source_intake(tmp_path)
    (tmp_path / intake.MANUAL_INTAKE_MANIFEST_PATH).mkdir(parents=True)
    with pytest.raises(ValueError, match="not a file"):
        intake.reconcile_manual_source_intake(tmp_path)


def test_ledger_without_terminal_newline_is_preserved_as_prefix(tmp_path: Path) -> None:
    old, new = _record(tmp_path, "old"), _record(tmp_path, "new")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [new])
    _write(tmp_path, intake.MANUAL_INTAKE_LEDGER_PATH, [old])
    ledger = tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH
    previous = ledger.read_bytes().rstrip(b"\n")
    ledger.write_bytes(previous)
    result = intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert ledger.read_bytes().startswith(previous + b"\n")
    assert result.report.archive_verification.missing_ledger_only_intake_ids == []
    assert result.report.archive_verification.ledger_only_intake_ids == [old.intake_id]


def test_malformed_report_fails_before_appending(tmp_path: Path) -> None:
    row = _record(tmp_path, "a")
    _write(tmp_path, intake.MANUAL_INTAKE_MANIFEST_PATH, [row])
    report = tmp_path / intake.MANUAL_INTAKE_REPORT_PATH
    report.parent.mkdir(parents=True)
    report.write_text('{"records": 0}')
    before = _inventory(tmp_path)
    with pytest.raises(ValueError):
        intake.reconcile_manual_source_intake(tmp_path, dry_run=False)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("path", [Path("../outside"), Path("/outside")])
def test_path_guard_refuses_outside_paths(tmp_path: Path, path: Path) -> None:
    with pytest.raises(ValueError, match="unsafe reconciliation path"):
        intake._reconciliation_path(tmp_path, path)


def test_cli_existing_intake_and_policy_modes_remain_usable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Adding the reconciliation mode does not divert existing CLI operations."""

    source = tmp_path / "official.pdf"
    source.write_bytes(b"%PDF official download fixture")
    args = [
        "manual-intake", "--root", str(tmp_path), "--source-file", str(source),
        "--record-id", "test", "--layer-id", "08_County_Authorities",
        "--official-source-name", "County", "--acquisition-method", "manual_official_download",
        "--received-from", "County public site", "--reviewer-name", "Reviewer",
        "--custody-note", "Direct official retrieval, acquisition independently documented.",
        "--expected-sha256", hashlib.sha256(source.read_bytes()).hexdigest().upper(),
    ]
    monkeypatch.setattr(sys, "argv", args)
    intake.main()
    assert "dry_run_pending_archive" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", [*args, "--apply"])
    intake.main()
    assert "archived_pending_pipeline" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["manual-intake", "--root", str(tmp_path), "--write-policy"])
    intake.main()
    assert "policy written" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["manual-intake"])
    with pytest.raises(ValueError, match="missing required"):
        intake.main()


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"layer_id": "unknown"}, "unknown layer_id"),
        ({"record_id": "../outside"}, "identifier"),
        ({"expected_sha256": "0"}, "64-character"),
        ({"expected_sha256": "0" * 64}, "does not match"),
    ],
)
def test_existing_intake_guards_still_reject_invalid_requests(
    tmp_path: Path, change: dict, error: str
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF incoming fixture")
    request = {
        "record_id": "incoming", "layer_id": "08_County_Authorities",
        "source_file": str(source), "official_source_name": "County",
        "acquisition_method": "manual_official_download", "received_from": "County",
        "reviewer_name": "Reviewer", "custody_note": "Official receipt for later review.",
        "official_source_url": "",
    }
    with pytest.raises(ValueError, match=error):
        intake.archive_manual_source(tmp_path, request | change)
    assert not (tmp_path / intake.MANUAL_INTAKE_LEDGER_PATH).exists()


@pytest.mark.parametrize("condition", ["missing", "empty", "already_raw"])
def test_source_file_guards(tmp_path: Path, condition: str) -> None:
    source = tmp_path / "source.pdf"
    if condition == "empty":
        source.touch()
    elif condition == "already_raw":
        source = tmp_path / "_RAW_ARCHIVE" / "source.pdf"
        source.parent.mkdir()
        source.write_bytes(b"raw")
    with pytest.raises(ValueError):
        intake._validate_source_file(source, tmp_path)


def test_write_once_sources_are_never_replaced(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"original")
    with pytest.raises(FileExistsError, match="already exists"):
        intake._write_raw_artifact_once(source, b"replacement")
    assert source.read_bytes() == b"original"
