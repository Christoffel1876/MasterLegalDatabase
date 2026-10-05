"""Bind every retained CCR catalog identity to exact PDF bytes and native pages."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import sys
from typing import Literal
from urllib.parse import parse_qs, urlsplit
from pydantic import Field
from scripts import verify_ccr_baseline as coverage
from scripts import verify_ccr_baseline_additions as pages
from scripts import verify_ccr_source_coverage as prior

Asset = coverage.Asset

class Binding(pages.Strict):
    """An actual selected source version, never an inferred operative version."""
    version_id: str
    designation: str
    pdf_url: str
    pdf: Asset
    word_url: str | None
    word: Asset | None
    physical_pages: int = Field(ge=1)

class Identity(pages.Strict):
    """One retained agency/rule identity and its source-bound PDF selection."""
    department_id: str
    agency_id: str
    rule_id: str
    source_citation: str
    source_kind: Literal['department_inventory', 'agency_capture_v2', 'partial_pdf']
    source_metadata: Asset
    history_url: str
    source_cutoff_claim: str | None
    observed_at_claim: str
    bindings: list[Binding] = Field(min_length=1)
    legal_currentness: Literal['not_verified'] = 'not_verified'

class Index(pages.Strict):
    """Closed retained-catalog accounting, with current-law approval explicitly false."""
    schema_version: Literal['ccr-identity-pdf-baseline-1'] = 'ccr-identity-pdf-baseline-1'
    prepared_at: str
    coverage_index: Asset
    completion_index: Asset
    completion_schema: Asset
    identity_ledger: Asset
    identity_schema: Asset
    department_count: Literal[25] = 25
    listed_identities: Literal[1156] = 1156
    pdf_bound_identities: Literal[1156] = 1156
    paired_identities: Literal[1155] = 1155
    unique_pdf_originals: Literal[1156] = 1156
    unique_physical_pages: Literal[39460] = 39460
    source_cutoff_claims: list[str]
    unchanged_department_publisher_count: Literal[23] = 23
    whole_state_complete: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    native_status: Literal['machine_extraction_unreviewed'] = 'machine_extraction_unreviewed'
    exact_remaining_pair_gap: Literal['department 21 / agency 124 / rule 3475 / version 12137 Word source'] = 'department 21 / agency 124 / rule 3475 / version 12137 Word source'


def key(row: Identity) -> tuple[str, str, str]:
    """Return the exact publisher selector, preserving department ownership."""
    return row.department_id, row.agency_id, row.rule_id


def asset(path: str, digest: str, size: int) -> Asset:
    """Validate an immutable repository member before reading or writing a row."""
    return Asset(path=path, sha256=digest, bytes=size)


def normalize(ref: object) -> Asset:
    """Adapt the older size_bytes spelling without weakening the pinned identity."""
    return asset(ref.path, ref.sha256, ref.size_bytes)


def document_pair(urls: list[str]) -> tuple[str, str]:
    """Require one literal PDF and Word URL from the source history version."""
    pdf = [u for u in urls if parse_qs(urlsplit(u).query).get('type') != ['word']]
    word = [u for u in urls if parse_qs(urlsplit(u).query).get('type') == ['word']]
    if len(pdf) != 1 or len(word) != 1:
        raise ValueError('Selected history version does not have exactly one source pair')
    return pdf[0], word[0]


def unique_rows(rows: list[Identity]) -> dict[tuple[str, str, str], Identity]:
    """Reject duplicate selectors rather than silently overwriting them."""
    result = {}
    for row in rows:
        if key(row) in result:
            raise ValueError('Duplicate identity selector')
        result[key(row)] = row
    return result


def compare_rows(declared: list[Identity], derived: list[Identity]) -> None:
    """Reject missing, foreign or altered identity/source bindings."""
    left, right = unique_rows(declared), unique_rows(derived)
    if left != right:
        raise ValueError('Missing, foreign or changed identity/source binding')


def projection_equivalence(root: Path, original: coverage.Capsule,
                           projection: Asset) -> None:
    """Prove the V2 bridge preserves every V1 URL and retained original body."""
    from geode.pipeline import ccr_agency_capture as v1
    from geode.pipeline import ccr_agency_capture_v2 as v2
    before = v1.verify(root / Path(original.manifest.path).parent, original.manifest.sha256)
    folder = root / Path(projection.path).parent
    coverage.read(root, projection)
    after = v2.verify(folder, projection.sha256)
    plan = v2.Plan.model_validate_json((folder / 'PLAN.json').read_bytes())
    old = {t.requested_url: (t.historical.body.sha256, t.historical.body.bytes)
           for t in before.plan.targets}
    new = {r.claim.requested_url: (r.body.sha256, r.body.bytes) for r in plan.responses}
    if len(old) != len(before.plan.targets) or len(new) != len(plan.responses) or old != new:
        raise ValueError('V1 projection changed URL/original identity')
    selectors = {(r.agency_id, r.rule_id) for r in after.selected_rules}
    coverage.validate_capture_selectors(original.selectors, selectors)


def derive(root: Path, index: Index, *, replay_sources: bool = True
           ) -> tuple[list[Identity], dict[str, pages.Original], set[tuple[str, str, str]]]:
    """Replay source evidence and independently reconstruct every exact PDF binding."""
    from geode.pipeline import ccr_current as ccr
    from geode.pipeline import ccr_agency_capture_v2 as v2
    from scripts.publish_ccr_current import validate_payload
    from jsonschema import Draft202012Validator
    base = coverage.Index.model_validate_json(coverage.read(root, index.coverage_index))
    if replay_sources:
        coverage.verify(root, base)
    completion = json.loads(coverage.read(root, index.completion_index))
    Draft202012Validator(json.loads(coverage.read(root, index.completion_schema))).validate(completion)
    if (completion['unique_pdf_originals'], completion['unique_physical_pages']) != (1156, 39460):
        raise ValueError('Native completion union changed')
    ledgers = completion['ledgers']
    if len(ledgers) != 7 or len({r['path'] for r in ledgers}) != 7:
        raise ValueError('Exactly seven distinct native ledgers required')
    native = {}
    for ref in ledgers:
        pages.merge(native, pages.ledger(coverage.read(root, Asset.model_validate(ref))))
    old = prior.Index.model_validate_json(coverage.read(root, base.prior_department_index))
    result, expected = [], set()
    for dept in old.departments:
        if dept.phase == 'catalog_only':
            continue
        inv = normalize(dept.inventory)
        raw = coverage.read(root, inv)
        if dept.department_id == '12' and replay_sources:
            # The previous index intentionally only replayed department12 metadata.
            # This independent proof strengthens it without changing that old claim.
            state = ccr.CCRState.model_validate_json(coverage.read(root, normalize(dept.state)))
            buffers = {dept.inventory.path: raw,
                       dept.state.path: coverage.read(root, normalize(dept.state))}
            for source in state.sources.values():
                if source.path not in buffers:
                    buffers[source.path] = coverage.read(root, asset(source.path, source.sha256, source.bytes))
            validate_payload(buffers.__getitem__, '12')
        for line in io.BytesIO(raw):
            rec = ccr.CCRCurrentRecord.model_validate_json(line, strict=True)
            sources = {s.url: s for s in rec.sources}
            bindings = []
            for version in rec.versions:
                pair = [u for u in version.document_urls if u in sources]
                if not pair:
                    continue
                pdf_url, word_url = document_pair(pair)
                pdf, word = sources[pdf_url], sources[word_url]
                if pdf.sha256 not in native:
                    raise ValueError('Selected department PDF lacks native ledger')
                bindings.append(Binding(version_id=version.version_id,
                    designation=version.designation, pdf_url=pdf_url,
                    pdf=asset(pdf.path, pdf.sha256, pdf.bytes), word_url=word_url,
                    word=asset(word.path, word.sha256, word.bytes),
                    physical_pages=len(native[pdf.sha256].pages)))
            row = Identity(department_id=rec.department_id, agency_id=rec.agency_id,
                rule_id=rec.rule_id, source_citation=rec.ccr_citation,
                source_kind='department_inventory', source_metadata=inv,
                history_url=rec.source_page_url,
                source_cutoff_claim=rec.source_publication_cutoff.isoformat(),
                observed_at_claim=rec.observed_at.isoformat(), bindings=bindings)
            expected.add(key(row))
            result.append(row)
    for scope in base.scopes:
        expected.update((scope.department_id, r.agency_id, r.rule_id) for r in scope.listed)
    bridge = next(p for p in completion['packages'] if p['package_id'] == 'PH-V1-NATIVE')
    projection = Asset.model_validate(bridge['source_manifest'])
    originals = [c for c in base.capsules if c.format == 'v1']
    if len(originals) != 1:
        raise ValueError('Expected exactly one original V1 source capsule')
    if replay_sources:
        projection_equivalence(root, originals[0], projection)
    manifests = [c.manifest for c in base.capsules if c.format == 'v2'] + [projection]
    for ref in manifests:
        manifest = json.loads(coverage.read(root, ref))
        folder = Path(ref.path).parent
        def member(name: str) -> bytes:
            found = [a for a in manifest['files'] if a['path'] == name]
            if len(found) != 1:
                raise ValueError('Missing or duplicated capture metadata member')
            a = found[0]
            return coverage.read(root, asset(str(folder / name), a['sha256'], a['bytes']))
        cap = v2.Capture.model_validate_json(member('CAPTURE.json'))
        plan = v2.Plan.model_validate_json(member('PLAN.json'))
        by_url = {r.claim.requested_url: r for r in plan.responses}
        by_id = {r.association_id: r for r in plan.responses}
        for rec in cap.selected_rules:
            bindings = []
            for version in rec.versions:
                if not version.selected:
                    continue
                pdf_url, word_url = document_pair(version.document_urls)
                pdf, word = by_url[pdf_url], by_url[word_url]
                if pdf.body.sha256 not in native:
                    raise ValueError('Selected capsule PDF lacks native ledger')
                bindings.append(Binding(version_id=version.version_id,
                    designation=version.designation, pdf_url=pdf_url,
                    pdf=asset(str(folder / pdf.body.path), pdf.body.sha256, pdf.body.bytes),
                    word_url=word_url,
                    word=asset(str(folder / word.body.path), word.body.sha256, word.body.bytes),
                    physical_pages=len(native[pdf.body.sha256].pages)))
            result.append(Identity(department_id=cap.department_id, agency_id=rec.agency_id,
                rule_id=rec.rule_id, source_citation=rec.source_citation,
                source_kind='agency_capture_v2', source_metadata=ref,
                history_url=by_id[rec.history_association_id].claim.requested_url,
                source_cutoff_claim=cap.source_cutoff_claim.isoformat(),
                observed_at_claim=cap.observed_finish_claim.isoformat(), bindings=bindings))
    for partial in base.partial_pairs:
        observations = {json.loads(coverage.read(root, o.receipt))['target_id']: o
                        for o in partial.observations}
        history = observations['transportation3475-history']
        hreceipt = json.loads(coverage.read(root, history.receipt))
        receipt = json.loads(coverage.read(root, observations['transportation3475-pdf'].receipt))
        version = next(v for v in ccr._versions(ccr._parse_html(
            coverage.read(root, history.body), hreceipt['safe_headers']['content-type']),
            hreceipt['requested_url']) if v.version_id == partial.version_id)
        pdf_url, word_url = document_pair(version.document_urls)
        if pdf_url != receipt['requested_url']:
            raise ValueError('Partial PDF history binding differs')
        citation = parse_qs(urlsplit(hreceipt['requested_url']).query)['seriesNum'][0]
        result.append(Identity(department_id=partial.department_id, agency_id=partial.agency_id,
            rule_id=partial.rule_id, source_citation=citation, source_kind='partial_pdf',
            source_metadata=index.coverage_index, history_url=hreceipt['requested_url'],
            source_cutoff_claim=None, observed_at_claim=receipt['finished_at'],
            bindings=[Binding(version_id=partial.version_id, designation=version.designation,
                pdf_url=pdf_url, pdf=partial.pdf, word_url=word_url, word=None,
                physical_pages=partial.pdf_pages)]))
    result.sort(key=lambda r: tuple(map(int, key(r))))
    if set(unique_rows(result)) != expected:
        raise ValueError('Retained catalog identity set differs from PDF binding set')
    return result, native, expected


def validate_union(rows: list[Identity], native: dict[str, pages.Original],
                   expected: set[tuple[str, str, str]]) -> dict:
    """Prove identity completeness and exact PDF/native union without relying on totals."""
    by_key = unique_rows(rows)
    if set(by_key) != expected:
        raise ValueError('Missing or foreign catalog identity')
    pdfs = {b.pdf.sha256 for r in rows for b in r.bindings}
    if pdfs != set(native):
        raise ValueError('Identity PDF set does not equal native PDF union')
    for row in rows:
        for binding in row.bindings:
            if binding.physical_pages != len(native[binding.pdf.sha256].pages):
                raise ValueError('Identity physical page count differs')
    return dict(department_count=len({r.department_id for r in rows}),
        listed_identities=len(expected), pdf_bound_identities=len(rows),
        paired_identities=sum(all(b.word is not None for b in r.bindings) for r in rows),
        unique_pdf_originals=len(pdfs), unique_physical_pages=pages.page_count(native))


def verify(root: Path, index: Index, *, publication_root: Path | None = None) -> dict:
    """Validate source joins, original PDF bytes, and every retained physical-page count."""
    import pymupdf
    pub = publication_root or root
    if json.loads(coverage.read(pub, index.identity_schema)) != Identity.model_json_schema():
        raise ValueError('Identity ledger schema differs')
    declared = [Identity.model_validate_json(line, strict=True)
                for line in io.BytesIO(coverage.read(pub, index.identity_ledger))]
    derived, native, expected = derive(root, index)
    compare_rows(declared, derived)
    counts = validate_union(derived, native, expected)
    if any(getattr(index, name) != value for name, value in counts.items()):
        raise ValueError('Declared completion counts differ')
    cutoffs = sorted({r.source_cutoff_claim for r in derived if r.source_cutoff_claim})
    if index.source_cutoff_claims != cutoffs:
        raise ValueError('Source cutoff claims differ')
    gaps = [(key(r), b.version_id) for r in derived for b in r.bindings if b.word is None]
    if gaps != [(('21', '124', '3475'), '12137')]:
        raise ValueError('Exact remaining Word-source gap differs')
    checked = {}
    for row in derived:
        for binding in row.bindings:
            pdf = coverage.read(root, binding.pdf)
            if binding.pdf.sha256 not in checked:
                with pymupdf.open(stream=pdf, filetype='pdf') as doc:
                    checked[binding.pdf.sha256] = doc.page_count
            if checked[binding.pdf.sha256] != binding.physical_pages:
                raise ValueError('Original PDF physical page count differs')
            if binding.word is not None:
                word = coverage.read(root, binding.word)
                if not word.startswith((b'PK\x03\x04', bytes.fromhex('d0cf11e0a1b11ae1'), b'{\\rtf')):
                    raise ValueError('Word source signature differs')
    return dict(status='pass', **counts, source_cutoff_claims=cutoffs,
        exact_remaining_pair_gap=index.exact_remaining_pair_gap,
        native_text_reextracted=False, legal_currentness='not_verified', whole_state_complete=False)


def read_index(path: Path, expected_sha256: str) -> Index:
    """Read bounded ordinary index/schema files and require the exact closed schema."""
    raw = prior.ordinary(path.parent, path.name)
    schema = prior.ordinary(path.parent, 'INDEX.schema.json')
    if coverage.sha(raw) != expected_sha256:
        raise ValueError('Index pin differs')
    if json.loads(schema) != Index.model_json_schema():
        raise ValueError('Index schema differs')
    return Index.model_validate_json(raw, strict=True)


def main() -> int:
    """Run the closed, offline verification without altering the repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--index-sha256', required=True)
    parser.add_argument('--publication-root', type=Path)
    args = parser.parse_args()
    index = read_index(args.index, args.index_sha256)
    result = verify(args.root.resolve(), index, publication_root=args.publication_root)
    sys.stdout.write(json.dumps(result, sort_keys=True) + '\n')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
