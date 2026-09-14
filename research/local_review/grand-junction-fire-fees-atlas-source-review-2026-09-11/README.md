---
title: Grand Junction fire-prevention fee source review
legal_currentness: not_verified
---

# Scope

Both complete source pages were directly viewed using newly rendered Poppler images. The review preserves all 3,673 native bytes and binds 57 fee rows to their labels. Five headings are restored as separate associations; no native source wording is changed.

Use [SOURCE_QA.json](SOURCE_QA.json) with [original.pdf](original.pdf). The copied access receipt describes event E008 in the separately preserved discovery; its original event-relative paths are historical references, not files promised here.

# Qualifications

- All 57 visible fee rows were directly checked against full 144-dpi Poppler renders. Native text has 3,673 bytes and 127 lines; words, amounts, whitespace and ligatures remain unchanged.
- The five native group headings occur after all fee rows and in reverse visual order. The reviewed map attaches 2 new-building, 4 tenant-finish, 2 fire-alarm, 2 sprinkler and 24 miscellaneous rows to their visible headings.
- The 23 page-two rows visibly continue the table under the page title Fire Prevention Service Fees Continued. Miscellaneous Permits is not reprinted; the cross-page group association is an explicit layout annotation, not inserted source text.
- Both page titles and contact lines occur after fee rows in native extraction but are visible at the top. Printed footer text remains separate. Each page has a fire-department emblem; native text does not transcribe its raster lettering. Exact emblem microlettering and font glyph code points are not certified.
- New-building tiers begin at 1-5,000 square feet; tenant-finish tiers begin at 1-200 and continue 201-500, 501-5,000 and >5,000. No unstated zero-area tier or calculation rule is added.
- The fire-alarm modification row visibly says flate fee= < 5 devices, while sprinkler modification says (=< 20 heads). Preserve these source spellings/operators without replacing them with a normalized inequality or merging their scopes.
- Includes inspections applies to the 1-200 tenant-finish row. Other listed per-inspection charges, the per-trip/paid-prior condition, per-tank versus flat charges and per-device wording remain inside their respective fee cells.
- Double regular fee belongs to work performed without obtaining a permit. The 1.5 X original plan review fee belongs to plans requiring more than two (2) reviews. Neither multiplier is applied to other rows.
- Annual Mobile Food Preparation Vehicles, hourly Alternative Materials/Designs/Methods Review, and Burn Permit per-year labels remain distinct. Repeated storage and spray labels on the source are not deduplicated.
- Explosives of blasting agents, PVP Systems and flate are preserved as printed/native source wording. Mixed native ligatures and plain letter sequences are not rewritten as corrections.
- No visible edition, adoption or effective date was observed. September 2025 PDF creation/modification metadata do not establish legal dates. The alternate linked fee endpoint and adopting instruments have not been reconciled.
- The city referral and printed Grand Junction contact details identify this source; its applicability to a separately named rural fire district or other authority is not established by this document review.

# Verification

Run `PYTHONDONTWRITEBYTECODE=1 python build_review.py --verify` with Python 3.11+, Pydantic 2, jsonschema and PyMuPDF 1.28.2. This checks every inventoried file, exhaustive native bytes, all label/fee assignments and fresh PDF geometry. It verifies image-file identity, not a repeat of human visual judgment. Keep the manifest hash outside this package. No legal currentness is certified.
