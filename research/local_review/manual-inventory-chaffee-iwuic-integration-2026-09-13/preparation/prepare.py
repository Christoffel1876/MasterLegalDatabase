"""Prepare exact inventory companions using read-only canonical evidence and a staged plan."""
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2] / 'MasterLegalDatabase'
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('proposed_inventory',
                                            BASE / 'proposed/manual_review_inventory.py')
inv = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = inv
spec.loader.exec_module(inv)
INTAKE = 'research/local_review/chaffee-county-intake-2026-09-13/prepared-transaction'


def write(name: str, model: inv.Strict) -> None:
    """Write a new typed proposal only after exported-schema validation."""
    payload = model.model_dump_json(indent=2) + '\n'
    jsonschema.validate(json.loads(payload), model.model_json_schema())
    with (BASE / 'proposed' / name).open('x') as stream:
        stream.write(payload)


def ref(name: str) -> dict:
    """Identify current canonical bytes without changing them."""
    return inv.identity(ROOT, name).model_dump()


def review_join(folder: str, scope: list[str], limits: list[str], note: str) -> inv.ReviewJoin:
    """Bind a literal accepted review and schema without rewriting historical fields."""
    parent = 'research/local_review/' + folder
    acceptance = json.loads((ROOT / parent / 'ACCEPTANCE.json').read_bytes())
    schema = json.loads((ROOT / parent / 'ACCEPTANCE.schema.json').read_bytes())
    jsonschema.validate(acceptance, schema)
    review = acceptance['source_review']
    review_schema = acceptance['source_review_schema']
    a = ref(parent + '/' + review['path'])
    b = ref(parent + '/' + review_schema['path'])
    assert (a['sha256'], a['size_bytes']) == (review['sha256'], review['size_bytes'])
    assert (b['sha256'], b['size_bytes']) == (review_schema['sha256'], review_schema['size_bytes'])
    assert acceptance['legal_currentness'] == 'not_verified' and not acceptance['answer_safe']
    receipt_sha = ref(parent + '/ACCEPTANCE.json')['sha256']
    return inv.ReviewJoin(
        record_id=acceptance['source_id'], review=inv.Artifact(**a),
        review_schema=inv.Artifact(**b), source_sha_pointer='/source/sha256',
        source_id_pointer='/source_id', expected_review_source_id=acceptance['source_id'],
        authority_pointer='/authority_id', scope_pointers=scope, limitation_pointers=limits,
        note=note + ' Separate Atlas acceptance: ' + parent + '/ACCEPTANCE.json SHA256 '
        + receipt_sha + '. Historical QA status and custody fields remain unchanged.')


def prepare() -> None:
    """Build the fixed 69/33 proposal and prove exact preservation before any installation."""
    old_plan = inv.JoinPlan.model_validate_json((BASE / 'preimages/join-plan.json').read_bytes())
    old = inv.Inventory.model_validate_json((BASE / 'preimages/inventory.json').read_bytes())
    assert (len(old.sources), old.rows_with_review, old.rows_without_review) == (67, 30, 37)
    receipt = json.loads((ROOT / INTAKE / 'execution/RECEIPT.json').read_bytes())
    assert receipt['actual_repository_received_at'] == '2026-09-13T16:44:04.840983Z'
    assert receipt['raw_records'] == 69 and receipt['ledger_records'] == 70
    assert receipt['status'] == 'completed_archived_pending_pipeline'
    preparation = json.loads((ROOT / INTAKE / 'PREPARATION.json').read_bytes())
    assert inv.identity(ROOT, INTAKE + '/PREPARATION.json').sha256 == (
        'a8f768ff4c00bf55ba2db4712d67183f8c739e8e59777fa9bfed77f1bd12ef4b')
    data = old_plan.model_dump(mode='json')
    data['prepared_at'] = datetime.now(timezone.utc).isoformat()
    data['manual_manifest'] = ref(old_plan.manual_manifest.path)
    assert data['manual_manifest']['sha256'] == receipt['raw_sha256'] == (
        'fa08f4ea1c021fc6247fa314f0c4a6df4f622ad3fdd29d92cd9f59e0005839b4')
    authority_doc = {'artifact': ref(INTAKE + '/PREPARATION.json'), 'jsonl_row': None}
    for n, source in enumerate(preparation['provenance']):
        pointer = f'/provenance/{n}/'
        result = INTAKE + '/' + source['result']['path']
        join = inv.AuthorityJoin(
            record_id=source['source_id'], authority_id='CO-COUNTY-CHAFFEE',
            provenance=inv.Document.model_validate(authority_doc),
            sha_pointer=pointer + 'source/sha256', source_id_pointer=pointer + 'source_id',
            authority_pointer=pointer + 'authority_id',
            reported_acquisition_pointers=[pointer + k for k in [
                'requested_url', 'final_url', 'http_started_at', 'http_completed_at']],
            role_pointers=[pointer + k for k in [
                'document_role', 'visible_label', 'physical_pages']],
            qualification_pointers=[pointer + k for k in [
                'limitations', 'actual_repository_received_at',
                'source_content_reviewed_in_this_intake',
                'original_tool_command_retained', 'legal_currentness']],
            verified_http=inv.HttpBinding(
                document=inv.Document(artifact=inv.Artifact(**ref(result))),
                sha_pointer='/body/sha256', status_pointer='/http_status',
                time_pointer='/completed_at'))
        data['authorities'].append(join.model_dump(mode='json'))
    additions = [
        review_join('gunnison-iwuic-source-qa-2026-09-13',
                    ['/scope', '/pages', '/checked_passages', '/amendment_instructions',
                     '/dates', '/findings'],
                    ['/method', '/normalization', '/source_role', '/status', '/provenance',
                     '/limitations', '/ocr_discrepancies', '/legal_currentness', '/answer_safe'],
                    'Four-page image-only source review: 43 passages and 14 exhibit instructions. '
                    'Original OCR and reviewed offsets remain separate. Proposed exhibit wording, '
                    'source citation/grammar anomalies, recorder and handwritten fields remain '
                    'qualified; no present code applicability or currentness certification.'),
        review_join('chaffee-electric-source-qa-2026-09-13',
                    ['/full_pages', '/pages', '/blocks', '/marks', '/tables', '/links', '/dates'],
                    ['/method', '/status', '/observations', '/limitations', '/native_bytes',
                     '/ocr_bytes', '/effective_date', '/repository_intake_at_review',
                     '/observed_get_completed_at', '/external_reviews_consulted',
                     '/legal_currentness', '/answer_safe'],
                    'Seven-page image-only source review, selected r1: 98 blocks, 85 markup spans, '
                    'seven logical tables/eight fragments/twelve data rows and six cross-page '
                    'links. '
                    'The final seal block and obscured printed-name character were corrected '
                    'in a separate revision. Strikes, additions, duplicate numbering and distinct '
                    'commercial/residential exceptions remain source evidence, '
                    'not consolidated law.'),
        review_join('chaffee-cwrc-source-qa-2026-09-13',
                    ['/scope', '/pages', '/segments', '/date_claims'],
                    ['/method', '/native_method', '/ocr_method', '/transcription_conventions',
                     '/source_role', '/acquisition', '/observations', '/external_reports_consulted',
                     '/verified_adoption_date', '/verified_effective_date', '/limitations',
                     '/legal_currentness', '/answer_safe'],
                    'Fourteen-page image-only marked-source review: 174 segments and 432 retained '
                    'OCR observations. Struck fencing text, added provisions, exceptions and role '
                    'statements remain distinct. Source wording/citation anomalies and the '
                    'under/exceeding 75000 gap remain unresolved. No consolidated operative code, '
                    'adoption/effective-date or signature-authenticity certification.'),
    ]
    data['reviews'] += [r.model_dump(mode='json') for r in additions]
    data['limitations'] += [
        'The three later Gunnison IWUIC/Chaffee review links preserve their original recorded '
        'source-fidelity scope and qualifications. Source QA pre-intake/pending-review fields '
        'remain historical; separate root acceptance and actual intake do not rewrite them.',
        'Chaffee direct HTTP completion times are separately bound to exact successful response '
        'receipts. Later repository receipt time does not establish adoption or current law.']
    plan = inv.JoinPlan.model_validate_json(json.dumps(data))
    assert plan.authorities[:67] == old_plan.authorities
    assert plan.reviews[:30] == old_plan.reviews
    write('join-plan.json', plan)
    original_safe_path = inv.safe_path
    def staged(root: Path, relative: str) -> Path:
        """Redirect only the proposed plan; all evidence remains read-only canonical input."""
        if root == ROOT and relative == inv.PLAN.as_posix():
            return BASE / 'proposed/join-plan.json'
        return original_safe_path(root, relative)
    inv.safe_path = staged
    current = inv.build_inventory(ROOT)
    assert (len(current.sources), current.rows_with_review, current.rows_without_review) == (
        69, 33, 36)
    for before, after in zip(old.sources, current.sources[:67], strict=True):
        if before.record_id == 'gunnison-iwuic-resolution-2022-33-sh-ext-003':
            assert before.reviews is None
            after = after.model_copy(update={'reviews': None,
                                            'review_status': 'metadata_only_review_unknown'})
        assert after == before
    assert current.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    for name, text in inv._render_outputs(current).items():
        with (BASE / 'proposed' / name).open('x') as stream:
            stream.write(text)
    sys.stdout.write('Prepared 69 sources / 33 linked reviews / 36 unmapped; '
                     'old joins preserved.\n')


if __name__ == '__main__':
    prepare()
