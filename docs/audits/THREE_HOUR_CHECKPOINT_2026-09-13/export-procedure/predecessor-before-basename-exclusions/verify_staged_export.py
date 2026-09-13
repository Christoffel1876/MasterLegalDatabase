"""Verify and export an already staged index; never stage, fetch, or run live watches."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import threading

import jsonschema
from pydantic import BaseModel

from models import Asset, Command, Digest, ExportAsset, IndexEntry, Receipt, Scan

USER_PATHS = {'docs/audits/PROJECT_STATUS_2026-09-09.md', 'geode/schemas/models 2.py'}
MAX_FILES = 25000
MAX_BLOB = 500_000_000
MAX_TOTAL = 4_000_000_000
MAX_SECONDS = 240
RUNTIME = '.geode_runtime/manual_source_watch_ci/staged-offline/'


def now() -> datetime:
    """Return actual UTC process time."""
    return datetime.now(timezone.utc)


def digest(raw: bytes) -> Digest:
    """Return an exact byte digest."""
    return Digest(sha256=sha256(raw).hexdigest(), size_bytes=len(raw))


def safe_path(value: str) -> PurePosixPath:
    """Reject aliases, absolute paths, Git internals and parent traversal."""
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or path.as_posix() != value
            or any(part.casefold() in {'..', '.', '.git'} for part in path.parts)
            or '\\' in value or '\x00' in value):
        raise ValueError('Unsafe index or manifest path: '+repr(value))
    return path


def parse_index(raw: bytes) -> dict[str, IndexEntry]:
    """Parse exact NUL-delimited stage entries and reject ambiguity."""
    entries: dict[str, IndexEntry] = {}
    folded: set[str] = set()
    if not raw.endswith(b'\0'):
        raise ValueError('Unterminated index listing')
    for line in raw[:-1].split(b'\0'):
        header, name = line.split(b'\t', 1)
        mode, oid, stage = header.decode('ascii').split(' ')
        path = name.decode('utf-8')
        safe_path(path)
        if stage != '0' or path in entries or path.casefold() in folded:
            raise ValueError('Unmerged, duplicate or case-aliased index entry')
        if mode not in {'100644', '100755'}:
            raise ValueError('Non-regular index mode is outside this procedure')
        entries[path] = IndexEntry(path=path, mode=mode, oid=oid)
        folded.add(path.casefold())
    if not entries or len(entries) > MAX_FILES:
        raise ValueError('Index entry count outside bound')
    if {path.casefold() for path in USER_PATHS} & folded:
        raise ValueError('Excluded user file is in the staged index')
    return entries


def compare_scan(scan: Scan, entries: dict[str, IndexEntry], changed: bytes) -> None:
    """Reject missing scan members, unexpected staging, and user-file inclusion."""
    selected = [asset.path for asset in scan.files]
    if len(selected) != len(set(selected)) or len({p.casefold() for p in selected}) != len(selected):
        raise ValueError('Duplicate or case-aliased scan member')
    for path in selected:
        safe_path(path)
    if set(scan.excluded_user_paths) != USER_PATHS or {p.casefold() for p in USER_PATHS} & {p.casefold() for p in selected}:
        raise ValueError('User exclusions differ')
    if set(selected) - set(entries):
        raise ValueError('Expected scan files are absent from index')
    changed_paths = {name.decode('utf-8') for name in changed.split(b'\0') if name}
    if changed_paths - set(selected):
        raise ValueError('Staged changes outside exact reviewed scan')


class Runner:
    """Capture every actual command without inheriting Git overrides or Python paths."""

    def __init__(self, repository: Path, output: Path) -> None:
        """Initialize local receipts and a credential-free child environment."""
        self.repository, self.output = repository, output
        self.commands: list[Command] = []
        self.env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
        self.env.update(GIT_OPTIONAL_LOCKS='0', GIT_LFS_SKIP_SMUDGE='1',
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                        GIT_NO_REPLACE_OBJECTS='1', PYTHONDONTWRITEBYTECODE='1',
                        PYTHONNOUSERSITE='1')

    def record(self, argv: list[str], cwd: Path, started: datetime, code: int | None,
               stdout: Digest, stderr: bytes, stdout_bytes: bytes | None,
               timed_out: bool = False) -> None:
        """Retain command logs and append a typed command record."""
        stem = f'command-{len(self.commands)+1:03d}'
        err = self.output/(stem+'.stderr')
        err.write_bytes(stderr)
        out_ref = None
        if stdout_bytes is not None:
            out = self.output/(stem+'.stdout')
            out.write_bytes(stdout_bytes)
            out_ref = Asset(path=out.name, **digest(stdout_bytes).model_dump())
        self.commands.append(Command(argv=argv, cwd=str(cwd), started_at=started,
                                     finished_at=now(), exit_code=code, stdout=stdout,
                                     stderr=Asset(path=err.name, **digest(stderr).model_dump()),
                                     stdout_file=out_ref, timed_out=timed_out))

    def run(self, argv: list[str], cwd: Path, timeout: int = 300) -> bytes:
        """Run one bounded, shell-free command and preserve failure output."""
        started = now()
        try:
            result = subprocess.run(argv, cwd=cwd, env=self.env, capture_output=True,
                                    timeout=timeout, check=False)
        except subprocess.TimeoutExpired as error:
            out, err = error.stdout or b'', error.stderr or b''
            self.record(argv, cwd, started, None, digest(out), err, out, True)
            raise ValueError('Command timed out') from error
        self.record(argv, cwd, started, result.returncode, digest(result.stdout),
                    result.stderr, result.stdout)
        if result.returncode:
            raise ValueError('Command returned '+str(result.returncode)+': '+argv[0])
        return result.stdout

    def git(self, *args: str) -> bytes:
        """Use only fixed read-only Git commands, with LFS explicitly disabled."""
        return self.run(['git', '-c', 'core.fsmonitor=false', '-c', 'filter.lfs.process=',
                         '-c', 'filter.lfs.smudge=cat',
                         '-c', 'filter.lfs.required=false', *args], self.repository)

    def blobs(self, entries: list[IndexEntry], destination: Path | None,
              expected: dict[str, Digest] | None = None) -> list[ExportAsset]:
        """Read raw index blobs without filters, optionally exporting exact payloads."""
        argv = ['git', 'cat-file', '--batch']
        started = now()
        process = subprocess.Popen(argv, cwd=self.repository, env=self.env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        timer = threading.Timer(MAX_SECONDS, process.kill)
        timer.start()
        stream_hash = sha256()
        stream_size = total = 0
        assets: list[ExportAsset] = []
        error: Exception | None = None
        try:
            assert process.stdin is not None and process.stdout is not None
            for entry in entries:
                process.stdin.write((entry.oid+'\n').encode())
                process.stdin.flush()
                header = process.stdout.readline(256)
                stream_hash.update(header)
                stream_size += len(header)
                oid, kind, raw_size = header.rstrip(b'\n').split(b' ')
                size = int(raw_size)
                if oid.decode() != entry.oid or kind != b'blob' or not 0 <= size <= MAX_BLOB:
                    raise ValueError('Unexpected or oversized Git blob')
                total += size
                if total > MAX_TOTAL:
                    raise ValueError('Export cumulative byte cap reached')
                target = destination/entry.path if destination else None
                if target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                handle = target.open('xb') if target else None
                body_hash = sha256()
                left = size
                try:
                    while left:
                        chunk = process.stdout.read(min(left, 1024*1024))
                        if not chunk:
                            raise ValueError('Truncated Git blob stream')
                        body_hash.update(chunk)
                        stream_hash.update(chunk)
                        stream_size += len(chunk)
                        left -= len(chunk)
                        if handle:
                            handle.write(chunk)
                finally:
                    if handle:
                        handle.close()
                ending = process.stdout.read(1)
                stream_hash.update(ending)
                stream_size += len(ending)
                if ending != b'\n':
                    raise ValueError('Bad Git batch delimiter')
                found = ExportAsset(**entry.model_dump(), sha256=body_hash.hexdigest(),
                                    size_bytes=size)
                if expected and entry.path in expected:
                    wanted = expected[entry.path]
                    if (found.sha256, found.size_bytes) != (wanted.sha256, wanted.size_bytes):
                        raise ValueError('Staged blob differs from expected pin: '+entry.path)
                if target:
                    target.chmod(0o755 if entry.mode == '100755' else 0o644)
                assets.append(found)
            process.stdin.close()
            process.wait(timeout=5)
        except Exception as caught:
            error = caught
            process.kill()
        finally:
            timer.cancel()
            process.wait(timeout=5)
            stderr = process.stderr.read() if process.stderr else b''
            self.record(argv, self.repository, started, process.returncode,
                        Digest(sha256=stream_hash.hexdigest(), size_bytes=stream_size),
                        stderr, None, (now()-started).total_seconds() >= MAX_SECONDS)
        if error:
            raise error
        if process.returncode:
            raise ValueError('Git blob reader failed')
        return assets


def verify_export(root: Path, assets: list[ExportAsset], allow_runtime: bool) -> None:
    """Recheck every exported blob and reject unexpected files outside CI runtime."""
    expected = {asset.path for asset in assets}
    actual: set[str] = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in exported tree')
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if allow_runtime and rel.startswith(RUNTIME):
                continue
            actual.add(rel)
    if actual != expected:
        raise ValueError('Export closure differs from index')
    for asset in assets:
        hashed = sha256()
        size = 0
        with (root/asset.path).open('rb') as handle:
            for block in iter(lambda: handle.read(1024*1024), b''):
                hashed.update(block)
                size += len(block)
        mode = stat.S_IMODE((root/asset.path).stat().st_mode)
        if mode != (0o755 if asset.mode == '100755' else 0o644):
            raise ValueError('Exported file mode drift: '+asset.path)
        if (hashed.hexdigest(), size) != (asset.sha256, asset.size_bytes):
            raise ValueError('Exported file drift: '+asset.path)


def verify_wrappers(root: Path, scan: Scan) -> int:
    """Validate each scan-selected wrapper using only exported staged bytes."""
    inventories = [asset for asset in scan.files if asset.path.endswith('/INVENTORY.json')
                   and 'closed wrapper inventory' in asset.basis]
    if len(inventories) != scan.wrappers:
        raise ValueError('Wrapper count or selection differs')
    for asset in inventories:
        path = root/asset.path
        base = path.parent
        data = json.loads(path.read_bytes())
        jsonschema.validate(data, json.loads((base/'INVENTORY.schema.json').read_bytes()))
        members: set[str] = set()
        prefix = base.relative_to(root).as_posix()+'/'
        for ref in data['files']:
            rel = ref['path']
            if rel.startswith(prefix):
                rel = rel[len(prefix):]
            safe_path(rel)
            if rel in members:
                raise ValueError('Duplicate wrapper member')
            members.add(rel)
            raw = (base/rel).read_bytes()
            if (sha256(raw).hexdigest(), len(raw)) != (ref['sha256'], ref['size_bytes']):
                raise ValueError('Wrapper member hash differs')
        actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        if actual != members | {'INVENTORY.json'}:
            raise ValueError('Wrapper closure differs')
    return len(inventories)


def write_model(path: Path, value: BaseModel) -> None:
    """Validate a typed payload against its schema and save it without replacement."""
    schema = type(value).model_json_schema()
    raw = value.model_dump_json(indent=2)+'\n'
    jsonschema.validate(json.loads(raw), schema)
    with path.with_suffix('.schema.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(schema, indent=2)+'\n')
    with path.open('x', encoding='utf-8') as handle:
        handle.write(raw)


def execute(args: argparse.Namespace) -> int:
    """Perform only the explicitly authorized staged export and offline checks."""
    from models import ExportInventory

    repository, output = args.repository.absolute(), args.output.absolute()
    if output.parent != Path('/private/tmp') or not output.name.startswith('geode-staged-'):
        raise ValueError('Output must be a new /private/tmp/geode-staged-* directory')
    for path in (repository, output):
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('Symlinked root or ancestor')
    if not repository.is_dir() or output.exists():
        raise ValueError('Repository missing or output already exists')
    python = args.python.absolute()
    if not python.is_file():
        raise ValueError('Supplied Python executable missing')
    output.mkdir()
    procedure = output/'procedure'
    procedure.mkdir()
    procedure_files = []
    for name in ['verify_staged_export.py', 'models.py']:
        raw_code = Path(__file__).with_name(name).read_bytes()
        (procedure/name).write_bytes(raw_code)
        procedure_files.append(Asset(path='procedure/'+name, **digest(raw_code).model_dump()))
    exported = output/'exported-index'
    runner = Runner(repository, output)
    start = now()
    before = after = None
    head = None
    checked = wrapper_count = 0
    assets: list[ExportAsset] = []
    inventory_ok = ci_ok = False
    failure = None
    try:
        raw = args.scan.read_bytes()
        schema_raw = args.scan.with_name('SCAN.schema.json').read_bytes()
        if sha256(raw).hexdigest() != args.scan_sha256:
            raise ValueError('Final scan hash differs')
        if sha256(schema_raw).hexdigest() != args.schema_sha256:
            raise ValueError('Final scan schema hash differs')
        scan = Scan.model_validate_json(raw)
        jsonschema.validate(json.loads(raw), json.loads(schema_raw))
        (output/'SCAN.json').write_bytes(raw)
        (output/'SCAN.schema.json').write_bytes(schema_raw)
        head = runner.git('rev-parse', 'HEAD').decode().strip()
        if head != scan.head:
            raise ValueError('HEAD differs from final reviewed scan')
        listing = runner.git('ls-files', '--stage', '-z')
        before = digest(listing)
        entries = parse_index(listing)
        changed = runner.git('diff', '--cached', '--no-renames', '--name-only', '-z', 'HEAD', '--')
        compare_scan(scan, entries, changed)
        expected = {asset.path: Digest(sha256=asset.sha256, size_bytes=asset.size_bytes)
                    for asset in scan.files}
        required = {'geode/pipeline/manual_review_inventory.py',
                    'scripts/manual_source_watch_ci.py'}
        if not required <= set(expected):
            raise ValueError('Both executable entrypoints must be pinned in final scan')
        runner.blobs([entries[path] for path in sorted(expected)], None, expected)
        checked = len(expected)
        # Direct raw-blob export invokes no checkout, clean, smudge, or process filter.
        exported.mkdir()
        assets = runner.blobs([entries[path] for path in sorted(entries)], exported, expected)
        verify_export(exported, assets, False)
        write_model(output/'EXPORTED_INDEX.json',
                    ExportInventory(recorded_at=now(), files=assets))
        wrapper_count = verify_wrappers(exported, scan)
        runner.run([str(python), '-B', '-m', 'geode.pipeline.manual_review_inventory',
                    '--root', str(exported), '--check'], exported)
        inventory_ok = True
        ci_stdout = runner.run([str(python), '-B', 'scripts/manual_source_watch_ci.py',
                                '--root', str(exported), '--run-name', 'staged-offline',
                                '--event', 'local_readiness'], exported, timeout=300)
        summary_folder = exported/'.geode_runtime/manual_source_watch_ci/staged-offline'
        summary_raw = (summary_folder/'summary.json').read_bytes()
        summary = json.loads(summary_raw)
        jsonschema.validate(summary, json.loads((summary_folder/'summary.schema.json').read_bytes()))
        if json.loads(ci_stdout) != summary:
            raise ValueError('CI printed and retained summary differ')
        if (summary['status'] != 'ready' or summary['execution_requested']
                or summary['event_context'] != 'local_readiness'
                or summary['publication_attempted'] or summary['baseline_updated']
                or summary['schedule_activation_verified']
                or summary['legal_currentness'] != 'not_verified'
                or len(summary['pairs']) != 4
                or any(pair['status'] != 'verified' or pair['execute_exit'] is not None
                       or pair['verify_exit'] is not None or pair['sources']
                       for pair in summary['pairs'])):
            raise ValueError('CI result is not the required offline readiness outcome')
        ci_ok = True
        verify_export(exported, assets, True)
        verify_wrappers(exported, scan)
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    finally:
        try:
            after = digest(runner.git('ls-files', '--stage', '-z'))
            if before is not None and before != after:
                raise ValueError('Original staged index metadata changed during verification')
            if head is not None and runner.git('rev-parse', 'HEAD').decode().strip() != head:
                raise ValueError('Original HEAD changed during verification')
        except Exception as error:
            failure = (failure+'; ' if failure else '')+type(error).__name__+': '+str(error)
        receipt = Receipt(status='failed' if failure else 'passed', started_at=start,
                          finished_at=now(), repository=str(repository),
                          export_directory=str(exported), expected_scan_sha256=args.scan_sha256,
                          expected_schema_sha256=args.schema_sha256, index_before=before,
                          index_after=after, head=head, scan_members_checked=checked,
                          exported_files=len(assets),
                          exported_bytes=sum(asset.size_bytes for asset in assets),
                          wrappers_checked=wrapper_count, inventory_check_passed=inventory_ok,
                          ci_default_readiness_passed=ci_ok, commands=runner.commands, procedure_files=procedure_files,
                          failure=failure, qualifications=[
                              'This checks staged bytes, not working files or remote publication.',
                              'LFS pointers remain pointer bytes; no object hydration was attempted.',
                              'Only default local readiness was requested; no live source mode ran.',
                              'No full suite, scheduler activation or legal-currentness review ran.',
                              'The export is local; Linux/GitHub Actions behavior remains unverified.',
                              'Command logs and partial export are preserved on any failure.'])
        write_model(output/'RECEIPT.json', receipt)
    sys.stdout.write(receipt.model_dump_json(indent=2)+'\n')
    return 2 if failure else 0


def main() -> int:
    """Require root-reviewed final pins and explicit execution authorization."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--scan', type=Path, required=True)
    parser.add_argument('--scan-sha256', required=True)
    parser.add_argument('--schema-sha256', required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute-reviewed-export', action='store_true')
    args = parser.parse_args()
    if not args.execute_reviewed_export:
        parser.error('No export authorized; root must pass --execute-reviewed-export explicitly')
    try:
        return execute(args)
    except (OSError, ValueError) as error:
        sys.stderr.write(type(error).__name__+': '+str(error)+'\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
