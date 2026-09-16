---
title: "Independent Douglas official-domain rationale"
status: exact_host_addition_supported_pending_reviewed_diff
legal_currentness: not_verified
---
# Recorded official domain transition

The current local registry explicitly binds `county_douglas_homepage` to
`CO-COUNTY-DOUGLAS` and `https://www.douglas.co.us/`. The preserved discovery
evidence supports a narrow addition of **`www.douglasco.gov`** to the intake
allowlist. It does not justify a wildcard, the unobserved bare hostname, or arbitrary
subdomains.

The following evidence lives under
`research/local_review/douglas-castle-rock-discovery-2026-09-12/frozen/`:

1. `events/E002/event.json` records the old registered homepage's HTTP 301.
   Its unchanged public header explicitly supplies
   `Location: https://www.douglasco.gov/`. Event SHA-256:
   `d3bdd262cec044fa50275d1841beadd12c4d803e743f7250b99be7c55c0be7bc`.
2. `events/E003/event.json` records HTTP 200 for that exact new homepage. Its
   retained HTML (SHA-256
   `bd18322f5c54d8cfe0b47a2b67ee7c01424c7252179dd09303016885671de22e`)
   contains **two** exact `Environmental Health` anchors to
   `https://www.douglasco.gov/health-department/environmental-health/`.
   Two repeated anchors are not two sources.
3. `events/E006/body.bin` (SHA-256
   `c5bac8b613ea08744bb33f79a6c11cdeec4c73f2c7ca6b28611969a6237d214f`)
   contains one exact `Environmental Health Fees` anchor to
   `https://www.douglasco.gov/health-department/fees/`.
4. `events/E012/body.bin` (SHA-256
   `f57bfda6319e5dc8f98b866f354095f18466062a55598ab19651c56efbfe455e`)
   contains one exact `Current Fee Schedule` anchor to
   `https://www.douglasco.gov/documents/fee-schedule.pdf/`.
5. `events/E017/event.json` records direct HTTP 200 at the exact PDF URL,
   with SHA-256 `35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687`,
   149,173 bytes and no redirect. Its body matches the accepted one-page source QA.

This independent check parsed each retained HTML anchor and checked the recorded
public Location header without making a request. The county's name and Health
Department wordmark are also visible in the source. The `Current Fee Schedule`
label is publisher navigation text, not an independent current-law finding.

`policy-preimage.py` preserves the unchanged policy before root's proposed edit:
SHA-256 `83dca55129755c9adb0829cae4cec1511d5b3624b452b5a6e826674a7e3b551a`.
No policy edit or intake was performed by this review. Root owns the exact-host
change, preflight and actual transaction. Private header values are not copied into
this review; their preserved omission remains qualified in the accepted public
custody package.
