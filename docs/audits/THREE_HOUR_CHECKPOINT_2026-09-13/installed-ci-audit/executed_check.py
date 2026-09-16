"""Read-only exact installation and bounded publication check; no public requests."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import jsonschema

base = Path('/Users/mcoors/Documents/Project Geode')
repo = base / 'MasterLegalDatabase'
audit = base / 'handoffs/run-2026-09-13/popper-manual-watch-ci-installation-audit'
sys.path.insert(0, str(audit))
from models import Acceptance, Asset, ScanEntry
bad = '24554bb0b1dd44a41e6dcb7db72e17e9f4a739a6b7d5ccd9fd59a4edd12aa411'
wrapper_rel = 'research/local_review/manual-watch-ci-integration-2026-09-13'
wrapper = repo / wrapper_rel


def checked(root: Path, ref: dict) -> bytes:
    """Read an ordinary safe path and validate bytes against the supplied identity."""
    path = Path(ref['path'])
    assert not path.is_absolute() and '..' not in path.parts
    full = root / path
    assert full.is_file() and not any(p.is_symlink() for p in [full, *full.parents])
    data = full.read_bytes()
    assert len(data) == ref['size_bytes']
    assert hashlib.sha256(data).hexdigest() == ref['sha256']
    assert ref['sha256'] != bad
    return data


def identity(root: Path, name: str) -> Asset:
    """Return an exact identity without copying file contents."""
    data = (root / name).read_bytes()
    return Asset(path=name, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


installation_raw = (wrapper / 'INSTALLATION.json').read_bytes()
assert hashlib.sha256(installation_raw).hexdigest() == (
    '5a9e25492d0fe21f1a2ff44a90d705550cb1eb7b8bd9733ea627fc9257819d5b')
installation = json.loads(installation_raw)
for stem in ['INSTALLATION', 'INVENTORY']:
    jsonschema.Draft202012Validator(json.loads((wrapper / (stem + '.schema.json')).read_bytes()
                                             )).validate(json.loads((wrapper / (stem + '.json')).read_bytes()))
inv = json.loads((wrapper / 'INVENTORY.json').read_bytes())
refs = {a['path']: a for a in inv['files']}
assert len(refs) == len(inv['files']) == 494
assert {p.relative_to(wrapper).as_posix() for p in wrapper.rglob('*') if p.is_file()} == (
    set(refs) | {'INVENTORY.json'})
for ref in inv['files']:
    checked(wrapper, ref)
assert installation['status'] == 'installed_locally_not_deployed'
assert installation['legal_currentness'] == 'not_verified' and not installation['answer_safe']
for name, expected in [('proposal_manifest', '0bd9034cb8888947c821890b846287c393c4b2326c9301c38137327420b4daab'),
                       ('audit_manifest', '082d1785e33ed73f1269f5fb5fec5be7b872be5f4d2b17ce4d3d4368b09d550e')]:
    assert installation[name]['sha256'] == expected
    checked(wrapper, installation[name])
assert len(installation['installed_files']) == 10
for ref in installation['installed_files']:
    current = checked(repo, ref)
    assert current == (wrapper / 'preparation/proposed' / ref['path']).read_bytes()
    assert current == (base / 'handoffs/run-2026-09-13/ptolemy-manual-watch-ci-publishable-revision/proposed' / ref['path']).read_bytes()
plan = json.loads((repo / 'config/manual_source_watch_ci.json').read_bytes())
assert len(plan['immutable_inputs']) == 87
for ref in plan['immutable_inputs']:
    checked(repo, ref)
    assert subprocess.run(['git', 'ls-files', '--error-unmatch', '--', ref['path']],
                          cwd=repo, capture_output=True).returncode == 0
    attr = subprocess.check_output(['git', 'check-attr', 'filter', '--', ref['path']],
                                   cwd=repo, text=True).rsplit(':', 1)[-1].strip()
    assert attr == 'unspecified'
# Selected wrapper discovery is captured before scanning; no whole repository body scan.
untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'],
                                    cwd=repo).decode().split('\0')
untracked = [s for s in untracked if s]
staged = subprocess.check_output(
    ['git', 'diff', '--cached', '--name-only', '--diff-filter=A', '-z'],
    cwd=repo).decode().split('\0')
staged = [s for s in staged if s]
roots = sorted({'/'.join(s.split('/')[:3]) for s in set(untracked) | set(staged)
                if s.startswith('research/local_review/')})
assert roots
(audit / 'observed-staged-added-paths.txt').write_text('\n'.join(staged) + '\n')
(audit / 'observed-untracked-paths.txt').write_text('\n'.join(untracked) + '\n')
count = total = candidates = 0
name_hits, digest_hits = [], []
with (audit / 'SCANNED_PATHS.jsonl').open('w', encoding='utf-8') as out:
    for root in roots:
        for path in sorted((repo / root).rglob('*')):
            assert not path.is_symlink(), path
            if not path.is_file():
                continue
            size = path.stat().st_size
            name_hit = path.name in {'models 2.py', 'PROJECT_STATUS_2026-09-09.md'}
            size_hit = size == 36560
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if size_hit else None
            rel = path.relative_to(repo).as_posix()
            entry = ScanEntry(path=rel, size_bytes=size, excluded_basename_match=name_hit,
                              excluded_size_match=size_hit, sha256_if_size_matches=digest)
            out.write(entry.model_dump_json() + '\n')
            count += 1
            total += size
            candidates += int(size_hit)
            if name_hit:
                name_hits.append(rel)
            if digest == bad:
                digest_hits.append(rel)
assert not name_hits and not digest_hits
user = identity(repo, 'geode/schemas/models 2.py')
assert user.sha256 == bad and user.size_bytes == 36560
# Only top-level public verifiers: historical incomplete trees remain evidence only.
commands = [
    [sys.executable, '-B', str(wrapper / 'preparation/verify_publishable.py'),
     '--repository-root', str(repo)],
    [sys.executable, '-B', str(wrapper / 'independent-audit/validate_public.py'),
     '--root', str(wrapper / 'independent-audit')],
]
for index, command in enumerate(commands, 1):
    result = subprocess.run(command, cwd='/private/tmp', capture_output=True, timeout=30)
    (audit / f'verifier-{index}.stdout').write_bytes(result.stdout)
    (audit / f'verifier-{index}.stderr').write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr
    print(index, result.stdout.decode().strip())
assert identity(repo, 'geode/schemas/models 2.py') == user
for name in ['INSTALLATION.json', 'INSTALLATION.schema.json', 'INVENTORY.json',
             'INVENTORY.schema.json', 'README.md']:
    destination = audit / 'wrapper-metadata' / name
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes((wrapper / name).read_bytes())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
receipt = Acceptance(
    status='accepted_with_recorded_limits', checked_at=datetime.now(timezone.utc).isoformat(),
    repository_head=head,
    installed_files=[Asset.model_validate(ref) for ref in installation['installed_files']],
    immutable_inputs=[Asset.model_validate(ref) for ref in plan['immutable_inputs']],
    all_87_inputs_tracked_non_lfs=True, wrapper_path=wrapper_rel,
    wrapper_inventory=identity(audit, 'wrapper-metadata/INVENTORY.json'),
    wrapper_payload_count=494, installation=identity(audit, 'wrapper-metadata/INSTALLATION.json'),
    proposal_manifest_sha256=installation['proposal_manifest']['sha256'],
    independent_manifest_sha256=installation['audit_manifest']['sha256'],
    discovered_untracked_path_count=len(untracked),
    discovered_staged_added_path_count=len(staged),
    wrapper_discovery_method='staged_additions_union_untracked_paths', scanned_wrapper_roots=roots,
    scanned_file_count=count, scanned_byte_sizes_total=total, exact_digest_candidates=candidates,
    excluded_basename_hits=name_hits, excluded_content_hits=digest_hits,
    original_user_file=user, original_matches_prior_identity=True, schema_validation_passed=True,
    copied_public_verifiers_passed=True, source_requests=0, canonical_writes=False,
    full_suite_rerun=False, deployment_verified=False, linux_execution_verified=False,
    legal_currentness='not_verified', findings=[], limitations=[
        'Snapshot audit of installed bytes and current pins; no full suite rerun or live HTTP.',
        'Exclusion scan covers only the listed wrapper roots discovered from staged additions plus remaining untracked paths. '
        'It is not a historical whole-repository content search.',
        'Every ordinary file in those roots was name/size checked. Only files of exactly36560 bytes '
        'require digest comparison for byte equality with the excluded user file; none were found.',
        'The original user file was read only to compare its present exact identity before/after. '
        'It was not copied. Equality does not prove an unwitnessed historical sequence.',
        'All87 dependency paths are Git-tracked, but approved workingtree policy bytes must reach '
        'the committed checkout before cloud execution can match them.',
        'Wrapper documentation retains its prepared-stage frontmatter; the later typed installation '
        'receipt explicitly records local installation only. No Linux/cloud/schedule activation proof.',
        'The two historical public subsets intentionally omit one user-content payload each. Only '
        'their current top-level public verifiers were invoked.',
    ])
(audit / 'ACCEPTANCE.json').write_text(receipt.model_dump_json(indent=2) + '\n')
print('installed', len(receipt.installed_files), 'pins', len(receipt.immutable_inputs),
      'wrapper_payloads', len(refs), 'roots', len(roots), 'scanned', count,
      'same_size', candidates, 'source_requests', 0)
