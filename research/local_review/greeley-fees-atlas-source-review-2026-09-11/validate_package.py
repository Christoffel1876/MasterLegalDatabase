"""Verify the Greeley source-review package offline, without repository dependencies."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, Field

sys.dont_write_bytecode = True

from package_models import FileRef, Package, Strict, ValidationReceipt


class BuildingSpan(Strict):
    """An untouched exhaustive interval in the building schedule native page."""

    label: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class BuildingReview(Strict):
    """Strictly parse the original building-schedule audit without rewriting it."""

    prepared_at: AwareDatetime
    source_id: Literal['greeley-building-fees-sd008-06']
    physical_pages: list[int]
    method: str
    source_sha256: str
    candidate_sha256: str
    native_sha256: str
    native_bytes: Literal[3236]
    candidate_native_start: Literal[56]
    candidate_native_end: Literal[3292]
    spans: list[BuildingSpan]
    source_order: list[str]
    footnote_links: dict[str, str]
    observations: list[str]
    files: dict[str, str]
    legal_currentness: Literal['not_verified']
    external_report_consulted: Literal[False]


def digest(data: bytes) -> str:
    """Hash the exact supplied bytes."""
    return hashlib.sha256(data).hexdigest()


def confined(base: Path, relative: str) -> Path:
    """Reject traversal and symlink paths before touching a referenced file."""
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or str(rel) != relative:
        raise ValueError('Unconfined file path')
    target = base / rel
    cursor = base
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('Symlink inside package')
    if not target.is_file() or not target.resolve().is_relative_to(base):
        raise ValueError(f'Missing package file: {relative}')
    return target


def read_ref(base: Path, ref: FileRef) -> bytes:
    """Read a bounded regular file and enforce its exact byte identity."""
    target = confined(base, ref.path)
    if target.stat().st_size != ref.size_bytes or ref.size_bytes > 20_000_000:
        raise ValueError(f'Unexpected file size: {ref.path}')
    data = target.read_bytes()
    if digest(data) != ref.sha256:
        raise ValueError(f'Changed file: {ref.path}')
    return data


def load_module(name: str, path: Path) -> ModuleType:
    """Load a frozen local verifier after the package inventory has passed."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError('Could not load frozen verifier')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_building(base: Path) -> BuildingReview:
    """Verify all building fee spans, order, conditions and footnote references."""
    review = BuildingReview.model_validate_json((base / 'SOURCE_QA.json').read_bytes())
    if review.physical_pages != [1] or len(review.spans) != 29:
        raise ValueError('Building page/span scope changed')
    for name, expected in review.files.items():
        if digest(confined(base, name).read_bytes()) != expected:
            raise ValueError('Building audit file changed')
    if digest((base / 'source.pdf').read_bytes()) != review.source_sha256:
        raise ValueError('Building source hash')
    candidate = (base / 'candidate.txt').read_bytes()
    if digest(candidate) != review.candidate_sha256:
        raise ValueError('Building candidate hash')
    with pymupdf.open(base / 'source.pdf') as pdf:
        if len(pdf) != 1 or pdf.is_repaired or pdf.is_encrypted:
            raise ValueError('Building PDF invalid')
        native = pdf[0].get_text('text', sort=False, flags=195).encode()
    evidence = json.loads((base / 'native-evidence.json').read_bytes())
    if (native != evidence['text'].encode() or digest(native) != review.native_sha256
            or len(native) != 3236):
        raise ValueError('Building native text changed')
    if candidate[review.candidate_native_start:review.candidate_native_end] != native:
        raise ValueError('Building candidate/page slice changed')
    offset = 0
    by_label = {}
    for span in review.spans:
        data = native[span.start:span.end]
        if (span.start != offset or data != span.text.encode()
                or digest(data) != span.sha256):
            raise ValueError('Building native partition gap/overlap/change')
        offset = span.end
        if span.label in by_label:
            raise ValueError('Duplicate building span label')
        by_label[span.label] = span
    if offset != len(native) or sorted(review.source_order) != sorted(by_label):
        raise ValueError('Building native or visible-order coverage incomplete')
    expected_order = [
        'document_title', 'table_1a_title', 'permit_table_heading', 'table_columns',
        *[f'valuation_{i}' for i in range(1, 9)], 'other_heading',
        *[f'other_{i}' for i in range(1, 10)], 'footnote_1', 'footnote_2',
        'sales_tax_heading', 'sales_tax_body', 'temporary_electrical_heading',
        'temporary_electrical_body', 'unlabeled_footer_date',
    ]
    if review.source_order != expected_order:
        raise ValueError('Building heading/body or visible-order association changed')
    links = {f'other_{i}': 'footnote_1' for i in range(1, 5)}
    links['other_5'] = 'footnote_2'
    if review.footnote_links != links:
        raise ValueError('Building fee/footnote association changed')
    for i in range(1, 5):
        if '$75.00 per hour1' not in by_label[f'other_{i}'].text:
            raise ValueError('Building footnote marker or unit changed')
    if 'Actual costs2' not in by_label['other_5'].text:
        raise ValueError('Outside-consultant footnote marker changed')
    return review


def verify_schema_pairs(base: Path) -> int:
    """Check every copied JSON record with its adjacent exported schema."""
    count = 0
    for path in sorted(base.rglob('*.json')):
        if path.name.endswith('.schema.json') or path.parent == base:
            continue
        schema = path.with_name(path.stem + '.schema.json')
        if schema.is_file():
            validator = jsonschema.Draft202012Validator(json.loads(schema.read_bytes()))
            validator.validate(json.loads(path.read_bytes()))
            count += 1
    return count


def verify(base: Path, rerender: bool = False) -> ValidationReceipt:
    """Validate custody closure and the three preserved source-review contracts."""
    if base.is_symlink():
        raise ValueError('Package root must not be a symlink')
    base = base.resolve()
    raw = (base / 'PACKAGE.json').read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError('Package manifest is too large')
    package = Package.model_validate_json(raw)
    schema = json.loads((base / 'PACKAGE.schema.json').read_bytes())
    if schema != Package.model_json_schema():
        raise ValueError('Package schema differs from strict model')
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    inventory = {item.file.path: item.file for item in package.payloads}
    expected = set(inventory) | {
        'PACKAGE.json', 'PACKAGE.schema.json', 'VALIDATION.json', 'VALIDATION.schema.json',
    }
    actual = set()
    for item in base.rglob('*'):
        if item.is_symlink():
            raise ValueError('Package contains a symlink')
        if item.is_file():
            actual.add(item.relative_to(base).as_posix())
    if actual - expected or (set(inventory) - actual):
        raise ValueError('Uninventoried or missing files')
    for ref in inventory.values():
        read_ref(base, ref)
    resolved = {r.original_path: r.frozen for r in package.historical_path_resolutions}
    packet_base = base / 'packet'
    packet_module = load_module(
        '_greeley_packet_verifier', packet_base / '04-verification/verify_packet.py'
    )
    packet_module.verify(packet_base, rerender)
    packet = json.loads(read_ref(base, package.packet_manifest))
    for document, received in zip(package.documents, packet['documents'], strict=True):
        if (document.assignment_id != received['assignment_id']
                or document.source_id != received['source_id']
                or document.expected_physical_pages != received['expected_pages']
                or document.source.sha256 != received['original']['sha256']
                or document.candidate.sha256 != received['candidate']['sha256']):
            raise ValueError('Package/packet source contract changed')
        folder = base / document.audit_directory
        audit = json.loads(read_ref(base, document.audit))
        if document.assignment_id == 'EB-PDF-015':
            b = verify_building(folder)
            if b.source_sha256 != document.source.sha256:
                raise ValueError('Wrong building review source')
        elif document.assignment_id == 'EB-PDF-016':
            mod = load_module('_greeley_eb016_verifier', folder / 'build_review.py')
            mod.verify(folder)
            if audit['source']['sha256'] != document.source.sha256:
                raise ValueError('Wrong impact memo source')
            for item in audit['input_copies']:
                ref = resolved[item['original_path']]
                frozen = item['frozen']
                if (ref.sha256, ref.size_bytes) != (frozen['sha256'], frozen['size_bytes']):
                    raise ValueError('EB016 input custody not portable')
        else:
            # The copied validate() also reads historical originals. Use its portable
            # semantic function after resolving those exact inputs to package copies.
            old_path = list(sys.path)
            previous = sys.modules.get('review_models')
            try:
                sys.path.insert(0, str(folder))
                sys.modules.pop('review_models', None)
                mod = load_module('_greeley_eb017_verifier', folder / 'validate_source_review.py')
                checked = mod.Review.model_validate_json((folder / 'SOURCE_REVIEW.json').read_bytes())
                mod.validate_review(checked)
            finally:
                sys.path[:] = old_path
                sys.modules.pop('review_models', None)
                if previous is not None:
                    sys.modules['review_models'] = previous
            if checked.source_pdf.sha256 != document.source.sha256:
                raise ValueError('Wrong utility notice source')
            receipt = json.loads((folder / 'CUSTODY_RECEIPT.json').read_bytes())
            for item in receipt['files']:
                ref = resolved[item['original_path']]
                copied = item['copied_file']
                if (ref.sha256, ref.size_bytes) != (copied['sha256'], copied['size_bytes']):
                    raise ValueError('EB017 input custody not portable')
        anchors = (
            {s['label'] for s in audit['spans']} if document.assignment_id == 'EB-PDF-015'
            else {o['id'] for o in audit['observations']}
        )
        for note in document.scope_notes:
            if not set(note.audit_anchors).issubset(anchors):
                raise ValueError('Scope note has an absent source-audit anchor')
    schema_count = verify_schema_pairs(base)
    ref = FileRef(path='PACKAGE.json', sha256=digest(raw), size_bytes=len(raw))
    receipt = ValidationReceipt(
        schema_version=1, verified_at=datetime.now(timezone.utc), package=ref,
        status='passed', payload_files=len(inventory), physical_pages=6, native_bytes=11743,
        audit_scope_checks={
            'building_native_spans': 29, 'building_valuation_rows': 8,
            'building_other_fee_items': 9, 'building_footnotes': 2,
            'impact_fee_rows': 30, 'impact_table_cells_including_headers_blanks': 191,
            'utility_left_table_rows': 7, 'utility_right_table_rows': 1,
            'utility_data_cells': 24, 'utility_printed_dollar_sign_cells': 4,
        }, schema_pairs_checked=schema_count,
        historical_paths_resolved=len(resolved), full_page_rerender_performed=rerender,
        external_report_intake=False, legal_currentness='not_verified',
        checks=[
            'Exact closed payload inventory; no symlinks or outside verification reads',
            'Strict package Pydantic model and exported schema',
            'Frozen packet schema, full candidate packaging and six native extraction replays',
            'Frozen raw manifest selected lines, intake provenance, receipt and referral anchors',
            'Unchanged audits, exhaustive native byte partitions and original source bindings',
            'Building heading/body ordering and source fee/footnote links',
            'Impact memo complete table cells, fee group references and carried column headings',
            'Utility separate tables, exact source rectangles and conditional-scope observations',
            'Historical original paths resolved to frozen equivalent copies inside this package',
        ],
    )
    # If a saved receipt exists, verify its binding rather than replacing its time.
    saved = base / 'VALIDATION.json'
    if saved.exists():
        prior = ValidationReceipt.model_validate_json(saved.read_bytes())
        if prior.package != ref or prior.payload_files != len(inventory):
            raise ValueError('Saved validation receipt binds another package')
        jsonschema.Draft202012Validator(
            json.loads((base / 'VALIDATION.schema.json').read_bytes())
        ).validate(json.loads(saved.read_bytes()))
    return receipt


def main() -> None:
    """Run a read-only check rooted at this portable package."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--rerender', action='store_true')
    args = parser.parse_args()
    result = verify(args.root, args.rerender)
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('%s', result.model_dump_json(indent=2))


if __name__ == '__main__':
    main()
