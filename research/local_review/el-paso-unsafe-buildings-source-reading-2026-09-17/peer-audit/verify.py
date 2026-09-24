"""Read-only audit closure/native verifier; this cannot automate visual judgment."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pymupdf

from models import Asset, Audit, Manifest


def require(value: bool, message: str) -> None:
    """Fail closed on a mismatched binding."""
    if not value:
        raise ValueError(message)


def bound(root: Path, item: Asset) -> bytes:
    """Capture and hash one ordinary, contained file once."""
    relative = Path(item.path)
    require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe path')
    path = root / relative
    require(not path.is_symlink() and path.is_file(), 'Ordinary file required')
    require(path.resolve().is_relative_to(root.resolve()), 'Outside packet')
    data = path.read_bytes()
    require(len(data) == item.size_bytes, 'Size mismatch: ' + item.path)
    require(hashlib.sha256(data).hexdigest() == item.sha256, 'Hash mismatch: ' + item.path)
    return data


def main() -> None:
    """Replay strict schemas, closed membership, native excerpts and optional Git identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((root / 'MANIFEST.json').read_bytes())
    require(manifest.exclusions == ['MANIFEST.json'], 'Unexpected exclusion')
    expected = {a.path for a in manifest.files}
    require(len(expected) == len(manifest.files), 'Duplicate manifest member')
    actual = set()
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Symlink refused')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == expected | {'MANIFEST.json'}, 'Closed inventory mismatch')
    captured = {a.path: bound(root, a) for a in manifest.files}
    audit = Audit.model_validate_json(captured['AUDIT.json'])
    for name, model in [('AUDIT', Audit), ('MANIFEST', Manifest)]:
        require(json.loads(captured[name + '.schema.json']) == model.model_json_schema(),
                'Schema differs: ' + name)
    target = json.loads(captured[audit.target_manifest.path])
    prefix = 'reviewed-target/'
    for item in target['files']:
        ref = Asset.model_validate(item)
        data = captured[prefix + ref.path]
        require(len(data) == ref.size_bytes and hashlib.sha256(data).hexdigest() == ref.sha256,
                'Target member differs')
    require({p.removeprefix(prefix) for p in captured if p.startswith(prefix)}
            == {a['path'] for a in target['files']} | {'MANIFEST.json'}, 'Target closure')
    review = json.loads(captured[audit.review.path])
    jsonschema.Draft202012Validator(
        json.loads(captured[prefix + 'REVIEW.schema.json'])).validate(review)
    source = captured[audit.source.path]
    require(hashlib.sha256(source).hexdigest()
            == '86eed9d885a9cec1cb01528318f66f8eed525ddb0860655a1983865bfa196d00',
            'Fixed source differs')
    doc = pymupdf.open(stream=source, filetype='pdf')
    require(len(doc) == 8, 'Physical page count')
    for crop in audit.supplementary_crops:
        data = doc[crop.physical_page - 1].get_pixmap(
            matrix=pymupdf.Matrix(3, 3),
            clip=pymupdf.Rect(*crop.rectangle_points), alpha=False).tobytes('png')
        require(data == captured[crop.image.path], 'Supplementary crop replay differs')
    texts = [page.get_text() for page in doc]
    native = ''.join(f'=== PHYSICAL PDF PAGE {i + 1} ===\n{t}'
                     for i, t in enumerate(texts)).encode()
    require(native == captured[audit.native.path], 'Native re-extraction differs')
    require([p.physical_page for p in audit.pages] == list(range(1, 9)), 'Visual scope')
    require([p['physical_page'] for p in review['inspected_pages']] == list(range(1, 9)),
            'Reviewed page scope')
    for page, text in zip(review['inspected_pages'], texts, strict=True):
        require(page['native_text_characters'] == len(text), 'Native page length')
    for finding in review['findings']:
        excerpt = finding['candidate_excerpt']
        start, end = finding['candidate_character_start'], finding['candidate_character_end']
        if excerpt is None:
            require(start is None and end is None, 'Invented omitted-region offset')
        else:
            require(isinstance(start, int) and isinstance(end, int), 'Missing offset')
            require(texts[finding['page'] - 1][start:end] == excerpt, 'Finding span mismatch')
    require(len(review['findings']) == 23, 'Finding count')
    record_bytes = captured[prefix + 'inputs/canonical-record.jsonl']
    record = json.loads(record_bytes)
    require(record['record_id'] == audit.source_id, 'Source identity')
    require(record['sha256'] == audit.source.sha256, 'Canonical source digest')
    require(record['received_at'] == audit.canonical.actual_repository_received_at,
            'Receipt time differs')
    if args.repo:
        binding = audit.canonical
        refs = [binding.raw_manifest, binding.intake_ledger, binding.source, binding.inventory]
        blobs = {}
        for ref in refs:
            data = subprocess.check_output(
                ['git', 'show', f'{binding.commit}:{ref.path}'], cwd=args.repo)
            require(len(data) == ref.size_bytes and hashlib.sha256(data).hexdigest() == ref.sha256,
                    'Canonical input pin differs')
            blobs[ref.path] = data
        require(blobs[binding.raw_manifest.path].splitlines(keepends=True)
                [binding.raw_line - 1] == record_bytes, 'Raw exact line differs')
        require(blobs[binding.intake_ledger.path].splitlines(keepends=True)
                [binding.ledger_line - 1] == record_bytes, 'Ledger exact line differs')
        require(blobs[binding.source.path] == source, 'Canonical PDF differs')
        row = json.loads(blobs[binding.inventory.path])['sources'][binding.inventory_source_index]
        require(row['record_id'] == audit.source_id and row['authority_id'] == audit.authority_id,
                'Authority identity differs')
        require(row['verified_http_acquired_at'] is None, 'Unexpected HTTP promotion')
    sys.stdout.write('PASS: closed audit, exact target, eight native pages, 23 finding '
                     'bindings; visual judgments and legal currentness are not automated.\n')


if __name__ == '__main__':
    main()
