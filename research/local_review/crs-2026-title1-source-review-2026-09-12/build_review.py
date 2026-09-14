"""Build and verify scoped source QA for three sections in a distinct 2026 PDF."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import pymupdf
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field

from acquire import Receipt, Ref

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = "1c6b021e612929ca8024bebf1022ba45f57aa99712d080c404da8f7f7e90cd1d"
REFERRAL_SHA = "95f7acf502bd6ec9386f47e4ecf0f3c2bc27741736cde3943dda7aa60bf34735"
OLD_META_SHA = "32eaf09373a4a13bbe7735fd681665b8a209abf86455914d6bc1fbd8730439ae"
SOURCE_URL = "https://olls.info/crs/crs2026-title-01.pdf"


class Strict(BaseModel):
    """Reject undeclared review fields."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Page(Strict):
    """An exact uncorrected native page and complete visual rendering."""
    physical_page: int = Field(ge=1, le=6)
    printed_page: str
    native: Ref
    image: Ref
    visual_review: Literal["full_page_candidate_aware"] = "full_page_candidate_aware"
    native_order_note: str


class Region(Strict):
    """A byte-exact native region, classified by visible source role."""
    region_id: str
    physical_page: int = Field(ge=1, le=6)
    role: Literal["footer", "title_editorial_context", "table_of_contents", "part_heading",
                  "section_heading", "statutory_paragraph", "source_history_note",
                  "editors_note", "cross_references", "annotation_heading", "case_annotation",
                  "outside_selected_sections"]
    section_id: str | None
    native_start: int = Field(ge=0)
    native_end: int = Field(gt=0)
    native_sha256: str
    text: str
    text_sha256: str
    visible_location: str
    qualification: str


class Paragraph(Strict):
    """Source paragraph label and ordered fragments, without semantic interpretation."""
    label: str | None
    fragments: list[str] = Field(min_length=1)
    continuation_note: str | None


class Section(Strict):
    """Only one of the three authorized section selections."""
    section_id: Literal["CRS-1-1-101", "CRS-1-1-102", "CRS-1-1-103"]
    heading_region: str
    paragraphs: list[Paragraph]
    source_note_regions: list[str]
    ancillary_regions: list[str]
    scope_note: str


class TokenDelta(Strict):
    """A mechanical token difference, not a legal amendment determination."""
    operation: str
    inherited_tokens: list[str]
    new_pdf_tokens: list[str]


class Comparison(Strict):
    """Cross-edition derived-record comparison with exact raw strings retained."""
    section_id: str
    inherited_meta_line: int
    inherited_meta_line_sha256: str
    inherited_data_version: Literal["2025_official_sgml"]
    inherited_body: str
    inherited_history: str
    new_body_regions: list[str]
    new_history_regions: list[str]
    literal_body_diff: str
    literal_history_diff: str
    body_token_deltas: list[TokenDelta]
    history_token_deltas: list[TokenDelta]
    method: str
    ancillary_qualification: str
    legal_change_determination: Literal["not_assessed"] = "not_assessed"
    original_source_identity_claim: Literal[False] = False


class QA(Strict):
    """Limited source-review result; it cannot authorize legal answers."""
    schema_version: Literal[1] = 1
    source_id: Literal["crs-2026-title1-official-pdf"] = "crs-2026-title1-official-pdf"
    prepared_at: str
    source: Ref
    source_url: Literal[SOURCE_URL] = SOURCE_URL
    acquisition_receipt: Ref
    official_referral: Ref
    publisher_role: Literal["Office of Legislative Legal Services, Colorado General Assembly"]
    representation: Literal["distinct_new_officially_linked_2026_pdf"]
    pdf_page_count: Literal[1008]
    pdf_metadata_claims: dict[str, Any]
    printed_edition: Literal["Colorado Revised Statutes 2026"]
    catalog_session_statement: str
    legal_effective_date: None = None
    date_qualification: str
    pages: list[Page]
    regions: list[Region]
    selected_sections: list[Section]
    comparisons: list[Comparison]
    tables_and_footnotes: str
    typography_qualification: str
    limits: list[str]
    prior_2025_original_custody: Literal["unresolved"] = "unresolved"
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    research_only: Literal[True] = True
    canonical_or_catalog_changes: Literal[False] = False


class Manifest(Strict):
    """Closed byte inventory for this standalone review."""
    schema_version: Literal[1] = 1
    files: list[Ref]
    excluded_files: Literal["FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only"]


def digest(data: bytes) -> str:
    """Return exact SHA-256."""
    return hashlib.sha256(data).hexdigest()


def ref(path: Path) -> Ref:
    """Describe one retained file."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(ROOT).as_posix(), sha256=digest(data), size_bytes=len(data))


def write_new(path: Path, data: bytes) -> None:
    """Create atomically and never overwrite frozen evidence."""
    if path.exists() or path.is_symlink():
        raise ValueError(f"Refusing replacement: {path}")
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def dump(path: Path, value: Any) -> None:
    """Write an already validated record or generated schema."""
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def deltas(old: str, new: str) -> list[TokenDelta]:
    """Compare word/punctuation sequences without altering retained source strings."""
    left = re.findall(r"\w+|[^\w\s]", old, flags=re.UNICODE)
    right = re.findall(r"\w+|[^\w\s]", new, flags=re.UNICODE)
    return [TokenDelta(operation=op, inherited_tokens=left[a:b], new_pdf_tokens=right[c:d])
            for op, a, b, c, d in difflib.SequenceMatcher(a=left, b=right, autojunk=False).get_opcodes()
            if op != "equal"]


def line_diff(old: str, new: str) -> str:
    """Preserve a literal line comparison, including the different extraction layout."""
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                      fromfile="inherited_2025_claim", tofile="new_2026_pdf"))


def build() -> None:
    """Build the fixed three-section source QA from directly inspected pages."""
    native = {n: (ROOT / f"native/page-{n:04}.txt").read_bytes() for n in range(1, 7)}
    regions: list[Region] = []

    def region(rid: str, page: int, start: int, end: int, role: str, sid: str | None,
               location: str, note: str) -> None:
        piece = native[page][start:end]
        regions.append(Region(region_id=rid, physical_page=page, role=role, section_id=sid,
                              native_start=start, native_end=end, native_sha256=digest(native[page]),
                              text=piece.decode("utf-8"), text_sha256=digest(piece),
                              visible_location=location, qualification=note))

    for n in range(1, 7):
        region(f"P{n}-FOOTER", n, 0, 60, "footer", None, "Bottom centered three-line footer",
               "Native extraction emits this footer first; visual page order puts it last.")
    for n in (1, 2, 3):
        region(f"P{n}-CONTEXT", n, 60, len(native[n]),
               "title_editorial_context" if n == 1 else "table_of_contents", None,
               "Complete page body above footer",
               "Frontmatter/catalog context only. No other statute is admitted. Page3 uses two columns; "
               "native text follows the left column then the right, not alternating rows.")
    region("P4-CATALOG", 4, 60, 680, "table_of_contents", None, "Upper two-column continuation",
           "Part2 and Part3/4 catalog entries precede the distinct substantive Part1 heading below.")
    region("P4-PART1", 4, 680, 724, "part_heading", None, "Centered heading below catalog",
           "Substantive Part1 heading; do not confuse with table-of-contents occurrences.")
    specs = [
        ("S101-H", 4, 724, 752, "section_heading", "101", "Bold heading", ""),
        ("S101-B", 4, 752, 937, "statutory_paragraph", "101", "Single unnumbered paragraph", ""),
        ("S101-SOURCE", 4, 937, 1017, "source_history_note", "101", "Source note below paragraph", "Historical dates only."),
        ("S101-EDITOR", 4, 1017, 1109, "editors_note", "101", "Editor's note below source note", "Ancillary editorial text, not statutory body."),
        ("S102-H", 4, 1109, 1139, "section_heading", "102", "Bold heading near lower page", ""),
        ("S102-B1A", 4, 1139, 1639, "statutory_paragraph", "102", "Bottom paragraph labeled(1)", "Continues at physical5 first body line; footer is excluded."),
        ("S102-B1B", 5, 60, 172, "statutory_paragraph", "102", "First two body lines", "Continuation of(1), not a new unlabeled paragraph."),
        ("S102-B2", 5, 172, 646, "statutory_paragraph", "102", "Paragraph labeled(2)", ""),
        ("S102-SOURCE", 5, 646, 844, "source_history_note", "102", "Source note following(2)", "Historical amendment/effectiveness statements, not a2026 effective date."),
        ("S102-EDITOR", 5, 844, 936, "editors_note", "102", "Editor's note", "Ancillary editorial text."),
        ("S102-XREF", 5, 936, 1128, "cross_references", "102", "Cross references above103 heading", "Respectively attaches17→general,32→primary,5→congressional vacancy in printed order; references are not resolved here."),
        ("S103-H", 5, 1128, 1178, "section_heading", "103", "Bold heading below cross references", ""),
        ("S103-B1", 5, 1178, 1401, "statutory_paragraph", "103", "Paragraph labeled(1)", ""),
        ("S103-B2", 5, 1401, 1714, "statutory_paragraph", "103", "Paragraph labeled(2)", ""),
        ("S103-B3", 5, 1714, 1887, "statutory_paragraph", "103", "Paragraph labeled(3)", ""),
        ("S103-SOURCE", 5, 1887, 2035, "source_history_note", "103", "Bottom source note", "Ancillary material continues on physical6."),
        ("S103-EDITOR", 6, 60, 152, "editors_note", "103", "First body paragraph", "Continues103 ancillary material; not part of104."),
        ("S103-ANN-H", 6, 152, 164, "annotation_heading", "103", "Centered ANNOTATION heading", "Separate commentary label."),
        ("S103-ANN", 6, 164, 452, "case_annotation", "103", "Two-column annotation above104", "Read full left column then right. Bold first sentence ends candidate petitions. Remaining text and Griswold v. Ferrigno Warren citation are commentary, not statutory body or independently verified case holding."),
    ]
    for rid, page, start, end, role, sid, location, note in specs:
        region(rid, page, start, end, role, f"CRS-1-1-{sid}", location, note)
    region("P6-OUTSIDE", 6, 452, len(native[6]), "outside_selected_sections", None,
           "Section104 heading and following body to footer",
           "Visible/native custody only.104and later sections are outside this review's selected records.")
    regions.sort(key=lambda r: (r.physical_page, r.native_start))
    sections = [
        Section(section_id="CRS-1-1-101", heading_region="S101-H",
                paragraphs=[Paragraph(label=None, fragments=["S101-B"], continuation_note=None)],
                source_note_regions=["S101-SOURCE"], ancillary_regions=["S101-EDITOR"],
                scope_note="Heading/body/source/editor note on physical4."),
        Section(section_id="CRS-1-1-102", heading_region="S102-H",
                paragraphs=[Paragraph(label="(1)", fragments=["S102-B1A", "S102-B1B"],
                                      continuation_note="Physical4 bottom continues on5 before(2)."),
                            Paragraph(label="(2)", fragments=["S102-B2"], continuation_note=None)],
                source_note_regions=["S102-SOURCE"], ancillary_regions=["S102-EDITOR", "S102-XREF"],
                scope_note="Heading/body on4–5; source/editor/cross-reference notes on5."),
        Section(section_id="CRS-1-1-103", heading_region="S103-H",
                paragraphs=[Paragraph(label=f"({i})", fragments=[f"S103-B{i}"], continuation_note=None)
                            for i in (1, 2, 3)], source_note_regions=["S103-SOURCE"],
                ancillary_regions=["S103-EDITOR", "S103-ANN-H", "S103-ANN"],
                scope_note="Body/source on5; editor note and complete two-column case annotation on6."),
    ]
    by_id = {r.region_id: r for r in regions}
    old_rows = []
    with (ROOT / "reference/inherited/prototype/inputs/meta.jsonl").open("rb") as stream:
        for i, line in enumerate(stream, 1):
            if i > 3:
                break
            old_rows.append((i, line, json.loads(line)))
    comparisons = []
    for section, (number, line, old) in zip(sections, old_rows, strict=True):
        assert old["id"] == section.section_id
        body_ids = [rid for paragraph in section.paragraphs for rid in paragraph.fragments]
        new_body = "".join(by_id[rid].text for rid in body_ids)
        new_history = "".join(by_id[rid].text for rid in section.source_note_regions)
        comparisons.append(Comparison(
            section_id=section.section_id, inherited_meta_line=number,
            inherited_meta_line_sha256=digest(line), inherited_data_version=old["data_version"],
            inherited_body=old["full_text"], inherited_history=old["history_note"],
            new_body_regions=body_ids, new_history_regions=section.source_note_regions,
            literal_body_diff=line_diff(old["full_text"], new_body),
            literal_history_diff=line_diff(old["history_note"], new_history),
            body_token_deltas=deltas(old["full_text"], new_body),
            history_token_deltas=deltas(old["history_note"], new_history),
            method="Literal unified line diff plus mechanical Unicode word/punctuation token delta "
            "(regex \\w+|[^\\w\\s], no casefold or source rewrite). Empty token deltas describe only "
            "these compared strings; they do not establish section/edition equivalence or original custody.",
            ancillary_qualification="2026 editor/cross-reference/case notes remain separate regions. "
            "They are not present in the selected inherited full_text/history_note fields; this may "
            "reflect extraction omission, not a2026 legislative addition. Original2025 bytes remain missing.",
        ))
    soup = BeautifulSoup((ROOT / "reference/events/E009/body.bin").read_bytes(), "html.parser")
    text = soup.select_one(".region-content").get_text(" ", strip=True)
    statement = text.split("All Titles,", 1)[0].strip()
    with pymupdf.open(ROOT / "events/E001/body.bin") as doc:
        qa = QA(
            prepared_at=datetime.now(timezone.utc).isoformat(), source=ref(ROOT / "events/E001/body.bin"),
            acquisition_receipt=ref(ROOT / "events/E001.json"),
            official_referral=ref(ROOT / "reference/events/E009/body.bin"),
            publisher_role="Office of Legislative Legal Services, Colorado General Assembly",
            representation="distinct_new_officially_linked_2026_pdf", pdf_page_count=len(doc),
            pdf_metadata_claims=doc.metadata, printed_edition="Colorado Revised Statutes 2026",
            catalog_session_statement=statement,
            date_qualification="Printed2026 edition and catalog session coverage are source claims. "
            "PDF creation/modification metadata are not adoption/effective dates. Historical source-note "
            "dates remain literal notes; no operative2026 section date is assigned.",
            pages=[Page(physical_page=n, printed_page=f"-{n}-",
                        native=ref(ROOT / f"native/page-{n:04}.txt"),
                        image=ref(ROOT / f"pages/page-{n:04}.png"),
                        native_order_note="Footer native bytes0–60 precede body; visually footer is last. "
                        "Preserve native uncorrected, use explicit regions/order for selected paragraphs.")
                   for n in range(1, 7)], regions=regions, selected_sections=sections,
            comparisons=comparisons,
            tables_and_footnotes="Pages1–4 contain contents listings, including two-column layouts3–4; "
            "these are catalogs, not statutory paragraphs. No fee/data table or numbered footnote "
            "was observed within the first3 substantive selections. Source/editor/cross-reference notes "
            "and the103case annotation are retained in full. No referenced external provision or case opened.",
            typography_qualification="Full pages1–6 viewed after native/old-record context; not blind. "
            "Bold headings/source labels and annotation's bold first sentence are visible. No strikeout, "
            "handwritten alteration, signature or form fill observed in selected regions. Exact Unicode "
            "codepoints come from native bytes, not visual character-encoding certification. No OCR correction.",
            limits=["1008 is PDF structural pagecount; only complete physical1–6 were visually reviewed and "
                    "have retained native text. Page7native was briefly read to locate the selection boundary; "
                    "no page7review/annotation and no page8–1008inspection is claimed.",
                    "Only three section selections; contextual catalogs and104tail do not expand admission.",
                    "One public GET/one target/no redirects,3,967,221response bytes. No HTML source download.",
                    "The frozen2025custody gap remains unchanged. No canonical intake/catalog/index/control update."],
        )
    dump(ROOT / "SOURCE_QA.json", qa.model_dump())
    dump(ROOT / "SOURCE_QA.schema.json", QA.model_json_schema())


def freeze() -> None:
    """Create a complete immutable byte inventory after notes are finalized."""
    entries = [ref(p) for p in sorted(ROOT.rglob("*")) if p.is_file()]
    model = Manifest(files=entries,
                     excluded_files="FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only")
    dump(ROOT / "FINAL_MANIFEST.json", model.model_dump())
    dump(ROOT / "FINAL_MANIFEST.schema.json", Manifest.model_json_schema())


def verify() -> None:
    """Verify exact source, referral, page/native offsets, ordered selections and comparisons."""
    if sys.flags.optimize:
        raise ValueError("Run without -O/PYTHONOPTIMIZE")
    qa = QA.model_validate_json((ROOT / "SOURCE_QA.json").read_text())
    manifest = Manifest.model_validate_json((ROOT / "FINAL_MANIFEST.json").read_text())
    assert json.loads((ROOT / "SOURCE_QA.schema.json").read_text()) == QA.model_json_schema()
    assert json.loads((ROOT / "FINAL_MANIFEST.schema.json").read_text()) == Manifest.model_json_schema()
    expected = {r.path for r in manifest.files}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()
              and p not in {ROOT / "FINAL_MANIFEST.json", ROOT / "FINAL_MANIFEST.schema.json"}}
    assert actual == expected and len(expected) == len(manifest.files)
    for value in manifest.files:
        path = ROOT / value.path
        assert not path.is_symlink() and path.resolve().is_relative_to(ROOT)
        assert ref(path) == value
    source = ROOT / qa.source.path
    assert ref(source) == qa.source and qa.source.sha256 == SOURCE_SHA
    assert source.read_bytes().startswith(b"%PDF-") and source.read_bytes().rstrip().endswith(b"%%EOF")
    receipt = Receipt.model_validate_json((ROOT / qa.acquisition_receipt.path).read_text())
    assert receipt.body == qa.source and receipt.requested_url == receipt.observed_response_url == SOURCE_URL
    assert receipt.http_status == 200 and receipt.curl_exit == 0 and receipt.tls_verification_result == 0
    assert receipt.response_complete and not receipt.redirect_location
    assert qa.official_referral.sha256 == REFERRAL_SHA
    soup = BeautifulSoup((ROOT / qa.official_referral.path).read_bytes(), "html.parser")
    anchor = soup.find("a", href=SOURCE_URL)
    assert anchor and anchor.get_text(strip=True) == "PDF"
    assert "Title 1" in anchor.find_parent("tr").get_text(" ", strip=True)
    assert [p.physical_page for p in qa.pages] == list(range(1, 7))
    by_id = {r.region_id: r for r in qa.regions}
    assert len(by_id) == len(qa.regions)
    with pymupdf.open(source) as doc:
        assert len(doc) == qa.pdf_page_count == 1008 and not doc.is_repaired and not doc.is_encrypted
        assert doc.metadata == qa.pdf_metadata_claims
        for page in qa.pages:
            data = doc[page.physical_page - 1].get_text(flags=195, sort=False).encode()
            assert data == (ROOT / page.native.path).read_bytes()
            regions = [r for r in qa.regions if r.physical_page == page.physical_page]
            position = 0
            for region in regions:
                assert region.native_start == position < region.native_end <= len(data)
                piece = data[region.native_start:region.native_end]
                assert region.native_sha256 == digest(data)
                assert region.text.encode() == piece and region.text_sha256 == digest(piece)
                position = region.native_end
            assert position == len(data)
    assert [s.section_id for s in qa.selected_sections] == [f"CRS-1-1-{i}" for i in (101, 102, 103)]
    assert [p.label for p in qa.selected_sections[0].paragraphs] == [None]
    assert [p.label for p in qa.selected_sections[1].paragraphs] == ["(1)", "(2)"]
    assert [p.label for p in qa.selected_sections[2].paragraphs] == ["(1)", "(2)", "(3)"]
    assert qa.selected_sections[1].paragraphs[0].fragments == ["S102-B1A", "S102-B1B"]
    meta = ROOT / "reference/inherited/prototype/inputs/meta.jsonl"
    assert digest(meta.read_bytes()) == OLD_META_SHA
    old_lines = []
    with meta.open("rb") as stream:
        for _ in range(3):
            old_lines.append(next(stream))
    for section, comparison, line in zip(qa.selected_sections, qa.comparisons, old_lines, strict=True):
        old = json.loads(line)
        assert section.section_id == comparison.section_id == old["id"]
        assert comparison.inherited_meta_line_sha256 == digest(line)
        assert comparison.inherited_body == old["full_text"] and comparison.inherited_history == old["history_note"]
        ids = [r for para in section.paragraphs for r in para.fragments]
        assert ids == comparison.new_body_regions
        assert all(by_id[r].section_id == section.section_id and by_id[r].role == "statutory_paragraph"
                   for r in ids)
        assert all(by_id[r].section_id == section.section_id for r in
                   [section.heading_region, *section.source_note_regions, *section.ancillary_regions])
        body = "".join(by_id[r].text for r in ids)
        history = "".join(by_id[r].text for r in section.source_note_regions)
        assert comparison.literal_body_diff == line_diff(old["full_text"], body)
        assert comparison.literal_history_diff == line_diff(old["history_note"], history)
        assert comparison.body_token_deltas == deltas(old["full_text"], body)
        assert comparison.history_token_deltas == deltas(old["history_note"], history)


if __name__ == "__main__":
    if sys.argv[1:] == ["--build"]:
        build()
    elif sys.argv[1:] == ["--freeze"]:
        freeze()
        verify()
    elif sys.argv[1:] == ["--verify"]:
        verify()
    else:
        raise SystemExit("Use --build, --freeze or --verify")
    sys.stdout.write("PASS: distinct2026PDF, six reviewed pages, three source-only selections.\n")
