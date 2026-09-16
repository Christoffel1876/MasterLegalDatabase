"""Run only focused inventory tests against private copied source/metadata inputs."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
from pydantic import AwareDatetime, Field

from models import Asset, Strict

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2] / 'MasterLegalDatabase'
INVENTORY = Path('research/local_review/manual-source-review-inventory-2026-09-11')


class TestRun(Strict):
    """Actual focused execution; no production files are changed."""
    started_at: AwareDatetime
    completed_at: AwareDatetime
    command: list[str]
    cwd: str
    environment_overrides: dict[str, str]
    exit_code: int
    temporary_directory_removed: bool
    production_writes: int = Field(ge=0, le=0)


def collect(value: Any) -> set[str]:
    """Collect exact artifact references in typed plan/source records."""
    result = set()
    if isinstance(value, dict):
        if {'path', 'sha256', 'size_bytes'} <= value.keys():
            result.add(value['path'])
        for child in value.values():
            result |= collect(child)
    elif isinstance(value, list):
        for child in value:
            result |= collect(child)
    return result


def run() -> None:
    """Copy only required inputs and historical inventory fixtures; isolate every test write."""
    if (BASE / 'STAGED_TEST_RUN.json').exists():
        raise ValueError('Preserve the prior test receipt before another run')
    stage = Path(tempfile.mkdtemp(dir='/private/tmp', prefix='plato-inventory70-'))
    shutil.copytree(ROOT / 'geode', stage / 'geode', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT / INVENTORY, stage / INVENTORY)
    for relative in [
        'docs/audits/ONE_HOUR_CONTINUATION_2026-09-11/inventory-at-first-checkpoint',
        'docs/audits/FOUR_HOUR_RUN_2026-09-12/EL_PASO_INTAKE/inventory-after',
    ]:
        shutil.copytree(ROOT / relative, stage / relative)
    plan = json.loads((BASE / 'proposed/join-plan.json').read_bytes())
    data = json.loads((BASE / 'proposed/inventory.json').read_bytes())
    for name in collect(plan) | {row['source']['path'] for row in data['sources']}:
        src, dst = ROOT / name, stage / name
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    snapshot = stage / INVENTORY / '_SNAPSHOTS/BEFORE_FINAL_FEE_CODE_2026-09-13'
    shutil.copytree(BASE / 'preimages', snapshot)
    for name in ['join-plan.json', 'inventory.json', 'inventory.schema.json', 'README.md']:
        shutil.copyfile(BASE / 'proposed' / name, stage / INVENTORY / name)
    shutil.copyfile(BASE / 'proposed/manual_review_inventory.py',
                    stage / 'geode/pipeline/manual_review_inventory.py')
    (stage / 'tests').mkdir()
    shutil.copyfile(BASE / 'proposed/test_manual_review_inventory.py',
                    stage / 'tests/test_manual_review_inventory.py')
    env = dict(os.environ)
    overrides = {'PYTHONPATH': str(stage), 'PYTHONDONTWRITEBYTECODE': '1',
                 'COVERAGE_FILE': str(stage / '.coverage')}
    env.update(overrides)
    command = [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               'tests/test_manual_review_inventory.py',
               '--cov=geode.pipeline.manual_review_inventory', '--cov-branch',
               '--cov-report=json:' + str(BASE / 'coverage.json'), '--cov-report=term']
    start = datetime.now(timezone.utc)
    result = subprocess.run(command, cwd=stage, env=env, capture_output=True, check=False,
                            timeout=180)
    end = datetime.now(timezone.utc)
    with (BASE / 'focused-tests.log').open('xb') as handle:
        handle.write(result.stdout + result.stderr)
    shutil.rmtree(stage)
    receipt = TestRun(started_at=start, completed_at=end, command=command, cwd=str(stage),
                      environment_overrides=overrides, exit_code=result.returncode,
                      temporary_directory_removed=not stage.exists(), production_writes=0)
    raw = receipt.model_dump_json(indent=2) + '\n'
    schema = TestRun.model_json_schema()
    jsonschema.validate(json.loads(raw), schema)
    with (BASE / 'STAGED_TEST_RUN.schema.json').open('x') as handle:
        handle.write(json.dumps(schema, indent=2) + '\n')
    with (BASE / 'STAGED_TEST_RUN.json').open('x') as handle:
        handle.write(raw)
    sys.stdout.write('Focused exit ' + str(result.returncode) + '\n')


if __name__ == '__main__':
    run()
