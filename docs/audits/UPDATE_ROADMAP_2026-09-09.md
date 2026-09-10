# Process for current Colorado source coverage

Prepared September 9, 2026; approved by the owner for implementation. This roadmap
is based on the checkout, existing collectors, and a focused check of official
publishing sources. Approval of the process does not certify unreviewed legal
content. The [coverage and CCR guide](../COVERAGE_AND_CCR_PILOT.md) describes the
first implementation package and its bounded scope.

The working repository is
[Christoffel1876/MasterLegalDatabase](https://github.com/Christoffel1876/MasterLegalDatabase).
The Colorado Register daily pilot is active. Its first successful run proposed
124 additions in [data PR #2](https://github.com/Christoffel1876/MasterLegalDatabase/pull/2),
which remains open for review. Seven consecutive scheduled runs have not yet been
demonstrated.

## Intended result

Maintain a traceable, current collection of Colorado state, county, municipal,
and district authorities, with a visible coverage record for every jurisdiction
and source category. Preserve history while distinguishing operative text,
proposals, future-effective provisions, repealed versions, guidance, and unknown
status. Begin useful research on verified portions as coverage expands.

Current-source coverage and historical backfill have separate completion measures.
Federal and tribal authorities, judicial decisions, and complete obligation/cost
analysis require separately defined coverage; their presence in selected existing
records does not establish comprehensive coverage.

## What the repository actually supports today

| Area | Verified starting point | Planning consequence |
| --- | --- | --- |
| State | Existing indexes contain 34,717 statute sections and 1,035 CCR documents; the new Register collector has completed a live run. | Reconcile existing documents to official versions before describing them as current. |
| County | 64 county identities and a substantial source registry exist. The county index, legal-document metadata, and rule-unit files remain unresolved Git LFS pointers. | Recover or recollect source evidence before trusting historical coverage reports. |
| Municipal | The active layer contains 85 authority identities and no municipal legal-rule files. The larger registry names 272 municipalities and records an unresolved directory-count discrepancy. | Reconcile the complete jurisdiction list, then collect actual legal documents. Identity records are not rules. |
| District | Two authority identities and two source-preservation records exist. All 708 generated units are marked source-preservation-only. | Build a complete district inventory and distinguish landing-page text from substantive requirements. |
| Evidence | The inherited original archive is absent from the main checkout. New Register originals exist on the pending data branch and in local trial evidence. | Audit inherited and newly collected evidence separately. |
| Monitoring | Some existing collectors skip cached files, and local freshness reporting measures download age without checking live sources. | Adapt tested components to genuine change detection before scheduling them. |

These are checkout findings, not certified statewide totals. Historical download
attempts, retries, directory entries, source documents, extracted units, and
reviewed obligations must have separate counts.

## Phase 1: Recover the handoff and establish coverage

Inventory every layer's actual files, indexes, schema validity, raw evidence,
snapshots, and unresolved large-file references. Recover missing Git LFS objects
and available originals; where recovery fails, recollect from an identified
official source and record the new retrieval accurately. Preserve missing-evidence
status for unrecovered historical records.

Reconcile county and municipality identities against current official directories.
Use [DOLA's Local Government Information System](https://dola.colorado.gov/dlg_lgis_ui_pu/)
as a starting source, cross-checked against governments' own sources. DOLA describes
its directory as based on government filings and does not guarantee completeness.
Use an available approved export or documented manual intake where its interactive
access prevents automated collection. Reconcile consolidated city/counties,
cross-county municipalities, and active/inactive district identities without
double-counting them.

Build a jurisdiction-by-category coverage table. For local governments, include
charters and codes, adopted ordinances/resolutions awaiting codification, land use
and zoning, building/fire adoption and local amendments, permits/licenses, fees,
tax provisions, health/environmental rules, and public-facing utility or district
requirements. Record authoritative publishers, document lists, jurisdiction or
service-area boundaries, publication coverage, and access dependencies.

Each cell must distinguish verified coverage, pending review, missing evidence,
blocked access, and positively established inapplicability. Failure to find a
document does not establish that no requirement exists.

**Deliverable:** A coverage dashboard and prioritized gap list generated from
actual evidence, with recoverable source storage and a tested restore process.
Choose archive storage and budget from measured volume before statewide expansion;
keep a hash-indexed inventory so originals cannot disappear behind unresolved links.

## Phase 2: Bring the state baseline current

Start the next collection pilot with one CCR department, then expand to the full
official rule catalog. Preserve each rule's current text, version history,
effective dates, repeal status, and relationships to Register/eDocket changes.
The [Secretary of State's CCR site](https://www.sos.state.co.us/CCR/Welcome.do)
provides current rules and version history separately from the Register notices.
During this review it stated a published currency cutoff of August 13, 2026;
checking the page on September 9 does not advance that legal coverage date.

In parallel, identify the latest consolidated CRS edition and obtain the official
SGML package. The [official data page](https://content.leg.colorado.gov/agencies/office-legislative-legal-services/colorado-revised-statutes-data)
provides a dataset-request process and describes intended-use submissions for
redistribution. Reconcile the repository's existing not-submitted intake record
before publishing a new bulk edition. Prepare any needed request for the owner;
do not assume it has already been submitted.

Reconcile enactments after the consolidated edition using official
[session laws](https://www.leg.colorado.gov/laws/session-laws) and the
[Red Book](https://content.leg.colorado.gov/agencies/office-legislative-legal-services/red-book),
which lists amendments, additions, and repeals. Keep enactment, effective, and
incorporation dates distinct, including provisions whose effect is conditional.
Resolve provision-level uncertainty through review rather than treating an entire
bill's date as sufficient.

Then refresh bill versions/actions, executive orders and rescissions, AG opinions,
and COPRRR reports. Reuse discovery, parsing, and validation components, while
replacing skip-existing-file behavior and whole-layer freshness claims after
partial runs. LegiScan can supplement official legislative evidence if its account
configuration is available; its absence does not prevent the CCR work.

**Deliverable:** Each state layer has a reconciled official catalog, preserved
originals, supported status/version metadata, and a validated reviewable update.
Unresolved items stay visible and prevent an unqualified complete/current claim.

## Phase 3: Prove local collection while state work proceeds

Select two counties, two municipalities, and two districts with differing source
formats and publishing systems. Include a rural and an urban example and a fire
or water/sanitation authority. Select exact jurisdictions after the coverage map
shows which examples best exercise the collection methods.

Collect the whole agreed category checklist for each pilot jurisdiction. Monitor
both code compilations and subsequent adopted changes, plus separately published
fees, regulations, and permit documents. For example, Jefferson County separately
lists [land-use fees, policies, and ordinances](https://www.jeffco.us/303/Land-Use-Planning);
Denver lists [codes and department regulations](https://www.denvergov.org/My-Property/Remodeling-and-Construction/Permit-Office/Code).
A municipal code alone does not demonstrate completion of that checklist.

Retain section/page provenance, effective dates, amendments, exceptions, and exact
source labels. Distinguish enacted text from navigation, meeting materials,
proposals, and explanatory guidance. Record referenced model-code editions and
local amendments, with explicit gaps where incorporated material is unavailable.
Extend the inherited review/promotion path to municipal records, which it
currently omits. Send scanned-text and ambiguous-status failures to review.

**Deliverable:** A complete, reconciled source inventory for each pilot
jurisdiction; original evidence; validated changes in a review PR; a stable
no-change replay; and demonstrated handling of changed, missing, and failed sources.

## Phase 4: Expand in measured batches

Expand across the complete reconciled county and municipal lists, and the district
inventory by type and service area. Shared website/publisher adapters should
reduce duplicated work, but every government's source list still needs verification.
Prioritize broadly applicable current requirements and recent adopted changes;
track historical recovery separately.

Give every finished source a change checker and start monitoring it immediately.
Maintain an assigned manual route for unavailable automated sources, with a visible
overdue or blocked status if evidence is not received. A manual route alone does
not make a source current. Reconcile newly formed, renamed, dissolved, or merged
authorities periodically.

**Deliverable:** Increasing verified coverage against a known denominator. Every
in-scope gap remains visible until supported by collected evidence or a justified
scope decision; the overall system does not become complete merely because all
known downloads ran.

## Phase 5: Operate the update service

Every source uses the same progression:

**Discover → preserve originals → compare versions/content → validate → review → publish.**

Proposed operating cadence:

| Frequency | Activity |
| --- | --- |
| Daily | Bounded source-list/version checks; retrieve changed documents; rerun checks that failed transiently; retain a report even when nothing changed. |
| Weekly | Reconcile full document lists for onboarded sources; detect missing items, outdated adapters, and pending review backlogs. |
| Monthly | Reconcile the jurisdiction/source registry, review exceptions, audit representative source-to-record mappings, and verify archive recovery. |
| On material change or failure | Create a reviewable update or actionable issue for the assigned owner. Detect missing scheduled runs as well as explicit failures. |

These are proposed service targets, adjusted to publication behavior, access limits,
and measured cost. Lightweight daily checking does not mean redownloading every
historical document each day. Revisit the Register pilot's collection window and
hard limits before they constrain ongoing collection.

Show last attempted check, last successful source check, source publication/version
cutoff, legal effective date/status, and reviewed publication date separately.
Expose downloaded-but-unmerged updates as pending review. A reachable homepage or
a local reprocessing run cannot turn a missing source green.

Code and source-specific regression checks must exercise changed text, no-change
replays, new/deleted list entries, bad source responses, corrupt originals,
rollbacks, and pending PR preservation. Require a successful live update, a
verified unchanged replay, and seven consecutive actual scheduled successes for
each new collector's initial operational milestone.

## Completion and the next decision

Call a defined coverage scope current only when its expected source inventory is
reconciled, original evidence is accessible, current/status dates are supported,
indexes and records agree, substantive updates have been reviewed, and monitoring
meets its documented freshness target. Show any remaining source publication lag
or unresolved legal status explicitly.

The immediate next work package should be **baseline recovery, the coverage
dashboard, and the first CCR current-rule pilot**, with local source discovery
running alongside it. Estimate the broader rollout after the inventory and small
local pilot establish actual access barriers, data volume, and review workload.
Set an archive/runner budget and name the source-maintenance and substantive-review
owners before scaling.

Once a scope is verified, use it for a focused burden study: obligations, permits,
fees, deadlines, exceptions, regulated entities, and overlapping authorities with
exact citations. Remove and validate the inherited capped extraction behavior
before reporting complete requirement counts. Published fees and sourced duties
must remain distinguishable from estimated compliance cost or interpretive findings.
