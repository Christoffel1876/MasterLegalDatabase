"""Reproduce late restamping with a synthetic corpus and stubbed Git, without Git operations."""
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SOURCE = Path('/private/tmp/geode_packaging_scan.py')
code = SOURCE.read_bytes()
source_sha = hashlib.sha256(code).hexdigest()

with tempfile.TemporaryDirectory(dir='/private/tmp', prefix='plato-packaging-scan-') as temporary:
    root = Path(temporary) / 'repository'
    handoffs = Path(temporary) / 'handoffs'
    wrapper = root / 'research/local_review/fixture-approved'
    wrapper.mkdir(parents=True)
    victim = wrapper / 'source.txt'
    approved, changed = b'APPROVED EXACT SOURCE\n', b'INJECTED UNVERIFIED SOURCE\n'
    victim.write_bytes(approved)
    schema = wrapper / 'INVENTORY.schema.json'
    schema.write_text(json.dumps({'type': 'object', 'required': ['files']}))
    def ref(path: Path) -> dict:
        raw = path.read_bytes()
        return {'path': path.name, 'sha256': hashlib.sha256(raw).hexdigest(),
                'size_bytes': len(raw)}
    (wrapper / 'INVENTORY.json').write_text(json.dumps({'files': [ref(victim), ref(schema)]}))
    prior = handoffs / 'ptolemy-inventory69-packaging-audit'
    prior.mkdir(parents=True)
    (prior / 'NEEDED_FORCE_ADD.json').write_text('{"files": []}')
    old = b'{"historical":true}\n'
    manifest = root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    manifest.parent.mkdir(parents=True)
    records = []
    for i in range(6):
        p = root / '_RAW_ARCHIVE' / ('synthetic-' + str(i) + '.pdf')
        p.write_bytes(('synthetic original ' + str(i)).encode())
        raw = p.read_bytes()
        records.append({'archive_path': p.relative_to(root).as_posix(),
                        'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw)})
    manifest.write_bytes(old + b''.join((json.dumps(row) + '\n').encode() for row in records))
    tests = root / 'tests'; tests.mkdir()
    (tests / 'test_chaffee_source_path.py').write_bytes(b'# synthetic test placeholder\n')
    tree = ast.parse(code)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'R', 'B'}:
                node.value = ast.Call(func=ast.Name(id='Path', ctx=ast.Load()),
                    args=[ast.Constant(str(root if node.targets[0].id == 'R' else handoffs))],
                    keywords=[])
        if isinstance(node, ast.FunctionDef) and node.name == 'git':
            node.body = ast.parse('''
if args[0] == 'ls-files': return b''
if args[0] == 'show': return OLD
if args[0] == 'diff': return b''
if args[0] == 'rev-parse': return b'ffffffffffffffffffffffffffffffffffffffff\\n'
raise ValueError('unexpected Git request')
''').body
        if isinstance(node, ast.FunctionDef) and node.name == 'hashasset':
            node.name = '_original_hashasset'
    index = next(i for i, node in enumerate(tree.body)
                 if isinstance(node, ast.FunctionDef) and node.name == '_original_hashasset') + 1
    hook = ast.parse('''
HITS = 0
def hashasset(p):
    global HITS
    if p == VICTIM:
        HITS += 1
        if HITS == 2:
            p.write_bytes(CHANGED)
    return _original_hashasset(p)
''').body
    tree.body[index:index] = hook
    ast.fix_missing_locations(tree)
    space = {'__name__': '__main__', 'OLD': old, 'VICTIM': victim, 'CHANGED': changed}
    with patch.object(sys, 'argv', [str(SOURCE), 'late-buffer-probe']), patch.object(
            subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout=b'', stderr=b'')):
        exec(compile(tree, '<exact-scanner-with-isolated-path-and-Git-fixtures>', 'exec'), space)
    scan = json.loads((handoffs / 'atlas-final-packaging/late-buffer-probe/SCAN.json').read_bytes())
    item = next(x for x in scan['files'] if x['path'] == victim.relative_to(root).as_posix())
    assert item['sha256'] == hashlib.sha256(changed).hexdigest()
    assert item['sha256'] != hashlib.sha256(approved).hexdigest()
    assert item['basis'] == ['closed wrapper fixture-approved']
    assert SOURCE.read_bytes() == code
    result = {'scanner_sha256': source_sha, 'isolated_reproduction': 'late_wrapper_body_restamped',
              'canonical_writes': 0, 'git_operations': 0, 'public_requests': 0,
              'expected_wrapper_payload_sha256': hashlib.sha256(approved).hexdigest(),
              'returned_payload_sha256': item['sha256'], 'returned_basis': item['basis'],
              'scanner_status': scan['status'], 'actual_production_occurrence_asserted': False}
    sys.stdout.write(json.dumps(result, indent=2) + '\n')
