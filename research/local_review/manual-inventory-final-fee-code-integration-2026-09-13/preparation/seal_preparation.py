"""Seal a tested final inventory proposal; never install it or alter canonical sources."""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from models import Asset, Manifest, Preparation, Review, Target

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2] / 'MasterLegalDatabase'
PACKAGE = 'research/local_review/manual-source-review-inventory-2026-09-11'
INTAKE = 'research/local_review/chaffee-planning-fees-intake-2026-09-13/prepared-transaction'


def ref(path: Path, relative: Path) -> Asset:
    """Hash exact bytes with a declared containing root."""
    raw = path.read_bytes()
    return Asset(path=path.relative_to(relative).as_posix(),
                 sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def save(name: str, value: Any) -> None:
    """Validate strict JSON and its exported schema before a write-once publication."""
    raw = value.model_dump_json(indent=2) + '\n'
    schema = type(value).model_json_schema()
    jsonschema.validate(json.loads(raw), schema)
    with (BASE / (name + '.schema.json')).open('x') as handle:
        handle.write(json.dumps(schema, indent=2) + '\n')
    with (BASE / (name + '.json')).open('x') as handle:
        handle.write(raw)


def seal() -> None:
    """Bind actual intake and acceptance metadata to the exact tested proposal."""
    test = json.loads((BASE / 'STAGED_TEST_RUN.json').read_bytes())
    assert test['exit_code'] == 0 and test['temporary_directory_removed']
    log = (BASE / 'focused-tests.log').read_text()
    matches = re.findall(r'(\d+) passed', log)
    assert len(matches) == 1
    passed = int(matches[0])
    coverage = json.loads((BASE / 'coverage.json').read_bytes())['totals']['percent_covered']
    assert coverage >= 90
    newplan = json.loads((BASE / 'proposed/join-plan.json').read_bytes())
    roots = ['gunnison-building-code-source-qa-2026-09-13',
             'chaffee-planning-fees-source-qa-2026-09-13']
    reviews = []
    for name, join in zip(roots, newplan['reviews'][33:], strict=True):
        parent = ROOT / 'research/local_review' / name
        acceptance = json.loads((parent / 'ACCEPTANCE.json').read_bytes())
        qa = parent / acceptance['source_review']['path']
        schema = parent / acceptance['source_review_schema']['path']
        body = json.loads(qa.read_bytes())
        reviews.append(Review(
            source_id=body['source_id'], source_sha256=body['source']['sha256'],
            authority_id=body['authority_id'], acceptance=ref(parent / 'ACCEPTANCE.json', ROOT),
            acceptance_schema=ref(parent / 'ACCEPTANCE.schema.json', ROOT),
            review=ref(qa, ROOT), review_schema=ref(schema, ROOT),
            review_kind='checked_passages' if 'gunnison' in name else 'checked_tables'))
        assert join['review'] == reviews[-1].review.model_dump()
        assert join['review_schema'] == reviews[-1].review_schema.model_dump()
    targets = []
    for name, path in [
        ('manual_review_inventory.py', 'geode/pipeline/manual_review_inventory.py'),
        ('test_manual_review_inventory.py', 'tests/test_manual_review_inventory.py'),
        *[(n, PACKAGE + '/' + n) for n in [
            'join-plan.json', 'inventory.json', 'inventory.schema.json', 'README.md']],
    ]:
        before, after = BASE / 'preimages' / name, BASE / 'proposed' / name
        assert (ROOT / path).read_bytes() == before.read_bytes(), 'Maintained predecessor changed'
        targets.append(Target(repository_path=path, before=ref(before, BASE), after=ref(after, BASE)))
    receipt = json.loads((ROOT / INTAKE / 'execution/RECEIPT.json').read_bytes())
    prep = Preparation(recorded_at=datetime.now(timezone.utc), status='prepared_tested_not_installed',
        reviewer='Plato', targets=targets, reviews=reviews,
        actual_intake_receipt=ref(ROOT / INTAKE / 'execution/RECEIPT.json', ROOT),
        actual_intake_received_at=datetime.fromisoformat(
            receipt['actual_repository_received_at'].replace('Z', '+00:00')),
        raw_manifest=Asset(**newplan['manual_manifest']), prior_sources=69, prior_review_links=33,
        proposed_sources=70, proposed_review_links=35, proposed_unmapped=35,
        old_authority_joins_preserved=69, old_review_joins_preserved=33,
        only_old_row_with_new_review='gunnison-building-code-resolution-2023-22-sh-ext-003',
        test_log=ref(BASE / 'focused-tests.log', BASE), initial_failure_log=None,
        coverage=ref(BASE / 'coverage.json', BASE), passed_tests=passed,
        branch_inclusive_coverage_percent=coverage,
        limitations=[
            'Metadata mapping of two accepted source reviews only; no lookup adapter, RuleUnit, '
            'coverage, current-law or answer-safe promotion.',
            'All 69 authority and 33 review joins are unchanged. Only the existing Gunnison code '
            'row gains a review; the single newly preserved Chaffee fee row is added.',
            'Gunnison original HTTP acquisition remains unverified. Chaffee observed acquisition '
            'and actual repository receipt remain separate from printed source date claims.',
            'Review QA fields predating independent acceptance or canonical intake remain unchanged '
            'historical assertions. Acceptance receipts are separately bound in join notes.',
            'Focused tests ran only in a removed temporary copy. Full maintained-suite execution '
            'and eventual installation are separate root actions, not claimed by this preparation.',
        ], public_requests=0, canonical_source_writes=0, legal_currentness='not_verified',
        answer_safe=False)
    save('PREPARATION', prep)
    save('FINAL_MANIFEST', Manifest(recorded_at=datetime.now(timezone.utc),
         status='closed_inventory_preparation',
         files=[ref(p, BASE) for p in sorted(BASE.rglob('*')) if p.is_file()],
         exclusions='FINAL_MANIFEST.json, FINAL_MANIFEST.schema.json, execution/**'))
    sys.stdout.write('Sealed tested inventory proposal.\n')


if __name__ == '__main__':
    seal()
