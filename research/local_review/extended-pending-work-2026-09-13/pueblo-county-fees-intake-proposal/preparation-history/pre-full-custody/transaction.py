"""Prepared one-source append; immutable inputs, exact prefixes, existing reconciliation API."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from pydantic import AwareDatetime, ConfigDict
from models import Asset, Preparation, Strict

BASE = Path(__file__).absolute().parent
RUNTIME_ROOT = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
PLAN_SHA = '49d4a7e90d005433969ef182b6974cf8101bcc3df10675c44bd884ddbeb40c4c'
RAW = '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
LEDGER = '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl'
REPORT = '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json'
ID = 'pueblo-county-planning-fees-sh-ext-002'
SOURCE_SHA = '1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084'
sys.dont_write_bytecode = True


def digest(raw: bytes) -> str:
    """Hash captured bytes."""
    return hashlib.sha256(raw).hexdigest()


def ordinary(root: Path, name: str, missing: bool = False) -> Path:
    """Reject nonordinary paths and symlink ancestors before reads or writes."""
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts or '\\' in name:
        raise ValueError('unsafe path')
    path = root / rel
    if any(p.is_symlink() for p in (path, *path.parents)) or any(
            p.exists() and not p.is_dir() for p in path.parents):
        raise ValueError('symlink path')
    if (path.exists() and not path.is_file()) or (not missing and not path.is_file()):
        raise ValueError('not an ordinary file: ' + name)
    return path


def capture(root: Path, asset: Asset) -> bytes:
    """Consume only the exact checked buffer."""
    raw = ordinary(root, asset.path).read_bytes()
    if len(raw) != asset.size_bytes or digest(raw) != asset.sha256:
        raise ValueError('input changed: ' + asset.path)
    return raw


def load_plan(base: Path = BASE) -> Preparation:
    """Read and validate the immutable prepared plan once."""
    raw = ordinary(base, 'PREPARATION.json').read_bytes()
    if digest(raw) != PLAN_SHA:
        raise ValueError('preparation pin differs')
    plan = Preparation.model_validate_json(raw)
    for path, expected in plan.runtime_pins.items():
        if digest(ordinary(RUNTIME_ROOT, path).read_bytes()) != expected:
            raise ValueError('reviewed runtime changed: ' + path)
    return plan


# Pin local runtime before importing its schemas and validated reconciliation functions.
load_plan()
sys.path.insert(0, str(RUNTIME_ROOT))
from geode.pipeline import manual_source_intake as mi


class NewRecord(mi.ManualSourceIntakeRecord):
    """Final received-package record; no implied independently verified acquisition."""
    model_config = ConfigDict(extra='forbid', strict=True)
    record_id: Literal['pueblo-county-planning-fees-sh-ext-002']
    layer_id: Literal['08_County_Authorities']
    official_source_url: None
    acquisition_method: Literal['received_review_package']
    original_filename: Literal['original.pdf']
    source_format: Literal['pdf']
    status: Literal['archived_pending_pipeline']
    blocked_queue_match: Literal[False]
    received_at: AwareDatetime


class Intent(Strict):
    """One actual application timestamp and final record, reused on interruption."""
    preparation_sha256: str
    actual_repository_received_at: AwareDatetime
    record: NewRecord


class Receipt(Strict):
    """Completion describes byte custody only."""
    status: Literal['completed_archived_pending_pipeline']
    preparation_sha256: str
    intent_sha256: str
    actual_repository_received_at: AwareDatetime
    raw_sha256: str
    ledger_sha256: str
    report_sha256: str
    raw_records: int
    ledger_records: int
    source_sha256: Literal['1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084']
    legal_currentness: Literal['not_verified']


def record_for(plan: Preparation, timestamp: datetime) -> NewRecord:
    """Construct a validated record using application time, never reported HTTP time."""
    t = plan.template
    stamp = timestamp.strftime('%Y%m%dT%H%M%S%fZ')
    return NewRecord(intake_id=f'MSI-{stamp}-{ID}', record_id=t.record_id, layer_id=t.layer_id,
        official_source_name=t.official_source_name, official_source_url=None,
        acquisition_method=t.acquisition_method, received_from='Sherlock SH-EXT-002 delivery',
        reviewer_name='Atlas', reviewer_email=None, custody_note=t.custody_note,
        original_filename=t.original_filename,
        archive_path=f'_RAW_ARCHIVE/manual_intake/{t.layer_id}/{ID}/{stamp}_original.pdf',
        sha256=t.source.sha256, size_bytes=t.source.size_bytes, source_format='pdf',
        received_at=timestamp, status='archived_pending_pipeline', blocked_queue_match=False,
        boundary=('Received byte custody only; no legal currentness, adoption, '
                  'or structured-rule promotion.'))


def atomic_once(path: Path, raw: bytes) -> None:
    """Atomically create immutable bytes or require the same existing bytes."""
    ordinary(path.parent, path.name, missing=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('immutable conflict: ' + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.intake-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.link(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def atomic_replace(path: Path, before: bytes, after: bytes) -> None:
    """Require exact old bytes and atomically replace with their deterministic suffix."""
    ordinary(path.parent, path.name)
    if path.read_bytes() != before:
        raise ValueError('prefix changed before replacement')
    fd, temp = tempfile.mkstemp(prefix='.intake-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(after)
            out.flush()
            os.fsync(out.fileno())
        if path.read_bytes() != before:
            raise ValueError('prefix changed during replacement')
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def preflight(root: Path, base: Path, plan: Preparation, record: NewRecord | None) -> dict:
    """Validate every current/input/source binding before any canonical mutation."""
    raw_source = capture(base, plan.template.source)
    if digest(raw_source) != SOURCE_SHA or len(raw_source) != 75214:
        raise ValueError('wrong selected PDF')
    if plan.template.authority_id != 'CO-COUNTY-PUEBLO':
        raise ValueError('wrong authority')
    if Path(plan.template.source.path).name != plan.template.original_filename:
        raise ValueError('incoming filename differs')
    for asset in [plan.source_review, plan.source_review_schema, plan.independent_review,
                  plan.root_source_qa_approval]:
        capture(base, asset)
    approval = json.loads(capture(base, plan.root_source_qa_approval))
    if (approval['source_id'] != ID or approval['authority_id'] != 'CO-COUNTY-PUEBLO'
            or approval['source']['sha256'] != SOURCE_SHA
            or approval['source_qa']['sha256'] != plan.source_review.sha256
            or approval['status'] != 'accepted_complete_source_fidelity_pending_separate_intake'
            or approval['legal_currentness'] != 'not_verified' or approval['answer_safe']):
        raise ValueError('source-fidelity approval differs')
    ordinary(root, '_SNAPSHOTS/.preflight', missing=True)
    original = {r.repository_path: capture(base, r.preserved) for r in plan.baseline}
    current = {name: ordinary(root, name).read_bytes() for name in original}
    suffix = (record.model_dump_json() + '\n').encode() if record else b''
    for name in [RAW, LEDGER]:
        if not original[name].endswith(b'\n'):
            raise ValueError('historical JSONL lacks final newline')
        allowed = [original[name]] + ([original[name] + suffix] if record else [])
        if current[name] not in allowed:
            raise ValueError('unrecognized canonical prefix/state: ' + name)
    for name in original.keys() - {RAW, LEDGER, REPORT}:
        if current[name] != original[name]:
            raise ValueError('guard changed: ' + name)
    if (plan.raw_after != plan.raw_before + 1 or
            plan.ledger_after != plan.ledger_before + 1):
        raise ValueError('proposed count equation differs')
    if mi._blocked_queue_contains(root, ID):
        raise ValueError('unexpected blocked-queue match')
    for name in [RAW, LEDGER]:
        count = 0
        with io.BytesIO(original[name]) as handle:
            for line in handle:
                count += 1
                row = mi.ManualSourceIntakeRecord.model_validate_json(line)
                mi._validate_reconciliation_record(root, row)
                if row.record_id == ID or row.sha256 == SOURCE_SHA:
                    raise ValueError('source already present in frozen baseline')
        expected_count = plan.raw_before if name == RAW else plan.ledger_before
        if count != expected_count:
            raise ValueError('baseline count differs')
    if record:
        expected = record_for(plan, record.received_at)
        if record != expected:
            raise ValueError('intent record differs')
        dest = mi._validate_reconciliation_record(root, record)
        ordinary(root, record.archive_path, missing=True)
        if dest.exists() and dest.read_bytes() != raw_source:
            raise ValueError('source destination conflict')
        if current[RAW] == original[RAW] and current[LEDGER] != original[LEDGER]:
            raise ValueError('ledger ahead of raw manifest')
    elif current[REPORT] != original[REPORT]:
        raise ValueError('report baseline changed')
    preview = mi.reconcile_manual_source_intake(root, dry_run=True)
    if current[REPORT] != original[REPORT] and preview.report_needs_update:
        raise ValueError('unrecognized changed report')
    if current[RAW] == original[RAW] and (preview.added_intake_ids or preview.report_needs_update):
        raise ValueError('baseline requires unrelated reconciliation')
    return {'original': original, 'current': current, 'suffix': suffix,
            'source': raw_source, 'preview': preview}


def run(root: Path, *, apply: bool = False, verify: bool = False,
        base: Path = BASE, fault: Callable[[str], None] = lambda _: None) -> dict:
    """Prepare by default; apply only after separate root review and explicit CLI selection."""
    root = root.expanduser().absolute()
    plan = load_plan(base)
    execution = base / 'execution'
    intent_path = ordinary(execution, 'INTENT.json', missing=True)
    intent = Intent.model_validate_json(intent_path.read_bytes()) if intent_path.exists() else None
    if intent and (intent.preparation_sha256 != PLAN_SHA or
                   intent.record.received_at != intent.actual_repository_received_at):
        raise ValueError('intent identity differs')
    state = preflight(root, base, plan, intent.record if intent else None)
    if not apply and not verify:
        return {'status': 'dry_run', 'raw_before': plan.raw_before, 'raw_after': plan.raw_after,
                'ledger_before': plan.ledger_before, 'ledger_after': plan.ledger_after,
                'actual_repository_received_at': None if intent is None else
                    intent.actual_repository_received_at.isoformat(),
                'source_qa_approval_sha256': plan.root_source_qa_approval.sha256,
                'canonical_mutations': 0}
    if verify and intent is None:
        raise ValueError('no completed execution to verify')
    if apply:
        ordinary(execution, 'LOCK', missing=True)
        execution.mkdir(parents=True, exist_ok=True)
        with (execution / 'LOCK').open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Re-read under lock so simultaneous calls cannot choose different receipt times.
            if intent_path.exists():
                intent = Intent.model_validate_json(intent_path.read_bytes())
            else:
                now = datetime.now(timezone.utc)
                candidate = Intent(preparation_sha256=PLAN_SHA,
                    actual_repository_received_at=now, record=record_for(plan, now))
                preflight(root, base, plan, candidate.record)
                atomic_once(intent_path, candidate.model_dump_json(indent=2).encode() + b'\n')
                intent = candidate
            if (intent.preparation_sha256 != PLAN_SHA or
                    intent.actual_repository_received_at != intent.record.received_at):
                raise ValueError('intent pin differs')
            state = preflight(root, base, plan, intent.record)
            for name, raw in state['original'].items():
                atomic_once(execution / 'preimages' / Path(name).name, raw)
            fault('intent')
            source = ordinary(root, intent.record.archive_path, missing=True)
            atomic_once(source, state['source'])
            fault('original')
            if state['current'][RAW] == state['original'][RAW]:
                atomic_replace(root / RAW, state['original'][RAW],
                               state['original'][RAW] + state['suffix'])
            fault('raw')
            # Existing API preserves ledger bytes and repairs interrupted report writes.
            mi.reconcile_manual_source_intake(root, dry_run=False)
            fault('reconciled')
            state = preflight(root, base, plan, intent.record)
            if state['preview'].added_intake_ids or state['preview'].report_needs_update:
                raise ValueError('reconciliation incomplete')
            receipt = Receipt(status='completed_archived_pending_pipeline',
                preparation_sha256=PLAN_SHA, intent_sha256=digest(intent_path.read_bytes()),
                actual_repository_received_at=intent.actual_repository_received_at,
                raw_sha256=digest(state['current'][RAW]),
                ledger_sha256=digest(state['current'][LEDGER]),
                report_sha256=digest(state['current'][REPORT]), raw_records=plan.raw_after,
                ledger_records=plan.ledger_after, source_sha256=SOURCE_SHA,
                legal_currentness='not_verified')
            receipt_bytes = receipt.model_dump_json(indent=2).encode() + b'\n'
            atomic_once(execution / 'RECEIPT.json', receipt_bytes)
    # Complete-state verification is independent of whether this call applied anything.
    receipt = Receipt.model_validate_json(ordinary(execution, 'RECEIPT.json').read_bytes())
    state = preflight(root, base, plan, intent.record)
    if (receipt.preparation_sha256 != PLAN_SHA
            or receipt.intent_sha256 != digest(intent_path.read_bytes())
            or receipt.actual_repository_received_at != intent.actual_repository_received_at
            or receipt.raw_sha256 != digest(state['current'][RAW])
            or receipt.ledger_sha256 != digest(state['current'][LEDGER])
            or receipt.report_sha256 != digest(state['current'][REPORT])
            or receipt.raw_records != plan.raw_after or receipt.ledger_records != plan.ledger_after
            or state['current'][RAW] != state['original'][RAW] + state['suffix']
            or state['current'][LEDGER] != state['original'][LEDGER] + state['suffix']
            or state['preview'].added_intake_ids or state['preview'].report_needs_update):
        raise ValueError('completed receipt/state differs')
    return receipt.model_dump(mode='json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=RUNTIME_ROOT)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--dry-run', action='store_true')
    action.add_argument('--apply', action='store_true')
    action.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    try:
        result = run(args.root, apply=args.apply, verify=args.verify)
    except (ValueError, OSError) as error:
        sys.stderr.write(str(error) + '\n')
        raise SystemExit(1)
    sys.stdout.write(json.dumps(result, indent=2) + '\n')
