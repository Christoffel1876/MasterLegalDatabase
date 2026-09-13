"""Read-only structural and custody verification of this frozen source review."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import jsonschema
import pymupdf

from review_models import Asset, Manifest, Review

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = '53bd127e25d331ab0086fb09c5e1485d52dc46a96235d84476ef17a989022bab'


def digest(data: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(data).hexdigest()


def read_asset(root: Path, asset: Asset) -> bytes:
    """Reject traversal or symbolic links and check exact consumed bytes."""
    relative = Path(asset.path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe asset path')
    path = root / relative
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Symbolic link is not evidence')
    data = path.read_bytes()
    if len(data) != asset.size_bytes or digest(data) != asset.sha256:
        raise ValueError(f'Asset mismatch: {asset.path}')
    return data


def validate_content(root: Path, review: Review) -> None:
    """Replay page, transcript, OCR, fee, date and custody associations."""
    source = read_asset(root, review.source)
    assert review.source.sha256 == SOURCE_SHA and len(source) == 126763
    document = pymupdf.open(stream=source, filetype='pdf')
    assert len(document) == 3 and not document.is_encrypted and not document.is_repaired
    assert [p.number for p in review.pages] == [1, 2, 3]
    assert len(review.blocks) == 34 and len(review.fees) == 12
    blocks = {b.id: b for b in review.blocks}
    assert len(blocks) == 34
    for asset in review.custody:
        read_asset(root, asset)
    result = json.loads((root / 'inputs/result.json').read_bytes())
    reservation = json.loads((root / 'inputs/reservation.json').read_bytes())
    assert result['body_sha256'] == SOURCE_SHA
    assert result['observed_body_bytes'] == 126763
    assert reservation['requested_url'] == review.supplied_requested_url
    assert (reservation['reserved_at'], result['finished_at']) == (
        review.supplied_acquisition_interval
    )
    for page in review.pages:
        image = read_asset(root, page.image)
        pix = pymupdf.Pixmap(image)
        assert (pix.width, pix.height) == (2550, 3300)
        native = read_asset(root, page.native)
        assert native == b'' and page.native_spans == []
        assert document[page.number - 1].get_text('text', flags=195, sort=False) == ''
        ocr_json = read_asset(root, page.ocr_json)
        ocr = json.loads(ocr_json)
        jsonschema.validate(ocr, json.loads((root / 'ocr-escalated/OCR.schema.json').read_bytes()))
        candidate = read_asset(root, page.ocr_text)
        assert candidate == ('\n'.join(x['text'] for x in ocr['lines']) + '\n').encode()
        assert len(page.ocr_observation_spans) == len(ocr['lines'])
        pos = 0
        for observation, s in zip(ocr['lines'], page.ocr_observation_spans):
            data = (observation['text'] + '\n').encode()
            assert s.start == pos and s.end == pos + len(data)
            assert candidate[s.start:s.end] == data and s.sha256 == digest(data)
            pos = s.end
        assert pos == len(candidate)
        transcript = read_asset(root, page.reviewed_transcript)
        pos = 0
        for block in (b for b in review.blocks if b.page == page.number):
            assert block.image == page.image and block.transcript == page.reviewed_transcript
            x0, y0, x1, y1 = block.region_xyxy
            assert 0 <= x0 < x1 <= 2550 and 0 <= y0 < y1 <= 3300
            data = (block.text + '\n').encode()
            s = block.transcript_span
            assert s.start == pos and s.end == pos + len(data)
            assert transcript[s.start:s.end] == data and s.sha256 == digest(data)
            pos = s.end
        assert pos == len(transcript)
    expected = ['0.9%', '$300', '$1,000', '$200', '0.7%', '$150.00', '$100.00',
                'actual cost', '$75.00', '0.75%', '$55.00', '65%']
    assert [f.amount_literal for f in review.fees] == expected
    expected_ids = ['P3-GENERAL', 'P3-MIN', 'P3-DEPOSIT', 'P3-DEPOSIT', 'P3-MODEL',
                    'P3-REVIEW', 'P3-REVIEW', 'P3-REVIEW', 'P3-REVIEW', 'P3-MECH',
                    'P3-MECH-MIN', 'P3-MECH-REVIEW']
    assert [f.block_id for f in review.fees] == expected_ids
    for fee in review.fees:
        block = blocks[fee.block_id]
        data = block.text.encode()[fee.amount_in_block.start:fee.amount_in_block.end]
        assert data == fee.amount_literal.encode()
        assert digest(data) == fee.amount_in_block.sha256
        assert fee.label_literal in block.text
        assert fee.block_id in fee.conditions_block_ids
        assert 'P1-CONDITION' in fee.conditions_block_ids
        assert all(x in blocks for x in fee.conditions_block_ids)
    assert 'recommended and increase of' in blocks['P1-R2'].text
    assert 'Exhibit A' in blocks['P1-ADOPTION'].text
    assert 'ATTACHMENT A' in blocks['P3-HEADER'].text
    assert 'or the Building Safety Journal' in blocks['P3-VALUATION'].text
    assert 'unless and until' in blocks['P1-CONDITION'].text.lower()
    assert 'forfeited if the permit is not issued' in blocks['P3-DEPOSIT'].text
    assert 'beyond two hours' in blocks['P3-REVIEW'].text
    assert 'if plan review is needed' in blocks['P3-MECH-REVIEW'].text
    assert len(review.dates) == 4
    for date in review.dates:
        assert all(date.literal in blocks[i].text for i in date.block_ids)
    crops = json.loads((root / 'CROPS.json').read_bytes())['crops']
    crops += json.loads((root / 'CROPS_SUPPLEMENT.json').read_bytes())['crops']
    crops += json.loads((root / 'CROPS_FINAL.json').read_bytes())['crops']
    for crop in crops:
        image = (root / crop['image_path']).read_bytes()
        assert digest(image) == crop['image_sha256']
        pix = pymupdf.Pixmap(image)
        x0, y0, x1, y1 = crop['rectangle']
        data = b''.join(pix.samples[y * pix.stride + x0 * pix.n:
                                   y * pix.stride + x1 * pix.n] for y in range(y0, y1))
        expected_crop = pymupdf.Pixmap(pymupdf.csRGB, x1 - x0, y1 - y0, data, False)
        actual = (root / crop['path']).read_bytes()
        assert digest(actual) == crop['sha256']
        assert pymupdf.Pixmap(actual).samples == expected_crop.samples


def verify(root: Path, rerender: bool = False) -> tuple[int, int]:
    """Check the closed package, then replay content and optional full rendering."""
    raw_manifest = (root / 'FINAL_MANIFEST.json').read_bytes()
    manifest = Manifest.model_validate_json(raw_manifest)
    jsonschema.validate(json.loads(raw_manifest), Manifest.model_json_schema())
    expected = {a.path for a in manifest.files}
    assert len(expected) == len(manifest.files)
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    assert actual == expected | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'}
    for asset in manifest.files:
        read_asset(root, asset)
    raw = (root / 'SOURCE_QA.json').read_bytes()
    review = Review.model_validate_json(raw)
    jsonschema.validate(json.loads(raw), json.loads((root / 'SOURCE_QA.schema.json').read_bytes()))
    validate_content(root, review)
    if rerender:
        executable = ('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
                      'dependencies/bin/override/pdftoppm')
        with tempfile.TemporaryDirectory(prefix='gunnison-render-') as temp:
            output = Path(temp) / 'page'
            subprocess.run([executable, '-r', '300', '-png', str(root / review.source.path),
                            str(output)], check=True, capture_output=True, timeout=60)
            for page in review.pages:
                original = pymupdf.Pixmap(read_asset(root, page.image))
                again = pymupdf.Pixmap(str(Path(temp) / f'page-{page.number}.png'))
                assert again.samples == original.samples
    return len(manifest.files), len(review.blocks)


def main() -> None:
    """Verify without changing package, native source or OCR output."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerender', action='store_true')
    args = parser.parse_args()
    count, blocks = verify(ROOT, args.rerender)
    sys.stdout.write(f'PASS: {count} closed payloads; 3 pages; {blocks} blocks; 12 fees.\n')


if __name__ == '__main__':
    main()
