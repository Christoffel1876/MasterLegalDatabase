"""Preserve the actual maintained watch run and its root offline checks."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import hashlib
import json
import shutil
import sys

from pydantic import BaseModel, ConfigDict, Field

BASE = Path('/Users/mcoors/Documents/Project Geode')
REPO = BASE / 'MasterLegalDatabase'
sys.path.insert(0, str(REPO))
from geode.pipeline import manual_source_watch as watch

NAME = 'atlas-maintained-20260913T004429Z'
SOURCE = REPO / watch.RUNTIME / NAME
DISPATCH = BASE / 'handoffs/run-2026-09-12/manual-watch-maintained-root-dispatch'
DEST = REPO / 'research/local_review/manual-source-watch-live-2026-09-13'
AUDIT = REPO / 'docs/audits/FOUR_HOUR_RUN_2026-09-12/MANUAL_SOURCE_WATCH'


class Ref(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Receipt(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    captured_at: str
    status: Literal['accepted_finite_maintained_live_check_not_recurring']
    source_runtime: str
    dispatch_at: str
    completed_at: str
    actual_request_count: Literal[2] = 2
    actual_retained_bytes: Literal[421075] = 421075
    source_outcomes: list[Literal['unchanged']]
    fixed_sources: list[str]
    preserved_files: list[Ref]
    root_checks: list[str]
    limitations: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Manifest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    files: list[Ref]


def ref(path: Path, root: Path) -> Ref:
    raw = path.read_bytes()
    return Ref(path=path.relative_to(root).as_posix(),
               sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def copy_file(source: Path, relative: str) -> None:
    target = DEST / relative
    assert source.is_file() and not source.is_symlink() and not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert source.read_bytes() == target.read_bytes()


if __name__ == '__main__':
    assert not DEST.exists()
    report = watch.verify_run(REPO / watch.SELECTION, SOURCE)
    assert report.status == 'completed' and report.mode == 'live_http'
    assert report.clock_basis == 'actual_utc_clock'
    assert report.state.request_count == 2 and report.state.charged_bytes == 421075
    assert [o.status for o in report.observations] == ['unchanged', 'unchanged']
    assert (DISPATCH / 'stdout.json').read_bytes() == (SOURCE / 'report.json').read_bytes()
    assert (DISPATCH / 'offline-verification.json').read_bytes() == (SOURCE / 'report.json').read_bytes()
    replay = json.loads((DISPATCH / 'EXPIRED_REPLAY.json').read_bytes())
    assert (replay['transport_calls'] == 0 and replay['all_run_bytes_unchanged']
            and replay['check_occurred_after_original_deadline']
            and replay['returned_original_report_bytes'] and replay['exit_code'] == 0)
    DEST.mkdir()
    for path in sorted(SOURCE.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            copy_file(path, 'run/' + path.relative_to(SOURCE).as_posix())
    for path in sorted(DISPATCH.iterdir()):
        if path.is_file():
            copy_file(path, 'dispatch/' + path.name)
    copy_file(Path('/private/tmp/geode_watch_expired_replay.py'), 'dispatch/replay-check.py')
    for name in ['geode/pipeline/manual_source_watch.py', 'geode/pipeline/manual_watch_http.py',
                 'config/manual_source_watch.json', 'config/manual_source_watch.schema.json']:
        copy_file(REPO / name, 'implementation/' + name)
    for index, observation in enumerate(report.observations, 1):
        copy_file(REPO / observation.baseline.path, f'baseline/{index:04d}.pdf')
    copy_file(BASE / 'handoffs/run-2026-09-12/springs-watch-final-suite/pytest.log',
              'checks/watch-full-suite.log')
    for name, model in [('report', watch.Report), ('run-manifest', watch.FileInventory),
                        ('invocation', watch.Invocation), ('reservation', watch.g.Reservation),
                        ('result', watch.g.Result), ('headers', watch.g.HeaderRecord)]:
        path = DEST / 'schemas' / f'{name}.schema.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + '\n')
    preserved = [ref(p, DEST) for p in sorted(DEST.rglob('*')) if p.is_file()]
    receipt = Receipt(captured_at=datetime.now(timezone.utc).isoformat(),
        status='accepted_finite_maintained_live_check_not_recurring', source_runtime=str(SOURCE),
        dispatch_at=report.dispatch_at.isoformat(), completed_at=report.generated_at.isoformat(),
        source_outcomes=[o.status for o in report.observations],
        fixed_sources=[o.canonical_source_id for o in report.observations], preserved_files=preserved,
        root_checks=[
            'Installed CLI executed exactly2publicGETs, bothHTTP200complete/unrepaired7pagePDFs.',
            'Installed offline verifier returned byte-identical report with no source requests.',
            'Same-run CLI replay after original300second deadline returned original report '
            'with transport disabled;0transportcalls and allrunbytesunchanged.',
            '173focused tests and2548repository tests passed before this actual public check.',
            'Original repository rawmanifest and baseline originals remain unchanged.'
        ], limitations=[
            'These are two source checks at fixed URLs, not recurring scheduling or all-manual coverage.',
            'Each unchanged status means byte equality to its prior original at retrieval time, '
            'not current law, no future changes, or an available newer edition elsewhere.',
            'review_needed:false refers to no new byte discrepancy; existing source-review '
            'and legal-currentness limitations still apply.',
            'The portable verifier checks saved custody/byte/classification consistency; '
            'the full maintained verifier was run at the original repository location.',
            'Saved implementation/replay scripts are historical evidence, not commands '
            'authorized for future live execution.'
        ])
    (DEST / 'ACCEPTANCE.json').write_text(receipt.model_dump_json(indent=2) + '\n')
    (DEST / 'ACCEPTANCE.schema.json').write_text(json.dumps(Receipt.model_json_schema(), indent=2) + '\n')
    shutil.copyfile('/private/tmp/verify_maintained_watch_copy.py', DEST / 'verify_copy.py')
    (DEST / 'README.md').write_text(
        '# Actual finite manual PDF watch\n\n'
        'The maintained checker made two public requests at00:44:41–43UTC on September13,2026. '
        'Both Colorado Springs PDFs returned HTTP200 and matched their accepted original bytes. '
        'The receipt preserves actual response times, immutable input snapshots and original bodies.\n\n'
        'Root offline verification and same-run replay after the original deadline passed; the '
        'replay disabled transport and retained every run byte. The2,548-test full suite predates '
        'this public check and applies to the copied implementation. It is not a claim about '
        'subsequent unrelated feature changes.\n\n'
        'Run `python -I -B /absolute/path/to/verify_copy.py` for a read-only portable check. '
        'It checks saved hashes, schemas, actual timing/URL/body/classification relationships and '
        'both PDF structures. It does not import the saved implementation, make requests, or '
        'replay the full repository-dependent canonical preflight.\n\n'
        'No scheduler was installed. These two fixed URLs do not cover the other manual PDFs '
        'or discover new editions at different URLs. `review_needed:false` is limited to the '
        'byte comparison; source-quality and legal-currentness questions remain unresolved. '
        'See the maintained [operator guide](../../../docs/MANUAL_SOURCE_WATCH.md).\n')
    (DEST / 'FINAL_MANIFEST.schema.json').write_text(
        json.dumps(Manifest.model_json_schema(), indent=2) + '\n')
    manifest = Manifest(files=[ref(p, DEST) for p in sorted(DEST.rglob('*')) if p.is_file()])
    (DEST / 'FINAL_MANIFEST.json').write_text(manifest.model_dump_json(indent=2) + '\n')
    print(json.dumps({'files': len(manifest.files) + 1,
                      'acceptance_sha256': ref(DEST / 'ACCEPTANCE.json', DEST).sha256,
                      'manifest_sha256': ref(DEST / 'FINAL_MANIFEST.json', DEST).sha256}))
