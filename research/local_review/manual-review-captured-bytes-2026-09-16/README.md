# Parse the exact bytes whose identity was checked

A file changed between hash verification and parsing could previously supply altered review scope under the earlier approved hash. A same-size change followed by restoration could also escape an end-of-build recheck. Plato reproduced the inherited issue in an isolated fixture; this does not establish that maintained data was ever corrupted.

The reader now captures and verifies the exact bytes used for review JSON, its schema, provenance JSON/JSONL, the join plan and the manual manifest. JSONL parsing preserves strict object/blank-line rules and universal newlines. Raw PDF and unchanged legacy-ledger checks remain streamed. This binds the consumed metadata to its recorded identity; it does not provide a global filesystem lock or authenticate historical events.

Nine regression cases cover read-time changes with restoration, a schema substitution that would relax a forbidden literal, and JSONL boundaries. The preceding source integration is preserved at commit `9873868f7ddec52f4f938639cb7570212eac2eb2`. Its receipt accurately checks that earlier implementation; after this code repair, its exact installed-code hash check is historical and is expected to differ. To replay it, use that commit. The review/source/authority inventory data itself remains unchanged at 70 sources, 38 scoped reviews and 32 unmapped sources.

Before-images of the two changed maintained files are retained under `preimages/`. No accepted source, review package, source custody, date role or currentness classification was rewritten by this repair.

| Maintained file | Before SHA-256 | Fixed SHA-256 |
|---|---|---|
| manual_review_inventory.py | `5d0a4f1e113c0b6f044898ef349fb68823cb94fce97257283263eaada77e2504` | `ebea75c2c1413dd5de8befd03ecc83e27c5da4df6337379f5f6ae504ff1ee3c4` |
| test_manual_review_inventory.py | `26a5a97be972f149d7c5e168223dc620d315f7df3290d0e150d83006704bf1f1` | `bf25fa353edf02184ba4bbe9e1d98d7eed99d90982ab55b40d081a9626547cd3` |

Run `python -B -m pytest tests/test_manual_review_inventory.py -q` and `python -B -m geode.pipeline.manual_review_inventory --root . --check`. The broader suite result is recorded separately after completion.
