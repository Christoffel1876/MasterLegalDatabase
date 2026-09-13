"""Record actual offline checks and close a new preparation revision; never execute HTTP."""
from __future__ import annotations
import difflib
import hashlib
import json
import shutil
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from preparation_models import Design, Manifest, Ref, SourceCheck, TestCheck, Validation
from load_proposed import load, ROOT

BASE = Path(__file__).resolve().parent


def ref(root: Path, path: Path) -> Ref:
    """Hash an ordinary file without loading source content into memory."""
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Unsafe input')
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return Ref(path=path.relative_to(root).as_posix(), sha256=digest,
               size_bytes=path.stat().st_size)


def write(path: Path, text: str) -> None:
    """Preserve any prior bytes before one atomic preparation-file replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = path.read_bytes()
        preimage = BASE / 'preimages/finalization' / hashlib.sha256(old).hexdigest() / path.name
        preimage.parent.mkdir(parents=True, exist_ok=True)
        if preimage.exists() and preimage.read_bytes() != old:
            raise ValueError('Preimage collision')
        if not preimage.exists():
            preimage.write_bytes(old)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(text)
    temporary.replace(path)


def refuse(*args: Any, **kwargs: Any) -> Any:
    """Reject every public transport path in this recording process."""
    raise AssertionError('No network during preparation verification')


socket.getaddrinfo = refuse
watch = load()
watch.g.transport = refuse
records, hashes, manual_ref = watch.manual_records(ROOT)
checks = []
for batch, relative in watch.SELECTIONS.items():
    plan = watch.load_plan(BASE / 'proposed' / relative, root=ROOT,
                           catalog_path=BASE / 'proposed' / watch.CATALOG)
    for target in plan.targets:
        checks.append(SourceCheck(batch_id=batch, source_id=target.source_id,
            authority_id=target.authority_id, baseline=Ref(**target.baseline.model_dump()),
            pages=target.baseline_page_count, exact_requested_url=target.url,
            baseline_request_started_at=target.baseline_request_started_at,
            baseline_recorded_http_time=target.baseline_recorded_http_time,
            baseline_http_time_role=target.baseline_http_time_role,
            repository_received_at=target.repository_received_at,
            raw_manifest_line_sha256=hashes[target.source_id]))

# Replay the existing maintained Springs run with all transport disabled.
from geode.pipeline import manual_source_watch as old
old.g.transport = refuse
old_run = ROOT / old.RUNTIME / 'atlas-maintained-20260913T004429Z'
before = [ref(ROOT, p) for p in sorted(old_run.rglob('*')) if p.is_file()]
report = old.verify_run(ROOT / old.SELECTION, old_run)
if before != [ref(ROOT, p) for p in sorted(old_run.rglob('*')) if p.is_file()]:
    raise ValueError('Existing Springs replay changed bytes')
if report.status != 'completed':
    raise ValueError('Existing Springs replay failed')

# Validate the final explicit design; superseded planning bytes remain under preimages.
design_data = json.loads((BASE / 'DESIGN.json').read_bytes())
design_data['notes'][-1] = (
    'Original Springs code/config/helper and saved-run bytes remain unchanged. '
    'The approved successor is an ordinary separately versioned module with explicit policy; '
    'the earlier private-helper option is superseded and retained only in the design preimage.')
design = Design.model_validate_json(json.dumps(design_data))
write(BASE / 'DESIGN.json', design.model_dump_json(indent=2) + '\n')
write(BASE / 'DESIGN.schema.json', json.dumps(Design.model_json_schema(), indent=2) + '\n')
for item in design.existing_code:
    if ref(ROOT, ROOT / item.path) != item:
        raise ValueError('Original Springs implementation changed')

coverage_source = Path('/private/tmp/geode-watch-batches-revision-coverage.json')
coverage = json.loads(coverage_source.read_bytes())
coverage_path = BASE / 'validation/coverage.json'
coverage_path.parent.mkdir(exist_ok=True)
shutil.copyfile(coverage_source, coverage_path)
log = (BASE / 'revision-tests.log').read_text()
if '205 passed' not in log or 'FAILED ' in log:
    raise ValueError('Focused test run did not pass')

write(BASE / 'proposed/config/manual_source_watch_sources_v1.schema.json',
      json.dumps(watch.Catalog.model_json_schema(), indent=2) + '\n')
proposed = sorted(p for p in (BASE / 'proposed').rglob('*') if p.is_file())
install = [p.relative_to(BASE / 'proposed').as_posix() for p in proposed]
# No existing target may be overwritten by this additive installation proposal.
if any((ROOT / p).exists() for p in install):
    raise ValueError('An installation target already exists')
patch = ''.join(''.join(difflib.unified_diff([], p.read_text().splitlines(True),
    fromfile='/dev/null', tofile='b/' + p.relative_to(BASE / 'proposed').as_posix()))
    for p in proposed)
write(BASE / 'INSTALL.patch', patch)
for earlier, later, name in [
    ('manual_watch_http.py', 'manual_watch_http_v2.py', 'TRANSPORT_CHANGES.diff'),
    ('manual_source_watch.py', 'manual_source_watch_batches.py', 'ADAPTER_CHANGES.diff'),
]:
    first = (ROOT / 'geode/pipeline' / earlier).read_text().splitlines(True)
    second = (BASE / 'proposed/geode/pipeline' / later).read_text().splitlines(True)
    write(BASE / name, ''.join(difflib.unified_diff(first, second, earlier, later)))

validation = Validation(checked_at=datetime.now(timezone.utc),
    status='PREPARED_NOT_INSTALLED_OR_EXECUTED',
    proposed_implementation=[ref(BASE, p) for p in proposed],
    current_manual_manifest=Ref(**manual_ref.model_dump()), current_manual_records=len(records),
    source_checks=checks,
    tests=TestCheck(command=['python', '-B', '-m', 'pytest', 'proposed/tests', '-q',
        '-p', 'no:cacheprovider', '--cov=proposed/geode/pipeline', '--cov-branch'], return_code=0,
        passed=205, branch_inclusive_coverage_percent=coverage['totals']['percent_covered'],
        log=ref(BASE, BASE / 'revision-tests.log'), coverage=ref(BASE, coverage_path),
        scope='Offline injected HTTP and local socket-pair tests; no public requests'),
    old_springs_inputs=design.existing_code, old_springs_run_files=before,
    old_springs_report_status='completed',
    old_springs_readonly_replay='passed_with_transport_disabled',
    old_springs_bytes_unchanged=True, limits=[
        'Prepared-only implementation; root must separately review and install or execute.',
        'Current catalog fixes six source identities, URLs, bytes and custody evidence.',
        'Arapahoe observed time is not called a witnessed response completion.',
        'Greeley later reacquisition does not rewrite earlier package-acquisition claims.',
        'No new source reading, transcription, adoption, legal-currentness or coverage review.',
        'The historical preparation input manifest may precede later unrelated raw intake.'])
write(BASE / 'VALIDATION.json', validation.model_dump_json(indent=2) + '\n')
write(BASE / 'VALIDATION.schema.json', json.dumps(Validation.model_json_schema(), indent=2) + '\n')
write(BASE / 'FINAL_MANIFEST.schema.json', json.dumps(Manifest.model_json_schema(), indent=2) + '\n')
manifest = Manifest(status='PREPARED_NOT_INSTALLED_OR_EXECUTED',
    files=[ref(BASE, p) for p in sorted(BASE.rglob('*'))
           if p.is_file() and p.relative_to(BASE).as_posix() != 'FINAL_MANIFEST.json'],
    installation_files=install)
# Closing is write-once: later revision must preserve the previous complete package separately.
if (BASE / 'FINAL_MANIFEST.json').exists():
    raise ValueError('Preparation already frozen')
write(BASE / 'FINAL_MANIFEST.json', manifest.model_dump_json(indent=2) + '\n')
sys.stdout.write(json.dumps(dict(files=len(manifest.files), installation_files=len(install),
    sources=len(checks), current_manual_records=len(records),
    coverage=validation.tests.branch_inclusive_coverage_percent,
    manifest=ref(BASE, BASE / 'FINAL_MANIFEST.json').model_dump()), indent=2) + '\n')
