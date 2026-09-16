"""Record one actual installed-repository full-suite execution and its exact outputs."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

from pydantic import BaseModel, ConfigDict

ROOT = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
OUT = ROOT / 'docs/audits/FOUR_HOUR_RUN_2026-09-12/CAPTURED_BUFFER_INTEGRATION'
PYTHON = '/private/tmp/geode-status-venv/bin/python'


class Run(BaseModel):
    """Exact command, execution interval and observed status; no inferred test success."""
    model_config = ConfigDict(extra='forbid')
    started_at: datetime
    finished_at: datetime | None = None
    command: list[str]
    status: str
    exit_code: int | None = None
    log_sha256: str | None = None
    coverage_sha256: str | None = None


def save(path: Path, raw: bytes) -> None:
    """Write a new receipt atomically without replacing earlier results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    if path.exists() or temp.exists():
        raise ValueError('Existing result path')
    with temp.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def main() -> None:
    """Run the full required test suite using only the installed maintained files."""
    if hashlib.sha256((ROOT / 'scripts/research_source_lookup.py').read_bytes()).hexdigest() != '1f4da2ec117996c21a2676bdd82226018ecf4ad0e583297c1f52ece43d1ffe55':
        raise ValueError('Expected reviewed captured-buffer implementation is not installed')
    OUT.mkdir()
    command = [PYTHON, '-B', '-m', 'pytest', 'tests/', '-q', '-p', 'no:cacheprovider',
        '--basetemp=/private/tmp/geode-captured-buffer-integration', '--cov=geode',
        '--cov=scripts.research_source_lookup', '--cov-branch',
        '--cov-report=json:' + str(OUT / 'coverage.json'), '--cov-report=term-missing']
    started = datetime.now(timezone.utc)
    begin = Run(started_at=started, command=command, status='running')
    save(OUT / 'RUN.schema.json', (json.dumps(Run.model_json_schema(), indent=2) + '\n').encode())
    save(OUT / 'START.json', (begin.model_dump_json(indent=2) + '\n').encode())
    save(OUT / Path(__file__).name, Path(__file__).read_bytes())
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               COVERAGE_FILE='/private/tmp/geode-captured-buffer-integration.coverage')
    with (OUT / 'pytest.log').open('xb') as output:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=output,
                                stderr=subprocess.STDOUT, check=False)
    log = (OUT / 'pytest.log').read_bytes()
    coverage = OUT / 'coverage.json'
    final = Run(started_at=started, finished_at=datetime.now(timezone.utc), command=command,
        status='passed' if result.returncode == 0 else 'failed', exit_code=result.returncode,
        log_sha256=hashlib.sha256(log).hexdigest(),
        coverage_sha256=hashlib.sha256(coverage.read_bytes()).hexdigest()
            if coverage.exists() else None)
    save(OUT / 'RESULT.json', (final.model_dump_json(indent=2) + '\n').encode())
    print(final.model_dump_json(indent=2))
    print(log.decode(errors='replace')[-2200:])
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
