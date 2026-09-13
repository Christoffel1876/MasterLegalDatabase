"""Preserve three completed, replay-verified manual watch observations."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

from preserve_extended_receipts import preserve

BASE = Path('/Users/mcoors/Documents/Project Geode')
ROOT = BASE / 'MasterLegalDatabase'
OUT = ROOT / 'research/local_review/manual-watch-expanded-live-2026-09-13'


def main() -> None:
    """Freeze original run histories and the exact implementation that verified them."""
    now = datetime.now(timezone.utc)
    selections = []
    reports = []
    for kind in ['county', 'western', 'greeley']:
        folder = ROOT / ('.geode_runtime/manual_source_watch_batches/'
                         f'atlas-{kind}-fees-session-extension-01')
        manifest = json.loads((folder / 'RUN_MANIFEST.json').read_bytes())
        names = {ref['path'] for ref in manifest['files']}
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
        if actual != names | {'RUN_MANIFEST.json'}:
            raise ValueError('Run closure differs')
        for ref in manifest['files']:
            data = (folder / ref['path']).read_bytes()
            if len(data) != ref['size_bytes'] or hashlib.sha256(data).hexdigest() != ref['sha256']:
                raise ValueError('Run payload mismatch')
        run = json.loads((folder / 'run.json').read_bytes())
        if datetime.fromisoformat(run['deadline'].replace('Z', '+00:00')) >= now:
            raise ValueError('Not yet an expired-run verification checkpoint')
        report = json.loads((folder / 'report.json').read_bytes())
        if report['status'] != 'completed' or report['state']['request_count'] != 2:
            raise ValueError('Unexpected watch completion')
        for observation in report['observations']:
            if (observation['status'] != 'unchanged' or observation['http_status'] != 200 or
                    not observation['bytes_equal_to_baseline'] or
                    observation['response_body']['sha256'] != observation['baseline']['sha256']):
                raise ValueError('Watch equality scope changed')
        reports.append(report)
        selections.extend((p, 'runs/' + folder.name + '/' + p.relative_to(folder).as_posix())
                          for p in sorted(folder.rglob('*')) if p.is_file())
    paths = ['geode/pipeline/manual_source_watch_batches.py',
             'geode/pipeline/manual_watch_http_v2.py', 'config/manual_source_watch_sources_v1.json',
             'config/manual_source_watch_sources_v1.schema.json', 'docs/MANUAL_SOURCE_WATCH_BATCHES.md']
    for kind in ['county', 'western', 'greeley']:
        paths.extend([f'config/manual_source_watch_{kind}_fees_v1.json',
                      f'config/manual_source_watch_{kind}_fees_v1.schema.json'])
    selections.extend((ROOT / p, 'installed/' + p) for p in paths)
    selections.append((Path(__file__), 'preserve_expanded_watch_runs.py'))
    if sum(r['state']['charged_bytes'] for r in reports) != 2191486:
        raise ValueError('Recorded received byte totals differ')
    preserve(OUT, selections, 'completed_six_source_byte_checks_and_expired_replay_verified', [
        'Root executed three reviewed two-source plans with actual UTC clock; six HTTP200 '
        'responses total2191486 bytes, all equal their exact preserved PDF baselines.',
        'Dispatch/completion intervals: county02:21:52.868670–02:21:54.454276UTC; '
        'western02:22:33.585354–02:22:34.949999UTC; Greeley02:23:13.289255–02:23:14.913548UTC.',
        'After all three five-minute deadlines expired, root ran the installed read-only '
        '--verify-run commands successfully. Their returned report timestamps, request counts '
        'and PDF identities remained the original observations; no new request was requested.',
        'The original full run manifests, invocation/request reservations, results, public '
        'headers, complete response bodies, selected plans and raw-manifest preimages are retained.',
        'Earlier custody and source-review limits remain inside every source binding. '
        'Historical PREPARED status inside copied catalog context is not the outer live-run status.',
        'Exact byte equality does not establish current law or discover a new edition at '
        'another URL. No baseline/raw archive update, recurring deployment or publication occurred.',
        'The old Springs code/config and historical run remain unchanged. This evidence '
        'belongs to the separately reviewed successor modules and their exact implementation hashes.',
    ])


if __name__ == '__main__':
    main()
