# PASS1_frozen — EB-PDF-014

- assignment_id: EB-PDF-014
- source_id: fort-collins-land-use-article-1-sd005-07
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 1 (blind image-only transcription)
- legal_currentness: not_verified
- prior_candidate_exposure: none
- utc_start: 2026-09-11T19:22:25Z
- expected_pages: 7
- inspected_pages: 7
- image_method: Read on full-page PNGs page-0001.png … page-0007.png; Pillow crops re-read via Read (section/line bands). No OCR, no native PDF text extraction, candidate not opened.
- captions_assistance: Vision returns were caption-mediated. Captions treated as non-authoritative; conflicting caption injections (e.g. alien section numbers on one band crop) ignored; wording taken from repeated full-page and multi-crop re-reads. Chat also supplied image_description blocks for the same pages; those were not used as substitute quotations where crops conflicted.
- packet_manifest_sha256: ee87ef2806e3cf9b955dbceca927087918ed0906894879a8597d7436ad67db0b
- original_pdf_sha256: 555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a

## Page image SHA-256 (verified before transcription)

| file | sha256 |
|------|--------|
| page-0001.png | 7ed3f49842c2039bb73f2776d3ad373a7955e6d0b36ebebd5ae4c2e23f141b2c |
| page-0002.png | a3c3dbe905ac1901d482f474671c474f10d30ed8d33ee11219f332e4a2e5248e |
| page-0003.png | 6c4696f83452f7eafd6f3f8c79a762f37f01bedd8c6e8ac6f6be61ec040a0ca3 |
| page-0004.png | 812fc96f8f1a01e7301aaf6f7a725201e2fdfd666a8e0e62c89d65a224c234fc |
| page-0005.png | 4c3e9b0d1e956212d3c025fb0c2936358b5f596d3f91c5c8045fdce38476fb3f |
| page-0006.png | b84cd01abd9808f61997c651f2810de27df956ca46d09b391fa15bc9f5decbc9 |
| page-0007.png | dadd797082f6f669395a1a230fac4a40fd324befe7f8a4d48f2afd2db4ea1288 |

## Coverage table

| physical_page | file | printed_page_label | inspection | unviewed_or_unresolved |
|---------------|------|--------------------|------------|-------------------------|
| 1 | page-0001.png | (none; title/cover) | full-page Read + upper crop | Exact Unicode of header dash; exact logo geometry; title horizontal alignment (appears centered-left in upper half) |
| 2 | page-0002.png | (none; accessibility notice) | full-page Read + upper/links/photo crops | Photo scene details not fully itemized; exact hyperlink destinations unknown from pixels; dotted border / watermark geometry approximate |
| 3 | page-0003.png | (none; TOC) | full-page Read + TOC crop | No page-number column visible; large blank lower region (intentionally empty) |
| 4 | page-0004.png | 1-1 | full-page Read + hdr/body/footer crops | Exact bold/link blue styling; quotation mark glyph shape (curly vs straight) approximate |
| 5 | page-0005.png | 1-2 | full-page Read + section crops | Italics on *Our Climate Future* confirmed visually as italic; exact apostrophe glyph in "city's" approximate |
| 6 | page-0006.png | 1-3 | full-page Read + disclaimer/auth/applicability/end crops | Embedded "- 4 -" in body confirmed; Authority semicolon vs comma after "Constitution" resolved as semicolon from start-of-sentence crop; Charter "The" capitalization marked below |
| 7 | page-0007.png | 1-4 | full-page Read + division/conflict/severability/footer crops | Missing "and" in 1.3.2(A) preserved; lowercase "it" in 1.3.3 preserved |

## Typography / layout notes (global)

- Running header on content pages 4–7: dark blue left banner, white text approximately `ARTICLE 1 – GENERAL PURPOSE and PROVISIONS` (word "and" lowercase; dash glyph not claimed as exact Unicode).
- Section headings (e.g. `1.2.1 TITLE`) appear medium/dark blue, all-caps.
- Division headings (e.g. `DIVISION 1.1 …`) appear light gray, all-caps, often with a thin horizontal rule beneath.
- Lettered purpose list markers `(A)`…`(N)` appear blue.
- Article labels in Division 1.1 list appear blue before black titles.
- Footers on pages labeled 1-1 … 1-4: `N-N | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE` (first segments bluer; city name segment lighter gray).
- No signatures or handwriting observed on any page.
- No strike-through or handwritten additions observed.
- legal_currentness: not_verified

---

## Page 1 — Article title cover

**Printed label:** none

**Visual:** Light blue full-page background. Dark blue top-left banner. City of Fort Collins logo (text + stylized mountain/wave graphic). Large `ARTICLE 1`. Title lines below.

**Transcribed text (reading order):**

```
ARTICLE 1 – GENERAL PURPOSE and PROVISIONS
```
[banner; "and" lowercase]

[logo text]
```
City of
Fort Collins
```
[stylized graphic under logo]

```
ARTICLE 1

General Purpose
and Provisions
```

**Notes:** Lower ~half of page blank (light blue). Title case on "General Purpose" / "and Provisions" (not all-caps). No footer.

---

## Page 2 — Accessibility / assistance notice

**Printed label:** none

**Visual:** White page; faint large circular accessibility-style watermark centered behind text; light dotted rectangular frame; City logo at top; color photograph of Old Town streetscape across bottom third.

**Transcribed text (reading order):**

[logo]
```
City of
Fort Collins
```

```
FOR ASSISTANCE VIEWING OR READING
ANY CITY DOCUMENTS,
```

```
please call 970-221-6515 (V/TDD: Dial 711 for Relay Colorado) for assistance or contact the City's ADA Coordinator via email adacoordinator@fortcollins.gov or phone: 970-416-4254.
```

[email appears blue + underlined]

```
A Request for Reasonable Accommodation
can also be completed online.
```

["A Request for Reasonable Accommodation" appears blue + underlined; may wrap as two lines with the remainder in black]

```
For more information about the City's Non-Discrimination policy and Accessibility efforts, visit fortcollins.gov/Non-Discrimination.
```

[URL appears blue + underlined]

**[Photograph — graphical, not text]:** Historic brick building with corner turret; trees; flower beds; string lights / circular overhead frames; blue sky; parked cars. Not transcribed as prose.

**Notes:** No page footer of the Article 1 style. Apostrophe in "City's" glyph not claimed exactly.

---

## Page 3 — Table of Contents

**Printed label:** none

**Visual:** Light pale-blue background; left-aligned TOC in upper portion; large empty lower region.

**Transcribed text:**

```
City of Fort Collins - Land Use Code

TABLE OF CONTENTS

DIVISION 1.1 ORGANIZATION OF LAND USE CODE

DIVISION 1.2 TITLE, PURPOSE, AND AUTHORITY
    1.2.1 Title
    1.2.2 Purpose
    1.2.3 Authority
    1.2.4 Applicability
    1.2.5 Minimum standards

DIVISION 1.3 LEGAL
    1.3.1 Relationship to code of the City
    1.3.2 Conflict between Land Use Code standards and Conflict with other laws
    1.3.3 Severability
```

**Anomaly:** TOC entry 1.3.2 repeats the word "Conflict" (`…standards and Conflict with other laws`).

**Notes:** Division lines light gray all-caps; numbered entries darker blue. No dotted leaders or page numbers beside entries. Indentation of 1.2.x / 1.3.x under divisions is visual layout, not wording.

---

## Page 4 — printed label 1-1 — DIVISION 1.1

**Header banner:** `ARTICLE 1 – GENERAL PURPOSE and PROVISIONS`

**Main title:**
```
ARTICLE 1
GENERAL PURPOSE and PROVISIONS
```

**Division:**
```
DIVISION 1.1 ORGANIZATION OF LAND USE CODE
```
[thin horizontal rule]

**Body:**

```
The City of Fort Collins Land Use Code is organized into seven (7) Articles as follows:

Article 1: General Purpose and Provisions
Article 2: Zone Districts
Article 3: Building Types
Article 4: Use Standards
Article 5: General Development and Site Design
Article 6: Administration and Procedures
Article 7: Rules of Measurement and Definition
```

["Article N:" appears blue; titles black]

```
The General Purpose and Provisions contained in Article 1 address the organization of this Land Use Code ("LUC" or "Code"); its title, purpose and authority and the relationship to the Code of the City of Fort Collins.

All zone districts within the City of Fort Collins and their respective list of permitted uses, prohibited uses, and development standards for particular uses are described in Articles 2 and 4. These zone districts directly relate to the Zoning Map and Zone Districts established in Article 6.

Articles 3 and 5 establish standards that apply to all types of development applications unless otherwise indicated. Collectively, these articles are known as the general development standards and address standards for environmental and historic resource protection (see also, Code of the City of Fort Collins Chapter 14), site, building, and infrastructure design, compact urban growth, and transportation and circulation.

Article 6, Administration and Procedures, guides the reader through the procedural and decision-making process by providing divisions pertaining to general procedural requirements and a twelve-step common development review process, as well as providing a separate division for each type of development application and other land use requests; rules for interpretation; rules for nonconformities; amendments to the text of this Code and/or Zoning Map, enforcement mechanisms, and guidelines and regulations for areas and activities of state interest.

Definitions of terms and measurements used throughout this LUC are included in Article 7 although definitions specific to areas and activities of state interest are contained in Article 6.

This method of organization, which distinguishes and separates general provisions, administration, general development standards, district standards and definitions, use-specific standards, and sign standards is intended to provide a user-friendly and easily accessible LUC. This is accomplished by consolidating most city regulations addressing land use and development, standardizing the regulatory format, providing common development review procedures, and clarifying standards and definitions.

For an overview on how to use this LUC when applying for a development application or other request, see Section 6.2.2, Overview of Development Review Procedures.
```

**Footer:** `1-1 | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE`

**Notes:** Bold emphasis observed on several "Article …" mentions in body; quotation marks around LUC/Code appear typographic/curly — exact codepoints not claimed. Uncertainty: whether `"LUC" or "Code"` uses curly double quotes.

---

## Page 5 — printed label 1-2 — DIVISION 1.2 (start)

**Header banner:** `ARTICLE 1 – GENERAL PURPOSE and PROVISIONS`

```
DIVISION 1.2 TITLE, PURPOSE, AND AUTHORITY
```
[thin horizontal rule]

```
1.2.1 TITLE
The provisions contained herein shall be known, cited and referred to as the "City of Fort Collins Land Use Code," the "Land Use Code," the "LUC," or as referenced in the Land Use Code, the "Code."

1.2.2 PURPOSE
The purpose of this Code is to improve and protect the public health, safety, and welfare by furthering one or more of the following considerations with respect to proposed development:

(A) Ensuring that all growth and development which occurs is consistent with this Code, and in general alignment with City Plan and its adopted elements, including, but not limited to, the Structure Plan, Principles and Policies, and associated sub-area plans.

(B) Implementing the vision of the Housing Strategic Plan that everyone in Fort Collins has healthy, stable housing they can afford.

(C) Supporting Our Climate Future goals to reduce energy consumption and greenhouse gas emissions, provide renewable electricity, and achieve zero waste.
```
[*Our Climate Future* appears italicized]

```
(D) Encouraging innovation and responsive design solutions in land development and redevelopment.

(E) Fostering the safe and efficient use of the land, the city's transportation infrastructure, and other public facilities and services.

(F) Ensuring the provision of adequate public facilities and services such as transportation (streets, bicycle routes, sidewalks and mass transit), water, wastewater, storm drainage, fire and emergency services, police, electricity, open space, recreation, and public parks.

(G) Avoiding the inappropriate development of lands and providing for adequate drainage and reduction of flood damage.

(H) Encouraging efficient and functional patterns of land use which decrease reliance on automobile travel and encourage trip consolidation.

(I) Increasing public safety, availability, and access to mass transit, sidewalks, trails, bicycle routes and other alternative modes of transportation.

(J) Minimizing adverse impacts of development on natural systems and the environment.

(K) Improving the design, quality and character of development.

(L) Fostering a more integrated and purposeful development pattern that incorporates a resilient balance of uses.
```

**Footer:** `1-2 | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE`

---

## Page 6 — printed label 1-3 — PURPOSE continued; 1.2.3; 1.2.4

**Header banner:** `ARTICLE 1 – GENERAL PURPOSE and PROVISIONS`

```
(M) Encouraging appropriate development and redevelopment within established areas

(N) Encouraging a wide variety of housing opportunities at various densities that are well-served by public transportation for people of all ages, abilities, and income levels.

The purpose statements set forth in this Section and all other purpose statements set forth in this Land Use Code are not intended to be interpreted or applied as binding standards, terms, conditions, requirements, or procedures pursuant to Section 1.2.4 or otherwise, unless specifically referenced in the Land Use Code including but not limited to Sections 6.8.2 and 6.14.4, and only to the extent the purpose statements in this Section reasonably apply in consideration of the specific context. Purpose statements are solely intended to provide guidance in the interpretation and application of the accompanying Land Use Code standards that have been adopted to implement the purposes described in such statements.

1.2.3 AUTHORITY
The City Council of the City of Fort Collins has the authority to adopt this Land Use Code pursuant to Article XX of the Colorado Constitution; Title 31, Article 2 of the Colorado Revised Statutes, the Charter of The City of Fort Collins, Colorado, and such other authorities and provisions as are established in the statutory and common law of the State of Colorado.

1.2.4 APPLICABILITY
The provisions of this Code shall apply to any and all development of land, as defined in Article 7 of this Code, within the municipal boundaries of the City, unless expressly and specifically exempted or provided otherwise in this Code. For example, this Code is meant to complement and not override or substitute for the requirements of Chapter 14 of the Code of the City of Fort Collins regarding landmarks. No development shall be undertaken without prior and proper approval or authorization pursuant to the terms of this Code. All development shall comply with the applicable terms, conditions, requirements, standards and procedures established in this Code. However, (1) purpose statements set forth in this Code, and (2) City Council adopted policy plans, including but not limited to City Plan and its adopted elements or sub-area plans, are not intended to establish applicable terms, conditions, requirements, standards or procedures, unless explicitly identified and specified otherwise in this Code. Instead, purpose statements and Council adopted policy plans are solely intended to provide guidance in the interpretation - 4 - and application of the accompanying Land Use Code standards that have been adopted to implement the purposes described in such statements.

Except as hereinafter provided, no building, structure or land shall be used and no building or structure or part thereof shall be erected, constructed, reconstructed, altered, repaired, moved or structurally altered except in conformance with the regulations herein specified for the district in which it is located, nor shall a yard, lot or open space be reduced in dimensions or area to an amount less than the minimum requirements set forth herein and all other applicable standards of the City or to an amount greater than the maximum requirements set forth herein and all other applicable standards of the City.

This Land Use Code establishes procedural and substantive rules for obtaining the necessary approval to develop land and construct buildings and structures. Development applications for overall development plans, project development plans, and final plans will be reviewed for compliance with the applicable development standards herein and all other applicable standards of the City. Building permit applications will also be reviewed for compliance with the applicable development standards and District Standards and all other applicable standards of the City and will be further reviewed for compliance with the approved final plan in which they are located.
```

**Footer:** `1-3 | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE`

**Anomalies / uncertainty:**
- Embedded page-marker artifact `- 4 -` appears mid-sentence between "interpretation" and "and application".
- Cross-refs read as `Sections 6.8.2 and 6.14.4` on multi-crop re-read (one thin band caption briefly hallucinated other numbers; ignored).
- `Charter of The City of Fort Collins` — capital "T" in "The" as read on Authority crop; mark as medium-confidence glyph capitalization.
- After "Colorado Constitution" punctuation read as semicolon on the Authority start crop.

---

## Page 7 — printed label 1-4 — APPLICABILITY continued; 1.2.5; DIVISION 1.3

**Header banner:** `ARTICLE 1 – GENERAL PURPOSE and PROVISIONS`

```
This Land Use Code shall also apply to the use of land following development to the extent that the provisions of this Land Use Code can be reasonably and logically interpreted as having such ongoing application.

1.2.5 MINIMUM STANDARDS
The provisions of this Land Use Code are the minimum standards necessary to accomplish the purposes of this Land Use Code.

DIVISION 1.3 LEGAL
```
[thin horizontal rule]

```
1.3.1 RELATIONSHIP TO CODE OF THE CITY
This Land Use Code, although not a numbered Chapter of the Code of the City, is adopted by reference in Chapter 29 of the Code of the City and made part thereof, with the same legal significance as though it were a numbered Chapter. This Land Use Code may be used, as applicable, to support the implementation of the Code of the City; and the Code of the City may be used, as applicable, to support the implementation of this Land Use Code. Particularly, but without limitation, the provisions of Chapter 1 of the Code of the City are incorporated into this Land Use Code by reference.

1.3.2 CONFLICT BETWEEN LAND USE CODE STANDARDS AND CONFLICT WITH OTHER LAWS
(A) In the event of a conflict between a standard or requirement contained in Articles 2, 3, or 4 a standard or requirement in Article 5, the standard or requirement in Article 2, 3, or 4 shall prevail to the extent of the conflict. In the event there is a conflict between standards or requirements contained in Article 2, 3, or 4, the more specific standard or requirement shall prevail to the extent of the conflict. If neither standard or requirement is more specific, the more stringent standard or requirement shall prevail to the extent of the conflict.

(B) In the event of conflicts not addressed in (A), if the provisions of this Land Use Code are internally conflicting or if they conflict with any other statute, code, local ordinance, resolution, regulation or other applicable Federal, State, or local law, the more specific standard, limitation, or requirement shall govern or prevail to the extent of the conflict. If neither standard is more specific, then the more stringent standard, limitation or requirement shall govern or prevail to the extent of the conflict.

1.3.3 SEVERABILITY
It is the legislative intent of the City Council in adopting this Land Use Code that all provisions hereof shall be liberally construed to protect and preserve the peace, health, safety and general welfare of the inhabitants of the City. it is the further intent of the City Council that this Land Use Code shall stand, notwithstanding the invalidity of any part thereof, and that should any provision of this Land Use Code be held to be unconstitutional or invalid by a court or tribunal of competent jurisdiction, such holding shall not be construed as affecting the validity of any of the remaining provisions.
```

**Footer:** `1-4 | ARTICLE 1 | CITY OF FORT COLLINS - LAND USE CODE`

**Anomalies (preserved):**
- Heading and TOC: repeated "CONFLICT" in 1.3.2 title.
- 1.3.2(A): missing conjunction — reads `Articles 2, 3, or 4 a standard or requirement in Article 5` (no "and" visible between "4" and "a").
- 1.3.3: second sentence begins with lowercase `it`.

---

## Source anomalies summary

1. TOC / §1.3.2 title: "Conflict … and Conflict with other laws" / "CONFLICT … AND CONFLICT WITH OTHER LAWS".
2. §1.3.2(A): missing "and" between Articles 2/3/4 clause and Article 5 clause.
3. §1.3.3: lowercase "it" starting second sentence.
4. §1.2.4 body: stray embedded `- 4 -` between "interpretation" and "and application".
5. legal_currentness: not_verified.

## Unresolved regions

- Exact Unicode for dashes in banners/footers and for quotation/apostrophe glyphs.
- Exact hyperlink URL targets on page 2 (only visible link text/URL strings transcribed).
- Fine photographic inventory on page 2 bottom image (non-text).
- Medium confidence: capitalization `The` in "Charter of The City of Fort Collins".
- Caption mediation: one thin band crop briefly proposed different section numbers; resolved via wider crops to 6.8.2 and 6.14.4.

## Blindness / non-use confirmations

- candidate.txt / 02-candidate-text / native extraction / OCR: NOT opened for this pass.
- 03-custody / 04-verification / Sherlock / Atlas / repository text / EB-PDF-013 materials: NOT opened for this pass.
- prior_candidate_exposure: none
- Candidate SHA listed in assignment noted only as reserved for post-freeze; file not opened.

## End of PASS1_frozen
