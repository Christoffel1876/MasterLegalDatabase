---
assignment_id: SH-EXT-003
status: PREPARED_NOT_DISPATCHED
public_actions_during_preparation: 0
---
# Prepared Sherlock assignment: Chaffee and Gunnison counties

Atlas must explicitly dispatch this assignment before any public activity. Read **INSTRUCTIONS.md** completely; PLAN.json binds the eight recorded starting URLs. The obsolete SH-EXT-001 timing does not apply here. Research stops September 13 at **03:05 UTC**, and the local report is due **03:20 UTC**. There is no SH-EXT-004 authorization.

First run the three read-only checks:

```bash
python -B verify_packet.py
python -B verify_comparison.py
python -B validate_templates.py
```

COMPARISON.json and the two exact selected legacy exports distinguish current files from pinned commit `2f2b450d8ecb3eff5258598d7be27189bc5e4cff`. SEED_HISTORY.json separates a historical direct request (`requested_url`) from the same URL appearing only as parent context (`source_url`). All eight starting URLs have recorded historical direct attempts; none should be called new to the repository.

Use **budget.py** to reserve and close each visible public action serially. It performs no HTTP itself and does not certify hidden browser traffic. The limits are 40 charged actions total, 20 per county, 30 distinct URLs, 20 MB per response and 80 MB total. Preserve failed/partial/unknown results; do not retry denied endpoints or reset the budget by starting another delivery directory. Use one delivery directory for this assignment. If the helper, clock or necessary evidence is unavailable, stop and report the limitation.

All results remain source-discovery evidence pending Atlas review. Nothing in this packet promotes legal currentness or completeness, edits canonical data, enrolls monitoring or authorizes contacts.
