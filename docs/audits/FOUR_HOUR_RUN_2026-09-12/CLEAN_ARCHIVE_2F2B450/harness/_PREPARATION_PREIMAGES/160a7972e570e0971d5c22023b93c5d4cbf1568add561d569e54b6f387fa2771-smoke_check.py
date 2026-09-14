"""Prepared-only offline smoke harness for an explicitly supplied clean Git archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ORIGINAL = Path('/Users/mcoors/Documents/Project Geode')
NATIVE = [
    ('grand-junction-fire-fees-atlas-directed', 'rows', 57, 'CO-MUNICIPAL-GRAND_JUNCTION'),
    ('greeley-building-fees-sd008-06', 'entries', 19, 'CO-MUNICIPAL-GREELEY'),
    ('weld-ehs-fees-2026-atlas-directed', 'rows', 137, 'CO-COUNTY-WELD'),
    ('greeley-development-impact-fee-memo-sd008-07', 'rows', 30, 'CO-MUNICIPAL-GREELEY'),
    ('greeley-water-sewer-proposed-pif-notice-sd008-08', 'rows', 8, 'CO-MUNICIPAL-GREELEY'),
    ('colorado-springs-construction-fees-atlas-directed', 'rows', 128,
     'CO-MUNICIPAL-COLORADO_SPRINGS'),
    ('el-paso-boh-ehs-fees-sd011', 'rows', 65, 'CO-COUNTY-EL_PASO'),
]
BOOTSTRAP = '''import runpy,sys
from pathlib import Path
root,kind,target,*args=sys.argv[1:]
sys.path.insert(0,root)
sys.argv=[target,*args]
if kind=="script":runpy.run_path(str(Path(root)/target),run_name="__main__")
else:runpy.run_module(target,run_name="__main__",alter_sys=True)
'''


class Strict(BaseModel):
    """Keep preparation and measured execution records distinct."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Check(Strict):
    id: str
    command: list[str]
    started_at: str
    finished_at: str
    expected_exit: int
    actual_exit: int | None
    timed_out: bool
    stdout: Asset
    stderr: Asset
    passed: bool
    errors: list[str]
    evidence_paths_checked: int
    observations: list[str]


class RunReceipt(Strict):
    """A receipt exists only after an operator actually invokes the harness."""
    status: Literal['passed','failed','blocked']
    started_at: str
    finished_at: str
    archive_root: str
    output_root: str
    commit_label: str
    harness: Asset
    interpreter: str
    isolation: Literal['sandbox_exec','unisolated_explicit']
    sandbox_profile: Asset | None
    isolation_scope: list[str]
    expected_inventory_sources: int
    expected_reviewed_sources: int
    checks: list[Check]
    archive_evidence_paths: list[str]
    public_activity_requested: Literal[False] = False
    watch_execution_requested: Literal[False] = False
    scheduling_requested: Literal[False] = False
    network_denied_for_child_processes: bool
    limitations: list[str]


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def asset(path: Path, base: Path | None = None) -> Asset:
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return Asset(path=str(path.relative_to(base)) if base else str(path),
                 sha256=digest, size_bytes=path.stat().st_size)


def save(path: Path, data: bytes) -> None:
    """Write a new report atomically, refusing reuse of an earlier execution path."""
    if path.exists():
        raise ValueError('Refusing to overwrite execution evidence')
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('xb') as handle:
        handle.write(data)
    os.replace(temporary, path)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def evidence_paths(data: Any, root: Path) -> set[str]:
    """Check active structured evidence paths, not quoted historical custody strings."""
    found: set[str] = set()
    names = {'pdf_path','review_path','native_path','page_image_path','candidate_path',
             'provenance_path','access_receipt_path','reconciliation_path',
             'superseding_disposition_path'}
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, str) and (key in names or
                        (key == 'path' and 'sha256' in value and 'size_bytes' in value)):
                    path = Path(child)
                    ensure(path.is_absolute(), 'Evidence path is not absolute: ' + child)
                    ensure(not any(p.is_symlink() for p in [path,*path.parents]),
                           'Symlinked evidence path: ' + child)
                    ensure(path.is_relative_to(root) and path.is_file(),
                           'Evidence does not resolve inside archive: ' + child)
                    found.add(child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)
    ensure(bool(found), 'No structured evidence paths were checked')
    return found


def flags(data: dict) -> None:
    ensure(data['legal_currentness'] == 'not_verified' and data['answer_safe'] is False,
           'Currentness/answer-safety changed')
    for key in ['adoption_date','effective_date','source_edition_date']:
        ensure(data.get(key) is None, 'A source date was promoted: ' + key)


def native_check(data: dict, index: int) -> None:
    source_id, field, count, authority = NATIVE[index]
    flags(data)
    ensure(data['status'] == 'matched' and data['evidence_verified'], 'Native evidence not matched')
    ensure(len(data[field]) == count, f'{source_id}: incorrect source row/entry count')
    ensure(data.get('authority_id', data['source'].get('authority_id')) == authority,
           'Authority changed')
    if index == 1:
        row = next(e for e in data['entries'] if e['entry_id'] == 'other_1')
        ensure('minimum charge, two hours' in row['statement']['text'] and row['footnotes'],
               'Greeley minimum/footnote lost')
        ensure(data['source']['original_acquisition_time'] is None, 'Receipt became acquisition')
    elif index == 2:
        blank = [r for r in data['rows'] if r['fee'] is None]
        ensure(len(blank) == 1 and blank[0]['fee_cell_status'] == 'visibly_blank',
               'Weld blank fee changed')
        ensure(len(data['page_context']) == 3, 'Weld page conditions lost')
    elif index in (3,4):
        ensure(data['context'] and data['context_tables'] and data['date_statements'],
               'Greeley grid context lost')
        if index == 4:
            ensure('assuming they are adopted' in data['mandatory_qualification'],
                   'Proposed PIF adoption condition lost')
    elif index == 5:
        ensure(set(data['global_context_ids']) ==
               {'GENERAL-PLAN-REVIEW','IMPLEMENTATION','OTHER-SCHEDULE','P4-MISC-01'},
               'Springs global implementation/fee context lost')
        ensure(data['source']['canonical_intake_verified'], 'Springs intake binding failed')
    elif index == 6:
        rows = {r['row_id']:r for r in data['rows']}
        context = {c['context_id']:c for c in data['context']}
        ensure(len(context) == 37, 'EHS complete context lost')
        ensure(rows['R031']['fee'] == '$211.50 in 2024 ($368 in 2025)' and
               rows['R032']['fee'] == '$281.00 in 2024', 'EHS year-specific fees changed')
        ensure(rows['R056']['fee'] == 'Per Section 25-4-1607 C.R.S.', 'Statutory fee inferred')
        ensure('STAR' in rows['R020']['linked_context'] and
               'except as otherwise provided by Section 2' in context['B']['text'] and
               'No fees will be assessed' in context['OTHER2']['text'], 'EHS exception lost')


def scanned_check(data: dict) -> None:
    flags(data)
    matches = data['matches']
    ensure(data['status'] == 'matched_rows' and
           [m['fee_row']['row']['id'] for m in matches] ==
           ['P1-ENG-01','P3-ENG-14','P3-ENG-19','P4-ENG-01'], 'Erosion row scope differs')
    ensure([m['fee_row']['row']['cells'][1]['text'] for m in matches] ==
           ['$104.00','$4,073.00','$3,076.00','$3,252.00'], 'Erosion fee association differs')
    context = data['mandatory_context']
    ensure(context['global_footnote']['row']['id'] == 'FN-01' and
           len(context['general_notes']) == 3, 'Scanned global notes lost')
    ensure(matches[1]['unresolved_clipped_label'], 'Clipped source tail silently completed')
    ensure(data['source']['native_text_bytes'] == 0 and
           data['source']['verified_http_acquisition_at'] is None, 'Native/custody invented')


def crs_check(data: dict) -> None:
    flags(data)
    ensure(data['status'] == 'matched' and data['research_only'], 'CRS research scope differs')
    section = data['section']
    ensure(section['section_id'] == 'CRS-1-1-102' and len(section['paragraphs']) == 2,
           'CRS section/paragraph scope differs')
    first = section['paragraphs'][0]
    ensure([f['physical_page'] for f in first['fragments']] == [4,5] and
           first['text'] == ''.join(f['text'] for f in first['fragments']),
           'CRS page4-to5 continuation lost')
    ensure([f['role'] for f in section['ancillary']] ==
           ['source_history_note','editors_note','cross_references'], 'CRS notes misclassified')
    ensure(data['custody']['total_pdf_pages'] == 1008 and
           data['custody']['reviewed_physical_pages'] == [1,2,3,4,5,6], 'CRS review scope expanded')


def main() -> int:
    """Run only the listed read-only APIs after explicit operator invocation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    parser.add_argument('--commit-label', required=True)
    parser.add_argument('--isolation', choices=['required','none'], default='required')
    parser.add_argument('--expected-sources', type=int, default=61)
    parser.add_argument('--expected-reviewed', type=int, default=22)
    parser.add_argument('--max-seconds', type=int, default=600)
    args = parser.parse_args()
    root, output = args.archive_root.absolute(), args.output.absolute()
    ensure(not any(p.is_symlink() for p in [root,output,*root.parents,*output.parents]),
           'Use ordinary absolute archive/output paths')
    ensure(root.is_dir() and not root.is_relative_to(ORIGINAL),
           'Archive must be outside the original workspace')
    ensure(not output.exists() and not output.is_relative_to(root) and
           not output.is_relative_to(ORIGINAL), 'Output must be a new external directory')
    ensure(1 <= args.max_seconds <= 900, 'Total runtime bound must be 1..900 seconds')
    output.mkdir(parents=True)
    for name in ['outputs','scratch','home']:
        (output/name).mkdir()
    started, deadline = stamp(), time.monotonic()+args.max_seconds
    sandbox = shutil.which('sandbox-exec') if args.isolation == 'required' else None
    profile = None
    if sandbox:
        profile = output/'read-only-test.sb'
        # The profile applies only to these child processes; no persistent settings change.
        save(profile, ('(version 1)\n(allow default)\n(deny network*)\n'
             f'(deny file-read* (subpath {json.dumps(str(ORIGINAL))}))\n'
             f'(deny file-write* (subpath {json.dumps(str(ORIGINAL))}))\n'
             f'(deny file-write* (subpath {json.dumps(str(root))}))\n').encode())
    checks: list[Check] = []
    paths: set[str] = set()
    environment = {'PATH':os.defpath,'HOME':str(output/'home'),'TMPDIR':str(output/'scratch'),
                   'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','LANG':'en_US.UTF-8'}

    def invoke(name: str, kind: str, target: str, arguments: list[str],
               validate: Any = None, expected_exit: int = 0, path_check: bool = False) -> None:
        ensure('--execute' not in arguments and '--write' not in arguments,
               'Mutating/watch execution is forbidden')
        command = [str(args.python),'-I','-B','-c',BOOTSTRAP,str(root),kind,target,*arguments]
        if sandbox:
            command = [sandbox,'-f',str(profile),*command]
        start, errors, timed_out, code, stdout, stderr = stamp(), [], False, None, b'', b''
        found: set[str] = set()
        remaining = deadline-time.monotonic()
        if args.isolation == 'required' and not sandbox:
            errors.append('sandbox-exec unavailable; isolated execution was not attempted')
        elif remaining <= 0:
            errors.append('Overall deadline exhausted; command not attempted')
        else:
            try:
                process = subprocess.Popen(command,cwd=output,env=environment,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
                try:
                    stdout,stderr = process.communicate(timeout=min(180,remaining))
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    stdout,stderr = process.communicate()
                    timed_out = True
                code = process.returncode
                ensure(not timed_out and code == expected_exit, 'Exit status/timeout differs')
                if validate is not None:
                    data = json.loads(stdout)
                    validate(data)
                    if path_check:
                        found = evidence_paths(data,root)
                        paths.update(found)
            except (OSError,ValueError,KeyError,TypeError,StopIteration) as error:
                errors.append(type(error).__name__+': '+str(error))
        out, err = output/'outputs'/f'{name}.stdout', output/'outputs'/f'{name}.stderr'
        save(out,stdout);save(err,stderr)
        checks.append(Check(id=name,command=command,started_at=start,finished_at=stamp(),
            expected_exit=expected_exit,actual_exit=code,timed_out=timed_out,
            stdout=asset(out,output),stderr=asset(err,output),passed=not errors,errors=errors,
            evidence_paths_checked=len(found),observations=[]))
        print(name, 'PASS' if not errors else 'FAIL', flush=True)

    native_script = 'scripts/research_source_lookup.py'
    for i,(source,_,_,_) in enumerate(NATIVE):
        invoke(f'native-{i+1}','script',native_script,
            ['--root',str(root),'--source-id',source,'--list-rows','--format','json'],
            lambda d,i=i:native_check(d,i),path_check=True)
    invoke('scanned-erosion','script','scripts/research_scanned_fee_lookup.py',
        ['--root',str(root),'--source-id','el-paso-planning-fees-sd011','--query','Erosion',
         '--format','json'],scanned_check,path_check=True)
    invoke('crs-102','script','scripts/crs_source_lookup.py',
           ['--section','CRS-1-1-102'],crs_check)
    invoke('inventory-check','module','geode.pipeline.manual_review_inventory',
           ['--root',str(root),'--check'])
    try:
        inventory=json.loads((root/'research/local_review/manual-source-review-inventory-2026-09-11/inventory.json').read_bytes())
        ensure(len(inventory['sources']) == args.expected_sources and
               inventory['rows_with_review'] == args.expected_reviewed and
               inventory['rows_without_review'] == args.expected_sources-args.expected_reviewed,
               'Inventory count mismatch')
        flags(inventory)
        ensure(inventory['coverage_promotion'] is False, 'Inventory coverage promotion')
    except (OSError,ValueError,KeyError) as error:
        checks[-1].passed=False;checks[-1].errors.append(str(error))

    def watch(data: dict) -> None:
        ensure(data['manual_pdf_records'] == args.expected_sources and
               data['locally_hash_verified_pdf_originals'] == args.expected_sources and
               data['unavailable_or_mismatch'] == [], 'Watch original availability differs')
        ensure(data['configured_sources'] == 2 and
               data['unselected_manual_pdf_records'] == args.expected_sources-2 and
               data['configured_source_ids'] == [
                   'colorado-springs-code-services-fees-2015-atlas-directed',
                   'colorado-springs-construction-fees-atlas-directed'], 'Watch selection changed')
        ensure(data['recurring_deployment'] == 'not_deployed_by_this_feature' and
               data['legal_currentness'] == 'not_verified', 'Watch status promoted')
    invoke('watch-readiness','module','geode.pipeline.manual_source_watch',
           ['--root',str(root)],watch)

    def refusal(data: dict) -> None:
        ensure(data['status'] == 'refused_current_law' and
               not data.get('rows') and not data.get('entries') and not data.get('matches'),
               'Current-law refusal exposed rows')
    invoke('native-current-law-refusal','script',native_script,
        ['--root',str(root),'--source-id',NATIVE[-1][0],'--query','OWTS',
         '--mode','current-law','--format','json'],refusal,2)
    invoke('scanned-current-law-refusal','script','scripts/research_scanned_fee_lookup.py',
        ['--root',str(root),'--source-id','el-paso-planning-fees-sd011','--query','Erosion',
         '--mode','current-law','--format','json'],refusal,2)
    invoke('crs-current-law-refusal','script','scripts/crs_source_lookup.py',
        ['--section','CRS-1-1-102','--mode','current_law'],
        lambda d:ensure(d['status']=='refused_mode' and d['section'] is None,
                        'CRS current-law refusal failed'),2)
    status = 'passed' if all(c.passed for c in checks) else 'failed'
    if args.isolation == 'required' and not sandbox:
        status = 'blocked'
    receipt = RunReceipt(status=status,started_at=started,finished_at=stamp(),
        archive_root=str(root),output_root=str(output),commit_label=args.commit_label,
        harness=asset(Path(__file__)),interpreter=str(args.python),
        isolation='sandbox_exec' if args.isolation=='required' else 'unisolated_explicit',
        sandbox_profile=asset(profile,output) if profile else None,
        isolation_scope=['Child process network denied when sandbox-exec is used.',
            'Original Project Geode subtree read/write denied; archive writes denied in isolated mode.',
            'Archive/output/interpreter/runtime reads remain available; unrelated /private/tmp is not globally denied.',
            'All active native/scanned output evidence paths must be ordinary files beneath the supplied archive.'],
        expected_inventory_sources=args.expected_sources,expected_reviewed_sources=args.expected_reviewed,
        checks=checks,archive_evidence_paths=sorted(paths),network_denied_for_child_processes=bool(sandbox),
        limitations=['No currentness, legal applicability or completeness claim.',
            'Commit label is supplied by the operator; this harness does not call Git or authenticate the archive.',
            'Python and declared third-party dependencies are external runtime requirements, not vendored project evidence.',
            'Historical path strings in custody notes are retained; they are not treated as active evidence references.',
            'Unisolated mode, if explicitly chosen, proves structural/CLI relocation only and makes no network/filesystem isolation claim.'])
    raw=(receipt.model_dump_json(indent=2)+'\n').encode()
    RunReceipt.model_validate_json(raw)
    save(output/'RUN_RECEIPT.json',raw)
    print('receipt',output/'RUN_RECEIPT.json',status)
    return 0 if status=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
