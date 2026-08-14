# Required New-Session Freshness Review

Project Geode is a maintained database snapshot, not a guarantee of current law. The local freshness report describes the files Geode contains; it does not prove that official sources have been checked recently.

Every new AI session must launch a brief freshness-search subagent, or perform the equivalent official-source web search, before substantive work:

1. Read MASTER_MANIFEST.json, SOURCE_FRESHNESS_REPORT.json, and FRESHNESS_VERIFICATION_QUEUE.json.
2. Read FRESHNESS_PRIORITIES.json.
3. Search official Colorado sources for recent changes in high-priority areas and stale or incomplete layers.
4. Record sources checked, search dates, results, and candidates using SESSION_FRESHNESS_REPORT.schema.json.
5. Compare candidates with existing indexes and update ledgers to identify duplicates.
6. Put credible candidates into the approved ingestion or freshness queue.
7. Briefly report the review result before answering the user's question.

## Current-answer rule

If the user asks for the most recent, current, latest, or up-to-date answer, an internet search is required. Search official Colorado government sources and compare the results with Geode. Clearly label what came from Geode and what was found during the current search. If internet access is unavailable, state that the answer is limited to the database snapshot.

"Fresh" in a local report means recently checked against local files. It does not mean current law. "Not found" means only that no verified record was found in the reviewed scope; it does not prove that a law, regulation, or update does not exist.

## Publication safeguards

A web discovery is a candidate update, not a database record. Before a candidate can be added, the pipeline must verify the official URL, preserve the original in _RAW_ARCHIVE/, validate the extracted record, check duplicates, capture citations and dates, and run integrity checks.

The AI must not commit or push legal data automatically merely because a new source was discovered. A normal session may prepare and queue an update; publication requires the approved authorization path.