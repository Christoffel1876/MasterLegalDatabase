"""Portable, unreviewed native-page research over pinned partial-agency captures."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Literal

import pymupdf
from pydantic import AwareDatetime, Field, model_validator

from . import ccr_agency_capture_v2 as capture
from . import ccr_source_text as native
from .ccr_agency_capture import atomic_new, bounded, encoded, ordinary, sha

MAX_FILE_BYTES = native.MAX_FILE_BYTES
MAX_TOTAL_BYTES = native.MAX_TOTAL_BYTES
MAX_FILES = native.MAX_FILES
MAX_DOCUMENTS = native.MAX_DOCUMENTS
MAX_PAGES = native.MAX_PAGES
MAX_TEXT_BYTES = native.MAX_TEXT_BYTES
WARNING = native.WARNING


class InputPlan(native.StrictModel):
    """Public exact capture pin and optional whole-PDF selection, without local root paths."""

    schema_version: Literal['ccr-agency-native-input-1'] = 'ccr-agency-native-input-1'
    capture_manifest_sha256: capture.Digest
    selected_pdf_sha256: list[capture.Digest] | None = Field(default=None, max_length=MAX_DOCUMENTS)

    @model_validator(mode='after')
    def selection(self) -> InputPlan:
        """An explicit selection must be a nonempty sorted exact set of complete PDFs."""
        if self.selected_pdf_sha256 is not None and (
            not self.selected_pdf_sha256
            or self.selected_pdf_sha256 != sorted(set(self.selected_pdf_sha256))
        ):
            raise ValueError('Whole-PDF selection must be nonempty, sorted and unique')
        return self


class Document(native.StrictModel):
    """Every retained document association, including aliases and unsearched originals."""

    association_id: str
    department_id: str
    agency_id: str
    rule_id: str
    source_citation: str
    listing_title: str
    history_title: str
    version: capture.VersionRow
    response: capture.Response
    original: native.Asset
    extraction_status: Literal['native_text', 'empty_native', 'unselected_pdf', 'unsupported_word']
    physical_pages: int | None = Field(ge=1, le=MAX_PAGES)
    empty_native_pages: list[int]
    review_status: Literal['machine_extraction_unreviewed'] = 'machine_extraction_unreviewed'
    answer_safe: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Page(native.StrictModel):
    """One complete physical native page, joined to each exact source association."""

    association_id: str
    physical_page: int = Field(ge=1, le=MAX_PAGES)
    original_sha256: capture.Digest
    text: native.Asset
    native_empty: bool


class Scope(native.StrictModel):
    """Capture and extraction denominators remain separate from departmental completeness."""

    department_id: str
    catalog_agencies: int
    source_cutoff_claim: date
    observed_start_claim: AwareDatetime
    observed_finish_claim: AwareDatetime
    capture_selected_agencies: int
    capture_selected_rules: int
    unselected_agency_ids: list[str]
    unselected_listing_rules: list[capture.Selection]
    selected_pdf_sha256: list[capture.Digest]
    unselected_pdf_sha256: list[capture.Digest]
    unsupported_word_associations: int
    empty_native_associations: int
    capture_document_associations: int
    department_complete: Literal[False] = False
    department_native_complete: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'


class Manifest(native.StrictModel):
    """Closed native package with its exact complete original V2 capture embedded."""

    schema_version: Literal['ccr-agency-native-manifest-1'] = 'ccr-agency-native-manifest-1'
    extractor: str
    input: InputPlan
    scope: Scope
    page_associations: int = Field(ge=0, le=MAX_PAGES)
    unique_physical_pages: int = Field(ge=0, le=MAX_PAGES)
    unique_native_bytes: int = Field(ge=0, le=MAX_TEXT_BYTES)
    files: list[native.Asset] = Field(min_length=1, max_length=MAX_FILES - 1)
    warning: Literal[WARNING] = WARNING
    answer_safe: Literal[False] = False


class Hit(native.StrictModel):
    """A whole physical page and the exact record/version/source association."""

    document: Document
    page: Page
    native_text: str


class QueryResult(native.StrictModel):
    """Literal source matches with explicit omitted, empty and unsupported scope."""

    package_manifest_sha256: capture.Digest
    query: str
    mode: Literal['phrase', 'citation']
    total_matching_page_associations: int = Field(ge=0)
    returned_page_associations: int = Field(ge=0, le=50)
    truncated: bool
    hits: list[Hit] = Field(max_length=50)
    scope: Scope
    warning: Literal[WARNING] = WARNING
    answer_safe: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'


def _asset(path: str, raw: bytes) -> native.Asset:
    return native.Asset(path=path, sha256=sha(raw), size_bytes=len(raw))


def _jsonl(rows: list[native.StrictModel]) -> bytes:
    return b''.join(encoded(row).replace(b'\n', b'') + b'\n' for row in rows)


def schemas() -> dict[str, bytes]:
    """Publish all deterministic schemas before emitting corresponding records."""
    return {name + '.schema.json': (json.dumps(model.model_json_schema(), indent=2) + '\n').encode()
            for name, model in [('InputPlan', InputPlan), ('Document', Document), ('Page', Page),
                                ('Manifest', Manifest), ('QueryResult', QueryResult)]}


def _read_tree(root: Path, refs: list[native.Asset], manifest: bytes,
               total_limit: int, member_limit: int) -> dict[str, bytes]:
    names = [ref.path for ref in refs]
    if (names != sorted(set(names)) or 'MANIFEST.json' in names
            or len(names) + 1 > member_limit
            or sum(ref.size_bytes for ref in refs) + len(manifest) > total_limit):
        raise ValueError('Closed member/count/byte budget differs')
    actual, directories = set(), set()
    for path in root.rglob('*'):
        ordinary(path)
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            directories.add(relative)
        else:
            if not path.is_file():
                raise ValueError('Nonregular package member')
            actual.add(relative)
    expected_dirs = {parent.as_posix() for name in names for parent in Path(name).parents
                     if parent.as_posix() != '.'}
    if actual != set(names) | {'MANIFEST.json'} or directories != expected_dirs:
        raise ValueError('Closed directory membership differs')
    result = {'MANIFEST.json': manifest}
    for ref in refs:
        if ref.size_bytes > MAX_FILE_BYTES:
            raise ValueError('Individual file cap exceeded')
        raw = bounded(root / ref.path, ref.size_bytes)
        if len(raw) != ref.size_bytes or sha(raw) != ref.sha256:
            raise ValueError('Captured member identity differs')
        result[ref.path] = raw
    return result


def _capture_record(files: dict[str, bytes], pin: str) -> tuple[capture.Capture, capture.Plan]:
    raw = files['MANIFEST.json']
    if len(raw) > capture.MAX_METADATA_BYTES or sha(raw) != pin:
        raise ValueError('V2 capture manifest pin differs or exceeds metadata cap')
    manifest = capture.Manifest.model_validate_json(raw)
    if (len(files) > capture.MAX_MEMBERS or sum(map(len, files.values()))
            > capture.MAX_PACKAGE_BYTES):
        raise ValueError('Original V2 capture limits exceeded')
    if set(files) != {ref.path for ref in manifest.files} | {'MANIFEST.json'}:
        raise ValueError('Embedded V2 closed membership differs')
    for ref in manifest.files:
        body = files[ref.path]
        if len(body) != ref.bytes or sha(body) != ref.sha256:
            raise ValueError('Embedded V2 member differs')
        if not ref.path.startswith('bodies/') and ref.bytes > capture.MAX_METADATA_BYTES:
            raise ValueError('Embedded V2 metadata cap exceeded')
    if any(files.get(name) != raw for name, raw in capture.schemas().items()):
        raise ValueError('Embedded V2 schema differs')
    plan = capture.Plan.model_validate_json(files['PLAN.json'])
    record = capture.Capture.model_validate_json(files['CAPTURE.json'])
    expected = {r.body.path for r in plan.responses} | {
        'MANIFEST.json', 'PLAN.json', 'CAPTURE.json', *capture.schemas()}
    if set(files) != expected or any(
        r.body.path != 'bodies/' + r.body.sha256 + '.bin' for r in plan.responses
    ):
        raise ValueError('Embedded V2 projection differs')
    if record != capture.derive(plan, files, record.input_plan_sha256):
        raise ValueError('Embedded V2 semantic replay differs')
    return record, plan


def _outputs(plan: InputPlan, original: dict[str, bytes]) -> tuple[dict[str, bytes], Manifest]:
    record, source_plan = _capture_record(original, plan.capture_manifest_sha256)
    pdfs = {r.body.sha256 for r in source_plan.responses if r.role == 'pdf'}
    selected = set(plan.selected_pdf_sha256) if plan.selected_pdf_sha256 is not None else pdfs
    if not selected or not selected <= pdfs:
        raise ValueError('Selected original PDF is absent from verified capture')
    association_rows = {url: (rule, version) for rule in record.selected_rules
                        for version in rule.versions if version.selected
                        for url in version.document_urls}
    docs, pages, texts = [], [], {}
    extracted: dict[str, list[bytes]] = {}
    for response in source_plan.responses:
        if response.role not in {'pdf', 'word'}:
            continue
        rule, version = association_rows[response.claim.requested_url]
        digest = response.body.sha256
        original_path = 'capture/' + response.body.path
        raw = original[response.body.path]
        status, physical, empty = 'unsupported_word', None, []
        if response.role == 'pdf':
            status = 'unselected_pdf'
            if digest in selected:
                if digest not in extracted:
                    extracted[digest] = native.extract_pdf_pages(raw)
                    for number, text in enumerate(extracted[digest], 1):
                        path = f'native/{digest}/{number:06}.txt'
                        if len(text) > MAX_FILE_BYTES:
                            raise ValueError('Individual native page byte cap exceeded')
                        texts[path] = text
                    if (len(texts) > MAX_PAGES or sum(map(len, texts.values())) > MAX_TEXT_BYTES
                            or len(texts) + len(original) + 9 > MAX_FILES):
                        raise ValueError('Native page/text/file budget exceeded')
                physical = len(extracted[digest])
                empty = [n for n, text in enumerate(extracted[digest], 1) if not text.strip()]
                status = 'empty_native' if len(empty) == physical else 'native_text'
                for number, text in enumerate(extracted[digest], 1):
                    path = f'native/{digest}/{number:06}.txt'
                    pages.append(Page(association_id=response.association_id, physical_page=number,
                                      original_sha256=digest, text=_asset(path, text),
                                      native_empty=not bool(text.strip())))
        docs.append(Document(
            association_id=response.association_id, department_id=record.department_id,
            agency_id=rule.agency_id, rule_id=rule.rule_id, source_citation=rule.source_citation,
            listing_title=rule.listing_title, history_title=rule.history_title, version=version,
            response=response, original=_asset(original_path, raw), extraction_status=status,
            physical_pages=physical, empty_native_pages=empty))
    if len(docs) > MAX_DOCUMENTS or len(pages) > MAX_PAGES:
        raise ValueError('Document/page association cap exceeded')
    scope = Scope(
        department_id=record.department_id, catalog_agencies=record.catalog_agency_count,
        source_cutoff_claim=record.source_cutoff_claim,
        observed_start_claim=record.observed_start_claim,
        observed_finish_claim=record.observed_finish_claim,
        capture_selected_agencies=record.selected_agency_count,
        capture_selected_rules=record.selected_rule_count,
        unselected_agency_ids=[a.agency_id for a in record.agencies if not a.selected],
        unselected_listing_rules=[capture.Selection(agency_id=a.agency_id, rule_id=r.rule_id)
                                 for a in record.agencies for r in a.rules if not r.selected],
        selected_pdf_sha256=sorted(selected), unselected_pdf_sha256=sorted(pdfs - selected),
        unsupported_word_associations=sum(d.extraction_status == 'unsupported_word' for d in docs),
        empty_native_associations=sum(d.extraction_status == 'empty_native' for d in docs),
        capture_document_associations=len(docs))
    files = {**schemas(), 'INPUT.json': encoded(plan), 'documents.jsonl': _jsonl(docs),
             'pages.jsonl': _jsonl(pages), **texts,
             **{'capture/' + name: raw for name, raw in original.items()}}
    if (len(files) + 1 > MAX_FILES or any(len(raw) > MAX_FILE_BYTES for raw in files.values())
            or sum(map(len, files.values())) > MAX_TOTAL_BYTES):
        raise ValueError('Output package limits exceeded')
    manifest = Manifest(
        extractor=f'PyMuPDF {pymupdf.VersionBind}; get_text(text), sort=False', input=plan,
        scope=scope, page_associations=len(pages), unique_physical_pages=len(texts),
        unique_native_bytes=sum(map(len, texts.values())),
        files=[_asset(name, raw) for name, raw in sorted(files.items())])
    if sum(map(len, files.values())) + len(encoded(manifest)) > MAX_TOTAL_BYTES:
        raise ValueError('Manifest-inclusive native package limit exceeded')
    return files, manifest


def build(source: Path, output: Path, plan: InputPlan) -> Manifest:
    """Create a fresh portable research package exclusively from exact captured input buffers."""
    ordinary(output)
    if output.exists():
        raise ValueError('Output already exists; partial outputs cannot be resumed')
    raw = bounded(source / 'MANIFEST.json', capture.MAX_METADATA_BYTES)
    if sha(raw) != plan.capture_manifest_sha256:
        raise ValueError('V2 capture manifest pin differs')
    original_manifest = capture.Manifest.model_validate_json(raw)
    refs = [native.Asset(path=r.path, sha256=r.sha256, size_bytes=r.bytes)
            for r in original_manifest.files]
    original = _read_tree(source, refs, raw, capture.MAX_PACKAGE_BYTES, capture.MAX_MEMBERS)
    files, manifest = _outputs(plan, original)
    output.mkdir(parents=True, exist_ok=False)
    for name, body in {**files, 'MANIFEST.json': encoded(manifest)}.items():
        atomic_new(output / name, body)
    return manifest


def _verified(root: Path, pin: str) -> tuple[dict[str, bytes], Manifest]:
    raw = bounded(root / 'MANIFEST.json', MAX_FILE_BYTES)
    if sha(raw) != pin:
        raise ValueError('Native manifest pin differs')
    manifest = Manifest.model_validate_json(raw)
    files = _read_tree(root, manifest.files, raw, MAX_TOTAL_BYTES, MAX_FILES)
    original = {name.removeprefix('capture/'): body for name, body in files.items()
                if name.startswith('capture/')}
    plan = InputPlan.model_validate_json(files['INPUT.json'])
    expected, derived = _outputs(plan, original)
    if {k: v for k, v in files.items() if k != 'MANIFEST.json'} != expected or manifest != derived:
        raise ValueError('Native extraction/schema/metadata replay differs')
    return files, manifest


def verify(root: Path, manifest_sha256: str) -> Manifest:
    """Replay all embedded custody and native pages from a caller-pinned portable package."""
    return _verified(root, manifest_sha256)[1]


def query(root: Path, manifest_sha256: str, text: str, *,
          mode: Literal['phrase', 'citation'] = 'phrase', limit: int = 10) -> QueryResult:
    """Return complete literal matched pages; no-match never certifies legal absence."""
    if (not text.strip() or len(text) > 500
            or mode not in {'phrase', 'citation'} or not 1 <= limit <= 50):
        raise ValueError('Nonempty query <=500 characters, source mode, limit1..50 required')
    files, manifest = _verified(root, manifest_sha256)
    documents = {doc.association_id: doc for line in files['documents.jsonl'].splitlines()
                 if (doc := Document.model_validate_json(line))}
    hits, total, returned_bytes = [], 0, 0
    for line in files['pages.jsonl'].splitlines():
        page = Page.model_validate_json(line)
        doc = documents[page.association_id]
        text_value = files[page.text.path].decode('utf-8')
        matched = (text.casefold() in text_value.casefold() if mode == 'phrase'
                   else text.casefold() == doc.source_citation.casefold())
        if matched:
            total += 1
            if len(hits) < limit and returned_bytes + page.text.size_bytes <= 2_000_000:
                hits.append(Hit(document=doc, page=page, native_text=text_value))
                returned_bytes += page.text.size_bytes
    return QueryResult(
        package_manifest_sha256=manifest_sha256, query=text, mode=mode,
        total_matching_page_associations=total, returned_page_associations=len(hits),
        truncated=total > len(hits), hits=hits, scope=manifest.scope)


def main(argv: list[str] | None = None) -> int:
    """Expose offline construction, pinned replay, and literal source research queries."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('build')
    create.add_argument('--source', type=Path, required=True)
    create.add_argument('--output', type=Path, required=True)
    create.add_argument('--capture-sha256', required=True)
    create.add_argument('--select-pdf', action='append')
    for name in ['verify', 'query']:
        command = sub.add_parser(name)
        command.add_argument('--root', type=Path, required=True)
        command.add_argument('--manifest-sha256', required=True)
        if name == 'query':
            command.add_argument('--text', required=True)
            command.add_argument('--mode', choices=['phrase', 'citation'], default='phrase')
            command.add_argument('--limit', type=int, default=10)
    args = parser.parse_args(argv)
    if args.command == 'build':
        plan = InputPlan(capture_manifest_sha256=args.capture_sha256,
                         selected_pdf_sha256=args.select_pdf)
        result = build(args.source, args.output, plan)
    elif args.command == 'verify':
        result = verify(args.root, args.manifest_sha256)
    else:
        result = query(args.root, args.manifest_sha256, args.text, mode=args.mode, limit=args.limit)
    sys.stdout.write(encoded(result).decode())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
