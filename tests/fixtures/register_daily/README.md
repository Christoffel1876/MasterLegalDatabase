# Colorado Register source fixtures

These are factual source excerpts fetched on 2026-09-09 with standard HTTPS GETs:

- `official_2026_08_25_excerpt.html`: the source-declared JavaScript URL templates,
  table headers, and first row of each of the four rulemaking table types from
  [the August 25, 2026 issue](https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/25/2026&Volume=49&yearPublishNumber=16&Month=8&Year=2026).
  Surrounding document markup is minimal test scaffolding.
- `official_hearing_2026_00370_excerpt.html`: the unmodified first identity table
  from [hearing tracking number 2026-00370](https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00370).
- `official_passive_cf_script.html`: the exact passive Cloudflare JavaScript
  wrapper appended to the complete [2026 Register index](https://www.sos.state.co.us/CCR/RegisterHome.do?pyear=2026).
  Repeated GETs returned complete official content with rotating ray/timestamp
  values in this wrapper. The fingerprint helper recognizes only this exact
  wrapper with those two value fields variable. It does not execute the script.

Tests label synthesized pages and deliberately modified source variants as such.
