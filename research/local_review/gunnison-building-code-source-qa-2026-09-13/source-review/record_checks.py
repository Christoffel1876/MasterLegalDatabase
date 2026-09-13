"""Record focused local verification; no source, canonical or network mutation."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Literal
from models import Asset, Strict
from prepare import ROOT, asset, write


class Check(Strict):
    """Actual local command outcome and exact retained output."""
    name: str
    started_at: str
    completed_at: str
    command: list[str]
    cwd: str
    returncode: int
    stdout: Asset
    stderr: Asset


class Validation(Strict):
    """A focused check receipt, distinct from visual source judgments."""
    status: Literal['pass']
    source_qa: Asset
    input_manifest: Asset
    checks: list[Check]
    coverage: Asset
    branch_inclusive_percent: float
    public_requests: Literal[0]
    canonical_mutations: Literal[0]
    limits: list[str]


def main() -> None:
    """Run final focused tests with outputs outside the closed input package."""
    python = '/private/tmp/geode-status-venv/bin/python'
    environment = dict(os.environ)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    with tempfile.TemporaryDirectory(prefix='gunnison-code-qa-check-') as temporary:
        work = Path(temporary)
        environment['COVERAGE_FILE'] = str(work / 'coverage.db')
        coverage = work / 'coverage.json'
        command = [python, '-B', '-m', 'pytest', str(ROOT / 'test_validate_qa.py'),
                   '-q', '-p', 'no:cacheprovider', '--cov=validate_qa', '--cov=crop_tools',
                   '--cov=models', '--cov=process_models', '--cov-branch',
                   '--cov-report=term-missing', f'--cov-report=json:{coverage}']
        input_manifest = asset(ROOT / 'FINAL_MANIFEST.json')
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(command, cwd=work, env=environment,
                                capture_output=True, timeout=180)
        completed = datetime.now(timezone.utc).isoformat()
        write(ROOT / 'checks/focused-tests.stdout', result.stdout)
        write(ROOT / 'checks/focused-tests.stderr', result.stderr)
        write(ROOT / 'checks/coverage.json', coverage.read_bytes())
        check = Check(name='focused adversarial checks plus full source rerender',
                      started_at=started, completed_at=completed, command=command,
                      cwd=str(work), returncode=result.returncode,
                      stdout=asset(ROOT / 'checks/focused-tests.stdout'),
                      stderr=asset(ROOT / 'checks/focused-tests.stderr'))
        if result.returncode:
            write(ROOT / 'checks/failure.json', (check.model_dump_json(indent=2) + '\n').encode())
            raise RuntimeError('Focused verification failed; exact output retained')
        percent = json.loads(coverage.read_bytes())['totals']['percent_covered']
        assert percent >= 90, percent
        record = Validation(status='pass', source_qa=asset(ROOT / 'SOURCE_QA.json'),
                            input_manifest=input_manifest, checks=[check],
                            coverage=asset(ROOT / 'checks/coverage.json'),
                            branch_inclusive_percent=percent, public_requests=0,
                            canonical_mutations=0,
                            limits=['Tests check integrity and semantic binding, not independent '
                                    'visual truth, execution identity or legal currentness.',
                                    'The input inventory was sealed before check outputs were '
                                    'added; the final closed inventory also includes these '
                                    'additive receipts.'])
        write(ROOT / 'VALIDATION.json', (record.model_dump_json(indent=2) + '\n').encode())
        write(ROOT / 'VALIDATION.schema.json',
              (json.dumps(Validation.model_json_schema(), indent=2) + '\n').encode())


if __name__ == '__main__':
    main()
