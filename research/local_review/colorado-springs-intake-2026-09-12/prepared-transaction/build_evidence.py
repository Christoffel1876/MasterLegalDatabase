"""Capture final preparation checks; never apply to the actual repository."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).absolute().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(BASE))
import transaction as tx
from package_models import Asset, Baseline, Invocation, Package, Validation


def asset(path: Path, label: str | None = None) -> Asset:
    """Bind ordinary bytes by streaming SHA-256."""
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return Asset(path=label or path.relative_to(BASE).as_posix(), sha256=digest,
                 size_bytes=path.stat().st_size)


def save(name: str, value: object) -> None:
    """Write new typed/schema outputs, refusing overwrite."""
    raw = (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode()
    target=BASE/name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ValueError('Refusing evidence overwrite: '+name)
    temporary=target.with_suffix(target.suffix+'.tmp')
    temporary.write_bytes(raw)
    os.replace(temporary, target)


def run(name: str, argv: list[str], env: dict) -> Invocation:
    """Preserve the exact completed command output and actual observation interval."""
    start=datetime.now(timezone.utc)
    result=subprocess.run(argv,cwd='/private/tmp',env=env,capture_output=True,timeout=120)
    end=datetime.now(timezone.utc)
    outputs=[]
    for ext, data in [('stdout',result.stdout),('stderr',result.stderr)]:
        path=BASE/'validation'/f'{name}.{ext}.txt'
        with path.open('xb') as handle: handle.write(data)
        outputs.append(asset(path))
    if result.returncode: raise ValueError(f'{name} failed: '+result.stderr.decode()[-1000:])
    return Invocation(argv=argv,cwd='/private/tmp',started_at=start,completed_at=end,
                      exit_code=result.returncode,stdout=outputs[0],stderr=outputs[1])


def main() -> None:
    """Capture tests and dry-run; check real baselines and build the closed inventory."""
    (BASE/'validation').mkdir(exist_ok=True)
    if (BASE/'execution').exists(): raise ValueError('Actual execution unexpectedly exists')
    before=[asset(tx.DEFAULT_ROOT/p,p) for p in tx.TARGETS]
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',
         'COVERAGE_FILE':'/private/tmp/csfd-tx-recorded.coverage'}
    python=sys.executable
    tests=run('focused-tests',[python,'-B','-m','pytest',str(BASE/'test_transaction.py'),
       '-q','-p','no:cacheprovider','--basetemp=/private/tmp/csfd-tx-recorded-tests',
       '--cov=transaction','--cov-branch','--cov-report=term-missing',
       '--cov-report=json:'+str(BASE/'validation/coverage.json')],env)
    dry=run('actual-dry-run',[python,'-I','-B',str(BASE/'transaction.py'),
                            '--root',str(tx.DEFAULT_ROOT),'--dry-run'],env)
    after=[asset(tx.DEFAULT_ROOT/p,p) for p in tx.TARGETS]
    if (BASE/'execution').exists(): raise ValueError('Actual execution unexpectedly created')
    cov=json.loads((BASE/'validation/coverage.json').read_bytes())
    stamp=datetime.now(timezone.utc)
    validation=Validation(schema_version=1,status='prepared_not_applied',frozen_at=stamp,
        implementation=asset(BASE/'transaction.py'),tests=asset(BASE/'test_transaction.py'),
        focused_tests=tests,tests_passed=56,test_warnings=5,
        coverage=asset(BASE/'validation/coverage.json'),
        branch_inclusive_coverage_percent=cov['totals']['percent_covered'],
        coverage_scope='56 focused tests, including actual read-only two-record preflight',
        actual_dry_run=dry,baselines=[Baseline(before=b,after=a) for b,a in zip(before,after)],
        approved_preparation_manifest=asset(tx.PREP/'FINAL_MANIFEST.json'),
        expected_source_ids=[s['proposed_record_id'] for s in tx.load_plan(tx.DEFAULT_ROOT).sources],
        baseline_raw_records=59,baseline_ledger_records=60,expected_raw_after=61,
        expected_ledger_after=62,
        missing_historical_original='MSI-20260707T221329208329Z-EO-2019-007',
        real_repository_apply_performed=False,real_execution_directory_exists=False,
        legal_currentness='not_verified',answer_safe=False,
        full_corpus_validation='not_run_by_this_subtask',
        tested_recovery_scope='process_interruption_and_deterministic_replay',
        power_loss_durability_verified=False)
    save('VALIDATION.json',validation.model_dump(mode='json'))
    save('VALIDATION.schema.json',Validation.model_json_schema())
    save('INTENT.schema.json',tx.Intent.model_json_schema())
    save('RECEIPT.schema.json',tx.Receipt.model_json_schema())
    save('NewRecord.schema.json',tx.NewRecord.model_json_schema())
    save('FINAL_MANIFEST.schema.json',Package.model_json_schema())
    files=[]
    for path in sorted(BASE.rglob('*')):
        if path.is_symlink(): raise ValueError('Symlink')
        if path.is_file() and path.name not in ['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json']:
            files.append(asset(path))
    # Nested preparation's two manifest files are included; only root self-files excluded.
    indexed={a.path:a for a in files}
    for path in sorted(BASE.rglob('FINAL_MANIFEST*')):
        if path.parent != BASE and path.is_file(): indexed[path.relative_to(BASE).as_posix()]=asset(path)
    package=Package(schema_version=1,status='prepared_not_applied',frozen_at=stamp,
        files=[indexed[k] for k in sorted(indexed)],excluded_prefixes=['execution/'],
        excluded_files=['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'],
        legal_currentness='not_verified',answer_safe=False)
    save('FINAL_MANIFEST.json',package.model_dump(mode='json'))


if __name__=='__main__': main()
