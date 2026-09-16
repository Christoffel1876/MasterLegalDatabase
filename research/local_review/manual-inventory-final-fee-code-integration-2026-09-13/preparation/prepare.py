"""Prepare the last two review joins against actual intake, without canonical writes."""
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
INTAKE = 'research/local_review/chaffee-planning-fees-intake-2026-09-13/prepared-transaction'


def write(name: str, model: inv.Strict) -> None:
    """Validate model/exported schema before writing a new proposal."""
    payload = model.model_dump_json(indent=2) + '\n'
    jsonschema.validate(json.loads(payload), model.model_json_schema())
    with (BASE / 'proposed' / name).open('x') as stream:
        stream.write(payload)


def ref(name: str) -> dict:
    """Bind current canonical evidence without altering it."""
    return inv.identity(ROOT, name).model_dump()


def review_join(folder: str, scope: list[str], limits: list[str], note: str) -> inv.ReviewJoin:
    """Require exact root acceptance, source review and schema before mapping metadata."""
    parent = 'research/local_review/' + folder
    acceptance = json.loads((ROOT / parent / 'ACCEPTANCE.json').read_bytes())
    schema = json.loads((ROOT / parent / 'ACCEPTANCE.schema.json').read_bytes())
    jsonschema.validate(acceptance, schema)
    review, review_schema = acceptance['source_review'], acceptance['source_review_schema']
    a, b = ref(parent + '/' + review['path']), ref(parent + '/' + review_schema['path'])
    assert (a['sha256'], a['size_bytes']) == (review['sha256'], review['size_bytes'])
    assert (b['sha256'], b['size_bytes']) == (review_schema['sha256'], review_schema['size_bytes'])
    assert acceptance['legal_currentness'] == 'not_verified' and not acceptance['answer_safe']
    return inv.ReviewJoin(
        record_id=acceptance['source_id'], review=inv.Artifact(**a),
        review_schema=inv.Artifact(**b), source_sha_pointer='/source/sha256',
        source_id_pointer='/source_id', expected_review_source_id=acceptance['source_id'],
        authority_pointer='/authority_id', scope_pointers=scope, limitation_pointers=limits,
        note=note + ' Separate Atlas acceptance: ' + parent + '/ACCEPTANCE.json SHA256 '
        + ref(parent + '/ACCEPTANCE.json')['sha256'] + '. Original QA statuses remain historical.')


def prepare() -> None:
    """Build 70/35/35 only after both accepted QA packages exist; preserve all old joins."""
    old_plan = inv.JoinPlan.model_validate_json((BASE / 'preimages/join-plan.json').read_bytes())
    old = inv.Inventory.model_validate_json((BASE / 'preimages/inventory.json').read_bytes())
    assert (len(old.sources), old.rows_with_review, old.rows_without_review) == (69, 33, 36)
    receipt = json.loads((ROOT / INTAKE / 'execution/RECEIPT.json').read_bytes())
    assert receipt['actual_repository_received_at'] == '2026-09-13T17:02:09.370066Z'
    assert receipt['raw_records'] == 70 and receipt['ledger_records'] == 71
    assert receipt['status'] == 'completed_archived_pending_pipeline'
    preparation = json.loads((ROOT / INTAKE / 'PREPARATION.json').read_bytes())
    assert ref(INTAKE + '/PREPARATION.json')['sha256'] == (
        'a25b2071c9275af9b7299edf198b96870a79ba5ac8e0c412f6b8647774d683ca')
    data = old_plan.model_dump(mode='json')
    data['prepared_at'] = datetime.now(timezone.utc).isoformat()
    data['manual_manifest'] = ref(old_plan.manual_manifest.path)
    assert data['manual_manifest']['sha256'] == receipt['raw_sha256'] == (
        'd32afb35ca30d113e786ba98768dace04c8e4d433322355a14ab35d7a3810537')
    source = preparation['provenance'][0]
    assert source['source_id'] == 'chaffee-planning-application-fees-atlas-directed'
    pointer = '/provenance/0/'
    result = INTAKE + '/' + source['result']['path']
    join = inv.AuthorityJoin(
        record_id=source['source_id'], authority_id='CO-COUNTY-CHAFFEE',
        provenance=inv.Document(artifact=inv.Artifact(**ref(INTAKE + '/PREPARATION.json'))),
        sha_pointer=pointer + 'source/sha256', source_id_pointer=pointer + 'source_id',
        authority_pointer=pointer + 'authority_id',
        reported_acquisition_pointers=[pointer + k for k in [
            'requested_url', 'final_url', 'http_started_at', 'http_completed_at']],
        role_pointers=[pointer + k for k in ['document_role', 'visible_label', 'physical_pages']],
        qualification_pointers=[pointer + k for k in [
            'limitations', 'actual_repository_received_at', 'source_content_reviewed_in_this_intake',
            'original_tool_command_retained', 'legal_currentness']],
        verified_http=inv.HttpBinding(
            document=inv.Document(artifact=inv.Artifact(**ref(result))),
            sha_pointer='/body/sha256', status_pointer='/http_status', time_pointer='/completed_at'))
    data['authorities'].append(join.model_dump(mode='json'))
    additions = [
        review_join('gunnison-building-code-source-qa-2026-09-13',
                    ['/page_count', '/pages', '/associations', '/markings'],
                    ['/native_total_bytes', '/source_currentness', '/review_method',
                     '/external_reports_consulted', '/legal_adoption_verified',
                     '/signature_identity_verified', '/custody', '/limitations', '/answer_safe'],
                    'Sixteen-page image-only resolution/amendment review: 132 blocks, 27 design '
                    'entries and 521 original OCR lines. Three strikes, handwritten fills, the '
                    'design and exception continuations, and the restored appeals paragraph remain '
                    'explicit source evidence. Fee conditions and source anomalies are preserved; '
                    'incorporated external code texts and their current applicability are not supplied.'),
        review_join('chaffee-planning-fees-source-qa-2026-09-13',
                    ['/source_pages', '/native_pages', '/native_lines', '/groups', '/rows',
                     '/passages', '/graphics', '/inspected_full_pages', '/source_date_claims'],
                    ['/status', '/method', '/reviewed_at', '/verified_effective_date',
                     '/limitations', '/custody', '/legal_currentness', '/answer_safe'],
                    'Two-page native/source-image review: 49 physical fee rows in ten categories, '
                    'including the first four second-page subdivision-exemption rows without a '
                    'repeated heading. Refund, rental-license, hourly and schedule-wide escrow '
                    'notes remain linked. Printed January 2025/December 2024 dates remain claims; '
                    'the planned-development expression and exact exploration-threshold gap are '
                    'not repaired, computed or converted to current-law advice. '
                    'The acceptance qualifies the original QA custody wording: one fresh fee GET, '
                    'with separate earlier actual A003 county HTTP 302 referral evidence and supplied '
                    'historical catalog evidence; A001/A002 fetched other ordinance PDFs.'),
    ]
    data['reviews'] += [r.model_dump(mode='json') for r in additions]
    data['limitations'] += [
        'The final Gunnison code/Chaffee fee review links preserve original source wording, '
        'conditions, image/OCR/native distinctions and pending-review chronology. Root acceptance '
        'does not replace those historical fields or authenticate signatures/current applicability.',
        'The last Chaffee fee original has an actual 2026-09-13T17:02:09.370066Z repository receipt, '
        'separate from the observed 16:44:33.133961Z HTTP completion. Neither is a legal effective date.']
    plan = inv.JoinPlan.model_validate_json(json.dumps(data))
    assert plan.authorities[:69] == old_plan.authorities and plan.reviews[:33] == old_plan.reviews
    write('join-plan.json', plan)
    original = inv.safe_path
    def staged(root: Path, relative: str) -> Path:
        """Redirect only the proposal plan; every input evidence read stays canonical and read-only."""
        if root == ROOT and relative == inv.PLAN.as_posix():
            return BASE / 'proposed/join-plan.json'
        return original(root, relative)
    inv.safe_path = staged
    current = inv.build_inventory(ROOT)
    assert (len(current.sources), current.rows_with_review, current.rows_without_review) == (
        70, 35, 35)
    for before, after in zip(old.sources, current.sources[:69], strict=True):
        if before.record_id == 'gunnison-building-code-resolution-2023-22-sh-ext-003':
            assert before.reviews is None and len(after.reviews) == 1
            after = after.model_copy(update={'reviews': None,
                                            'review_status': 'metadata_only_review_unknown'})
        assert after == before
    assert current.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    for name, text in inv._render_outputs(current).items():
        with (BASE / 'proposed' / name).open('x') as stream:
            stream.write(text)
    sys.stdout.write('Prepared 70 sources / 35 linked reviews / 35 unmapped.\n')


if __name__ == '__main__':
    prepare()
