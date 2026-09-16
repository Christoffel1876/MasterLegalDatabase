# PASS 1 — Independent Visual Transcription (FROZEN)

## 1. Metadata

| Field | Value |
| :--- | :--- |
| assignment_id | EB-PDF-013 |
| source_id | fort-collins-wildfire-code-sd005-05 |
| expected_pages | 8 |
| utc_start | 2026-09-11T19:03:46Z |
| utc_freeze | 2026-09-11T19:14:20Z |
| packet (batch-4) manifest SHA-256 | ee87ef2806e3cf9b955dbceca927087918ed0906894879a8597d7436ad67db0b (assignment-supplied; local packet/manifest file not present in `/workspace/geode-013/`; not independently hashed this pass) |
| original.pdf SHA-256 | 00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2 (assignment-supplied; independently confirmed by hashing `/workspace/geode-discovery-005/raw/009_www.fortcollins.gov_2025-colorado-wildfire-resiliency-code-final-for-brc.pdf` only — PDF text **not** extracted; PDF not used as transcription source) |
| page-0001.png SHA-256 | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 |
| page-0002.png SHA-256 | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b |
| page-0003.png SHA-256 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 |
| page-0004.png SHA-256 | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 |
| page-0005.png SHA-256 | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 |
| page-0006.png SHA-256 | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 |
| page-0007.png SHA-256 | 08c0444d4ea6ff1def3209a63be2383dfe12cecd52c5c408312eab393b3cf8d3 |
| page-0008.png SHA-256 | 7d6ae0f60370b4adf01e818d8dc2368a5791b66aad2f0535e542554feb76c0af |
| candidate SHA (withheld) | 9fc7fe62d1d678407db0d228a6e5ddc2397765a1d2f6d5ab4430a7cac3922ea7 (assignment-supplied; file **not opened**, not hashed from disk this pass; no candidate.txt present in workdir at pass-1 start) |
| queue auth | handoffs/EBENEZER_QUEUE_013_014_2026-09-11.md SHA 26de06e50f00a940202cecd8e4f2b603927d5e8befb986282f46f9cbb02064a0 (assignment-supplied; file not present under `/workspace/geode-013/` this pass) |
| reviewer | Ebenezer (Grok Bot) |
| model | unknown |
| prior_candidate_exposure | none |
| prior_atlas_sherlock_consultation | none for this document |
| legal_currentness | not_verified |
| pass | PASS1_frozen (blind visual transcription only) |
| status | pass1_frozen_pending_pass2 |

## 2. Access / hash verification

| Asset | Expected SHA-256 | Observed SHA-256 (this pass) | Match |
| :--- | :--- | :--- | :--- |
| page-0001.png | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 | YES |
| page-0002.png | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | YES |
| page-0003.png | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | YES |
| page-0004.png | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 | YES |
| page-0005.png | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | YES |
| page-0006.png | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | YES |
| page-0007.png | 08c0444d4ea6ff1def3209a63be2383dfe12cecd52c5c408312eab393b3cf8d3 | 08c0444d4ea6ff1def3209a63be2383dfe12cecd52c5c408312eab393b3cf8d3 | YES |
| page-0008.png | 7d6ae0f60370b4adf01e818d8dc2368a5791b66aad2f0535e542554feb76c0af | 7d6ae0f60370b4adf01e818d8dc2368a5791b66aad2f0535e542554feb76c0af | YES |
| original.pdf (discovery raw, hash-only) | 00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2 | 00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2 | YES |
| packet manifest (batch-4) | ee87ef2806e3cf9b955dbceca927087918ed0906894879a8597d7436ad67db0b | not present in workdir | not independently hashed |

**Access scope (this pass):** Inspected only `/workspace/geode-013/page-0001.png` … `page-0008.png` (and Pillow crops derived from those PNGs). Read `PASS_1_PROMPT.md`. Hashed the matching source PDF path above without extracting text. Did **not** open, read, or hash from disk any `candidate.txt`, `02-candidate-text`, `03-custody`, `04-verification`, ocr-evidence, native extraction, Sherlock, Atlas, EB-PDF-014 materials, or repository/candidate text of this ordinance. Workdir at start contained only `PASS_1_PROMPT.md` and the eight page PNGs.

**Image geometry:** All eight pages 2550×3300 px, RGB (letter 8.5×11 in at 300 dpi appearance).

## 3. Image-viewing method / caption-mediation disclosure

- Page images were inspected with the **Read** tool. Read returns **caption-mediated vision captions** (model-generated descriptions of the pixels). **Captions are NOT source quotations** and are **not** OCR output.
- The user-message attachments of the same eight pages were also caption-mediated; those captions were **not** treated as source text.
- Captions can truncate, invent, or inject prior-conversation / metadata context. Examples this pass (alien caption content **rejected** after crop re-reads):
  - One crop caption invented spelling **“Coloradaoan”**; tight re-read shows *Coloradoan*.
  - One crop caption invented **“2021 International Code”**; tight re-read shows **“2024 International Codes”**.
  - Competing captions disagreed on whether “building official” and “Tree crowns” were italicized in specific lines; marked **[UNCERTAIN]** below where unresolved.
- Dense amendment/exemption lists, green date redactions, yellow highlights, and struck-through deleted sections were **cropped with Pillow** and re-read via Read (horizontal bands + targeted zooms).
- Limitation: **not** certified full visual coverage equivalent to unaided pixel inspection. Typographic quotes, exact Unicode code points, justification spacing, em-dash vs en-dash, and highlight edge boundaries are **described**, not claimed as exact code points from raster.
- Printed names (e.g., Approving Attorney Madelene Shehan) are transcribed from printed type. Signature lines are blank; **no handwritten signatures** observed. Signer identity is not inferred from adjacent printed office titles.
- Graphical strikethrough and yellow highlighting are **visual observations** of draft markup; they do **not** establish enacted legal effect.
- `legal_currentness: not_verified`. Draft status, dates, and `source_id` are not evidence that the ordinance or CWRC adoption is presently in force.

## 4. Markup conventions used in this transcript

| Markup | Meaning (visual observation only) |
| :--- | :--- |
| `~~text~~` | Horizontal strikethrough through the words (deletion markup visible) |
| `==text==` | Yellow highlighter background (addition / replacement markup visible) |
| `[GREEN DATE REDACTION]` | Solid bright-green rectangular block obscuring month/day before `, 2025` |
| `[UNDERLINE: Exhibit A]` | Underlined phrase |
| Yellow rectangular border | Thin yellow frame around new Article IX / amendment block (pages 2–7 continuing onto page 8 start) |
| `[UNCERTAIN: …]` | Competing or incomplete readings before inference |

## 5. Full page-by-page verbatim transcript

### Page 1 (`page-0001.png`) — printed folio `- 1 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**Centered title block (all caps):**

```text
ORDINANCE NO. XXX, 2025
OF THE COUNCIL OF THE CITY OF FORT COLLINS
AMENDING CHAPTER 5 OF THE CODE OF THE CITY OF FORT COLLINS FOR THE
PURPOSE OF ADOPTING THE 2025 COLORADO WILDFIRE RESILIENCY CODE
AND APPENDICES, WITH AMENDMENTS
```

**Recitals (lettered A–H; hanging indent; no “WHEREAS” lead-in observed):**

**A.** The unrestricted use of property in wildland-urban interface areas is a potential threat to life and property from fire and resulting erosion.

**B.** On July 1, 2025, the Wildfire Resiliency Code Board (“Board”) created in Colorado Revised Statutes 24-33.5-1236(2), within the Division of Fire Prevention and Control in the Colorado Department of Public Safety, adopted the *2025 Colorado Wildfire Resiliency Code* (“CWRC”) at 8 Code of Regulations Colorado 1507-39(3).

**C.** The CWRC establishes minimum regulations to safeguard life and property from intrusion of fire from wildland fire exposures and fire exposures from adjacent structures and to provide adequate fire protection facilities to control the spread of fire in wildland-urban interface areas.

**C.** Colorado Revised Statutes Section 24-33.5-1237(2)(a), as amended by Colorado Senate Bill 25-142, requires any governing body with jurisdiction in an area within the wildland-urban interface that has authority to adopt building codes to adopt a code that meets or exceeds the minimum standards set forth in the CWRC within nine months of its adoption by the Board.

*(Source anomaly preserved: two consecutive paragraphs are both labeled **C.** — no **C.** then **D.** renumbering observed on this page.)*

**D.** The City of Fort Collins has jurisdiction in an area within the wildland-urban interface and has authority to adopt building codes; therefore, the City is required to adopt a code meeting or exceeding the standards set forth in the CWRC.

**E.** The CWRC is an adaptation of Chapters 1, 2, 3, and 5 of the *2024 International Wildland Urban Interface Code*, published by the International Code Council.

**F.** The City is concurrently adopting, with local amendments, the 2024 publications of the following ten other interconnected basic construction codes published by the International Code Council: the *International Building Code*, *International Residential Code*, *International Mechanical Code*, *International Fuel Gas Code*, *International Energy Conservation Code*, *International Property Maintenance Code*, *International Swimming Pool and Spa Code*, *International Existing Building Code*, *International Plumbing Code*, and the *International Fire Code*.

**G.** The CWRC is also intended to be interconnected with these basic construction codes.

**H.** The City Council has determined that it is in the best interests of the health, safety and welfare of the City and its residents that the *2025 Colorado Wildfire Resiliency Code* be adopted, with local amendments as set forth in this Ordinance.

**Footer:** `- 1 -` (centered).

---

### Page 2 (`page-0002.png`) — printed folio `- 2 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**I.** Pursuant to the City Charter Article II, Section 7, City Council may enact any ordinance which adopts a code by reference in whole or in part provided that before adoption of such ordinance the Council hold a public hearing thereon and that notice of the hearing shall be published twice in a newspaper of general circulation published in the City, with one of such publications occurring at least eight (8) days preceding the hearing and the other publication occurring at least fifteen (15) days preceding the hearing.

**J.** In compliance with City Charter, Article II, Section 7, the City Clerk published in the Fort Collins *Coloradoan* such notice of hearing concerning adoption of the 2024 International Codes on [GREEN DATE REDACTION], 2025, and [GREEN DATE REDACTION], 2025.

**K.** Attached as [UNDERLINE: Exhibit A] and incorporated herein by reference is the Notice of Public Hearing dated [GREEN DATE REDACTION], 2025, that was so published and which the Council hereby finds meets the requirements of Article II, Section 7 of the City Charter.

**Enacting clause:**

In light of the foregoing recitals, which the Council hereby makes and adopts as determinations and findings, BE IT ORDAINED BY THE COUNCIL OF THE CITY OF FORT COLLINS as follows:

**Section 1.** Chapter 5 of the City of Fort Collins is hereby amended by the addition of a new Article IX, which reads in its entirety as follows:

**(Yellow rectangular border begins around the following inserted code text and continues onto subsequent pages through the amendment list.)**

```text
CHAPTER 5

Article IX. Wildfire Resiliency Standards

Sec. 5-370. - Adoption of standards.
```

Pursuant to the power and authority conferred on the City Council by Colorado Revised Statutes Section 31-16-202 and Article II, Section 7 of the Charter, there is hereby adopted by reference as the wildfire resiliency code of the City, for the purposes of safeguarding life and property from intrusion of fire from wildland fire exposures and fire exposures from adjacent structures and mitigating structure fires from spreading to wildland fuels, the *2025 Colorado Wildfire Resiliency Code*, published by the Division of Fire Prevention and Control in the Colorado Department of Public Safety on June 1, 2025, and its referenced standards for the construction and maintenance of all property, buildings, and structures. Except as to any portion of this wildfire resiliency code that is hereinafter amended by the City in this Chapter, this wildfire resiliency code shall include all articles and appendices in the *2025 Colorado Wildfire Resiliency Code*. The wildfire resiliency code is adopted and incorporated fully as if set forth at length herein and the provisions shall be controlling within the City.

**Footer:** `- 2 -` (centered).

---

### Page 3 (`page-0003.png`) — printed folio `- 3 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**(Yellow rectangular border continues around main body.)**

**Sec. 5-371. - Amendments and Deletions to the 2025 Colorado Wildfire Resiliency Code.**

The *2025 Colorado Wildfire Resiliency Code* as adopted in § 5-370 is amended as follows:

**1. Section 101.1 Title** is amended to read as follows:

**101.1 Title.** These regulations shall be known as the Colorado Wildfire Resiliency Code as adopted by ~~[NAME OF JURISDICTION]~~ ==the City of Fort Collins==, hereinafter referred to as “this code.”

**2. Section 102.9 Historic Structures** is amended to read as follows:

**102.9. Historic Structures.** A ~~variance~~ ==modification== is authorized to be issued for the repair or rehabilitation of a historic structure or construction of a contributing structure upon a determination that the proposed repair or rehabilitation will not preclude the structure’s continued designation as a historic structure, and the ~~variance~~ ==modification== is the minimum necessary to preserve the historic character and design of the structure, within the spirit of this code.

**Exception:** Within wildfire hazard areas, historic structures that do not meet one or more of the following designations:
1. Listed or preliminarily determined to be eligible for listing in the National Register of Historic Places.
2. Determined as contributing to the historical significance of a registered historic district or a district preliminarily determined to qualify as an historic district.
3. Designated as historic under a state or local historic preservation program.

**3. Section 102.9.1 Historic preservation exemption** is deleted in its entirety.

~~**102.9.1 Historic preservation exemption.** The authority having jurisdiction may establish a historic preservation exemption or exemptions in their jurisdiction that consists of the spirit and intent of this code.~~

**4. Section 102.10 Work exempt from permit under this code** is amended to read as follows:

**102.10 Work exempt from permit under this code.** Exemptions from code requirements shall not be deemed to grant authorization for any work to be done in any manner in violation of the provisions of this code or any other laws or ordinances of the jurisdiction. Compliance with this code shall not be required for the following:
1. Interior alterations of existing structures.

**Footer:** `- 3 -` (centered).

*(Page continues the exemption list onto page 4 as items 2–10.)*

---

### Page 4 (`page-0004.png`) — printed folio `- 4 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**(Yellow rectangular border continues.)**

*(Continuation of Sec. 102.10 exemption list:)*

2. Additions that do not increase the footprint of a structure by more than 500 square feet ==compared to the condition of the structure on April 1, 2026, as determined based on city and county records.==

3. The reconstruction, replacement, alteration, or repair of the exterior walls of an existing building, when less than 25 percent of the surface area of all exterior walls is affected ==compared to the condition of the exterior walls on April 1, 2026, as determined based on city and county records.==

4. The reconstruction, replacement, alteration, or repair of the exterior *roof covering* of an existing building, when less than 25 percent of the surface area of the exterior *roof covering* or an attachment thereto is affected ==compared to the condition of the exterior *roof covering* on April 1, 2026, as determined based on city and county records.==

5. Alterations or repairs to the exterior of an existing structure, or an attachment to it, when less than twenty-five percent of the exterior of the structure is affected by the alteration or repair.

6. Painting, staining and similar maintenance or restorative work.

7. One-story detached accessory, nonhabitable structures, such as tool and storage sheds, playhouses and similar uses, provided that the floor area does not exceed 120 square feet and the structure is located greater than or equal to 10 feet from the nearest adjacent occupiable structure.

8. *Accessory structures* and buildings of an accessory character classified as Utility and Miscellaneous Group U (including Agricultural Structures) located more than 50 feet from a structure containing *occupiable* or *habitable* space.

   *[UNCERTAIN: whether final defined term is italicized as “*habitable* space” (word only) or “*habitable space*” (phrase); captions conflict. Words *Accessory structures*, *occupiable*, and *habitable* appear italicized.]*

9. Fences located more than 8 feet from a *habitable* structure.

10. Any thirty-five acre parcel with only one residential structure on it that does not abut a residential or commercial area.

**5. SECTION 103—CODE COMPLIANCE AGENCY** is deleted in its entirety and replaced with the following:

~~**SECTION 103—CODE COMPLIANCE AGENCY**~~

~~**103.1 Creation of agency.** The [INSERT NAME OF DEPARTMENT] is hereby created and the official in charge thereof shall be known as the *code official*. The function of the agency shall be the implementation, administration and enforcement of the provisions of this code.~~

~~**103.2 Appointment.** The *code official* shall be appointed by the chief appointing authority of the jurisdiction.~~

~~**103.3 Deputies.** In accordance with the prescribed procedures of this jurisdiction and with the concurrence of the appointing authority, the *code official* shall have the authority to appoint a deputy *code official*, other related technical officers, inspectors and other employees. Such employees shall have powers as delegated by the *code official*.~~

==**SECTION 103—CODE COMPLIANCE AGENCY**==

*(Replacement body for Section 103 continues at top of page 5.)*

**Footer:** `- 4 -` (centered).

---

### Page 5 (`page-0005.png`) — printed folio `- 5 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**(Yellow rectangular border continues.)**

==**103.1 Entity charged with code administration.** The entity charged with code administration shall be as determined in accordance with Section 103 of the adopted *International Building Code*, entitled “Code Administration.”==

**6. Section 105.2 Conformance** is amended to read as follows:

**105.2 Conformance.** Temporary uses, equipment and systems shall conform to the requirements of this code ==and all other applicable local, state and federal regulations,== as necessary to ensure health, safety and general welfare.

**7. Section 106.1 General** is deleted in its entirety and replaced with the following:

~~**106.1 General.** An AHJ has the authority to establish fees.~~

==**106.1 Fees.** All items relating to fees shall be as specified in Section 109 of the adopted *International Building Code*, entitled “FEES.”==

**8. Section 202 Definitions** is amended to modify, or add, the following definitions in alphabetical order:

. . .

==**AUTHORITY HAVING JURISDICTION (AHJ).** The City Council of the City of Fort Collins.==

. . .

**CODE OFFICIAL.** The official designated by the jurisdiction to interpret and enforce this code, or the *code official’s* authorized representative. ==The term *code official* is interchangeable with the term building official.==

*[UNCERTAIN: whether “building official” in the yellow-added sentence is italicized; competing captions. *code official* / *code official’s* appear italicized.]*

. . .

**9. Section 301.1 Scope** is amended to read as follows:

**301.1 Scope.** The provisions of this chapter provide methodology to establish and record wildfire hazard based on the ~~findings of fact~~ ==Colorado Wildfire Resiliency State Code Map (CWRC Map), developed and amended from time to time by the Division of Fire Prevention and Control within the Colorado Department of Public Safety and the Colorado State Forest Service at the direction of the Colorado Wildfire Resiliency Code Board,== to be regulated by this code.

**10. Section 302.1 Declaration** is amended to read as follows:

*(Section 302.1 body begins on page 6.)*

**Footer:** `- 5 -` (centered).

---

### Page 6 (`page-0006.png`) — printed folio `- 6 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**(Yellow rectangular border continues.)**

**302.1 Declaration.** The AHJ shall declare the *wildland-urban interface* areas within the jurisdiction as defined by this code. The *wildland-urban interface* areas shall be based on the ~~findings of fact~~ ==CWRC Map==.

**11. Section 401.1 Scope** is amended to read as follows:

**401.1 Scope.** Exterior design and construction of new buildings and structures within the *wildland-urban interface* areas of Colorado shall be constructed in accordance with this chapter.

**Exceptions:**

1. Buildings of an accessory character classified as Group U occupancy (including *agricultural buildings*) of any size located at least 50 feet from a structure containing *occupiable* or *habitable space*.

2. One-story detached accessory, nonhabitable structures, such as tool and storage sheds, playhouses and similar uses, provided that the floor area does not exceed 120 square feet and the structure is located greater than or equal to 10 feet from the nearest adjacent occupiable structure.

3. The reconstruction, replacement, alteration, or repair of the exterior walls of an existing building, when less than 25 percent of the surface area of all exterior walls is affected ==compared to the condition of the exterior walls on April 1, 2026, as determined based on city and county records.==

4. The reconstruction, replacement, alteration, or repair of the exterior *roof covering* of an existing building, when less than 25 percent of the surface area of the exterior *roof covering* or an attachment thereto is affected ==compared to the condition of the exterior *roof covering* on April 1, 2026, as determined based on city and county records.==

5. Alterations or repairs to the exterior of an existing structure, or an attachment to it, when less than twenty-five percent of the exterior of the structure is affected by the alteration or repair.

6. Additions that do not increase the footprint of a structure by more than 500 ==square feet compared to the condition of the structure on April 1, 2026, as determined based on city and county records.==

7. ==Modifications may be considered for structures older than 50 years, if otherwise required to meet the standards in Chapter X of the City Code to protect identified historic resources. Additional site and area requirements may be needed to offset approved modifications and lower fire risk.==

*(Entire exception 7 appears yellow-highlighted.)*

**12. Section 502.1.2 Materials** is deleted in its entirety.

~~**502.1.2 Materials.** Use *noncombustible*, hard surface materials in this zone, such as rock, gravel, sand, concrete, bare earth or stone/concrete pavers.~~

~~**Exception:** Ignition-resistant plantings, per an approved list by the AHJ that is not less than that created by the Colorado State Forest Service, are allowed in the Immediate Zone.~~

**Footer:** `- 6 -` (centered).

---

### Page 7 (`page-0007.png`) — printed folio `- 7 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**(Yellow rectangular border continues.)**

**13. Section 502.1.3 Plantings** is deleted in its entirety.

~~**502.1.3 Plantings.** Remove all plantings including shrubs, slash, combustible mulch and other woody debris, with the exception of ignition-resistant vegetation.~~

**14. Section 502.1.4 Trees** is deleted in its entirety.

~~**502.1.4 Trees.** There shall be no planting of new trees in the immediate zone. Mature trees of no less than 10-inch diameter at 4.5 feet above ground level may be maintained. *Tree crowns extending to within 10 feet of any structure shall be pruned to maintain a minimum clearance of 10 feet.* Prune tree branches to a height of 6-10 feet from the ground or a third of the total height of the tree, whichever is less.~~

**15. Section 503.2.4 Trees** is deleted in its entirety.

~~**503.2.4 Trees.** Tree crowns extending to within 10 feet of any structure shall be pruned to maintain a minimum clearance of 10 feet.~~
~~Prune tree branches to a height of 6-10 feet from the ground or a third of the total height of the tree, whichever is less.~~

*[UNCERTAIN: whether the first sentence of struck 503.2.4 (Tree crowns …) is italicized like the parallel sentence in 502.1.4; captions conflict.]*

**16. Section 503.2.4.1 Tree Spacing** is deleted in its entirety.

~~**503.2.4.1 Tree Spacing.** Tree crowns within this zone shall be spaced to prevent structure ignition and promote fuel discontinuity to limit fire spread.~~

*[UNCERTAIN: italics on “Tree crowns” in this struck paragraph.]*

**17. Section 503.2.5 Shrubs** is deleted in its entirety.

~~**503.2.5 Shrubs.** Shrub groups within this zone shall be spaced to prevent structure ignition. Shrubs shall be at least 10 feet away from the edge of tree branches.~~

**18. Section 503.3.2 Tree Spacing** is deleted in its entirety.

~~**503.3.2 Tree Spacing.** *Tree crowns* within this zone shall be spaced at a minimum of 6-10 feet.~~

*[Reading retained: “Tree crowns” appears italicized in this struck paragraph per crop caption; still mark mild uncertainty.]*

**19. Section C101.3.7 Violation penalties** is deleted in its entirety and replaced with the following:

~~**C101.3.7 Violation penalties.** An AHJ has the authority to establish fees.~~

==**C101.3.7 Violation penalties.** Any person who violates a provision of this code or fails to comply with any of the requirements thereof or who erects, constructs, alters or repairs a *building* or *structure* in violation of the *approved* construction==

*(Sentence continues on page 8; yellow highlight continues.)*

**Footer:** `- 7 -` (centered).

---

### Page 8 (`page-0008.png`) — printed folio `- 8 -`

**Centered header (bold, all caps, two lines):**

```text
DRAFT FOR DISCUSSION ONLY -
SUBJECT TO FURTHER REVIEW AND REVISION
```

**(Yellow rectangular border / yellow highlight continues for the finishing clause of item 19, then ends.)**

==documents or directive of the *code official*, or of a permit or certificate issued under the provisions of this code, commits a civil infraction and is subject to the provisions contained in § 1-15(f) of the City Code. Each day that a violation continues shall be deemed a separate offense.==

*(Joined reading of item 19 replacement, pages 7–8:)*

> **C101.3.7 Violation penalties.** Any person who violates a provision of this code or fails to comply with any of the requirements thereof or who erects, constructs, alters or repairs a *building* or *structure* in violation of the *approved* construction documents or directive of the *code official*, or of a permit or certificate issued under the provisions of this code, commits a civil infraction and is subject to the provisions contained in § 1-15(f) of the City Code. Each day that a violation continues shall be deemed a separate offense.

**Section 2.** The codifier of the Code of the City of Fort Collins is hereby directed to amend all existing cross references in the City Code and the Land Use Code in accordance with the provisions of this ordinance.

**Section 3.** The City Attorney and the City Clerk are hereby authorized to modify the formatting and to make such other amendments to this Ordinance as necessary to facilitate publication in the Fort Collins City Code; provided, however, that such modifications and amendments shall not change the substance of the Code provisions.

**Adoption / signature block (printed; blanks unfilled; no handwriting observed):**

```text
Introduced, considered favorably on first reading on __________, 2025, and approved on
second reading for final passage on _______________, 2025.

________________________________________
Mayor

ATTEST:

________________________________
City Clerk

Effective Date: _______________, 2025

Approving Attorney: Madelene Shehan
```

*(Blank underscore runs are approximate; exact underscore count not claimed from raster. No ink signatures, initials, or handwritten dates observed on the signature lines.)*

**Footer:** `- 8 -` (centered).

---

## 6. Coverage table

| Physical page | File | Printed folio | Inspection method | Unviewed / unresolved regions |
| :---: | :--- | :---: | :--- | :--- |
| 1 | page-0001.png | - 1 - | Full-page Read + 5 horizontal strip crops | Exact curly vs straight quote code points; line-break positions approximate |
| 2 | page-0002.png | - 2 - | Full-page Read + strips + J/K/date zooms | Exact month/day under green redaction blocks **unreadable**; green blocks themselves transcribed as redactions |
| 3 | page-0003.png | - 3 - | Full-page Read + strips | Em-dash vs hyphen in section titles; exact strike thickness |
| 4 | page-0004.png | - 4 - | Full-page Read + strips + §103 crop | *[UNCERTAIN]* italics extent for *habitable* / *habitable space* in item 8 |
| 5 | page-0005.png | - 5 - | Full-page Read + strips + definitions crop | *[UNCERTAIN]* whether “building official” italicized in yellow CODE OFFICIAL sentence; exact ellipsis glyph (`.` `.` `.` vs `…`) |
| 6 | page-0006.png | - 6 - | Full-page Read + strips + exception-7 crop | Chapter “X” placeholder retained as printed; exact highlight boundary mid-word on item 6 |
| 7 | page-0007.png | - 7 - | Full-page Read + strips + item-19 crop | *[UNCERTAIN]* italics on some struck “Tree crowns” sentences (503.2.4 / 503.2.4.1); whether *building*/*structure* italicized separately vs as one phrase |
| 8 | page-0008.png | - 8 - | Full-page Read + top/mid/bot crops | Exact underscore lengths; blank signature lines (no handwriting) |

**All 8 expected physical pages inspected.** No page left unviewed.

## 7. Notable source anomalies (preserved, not “fixed”)

1. Ordinance number placeholder: **XXX, 2025**.
2. Duplicate recital label **C.** (two consecutive paragraphs).
3. Green date redactions in recitals **J** and **K** (three green blocks total obscuring month/day).
4. Draft banner on every page: **DRAFT FOR DISCUSSION ONLY - SUBJECT TO FURTHER REVIEW AND REVISION**.
5. Local amendment draft markup: yellow highlights (additions), strikethrough (deletions), yellow border around Article IX / §5-371 block.
6. Exception 7 references **Chapter X** of the City Code (placeholder chapter letter).
7. Baseline date **April 1, 2026** appears repeatedly in yellow-highlighted comparison clauses.
8. Signature / effective-date blanks unfilled; printed Approving Attorney name **Madelene Shehan** only (no handwritten signature).

## 8. Limitations

- Caption-mediated vision is not certified unaided pixel inspection.
- Exact Unicode for quotation marks, apostrophes, section symbol, em/en dashes, and ellipsis not claimed from raster.
- Green-redacted dates are unresolved as to underlying characters.
- Graphical strikes/highlights do not establish enacted effect.
- Packet manifest and queue auth file were not present in the workdir for independent hashing (assignment-supplied hashes recorded).
- original.pdf hashed only; text not extracted; PNGs were the transcription source.
- Candidate / 03-custody / 04-verification / OCR / native extraction / Sherlock / Atlas / EB-PDF-014 **not opened**.
- `legal_currentness: not_verified`.

## 9. Printed identity (brief)

City of Fort Collins draft **Ordinance No. XXX, 2025** amending Chapter 5 to adopt the **2025 Colorado Wildfire Resiliency Code** (and appendices) with local amendments as new **Article IX (Wildfire Resiliency Standards)**, §§ 5-370–5-371; concurrent reference to adopting ten 2024 ICC codes; draft for discussion only; approving attorney printed as Madelene Shehan; introduction/passage/effective dates blank “_____, 2025”.
