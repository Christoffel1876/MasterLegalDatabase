---
assignment_id: SH-EXT-003
status: PREPARED_NOT_DISPATCHED
prepared_date: 2026-09-13
research_cutoff_utc: 2026-09-13T03:05:00Z
report_cutoff_utc: 2026-09-13T03:20:00Z
legal_currentness: not_verified
---
# Chaffee and Gunnison county source discovery

This is a prepared assignment for Sherlock. It is not active until Atlas confirms dispatch in the existing conversation. Preserve this packet and all earlier packets unchanged. This assignment replaces expired SH-EXT-001 timing only for these two counties; it does not authorize SH-EXT-004, another jurisdiction, a follow-on batch, scheduling, or contacts.

Identify useful county legal catalogs and exact short fee schedules or adopting instruments. The two authorities are **CO-COUNTY-CHAFFEE** and **CO-COUNTY-GUNNISON**. County ownership must be evidenced separately from municipalities, special districts, regional agencies and publisher hosts. Do not label City of Gunnison, Salida, Buena Vista or a fire district as county authority merely because a county page links it. Preserve an out-of-scope link as an unopened lead if useful.

Read PLAN.json, METHODS.md and COMPARISON.json before public work. Verify the closed packet first with `python -B verify_packet.py`, then run `python -B verify_comparison.py` and `python -B validate_templates.py`. If required files or the local accounting helper cannot be used, stop and report the limitation; do not improvise an unlogged search.

## Exact initial URLs

These are recorded registry leads, not freshly verified endpoints. Preserve their exact spelling, case and bare/www host. The source IDs and original JSON pointers are in PLAN.json.

| County | Initial URL | First purpose |
| --- | --- | --- |
| Chaffee | https://www.chaffeecounty.org/ | County identity and official referrals |
| Chaffee | https://www.chaffeecounty.org/departments/building_department/adopted_codes_design_criteria.php | Building adoptions, amendments and short fees |
| Chaffee | https://search.chaffeecounty.org/Planning-and-Zoning-Land-Use-Code | Land-use catalog and planning fees |
| Chaffee | https://www.chaffeecounty.org/government/county_commissioners.php | Adopted resolutions and ordinances |
| Gunnison | https://www.gunnisoncounty.org/ | County identity and official referrals |
| Gunnison | https://gunnisoncounty.org/139/Building-Office | Building Office fee/adoption links |
| Gunnison | https://gunnisoncounty.org/410/Building-Codes | Building adoptions and local amendments |
| Gunnison | https://www.gunnisoncounty.org/378/Land-Use-Resolution | Land-use catalog, planning fees and instruments |

Prioritize short, expressly linked fee PDFs and the instrument that adopts them, followed by legal catalogs. A page, agenda, unsigned attachment, adopted instrument as labeled, form and guidance are different source roles. Do not infer adoption, legal effect, currency or supersession from a filename, title, search snippet or HTML listing. Preserve every source date with its stated role and exact location; acquisition and report times are separate.

Additional opened URLs must be exact links observed on the authorized county pages, a recorded official referral, or an explicitly logged relevant search result. No guessed file paths, guessed document IDs, bulk endpoints, automated crawling, recursive site mirroring or batched public tool calls. Each search call may contain only one query and costs one action. Each discovered but unopened URL goes in BACKLOG.json, with its observed parent and reason it remains unopened.

## Hard finite limits

Stop research by **03:05 UTC on September 13**, even if work remains. Finish the local report by **03:20 UTC**. Never begin an action whose timeout could knowingly extend past the research cutoff. The broader session cutoff does not extend this assignment.

- At most **40 visible public actions total**, **20 charged to each county**, and **30 distinct requested or observed redirect URLs**.
- At most **20,000,000 bytes per response body** and **80,000,000 bytes total across response bodies**. A repeated download counts its bytes again; local copies do not become new acquisitions.
- One pending reserved action at a time. Open, search, download, browser navigation, click, failed call, preflight failure, deliberate retry and visible redirect follow-up all count.
- No denial retries are authorized. Stop a 401/403/429, login, challenge or otherwise denied endpoint. Do not change identity, TLS policy, route, hostname spelling, tool or browser to evade it. A different, independently observed official source can remain eligible within the same budgets; the blocked endpoint stays blocked.
- No credentials, login, cookies copied to public reports, contacts, circumvention or hidden transport. Ordinary verified HTTPS only. A TLS failure is a failure, not permission to disable verification.

Prefer a tool that does not follow redirects automatically. A deliberately followed redirect gets a new reserved action before its request. If a tool automatically follows visible redirects, list each additional followed destination once in that result's `visible_redirect_urls`; those hops are additionally charged to action, county and URL budgets. Do not double-charge a hop that received its own separate reservation. A redirect simply observed but not followed is an unopened lead, not a fetched destination. If the tool cannot expose hidden internal requests, say so; these counters do **not** certify a wire-request total. Stop if newly revealed hops exceed a cap; retain the overrun evidence rather than editing the counters to fit.

Before each download use the available remaining body budget and a supported transfer cap. The local helper does not intercept public tools or enforce transfer limits. If the chosen tool cannot bound or measure a response, stop that acquisition rather than claiming compliance. Unknown or partial body accounting stops further public activity. Preserve partial/error bytes with their true role. A late or oversized response is an overrun to report, not a successful within-budget acquisition.

## Reserve, act, record

Create one new delivery directory under `deliveries/<actual-dispatch-UTC>/`. Never write into an earlier delivery. Read the schemas and templates; all action IDs begin `SHEXT003-A` and form one serial sequence. Priority IDs are `SHEXT003-01` through `SHEXT003-16`, with no more than eight single-resource priorities per county.

For each action, create a reservation-input JSON matching Reservation in models.py. Include the exact target or one query, authority, tool, purpose and observed referral. Its `reserved_at` input is replaced by the helper's actual UTC clock. Then run:

```bash
python -B budget.py reserve --delivery deliveries/<run> --input <reservation-input.json>
```

Only a successful local reservation permits the **one** corresponding public action. The helper performs zero public requests. It locks local accounting against concurrent reservations, persists a validated record atomically, and refuses a second pending action. Never run parallel public calls, including through subagents.

After the action, preserve its body and public-only response metadata under a unique action-specific path. Save a Result JSON with the actual observations, then run:

```bash
python -B budget.py complete --delivery deliveries/<run> --input <result-input.json>
python -B budget.py status --delivery deliveries/<run>
```

A process interruption leaves the reservation pending. Reconcile what actually happened and save an honest result; **do not replay the request**. If timing, HTTP status or original-body identity is unavailable, leave it null with the reason. For a known no-body preflight failure, use `body_size_basis: no_body_observed` and `observed_body_bytes: 0`. For unknown transport consumption, use `unknown` and null, then stop. Use `retained_complete` or `retained_partial` only for measured, hash-bound retained body bytes. A duplicate path cannot replace an earlier record. Even a cap-violating result is preserved before the helper refuses continuation; retain any error output and report the breach.

The helper validates recorded state. A hash or successful invocation does not independently prove that the worker reserved before the public tool call. Preserve the original tool log so Atlas can assess the sequence.

## Compare and deliver

COMPARISON.json binds the separate current and pinned registry/manual snapshots and exact historical selected lines. For every priority, report exact-URL history, source-ID history, recorded digest comparisons and actual available bytes as separate questions. Do not call a URL newly discovered merely because it was absent from a sample. A matching historical digest is a metadata match until the historical bytes are also available and checked. Old Windows raw paths do not establish local preservation.

Retain original PDF bytes only when actually obtained. Record measured SHA256, length, PDF magic and parseable page count. Browser-print output, WebFetch text, captions and HTML shells are derivatives or other roles, never exact publisher PDFs. PDF parsing is structural validation, not a complete legal or visual review. Keep forms, staff proposals, signed documents as observed and complete meeting packets separate. Do not substitute a linked draft for a missing final instrument.

Produce ACTION_LOG.json, CHECKLIST.json, PRIORITIES.json, BACKLOG.json and ARTIFACT_INVENTORY.json using the supplied schemas. ACTION_LOG must aggregate the unchanged immutable reservation/result records. The checklist has 24 county/category combinations, including honest `not_searched` or `access_blocked` entries. It is not a completeness certificate. Retain the full body/hash inventory and report actual versus claimed timing, unknown statuses, missing bytes, budget overruns and unresolved ownership. Do not omit failed attempts. Keep raw response cookies/authentication values out of distributable copies; bind any redacted derivative to the original retained privately.

Run `python -B validate_templates.py --delivery deliveries/<run>` and preserve its actual output. If validation fails, preserve the original data and explain the failure; do not delete evidence to make the report pass. Return a concise report, exact artifact paths, hashes, counts and qualified gaps to Atlas in the existing conversation. **Stop after SH-EXT-003.** All delivered sources remain pending Atlas intake and legal review.
