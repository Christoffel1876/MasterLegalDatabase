"""Freeze and verify a bounded image review of Grand Junction Ordinance 5340."""
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
SOURCE_SHA = "ee803ba2d03f7d7ba93b9135812244f904a83ab36a7f06f8434c93554a2eeb78"


class Strict(BaseModel):
    """Reject coercion and unknown data fields."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Bind a relative file to its exact bytes."""
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Page(Strict):
    """Distinguish visual inspection from native extraction usability."""
    physical_page: int = Field(ge=1, le=5)
    image: Asset
    native: Asset
    full_page_viewed: Literal[True] = True
    native_status: Literal["partial_ocr_with_errors", "empty_despite_visible_text",
                           "largely_unusable_ocr", "printed_body_readable_graphics_separate"]


class Passage(Strict):
    """Bind a manually reviewed passage to its original page image."""
    physical_page: int
    start: int
    end: int
    text: str
    image_path: str
    evidence_scope: Literal["full_page_image_manual_check"] = "full_page_image_manual_check"


class Correction(Strict):
    """Keep checked print separate from unchanged OCR and handwritten marks."""
    physical_page: int
    candidate: str
    checked_print: str
    qualification: str


class DateStatement(Strict):
    """A source statement, not an independently verified legal date."""
    physical_page: int
    role: str
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    native_anchor: str
    status: Literal["source_assertion_only"] = "source_assertion_only"


class Review(Strict):
    """Qualified complete page inspection with partial passage transcription."""
    schema_version: Literal[1] = 1
    reviewed_at: AwareDatetime
    source: Asset
    receipt: Asset
    passages_file: Asset
    mode: Literal["atlas_candidate_aware_direct_image_review"]
    status: Literal["bounded_passages_checked_graphical_limits_preserved"]
    legal_currentness: Literal["not_verified"] = "not_verified"
    adoption_date_verified: None = None
    effective_date_verified: None = None
    full_diplomatic_transcription: Literal[False] = False
    external_blind_review: Literal[False] = False
    original_and_native_edited: Literal[False] = False
    native_bytes: Literal[4465] = 4465
    pages: list[Page] = Field(min_length=5, max_length=5)
    derivatives: list[Asset]
    derivative_recipe: list[str]
    passages: list[Passage]
    corrections: list[Correction]
    dates: list[DateStatement]
    unresolved: list[str]


class Manifest(Strict):
    """Every distributed file except the inventory and its schema."""
    files: list[Asset]
    excludes: Literal["MANIFEST.json;MANIFEST.schema.json"] = "MANIFEST.json;MANIFEST.schema.json"


def asset(path: Path) -> Asset:
    """Read exact identity of a safe relative file."""
    data = path.read_bytes()
    return Asset(path=path.relative_to(BASE).as_posix(),
                 sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def build() -> Review:
    """Bind checked Markdown paragraphs without presenting them as raw source text."""
    raw = (BASE/"REVIEWED_PASSAGES.md").read_bytes()
    passages, page, cursor = [], None, 0
    for chunk in raw.split(b"\n\n"):
        text = chunk.decode()
        if text.startswith("## Page "):
            page = int(text[8])
        if page is not None:
            passages.append(Passage(physical_page=page, start=cursor, end=cursor+len(chunk),
                                    text=text, image_path=f"page-{page}.png"))
        cursor += len(chunk)+2
    statuses = ["partial_ocr_with_errors", "empty_despite_visible_text", "largely_unusable_ocr",
                "partial_ocr_with_errors", "printed_body_readable_graphics_separate"]
    corrections = [(1,"BE tT","BE IT","Printed operative introduction; native bytes unchanged."),
                   (1,"underimed","underlined","Printed typography example, not a substantive amendment."),
                   (4,"prosorved","preserved","Inside visibly struck paragraph (g)."),
                   (4,"thrco","three","Inside visibly struck paragraph (g)."),
                   (4,"Selestina Sa","Selestina Sandoval","Printed clerk label only; no handwriting identity claim.")]
    dates = [(1,"historical_recital_resolution_47_25","2025-08-06","On August 6, 2025"),
             (4,"introduction_first_reading","2026-08-05","5th day of August 2026"),
             (4,"adoption_second_reading","2026-09-02","2nd day of September 2026"),
             (5,"certification","2026-09-08","8th day of September 2026"),
             (5,"first_publication","2026-08-08","Published: August 8, 2026"),
             (5,"second_publication","2026-09-05","Published: September 5, 2026"),
             (5,"effective_as_stated_future_at_capture","2026-10-05","Effective: October 5, 2026")]
    return Review(reviewed_at=datetime.now(timezone.utc), source=asset(BASE/"original.pdf"),
                  receipt=asset(BASE/"access-event.json"), passages_file=asset(BASE/"REVIEWED_PASSAGES.md"),
                  mode="atlas_candidate_aware_direct_image_review",
                  status="bounded_passages_checked_graphical_limits_preserved",
                  pages=[Page(physical_page=i, image=asset(BASE/f"page-{i}.png"),
                              native=asset(BASE/f"page-{i}.native.txt"), native_status=statuses[i-1])
                         for i in range(1,6)],
                  derivatives=[asset(BASE/"page-3-upright.png"), asset(BASE/"page-3-table-detail.png")],
                  derivative_recipe=["Original page images: pdftoppm -r 144 -png original.pdf page",
                      "Upright page3: PyMuPDF page index2 get_pixmap(Matrix(2,2).prerotate(-90), alpha=False).",
                      "Table detail: upright image pixel rectangle(135,550,1120,835), doubled; rendered through PyMuPDF image-to-PDF coordinates. No source alteration."],
                  passages=passages,
                  corrections=[Correction(physical_page=p,candidate=c,checked_print=t,qualification=q)
                               for p,c,t,q in corrections],
                  dates=[DateStatement(physical_page=p,role=r,date=d,native_anchor=a) for p,r,d,a in dates],
                  unresolved=["The table ratios and all footnote characters under heavy red strike marks are not certified.",
                      "Page2 manual passage recovery and page3 body passages require an independent external review before any stronger transcription status.",
                      "Exact Unicode typography, joined sentence whitespace and seal microlettering are not certified.",
                      "Handwritten identities and signature authenticity are not determined.",
                      "Source effect is stated in the future at acquisition; consolidation and later changes remain unverified.",
                      "Visible ellipses do not supply omitted provisions; the struck heading of 21.07.100 does not alone establish deletion of the entire undisplayed section."])


def verify(review: Review) -> dict[str, object]:
    """Replay native bytes and exact evidence bindings without claiming visual proof."""
    for a in [review.source, review.receipt, review.passages_file, *review.derivatives]:
        assert asset(BASE/a.path) == a
    assert review.source.sha256 == SOURCE_SHA
    receipt=json.loads((BASE/review.receipt.path).read_text())
    assert SOURCE_SHA in json.dumps(receipt)
    natives={}
    with pymupdf.open(BASE/review.source.path) as d:
        assert len(d)==5
        for p in review.pages:
            assert asset(BASE/p.native.path)==p.native and asset(BASE/p.image.path)==p.image
            text=d[p.physical_page-1].get_text("text",sort=False,flags=195).encode()
            assert text==(BASE/p.native.path).read_bytes()
            natives[p.physical_page]=text.decode()
    assert sum(p.native.size_bytes for p in review.pages)==4465
    assert natives[2]=="" and review.pages[1].native_status=="empty_despite_visible_text"
    raw=(BASE/review.passages_file.path).read_bytes()
    for p in review.passages:
        assert raw[p.start:p.end].decode()==p.text
        assert p.image_path==f"page-{p.physical_page}.png" and (BASE/p.image_path).is_file()
    assert {p.physical_page for p in review.passages}=={1,2,3,4,5}
    for c in review.corrections:
        assert c.candidate in natives[c.physical_page] and c.checked_print in raw.decode()
    for date in review.dates:
        assert date.native_anchor in natives[date.physical_page]
    return {"status":"passed","physical_pages_viewed":5,"native_bytes":4465,
            "manual_passage_blocks":len(review.passages),"bounded_print_corrections":5,
            "date_statements":7,"full_transcription_certified":False,
            "table_ratios_certified":False,"legal_currentness":"not_verified"}


def write_new(path: Path, text: str) -> None:
    """Write atomically once, refusing to overwrite frozen files."""
    assert not path.exists(),path
    temporary=path.with_name(path.name+".tmp")
    temporary.write_text(text,encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    """Create the review once or verify its frozen file inventory offline."""
    parser=argparse.ArgumentParser();parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    if args.verify:
        manifest=Manifest.model_validate_json((BASE/"MANIFEST.json").read_bytes())
        paths=sorted(p.relative_to(BASE).as_posix() for p in BASE.rglob("*") if p.is_file()
                     and p.name not in ["MANIFEST.json","MANIFEST.schema.json"]
                     and "__pycache__" not in p.parts)
        assert paths==sorted(a.path for a in manifest.files)
        for a in manifest.files: assert asset(BASE/a.path)==a
        review=Review.model_validate_json((BASE/"SOURCE_QA.json").read_bytes())
        jsonschema.validate(review.model_dump(mode="json"),json.loads((BASE/"SOURCE_QA.schema.json").read_text()))
    else:
        review=build()
    result=verify(review)
    if not args.verify:
        write_new(BASE/"SOURCE_QA.json",review.model_dump_json(indent=2)+"\n")
        write_new(BASE/"SOURCE_QA.schema.json",json.dumps(Review.model_json_schema(),indent=2)+"\n")
        write_new(BASE/"README.md","---\ntitle: Grand Junction Ordinance 5340 source review\nlegal_currentness: not_verified\n---\n\n"
                  "Read [the checked passages](REVIEWED_PASSAGES.md) alongside [the original PDF](original.pdf). "
                  "All five pages were directly inspected. Native page 2 is empty despite visible text; "
                  "page 3 OCR is largely unusable and its physical orientation is sideways. The review recovers "
                  "bounded passages and preserves their visible strikes, while leaving heavily crossed table "
                  "ratios and exact footnote characters uncertified. It does not create a consolidated code.\n\n"
                  "The printed effective date is October 5, 2026, after capture on September 11. Source-stated "
                  "introduction, adoption, publication, certification and effectiveness are recorded separately. "
                  "Current applicability, subsequent changes and execution authenticity remain unverified.\n\n"
                  "The copied access receipt belongs to the separately preserved directed-gap audit. Its "
                  "event-relative paths describe that historical capture and are not promised as local files here. "
                  "Source and native bytes are unchanged; this review is candidate-aware, not an external blind pass.\n\n"
                  "Run `PYTHONDONTWRITEBYTECODE=1 python build_review.py --verify` with Python 3.11+, "
                  "Pydantic 2, jsonschema and PyMuPDF 1.28.2. The check verifies the inventory, native replay, "
                  "passage offsets, page/image bindings, printed-correction candidate anchors and date anchors. "
                  "It cannot mechanically prove the manually read words or strike extents. Do not run with -O. "
                  "Keep the manifest hash separately.\n")
        manifest=Manifest(files=[asset(p) for p in sorted(BASE.rglob("*")) if p.is_file()
                                 and "__pycache__" not in p.parts])
        write_new(BASE/"MANIFEST.json",manifest.model_dump_json(indent=2)+"\n")
        write_new(BASE/"MANIFEST.schema.json",json.dumps(Manifest.model_json_schema(),indent=2)+"\n")
    logging.warning(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
