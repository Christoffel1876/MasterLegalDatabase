"""Verify captured Pueblo County source bytes and complete physical table associations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import jsonschema
import pymupdf
from pydantic import BaseModel, ConfigDict

QA_PIN = 'e1af59772ed9d1ee9d2bcb2ee20f8514efdbaa8fe5743dd0a029c5f5d4399536'
PDF_PIN = '1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084'
SCHEMA_PIN = 'd55009c3f3bd8ef2930186854c343fa33ff6589ad21eb97cc9f12d6dc5754c03'


class Result(BaseModel):
    """Precisely scoped read-only structural verification, without visual certification."""
    model_config = ConfigDict(extra='forbid')
    status: Literal['passed'] = 'passed'
    qa_sha256: str
    source_sha256: str
    source_bytes: Literal[75214] = 75214
    physical_pages: Literal[2] = 2
    physical_rows: Literal[88] = 88
    labeled_fee_rows: Literal[69] = 69
    native_lines: Literal[145] = 145
    native_bytes: Literal[3187] = 3187
    newly_inspected_visual_pages: Literal[0] = 0
    public_requests: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    canonical_intakes: Literal[0] = 0


def digest(raw: bytes) -> str:
    """Hash an in-memory buffer."""
    return hashlib.sha256(raw).hexdigest()


def need(condition: bool, message: str) -> None:
    """Fail closed without assertions that can disappear under optimized Python."""
    if not condition:
        raise ValueError(message)


def ordinary(root: Path, name: str, limit: int = 2_000_000) -> bytes:
    """Read a bounded ordinary relative file, rejecting traversal and aliases."""
    rel = Path(name)
    need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe relative path')
    path = root / rel
    need(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)),
         'Nonordinary input')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    need(len(data) <= limit, 'Input byte cap exceeded')
    return data


def capture(root: Path, ref: dict[str, Any]) -> bytes:
    """Verify the same source/native/image bytes consumed by subsequent checks."""
    raw = ordinary(root, ref['path'])
    need(len(raw) == ref['size_bytes'] and digest(raw) == ref['sha256'], 'Asset mismatch')
    return raw


def check_structure(qa: dict[str, Any], buffers: dict[str, bytes]) -> None:
    """Reject dropped bytes, mixed columns, broken continuations and detached marker notes."""
    need([p['physical_page'] for p in qa['pages']] == [1, 2], 'Physical page scope')
    rows = [row for page in qa['pages'] for row in page['rows']]
    by_id = {row['row_id']: row for row in rows}
    need(len(rows) == len(by_id) == 88, 'Physical row identity')
    need(sum(row['kind'] == 'fee' for row in rows) == 69, 'Fee-label count')
    need(qa['adoption_date'] is None and qa['effective_date'] is None and
         qa['answer_safe'] is False and qa['legal_currentness'] == 'not_verified', 'Scope')
    line_count = byte_count = 0
    for page, expected_rows in zip(qa['pages'], [45, 43], strict=True):
        number = page['physical_page']
        need(len(page['rows']) == expected_rows, 'Page row count')
        raw = buffers[page['native']['path']]
        byte_count += len(raw)
        line_count += len(page['native_lines'])
        pos = 0
        lines = {}
        for line in page['native_lines']:
            need(line['line_id'] not in lines and line['start'] == pos, 'Native line order')
            need(raw[line['start']:line['end']] == line['text'].encode(), 'Native line text')
            need(raw[line['end']:line['end'] + 1] == b'\n', 'Native line terminator')
            pos = line['end'] + 1
            lines[line['line_id']] = line
        need(pos == len(raw), 'Unassigned native suffix')
        assignments: dict[str, list[tuple[int, int]]] = {key: [] for key in lines}
        for index, row in enumerate(page['rows'], 1):
            need(row['row_id'] == f'P{number}-{index:02d}' and
                 row['physical_page'] == number, 'Physical row order')
            full = row['kind'] in {'note', 'section_header', 'subheading'}
            roles = ['full_row'] if full else ['application', 'fee']
            need([cell['role'] for cell in row['cells']] == roles, 'Column roles')
            for cell in row['cells']:
                need(cell['native_text'] == '\n'.join(s['text'] for s in cell['spans']),
                     'Cell wording differs')
                for span in cell['spans']:
                    need(span['line_id'] in lines, 'Unbound line')
                    line = lines[span['line_id']]
                    a, b = span['start'], span['end']
                    need(line['start'] <= a < b <= line['end'], 'Span bounds')
                    need(raw[a:b] == span['text'].encode(), 'Span text differs')
                    center_y = (span['bbox'][1] + span['bbox'][3]) / 2
                    need(row['bbox'][1] < center_y < row['bbox'][3], 'Row association')
                    center_x = (span['bbox'][0] + span['bbox'][2]) / 2
                    need(full or (center_x < 366) == (cell['role'] == 'application'),
                         'Column association')
                    assignments[span['line_id']].append((a, b))
            refs = (row['section_context_ids'] + row['note_ids_from_explicit_marker'] +
                    row['group_marker_context_only'])
            need(not (set(refs) - set(by_id)), 'Unknown context')
            for context in row['section_context_ids']:
                need(by_id[context]['kind'] in {'section_header', 'subheading'}, 'Context role')
            note_map = {'*': 'P2-42', '^': 'P2-43', '†': 'P2-11'}
            app = next((c['native_text'] for c in row['cells'] if c['role'] == 'application'), '')
            fee = next((c['native_text'] for c in row['cells'] if c['role'] == 'fee'), '')
            markers = ([m for m in ('*', '^') if m in app] + (['†'] if '†' in fee else []))
            if row['kind'] != 'fee':
                markers = []
            need(row['explicit_markers'] == markers and
                 row['note_ids_from_explicit_marker'] == [note_map[m] for m in markers],
                 'Explicit marker association')
        for line_id, spans in assignments.items():
            spans.sort()
            line = lines[line_id]
            need(bool(spans) and spans[0][0] == line['start'] and
                 spans[-1][1] == line['end'], 'Dropped native bytes')
            need(all(a[1] == b[0] for a, b in zip(spans, spans[1:])),
                 'Duplicated or omitted native bytes')
    need((line_count, byte_count) == (145, 3187), 'Native total scope')
    expected_continuations = {'P1-04': 'P1-03', 'P1-06': 'P1-05',
                              'P1-08': 'P1-07', 'P1-19': 'P1-18'}
    need({row['row_id']: row['continues_row_id'] for row in rows
          if row['continues_row_id'] is not None} == expected_continuations,
         'Continuation associations')
    for row_id in ('P2-42', 'P2-43'):
        need(by_id[row_id]['section_context_ids'] == [], 'Global notes misbound')
    for number in range(1, 6):
        need(by_id[f'P2-{number:02d}']['section_context_ids'] == ['P1-39'],
             'Land Division continuation')
    for row in rows:
        expected = ['P2-23', 'P2-43'] if row['row_id'] in {
            'P2-24', 'P2-25', 'P2-26', 'P2-27'} else []
        need(row['group_marker_context_only'] == expected, 'Certificates marker context')


def verify(root: Path, qa_pin: str = QA_PIN) -> Result:
    """Check the pinned review and its exact original/native/image identities offline."""
    raw = ordinary(root, 'SOURCE_QA.json')
    need(digest(raw) == qa_pin == QA_PIN, 'QA pin differs')
    qa = json.loads(raw)
    schema_raw = ordinary(root, 'SOURCE_QA.schema.json')
    need(digest(schema_raw) == SCHEMA_PIN, 'Review schema differs')
    schema = json.loads(schema_raw)
    jsonschema.Draft202012Validator(schema).validate(qa)
    source = capture(root, qa['source'])
    need(digest(source) == PDF_PIN and len(source) == 75214, 'Original source pin')
    buffers = {}
    with pymupdf.open(stream=source, filetype='pdf') as doc:
        need(len(doc) == 2, 'PDF page count')
        for page in qa['pages']:
            native = capture(root, page['native'])
            buffers[page['native']['path']] = native
            need(doc[page['physical_page'] - 1].get_text('text', flags=195).encode() == native,
                 'Native extraction differs from current runtime')
            image = pymupdf.Pixmap(capture(root, page['image']))
            need((image.width, image.height) == (1224, 1584), 'Full-page image dimensions')
    check_structure(qa, buffers)
    return Result(qa_sha256=digest(raw), source_sha256=digest(source))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    print(verify(args.root.absolute()).model_dump_json(indent=2))
