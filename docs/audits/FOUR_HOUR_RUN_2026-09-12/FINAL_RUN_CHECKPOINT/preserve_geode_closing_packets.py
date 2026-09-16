"""Preserve frozen reviewed packets and root verification without changing originals."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import hashlib
import json
import shutil
import subprocess
import sys

import jsonschema
from pydantic import BaseModel, ConfigDict, Field

BASE = Path('/Users/mcoors/Documents/Project Geode')
REPO = BASE / 'MasterLegalDatabase'
RUN = BASE / 'handoffs/run-2026-09-12'
AUDIT = REPO / 'docs/audits/FOUR_HOUR_RUN_2026-09-12'
PYTHON = '/private/tmp/geode-status-venv/bin/python'


class Ref(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int = Field(ge=0)


class Acceptance(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    checked_at: str
    status: str
    copied_originals: list[Ref]
    verification_artifacts: list[Ref]
    findings: list[str]
    public_requests_by_this_preservation: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'


def ref(path: Path, root: Path) -> Ref:
    data = path.read_bytes()
    return Ref(path=path.relative_to(root).as_posix(),
               sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def copy_closed(source: Path, target: Path, manifest_name: str,
                resume_identical_copy: bool = False) -> list[Ref]:
    """Verify existing closed inventory and copy exact ordinary bytes."""
    assert not target.exists() or resume_identical_copy, target
    record = json.loads((source / manifest_name).read_bytes())
    schema = json.loads((source / manifest_name.replace('.json', '.schema.json')).read_bytes())
    jsonschema.validate(record, schema)
    expected = {r['path'] for r in record['files']} | {manifest_name}
    actual = set()
    for path in source.rglob('*'):
        assert not path.is_symlink()
        assert path.is_file() or path.is_dir()
        if path.is_file():
            actual.add(path.relative_to(source).as_posix())
    assert actual == expected
    for item in record['files']:
        rel = Path(item['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        assert ref(source / rel, source).model_dump() == item
    if not target.exists():
        shutil.copytree(source, target)
    else:
        assert all(not p.is_symlink() and (p.is_dir() or p.is_file())
                   for p in target.rglob('*'))
        assert {p.relative_to(target).as_posix() for p in target.rglob('*')
                if p.is_file()} == expected
    refs = [ref(path, target) for path in sorted(target.rglob('*')) if path.is_file()]
    for item in refs:
        assert (source / item.path).read_bytes() == (target / item.path).read_bytes()
    return refs


def verify(command: list[str], destination: Path) -> Ref:
    """Save actual root verifier output; no public network is invoked."""
    result = subprocess.run(command, cwd='/private/tmp', capture_output=True,
                            text=True, timeout=100)
    value = {'command': command, 'exit_code': result.returncode,
             'stdout': result.stdout, 'stderr': result.stderr,
             'checked_at': datetime.now(timezone.utc).isoformat()}
    destination.write_text(json.dumps(value, indent=2) + '\n')
    assert result.returncode == 0, value
    return ref(destination, destination.parent)


def write_acceptance(folder: Path, record: Acceptance) -> None:
    """Validate a new root receipt before its first write."""
    schema = Acceptance.model_json_schema()
    data = json.loads(record.model_dump_json())
    jsonschema.validate(data, schema)
    (folder / 'ACCEPTANCE.schema.json').write_text(json.dumps(schema, indent=2) + '\n')
    (folder / 'ACCEPTANCE.json').write_text(json.dumps(data, indent=2) + '\n')


def pueblo() -> None:
    """Keep limited discovery separate from the ongoing complete table review."""
    source = RUN / 'pueblo-fee-discovery'
    target = REPO / 'research/local_review/pueblo-fee-discovery-2026-09-13'
    output = AUDIT / 'PUEBLO_DISCOVERY'
    output.mkdir()
    copied = copy_closed(source, target, 'FINAL_MANIFEST.json')
    verified = verify([PYTHON, '-I', '-B', str(target / 'verify.py')],
                      output / 'copied-packet-verification.json')
    write_acceptance(output, Acceptance(
        checked_at=datetime.now(timezone.utc).isoformat(),
        status='accepted_bounded_discovery_one_city_pdf_county_HTTP403_gap',
        copied_originals=copied, verification_artifacts=[verified], findings=[
            '47 exact files copied; one City of Pueblo planning fee PDF, four structural pages.',
            'Five attempts/four URLs; initial county sandbox failure followed by one authorized '
            'network retry returned HTTP403; no further county request.',
            'Official city HTML anchor and same-host redirect bind exact retained PDF bytes.',
            'Discovery viewed only pages1/4. Separate full source QA is not incorporated here.',
            'The printed2-13-26 date is a source claim, not verified adoption/effectiveness.',
            'Full-file exact URL/hash negative scan is documented, not reproducible from '
            'selected legacy/registry copies; it does not prove statewide absence.',
            'No canonical intake, numeric lookup or current-law promotion.'
        ]))
    print('Preserved Pueblo47-file packet and root acceptance.')


def watch() -> None:
    """Freeze production preparation/reproduction evidence pending final root acceptance."""
    output = AUDIT / 'MANUAL_SOURCE_WATCH'
    output.mkdir()
    production = copy_closed(RUN / 'manual-source-watch-production/final',
                             output / 'preparation', 'FINAL_MANIFEST.json')
    helper = copy_closed(RUN / 'manual-watch-http-review', output / 'http-review', 'MANIFEST.json')
    refs = [Ref(path='preparation/' + x.path, sha256=x.sha256, size_bytes=x.size_bytes)
            for x in production]
    refs += [Ref(path='http-review/' + x.path, sha256=x.sha256, size_bytes=x.size_bytes)
             for x in helper]
    for name in ['geode-watch-final-adapter-check.py',
                 'geode-watch-final-adapter-check-result.json']:
        shutil.copyfile(Path('/private/tmp') / name, output / name)
        refs.append(ref(output / name, output))
    verification = [verify([PYTHON, '-I', '-B', str(output / 'http-review/validate_evidence.py')],
                           output / 'http-review-verification.json')]
    result = json.loads((output / 'geode-watch-final-adapter-check-result.json').read_bytes())
    for name, digest in result['hashes'].items():
        assert hashlib.sha256((REPO / 'geode/pipeline' / name).read_bytes()).hexdigest() == digest
    write_acceptance(output, Acceptance(
        checked_at=datetime.now(timezone.utc).isoformat(),
        status='preparation_preserved_pending_full_suite_and_root_live_decision',
        copied_originals=refs, verification_artifacts=verification, findings=[
            '171 focused tests recorded; adapter90.92% and HTTP helper94.90% combined '
            'statement/branch coverage. Branch-only figures remain separate in PREPARATION.',
            'Independent local replay demonstrates zero-request final-seal recovery, '
            'zero-request initialization expiry and stopped transport_error for slow chunk trailers.',
            'HTTP review historical helper hash differs from final production due to later '
            'typed docstrings/wrapping; final replay binds actual final production hashes.',
            'Root reviewed final adapter execution/recovery/verification and helper framing/deadlines.',
            'No production public execution or scheduler is established by this receipt.',
            'The two earlier actual prototype requests remain separately preserved.'
        ]))
    print('Preserved watch preparation and independent replay, pending final root acceptance.')


def watch_finalization() -> None:
    """Retain the later narrow correction separately from its historical preparation."""
    output = AUDIT / 'MANUAL_SOURCE_WATCH/finalization-review'
    output.mkdir()
    copied = copy_closed(RUN / 'manual-watch-independent-review',
                         output / 'packet', 'FINAL_MANIFEST.json')
    copied = [Ref(path='packet/' + r.path, sha256=r.sha256, size_bytes=r.size_bytes)
              for r in copied]
    checked = verify([PYTHON, '-I', '-B', str(output / 'packet/verify_packet.py')],
                     output / 'root-verification.json')
    write_acceptance(output, Acceptance(
        checked_at=datetime.now(timezone.utc).isoformat(),
        status='accepted_narrow_finalization_fix_focused_tests_passed_full_suite_pending',
        copied_originals=copied, verification_artifacts=[checked], findings=[
            'Root read exact helper/test diff: capture finalization timestamp after hashing '
            'and downgrade complete results at/after their deadline to timeout/partial.',
            'The failed old event never produced false byte equality, but could not seal its report.',
            'Both exact-deadline and1ms-late regressions now preserve bytes, verify a stopped '
            'report and replay with zero extra fixture requests.173 focused tests passed.',
            'Original failing fixture uses an injected clock; it is historical and should '
            'not be rerun against corrected code. This portable verifier checks hashes only.',
            'Root full-suite regression was restarted after this two-file correction.',
            'Earlier preparation remains unchanged and is superseded for these two final hashes.'
        ]))
    print('Preserved finalization repair61-file packet and scoped root acceptance.')


def el_paso_ehs() -> None:
    """Accept the English source review without rewriting intake or legal status."""
    target = REPO / 'research/local_review/el-paso-ehs-fees-source-qa-2026-09-13'
    output = AUDIT / 'EL_PASO_EHS_SOURCE_QA'
    output.mkdir()
    copied = copy_closed(RUN / 'el-paso-ehs-source-qa', target, 'FINAL_MANIFEST.json')
    checked = verify([PYTHON, '-I', '-B', str(target / 'validate_review.py'), '--rerender'],
                     output / 'root-portable-verification.json')
    write_acceptance(output, Acceptance(
        checked_at=datetime.now(timezone.utc).isoformat(),
        status='accepted_complete_english_source_fidelity_review_not_current_law',
        copied_originals=copied, verification_artifacts=[checked], findings=[
            'Source el-paso-boh-ehs-fees-sd011, SHA256 '
            '1b0529fb7514bcc50c0dd36c903ca361f6ab431712b4aebc48bca8e3f5373622: '
            '151508bytes and all5physical pages retained.',
            'Root directly viewed all5full page images plus page5approval-footer crop, '
            'compared all65fee rows/37contexts and read full models/derive/verifier.',
            '65service rows in7groups,74physical grid rows/148cells and102native bindings; '
            'all8060native bytes remain unchanged. Copied rerender/native/grid/crop replay passed.',
            'Printed approval October25,2023/effective January1,2024 and2024/2025fees '
            'remain source claims. Issuer Board of Health and administering Public Health '
            'are distinct from municipal authorities.',
            'General per-visit note, no-fee investigation exception, explicit definitions, '
            'new-permit asterisk and failure-to-pay Section2exception stay attached.',
            'Source closing quote without opening quote, missing for in Full Menu fee, '
            'year-specific cells and statutory-reference-only fee are not silently repaired.',
            'First-pass packaging errata are additive; source-first sequence is recorded, '
            'not independently authenticated. Same-model verification is not external blind review.',
            'No Spanish file reviewed, no translation-equivalence claim, no canonical append '
            'or lookup/monitoring deployment by this acceptance. Integration is a separate decision.',
            'Original received-review-package acquisition and Sherlock transport/cap limits '
            'remain unchanged; source text review does not repair historical HTTP evidence.'
        ]))
    print(json.dumps({'packet_files': len(copied),
                      'acceptance': str(output / 'ACCEPTANCE.json'),
                      'acceptance_sha256': ref(output / 'ACCEPTANCE.json', output).sha256}))


def pueblo_qa() -> None:
    """Keep complete table QA and its corrections separate from discovery and intake."""
    target = REPO / 'research/local_review/pueblo-planning-fees-source-qa-2026-09-13'
    output = AUDIT / 'PUEBLO_SOURCE_QA'
    output.mkdir(exist_ok=True)
    assert not (output / 'ACCEPTANCE.json').exists()
    copied = copy_closed(RUN / 'pueblo-planning-fee-source-qa', target, 'MANIFEST.json', True)
    checked = verify([PYTHON, '-B', str(target / 'validate_qa.py'), '--rerender'],
                     output / 'root-portable-verification-python-B.json')
    write_acceptance(output, Acceptance(
        checked_at=datetime.now(timezone.utc).isoformat(),
        status='accepted_complete_city_source_fidelity_review_pending_separate_intake',
        copied_originals=copied, verification_artifacts=[checked,
            ref(output / 'root-portable-verification.json', output)], findings=[
            'City of Pueblo original SHA256 '
            '0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b, '
            '228376bytes and4physical pages; this is not Pueblo County evidence.',
            'Root directly viewed all4full page images, header/date crops on pages2/3, '
            'and remodel/CCN detail; reviewed full44-row display and QA models/verifier.',
            '44physical application rows and43nested entries are preserved:15paired '
            'subcategories plus28fee bullets, including11Rezoning pairs and6CommercialSitePlan bullets.',
            'All4923native bytes/243lines remain unchanged. Both remodel clauses retain nor; '
            'CCN low graphical mark is annotated separately, not certified as encoded underscore.',
            'Frozen root review erroneously claimed headers/dates missing on pages2/3 '
            'and read or instead of nor. Additive errata explicitly withdraw these claims; '
            'the original frozen review and16original inputs are unchanged.',
            'All4pages visibly carry letterhead, Applications/Fees headers and2-13-26. '
            'No unverified explanation of earlier visual omission is inferred.',
            'Official city referral and redirect/source bytes verified; printed2-13-26 '
            'remains a source date without an established adoption/effectiveness label.',
            '66focused tests recorded; root portable hash/native/grid/crop/full-render replay passed.',
            'Root first invoked isolated Python-I, which excludes sibling qa_model imports '
            'and failed before QA execution. The documented Python-B invocation from outside '
            'the package passed; no package bytes changed. Both invocation records are preserved.',
            'No canonical intake, lookup release, monitoring enrollment, fee calculation '
            'or legal-currentness promotion. County HTTP403 remains separate discovery gap.'
        ]))
    print(json.dumps({'packet_files': len(copied),
                      'acceptance_sha256': ref(output / 'ACCEPTANCE.json', output).sha256}))


if __name__ == '__main__':
    {'pueblo': pueblo, 'watch': watch, 'watch-finalization': watch_finalization,
     'el-paso-ehs': el_paso_ehs, 'pueblo-qa': pueblo_qa}[sys.argv[1]]()
