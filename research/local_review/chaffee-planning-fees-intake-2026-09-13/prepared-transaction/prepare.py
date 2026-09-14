"""Prepare one new Chaffee transaction; never execute old builders or canonical writes."""
from __future__ import annotations

from typing import Any

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
RETRIEVAL = HERE.parent / 'ptolemy-chaffee-fee-directed-retrieval'
RETRIEVAL_SHA = 'ecfdc65448dd2cc58d00eec7ec1ba3e9987457d5d9270d5e3362c165602ab8f3'
SELECTED = [
    ('chaffee-planning-application-fees-atlas-directed', 'A001', 2,
     '8c6b6176f8617a43c4f4eb422f5c9c7287ffba8f2daee4af803c6831d2682205', 206144),
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
    """Validate sha within the prepared offline scope."""
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
    """Validate copied within the prepared offline scope."""
    for path in (source, *source.parents):
        if path.is_symlink():
            raise ValueError('linked input')
    body = source.read_bytes()
    write(HERE / destination, body)
    return Asset(path=destination, sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))


def strings(value: Any) -> Any:
    """Validate strings within the prepared offline scope."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def compare(targets: Any) -> Any:
    """Stream all current local legacy rows; do not infer remote missing-byte equality."""
    needles = {s[0] for s in SELECTED} | {s[3] for s in SELECTED}
    for target in targets:
        needles.update(target[k] for k in ['request_url', 'raw_location', 'prior_request_url'])
    county_url = URLS[SELECTED[0][0]].replace(
        'cms2.revize.com/revize/chaffeecounty', 'www.chaffeecounty.org')
    needles.update([county_url, county_url.replace('%20', ' ')])
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
    if scans[0]['jsonl_rows'] != 69 or scans[1]['jsonl_rows'] != 70:
        raise ValueError('current canonical baseline is not 69/70')
    if scans[0]['exact_value_matches'] or scans[1]['exact_value_matches'] or raw_matches:
        raise ValueError('selected identity/URL/digest already preserved canonically')
    raw = result.model_dump_json(indent=2).encode() + b'\n'
    Comparison.model_validate_json(raw)
    write(HERE / 'COMPARISON.json', raw)
    write(HERE / 'COMPARISON.schema.json',
          (json.dumps(Comparison.model_json_schema(), indent=2) + '\n').encode())
    return Asset(path='COMPARISON.json', sha256=hashlib.sha256(raw).hexdigest(),
                 size_bytes=len(raw))


def current_commit() -> str:
    """Read the current ordinary Git identity without executing Git or changing state."""
    gitdir = REPO / '.git'
    if gitdir.is_file():
        gitdir = (REPO / gitdir.read_text().strip().removeprefix('gitdir: ')).resolve()
    head = (gitdir / 'HEAD').read_text().strip()
    if not head.startswith('ref: '):
        return head
    name = head.removeprefix('ref: ')
    loose = gitdir / name
    if loose.is_file():
        return loose.read_text().strip()
    for line in (gitdir / 'packed-refs').read_text().splitlines():
        if line.endswith(' ' + name):
            return line.split()[0]
    raise ValueError('current commit unavailable')


def main() -> None:
    """Validate main within the prepared offline scope."""
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
        earlier_path = 'evidence/prior-retrieval/PLAN.json'
        earlier = json.loads((HERE / bypath[earlier_path].path).read_bytes())['targets'][2]
        result_path = f'events/{action}/RESULT.json'
        result = json.loads((HERE / bypath[result_path].path).read_bytes())
        body = bypath[f'events/{action}/response.body']
        if (body.sha256, body.size_bytes) != (expected_sha, expected_size):
            raise ValueError('exact selected PDF differs')
        selected = copied(HERE / body.path, f'sources/{sid}/original.pdf')
        limits = [
            target['evidence_limit'],
            'The new exact GET, TLS/writeout and complete body are observed direct acquisition '
            'evidence; this does not authenticate the older supplied county parent-page '
            'acquisition.',
            result['headers']['limitation'],
            'The source-only intake does not certify adoption, execution/signatures, '
            'effective dates, current law, complete extraction or structured-rule promotion.',
            'HTTP retrieval completed_at is separate from future received_at, '
            'frozen only on apply.',
            'The incoming local source is the exact response-body copy sources/' + sid
            + '/original.pdf; original_filename is that actual local basename, not a claim '
            'about a publisher Content-Disposition filename.',
        ]
        note = (
            'Exact county-linked Revize PDF acquired by an ordinary direct GET. '
            f'Observed request {result["started_at"]} through {result["completed_at"]}, '
            'HTTP200, TLS verified, no followed redirects, complete body. Actual argv, curl '
            'writeout and public header subset are preserved in the frozen retrieval packet. '
            'The parent county-page acquisition remains supplied historical evidence. The retained '
            'county redirect and new PDF GET are actual observed acquisitions; neither '
            'authenticates the earlier parent-page acquisition. This received_at is the later '
            'repository intake time '
            'only. Original local input basename is original.pdf. Source content review, '
            'adoption, legal effect and currentness are outside this intake.'
        )
        templates.append({
            'record_id': sid, 'authority_id': 'CO-COUNTY-CHAFFEE',
            'layer_id': '08_County_Authorities',
            'official_source_name': 'Chaffee County county-link label: ' + earlier['visible_label'],
            'official_source_url': target['request_url'],
            'acquisition_method': 'manual_official_download', 'source': selected,
            'original_filename': 'original.pdf', 'custody_note': note,
            'actual_repository_received_at': None, 'intake_id': None, 'archive_path': None,
        })
        provenance.append({
            'source_id': sid, 'action_id': action, 'target_id': target['target_id'],
            'authority_id': 'CO-COUNTY-CHAFFEE', 'source': selected, 'response_body': body,
            'physical_pages': pages,
            'parent': bypath['evidence/prior-retrieval/' + earlier['parent_body']['path']],
            'parent_url': earlier['parent_url'], 'base_href': earlier['base_href'],
            'original_href': earlier['literal_href'], 'visible_label': earlier['visible_label'],
            'prior_redirect_notice': bypath[target['prior_response_body']['path']],
            'prior_actual_result': bypath[target['prior_actual_result']['path']],
            'prior_public_headers': bypath[target['prior_public_headers']['path']],
            'earlier_referral_plan': bypath[earlier_path],
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
            'document_role': ('County-linked application fee schedule; source-fidelity QA is '
                              'separate and not asserted by intake'),
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
        'comparison_commit': current_commit(),
        'templates': templates, 'provenance': provenance, 'baseline': baseline,
        'runtime_pins': runtime, 'custody_subset': subset,
        'retrieval_plan': bypath['PLAN.json'], 'retrieval_manifest': rec_manifest,
        'deduplication': comparison, 'legacy_guard': legacy,
        'raw_before': 69, 'ledger_before': 70, 'raw_after': 70, 'ledger_after': 71,
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
    sys.stdout.write(hashlib.sha256(raw).hexdigest() + '\n')


if __name__ == '__main__':
    main()
