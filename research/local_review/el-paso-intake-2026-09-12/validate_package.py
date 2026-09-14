"""Validate portable El Paso custody and optional actual repository files, without writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterator

import jsonschema

BASE = Path(__file__).absolute().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(BASE))
from package_models import Asset, Inventory, Receipt, Record


def checked(root: Path, item: Asset) -> bytes:
    """Require exact ordinary bytes and reject every symlink ancestor."""
    path = root / item.path
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Nonordinary evidence: ' + item.path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != item.sha256 or path.stat().st_size != item.size_bytes:
        raise ValueError('Evidence hash/size mismatch: ' + item.path)
    return path.read_bytes()


def rows(path: Path) -> Iterator[dict]:
    """Stream UTF-8 JSONL records without generic historical reserialization."""
    with path.open('rb') as stream:
        for line in stream:
            yield json.loads(line)


def validate_schema(data: dict, path: Path) -> None:
    """Use preserved data schemas; never import or execute historical write scripts."""
    schema = json.loads(path.read_bytes())
    def local(node: object) -> None:
        if isinstance(node, dict):
            if '$ref' in node and not node['$ref'].startswith('#'):
                raise ValueError('External schema reference refused')
            for value in node.values():
                local(value)
        elif isinstance(node, list):
            for value in node:
                local(value)
    local(schema)
    jsonschema.Draft202012Validator(schema).validate(data)


def verify(root: Path | None = None) -> dict:
    """Check all portable byte equations and optionally the thirteen actual raw destinations."""
    inventory = Inventory.model_validate_json((BASE / 'PACKAGE_INVENTORY.json').read_bytes())
    actual = set()
    for path in BASE.rglob('*'):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise ValueError('Nonordinary package member')
        if path.is_file() and path != BASE / 'PACKAGE_INVENTORY.json':
            actual.add(path.relative_to(BASE).as_posix())
    names = [item.path for item in inventory.files]
    if len(names) != len(set(names)) or set(names) != actual:
        raise ValueError('Portable membership differs')
    for item in inventory.files:
        checked(BASE, item)
    receipt = Receipt.model_validate_json((BASE / 'PRESERVATION_RECEIPT.json').read_bytes())
    for name, model in [('PRESERVATION_RECEIPT', Receipt), ('PACKAGE_INVENTORY', Inventory)]:
        schema = json.loads((BASE / (name + '.schema.json')).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError('Portable schema differs')
        validate_schema(json.loads((BASE / (name + '.json')).read_bytes()),
                        BASE / (name + '.schema.json'))
    for directory, item, manifest_name in [
        ('transaction', receipt.transaction_manifest, 'FINAL_MANIFEST.json'),
        ('recovery', receipt.recovery_inventory, 'PACKAGE_INVENTORY.json'),
    ]:
        old = json.loads(checked(BASE, item))
        expected = {a['path'] for a in old['files']} | {manifest_name}
        actual_old = {p.relative_to(BASE / directory).as_posix()
                      for p in (BASE / directory).rglob('*') if p.is_file()}
        if expected != actual_old:
            raise ValueError('Frozen selected payload membership differs')
        for value in old['files']:
            checked(BASE / directory, Asset.model_validate(value))
    intent = json.loads(checked(BASE, receipt.original_intent))
    completion = json.loads(checked(BASE, receipt.original_completion_receipt))
    validate_schema(intent, BASE / 'transaction/INTENT.schema.json')
    validate_schema(completion, BASE / 'transaction/RECEIPT.schema.json')
    if (completion['intent'] != intent
            or completion['intent_sha256'] != receipt.original_intent.sha256
            or completion['reconciliation_added_ids']
            or completion['reconciliation_report_changed']):
        raise ValueError('Original completion/intent binding differs')
    expected_time = receipt.original_actual_repository_received_at.isoformat().replace('+00:00', 'Z')
    if intent['actual_repository_received_at'] != expected_time:
        raise ValueError('Original intake time changed')
    completed_time = receipt.original_completed_at.isoformat().replace('+00:00', 'Z')
    if completion['completed_at'] != completed_time or completion['actual_repository_received_at'] != expected_time:
        raise ValueError('Completion time differs from preserved receipt')
    expected_originals = [
        {'path': s.record.archive_path, 'sha256': s.record.sha256, 'size_bytes': s.record.size_bytes}
        for s in receipt.sources
    ]
    if completion['originals'] != expected_originals:
        raise ValueError('Completion original set differs')
    suffix = checked(BASE, receipt.exact_suffix)
    for p, change in zip(receipt.prefixes, intent['changes'][:2], strict=True):
        if (p.repository_path != change['path'] or p.before.sha256 != change['before']['sha256']
                or p.after.sha256 != change['after']['sha256']):
            raise ValueError('Prefix hashes differ from original intent')
        before, after = checked(BASE, p.before), checked(BASE, p.after)
        if after != before + suffix:
            raise ValueError('Exact historical prefix/suffix equation failed')
        if sum(1 for _ in rows(BASE / p.before.path)) != p.before_records:
            raise ValueError('Before count differs')
        if sum(1 for _ in rows(BASE / p.after.path)) != p.after_records:
            raise ValueError('After count differs')
        if root:
            checked(root, Asset(path=p.repository_path, sha256=p.after.sha256,
                                size_bytes=p.after.size_bytes))
    suffix_rows = list(rows(BASE / receipt.exact_suffix.path))
    if suffix_rows != intent['records'] or len(suffix_rows) != 13:
        raise ValueError('Final record suffix differs')
    if [s.record.model_dump(mode='json') for s in receipt.sources] != suffix_rows:
        raise ValueError('Portable record bindings differ')
    seen = set()
    for source in receipt.sources:
        row = source.record
        if row.record_id in seen or row.received_at != receipt.original_actual_repository_received_at:
            raise ValueError('Duplicate identity or changed intake time')
        seen.add(row.record_id)
        original = checked(BASE, source.preserved_original)
        if (hashlib.sha256(original).hexdigest() != row.sha256 or len(original) != row.size_bytes
                or not original.startswith(b'%PDF-')):
            raise ValueError('Original bytes do not match the final custody record')
        checked(BASE, source.provenance)
        provenance = next(value for n, value in enumerate(rows(BASE / source.provenance.path))
                          if n == source.provenance_jsonl_row)
        if (provenance['source_id'] != row.record_id
                or provenance['authority_id'] != source.authority_id
                or provenance['original']['sha256'] != row.sha256
                or provenance['decision'] != 'propose_county_intake'):
            raise ValueError('Explicit source/authority/provenance binding differs')
        if root:
            checked(root, Asset(path=row.archive_path, sha256=row.sha256, size_bytes=row.size_bytes))
    report = json.loads(checked(BASE, receipt.after_report))
    checked(BASE, receipt.before_report)
    if (receipt.before_report.sha256 != intent['changes'][2]['before']['sha256']
            or receipt.after_report.sha256 != intent['changes'][2]['after']['sha256']):
        raise ValueError('Report hashes differ from original intent')
    verification = report['archive_verification']
    if (report['records'] != 60 or verification['manifest_records'] != 59
            or len(verification['missing_ledger_only_intake_ids']) != 1):
        raise ValueError('Final ledger/report counts differ')
    before_result = json.loads(checked(BASE, receipt.before_corpus_validation))
    after_result = json.loads(checked(BASE, receipt.after_corpus_validation))
    if (before_result['valid'] or after_result['valid']
            or before_result['issues'] != after_result['issues']
            or [x['path'] for x in after_result['issues']] != receipt.unchanged_inherited_lfs_error_paths):
        raise ValueError('Full-corpus outcome misrepresented')
    checked(BASE, receipt.unchanged_legacy_coverage_ledger)
    if root:
        checked(root, Asset(path=receipt.legacy_coverage_ledger_repository_path,
                            sha256=receipt.unchanged_legacy_coverage_ledger.sha256,
                            size_bytes=receipt.unchanged_legacy_coverage_ledger.size_bytes))
        checked(root, Asset(path='_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json',
                            sha256=receipt.after_report.sha256, size_bytes=receipt.after_report.size_bytes))
    return {'status': 'portable_custody_verified', 'sources': 13, 'raw_records': 59,
            'ledger_records': 60, 'actual_repository_checked': root is not None,
            'unchanged_inherited_lfs_errors': 2, 'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    sys.stdout.write(json.dumps(verify(args.root.absolute() if args.root else None), indent=2) + '\n')
