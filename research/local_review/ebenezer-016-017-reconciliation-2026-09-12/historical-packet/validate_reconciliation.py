"""Read-only validation of frozen reports, custody and qualified source associations."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import jsonschema
import pymupdf

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from reconciliation_models import Manifest, Reconciliation, Supplement


def digest(raw: bytes) -> str:
    """Hash bytes, preserving all Unicode and whitespace."""
    return hashlib.sha256(raw).hexdigest()


def read(path: str) -> bytes:
    """Reject escaping paths and symlinks before reading a package asset."""
    relative = Path(path)
    target = BASE / relative
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe package path')
    if target.is_symlink() or not target.resolve().is_relative_to(BASE):
        raise ValueError('Escaping package asset')
    for parent in target.parents:
        if parent == BASE:
            break
        if parent.is_symlink():
            raise ValueError('Symlink parent')
    return target.read_bytes()


def check(ref: Any) -> bytes:
    """Check an exact file identity without consulting historical absolute paths."""
    raw = read(ref.path)
    if digest(raw) != ref.sha256 or len(raw) != ref.size_bytes:
        raise ValueError(f'Changed asset: {ref.path}')
    return raw


def load_module(name: str, path: Path) -> Any:
    """Load only a module already protected by the closed package manifest."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError('Cannot load frozen verifier')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate() -> dict[str, Any]:
    """Validate all report bindings and replay the frozen source-specific checks."""
    manifest_raw = read('FINAL_MANIFEST.json')
    manifest = Manifest.model_validate_json(manifest_raw)
    if json.loads(read('FINAL_MANIFEST.schema.json')) != Manifest.model_json_schema():
        raise ValueError('Manifest schema changed')
    excluded = {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'}
    actual = {p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()}
    expected = {ref.path for ref in manifest.files}
    if len(expected) != len(manifest.files) or actual != expected | excluded:
        raise ValueError('Package is not closed')
    for ref in manifest.files:
        check(ref)
    raw = read('RECONCILIATION.json')
    record = Reconciliation.model_validate_json(raw)
    if json.loads(read('RECONCILIATION.schema.json')) != Reconciliation.model_json_schema():
        raise ValueError('Reconciliation schema changed')
    jsonschema.Draft202012Validator(Reconciliation.model_json_schema()).validate(json.loads(raw))
    for item in record.copies:
        check(item.frozen)
    supplement = Supplement.model_validate_json(read('ATLAS_ADDITIONAL_FINDINGS.json'))
    if json.loads(read('ATLAS_ADDITIONAL_FINDINGS.schema.json')) != Supplement.model_json_schema():
        raise ValueError('Supplement schema changed')
    for binding in supplement.bindings:
        raw_line = read(binding.path).splitlines(keepends=True)[binding.line - 1]
        if digest(raw_line) != binding.line_sha256:
            raise ValueError('Supplement line anchor changed')
    details = []
    for document in record.documents:
        source = check(document.source_pdf)
        candidate = check(document.candidate)
        report = check(document.report)
        receipt = json.loads(check(document.completion_receipt))
        check(document.baseline_review)
        if document.direct_review_pages != list(range(1, document.page_count + 1)):
            raise ValueError('Atlas coverage changed')
        for ref in document.source_images:
            check(ref)
        lines = report.splitlines(keepends=True)
        for decision in document.decisions:
            if decision.report != document.report.path:
                raise ValueError('Wrong report binding')
            if digest(lines[decision.report_line - 1]) != decision.report_line_sha256:
                raise ValueError('Claim line changed')
            if not set(decision.source_physical_pages) <= set(document.direct_review_pages):
                raise ValueError('Decision exceeds direct page coverage')
        number = document.assignment_id[-3:]
        prefix = f'reports/EB-PDF-{number}/'
        if number == '016':
            hashes = receipt['hashes']
            keys = ('PASS1_frozen_md_sha256', 'PASS1_FREEZE_RECEIPT_json_sha256',
                    'PASS2_REVIEW_md_sha256')
            expected_source = hashes['original_pdf_sha256']
            expected_candidate = hashes['candidate_txt_sha256']
        else:
            hashes = receipt
            keys = ('PASS1_frozen_md_sha256', 'PASS1_FREEZE_RECEIPT_sha256',
                    'PASS2_REVIEW_md_sha256')
            expected_source = hashes['original_pdf_sha256']
            expected_candidate = hashes['candidate_sha256']
        for name, key in zip(('PASS1_frozen.md', 'PASS1_FREEZE_RECEIPT.json',
                              'PASS2_REVIEW.md'), keys, strict=True):
            if digest(read(prefix + name)) != hashes[key]:
                raise ValueError('External completion receipt mismatch')
        if digest(source) != expected_source or digest(candidate) != expected_candidate:
            raise ValueError('Source/candidate receipt mismatch')
        with pymupdf.open(stream=source, filetype='pdf') as pdf:
            if len(pdf) != document.page_count or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError('PDF structure changed')
        directory = BASE / 'baseline' / document.assignment_id
        if number == '016':
            module = load_module('_eb016_frozen', directory / 'build_review.py')
            details.append(module.verify(directory))
        else:
            old_path = sys.path.copy()
            previous = sys.modules.pop('review_models', None)
            try:
                sys.path.insert(0, str(directory))
                module = load_module('_eb017_frozen', directory / 'validate_source_review.py')
                review = module.Review.model_validate_json(
                    (directory / 'SOURCE_REVIEW.json').read_bytes())
                # validate() reads historical paths. This semantic function uses frozen copies only.
                module.validate_review(review)
                details.append({'pages': 2, 'native_bytes': 1316, 'table_rows': [7, 1]})
            finally:
                sys.path[:] = old_path
                sys.modules.pop('review_models', None)
                if previous is not None:
                    sys.modules['review_models'] = previous
    # The supplied inventory covers three documents. Validate only the two scoped crop trees.
    supplied = read('supplemental/INVENTORY_sha256.txt').decode().splitlines()
    matched = set()
    for line in supplied:
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            continue
        relative = parts[1].lstrip('*')
        if relative.startswith('./'):
            relative = relative[2:]
        for number in ('016', '017'):
            marker = f'EB-PDF-{number}/'
            if marker in relative:
                local = 'supplemental/' + marker + relative.split(marker, 1)[1]
                if digest(read(local)) != parts[0]:
                    raise ValueError('External crop inventory mismatch')
                matched.add(local)
    crops = {p.relative_to(BASE).as_posix() for p in (BASE / 'supplemental').rglob('*.png')}
    if matched != crops:
        raise ValueError('Unbound supplemental crop')
    for ref in manifest.files:
        check(ref)
    return {'status': 'passed', 'documents': 2, 'direct_pages': 5,
            'decisions': sum(len(d.decisions) for d in record.documents),
            'supplemental_crops': len(crops), 'files': len(actual),
            'source_checks': details, 'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
