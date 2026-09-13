# Colorado Springs fire fees: custody and source structure

Two official City PDF responses completed on 12 September 2026 at 23:10:46–47 UTC,
with HTTP 200, no redirects and 421,075 retained bytes. Both PDFs have seven
physical pages. This packet preserves their bytes, all native text and page
renderings, exact response receipts, official parent links and bounded source
observations. It does not add them to the canonical raw archive.

The first source visibly names the **2015 Fee Schedule - Code Services**. Atlas
viewed all seven pages for structure and selected context. It covers construction
review, operational permits, other fees and definitions. Complete numeric table
QA has not been performed. Its native text contains white-on-white numbers on
page 1 and “2015 Proposed changes” on pages 2–6. Exact text traces and cropped RGB
regions reproduce that distinction. These strings are present in the PDF's text
layer, but are not visible in the checked white regions. Neither those strings
nor its visible title prove enactment or present applicability.

The second source visibly states **Construction Services Fee Schedule** and
**Effective 07/01/2026**. The date is the source's claim; an adopting instrument has
not been independently verified. Atlas checked physical pages 1, 5, 6 and 7 here;
complete table review is a separate task. The contents page places definitions on
page 5 although the section starts on physical page 6. Page 6 describes PPRBD's
collection of the construction-plan-check fee and the conditional deduction on
CSFD approval; PPRBD is not substituted for the municipal issuer.

Page 7 states that assessment occurs on the plan approval date, and refers
high-pile storage and hazardous-material fees to the Code Services Fee Schedule.
It does not specify that schedule's edition. This packet makes no supersession
finding between the two PDFs and performs no fee calculations.

`SOURCE_SCOPE.json` and its schema bind seven selected native passages to exact
UTF-8 byte offsets. They also bind all fourteen native pages/renderings, source
identities, acquisition intervals and eight white-text regions. Native extraction
is an uncorrected candidate: the 2015 definition headings are detached from their
bodies and one body is out of order. Reading order and numeric associations
require their own layout checks.

Run `validate_scope.py` with Python, Pydantic 2, PyMuPDF and BeautifulSoup from any
working directory. It verifies the closed inventory, unchanged source text and
pixels, exact iframe link derivation, receipt hashes, selected passage slices and
white-region proof. It performs no source requests, OCR or corpus writes. The
acquisition guard and preparation script are historical records; do not rerun
them in this frozen copy. Hash checks establish preserved evidence, not legal
accuracy. Legal currentness remains **not_verified**.
