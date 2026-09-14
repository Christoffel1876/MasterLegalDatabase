"""Preserve frozen complete reviews after Atlas's own full-page and wording checks."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from jsonschema import Draft202012Validator

RUN = Path(__file__).resolve().parent
REPO = RUN.parents[1] / 'MasterLegalDatabase'

class Asset(BaseModel):
    """Exact portable evidence bytes."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int

class Acceptance(BaseModel):
    """Source-fidelity acceptance bounded by the actual reviewed document."""
    model_config = ConfigDict(extra='forbid', strict=True)
    status: Literal['accepted_complete_source_fidelity']
    recorded_at: datetime
    source_id: str
    authority_id: str
    source: Asset
    source_qa: Asset
    source_qa_schema: Asset
    independent_manifest: Asset
    full_pages_directly_inspected_by_atlas: list[int]
    root_review: str
    validated_scope: dict[str, int]
    code_validation: str
    original_source_and_candidate_unchanged: Literal[True]
    original_review_reports_unchanged: Literal[True]
    legal_currentness: Literal['not_verified']
    adoption_date: None
    effective_date: None
    answer_safe: Literal[False]
    limitations: list[str]

def asset(root: Path, path: Path) -> Asset:
    raw = path.read_bytes()
    return Asset(path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))

def accept(folder: str, output: str, manifest_pin: str, qa_pin: str, schema_pin: str,
           pages: int, root_review: str, scope: dict[str, int]) -> None:
    source = RUN / 'extended-run' / folder
    output_path = REPO / 'research/local_review' / output
    assert not output_path.exists()
    for name, expected in [('FINAL_MANIFEST.json', manifest_pin), ('SOURCE_QA.json',qa_pin),
                           ('SOURCE_QA.schema.json', schema_pin)]:
        assert asset(source, source / name).sha256 == expected
    manifest = json.loads((source / 'FINAL_MANIFEST.json').read_bytes())
    items = manifest['files'] if isinstance(manifest, dict) else manifest
    names = [item['path'] for item in items]
    assert len(names) == len(set(names))
    extras = {'FINAL_MANIFEST.json'}
    if (source / 'FINAL_MANIFEST.schema.json').is_file():
        Draft202012Validator(json.loads((source / 'FINAL_MANIFEST.schema.json').read_bytes())).validate(manifest)
        extras.add('FINAL_MANIFEST.schema.json')
    assert {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()} == set(names) | extras
    for item in items:
        assert asset(source, source / item['path']).model_dump() == item
    qa = json.loads((source / 'SOURCE_QA.json').read_bytes())
    Draft202012Validator(json.loads((source / 'SOURCE_QA.schema.json').read_bytes())).validate(qa)
    shutil.copytree(source, output_path / 'independent-review')
    saved = output_path / 'independent-review'
    acceptance = Acceptance(status='accepted_complete_source_fidelity', recorded_at=datetime.now(timezone.utc),
        source_id=qa['source_id'], authority_id=qa['authority_id'],
        source=asset(output_path, saved / qa['source']['path']),
        source_qa=asset(output_path, saved / 'SOURCE_QA.json'),
        source_qa_schema=asset(output_path, saved / 'SOURCE_QA.schema.json'),
        independent_manifest=asset(output_path, saved / 'FINAL_MANIFEST.json'),
        full_pages_directly_inspected_by_atlas=list(range(1,pages+1)),
        root_review=root_review, validated_scope=scope,
        code_validation='Root ran the frozen closed verifier and exact complete-page Poppler rerender successfully. This binds artifacts and does not rerun visual judgment.',
        original_source_and_candidate_unchanged=True, original_review_reports_unchanged=True,
        legal_currentness='not_verified', adoption_date=None, effective_date=None, answer_safe=False,
        limitations=qa['limitations'] + ['Source fidelity only; no current-law, adoption, complete-authority or statewide coverage certification.',
            'Separate root acceptance does not modify the independent report historical pending status.',
            'No reported third-party image-reopening chronology or handwriting identity is certified.'])
    (output_path / 'ROOT_ACCEPTANCE.schema.json').write_text(json.dumps(Acceptance.model_json_schema(),indent=2)+'\n')
    (output_path / 'ROOT_ACCEPTANCE.json').write_text(acceptance.model_dump_json(indent=2)+'\n')
    shutil.copy2(__file__, output_path / 'accept_final_pdf_reviews.py')
    (output_path / 'README.md').write_text('# '+qa['source_id']+' — source-fidelity review accepted\n\n'
        +root_review+'\n\nThe complete independent review and original evidence remain unchanged in independent-review/. ROOT_ACCEPTANCE.json records Atlas’s separate decision. '
        'Legal currentness, adoption and effective dates remain unverified. No current-law answer or raw-source correction was published.\n')
    print(json.dumps({'source_id':qa['source_id'],'root_acceptance':asset(output_path,output_path/'ROOT_ACCEPTANCE.json').model_dump()}))

if __name__ == '__main__':
    accept('eb023-independent-source-review-2026-09-13','eb023-equity-memo-source-qa-2026-09-13',
        '7fc1136d3e233386c19b214f719de82a2448a0cb1c1d2cfc81bffbfad842d196',
        '20f268b2f632d655d25d739002f43b67654c9ce351ca8b6a5bdebac107baa92d',
        '65441faa7e989c6014d4214bb52e6044b95d8c740824145dacee7cf964e64efc',4,
        'Atlas inspected all four full source-page images and the candidate, then read the complete82-block reviewed transcript and all findings. The staff-recommendation role, conditional implementation, missing referenced attachments, all proposed fee tiers and their exceptions are retained. Tier2 continues from page3 to page4; its DNR fee and two remaining characteristics remain attached. Five page4 OCR wording blocks are corrected only in the separate reviewed text; raw OCR remains untouched. Graphic marks are not certified as deletions. Prior unfinished root notes remain historical.',
        {'physical_pages':4,'source_blocks':82,'logical_table_rows':4,'physical_table_fragments':5,'ocr_observations':181,'candidate_bytes':9796})
    accept('eb024-bylaws-independent-review','eb024-bylaws-source-qa-2026-09-13',
        '515205338cbdc4790b99e9c4a91ccbf35beabaf2cf2beeb8d47153a1ef1032d2',
        '8a3d6f2c37fbacacc104ce3fd0dba53806157858f4cb487caf44f1a511657ec6',
        '93882b1944db87dc4e0bd23ce7333497b15c842e977a92a315aa217776800f5c',5,
        'Atlas inspected all five full source-page images, the complete native candidate and the54 contextual portions. Ten sections, all conditions/exceptions and the page4-to-page5 annual-budget continuation are preserved. Source citation spacing, ArticleI versus1 and practical versuspracticable remain unchanged. Atlas initially suspected an absent page5footer; individual-image reinspection and byte-identical root/independent crops disproved that suspicion. The printed5/23/2012 date is visible on all five pages and is an unlabeled footer, not verified adoption. The falsealarm is withdrawn without modifying source or candidate.',
        {'physical_pages':5,'native_bytes':12640,'native_lines':400,'nonblank_lines':170,'paragraph_portions':54,'sections':10})
