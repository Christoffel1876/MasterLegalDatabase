"""Freeze the independently checked County fee source without canonical ingestion."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import json

from pydantic import BaseModel, ConfigDict
from install_reviewed_watch_batches import ROOT, HANDOFF, Ref, closed, identity, new_file, read

OUT = ROOT / 'research/local_review/pueblo-county-planning-fees-source-qa-2026-09-13'
QA_PIN = 'e1af59772ed9d1ee9d2bcb2ee20f8514efdbaa8fe5743dd0a029c5f5d4399536'
AUDIT_PIN = '409932920312c5f0e6e509f4d2289279d41e6ad24471cd72e7e0ae4331889d87'


class Acceptance(BaseModel):
    """Complete document fidelity approval remains separate from intake and currentness."""
    model_config = ConfigDict(extra='forbid')
    accepted_at: datetime
    status: Literal['accepted_complete_source_fidelity_pending_separate_intake']
    source_id: Literal['pueblo-county-planning-fees-sh-ext-002']
    authority_id: Literal['CO-COUNTY-PUEBLO']
    source: Ref
    source_qa: Ref
    independent_manifest_sha256: str
    root_direct_visual_pages: list[int]
    independent_direct_visual_pages: list[int]
    physical_rows: Literal[88] = 88
    labeled_fee_rows: Literal[69] = 69
    native_lines: Literal[145] = 145
    native_bytes: Literal[3187] = 3187
    structural_tests_passed: Literal[34] = 34
    structural_coverage_combined_percent: float
    root_review_method: str
    qualifications: list[str]
    canonical_intakes: Literal[0] = 0
    public_requests_by_acceptance: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None


class Manifest(BaseModel):
    """All preserved files, excluding only this externally pinned manifest."""
    model_config = ConfigDict(extra='forbid')
    files: list[Ref]
    status: Literal['frozen_source_qa_with_separate_root_acceptance']
    legal_currentness: Literal['not_verified'] = 'not_verified'


def main() -> None:
    """Preserve preparation history, exact reviewed data and independent acceptance."""
    if OUT.exists():
        raise ValueError('Source review already preserved')
    _, audit = closed(HANDOFF / 'pueblo-county-fees-independent-review', AUDIT_PIN)
    current = HANDOFF / 'pueblo-county-fees-source-review-revision'
    qa_raw = read(current / 'SOURCE_QA.json')
    if identity('SOURCE_QA.json', qa_raw).sha256 != QA_PIN:
        raise ValueError('Reviewed source data changed')
    payloads = {'independent-review/' + k: v for k, v in audit.items()}
    for name in ['pueblo-county-fees-source-review', 'pueblo-county-fees-source-review-revision',
                 'pueblo-county-fees-validation']:
        directory = HANDOFF / name
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                relative = name + '/' + path.relative_to(directory).as_posix()
                payloads[relative] = read(path)
    coverage = read(Path('/private/tmp/pueblo-county-qa-coverage.json'))
    payloads['pueblo-county-fees-validation/coverage.json'] = coverage
    totals = json.loads(coverage)['totals']
    percent = 100 * (totals['covered_lines'] + totals['covered_branches']) / (
        totals['num_statements'] + totals['num_branches'])
    acceptance = Acceptance(accepted_at=datetime.now(timezone.utc),
        status='accepted_complete_source_fidelity_pending_separate_intake',
        source_id='pueblo-county-planning-fees-sh-ext-002', authority_id='CO-COUNTY-PUEBLO',
        source=identity('pueblo-county-fees-source-review-revision/original.pdf',
                        read(current / 'original.pdf')),
        source_qa=identity('pueblo-county-fees-source-review-revision/SOURCE_QA.json', qa_raw),
        independent_manifest_sha256=AUDIT_PIN, root_direct_visual_pages=[1, 2],
        independent_direct_visual_pages=[1, 2], structural_coverage_combined_percent=percent,
        root_review_method='Candidate-aware comparison of both complete source images, all '
            'physical rows and exact native characters/drawing geometry. Independent reviewer '
            'also directly viewed both pages and replayed their complete pixels from the PDF.',
        qualifications=[
            'Table row counts are not counts of legal obligations or statewide coverage.',
            'The initial preparation attached global marker notes too narrowly to Appeals. '
            'The preserved revision removes that association and retains explicit markers, '
            'all four continuation rows and the Certificates caret group context.',
            'Preserve source wording, Actual Cost and No Charge, all conditional amounts, '
            'advertising/recording notes, and both fire-fee payment milestones without arithmetic.',
            'County attribution derives from the exact official-parent DOM link. The two '
            'PDF faces have no clear issuer, adopting instrument, date or execution heading.',
            'Filename Adopted5.8.25, Last-Modified and PDF metadata are separate recorded claims; '
            'they are not verified adoption/effectiveness. The denied commissioner catalog '
            'remains unresolved.',
            'HTTP statuses/times and bodies were received from Sherlock. Root did not witness '
            'his original transfer command; do not relabel this as a root public acquisition.',
            'Independent review used a selected1415-row legacy comparison. A separate full '
            'legacy/custody audit and concrete intake transaction remain pending.',
            'No canonical record, legal-currentness status, fee calculation or ordinary '
            'answering capability is added by this source-fidelity acceptance.',
        ])
    payloads['ROOT_ACCEPTANCE.schema.json'] = (
        json.dumps(Acceptance.model_json_schema(), indent=2) + '\n').encode()
    payloads['ROOT_ACCEPTANCE.json'] = (acceptance.model_dump_json(indent=2) + '\n').encode()
    payloads[Path(__file__).name] = read(Path(__file__))
    payloads['MANIFEST.schema.json'] = (json.dumps(Manifest.model_json_schema(), indent=2) + '\n').encode()
    payloads['README.md'] = (
        '---\nstatus: accepted_complete_source_fidelity_pending_separate_intake\n'
        'legal_currentness: not_verified\nanswer_safe: false\n---\n'
        '# Pueblo County planning fee source review\n\n'
        'Atlas and an independent reviewer compared both complete pages and all88 physical '
        'table rows. Exact source/native bytes and conditional row context remain preserved. '
        'This is source-fidelity approval; collection ownership, received transport and unknown '
        'adoption/currentness are explicitly qualified in ROOT_ACCEPTANCE.json.\n\n'
        'The first preparation, its corrected global-note association, all received discovery '
        'artifacts and the independent review are retained separately. No canonical intake '
        'is performed by this package.\n\n'
        'Read-only source check: python -B pueblo-county-fees-validation/verify_source_review.py '
        '--root pueblo-county-fees-source-review-revision\n'
    ).encode()
    manifest = Manifest(status='frozen_source_qa_with_separate_root_acceptance',
                        files=[identity(k, v) for k, v in sorted(payloads.items())])
    for name, raw in payloads.items():
        new_file(OUT / name, raw)
    raw = (manifest.model_dump_json(indent=2) + '\n').encode()
    new_file(OUT / 'MANIFEST.json', raw)
    print(json.dumps({'root': str(OUT), 'files': len(payloads),
                      'manifest_sha256': identity('MANIFEST.json', raw).sha256,
                      'acceptance_sha256': identity('ROOT_ACCEPTANCE.json',
                                                    payloads['ROOT_ACCEPTANCE.json']).sha256}))


if __name__ == '__main__':
    main()
