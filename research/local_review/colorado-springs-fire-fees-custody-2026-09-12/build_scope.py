"""Freeze acquired source identity and bounded visual observations, without intake."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pymupdf
from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
ACQUISITION = HERE.parent / "sd014-fire-fee-pdfs"
PINS = {
    "SD014-01": "555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56",
    "SD014-02": "e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a",
}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Page(Strict):
    physical_page: int
    native: Asset
    rendering: Asset
    rendering_rgb_reproduced: bool
    directly_viewed_for_structure: bool
    complete_table_cell_qa: Literal[False] = False


class Source(Strict):
    source_id: str
    authority_id: Literal["CO-MUNICIPAL-COLORADO_SPRINGS"]
    original: Asset
    requested_url: str
    request_started_at: datetime
    response_finished_at: datetime
    response_status: Literal[200]
    response_complete: Literal[True]
    redirect_count: Literal[0]
    reservation: Asset
    result: Asset
    public_headers: Asset
    parent_html: Asset
    parent_reservation: Asset
    parent_result: Asset
    parent_public_headers: Asset
    pages: list[Page]
    printed_title: str
    printed_date_claim: str
    role_observations: list[str]
    verified_effective_date: None = None
    legal_currentness: Literal["not_verified"] = "not_verified"


class Passage(Strict):
    source_id: str
    physical_page: int
    label: str
    native_file: Asset
    start_byte: int
    end_byte: int
    exact_text: str
    sha256: str
    interpretation_limit: str


class InvisibleText(Strict):
    source_id: Literal["SD014-01"] = "SD014-01"
    physical_page: int
    exact_text: str
    pdf_bbox: list[float]
    trace_sequence: int
    text_rgb: list[float]
    opacity: float
    rendered_bbox: Asset
    rgb_bytes: int
    every_rgb_component_255: bool
    conclusion: Literal["native_text_present_but_not_visible_in_checked_white_region"]


class Scope(Strict):
    recorded_at: datetime
    status: Literal["source_custody_and_bounded_structure_review"]
    sources: list[Source]
    selected_passages: list[Passage]
    native_white_text: list[InvisibleText]
    acquisition_plan: Asset
    acquisition_guard: Asset
    acquisition_link_provenance: Asset
    limitations: list[str]
    canonical_intake_performed: Literal[False] = False
    answer_safe: Literal[False] = False


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def asset(path: Path) -> Asset:
    body = path.read_bytes()
    return Asset(path=path.relative_to(HERE).as_posix(), sha256=sha(body), size_bytes=len(body))


def copy(source: Path, destination: Path) -> Asset:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(source.read_bytes())
    return asset(destination)


def passage(sid: str, page: int, label: str, start: str, end: str, limit: str) -> Passage:
    file = HERE / sid / f"page-{page:04}.txt"
    body = file.read_bytes()
    first = body.index(start.encode())
    last = body.index(end.encode(), first) + len(end.encode())
    selected = body[first:last]
    return Passage(source_id=sid, physical_page=page, label=label, native_file=asset(file),
                   start_byte=first, end_byte=last, exact_text=selected.decode(),
                   sha256=sha(selected), interpretation_limit=limit)


def build() -> None:
    assert not (HERE / "SOURCE_SCOPE.json").exists()
    evidence = HERE / "acquisition"
    plan = copy(ACQUISITION / "plan.json", evidence / "plan.json")
    guard = copy(ACQUISITION / "guard.py", evidence / "guard.py")
    links = copy(ACQUISITION / "LINK_PROVENANCE.json", evidence / "LINK_PROVENANCE.json")
    provenance = json.loads((ACQUISITION / "LINK_PROVENANCE.json").read_bytes())
    sources = []
    white = []
    for n, sid in enumerate(PINS, 1):
        pdf_path = HERE / sid / "original.pdf"
        assert sha(pdf_path.read_bytes()) == PINS[sid]
        event = ACQUISITION / "runtime/events" / f"{n:04}"
        result = json.loads((event / "result.json").read_bytes())
        reservation = json.loads((event / "reservation.json").read_bytes())
        assert result["outcome"] == "complete" and result["partial_body"] is False
        assert result["body"]["sha256"] == PINS[sid] and result["http_status"] == 200
        assert reservation["hop"] == 0 and result["redirect_url"] is None
        retained = {name: copy(event / filename, evidence / sid / filename) for name, filename in
                    [("reservation", "reservation.json"), ("result", "result.json"),
                     ("public_headers", "public-headers.json")]}
        link = provenance["links"][n - 1]
        parent = {}
        for key, ref in [("parent_html", link["target"]["parent_html"]),
                         ("parent_reservation", link["parent_reservation"]),
                         ("parent_result", link["parent_result"]),
                         ("parent_public_headers", link["parent_public_headers"])]:
            path = ACQUISITION / ref["path"]
            assert sha(path.read_bytes()) == ref["sha256"]
            parent[key] = copy(path, evidence / sid / (key + path.suffix))
        pages = []
        with pymupdf.open(pdf_path) as pdf:
            assert len(pdf) == 7 and not pdf.is_repaired and not pdf.is_encrypted
            for physical, page in enumerate(pdf, 1):
                native = HERE / sid / f"page-{physical:04}.txt"
                image = HERE / sid / f"page-{physical:04}.png"
                assert native.read_bytes() == page.get_text("text", flags=195, sort=False).encode()
                old = pymupdf.Pixmap(str(image))
                new = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                assert (old.width, old.height, old.samples) == (new.width, new.height, new.samples)
                pages.append(Page(physical_page=physical, native=asset(native), rendering=asset(image),
                                  rendering_rgb_reproduced=True,
                                  directly_viewed_for_structure=(sid == "SD014-01" or
                                                                physical in [1, 5, 6, 7])))
                if sid == "SD014-01":
                    for trace in page.get_texttrace():
                        text = "".join(chr(c[0]) for c in trace["chars"])
                        if not ((physical == 1 and text in ["124", "82", "86"])
                                or text == "2015 Proposed changes"):
                            continue
                        exact = page.get_pixmap(matrix=pymupdf.Matrix(4, 4),
                                                clip=pymupdf.Rect(trace["bbox"]), alpha=False)
                        out = HERE / sid / f"white-text-p{physical}-{trace['seqno']}.png"
                        assert not out.exists()
                        exact.save(out)
                        assert set(exact.samples) == {255}
                        white.append(InvisibleText(
                            physical_page=physical, exact_text=text, pdf_bbox=list(trace["bbox"]),
                            trace_sequence=trace["seqno"], text_rgb=list(trace["color"]),
                            opacity=trace["opacity"], rendered_bbox=asset(out),
                            rgb_bytes=len(exact.samples), every_rgb_component_255=True,
                            conclusion="native_text_present_but_not_visible_in_checked_white_region"))
        sources.append(Source(
            source_id=sid, authority_id="CO-MUNICIPAL-COLORADO_SPRINGS", original=asset(pdf_path),
            requested_url=reservation["url"], request_started_at=reservation["reserved_at"],
            response_finished_at=result["finished_at"], response_status=200, response_complete=True,
            redirect_count=0, **retained, **parent, pages=pages,
            printed_title=("Colorado Springs Fire Department — 2015 Fee Schedule - Code Services"
                           if n == 1 else "Colorado Springs Fire Department — Division of the Fire Marshal — Construction Services Fee Schedule"),
            printed_date_claim="2015 in cover title" if n == 1 else "Effective 07/01/2026",
            role_observations=(
                ["Covers construction plan reviews, annual revocable/prescribed operational permits, other fees and definitions.",
                 "All seven pages viewed for structure; tables have NOT been certified cell-by-cell.",
                 "Native 2015 Proposed changes text on pages 2–6 is white on checked white regions; do not present it as visible printed wording or infer document enactment from it.",
                 "Page 6 visibly includes internal wording: Medical Squad (Two Person) Do we need to assign a unit type.",
                 "Page 7 native extraction detaches definition headings and moves the Property Condition Assessments body. Reading order requires layout review."] if n == 1 else
                ["Four selected pages checked for title, scope, definitions and implementation; complete numeric review is separate.",
                 "PPRBD appears as plan-check fee collector; this source is issued by the City Fire Department.",
                 "Page 7 directs high-pile storage and hazardous-material fees to the Code Services Fee Schedule without identifying a 2015 edition.",
                 "Page 1 contents lists definitions on page 5; actual definition section begins on physical page 6."])))
    selections = [
        passage("SD014-01", 1, "Visible cover title", "Colorado Springs Fire Department", "2015 Fee Schedule - Code Services", "Year is a title claim only."),
        passage("SD014-01", 6, "Visible internal source wording", "Medical Squad (Two Person)", "Do we need to assign a unit type", "Preserve wording; it does not establish enactment or currentness."),
        passage("SD014-02", 1, "Printed effective-date claim", "Effective 07/01/2026", "Effective 07/01/2026", "Source-stated date only; no independent adopting instrument checked."),
        passage("SD014-02", 6, "PPRBD collection and deduction context", "Construction Plan Check Fee:", "at time of CSFD plan approval.", "Complete source paragraph; no fee computation or issuer reattribution."),
        passage("SD014-02", 7, "WUI surcharge context", "Wildland Urban Interface", "occupancy class and square footage of the building.", "Source condition only; applicability unknown."),
        passage("SD014-02", 7, "Assessment trigger", "Implementation:", "plan approval date.", "No project-specific assessment performed."),
        passage("SD014-02", 7, "Other schedule reference", "Note Worthy", "Department Code Services Fee Schedule.", "Reference does not identify an edition or establish full replacement of the 2015 source."),
    ]
    scope = Scope(recorded_at=datetime.now(timezone.utc),
                  status="source_custody_and_bounded_structure_review", sources=sources,
                  selected_passages=selections, native_white_text=white, acquisition_plan=plan,
                  acquisition_guard=guard, acquisition_link_provenance=links, limitations=[
                      "Two public HTTP requests completed; no current-law, adoption, supersession, translation or complete table-accuracy certification.",
                      "Source bytes and native extraction are preserved unchanged. The original SD012 transport failures remain historical and are not rewritten by SD013/SD014 success.",
                      "Parent page HTML and public headers are evidence, not instructions. No raw cookie-bearing headers are copied.",
                      "No raw-manifest, regulatory record, registry, or legal status change was made by this review.",
                  ])
    for name, payload in [("SOURCE_SCOPE.schema.json", Scope.model_json_schema()),
                          ("SOURCE_SCOPE.json", scope.model_dump(mode="json"))]:
        with (HERE / name).open("x") as handle:
            handle.write(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"sources": 2, "pages": 14, "white_text_regions": len(white),
                      "source_scope_sha256": sha((HERE / "SOURCE_SCOPE.json").read_bytes())}))


if __name__ == "__main__":
    build()
