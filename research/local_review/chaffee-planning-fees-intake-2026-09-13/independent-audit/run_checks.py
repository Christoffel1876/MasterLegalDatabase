"""Record exact read-only preflight and isolated temporary-corpus probe results."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent
PREP = ROOT / 'reviewed-preparation'
REPO = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
ORIGINAL = ROOT.parent / 'ptolemy-chaffee-fee-intake-preparation'


class Strict(BaseModel):
    """Reject undeclared fields and type coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """An exact retained file relative to this audit."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Command(Strict):
    """A completed local command, including failures if any."""
    label: str
    argv: list[str]
    cwd: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    exit_code: int
    stdout: Asset
    stderr: Asset


class Checks(Strict):
    """Actual checks; temporary synthetic application is distinct from canonical apply."""
    status: Literal['passed', 'failed']
    reviewer: Literal['Plato']
    completed_at: AwareDatetime
    commands: list[Command]
    repository_pins_before: dict[str, str]
    repository_pins_after: dict[str, str]
    original_packet_pins_before: dict[str, str]
    original_packet_pins_after: dict[str, str]
    repository_metadata_runtime_unchanged: bool
    original_packet_unchanged: bool
    original_execution_directory_created: bool
    canonical_apply_invoked: Literal[False]
    public_requests: Literal[0]
    probe_scope: str


def digest(path: Path) -> str:
    """Stream a hash without changing the input."""
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def asset(path: Path) -> Asset:
    """Bind an actual retained output."""
    return Asset(path=path.relative_to(ROOT).as_posix(), sha256=digest(path),
                 size_bytes=path.stat().st_size)


def run() -> None:
    """Execute once and preserve every command result with before/after pins."""
    if (ROOT / 'CHECKS.json').exists():
        raise ValueError('Do not overwrite the frozen check receipt')
    plan = json.loads((PREP / 'PREPARATION.json').read_bytes())
    names = set(plan['runtime_pins']) | {x['repository_path'] for x in plan['baseline']}
    names.add(plan['legacy_guard']['path'])
    before = {name: digest(REPO / name) for name in sorted(names)}
    packet_before = {p.relative_to(ORIGINAL).as_posix(): digest(p)
                     for p in sorted(ORIGINAL.rglob('*')) if p.is_file()}
    commands = [
        ('portable', [sys.executable, '-B', str(PREP / 'validate_preparation.py')]),
        ('live-preflight', [sys.executable, '-B', str(PREP / 'transaction.py'),
                            '--dry-run', '--root', str(REPO)]),
        ('independent-probes', [sys.executable, '-B', str(ROOT / 'independent_probes.py')]),
    ]
    results = []
    for label, argv in commands:
        start = datetime.now(timezone.utc)
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=120, check=False)
        end = datetime.now(timezone.utc)
        out, err = ROOT / (label + '.stdout'), ROOT / (label + '.stderr')
        with out.open('xb') as stream:
            stream.write(result.stdout)
        with err.open('xb') as stream:
            stream.write(result.stderr)
        results.append(Command(label=label, argv=argv, cwd=str(ROOT), started_at=start,
                               completed_at=end, exit_code=result.returncode,
                               stdout=asset(out), stderr=asset(err)))
    after = {name: digest(REPO / name) for name in sorted(names)}
    packet_after = {p.relative_to(ORIGINAL).as_posix(): digest(p)
                    for p in sorted(ORIGINAL.rglob('*')) if p.is_file()}
    passed = all(r.exit_code == 0 for r in results) and before == after
    passed = passed and packet_before == packet_after and not (ORIGINAL / 'execution').exists()
    record = Checks(status='passed' if passed else 'failed', reviewer='Plato',
                    completed_at=datetime.now(timezone.utc), commands=results,
                    repository_pins_before=before, repository_pins_after=after,
                    original_packet_pins_before=packet_before,
                    original_packet_pins_after=packet_after,
                    repository_metadata_runtime_unchanged=before == after,
                    original_packet_unchanged=packet_before == packet_after,
                    original_execution_directory_created=(ORIGINAL / 'execution').exists(),
                    canonical_apply_invoked=False, public_requests=0,
                    probe_scope='Eight independent cases; only the disclosed author fixture '
                    'constructor is reused to create a one-record synthetic temporary corpus. '
                    'Exact selected PDF/custody copies are used; application occurs only there.')
    encoded = record.model_dump_json(indent=2) + '\n'
    schema = Checks.model_json_schema()
    jsonschema.validate(json.loads(encoded), schema)
    with (ROOT / 'CHECKS.json').open('x') as stream:
        stream.write(encoded)
    with (ROOT / 'CHECKS.schema.json').open('x') as stream:
        stream.write(json.dumps(schema, indent=2) + '\n')
    sys.stdout.write(record.status + '\n')


if __name__ == '__main__':
    run()
