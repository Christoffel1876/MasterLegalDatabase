"""Two-source manual PDF byte watch with canonical custody and read-only readiness."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Literal
from urllib.parse import unquote

import jsonschema
import pymupdf
from bs4 import BeautifulSoup
from pydantic import AwareDatetime, Field, model_validator

from geode.pipeline import manual_watch_http as g
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord

SELECTION = Path('config/manual_source_watch.json')
MANUAL_MANIFEST = Path('_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl')
RUNTIME = Path('.geode_runtime/manual_source_watch')
SCOPE_SHA = 'd5ad6056f8b7d820dfd01d09366744dc368fe6c604811eddfb0f225616f94ef5'
ACCEPTANCE_SHA = '503b98fb62561d3cee436f938c0555554a458547ef546f94576cf0abcafe5f12'
INTAKE_RECEIPT_SHA = '59efef8ab0b90059004f85054acca3b82bcf613c34eaaba20b37d5a521b8d5ff'

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

class Target(g.Target):
    """One canonical original, its actual intake record, and earlier official HTTP custody."""
    canonical_source_id: str
    authority_id: Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    baseline: g.Ref
    baseline_page_count: Literal[7]
    baseline_request_started_at: AwareDatetime
    baseline_response_finished_at: AwareDatetime
    repository_received_at: AwareDatetime
    intake_id: str
    raw_manifest_line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_context: list[str] = Field(min_length=1)
    legal_currentness: Literal['not_verified'] = 'not_verified'


class PriorLive(g.Strict):
    """Data-only pointers to an accepted finite check, not recurring-operation evidence."""
    report: g.Ref
    report_schema: g.Ref
    run_manifest: g.Ref
    authorization: g.Ref


class Plan(g.Plan):
    """Fixed two-source selection; invocation limits do not install or imply scheduling."""
    status: Literal['configured_not_scheduled']
    targets: list[Target] = Field(min_length=2, max_length=2)
    custody_scope: g.Ref
    custody_schema: g.Ref
    intake_acceptance: g.Ref
    intake_receipt: g.Ref
    prior_live: PriorLive
    automatic_baseline_updates: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    qualifications: list[str]

    @model_validator(mode='after')
    def fixed_sources(self) -> Plan:
        """Refuse replacement identities, source bytes, jurisdiction or custody anchors."""
        if [t.source_id for t in self.targets] != ['SD014-01', 'SD014-02']:
            raise ValueError('Exactly the two ordered reviewed sources are required')
        for target in self.targets:
            if (target.canonical_source_id, target.url, target.baseline.sha256,
                    target.baseline.size_bytes) != IDENTITIES[target.source_id]:
                raise ValueError('Source URL/ID/baseline substitution refused')
            prefix = ('_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/'
                      + target.canonical_source_id + '/')
            if not target.baseline.path.startswith(prefix):
                raise ValueError('Unexpected canonical original path')
        if (self.custody_scope.sha256 != SCOPE_SHA or
                self.intake_acceptance.sha256 != ACCEPTANCE_SHA or
                self.intake_receipt.sha256 != INTAKE_RECEIPT_SHA):
            raise ValueError('Wrong accepted source custody')
        if self.custody_schema.sha256 != (
                '131d3c397e3a3f6e3c12c1559e2cdbe383a5a0a22519dd1021893368d49f19e2'):
            raise ValueError('Wrong original source schema')
        expected_prior = {
            'report': 'f2ede7e3b8f6673e0d6709e137444ffdb3220d9f23bebe81fb5caf91327e9e63',
            'report_schema': '7853239374b3655fe9f81b9970628015cc4ac961bcf727a15f7eccb4009a0a0e',
            'run_manifest': 'e96b713dcce69a9e0229141f6cd950d68268437b4619570e2342565839567bc3',
            'authorization': 'ab7db4324c60e9cad82300ed3ee47f24c4bee955cc2c711d060903b642ed4246',
        }
        if any(getattr(self.prior_live, key).sha256 != value
               for key, value in expected_prior.items()):
            raise ValueError('Wrong accepted prior live-check evidence')
        return self


class Availability(g.Strict):
    """One recorded original's actual local hash check, not transcription review."""
    record_id: str
    status: Literal['hash_verified', 'unavailable_or_mismatch']
    reason: str | None


class Readiness(g.Strict):
    """Separate preservation, explicit selection, finite checks and recurring deployment."""
    generated_at: AwareDatetime
    selection: g.Ref
    manual_manifest: g.Ref
    manual_pdf_records: int
    locally_hash_verified_pdf_originals: int
    unavailable_or_mismatch: list[Availability]
    configured_sources: int
    configured_source_ids: list[str]
    unselected_manual_pdf_records: int
    accepted_prior_finite_live_source_checks: int
    prior_live_checked_at: AwareDatetime
    recurring_deployment: Literal['not_deployed_by_this_feature']
    existing_collectors: Literal['Register, CCR and county collectors unchanged by this feature']
    fixed_urls_find_new_editions_elsewhere: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Observation(g.Strict):
    """Transport/byte observations only; an absent response is never an unchanged source."""
    source_id: str
    canonical_source_id: str
    authority_id: Literal['CO-MUNICIPAL-COLORADO_SPRINGS']
    requested_url: str
    baseline: g.Ref
    baseline_request_started_at: AwareDatetime
    baseline_response_finished_at: AwareDatetime
    repository_received_at: AwareDatetime
    intake_id: str
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
    transport_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    mode: Literal['live_http', 'offline_fixture']
    clock_basis: Literal['actual_utc_clock', 'injected_fixture_clock']
    authorization_basis: Literal['operator_supplied_time_and_plan_digest_not_independent_proof']
    selection_snapshot: g.Ref
    manual_manifest_snapshot: g.Ref


class Report(g.Strict):
    """Immutable per-invocation result with time/clock origin and incomplete scope explicit."""
    status: Literal['completed', 'stopped']
    mode: Literal['live_http', 'offline_fixture']
    clock_basis: Literal['actual_utc_clock', 'injected_fixture_clock']
    generated_at: AwareDatetime
    plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    implementation_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    invocation: g.Ref
    transport_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
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
    kind: Literal['run']
    files: list[g.Ref]

    @model_validator(mode='after')
    def unique_paths(self) -> FileInventory:
        """Reject ambiguous inventories."""
        if len({f.path for f in self.files}) != len(self.files):
            raise ValueError('Duplicate inventory member')
        return self


def implementation_identity() -> str:
    """Bind the maintained adapter actually loaded from this repository installation."""
    return g.sha(Path(__file__))


def transport_identity() -> str:
    """Bind the maintained transport, with no executable research-package dependency."""
    return g.sha(Path(g.__file__))


def repository_root(path: Path) -> Path:
    """Infer only the standard reviewed config location, rejecting symlinked inputs."""
    path = path.absolute()
    g.ordinary(path)
    if path.name != SELECTION.name or path.parent.name != 'config' or '..' in path.parts:
        raise ValueError('Selection must be <repository>/config/manual_source_watch.json')
    return path.parent.parent


def checked_bytes(root: Path, ref: g.Ref) -> bytes:
    """Bind bytes used for parsing, not just an earlier path stat/hash."""
    data = g.check_ref(root, ref).read_bytes()
    if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError('Input changed while reading')
    return data


def local_schema(schema: Any) -> None:
    """Never follow external schema references from data packages."""
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key in {'$ref', '$dynamicRef', '$recursiveRef'} and (
                    not isinstance(value, str) or not value.startswith('#')):
                raise ValueError('External JSON schema reference refused')
            local_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            local_schema(value)


def schema_check(data: bytes, schema: bytes) -> Any:
    """Validate only supplied local declarative schemas; never import review scripts."""
    definition = json.loads(schema)
    local_schema(definition)
    value = json.loads(data)
    jsonschema.Draft202012Validator(definition).validate(value)
    return value


def manual_records(root: Path) -> tuple[dict[str, ManualSourceIntakeRecord], dict[str, str], g.Ref]:
    """Stream and validate every raw-manifest row, keeping exact selected-line identities."""
    path = root / MANUAL_MANIFEST
    before = g.file_ref(root, path)
    records, hashes = {}, {}
    with g.ordinary(path).open('rb') as handle:
        for raw in handle:
            if not raw.strip():
                raise ValueError('Blank raw-manifest record')
            record = ManualSourceIntakeRecord.model_validate_json(raw, strict=True)
            if record.record_id in records or record.received_at.tzinfo is None:
                raise ValueError('Duplicate source identity or unqualified intake time')
            records[record.record_id] = record
            hashes[record.record_id] = hashlib.sha256(raw).hexdigest()
    if not records or g.file_ref(root, path) != before:
        raise ValueError('Missing or changing raw-manifest baseline')
    return records, hashes, before


def prior_live_check(root: Path, plan: Plan) -> tuple[int, datetime]:
    """Verify the accepted historical run's data-only source/body/authorization bindings."""
    evidence = plan.prior_live
    report = schema_check(checked_bytes(root, evidence.report),
                          checked_bytes(root, evidence.report_schema))
    inventory = FileInventory.model_validate_json(checked_bytes(root, evidence.run_manifest))
    run_root = (root / evidence.report.path).parent
    expected = {p.relative_to(run_root).as_posix() for p in run_root.rglob('*')
                if p.is_file() and p.name != 'RUN_MANIFEST.json'}
    if inventory.kind != 'run' or expected != {f.path for f in inventory.files}:
        raise ValueError('Historical live run inventory mismatch')
    for ref in inventory.files:
        checked_bytes(run_root, ref)
    auth = json.loads(checked_bytes(root, evidence.authorization))
    if (report['status'] != 'completed' or report['mode'] != 'live_http'
            or report['clock_basis'] != 'actual_utc_clock'
            or report['legal_currentness'] != 'not_verified'
            or auth['dispatch_at'] != report['dispatch_at']
            or auth['pins']['WATCH_PLAN.json'] != report['plan_sha256']
            or auth['pins']['watch.py'] != report['implementation_sha256']
            or auth['pins']['sd014_guard.py'] != report['transport_sha256']
            or auth['run_name'] != run_root.name or len(report['observations']) != 2):
        raise ValueError('Historical live-check provenance differs')
    for target, observation in zip(plan.targets, report['observations']):
        if (observation['source_id'] != target.source_id or
                observation['canonical_source_id'] != target.canonical_source_id or
                observation['authority_id'] != target.authority_id or
                observation['status'] != 'unchanged' or observation['http_status'] != 200 or
                not observation['bytes_equal_to_baseline'] or
                observation['response_body']['sha256'] != target.baseline.sha256 or
                observation['requested_url'] != target.url):
            raise ValueError('Historical live source identity differs')
        checked_bytes(run_root, g.Ref.model_validate(observation['response_body']))
    return 2, datetime.fromisoformat(report['generated_at'].replace('Z', '+00:00'))


def load_plan(path: Path) -> Plan:
    """Bind selection to canonical originals, actual intake and immutable original HTTP evidence."""
    root = repository_root(path)
    plan = Plan.model_validate_json(g.ordinary(path).read_bytes())
    records, hashes, _ = manual_records(root)
    scope = schema_check(checked_bytes(root, plan.custody_scope),
                         checked_bytes(root, plan.custody_schema))
    acceptance = json.loads(checked_bytes(root, plan.intake_acceptance))
    receipt = json.loads(checked_bytes(root, plan.intake_receipt))
    acceptance_root = (root / plan.intake_acceptance.path).parent
    if (acceptance['status'] != 'accepted_custody_only' or acceptance['legal_currentness'] !=
            'not_verified' or acceptance['answer_safe'] is not False or
            acceptance['receipt']['sha256'] != plan.intake_receipt.sha256 or
            acceptance_root / acceptance['receipt']['path'] != root / plan.intake_receipt.path or
            receipt['status'] != 'completed_archived_pending_pipeline'):
        raise ValueError('Accepted intake receipt mismatch')
    receipt_records = {r['record_id']: ManualSourceIntakeRecord.model_validate(r)
                       for r in receipt['intent']['records']}
    scope_root = (root / plan.custody_scope.path).parent
    for target, source in zip(plan.targets, scope['sources']):
        row = records.get(target.canonical_source_id)
        if (row is None or hashes[target.canonical_source_id] != target.raw_manifest_line_sha256
                or row != receipt_records.get(target.canonical_source_id)
                or row.intake_id != target.intake_id or row.archive_path != target.baseline.path
                or row.sha256 != target.baseline.sha256
                or row.size_bytes != target.baseline.size_bytes
                or row.official_source_url != target.url
                or row.layer_id != '10_Municipal_Authorities'
                or row.source_format != 'pdf' or row.received_at != target.repository_received_at
                or datetime.fromisoformat(acceptance['actual_repository_received_at'].replace(
                    'Z', '+00:00')) != target.repository_received_at):
            raise ValueError('Canonical source/intake binding mismatch')
        if (source['source_id'] != target.source_id
                or source['authority_id'] != target.authority_id
                or source['requested_url'] != target.url
                or source['original']['sha256'] != row.sha256
                or source['original']['size_bytes'] != row.size_bytes or
                datetime.fromisoformat(source['request_started_at'].replace('Z', '+00:00')) !=
                target.baseline_request_started_at or
                datetime.fromisoformat(source['response_finished_at'].replace('Z', '+00:00')) !=
                target.baseline_response_finished_at):
            raise ValueError('Original HTTP/source binding mismatch')
        if pdf_pages(checked_bytes(root, target.baseline)) != target.baseline_page_count:
            raise ValueError('Canonical PDF structure differs')
        original_result = json.loads(checked_bytes(
            scope_root, g.Ref.model_validate(source['result'])))
        original_reservation = json.loads(checked_bytes(
            scope_root, g.Ref.model_validate(source['reservation'])))
        if (original_result['body']['sha256'] != row.sha256 or original_result['http_status'] != 200
                or original_result['partial_body'] or original_result['outcome'] != 'complete'
                or original_result['finished_at'] != source['response_finished_at']
                or original_reservation['reserved_at'] != source['request_started_at']
                or original_reservation['url'] != target.url or
                original_result['reservation_sha256'] != source['reservation']['sha256']):
            raise ValueError('Original HTTP receipt mismatch')
        html = checked_bytes(scope_root, g.Ref.model_validate(source['parent_html']))
        soup = BeautifulSoup(html, 'html.parser')
        frames = soup.select('div.field--name-field-media-document iframe.pdf')
        if len(frames) != 1 or frames[0].get('data-src') != target.url:
            raise ValueError('Official parent iframe differs')
        prefix = '/libraries/pdf.js/web/viewer.html?file='
        viewer = frames[0].get('src', '')
        if not viewer.startswith(prefix) or unquote(viewer[len(prefix):]) != target.url:
            raise ValueError('Official viewer reference differs')
    prior_live_check(root, plan)
    return plan


def readiness(root: Path, selection_path: Path | None = None) -> Readiness:
    """Count preserved and hash-available originals dynamically, without source requests."""
    path = selection_path or root / SELECTION
    plan = load_plan(path)
    records, _, manifest = manual_records(root)
    unavailable = []
    pdfs = [row for row in records.values() if row.source_format == 'pdf']
    for row in pdfs:
        try:
            artifact = g.Ref(path=row.archive_path, sha256=row.sha256, size_bytes=row.size_bytes)
            if not row.archive_path.startswith('_RAW_ARCHIVE/manual_intake/'):
                raise ValueError('Wrong manual archive root')
            g.check_ref(root, artifact)
        except (ValueError, OSError) as error:
            unavailable.append(Availability(record_id=row.record_id,
                status='unavailable_or_mismatch', reason=type(error).__name__))
    count, checked_at = prior_live_check(root, plan)
    if g.file_ref(root, root / MANUAL_MANIFEST) != manifest:
        raise ValueError('Raw manifest changed during readiness scan')
    return Readiness(generated_at=g.utcnow(), selection=g.file_ref(root, path),
        manual_manifest=manifest, manual_pdf_records=len(pdfs),
        locally_hash_verified_pdf_originals=len(pdfs) - len(unavailable),
        unavailable_or_mismatch=unavailable, configured_sources=len(plan.targets),
        configured_source_ids=[t.canonical_source_id for t in plan.targets],
        unselected_manual_pdf_records=len(pdfs) - len(plan.targets),
        accepted_prior_finite_live_source_checks=count, prior_live_checked_at=checked_at,
        recurring_deployment='not_deployed_by_this_feature',
        existing_collectors='Register, CCR and county collectors unchanged by this feature')


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


def observation(target: Target, pairs: list[Any], root: Path) -> Observation:
    """Keep availability, byte equality, source context and legal status separate."""
    history = [(r, s) for r, s in pairs if r.source_id == target.source_id]
    common = dict(source_id=target.source_id, canonical_source_id=target.canonical_source_id,
                  authority_id=target.authority_id, requested_url=target.url,
                  baseline=target.baseline,
                  baseline_request_started_at=target.baseline_request_started_at,
                  baseline_response_finished_at=target.baseline_response_finished_at,
                  repository_received_at=target.repository_received_at,
                  intake_id=target.intake_id, source_context=target.source_context,
                  events=[r.event for r, _ in history])
    if not history:
        return Observation(**common, status='not_checked',
            reason='No request reserved for this source',
            request_started_at=None, response_finished_at=None, response_url=None, http_status=None,
            response_body=None, response_public_headers=None, valid_pdf_pages=None,
            bytes_equal_to_baseline=None, review_needed=True)
    res, result = history[-1]
    if result is None:
        raise ValueError('Unclosed reservation requires recovery before reporting')
    status, reason = 'transport_error', result.outcome
    equal, pages = None, None
    if result.outcome == 'complete' and result.finished_at >= res.deadline:
        status, reason = 'transport_error', 'Response completed after its declared deadline'
    elif result.http_status in {401, 403, 407}:
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
        head = g.HeaderRecord.model_validate_json(
            g.check_ref(root, result.public_headers).read_bytes())
        content_type = head.headers.get('content-type', '').split(';', 1)[0].strip().lower()
        if content_type != 'application/pdf':
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
                          'Different valid PDF bytes; source review required, '
                          'no legal-change inference')
    elif result.http_status is not None:
        reason = 'Unexpected HTTP status; source could not be compared'
    return Observation(**common, status=status, reason=reason,
        request_started_at=history[0][0].reserved_at, response_finished_at=result.finished_at,
        response_url=res.url, http_status=result.http_status, response_body=result.body,
        response_public_headers=result.public_headers, valid_pdf_pages=pages,
        bytes_equal_to_baseline=equal, review_needed=status != 'unchanged')


class WatchGuard(g.Guard):
    """Add canonical-source preflight to the maintained bounded transport."""
    def __init__(self, plan_path: Path, output: Path,
                 clock: Callable[[], datetime] = g.utcnow,
                 fetch: Callable[..., Any] | None = None) -> None:
        """Read only fixed source evidence before a transport can be selected."""
        before = g.sha(plan_path)
        plan = load_plan(plan_path)
        super().__init__(plan_path, output, clock=clock,
                         fetch=g.transport if fetch is None else fetch, plan=plan)
        if self.plan_sha != before or g.sha(plan_path) != before:
            raise ValueError('Selection changed during canonical preflight')
        self.mode = 'live_http' if fetch is None else 'offline_fixture'
        self.clock_basis = 'actual_utc_clock' if clock is g.utcnow else 'injected_fixture_clock'


def check_output(root: Path, output: Path) -> None:
    """Confine immutable runs to the separate ignored watch runtime directory."""
    if (output.parent != root / RUNTIME or not re.fullmatch(
            r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', output.name)):
        raise ValueError(
            'Output must be <repository>/.geode_runtime/manual_source_watch/<run-name>')
    if output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise ValueError('Symlinked runtime ancestor')


def seal(root: Path, kind: Literal['run']) -> FileInventory:
    """Write one closed inventory without replacing prior evidence."""
    name = 'RUN_MANIFEST.json'
    files = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in package')
        relative = path.relative_to(root)
        if path.is_file() and relative.as_posix() != name:
            files.append(g.file_ref(root, path))
    result = FileInventory(kind=kind, files=files)
    g.save_model(root / name, result)
    return result


def verify_inventory(root: Path, kind: Literal['run']) -> FileInventory:
    """Reject unlisted/missing files and all symlinks before or after reading results."""
    name = 'RUN_MANIFEST.json'
    record = FileInventory.model_validate_json(g.ordinary(root / name).read_bytes())
    if record.kind != kind:
        raise ValueError('Wrong inventory kind')
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in closed package')
        relative = path.relative_to(root)
        if path.is_file() and relative.as_posix() != name:
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
        implementation_sha256=implementation_identity(), transport_sha256=transport_identity(),
        authorization_basis='operator_supplied_time_and_plan_digest_not_independent_proof',
        dispatch_at=dispatch_at, stop_reason=stop, state=guard.state(pairs),
        observations=observations)


def run_watch(plan_path: Path, output: Path, dispatch_at: datetime, reviewed_plan_sha256: str,
              clock: Callable[[], datetime] = g.utcnow,
              fetch: Callable[..., Any] | None = None) -> Report:
    """Run one invocation without a scheduler, baseline update or canonical write."""
    root = repository_root(plan_path)
    check_output(root, output)
    if reviewed_plan_sha256 != g.sha(plan_path):
        raise ValueError('Supplied reviewed plan digest differs')
    guard = WatchGuard(plan_path, output, clock=clock, fetch=fetch)
    if (output / 'report.json').exists():
        with guard.lock():
            sealed = (output / 'RUN_MANIFEST.json').exists()
            prior_report = _verify_report(plan_path, output, sealed)
            if prior_report.dispatch_at != dispatch_at:
                raise ValueError('Existing run dispatch differs')
            if not sealed:
                seal(output, 'run')
        if prior_report.dispatch_at != dispatch_at:
            raise ValueError('Existing run dispatch differs')
        return prior_report
    now = clock()
    if dispatch_at.tzinfo is None:
        raise ValueError('Dispatch must be timezone aware')
    deadline = dispatch_at + timedelta(seconds=guard.plan.max_run_seconds)
    resuming = (output / 'INVOCATION.json').exists()
    if dispatch_at > now or (now >= deadline and not resuming):
        raise ValueError('Invalid or expired operator dispatch time')
    with guard.lock():
        snapshots = {}
        for name, source in [('selection.json', plan_path),
                             ('manual_manifest.jsonl', root / MANUAL_MANIFEST)]:
            destination = output / 'inputs' / name
            if name.endswith('.jsonl') and destination.exists():
                # Appended unrelated canonical records do not rewrite a frozen run preimage.
                snapshots[name] = g.file_ref(output, destination)
                continue
            if name.endswith('.jsonl'):
                _, _, identity = manual_records(root)
                with g.ordinary(source).open('rb') as handle:
                    content = b''.join(handle)
                if hashlib.sha256(content).hexdigest() != identity.sha256:
                    raise ValueError('Manual manifest changed during runtime snapshot')
            else:
                content = g.ordinary(source).read_bytes()
                if (hashlib.sha256(content).hexdigest() != guard.plan_sha or
                        Plan.model_validate_json(content) != guard.plan):
                    raise ValueError('Selection snapshot differs from preflight')
            if destination.exists():
                if g.ordinary(destination).read_bytes() != content:
                    raise ValueError('Existing immutable runtime input snapshot differs')
            else:
                g.immutable(destination, content)
            snapshots[name] = g.file_ref(output, destination)
        invocation = Invocation(recorded_at=now, dispatch_at=dispatch_at,
            plan_sha256=guard.plan_sha, implementation_sha256=implementation_identity(),
            transport_sha256=transport_identity(), mode=guard.mode, clock_basis=guard.clock_basis,
            authorization_basis='operator_supplied_time_and_plan_digest_not_independent_proof',
            selection_snapshot=snapshots['selection.json'],
            manual_manifest_snapshot=snapshots['manual_manifest.jsonl'])
        invocation_path = output / 'INVOCATION.json'
        if invocation_path.exists():
            old = Invocation.model_validate_json(g.ordinary(invocation_path).read_bytes())
            if old.model_dump(exclude={'recorded_at'}) != invocation.model_dump(
                    exclude={'recorded_at'}):
                raise ValueError('Invocation metadata substitution refused')
        else:
            g.save_model(invocation_path, invocation)
        run_path = output / 'run.json'
        if not run_path.exists():
            g.save_model(run_path, g.Run(plan_sha256=guard.plan_sha, dispatch_at=dispatch_at,
                initialized_at=now, deadline=deadline))
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
        _verify_report(plan_path, output, False)
        seal(output, 'run')
    return report


def verify_run(plan_path: Path, output: Path) -> Report:
    """Replay a report without transport or treating failed sources as unchanged."""
    return _verify_report(plan_path, output, True)


def _verify_report(plan_path: Path, output: Path, sealed: bool) -> Report:
    """Validate all semantics before recovering an interrupted final inventory write."""
    check_output(repository_root(plan_path), output)
    before = verify_inventory(output, 'run') if sealed else None
    report = Report.model_validate_json(g.ordinary(output / 'report.json').read_bytes())
    guard = WatchGuard(plan_path, output)
    if (report.plan_sha256 != guard.plan_sha or report.implementation_sha256 !=
            implementation_identity() or report.transport_sha256 != transport_identity()):
        raise ValueError('Run implementation/plan binding mismatch')
    if report.invocation.path != 'INVOCATION.json':
        raise ValueError('Wrong invocation receipt path')
    invocation = Invocation.model_validate_json(g.check_ref(output, report.invocation).read_bytes())
    if (invocation.selection_snapshot.path != 'inputs/selection.json' or
            invocation.manual_manifest_snapshot.path != 'inputs/manual_manifest.jsonl' or
            invocation.selection_snapshot.sha256 != report.plan_sha256):
        raise ValueError('Runtime input snapshot path/identity mismatch')
    snapshot_plan = Plan.model_validate_json(checked_bytes(output, invocation.selection_snapshot))
    if snapshot_plan != guard.plan:
        raise ValueError('Runtime selection snapshot differs')
    snapshot_path = g.check_ref(output, invocation.manual_manifest_snapshot)
    selected_lines = {}
    with snapshot_path.open('rb') as handle:
        for line in handle:
            row = ManualSourceIntakeRecord.model_validate_json(line, strict=True)
            if row.record_id in selected_lines:
                raise ValueError('Duplicate source in runtime manifest snapshot')
            selected_lines[row.record_id] = hashlib.sha256(line).hexdigest()
    if any(selected_lines.get(t.canonical_source_id) != t.raw_manifest_line_sha256
           for t in guard.plan.targets):
        raise ValueError('Runtime canonical-record snapshot differs')
    run = g.Run.model_validate_json(g.ordinary(output / 'run.json').read_bytes())
    deadline = report.dispatch_at + timedelta(seconds=guard.plan.max_run_seconds)
    if (invocation.plan_sha256 != report.plan_sha256 or
            invocation.implementation_sha256 != report.implementation_sha256 or
            invocation.transport_sha256 != report.transport_sha256 or
            invocation.mode != report.mode or invocation.clock_basis != report.clock_basis or
            invocation.dispatch_at != report.dispatch_at or
            run.plan_sha256 != report.plan_sha256 or run.dispatch_at != report.dispatch_at or
            run.deadline != deadline or invocation.recorded_at < report.dispatch_at or
            run.initialized_at < invocation.recorded_at or
            report.generated_at < run.initialized_at):
        raise ValueError('Invocation/run/report binding mismatch')
    pairs = guard.ledger()
    allowed = {'.guard.lock', 'INVOCATION.json', 'run.json', 'report.json',
               'inputs/selection.json', 'inputs/manual_manifest.jsonl'}
    if sealed:
        allowed.add('RUN_MANIFEST.json')
    for reservation, result in pairs:
        if (result is None or reservation.reserved_at < run.initialized_at or
                reservation.reserved_at >= run.deadline or reservation.deadline > run.deadline or
                result.finished_at < reservation.reserved_at or
                report.generated_at < result.finished_at):
            raise ValueError('Event time or completion binding mismatch')
        prefix = f'events/{reservation.event:04d}/'
        if (result.body.path != prefix + 'body.bin' or
                result.public_headers.path != prefix + 'public-headers.json'):
            raise ValueError('Event evidence path mismatch')
        if result.outcome == 'complete' and result.finished_at >= reservation.deadline:
            raise ValueError('Complete response exceeds declared request deadline')
        allowed.update(prefix + name for name in [
            'reservation.json', 'result.json', 'body.bin', 'public-headers.json'])
        header = g.HeaderRecord.model_validate_json(g.check_ref(
            output, result.public_headers).read_bytes())
        if header.request_url is not None and header.request_url != reservation.url:
            raise ValueError('Event public-header URL mismatch')
    actual = set()
    for path in output.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in run evidence')
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
    if actual != allowed:
        raise ValueError('Unexpected or missing run evidence file')
    expected = [observation(t, pairs, output) for t in guard.plan.targets]
    if expected != report.observations or guard.state(pairs) != report.state:
        raise ValueError('Report/evidence classification mismatch')
    done = all(o.status in {'unchanged', 'changed'} for o in expected)
    if report.status != ('completed' if done and report.stop_reason is None else 'stopped'):
        raise ValueError('Report completeness differs')
    if sealed and verify_inventory(output, 'run') != before:
        raise ValueError('Run changed during validation')
    return report


def main(argv: list[str] | None = None) -> int:
    """Read readiness by default; execution is an explicit finite operator action."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--execute', action='store_true')
    group.add_argument('--verify-run')
    parser.add_argument('--run-name')
    parser.add_argument('--reviewed-selection-sha256')
    args = parser.parse_args(argv)
    try:
        root = args.root.absolute()
        plan_path = root / SELECTION
        repository_root(plan_path)
        if args.verify_run:
            result = verify_run(plan_path, root / RUNTIME / args.verify_run)
        elif args.execute:
            if not args.run_name or not args.reviewed_selection_sha256:
                raise ValueError('Execution requires run name and exact reviewed selection digest')
            output = root / RUNTIME / args.run_name
            check_output(root, output)
            invocation_path = output / 'INVOCATION.json'
            dispatch = (Invocation.model_validate_json(g.ordinary(invocation_path).read_bytes())
                        .dispatch_at if invocation_path.exists() else g.utcnow())
            result = run_watch(plan_path, output, dispatch, args.reviewed_selection_sha256)
        else:
            result = readiness(root)
            sys.stdout.write(result.model_dump_json(indent=2) + '\n')
            return 0
        sys.stdout.write(result.model_dump_json(indent=2) + '\n')
        return 0 if result.status == 'completed' else 2
    except (ValueError, OSError, jsonschema.ValidationError) as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

