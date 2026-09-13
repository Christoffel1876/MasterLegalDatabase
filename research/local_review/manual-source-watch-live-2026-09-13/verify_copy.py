"""Read-only portable checks of saved live-run evidence; no saved code is executed."""
from datetime import datetime
from pathlib import Path
import hashlib
import json

import jsonschema
import pymupdf

ROOT = Path(__file__).resolve().parent


def read(name: str) -> bytes:
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts or rel.as_posix() != name:
        raise ValueError('Unsafe evidence path')
    path = ROOT / rel
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Nonordinary evidence')
    return path.read_bytes()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked(ref: dict, prefix: str = '') -> bytes:
    data = read(prefix + ref['path'])
    if len(data) != ref['size_bytes'] or sha(data) != ref['sha256']:
        raise ValueError('Evidence bytes differ: ' + ref['path'])
    return data


def schema(value: dict, name: str) -> None:
    definition = json.loads(read(name))

    def local(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key in {'$ref', '$dynamicRef'} and not str(value).startswith('#'):
                    raise ValueError('External schema resolution refused')
                local(value)
        elif isinstance(item, list):
            for value in item:
                local(value)

    local(definition)
    jsonschema.Draft202012Validator(definition).validate(value)


def utc(text: str) -> datetime:
    value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('Naive event time')
    return value


def verify() -> dict:
    manifest = json.loads(read('FINAL_MANIFEST.json'))
    schema(manifest, 'FINAL_MANIFEST.schema.json')
    expected = {r['path'] for r in manifest['files']} | {'FINAL_MANIFEST.json'}
    actual = set()
    for path in ROOT.rglob('*'):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError('Nonordinary package member')
        if path.is_file():
            actual.add(path.relative_to(ROOT).as_posix())
    if actual != expected or len(expected) != len(manifest['files']) + 1:
        raise ValueError('Closed inventory differs')
    for item in manifest['files']:
        checked(item)
    acceptance = json.loads(read('ACCEPTANCE.json'))
    schema(acceptance, 'ACCEPTANCE.schema.json')
    for item in acceptance['preserved_files']:
        checked(item)
    report = json.loads(read('run/report.json'))
    schema(report, 'schemas/report.schema.json')
    invocation = json.loads(read('run/INVOCATION.json'))
    schema(invocation, 'schemas/invocation.schema.json')
    run_manifest = json.loads(read('run/RUN_MANIFEST.json'))
    schema(run_manifest, 'schemas/run-manifest.schema.json')
    if {r['path'] for r in run_manifest['files']} | {'RUN_MANIFEST.json'} != {
            p[4:] for p in expected if p.startswith('run/')}:
        raise ValueError('Original closed run inventory differs')
    for item in run_manifest['files']:
        checked(item, 'run/')
    for name in ['stdout.json', 'offline-verification.json']:
        if read('dispatch/' + name) != read('run/report.json'):
            raise ValueError('Actual CLI/offline report differs')
    config = read('implementation/config/manual_source_watch.json')
    if config != read('run/inputs/selection.json') or sha(config) != report['plan_sha256']:
        raise ValueError('Selection snapshot differs')
    if (sha(read('implementation/geode/pipeline/manual_source_watch.py')) !=
            report['implementation_sha256'] or
            sha(read('implementation/geode/pipeline/manual_watch_http.py')) !=
            report['transport_sha256']):
        raise ValueError('Actual implementation differs')
    if (report['status'] != 'completed' or report['mode'] != 'live_http' or
            report['clock_basis'] != 'actual_utc_clock' or report['stop_reason'] is not None or
            report['state']['request_count'] != 2 or report['state']['charged_bytes'] != 421075):
        raise ValueError('Unexpected live outcome or budget')
    auth = json.loads(read('dispatch/AUTHORIZATION.json'))
    schema(auth, 'dispatch/AUTHORIZATION.schema.json')
    if utc(auth['prepared_at']) > utc(report['dispatch_at']):
        raise ValueError('Preparation occurred after dispatch')
    selection = json.loads(config)
    if [t['url'] for t in selection['targets']] != auth['selected_urls']:
        raise ValueError('Authorized source URLs differ')
    total = 0
    for index, (target, observation) in enumerate(zip(
            selection['targets'], report['observations'], strict=True), 1):
        prefix = f'run/events/{index:04d}/'
        reservation = json.loads(read(prefix + 'reservation.json'))
        result = json.loads(read(prefix + 'result.json'))
        schema(reservation, 'schemas/reservation.schema.json')
        schema(result, 'schemas/result.schema.json')
        if (result['reservation_sha256'] != sha(read(prefix + 'reservation.json')) or
                result['http_status'] != 200 or result['outcome'] != 'complete' or
                result['partial_body'] or result['redirect_url'] is not None or
                reservation['url'] != target['url'] or reservation['source_id'] != target['source_id']):
            raise ValueError('Event identity or complete HTTP status differs')
        if not (utc(report['dispatch_at']) <= utc(reservation['reserved_at']) <=
                utc(result['finished_at']) < utc(reservation['deadline'])):
            raise ValueError('Actual event time binding differs')
        if utc(result['finished_at']) > utc(report['generated_at']):
            raise ValueError('Report predates its response')
        body = checked(result['body'], 'run/')
        if body != read(f'baseline/{index:04d}.pdf') or sha(body) != target['baseline']['sha256']:
            raise ValueError('Baseline equality differs')
        with pymupdf.open(stream=body, filetype='pdf') as pdf:
            if len(pdf) != 7 or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError('PDF structure differs')
        header = json.loads(checked(result['public_headers'], 'run/'))
        schema(header, 'schemas/headers.schema.json')
        if set(header['headers']) & {'set-cookie', 'cookie', 'authorization', 'proxy-authorization'}:
            raise ValueError('Private headers present')
        if (observation['status'] != 'unchanged' or not observation['bytes_equal_to_baseline'] or
                observation['response_body'] != result['body'] or
                observation['canonical_source_id'] != target['canonical_source_id'] or
                observation['response_finished_at'] != result['finished_at'] or
                observation['legal_currentness'] != 'not_verified' or
                observation['canonical_update'] != 'not_attempted'):
            raise ValueError('Observation body/custody/classification differs')
        total += len(body)
    if total != 421075 or len(report['observations']) != 2:
        raise ValueError('Actual retained byte/source count differs')
    replay = json.loads(read('dispatch/EXPIRED_REPLAY.json'))
    schema(replay, 'dispatch/EXPIRED_REPLAY.schema.json')
    if (replay['transport_calls'] or replay['exit_code'] or
            not replay['all_run_bytes_unchanged'] or not replay['returned_original_report_bytes'] or
            not utc(replay['checked_at']) > utc(replay['original_deadline']) or
            replay['report_sha256'] != sha(read('run/report.json'))):
        raise ValueError('Expired zero-transport replay differs')
    return {'status': 'verified_saved_live_custody_and_consistency',
            'files': len(expected), 'actual_requests': 2, 'retained_bytes': total,
            'outcomes': ['unchanged', 'unchanged'], 'requests_by_this_verifier': 0,
            'saved_implementation_executed': False, 'recurring_deployment': 'not_established',
            'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
