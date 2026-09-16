"""Independent temporary-corpus probes; never apply the actual repository."""
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

BASE = Path(__file__).resolve().parent / 'reviewed-preparation'
sys.path.insert(0, str(BASE))
import transaction as tx

spec = importlib.util.spec_from_file_location('provided_fixture', BASE / 'test_transaction.py')
provided = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provided)


def setup(path: Path, patch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    """Reuse only the disclosed synthetic historical baseline constructor."""
    return provided.fixture.__wrapped__(path, patch)


def files(root: Path) -> dict[str, bytes]:
    """Capture regular temporary files for exact before/after comparison."""
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def run() -> list[str]:
    """Exercise eight bounded conditions using the exact one received PDF body."""
    outcomes = []
    for case in range(8):
        with tempfile.TemporaryDirectory(dir='/private/tmp', prefix='plato-chaffee-fee-probe-') as temp:
            with pytest.MonkeyPatch.context() as patch:
                root, base, plan = setup(Path(temp), patch)
                initial = files(root)
                if case == 0:
                    dry = tx.run(root, base=base)
                    assert files(root) == initial and not (base / 'execution').exists()
                    assert dry['actual_repository_received_at'] is None
                    result = tx.run(root, base=base, apply=True)
                    after = files(root)
                    assert tx.run(root, base=base, apply=True) == result
                    assert tx.run(root, base=base, verify=True) == result
                    assert files(root) == after
                    intent = tx.Intent.model_validate_json(
                        (base / 'execution/INTENT.json').read_bytes())
                    suffix = b''.join((r.model_dump_json() + '\n').encode()
                                      for r in intent.records)
                    for name in (tx.RAW, tx.LEDGER):
                        assert after[name] == initial[name] + suffix
                        with (root / name).open('rb') as handle:
                            assert sum(1 for _ in handle) == 2
                    assert len(intent.records) == 1 and result['raw_records'] == 2
                    assert result['legal_currentness'] == 'not_verified'
                    assert result['answer_safe'] is False
                    for row, template, provenance in zip(
                            intent.records, plan.templates, plan.provenance):
                        assert row.official_source_url == provenance.final_url
                        assert row.acquisition_method == 'manual_official_download'
                        assert row.received_at >= provenance.http_completed_at
                        assert row.original_filename == 'original.pdf'
                        assert (root / row.archive_path).read_bytes() == (
                            base / template.source.path).read_bytes()
                    outcomes.append('exact_one_source_prefix_and_noop_replay_passed')
                elif case == 1:
                    def interrupt(stage: str) -> None:
                        """Stop after canonical metadata, before completion receipt."""
                        if stage == 'reconciled':
                            raise RuntimeError('independent terminal interruption')
                    with pytest.raises(RuntimeError):
                        tx.run(root, base=base, apply=True, fault=interrupt)
                    before = files(root)
                    times = {p: p.stat().st_mtime_ns for p in root.rglob('*') if p.is_file()}
                    intent = (base / 'execution/INTENT.json').read_bytes()
                    assert not (base / 'execution/RECEIPT.json').exists()
                    result = tx.run(root, base=base, apply=True)
                    assert files(root) == before
                    assert {p: p.stat().st_mtime_ns for p in times} == times
                    assert (base / 'execution/INTENT.json').read_bytes() == intent
                    assert tx.run(root, base=base, verify=True) == result
                    outcomes.append('missing_receipt_resume_no_canonical_rewrite_passed')
                elif case == 2:
                    original = tx.atomic_once
                    source = base / plan.templates[0].source.path
                    exact = source.read_bytes()
                    hits = []
                    def late_source(path: Path, data: bytes) -> None:
                        """Substitute and restore source only after its buffer was checked."""
                        if path.parent.name == plan.templates[0].record_id:
                            source.write_bytes(b'UNVERIFIED SOURCE ABA')
                            try:
                                original(path, data)
                                assert path.read_bytes() == exact
                                hits.append(True)
                            finally:
                                source.write_bytes(exact)
                        else:
                            original(path, data)
                    patch.setattr(tx, 'atomic_once', late_source)
                    result = tx.run(root, base=base, apply=True)
                    assert hits == [True]
                    assert tx.run(root, base=base, verify=True) == result
                    outcomes.append('captured_original_buffer_resists_late_ABA_passed')
                elif case == 3:
                    original = tx.capture
                    parent = base / plan.provenance[0].parent.path
                    exact = parent.read_bytes()
                    hits = []
                    def late_parent(folder: Path, item: Any) -> bytes:
                        """Change parent after all custody buffers were captured."""
                        value = original(folder, item)
                        if item.path == plan.custody_subset[-1].path:
                            parent.write_bytes(b'UNVERIFIED REFERRAL ABA')
                            hits.append(True)
                        return value
                    patch.setattr(tx, 'capture', late_parent)
                    try:
                        bodies = tx.check_custody(base, plan)
                        assert hits == [True]
                        assert [tx.digest(x) for x in bodies] == [
                            t.source.sha256 for t in plan.templates]
                    finally:
                        parent.write_bytes(exact)
                    assert files(root) == initial
                    outcomes.append('captured_parent_referral_resists_late_ABA_passed')
                elif case == 4:
                    def at_intent(stage: str) -> None:
                        """Leave a valid intent before any original writes."""
                        if stage == 'intent':
                            raise RuntimeError('fixture intent stop')
                    with pytest.raises(RuntimeError):
                        tx.run(root, base=base, apply=True, fault=at_intent)
                    intent = tx.Intent.model_validate_json(
                        (base / 'execution/INTENT.json').read_bytes())
                    (root / tx.REPORT).write_bytes(tx.report_bytes(intent))
                    before = files(root)
                    with pytest.raises(ValueError, match='phase order'):
                        tx.run(root, base=base, apply=True)
                    assert files(root) == before
                    outcomes.append('report_ahead_of_raw_and_originals_refused_passed')
                elif case == 5:
                    class EarlyClock(datetime):
                        """Simulate an intake clock earlier than retained acquisition."""
                        @classmethod
                        def now(cls, tz: Any = None) -> datetime:
                            """Return a fixed deliberately invalid pre-acquisition time."""
                            return datetime(2026, 9, 13, 16, 0, tzinfo=timezone.utc)
                    patch.setattr(tx, 'datetime', EarlyClock)
                    with pytest.raises(ValueError, match='precedes observed acquisition'):
                        tx.run(root, base=base, apply=True)
                    assert files(root) == initial
                    assert not (base / 'execution/INTENT.json').exists()
                    outcomes.append('repository_time_cannot_precede_HTTP_completion_passed')
                elif case == 6:
                    observed = {}
                    def arrival(stage: str) -> None:
                        """Append an unrelated raw line at a reviewed boundary."""
                        if stage == 'raw':
                            with (root / tx.RAW).open('rb') as handle:
                                row = tx.mi.ManualSourceIntakeRecord.model_validate_json(
                                    next(handle))
                            data = row.model_dump(mode='json')
                            data.update(record_id='foreign-unselected', intake_id='MSI-foreign')
                            record = tx.mi.ManualSourceIntakeRecord.model_validate_json(
                                json.dumps(data))
                            with (root / tx.RAW).open('ab') as handle:
                                handle.write((record.model_dump_json() + '\n').encode())
                            observed.update(files(root))
                    with pytest.raises(ValueError, match='unrecognized canonical prefix'):
                        tx.run(root, base=base, apply=True, fault=arrival)
                    assert files(root) == observed
                    assert b'MSI-foreign' not in (root / tx.LEDGER).read_bytes()
                    assert not (base / 'execution/RECEIPT.json').exists()
                    outcomes.append('foreign_suffix_preserved_without_ledger_promotion_passed')
                else:
                    source = base / plan.templates[0].source.path
                    saved = source.with_suffix('.saved')
                    source.rename(saved)
                    source.symlink_to(saved)
                    with pytest.raises(ValueError, match='symlink'):
                        tx.run(root, base=base, apply=True)
                    assert files(root) == initial and not (base / 'execution').exists()
                    outcomes.append('linked_incoming_original_refused_before_mutation_passed')
    assert len(outcomes) == len(set(outcomes)) == 8
    return outcomes


if __name__ == '__main__':
    sys.stdout.write('\n'.join(run()) + '\n')
