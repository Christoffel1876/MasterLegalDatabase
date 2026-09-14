"""Independently stream local predecessor metadata; never modify the corpus."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import jsonschema
from pydantic import AwareDatetime, Field

from run_checks import Asset, Strict

HERE = Path(__file__).resolve().parent
REPO = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
PREP = HERE / 'reviewed-preparation'


class Scan(Strict):
    """Exact observed metadata bytes and exact-value matches only."""
    path: str
    sha256: str
    size_bytes: int
    rows: int | None
    exact_value_matches: list[str]


class DataCheck(Strict):
    """Bounded duplicate comparison, not coverage or source-currentness certification."""
    recorded_at: AwareDatetime
    status: Literal['passed_no_exact_local_match']
    source_id: str
    source_sha256: str
    source_size_bytes: int
    metadata: list[Scan]
    ordinary_raw_files: int
    matching_size_files: list[Asset]
    equal_digest_paths: list[str]
    public_header_files: int
    sensitive_header_names_present: list[str]
    canonical_apply: Literal[False]
    public_requests: Literal[0]
    limitations: list[str]


def strings(value: Any) -> set[str]:
    """Extract literal string values only, without URL or filename inference."""
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(strings(x) for x in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(strings(x) for x in value)) if value else set()
    return set()


def run() -> None:
    """Compare exact targets across retained metadata and actual matching-size originals."""
    plan = json.loads((PREP / 'PREPARATION.json').read_bytes())
    comparison = json.loads((PREP / 'COMPARISON.json').read_bytes())
    template = plan['templates'][0]
    targets = {template['record_id'], template['source']['sha256'], template['official_source_url']}
    scans = []
    for declared in comparison['scans']:
        path = REPO / declared['path']
        assert not path.is_symlink()
        digest = hashlib.sha256()
        size = 0
        rows = 0 if path.suffix == '.jsonl' else None
        hits: set[str] = set()
        with path.open('rb') as handle:
            if rows is not None:
                for line in handle:
                    digest.update(line)
                    size += len(line)
                    rows += 1
                    hits |= targets & strings(json.loads(line))
            else:
                raw = handle.read()
                digest.update(raw)
                size = len(raw)
                hits = targets & strings(json.loads(raw))
        assert digest.hexdigest() == declared['sha256'] and size == declared['size_bytes']
        assert rows == declared['jsonl_rows'] and not hits
        scans.append(Scan(path=declared['path'], sha256=digest.hexdigest(),
                          size_bytes=size, rows=rows, exact_value_matches=sorted(hits)))
    count = 0
    candidates = []
    matches = []
    for top, dirs, names in os.walk(REPO / '_RAW_ARCHIVE', followlinks=False):
        for name in dirs + names:
            assert not (Path(top) / name).is_symlink()
        for name in names:
            path = Path(top) / name
            assert path.is_file()
            count += 1
            if path.stat().st_size == template['source']['size_bytes']:
                with path.open('rb') as handle:
                    sha = hashlib.file_digest(handle, 'sha256').hexdigest()
                ref = Asset(path=path.relative_to(REPO).as_posix(), sha256=sha,
                            size_bytes=path.stat().st_size)
                candidates.append(ref)
                if sha == template['source']['sha256']:
                    matches.append(ref.path)
    assert count == comparison['raw_ordinary_files_seen'] and not matches
    header_files = 0
    sensitive = set()
    for path in PREP.rglob('*'):
        if path.is_file() and ('headers' in path.name.lower()) and path.suffix != '.json':
            header_files += 1
            for line in path.read_bytes().splitlines():
                name = line.split(b':', 1)[0].strip().lower()
                if name in {b'authorization', b'proxy-authorization', b'cookie', b'set-cookie'}:
                    sensitive.add(name.decode('ascii'))
    record = DataCheck(recorded_at=datetime.now(timezone.utc),
        status='passed_no_exact_local_match', source_id=template['record_id'],
        source_sha256=template['source']['sha256'], source_size_bytes=template['source']['size_bytes'],
        metadata=scans, ordinary_raw_files=count, matching_size_files=candidates,
        equal_digest_paths=matches, public_header_files=header_files,
        sensitive_header_names_present=sorted(sensitive), canonical_apply=False, public_requests=0,
        limitations=['Only exact literal values were compared; differently encoded URLs may differ.',
            'Absent LFS content and external handoff/research files were not original-byte candidates.',
            'Header-name check covers retained header files only and does not replay omitted originals.',
            'PDF framing/page count is structural evidence, not complete content or legal review.'])
    raw = record.model_dump_json(indent=2) + '\n'
    schema = DataCheck.model_json_schema()
    jsonschema.validate(json.loads(raw), schema)
    with (HERE / 'LOCAL_DATA_CHECK.json').open('x') as handle:
        handle.write(raw)
    with (HERE / 'LOCAL_DATA_CHECK.schema.json').open('x') as handle:
        handle.write(json.dumps(schema, indent=2) + '\n')
    sys.stdout.write(record.status + '\n')


if __name__ == '__main__':
    run()
