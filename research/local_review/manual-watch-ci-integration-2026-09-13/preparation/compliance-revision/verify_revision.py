"""Read-only hash, schema, annotation and frontmatter verification; never run tests or HTTP."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import jsonschema

from models import Manifest, Receipt


class Normalize(ast.NodeTransformer):
    """Remove only annotation syntax and its one added typing import."""
    def visit_arg(self, node: ast.arg) -> ast.arg:
        """Ignore the requested parameter type additions."""
        node.annotation = None
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Ignore return/type-comment metadata while retaining executable bodies."""
        node.returns = None
        node.type_comment = None
        self.generic_visit(node)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        """Ignore only the explicitly documented annotation-only Any import."""
        if node.module == 'typing' and [n.name for n in node.names] == ['Any']:
            return None
        return node


def verify(root: Path) -> dict[str, object]:
    """Check every local payload and the exact allowed two-file differences."""
    manifest_bytes = (root / 'FINAL_MANIFEST.json').read_bytes()
    manifest = Manifest.model_validate_json(manifest_bytes)
    files = {}
    for ref in manifest.files:
        rel = Path(ref.path)
        if rel.is_absolute() or '..' in rel.parts or ref.path in files:
            raise ValueError('Unsafe or duplicate payload')
        path = root / rel
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError('Symlinked payload')
        data = path.read_bytes()
        if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
            raise ValueError('Changed payload')
        files[ref.path] = data
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(files) | {'FINAL_MANIFEST.json'}:
        raise ValueError('Missing or additional payload')
    for name, data in [('FINAL_MANIFEST', manifest_bytes), ('RECEIPT', files['RECEIPT.json'])]:
        jsonschema.Draft202012Validator(json.loads(files[name + '.schema.json'])).validate(
            json.loads(data))
    receipt = Receipt.model_validate_json(files['RECEIPT.json'])
    predecessor = json.loads(files[receipt.predecessor_manifest.path])
    prior = {r['path']: r for r in predecessor['files']}
    for change in receipt.changes:
        before, after = files[change.before.path], files[change.after.path]
        old = prior['proposed/' + change.install_path]
        if old['sha256'] != hashlib.sha256(before).hexdigest():
            raise ValueError('Before file differs from frozen predecessor')
        for ref, data in [(change.before, before), (change.after, after)]:
            if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
                raise ValueError('Change identity differs')
        if change.scope == 'annotations_only':
            old_ast = Normalize().visit(ast.parse(before))
            new_ast = Normalize().visit(ast.parse(after, feature_version=(3, 11)))
            if ast.dump(old_ast, include_attributes=False) != ast.dump(
                    new_ast, include_attributes=False):
                raise ValueError('Executable test AST differs')
            tree = ast.parse(after)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            if any(n.returns is None for n in functions):
                raise ValueError('Missing return annotation')
            for node in functions:
                args = [*node.args.args, *node.args.kwonlyargs]
                if node.args.kwarg:
                    args.append(node.args.kwarg)
                if any(a.annotation is None for a in args):
                    raise ValueError('Missing parameter annotation')
            if any(len(line) > 100 for line in after.decode().splitlines()):
                raise ValueError('Long maintained test line')
        else:
            if not after.endswith(before):
                raise ValueError('Original documentation body differs')
            prefix = after[:-len(before)]
            expected = (b'---\nstatus: prepared_not_installed_not_deployed\n'
                        b'scope: eight_fixed_manual_pdf_sources\n'
                        b'scheduled_http_default: disabled\nmanual_http_default: disabled\n'
                        b'legal_currentness: not_verified\n---\n\n')
            if prefix != expected:
                raise ValueError('Unexpected frontmatter addition')
    return {'status': 'PASS', 'payloads': len(files), 'changed_files': 2,
            'focused_tests_recorded': 44, 'execution_behavior_changed': False,
            'installed_or_deployed': False}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).parent.resolve()), indent=2))
