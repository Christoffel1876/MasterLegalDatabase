"""Portable byte/native/geometry audit; visual judgments remain separately declared."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import pymupdf
from jsonschema import validate as jsonschema_validate
from audit_models import Asset, Audit, Inventory, Geometry, RowGeometry
from html.parser import HTMLParser
from urllib.parse import urljoin
sys.path.insert(0, str(Path(__file__).resolve().parent / 'received'))
from review_models import Review

SOURCE_SHA = '8c6b6176f8617a43c4f4eb422f5c9c7287ffba8f2daee4af803c6831d2682205'
QA_SHA = '34eb66bf9aa073cb065fbc26bdac800f943f39010119010719b123bf36821375'


def sha(data: bytes) -> str:
    """Digest exact bytes."""
    return hashlib.sha256(data).hexdigest()


def safe(root: Path, name: str) -> Path:
    """Admit only ordinary canonical relative files beneath the packet."""
    pure = PurePosixPath(name)
    if (not name or pure.is_absolute() or '\\' in name or
            any(p in ['', '.', '..'] for p in name.split('/'))):
        raise ValueError('Unsafe path')
    result = root.joinpath(*pure.parts)
    if any(p.is_symlink() for p in [result, *result.parents]) or not result.is_file():
        raise ValueError('Nonordinary path')
    return result


def read_asset(root: Path, asset: object) -> bytes:
    """Read already-declared bytes and require exact size/digest."""
    data = safe(root, asset.path).read_bytes()
    if len(data) != asset.size_bytes or sha(data) != asset.sha256:
        raise ValueError('Asset mismatch: ' + asset.path)
    return data


def normalize(text: str) -> str:
    """Normalize disclosed source soft wrapping; retain numeric expressions literally."""
    return ' '.join(text.split()).replace('10- 401', '10-401')


def native_geometry(document: pymupdf.Document) -> dict[tuple[str, int, int], list[float]]:
    """Reproduce source line bounds and exact native offsets from the unchanged PDF."""
    result = {}
    for number, page in enumerate(document, 1):
        offset = 0
        for block in page.get_text('dict', flags=195, sort=False)['blocks']:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                raw = (''.join(s['text'] for s in line['spans']) + '\n').encode()
                result[(f'native/page-{number}.txt', offset, offset + len(raw))] = list(line['bbox'])
                offset += len(raw)
    return result


def verify_qa(root: Path, review: Review) -> dict[str, int]:
    """Check every row, heading, native line, note and exact source crop."""
    data = read_asset(root, review.source)
    if sha(data) != SOURCE_SHA or len(data) != 206144:
        raise ValueError('Wrong fixed source')
    document = pymupdf.open(stream=data, filetype='pdf')
    if len(document) != 2:
        raise ValueError('Wrong page count')
    geometry = native_geometry(document)
    natives = {}
    for number, asset in enumerate(review.native_pages, 1):
        raw = read_asset(root, asset)
        if raw != document[number - 1].get_text('text', flags=195, sort=False).encode():
            raise ValueError('Native text does not reproduce')
        natives[asset.path] = raw
    rows = {r.id: r for r in review.rows}
    passages = {p.id: p for p in review.passages}
    groups = {g.id: g for g in review.groups}
    if list(rows) != [f'R{i:02}' for i in range(1, 50)] or len(groups) != 10:
        raise ValueError('Complete unique ordered rows/groups required')
    used = {}

    def check(span: object, owner: str) -> list[float]:
        """Validate exact source interval and single-owner membership."""
        raw = natives.get(span.path)
        if raw is None or not 0 <= span.start < span.end <= len(raw):
            raise ValueError('Native span bounds')
        selected = raw[span.start:span.end]
        if selected != span.text.encode() or sha(selected) != span.sha256:
            raise ValueError('Native span mismatch')
        key = (span.path, span.start, span.end)
        if key not in geometry:
            raise ValueError('Not a complete original PDF line')
        if key in used:
            raise ValueError('Native line claimed twice')
        used[key] = owner
        return geometry[key]

    for index, row in enumerate(review.rows):
        expected_path = f'native/page-{row.page}.txt'
        if any(s.path != expected_path for s in [*row.application_native, row.fee_native]):
            raise ValueError('Row page mismatch')
        label = normalize(''.join(s.text for s in row.application_native))
        if row.application != label or row.fee != normalize(row.fee_native.text):
            raise ValueError('Row label or fee does not match source')
        boxes = [check(s, row.id) for s in row.application_native]
        fee_box = check(row.fee_native, row.id)
        for left, right in zip(row.application_native, row.application_native[1:]):
            if left.end != right.start:
                raise ValueError('Application continuation is not contiguous')
        if row.fee_native.start != row.application_native[-1].end:
            raise ValueError('Fee belongs to another source row')
        if index + 1 < len(review.rows) and review.rows[index + 1].page == row.page:
            if row.fee_native.end > review.rows[index + 1].application_native[0].start:
                raise ValueError('Fee crosses next application row')
        if abs(boxes[0][1] - fee_box[1]) > 0.1 or fee_box[0] <= boxes[0][0]:
            raise ValueError('Application/fee PDF geometry differs')
        if row.group_id not in groups:
            raise ValueError('Unknown row category')
        expected_notes = ['N03']
        if row.id == 'R38':
            expected_notes.append('N01')
        if row.id == 'R41':
            expected_notes.append('N02')
        if row.id in ['R48', 'R49']:
            expected_notes.append('H01')
        if row.related_note_ids != expected_notes:
            raise ValueError('Required fee qualifications missing or broadened')
    expected_ranges = [(1, 10), (11, 15), (16, 17), (18, 20), (21, 31),
                       (32, 36), (37, 38), (39, 41), (42, 47), (48, 49)]
    for number, group in enumerate(review.groups, 1):
        low, high = expected_ranges[number - 1]
        members = [f'R{i:02}' for i in range(low, high + 1)]
        if group.id != f'G{number:02}' or group.row_ids != members:
            raise ValueError('Category row membership changed')
        if any(rows[i].group_id != group.id for i in members):
            raise ValueError('Row category disagrees with heading')
        if group.pages != sorted({rows[i].page for i in members}):
            raise ValueError('Category physical coverage mismatch')
        if normalize(group.heading_native.text) != group.heading:
            raise ValueError('Category heading does not match source')
        check(group.heading_native, group.id)
        expected_parent = ('LAND USE/DEVELOPMENT APPLICATIONS' if number <= 4 else
                           'LAND DIVISION APPLICATIONS' if number <= 6 else None)
        if group.parent_heading != expected_parent:
            raise ValueError('Category parent mismatch')
    if groups['G05'].heading_on_page2 or groups['G05'].pages != [1, 2]:
        raise ValueError('Subdivision exemption page continuation lost')
    for passage in review.passages:
        if passage.text != normalize(''.join(s.text for s in passage.native)):
            raise ValueError('Passage text differs from full source wording')
        for s in passage.native:
            if s.path != f'native/page-{passage.page}.txt':
                raise ValueError('Passage page mismatch')
            check(s, passage.id)
    scopes = {'N01': ['R38'], 'N02': ['R41'], 'H01': ['R48', 'R49'],
              'N03': list(rows)}
    for identity, required in scopes.items():
        if identity not in passages or passages[identity].applies_to_rows != required:
            raise ValueError('Note/condition source scope altered')
    offsets = {1: 0, 2: 0}
    for line in review.native_lines:
        raw = natives[line.span.path][line.span.start:line.span.end]
        key = (line.span.path, line.span.start, line.span.end)
        if (line.span.start != offsets[line.page] or raw != line.span.text.encode() or
                sha(raw) != line.span.sha256):
            raise ValueError('Native coverage gap or changed line')
        if line.associated_with != used.get(key):
            raise ValueError('Native line association mismatch')
        if raw.strip() and line.associated_with is None:
            raise ValueError('Unassociated source wording')
        offsets[line.page] = line.span.end
    if any(offsets[n] != len(natives[f'native/page-{n}.txt']) for n in [1, 2]):
        raise ValueError('Native source tail omitted')
    for image in review.source_pages:
        read_asset(root, image)
    crops = json.loads(safe(root, 'CROPS.json').read_bytes())
    for entry in crops:
        original = Asset.model_validate(entry['source'])
        retained = Asset.model_validate(entry['crop'])
        pix = pymupdf.Pixmap(read_asset(root, original))
        rect = pymupdf.IRect(entry['rect'])
        if not pymupdf.IRect(0, 0, pix.width, pix.height).contains(rect):
            raise ValueError('Crop outside source page')
        crop = pymupdf.Pixmap(pix.colorspace, rect, pix.alpha)
        crop.copy(pix, rect)
        if crop.tobytes('png') != read_asset(root, retained):
            raise ValueError('Crop does not reproduce')
    return {'pages': 2, 'rows': 49, 'groups': 10, 'native_lines': len(review.native_lines),
            'native_bytes': sum(map(len, natives.values())), 'crops': len(crops)}


class Links(HTMLParser):
    """Parse only retained explicit base/href attributes; never open a URL."""
    def __init__(self) -> None:
        super().__init__()
        self.bases = []
        self.hrefs = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag.lower() == 'base' and values.get('href'):
            self.bases.append(values['href'])
        if tag.lower() == 'a' and values.get('href'):
            self.hrefs.append(values['href'])


def verify_custody(root: Path) -> None:
    """Check exact prior Location to fresh GET and distinguish its source-date role."""
    folder = root / 'custody'
    manifest = json.loads(safe(folder, 'FINAL_MANIFEST.json').read_bytes())
    for value in manifest['files']:
        read_asset(folder, Asset.model_validate(value))
    plan = json.loads(safe(folder, 'PLAN.json').read_bytes())
    target = plan['targets'][0]
    prior_root = folder / 'evidence/prior-retrieval'
    prior_plan = json.loads(safe(prior_root, 'PLAN.json').read_bytes())
    original_target = next(t for t in prior_plan['targets']
                           if t['target_id'] == 'CHAFFEE-D003')
    html = read_asset(prior_root, Asset.model_validate(original_target['parent_body']))
    links = Links()
    links.feed(html.decode('utf-8'))
    if (not links.bases or links.bases[0] != original_target['base_href'] or
            original_target['literal_href'] not in links.hrefs or
            urljoin(links.bases[0], original_target['literal_href']).replace(' ', '%20') !=
            target['prior_request_url']):
        raise ValueError('Original catalog/base/referral mismatch')
    prior = json.loads(read_asset(folder, Asset.model_validate(target['prior_actual_result'])))
    if prior['requested_url'] != target['prior_request_url']:
        raise ValueError('Prior action requested a different county URL')
    headers = read_asset(folder, Asset.model_validate(target['prior_public_headers'])).decode()
    locations = [line.split(':', 1)[1].strip() for line in headers.splitlines()
                 if line.lower().startswith('location:')]
    result = json.loads(safe(folder, 'events/A001/RESULT.json').read_bytes())
    reservation = json.loads(safe(folder, 'events/A001/RESERVATION.json').read_bytes())
    if (prior['http_status'] != 302 or locations != [target['raw_location']] or
            target['request_url'] != target['raw_location'].replace(' ', '%20') or
            result['requested_url'] != target['request_url'] or
            result['final_url'] != target['request_url'] or result['http_status'] != 200 or
            result['curl_reported_redirects'] != 0 or not result['body_complete'] or
            result['partial_or_unknown'] or result['tls_verify_result'] != 0 or
            reservation['request_url'] != target['request_url'] or
            reservation['plan_sha256'] != sha(safe(folder, 'PLAN.json').read_bytes())):
        raise ValueError('Actual prior-to-fresh GET chain mismatch')
    redirect = Links()
    redirect.feed(read_asset(folder, Asset.model_validate(target['prior_response_body'])).decode())
    if target['raw_location'] not in redirect.hrefs:
        raise ValueError('Redirect body does not support Location')
    if sha(read_asset(folder, Asset.model_validate(result['body']))) != SOURCE_SHA:
        raise ValueError('Acquired fee body differs from reviewed original')


def validate(root: Path, rerender: str | None = None) -> dict[str, int]:
    """Verify a closed package offline without running a builder or intake."""
    manifest = Inventory.model_validate_json(safe(root, 'FINAL_MANIFEST.json').read_bytes())
    names = [a.path for a in manifest.files]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate inventory entry')
    actual = set()
    for directory, dirs, files in os.walk(root, followlinks=False):
        if any((Path(directory) / d).is_symlink() for d in dirs):
            raise ValueError('Symlink directory')
        for name in files:
            rel = (Path(directory) / name).relative_to(root).as_posix()
            if rel != 'FINAL_MANIFEST.json':
                actual.add(rel)
    if actual != set(names):
        raise ValueError('Closed inventory mismatch')
    for a in manifest.files:
        read_asset(root, a)
    raw = safe(root, 'received/SOURCE_QA.json').read_bytes()
    if sha(raw) != QA_SHA:
        raise ValueError('Original reviewed draft changed')
    review = Review.model_validate_json(raw)
    schema = json.loads(safe(root, 'received/SOURCE_QA.schema.json').read_bytes())
    if schema != Review.model_json_schema():
        raise ValueError('Draft schema mismatch')
    jsonschema_validate(json.loads(raw), schema)
    result = verify_qa(root / 'received', review)
    recorded = Geometry.model_validate_json(safe(root, 'ROW_GEOMETRY.json').read_bytes())
    document = pymupdf.open(root / 'received/source/original.pdf')
    native = native_geometry(document)
    expected = []
    for row in review.rows:
        boxes = [native[(s.path, s.start, s.end)] for s in row.application_native]
        fee = row.fee_native
        expected.append(RowGeometry(row_id=row.id, page=row.page, application_boxes=boxes,
                                    fee_box=native[(fee.path, fee.start, fee.end)],
                                    fee_start=fee.start,
                                    application_end=row.application_native[-1].end))
    if recorded.source_sha256 != SOURCE_SHA or recorded.rows != expected:
        raise ValueError('Recorded row geometry differs from original PDF')
    verify_custody(root)
    if rerender:
        with tempfile.TemporaryDirectory(prefix='chaffee-fee-render-') as tmp:
            proc = subprocess.run([rerender, '-r', '300', '-png',
                                   str(root / 'received/source/original.pdf'),
                                   str(Path(tmp) / 'page')], capture_output=True, timeout=60)
            if proc.returncode:
                raise ValueError('Renderer failed')
            for n, a in enumerate(review.source_pages, 1):
                if sha((Path(tmp) / f'page-{n}.png').read_bytes()) != a.sha256:
                    raise ValueError('Full image does not reproduce')
    result['payloads'] = len(names)
    return result


def main() -> None:
    """Read only the specified package, with an optional renderer path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--pdftoppm')
    args = parser.parse_args()
    sys.stdout.write(json.dumps({'status': 'pass', **validate(args.root, args.pdftoppm)}) + '\n')


if __name__ == '__main__':
    main()
