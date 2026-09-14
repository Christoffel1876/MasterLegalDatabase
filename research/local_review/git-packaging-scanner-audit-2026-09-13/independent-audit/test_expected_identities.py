"""Exercise exact proposed scanner functions against temporary files only."""
import ast
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
TREE = ast.parse((HERE / 'proposed/geode_packaging_scan.py').read_bytes())


@pytest.fixture
def scanner(tmp_path: Path) -> dict:
    """Load only the real admission/checking functions and final loop from the proposal AST."""
    nodes = [n for n in TREE.body if isinstance(n, ast.FunctionDef)
             and n.name in {'hashasset', 'add', 'bound_json'}]
    tree = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    namespace = {'Path': Path, 'sha256': hashlib.sha256, 'R': tmp_path,
                 'selected': {}, 'expected_identities': {}, 'json': json}
    exec(compile(tree, '<proposed-scanner-identity-functions>', 'exec'), namespace)
    return namespace


def pin(raw: bytes) -> tuple[str, int]:
    """Identify exact synthetic bytes."""
    return hashlib.sha256(raw).hexdigest(), len(raw)


def final_loop(scanner: dict) -> None:
    """Replay the unchanged final publication loop from the proposed scanner itself."""
    node = next(n for n in TREE.body if isinstance(n, ast.For)
                and isinstance(n.iter, ast.Name) and n.iter.id == 'paths')
    tree = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    class Asset(BaseModel):
        """Minimal result carrier; the tested integrity gate is the proposal's real AST."""
        path: str
        sha256: str
        size_bytes: int
        tracked: bool
        ignored: bool
        basis: list[str]
    scanner.update(paths=sorted(scanner['selected']), assets=[], tracked=set(), ignored=set(),
                   Asset=Asset)
    exec(compile(tree, '<proposed-scanner-final-loop>', 'exec'), scanner)


def test_expected_pin_survives_clean_final_loop(scanner: dict) -> None:
    """An unchanged accepted body keeps its declared identity."""
    raw = b'approved\n'
    (scanner['R'] / 'source.txt').write_bytes(raw)
    scanner['add']('source.txt', 'closed wrapper fixture', pin(raw))
    final_loop(scanner)
    assert scanner['assets'][0].sha256 == pin(raw)[0]


def test_late_change_cannot_be_restamped(scanner: dict) -> None:
    """A body changed after admission fails at the actual final asset loop."""
    path = scanner['R'] / 'source.txt'
    path.write_bytes(b'approved\n')
    scanner['add']('source.txt', 'closed wrapper fixture', pin(path.read_bytes()))
    path.write_bytes(b'INJECTED UNVERIFIED SOURCE\n')
    with pytest.raises(ValueError, match='final identity drift'):
        final_loop(scanner)
    assert scanner['assets'] == []


def test_conflicting_collection_pins_rejected(scanner: dict) -> None:
    """Different wrapper/prior/raw identities cannot silently overwrite one another."""
    path = scanner['R'] / 'source.txt'
    path.write_bytes(b'approved\n')
    scanner['add']('source.txt', 'wrapper', pin(path.read_bytes()))
    with pytest.raises(ValueError, match='conflicting expected identity'):
        scanner['add']('source.txt', 'raw manifest', pin(b'changed\n'))


def test_matching_duplicate_basis_is_retained(scanner: dict) -> None:
    """Multiple agreeing custody authorities preserve one identity and both bases."""
    path = scanner['R'] / 'source.txt'; path.write_bytes(b'approved\n')
    scanner['add']('source.txt', 'wrapper', pin(path.read_bytes()))
    scanner['add']('source.txt', 'prior audit', pin(path.read_bytes()))
    final_loop(scanner)
    assert scanner['assets'][0].basis == ['prior audit', 'wrapper']


def test_admission_rejects_wrong_declared_pin(scanner: dict) -> None:
    """A mismatch is rejected before it can become selected."""
    (scanner['R'] / 'source.txt').write_bytes(b'changed\n')
    with pytest.raises(ValueError, match='selected identity drift'):
        scanner['add']('source.txt', 'wrapper', pin(b'approved\n'))
    assert not scanner['selected']


def test_bound_metadata_cannot_change_before_parse(scanner: dict) -> None:
    """Receipt/preparation JSON is parsed only from identity-checked consumed bytes."""
    path = scanner['R'] / 'receipt.json'; path.write_bytes(b'{"approved":true}')
    scanner['add']('receipt.json', 'closed receipt', pin(path.read_bytes()))
    path.write_bytes(b'{"approved":false}')
    with pytest.raises(ValueError, match='metadata identity drift'):
        scanner['bound_json']('receipt.json')


def test_unbound_ci_receipt_is_refused(scanner: dict) -> None:
    """An installation receipt cannot enter through existence alone."""
    (scanner['R'] / 'INSTALLATION.json').write_bytes(b'{"installed_files":[]}')
    with pytest.raises(ValueError, match='unbound metadata'):
        scanner['bound_json']('INSTALLATION.json')


def test_unknown_inventory_file_is_refused(scanner: dict) -> None:
    """The actual untracked-file gate refuses a file absent from approved pin anchors."""
    start = next(i for i, n in enumerate(TREE.body) if isinstance(n, ast.Assign)
                 and isinstance(n.targets[0], ast.Name)
                 and n.targets[0].id == 'unknown_inventory')
    nodes = TREE.body[start:start + 3]
    assert isinstance(nodes[-1], ast.If)
    scanner.update(prefix='reviewed/inventory/',
                   git=lambda *args: b'reviewed/inventory/unbound-user.txt\0')
    with pytest.raises(ValueError, match='unbound inventory files require review'):
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                     '<proposed-scanner-unbound-inventory-gate>', 'exec'), scanner)


def test_case_alias_and_user_exclusion_refused(scanner: dict) -> None:
    """The exact two user-owned exclusions and case aliases cannot be selected."""
    for name in ['docs/audits/PROJECT_STATUS_2026-09-09.md', 'geode/schemas/models 2.py']:
        with pytest.raises(ValueError, match='user path'):
            scanner['add'](name, 'unrelated', pin(b''))
    path = scanner['R'] / 'source.txt'; path.write_bytes(b'approved')
    scanner['add']('source.txt', 'wrapper', pin(path.read_bytes()))
    with pytest.raises(ValueError, match='case-aliased'):
        scanner['add']('SOURCE.txt', 'wrapper', pin(path.read_bytes()))
