---
status: PREPARED_NOT_APPLIED
source_id: chaffee-planning-application-fees-atlas-directed
authority_id: CO-COUNTY-CHAFFEE
legal_currentness: not_verified
answer_safe: false
---
# One Chaffee planning application fee original, prepared intake

The proposed intake preserves one exact two-page PDF (206,144 bytes; SHA256 `8c6b6176f8617a43c4f4eb422f5c9c7287ffba8f2daee4af803c6831d2682205`) as `manual_official_download`, county layer `08_County_Authorities`. The current 69-record raw manifest and 70-record intake ledger are exact preimages; application would append one newly validated record to each, producing 70/71. The separate legacy coverage ledger is pinned and unchanged. No application has occurred in this preparation.

`PREPARATION.json` and its strict schema are the authoritative prospective plan. `REQUEST.json` is a typed API-field preview, not an instruction to run generic intake. Its source file is the selected retained copy named `original.pdf`; this actual local basename is preserved as `original_filename`. Publisher filename, source content dates, adoption, fees and currentness are not inferred. All actual repository receipt/archive/intake identifiers remain unset until explicit application.

The observed county parent anchor is `Application Fee Schedule`. Its acquisition remains supplied historical evidence. A previously observed county HTTP 302 supplies the exact Revize Location, corroborated against the public header, result and redirect-body anchor. The new GET replaced only literal spaces with `%20` and returned HTTP200 without automatic redirects, ordinary verified TLS, complete framing and no retry. Its actual interval is 2026-09-13T16:44:32.759460Z through 16:44:33.133961Z. That time is acquisition, never the future canonical receipt time. The complete public retrieval packet is copied unchanged under `inputs/retrieval`; public header subsets deliberately omit original fields, and omitted values cannot be replayed offline.

`COMPARISON.json` records the full 48,390-row current legacy stream and exact current manifest, ledger, source-registry and coverage-ledger comparisons. No exact selected ID/URL/digest match was found. The 573 present ordinary raw files included zero equal-size candidates. This does not prove equality or absence of missing LFS bodies, external handoff copies, or differently spelled URLs. The recorded comparison commit is historical context; evidence-only descendants are allowed if exact affected-file and runtime pins still match.

`transaction.py` is a new adapted copy of the frozen reviewed two-source implementation, retained under `reference-only`. It captures and checks exact preparation, provenance and source buffers, verifies current originals/policy, and derives the new report from only the captured ledger plus this one record. It never invokes mutating generic reconciliation. Every original is written once; raw and ledger receive exact suffix bytes with no reserialization of historical lines. Only recognized monotone states (original, raw, ledger, report) can resume with the original intent/time. Foreign rows, altered prefixes, unrelated duplicate source bytes, tampered inputs, unsafe paths and backdated receipts fail closed.

After reviewer acceptance, run only the new commands below. Do not run historical builders, reference transaction scripts, or the retained network collector. The portable verifier never imports the transaction and checks the fixed public packet from captured temporary copies. Its success is preparation evidence, not an application receipt.

```sh
python -B validate_preparation.py
python -B transaction.py --dry-run --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
# Atlas alone, after explicit review:
python -B transaction.py --apply --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
python -B transaction.py --verify --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

A dry-run creates no execution directory or canonical writes. After application begins, preserve `execution/INTENT.json`, exact preimages, originals and recognized partial states; replay the same transaction to complete. Do not delete an original or restore historical metadata independently. An unrecognized state requires review, not automatic rollback. Tests exercise process interruption and replay; they do not prove power-loss/filesystem durability because directory entries are not fsynced. The transaction assumes serialized authorized writers and is not a general cross-process database lock.

Source QA remains a separate acceptance path. This packet makes no table/amount transcription, source-fidelity, legal-currentness, coverage or answer-safety promotion. Prior preparation revisions and the initial test observation remain explicitly historical; `VALIDATION.json` binds final code and actual captured final test/dry-run output.
