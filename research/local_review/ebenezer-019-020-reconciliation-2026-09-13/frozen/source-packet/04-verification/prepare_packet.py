"""Build only this new Weld review packet from already retained repository bytes."""
from __future__ import annotations

import hashlib
import json
import os
import runpy
import struct
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2] / 'MasterLegalDatabase'
M = runpy.run_path(str(BASE / '04-verification/validate_packet.py'))
_existing_native = BASE / '02-candidate-text/weld-building-fees-sd008-01/native-evidence/page-0001.json'
NOW = (datetime.fromisoformat(json.loads(_existing_native.read_bytes())['extracted_at'].replace('Z', '+00:00'))
       if _existing_native.exists() else datetime.now(timezone.utc))
COPIES = []


def write_new(path: Path, body: bytes) -> None:
    """Allow exact existing preparation inputs, refusing any changed overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError(f'Refusing changed overwrite: {path}')
        return
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(body)
    os.replace(temp, path)


def encoded(model) -> bytes:
    """Validate a typed record before serialization and atomic creation."""
    body = (model.model_dump_json(indent=2) + '\n').encode('utf-8')
    type(model).model_validate_json(body)
    return body


def copy(source: Path, relative: str, role: str):
    """Retain original bytes under an exact historical-to-frozen identity."""
    source = M['ordinary'](source)
    dest = BASE / relative
    write_new(dest, source.read_bytes())
    result = M['Copy'](
        original=M['HistoricalRef'](path=str(source), sha256=M['digest'](source),
                                    size_bytes=source.stat().st_size),
        frozen=M['ref'](BASE, dest), role=role)
    COPIES.append(result)
    return result


def find_row(path: Path, key: str, value: str):
    """Stream exact rows and select one, rejecting duplicate identities."""
    selected = []
    with path.open('rb') as stream:
        for number, line in enumerate(stream, 1):
            row = json.loads(line)
            if row.get(key) == value:
                selected.append((number, line, row))
    if len(selected) != 1:
        raise ValueError('Missing/duplicate selected custody row')
    return selected[0]


def row_ref(frozen, schema, number: int, line: bytes):
    """Bind exact original raw JSONL line bytes including its newline."""
    return M['JSONLRow'](file=frozen, schema_file=schema, physical_line=number,
                         line_sha256=hashlib.sha256(line).hexdigest(),
                         line_size_bytes=len(line))


def main() -> None:
    """Build the neutral identities, sealed evidence and closed inventory once."""
    for filename, model in [
        ('manifest.schema.json', M['Manifest']),
        ('SOURCE_ONLY_IDENTITIES.schema.json', M['SourceIdentities']),
        ('02-candidate-text/native-page.schema.json', M['NativePage']),
        ('04-verification/PREPARATION_CHECK.schema.json', M['CheckReceipt']),
        ('INVENTORY.schema.json', M['Inventory']),
    ]:
        write_new(BASE / filename, (json.dumps(model.model_json_schema(), indent=2) + '\n').encode())
    raw = REPO / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    raw_copy = copy(raw, f'03-custody/manual-source-intake-manifest.{M["digest"](raw)}.jsonl',
                    'Exact current manual manifest preimage; source dates and notes remain qualified.')
    common = REPO / 'research/local_review/weld-greeley-intake-sherlock008-2026-09-11'
    direct = REPO / 'research/local_review/weld-directed-intake-2026-09-11'
    raw_schema = copy(common / 'intake-record.schema.json', '03-custody/manual-record.schema.json',
                      'Existing strict ManualSourceIntakeRecord schema.')
    provenance_files = {}
    for folder, prefix, stem in [(common, 'received-sd008', 'source-provenance'),
                                 (direct, 'directed-weld', 'source-provenance.final')]:
        prov = copy(folder / (stem + '.jsonl'), f'03-custody/{prefix}/source-provenance.jsonl',
                    'Exact source provenance; prior findings withheld until first-pass freeze.')
        schema = copy(folder / (stem + '.schema.json'),
                      f'03-custody/{prefix}/source-provenance.schema.json',
                      'Exact matching provenance schema.')
        provenance_files[prefix] = (folder / (stem + '.jsonl'), prov.frozen, schema.frozen)
        for name in ('intake-receipt.json', 'intake-receipt.schema.json'):
            copy(folder / name, f'03-custody/{prefix}/{name}',
                 'Exact historical intake receipt/schema; original referenced histories not recertified.')
    prior = copy(BASE.parent / 'ebenezer/ACTIVATION.md', '03-custody/prior-activation-method.md',
                 'Exact prior queue method policy; its assignments are not activated by this packet.')
    documents = []
    native_bytes = 0
    qa_viewed = []
    for aid, sid, count, expected_sha in M['SPECS']:
        line_number, raw_line, row = find_row(raw, 'record_id', sid)
        source = REPO / row['archive_path']
        if (M['digest'](source), source.stat().st_size) != (expected_sha, row['size_bytes']):
            raise ValueError('Current canonical original differs')
        original_copy = copy(source, f'01-source-only/{sid}/original.pdf',
                             'Byte-exact original PDF; no re-export or repair.')
        prefix = 'received-sd008' if aid == 'EB-PDF-018' else 'directed-weld'
        prov_path, prov_ref, prov_schema = provenance_files[prefix]
        pn, pline, pro = find_row(prov_path, 'source_id', sid)
        if pro['authority_id'] != 'CO-COUNTY-WELD':
            raise ValueError('Wrong preserved source authority')
        if prefix == 'directed-weld':
            for key in ('access_receipt', 'public_headers'):
                historical = pro[key]
                src = direct / historical['path']
                if M['digest'](src) != historical['sha256']:
                    raise ValueError('Retained HTTP evidence changed')
                copy(src, f'03-custody/{prefix}/{sid}/{key}' + src.suffix,
                     'Exact retained public acquisition evidence; no new network replay.')
        images = []
        candidate_pages = []
        candidate = bytearray()
        with pymupdf.open(source) as pdf:
            if pdf.is_repaired or pdf.is_encrypted or len(pdf) != count:
                raise ValueError('PDF page count/structure differs')
            for index, page in enumerate(pdf, 1):
                image = BASE / f'01-source-only/{sid}/page-{index:04d}.png'
                with image.open('rb') as stream:
                    header = stream.read(24)
                width, height = struct.unpack('>II', header[16:24])
                image_ref = M['ref'](BASE, image)
                images.append(M['ImageIdentity'](physical_page=index, image=image_ref,
                                                  width=width, height=height))
                text = page.get_text('text', sort=False, flags=195)
                b = text.encode('utf-8')
                native_bytes += len(b)
                evidence = M['NativePage'](source_id=sid, source_sha256=expected_sha,
                    physical_page=index, expected_pages=count, source_image_sha256=image_ref.sha256,
                    extracted_at=NOW, text=text, text_sha256=hashlib.sha256(b).hexdigest(),
                    text_size_bytes=len(b))
                ep = BASE / f'02-candidate-text/{sid}/native-evidence/page-{index:04d}.json'
                write_new(ep, encoded(evidence))
                candidate.extend(f'===== PHYSICAL PDF PAGE {index} OF {count} (PACKAGING MARKER) =====\n'.encode())
                start = len(candidate)
                candidate.extend(b)
                candidate_pages.append(M['CandidatePage'](physical_page=index,
                    evidence=M['ref'](BASE, ep), text_sha256=evidence.text_sha256,
                    text_size_bytes=len(b), start_byte=start, end_byte_exclusive=len(candidate)))
                candidate.extend(f'\n===== END PHYSICAL PDF PAGE {index} (PACKAGING MARKER) =====\n\n'.encode())
                qa_viewed.append(f'{sid}:page-{index:04d}')
        candidate_path = BASE / f'02-candidate-text/{sid}/candidate.txt'
        write_new(candidate_path, bytes(candidate))
        identity = M['BlindDocument'](assignment_id=aid, source_id=sid, expected_pages=count,
                                     original=original_copy.frozen, pages=images)
        custody = M['Custody'](raw_copy=original_copy,
            manual_record=row_ref(raw_copy.frozen, raw_schema.frozen, line_number, raw_line),
            provenance_record=row_ref(prov_ref, prov_schema, pn, pline),
            preserved_acquisition_method=row['acquisition_method'],
            preserved_repository_received_at=datetime.fromisoformat(row['received_at'].replace('Z', '+00:00')))
        documents.append(M['Document'](identity=identity, custody=custody,
            candidate=M['ref'](BASE, candidate_path), candidate_pages=candidate_pages,
            native_evidence_schema=M['ref'](BASE, BASE / '02-candidate-text/native-page.schema.json')))
    identities = M['SourceIdentities'](documents=[d.identity for d in documents])
    write_new(BASE / 'SOURCE_ONLY_IDENTITIES.json', encoded(identities))
    manifest = M['Manifest'](prepared_at=NOW,
        start_no_document_at_or_after='2026-09-13T01:25:00Z', hard_stop='2026-09-13T01:55:00Z',
        task_id='01a08848-5f8e-7c51-9b66-fd82eff860fe',
        source_only_identities=M['ref'](BASE, BASE / 'SOURCE_ONLY_IDENTITIES.json'),
        source_only_schema=M['ref'](BASE, BASE / 'SOURCE_ONLY_IDENTITIES.schema.json'),
        instructions=M['ref'](BASE, BASE / 'START_HERE.md'), documents=documents,
        custody_copies=COPIES, limitations=[
            'PREPARED_NOT_DISPATCHED. Completion of EB015–017 does not dispatch this queue; Atlas must explicitly activate it before the current no-new-document cutoff.',
            'Thirteen full source-page images and every native text byte are retained. Native candidates are uncorrected and unreviewed in this packet; tables, notes, glyphs, graphics and layout may be lost or misassociated.',
            'Direct pixels are preferred; a disclosed caption-mediated source-first method is permitted only as assisted work pending Atlas actual-image verification. Candidate access stays sealed until each pass-1 report, receipt and chat hash are frozen.',
            'Historical raw-manifest/source-provenance and intake receipt copies contain earlier qualified findings. They are withheld from source-first review. Receipt times remain distinct from actual/reported acquisition times; no new HTTP replay occurred.',
            'Weld building-fee successful request/final URL remains unresolved in retained received-package provenance. Two directed-source acquisition records retain their direct HTTP evidence. No transport or status claim is newly inferred.',
            'The ordinance is a separate zoning instrument, not demonstrated here to adopt either fee schedule. The queue order does not create a legal chain.',
            'Prior full review packages, full original HTTP headers, delivery archives and every historical file mentioned by copied receipts are not all included or revalidated. Frozen selected custody rows and available public HTTP evidence are included; absolute original paths are historical only.',
            'Source defects, blanks, dates, source claims and native/visible discrepancies remain untouched. No currentness, applicability, adoption, signature identity, arithmetic, RuleUnit or geographic-coverage promotion is made.',
        ])
    write_new(BASE / 'manifest.json', encoded(manifest))
    write_new(BASE / 'MANIFEST_SHA256.txt', (M['digest'](BASE / 'manifest.json') + '\n').encode())
    receipt = M['CheckReceipt'](prepared_at=NOW, manifest=M['ref'](BASE, BASE / 'manifest.json'),
                                prior_activation=prior, native_bytes=native_bytes,
                                render_qa_viewed=qa_viewed)
    write_new(BASE / '04-verification/PREPARATION_CHECK.json', encoded(receipt))
    inventory = M['Inventory'](files=[M['ref'](BASE, p) for p in sorted(BASE.rglob('*'))
        if p.is_file() and p.relative_to(BASE).as_posix() not in {'INVENTORY.json', 'INVENTORY.schema.json'}])
    write_new(BASE / 'INVENTORY.json', encoded(inventory))
    print(json.dumps({'prepared_at': NOW.isoformat(), 'documents': 3, 'physical_pages': 13,
                      'native_bytes': native_bytes, 'inventory_files': len(inventory.files)}))


if __name__ == '__main__':
    main()
