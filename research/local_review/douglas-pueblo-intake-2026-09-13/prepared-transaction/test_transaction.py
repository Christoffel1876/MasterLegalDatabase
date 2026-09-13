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
    """Create 61 small synthetic originals, one missing historical row and two PDFs."""
    root, staged, state = tmp_path / "repo", tmp_path / "sources", tmp_path / "execution"
    root.mkdir(); staged.mkdir()
    when = datetime(2020, 1, 1, tzinfo=timezone.utc)
    old = []
    for i in range(61):
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
        manifest_records=61, verified_intake_ids=[r.intake_id for r in old],
        ledger_only_intake_ids=[missing.intake_id], missing_ledger_only_intake_ids=[missing.intake_id],
    )
    before = {tx.RAW: raw, tx.LEDGER: ledger, tx.REPORT: tx.encoded(report)}
    for name, data in before.items():
        write(root, name, data)
    guard = b"reviewed fixture policy\n"
    write(root, "policy.txt", guard)
    sources, templates = [], []
    for i in range(2):
        sid = ["douglas-ehs-fees-atlas-directed", "pueblo-planning-fees-atlas-directed"][i]
        with pymupdf.open() as doc:
            page = doc.new_page(); page.insert_text((72, 72), f"Isolated source {i}")
            data = doc.tobytes()
        write(staged, sid + ".pdf", data)
        original = tx.ref(sid + ".pdf", data).model_dump()
        sources.append(dict(source_id=f"SD014-{i+1:02}", proposed_record_id=sid, authority_id=("CO-COUNTY-DOUGLAS" if i==0 else "CO-MUNICIPAL-PUEBLO"),
                            layer_id=("08_County_Authorities" if i==0 else "10_Municipal_Authorities"), original=original, http_url=("https://www.douglasco.gov/documents/fee-schedule.pdf/" if i==0 else "https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId=")))
        templates.append(dict(record_id=sid, layer_id=("08_County_Authorities" if i==0 else "10_Municipal_Authorities"), acquisition_method="manual_official_download",
                              expected_sha256=tx.digest(data), source_file=original,
                              official_source_name="Fixture only", official_source_url=("https://www.douglasco.gov/documents/fee-schedule.pdf/" if i==0 else "https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId="),
                              reviewer_email=None,allow_duplicate=False,intake_id=None,archive_path=None,received_at=None,status="proposed_not_applied",original_filename=sid+".pdf",received_from="Fixture", reviewer_name="Fixture",
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
    """Both sources append once while original whitespace and one missing history row remain."""
    plan, root, state = fixture
    result = tx.execute(plan, root, state, apply=True)
    assert result["status"] == "verified_complete"
    intent = tx.Intent.model_validate_json((state / "INTENT.json").read_bytes())
    suffix = (state / "records.jsonl").read_bytes()
    for name in (tx.RAW, tx.LEDGER):
        assert (root / name).read_bytes() == plan.before[name] + suffix
    assert len(tx.rows((root / tx.RAW).read_bytes())) == 63
    assert len(tx.rows((root / tx.LEDGER).read_bytes())) == 64
    assert len({r.received_at for r in intent.records}) == 1
    assert all(r.acquisition_method == "manual_official_download" for r in intent.records)
    before = membership(root), membership(state)
    assert tx.execute(plan, root, state, apply=True)["status"] == "verified_complete"
    assert before == (membership(root), membership(state))
    report = tx.ManualSourceIntakeReport.model_validate_json((root / tx.REPORT).read_bytes())
    assert report.archive_verification.missing_ledger_only_intake_ids == ["MISSING-OLD"]


@pytest.mark.parametrize("point", ["intent", "snapshots", "original:pueblo-planning-fees-atlas-directed",
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
        (plan.originals_root / "douglas-ehs-fees-atlas-directed.pdf").write_bytes(b"tampered")
    elif kind == "baseline":
        with (root / tx.RAW).open("ab") as handle:
            handle.write(b"foreign\n")
    elif kind == "policy":
        (root / "policy.txt").write_bytes(b"changed")
    elif kind == "owner":
        sources = copy.deepcopy(plan.sources)
        sources[0]["authority_id"] = "CO-COUNTY-EL_PASO"
        plan = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256, sources,
                       plan.templates, plan.originals_root, plan.before, plan.guards)
    else:
        write(root, "_RAW_ARCHIVE/unrelated-copy.pdf",
              (plan.originals_root / "douglas-ehs-fees-atlas-directed.pdf").read_bytes())
    before = membership(root)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert membership(root) == before and not state.exists()


def test_corrupt_partial_original_stops_replay(fixture: tuple) -> None:
    """Unexpected bytes at an intended raw path cannot be overwritten or blessed."""
    plan, root, state = fixture
    def stop(name: str) -> None:
        if name == "original:douglas-ehs-fees-atlas-directed":
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


def test_actual_two_record_plan_is_read_only() -> None:
    """The real approved pair passes strict preflight without any actual intake."""
    before = {p: tx.digest((tx.DEFAULT_ROOT / p).read_bytes()) for p in tx.TARGETS}
    plan = tx.load_plan(tx.DEFAULT_ROOT)
    state = tx.BASE / 'execution'
    assert not state.exists()
    result = tx.execute(plan, tx.DEFAULT_ROOT, state)
    assert result['status'] == 'dry_run_ready' and result['sources'] == 2
    assert not state.exists()
    assert before == {p: tx.digest((tx.DEFAULT_ROOT / p).read_bytes()) for p in tx.TARGETS}
    assert [s['proposed_record_id'] for s in plan.sources] == [
        'douglas-ehs-fees-atlas-directed',
        'pueblo-planning-fees-atlas-directed']


@pytest.mark.parametrize('issue', ['host', 'layer', 'missing_null', 'source_url', 'filename'])
def test_final_validation_before_any_write(fixture: tuple, issue: str) -> None:
    """Former permissive-record/strict-reconciliation mismatch stops before intent/raw writes."""
    plan, root, state = fixture
    templates, sources = copy.deepcopy(plan.templates), copy.deepcopy(plan.sources)
    if issue == 'host':
        templates[0]['official_source_url'] = sources[0]['http_url'] = 'https://unapproved.invalid/x.pdf'
    elif issue == 'layer':
        templates[0]['layer_id'] = '09_District_Authorities'
    elif issue == 'missing_null':
        templates[0]['received_at'] = '2020-01-01T00:00:00Z'
    elif issue == 'source_url':
        sources[0]['http_url'] = 'https://www.pueblo.us/different.pdf'
    else:
        templates[0]['record_id'] = sources[0]['proposed_record_id'] = '../escape'
    plan = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256, sources,
                   templates, plan.originals_root, plan.before, plan.guards)
    before = membership(root)
    with pytest.raises(ValueError): tx.execute(plan, root, state, apply=True)
    assert membership(root) == before and not state.exists()


def test_strict_reconciliation_validator_called_before_write(fixture: tuple,
                                                            monkeypatch) -> None:
    plan, root, state = fixture
    def reject(*args): raise ValueError('strict record policy rejection')
    monkeypatch.setattr(tx, '_validate_reconciliation_record', reject)
    before = membership(root)
    with pytest.raises(ValueError, match='strict record'): tx.execute(plan, root, state, apply=True)
    assert before == membership(root) and not state.exists()


@pytest.mark.parametrize('name', ['records.jsonl', 'RECEIPT.json', 'unrelated.json'])
def test_orphan_or_foreign_state_rejected(fixture: tuple, name: str) -> None:
    plan, root, state = fixture;state.mkdir();(state / name).write_bytes(b'{}')
    before = membership(root), membership(state)
    with pytest.raises(ValueError): tx.execute(plan, root, state, apply=True)
    assert before == (membership(root), membership(state))


def test_global_lfs_pointer_collision(fixture: tuple) -> None:
    plan, root, state = fixture
    source = plan.sources[0]['original']
    pointer = ('version https://git-lfs.github.com/spec/v1\noid sha256:' +
               source['sha256'] + '\nsize ' + str(source['size_bytes']) + '\n').encode()
    write(root, '_RAW_ARCHIVE/legacy/source.pdf', pointer)
    before = membership(root)
    with pytest.raises(ValueError, match='LFS pointer'): tx.execute(plan, root, state, apply=True)
    assert before == membership(root) and not state.exists()


def test_canonical_original_uses_independent_inode(fixture: tuple) -> None:
    plan, root, state = fixture;tx.execute(plan, root, state, apply=True)
    intent = tx.Intent.model_validate_json((state/'INTENT.json').read_bytes())
    for source, record in zip(plan.sources, intent.records, strict=True):
        assert (plan.originals_root/source['original']['path']).stat().st_ino != (
            root/record.archive_path).stat().st_ino


def test_changed_runtime_pin_blocks_before_import_or_write(fixture: tuple, monkeypatch) -> None:
    plan, root, state = fixture
    monkeypatch.setattr(tx, 'RUNTIME_CODE', {'geode/constants.py': '0'*64})
    before = membership(root)
    with pytest.raises(ValueError, match='runtime changed'):tx.execute(plan, root, state, apply=True)
    assert before == membership(root) and not state.exists()


def test_interruption_after_each_of_two_originals(fixture: tuple) -> None:
    plan, root, state = fixture
    def stop(name):
        if name.startswith('original:'):raise RuntimeError('first original complete')
    with pytest.raises(RuntimeError):tx.execute(plan,root,state,apply=True,checkpoint=stop)
    assert (root/tx.RAW).read_bytes()==plan.before[tx.RAW]
    assert (root/tx.LEDGER).read_bytes()==plan.before[tx.LEDGER]
    tx.execute(plan,root,state,apply=True)
    assert tx.execute(plan,root,state,verify_only=True)['sources']==2


@pytest.mark.parametrize("mode", ["--dry-run", "--apply", "--verify"])
def test_cli_mode_dispatch(monkeypatch, tmp_path, mode):
    """CLI forwards mutually exclusive intent without changing hidden defaults."""
    root = tmp_path / "root"
    root.mkdir()
    calls = []
    sentinel = object()
    monkeypatch.setattr(tx, "load_plan", lambda selected: sentinel)
    def fake_execute(plan, selected, state, **kwargs):
        calls.append((plan, selected, state, kwargs))
        return {"status": "fixture"}
    monkeypatch.setattr(tx, "execute", fake_execute)
    monkeypatch.setattr(tx.sys, "argv", ["transaction.py", "--root", str(root), mode])
    tx.main()
    assert calls == [(sentinel, root, tx.BASE / "execution",
                      {"apply": mode == "--apply", "verify_only": mode == "--verify"})]


def test_cli_refuses_lexical_root_escape(monkeypatch, tmp_path):
    """The CLI refuses '..' before loading any source plan."""
    monkeypatch.setattr(tx.sys, "argv", ["transaction.py", "--root", str(tmp_path / "..")])
    with pytest.raises(SystemExit) as error:
        tx.main()
    assert error.value.code == 2


@pytest.mark.parametrize("issue", ["count", "newline", "archive_verification"])
def test_invalid_prefix_shape_never_creates_state(fixture, issue):
    """Even internally consistent malformed prefixes cannot start this exact migration."""
    plan, root, state = fixture
    before = dict(plan.before)
    if issue == "count":
        before[tx.RAW] += before[tx.RAW].splitlines(keepends=True)[0]
    elif issue == "newline":
        before[tx.RAW] = before[tx.RAW].rstrip(b"\n")
    else:
        report = json.loads(before[tx.REPORT])
        report["archive_verification"] = None
        before[tx.REPORT] = tx.encoded(report)
    changed = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256,
                      plan.sources, plan.templates, plan.originals_root, before, plan.guards)
    with pytest.raises(ValueError):
        tx.execute(changed, root, state, apply=True)
    assert not state.exists()


@pytest.mark.parametrize("issue", ["staging_file", "staging_extra", "staging_symlink", "raw_fifo"])
def test_nonordinary_staging_and_raw_refused(fixture, issue):
    """Staging remnants and global raw scans never follow links or open named pipes."""
    plan, root, state = fixture
    if issue == "raw_fifo":
        tx.os.mkfifo(root / "_RAW_ARCHIVE" / "not-a-file")
    else:
        state.mkdir()
        staging = state / ".staging"
        if issue == "staging_file":
            staging.write_bytes(b"wrong type")
        else:
            staging.mkdir()
            if issue == "staging_extra":
                (staging / "unrelated").write_bytes(b"foreign")
            else:
                (staging / "staged-link").symlink_to(root / tx.RAW)
    with pytest.raises(ValueError):
        tx.execute(plan, root, state, apply=True)
    assert not (state / "INTENT.json").exists()


def test_write_once_collision_preserves_other_writer(tmp_path, monkeypatch):
    """Atomic creation never overwrites a concurrent destination, even after preflight."""
    root, stage = tmp_path / "root", tmp_path / "stage"
    root.mkdir()
    def collision(source, target):
        target.write_bytes(b"outside writer")
        raise FileExistsError("simulated creation race")
    monkeypatch.setattr(tx.os, "link", collision)
    with pytest.raises(ValueError, match="Concurrent write collision"):
        tx._write_once(root, "original.pdf", b"expected", stage)
    assert (root / "original.pdf").read_bytes() == b"outside writer"
    assert list(stage.iterdir()) == []


@pytest.mark.parametrize('swap', ['url', 'authority_and_layer'])
def test_fixed_county_city_identity_cannot_be_swapped(fixture, swap):
    """An otherwise approved host/layer cannot be reassigned to the other selected source."""
    plan, root, state = fixture
    sources, templates = copy.deepcopy(plan.sources), copy.deepcopy(plan.templates)
    if swap == 'url':
        sources[0]['http_url'] = sources[1]['http_url']
        templates[0]['official_source_url'] = sources[1]['http_url']
    else:
        sources[0]['authority_id'] = sources[1]['authority_id']
        sources[0]['layer_id'] = templates[0]['layer_id'] = sources[1]['layer_id']
    changed = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256,
                      sources, templates, plan.originals_root, plan.before, plan.guards)
    before = membership(root)
    with pytest.raises(ValueError, match='authority mismatch'):
        tx.execute(changed, root, state, apply=True)
    assert membership(root) == before and not state.exists()


def test_final_records_keep_county_and_city_layers(fixture):
    """The mixed-layer transaction keeps both source identities and exact file parents."""
    plan, root, state = fixture
    tx.execute(plan, root, state, apply=True)
    intent = tx.Intent.model_validate_json((state / 'INTENT.json').read_bytes())
    assert [(r.record_id, r.layer_id) for r in intent.records] == [
        ('douglas-ehs-fees-atlas-directed', '08_County_Authorities'),
        ('pueblo-planning-fees-atlas-directed', '10_Municipal_Authorities')]
    for r in intent.records:
        assert r.archive_path.startswith(f'_RAW_ARCHIVE/manual_intake/{r.layer_id}/{r.record_id}/')


def test_pinned_metadata_consumed_from_captured_bytes(tmp_path, monkeypatch):
    """A later reread cannot replace the verified name, manifest, provenance or prefix."""
    import shutil
    from collections import Counter
    staged = tmp_path / 'preparation'
    shutil.copytree(tx.PREP, staged)
    original_read = Path.read_bytes
    pinned_data = json.loads(original_read(staged / 'PREPARATION.json'))
    expected_name = pinned_data['proposed_records'][0]['official_source_name']
    selected = {
        'PREPARATION.json', 'FINAL_MANIFEST.json', 'source-provenance.jsonl',
        'baseline/' + tx.RAW, 'baseline/' + tx.LEDGER,
    }
    counts = Counter()
    def late_substitution(path):
        if path.is_relative_to(staged):
            relative = path.relative_to(staged).as_posix()
            if relative in selected:
                counts[relative] += 1
                if counts[relative] > 1:
                    if relative == 'PREPARATION.json':
                        changed = copy.deepcopy(pinned_data)
                        changed['proposed_records'][0]['official_source_name'] = 'Unverified name'
                        return json.dumps(changed).encode()
                    return b'Unverified bytes returned only on a later read'
        return original_read(path)
    monkeypatch.setattr(tx, 'PREP', staged)
    monkeypatch.setattr(Path, 'read_bytes', late_substitution)
    plan = tx.load_plan(tmp_path)
    assert plan.templates[0]['official_source_name'] == expected_name
    assert plan.source_provenance_sha256 == tx.digest(
        original_read(staged / 'source-provenance.jsonl'))
    assert plan.before[tx.RAW] == original_read(staged / 'baseline' / tx.RAW)
    assert plan.before[tx.LEDGER] == original_read(staged / 'baseline' / tx.LEDGER)
    assert counts == {name: 1 for name in selected}


def test_source_changed_after_pinned_plan_still_refused(tmp_path, monkeypatch):
    """Captured metadata never substitutes for a fresh exact source read before writes."""
    import shutil
    staged = tmp_path / 'preparation'
    shutil.copytree(tx.PREP, staged)
    monkeypatch.setattr(tx, 'PREP', staged)
    plan = tx.load_plan(tmp_path)
    path = staged / plan.sources[0]['original']['path']
    path.write_bytes(b'Changed source after the approved metadata was captured')
    with pytest.raises(ValueError, match='Hash/size mismatch'):
        tx._source_bytes(plan)
    assert not (tmp_path / 'execution').exists()



def test_incoming_filename_cannot_be_invented(fixture):
    """The input basename, rather than a curated descriptive label, enters the raw record."""
    plan, root, state = fixture
    templates = copy.deepcopy(plan.templates)
    templates[0]['original_filename'] = 'invented_descriptive_publisher_name.pdf'
    changed = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256,
                      plan.sources, templates, plan.originals_root, plan.before, plan.guards)
    before = membership(root)
    with pytest.raises(ValueError, match='actual incoming basename'):
        tx.execute(changed, root, state, apply=True)
    assert membership(root) == before and not state.exists()
