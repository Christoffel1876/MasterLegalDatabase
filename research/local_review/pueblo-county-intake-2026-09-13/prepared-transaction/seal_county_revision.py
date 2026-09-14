"""Seal and test the fixed-source revision; never perform canonical intake."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

RUN = Path(__file__).resolve().parent
BASE = RUN / 'extended-run/pueblo-county-fees-intake-revision'
INDEP = RUN / 'extended-run/pueblo-county-intake-revision-independent'
REPO = RUN.parents[1] / 'MasterLegalDatabase'
sys.dont_write_bytecode = True
sys.path.insert(0, str(BASE))
import transaction as tx
from models import Asset, Manifest, Strict
from pydantic import AwareDatetime

class Validation(Strict):
    """Actual final combined test evidence; source custody remains unapplied."""
    status: Literal['PREPARED_NOT_APPLIED']
    recorded_at: AwareDatetime
    tests_passed: Literal[44]
    combined_coverage_percent: float
    line_coverage_percent: float
    branch_coverage_percent: float
    fixture_scope: str
    tests: Asset
    independent_tests: Asset
    test_log: Asset
    coverage: Asset
    code: Asset
    plan: Asset
    canonical_mutations: Literal[0]
    public_requests: Literal[0]
    source_intake_time: None
    current_baseline_unchanged: Literal[True]
    legal_currentness: Literal['not_verified']
    command: list[str]
    started_at: AwareDatetime
    finished_at: AwareDatetime

def write(name, raw):
    p = BASE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    temporary = p.with_name(p.name + '.sealing-tmp')
    temporary.write_bytes(raw)
    temporary.replace(p)

def dump(name, obj):
    write(name, (json.dumps(obj, indent=2) + '\n').encode())

def ref(name):
    raw = (BASE / name).read_bytes()
    return Asset(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))

if __name__ == '__main__':
    assert not (BASE / 'FINAL_MANIFEST.json').exists()
    assert not (BASE / 'execution').exists()
    assert ref('transaction.py').sha256 == 'dcacd5e6de2cb8bc7b3e37a8dcc20b705f97c8e90747768227b4b8b8b478c5f2'
    history = BASE / 'historical/before-final-combined-run'
    history.mkdir(parents=True)
    for name in ['VALIDATION.json', 'VALIDATION.schema.json', 'coverage.json',
                 'focused-tests.log', 'DRY_RUN.json', 'README.md', 'INTENT.schema.json', '.coverage']:
        if (BASE / name).exists():
            shutil.copy2(BASE / name, history / name)
    shutil.copytree(INDEP, BASE / 'independent-final-review')
    shutil.copytree(RUN / 'extended-run/pueblo-county-intake-independent-review',
                    BASE / 'historical/original-blocking-independent-review')
    if (BASE / '.coverage').exists():
        (BASE / '.coverage').unlink()  # Exact initial31-test database preserved above.
    write('seal_county_revision.py', Path(__file__).read_bytes())
    dump('INTENT.schema.json', tx.Intent.model_json_schema())
    dump('VALIDATION.schema.json', Validation.model_json_schema())
    dump('DRY_RUN.json', tx.run(REPO, base=BASE))
    before = {b.repository_path: tx.digest((REPO / b.repository_path).read_bytes())
              for b in tx.load_plan().baseline}
    command = [sys.executable, '-B', '-m', 'pytest', str(BASE / 'test_transaction.py'),
               str(INDEP / 'test_revision_independent.py'), '-q', '-p', 'no:cacheprovider',
               '--basetemp=/private/tmp/geode-pueblo-final44', '--cov=transaction',
               '--cov-branch', '--cov-report=json:' + str(BASE / 'coverage.json'),
               '--cov-report=term-missing']
    started = datetime.now(timezone.utc)
    result = subprocess.run(command, cwd=BASE, env={**os.environ,
        'PYTHONDONTWRITEBYTECODE': '1', 'COVERAGE_FILE': '/private/tmp/geode-pueblo-final44.coverage'},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    finished = datetime.now(timezone.utc)
    write('focused-tests.log', result.stdout)
    assert result.returncode == 0 and b'44 passed' in result.stdout, result.stdout.decode()
    assert before == {b.repository_path: tx.digest((REPO / b.repository_path).read_bytes())
                      for b in tx.load_plan().baseline}
    stats = json.loads((BASE / 'coverage.json').read_bytes())['totals']
    validation = Validation(status='PREPARED_NOT_APPLIED', recorded_at=finished,
        tests_passed=44, combined_coverage_percent=stats['percent_covered'],
        line_coverage_percent=100 * stats['covered_lines'] / stats['num_statements'],
        branch_coverage_percent=100 * stats['covered_branches'] / stats['num_branches'],
        fixture_scope='31 author and13 independent cases executed in temporary synthetic corpora. The unchanged copied independent module is evidence; its execution used the original sibling path in command because its fixture locator is relative. Actual repository used only for read-only preflight. No source HTTP request or intake occurred.',
        tests=ref('test_transaction.py'), independent_tests=ref('independent-final-review/test_revision_independent.py'),
        test_log=ref('focused-tests.log'), coverage=ref('coverage.json'), code=ref('transaction.py'),
        plan=ref('PREPARATION.json'), canonical_mutations=0, public_requests=0,
        source_intake_time=None, current_baseline_unchanged=True, legal_currentness='not_verified',
        command=command, started_at=started, finished_at=finished)
    assert validation.combined_coverage_percent >= 90
    dump('VALIDATION.json', validation.model_dump(mode='json'))
    old = (history / 'README.md').read_text()
    old = old.replace('invokes the existing reconciliation API to append the same ledger suffix and repair its derived report',
        'appends only the same frozen ledger suffix and writes the exact typed report frozen in its immutable intent; generic reconciliation is invoked only read-only')
    old = old.replace('reconciliation also snapshots its control writes through the maintained API',
        'the exact raw, ledger and report preimages are also preserved under repository _SNAPSHOTS/<intake_id>/ before the first canonical write')
    old = old.replace('reconciliation repairs that recognized state', 'the fixed-source writer repairs only that recognized state')
    old = old.replace('pueblo-county-fees-intake-proposal', 'pueblo-county-fees-intake-revision')
    old += '\n## Fixed-source revision disposition\n\nThe original proposal was held because a foreign raw record arriving before generic reconciliation could be added to the ledger/report. Its original bytes and blocking independent reproduction remain historical evidence. This revision never calls generic reconciliation in write mode. It freezes the expected report before mutation and checks exact state again after each raw/ledger/report boundary. Foreign additions reject and remain unpromoted.44 combined temporary-fixture cases passed, including13 independent cases, five interruption boundaries and report tampering. This does not certify global atomicity against arbitrary noncooperating writers. No original source text, legal status or reported acquisition time was changed.\n'
    write('README.md', old.encode())
    dump('FINAL_MANIFEST.schema.json', Manifest.model_json_schema())
    manifest = Manifest(schema_version=1, files=[ref(p.relative_to(BASE).as_posix())
        for p in sorted(BASE.rglob('*')) if p.is_file() and p.name != 'FINAL_MANIFEST.json'])
    # Nested historical FINAL_MANIFEST files are payloads too.
    manifest = Manifest(schema_version=1, files=[ref(p.relative_to(BASE).as_posix())
        for p in sorted(BASE.rglob('*')) if p.is_file() and p != BASE / 'FINAL_MANIFEST.json'])
    dump('FINAL_MANIFEST.json', manifest.model_dump(mode='json'))
    print(json.dumps({'manifest': ref('FINAL_MANIFEST.json').model_dump(),
        'tests_passed':44, 'coverage': validation.combined_coverage_percent,
        'canonical_mutations':0}, indent=2))
