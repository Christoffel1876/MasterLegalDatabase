"""Portable read-only verification of captured Chaffee source-QA evidence."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema
import pymupdf

from audit_models import Asset, Audit, Checks, GapProof, Inspection, Manifest
from draft.review_models import Review as OriginalReview
from revision.review_models import Review

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = 'c0bfb6e8d4adb846fd62ec7dabbdd824286f7432be6a82b6b2d2264d4553cdf6'
COPY_SHA = '632592048ba8f23d1e0853f6aef69b054898a3c13ca2718d2726dc9038dcb108'
RENDERER_SHA = 'de772e88ab9977ccde25def9b403bf42675d75f5dd82b19fbd7d8123ad183159'
TABLES = {
    'C406.1(2)': (['p3-b01'], ['p2-b12', 'p2-b13'], [2, 3], 2),
    'C406.1(3)': (['p3-b04'], ['p3-b02', 'p3-b03', 'p3-b05'], [3], 2),
    'C406.1(5)': (['p3-b08'], ['p3-b06', 'p3-b07', 'p3-b09'], [3], 2),
    'C407.2': (['p3-b12', 'p4-b01'], ['p3-b10', 'p3-b11'], [3, 4], 3),
    'R405.2': (['p6-b06'], ['p6-b04', 'p6-b05'], [6], 1),
    'R406.2': (['p6-b09'], ['p6-b07', 'p6-b08'], [6], 1),
    'R406.5': (['p7-b03'], ['p7-b02', 'p7-b01'], [7], 1),
}
LINKS = [('c401', 'p1-b17', 'p2-b01'), ('table-ri', 'p2-b13', 'p3-b01'),
         ('envelope', 'p3-b12', 'p4-b01'), ('r401', 'p4-b17', 'p5-b01'),
         ('r404', 'p5-b15', 'p6-b01'), ('eri', 'p6-b10', 'p7-b01')]


# Literal data-cell associations independently checked in the source images.
DATA_ROWS = {
    'p3-b01': [
        ['C406.7.3: Efficient fossil fuel water heater <sup>b</sup>', '<s>9</s> <u>9</u>'],
        ['C406.7.4: Heat pump water heater <sup>b</sup>', '<s>5</s> <u>9</u>']],
    'p3-b04': [
        ['C406.7.3: Efficient fossil fuel water heater <sup>a</sup>', '<s>3</s> <u>3</u>'],
        ['C406.7.4: Heat pump water heater <sup>a</sup>', '<s>1</s> <u>3</u>']],
    'p3-b08': [
        ['C406.7.3: Efficient fossil fuel water heater <sup>b</sup>', '<s>9</s> <u>9</u>'],
        ['C406.7.4: Heat pump water heater <sup>b</sup>', '<s>5</s> <u>9</u>']],
    'p3-b12': [['<u>C401.3</u>', '<u>Thermal envelope certificate</u>']],
    'p4-b01': [['<u>C402.2.4</u>', '<u>Slabs-on-grade</u>'],
               ['<u>C402.2.6</u>', '<u>Insulation of radiant heating system</u>']],
    'p6-b06': [['<u>R403.5.4</u>', '<u>Water heating equipment location</u>']],
    'p6-b09': [['<u>R403.5.4</u>', '<u>Water heating equipment</u>']],
    'p7-b03': [['6', '54', '<u>50</u>']],
}


def require(value: bool, message: str) -> None:
    """Reject invalid evidence even when Python optimization is enabled."""
    if not value:
        raise ValueError(message)


def digest(data: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(data).hexdigest()


def capture(root: Path) -> dict[str, bytes]:
    """Capture ordinary finite files once; never follow links or historical paths."""
    require(root.is_dir() and not any(p.is_symlink() for p in [root, *root.parents]),
            'Unsafe audit root')
    files: dict[str, bytes] = {}
    total = 0
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), 'Symlink in audit')
        if p.is_dir():
            continue
        require(p.is_file() and p.stat().st_size <= 20_000_000, 'Unsafe audit file')
        data = p.read_bytes()
        total += len(data)
        require(total <= 80_000_000, 'Audit byte cap')
        files[p.relative_to(root).as_posix()] = data
    dirs = {str(d) for name in files for d in Path(name).parents}
    require(all(p.relative_to(root).as_posix() in dirs for p in root.rglob('*') if p.is_dir()),
            'Unexpected empty directory')
    return files


def read(files: dict[str, bytes], ref: Any, prefix: str = '') -> bytes:
    """Return the pinned buffer actually consumed by verification."""
    if hasattr(ref, 'model_dump'):
        ref = ref.model_dump()
    name = prefix + ref['path']
    rel = Path(name)
    require(not rel.is_absolute() and '..' not in rel.parts and rel.as_posix() == name,
            'Unsafe reference')
    require(name in files, f'Missing reference: {name}')
    data = files[name]
    require(len(data) == ref['size_bytes'] and digest(data) == ref['sha256'],
            f'Changed asset: {name}')
    return data


def parse(files: dict[str, bytes], path: str) -> Any:
    """Parse a captured buffer without a second filesystem read."""
    return json.loads(files[path])


def span(data: bytes, ref: Any) -> None:
    """Check a complete exact literal byte span."""
    if hasattr(ref, 'model_dump'):
        ref = ref.model_dump()
    actual = data[ref['start']:ref['end']]
    require(0 <= ref['start'] < ref['end'] <= len(data)
            and actual == ref['text'].encode() and digest(actual) == ref['sha256'],
            'Text span mismatch')


def verify_copy(files: dict[str, bytes]) -> None:
    """Prove all seventy initially copied draft assets remain unchanged."""
    require(digest(files['COPY_RECEIPT.json']) == COPY_SHA, 'Original copy receipt changed')
    receipt = parse(files, 'COPY_RECEIPT.json')
    jsonschema.validate(receipt, parse(files, 'COPY_RECEIPT.schema.json'))
    require(len(receipt['files']) == 70, 'Original draft count differs')
    for ref in receipt['files']:
        read(files, ref)


def verify_crop(files: dict[str, bytes], original: bytes, actual: bytes,
                xyxy: list[int] | tuple[int, int, int, int]) -> None:
    """Replay an exact source-pixel crop; no enhancement or resampling."""
    p = pymupdf.Pixmap(original)
    x0, y0, x1, y1 = xyxy
    require(0 <= x0 < x1 <= p.width and 0 <= y0 < y1 <= p.height, 'Invalid crop box')
    expected = b''.join(p.samples[y * p.stride + x0 * p.n:y * p.stride + x1 * p.n]
                        for y in range(y0, y1))
    a = pymupdf.Pixmap(actual)
    require((a.width, a.height) == (x1 - x0, y1 - y0) and a.samples == expected,
            'Crop pixel mismatch')


def validate_review(files: dict[str, bytes], qa_path: str, transcript_path: str,
                    schema_path: str) -> dict[str, int]:
    """Validate source, extraction, complete paragraphs, markup and associations."""
    model = OriginalReview if qa_path.startswith('draft/') else Review
    qa = model.model_validate_json(files[qa_path])
    require(parse(files, schema_path) == model.model_json_schema(), 'Review schema changed')
    jsonschema.validate(parse(files, qa_path), parse(files, schema_path))
    text = files[transcript_path]
    require(digest(text) == qa.transcript.sha256 and len(text) == qa.transcript.size_bytes,
            'Selected transcript differs')
    source = read(files, qa.source, 'draft/')
    require(digest(source) == SOURCE_SHA and len(source) == 529100, 'Wrong source original')
    doc = pymupdf.open(stream=source, filetype='pdf')
    require(len(doc) == 7 and not doc.is_repaired and not doc.is_encrypted, 'Invalid source PDF')
    prep = parse(files, 'draft/PREPARATION.json')
    jsonschema.validate(prep, parse(files, 'draft/PREPARATION.schema.json'))
    require(prep['source'] == qa.source.model_dump() and prep['page_count'] == 7,
            'Render source binding differs')
    render = prep['events'][0]
    require(render['kind'] == 'render' and render['exit_code'] == 0, 'Render failed')
    for ref in render['outputs'] + [render['stdout'], render['stderr']]:
        read(files, ref, 'draft/')
    ocr_events = [x for x in parse(files, 'draft/OCR_PREPARATION.json')['events']
                  if x['kind'] == 'ocr']
    require([x['page'] for x in ocr_events] == list(range(1, 8)), 'OCR pages differ')
    headings = list(re.finditer(rb'^# Physical page ([1-7])\n', text, re.M))
    require([int(h[1]) for h in headings] == qa.full_pages == list(range(1, 8)),
            'Physical page selection differs')
    require([p.number for p in qa.pages] == list(range(1, 8)), 'Page records differ')
    blocks = {b.id: b for b in qa.blocks}
    require(len(blocks) == len(qa.blocks), 'Duplicate paragraph ID')
    ocr_bytes = 0
    expected_marks = []
    for index, page in enumerate(qa.pages):
        image = read(files, page.image, 'draft/')
        pix = pymupdf.Pixmap(image)
        require((pix.width, pix.height) == (2550, 3300), 'Full-page geometry differs')
        require(page.image.model_dump() == render['outputs'][index], 'Rendered page differs')
        require(read(files, page.native, 'draft/') == b'' and page.native_spans == []
                and doc[index].get_text('text', flags=195, sort=False) == '',
                'Native text must remain empty')
        raw_ocr = read(files, page.ocr_json, 'draft/')
        ocr = json.loads(raw_ocr)
        ocr_text = read(files, page.ocr_text, 'draft/')
        require(ocr['revision'] == 3
                and ocr_text == ''.join(x['text'] + '\n' for x in ocr['lines']).encode(),
                'OCR observation bytes changed')
        event = ocr_events[index]
        require(event['exit_code'] == 0 and event['stdout'] == page.ocr_json.model_dump()
                and event['outputs'] == [page.ocr_text.model_dump()], 'OCR receipt binding differs')
        read(files, event['stderr'], 'draft/')
        ocr_bytes += len(ocr_text)
        start = headings[index].end()
        end = headings[index + 1].start() if index < 6 else len(text)
        span(text, page.transcript_span)
        require((page.transcript_span.start, page.transcript_span.end) == (start, end),
                'Page transcript extent differs')
        pos = start
        selected = [b for b in qa.blocks if b.page == page.number]
        for n, block in enumerate(selected, 1):
            require(block.id == f'p{page.number}-b{n:02d}' and block.image == page.image,
                    'Block order or image binding differs')
            s = block.transcript_span
            require(start <= s.start < s.end <= end and not text[pos:s.start].strip(),
                    'Uncovered paragraph or block overlap')
            span(text, s)
            expected_kind = ('table_fragment' if s.text.startswith('|') else
                             'editorial_graphic_note' if s.text.startswith('[editorial:') else
                             'printed_context')
            require(block.kind == expected_kind, 'Paragraph kind differs')
            pos = s.end
        require(not text[pos:end].strip(), 'Uncovered terminal paragraph')
        for m in re.finditer(rb'<(u|s|sup)>(.*?)</\1>', text[start:end], re.S):
            expected_marks.append((page.number, {'u': 'underline', 's': 'strikethrough',
                                                 'sup': 'superscript'}[m[1].decode()],
                                   start + m.start(2), start + m.end(2)))
    require(ocr_bytes == qa.ocr_bytes == 14190, 'OCR total differs')
    actual_marks = [(m.page, m.kind, m.transcript_span.start, m.transcript_span.end)
                    for m in qa.marks]
    require(actual_marks == expected_marks and len(actual_marks) == 85, 'Markup spans differ')
    require(Counter(m.kind for m in qa.marks)
            == {'underline': 65, 'strikethrough': 12, 'superscript': 8}, 'Markup kinds differ')
    for mark in qa.marks:
        span(text, mark.transcript_span)
    require([t.id for t in qa.tables] == list(TABLES), 'Table order differs')
    for table in qa.tables:
        f, c, pages, rows = TABLES[table.id]
        require((table.fragment_block_ids, table.context_block_ids, table.pages,
                 table.physical_data_rows) == (f, c, pages, rows), 'Table association differs')
        require(all(blocks[i].kind == 'table_fragment' for i in f), 'Wrong table fragment kind')
    for block_id, expected_rows in DATA_ROWS.items():
        lines = blocks[block_id].transcript_span.text.splitlines()
        rows = [[cell.strip() for cell in line.strip('|').split('|')]
                for line in lines[2:] if line.startswith('|')
                and '[editorial: merged heading' not in line]
        require(rows == expected_rows, 'Source data-cell associations differ')
    require([(x.id, x.from_block_id, x.to_block_id) for x in qa.links] == LINKS,
            'Cross-page link differs')
    for link in qa.links:
        require(link.kind == 'cross_page_continuation'
                and blocks[link.to_block_id].page == blocks[link.from_block_id].page + 1,
                'Cross-page adjacency differs')
    anchors = {
        'p2-b03': ['not less than 50 percent',
                   '<u>not including any capacity used for compliance with '
                   'Section C406 of this code</u>'],
        'p2-b07': ['more than 300,000 Btu/h.</u>'],
        'p2-b09': ['<s>shall not be equipped with continuously burning pilot ignition systems</s>',
                   '<u>are not permitted</u>'],
        'p4-b12': ['<u>2.2. For mixed-fuel buildings, two of the additional efficiency packages'],
        'p4-b14': ['R405.<s>; or</s>'],
        'p4-b17': ['less than or equal to 80 percent'],
        'p5-b12': ['greater than 300,000 Btu/h that serves multiple dwelling units '
                   'or sleeping units'],
        'p5-b14': ['<s>shall not have continuously burning pilot lights</s>',
                   '<u>are prohibited</u>'],
        'p6-b01': ['continuous raceways and or conductors'],
        'p6-b03': ['208/240-volt', 'minimum capacity of 40 amps',
                   'greater than 300,000 Btu/h that serves multiple dwelling units '
                   'or sleeping units'],
        'p7-b01': ['indicated in Table R406.4'],
        'p7-b03': ['| 6 | 54 | <u>50</u> |'],
        'p7-b04': ['30 days after publication as required by law'],
        'p7-b10': ['April 21, 2026', 'April 30, 2026'],
        'p7-b11': ['May 28, 2026'],
    }
    for name, literals in anchors.items():
        require(all(x in blocks[name].transcript_span.text for x in literals),
                f'Checked qualifier changed: {name}')
    require('multiple dwelling' not in blocks['p2-b07'].transcript_span.text,
            'Residential qualifier incorrectly added to commercial exception')
    for date in qa.dates:
        require(date.external_verification is False and all(
            date.literal in re.sub(r'</?(?:u|s|sup)>', '', blocks[i].transcript_span.text)
            for i in date.block_ids), 'Date source binding differs')
    numbered = [int(m[1]) for b in qa.blocks if (m := re.match(
        r'^(\d+)\. (?:Section|TABLE|Table|A new Section)', b.transcript_span.text))]
    require(numbered == list(range(1, 23)), 'Numbered amendment sequence differs')
    crops = parse(files, 'draft/CROPS.json')
    jsonschema.validate(crops, parse(files, 'draft/CROPS.schema.json'))
    require(len(crops['items']) == len(qa.focused_crops) == 9, 'Crop count differs')
    for c in crops['items']:
        original = files[f"draft/source/page-{c['page']:04d}.png"]
        actual = files['draft/' + c['path']]
        require(digest(original) == c['parent_sha256'] and digest(actual) == c['crop_sha256'],
                'Crop identity differs')
        verify_crop(files, original, actual, c['xyxy'])
    for ref in qa.focused_crops:
        read(files, ref, 'draft/')
    verify_http_subset(files, qa)
    return dict(pages=7, crops=9, blocks=len(blocks), marks=len(qa.marks),
                logical_tables=7, fragments=8, data_rows=12, ocr_bytes=ocr_bytes,
                transcript_bytes=len(text))


def verify_http_subset(files: dict[str, bytes], qa: Review) -> None:
    """Check only the supplied subset; never treat missing upstream assets as present."""
    for ref in qa.acquisition_evidence:
        read(files, ref, 'draft/')
    prefix = 'draft/retrieval-evidence/'
    upstream = parse(files, prefix + 'FINAL_MANIFEST.json')
    jsonschema.validate(upstream, parse(files, prefix + 'FINAL_MANIFEST.schema.json'))
    refs = {a['path']: a for a in upstream['files']}
    for path in files:
        if path.startswith(prefix) and not path.endswith('/FINAL_MANIFEST.json'):
            rel = path.removeprefix(prefix)
            require(rel in refs, 'Unbound upstream subset member')
            read(files, refs[rel], prefix)
    result = parse(files, prefix + 'events/A002/RESULT.json')
    reservation = parse(files, prefix + 'events/A002/RESERVATION.json')
    require(result['body']['sha256'] == SOURCE_SHA and result['body']['size_bytes'] == 529100
            and result['http_status'] == 200 and result['body_complete'] is True
            and result['partial_or_unknown'] is False
            and result['completed_at'] == qa.observed_get_completed_at,
            'HTTP source or timing differs')
    require(reservation['request_url'] == result['requested_url'] == result['final_url']
            and reservation['plan_sha256'] == digest(files[prefix + 'PLAN.json']),
            'Request provenance differs')
    read(files, result['headers']['public_subset'], prefix)
    for label in ['stdout', 'stderr']:
        read(files, result[label], prefix)
    require(result['headers']['original_retained'] is False,
            'Header omission history changed')


def validate_audit(files: dict[str, bytes]) -> dict[str, int]:
    """Validate additive findings and table-cell spans against selected source QA."""
    audit = Audit.model_validate_json(files['AUDIT.json'])
    require(parse(files, 'AUDIT.schema.json') == Audit.model_json_schema(), 'Audit schema differs')
    for ref in [audit.source, audit.original_review, audit.original_transcript,
                audit.selected_review, audit.selected_schema, audit.selected_transcript,
                audit.copy_receipt, audit.revision_receipt, audit.inspection]:
        read(files, ref)
    verify_copy(files)
    revision_receipt = parse(files, audit.revision_receipt.path)
    jsonschema.validate(revision_receipt, parse(files, 'REVISION_RECEIPT.schema.json'))
    require(len(revision_receipt['files']) == 77, 'Revision copy count differs')
    for ref in revision_receipt['files']:
        read(files, ref)
    change = parse(files, 'revision/REVISION.json')
    jsonschema.validate(change, parse(files, 'revision/REVISION.schema.json'))
    for before, after in zip(change['before'], change['after']):
        old = read(files, before, 'revision/')
        read(files, after, 'revision/')
        require(old == files['draft/' + after['path']], 'Preimage differs from received draft')
    changed = {a['path'] for a in change['after']}
    for ref in parse(files, 'COPY_RECEIPT.json')['files']:
        relative = ref['path'].removeprefix('draft/')
        if relative not in changed:
            require(files['draft/' + relative] == files['revision/' + relative],
                    'Unintended revision payload change')
    result = validate_review(files, audit.selected_review.path, audit.selected_transcript.path,
                             audit.selected_schema.path)
    text = read(files, audit.selected_transcript)
    qa = Review.model_validate_json(read(files, audit.selected_review))
    blocks = {b.id: b for b in qa.blocks}
    require(len(audit.table_fragments) == 8, 'Audit fragment count differs')
    data_rows = 0
    actual_fragments = []
    for fragment in audit.table_fragments:
        require(fragment.block_id in TABLES[fragment.table_id][0]
                and blocks[fragment.block_id].page == fragment.page, 'Audit table identity differs')
        actual_fragments.append(fragment.block_id)
        lines = blocks[fragment.block_id].transcript_span.text.splitlines()
        expected_lines = [line for line in lines
                          if line.startswith('|') and not line.startswith('| ---')]
        require(len(expected_lines) == len(fragment.rows), 'Audit table row count differs')
        for line, row in zip(expected_lines, fragment.rows):
            literals = [cell.strip() for cell in line.strip('|').split('|')]
            require([cell.text for cell in row.cells] == literals,
                    'Table row/cell association differs')
            for cell in row.cells:
                span(text, cell)
                s = blocks[fragment.block_id].transcript_span
                require(s.start <= cell.start < cell.end <= s.end, 'Cell outside fragment')
            if row.kind == 'data':
                data_rows += 1
            if any('[editorial: merged heading' in x for x in literals):
                require(row.kind == 'merged_heading_with_editorial_placeholder',
                        'Merged heading promoted to fee row')
        require(fragment.rows[0].kind == 'header', 'Table header not preserved')
    require(actual_fragments == [i for v in TABLES.values() for i in v[0]] and data_rows == 12,
            'Audit table data coverage differs')
    inspection = Inspection.model_validate_json(read(files, audit.inspection))
    require(len(inspection.full_pages) == 7 and len(inspection.supplied_crops) == 9,
            'Incomplete inspection receipt')
    for ref in inspection.full_pages + inspection.supplied_crops:
        read(files, ref)
    for crop in inspection.supplemental_crops:
        verify_crop(files, read(files, crop.source_image), read(files, crop.crop), crop.xyxy)
    return result


def rerender(files: dict[str, bytes], renderer: Path) -> None:
    """Replay all seven full PNGs in temporary storage using pinned Poppler."""
    require(renderer.is_file() and digest(renderer.read_bytes()) == RENDERER_SHA,
            'Renderer wrapper identity differs')
    version = subprocess.run([str(renderer), '-v'], capture_output=True, check=True, timeout=10)
    require(b'pdftoppm version 26.05.0' in version.stdout + version.stderr,
            'Renderer version differs')
    with tempfile.TemporaryDirectory(prefix='chaffee-audit-', dir='/private/tmp') as tmp:
        folder = Path(tmp)
        (folder / 'source.pdf').write_bytes(files['draft/source/original.pdf'])
        subprocess.run([str(renderer), '-r', '300', '-png', str(folder / 'source.pdf'),
                        str(folder / 'page')], check=True, capture_output=True, timeout=60)
        images = sorted(folder.glob('page-*.png'))
        require(len(images) == 7, 'Rerender count differs')
        for n, p in enumerate(images, 1):
            require(p.read_bytes() == files[f'draft/source/page-{n:04d}.png'],
                    'Rerender PNG bytes differ')


def verify(root: Path, renderer: Path | None = None) -> dict[str, int]:
    """Verify the closed package using only its captured buffers."""
    files = capture(root)
    manifest = Manifest.model_validate_json(files['FINAL_MANIFEST.json'])
    require(parse(files, 'FINAL_MANIFEST.schema.json') == Manifest.model_json_schema(),
            'Final manifest schema differs')
    paths = {r.path for r in manifest.files}
    require(len(paths) == len(manifest.files)
            and set(files) == paths | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'},
            'Closed audit inventory differs')
    for ref in manifest.files:
        read(files, ref)
    result = validate_audit(files)
    for name, model in [('ORIGINAL_GAP_PROOF', GapProof), ('CHECKS', Checks),
                        ('INSPECTION', Inspection)]:
        require(parse(files, name + '.schema.json') == model.model_json_schema(),
                'Supplementary record schema differs')
        model.model_validate_json(files[name + '.json'])
    checks = Checks.model_validate_json(files['CHECKS.json'])
    require(f'{checks.test_count} passed'.encode() in read(files, checks.test_log),
            'Recorded test result differs')
    gap = GapProof.model_validate_json(files['ORIGINAL_GAP_PROOF.json'])
    original = OriginalReview.model_validate_json(read(files, gap.original_review))
    original_text = read(files, gap.original_transcript)
    require(gap.last_recorded_block_end == original.blocks[-1].transcript_span.end
            == gap.unrepresented_suffix.start
            and gap.transcript_bytes == len(original_text) == gap.unrepresented_suffix.end,
            'Historical omission extent differs')
    span(original_text, gap.unrepresented_suffix)
    if renderer:
        rerender(files, renderer)
    return {**result, 'payloads': len(paths), 'rerendered_pages': 7 if renderer else 0}


def main() -> None:
    """Run offline verification, optionally with temporary full-page rerendering."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--rerender', action='store_true')
    p.add_argument('--renderer', type=Path, default=Path(
        '/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
        'dependencies/bin/override/pdftoppm'))
    args = p.parse_args()
    result = verify(args.root, args.renderer if args.rerender else None)
    sys.stdout.write(json.dumps({'status': 'passed', **result}, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
