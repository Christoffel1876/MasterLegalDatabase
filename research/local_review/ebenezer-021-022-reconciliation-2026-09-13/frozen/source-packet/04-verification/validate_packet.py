"""Read-only closed-packet verification; this script contains sealed candidate metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
import logging
import struct
import sys
from pathlib import Path
import pymupdf
sys.dont_write_bytecode = True
from models import Identities, Manifest, Preparation, Ref

EXPECTED = {
    'douglas-ehs-fees-atlas-directed': '35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687',
    'pueblo-planning-fees-atlas-directed': '0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b',
}


def ordinary(path: Path) -> bytes:
    """Read an ordinary file without accepting symlink ancestors."""
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('Nonordinary file: ' + str(path))
    return path.read_bytes()


def checked(base: Path, ref: Ref) -> bytes:
    """Enforce a confined relative path, exact hash and size."""
    p = Path(ref.path)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Package path escape')
    data = ordinary(base / p)
    if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError('Hash or size differs: ' + ref.path)
    return data


def candidate_bytes(pages: list[bytes]) -> bytes:
    """Package exact native bytes with explicit physical-page markers."""
    result = bytearray()
    for number, native in enumerate(pages, 1):
        result.extend((f'===== PHYSICAL PDF PAGE {number} OF {len(pages)} '
                       '(PACKAGING MARKER) =====\n').encode())
        result.extend(native)
        result.extend((f'\n===== END PHYSICAL PDF PAGE {number} '
                       '(PACKAGING MARKER) =====\n\n').encode())
    return bytes(result)


def validate(base: Path, expected_manifest: str | None = None) -> dict:
    """Verify immutable identities, native page bytes and complete source image bindings."""
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise ValueError('Symlink root')
    manifest_bytes = ordinary(base / 'manifest.json')
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if ordinary(base / 'MANIFEST_SHA256.txt') != (digest + '\n').encode():
        raise ValueError('Opaque digest differs')
    if expected_manifest is not None and expected_manifest != digest:
        raise ValueError('External manifest pin differs')
    manifest = Manifest.model_validate_json(manifest_bytes)
    names = [x.path for x in manifest.files]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate member')
    expected = set(names) | {'manifest.json', 'MANIFEST_SHA256.txt'}
    directories = {str(p) for name in expected for p in Path(name).parents if str(p) != '.'}
    actual = set()
    for p in base.rglob('*'):
        relative = p.relative_to(base).as_posix()
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise ValueError('Nonordinary member')
        if p.is_file():
            actual.add(relative)
        elif relative not in directories:
            raise ValueError('Unlisted directory')
    if actual != expected:
        raise ValueError('Closed membership differs')
    for item in manifest.files:
        checked(base, item)
    identities = Identities.model_validate_json(checked(base, manifest.identities))
    prep = Preparation.model_validate_json(checked(base, manifest.preparation))
    if [d.source_id for d in identities.documents] != list(EXPECTED):
        raise ValueError('Source ordering differs')
    if prep.no_new_document_at_or_after.isoformat() != '2026-09-13T03:55:00+00:00':
        raise ValueError('Start cutoff differs')
    if prep.stop_at.isoformat() != '2026-09-13T04:15:00+00:00':
        raise ValueError('Stop cutoff differs')
    native_total = 0
    for identity, extraction, render, custody in zip(
        identities.documents, prep.extraction, prep.renders, prep.inputs, strict=True
    ):
        sid = identity.source_id
        if any(x.source_id != sid for x in (extraction, render, custody)):
            raise ValueError('Cross-source method binding')
        if any(x.source_sha256 != EXPECTED[sid] for x in (extraction, render, custody)):
            raise ValueError('Wrong source hash')
        if identity.original.sha256 != EXPECTED[sid] or render.pages != identity.pages:
            raise ValueError('Source/image binding differs')
        source = checked(base, identity.original)
        with pymupdf.open(stream=source, filetype='pdf') as pdf:
            if len(pdf) != identity.expected_pages or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError('PDF page count or integrity differs')
            natives = []
            if len(extraction.page_native) != len(pdf):
                raise ValueError('Native page count differs')
            for number, page in enumerate(pdf):
                native = page.get_text('text', sort=False, flags=195).encode('utf-8')
                if checked(base, extraction.page_native[number]) != native:
                    raise ValueError('Native text changed')
                natives.append(native)
                png = checked(base, identity.pages[number].image)
                if png[:8] != b'\x89PNG\r\n\x1a\n':
                    raise ValueError('Not a PNG')
                width, height = struct.unpack('>II', png[16:24])
                declared = identity.pages[number]
                if (width, height) != (declared.width, declared.height):
                    raise ValueError('Image dimensions differ')
                if abs(width - page.rect.width * 300 / 72) > 1:
                    raise ValueError('Image width is not complete 300 dpi page')
                if abs(height - page.rect.height * 300 / 72) > 1:
                    raise ValueError('Image height is not complete 300 dpi page')
        if checked(base, extraction.candidate) != candidate_bytes(natives):
            raise ValueError('Candidate differs from exact native packaging')
        native_total += sum(map(len, natives))
    for model, path in [(Manifest, 'manifest.schema.json'),
                        (Identities, 'SOURCE_ONLY_IDENTITIES.schema.json'),
                        (Preparation, '03-custody/PREPARATION.schema.json')]:
        if json.loads(ordinary(base / path)) != model.model_json_schema():
            raise ValueError('Schema differs: ' + path)
    instructions = checked(base, manifest.instructions).decode('utf-8')
    if '2026-09-13T03:55:00Z' not in instructions or '2026-09-13T04:15:00Z' not in instructions:
        raise ValueError('Instruction deadlines differ')
    return {'status': 'verified_prepared_not_dispatched', 'documents': 2, 'physical_pages': 5,
            'native_bytes': native_total, 'images_dpi': 300, 'payloads': len(names),
            'manifest_sha256': digest, 'public_requests': 0,
            'source_fidelity_review_performed_by_validator': False,
            'legal_currentness': 'not_verified'}


def main() -> None:
    """Check the packet locally without dispatching or changing any file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-manifest')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('%s', json.dumps(validate(Path(__file__).absolute().parents[1],
                                         args.expected_manifest), indent=2))


if __name__ == '__main__':
    main()
