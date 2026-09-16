"""Preserve supplied evidence and check identities offline; do not adjudicate source glyphs."""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import jsonschema
import pymupdf
from PIL import Image
from models import Audit, Issue, Manifest, NativePage, PageCheck, PromptCheck, Ref, SourceCheck
from models import SuppliedPrompt

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[3]
REPO = PROJECT / 'MasterLegalDatabase'
PRIOR = REPO / 'research/local_review/ebenezer-019-020-reconciliation-2026-09-13'
REVIEWS = PROJECT / 'handoffs/run-2026-09-12/ebenezer/reviews'
PACKET = PRIOR / 'frozen/source-packet'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ordinary(path: Path) -> Path:
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Unsafe ordinary input')
    return path


def reference(path: Path) -> Ref:
    data = ordinary(path).read_bytes()
    return Ref(path=path.relative_to(BASE).as_posix(), sha256=digest(data), size_bytes=len(data))


def save(path: Path, data: bytes) -> Ref:
    if path.exists():
        raise ValueError('Refuse to overwrite audit evidence')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(data)
    temp.replace(path)
    return reference(path)


def copy(source: Path, relative: str) -> Ref:
    return save(BASE / relative, ordinary(source).read_bytes())


def check(root: Path, ref: dict) -> bytes:
    path = PurePosixPath(ref['path'])
    if path.is_absolute() or '..' in path.parts or str(path) != ref['path']:
        raise ValueError('Unconfined input reference')
    data = ordinary(root / path).read_bytes()
    if len(data) != ref['size_bytes'] or digest(data) != ref['sha256']:
        raise ValueError('Input hash mismatch: ' + str(path))
    return data


def save_json(path: Path, model) -> None:
    save(path, (model.model_dump_json(indent=2) + '\n').encode())
    save(path.with_suffix('.schema.json'),
         (json.dumps(model.model_json_schema(), indent=2) + '\n').encode())


receipt_data = ordinary(PRIOR / 'RECEIPT.json').read_bytes()
receipt = json.loads(receipt_data)
jsonschema.Draft202012Validator(json.loads((PRIOR / 'RECEIPT.schema.json').read_bytes())).validate(receipt)
for item in receipt['files']:
    check(PRIOR / 'frozen', item)
receipt_ref = copy(PRIOR / 'RECEIPT.json', 'inputs/prior-root-RECEIPT.json')
copy(PRIOR / 'RECEIPT.schema.json', 'inputs/prior-root-RECEIPT.schema.json')

# Preserve the tar first; validate all members and its inventory before creating any member file.
tar_name = 'methods-clarification-019-020_20260913T014200Z.tar.gz'
tar_ref = copy(REVIEWS / tar_name, 'received/' + tar_name)
loose_name = 'ADDITIVE_METHODS_CLARIFICATION_019-020_20260913T014200Z.md'
loose_ref = copy(REVIEWS / loose_name, 'received/' + loose_name)
members = {}
directories = 0
seen = set()
with tarfile.open(BASE / tar_ref.path, 'r:gz') as archive:
    for member in archive:
        path = PurePosixPath(member.name)
        normalized = member.name.rstrip('/') if member.isdir() else member.name
        if (path.is_absolute() or '..' in path.parts or str(path) != normalized or
                member.name in seen or not (member.isfile() or member.isdir())):
            raise ValueError('Unsafe/duplicate/link archive member')
        seen.add(member.name)
        if len(seen) > 20 or member.size > 100000 or sum(len(x) for x in members.values()) > 1000000:
            raise ValueError('Unexpected archive bounds')
        if member.isdir():
            directories += 1
            continue
        content = archive.extractfile(member).read(member.size + 1)
        if len(content) != member.size:
            raise ValueError('Archive member size mismatch')
        members[member.name] = content
prefix = 'geode-methods-clarification-019-020/'
if any(not name.startswith(prefix) for name in members):
    raise ValueError('Unexpected archive root')
claims = {}
for line in members[prefix + 'INVENTORY_sha256.txt'].decode().splitlines():
    match = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9_.-]+)', line)
    if not match or match[2] in claims:
        raise ValueError('Invalid or duplicate supplied inventory claim')
    claims[match[2]] = match[1]
if set(claims) != {name[len(prefix):] for name in members if not name.endswith('/INVENTORY_sha256.txt')}:
    raise ValueError('Supplied inventory membership mismatch')
for name, expected in claims.items():
    if digest(members[prefix + name]) != expected:
        raise ValueError('Supplied inventory digest differs')
if members[prefix + loose_name] != (BASE / loose_ref.path).read_bytes():
    raise ValueError('Loose clarification differs from tar')
for name, content in members.items():
    save(BASE / 'received/tar-members' / name, content)

prompts = []
for name, content in sorted(members.items()):
    if not name.endswith('.json'):
        continue
    prompt = SuppliedPrompt.model_validate_json(content)
    material = prompt.prompt.encode('utf-8')
    observations = ['Received Task input JSON; parent transcript and automatic attachment captions are not included.']
    if 'pass2' in name:
        observations += ['Contains coordinator-supplied expected candidate SHA and frozen Pass1 hashes.',
                         'This is a candidate-aware comparison, not a blind source-first pass.']
    else:
        observations += ['Instructs caption-mediated access and sealed candidate until Pass1 freeze.']
    if 'fresh_019b' in name and 'pass1' in name:
        observations += ['Explicitly discloses interrupted earlier source exposure and possible recollection.']
    if name.startswith(prefix + '020_pass2'):
        observations += ['Prompt explicitly supplies Pass1 spelling uncertainties; not an independent new finding.']
    prompts.append(PromptCheck(artifact=reference(BASE / 'received/tar-members' / name),
        supplied_transcript_line=prompt.transcript_line, prompt_utf8_sha256=digest(material),
        prompt_utf8_bytes=len(material), prompt_characters=len(prompt.prompt),
        attachment_count=len(prompt.attachments), purpose=prompt.description,
        observations=observations))

# Retain exact root instruction/dispatch bytes separately from supplied Task extracts.
for path in sorted((PRIOR / 'frozen/restart-authorization').iterdir()):
    if path.is_file():
        copy(path, 'inputs/restart-authorization/' + path.name)
manifest_data = ordinary(PACKET / 'manifest.json').read_bytes()
if digest(manifest_data) != 'b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112':
    raise ValueError('Wrong original source-packet manifest')
manifest = json.loads(manifest_data)
jsonschema.Draft202012Validator(json.loads((PACKET / 'manifest.schema.json').read_bytes())).validate(manifest)
manifest_ref = copy(PACKET / 'manifest.json', 'inputs/original-source-packet-manifest.json')
copy(PACKET / 'manifest.schema.json', 'inputs/original-source-packet-manifest.schema.json')
report_files = []
for path in sorted((PRIOR / 'frozen/received').rglob('*')):
    if path.is_file():
        report_files.append(copy(path, 'received/reviewer/' + path.relative_to(
            PRIOR / 'frozen/received').as_posix()))

sources = []
for document in manifest['documents']:
    identity = document['identity']
    assignment = identity['assignment_id']
    if assignment not in {'EB-PDF-019', 'EB-PDF-020'}:
        continue
    sid = identity['source_id']
    source_body = check(PACKET, identity['original'])
    canonical = Path(document['custody']['raw_copy']['original']['path'])
    if not canonical.is_relative_to(REPO / '_RAW_ARCHIVE/manual_intake'):
        raise ValueError('Unexpected original repository path')
    if ordinary(canonical).read_bytes() != source_body:
        raise ValueError('Canonical original differs')
    source_ref = save(BASE / 'source-evidence' / sid / 'original.pdf', source_body)
    candidate = check(PACKET, document['candidate'])
    candidate_ref = save(BASE / 'source-evidence' / sid / 'candidate.txt', candidate)
    received = BASE / 'received/reviewer' / assignment
    freeze = json.loads((received / 'PASS1_FREEZE_RECEIPT.json').read_bytes())
    complete = json.loads((received / 'COMPLETION_RECEIPT.json').read_bytes())
    if assignment == 'EB-PDF-019':
        bindings = complete['bindings']
        expected_candidate = bindings['candidate_txt']
        reported_pdf = bindings['original_pdf']['sha256']
        reported_pages = bindings['pages']
        report_bindings = [('PASS1_frozen.md', bindings['PASS1_frozen_md']),
            ('PASS1_FREEZE_RECEIPT.json', bindings['PASS1_FREEZE_RECEIPT_json']),
            ('PASS1_NOTES.md', bindings['PASS1_NOTES_md']),
            ('PASS2_REVIEW.md', bindings['PASS2_REVIEW_md'])]
        assert freeze['bindings']['full_manifest_opened'] is False
    else:
        expected_candidate = complete['candidate']
        reported_pdf = complete['original_pdf']['sha256']
        reported_pages = complete['pages']
        report_bindings = [('PASS1_frozen.md', complete['PASS1_frozen_md']),
            ('PASS1_FREEZE_RECEIPT.json', complete['PASS1_FREEZE_RECEIPT']),
            ('PASS1_NOTES.md', complete['PASS1_NOTES_md']),
            ('PASS2_REVIEW.md', complete['PASS2_REVIEW_md'])]
        assert complete['full_manifest_opened'] is False
    for name, binding in report_bindings:
        body = (received / name).read_bytes()
        if digest(body) != binding['sha256'] or len(body) != binding['size_bytes']:
            raise ValueError('External report/receipt binding differs')
    if (expected_candidate['sha256'] != digest(candidate) or
            expected_candidate['size_bytes'] != len(candidate) or
            reported_pdf != digest(source_body)):
        raise ValueError('Candidate or declared PDF identity differs')
    pages = []
    with pymupdf.open(stream=source_body, filetype='pdf') as pdf:
        if len(pdf) != identity['expected_pages'] or pdf.is_repaired or pdf.is_encrypted:
            raise ValueError('Unexpected source PDF structure')
        for image_record, native_record, reported in zip(
                identity['pages'], document['candidate_pages'], reported_pages, strict=True):
            page_number = image_record['physical_page']
            image = check(PACKET, image_record['image'])
            image_ref = save(BASE / 'source-evidence' / sid / f'page-{page_number:04d}.png', image)
            with Image.open(BASE / image_ref.path) as png:
                dimensions = png.size
                png.verify()
            if dimensions != (image_record['width'], image_record['height']):
                raise ValueError('Page geometry differs')
            if (reported['physical_page'] != page_number or reported['sha256'] != digest(image)
                    or reported['size_bytes'] != len(image)):
                raise ValueError('External page-image identity differs')
            evidence = check(PACKET, native_record['evidence'])
            native = NativePage.model_validate_json(evidence)
            extracted = pdf[page_number - 1].get_text('text', sort=False, flags=195).encode('utf-8')
            start, end = native_record['start_byte'], native_record['end_byte_exclusive']
            if (native.source_id != sid or native.source_sha256 != digest(source_body) or
                    native.physical_page != page_number or native.expected_pages != len(pdf) or
                    native.source_image_sha256 != digest(image) or native.text.encode() != extracted or
                    digest(extracted) != native.text_sha256 or len(extracted) != native.text_size_bytes or
                    candidate[start:end] != extracted or native_record['text_sha256'] != digest(extracted)):
                raise ValueError('Native extraction/candidate slice binding differs')
            evidence_ref = save(BASE / 'source-evidence' / sid / f'page-{page_number:04d}.json', evidence)
            pages.append(PageCheck(physical_page=page_number, image=image_ref, dimensions=dimensions,
                evidence=evidence_ref, native_sha256=digest(extracted), native_bytes=len(extracted),
                candidate_start_byte=start, candidate_end_byte_exclusive=end,
                native_reproduction='exact', external_receipt_image_match=True))
        sources.append(SourceCheck(assignment_id=assignment, source_id=sid,
            authority_id=identity['authority_id'], source=source_ref,
            source_canonical_path=canonical.relative_to(REPO).as_posix(),
            canonical_sha256_match=True, source_pdf_pages=len(pdf), candidate=candidate_ref,
            external_reported_candidate_sha_match=True, actual_manifest_identity_match_now=True,
            historical_worker_pdf_rehash='not_performed_reported_absent',
            historical_worker_manifest_identity_lookup='not_performed_reported_unopened', pages=pages))

issues = [
    Issue(issue_id='M01', classification='identity_verified_now',
        statement='Both retained PDFs, all eight complete page PNGs and both candidates match the original packet manifest; all eight native slices reproduce exactly with PyMuPDF 1.28.2.',
        evidence=['inputs/original-source-packet-manifest.json', 'source-evidence/'],
        consequence='Closes the current local byte-identity check only; not historical worker access, chronology, visual accuracy or currentness.'),
    Issue(issue_id='M02', classification='procedure_deviation',
        statement='Both workers report full_manifest_opened=false. Supplied Pass2 Task prompts give expected candidate hashes supplied by the coordinator, rather than demonstrating the required post-freeze manifest lookup.',
        evidence=['inputs/restart-authorization/START_HERE.md', 'received/tar-members/'],
        consequence='Keep expected-hash comparison separate from manifest identity verification performed in this audit. Do not retrospectively certify full protocol compliance.'),
    Issue(issue_id='M03', classification='method_limit',
        statement='Original PDFs were reported absent and unopened in both worker directories. Declared PDF hashes matched source-only identities; they were not locally recomputed by those workers.',
        evidence=['received/reviewer/EB-PDF-019/PASS1_FREEZE_RECEIPT.json', 'received/reviewer/EB-PDF-020/PASS1_FREEZE_RECEIPT.json'],
        consequence='The PDF hashes rechecked now do not establish historical PDF inspection. Page-image access was the reported review representation.'),
    Issue(issue_id='M04', classification='addendum_clarification',
        statement='The clarification initially says exact Task prompt bytes were not saved, then supplies five later-located Task input JSON extracts in its addendum. All five supplied file hashes match its inventory.',
        evidence=['received/' + loose_name, 'received/tar-members/' + prefix + 'INVENTORY_sha256.txt'],
        consequence='Retain both statements and treat the addendum as an additive delivery. Parent transcript origin and exact extraction chronology remain supplied claims, not independently authenticated.'),
    Issue(issue_id='M05', classification='addendum_clarification',
        statement='The supplied Task prompt text has paths/instructions rather than page-description prose. The clarification attributes extra descriptions to attachment mediation and Cursor Read, not to Atlas-authored activation text.',
        evidence=['inputs/restart-authorization/START_HERE.md', 'received/tar-members/'],
        consequence='Correct the interpretation of activating_user_message_image_descriptions; do not invent the unretained automatic attachment context or identify its unknown supplier.'),
    Issue(issue_id='M06', classification='method_limit',
        statement='EB019 reports prior interrupted source exposure and explicitly paraphrased/unchecked spans. EB020 retains caption-output inventories and crop images rather than exact full caption transcripts.',
        evidence=['received/reviewer/EB-PDF-019/PASS1_NOTES.md', 'received/reviewer/EB-PDF-020/tool_outputs/PASS1_tool_output_inventory.md', 'received/reviewer/EB-PDF-020/tool_outputs/PASS2_tool_output_inventory.md'],
        consequence='Reported all-page assisted coverage is not complete verbatim transcription or direct pixel verification. Keep specific unchecked spans and shared-caption/OCR error risks.'),
    Issue(issue_id='M07', classification='method_limit',
        statement='Reported freeze/release times and delivered hashes do not independently prove unseen worker chronology or the Pass1 chat-hash gate. Separate executor roles and underlying models remain reported identities.',
        evidence=['inputs/restart-authorization/DISPATCH.json', 'received/reviewer/'],
        consequence='No blind-pass, model-diversity or independently authenticated chronology claim.'),
    Issue(issue_id='M08', classification='procedure_deviation',
        statement='The activation ends with no bot delegation authorized; the clarification reports coordinator-to-executor subagent Tasks. No separately documented exception is in these retained activation artifacts.',
        evidence=['inputs/restart-authorization/START_HERE.md', 'received/' + loose_name],
        consequence='Root should explicitly reconcile the internal executor workflow with that instruction. This audit records the wording conflict without inferring unseen permissions.'),
    Issue(issue_id='M09', classification='inherited_visual_disposition',
        statement='Root independently rejected EB020-P2-001 through EB020-P2-004: Temproary, clipped if applicab, Transportion and Phenophthalein are source print, not candidate extraction errors.',
        evidence=['received/reviewer/EB-PDF-020/PASS2_REVIEW.md'],
        consequence='Preserve Root’s visual disposition separately from the external report. This methods audit performs no new visual adjudication and does not normalize those source strings.'),
]
audit = Audit(audited_at=datetime.now(timezone.utc),
    status='custody_verified_methods_qualified_pending_root_disposition',
    reviewed_scope='Offline custody, exact source/page/candidate identity and supplied reviewer methods; no visual source-content review.',
    original_manifest=manifest_ref, received_package_receipt=receipt_ref,
    frozen_receipt_files_verified=len(receipt['files']), clarification_tar=tar_ref,
    tar_regular_members=len(members), tar_directory_members=directories,
    supplied_inventory_files_verified=len(claims), loose_clarification_matches_tar=True,
    prompt_checks=prompts, source_checks=sources, received_report_files=report_files, issues=issues)
save_json(BASE / 'METHODS_AUDIT.json', audit)
print(audit.model_dump_json(exclude={'received_report_files','prompt_checks','source_checks','issues'},indent=2))
