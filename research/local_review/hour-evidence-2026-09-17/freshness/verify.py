"""Offline closed-packet/schema verifier; optional tracked-input hash replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from models import Manifest, Pin, Queue, Report


def check(condition: bool, message: str) -> None:
    """Reject a failed invariant without depending on assertions."""
    if not condition:
        raise ValueError(message)


def validate() -> None:
    """Validate only local artifacts and, when requested, pinned Git blobs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((base / 'FINAL_MANIFEST.json').read_bytes())
    check(manifest.excluded == ['FINAL_MANIFEST.json'], 'Unexpected exclusion')
    expected = {p.path for p in manifest.files}
    check(len(expected) == len(manifest.files), 'Duplicate inventory path')
    actual = set()
    for path in base.rglob('*'):
        check(not path.is_symlink(), 'Symlink refused')
        if path.is_file():
            actual.add(path.relative_to(base).as_posix())
    check(actual == expected | {'FINAL_MANIFEST.json'}, 'Inventory membership mismatch')
    for ref in manifest.files:
        path = Path(ref.path)
        check(not path.is_absolute() and '..' not in path.parts, 'Unsafe path')
        body = (base / path).read_bytes()
        check(len(body) == ref.size_bytes, 'Payload size mismatch: ' + ref.path)
        check(hashlib.sha256(body).hexdigest() == ref.sha256, 'Hash mismatch: ' + ref.path)
    report = Report.model_validate_json((base / 'REPORT.json').read_bytes())
    queue = Queue.model_validate_json((base / 'CANDIDATE_QUEUE.json').read_bytes())
    for name, model in [('REPORT', Report), ('CANDIDATE_QUEUE', Queue),
                        ('FINAL_MANIFEST', Manifest)]:
        check(json.loads((base / (name + '.schema.json')).read_bytes())
              == model.model_json_schema(), 'Schema companion mismatch: ' + name)
    policy = json.loads((base / 'policy-contract.json').read_bytes())
    check(set(policy['required_fields']) <= report.model_dump().keys(), 'Report contract')
    for candidate in report.candidates:
        check(set(policy['candidate_required_fields']) <= candidate.model_dump().keys(),
              'Candidate contract')
        check(candidate.status in policy['allowed_statuses'], 'Status contract')
        check(candidate.change_type in policy['allowed_change_types'], 'Change contract')
    check(queue.candidates == report.candidates[:2], 'Queue/report mismatch')
    check(report.public_action_count == len(report.sources_checked) == 4, 'Action count')
    check(len({e.event_id for e in report.sources_checked}) == 4, 'Duplicate event')
    check(len({c.authority_id for c in report.candidates}) == 3, 'Authority count')
    for event in report.sources_checked:
        check(event.evidence in manifest.files, 'Unbound evidence')
        evidence = json.loads((base / event.evidence.path).read_bytes())
        check(event.interval_start == evidence['start']['current_time'], 'Start mismatch')
        check(event.interval_end == evidence['end']['current_time'], 'End mismatch')
    counts = {c.input.path: c for c in report.comparisons}
    check(counts['_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'].row_count == 48390,
          'Legacy scan count')
    check(len(counts['04_Rulemaking/_index.jsonl'].matches['register_issue_ids']) == 39,
          'Register issue ID binding')
    check(counts['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl']
          .row_count == 70, 'Manual count')
    if args.repo:
        refs = report.controls + [c.input for c in report.comparisons]
        for ref in refs:
            process = subprocess.Popen(
                ['git', 'show', f'{report.baseline_commit}:{ref.path}'],
                cwd=args.repo, stdout=subprocess.PIPE)
            check(process.stdout is not None, 'No blob stream')
            digest = hashlib.sha256()
            size = 0
            while chunk := process.stdout.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
            check(process.wait() == 0, 'Git blob unavailable')
            check(size == ref.size_bytes and digest.hexdigest() == ref.sha256,
                  'Pinned input mismatch: ' + ref.path)
    sys.stdout.write('PASS: closed packet, strict schemas, four events, two proposals, '
                     'one known Register issue; legal currentness not verified.\n')


if __name__ == '__main__':
    validate()
