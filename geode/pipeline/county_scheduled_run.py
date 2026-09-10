"""Prepare collection-only county runs for an externally configured trusted scheduler.

This module installs no schedule, sends no notifications, and never publishes data.
Deployment must provide a dedicated account, reviewed code, and a seeded corpus.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import logging
import os
import signal
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import FrameType
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from geode.pipeline import county_reacquisition as county

LOGGER = logging.getLogger(__name__)
DEPENDENCIES = ("requirements-register.txt", "requirements-ci.txt", "requirements-county.txt")
MAX_TIMEOUT_SECONDS = 45 * 60


class CollectionReceipt(BaseModel):
    """Validated execution evidence; collection success never implies publication."""

    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    run_id: str
    phase: Literal["started", "completed"]
    started_at: datetime
    completed_at: datetime | None = None
    outcome: Literal["running", "succeeded", "failed", "timed_out", "overlap"] = "running"
    exit_code: int | None = None
    child_exit_code: int | None = None
    code_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    expected_code_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    expected_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_status: Literal["updated", "no_change", "failed"] | None = None
    publication_status: Literal["not_attempted"] = "not_attempted"
    corpus_root: str
    report_directory: str
    detail: str = ""

    @model_validator(mode="after")
    def execution_state(self) -> CollectionReceipt:
        """Require aware times and coherent start/completion and exit evidence."""
        for value in (self.started_at, self.completed_at):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("Receipt timestamps must include a timezone")
        if self.phase == "started":
            if (self.completed_at is not None or self.exit_code is not None
                    or self.outcome != "running"):
                raise ValueError("Start receipt cannot claim a completed outcome")
        elif (self.completed_at is None or self.completed_at < self.started_at
              or self.exit_code is None or self.outcome == "running"
              or (self.exit_code == 0) != (self.outcome == "succeeded")):
            raise ValueError("Completion receipt has inconsistent outcome or timing")
        return self


def _safe_path(path: Path) -> Path:
    path = path.absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"Scheduled collection paths must not contain symlinks: {path}")
    return path.resolve()


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def code_fingerprint(code_root: Path) -> str:
    """Hash all package Python files and frozen pilot dependency definitions by relative path."""
    code_root = _safe_path(code_root)
    package = code_root / "geode"
    files = []
    for path in package.rglob("*"):
        _safe_path(path)
        if path.suffix == ".py":
            files.append(path)
    if not files:
        raise ValueError("Reviewed code root has no geode Python package")
    files.extend(code_root / name for name in DEPENDENCIES)
    digest = hashlib.sha256(b"geode-county-collection-code-v1\n")
    for path in sorted(files):
        if not _safe_path(path).is_file():
            raise ValueError(f"Reviewed code/dependency file is missing: {path}")
        digest.update(path.relative_to(code_root).as_posix().encode() + b"\0")
        digest.update(bytes.fromhex(_digest(path)))
    return digest.hexdigest()


def _write_receipt(path: Path, receipt: CollectionReceipt) -> None:
    receipt = CollectionReceipt.model_validate(receipt.model_dump())
    if path.exists() or path.is_symlink():
        raise ValueError("Execution receipts are immutable")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write((receipt.model_dump_json(indent=2) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _stop_signal(signum: int, frame: FrameType | None) -> None:
    raise SystemExit(128 + signum)


def _kill_and_reap(process: subprocess.Popen[bytes]) -> int:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return process.wait()


def _child(
    command: list[str], code_root: Path, log: Path, timeout: int, lock_fd: int,
) -> tuple[int, bool]:
    environment = {"PATH": os.defpath, "PYTHONUNBUFFERED": "1",
                   "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
    with log.open("xb") as output:
        with subprocess.Popen(command, cwd=code_root, env=environment, stdout=output,
                              stderr=subprocess.STDOUT, start_new_session=True,
                              pass_fds=(lock_fd,)) as process:
            try:
                return process.wait(timeout=timeout), False
            except subprocess.TimeoutExpired:
                return _kill_and_reap(process), True
            except BaseException as exc:
                exc.child_exit_code = _kill_and_reap(process)
                raise


def run_scheduled_collection(
    *, code_root: Path, root: Path, report_root: Path, manifest: Path,
    expected_code_sha256: str, expected_manifest_sha256: str,
    timeout_seconds: int = MAX_TIMEOUT_SECONDS,
) -> int:
    """Run one exclusive, pinned, collection-only attempt and preserve its failure exit code."""
    code_root, root, report_root = map(_safe_path, (code_root, root, report_root))
    if any(a.is_relative_to(b) or b.is_relative_to(a) for a, b in (
        (root, code_root), (report_root, code_root), (root, report_root),
    )):
        raise ValueError("Code, corpus and execution reports must have separate directory trees")
    report_root.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    run_id = f"{started.strftime('%Y%m%dT%H%M%S.%fZ')}-{uuid.uuid4().hex}"
    run_dir = report_root / run_id
    run_dir.mkdir()
    receipt = CollectionReceipt(
        run_id=run_id, phase="started", started_at=started,
        expected_code_sha256=expected_code_sha256,
        expected_manifest_sha256=expected_manifest_sha256,
        corpus_root=str(root), report_directory=str(run_dir),
    )
    _write_receipt(run_dir / "start.json", receipt)
    lock = None
    previous_handler = signal.getsignal(signal.SIGTERM)
    handler_installed = False
    try:
        signal.signal(signal.SIGTERM, _stop_signal)
        handler_installed = True
        if not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise ValueError("Timeout must be positive and no more than 45 minutes")
        lock_path = _safe_path(root / ".county-collection.lock")
        lock = lock_path.open("a+b")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            receipt.outcome, receipt.exit_code = "overlap", 75
            receipt.detail = "Another collection attempt holds the exclusive lock"
            return 75
        receipt.code_sha256 = code_fingerprint(code_root)
        wrapper_path = code_root / "geode/pipeline/county_scheduled_run.py"
        collector_path = code_root / "geode/pipeline/county_reacquisition.py"
        if (Path(__file__).resolve() != wrapper_path
                or Path(county.__file__).resolve() != collector_path):
            raise ValueError("Running wrapper and collector must belong to the reviewed code root")
        manifest = _safe_path(manifest if manifest.is_absolute() else code_root / manifest)
        if not manifest.is_relative_to(code_root) or manifest.stat().st_size > 1_000_000:
            raise ValueError("Manifest must be a bounded file inside the reviewed code root")
        manifest_bytes = manifest.read_bytes()
        receipt.manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        if (receipt.code_sha256 != expected_code_sha256
                or receipt.manifest_sha256 != expected_manifest_sha256):
            raise ValueError("Code or manifest differs from its reviewed SHA-256 pin")
        selection = county.CountyPilotManifest.model_validate_json(manifest_bytes)
        previous, _ = county._load_previous(root, county._digest(county._json_bytes(selection)))
        if previous is None:
            raise ValueError("Scheduled collection requires an existing verified baseline")
        command = [sys.executable, "-m", "geode.pipeline.county_reacquisition",
                   "--root", str(root), "--manifest", str(manifest),
                   "--report-dir", str(run_dir / "collection"), "--delay", "1"]
        child_exit, timed_out = _child(
            command, code_root, run_dir / "collector.log", timeout_seconds, lock.fileno()
        )
        receipt.child_exit_code = child_exit
        receipt.exit_code = (
            124 if timed_out else (128 - child_exit if child_exit < 0 else child_exit)
        )
        receipt.outcome = "timed_out" if timed_out else "failed"
        if timed_out:
            receipt.detail = f"Collector exceeded its {timeout_seconds}-second execution limit"
        if receipt.exit_code == 0:
            report = county.CountyReacquisitionReport.model_validate_json(
                (run_dir / "collection/report.json").read_bytes()
            )
            receipt.source_status = report.status
            if (report.status not in {"updated", "no_change"} or not report.validation_passed
                    or not report.manifest_complete or report.errors
                    or not started <= report.checked_at <= datetime.now(timezone.utc)
                    or report.catalogs_checked != len(selection.catalogs)
                    or report.documents_checked != len(selection.documents)
                    or report.sources_checked
                    != len(selection.catalogs) + len(selection.documents)):
                raise ValueError(
                    "Child exited successfully without a complete validated source check"
                )
            receipt.outcome = "succeeded"
        return receipt.exit_code
    except (KeyboardInterrupt, SystemExit) as exc:
        status = exc.code if isinstance(exc, SystemExit) else 130
        receipt.exit_code = status if isinstance(status, int) and 1 <= status <= 255 else 1
        receipt.child_exit_code = getattr(exc, "child_exit_code", None)
        receipt.outcome, receipt.detail = "failed", "Collection interrupted"
        if receipt.child_exit_code is not None:
            receipt.detail += "; child stopped and reaped"
        return receipt.exit_code
    except Exception as exc:
        receipt.outcome, receipt.exit_code, receipt.detail = "failed", 1, str(exc)
        LOGGER.error("Scheduled county collection failed: %s", exc)
        return 1
    finally:
        receipt.phase, receipt.completed_at = "completed", datetime.now(timezone.utc)
        try:
            _write_receipt(run_dir / "completion.json", receipt)
        finally:
            if lock is not None:
                lock.close()
            if handler_installed:
                signal.signal(signal.SIGTERM, previous_handler)


def main(argv: list[str] | None = None) -> int:
    """Invoke a prepared collection service without installing or publishing anything."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("code-root", "root", "report-root", "manifest"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("expected-code-sha256", "expected-manifest-sha256"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=MAX_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        return run_scheduled_collection(**vars(args))
    except (OSError, ValueError) as exc:
        LOGGER.error("Unable to create county execution receipts: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
