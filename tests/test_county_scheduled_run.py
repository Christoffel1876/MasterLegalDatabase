"""Scheduled collection preparation must preserve evidence and never publish or overlap."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import signal
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pymupdf
import pytest
from pydantic import ValidationError

from geode.pipeline import county_scheduled_run as scheduled
from geode.pipeline.register_daily import FetchResult


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Create an isolated reviewed code copy and valid seeded baseline without network."""
    code, root, reports = (tmp_path / name for name in ("code", "corpus", "reports"))
    (code / "geode/pipeline").mkdir(parents=True)
    for name in ("county_scheduled_run", "county_reacquisition"):
        (code / f"geode/pipeline/{name}.py").write_text(f"# fixture {name}\n")
    for name in scheduled.DEPENDENCIES:
        (code / name).write_text("# reviewed fixture dependencies\n")
    monkeypatch.setattr(scheduled, "__file__", str(code / "geode/pipeline/county_scheduled_run.py"))
    monkeypatch.setattr(scheduled.county, "__file__", str(
        code / "geode/pipeline/county_reacquisition.py"
    ))
    catalog, document = "https://www.jeffco.us/Codes", "https://www.jeffco.us/a.pdf"
    manifest = scheduled.county.CountyPilotManifest(
        boundary="Fixture document only",
        catalogs=[dict(source_id="catalog", authority_id="CO-COUNTY-JEFFERSON",
                       authority_name="Jefferson County", url=catalog, title="Codes")],
        documents=[dict(source_id="document", authority_id="CO-COUNTY-JEFFERSON",
                        authority_name="Jefferson County", url=document, catalog_url=catalog,
                        source_label="Document", category="land_use_zoning")],
    )
    manifest_path = code / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json())
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((72, 72), "County source")
        body = pdf.tobytes()
    world = {
        catalog: FetchResult(catalog, b'<html><div id="page"><h1>Codes</h1>'
                             b'<a href="/a.pdf">Document</a></div></html>', "text/html"),
        document: FetchResult(document, body, "application/pdf"),
    }
    result = scheduled.county.collect_county_reacquisition(root, manifest, fetch=world.__getitem__)
    assert result.status == "updated", result.errors
    return dict(code_root=code, root=root, report_root=reports, manifest=Path("manifest.json"),
                expected_code_sha256=scheduled.code_fingerprint(code),
                expected_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest())


def receipts(setup: dict) -> list[dict]:
    """Read validated completion receipts from all isolated attempts."""
    return [scheduled.CollectionReceipt.model_validate_json(p.read_bytes()).model_dump(mode="json")
            for p in sorted(setup["report_root"].glob("*/completion.json"))]


def fake_child(monkeypatch: pytest.MonkeyPatch, **settings: object) -> list[dict]:
    """Stub the child process; assertions verify its exact privileges and source-only command."""
    calls = []

    class Process:
        pid = 424242

        def __init__(self, command: list[str], **kwargs: object) -> None:
            if settings.get("spawn_failure"):
                raise OSError("Cannot start interpreter")
            calls.append(dict(command=command, **kwargs))
            calls[-1]["waits"] = []
            self.waits = 0
            report_dir = Path(command[command.index("--report-dir") + 1])
            report_dir.mkdir()
            payload = scheduled.county.CountyReacquisitionReport(
                checked_at=datetime.now(timezone.utc), status="no_change", validation_passed=True,
                manifest_complete=True, catalogs_checked=1, documents_checked=1, sources_checked=2,
            ).model_dump(mode="json")
            payload.update(settings.get("report", {}))
            if not settings.get("missing_report"):
                (report_dir / "report.json").write_text(json.dumps(payload))

        def __enter__(self) -> Process:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def wait(self, timeout: int | None = None) -> int:
            self.waits += 1
            calls[-1]["waits"].append(timeout)
            if settings.get("timeout") and self.waits == 1:
                raise subprocess.TimeoutExpired("fixture", timeout)
            if settings.get("interrupt") and self.waits == 1:
                interruption = settings["interrupt"]
                if interruption == "sigterm":
                    signal.raise_signal(signal.SIGTERM)
                raise interruption
            return int(settings.get("exit_code", 0))

    monkeypatch.setattr(scheduled.subprocess, "Popen", Process)
    return calls


def test_success_is_collection_only_and_child_environment_is_isolated(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "SSH_AUTH_SOCK", "HTTPS_PROXY", "PYTHONPATH"):
        monkeypatch.setenv(key, "must-not-reach-child")
    calls = fake_child(monkeypatch)
    assert scheduled.run_scheduled_collection(**setup) == 0
    call = calls[0]
    assert call["command"][1:3] == ["-m", "geode.pipeline.county_reacquisition"]
    assert "publish" not in " ".join(call["command"])
    assert call["env"] == {"PATH": os.defpath, "PYTHONUNBUFFERED": "1",
                           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
    assert call["start_new_session"] is True
    assert len(call["pass_fds"]) == 1
    result = receipts(setup)[0]
    assert result["outcome"] == "succeeded" and result["source_status"] == "no_change"
    assert result["publication_status"] == "not_attempted"
    assert result["code_sha256"] == setup["expected_code_sha256"]
    assert result["manifest_sha256"] == setup["expected_manifest_sha256"]
    first_dir = next(setup["report_root"].iterdir())
    start = scheduled.CollectionReceipt.model_validate_json((first_dir / "start.json").read_bytes())
    assert start.phase == "started" and start.outcome == "running" and start.exit_code is None


def test_repeated_no_change_preserves_previous_receipts_and_unique_utc_runs(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_child(monkeypatch)
    assert scheduled.run_scheduled_collection(**setup) == 0
    first = {p: p.read_bytes() for p in setup["report_root"].rglob("*.json")}
    assert scheduled.run_scheduled_collection(**setup) == 0
    assert len(receipts(setup)) == 2
    assert len({r["run_id"] for r in receipts(setup)}) == 2
    assert all("Z-" in r["run_id"] for r in receipts(setup))
    assert all(p.read_bytes() == content for p, content in first.items())


@pytest.mark.parametrize("exit_code,expected", [(7, 7), (1, 1), (-15, 143)])
def test_child_failures_preserve_original_and_effective_exit_codes(
    setup: dict, monkeypatch: pytest.MonkeyPatch, exit_code: int, expected: int,
) -> None:
    fake_child(monkeypatch, exit_code=exit_code)
    assert scheduled.run_scheduled_collection(**setup) == expected
    receipt = receipts(setup)[0]
    assert receipt["child_exit_code"] == exit_code and receipt["exit_code"] == expected
    assert receipt["outcome"] == "failed"


@pytest.mark.parametrize("already_exited", [False, True])
def test_timeout_kills_only_own_process_group_and_retains_timeout_receipt(
    setup: dict, monkeypatch: pytest.MonkeyPatch, already_exited: bool,
) -> None:
    fake_child(monkeypatch, timeout=True, exit_code=-9)
    killed = []

    def kill(pid: int, sig: int) -> None:
        killed.append((pid, sig))
        if already_exited:
            raise ProcessLookupError()

    monkeypatch.setattr(scheduled.os, "killpg", kill)
    assert scheduled.run_scheduled_collection(**setup) == 124
    assert killed == [(424242, signal.SIGKILL)]
    assert receipts(setup)[0]["outcome"] == "timed_out"


def test_overlap_is_prevented_even_with_different_report_roots(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_child(monkeypatch)
    with (setup["root"] / ".county-collection.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert scheduled.run_scheduled_collection(**setup) == 75
        assert receipts(setup)[0]["outcome"] == "overlap"
        second = {**setup, "report_root": setup["report_root"].with_name("other-reports")}
        assert scheduled.run_scheduled_collection(**second) == 75
    assert not calls
    assert scheduled.run_scheduled_collection(**setup) == 0


@pytest.mark.parametrize("interruption,expected", [
    (KeyboardInterrupt(), 130), (SystemExit(23), 23), (SystemExit(None), 1), ("sigterm", 143),
])
def test_cancellation_reaps_before_unlock_and_restores_handler(
    setup: dict, monkeypatch: pytest.MonkeyPatch, interruption: object, expected: int,
) -> None:
    calls = fake_child(monkeypatch, interrupt=interruption, exit_code=-9)
    previous_handler = signal.getsignal(signal.SIGTERM)
    killed = []

    def kill(pid: int, sig: int) -> None:
        killed.append((pid, sig))
        with (setup["root"] / ".county-collection.lock").open("a+b") as contender:
            with pytest.raises(BlockingIOError):
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)

    monkeypatch.setattr(scheduled.os, "killpg", kill)
    assert scheduled.run_scheduled_collection(**setup) == expected
    assert killed == [(424242, signal.SIGKILL)]
    assert calls[0]["waits"] == [scheduled.MAX_TIMEOUT_SECONDS, None]
    assert signal.getsignal(signal.SIGTERM) == previous_handler
    receipt = receipts(setup)[0]
    assert receipt["exit_code"] == expected and receipt["child_exit_code"] == -9
    assert receipt["outcome"] == "failed" and "stopped and reaped" in receipt["detail"]
    fake_child(monkeypatch)
    assert scheduled.run_scheduled_collection(**setup) == 0


def test_real_child_is_reaped_after_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_popen = subprocess.Popen
    children = []

    def launch(command: list[str], **kwargs: object) -> subprocess.Popen[bytes]:
        process = real_popen(command, **kwargs)
        children.append(process)
        real_wait = process.wait
        waits = []

        def interrupt_once(timeout: int | None = None) -> int:
            waits.append(timeout)
            if len(waits) == 1:
                raise KeyboardInterrupt()
            return real_wait(timeout)

        monkeypatch.setattr(process, "wait", interrupt_once)
        return process

    monkeypatch.setattr(scheduled.subprocess, "Popen", launch)
    with (tmp_path / "lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        command = [scheduled.sys.executable, "-c", "import time; time.sleep(60)"]
        with pytest.raises(KeyboardInterrupt) as error:
            scheduled._child(command, tmp_path, tmp_path / "child.log", 30, lock.fileno())
        assert error.value.child_exit_code == -signal.SIGKILL
    assert len(children) == 1 and children[0].returncode == -signal.SIGKILL


def test_preflight_interrupt_does_not_claim_child_was_started(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous_handler = signal.getsignal(signal.SIGTERM)

    def interrupted(_: Path) -> str:
        raise KeyboardInterrupt()

    monkeypatch.setattr(scheduled, "code_fingerprint", interrupted)
    assert scheduled.run_scheduled_collection(**setup) == 130
    receipt = receipts(setup)[0]
    assert receipt["child_exit_code"] is None and receipt["detail"] == "Collection interrupted"
    assert signal.getsignal(signal.SIGTERM) == previous_handler


@pytest.mark.parametrize("mutation", ["code", "manifest", "missing_state", "pointer_state",
                                      "missing_raw", "pointer_raw", "empty_baseline",
                                      "wrong_runtime"])
def test_unreviewed_or_corrupt_baseline_stops_before_child(
    setup: dict, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    calls = fake_child(monkeypatch)
    state_path = setup["root"] / scheduled.county.STATE_PATH
    if mutation == "code":
        (setup["code_root"] / "geode/pipeline/county_reacquisition.py").write_text("changed")
    elif mutation == "manifest":
        (setup["code_root"] / "manifest.json").write_text("changed")
    elif mutation == "missing_state":
        state_path.unlink()
    elif mutation == "pointer_state":
        state_path.write_text("version https://git-lfs.github.com/spec/v1\n")
    elif mutation in {"missing_raw", "pointer_raw"}:
        state = json.loads(state_path.read_text())
        path = setup["root"] / next(iter(state["sources"].values()))["path"]
        if mutation == "missing_raw":
            path.unlink()
        else:
            path.write_text("version https://git-lfs.github.com/spec/v1\n")
    elif mutation == "empty_baseline":
        state_path.unlink()
        (setup["root"] / scheduled.county.INVENTORY_PATH).unlink()
    else:
        monkeypatch.setattr(scheduled.county, "__file__", "/unreviewed/collector.py")
    assert scheduled.run_scheduled_collection(**setup) == 1
    assert receipts(setup)[0]["outcome"] == "failed" and not calls


@pytest.mark.parametrize("change", [
    {"status": "failed"}, {"manifest_complete": False}, {"validation_passed": False},
    {"errors": ["partial source"]}, {"catalogs_checked": 0}, {"documents_checked": 0},
    {"sources_checked": 0}, {"checked_at": "2020-01-01T00:00:00Z"},
])
def test_zero_child_exit_cannot_override_incomplete_or_stale_report(
    setup: dict, monkeypatch: pytest.MonkeyPatch, change: dict,
) -> None:
    fake_child(monkeypatch, report=change)
    assert scheduled.run_scheduled_collection(**setup) == 1
    assert receipts(setup)[0]["child_exit_code"] == 0


@pytest.mark.parametrize("settings", [{"missing_report": True}, {"spawn_failure": True}])
def test_setup_failure_or_missing_child_report_gets_completed_failure_receipt(
    setup: dict, monkeypatch: pytest.MonkeyPatch, settings: dict,
) -> None:
    fake_child(monkeypatch, **settings)
    assert scheduled.run_scheduled_collection(**setup) == 1
    assert receipts(setup)[0]["exit_code"] == 1


@pytest.mark.parametrize("seconds", [0, 2701])
def test_timeout_boundaries_fail_before_child(setup: dict, seconds: int) -> None:
    assert scheduled.run_scheduled_collection(**setup, timeout_seconds=seconds) == 1
    assert "45 minutes" in receipts(setup)[0]["detail"]


def test_manifest_parent_escape_and_report_overlap_are_rejected(setup: dict) -> None:
    outside = setup["code_root"].parent / "outside.json"
    outside.write_bytes((setup["code_root"] / "manifest.json").read_bytes())
    assert scheduled.run_scheduled_collection(**{**setup, "manifest": Path("../outside.json")}) == 1
    assert "inside" in receipts(setup)[0]["detail"]
    with pytest.raises(ValueError, match="separate"):
        scheduled.run_scheduled_collection(**{**setup, "report_root": setup["root"] / "reports"})


def test_fingerprints_cover_dependencies_ignore_bytecode_and_reject_symlinks(setup: dict) -> None:
    code = setup["code_root"]
    (code / "geode/irrelevant.pyc").write_bytes(b"bytecode")
    assert scheduled.code_fingerprint(code) == setup["expected_code_sha256"]
    (code / "requirements-county.txt").write_text("new dependency")
    assert scheduled.code_fingerprint(code) != setup["expected_code_sha256"]
    (code / "requirements-county.txt").unlink()
    with pytest.raises(ValueError, match="missing"):
        scheduled.code_fingerprint(code)
    (code / "geode/linked.py").symlink_to(code / "geode/pipeline/county_reacquisition.py")
    with pytest.raises(ValueError, match="symlink"):
        scheduled.code_fingerprint(code)
    with pytest.raises(ValueError, match="no geode"):
        scheduled.code_fingerprint(code / "empty")


def test_receipt_atomicity_immutability_and_lock_release_after_write_failure(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_child(monkeypatch)
    write = scheduled._write_receipt

    def fail_completion(path: Path, receipt: scheduled.CollectionReceipt) -> None:
        if path.name == "completion.json":
            raise OSError("disk failure")
        write(path, receipt)

    monkeypatch.setattr(scheduled, "_write_receipt", fail_completion)
    with pytest.raises(OSError, match="disk failure"):
        scheduled.run_scheduled_collection(**setup)
    monkeypatch.setattr(scheduled, "_write_receipt", write)
    assert scheduled.run_scheduled_collection(**setup) == 0
    path = next(setup["report_root"].glob("*/completion.json"))
    receipt = scheduled.CollectionReceipt.model_validate_json(path.read_bytes())
    with pytest.raises(ValueError, match="immutable"):
        write(path, receipt)
    target = path.with_name("test-write.json")
    before = set(path.parent.iterdir())
    monkeypatch.setattr(scheduled.os, "replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
    with pytest.raises(OSError):
        write(target, receipt)
    assert set(path.parent.iterdir()) == before


def test_receipt_schema_rejects_misleading_times_and_outcomes(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_child(monkeypatch)
    assert scheduled.run_scheduled_collection(**setup) == 0
    payload = receipts(setup)[0]
    for update in [{"started_at": "2026-09-10"}, {"outcome": "failed"},
                   {"completed_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()},
                   {"phase": "started"}, {"publication_status": "published"}]:
        with pytest.raises(ValidationError):
            scheduled.CollectionReceipt.model_validate({**payload, **update})


def test_cli_success_and_invalid_configuration(
    setup: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_child(monkeypatch)
    arguments = [part for key, value in setup.items()
                 for part in ("--" + key.replace("_", "-"), str(value))]
    assert scheduled.main(arguments) == 0
    assert scheduled.main([*arguments, "--expected-code-sha256", "invalid"]) == 1
