"""Independent temporary-fixture execution; never applies the real repository."""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest

PREPARATION = Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/'
                   'popper-gunnison-intake-preparation')
sys.path.insert(0, str(PREPARATION))
import transaction as tx

spec = importlib.util.spec_from_file_location('provided_fixture', PREPARATION / 'test_transaction.py')
provided = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provided)


def setup(path: Path, patch: pytest.MonkeyPatch) -> tuple:
    """Reuse only the disclosed synthetic historical baseline construction."""
    return provided.fixture.__wrapped__(path, patch)


def files(root: Path) -> dict[str, bytes]:
    """Read all regular temporary files for exact immutability comparison."""
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def run() -> list[str]:
    """Exercise independent boundaries with exact three received source PDFs."""
    outcomes = []
    with tempfile.TemporaryDirectory(dir='/private/tmp', prefix='plato-gunnison-idempotence-') as temp:
        with pytest.MonkeyPatch.context() as patch:
            root, base, plan = setup(Path(temp), patch)
            before = files(root)
            dry = tx.run(root, base=base)
            assert files(root) == before and not (base / 'execution').exists()
            assert dry['actual_repository_received_at'] is None
            result = tx.run(root, base=base, apply=True)
            after = files(root)
            assert tx.run(root, base=base, apply=True) == result
            assert tx.run(root, base=base, verify=True) == result
            assert files(root) == after
            for name in (tx.RAW, tx.LEDGER):
                assert after[name].startswith(before[name])
                assert sum(1 for _ in (root / name).open('rb')) == 4
            report = tx.mi.ManualSourceIntakeReport.model_validate_json(after[tx.REPORT])
            assert report.archive_verification.manifest_records == 4
            outcomes.append('dry_run_no_writes_and_exact_prefix_idempotence_passed')
    with tempfile.TemporaryDirectory(dir='/private/tmp', prefix='plato-gunnison-receipt-') as temp:
        with pytest.MonkeyPatch.context() as patch:
            root, base, _ = setup(Path(temp), patch)
            def interrupt(stage: str) -> None:
                if stage == 'reconciled':
                    raise RuntimeError('independent terminal interruption')
            try:
                tx.run(root, base=base, apply=True, fault=interrupt)
                raise AssertionError('interruption not raised')
            except RuntimeError:
                pass
            before = files(root)
            assert not (base / 'execution/RECEIPT.json').exists()
            result = tx.run(root, base=base, apply=True)
            assert files(root) == before
            assert tx.run(root, base=base, verify=True) == result
            outcomes.append('terminal_receipt_recovery_without_canonical_rewrite_passed')
    with tempfile.TemporaryDirectory(dir='/private/tmp', prefix='plato-gunnison-foreign-') as temp:
        with pytest.MonkeyPatch.context() as patch:
            root, base, _ = setup(Path(temp), patch)
            observed = {}
            def arrival(stage: str) -> None:
                if stage == 'raw':
                    with (root / tx.RAW).open('rb') as handle:
                        foreign = json.loads(next(handle))
                    foreign['record_id'] = 'not-selected-gunnison'
                    foreign['intake_id'] = 'MSI-independent-foreign'
                    with (root / tx.RAW).open('ab') as handle:
                        handle.write((json.dumps(foreign) + '\n').encode())
                    observed.update(files(root))
            try:
                tx.run(root, base=base, apply=True, fault=arrival)
                raise AssertionError('foreign suffix accepted')
            except ValueError as exc:
                assert 'unrecognized canonical prefix' in str(exc)
            assert files(root) == observed
            assert b'MSI-independent-foreign' not in (root / tx.LEDGER).read_bytes()
            assert not (base / 'execution/RECEIPT.json').exists()
            outcomes.append('foreign_suffix_retained_and_not_promoted_passed')
    with tempfile.TemporaryDirectory(dir='/private/tmp', prefix='plato-gunnison-captured-source-') as temp:
        with pytest.MonkeyPatch.context() as patch:
            root, base, plan = setup(Path(temp), patch)
            original = tx.atomic_once
            source_path = base / plan.templates[0].source.path
            exact = source_path.read_bytes()
            invoked = []
            def late_change(path: Path, data: bytes) -> None:
                if path.parent.name == plan.templates[0].record_id:
                    source_path.write_bytes(b'UNVERIFIED LATE SOURCE SUBSTITUTION')
                    try:
                        original(path, data)
                        assert path.read_bytes() == exact
                        invoked.append(True)
                    finally:
                        source_path.write_bytes(exact)
                else:
                    original(path, data)
            patch.setattr(tx, 'atomic_once', late_change)
            result = tx.run(root, base=base, apply=True)
            assert invoked == [True] and source_path.read_bytes() == exact
            assert tx.run(root, base=base, verify=True) == result
            outcomes.append('late_source_ABA_does_not_change_consumed_canonical_bytes_passed')
    return outcomes


if __name__ == '__main__':
    sys.stdout.write('\n'.join(run()) + '\n')
