"""Read-only portable validation of the prepared watch and its injected examples."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import watch as w  # noqa: E402
from preparation_models import Check, Preparation  # noqa: E402


def validate() -> Check:
    """Check closed payloads, exact copied custody and every fixture result without HTTP."""
    before = w.verify_inventory(HERE, 'prototype')
    data = (HERE / 'PREPARATION_RECEIPT.json').read_bytes()
    receipt = Preparation.model_validate_json(data)
    jsonschema.Draft202012Validator(json.loads(
        (HERE / 'PREPARATION_RECEIPT.schema.json').read_bytes())).validate(json.loads(data))
    for ref in [receipt.plan, receipt.implementation, receipt.reused_guard,
                receipt.tests, receipt.test_log, *receipt.copied_source_subset]:
        w.g.check_ref(HERE, ref)
    if (receipt.plan.path != 'WATCH_PLAN.json' or receipt.implementation.path != 'watch.py'
            or receipt.reused_guard.path != 'sd014_guard.py'
            or receipt.reused_guard.sha256 != w.GUARD_SHA):
        raise ValueError('Preparation identity mismatch')
    plan = w.load_plan(HERE / receipt.plan.path)
    actual = {p.relative_to(HERE).as_posix() for p in (HERE / 'evidence/custody').rglob('*')
              if p.is_file()}
    if actual != {f.path for f in receipt.copied_source_subset} or len(actual) != 21:
        raise ValueError('Selected original custody subset differs')
    log = w.g.check_ref(HERE, receipt.test_log).read_text()
    if '71 passed' not in log or 'failed' in log:
        raise ValueError('Focused test result differs')
    total_events = 0
    for example in receipt.examples:
        w.g.check_ref(HERE, example.manifest)
        w.g.check_ref(HERE, example.report)
        if (example.manifest.path != f'runs/{example.name}/RUN_MANIFEST.json'
                or example.report.path != f'runs/{example.name}/report.json'):
            raise ValueError('Unexpected fixture result path')
        report = w.verify_run(HERE / 'WATCH_PLAN.json', HERE / 'runs' / example.name)
        jsonschema.Draft202012Validator(json.loads((HERE / 'REPORT.schema.json').read_bytes())).validate(
            report.model_dump(mode='json'))
        if (report.mode != 'offline_fixture' or report.clock_basis != 'injected_fixture_clock'
                or [o.status for o in report.observations] != example.expected_statuses):
            raise ValueError('Fixture claimed as live or classification differs')
        total_events += report.state.request_count
    if len(receipt.examples) != 3 or total_events != 5:
        raise ValueError('Fixture count mismatch')
    if w.verify_inventory(HERE, 'prototype') != before:
        raise ValueError('Preparation changed during verification')
    return Check(status='passed', prototype_files=len(before.files), copied_custody_files=21,
                 sources=len(plan.targets), pdf_baseline_pages=14, offline_examples=3,
                 offline_example_request_events=total_events, public_requests_made_by_verifier=0,
                 legal_currentness='not_verified')


def main() -> int:
    """Print a typed local verification result without creating or updating files."""
    try:
        result = validate()
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 1
    sys.stdout.write(result.model_dump_json(indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
