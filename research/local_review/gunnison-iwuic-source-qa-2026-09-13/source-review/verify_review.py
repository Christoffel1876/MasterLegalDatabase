"""Offline, read-only replay of exact captured source-review evidence."""
import argparse
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
import pymupdf

from review_models import Asset, Inspection, Manifest, Review, SOURCE_ID, SOURCE_SHA, Span

ROOT = Path(__file__).resolve().parent
PACKET_SHA = '9495e33579b9b310bb6ec1b7a19b7619037e60f4ba8cc3c5ca9194aa8428b434'
COPY_SHA = '2ca2de3549426080b564c98805a37cd590802edd61e6647b4ea95d4dcc8da643'
CANDIDATE_SHA = '6007089244c868b086df563d92d116c4ddfef254aba3a4a43a26105d45c50019'


def require(condition: bool, message: str) -> None:
    """Raise a stable verification failure without relying on Python assert settings."""
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(data).hexdigest()


def capture(root: Path) -> dict[str, bytes]:
    """Capture finite ordinary files once, rejecting links and unsafe ancestors."""
    require(root.is_dir(), 'Missing review directory')
    require(not any(p.is_symlink() for p in [root, *root.parents]), 'Symlink ancestor')
    files: dict[str, bytes] = {}
    total = 0
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'Symlink evidence')
        if path.is_dir():
            continue
        require(path.is_file(), 'Nonregular evidence')
        require(path.stat().st_size <= 20_000_000, 'Oversize evidence')
        data = path.read_bytes()
        total += len(data)
        require(total <= 40_000_000, 'Oversize review package')
        files[path.relative_to(root).as_posix()] = data
    expected_dirs = {str(Path(p).parent) for p in files}
    expected_dirs |= {str(q) for p in files for q in Path(p).parents}
    actual_dirs = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_dir()}
    require(actual_dirs <= expected_dirs, 'Unexpected empty directory')
    return files


def get(files: dict[str, bytes], ref: Asset) -> bytes:
    """Use only already captured, hash-bound bytes."""
    path = Path(ref.path)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == ref.path,
            'Unsafe asset reference')
    require(ref.path in files, f'Missing asset: {ref.path}')
    data = files[ref.path]
    require(len(data) == ref.size_bytes and digest(data) == ref.sha256,
            f'Asset mismatch: {ref.path}')
    return data


def js(files: dict[str, bytes], path: str) -> Any:
    """Parse only a captured JSON buffer."""
    return json.loads(files[path])


def check_span(data: bytes, ref: Span, expected: bytes) -> None:
    """Check exact UTF-8 span and content."""
    require(ref.end <= len(data) and data[ref.start:ref.end] == expected
            and digest(expected) == ref.sha256, 'Byte span mismatch')


def validate_content(files: dict[str, bytes]) -> dict[str, int]:
    """Replay bindings, OCR, page coverage, passage and instruction associations."""
    qa = Review.model_validate_json(files['SOURCE_QA.json'])
    require(js(files, 'SOURCE_QA.schema.json') == Review.model_json_schema(), 'QA schema differs')
    jsonschema.validate(js(files, 'SOURCE_QA.json'), js(files, 'SOURCE_QA.schema.json'))
    source = get(files, qa.source)
    require(qa.source.sha256 == SOURCE_SHA and len(source) == 114843, 'Wrong original')
    doc = pymupdf.open(stream=source, filetype='pdf')
    require(len(doc) == 4 and not doc.is_encrypted and not doc.is_repaired, 'Invalid original PDF')
    require([p.number for p in qa.pages] == [1, 2, 3, 4], 'Wrong physical page selection')
    packet = get(files, qa.packet_manifest)
    require(digest(packet) == PACKET_SHA, 'Wrong packet manifest')
    jsonschema.validate(json.loads(packet), js(files, 'inputs/PACKET_MANIFEST.schema.json'))
    copy = js(files, 'COPY_RECEIPT.json')
    jsonschema.validate(copy, js(files, 'COPY_RECEIPT.schema.json'))
    require(digest(files['COPY_RECEIPT.json']) == COPY_SHA, 'Copy receipt changed')
    require(copy['source_id'] == SOURCE_ID and copy['packet_manifest_sha256'] == PACKET_SHA,
            'Copy receipt source differs')
    original_prefix = next(
        x['original_path'] for x in copy['files']
        if x['path'] == 'inputs/PACKET_MANIFEST.json').removesuffix('MANIFEST.json')
    packet_files = {x['path']: x for x in json.loads(packet)['files']}
    require(len(copy['files']) == 33, 'Copy subset differs')
    for item in copy['files']:
        get(files, Asset.model_validate({k: item[k] for k in ['path', 'sha256', 'size_bytes']}))
        relative = item['original_path'].removeprefix(original_prefix)
        if relative not in ['MANIFEST.json', 'MANIFEST.schema.json']:
            require(relative in packet_files and all(item[k] == packet_files[relative][k]
                    for k in ['sha256', 'size_bytes']), 'Packet subset mapping differs')
    for ref in qa.custody:
        get(files, ref)
    canonical = list(io.BytesIO(get(files, qa.provenance.canonical_record)))
    require(len(canonical) == 1, 'Canonical selection is not exactly one record')
    record = json.loads(canonical[0])
    receipt = json.loads(get(files, qa.provenance.intake_receipt))
    jsonschema.validate(receipt, js(files, 'inputs/INTAKE_RECEIPT.schema.json'))
    intent_bytes = files['inputs/INTAKE_INTENT.json']
    require(digest(intent_bytes) == receipt['intent_sha256'], 'Intake intent differs')
    intent = json.loads(intent_bytes)
    require([r for r in intent['records'] if r['record_id'] == SOURCE_ID] == [record],
            'Canonical record is not exact intended record')
    require(record['record_id'] == SOURCE_ID and record['sha256'] == SOURCE_SHA
            and record['size_bytes'] == len(source) and record['layer_id'] == qa.layer
            and record['acquisition_method'] == 'received_review_package'
            and record['official_source_url'] is None, 'Canonical source custody differs')
    require(receipt['source_id_to_sha256'][SOURCE_ID] == SOURCE_SHA
            and record['archive_path'] in receipt['canonical_archive_paths']
            and record['received_at'] == receipt['actual_repository_received_at']
            == qa.provenance.repository_received_at
            and record['archive_path'] == qa.provenance.canonical_archive_path_claim,
            'Repository intake binding differs')
    reservation = js(files, 'inputs/reservation.json')
    result = js(files, 'inputs/result.json')
    require(reservation['authority_id'] == qa.authority_id
            and reservation['requested_url'] == qa.provenance.supplied_requested_url
            and reservation['reserved_at'] == qa.provenance.supplied_started_at
            and result['finished_at'] == qa.provenance.supplied_finished_at
            and result['body_sha256'] == SOURCE_SHA
            and result['observed_body_bytes'] == len(source),
            'Reported provenance binding differs')
    inspection = Inspection.model_validate_json(get(files, qa.inspection))
    require(js(files, 'INSPECTION.schema.json') == Inspection.model_json_schema(),
            'Inspection schema differs')
    require(inspection.full_pages == [p.image for p in qa.pages],
            'Inspection page identities differ')
    for ref in inspection.crops:
        get(files, ref)
    candidate = get(files, qa.candidate)
    require(digest(candidate) == CANDIDATE_SHA, 'Original candidate changed')
    extraction = js(files, 'inputs/EXTRACTION.json')
    jsonschema.validate(extraction, js(files, 'inputs/EXTRACTION.schema.json'))
    require(extraction['source_id'] == SOURCE_ID and extraction['source_sha256'] == SOURCE_SHA,
            'Extraction source differs')
    require(len(extraction['pages']) == 4, 'Extraction page selection differs')
    render = next(r for r in js(files, 'inputs/RENDER_STAGE.json')['renders']
                  if r['source_id'] == SOURCE_ID)
    ocr_receipt = js(files, 'inputs/OCR_RECEIPT.json')
    require(ocr_receipt['engine_revision'] == 3 and ocr_receipt['language_correction'] is False
            and ocr_receipt['recognition_languages'] == ['en-US'], 'OCR settings differ')
    events = [e for e in ocr_receipt['events'] if e['source_id'] == SOURCE_ID]
    require([e['physical_page'] for e in events] == [1, 2, 3, 4], 'OCR event pages differ')
    passages = {p.id: p for p in qa.checked_passages}
    require(len(passages) == len(qa.checked_passages) == 43, 'Passage count or IDs differ')
    reconstructed = b''
    ocr_bytes = reviewed_bytes = 0
    for page, ex, image_ref, event in zip(qa.pages, extraction['pages'], render['pages'], events):
        image = get(files, page.image)
        pix = pymupdf.Pixmap(image)
        require((pix.width, pix.height) == (page.width, page.height)
                == (image_ref['width'], image_ref['height']), 'Page geometry differs')
        require(page.image.sha256 == image_ref['image']['sha256'] == event['image']['sha256'],
                'Render or OCR image identity differs')
        require(get(files, page.native) == b'' and page.native_spans == []
                and doc[page.number - 1].get_text('text', flags=195, sort=False) == '',
                'Native text incorrectly invented')
        raw = get(files, page.ocr_json)
        ocr = json.loads(raw)
        jsonschema.validate(ocr, js(files, 'inputs/OCR_OUTPUT.schema.json'))
        require(digest(raw) == event['stdout']['sha256'] == ex['raw_ocr']['sha256'],
                'Raw OCR receipt differs')
        text = get(files, page.ocr_text)
        expected = ''.join(line['text'] + '\n' for line in ocr['lines']).encode()
        require(text == expected and page.ocr_text.sha256 == ex['ocr_text']['sha256'],
                'OCR observation order changed')
        require(len(page.ocr_observation_spans) == len(ocr['lines']), 'OCR span count differs')
        pos = 0
        for line, s in zip(ocr['lines'], page.ocr_observation_spans):
            require(s.start == pos, 'OCR gap or overlap')
            check_span(text, s, (line['text'] + '\n').encode())
            pos = s.end
        require(pos == len(text), 'OCR bytes omitted')
        n = page.number
        prefix = f'===== PHYSICAL PDF PAGE {n} OF 4 (PACKAGING MARKER) =====\n'.encode()
        suffix = f'\n===== END PHYSICAL PDF PAGE {n} (PACKAGING MARKER) =====\n\n'.encode()
        start = len(reconstructed) + len(prefix)
        reconstructed += prefix + text + suffix
        require(page.candidate_span.start == start == ex['candidate_start']
                and page.candidate_span.end == start + len(text) == ex['candidate_end'],
                'Candidate offset differs')
        check_span(candidate, page.candidate_span, text)
        reviewed = get(files, page.reviewed_transcript)
        pos = 0
        for passage in [p for p in qa.checked_passages if p.page == n]:
            require(passage.image == page.image and passage.reviewed_transcript
                    == page.reviewed_transcript, 'Passage page binding differs')
            require(passage.reviewed_span.start == pos, 'Reviewed transcript gap or overlap')
            check_span(reviewed, passage.reviewed_span, (passage.text + '\n\n').encode())
            pos = passage.reviewed_span.end
            require(all(c in files for c in passage.crop_paths), 'Missing passage crop')
            if passage.kind.endswith('annotation'):
                require(passage.text.startswith('[Reviewer annotation:'),
                        'Annotation passed as text')
        require(pos == len(reviewed), 'Reviewed transcript bytes omitted')
        ocr_bytes += len(text)
        reviewed_bytes += len(reviewed)
    require(candidate == reconstructed, 'Candidate packaging differs')
    require([a.id for a in qa.amendment_instructions]
            == [f'A{n:02d}' for n in range(1, 15)], 'Amendment ordering differs')
    for amendment in qa.amendment_instructions:
        p = passages[amendment.passage_ids[0]]
        require(amendment.target_literal in p.text and amendment.instruction_literal in p.text,
                'Instruction or target association differs')
        require(all(i in passages for i in amendment.passage_ids), 'Unknown instruction passage')
        for target in amendment.targets_within_literal:
            require(target in amendment.instruction_literal, 'Nested target differs')
    require(qa.amendment_instructions[3].targets_within_literal
            == ['403.1', '403.2', '403.2.1', '403.2.2', '403.2.3', '403.2.4', '403.2.5',
                '403.2.6', '403.3', '403.7'], 'Section 403 enumeration differs')
    require(qa.amendment_instructions[11].passage_ids == ['P3-A12', 'P4-CONTINUATION']
            and passages['P4-CONTINUATION'].continuation_of == 'P3-A12',
            'Hardened zone continuation lost')
    require([p.id for p in qa.checked_passages if p.continuation_of]
            == ['P4-CONTINUATION'], 'Unexpected continuation')
    anchors = {'P1-RECITAL-1': ['C.R.S §38-28-201', '2015', 'International Mechanical Code'],
               'P1-RECITAL-3': ['adoption of the 2015 Building Codes'],
               'P1-RECITAL-5': ['on the September 6, 2022'],
               'P1-2': ['upon recordation', 'major or minor impact'],
               'P1-3': ['new building permit applications beginning January 1, 2023'],
               'P1-EXECUTION': ['Commissioner Smith', 'Commissioner Mason',
                                '6th day of September'],
               'P2-SIGNER-1': ['Jonathan Houck, Chairperson'],
               'P2-ATTEST': ['Deputy County Clerk'],
               'P3-HEADER': ['Proposed Gunnison County Amendments'],
               'P3-A10': ['It is strongly encouraged that a vegetation management plan prepared'],
               'P3-A12': ['0-5 feet minimum'],
               'P4-CONTINUATION': ['rock, gravel, sand, cement, bare earth '
                                   'or stone/concrete pavers'],
               'P4-A13': ['“Extreme hazard”', '“Very High hazard”'],
               'P4-A14': ['It is strongly encouraged that a vegetation management plan prepared']}
    for identity, literals in anchors.items():
        require(all(x in passages[identity].text for x in literals),
                f'Checked source invariant changed: {identity}')
    require(sum(p.text.startswith('Section 502.2 Fire hazard severity reduction.')
                for p in qa.checked_passages) == 2, 'Repeated heading removed')
    require(passages['P1-HEADER'].kind == passages['P1-EXECUTION'].kind
            == 'mixed_printed_and_handwritten', 'Handwritten insertions misclassified')
    for date in qa.dates:
        require(all(i in passages and date.literal in passages[i].text for i in date.passage_ids),
                'Date role passage differs')
    require(len(qa.ocr_discrepancies) == 4, 'OCR comparisons missing')
    for discrepancy in qa.ocr_discrepancies:
        text = files[f'ocr/page-{discrepancy.page:04d}.txt']
        check_span(text, discrepancy.ocr_span, discrepancy.ocr_text_literal.encode())
        require(all(passages[i].page == discrepancy.page for i in discrepancy.reviewed_passage_ids),
                'OCR comparison wrong page')
    crops = js(files, 'CROPS.json')
    jsonschema.validate(crops, js(files, 'CROPS.schema.json'))
    require(len(crops['crops']) == 7, 'Crop selection differs')
    for crop in crops['crops']:
        original = files[crop['image_path']]
        require(digest(original) == crop['image_sha256'], 'Crop parent differs')
        pix = pymupdf.Pixmap(original)
        x0, y0, x1, y1 = crop['rectangle']
        require(0 <= x0 < x1 <= pix.width and 0 <= y0 < y1 <= pix.height, 'Unsafe crop')
        pixels = b''.join(pix.samples[y * pix.stride + x0 * pix.n:
                                     y * pix.stride + x1 * pix.n] for y in range(y0, y1))
        actual = files[crop['path']]
        require(digest(actual) == crop['sha256'], 'Crop bytes differ')
        crop_pix = pymupdf.Pixmap(actual)
        require((crop_pix.width, crop_pix.height) == (x1 - x0, y1 - y0)
                and crop_pix.samples == pixels, 'Crop pixel recipe differs')
    return dict(pages=4, crops=7, passages=len(passages), amendments=14,
                ocr_bytes=ocr_bytes, candidate_bytes=len(candidate), reviewed_bytes=reviewed_bytes)


def rerender(files: dict[str, bytes], renderer: Path) -> None:
    """Render captured original in temporary storage and compare all PNG bytes."""
    render = next(r for r in js(files, 'inputs/RENDER_STAGE.json')['renders']
                  if r['source_id'] == SOURCE_ID)
    require(renderer.is_file() and digest(renderer.read_bytes()) == render['renderer_sha256'],
            'Renderer wrapper differs')
    version = subprocess.run([str(renderer), '-v'], capture_output=True, check=True, timeout=10)
    require(render['renderer_version'] in (version.stdout + version.stderr).decode(),
            'Renderer version differs')
    with tempfile.TemporaryDirectory(prefix='iwuic-review-', dir='/private/tmp') as tmp:
        folder = Path(tmp)
        (folder / 'original.pdf').write_bytes(files['inputs/original.pdf'])
        subprocess.run([str(renderer), '-r', '300', '-png', str(folder / 'original.pdf'),
                        str(folder / 'page')], check=True, capture_output=True, timeout=60)
        pngs = sorted(folder.glob('page-*.png'))
        require(len(pngs) == 4, 'Rerender count differs')
        for n, path in enumerate(pngs, 1):
            require(path.read_bytes() == files[f'pages/page-{n:04d}.png'], 'Rerender bytes differ')


def verify(root: Path, renderer: Path | None = None) -> dict[str, int]:
    """Validate a closed manifest and every exact consumed evidence buffer."""
    files = capture(root)
    manifest = Manifest.model_validate_json(files['FINAL_MANIFEST.json'])
    require(js(files, 'FINAL_MANIFEST.schema.json') == Manifest.model_json_schema(),
            'Final schema differs')
    expected = {a.path for a in manifest.files}
    require(len(expected) == len(manifest.files), 'Duplicate manifest path')
    require(set(files) == expected | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'},
            'Closed inventory differs')
    for ref in manifest.files:
        get(files, ref)
    result = validate_content(files)
    if renderer is not None:
        rerender(files, renderer)
    return {**result, 'payloads': len(expected), 'rerendered_pages': 4 if renderer else 0}


def main() -> None:
    """Verify without changing the package or accessing public sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--rerender', action='store_true')
    parser.add_argument('--renderer', type=Path, default=Path(
        '/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
        'dependencies/bin/override/pdftoppm'))
    args = parser.parse_args()
    result = verify(args.root, args.renderer if args.rerender else None)
    sys.stdout.write(json.dumps({'status': 'passed', **result}, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
