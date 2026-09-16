"""Finite two-source byte watch prototype; default CLI is entirely offline."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal
from urllib.parse import urlsplit

import jsonschema
import pymupdf
from pydantic import AwareDatetime, Field, model_validator

HERE = Path(__file__).resolve().parent
GUARD_SHA = '2d4823b93fa6c4b96d9b7d218284cb9a787d820282bfb3bac84a57e1783a8635'
SCOPE_SHA = 'd5ad6056f8b7d820dfd01d09366744dc368fe6c604811eddfb0f225616f94ef5'
CUSTODY_SHA = '075bc58360d45c949418f4852ebac89375b86694c6122823c7c9c760c1ecded2'
_guard_path = HERE / 'sd014_guard.py'
if _guard_path.is_symlink() or hashlib.sha256(_guard_path.read_bytes()).hexdigest() != GUARD_SHA:
    raise ValueError('Frozen transport helper identity mismatch')
_spec = importlib.util.spec_from_file_location('manual_watch_sd014_guard', _guard_path)
g = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = g
_spec.loader.exec_module(g)

IDENTITIES = {
    'SD014-01': (
        'colorado-springs-code-services-fees-2015-atlas-directed',
        'https://coloradosprings.gov/system/files/feeschedule_codeservices_final_2015.pdf',
        '555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56', 162682),
    'SD014-02': (
        'colorado-springs-construction-fees-atlas-directed',
        'https://coloradosprings.gov/system/files/2026-07/'
        '2026%20Fee%20Schedule%20Construction%20Services.pdf',
        'e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a', 258393),
}
NO_NEW = datetime(2026, 9, 13, 1, 25, tzinfo=timezone.utc)
HARD_STOP = datetime(2026, 9, 13, 1, 55, tzinfo=timezone.utc)


class Target(g.Target):
    """A fixed official URL and verified previous source bytes, without legal status."""
    canonical_source_id: str
    authority_id: Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    baseline: g.Ref
    baseline_page_count: Literal[7]
    baseline_request_started_at: AwareDatetime
    baseline_response_finished_at: AwareDatetime
    repository_received_at: None = None
    repository_time_basis: Literal['not_yet_received_at_prototype_preparation']
    source_context: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Limits(g.Limits):
    """Narrow limits for two small existing PDFs; redirects consume request capacity."""
    requests: int = Field(default=4, ge=1, le=4)
    distinct_urls: int = Field(default=4, ge=1, le=4)
    redirects_per_source: int = Field(default=1, ge=0, le=1)
    bytes_per_source: int = Field(default=2_000_000, ge=1, le=2_000_000)
    total_bytes: int = Field(default=4_000_000, ge=1, le=4_000_000)


class Plan(g.Strict):
    """One proposed finite invocation; scheduling and canonical updates are excluded."""
    status: Literal['PREPARED_NOT_DISPATCHED']
    targets: list[Target] = Field(min_length=2, max_length=2)
    limits: Limits
    custody_scope: g.Ref
    custody_manifest: g.Ref
    proposed_finish_by: AwareDatetime
    no_new_source_at: AwareDatetime
    hard_stop: AwareDatetime
    max_run_seconds: Literal[300] = 300
    cadence_proposal: Literal['daily_after_separate_deployment_approval']
    automatic_baseline_updates: Literal[False] = False
    qualifications: list[str]

    @model_validator(mode='after')
    def fixed_sources(self) -> Plan:
        """Refuse replacement URLs, IDs, expected bytes or expanded time bounds."""
        if [t.source_id for t in self.targets] != ['SD014-01', 'SD014-02']:
            raise ValueError('Exactly the two ordered reviewed sources are required')
        for target in self.targets:
            identity = IDENTITIES[target.source_id]
            if (target.canonical_source_id, target.url, target.baseline.sha256,
                    target.baseline.size_bytes) != identity:
                raise ValueError('Source URL/ID/baseline substitution refused')
            g.safe_url(target.url)
            g.safe_url(target.parent_url)
            if target.baseline.path != f'evidence/custody/{target.source_id}/original.pdf':
                raise ValueError('Unexpected baseline original path')
        if (self.proposed_finish_by > HARD_STOP or self.hard_stop > HARD_STOP
                or self.no_new_source_at > NO_NEW
                or self.no_new_source_at > self.hard_stop
                or self.proposed_finish_by > self.hard_stop):
            raise ValueError('Watch exceeds authorized outer window')
        if (self.custody_scope.sha256 != SCOPE_SHA or
                self.custody_scope.path != 'evidence/custody/SOURCE_SCOPE.json' or
                self.custody_manifest.sha256 != CUSTODY_SHA or
                self.custody_manifest.path != 'evidence/custody/FINAL_MANIFEST.json'):
            raise ValueError('Wrong source custody receipt')
        return self


class Observation(g.Strict):
    """Transport/byte observations only; an absent response is never an unchanged source."""
    source_id: str
    canonical_source_id: str
    authority_id: Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    requested_url: str
    baseline: g.Ref
    baseline_request_started_at: AwareDatetime
    baseline_response_finished_at: AwareDatetime
    source_context: list[str]
    status: Literal['unchanged', 'changed', 'access_denied', 'not_found', 'transport_error',
                    'invalid_response', 'refused', 'not_checked']
    reason: str
    events: list[int]
    request_started_at: AwareDatetime | None
    response_finished_at: AwareDatetime | None
    response_url: str | None
    http_status: int | None
    response_body: g.Ref | None
    response_public_headers: g.Ref | None
    valid_pdf_pages: int | None
    bytes_equal_to_baseline: bool | None
    review_needed: bool
    legal_currentness: Literal['not_verified'] = 'not_verified'
    inferred_legal_change: None = None
    canonical_update: Literal['not_attempted'] = 'not_attempted'


class Invocation(g.Strict):
    """Bound operator-supplied invocation metadata, distinct from HTTP evidence."""
    recorded_at: AwareDatetime
    dispatch_at: AwareDatetime
    plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    implementation_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    transport_sha256: Literal[GUARD_SHA]
    mode: Literal['live_http', 'offline_fixture']
    clock_basis: Literal['actual_utc_clock', 'injected_fixture_clock']
    authorization_basis: Literal['operator_supplied_time_and_plan_digest_not_independent_proof']


class Report(g.Strict):
    """Immutable per-invocation result with time/clock origin and incomplete scope explicit."""
    status: Literal['completed', 'stopped']
    mode: Literal['live_http', 'offline_fixture']
    clock_basis: Literal['actual_utc_clock', 'injected_fixture_clock']
    generated_at: AwareDatetime
    plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    implementation_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    invocation: g.Ref
    transport_sha256: Literal[GUARD_SHA]
    authorization_basis: Literal['operator_supplied_time_and_plan_digest_not_independent_proof']
    dispatch_at: AwareDatetime
    stop_reason: str | None
    state: g.State
    observations: list[Observation] = Field(min_length=2, max_length=2)
    legal_currentness: Literal['not_verified'] = 'not_verified'
    publication_status: Literal['not_attempted'] = 'not_attempted'
    scheduler_installed: Literal[False] = False
    baseline_updated: Literal[False] = False


class FileInventory(g.Strict):
    """Closed files; runtime inventory includes every event even after failure."""
    kind: Literal['prototype', 'run']
    files: list[g.Ref]

    @model_validator(mode='after')
    def unique_paths(self) -> FileInventory:
        """Reject ambiguous inventories."""
        if len({f.path for f in self.files}) != len(self.files):
            raise ValueError('Duplicate inventory member')
        return self


def load_plan(path: Path) -> Plan:
    """Validate the immutable custody subset and exact original iframe referrals offline."""
    plan = Plan.model_validate_json(g.ordinary(path).read_bytes())
    root = path.parent
    scope_data = g.check_ref(root, plan.custody_scope).read_bytes()
    schema = json.loads(g.ordinary(root / 'evidence/custody/SOURCE_SCOPE.schema.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(json.loads(scope_data))
    scope = json.loads(scope_data)
    original_manifest = json.loads(g.check_ref(root, plan.custody_manifest).read_bytes())
    known = {f['path']: g.Ref.model_validate(f) for f in original_manifest['files']}
    custody = root / 'evidence/custody'
    for file in custody.rglob('*'):
        if not file.is_file():
            continue
        name = file.relative_to(custody).as_posix()
        if name == 'FINAL_MANIFEST.schema.json':
            if g.sha(file) != '277b8984be920f80b913ccafa1f95a13b2e0fe410b4817180b07df3491851bcb':
                raise ValueError('Custody schema differs')
        elif name != 'FINAL_MANIFEST.json':
            if name not in known:
                raise ValueError('Unbound custody subset member')
            g.check_ref(custody, known[name])
    for target, source in zip(plan.targets, scope['sources']):
        if (source['source_id'] != target.source_id or source['authority_id'] != target.authority_id
                or source['requested_url'] != target.url
                or source['original']['sha256'] != target.baseline.sha256
                or source['original']['size_bytes'] != target.baseline.size_bytes
                or len(source['pages']) != target.baseline_page_count
                or datetime.fromisoformat(source['request_started_at'].replace('Z', '+00:00'))
                != target.baseline_request_started_at
                or datetime.fromisoformat(source['response_finished_at'].replace('Z', '+00:00'))
                != target.baseline_response_finished_at):
            raise ValueError('Custody source/date binding mismatch')
        g.observed_url(target, root)
        original = g.check_ref(root, target.baseline).read_bytes()
        if pdf_pages(original) != 7:
            raise ValueError('Baseline PDF structure differs')
        result = g.Result.model_validate_json(g.ordinary(
            custody / source['result']['path']).read_bytes())
        reservation_path = custody / source['reservation']['path']
        reservation = g.Reservation.model_validate_json(g.ordinary(reservation_path).read_bytes())
        if (result.reservation_sha256 != g.sha(reservation_path)
                or result.body.sha256 != target.baseline.sha256 or result.http_status != 200
                or result.partial_body or result.outcome != 'complete'
                or result.finished_at != target.baseline_response_finished_at
                or reservation.reserved_at != target.baseline_request_started_at
                or reservation.url != target.url):
            raise ValueError('Original HTTP receipt binding mismatch')
    return plan


def pdf_pages(body: bytes) -> int:
    """Require a complete unrepaired, unencrypted finite PDF before comparing byte versions."""
    if not body.startswith(b'%PDF-') or not body.rstrip().endswith(b'%%EOF'):
        raise ValueError('Invalid PDF signature/end marker')
    try:
        with pymupdf.open(stream=body, filetype='pdf') as pdf:
            if pdf.is_repaired or pdf.is_encrypted or not 1 <= len(pdf) <= 100:
                raise ValueError('Invalid PDF structure or page limit')
            for page in pdf:
                if page.rect.is_empty or page.rect.is_infinite:
                    raise ValueError('Invalid PDF page geometry')
            return len(pdf)
    except RuntimeError as error:
        raise ValueError('Unparseable PDF') from error


class WatchGuard(g.Guard):
    """Reuse audited serial HTTP custody with a separate fixed two-source watch plan."""
    def __init__(self, plan_path: Path, output: Path,
                 clock: Callable[[], datetime] = g.utcnow,
                 fetch: Callable[..., Any] | None = None) -> None:
        self.plan_path = plan_path
        self.plan = load_plan(plan_path)
        self.plan_sha = g.sha(plan_path)
        self.output = output
        self.clock = clock
        self.fetch = g.transport if fetch is None else fetch
        self.mode = 'live_http' if fetch is None else 'offline_fixture'
        self.clock_basis = 'actual_utc_clock' if clock is g.utcnow else 'injected_fixture_clock'
        self._lock_owner = None

    def reserve(self, source: str, url: str, hop: int, run: g.Run) -> g.Reservation:
        """Disallow redirect host changes before the inherited guard can make a request."""
        target = next((t for t in self.plan.targets if t.source_id == source), None)
        if target is None or urlsplit(url).hostname != urlsplit(target.url).hostname:
            raise ValueError('Redirect host change refused before request')
        return super().reserve(source, url, hop, run)

    def execute(self, dispatch_at: datetime) -> g.State:
        """Install a five-minute maximum run receipt, then reuse append-only collection."""
        with self.lock():
            now = self.clock()
            deadline = min(dispatch_at + timedelta(seconds=self.plan.max_run_seconds),
                           self.plan.proposed_finish_by, self.plan.hard_stop)
            if dispatch_at > now or now >= deadline:
                raise ValueError('Invalid or expired operator dispatch time')
            path = self.output / 'run.json'
            run = g.Run(plan_sha256=self.plan_sha, dispatch_at=dispatch_at,
                        initialized_at=now, deadline=deadline)
            if path.exists():
                prior = g.Run.model_validate_json(g.ordinary(path).read_bytes())
                if (prior.plan_sha256 != self.plan_sha or prior.dispatch_at != dispatch_at
                        or prior.deadline != deadline):
                    raise ValueError('Run/dispatch/deadline substitution refused')
            else:
                g.save_model(path, run)
        return super().execute(dispatch_at)


def observation(target: Target, pairs: list[Any], root: Path) -> Observation:
    """Keep availability, byte equality, source context and legal status separate."""
    history = [(r, s) for r, s in pairs if r.source_id == target.source_id]
    common = dict(source_id=target.source_id, canonical_source_id=target.canonical_source_id,
                  authority_id=target.authority_id, requested_url=target.url,
                  baseline=target.baseline, baseline_request_started_at=target.baseline_request_started_at,
                  baseline_response_finished_at=target.baseline_response_finished_at,
                  source_context=target.source_context, events=[r.event for r, _ in history])
    if not history:
        return Observation(**common, status='not_checked', reason='No request reserved for this source',
            request_started_at=None, response_finished_at=None, response_url=None, http_status=None,
            response_body=None, response_public_headers=None, valid_pdf_pages=None,
            bytes_equal_to_baseline=None, review_needed=True)
    res, result = history[-1]
    if result is None:
        raise ValueError('Unclosed reservation requires recovery before reporting')
    status, reason = 'transport_error', result.outcome
    equal, pages = None, None
    if result.http_status in {401, 403, 407}:
        status, reason = 'access_denied', 'Publisher denied access; no retry or workaround'
    elif result.http_status in {404, 410}:
        status, reason = 'not_found', 'Publisher returned missing/gone; no repeal inference'
    elif result.outcome in {'redirect', 'refused_redirect', 'byte_limit', 'hard_stop'}:
        status, reason = 'refused', result.outcome + ': limit or routing requires review'
    elif result.outcome in {'timeout', 'transport_error', 'interrupted'}:
        status, reason = 'transport_error', result.outcome
    elif result.outcome == 'incomplete_body' or result.partial_body:
        status, reason = 'invalid_response', 'Incomplete body; no byte-version comparison'
    elif result.http_status == 200 and result.outcome == 'complete':
        head = g.HeaderRecord.model_validate_json(g.check_ref(root, result.public_headers).read_bytes())
        if head.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'application/pdf':
            status, reason = 'invalid_response', 'Content type changed or is absent; expected PDF'
        else:
            try:
                pages = pdf_pages(g.check_ref(root, result.body).read_bytes())
            except ValueError:
                status, reason = 'invalid_response', 'Body is not a complete permitted PDF'
            else:
                equal = result.body.sha256 == target.baseline.sha256
                status = 'unchanged' if equal else 'changed'
                reason = ('Exact bytes equal the pinned prior original' if equal else
                          'Different valid PDF bytes; source review required, no legal-change inference')
    elif result.http_status is not None:
        reason = 'Unexpected HTTP status; source could not be compared'
    return Observation(**common, status=status, reason=reason,
        request_started_at=history[0][0].reserved_at, response_finished_at=result.finished_at,
        response_url=res.url, http_status=result.http_status, response_body=result.body,
        response_public_headers=result.public_headers, valid_pdf_pages=pages,
        bytes_equal_to_baseline=equal, review_needed=status != 'unchanged')


def check_output(root: Path, output: Path) -> None:
    """Limit every invocation to a named run under this handoff package."""
    if (output.parent != root / 'runs' or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',
                                                        output.name)):
        raise ValueError('Output must be this package/runs/<simple-run-name>')
    if output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise ValueError('Symlinked output ancestor')


def seal(root: Path, kind: Literal['prototype', 'run']) -> FileInventory:
    """Write one closed inventory without replacing prior evidence."""
    name = 'PACKAGE_MANIFEST.json' if kind == 'prototype' else 'RUN_MANIFEST.json'
    files = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in package')
        relative = path.relative_to(root)
        if path.is_file() and relative.as_posix() != name:
            if kind == 'prototype' and relative.parts[0] == 'runs':
                continue
            files.append(g.file_ref(root, path))
    result = FileInventory(kind=kind, files=files)
    g.save_model(root / name, result)
    return result


def verify_inventory(root: Path, kind: Literal['prototype', 'run']) -> FileInventory:
    """Reject unlisted/missing files and all symlinks before or after reading results."""
    name = 'PACKAGE_MANIFEST.json' if kind == 'prototype' else 'RUN_MANIFEST.json'
    record = FileInventory.model_validate_json(g.ordinary(root / name).read_bytes())
    if record.kind != kind:
        raise ValueError('Wrong inventory kind')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in closed package')
        relative = path.relative_to(root)
        if path.is_file() and relative.as_posix() != name:
            if kind == 'prototype' and relative.parts[0] == 'runs':
                continue
            actual.add(relative.as_posix())
    if actual != {item.path for item in record.files}:
        raise ValueError('Closed inventory differs')
    for item in record.files:
        g.check_ref(root, item)
    return record


def compile_report(guard: WatchGuard, dispatch_at: datetime, stop: str | None) -> Report:
    """Bind every result to an immutable original and its actual/fixture event times."""
    pairs = guard.ledger()
    observations = [observation(t, pairs, guard.output) for t in guard.plan.targets]
    done = all(o.status in {'unchanged', 'changed'} for o in observations)
    return Report(status='completed' if done and stop is None else 'stopped', mode=guard.mode,
        clock_basis=guard.clock_basis, generated_at=guard.clock(), plan_sha256=guard.plan_sha,
        invocation=g.file_ref(guard.output, guard.output / 'INVOCATION.json'),
        implementation_sha256=g.sha(HERE / 'watch.py'), transport_sha256=GUARD_SHA,
        authorization_basis='operator_supplied_time_and_plan_digest_not_independent_proof',
        dispatch_at=dispatch_at, stop_reason=stop, state=guard.state(pairs), observations=observations)


def run_watch(plan_path: Path, output: Path, dispatch_at: datetime, reviewed_plan_sha256: str,
              clock: Callable[[], datetime] = g.utcnow,
              fetch: Callable[..., Any] | None = None) -> Report:
    """Run one approved invocation, never install a scheduler or update baseline/canonical data."""
    root = plan_path.parent
    check_output(root, output)
    if reviewed_plan_sha256 != g.sha(plan_path):
        raise ValueError('Supplied reviewed plan digest differs')
    guard = WatchGuard(plan_path, output, clock=clock, fetch=fetch)
    if (output / 'report.json').exists():
        prior_report = verify_run(plan_path, output)
        if prior_report.dispatch_at != dispatch_at:
            raise ValueError('Existing run dispatch differs')
        return prior_report
    now = clock()
    if dispatch_at.tzinfo is None:
        raise ValueError('Dispatch must be timezone aware')
    deadline = min(dispatch_at + timedelta(seconds=guard.plan.max_run_seconds),
                   guard.plan.proposed_finish_by, guard.plan.hard_stop)
    if dispatch_at > now or now >= deadline:
        raise ValueError('Invalid or expired operator dispatch time')
    invocation = Invocation(recorded_at=now, dispatch_at=dispatch_at,
        plan_sha256=guard.plan_sha, implementation_sha256=g.sha(HERE / 'watch.py'),
        transport_sha256=GUARD_SHA, mode=guard.mode, clock_basis=guard.clock_basis,
        authorization_basis='operator_supplied_time_and_plan_digest_not_independent_proof')
    with guard.lock():
        invocation_path = output / 'INVOCATION.json'
        if invocation_path.exists():
            old = Invocation.model_validate_json(g.ordinary(invocation_path).read_bytes())
            if old.model_dump(exclude={'recorded_at'}) != invocation.model_dump(
                    exclude={'recorded_at'}):
                raise ValueError('Invocation metadata substitution refused')
        else:
            g.save_model(invocation_path, invocation)
    stop = None
    try:
        guard.execute(dispatch_at)
    except (ValueError, BlockingIOError, KeyboardInterrupt) as error:
        stop = type(error).__name__
        # Interrupted reservations remain exact; inherited recovery never retries their source.
        if isinstance(error, KeyboardInterrupt):
            with guard.lock():
                for res, result in guard.ledger():
                    if result is None:
                        guard.finish(res, 'interrupted', error='operator_interrupted')
    with guard.lock():
        report = compile_report(guard, dispatch_at, stop)
        g.save_model(output / 'report.json', report)
        seal(output, 'run')
    return report


def verify_run(plan_path: Path, output: Path) -> Report:
    """Replay a completed report without invoking transport or treating failed sources as unchanged."""
    check_output(plan_path.parent, output)
    before = verify_inventory(output, 'run')
    report = Report.model_validate_json(g.ordinary(output / 'report.json').read_bytes())
    guard = WatchGuard(plan_path, output)
    if (report.plan_sha256 != guard.plan_sha or report.implementation_sha256 !=
            g.sha(HERE / 'watch.py') or report.transport_sha256 != GUARD_SHA):
        raise ValueError('Run implementation/plan binding mismatch')
    if report.invocation.path != 'INVOCATION.json':
        raise ValueError('Wrong invocation receipt path')
    invocation = Invocation.model_validate_json(g.check_ref(output, report.invocation).read_bytes())
    run = g.Run.model_validate_json(g.ordinary(output / 'run.json').read_bytes())
    deadline = min(report.dispatch_at + timedelta(seconds=guard.plan.max_run_seconds),
                   guard.plan.proposed_finish_by, guard.plan.hard_stop)
    if (invocation.plan_sha256 != report.plan_sha256 or
            invocation.implementation_sha256 != report.implementation_sha256 or
            invocation.mode != report.mode or invocation.clock_basis != report.clock_basis or
            invocation.dispatch_at != report.dispatch_at or
            run.plan_sha256 != report.plan_sha256 or run.dispatch_at != report.dispatch_at or
            run.deadline != deadline or invocation.recorded_at < report.dispatch_at or
            run.initialized_at < invocation.recorded_at or report.generated_at < run.initialized_at):
        raise ValueError('Invocation/run/report binding mismatch')
    pairs = guard.ledger()
    for reservation, result in pairs:
        if (result is None or reservation.reserved_at < run.initialized_at or
                reservation.reserved_at >= run.deadline or reservation.deadline > run.deadline or
                result.finished_at < reservation.reserved_at or
                report.generated_at < result.finished_at):
            raise ValueError('Event time or completion binding mismatch')
        header = g.HeaderRecord.model_validate_json(g.check_ref(
            output, result.public_headers).read_bytes())
        if header.request_url is not None and header.request_url != reservation.url:
            raise ValueError('Event public-header URL mismatch')
    expected = [observation(t, pairs, output) for t in guard.plan.targets]
    if expected != report.observations or guard.state(pairs) != report.state:
        raise ValueError('Report/evidence classification mismatch')
    done = all(o.status in {'unchanged', 'changed'} for o in expected)
    if report.status != ('completed' if done and report.stop_reason is None else 'stopped'):
        raise ValueError('Report completeness differs')
    if verify_inventory(output, 'run') != before:
        raise ValueError('Run changed during validation')
    return report


def main() -> int:
    """Validate offline by default; live execution requires an explicit reviewed digest/time."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--verify-run')
    parser.add_argument('--run-name')
    parser.add_argument('--dispatch-at')
    parser.add_argument('--reviewed-plan-sha256')
    args = parser.parse_args()
    try:
        verify_inventory(HERE, 'prototype')
        plan_path = HERE / 'WATCH_PLAN.json'
        plan = load_plan(plan_path)
        if args.execute and args.verify_run:
            raise ValueError('Choose either execution or offline verification')
        if args.verify_run:
            result = verify_run(plan_path, HERE / 'runs' / args.verify_run)
        elif args.execute:
            if not all([args.run_name, args.dispatch_at, args.reviewed_plan_sha256]):
                raise ValueError('Execution needs run name, reviewed plan digest and actual dispatch UTC')
            dispatch = datetime.fromisoformat(args.dispatch_at.replace('Z', '+00:00'))
            if dispatch.tzinfo is None:
                raise ValueError('Dispatch must be timezone aware')
            result = run_watch(plan_path, HERE / 'runs' / args.run_name, dispatch,
                               args.reviewed_plan_sha256)
        else:
            sys.stdout.write(json.dumps({'status': plan.status, 'targets': len(plan.targets),
                             'public_requests_made': 0, 'plan_sha256': g.sha(plan_path)}) + '\n')
            return 0
        sys.stdout.write(result.model_dump_json(indent=2) + '\n')
        return 0 if result.status == 'completed' else 2
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
