"""Additive prevalidated replay; no request or repository change without --apply."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

BASE = Path(__file__).absolute().parent
TRANSACTION = BASE.parent / 'el-paso-intake-transaction'
ROOT = BASE.parents[2] / 'MasterLegalDatabase'
TRANSACTION_SHA = '8b664308fb80a6d4338ec86900db840516d4146c330dfeec54fd52f2af2263e7'
INTENT_SHA = 'de90e01695abbc15162682c61f09eb99b01a973d45f86a1759a3eafb1375f742'
REVIEWED_FILES = {
    'geode/constants.py':
    '83dca55129755c9adb0829cae4cec1511d5b3624b452b5a6e826674a7e3b551a',
    'geode/schemas/validators.py':
    '8a1e279fa4979f53e9078c8204da21b0a2aba89db4a5c5d3095066d80ff4f076',
    'geode/pipeline/manual_source_intake.py':
    '5442b78cf16fb3b24f28a72f1c95753a444d39aaf8a906858e3fdcc9f439e0bd',
}
sys.dont_write_bytecode = True


def exact(path: Path, sha256: str) -> bytes:
    """Require exact reviewed ordinary bytes before importing or reading runtime inputs."""
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Nonordinary reviewed path')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError('Reviewed hash changed: ' + str(path))
    return data


def transaction_module() -> ModuleType:
    """Import only the frozen transaction whose exact source was independently reviewed."""
    exact(TRANSACTION / 'transaction.py', TRANSACTION_SHA)
    spec = importlib.util.spec_from_file_location('transaction', TRANSACTION / 'transaction.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validated_replay(
    tx: ModuleType, plan: Any, root: Path, state: Path, intent: Any, *,
    mode: Literal['dry-run', 'apply', 'verify'],
) -> dict:
    """Run full existing record validation before any unchanged transaction operation."""
    from geode.pipeline.manual_source_intake import _validate_reconciliation_record

    # Includes the official-host predicate missed by the original structural model check.
    for record in intent.records:
        _validate_reconciliation_record(root, record)
    tx._preflight(plan, root, intent)
    if mode == 'dry-run':
        return {'status': 'prevalidated_replay_ready', 'sources': 13,
                'repository_writes': 0, 'actual_repository_received_at':
                intent.actual_repository_received_at.isoformat(),
                'legal_currentness': 'not_verified'}
    return tx.execute(plan, root, state, apply=mode == 'apply', verify_only=mode == 'verify')


def main() -> None:
    """Pin reviewed policy, original intent and transaction, then select a bounded replay."""
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    for path, sha256 in REVIEWED_FILES.items():
        exact(ROOT / path, sha256)
    tx = transaction_module()
    intent = tx.Intent.model_validate_json(exact(TRANSACTION / 'execution/INTENT.json', INTENT_SHA))
    if intent.root != str(ROOT):
        raise ValueError('Interrupted intent belongs to another repository')
    plan = tx.load_plan(ROOT)
    mode = 'apply' if args.apply else 'verify' if args.verify else 'dry-run'
    result = validated_replay(tx, plan, ROOT, TRANSACTION / 'execution', intent, mode=mode)
    sys.stdout.write(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
