"""Replay this closed local evidence package without requests or repository writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import jsonschema
import pymupdf
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from capture import Event, Link, Parsed, Ref, Reservation, SENSITIVE  # noqa: E402
from closure_models import (  # noqa: E402
    AdditionalRender, AttemptLog, Backlog, Baseline, MethodReceipt, Verification,
)
from inspect_pdfs import Document  # noqa: E402
from review_models import Comparison, Discovery, LegacyMatch, Manifest  # noqa: E402


def require(condition: bool, message: str) -> None:
    """Reject inconsistencies explicitly, including under optimized Python."""
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    """Measure exact bytes."""
    return hashlib.sha256(data).hexdigest()


def confined(name: str) -> Path:
    """Reject absolute, dot-segment and symlinked evidence references."""
    part = Path(name)
    require(not part.is_absolute() and bool(part.parts), 'Invalid relative path')
    require(all(x not in {'.', '..'} for x in part.parts), 'Dot path component')
    require(part.as_posix() == name and '\\' not in name, 'Noncanonical path')
    result = HERE
    for component in part.parts:
        result = result / component
        require(not result.is_symlink(), 'Symlinked evidence')
    require(result.is_file(), 'Missing evidence file: ' + name)
    return result


def read_ref(record: Ref) -> bytes:
    """Verify each referenced payload before returning exact bytes."""
    data = confined(record.path).read_bytes()
    require(len(data) == record.bytes and digest(data) == record.sha256,
            'Reference mismatch: ' + record.path)
    return data


def load_model(name: str, model: Any, schema: str) -> Any:
    """Validate strict Pydantic and exported JSON Schema representations."""
    data = confined(name).read_bytes()
    value = model.model_validate_json(data)
    jsonschema.Draft202012Validator(json.loads(confined(schema).read_bytes())).validate(
        json.loads(data))
    return value


def inventory() -> Manifest:
    """Require every ordinary payload and directory in the closed manifest."""
    manifest = load_model('FINAL_MANIFEST.json', Manifest, 'FINAL_MANIFEST.schema.json')
    names = [x.path for x in manifest.assets]
    require(len(names) == len(set(names)), 'Duplicate manifest path')
    require('FINAL_MANIFEST.json' not in names, 'Recursive manifest')
    actual = set()
    directories = set()
    for path in HERE.rglob('*'):
        require(not path.is_symlink(), 'Symlink in closed package')
        if path.is_file():
            actual.add(path.relative_to(HERE).as_posix())
        elif path.is_dir():
            directories.add(path.relative_to(HERE).as_posix())
        else:
            raise ValueError('Nonregular package entry')
    require(actual == set(names) | {'FINAL_MANIFEST.json'}, 'Unlisted or missing payload')
    expected_dirs = {parent.as_posix() for name in actual for parent in Path(name).parents
                     if parent != Path('.')}
    require(directories == expected_dirs, 'Unlisted or empty directory')
    for asset in manifest.assets:
        read_ref(asset)
        private = asset.path.startswith('events/') and asset.path.endswith('/private.headers')
        require((asset.visibility == 'local_only_private_headers') == private,
                'Private-header custody classification mismatch')
    return manifest


def walk_objects(value: Any) -> list[dict[str, Any]]:
    """Enumerate existing registry objects without inventing source identities."""
    if isinstance(value, dict):
        return [value] + [row for x in value.values() for row in walk_objects(x)]
    if isinstance(value, list):
        return [row for x in value for row in walk_objects(x)]
    return []


def verify_headers(event: Event) -> bool:
    """Replay sanitized derivatives locally without displaying sensitive values."""
    kept, removed, dropping = [], set(), False
    location = None
    for line in read_ref(event.private_headers).splitlines(keepends=True):
        if line.startswith((b' ', b'\t')):
            if not dropping:
                kept.append(line)
            continue
        key = line.split(b':', 1)[0].strip().lower()
        dropping = key in SENSITIVE
        if dropping:
            removed.add(key.decode('ascii'))
        else:
            kept.append(line)
        if key == b'location':
            location = urljoin(event.requested_url,
                               line.split(b':', 1)[1].strip().decode('latin-1'))
    require(b''.join(kept) == read_ref(event.public_headers), 'Header derivative mismatch')
    require(sorted(removed) == event.removed_header_names, 'Header-removal metadata mismatch')
    require(location == event.redirect_location, 'Redirect Location mismatch')
    return bool(removed)


def verify_html(event: Event) -> Parsed:
    """Replay untouched HTML decoding, exact anchor order and readable derivative."""
    parsed = load_model(f'events/{event.event_id}/parsed.json', Parsed,
                        'PARSED_HTML.schema.json')
    require(parsed.source == event.body and parsed.event_id == event.event_id,
            'HTML source mismatch')
    match = re.search(r'charset=([^;\s]+)', event.content_type or '', re.I)
    encoding = match[1] if match else 'utf-8'
    require(parsed.encoding == encoding, 'HTML encoding mismatch')
    soup = BeautifulSoup(read_ref(event.body).decode(encoding), 'html.parser')
    links = [Link(url=urljoin(event.final_url or event.requested_url, a['href']),
                  label=a.get_text(' ', strip=True), href=a['href'])
             for a in soup.find_all('a', href=True)]
    require(links == parsed.links, 'HTML anchor mismatch')
    require(parsed.title == (soup.title.get_text(' ', strip=True) if soup.title else ''),
            'HTML title mismatch')
    for node in soup(['script', 'style']):
        node.decompose()
    require(parsed.text == soup.get_text('\n', strip=True), 'HTML text mismatch')
    require(confined(f'readable/{event.event_id}.txt').read_bytes() == parsed.text.encode(),
            'Readable HTML derivative mismatch')
    return parsed


def verify_pdfs(events: dict[str, Event], rerender: bool) -> tuple[dict[str, Document], int]:
    """Reextract every PDF page and optionally rerender every saved full-page PNG."""
    documents = {}
    rendered = 0
    for path in sorted((HERE / 'pdf-evidence').glob('E*/STRUCTURE.json')):
        record = load_model(path.relative_to(HERE).as_posix(), Document,
                            'PDF_STRUCTURE.schema.json')
        require(record.event_id == path.parent.name, 'PDF event identity mismatch')
        require(record.source == events[record.event_id].body, 'PDF original binding mismatch')
        data = read_ref(record.source)
        require(data.startswith(b'%PDF-'), 'Missing PDF magic')
        with pymupdf.open(stream=data, filetype='pdf') as pdf:
            require(not pdf.is_repaired and not pdf.is_encrypted, 'Invalid PDF structure')
            require(not record.repaired and not record.encrypted, 'False PDF metadata')
            require(record.page_count == len(pdf) == len(record.pages), 'PDF page count mismatch')
            require(record.engine == 'PyMuPDF ' + pymupdf.VersionBind, 'PyMuPDF version mismatch')
            require(record.native_method == 'get_text(text, sort=False, flags=195); UTF-8 unchanged'
                    and record.native_review_status == 'machine_native_text_unreviewed'
                    and record.render_dpi == 150, 'PDF method or review status mismatch')
            for number, (page, item) in enumerate(zip(pdf, record.pages), 1):
                require(item.physical_page == number, 'Nonexhaustive PDF page sequence')
                expected = f'pdf-evidence/{record.event_id}/page-{number:04d}.native.txt'
                require(item.native.path == expected, 'Native page path mismatch')
                require(read_ref(item.native) == page.get_text('text', sort=False,
                                                              flags=195).encode('utf-8'),
                        'Native extraction mismatch')
                require(item.width_points == page.rect.width and
                        item.height_points == page.rect.height, 'PDF page geometry mismatch')
                if item.render is not None:
                    require(item.render.path == expected.replace('.native.txt', '.png'),
                            'Render page path mismatch')
                    image = read_ref(item.render)
                    if rerender:
                        require(image == page.get_pixmap(dpi=150, alpha=False).tobytes('png'),
                                'Full-page render mismatch')
                        rendered += 1
            for extra_path in sorted(path.parent.glob('*.additional.json')):
                extra = load_model(extra_path.relative_to(HERE).as_posix(), AdditionalRender,
                                   'ADDITIONAL_RENDER.schema.json')
                require(extra.event_id == record.event_id and extra.source == record.source,
                        'Additional render source mismatch')
                require(1 <= extra.physical_page <= len(pdf), 'Additional render page range')
                expected = (f'pdf-evidence/{record.event_id}/'
                            f'page-{extra.physical_page:04d}.additional.png')
                require(extra.render.path == expected, 'Additional render page binding')
                image = read_ref(extra.render)
                if rerender:
                    require(image == pdf[extra.physical_page - 1].get_pixmap(
                        dpi=150, alpha=False).tobytes('png'), 'Additional render mismatch')
                    rendered += 1
        documents[record.event_id] = record
    require(len(documents) == 8 and sum(x.page_count for x in documents.values()) == 403,
            'PDF corpus count mismatch')
    require(set(documents) == {eid for eid, event in events.items()
                              if read_ref(event.body).startswith(b'%PDF-')},
            'Uninventoried genuine PDF')
    return documents, rendered


def verify_legacy(comparison: Comparison, events: dict[str, Event], pdf_ids: set[str]) -> None:
    """Recompute all cross-owner historical URL/digest comparisons by streaming."""
    require(comparison.legacy_manifest.path ==
            'baseline/_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl', 'Wrong legacy input')
    read_ref(comparison.legacy_manifest)
    matches, found_pdf, selected = [], set(), []
    with confined(comparison.legacy_manifest.path).open('rb') as handle:
        for number, line in enumerate(handle, 1):
            old = json.loads(line)
            if old.get('authority_id') in {'CO-COUNTY-DOUGLAS', 'CO-MUNICIPAL-CASTLE_ROCK'}:
                selected.append(line)
            matching, fields = [], set()
            for eid, event in events.items():
                for key in ['requested_url', 'final_url', 'source_url']:
                    if old.get(key) and old[key] in {event.requested_url, event.final_url}:
                        matching.append(eid)
                        fields.add(key)
                if old.get('sha256') == event.body.sha256 and event.body.bytes:
                    matching.append(eid)
                    fields.add('body_sha256')
                    if eid in pdf_ids:
                        found_pdf.add(eid)
            if matching:
                matches.append(LegacyMatch(
                    line_number=number, line_sha256=digest(line), source_id=old.get('source_id'),
                    authority_id=old.get('authority_id'), source_url=old.get('source_url'),
                    requested_url=old.get('requested_url'), final_url=old.get('final_url'),
                    historical_sha256=old.get('sha256'), matching_event_ids=sorted(set(matching)),
                    match_fields=sorted(fields), historical_raw_path_claim=old.get('raw_path')))
    require(number == 48390 and matches == comparison.matches and len(matches) == 16,
            'Full historical comparison mismatch')
    require(len(selected) == 33 and b''.join(selected) == confined(
        'baseline/selected_authority_legacy_rows.jsonl').read_bytes(), 'Selected legacy lines mismatch')
    require(comparison.absent_pdf_legacy_digest_matches == sorted(pdf_ids - found_pdf)
            and not found_pdf, 'PDF historical digest result mismatch')


def verify(rerender: bool) -> Verification:
    """Check custody, event accounting, source referrals and bounded content evidence."""
    before = confined('FINAL_MANIFEST.json').read_bytes()
    manifest = inventory()
    discovery = load_model('DISCOVERY.json', Discovery, 'DISCOVERY.schema.json')
    comparison = load_model('LEGACY_COMPARISON.json', Comparison, 'LEGACY_COMPARISON.schema.json')
    baseline = load_model('BASELINE_RECEIPT.json', Baseline, 'BASELINE_RECEIPT.schema.json')
    attempts = load_model('ATTEMPT_LOG.json', AttemptLog, 'ATTEMPT_LOG.schema.json')
    backlog = load_model('UNOPENED_BACKLOG.json', Backlog, 'UNOPENED_BACKLOG.schema.json')
    methods = load_model('CAPTURE_METHOD.json', MethodReceipt, 'CAPTURE_METHOD.schema.json')
    for entry in baseline.files:
        read_ref(entry)
    for period in methods.capture_versions:
        read_ref(period.script)
    for name, count in baseline.jsonl_row_counts.items():
        with confined('baseline/' + name).open('rb') as handle:
            actual_count = 0
            for actual_count, line in enumerate(handle, 1):
                json.loads(line)
        require(actual_count == count, 'Baseline JSONL count mismatch')
    for name, text in baseline.lfs_pointers.items():
        require(confined('baseline/' + name).read_bytes() == text.encode(), 'LFS pointer mismatch')
    events, parsed, sensitive = {}, {}, 0
    for number in range(1, 32):
        eid = f'E{number:03d}'
        event = load_model(f'events/{eid}/event.json', Event, 'EVENT.schema.json')
        reserved = load_model(f'events/{eid}/reservation.json', Reservation,
                              'RESERVATION.schema.json')
        require(event.event_id == reserved.event_id == eid and event.requested_url == reserved.url
                and event.basis == reserved.basis and event.started_at == reserved.reserved_at,
                'Request reservation mismatch')
        require(event.started_at <= event.completed_at and
                reserved.maximum_seconds == 30 and reserved.maximum_bytes == 20_000_000,
                'Invalid event timing or limits')
        require(event.legal_currentness == 'not_verified', 'Unsupported legal status')
        if events:
            require(event.started_at >= list(events.values())[-1].completed_at, 'Events overlap')
        metadata = read_ref(event.metadata).decode('utf-8', errors='replace').splitlines()
        status = int(metadata[0]) if metadata and metadata[0].isdigit() and int(metadata[0]) else None
        require(event.http_status == status and event.final_url == metadata[1] and
                event.content_type == (metadata[2] if len(metadata) > 2 else None),
                'Curl metadata mismatch')
        require(event.outcome == ('http_response' if status is not None else 'transport_failure'),
                'Outcome attribution mismatch')
        read_ref(event.body)
        read_ref(event.stderr)
        sensitive += verify_headers(event)
        events[eid] = event
        if status == 200 and event.curl_exit == 0 and 'html' in (event.content_type or ''):
            parsed[eid] = verify_html(event)
    require(attempts.events == list(events.values()), 'Consolidated attempt log mismatch')
    counts = Counter(str(e.http_status) for e in events.values() if e.http_status)
    require(dict(counts) == discovery.http_status_counts == {'301': 8, '200': 21, '403': 1},
            'HTTP accounting mismatch')
    require(sensitive == 7 and len({e.requested_url for e in events.values()}) == 30 and
            sum(e.http_status is not None for e in events.values()) == 30 and
            sum(e.body.bytes for e in events.values()) == discovery.retained_response_bytes == 14428668,
            'Event/byte/header counts mismatch')
    require(events['E001'].curl_exit == 6 and events['E001'].http_status is None and
            all(e.curl_exit == 0 for eid, e in events.items() if eid != 'E001'),
            'Transport accounting mismatch')
    require(discovery.public_started_at == events['E001'].started_at and
            discovery.public_finished_at == events['E031'].completed_at, 'Public time range mismatch')
    registries = []
    for name in ['LOCAL_SOURCE_REGISTRY', 'MUNICIPAL_SOURCE_REGISTRY']:
        registries.extend(walk_objects(json.loads(confined(
            f'baseline/_CONTROL_PLANE/{name}.json').read_bytes())))
    require([r.event_id for r in discovery.referrals] == list(events), 'Referral coverage mismatch')
    for referral in discovery.referrals:
        event = events[referral.event_id]
        if referral.type == 'registry_seed':
            candidates = [x for x in registries if x.get('source_id') == referral.seed_source_id]
            require(any(event.requested_url in x.values() for x in candidates), 'Unproved seed URL')
        else:
            parent = events[referral.parent_event]
            require(parent.completed_at <= event.started_at, 'Referral before parent')
            if referral.type == 'redirect':
                require(parent.http_status == 301 and parent.redirect_location == event.requested_url,
                        'Unproved redirect')
            elif referral.type == 'anchor':
                require(event.requested_url in {x.url for x in parsed[parent.event_id].links},
                        'Unproved source anchor')
            else:
                require(parent.curl_exit == 6 and parent.requested_url == event.requested_url,
                        'Invalid DNS route retry')
    documents, rendered = verify_pdfs(events, rerender)
    require(len(discovery.priorities) == 12 and len({p.priority_id for p in discovery.priorities}) == 12,
            'Priority identity mismatch')
    for priority in discovery.priorities:
        event = events[priority.event_id]
        require(priority.url == event.requested_url and priority.body == event.body,
                'Priority source binding mismatch')
        require(priority.pdf_pages == (documents[event.event_id].page_count
                if event.event_id in documents else None), 'Priority page count mismatch')
        require(priority.authority_id == ('CO-COUNTY-DOUGLAS' if priority.event_id in
                {'E018', 'E015', 'E017', 'E019', 'E026', 'E023'} else 'CO-MUNICIPAL-CASTLE_ROCK'),
                'Priority authority mismatch')
        for statement in priority.source_statements:
            excerpt = statement.evidence
            text = read_ref(excerpt.text_file)
            raw = excerpt.text.encode('utf-8')
            require(0 <= excerpt.start_byte < excerpt.end_byte <= len(text) and
                    text[excerpt.start_byte:excerpt.end_byte] == raw and digest(raw) ==
                    excerpt.text_sha256, 'Source statement byte range mismatch')
            read_ref(excerpt.original)
            eid = excerpt.original.path.split('/')[1]
            require(excerpt.original == events[eid].body, 'Statement original mismatch')
            expected = (f'pdf-evidence/{eid}/page-{excerpt.physical_page:04d}.native.txt'
                        if excerpt.physical_page else f'readable/{eid}.txt')
            require(excerpt.text_file.path == expected, 'Statement text/source association mismatch')
    require(len({(r.authority_id, r.category) for r in discovery.checklist}) == 24,
            'Duplicate checklist scope')
    require(all(eid in events for row in discovery.checklist for eid in row.event_ids),
            'Unknown checklist event')
    observations = 0
    for link in discovery.discovered_links:
        require(link.event_ids_opened == [e.event_id for e in events.values()
                if e.requested_url == link.url], 'Opened/unopened link mismatch')
        parts = urlsplit(link.url)
        public = parts.scheme == 'https' and not parts.fragment and not any(
            x in parts.path.lower() for x in ['/admin', '/login', '/email', '/cdn-cgi'])
        expected = ('opened' if link.event_ids_opened else 'unopened' if public
                    else 'not_public_https_source_target')
        require(link.disposition == expected, 'Discovered link disposition mismatch')
        for observation in link.observations:
            source = parsed[observation.event_id].links[observation.anchor_index_zero_based]
            require((source.url, source.href, source.label) ==
                    (link.url, observation.href, observation.label), 'Anchor locator mismatch')
            observations += 1
    require(len(discovery.discovered_links) == 438 and observations ==
            sum(len(p.links) for p in parsed.values()), 'Nonexhaustive observed anchors')
    require(backlog.links == [x for x in discovery.discovered_links if x.disposition == 'unopened']
            and len(backlog.links) == 381, 'Backlog subset mismatch')
    require(len(discovery.viewed_pages) == 14 and len({(x.event_id, x.physical_page)
            for x in discovery.viewed_pages}) == 14, 'Viewed-page record count mismatch')
    for view in discovery.viewed_pages:
        require(view.source == events[view.event_id].body, 'Viewed-page source mismatch')
        read_ref(view.image)
        base = f'pdf-evidence/{view.event_id}/page-{view.physical_page:04d}'
        require(view.image.path in {base + '.png', base + '.additional.png'},
                'Viewed-page image identity mismatch')
    verify_legacy(comparison, events, set(documents))
    require(inventory() == manifest and confined('FINAL_MANIFEST.json').read_bytes() == before,
            'Package changed during validation')
    return Verification(status='passed', payload_files=len(manifest.assets), event_count=31,
        exact_requested_urls=30, pdf_count=8, physical_pages=403, native_pages_replayed=403,
        rendered_pages_replayed=rendered, viewed_page_records=14, historical_rows_streamed=48390,
        legacy_matching_rows=16, unopened_urls=381, private_header_events=7,
        legal_currentness='not_verified', raw_size_probe='historical_local_check_not_replayed_portably')


def main() -> int:
    """Run a deterministic read-only replay from any working directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rerender', action='store_true', help='Replay all 18 saved full-page renders')
    args = parser.parse_args()
    try:
        result = verify(args.rerender)
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 1
    sys.stdout.write(result.model_dump_json(indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
