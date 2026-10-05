"""Rebuild the 47-PDF CCR native completion and verify its exact seven-ledger union."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterator, Literal
from scripts import verify_ccr_baseline_additions as common
from scripts import verify_ccr_source_coverage as sources

Asset = common.Asset

class NativePackage(common.Strict):
    """Exact reproducible native addendum."""
    package_id: str
    source_manifest: Asset | None
    input_plan: Asset | None
    native_manifest: Asset | None
    ledger: Asset
    build_command: list[str]
    verify_command: list[str]

class Index(common.Strict):
    """Source/native custody counts with explicitly limited legal meaning."""
    prepared_at: str
    previous_index: Asset
    ledgers: list[Asset]
    packages: list[NativePackage]
    unique_pdf_originals: int
    unique_physical_pages: int
    added_native_pdfs: int
    added_native_pages: int
    transportation_pdf: Asset
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    whole_state_complete: Literal[False] = False
    native_status: Literal['machine_extraction_unreviewed'] = 'machine_extraction_unreviewed'


@contextmanager
def working_directory(root: Path) -> Iterator[None]:
    """Resolve the published department root '.' without altering its pinned input."""
    before = Path.cwd()
    try:
        os.chdir(root)
        yield
    finally:
        os.chdir(before)


def rebuilt_ledger(output: Path, *, agency_format: bool = False) -> dict[str, common.Original]:
    """Count original PDFs and physical pages, never document aliases or local paths."""
    from geode.pipeline.ccr_source_text import Page as DepartmentPage
    from geode.pipeline.ccr_agency_text import Page as AgencyPage
    Page = AgencyPage if agency_format else DepartmentPage
    rows = {}
    with (output / 'pages.jsonl').open('rb') as handle:
        for line in handle:
            page = Page.model_validate_json(line, strict=True)
            value = common.Page(physical_page=page.physical_page,
                text_sha256=page.text.sha256, text_bytes=page.text.size_bytes)
            bucket = rows.setdefault(page.original_sha256, {})
            if page.physical_page in bucket and bucket[page.physical_page] != value:
                raise ValueError('Conflicting duplicate native page alias')
            bucket[page.physical_page] = value
    result = {}
    for digest, values in rows.items():
        row = common.Original(sha256=digest, pages=[values[n] for n in sorted(values)])
        common.validate_original(row)
        result[digest] = row
    return result


def exact_ledger(expected: dict, rebuilt: dict) -> None:
    """Require exact PDF/page/text identities, not just matching aggregate counts."""
    if expected != rebuilt:
        raise ValueError('Rebuilt original/native page ledger differs')


def exact_union(index: Index, previous: common.Index,
                data: list[dict[str, common.Original]]) -> dict:
    """Reject duplicate references, overlap, missing PDFs, or altered union totals."""
    expected_refs = previous.prior_page_sets + [previous.new_page_set]
    expected_refs += [p.ledger for p in index.packages]
    if index.ledgers != expected_refs or len(index.ledgers) != 7:
        raise ValueError('Seven-ledger chain differs from pinned predecessors')
    if len({x.path for x in index.ledgers}) != 7 or len(data) != 7:
        raise ValueError('Duplicate or missing native ledger')
    union, before, added = {}, {}, {}
    for position, rows in enumerate(data):
        if set(union) & set(rows):
            raise ValueError('Unexpected overlapping original PDF')
        common.merge(union, rows)
        common.merge(before if position < 4 else added, rows)
    if (len(before), common.page_count(before)) != (previous.union_pdfs, previous.union_pages):
        raise ValueError('Previous native union differs')
    actual = dict(unique_pdf_originals=len(union), unique_physical_pages=common.page_count(union),
        added_native_pdfs=len(added), added_native_pages=common.page_count(added))
    if any(getattr(index, name) != count for name, count in actual.items()):
        raise ValueError('Native completion counters differ')
    if tuple(actual.values()) != (1156, 39460, 47, 503):
        raise ValueError('Expected retained baseline changed')
    return actual


def transportation(root: Path, index: Index, reader: common.Reader,
                   expected: dict[str, common.Original]) -> None:
    """Re-extract all ten PDF pages and compare every committed UTF-8 native file."""
    import pymupdf
    raw = reader.read(index.transportation_pdf)
    if set(expected) != {index.transportation_pdf.sha256}:
        raise ValueError('Transportation PDF/ledger identity differs')
    row = expected[index.transportation_pdf.sha256]
    common.validate_original(row)
    if len(row.pages) != 10:
        raise ValueError('Transportation must contain ten physical pages')
    prefix = 'docs/audits/CCR_NATIVE_COMPLETION_2026-10-05/transportation-native'
    folder = root / prefix
    expected_names = {f'{n:04d}.txt' for n in range(1, 11)}
    if folder.is_symlink() or {p.name for p in folder.iterdir()} != expected_names:
        raise ValueError('Unexpected or missing Transportation native file')
    with pymupdf.open(stream=raw, filetype='pdf') as pdf:
        if pdf.page_count != 10 or pdf.is_repaired or pdf.is_encrypted:
            raise ValueError('Transportation PDF structure differs')
        for page, item in zip(pdf, row.pages, strict=True):
            text = page.get_text('text', sort=False).encode('utf-8')
            ref = Asset(path=f'{prefix}/{item.physical_page:04d}.txt',
                sha256=item.text_sha256, bytes=item.text_bytes)
            if reader.read(ref) != text:
                raise ValueError('Transportation native text differs from PDF re-extraction')


def verify(root: Path, index: Index, *, scratch_parent: Path | None = None) -> dict:
    """Rebuild/replay the two maintained packages and standalone PDF from portable inputs."""
    from geode.pipeline import ccr_agency_text as agency
    from geode.pipeline import ccr_source_text as department
    reader = common.Reader(root)
    previous = common.Index.model_validate_json(reader.read(index.previous_index), strict=True)
    if [p.package_id for p in index.packages] != [
            'PH-V1-NATIVE', 'DEPARTMENT12', 'TRANSPORTATION3475-PDF-ONLY']:
        raise ValueError('Native package identity/order differs')
    data = [common.ledger(reader.read(ref)) for ref in index.ledgers]
    counts = exact_union(index, previous, data)
    parent = (scratch_parent or Path(tempfile.gettempdir())).resolve()
    with tempfile.TemporaryDirectory(prefix='ccr-native-completion-', dir=parent) as tmp:
        scratch = Path(tmp)
        for package, expected in zip(index.packages[:2], data[4:6], strict=True):
            if any(ref is None for ref in [package.source_manifest, package.input_plan,
                                            package.native_manifest]):
                raise ValueError('Maintained package input reference missing')
            source = reader.read(package.source_manifest)
            input_bytes = reader.read(package.input_plan)
            native_bytes = reader.read(package.native_manifest)
            output = scratch / package.package_id
            if package.package_id == 'PH-V1-NATIVE':
                plan = agency.InputPlan.model_validate_json(input_bytes, strict=True)
                if plan.capture_manifest_sha256 != package.source_manifest.sha256:
                    raise ValueError('PH V1 source/native input binding differs')
                manifest = agency.build(root / Path(package.source_manifest.path).parent, output, plan)
                agency.verify(output, package.native_manifest.sha256)
                if (len(expected), common.page_count(expected)) != (20, 313):
                    raise ValueError('PH V1 native scope differs')
            else:
                receipt = json.loads(source)
                for entry in receipt['source_refs']:
                    ref = department.Asset.model_validate(entry, strict=True)
                    reader.read(Asset(path=ref.path, sha256=ref.sha256, bytes=ref.size_bytes))
                plan = department.InputPlan.model_validate_json(input_bytes, strict=True)
                if len(plan.departments) != 1 or plan.departments[0].department_id != '12' or plan.departments[0].root != '.':
                    raise ValueError('Department12 portable source scope differs')
                with working_directory(root):
                    manifest = department.build(plan, output)
                department.verify(output, package.native_manifest.sha256)
                if (len(expected), common.page_count(expected)) != (26, 180):
                    raise ValueError('Department12 native scope differs')
            if (output / 'MANIFEST.json').read_bytes() != native_bytes:
                raise ValueError('Rebuilt expected native manifest differs byte-for-byte')
            exact_ledger(expected, rebuilt_ledger(output, agency_format=package.package_id == 'PH-V1-NATIVE'))
        partial = index.packages[2]
        if any(ref is not None for ref in [partial.source_manifest, partial.input_plan,
                                           partial.native_manifest]) or partial.build_command or partial.verify_command:
            raise ValueError('Standalone Transportation source must remain a partial PDF')
        transportation(root, index, reader, data[6])
    return dict(status='pass', **counts, native_verification='rebuilt_and_replayed',
        source_packages_rebuilt=2, transportation_native_files_verified=10,
        legal_currentness='not_verified', whole_state_complete=False)


def main() -> int:
    """Run bounded offline verification; temporary rebuilds never write canonical paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=Path)
    parser.add_argument('--index-sha256', required=True)
    parser.add_argument('--scratch-parent', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    path = args.index or root / 'docs/audits/CCR_NATIVE_COMPLETION_2026-10-05/INDEX.json'
    raw = sources.ordinary(path.parent, path.name)
    if common.sha(raw) != args.index_sha256:
        raise ValueError('Native completion index pin differs')
    schema = json.loads(sources.ordinary(path.parent, 'INDEX.schema.json'))
    if schema != Index.model_json_schema():
        raise ValueError('Native completion index schema differs')
    from jsonschema import Draft202012Validator
    Draft202012Validator(schema).validate(json.loads(raw))
    index = Index.model_validate_json(raw, strict=True)
    sys.stdout.write(json.dumps(verify(root, index, scratch_parent=args.scratch_parent),
                               sort_keys=True) + '\n')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
