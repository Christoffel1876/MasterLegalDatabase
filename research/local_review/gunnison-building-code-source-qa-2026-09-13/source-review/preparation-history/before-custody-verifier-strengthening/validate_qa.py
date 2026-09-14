"""Read-only portable integrity replay; this cannot independently certify visual judgments."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import pymupdf
from jsonschema import validate as schema_validate
from models import Asset, Manifest, OCRResult, ProcessReceipt, Review, Span
from crop_tools import Crops, crop_bytes

SOURCE_SHA = '41dc3a6c962039878f4b49212c07e289a8658903dd63a9980e68ecdee9cc9b7b'
QA_SHA = 'be0c13e2b4ebdd9e83475aa2456a08df2f9eb64fa7c24c8ca6130ddb6e013b11'


def digest(data: bytes) -> str:
    """Return the exact byte digest."""
    return hashlib.sha256(data).hexdigest()


def ordinary(path: Path) -> None:
    """Reject a nonordinary file or symlink anywhere in its ancestry."""
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError('Symlink refused')
    if not path.is_file():
        raise ValueError('Ordinary file required')


def local(root: Path, name: str) -> Path:
    """Resolve a canonical relative path without leaving the package."""
    pure = PurePosixPath(name)
    if (not name or pure.is_absolute() or '\\' in name or
            any(x in ['', '.', '..'] for x in name.split('/'))):
        raise ValueError('Unsafe package path')
    result = root.joinpath(*pure.parts)
    ordinary(result)
    return result


def content(root: Path, asset: Asset) -> bytes:
    """Verify exact bytes before returning an in-memory immutable buffer."""
    path = local(root, asset.path)
    data = path.read_bytes()
    if len(data) != asset.size_bytes or digest(data) != asset.sha256:
        raise ValueError(f'Asset mismatch: {asset.path}')
    return data


def check_span(span: Span, texts: dict[int, bytes]) -> None:
    """Reject truncated, out-of-page or changed transcript intervals."""
    data = texts.get(span.page)
    if data is None or not 0 <= span.start < span.end <= len(data):
        raise ValueError('Span bounds invalid')
    selected = data[span.start:span.end]
    if selected != span.text.encode() or digest(selected) != span.sha256:
        raise ValueError('Transcript span mismatch')


def verify_manifest(root: Path) -> Manifest:
    """Require all and only the closed inventory's ordinary payload files."""
    path = local(root, 'FINAL_MANIFEST.json')
    manifest = Manifest.model_validate_json(path.read_bytes())
    names = [a.path for a in manifest.files]
    if len(names) != len(set(names)) or 'FINAL_MANIFEST.json' in names:
        raise ValueError('Duplicate or self-referential manifest')
    actual = set()
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise ValueError('Symlink directory refused')
        for name in files:
            candidate = Path(directory) / name
            ordinary(candidate)
            relative = candidate.relative_to(root).as_posix()
            if relative != 'FINAL_MANIFEST.json':
                actual.add(relative)
    if actual != set(names):
        raise ValueError('Closed payload set mismatch')
    for asset in manifest.files:
        content(root, asset)
    return manifest


def expected_parent(label: str) -> str:
    """Preserve visually reviewed indentation for the 27 design entries."""
    if label in ['Speed (mph)', 'Topographic effects', 'Special wind region',
                 'Windborne debris zone']:
        return 'Wind Design'
    if label in ['Weathering', 'Frost line depth', 'Termite']:
        return 'Subject to Damage from'
    if label in ['Ground Snow Load', 'Seismic Design Category',
                 'Ice Barrier Underlayment Required', 'Flood Hazards',
                 'Air Freezing Index', 'Mean Annual Temp']:
        return 'Table R301.2 Climatic and Geographic Design Criteria'
    return 'Manual J Design Criteria'


def verify_review(root: Path, review: Review) -> dict[str, int]:
    """Replay source/custody, complete transcript partitions and classified associations."""
    source = content(root, review.source)
    if digest(source) != SOURCE_SHA or len(source) != 682037:
        raise ValueError('Wrong fixed source')
    document = pymupdf.open(stream=source, filetype='pdf')
    if len(document) != 16:
        raise ValueError('Wrong source page count')
    texts = {p.number: content(root, p.transcript) for p in review.pages}
    blocks = {}
    machine_lines = 0
    for page in review.pages:
        image = pymupdf.Pixmap(content(root, page.image))
        if [image.width, image.height] != [page.image_width, page.image_height]:
            raise ValueError('Full image dimensions differ')
        native = document[page.number - 1].get_text('text', flags=195, sort=False).encode()
        if native or content(root, page.native):
            raise ValueError('Expected genuinely empty native text')
        ocr = OCRResult.model_validate_json(content(root, page.ocr))
        expected_text = ('\n'.join(line.text for line in ocr.lines) + '\n').encode()
        if expected_text != content(root, page.ocr_text) or not ocr.lines:
            raise ValueError('OCR candidate changed or empty')
        for line in ocr.lines:
            x, y, width, height = line.bbox
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 <= width <= 1 and 0 <= height <= 1):
                raise ValueError('OCR normalized geometry invalid')
        machine_lines += len(ocr.lines)
        receipt = ProcessReceipt.model_validate_json(
            local(root, f'ocr/receipt-{page.number:04}.json').read_bytes())
        if receipt.returncode or receipt.stdout != page.ocr:
            raise ValueError('OCR receipt mismatch')
        if content(root, receipt.stderr):
            raise ValueError('Successful OCR stderr is not empty')
        offset = 0
        for block in page.blocks:
            check_span(block.span, texts)
            if block.span.page != page.number or block.span.start != offset:
                raise ValueError('Transcript partition gap, overlap or page swap')
            if block.id in blocks:
                raise ValueError('Duplicate block identity')
            x0, y0, x1, y1 = block.pixel_box
            if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
                raise ValueError('Block outside full image')
            blocks[block.id] = block
            offset = block.span.end
        if offset != len(texts[page.number]):
            raise ValueError('Unbound transcript tail')
        for note in page.notes:
            if note.transcript_start is None or note.transcript_end is None:
                raise ValueError('Unbound source note')
            if (texts[page.number][note.transcript_start:note.transcript_end].decode()
                    != note.exact_transcript):
                raise ValueError('Note excerpt mismatch')
            if note.crop:
                content(root, note.crop)
    for page, previous, heading in [(8, 7, 'Table R301.2'), (13, 12, 'Section R401.2')]:
        first = review.pages[page - 1].blocks[0]
        parent = blocks.get(first.continuation_of)
        if not parent or parent.span.page != previous or not parent.span.text.startswith(heading):
            raise ValueError('Required cross-page continuation missing')
    for block in blocks.values():
        if block.continuation_of and block.continuation_of not in blocks:
            raise ValueError('Unknown continuation parent')
    if len(review.associations) != 27:
        raise ValueError('All 27 design entries required')
    labels = set()
    for number, item in enumerate(review.associations, 1):
        check_span(item.span, texts)
        if item.id != f'DESIGN-{number:02}' or item.label in labels:
            raise ValueError('Design entry order or duplicate invalid')
        labels.add(item.label)
        label, value = item.span.text.rstrip('\n').split(':', 1)
        if item.label != label or item.value != value.strip():
            raise ValueError('Design label/value diverges from source span')
        if item.parent_heading != expected_parent(item.label):
            raise ValueError('Design parent heading mismatch')
        if not item.context_block_ids:
            raise ValueError('Design context missing')
        for identity in item.context_block_ids:
            if identity not in blocks:
                raise ValueError('Design context does not exist')
    struck = []
    for marking in review.markings:
        if not 1 <= marking.page <= 16:
            raise ValueError('Marking page invalid')
        if marking.span:
            check_span(marking.span, texts)
            if marking.span.page != marking.page:
                raise ValueError('Marking page mismatch')
        if marking.kind == 'struck':
            struck.append(marking.span.text if marking.span else None)
    if struck != ['International Private Sewage Disposal Code',
                  'private sewage disposal systems', '120']:
        raise ValueError('Struck source text omitted or altered')
    custody = review.custody
    content(root, custody.preparation)
    receipt_data = json.loads(content(root, custody.receipt))
    raw_line = content(root, custody.exact_record)
    manifest_path = local(root, custody.manifest.path)
    content(root, custody.manifest)
    selected = None
    with manifest_path.open('rb') as stream:
        for number, line in enumerate(stream, 1):
            json.loads(line)
            if number == custody.record_line:
                selected = line
    if selected != raw_line:
        raise ValueError('Exact canonical manifest line mismatch')
    record = json.loads(raw_line)
    if (record['record_id'] != review.source_id or record['sha256'] != SOURCE_SHA or
            record['size_bytes'] != len(source) or record['official_source_url'] is not None or
            record['acquisition_method'] != 'received_review_package' or
            record['received_at'] != custody.received_at or
            record['layer_id'] != '08_County_Authorities'):
        raise ValueError('Source custody identity or clock mismatch')
    if not receipt_data:
        raise ValueError('Empty intake receipt')
    crops = Crops.model_validate_json(local(root, 'CROPS.json').read_bytes())
    for crop in crops.crops:
        source_image = local(root, review.pages[crop.page - 1].image.path)
        if crop_bytes(source_image, crop.box) != content(root, crop.image):
            raise ValueError('Crop pixels do not reproduce')
    return {'pages': 16, 'native_bytes': 0, 'transcript_bytes': sum(map(len, texts.values())),
            'blocks': len(blocks), 'design_entries': 27, 'machine_lines': machine_lines,
            'crops': len(crops.crops)}


def rerender(root: Path, review: Review, binary: str) -> None:
    """Optionally replay all full-page Poppler renders in a disposable external directory."""
    with tempfile.TemporaryDirectory(prefix='gunnison-qa-render-') as temporary:
        destination = Path(temporary)
        result = subprocess.run([binary, '-r', '150', '-png',
                                 str(local(root, review.source.path)),
                                 str(destination / 'page')], capture_output=True, timeout=120)
        if result.returncode:
            raise ValueError('Poppler rerender failed')
        for page in review.pages:
            actual = (destination / f'page-{page.number:02}.png').read_bytes()
            if digest(actual) != page.image.sha256:
                raise ValueError('Full-page render mismatch; renderer/version may differ')


def validate(root: Path, render_binary: str | None = None) -> dict[str, int]:
    """Validate a closed packet without reading a repository or running OCR/network."""
    root = root.absolute()
    manifest = verify_manifest(root)
    raw = local(root, 'SOURCE_QA.json').read_bytes()
    if digest(raw) != QA_SHA:
        raise ValueError('Frozen reviewed record changed')
    review = Review.model_validate_json(raw)
    schema = json.loads(local(root, 'SOURCE_QA.schema.json').read_bytes())
    if schema != Review.model_json_schema():
        raise ValueError('Exported schema differs from strict model')
    schema_validate(json.loads(raw), schema)
    result = verify_review(root, review)
    if render_binary:
        rerender(root, review, render_binary)
    result['payload_files'] = len(manifest.files)
    return result


def main() -> None:
    """Run only offline validation and optional full-image reproduction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--rerender', action='store_true')
    parser.add_argument('--pdftoppm', default=shutil.which('pdftoppm'))
    args = parser.parse_args()
    if args.rerender and not args.pdftoppm:
        parser.error('--rerender requires --pdftoppm or pdftoppm on PATH')
    result = validate(args.root, args.pdftoppm if args.rerender else None)
    sys.stdout.write(json.dumps({'status': 'pass', **result}) + '\n')


if __name__ == '__main__':
    main()
