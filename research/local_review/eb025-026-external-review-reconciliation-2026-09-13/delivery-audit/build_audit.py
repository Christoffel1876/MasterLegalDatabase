"""Build the additive audit from captured files only; never open original reports."""
import json
from datetime import datetime, timezone
from pathlib import Path
import jsonschema
from models import Audit, DocumentAudit
from verify_audit import document_bindings, sha

HERE = Path(__file__).absolute().parent


def main():
    documents = []
    for directory in sorted((HERE / 'received').iterdir()):
        complete = json.loads((directory / 'COMPLETION_RECEIPT.json').read_bytes())
        freeze = json.loads((directory / 'PASS1_FREEZE_RECEIPT.json').read_bytes())
        bindings, findings = document_bindings(HERE, directory.name)
        assert all(b.matches for b in bindings)
        is25 = complete['assignment_id'] == 'EB-PDF-025'
        common = [
            'No chat export or contemporaneous chat-hash receipt is delivered. The required '
            'chat freeze gate and actual pre-candidate order are not independently established.',
            'The exact saved pass-1 Task prompt exists and its receipt hash matches. A retained '
            'Task-generated narrative describes full-page and crop reads, but no raw per-request '
            'image tool inputs/responses, request identifiers or response timestamps are supplied.',
            'Both Task narratives refer to tool_outputs/crops/ and overlapping bands. Those crop '
            'images, dimensions, crop hashes, invocation logs and individual raw caption responses '
            'are absent from the captured delivery. Referenced page numbering mistakes are reported '
            'by the assistant; they were not independently witnessed here.',
            'No pass-2 Task prompt is retained. The file named PASS2_REOPEN_TASK.md is a generated '
            'narrative, not an exact prompt or raw request/response transcript.',
            'The completion receipt does not bind the pass-1 executor narrative or pass-2 reopen '
            'narrative by hash. This audit newly binds their delivered bytes, not their availability '
            'at the earlier reported completion time.',
            'No packet validator command/output or full-manifest/canonical-record verification log '
            'is delivered. This auditor verifies retained identities now; that cannot certify the '
            'worker performed those checks before completion.',
            'The receipts omit requested report sizes and several exact paths; observed sizes/paths '
            'are now recorded in custody. A final assistant model/supplier identity and known time/cost '
            'or explicit unknown fields are incomplete.',
            'Both principal frozen pass-1 reports expressly compress dense paragraphs. A declared '
            'six-page assisted procedure is not a complete literal transcription or pixel review.',
        ]
        if is25:
            specific = [
                'The reopen narrative is labeled utc_pass2 15:40:58Z, eight seconds later than '
                'the parent PASS2/COMPLETION time 15:40:50Z. It may be later supporting material; '
                'the files do not establish its use by the reported completion time.',
                'No separate per-page reopen output files are retained for EB025. Both passes '
                'claim six source representations processed, but the delivered evidence is '
                'aggregate narrative rather than an independently timed per-page execution trace.',
                'The freeze receipt names a Task agent ID, but the assistance model and supplier '
                'behind caption generation remain unverified.',
            ]
            start = '2026-09-13T15:37:28Z'
            reopen = '2026-09-13T15:40:58Z'
        else:
            specific = [
                'PASS1_TASK_executor.md limitation 8 states that English EB024 was used only as '
                'optional structural cross-check awareness. It also names the English date '
                '5/23/2012. This conflicts with the packet prohibition on pre-freeze English '
                'consultation and qualifies no-exposure/source-first claims. The artifact cannot '
                'establish when or how that awareness arose.',
                'The retained EB026 pass-1 Task prompt only says Spanish fidelity and no candidate; '
                'it does not repeat the full START_HERE prohibition on English/prior-review '
                'consultation. This narrower saved prompt does not document the worker receiving '
                'every global restriction, even though the main process had those instructions.',
                'The reopen narrative is labeled utc_pass2 15:48:15Z, three minutes 49 seconds '
                'after the parent PASS2/COMPLETION time 15:44:26Z. It cannot by itself support a '
                'claim that its full recheck preceded that completion.',
                'The reopen narrative explicitly says original.pdf was not present in that '
                'worker workdir and its PDF hash came from receipts. The correct original is now '
                'present in delivery; current byte identity does not retrospectively prove the '
                'assistant opened/copied/hashed it during its reported recheck.',
                'Six page-named reopen Markdown files are short summary blurbs without raw '
                'request payloads, execution timestamps or individual source/page hash receipts. '
                'Their filenames and existence are not proof of individual image opens.',
                'The freeze receipt lacks utc_start; the main frozen report and attempt directory '
                'supply a claimed start instead. START_UTC.txt is absent for EB026.',
                'Two findings are classified critical in the principal report, whereas the '
                'retained reopen narrative labels the same citation grouping unresolved and its '
                'continuous-number associations inference only. This records an internal evidence '
                'qualification, not a source-content verdict.',
            ]
            start = '2026-09-13T15:41:18Z'
            reopen = '2026-09-13T15:48:15Z'
        documents.append(DocumentAudit(
            assignment=complete['assignment_id'], source_id=complete['source_id'],
            report_directory=directory.name, expected_pages=6, pdf_pages_observed=6,
            bindings=bindings, claimed_status=complete['status'],
            declared_method=complete['review_method'],
            declared_critical_count=complete['findings']['critical'], claimed_findings=findings,
            chronology_claims={'start_from_frozen_report': start,
                               'freeze': freeze['utc_freeze'],
                               'candidate_release': complete['utc_candidate_release'],
                               'parent_completion': complete['utc_pass2_complete'],
                               'supporting_reopen_narrative': reopen},
            method_evidence=[
                'PASS1_frozen.md and PASS1_NOTES.md: self-described caption-mediated source-first '
                'procedure and unresolved/condensed regions.',
                'prompts/PASS1_TASK_PROMPT.txt: exact saved assistance prompt, matched to freeze '
                'receipt SHA; source-only/no-candidate language as retained.',
                'tool_outputs/PASS1_TASK_executor.md: full assistant-authored narrative read by '
                'this auditor; its descriptions of image/crop operations are claims.',
                'PASS2_REVIEW.md and pass2_reopen/PASS2_REOPEN_TASK.md: full retained reports read '
                'by this auditor; source meaning and translations not adjudicated.',
                'COMPLETION_RECEIPT.json and PASS1_FREEZE_RECEIPT.json: current hash bindings '
                'match copied assets. Timestamps/status remain worker-recorded claims.',
            ], unresolved_or_missing_evidence=common + specific, source_meaning_assessed=False))
    audit = Audit(
        audited_at=datetime.now(timezone.utc),
        status='post_report_custody_checked_substantive_reconciliation_pending',
        custody_sha256=sha((HERE / 'CUSTODY.json').read_bytes()), documents=documents,
        shared_limits=[
            'This is a new post-report audit. The earlier EB025 source QA remains unchanged with '
            'external_reports_consulted=false; reading these later reports does not rewrite that chronology.',
            'The Mac was locked and no Grok UI execution was witnessed by this auditor. On-disk '
            'reports claim both documents complete_pending_atlas_verification; UI delivery/stop '
            'and exact activation are not independently established by this package.',
            'START_HERE/MANIFEST preserve historical PREPARED_NOT_DISPATCHED status. That immutable '
            'preparation status is not evidence that a later activation did or did not occur.',
            'Hash equality establishes now-retained artifact identity, not human/model independence, '
            'candidate sealing, historical source opens, fresh page reading or absence of prior exposure.',
            'All 16 main-report finding IDs and reported classifications are enumerated without '
            'accepting their materiality, source wording or proposed corrections. Atlas owns the '
            'substantive source reconciliation.',
            'No visual inspection, OCR, translation comparison, source discovery, status promotion '
            'or original report change occurred. Filesystem mtimes are custody observations only.',
            'The complete two delivered folders and selected packet metadata are preserved. The '
            'original full packet manifest is retained as evidence; unselected packet payloads '
            'are not claimed copied or fully replayed here.',
        ], original_source_qa_changed=False, new_visual_review_pages=0,
        public_requests=0, canonical_changes=0)
    raw = audit.model_dump_json(indent=2).encode() + b'\n'
    Audit.model_validate_json(raw)
    jsonschema.validate(json.loads(raw), Audit.model_json_schema())
    with (HERE / 'AUDIT.json').open('xb') as out:
        out.write(raw)
    (HERE / 'AUDIT.schema.json').write_text(json.dumps(Audit.model_json_schema(), indent=2) + '\n')
    print(sha(raw))


if __name__ == '__main__':
    main()
