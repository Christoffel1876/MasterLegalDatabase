"""Build a finite source-first packet from accepted local originals; no public requests."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import pymupdf
sys.dont_write_bytecode = True
from models import Custody, Extraction, Identities, Identity, Manifest, Page, Preparation, Ref, Render
from validate_packet import candidate_bytes

BASE = Path(__file__).absolute().parents[1]
PROJECT = Path('/Users/mcoors/Documents/Project Geode')
ROOT = PROJECT / 'MasterLegalDatabase/research/local_review'
SOURCES = [
    ('EB-PDF-021', 'douglas-ehs-fees-atlas-directed', 'CO-COUNTY-DOUGLAS',
     ROOT / 'douglas-ehs-fees-source-qa-2026-09-13',
     '35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687', 1,
     'https://www.douglasco.gov/documents/fee-schedule.pdf/', '2026-09-12T23:34:39.577252Z'),
    ('EB-PDF-022', 'pueblo-planning-fees-atlas-directed', 'CO-MUNICIPAL-PUEBLO',
     ROOT / 'pueblo-planning-fees-source-qa-2026-09-13',
     '0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b', 4,
     'https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId=',
     '2026-09-13T00:23:02.695819Z'),
]


def write(path: Path, data: bytes) -> None:
    """Atomically create a new complete file; existing files are never overwritten."""
    if path.exists() or path.is_symlink():
        raise ValueError('Existing output: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def ref(path: Path, relative: bool = True) -> Ref:
    """Describe exact output bytes or a historical original reference."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(BASE).as_posix() if relative else str(path),
               sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def record(path: Path, value: object) -> None:
    """Serialize a validated Pydantic record or generated schema."""
    data = value.model_dump(mode='json') if hasattr(value, 'model_dump') else value
    write(path, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode())


def main() -> None:
    """Copy originals, render full pages, and preserve unchanged native extraction."""
    if pymupdf.VersionBind != '1.28.2':
        raise ValueError('Recorded extractor version required')
    renderer = shutil.which('pdftoppm')
    if not renderer:
        raise ValueError('Poppler unavailable')
    version = subprocess.run([renderer, '-v'], capture_output=True, timeout=10, check=True)
    version_text = (version.stdout + version.stderr).decode().splitlines()[0]
    config = BASE / '04-verification/fontconfig.xml'
    write(config, b'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
          b'<fontconfig><dir>/System/Library/Fonts</dir><dir>/Library/Fonts</dir>'
          b'<cachedir>/private/tmp/geode-eb021-022-fontcache</cachedir></fontconfig>')
    identities, extractions, renders, custody = [], [], [], []
    for assignment, sid, authority, accepted, sha, count, url, acquired in SOURCES:
        origin = accepted / 'original.pdf'
        if any(p.is_symlink() for p in (origin, *origin.parents)):
            raise ValueError('Source symlink')
        body = origin.read_bytes()
        if hashlib.sha256(body).hexdigest() != sha:
            raise ValueError('Original differs')
        source_dir = BASE / '01-source-only' / sid
        target = source_dir / 'original.pdf'
        write(target, body)
        command = [renderer, '-r', '300', '-png', str(target), str(source_dir / 'rendered')]
        started = datetime.now(timezone.utc)
        result = subprocess.run(command, capture_output=True, timeout=30,
                                env=dict(os.environ, FONTCONFIG_FILE=str(config)))
        completed = datetime.now(timezone.utc)
        stderr = BASE / '04-verification' / (assignment + '-render.stderr.txt')
        write(stderr, result.stderr)
        if result.returncode or result.stdout:
            raise ValueError('Renderer failure or unexpected stdout')
        pages = []
        for number in range(1, count + 1):
            source_image = source_dir / f'rendered-{number}.png'
            image = source_dir / f'page-{number:04d}.png'
            os.replace(source_image, image)
            width, height = struct.unpack('>II', image.read_bytes()[16:24])
            pages.append(Page(physical_page=number, image=ref(image), width=width, height=height))
        native_parts, native_refs, prior_refs = [], [], []
        with pymupdf.open(stream=body, filetype='pdf') as pdf:
            if len(pdf) != count or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError('PDF structure differs')
            for number, page in enumerate(pdf, 1):
                native = page.get_text('text', sort=False, flags=195).encode('utf-8')
                prior = (accepted / 'candidate-native.txt' if count == 1 else
                         accepted / 'native' / f'page-{number:04d}.txt')
                if prior.read_bytes() != native:
                    raise ValueError('Prior native bytes differ')
                output = BASE / '02-candidate-text' / sid / f'page-{number:04d}.native.txt'
                write(output, native)
                native_parts.append(native)
                native_refs.append(ref(output))
                prior_refs.append(ref(prior, False))
        candidate = BASE / '02-candidate-text' / sid / 'candidate.txt'
        write(candidate, candidate_bytes(native_parts))
        identities.append(Identity(assignment_id=assignment, source_id=sid, authority_id=authority,
            expected_pages=count, original=ref(target), pages=pages))
        extractions.append(Extraction(source_id=sid, source_sha256=sha,
            method='Page.get_text("text", sort=False, flags=195)', candidate=ref(candidate),
            page_native=native_refs, prior_native=prior_refs))
        renders.append(Render(source_id=sid, source_sha256=sha, renderer_version=version_text,
            command=command, started_at=started, completed_at=completed, stderr=ref(stderr), pages=pages))
        custody.append(Custody(source_id=sid, original_input=ref(origin, False), source_sha256=sha,
            official_url=url, earlier_http_completed_at=datetime.fromisoformat(
                acquired.replace('Z', '+00:00'))))
    record(BASE / 'SOURCE_ONLY_IDENTITIES.schema.json', Identities.model_json_schema())
    record(BASE / 'SOURCE_ONLY_IDENTITIES.json', Identities(documents=identities))
    prep = Preparation(prepared_at=datetime.now(timezone.utc), inputs=custody,
        extraction=extractions, renders=renders,
        no_new_document_at_or_after=datetime(2026, 9, 13, 3, 55, tzinfo=timezone.utc),
        stop_at=datetime(2026, 9, 13, 4, 15, tzinfo=timezone.utc))
    record(BASE / '03-custody/PREPARATION.schema.json', Preparation.model_json_schema())
    record(BASE / '03-custody/PREPARATION.json', prep)
    baseline = PROJECT / 'handoffs/run-2026-09-12/extended-run/ebenezer-019-020/START_HERE.md'
    old_text = baseline.read_text()
    tail = old_text[old_text.index('## Pass 1:'):].replace('EB-PDF-020', 'EB-PDF-022')
    lead = (BASE / '04-verification/instruction-lead.txt').read_text()
    write(BASE / 'START_HERE.md', (lead + tail).encode())
    record(BASE / 'manifest.schema.json', Manifest.model_json_schema())
    files = [ref(p) for p in sorted(BASE.rglob('*'), key=lambda p:p.relative_to(BASE).as_posix())
             if p.is_file()]
    manifest = Manifest(frozen_at=datetime.now(timezone.utc), files=files,
        identities=ref(BASE / 'SOURCE_ONLY_IDENTITIES.json'),
        preparation=ref(BASE / '03-custody/PREPARATION.json'),
        instructions=ref(BASE / 'START_HERE.md'))
    record(BASE / 'manifest.json', manifest)
    write(BASE / 'MANIFEST_SHA256.txt', (ref(BASE / 'manifest.json').sha256 + '\n').encode())


if __name__ == '__main__':
    main()
