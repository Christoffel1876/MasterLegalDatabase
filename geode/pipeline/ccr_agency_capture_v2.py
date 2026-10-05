"""Offline whole-rule CCR selections with complete retained catalog denominators.

This v2 format is deliberately separate from departmental publisher inputs and v1.
It performs no HTTP, legal-text extraction, canonical installation or activation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qs, urlparse

import pymupdf as fitz
from pydantic import AwareDatetime, Field, field_validator, model_validator

from . import ccr_current as ccr
from .ccr_agency_capture import Asset, Strict, atomic_new, bounded, encoded, ordinary, sha

MAX_FILE_BYTES = 15_000_000
MAX_PACKAGE_BYTES = 50_000_000
MAX_INPUT_BYTES = 48_000_000
MAX_MEMBERS = 100
MAX_ASSOCIATIONS = 80
MAX_METADATA_BYTES = 1_000_000
MAX_PDF_PAGES = 20_000
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Numeric = Annotated[str, Field(pattern=r'^[0-9]+$', max_length=20)]
Role = Literal['welcome', 'catalog', 'listing', 'history', 'pdf', 'word']


def official_url(value: str) -> str:
    """Reject URL ambiguity before using the maintained exact source resolver."""
    if re.search(r'[\x00-\x20\x7f\\]', value):
        raise ValueError('Whitespace, controls or backslashes in source URL')
    ccr.require_sos_url(value)
    parsed = urlparse(value)
    if parsed.fragment or parsed.username or parsed.password:
        raise ValueError('Unexpected source URL fragment or credentials')
    pairs = parse_qs(parsed.query, keep_blank_values=True)
    if any(len(values) != 1 or not values[0] for values in pairs.values()):
        raise ValueError('Duplicate or empty source URL parameter')
    return value


class ReceiptClaim(Strict):
    """Nonsecret historical claims; opaque receipt pins are not transport attestations."""

    receipt_sha256: Digest
    requested_url: str
    observed_final_url: str | None = None
    started_at: AwareDatetime
    finished_at: AwareDatetime
    http_status: Literal[200]
    content_type: str = Field(min_length=1, max_length=200, pattern=r'^[\x20-\x7e]+$')
    charged_bytes: int = Field(ge=1, le=MAX_FILE_BYTES)

    _url = field_validator('requested_url')(official_url)

    @field_validator('observed_final_url')
    @classmethod
    def optional_final_url(cls, value: str | None) -> str | None:
        """Preserve missing final-URL observations instead of inventing them."""
        return official_url(value) if value is not None else None

    @model_validator(mode='after')
    def consistent(self) -> ReceiptClaim:
        """This offline contract accepts only complete, nonredirected response claims."""
        if (self.finished_at < self.started_at or (self.observed_final_url is not None
                and self.requested_url != self.observed_final_url)):
            raise ValueError('Response interval or exact final URL differs')
        return self


class Response(Strict):
    """One retained response association, with no asserted rule identity or free label."""

    association_id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
    role: Role
    parent_id: str | None = Field(default=None, pattern=r'^[A-Za-z0-9_-]{1,80}$')
    body: Asset
    claim: ReceiptClaim

    @model_validator(mode='after')
    def conservative_charge(self) -> Response:
        """Retained bytes are a minimum conservative charge for each URL association."""
        if self.claim.charged_bytes < self.body.bytes:
            raise ValueError('Charged bytes cannot be smaller than the retained response body')
        return self


class Selection(Strict):
    """A whole rule selected by the two observed numeric source identities."""

    agency_id: Numeric
    rule_id: Numeric


class Plan(Strict):
    """Pinned bounded offline inputs; source labels and denominators are derived."""

    schema_version: Literal['ccr-agency-selection-plan-2'] = 'ccr-agency-selection-plan-2'
    department_id: Numeric
    provenance_sha256: list[Digest] = Field(min_length=1, max_length=20)
    selections: list[Selection] = Field(min_length=1, max_length=25)
    responses: list[Response] = Field(min_length=5, max_length=MAX_ASSOCIATIONS)
    document_policy: Literal['all_source_nonarchived_pdf_word_pairs'] = (
        'all_source_nonarchived_pdf_word_pairs')
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False

    @model_validator(mode='after')
    def unique(self) -> Plan:
        """Reject duplicate selectors, response IDs and URL associations."""
        selectors = [(item.agency_id, item.rule_id) for item in self.selections]
        ids = [item.association_id for item in self.responses]
        urls = [item.claim.requested_url for item in self.responses]
        if (len(set(selectors)) != len(selectors) or len(set(ids)) != len(ids)
                or len(set(urls)) != len(urls)
                or len(set(self.provenance_sha256)) != len(self.provenance_sha256)):
            raise ValueError('Duplicate selection, association, URL or provenance pin')
        return self


class Link(Strict):
    """Exact parsed parent attribute and label, without executing source JavaScript."""

    parent_id: str
    child_id: str
    attribute_name: Literal['href', 'onclick']
    attribute: str
    label: str


class RuleRow(Strict):
    """Every source listing row, including unselected rules with unknown documents."""

    rule_id: Numeric
    source_citation: str
    source_title: str
    history_url: str
    selected: bool
    document_status: Literal['selected_pairs_retained_unreviewed', 'unknown_not_selected']


class AgencyRow(Strict):
    """A complete catalog row; only selected agencies have a retained listing scope."""

    agency_id: Numeric
    source_label: str
    listing_url: str
    selected: bool
    listing_association_id: str | None
    listed_rule_count: int | None = Field(ge=0)
    rules: list[RuleRow]
    unselected_status: Literal['unknown_not_evaluated'] = 'unknown_not_evaluated'


class VersionRow(Strict):
    """Source-owned version labels and dates, never a legal-currentness decision."""

    version_id: Numeric
    designation: Literal['current', 'future', 'history', 'unknown']
    source_label: str
    effective_date: date | None
    adopted_date: date | None
    publication_date: date | None
    filing_type: str | None
    document_urls: list[str]
    edocket_urls: list[str]
    selected: bool
    omission: Literal['archived_not_selected'] | None


class RuleCapture(Strict):
    """Complete parsed history, with archived rows explicitly excluded from acquisition."""

    agency_id: Numeric
    rule_id: Numeric
    source_citation: str
    listing_title: str
    history_title: str
    history_association_id: str
    versions: list[VersionRow]


class DocumentCheck(Strict):
    """Structural PDF parsing or Word signature observation; no content verification."""

    association_id: str
    role: Literal['pdf', 'word']
    sha256: Digest
    pages: int | None = Field(ge=1, le=MAX_PDF_PAGES)
    status: Literal['pdf_parsed_unreviewed', 'word_signature_only_unparsed']


class Capture(Strict):
    """Portable replay derived solely from verified captured source buffers."""

    schema_version: Literal['ccr-agency-offline-capture-2'] = 'ccr-agency-offline-capture-2'
    status: Literal['offline_selected_whole_rules_replayed'] = (
        'offline_selected_whole_rules_replayed')
    input_plan_sha256: Digest
    public_plan_sha256: Digest
    department_id: Numeric
    source_department_label: str
    source_cutoff_claim: date
    catalog_agency_count: int = Field(ge=1)
    selected_agency_count: int = Field(ge=1)
    selected_rule_count: int = Field(ge=1, le=25)
    response_associations: int = Field(le=MAX_ASSOCIATIONS)
    distinct_body_count: int = Field(ge=1)
    retained_unique_body_bytes: int = Field(le=MAX_INPUT_BYTES)
    charged_response_bytes_claim: int = Field(le=MAX_PACKAGE_BYTES)
    observed_start_claim: AwareDatetime
    observed_finish_claim: AwareDatetime
    agencies: list[AgencyRow]
    selected_rules: list[RuleCapture]
    links: list[Link]
    documents: list[DocumentCheck]
    department_complete: Literal[False] = False
    existing_department_publisher_admissible: Literal[False] = False
    canonical_installation: Literal[False] = False
    fresh_requests: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    limitations: list[str]


class Manifest(Strict):
    """Closed v2 file identities; manifest bytes also count toward the physical cap."""

    schema_version: Literal['ccr-agency-capture-manifest-2'] = 'ccr-agency-capture-manifest-2'
    files: list[Asset] = Field(max_length=MAX_MEMBERS - 1)
    excluded: Literal['MANIFEST.json'] = 'MANIFEST.json'

    @model_validator(mode='after')
    def closed(self) -> Manifest:
        """Reject duplicate, unordered, self-listed and excessive payloads."""
        paths = [ref.path for ref in self.files]
        if (paths != sorted(set(paths)) or 'MANIFEST.json' in paths
                or sum(ref.bytes for ref in self.files) > MAX_PACKAGE_BYTES):
            raise ValueError('Invalid closed inventory or package cap')
        return self


def _sources(plan: Plan, buffers: dict[str, bytes]) -> dict[str, bytes]:
    refs: dict[str, Asset] = {}
    for response in plan.responses:
        ref = response.body
        if ref.path in refs and refs[ref.path] != ref:
            raise ValueError('Conflicting body identity')
        refs[ref.path] = ref
    if len(refs) > MAX_MEMBERS - 6 or sum(ref.bytes for ref in refs.values()) > MAX_INPUT_BYTES:
        raise ValueError('Input body budget exceeded')
    result = {}
    for path, ref in refs.items():
        raw = buffers.get(path)
        if raw is None or len(raw) != ref.bytes or sha(raw) != ref.sha256:
            raise ValueError('Captured source identity differs')
        result[path] = raw
    return result


def _linked(parent: Response, child: Response, document: ccr._Document) -> Link:
    attr = 'onclick' if child.role in {'pdf', 'word'} else 'href'
    matches = []
    if attr == 'onclick':
        for anchor in document.root.nodes('a'):
            if 'OpenRule' in anchor.attrs.get(attr, ''):
                _, target = ccr._document_link(anchor, parent.claim.requested_url)
                if target == child.claim.requested_url:
                    matches.append((anchor.attrs[attr], anchor.text()))
    else:
        endpoint = urlparse(child.claim.requested_url).path.rsplit('/', 1)[-1]
        matches = [(anchor.attrs[attr], anchor.text()) for url, anchor in
                   ccr._links(document, parent.claim.requested_url, endpoint)
                   if url == child.claim.requested_url]
    if not matches or len(set(matches)) != 1:
        raise ValueError('Missing or ambiguous exact parent source link')
    return Link(parent_id=parent.association_id, child_id=child.association_id,
                attribute_name=attr, attribute=matches[0][0], label=matches[0][1])


def _document_check(response: Response, raw: bytes) -> DocumentCheck:
    pages = None
    status = 'word_signature_only_unparsed'
    if response.role == 'pdf':
        if not raw.startswith(b'%PDF-'):
            raise ValueError('PDF signature differs')
        with fitz.open(stream=raw, filetype='pdf') as document:
            if document.is_encrypted or document.is_repaired or len(document) < 1:
                raise ValueError('PDF is empty, encrypted or repaired')
            pages = len(document)
        status = 'pdf_parsed_unreviewed'
    elif not raw.startswith((b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', b'PK\x03\x04')):
        raise ValueError('Word signature differs; body is not an admitted source document')
    return DocumentCheck(association_id=response.association_id, role=response.role,
                         sha256=sha(raw), pages=pages, status=status)


def derive(plan: Plan, buffers: dict[str, bytes], input_pin: str) -> Capture:
    """Replay complete source tables, exact selected joins, formats and bounded accounting."""
    sources = _sources(plan, buffers)
    responses = {item.association_id: item for item in plan.responses}
    by_url = {item.claim.requested_url: item for item in plan.responses}
    documents = {}
    links = []
    seen = set()
    for item in plan.responses:
        role_path = {'welcome': 'Welcome.do', 'catalog': 'NumericalDeptList.do',
                     'listing': 'NumericalCCRDocList.do', 'history': 'DisplayRule.do',
                     'pdf': 'GenerateRulePdf.do', 'word': 'GenerateRulePdf.do'}[item.role]
        if urlparse(item.claim.requested_url).path != '/CCR/' + role_path:
            raise ValueError('Response role endpoint differs')
        if item.role not in {'pdf', 'word'}:
            parsed = ccr._parse_html(sources[item.body.path], item.claim.content_type)
            if parsed.root.nodes('base'):
                raise ValueError('HTML base overrides are unsupported')
            documents[item.association_id] = parsed
        if item.role == 'welcome':
            if item.parent_id is not None or item.claim.requested_url != ccr.WELCOME_URL:
                raise ValueError('Invalid welcome seed')
        else:
            if item.parent_id not in seen or item.parent_id not in documents:
                raise ValueError('Parent is absent, later, or not HTML')
            links.append(_linked(responses[item.parent_id], item,
                                 documents[item.parent_id]))
        seen.add(item.association_id)
    welcomes = [r for r in plan.responses if r.role == 'welcome']
    catalogs = [r for r in plan.responses if r.role == 'catalog']
    if (len(welcomes) != 1 or len(catalogs) != 1
            or catalogs[0].parent_id != welcomes[0].association_id):
        raise ValueError('Exactly one welcome and its catalog are required')
    welcome, catalog = welcomes[0], catalogs[0]
    cutoff = ccr._cutoff(documents[welcome.association_id], welcome.claim.finished_at.date())
    roster = ccr._agencies(documents[catalog.association_id], catalog.claim.requested_url,
                           plan.department_id)
    selected = {(item.agency_id, item.rule_id) for item in plan.selections}
    selected_agencies = {item.agency_id for item in plan.selections}
    if not selected_agencies <= set(roster):
        raise ValueError('Selected agency is absent from complete catalog')
    expected = {welcome.association_id, catalog.association_id}
    agencies = []
    rule_captures = []
    checks = []
    for aid, (listing_url, label, _) in sorted(roster.items(), key=lambda pair: int(pair[0])):
        rules = []
        listing = None
        if aid in selected_agencies:
            listing = by_url.get(listing_url)
            if (listing is None or listing.role != 'listing'
                    or listing.parent_id != catalog.association_id):
                raise ValueError('Selected listing is missing or has wrong parent/role')
            expected.add(listing.association_id)
            source_rules = ccr._rules(documents[listing.association_id], listing_url)
            if not {rid for agency, rid in selected if agency == aid} <= set(source_rules):
                raise ValueError('Selected rule absent from complete listing')
            for rid, (history_url, citation, title) in source_rules.items():
                chosen = (aid, rid) in selected
                rules.append(RuleRow(rule_id=rid, source_citation=citation, source_title=title,
                                     history_url=history_url, selected=chosen, document_status=(
                                         'selected_pairs_retained_unreviewed' if chosen
                                         else 'unknown_not_selected')))
                if not chosen:
                    continue
                history = by_url.get(history_url)
                if (history is None or history.role != 'history'
                        or history.parent_id != listing.association_id):
                    raise ValueError('Selected history is missing or has wrong parent/role')
                expected.add(history.association_id)
                parsed = documents[history.association_id]
                versions = ccr._versions(parsed, history_url)
                version_rows = []
                for version in versions:
                    chosen_version = version.designation != 'history'
                    version_rows.append(VersionRow(
                        version_id=version.version_id, designation=version.designation,
                        source_label=version.source_label, effective_date=version.effective_date,
                        adopted_date=version.adopted_date,
                        publication_date=version.publication_date,
                        filing_type=version.filing_type, document_urls=version.document_urls,
                        edocket_urls=version.edocket_urls,
                        selected=chosen_version,
                        omission=None if chosen_version else 'archived_not_selected'))
                    if not chosen_version:
                        continue
                    if len(version.document_urls) != 2:
                        raise ValueError(
                            'Whole-rule selection requires a displayed PDF and Word pair')
                    roles = set()
                    for url in version.document_urls:
                        child = by_url.get(url)
                        word = parse_qs(urlparse(url).query).get('type') == ['word']
                        role = 'word' if word else 'pdf'
                        if (child is None or child.role != role
                                or child.parent_id != history.association_id):
                            raise ValueError('Selected document pair missing or wrong parent/role')
                        roles.add(role)
                        expected.add(child.association_id)
                        checks.append(_document_check(child, sources[child.body.path]))
                    if roles != {'pdf', 'word'}:
                        raise ValueError('Source pair does not contain both formats')
                rule_captures.append(RuleCapture(
                    agency_id=aid, rule_id=rid, source_citation=citation, listing_title=title,
                    history_title=ccr._title(parsed), history_association_id=history.association_id,
                    versions=version_rows))
        agencies.append(AgencyRow(
            agency_id=aid, source_label=label, listing_url=listing_url,
            selected=aid in selected_agencies,
            listing_association_id=listing.association_id if listing else None,
            listed_rule_count=len(rules) if listing else None, rules=rules))
    if expected != set(responses):
        raise ValueError('Extra or missing associations beyond selected whole-rule scope')
    if sum(check.pages or 0 for check in checks) > MAX_PDF_PAGES:
        raise ValueError('Aggregate PDF page cap exceeded')
    return Capture(
        input_plan_sha256=input_pin, public_plan_sha256=sha(encoded(plan)),
        department_id=plan.department_id, source_department_label=next(iter(roster.values()))[2],
        source_cutoff_claim=cutoff, catalog_agency_count=len(roster),
        selected_agency_count=len(selected_agencies), selected_rule_count=len(selected),
        response_associations=len(plan.responses), distinct_body_count=len(sources),
        retained_unique_body_bytes=sum(map(len, sources.values())),
        charged_response_bytes_claim=sum(r.claim.charged_bytes for r in plan.responses),
        observed_start_claim=min(r.claim.started_at for r in plan.responses),
        observed_finish_claim=max(r.claim.finished_at for r in plan.responses),
        agencies=agencies, selected_rules=rule_captures, links=links, documents=checks,
        limitations=[
            'Offline historical evidence replay; no fresh requests or canonical installation.',
            'Catalog and selected listings are complete only within the retained source snapshots.',
            'Unselected agencies/rules and archived documents remain unknown, not absent.',
            'Source labels, cutoff and response times are claims; observations may span dates.',
            'A null final URL means the retained receipt did not record one.',
            'No legal currentness, visible fidelity, native extraction or PDF/Word equivalence.',
            'Word has a recognized signature only; its structure and contents are unparsed.',
            'Opaque receipt pins and claims do not independently prove original transport.',
        ])


def schemas() -> dict[str, bytes]:
    """Return all deterministic public schemas before writing any metadata."""
    return {name + '.schema.json': (json.dumps(model.model_json_schema(), indent=2) + '\n').encode()
            for name, model in [('Plan', Plan), ('Capture', Capture), ('Manifest', Manifest)]}


def build(input_root: Path, plan_path: Path, output: Path, plan_sha256: str) -> Manifest:
    """Capture verified input buffers and atomically write fresh members, manifest last."""
    ordinary(output)
    if output.exists():
        raise ValueError('Output already exists; partial outputs cannot be resumed')
    raw_plan = bounded(plan_path, MAX_METADATA_BYTES)
    if sha(raw_plan) != plan_sha256:
        raise ValueError('Plan pin differs')
    plan = Plan.model_validate_json(raw_plan)
    # Bound declared totals before any source read, then verify each captured buffer once.
    refs = {item.body.path: item.body for item in plan.responses}
    if (len(refs) > MAX_MEMBERS - 6
            or sum(ref.bytes for ref in refs.values()) > MAX_INPUT_BYTES):
        raise ValueError('Input body budget exceeded')
    buffers = {path: bounded(input_root / path, ref.bytes) for path, ref in refs.items()}
    _sources(plan, buffers)
    public = plan.model_dump(mode='json')
    bodies = {}
    for response in public['responses']:
        previous = response['body']['path']
        target = 'bodies/' + response['body']['sha256'] + '.bin'
        response['body']['path'] = target
        bodies[target] = buffers[previous]
    public_plan = Plan.model_validate_json(json.dumps(public))
    record = derive(public_plan, bodies, plan_sha256)
    payload = {**schemas(), 'PLAN.json': encoded(public_plan),
               'CAPTURE.json': encoded(record), **bodies}
    manifest = Manifest(files=[Asset(path=name, sha256=sha(body), bytes=len(body))
                               for name, body in sorted(payload.items())])
    if any(len(payload[name]) > MAX_METADATA_BYTES
           for name in [*schemas(), 'PLAN.json', 'CAPTURE.json']):
        raise ValueError('Public metadata cap exceeded')
    manifest_bytes = encoded(manifest)
    if sum(map(len, payload.values())) + len(manifest_bytes) > MAX_PACKAGE_BYTES:
        raise ValueError('Closed package including manifest exceeds cap')
    output.mkdir(parents=True, exist_ok=False)
    for name, body in payload.items():
        atomic_new(output / name, body)
    atomic_new(output / 'MANIFEST.json', manifest_bytes)
    return manifest


def verify(root: Path, manifest_sha256: str) -> Capture:
    """Verify exact closed members and replay a relocated v2 capture without input paths."""
    raw_manifest = bounded(root / 'MANIFEST.json', MAX_METADATA_BYTES)
    if sha(raw_manifest) != manifest_sha256:
        raise ValueError('Manifest pin differs')
    manifest = Manifest.model_validate_json(raw_manifest)
    if sum(ref.bytes for ref in manifest.files) + len(raw_manifest) > MAX_PACKAGE_BYTES:
        raise ValueError('Closed package including manifest exceeds cap')
    actual = set()
    for path in root.rglob('*'):
        ordinary(path)
        if path.is_dir():
            if path != root / 'bodies':
                raise ValueError('Unexpected output directory')
        else:
            if not path.is_file():
                raise ValueError('Nonregular package member')
            actual.add(path.relative_to(root).as_posix())
    if actual != {ref.path for ref in manifest.files} | {'MANIFEST.json'}:
        raise ValueError('Closed package membership differs')
    buffers = {}
    for ref in manifest.files:
        if not ref.path.startswith('bodies/') and ref.bytes > MAX_METADATA_BYTES:
            raise ValueError('Public metadata cap exceeded')
        raw = bounded(root / ref.path, ref.bytes)
        if len(raw) != ref.bytes or sha(raw) != ref.sha256:
            raise ValueError('Manifest member identity differs')
        buffers[ref.path] = raw
    if any(buffers.get(name) != raw for name, raw in schemas().items()):
        raise ValueError('Schema differs')
    plan = Plan.model_validate_json(buffers['PLAN.json'])
    record = Capture.model_validate_json(buffers['CAPTURE.json'])
    for response in plan.responses:
        if response.body.path != 'bodies/' + response.body.sha256 + '.bin':
            raise ValueError('Public body path is not content-addressed')
    expected = {r.body.path for r in plan.responses} | {'PLAN.json', 'CAPTURE.json', *schemas()}
    if set(buffers) != expected:
        raise ValueError('Unexpected public member')
    if record != derive(plan, buffers, record.input_plan_sha256):
        raise ValueError('Derived capture differs')
    return record


def main(argv: list[str] | None = None) -> int:
    """Expose only offline build and pinned read-only verification."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('build')
    create.add_argument('--input-root', type=Path, required=True)
    create.add_argument('--plan', type=Path, required=True)
    create.add_argument('--plan-sha256', required=True)
    create.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('verify')
    check.add_argument('--root', type=Path, required=True)
    check.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args(argv)
    if args.command == 'build':
        manifest = build(args.input_root, args.plan, args.output, args.plan_sha256)
        result = {'manifest_sha256': sha(encoded(manifest)), 'fresh_requests': 0}
    else:
        record = verify(args.root, args.manifest_sha256)
        result = {'status': record.status, 'rules': record.selected_rule_count,
                  'catalog_agencies': record.catalog_agency_count, 'department_complete': False}
    sys.stdout.write(json.dumps(result, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
