"""Run four fixed manual-source watch pairs; retain truthful, bounded CI evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field

CONFIG = Path('config/manual_source_watch_ci.json')
CONFIG_SHA = '042af89caabc9cb5aa247052102d1ff2a6bbc088a6dd4b1143670eaee710abcb'
RUNTIME = Path('.geode_runtime/manual_source_watch_ci')
BATCH_IDS = ('springs', 'county-fees-v1', 'western-fees-v1', 'greeley-fees-v1')
COMPLETE = {'changed', 'unchanged'}
STATUSES = COMPLETE | {'access_denied', 'not_found', 'transport_error', 'invalid_response',
                       'refused', 'not_checked'}


class Strict(BaseModel):
    """Reject unrecognized fields and implicit coercions."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Pair(Strict):
    batch_id: str
    module: Literal['geode.pipeline.manual_source_watch',
                    'geode.pipeline.manual_source_watch_batches']
    selection: Ref
    source_ids: list[str] = Field(min_length=2, max_length=2)


class Plan(Strict):
    schema_version: Literal['manual-watch-ci-v1']
    pairs: list[Pair] = Field(min_length=4, max_length=4)
    immutable_inputs: list[Ref]
    max_source_events: Literal[16]
    max_source_body_bytes: Literal[16000000]
    max_source_seconds: Literal[1200]
    legal_currentness: Literal['not_verified']


class SourceResult(Strict):
    source_id: str
    status: str
    reason: str
    requested_url: str
    response_url: str | None
    http_status: int | None
    baseline_sha256: str
    response_sha256: str | None
    request_started_at: str | None
    response_finished_at: str | None


class PairResult(Strict):
    batch_id: str
    status: Literal['pending', 'verified', 'incomplete', 'setup_failed', 'execution_failed',
                    'verification_failed']
    execute_exit: int | None = None
    verify_exit: int | None = None
    reason: str | None = None
    sources: list[SourceResult] = Field(default_factory=list)
    report: Ref | None = None


class Summary(Strict):
    schema_version: Literal['manual-watch-ci-summary-v1'] = 'manual-watch-ci-summary-v1'
    created_at: str
    finished_at: str | None = None
    failure_reason: str | None = None
    event_context: Literal['schedule', 'workflow_dispatch', 'local_readiness']
    run_name: str
    commit_claim: str | None
    execution_requested: bool
    status: Literal['pending', 'ready', 'unchanged', 'changed', 'incomplete', 'setup_failed']
    pairs: list[PairResult]
    plan_sha256: str
    legal_currentness: Literal['not_verified'] = 'not_verified'
    baseline_updated: Literal[False] = False
    publication_attempted: Literal[False] = False
    schedule_activation_verified: Literal[False] = False
    producer_scheduler_flag_is_historical: Literal[True] = True


def utcnow() -> str:
    """Capture actual UTC time, never substitute an acquisition timestamp."""
    return datetime.now(timezone.utc).isoformat()


def ordinary(path: Path) -> bytes:
    """Require an ordinary file and ordinary ancestors before consuming it."""
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise ValueError('Missing or symlinked input: ' + str(path))
    return path.read_bytes()


def check_ref(root: Path, ref: Ref) -> bytes:
    """Check the captured bytes against an exact reviewed identity."""
    path = Path(ref.path)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != ref.path:
        raise ValueError('Unsafe evidence path')
    data = ordinary(root / path)
    if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError('Immutable input changed: ' + ref.path)
    return data


def load_plan(root: Path) -> Plan:
    """Load only the pinned four-pair plan and preflight all immutable inputs."""
    data = ordinary(root / CONFIG)
    if hashlib.sha256(data).hexdigest() != CONFIG_SHA:
        raise ValueError('Unreviewed CI plan')
    plan = Plan.model_validate_json(data)
    if tuple(p.batch_id for p in plan.pairs) != BATCH_IDS:
        raise ValueError('Wrong pair order or identity')
    if len({s for p in plan.pairs for s in p.source_ids}) != 8:
        raise ValueError('Repeated source identity')
    if len({r.path for r in plan.immutable_inputs}) != len(plan.immutable_inputs):
        raise ValueError('Duplicate immutable identity')
    for ref in plan.immutable_inputs:
        check_ref(root, ref)
    for pair in plan.pairs:
        data = check_ref(root, pair.selection)
        selection = json.loads(data)
        if [s['canonical_source_id'] for s in selection['targets']] != pair.source_ids:
            raise ValueError('Selected source identity differs')
        if selection['limits'] != {
            'requests': 4, 'distinct_urls': 4, 'redirects_per_source': 1,
            'bytes_per_source': 2000000, 'total_bytes': 4000000, 'request_seconds': 30
        } or selection['max_run_seconds'] != 300:
            raise ValueError('Selected source caps differ')
    return plan


def safe_output(root: Path, name: str) -> Path:
    """Create no output until name/root/path safety is established."""
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}', name):
        raise ValueError('Unsafe or overlong run name')
    out = root / RUNTIME / name
    if any(p.is_symlink() for p in (out, *out.parents)) or out.exists():
        raise ValueError('Output already exists or is symlinked; use a fresh invocation')
    return out


def command(root: Path, pair: Pair, name: str, mode: str) -> list[str]:
    """Construct one shell-free maintained command with exact batch selection."""
    argv = [sys.executable, '-B', '-m', pair.module, '--root', str(root)]
    if pair.batch_id != 'springs':
        argv += ['--batch', pair.batch_id]
    if mode == 'execute':
        argv += ['--execute', '--run-name', name,
                 '--reviewed-selection-sha256', pair.selection.sha256]
    elif mode == 'verify':
        argv += ['--verify-run', name]
    return argv


def invoke(argv: list[str], root: Path, out: Path, stem: str, timeout: int,
           run: Callable = subprocess.run) -> tuple[int, bytes]:
    """Retain every process result and partial output; never retry a timed-out call."""
    env = dict(os.environ)
    for key in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONOPTIMIZE', 'PYTHONSTARTUP'):
        env.pop(key, None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    started = utcnow()
    try:
        proc = run(argv, cwd=root, env=env, capture_output=True, timeout=timeout, check=False)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b'', error.stderr or b''
    except OSError as error:
        code, stdout, stderr = 127, b'', (type(error).__name__ + ': ' + str(error)).encode()
    for suffix, body in [('stdout', stdout), ('stderr', stderr)]:
        with (out / (stem + '.' + suffix)).open('xb') as handle:
            handle.write(body)
    receipt = {'argv': argv, 'started_at': started, 'finished_at': utcnow(), 'exit_code': code,
               'timeout_seconds': timeout, 'retried': False}
    with (out / (stem + '.process.json')).open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    return code, stdout


def read_verified(root: Path, pair: Pair, name: str, stdout: bytes) -> tuple[list[SourceResult], Ref]:
    """Bind the verifier's result to the actual report; retain source statuses verbatim."""
    runtime = 'manual_source_watch' if pair.batch_id == 'springs' else 'manual_source_watch_batches'
    path = root / '.geode_runtime' / runtime / name / 'report.json'
    data = ordinary(path)
    report = json.loads(data)
    if json.loads(stdout) != report:
        raise ValueError('Verifier output differs from saved report')
    if report['plan_sha256'] != pair.selection.sha256 or report['mode'] != 'live_http':
        raise ValueError('Wrong report plan or transport mode')
    if report['legal_currentness'] != 'not_verified' or report['baseline_updated'] is not False:
        raise ValueError('Unexpected promotion claim')
    observations = report['observations']
    if [s['canonical_source_id'] for s in observations] != pair.source_ids:
        raise ValueError('Wrong or incomplete source observations')
    results = []
    for obs in observations:
        if obs['status'] not in STATUSES or obs['legal_currentness'] != 'not_verified':
            raise ValueError('Unknown observation or legal claim')
        response = obs['response_body']
        results.append(SourceResult(
            source_id=obs['canonical_source_id'], status=obs['status'], reason=obs['reason'],
            requested_url=obs['requested_url'], response_url=obs['response_url'],
            http_status=obs['http_status'], baseline_sha256=obs['baseline']['sha256'],
            response_sha256=response['sha256'] if response else None,
            request_started_at=obs['request_started_at'],
            response_finished_at=obs['response_finished_at']))
    ref = Ref(path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
              size_bytes=len(data))
    return results, ref


def final_status(pairs: list[PairResult], execute: bool) -> str:
    """Preserve partial failures even when a sibling is unchanged or changed."""
    if any(p.status not in {'verified'} for p in pairs):
        return 'incomplete'
    if not execute:
        return 'ready'
    if any(s.status not in COMPLETE for p in pairs for s in p.sources):
        return 'incomplete'
    return 'changed' if any(s.status == 'changed' for p in pairs for s in p.sources) else 'unchanged'


def markdown(summary: Summary) -> str:
    """Render controlled identifiers/statuses only; arbitrary source text stays in JSON."""
    lines = ['# Manual PDF source watch', '', 'Result: **' + summary.status + '**.', '',
             'Fixed URL byte comparison only. Legal currentness is not verified; no baseline was updated.',
             '', '| Pair | Source ID | Outcome |', '|---|---|---|']
    for pair in summary.pairs:
        if pair.sources:
            for source in pair.sources:
                lines.append('| ' + pair.batch_id + ' | ' + source.source_id + ' | ' +
                             source.status + ' (' + pair.status + ') |')
        else:
            lines.append('| ' + pair.batch_id + ' | No verified source result | ' +
                         pair.status + ' |')
    lines += ['', 'A changed PDF needs review. Refused, missing, timed-out, or unverified results are not unchanged.',
              'Producer scheduler flags describe the historical component; this receipt does not certify schedule activation.', '']
    return '\n'.join(lines)


def save_summary(out: Path, summary: Summary) -> None:
    """Refresh only the CI progress summary, never overwrite retained source evidence."""
    for name, body in [('summary.json', summary.model_dump_json(indent=2) + '\n'),
                       ('summary.md', markdown(summary))]:
        path = out / name
        if path.is_symlink():
            raise ValueError('Symlinked summary')
        temp = out / (name + '.tmp')
        with temp.open('x', encoding='utf-8') as handle:
            handle.write(body)
        os.replace(temp, path)


def run_ci(root: Path, name: str, execute: bool, event: str, commit: str | None,
           run: Callable = subprocess.run) -> Summary:
    """Preflight all pairs before HTTP, execute once serially, verify and retain every result."""
    root = root.absolute()
    out = safe_output(root, name)
    out.mkdir(parents=True)
    summary = Summary(created_at=utcnow(), event_context=event, run_name=name, commit_claim=commit,
                      execution_requested=execute, status='pending', plan_sha256=CONFIG_SHA,
                      pairs=[PairResult(batch_id=p, status='pending') for p in BATCH_IDS])
    save_summary(out, summary)
    try:
        plan = load_plan(root)
        raw_path = root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
        raw_before = hashlib.sha256(ordinary(raw_path)).hexdigest()
        for pair, result in zip(plan.pairs, summary.pairs):
            code, _ = invoke(command(root, pair, name + '-' + pair.batch_id, 'readiness'),
                             root, out, pair.batch_id + '-readiness', 60, run)
            if code != 0:
                result.status, result.reason = 'setup_failed', 'Readiness failed; no HTTP started'
        load_plan(root)
        if any(p.status == 'setup_failed' for p in summary.pairs):
            summary.status = 'setup_failed'
            summary.failure_reason = 'At least one readiness check failed; no source HTTP started'
            return summary
        for pair, result in zip(plan.pairs, summary.pairs):
            load_plan(root)
            pair_name = name + '-' + pair.batch_id
            if not execute:
                result.status = 'verified'
                continue
            code, _ = invoke(command(root, pair, pair_name, 'execute'), root, out,
                             pair.batch_id + '-execute', 330, run)
            result.execute_exit = code
            load_plan(root)
            verify_code, stdout = invoke(command(root, pair, pair_name, 'verify'), root, out,
                                        pair.batch_id + '-verify', 60, run)
            result.verify_exit = verify_code
            try:
                # Maintained verification returns 2 for a valid but incomplete report.
                if verify_code not in (0, 2) or not stdout.strip():
                    raise ValueError('No verified report')
                result.sources, result.report = read_verified(root, pair, pair_name, stdout)
                complete = all(s.status in COMPLETE for s in result.sources)
                if (verify_code == 0) != complete or (code == 0) != complete:
                    raise ValueError('Exit status and observations disagree')
                result.status = 'verified' if complete else 'incomplete'
            except (ValueError, KeyError, TypeError, OSError) as error:
                result.status = 'verification_failed'
                result.reason = type(error).__name__ + ': ' + str(error)
            save_summary(out, summary)
        load_plan(root)
        if hashlib.sha256(ordinary(raw_path)).hexdigest() != raw_before:
            raise ValueError('Canonical manifest changed during CI invocation')
        summary.status = final_status(summary.pairs, execute)
    except (ValueError, OSError, KeyError) as error:
        summary.status = 'setup_failed'
        summary.failure_reason = type(error).__name__ + ': ' + str(error)
        for result in summary.pairs:
            if result.status == 'pending':
                result.status, result.reason = 'setup_failed', type(error).__name__ + ': ' + str(error)
    finally:
        summary.finished_at = utcnow()
        save_summary(out, summary)
        with (out / 'summary.schema.json').open('x', encoding='utf-8') as handle:
            json.dump(Summary.model_json_schema(), handle, indent=2)
            handle.write('\n')
    return summary


def main(argv: list[str] | None = None) -> int:
    """Default to offline readiness; live execution requires an explicit flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--event', choices=['schedule', 'workflow_dispatch', 'local_readiness'],
                        default='local_readiness')
    parser.add_argument('--commit', default=None)
    args = parser.parse_args(argv)
    try:
        result = run_ci(args.root, args.run_name, args.execute, args.event, args.commit)
        sys.stdout.write(result.model_dump_json(indent=2) + '\n')
        return 0 if result.status in {'ready', 'changed', 'unchanged'} else 2
    except (ValueError, OSError) as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
