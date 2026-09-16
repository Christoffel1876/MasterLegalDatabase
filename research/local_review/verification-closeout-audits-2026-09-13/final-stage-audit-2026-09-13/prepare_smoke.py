"""Prepare an additive nine-source smoke harness without executing an archive."""
from pathlib import Path
import hashlib, json, importlib.util, sys
from pydantic import BaseModel, ConfigDict
HERE=Path(__file__).resolve().parent
old=HERE.parents[1]/'clean-archive-smoke'/'smoke_check.py'
# extended-run/<audit> -> run-2026-09-12 is parents[1].
raw=old.read_bytes()
(HERE/'previous-smoke_check.py').write_bytes(raw)
s=raw.decode()
s=s.replace("    ('el-paso-boh-ehs-fees-sd011', 'rows', 65, 'CO-COUNTY-EL_PASO'),\n", "    ('el-paso-boh-ehs-fees-sd011', 'rows', 65, 'CO-COUNTY-EL_PASO'),\n    ('douglas-ehs-fees-atlas-directed', 'rows', 44, 'CO-COUNTY-DOUGLAS'),\n    ('pueblo-planning-fees-atlas-directed', 'rows', 44, 'CO-MUNICIPAL-PUEBLO'),\n")
s=s.replace("    parser.add_argument('--expected-sources', type=int, default=61)", "    parser.add_argument('--expected-sources', type=int, required=True)")
s=s.replace("    parser.add_argument('--expected-reviewed', type=int, default=22)", "    parser.add_argument('--expected-reviewed', type=int, required=True)")
anchor="\n\ndef scanned_check(data: dict) -> None:"
addition='''
    elif index == 7:
        rows = data['rows']
        ensure(len(data['context']) == 7, 'Douglas complete captions and notes lost')
        ensure(sum(r['table'] == 'county' for r in rows) == 27 and
               sum(r['table'] == 'state' for r in rows) == 17,
               'Douglas county/state caption associations changed')
        ensure(all(len(r['cells']) == 5 for r in rows), 'Douglas columns missing')
        blank = [r['cells'][-1] for r in rows if r['cells'][-1]['native_text'] is None]
        ensure(len(blank) == 2 and all(c['blank_region'] is not None for c in blank),
               'Douglas source blanks were lost or replaced by zero')
        ensure(data['source']['original_filename'] == 'original.pdf' and
               data['source']['date_verification'] == 'printed_claims_only_not_legal_effect',
               'Douglas receipt or date qualification changed')
    elif index == 8:
        rows = data['rows']
        ensure(len(data['context']) == 4 and
               {c['physical_page'] for c in data['context']} == {1,2,3,4},
               'Pueblo all-page context missing')
        nested = [n for r in rows for n in r['nested']]
        ensure(len(nested) == 43 and
               sum(n['kind'] == 'paired_subcategory' for n in nested) == 15 and
               sum(n['kind'] == 'fee_bullet' for n in nested) == 28,
               'Pueblo nested category/fee associations flattened')
        remodel = next(r for r in rows if r['row_id'] == 'P1-11')
        ensure('nor site improvements' in ''.join(c['displayed_text'] for c in remodel['cells']),
               'Pueblo conditional source wording changed')
        ensure(data['source']['original_filename'] == 'original.pdf' and
               data['source']['date_verification'] == 'printed_claims_only_not_legal_effect',
               'Pueblo receipt or date qualification changed')
'''
assert anchor in s
s=s.replace(anchor,'\n'+addition+anchor)
anchor2="\n    def refusal(data: dict) -> None:"
addition2='''
    batches = {
        'county-fees-v1': ['arapahoe-planning-fees-sd002-14',
                           'weld-ehs-fees-2026-atlas-directed'],
        'western-fees-v1': ['grand-junction-fire-fees-atlas-directed',
                            'mesa-building-fees-exhibit-a-atlas-directed'],
        'greeley-fees-v1': ['greeley-building-fees-sd008-06',
                            'greeley-development-impact-fee-memo-sd008-07'],
    }
    def batch_watch(data: dict, batch: str) -> None:
        ensure(data['batch_id'] == batch and data['configured_sources'] == 2 and
               data['configured_source_ids'] == batches[batch], 'Watch pair changed')
        ensure(data['manual_pdf_records'] == args.expected_sources and
               data['locally_hash_verified_pdf_originals'] == args.expected_sources and
               data['unavailable_or_mismatch'] == [], 'Batch original availability differs')
        ensure(data['prior_watch_execution'] == 'not_asserted' and
               data['recurring_deployment'] == 'not_deployed_by_this_feature' and
               data['fixed_urls_find_new_editions_elsewhere'] is False and
               data['legal_currentness'] == 'not_verified', 'Batch claim promoted')
    for batch in batches:
        invoke('watch-' + batch, 'module', 'geode.pipeline.manual_source_watch_batches',
               ['--root', str(root), '--batch', batch],
               lambda d, batch=batch: batch_watch(d, batch))
'''
assert anchor2 in s
s=s.replace(anchor2,'\n'+addition2+anchor2)
# Keep the original EHS current-law refusal query separate from new source ordering.
s=s.replace("'--source-id',NATIVE[-1][0],'--query','OWTS'", "'--source-id',NATIVE[6][0],'--query','OWTS'")
new=HERE/'smoke_check.py'
new.write_text(s)
compile(s,str(new),'exec')
spec=importlib.util.spec_from_file_location('prepared_smoke',new)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
(HERE/'RUN_RECEIPT.schema.json').write_text(json.dumps(m.RunReceipt.model_json_schema(),indent=2)+'\n')
class Prep(BaseModel):
    model_config=ConfigDict(extra='forbid')
    status: str
    previous_harness_sha256: str
    prepared_harness_sha256: str
    native_sources: list[tuple[str,str,int,str]]
    expected_check_count: int
    archive_executions: int
    public_requests: int
    changes: list[str]
record=Prep(status='PREPARED_NOT_EXECUTED',previous_harness_sha256=hashlib.sha256(raw).hexdigest(),
 prepared_harness_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),native_sources=m.NATIVE,
 expected_check_count=19,archive_executions=0,public_requests=0,changes=[
 'Retain seven existing native source cases and add Douglas44 and CityPueblo44 complete-row cases.',
 'Add three installed fixed-batch readiness checks; no --execute, source HTTP or scheduling.',
 'Require explicit inventory counts at execution to prevent a stale default after pending intake.',
 'Preserve isolated child environment without HOME override and exact original network/workspace-denial profile.',
 'Keep source-only/current-law refusal, scanned Erosion, CRS102 continuation and absolute evidence-path checks.',
 'Compile/import/schema preparation only; no archive CLI executed.'])
text=record.model_dump_json(indent=2)+'\n';Prep.model_validate_json(text)
(HERE/'SMOKE_PREPARATION.json').write_text(text)
(HERE/'SMOKE_PREPARATION.schema.json').write_text(json.dumps(Prep.model_json_schema(),indent=2)+'\n')
print(record.model_dump_json(indent=2))
