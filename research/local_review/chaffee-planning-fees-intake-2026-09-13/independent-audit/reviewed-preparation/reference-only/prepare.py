"""Prepare one new Chaffee transaction; never execute old builders or canonical writes."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

from pydantic import ConfigDict, BaseModel
from models import Asset, Baseline, Preparation, URLS

HERE = Path(__file__).absolute().parent
PROJECT = HERE.parents[2]
REPO = PROJECT / 'MasterLegalDatabase'
RETRIEVAL = HERE.parent / 'ptolemy-chaffee-directed-retrieval'
RETRIEVAL_SHA = '0ad7b970736921a175de778e05629db8b9191ba2394a692d3715c0a51421c95f'
SELECTED = [
    ('chaffee-cwrc-ordinance-2026-02-atlas-directed', 'A001', 14,
     '0688818dfd4d7726f1eb84b5b57c47580d01b094297a92d4ce88c600ccfe7eba', 1146747),
    ('chaffee-electric-ordinance-2026-01-atlas-directed', 'A002', 7,
     'c0bfb6e8d4adb846fd62ec7dabbdd824286f7432be6a82b6b2d2264d4553cdf6', 529100),
]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO))
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord


class ExactMatch(BaseModel):
    """An exact value match, with a physical JSONL row when available."""
    model_config = ConfigDict(extra='forbid', strict=True)
    physical_line: int | None = None
    matched_values: list[str]


class Scan(BaseModel):
    """A complete local file comparison and its qualified matches."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str
    size_bytes: int
    jsonl_rows: int | None
    exact_value_matches: list[ExactMatch]


class Comparison(BaseModel):
    """Exact local metadata comparisons with explicit unavailable-byte limits."""
    model_config = ConfigDict(extra='forbid', strict=True)
    compared_at: str
    source_ids: list[str]
    source_sha256: list[str]
    scans: list[Scan]
    raw_ordinary_files_seen: int
    raw_equal_size_files_hashed: int
    raw_digest_matches: list[str]
    limitations: list[str]


def sha(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path: Path, body: bytes) -> None:
    """Create once, atomically; refuse a conflicting previous result."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError('Refuse overwrite ' + str(path))
        return
    temp = path.with_name(path.name + '.tmp')
    with temp.open('xb') as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def copied(source: Path, destination: str) -> Asset:
    for path in (source, *source.parents):
        if path.is_symlink():
            raise ValueError('linked input')
    body = source.read_bytes()
    write(HERE / destination, body)
    return Asset(path=destination, sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def compare(targets):
    """Stream all current local legacy rows; do not infer remote missing-byte equality."""
    needles = {s[0] for s in SELECTED} | {s[3] for s in SELECTED}
    for target in targets[:2]:
        needles.update(target[k] for k in ['request_url', 'raw_location',
                       'encoded_county_url', 'resolved_county_url'])
    scans = []
    for name in [
        '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl',
        '_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl',
        '_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json',
        '_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json',
    ]:
        path = REPO / name
        matches = []
        count = 0
        if path.suffix == '.jsonl':
            with path.open('rb') as handle:
                for count, line in enumerate(handle, 1):
                    value = json.loads(line)
                    if 'manual' in name.lower():
                        ManualSourceIntakeRecord.model_validate_json(line)
                    exact = sorted(needles.intersection(strings(value)))
                    if exact:
                        matches.append({'physical_line': count, 'matched_values': exact})
        else:
            exact = sorted(needles.intersection(strings(json.loads(path.read_bytes()))))
            if exact:
                matches.append({'matched_values': exact})
        scans.append({'path': name, 'sha256': sha(path), 'size_bytes': path.stat().st_size,
                      'jsonl_rows': count if path.suffix == '.jsonl' else None,
                      'exact_value_matches': matches})
    sizes = {s[4] for s in SELECTED}
    hashes = {s[3] for s in SELECTED}
    seen = hashed = 0
    raw_matches = []
    for top, dirs, files in os.walk(REPO / '_RAW_ARCHIVE', followlinks=False):
        for name in dirs + files:
            if (Path(top) / name).is_symlink():
                raise ValueError('linked raw archive entry')
        for name in files:
            path = Path(top) / name
            if not path.is_file():
                raise ValueError('nonordinary raw archive entry')
            seen += 1
            if path.stat().st_size in sizes:
                hashed += 1
                if sha(path) in hashes:
                    raw_matches.append(path.relative_to(REPO).as_posix())
    result = Comparison(
        compared_at=datetime.now(timezone.utc).isoformat(),
        source_ids=[s[0] for s in SELECTED], source_sha256=[s[3] for s in SELECTED],
        scans=scans, raw_ordinary_files_seen=seen, raw_equal_size_files_hashed=hashed,
        raw_digest_matches=raw_matches,
        limitations=[
            'Complete 48,390-row local legacy metadata stream compared; exact string-value '
            'matches distinguish URLs, IDs and digests. URL matches do not establish '
            'body equality.',
            'Raw scan covers present ordinary _RAW_ARCHIVE files only, using exact size before '
            'SHA256. It excludes absent LFS content, .git objects and external '
            'handoff/research copies.',
            'New identifiers, authority/layer, selected hashes and canonical prefixes are '
            'rechecked at transaction preflight. No currentness or adoption inference is made.',
        ],
    )
    if scans[0]['jsonl_rows'] != 67 or scans[1]['jsonl_rows'] != 68:
        raise ValueError('current canonical baseline is not 67/68')
    if scans[0]['exact_value_matches'] or scans[1]['exact_value_matches'] or raw_matches:
        raise ValueError('selected identity/URL/digest already preserved canonically')
    raw = result.model_dump_json(indent=2).encode() + b'\n'
    Comparison.model_validate_json(raw)
    write(HERE / 'COMPARISON.json', raw)
    write(HERE / 'COMPARISON.schema.json',
          (json.dumps(Comparison.model_json_schema(), indent=2) + '\n').encode())
    return Asset(path='COMPARISON.json', sha256=hashlib.sha256(raw).hexdigest(),
                 size_bytes=len(raw))


def main() -> None:
    if (HERE / 'PREPARATION.json').exists():
        raise ValueError('Frozen preparation exists; do not rerun')
    if sha(RETRIEVAL / 'FINAL_MANIFEST.json') != RETRIEVAL_SHA:
        raise ValueError('retrieval seal changed')
    manifest = json.loads((RETRIEVAL / 'FINAL_MANIFEST.json').read_bytes())
    subset = []
    for pin in manifest['files']:
        value = copied(RETRIEVAL / pin['path'], 'inputs/retrieval/' + pin['path'])
        if (value.sha256, value.size_bytes) != (pin['sha256'], pin['size_bytes']):
            raise ValueError('retained retrieval member changed')
        subset.append(value)
    rec_manifest = copied(RETRIEVAL / 'FINAL_MANIFEST.json',
                          'inputs/retrieval/FINAL_MANIFEST.json')
    subset.append(rec_manifest)
    bypath = {a.path.removeprefix('inputs/retrieval/'): a for a in subset}
    plan = json.loads((HERE / bypath['PLAN.json'].path).read_bytes())
    comparison = compare(plan['targets'])
    templates, provenance = [], []
    for index, (sid, action, pages, expected_sha, expected_size) in enumerate(SELECTED):
        target = plan['targets'][index]
        result_path = f'events/{action}/RESULT.json'
        result = json.loads((HERE / bypath[result_path].path).read_bytes())
        body = bypath[f'events/{action}/response.body']
        if (body.sha256, body.size_bytes) != (expected_sha, expected_size):
            raise ValueError('exact selected PDF differs')
        selected = copied(HERE / body.path, f'sources/{sid}/original.pdf')
        limits = [
            target['evidence_limit'],
            'The new exact GET, TLS/writeout and complete body are observed direct acquisition '
            'evidence; this does not authenticate the older supplied county redirect acquisition.',
            result['headers']['limitation'],
            'The source-only intake does not certify adoption, execution/signatures, '
            'effective dates, current law, complete extraction or structured-rule promotion.',
            'HTTP retrieval completed_at is separate from future received_at, '
            'frozen only on apply.',
            'The incoming local source is the exact response-body copy sources/' + sid
            + '/original.pdf; original_filename is that actual local basename, not a claim '
            'about a publisher Content-Disposition filename.',
        ]
        if index == 0:
            limits.append('Literal county label 2025 BOCC Ordinance 2026-02 is preserved; '
                          'the label/filename year mismatch is not resolved.')
        note = (
            'Exact county-linked Revize PDF acquired by an ordinary direct GET. '
            f'Observed request {result["started_at"]} through {result["completed_at"]}, '
            'HTTP200, TLS verified, no followed redirects, complete body. Actual argv, curl '
            'writeout and public header subset are preserved in the frozen retrieval packet. '
            'Earlier county-link and redirect custody is supplied historical evidence, not '
            'retroactively authenticated. This received_at is the later repository intake time '
            'only. Original local input basename is original.pdf. Source content review, '
            'adoption, legal effect and currentness are outside this intake.'
        )
        templates.append({
            'record_id': sid, 'authority_id': 'CO-COUNTY-CHAFFEE',
            'layer_id': '08_County_Authorities',
            'official_source_name': 'Chaffee County county-link label: ' + target['visible_label'],
            'official_source_url': target['request_url'],
            'acquisition_method': 'manual_official_download', 'source': selected,
            'original_filename': 'original.pdf', 'custody_note': note,
            'actual_repository_received_at': None, 'intake_id': None, 'archive_path': None,
        })
        provenance.append({
            'source_id': sid, 'action_id': action, 'target_id': target['target_id'],
            'authority_id': 'CO-COUNTY-CHAFFEE', 'source': selected, 'response_body': body,
            'physical_pages': pages, 'parent': bypath[target['parent_body']['path']],
            'parent_url': target['parent_url'], 'base_href': target['base_href'],
            'original_href': target['literal_href'], 'visible_label': target['visible_label'],
            'prior_redirect_notice': bypath[target['prior_redirect_notice']['path']],
            'prior_header_summary': bypath[target['prior_header_summary']['path']],
            'original_location': target['raw_location'],
            'reservation': bypath[f'events/{action}/RESERVATION.json'],
            'result': bypath[result_path],
            'public_headers': bypath[result['headers']['public_subset']['path']],
            'curl_writeout': bypath[result['stdout']['path']],
            'requested_url': result['requested_url'],
            'final_url': result['final_url'], 'http_status': 200,
            'http_started_at': result['started_at'], 'http_completed_at': result['completed_at'],
            'tls_verified': True, 'redirects_followed': 0, 'original_tool_command_retained': True,
            'acquisition_method': 'manual_official_download', 'actual_repository_received_at': None,
            'source_content_reviewed_in_this_intake': False,
            'document_role': target['anticipated_role'],
            'legal_currentness': 'not_verified', 'limitations': limits,
        })
    old = json.loads((HERE / 'reference-only/PREPARATION.json').read_bytes())
    baseline = []
    for item in old['baseline']:
        name = item['repository_path']; path = REPO / name
        count = None
        if path.suffix == '.jsonl':
            count = 0
            with path.open('rb') as handle:
                for line in handle:
                    ManualSourceIntakeRecord.model_validate_json(line); count += 1
        baseline.append(Baseline(repository_path=name,
                        preserved=copied(path, 'preimages/' + path.name), records=count))
    runtime = {name: sha(REPO / name) for name in old['runtime_pins']}
    legacy_path = '_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'
    legacy = Asset(path=legacy_path, sha256=sha(REPO / legacy_path),
                   size_bytes=(REPO / legacy_path).stat().st_size)
    data = {
        'schema_version': 1, 'prepared_at': datetime.now(timezone.utc).isoformat(),
        'status': 'PREPARED_NOT_APPLIED',
        'comparison_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                                                     text=True).strip(),
        'templates': templates, 'provenance': provenance, 'baseline': baseline,
        'runtime_pins': runtime, 'custody_subset': subset,
        'retrieval_plan': bypath['PLAN.json'], 'retrieval_manifest': rec_manifest,
        'deduplication': comparison, 'legacy_guard': legacy,
        'raw_before': 67, 'ledger_before': 68, 'raw_after': 69, 'ledger_after': 70,
        'public_requests': 0, 'canonical_mutations': 0, 'legal_currentness': 'not_verified',
        'answer_safe': False,
    }
    record = Preparation.model_validate_json(json.dumps(
        data, default=lambda v: v.model_dump(mode='json')))
    raw = record.model_dump_json(indent=2).encode() + b'\n'
    Preparation.model_validate_json(raw)
    write(HERE / 'PREPARATION.json', raw)
    write(HERE / 'PREPARATION.schema.json',
          (json.dumps(Preparation.model_json_schema(), indent=2) + '\n').encode())
    print(hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main()
