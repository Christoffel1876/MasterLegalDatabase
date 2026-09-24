# September 17 session freshness check

Four deliberate web-tool opens checked three official subjects. Two catalog leads are
proposed for later validation; the Register issue is already represented locally.
No source original was downloaded and no canonical data, queue or automation changed.

| Subject | Observed official evidence | Local comparison and disposition |
| --- | --- | --- |
| Colorado Register | [Official issue list](https://www.sos.state.co.us/CCR/RegisterHome.do) and September 10 contents list 49 CR 17. | The pinned refresh state already identifies this issue and all 39 listed notice IDs appear in the 8,120-row rulemaking index. Duplicate issue identity only; today's parsed webpage was not compared byte-for-byte with the archived HTML. |
| El Paso County | [County catalog](https://clerkandrecorder.elpasoco.com/clerk-to-the-board/ordinances/) lists 26-54, Control and Prevention of Graffiti, under resolutions. | No same-authority matching subject label in the scanned manual/legacy metadata. Thirteen county originals already have custody entries, including Ordinance 26-01; this is a separate lead. Obtain the exact linked resolution and its date/role evidence only if separately authorized. |
| City of Arvada | [City legal notices](https://www.arvadaco.gov/245/Meetings-and-Other-Legal-Notices) lists CB26-029 Data Centers. | Arvada has an authority index entry and twelve inherited collection rows, but no manual original in the pinned inventory. The CB label is a notice lead; no adoption or operative text was inspected. City authority is separate from Jefferson and Adams Counties. |

The saved freshness report is dated August 11 and explicitly says no network refresh
was performed. Its age-zero/fresh labels cannot establish September 17 currency.
The Register contents display future effective-date claims, including September 30,
October 1 and December 31, 2026; those dates do not make the listed texts current now.

The comparison baseline is tracked commit
`06504e53ca64734b05eb2362bd48d04b1f223078`. Complete metadata streams scanned were
48,390 legacy download rows, 70 manual original rows, 71 intake-ledger rows,
85 municipal index records and 8,120 rulemaking index records. The pinned manual
inventory has 37 scoped review links and 33 unmapped originals. These are custody
and index counts, not legal or geographic completeness measures. The county index
and local review queue are Git LFS pointers; their underlying records were not
read. No source absence was inferred from those pointers or from a metadata nonmatch.

`REPORT.json` carries the exact input pins, row-count scope and matches.
Broad textual matches from other authorities (including Larimer's data-center
moratorium) are retained in the comparison and are not treated as Arvada duplicates.
No candidate body was obtained, so candidate digest equality is unknown.

`evidence/web-*.json` preserves tool-returned parsed text, including its reported
today/yesterday crawl labels. The retained intervals are tool batch wall-clock times,
not HTTP start/end. Original response status, headers and body hashes are unknown.
Thus this is an official-page check through a web tool, not an independently retained
fresh HTTP original. Linked document bodies, legal dates, full histories, other
jurisdictions and unmerged or prior external handoffs remain outside this check.

`CANDIDATE_QUEUE.json` is a nonactivated handoff proposal. Both candidates remain
`needs_validation`, change type `unknown`, legal currentness `not_verified`, and
`answer_safe=false`. It neither revives old queues nor schedules new work.

The repository's named report-schema file is a required-field/enumeration policy
descriptor. This packet also supplies strict Pydantic models and generated actual
JSON Schemas, and checks the policy descriptor explicitly.

Offline verification from any directory:

```sh
/Users/mcoors/Documents/Project\ Geode/.geode-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/hour-2026-09-17-2037/ptolemy-freshness/verify.py'
```

Add `--repo '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'` to replay
all pinned tracked-input hashes. This performs no network access or repository writes.
The builder is historical preparation code and refuses to replace its existing outputs.
