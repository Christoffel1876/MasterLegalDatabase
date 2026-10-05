# SH-CHAIN-2026-09-17-01 Report

assignment_id: SH-CHAIN-2026-09-17-01  
delivery: `/Users/mcoors/Documents/Project Geode/handoffs/hour-2026-09-17-2037/sherlock-delivery/SH-CHAIN-2026-09-17-01-20260917T204333Z`  
start_utc: 2026-09-17T20:43:33Z (from ACTIVATION.json stamp)  
report_utc: 2026-09-17T20:48:27Z  
host: Mac machineId 23155929-a935-400b-ad25-bcf86e364bd7 (direct curl; not box-mediated)  
legal_currentness: not_verified  
review_status: pending_atlas_verification  
answer_safe: false  

## Caps / stop

| metric | used | cap |
|---|---:|---:|
| deliberate public actions | 20 | 30 |
| distinct targets | 20 | 20 |
| retained response bytes | 15776357 | 30000000 |

stop_reason: **distinct_target_cap** (20/20). Public stop was 21:10Z; collection ended ~20:47Z. No further distinct URLs opened. Partial delivery is intentional and honest.

Transport evidence: each `events/A###.json` includes full `curl_argv`, `curl_exit_code`, headers path, body path, SHA-256, timestamps. No `-L` auto-follow.

## Chain findings (keep proposal / catalog / retained bytes distinct)

### 1) Resolution 22-401

- **Catalog claim (A019 AgendaSuite resolutions list HTML):** number `22-401`, description is Board of Adjustment **Bylaws** amendments (compliance with BoCC Res 22-73; BOA approved amendments 2022-10-26). Observed getfile: `https://www.agendasuite.org/iip/elpaso/file/getfile/33301` (claim 674 kB). **PDF not opened** (target cap).
- **25-290 retained text (local prior review + A003):** repeals Resolution No. 22-401 recorded at Reception No. 222141805. Reception search not opened this run.
- County site search for `Resolution 22-401` (A009): **Nothing Found**.

### 2) Amended Legislative / Parliamentary procedures (per 25-290)

- **25-290** states BoCC intends to concurrently adopt Amended Legislative and Parliamentary Rules and Procedures for sitting as BOA.
- **Catalog claim (A019):** Resolution **25-291** — “Resolution to amend the Legislative and Parliamentary Rules and Procedures…” with getfile `https://www.agendasuite.org/iip/elpaso/file/getfile/50986` (claim 1 MB). Numbering is adjacent to 25-290; **concurrency is a catalog/adjacency inference, not proved by opened PDF text.** PDF not opened (target cap).
- Later related catalog claims (also unopened): 26-8 (`getfile/52035`), 25-147, 25-2, etc.
- County site search for Amended Legislative and Parliamentary (A011): **Nothing Found**.
- Observed planning `Procedures/0401_001.pdf` retained as **A008** (4-page scanned image PDF). Content **not verified** as the parliamentary rules instrument.

### 3) Resulting Chapter Two LDC amendment

- **Not found** as an adopting instrument in this bounded run (see REMAINING_GAPS.json).
- A004 “amendments not yet codified” showed Chapter 6.3.3/6.3.4 / Res 26-202 material, not Chapter Two / BOA conformity.
- A019 HTML scan: no `Chapter Two` / `Chapter 2` hits.
- Municode LDC (A014): JS shell only; chapter body not retrieved.
- Pinned older 7-page Chapter Two digest `f3d527fd6a9da5b0043672582dda812dc9c3dfe9958d8b53eec876957ed10953` located locally at prior Plato inputs path; **not** redownloaded; comparison to any new instrument **not performed**.

### 4) Resolution 25-290 (context anchor)

- Retained **A003** from observed homepage link `…/Misc/25-290.pdf`.
- SHA-256 `754e98fb7908b66e54a192cefca9817f7bb4cf2a428cf7c469d59f7cfdcdf427` **matches** pinned comparison digest `754e98fb7908b66e54a192cefca9817f7bb4cf2a428cf7c469d59f7cfdcdf427`.
- AgendaSuite also lists 25-290 getfile/50985 (unopened; duplicate candidate).

## Off-chain / budget notes

Early wave retained large LDC wildfire / Ch.6 PDFs (A002, A005–A007) from high-scoring homepage links. They consumed distinct-target budget before AgendaSuite getfiles could be opened. Those PDFs are retained exactly but are **not** primary chain instruments.

## Deliverables in this folder

- `REPORT.md` (this file)
- `ATTEMPTED_URLS.json`
- `EXACT_DOCUMENT_CANDIDATES.json`
- `REMAINING_GAPS.json`
- `logs/priority_catalog_claims.json` / `logs/agendasuite_chain_catalog.json`
- `INVENTORY.json` + `SHA256SUMS.txt` (inventory excludes itself and SHA256SUMS)
- `events/`, `bodies/`, `candidates/`, `ACTIVATION.json`, `collector.py`

## Standing down

No next job. No old queues resumed. Hard stop / stand-down per activation after this delivery.
