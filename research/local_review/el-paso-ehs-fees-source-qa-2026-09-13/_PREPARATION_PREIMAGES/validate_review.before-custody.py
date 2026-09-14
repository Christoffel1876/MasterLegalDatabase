"""Read-only portable validation of the English El Paso EHS source review."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

import jsonschema
import pymupdf
from pydantic import Field

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_review import derive, normalized
from review_models import CompleteReview, FirstPass, Inventory, Ref, Strict

SOURCE_SHA = '1b0529fb7514bcc50c0dd36c903ca361f6ab431712b4aebc48bca8e3f5373622'
FIRST_PASS_SHA = '4cd861ca11fe9b333c7d3c74b1e0ca922323884efdf3223562209e460e8a98e3'
NATIVE_BYTES = 8060


class Result(Strict):
    """Typed bounded result with no currentness or translation promotion."""
    status: Literal['passed'] = 'passed'
    closed_files: int = Field(ge=0)
    physical_pages: Literal[5] = 5
    service_rows: Literal[65] = 65
    named_groups: Literal[7] = 7
    table_grid_rows: Literal[74] = 74
    grid_cells_including_merged_nulls: Literal[148] = 148
    context_records: Literal[37] = 37
    native_bytes: Literal[8060] = 8060
    native_text_reproduced: Literal[True] = True
    candidate_offsets_replayed: Literal[True] = True
    table_geometry_replayed: Literal[True] = True
    all_nonwhitespace_native_bytes_bound: Literal[True] = True
    source_first_freeze_precedes_native_extraction_as_recorded: Literal[True] = True
    chronology_independently_authenticated: Literal[False] = False
    rerendered: bool
    public_requests: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    translation_equivalence: Literal['not_reviewed'] = 'not_reviewed'


def sha(data: bytes) -> str:
    """Hash bytes used in a check."""
    return hashlib.sha256(data).hexdigest()


def checked(root: Path, ref: Ref) -> bytes:
    """Refuse escaping, missing, symlinked or changed evidence members."""
    rel = Path(ref.path)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Unsafe evidence member')
    path = root / rel
    if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Missing or symlinked evidence')
    data = path.read_bytes()
    if len(data) != ref.size_bytes or sha(data) != ref.sha256:
        raise ValueError('Evidence bytes differ: ' + ref.path)
    return data


def schema_check(root: Path, name: str) -> Any:
    """Use only local schema definitions without remote reference resolution."""
    schema = json.loads((root / f'{name}.schema.json').read_bytes())

    def local(value: Any) -> None:
        """Reject external schema resolution."""
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {'$ref', '$dynamicRef'} and not str(child).startswith('#'):
                    raise ValueError('External schema reference')
                local(child)
        elif isinstance(value, list):
            for child in value:
                local(child)

    local(schema)
    data = json.loads((root / f'{name}.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(data)
    return data


def validate_data(root: Path, data: CompleteReview) -> None:
    """Check actual source bytes, native spans, complete grids and every required context."""
    if root != HERE:
        raise ValueError('Semantic replay uses this portable package directory only')
    if data.source.sha256 != SOURCE_SHA or data.first_pass.sha256 != FIRST_PASS_SHA:
        raise ValueError('Source/first-pass identity changed')
    original = checked(root, data.source)
    first = FirstPass.model_validate_json(checked(root, data.first_pass))
    if data.source.path != 'source/original.pdf' or data.first_pass.path != 'PASS1.json':
        raise ValueError('Source/first-pass path changed')
    candidate = checked(root, data.candidate)
    if data.candidate.path != 'candidate.txt' or data.extraction_version != pymupdf.VersionBind:
        raise ValueError('Candidate/version differs')
    extraction = schema_check(root, 'NATIVE_EXTRACTION')
    freeze = schema_check(root, 'PASS1_FREEZE')
    if (extraction['started_at'] <= freeze['frozen_at'] or
            freeze['frozen_at'] < first.frozen_at.isoformat().replace('+00:00', 'Z')):
        raise ValueError('Recorded source-first chronology differs')
    for item in freeze['files']:
        checked(root, Ref.model_validate(item))
    checked(root, Ref.model_validate(extraction['prior_freeze']))
    if Ref.model_validate(extraction['candidate']) != data.candidate:
        raise ValueError('Extraction candidate binding differs')
    total = 0
    reconstructed = b''
    raw_pages = {}
    with pymupdf.open(stream=original, filetype='pdf') as pdf:
        if len(pdf) != 5 or pdf.is_encrypted or pdf.is_repaired:
            raise ValueError('Source PDF structure differs')
        for index, page in enumerate(data.pages, 1):
            if page.physical_page != index:
                raise ValueError('Physical page order differs')
            raw = checked(root, page.native)
            if page.native.path != f'native/page-{index:04d}.txt':
                raise ValueError('Unexpected native page path')
            if pdf[index - 1].get_text('text', flags=195, sort=False).encode('utf-8') != raw:
                raise ValueError('Native extraction differs')
            checked(root, page.image)
            if page.image != first.page_images[index - 1]:
                raise ValueError('Original page image differs')
            reconstructed += f'=== PHYSICAL PAGE {index} ===\n'.encode()
            if page.candidate_start != len(reconstructed):
                raise ValueError('Candidate start differs')
            reconstructed += raw
            if page.candidate_end != len(reconstructed):
                raise ValueError('Candidate end differs')
            reconstructed += b'\n'
            total += len(raw)
            raw_pages[index] = raw
    if reconstructed != candidate or total != NATIVE_BYTES:
        raise ValueError('Candidate packaging/byte preservation differs')
    expected = derive()
    for name in ['rows', 'contexts', 'bindings', 'tables', 'pages']:
        if getattr(data, name) != expected[name]:
            raise ValueError('Source-bound ' + name + ' differ')
    covered = {i: bytearray(len(raw)) for i, raw in raw_pages.items()}
    for binding in data.bindings:
        raw = raw_pages[binding.physical_page]
        for span in binding.spans:
            if not 0 <= span.start < span.end <= len(raw):
                raise ValueError('Invalid native byte span')
            part = raw[span.start:span.end]
            if sha(part) != span.sha256 or part.decode('utf-8') != span.text:
                raise ValueError('Native span bytes differ')
            covered[binding.physical_page][span.start:span.end] = b'1' * len(part)
    for number, raw in raw_pages.items():
        unbound = bytes(b for b, mark in zip(raw, covered[number]) if not mark)
        if unbound.strip():
            raise ValueError('Nonwhitespace native content omitted')
    groups = {row.group for row in data.rows}
    if len(groups) != 7 or sum(len(t.rows) for t in data.tables) != 74:
        raise ValueError('Group/grid count differs')
    # Explicit source markers and exceptions must stay linked to the correct service cells.
    links = {row.row_id: set(row.linked_context) for row in data.rows}
    required = {'R020': 'STAR', 'R022': 'D5', 'R023': 'D6', 'R033': 'D7',
                'R051': 'D1', 'R052': 'D2', 'R053': 'D2', 'R059': 'D3', 'R060': 'D4'}
    if any(context not in links[row] for row, context in required.items()):
        raise ValueError('Explicit definition or asterisk link omitted')
    if any(not {'A', 'B', 'OTHER1', 'OTHER2', 'OTHER3'} <= value for value in links.values()):
        raise ValueError('General source conditions omitted')
    if 'CHILD1' in links['R019']:
        raise ValueError('Unsupported routine-inspection inference')
    if any(not normalized(r.fee) for r in data.rows):
        raise ValueError('Unexpected blank fee cell')


def inventory(root: Path) -> Inventory:
    """Check the complete closed inventory without mutating its evidence."""
    record = Inventory.model_validate(schema_check(root, 'FINAL_MANIFEST'))
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlinked package')
        if path.is_file() and path.relative_to(root).as_posix() != 'FINAL_MANIFEST.json':
            actual.add(path.relative_to(root).as_posix())
    if actual != {r.path for r in record.files}:
        raise ValueError('Closed inventory differs')
    for ref in record.files:
        checked(root, ref)
    return record


def rerender(data: CompleteReview) -> None:
    """Reproduce all five original full-page PNGs in temporary storage only."""
    renderer = shutil.which('pdftoppm')
    if renderer is None:
        raise ValueError('pdftoppm required for requested render replay')
    with tempfile.TemporaryDirectory(prefix='geode-ehs-render-') as directory:
        output = Path(directory)
        subprocess.run([renderer, '-r', '300', '-png', str(HERE / data.source.path),
                        str(output / 'page')], check=True, capture_output=True, timeout=60)
        files = sorted(output.glob('page-*.png'))
        if len(files) != 5:
            raise ValueError('Render count differs')
        for page, image in zip(data.pages, files):
            if image.read_bytes() != checked(HERE, page.image):
                raise ValueError('Exact Poppler PNG bytes differ; check renderer version')


def verify(render: bool = False) -> Result:
    """Validate closed custody, source semantics and optional exact render reproduction."""
    before = inventory(HERE)
    for name in ['CAPTURE', 'PASS1', 'SOURCE_QA']:
        schema_check(HERE, name)
    data = CompleteReview.model_validate_json((HERE / 'SOURCE_QA.json').read_bytes())
    validate_data(HERE, data)
    if render:
        rerender(data)
    if inventory(HERE) != before:
        raise ValueError('Package changed during verification')
    return Result(closed_files=len(before.files), rerendered=render)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rerender', action='store_true')
    arguments = parser.parse_args()
    try:
        result = verify(arguments.rerender)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(1)
    sys.stdout.write(result.model_dump_json(indent=2) + '\n')
