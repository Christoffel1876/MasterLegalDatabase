"""Prepare three research inventory joins without writing maintained repository files."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / 'MasterLegalDatabase'
PACKAGE = Path('research/local_review/manual-source-review-inventory-2026-09-11')
PROPOSED = HERE / 'proposed'
BASELINE = HERE / 'preimages'
ACCEPTANCES = {
 'research/local_review/pueblo-county-planning-fees-source-qa-2026-09-13/ROOT_ACCEPTANCE.json': 'ec064067521ee2d4c350f049b4ce03bfa2acc31cb378a1008e2f53a6efe07289',
 'research/local_review/pueblo-county-intake-2026-09-13/ROOT_ACCEPTANCE.json': '8decf7b300e2a8d7c139748617e630b8d746caa3b27d08b67e6cdd947acd0bd5',
 'research/local_review/eb023-equity-memo-source-qa-2026-09-13/ROOT_ACCEPTANCE.json': '5cc5d1199ab6af73ee0aa7a0eaf7dd4ab9c620f22470e14586245589f7bcca51',
 'research/local_review/eb024-bylaws-source-qa-2026-09-13/ROOT_ACCEPTANCE.json': '2fe2e6e58d3b52234f2318f816335aea672af5dec7217eab7129a7b32770447a',
}
SCHEMAS = {
 'd55009c3f3bd8ef2930186854c343fa33ff6589ad21eb97cc9f12d6dc5754c03': 'checked_tables',
 '65441faa7e989c6014d4214bb52e6044b95d8c740824145dacee7cf964e64efc': 'checked_tables',
 '93882b1944db87dc4e0bd23ce7333497b15c842e977a92a315aa217776800f5c': 'checked_passages',
}

def asset(path: Path, relative: str | None = None) -> dict:
    """Identify exact ordinary file bytes."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(str(path))
    data = path.read_bytes()
    return dict(path=relative or path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))

def load_proposed():
    """Load staged code and redirect only its canonical plan/companions to this handoff."""
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location('prepared_inventory',
                                                PROPOSED/'manual_review_inventory.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    original = module.safe_path
    def redirected(root: Path, relative: str) -> Path:
        if root == ROOT and relative in {(PACKAGE/n).as_posix() for n in
            ['join-plan.json','inventory.json','inventory.schema.json','README.md']}:
            return original(PROPOSED, Path(relative).name)
        return original(root, relative)
    module.safe_path = redirected
    return module

def prepare() -> None:
    """Snapshot inputs, type-check exact joins, then render only proposed artifacts."""
    PROPOSED.mkdir(exist_ok=True)
    BASELINE.mkdir(exist_ok=True)
    for rel, expected in ACCEPTANCES.items():
        assert asset(ROOT/rel)['sha256'] == expected, rel
    files = {'manual_review_inventory.py': Path('geode/pipeline/manual_review_inventory.py'),
             'test_manual_review_inventory.py': Path('tests/test_manual_review_inventory.py'),
             **{name: PACKAGE/name for name in
                ['join-plan.json','inventory.json','inventory.schema.json','README.md']}}
    for name, rel in files.items():
        target = BASELINE/name
        if target.exists():
            assert target.read_bytes() == (ROOT/rel).read_bytes()
        else:
            shutil.copyfile(ROOT/rel, target)
    code = (BASELINE/'manual_review_inventory.py').read_text()
    code = code.replace('ALLOWED_REVIEW_SCHEMAS: dict[str, ReviewKind] = {',
        'ALLOWED_REVIEW_SCHEMAS: dict[str, ReviewKind] = {\n' + ''.join(
            f'    "{sha}": "{kind}",\n' for sha, kind in SCHEMAS.items()))
    (PROPOSED/'manual_review_inventory.py').write_text(code)
    module = load_proposed()
    plan = json.loads((BASELINE/'join-plan.json').read_bytes())
    assert len(plan['authorities']) == 63 and len(plan['reviews']) == 24
    plan['prepared_at'] = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    rawpath = plan['manual_manifest']['path']
    plan['manual_manifest'] = asset(ROOT/rawpath)
    assert plan['manual_manifest']['sha256'] == '7b8f882ec45286f69713a023345d8c5ef7f5859ecdb5f8d4036c8d8900eb8570'
    prep = 'research/local_review/pueblo-county-intake-2026-09-13/prepared-transaction/PREPARATION.json'
    plan['authorities'].append(dict(record_id='pueblo-county-planning-fees-sh-ext-002',
        authority_id='CO-COUNTY-PUEBLO', provenance={'artifact': asset(ROOT/prep), 'jsonl_row':None},
        sha_pointer='/template/source/sha256',source_id_pointer='/template/record_id',
        authority_pointer='/template/authority_id', verified_http=None,
        reported_acquisition_pointers=['/provenance/'+n for n in
          ['requested_url_reported','final_url_reported','http_status_reported',
           'reported_reserved_at','reported_finished_at']],
        role_pointers=['/template/official_source_name','/provenance/parent_representation'],
        qualification_pointers=['/template/custody_note','/provenance/limitations',
          '/provenance/independently_verified_http_time','/provenance/original_tool_command_retained',
          '/provenance/catalog_status_reported','/provenance/adoption_date',
          '/provenance/effective_date','/template/actual_repository_received_at']))
    entries = [
      ('pueblo-county-planning-fees-sh-ext-002',
       'pueblo-county-planning-fees-source-qa-2026-09-13/pueblo-county-fees-source-review-revision',
       '/collection_authority_id', ['/counts','/pages','/method'],
       ['/observations','/attribution_basis','/status','/adoption_date','/effective_date',
        '/legal_currentness','/answer_safe','/canonical_intakes'],
       'Two complete physical pages and 88 physical rows, including conditional markers and continuation rows. Root acceptance is later than the unchanged QA pending-review/zero-intake status. This received package does not prove witnessed HTTP, adoption or current applicability.'),
      ('larimer-equity-fee-memo-sd007-05',
       'eb023-equity-memo-source-qa-2026-09-13/independent-review', '/authority_id',
       ['/complete_physical_pages','/complete_source_blocks','/pages','/blocks',
        '/table_rows','/table_fragments','/review_method'],
       ['/status','/source_type','/adopted_effect','/provenance','/findings','/limitations',
        '/legal_currentness','/original_ocr_observations','/candidate_size_bytes',
        '/original_ocr_body_bytes'],
       'Four-page staff recommendation memo with four logical table rows/five fragments; OCR remains unchanged and the reviewed source text is separate. Proposed fee/implementation conditions remain attached. Historical pending-root status predates the accepted package; no enacted effect, calculations or current-law claim.'),
      ('el-paso-boh-bylaws-sd011',
       'eb024-bylaws-source-qa-2026-09-13/independent-review', '/authority_id',
       ['/full_pages_directly_viewed','/native_bytes','/native_lines','/nonblank_lines',
        '/pages','/method'],
       ['/limitations','/observations','/metadata_as_received','/printed_date',
        '/printed_date_role','/adoption_date','/effective_date','/original_acquisition_at',
        '/legal_currentness','/answer_safe'],
       'Complete five-page English source-fidelity review, 12640 native bytes, 170 nonblank lines and 54 paragraph portions. The 5/23/2012 footer is visible on all five pages; a root blank-footer false alarm was withdrawn. The printed date is unlabeled, not verified adoption/effectiveness. Spanish equivalence and current governance remain unreviewed.')]
    for sid, relative, authority, scope, limits, note in entries:
        prefix = 'research/local_review/'+relative
        plan['reviews'].append(dict(record_id=sid,
          review=asset(ROOT/(prefix+'/SOURCE_QA.json')),
          review_schema=asset(ROOT/(prefix+'/SOURCE_QA.schema.json')),
          source_sha_pointer='/source/sha256',source_id_pointer='/source_id',
          expected_review_source_id=sid,authority_pointer=authority,
          scope_pointers=scope,limitation_pointers=limits,note=note))
    plan['limitations'].append('This snapshot adds accepted Pueblo County fee, Larimer staff memo and El Paso English bylaws reviews. Review links describe source fidelity, not enactment, calculation, statewide completeness or current law. Earlier receipt/acquisition claims and null verified HTTP times remain unchanged. Pueblo County is distinct from the City of Pueblo; its reported reservation/result interval is not independently witnessed HTTP timing.')
    checked = module.JoinPlan.model_validate_json(json.dumps(plan))
    (PROPOSED/'join-plan.json').write_text(checked.model_dump_json(indent=2)+'\n')
    result = module.build_inventory(ROOT)
    assert (len(result.sources),result.rows_with_review,result.rows_without_review)==(64,27,37)
    old = module.Inventory.model_validate_json((BASELINE/'inventory.json').read_bytes())
    for current, previous in zip(result.sources[:63],old.sources,strict=True):
        if current.record_id in {'larimer-equity-fee-memo-sd007-05','el-paso-boh-bylaws-sd011'}:
            current = current.model_copy(update={'reviews':None,'review_status':'metadata_only_review_unknown'})
        assert current == previous, current.record_id
    for name, text in module._render_outputs(result).items():
        (PROPOSED/name).write_text(text,encoding='utf-8')
    module.check_inventory(ROOT,result)
    sys.stdout.write('Prepared 64 sources / 27 linked reviews / 37 unmapped; prior 63 metadata rows preserved except two review fields.\n')

if __name__ == '__main__':
    prepare()
