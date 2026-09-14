"""Build or verify a source-bound Grand Junction fire-fee table review."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

BASE = Path(__file__).resolve().parent
SOURCE_SHA = "1f7faf078188c26fa803e4ec6225d20caad2fcce48f69d2d2ae9563c96732884"
GROUPS = {72: "Miscellaneous Permits", 73: "Fire Sprinkler System Plan Review Fee",
          74: "Fire Alarm Plan Review Fee", 75: "Tenant Finish Plan Review Fee",
          76: "New Building Review Fee"}


class Strict(BaseModel):
    """Reject unknown fields and implicit type conversion."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Bind one local file by its exact bytes."""
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Span(Strict):
    """Preserve one exhaustive native line with byte offsets."""
    id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    role: Literal["label", "fee", "group", "header", "footer"]


class Page(Strict):
    """Bind a directly viewed Poppler page and all native text."""
    physical_page: int = Field(ge=1, le=2)
    native: Asset
    image: Asset
    full_page_directly_viewed: Literal[True] = True
    spans: list[Span]


class Row(Strict):
    """Keep the complete source fee text attached to its visible label."""
    id: str
    physical_page: int
    label_span: str
    fee_span: str
    group_span: str
    group_basis: Literal["visible_preceding_heading", "continued_table_no_repeated_heading"]


class Observation(Strict):
    """Separate a qualified visual observation from source text."""
    id: str
    pages: list[int]
    statement: str


class Review(Strict):
    """Source-only review, with no present-law or adoption certification."""
    schema_version: Literal[1] = 1
    reviewed_at: AwareDatetime
    reviewer: Literal["Atlas"] = "Atlas"
    mode: Literal["candidate_aware_direct_source_review"] = "candidate_aware_direct_source_review"
    source: Asset
    source_id: Literal["grand-junction-fire-fees-mg-07"] = "grand-junction-fire-fees-mg-07"
    official_url: Literal["https://www.gjcity.org/DocumentCenter/View/15794/Fire-Prevention-Fee-Schedule"]
    access_receipt: Asset
    structure_receipt: Asset
    status: Literal["source_checked_pending_legal_review"] = "source_checked_pending_legal_review"
    legal_currentness: Literal["not_verified"] = "not_verified"
    adoption_date: None = None
    effective_date: None = None
    source_edition_date: None = None
    native_bytes: Literal[3673] = 3673
    pages: list[Page] = Field(min_length=2, max_length=2)
    rows: list[Row] = Field(min_length=57, max_length=57)
    observations: list[Observation]
    external_review_consulted: Literal[False] = False
    edited_source_bytes: Literal[False] = False


class Manifest(Strict):
    """Complete package inventory excluding its own two files."""
    schema_version: Literal[1] = 1
    files: list[Asset]
    excluded: list[str]


def asset(path: Path) -> Asset:
    """Return the exact relative file identity."""
    data = path.read_bytes()
    return Asset(path=path.relative_to(BASE).as_posix(),
                 sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def build() -> Review:
    """Apply the row and group map checked against both complete page images."""
    pages, rows = [], []
    for page_num, row_count in ((1, 34), (2, 23)):
        spans, cursor = [], 0
        for index, line in enumerate((BASE/f"page-{page_num}.native.txt").read_text().splitlines(True), 1):
            role = ("label" if index % 2 else "fee") if index <= row_count*2 else "header"
            if page_num == 1 and index in GROUPS:
                role = "group"
            if line.startswith(f"Page {page_num} of 2"):
                role = "footer"
            end = cursor + len(line.encode())
            spans.append(Span(id=f"P{page_num}-L{index:03d}", start=cursor,
                              end=end, text=line, role=role))
            cursor = end
        pages.append(Page(physical_page=page_num, native=asset(BASE/f"page-{page_num}.native.txt"),
                          image=asset(BASE/f"page-{page_num}.png"), spans=spans))
        for index in range(row_count):
            group = 76 if index < 2 else 75 if index < 6 else 74 if index < 8 else 73 if index < 10 else 72
            if page_num == 2:
                group = 72
            rows.append(Row(id=f"GJF-R{len(rows)+1:03d}", physical_page=page_num,
                            label_span=f"P{page_num}-L{index*2+1:03d}",
                            fee_span=f"P{page_num}-L{index*2+2:03d}",
                            group_span=f"P1-L{group:03d}",
                            group_basis="visible_preceding_heading" if page_num == 1
                            else "continued_table_no_repeated_heading"))
    notes = [
        ([1, 2], "All 57 visible fee rows were directly checked against full 144-dpi Poppler renders. Native text has 3,673 bytes and 127 lines; words, amounts, whitespace and ligatures remain unchanged."),
        ([1], "The five native group headings occur after all fee rows and in reverse visual order. The reviewed map attaches 2 new-building, 4 tenant-finish, 2 fire-alarm, 2 sprinkler and 24 miscellaneous rows to their visible headings."),
        ([2], "The 23 page-two rows visibly continue the table under the page title Fire Prevention Service Fees Continued. Miscellaneous Permits is not reprinted; the cross-page group association is an explicit layout annotation, not inserted source text."),
        ([1, 2], "Both page titles and contact lines occur after fee rows in native extraction but are visible at the top. Printed footer text remains separate. Each page has a fire-department emblem; native text does not transcribe its raster lettering. Exact emblem microlettering and font glyph code points are not certified."),
        ([1], "New-building tiers begin at 1-5,000 square feet; tenant-finish tiers begin at 1-200 and continue 201-500, 501-5,000 and >5,000. No unstated zero-area tier or calculation rule is added."),
        ([1], "The fire-alarm modification row visibly says flate fee= < 5 devices, while sprinkler modification says (=< 20 heads). Preserve these source spellings/operators without replacing them with a normalized inequality or merging their scopes."),
        ([1], "Includes inspections applies to the 1-200 tenant-finish row. Other listed per-inspection charges, the per-trip/paid-prior condition, per-tank versus flat charges and per-device wording remain inside their respective fee cells."),
        ([1], "Double regular fee belongs to work performed without obtaining a permit. The 1.5 X original plan review fee belongs to plans requiring more than two (2) reviews. Neither multiplier is applied to other rows."),
        ([1, 2], "Annual Mobile Food Preparation Vehicles, hourly Alternative Materials/Designs/Methods Review, and Burn Permit per-year labels remain distinct. Repeated storage and spray labels on the source are not deduplicated."),
        ([1, 2], "Explosives of blasting agents, PVP Systems and flate are preserved as printed/native source wording. Mixed native ligatures and plain letter sequences are not rewritten as corrections."),
        ([1, 2], "No visible edition, adoption or effective date was observed. September 2025 PDF creation/modification metadata do not establish legal dates. The alternate linked fee endpoint and adopting instruments have not been reconciled."),
        ([1, 2], "The city referral and printed Grand Junction contact details identify this source; its applicability to a separately named rural fire district or other authority is not established by this document review."),
    ]
    return Review(reviewed_at=datetime.now(timezone.utc), source=asset(BASE/"original.pdf"),
                  official_url="https://www.gjcity.org/DocumentCenter/View/15794/Fire-Prevention-Fee-Schedule",
                  access_receipt=asset(BASE/"access-event.json"),
                  structure_receipt=asset(BASE/"STRUCTURE.json"), pages=pages, rows=rows,
                  observations=[Observation(id=f"GJF-O{i:02d}", pages=ps, statement=s)
                                for i, (ps, s) in enumerate(notes, 1)])


def verify(review: Review) -> dict[str, object]:
    """Check byte coverage and independently recover all native row geometry."""
    assert review.source.sha256 == SOURCE_SHA
    for a in [review.source, review.access_receipt, review.structure_receipt]:
        assert asset(BASE/a.path) == a
    event = json.loads((BASE/review.access_receipt.path).read_text())
    assert event["body_sha256"] == SOURCE_SHA and event["http_status"] == 200
    assert event["requested_url"] == event["final_url"] == review.official_url
    all_spans, boxes = {}, {}
    with pymupdf.open(BASE/review.source.path) as doc:
        assert len(doc) == 2
        for page in review.pages:
            assert asset(BASE/page.native.path) == page.native
            assert asset(BASE/page.image.path) == page.image
            raw = (BASE/page.native.path).read_bytes()
            pdf_page = doc[page.physical_page-1]
            assert pdf_page.get_text("text", sort=False, flags=195).encode() == raw
            lines = [line for b in pdf_page.get_text("dict", sort=False, flags=195)["blocks"]
                     if b["type"] == 0 for line in b["lines"]]
            assert ["".join(s["text"] for s in l["spans"])+"\n" for l in lines] == [s.text for s in page.spans]
            cursor = 0
            for span, line in zip(page.spans, lines):
                assert span.id not in all_spans
                assert span.start == cursor and raw[span.start:span.end] == span.text.encode()
                cursor = span.end
                all_spans[span.id], boxes[span.id] = span, tuple(line["bbox"])
            assert cursor == len(raw)
    assert sum(p.native.size_bytes for p in review.pages) == 3673
    assert len(all_spans) == 127
    for n, title in GROUPS.items():
        assert all_spans[f"P1-L{n:03d}"].text.strip() == title
    labels, fees = [], []
    for row in review.rows:
        label, fee = all_spans[row.label_span], all_spans[row.fee_span]
        assert label.role == "label" and fee.role == "fee"
        assert label.id.startswith(f"P{row.physical_page}-")
        assert fee.id.startswith(f"P{row.physical_page}-")
        a, b = boxes[label.id], boxes[fee.id]
        assert b[0] > a[2] and max(a[1], b[1]) < min(a[3], b[3])
        candidates = [s for s in all_spans.values() if s.role == "fee"
                      and s.id.startswith(f"P{row.physical_page}-")]
        assert min(candidates, key=lambda s: abs(sum(boxes[s.id][1::2])-sum(a[1::2]))).id == fee.id
        if row.physical_page == 1:
            preceding = [f"P1-L{n:03d}" for n in GROUPS if boxes[f"P1-L{n:03d}"][1] < a[1]]
            assert max(preceding, key=lambda g: boxes[g][1]) == row.group_span
            assert row.group_basis == "visible_preceding_heading"
        else:
            assert row.group_span == "P1-L072"
            assert row.group_basis == "continued_table_no_repeated_heading"
        labels.append(label.id)
        fees.append(fee.id)
    assert len(labels) == len(set(labels)) == len(fees) == len(set(fees)) == 57
    assert set(labels) == {s.id for s in all_spans.values() if s.role == "label"}
    assert set(fees) == {s.id for s in all_spans.values() if s.role == "fee"}
    return {"status": "passed", "physical_pages": 2, "native_bytes": 3673,
            "native_lines": 127, "fee_rows": 57, "visible_group_headings": 5,
            "cross_page_continuation_rows": 23, "row_geometry_checked": True,
            "legal_currentness": "not_verified"}


def write_new(path: Path, text: str) -> None:
    """Write atomically once and refuse to overwrite frozen evidence."""
    assert not path.exists(), path
    temporary = path.with_name(path.name+".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    """Build a new package once, or verify it offline without writes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        inventory = Manifest.model_validate_json((BASE/"MANIFEST.json").read_bytes())
        assert inventory.excluded == ["MANIFEST.json", "MANIFEST.schema.json"]
        actual = sorted(p.relative_to(BASE).as_posix() for p in BASE.rglob("*") if p.is_file()
                        and p.name not in inventory.excluded and "__pycache__" not in p.parts)
        assert actual == sorted(a.path for a in inventory.files)
        for a in inventory.files:
            assert asset(BASE/a.path) == a
        review = Review.model_validate_json((BASE/"SOURCE_QA.json").read_bytes())
        jsonschema.validate(review.model_dump(mode="json"), json.loads((BASE/"SOURCE_QA.schema.json").read_text()))
    else:
        review = build()
    result = verify(review)
    if not args.verify:
        write_new(BASE/"SOURCE_QA.json", review.model_dump_json(indent=2)+"\n")
        write_new(BASE/"SOURCE_QA.schema.json", json.dumps(Review.model_json_schema(), indent=2)+"\n")
        lines = ["---", "title: Grand Junction fire-prevention fee source review",
                 "legal_currentness: not_verified", "---", "", "# Scope", "",
                 "Both complete source pages were directly viewed using newly rendered Poppler images. "
                 "The review preserves all 3,673 native bytes and binds 57 fee rows to their labels. "
                 "Five headings are restored as separate associations; no native source wording is changed.", "",
                 "Use [SOURCE_QA.json](SOURCE_QA.json) with [original.pdf](original.pdf). "
                 "The copied access receipt describes event E008 in the separately preserved discovery; "
                 "its original event-relative paths are historical references, not files promised here.", "",
                 "# Qualifications", ""]
        lines += [f"- {o.statement}" for o in review.observations]
        lines += ["", "# Verification", "", "Run `PYTHONDONTWRITEBYTECODE=1 python build_review.py --verify` "
                  "with Python 3.11+, Pydantic 2, jsonschema and PyMuPDF 1.28.2. This checks "
                  "every inventoried file, exhaustive native bytes, all label/fee assignments and "
                  "fresh PDF geometry. It verifies image-file identity, not a repeat of human visual judgment. "
                  "Keep the manifest hash outside this package. No legal currentness is certified.", ""]
        write_new(BASE/"README.md", "\n".join(lines))
        files = [asset(p) for p in sorted(BASE.rglob("*")) if p.is_file()
                 and "__pycache__" not in p.parts]
        inventory = Manifest(files=files, excluded=["MANIFEST.json", "MANIFEST.schema.json"])
        write_new(BASE/"MANIFEST.json", inventory.model_dump_json(indent=2)+"\n")
        write_new(BASE/"MANIFEST.schema.json", json.dumps(Manifest.model_json_schema(), indent=2)+"\n")
    logging.warning(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
