"""Portable read-only custody checks; no source-accuracy or historical-process certification."""
from __future__ import annotations
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath

import pymupdf
from models import Audit, Manifest, NativePage, SuppliedPrompt

BASE = Path(__file__).resolve().parent


def checked(ref) -> bytes:
    path = BASE / ref.path
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Nonordinary evidence')
    content = path.read_bytes()
    if len(content) != ref.size_bytes or hashlib.sha256(content).hexdigest() != ref.sha256:
        raise ValueError('Evidence identity mismatch: ' + ref.path)
    return content


def verify() -> dict:
    manifest = Manifest.model_validate_json((BASE / 'FINAL_MANIFEST.json').read_bytes())
    actual = set()
    for path in BASE.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in audit package')
        if path.is_file() and path.relative_to(BASE).as_posix() != 'FINAL_MANIFEST.json':
            actual.add(path.relative_to(BASE).as_posix())
    if actual != {r.path for r in manifest.files}:
        raise ValueError('Closed inventory mismatch')
    for ref in manifest.files:
        checked(ref)
    audit = Audit.model_validate_json((BASE / 'METHODS_AUDIT.json').read_bytes())
    original = json.loads(checked(audit.original_manifest))
    by_id = {d['identity']['assignment_id']: d for d in original['documents']}
    seen = set()
    with tarfile.open(BASE / audit.clarification_tar.path, 'r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            normalized = member.name.rstrip('/') if member.isdir() else member.name
            if (path.is_absolute() or '..' in path.parts or str(path) != normalized or
                    normalized in seen or not (member.isfile() or member.isdir())):
                raise ValueError('Unsafe archive member')
            seen.add(normalized)
            if member.isfile():
                value = archive.extractfile(member).read(member.size + 1)
                if len(value) != member.size:
                    raise ValueError('Archive length mismatch')
                if value != (BASE / 'received/tar-members' / path).read_bytes():
                    raise ValueError('Archive retained member mismatch')
    for row in audit.prompt_checks:
        prompt = SuppliedPrompt.model_validate_json(checked(row.artifact))
        raw = prompt.prompt.encode()
        if (hashlib.sha256(raw).hexdigest() != row.prompt_utf8_sha256 or
                len(raw) != row.prompt_utf8_bytes or len(prompt.prompt) != row.prompt_characters or
                len(prompt.attachments) != row.attachment_count or
                prompt.transcript_line != row.supplied_transcript_line):
            raise ValueError('Task extract binding mismatch')
    for source in audit.source_checks:
        body = checked(source.source)
        candidate = checked(source.candidate)
        document = by_id[source.assignment_id]
        if (source.source.sha256 != document['identity']['original']['sha256'] or
                source.candidate.sha256 != document['candidate']['sha256']):
            raise ValueError('Original manifest source/candidate mismatch')
        path = BASE / 'received/reviewer' / source.assignment_id
        freeze = json.loads((path / 'PASS1_FREEZE_RECEIPT.json').read_bytes())
        completion = json.loads((path / 'COMPLETION_RECEIPT.json').read_bytes())
        if source.assignment_id == 'EB-PDF-019':
            receipt_pages = freeze['bindings']['pages']
            reported = completion['bindings']
            if reported['full_manifest_opened'] or reported['original_pdf']['present_in_workdir']:
                raise ValueError('Historical method limit changed')
        else:
            receipt_pages = freeze['pages']
            if completion['full_manifest_opened'] or completion['original_pdf']['locally_rehashed']:
                raise ValueError('Historical method limit changed')
        with pymupdf.open(stream=body, filetype='pdf') as pdf:
            if len(pdf) != source.source_pdf_pages or len(source.pages) != len(pdf):
                raise ValueError('Source page coverage mismatch')
            for page, receipt, declared in zip(source.pages, receipt_pages,
                    document['identity']['pages'], strict=True):
                image = checked(page.image)
                pixmap = pymupdf.Pixmap(image)
                if ((pixmap.width, pixmap.height) != page.dimensions or
                        receipt['physical_page'] != page.physical_page or
                        receipt['sha256'] != page.image.sha256 or
                        declared['image']['sha256'] != page.image.sha256):
                    raise ValueError('Page identity/dimensions mismatch')
                evidence = NativePage.model_validate_json(checked(page.evidence))
                native = pdf[page.physical_page - 1].get_text('text', sort=False, flags=195).encode()
                start, end = page.candidate_start_byte, page.candidate_end_byte_exclusive
                if (not 0 <= start < end <= len(candidate) or candidate[start:end] != native or
                        native != evidence.text.encode() or len(native) != page.native_bytes or
                        hashlib.sha256(native).hexdigest() != page.native_sha256):
                    raise ValueError('Native/candidate page slice mismatch')
    for ref in manifest.files:
        checked(ref)
    return dict(status='custody_and_methods_audit_valid', sources=2, pages=8,
                prompt_extracts=5, direct_visual_pages=0, public_requests=0,
                historical_protocol_certified=False, legal_currentness='not_verified')


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
