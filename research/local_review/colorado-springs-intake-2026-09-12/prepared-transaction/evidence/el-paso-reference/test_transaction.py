"""Isolated fixture tests. Never call apply against the real repository or raw originals."""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import pytest

import transaction as tx


def write(root: Path, path: str, data: bytes) -> None:
    """Create synthetic fixture bytes only."""
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


@pytest.fixture
def fixture(tmp_path: Path) -> tuple[tx.Plan, Path, Path]:
    """Create 46 small synthetic originals, one missing historical row and 13 PDFs."""
    root, staged, state = tmp_path / "repo", tmp_path / "sources", tmp_path / "execution"
    root.mkdir(); staged.mkdir()
    when = datetime(2020, 1, 1, tzinfo=timezone.utc)
    old = []
    for i in range(46):
        sid = f"fixture-old-{i:02}"
        data = f"Isolated existing original fixture {i}".encode()
        path = f"_RAW_ARCHIVE/manual_intake/08_County_Authorities/{sid}/old.pdf"
        write(root, path, data)
        old.append(tx.ManualSourceIntakeRecord(
            intake_id="OLD-" + sid, record_id=sid, layer_id="08_County_Authorities",
            official_source_name="Fixture only", official_source_url=None,
            acquisition_method="received_review_package", received_from="Test fixture",
            reviewer_name="Test fixture", reviewer_email=None, custody_note="Synthetic fixture only",
            original_filename="old.pdf", archive_path=path, sha256=tx.digest(data), size_bytes=len(data),
            source_format="pdf", received_at=when, status="archived_pending_pipeline",
            blocked_queue_match=False, boundary="Fixture only",
        ))
    missing = old[0].model_copy(update={
        "intake_id": "MISSING-OLD", "record_id": "fixture-missing",
        "archive_path": "_RAW_ARCHIVE/manual_intake/08_County_Authorities/fixture-missing/missing.pdf",
    })
    raw = b"".join((r.model_dump_json() + "\n").encode() for r in old)
    # Deliberately retain noncanonical whitespace in one old line.
    raw = raw.replace(b'{"intake_id":', b'{  "intake_id" : ', 1)
    ledger = raw + (missing.model_dump_json() + "\n").encode()
    report = tx._report_from_records([*old, missing])
    report.archive_verification = tx.ManualIntakeArchiveVerification(
        manifest_records=46, verified_intake_ids=[r.intake_id for r in old],
        ledger_only_intake_ids=[missing.intake_id], missing_ledger_only_intake_ids=[missing.intake_id],
    )
    before = {tx.RAW: raw, tx.LEDGER: ledger, tx.REPORT: tx.encoded(report)}
    for name, data in before.items():
        write(root, name, data)
    guard = b"reviewed fixture policy\n"
    write(root, "policy.txt", guard)
    sources, templates = [], []
    for i in range(13):
        sid = f"fixture-new-{i:02}"
        with pymupdf.open() as doc:
            page = doc.new_page(); page.insert_text((72, 72), f"Isolated source {i}")
            data = doc.tobytes()
        write(staged, sid + ".pdf", data)
        original = tx.ref(sid + ".pdf", data).model_dump()
        sources.append(dict(source_id=sid, authority_id="CO-COUNTY-EL_PASO",
                            layer_id="08_County_Authorities", original=original))
        templates.append(dict(record_id=sid, acquisition_method="received_review_package",
                              expected_sha256=tx.digest(data), source_file=original,
                              official_source_name="Fixture only", official_source_url=None,
                              received_from="Fixture", reviewer_name="Fixture",
                              custody_note="Synthetic fixture; upstream acquisition unknown."))
    plan = tx.Plan("fixture-preparation", "fixture-provenance", tuple(sources), tuple(templates),
                   staged, before, (tx.ref("policy.txt", guard),))
    return plan, root, state


def membership(root: Path) -> dict[str, str]:
    """Capture exact fixture file bytes to test a no-write failure."""
    return {p.relative_to(root).as_posix(): tx.digest(p.read_bytes())
            for p in root.rglob("*") if p.is_file()}


def test_dry_run_has_no_outputs(fixture: tuple) -> None:
    """Read-only mode does not create state, snapshots or new raw files."""
    plan, root, state = fixture
    before = membership(root)
    result = tx.execute(plan, root, state)
    assert result["status"] == "dry_run_ready"
    assert result["actual_repository_received_at"] is None
    assert membership(root) == before and not state.exists()


def test_complete_prefixes_and_replay(fixture: tuple) -> None:
    """All 13 append once while original whitespace and one missing history row remain."""
    plan, root, state = fixture
    result = tx.execute(plan, root, state, apply=True)
    assert result["status"] == "verified_complete"
    intent = tx.Intent.model_validate_json((state / "INTENT.json").read_bytes())
    suffix = (state / "records.jsonl").read_bytes()
    for name in (tx.RAW, tx.LEDGER):
        assert (root / name).read_bytes() == plan.before[name] + suffix
    assert len(tx.rows((root / tx.RAW).read_bytes())) == 59
    assert len(tx.rows((root / tx.LEDGER).read_bytes())) == 60
    assert len({r.received_at for r in intent.records}) == 1
    assert all(r.acquisition_method == "received_review_package" for r in intent.records)
    before = membership(root), membership(state)
    assert tx.execute(plan, root, state, apply=True)["status"] == "verified_complete"
    assert before == (membership(root), membership(state))
    report = tx.ManualSourceIntakeReport.model_validate_json((root / tx.REPORT).read_bytes())
    assert report.archive_verification.missing_ledger_only_intake_ids == ["MISSING-OLD"]


@pytest.mark.parametrize("point", ["intent", "snapshots", "original:fixture-new-04",
                                   "raw_manifest", "ledger", "report"])
def test_interrupt_resume_keeps_time_and_ids(fixture: tuple, point: str) -> None:
    """Each interrupted boundary resumes the same immutable intent and suffix."""
    plan, root, state = fixture
    def stop(name: str) -> None:
        if name == point:
            raise KeyboardInterrupt("simulated interruption")
    with pytest.raises(KeyboardInterrupt):
        tx.execute(plan, root, state, apply=True, checkpoint=stop)
    intent = (state / "INTENT.json").read_bytes()
    tx.execute(plan, root, state, apply=True)
    assert (state / "INTENT.json").read_bytes() == intent
    assert tx.execute(plan, root, state, verify_only=True)["status"] == "verified_complete"


@pytest.mark.parametrize("kind", ["source", "baseline", "policy", "owner", "duplicate"])
def test_invalid_input_fails_before_repo_write(fixture: tuple, kind: str) -> None:
    """Tampered custody, old history, policy, wrong owner and duplicate bytes stop preflight."""
    plan, root, state = fixture
    if kind == "source":
        (plan.originals_root / "fixture-new-00.pdf").write_bytes(b"tampered")
    elif kind == "baseline":
        with (root / tx.RAW).open("ab") as handle:
            handle.write(b"foreign\n")
    elif kind == "policy":
        (root / "policy.txt").write_bytes(b"changed")
    elif kind == "owner":
        sources = copy.deepcopy(plan.sources)
        sources[0]["authority_id"] = "CO-MUNICIPAL-COLORADO_SPRINGS"
        plan = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256, sources,
                       plan.templates, plan.originals_root, plan.before, plan.guards)
    else:
        write(root, "_RAW_ARCHIVE/unrelated-copy.pdf",
              (plan.originals_root / "fixture-new-00.pdf").read_bytes())
    before = membership(root)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before and not state.exists()


def test_corrupt_partial_original_stops_replay(fixture: tuple) -> None:
    """Unexpected bytes at an intended raw path cannot be overwritten or blessed."""
    plan, root, state = fixture
    def stop(name: str) -> None:
        if name == "original:fixture-new-00":
            raise RuntimeError("stop")
    with pytest.raises(RuntimeError):
        tx.execute(plan, root, state, apply=True, checkpoint=stop)
    intent = tx.Intent.model_validate_json((state / "INTENT.json").read_bytes())
    (root / intent.records[0].archive_path).write_bytes(b"corrupt isolated new fixture")
    before = membership(root)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before


def test_foreign_ledger_and_tampered_intent_refused(fixture: tuple) -> None:
    """A restart accepts neither outside ledger edits nor altered approved records."""
    plan, root, state = fixture
    def stop(name: str) -> None:
        if name == "raw_manifest":
            raise RuntimeError("stop")
    with pytest.raises(RuntimeError):
        tx.execute(plan, root, state, apply=True, checkpoint=stop)
    with (root / tx.LEDGER).open("ab") as handle:
        handle.write(b"outside writer\n")
    before = membership(root)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before
    (root / tx.LEDGER).write_bytes(plan.before[tx.LEDGER])
    intent = json.loads((state / "INTENT.json").read_bytes())
    intent["records"][0]["sha256"] = "0" * 64
    (state / "INTENT.json").write_text(json.dumps(intent))
    before = membership(root)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before


def test_snapshot_symlink_prevents_any_apply(fixture: tuple, tmp_path: Path) -> None:
    """A snapshot escape is caught before creating an execution receipt or original."""
    plan, root, state = fixture
    outside = tmp_path / "outside"; outside.mkdir()
    (root / "_SNAPSHOTS").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert not state.exists() and not list(outside.iterdir())


def test_no_replace_on_existing_destination(fixture: tuple) -> None:
    """The write-once helper rejects a collision even after preliminary checks."""
    _, root, _ = fixture
    write(root, "new.pdf", b"first")
    with pytest.raises(ValueError):
        tx._write_once(root, "new.pdf", b"second", root / "stage")
    assert (root / "new.pdf").read_bytes() == b"first"


def test_unapproved_preparation_fails_before_verifier(monkeypatch: pytest.MonkeyPatch,
                                                      tmp_path: Path) -> None:
    """A changed input pin fails before executing a preparation-supplied verifier."""
    prep = tmp_path / "bad-preparation"; prep.mkdir()
    (prep / "PREPARATION.json").write_bytes(b"{}")
    monkeypatch.setattr(tx, "PREP", prep)
    monkeypatch.setattr(tx.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(ValueError, match="Unapproved preparation"):
        tx.load_plan(tmp_path)


@pytest.mark.parametrize("kind", ["relative_root", "escape", "directory", "parent_file", "missing"])
def test_ordinary_file_boundaries(tmp_path: Path, kind: str) -> None:
    """Reject lexical escapes and file/directory confusion without following outside paths."""
    with pytest.raises(ValueError):
        if kind == "relative_root":
            tx.safe(Path("relative"))
        elif kind == "escape":
            tx.safe(tmp_path, "../outside")
        elif kind == "directory":
            tx.destination(tmp_path, ".")
        elif kind == "parent_file":
            (tmp_path / "file").write_bytes(b"not a directory")
            tx.destination(tmp_path, "file/child")
        else:
            tx.checked(tmp_path, tx.ref("missing", b"expected"))


@pytest.mark.parametrize("kind", ["snapshot_file", "raw_symlink"])
def test_unsafe_archive_structure_has_no_apply(fixture: tuple, kind: str) -> None:
    """Unsafe preimage or raw directories fail before the immutable intent is created."""
    plan, root, state = fixture
    if kind == "snapshot_file":
        (root / "_SNAPSHOTS").write_bytes(b"not a directory")
    else:
        (root / "_RAW_ARCHIVE/alias").symlink_to(plan.originals_root, target_is_directory=True)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert not state.exists()


def test_out_of_order_publication_is_rejected(fixture: tuple) -> None:
    """An after-ledger with before-manifest is not a legitimate replay boundary."""
    plan, root, state = fixture
    def stop(name: str) -> None:
        if name == "intent":
            raise RuntimeError("stop")
    with pytest.raises(RuntimeError):
        tx.execute(plan, root, state, apply=True, checkpoint=stop)
    intent = tx.Intent.model_validate_json((state / "INTENT.json").read_bytes())
    _, after, _ = tx._derive(plan, root, intent.actual_repository_received_at)
    (root / tx.LEDGER).write_bytes(after[tx.LEDGER])
    before = membership(root)
    with pytest.raises(ValueError, match="publication order"):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before


def test_refuse_unapplied_or_false_completion_receipt(fixture: tuple) -> None:
    """Verification requires a real completed suffix and a receipt bound to its intent."""
    plan, root, state = fixture
    with pytest.raises(ValueError, match="not been applied"):
        tx.execute(plan, root, state, verify_only=True)
    tx.execute(plan, root, state, apply=True)
    receipt = json.loads((state / "RECEIPT.json").read_bytes())
    receipt["intent_sha256"] = "0" * 64
    (state / "RECEIPT.json").write_text(json.dumps(receipt))
    before = membership(root)
    with pytest.raises(ValueError, match="Receipt/intent"):
        tx.execute(plan, root, state, verify_only=True)
    assert membership(root) == before


def test_overlap_lock_prevents_second_apply(fixture: tuple) -> None:
    """A second invocation cannot mutate a corpus while the first holds its transaction lock."""
    plan, root, state = fixture
    state.mkdir()
    with (state / "transaction.lock").open("a+b") as lock:
        tx.fcntl.flock(lock.fileno(), tx.fcntl.LOCK_EX | tx.fcntl.LOCK_NB)
        before = membership(root)
        with pytest.raises(ValueError, match="holds the lock"):
            tx.execute(plan, root, state, apply=True)
        assert membership(root) == before and not (state / "INTENT.json").exists()


@pytest.mark.parametrize("name", ["INTENT.json", "transaction.lock"])
def test_special_state_files_do_not_block_or_apply(fixture: tuple, name: str) -> None:
    """Named pipes must be rejected as nonordinary files before opening them."""
    plan, root, state = fixture
    state.mkdir()
    tx.os.mkfifo(state / name)
    before = membership(root)
    with pytest.raises(ValueError, match="ordinary file"):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before
