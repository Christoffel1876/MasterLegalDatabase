"""Offline agency-scope replay; no network or departmental publication contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import stat
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import parse_qs, quote, urljoin, urlsplit

import pymupdf as fitz
from bs4 import BeautifulSoup
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from geode.pipeline import ccr_current as ccr

MAX_FILE_BYTES = 15_000_000
MAX_PACKAGE_BYTES = 50_000_000
MAX_MEMBERS = 100

class Strict(BaseModel):
    """Reject unspecified scope or custody claims."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Exact contained file identity."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    bytes: int = Field(ge=0, le=15000000)

    @model_validator(mode='after')
    def contained(self) -> Asset:
        """Reject noncanonical, absolute, symlink-escaping or traversal paths."""
        path = PurePosixPath(self.path)
        if (path.is_absolute() or '..' in path.parts or '\\' in self.path
                or str(path) != self.path or self.path in ('', '.')):
            raise ValueError('Unsafe asset path')
        return self


class HistoricalReceipt(Strict):
    """Public field projection of a private-header-bearing historical receipt."""
    original_receipt_path_claim: str
    original_receipt_sha256: str
    original_receipt_bytes: int
    historical_sequence: int
    requested_url: str
    recorded_started_at: AwareDatetime
    recorded_finished_at: AwareDatetime
    recorded_http_status: Literal[200]
    recorded_result: Literal['returned']
    content_type: str
    body: Asset
    recorded_charged_bytes: int
    private_headers_copied: Literal[False]
    projection: Literal['only explicit nonsecret URL/time/status/body/content-type fields retained']


class Agency(Strict):
    """One identity from the complete retained department catalog."""
    agency_id: str
    name: str
    original_href: str
    observed_url: str
    selected: bool
    expected_rule_count: int | None
    catalog: Asset


class Target(Strict):
    """One ordered exact historical request, not a newly activated request."""
    sequence: int = Field(ge=1, le=65)
    target_id: str
    role: Literal['welcome', 'catalog', 'agency_listing', 'rule_history', 'pdf', 'word']
    department_id: Literal['16']
    agency_id: Literal['137', '138', '140'] | None
    rule_id: str | None
    source_citation: str | None
    version_id: str | None
    source_designation: Literal['current', 'future', 'unknown'] | None
    requested_url: str
    parent_target_id: str | None
    observed_attribute: str | None
    attribute_kind: Literal['href', 'onclick', 'historically_requested_seed']
    resolution_method: str
    source_label_claim: str | None
    historical: HistoricalReceipt

    @model_validator(mode='after')
    def role_fields(self) -> Target:
        """Require exact meaningful identity fields and null unused source-role claims."""
        fields = ('agency_id', 'rule_id', 'source_citation', 'version_id',
                  'source_designation', 'source_label_claim')
        required = {
            'welcome': (), 'catalog': (), 'agency_listing': ('agency_id',),
            'rule_history': ('agency_id', 'rule_id', 'source_citation'),
            'pdf': fields, 'word': fields,
        }[self.role]
        if any((getattr(self, name) is not None) != (name in required) for name in fields):
            raise ValueError('Source role has missing or invented identity/label fields')
        return self


class Caps(Strict):
    """Proposed ceilings only; fresh activation is mandatory."""
    status: Literal['proposed_not_active']
    actual_http_events: Literal[80]
    distinct_requested_urls: Literal[80]
    response_bytes: Literal[15000000]
    aggregate_received_body_bytes: Literal[50000000]
    automatic_retries: Literal[0]
    automatic_redirects: Literal[0]
    timeout_seconds_per_event: Literal[30]
    overall_elapsed_seconds: Literal[900]
    activation_at: None
    public_stop_at: None
    reservation_before_request: Literal[True]


class Plan(Strict):
    """Fixed three-agency proposal, explicitly outside the departmental publisher."""
    schema_version: Literal['ccr16-agency-capture-plan-1']
    status: Literal['prepared_not_activated_not_acquired']
    prepared_at: AwareDatetime
    checkpoint_commit_claim: Literal['da3ba811be1599c77ad25fc1c135f3bd6108294d']
    checkpoint_basis: Literal[
        'root-provided commit; actual working input hashes independently pinned']
    department_id: Literal['16']
    department_name: Literal['1000 Department of Public Health and Environment']
    selected_agency_ids: list[Literal['137', '138', '140']]
    department_catalog_agencies: list[Agency] = Field(min_length=18, max_length=18)
    targets: list[Target] = Field(min_length=65, max_length=65)
    frozen_inputs: list[Asset]
    historical_rule_count: Literal[20]
    historical_url_associations: Literal[65]
    historical_distinct_urls: Literal[65]
    historical_received_body_bytes: int = Field(ge=1, le=50000000)
    historical_bytes_are_future_guarantee: Literal[False]
    shared_discovery_associations: Literal[2]
    shared_discovery_bytes: int = Field(ge=1, le=50000000)
    caps: Caps
    accounting_policy: list[str]
    success_criteria: list[str]
    failure_criteria: list[str]
    limitations: list[str]
    full_department_discovery: Literal[False]
    existing_department_publisher_admissible: Literal[False]
    department16_complete: Literal[False]
    review_required: Literal[True]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    new_public_requests: Literal[0]

    @model_validator(mode='after')
    def identities(self) -> Plan:
        """Forbid duplicate scope, missing targets and fabricated department completeness."""
        if self.selected_agency_ids != ['137', '138', '140']:
            raise ValueError('Exact selected agency order differs')
        ids = [a.agency_id for a in self.department_catalog_agencies]
        if len(set(ids)) != 18 or sum(a.selected for a in self.department_catalog_agencies) != 3:
            raise ValueError('Complete catalog denominator differs')
        if [t.sequence for t in self.targets] != list(range(1, 66)):
            raise ValueError('Ordered inventory has a gap or duplicate')
        if len({t.target_id for t in self.targets}) != 65:
            raise ValueError('Duplicate target identity')
        if len({t.requested_url for t in self.targets}) != 65:
            raise ValueError('Duplicate requested URL')
        return self


def query(url: str, key: str) -> str:
    """Require one unambiguous requested identity value."""
    values = parse_qs(urlsplit(url).query, keep_blank_values=True).get(key, [])
    if len(values) != 1:
        raise ValueError(f'Expected one source {key}')
    return values[0]


def resolve(base: str, href: str) -> str:
    """Use the maintained literal-space encoding convention for observed hrefs."""
    target = quote(urljoin(base, href), safe=":/?&=%+;,@-._~!$'()*[]")
    p = urlsplit(target)
    if p.scheme != 'https' or p.netloc != 'www.sos.state.co.us' or not p.path.startswith('/CCR/'):
        raise ValueError('Not an exact official CCR target')
    return target


def document_target(base: str, handler: str) -> tuple[str, str]:
    """Resolve the two observed SOS handlers without executing JavaScript."""
    pattern = r"\s*OpenRule(Window|WordVersion)\(\s*'([0-9]+)'\s*,\s*'([^']+)'\s*\)\s*;?\s*"
    match = re.fullmatch(pattern, handler)
    if match is None:
        raise ValueError('Unknown source document handler')
    prefix = 'type=word&' if match[1] == 'WordVersion' else ''
    return match[2], resolve(base, f'/CCR/GenerateRulePdf.do?{prefix}'
                            f'ruleVersionId={match[2]}&fileName={quote(match[3])}')


def soup(raw: bytes) -> BeautifulSoup:
    """Parse retained exact HTML as its recorded ISO-8859-1 source encoding."""
    return BeautifulSoup(raw.decode('iso-8859-1'), 'html.parser')


def observed_anchor(raw: bytes, base: str, target: str, kind: str) -> tuple[str, str]:
    """Find an exact literal href/handler that produces the observed target URL."""
    matches = []
    for anchor in soup(raw).find_all('a'):
        value = anchor.get(kind)
        if not value:
            continue
        try:
            resolved = (document_target(base, value)[1] if kind == 'onclick'
                        else resolve(base, value))
        except ValueError:
            continue
        if resolved == target:
            matches.append((value, anchor.get_text(' ', strip=True)))
    if not matches or len(set(matches)) != 1:
        raise ValueError('Missing or conflicting exact source anchor')
    return matches[0]


def roster(raw: bytes, base: str) -> list[dict[str, str]]:
    """Read the entire retained department-16 section, not only selected agencies."""
    document = soup(raw)
    heading = document.find('a', attrs={'name': '1000'})
    if heading is None:
        raise ValueError('Missing complete department heading')
    row = heading.find_parent('tr')
    if 'Department of Public Health and Environment' not in row.get_text(' ', strip=True):
        raise ValueError('Wrong department section')
    rows = []
    for following in row.find_next_siblings('tr'):
        if following.find('a', attrs={'name': True}):
            break
        anchors = following.find_all('a', href=True)
        if len(anchors) != 1 or len(following.find_all('td', recursive=False)) != 2:
            raise ValueError('Malformed department agency row')
        href = anchors[0]['href']; target = resolve(base, href)
        if query(target, 'deptID') != '16':
            raise ValueError('Foreign department agency')
        rows.append({'agency_id': query(target, 'agencyID'), 'name': query(target, 'agencyName'),
                     'original_href': href, 'observed_url': target})
    if len(rows) != 18 or len({x['agency_id'] for x in rows}) != 18:
        raise ValueError('Department agency denominator differs')
    return rows


EXPECTED_IDS = {'132', '137', '138', '140', '141', '142', '143', '144', '145',
                '146', '147', '15', '167', '170', '201', '207', '209', '7'}


def validate(plan: Plan, captured: dict[str, bytes]) -> dict[str, object]:
    """Recount complete roster, exact source joins and historical scope only."""
    for target in plan.targets:
        ref = target.historical.body
        if ref.path != f'bodies/{ref.sha256}.bin':
            raise ValueError('Body path is not its exact digest identity')
    bodies = {target.target_id: captured[target.historical.body.path] for target in plan.targets}
    parsed_html = {target.target_id: ccr._parse_html(
        bodies[target.target_id], target.historical.content_type)
        for target in plan.targets if target.role not in ('pdf', 'word')}
    by_id = {target.target_id: target for target in plan.targets}
    catalog = plan.targets[1]
    observed_roster = roster(bodies[catalog.target_id], catalog.requested_url)
    expected_roster = [{key: getattr(a, key) for key in
                       ['agency_id', 'name', 'original_href', 'observed_url']}
                      for a in plan.department_catalog_agencies]
    roster_ids = {a.agency_id for a in plan.department_catalog_agencies}
    if observed_roster != expected_roster or roster_ids != EXPECTED_IDS:
        raise ValueError('Full retained catalog roster differs')
    for agency in plan.department_catalog_agencies:
        if (agency.selected != (agency.agency_id in plan.selected_agency_ids) or
                agency.catalog != catalog.historical.body or
                agency.expected_rule_count != {'137': 7, '138': 7, '140': 6}.get(agency.agency_id)):
            raise ValueError('Selected versus unselected scope differs')
    if [t.historical.historical_sequence for t in plan.targets] != [1, 2, *range(133, 196)]:
        raise ValueError('Historical request order differs')
    rules = [t for t in plan.targets if t.role == 'rule_history']
    if len({t.rule_id for t in rules}) != 20:
        raise ValueError('Duplicate or missing selected rule identity')
    for target in plan.targets:
        historical = target.historical
        if target.role not in ('pdf', 'word') and target.source_label_claim is not None:
            raise ValueError('Unexpected label claim outside a document version row')
        if (target.requested_url != historical.requested_url or
                historical.recorded_charged_bytes != historical.body.bytes or
                historical.recorded_started_at > historical.recorded_finished_at):
            raise ValueError('Historical receipt projection mismatch')
        parts = urlsplit(target.requested_url)
        if parts.scheme != 'https' or parts.netloc != 'www.sos.state.co.us':
            raise ValueError('Unexpected requested source authority')
        if target.sequence == 1:
            if (target.role != 'welcome' or parts.path != '/CCR/Welcome.do'
                    or target.parent_target_id):
                raise ValueError('Historical welcome seed differs')
            continue
        parent = by_id.get(target.parent_target_id)
        if parent is None or parent.sequence >= target.sequence:
            raise ValueError('Missing or nonpreceding exact parent')
        attr, _ = observed_anchor(bodies[parent.target_id], parent.requested_url,
                                  target.requested_url, target.attribute_kind)
        if attr != target.observed_attribute:
            raise ValueError('Observed source attribute differs')
        if target.role == 'catalog':
            if parent.role != 'welcome' or parts.path != '/CCR/NumericalDeptList.do':
                raise ValueError('Catalog parent differs')
        elif target.role == 'agency_listing':
            if (parent.role != 'catalog'
                    or query(target.requested_url, 'agencyID') != target.agency_id):
                raise ValueError('Agency parent differs')
            if query(target.requested_url, 'deptID') != '16':
                raise ValueError('Foreign department')
            strict_rules = ccr._rules(parsed_html[target.target_id], target.requested_url)
            listing_links = []
            for anchor in soup(bodies[target.target_id]).find_all('a', href=True):
                if 'DisplayRule.do' in anchor['href']:
                    listing_links.append(resolve(target.requested_url, anchor['href']))
            children = [t.requested_url for t in rules if t.parent_target_id == target.target_id]
            expected_count = {'137': 7, '138': 7, '140': 6}[target.agency_id]
            strict_links = [value[0] for value in strict_rules.values()]
            if (sorted(listing_links) != sorted(children) or len(children) != expected_count
                    or sorted(strict_links) != sorted(children)):
                raise ValueError('Full selected agency rule listing differs')
        elif target.role == 'rule_history':
            if (parent.role != 'agency_listing' or parent.agency_id != target.agency_id or
                    query(target.requested_url, 'ruleId') != target.rule_id or
                    query(target.requested_url, 'agencyID') != target.agency_id or
                    query(target.requested_url, 'deptID') != '16' or
                    query(target.requested_url, 'seriesNum') != target.source_citation):
                raise ValueError('Rule identity/agency/citation differs')
            versions = ccr._versions(parsed_html[target.target_id], target.requested_url)
            wanted = [(url, version.version_id, version.designation, version.source_label)
                      for version in versions if version.designation != 'history'
                      for url in version.document_urls]
            children = [(t.requested_url, t.version_id, t.source_designation, t.source_label_claim)
                        for t in plan.targets if t.parent_target_id == target.target_id]
            if sorted(wanted) != sorted(children):
                raise ValueError('Selected document/version/source-label associations differ')
        elif target.role in {'pdf', 'word'}:
            if (parent.role != 'rule_history' or parent.agency_id != target.agency_id or
                    parent.rule_id != target.rule_id or
                    parent.source_citation != target.source_citation or
                    query(target.requested_url, 'ruleVersionId') != target.version_id or
                    query(target.requested_url, 'fileName') != target.source_citation):
                raise ValueError('Document association differs')
            kind = parse_qs(parts.query, keep_blank_values=True).get('type')
            if kind != (['word'] if target.role == 'word' else None):
                raise ValueError('Document URL format role differs')
            signature = bodies[target.target_id]
            if target.role == 'pdf' and not signature.startswith(b'%PDF-'):
                raise ValueError('Wrong PDF signature')
            if (target.role == 'word'
                    and not signature.startswith((b'\xd0\xcf\x11\xe0', b'PK\x03\x04'))):
                raise ValueError('Wrong Word signature')
    counts = Counter(t.role for t in plan.targets)
    if counts != {'welcome': 1, 'catalog': 1, 'agency_listing': 3,
                  'rule_history': 20, 'pdf': 20, 'word': 20}:
        raise ValueError('Target role counts differ')
    observed_bytes = sum(t.historical.body.bytes for t in plan.targets)
    if observed_bytes != plan.historical_received_body_bytes:
        raise ValueError('Historical body count differs')
    agency_counts = {}
    for aid in plan.selected_agency_ids:
        selected = [t for t in plan.targets if t.agency_id == aid]
        agency_counts[aid] = {'rules': sum(t.role == 'rule_history' for t in selected),
                             'url_associations': len(selected),
                             'historical_body_bytes': sum(
                                 t.historical.body.bytes for t in selected)}
    return {'status': 'passed', 'roster_agencies': 18, 'selected_agencies': 3,
            'unselected_agencies': 15, 'rules': 20, 'url_associations': 65,
            'historical_body_bytes': observed_bytes, 'agency_counts': agency_counts,
            'new_public_requests': 0, 'activated': False, 'department_complete': False}



class DocumentCheck(Strict):
    """Structural disposition only, never visible accuracy or Word/PDF equivalence."""
    target_id: str
    role: Literal['pdf', 'word']
    sha256: str
    status: Literal['pdf_parsed_unreviewed', 'word_signature_only_unparsed']
    pages: int | None = Field(ge=1)


class Capture(Strict):
    """Portable offline scope, with the entire source catalog and explicit unknowns."""
    schema_version: Literal['ccr-agency-offline-capture-1'] = 'ccr-agency-offline-capture-1'
    status: Literal['historical_agency_scope_replayed'] = 'historical_agency_scope_replayed'
    input_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    projection: Literal['receipt_paths_and_nonbody_inputs_omitted'] = (
        'receipt_paths_and_nonbody_inputs_omitted')
    plan: Plan
    unselected_agency_ids: list[str]
    unselected_status: Literal['unknown_not_evaluated'] = 'unknown_not_evaluated'
    observed_start_claim: AwareDatetime
    observed_finish_claim: AwareDatetime
    classification_cutoff: None = None
    cutoff_policy: Literal['historical_source_labels_not_reclassified'] = (
        'historical_source_labels_not_reclassified')
    document_checks: list[DocumentCheck]
    department_complete: Literal[False] = False
    existing_department_publisher_admissible: Literal[False] = False
    canonical_installation: Literal[False] = False
    fresh_requests: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    limitations: list[str]


class ClosedManifest(Strict):
    """One exact bounded offline output; not a departmental state or inventory."""
    schema_version: Literal['ccr-agency-capture-manifest-1'] = 'ccr-agency-capture-manifest-1'
    files: list[Asset]
    excluded: Literal['MANIFEST.json'] = 'MANIFEST.json'

    @model_validator(mode='after')
    def closed(self) -> ClosedManifest:
        """Reject duplicate or excessive members before consuming output files."""
        paths = [item.path for item in self.files]
        if (paths != sorted(set(paths)) or 'MANIFEST.json' in paths
                or len(paths) > MAX_MEMBERS
                or sum(item.bytes for item in self.files) > MAX_PACKAGE_BYTES):
            raise ValueError('Invalid closed membership or aggregate cap')
        return self


def sha(data: bytes) -> str:
    """Hash the exact captured buffer."""
    return hashlib.sha256(data).hexdigest()


def ordinary(path: Path) -> None:
    """Reject symlinks including parents before any input or output operation."""
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('Symlink input/output refused')


def bounded(path: Path, limit: int) -> bytes:
    """Read one ordinary file at most one byte beyond its explicit limit."""
    ordinary(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise ValueError('Input is not a bounded regular file')
    with path.open('rb') as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError('File size cap exceeded')
    return data


def load_inputs(root: Path, plan_sha256: str) -> tuple[Plan, dict[str, bytes]]:
    """Capture a caller-pinned plan and all identities without importing packet code."""
    raw = bounded(root / 'PLAN.json', 1_000_000)
    if sha(raw) != plan_sha256:
        raise ValueError('Plan pin differs')
    plan = Plan.model_validate_json(raw)
    refs = [target.historical.body for target in plan.targets] + plan.frozen_inputs
    indexed: dict[str, Asset] = {}
    for ref in refs:
        if ref.path in indexed and indexed[ref.path] != ref:
            raise ValueError('Conflicting input identity')
        indexed[ref.path] = ref
    if (len(indexed) > MAX_MEMBERS - 5
            or sum(ref.bytes for ref in indexed.values()) > MAX_PACKAGE_BYTES - 2_000_000):
        raise ValueError('Input package cap exceeded')
    captured = {'PLAN.json': raw}
    for ref in indexed.values():
        body = bounded(root / ref.path, ref.bytes)
        if len(body) != ref.bytes or sha(body) != ref.sha256:
            raise ValueError('Captured source identity differs')
        captured[ref.path] = body
    return plan, captured


def derive(plan: Plan, captured: dict[str, bytes], input_plan_sha256: str) -> Capture:
    """Derive scope exclusively from captured identities and complete source joins."""
    validate(plan, captured)
    starts = [target.historical.recorded_started_at for target in plan.targets]
    finishes = [target.historical.recorded_finished_at for target in plan.targets]
    if any(a > b for a, b in zip(finishes, starts[1:])):
        raise ValueError('Historical request intervals overlap or are out of order')
    if sum(t.historical.body.bytes for t in plan.targets[:2]) != plan.shared_discovery_bytes:
        raise ValueError('Shared discovery accounting differs')
    checks = []
    for target in plan.targets:
        if target.role not in ('pdf', 'word'):
            continue
        raw = captured[target.historical.body.path]
        pages = None
        status = 'word_signature_only_unparsed'
        if target.role == 'pdf':
            with fitz.open(stream=raw, filetype='pdf') as document:
                if document.is_encrypted or document.is_repaired or len(document) < 1:
                    raise ValueError('PDF is empty, encrypted or repaired')
                pages = len(document)
            status = 'pdf_parsed_unreviewed'
        checks.append(DocumentCheck(target_id=target.target_id, role=target.role,
                                    sha256=sha(raw), status=status, pages=pages))
    return Capture(
        input_plan_sha256=input_plan_sha256, plan_sha256=sha(captured['PLAN.json']), plan=plan,
        unselected_agency_ids=[a.agency_id for a in plan.department_catalog_agencies
                               if not a.selected],
        observed_start_claim=min(starts), observed_finish_claim=max(finishes),
        document_checks=checks,
        limitations=[
            'Offline replay of retained historical evidence; no new acquisition or activation.',
            'Full 18-agency catalog retained; 15 unselected agencies have '
            'unknown unreviewed scope.',
            'Source current/future labels and request times are preserved claims, not current law.',
            'PDF parsing is structural only; legacy Word signatures are not complete '
            'format validation.',
            'No native extraction, visible review, Word/PDF equivalence or '
            'departmental publication.',
            'Private-header receipts remain outside this output; public projections '
            'do not prove TLS.',
        ],
    )


def schemas() -> dict[str, bytes]:
    """Publish deterministic schemas before any new metadata record."""
    return {name + '.schema.json': (json.dumps(model.model_json_schema(), indent=2) + '\n').encode()
            for name, model in [('Capture', Capture), ('Manifest', ClosedManifest)]}


def encoded(model: BaseModel) -> bytes:
    """Round-trip a strict model before writing its new record."""
    data = (model.model_dump_json(indent=2) + '\n').encode()
    type(model).model_validate_json(data)
    return data


def atomic_new(path: Path, body: bytes) -> None:
    """Atomically publish a fresh member, retaining a partial temp on interruption."""
    ordinary(path)
    if path.exists():
        raise ValueError('Output member already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    ordinary(temporary)
    with temporary.open('xb') as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    if path.exists():
        raise ValueError('Output member appeared during write')
    os.replace(temporary, path)


def build(root: Path, output: Path, plan_sha256: str) -> ClosedManifest:
    """Create one fresh self-contained output; interrupted output is never overwritten."""
    ordinary(output)
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output cannot be inside the immutable input package')
    if output.exists():
        raise ValueError('Output already exists; use a new directory')
    plan, captured = load_inputs(root, plan_sha256)
    derive(plan, captured, plan_sha256)
    public = plan.model_dump(mode='json')
    public['frozen_inputs'] = []
    for target in public['targets']:
        target['historical']['original_receipt_path_claim'] = ''
    public_plan = Plan.model_validate_json(json.dumps(public))
    public_inputs = {target.historical.body.path: captured[target.historical.body.path]
                     for target in plan.targets}
    public_inputs['PLAN.json'] = encoded(public_plan)
    record = derive(public_plan, public_inputs, plan_sha256)
    payload = {**schemas(), **public_inputs, 'CAPTURE.json': encoded(record)}
    manifest = ClosedManifest(files=[Asset(path=name, sha256=sha(body), bytes=len(body))
                                    for name, body in sorted(payload.items())])
    output.mkdir(parents=True, exist_ok=False)
    for name, body in payload.items():
        atomic_new(output / name, body)
    atomic_new(output / 'MANIFEST.json', encoded(manifest))
    return manifest


def verify(root: Path, manifest_sha256: str) -> Capture:
    """Verify a relocated closed package and deterministically replay captured source joins."""
    raw = bounded(root / 'MANIFEST.json', 1_000_000)
    if sha(raw) != manifest_sha256:
        raise ValueError('Manifest pin differs')
    manifest = ClosedManifest.model_validate_json(raw)
    actual = set()
    for path in root.rglob('*'):
        ordinary(path)
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != {ref.path for ref in manifest.files} | {'MANIFEST.json'}:
        raise ValueError('Closed package membership differs')
    captured = {}
    for ref in manifest.files:
        body = bounded(root / ref.path, ref.bytes)
        if len(body) != ref.bytes or sha(body) != ref.sha256:
            raise ValueError('Manifest member differs')
        captured[ref.path] = body
    for name, body in schemas().items():
        if captured.get(name) != body:
            raise ValueError('Schema differs')
    record = Capture.model_validate_json(captured['CAPTURE.json'])
    plan = Plan.model_validate_json(captured['PLAN.json'])
    expected_members = {t.historical.body.path for t in plan.targets} | {
        'PLAN.json', 'CAPTURE.json', *schemas()}
    if set(captured) != expected_members:
        raise ValueError('Unexpected public capture member')
    # Explicitly rebind every plan reference to already captured manifest bytes.
    for ref in [t.historical.body for t in plan.targets] + plan.frozen_inputs:
        body = captured.get(ref.path)
        if body is None or len(body) != ref.bytes or sha(body) != ref.sha256:
            raise ValueError('Plan/member identity differs')
    if (plan.frozen_inputs or any(t.historical.original_receipt_path_claim for t in plan.targets)):
        raise ValueError('Private provenance is not permitted in public capture')
    if record != derive(plan, captured, record.input_plan_sha256):
        raise ValueError('Derived agency record differs')
    return record


def main(argv: list[str] | None = None) -> int:
    """Expose only fresh offline capture and read-only verification commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('build')
    create.add_argument('--input', type=Path, required=True)
    create.add_argument('--plan-sha256', required=True)
    create.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('verify')
    check.add_argument('--root', type=Path, required=True)
    check.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args(argv)
    if args.command == 'build':
        build(args.input, args.output, args.plan_sha256)
        output = {'manifest_sha256': sha((args.output / 'MANIFEST.json').read_bytes())}
    else:
        record = verify(args.root, args.manifest_sha256)
        output = {'status': record.status, 'rules': record.plan.historical_rule_count,
                  'agencies_selected': len(record.plan.selected_agency_ids),
                  'department_complete': False, 'fresh_requests': 0}
    sys.stdout.write(json.dumps(output, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
