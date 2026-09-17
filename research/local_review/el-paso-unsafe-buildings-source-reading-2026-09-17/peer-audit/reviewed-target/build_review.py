"""Bind a candidate-aware visual review without changing publisher or canonical bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import jsonschema
import pymupdf
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent
SHA = "86eed9d885a9cec1cb01528318f66f8eed525ddb0860655a1983865bfa196d00"


class Strict(BaseModel):
    """Reject unknown fields and scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Identify exact retained bytes relative to this package."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class Finding(Strict):
    """A bounded extraction defect or preserved source observation."""

    id: str
    page: int = Field(ge=1, le=8)
    location: str
    kind: Literal["extraction_error", "source_anomaly", "unresolved", "structure"]
    impact: Literal["substantive", "metadata", "cosmetic", "none"]
    candidate_excerpt: str | None
    candidate_character_start: int | None
    candidate_character_end: int | None
    image_supported_reading: str
    qualification: str


class Page(Strict):
    """Complete page identity and actual inspection scope."""

    physical_page: int = Field(ge=1, le=8)
    image: Asset
    native_text_characters: int
    directly_displayed: Literal[True]
    scope: str
    remaining_uncertainties: list[str]


class Review(Strict):
    """Research findings, explicitly not a current-law or full-glyph certificate."""

    source_id: Literal["el-paso-unsafe-buildings-18-03-sd011"]
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    source: Asset
    canonical_record: Asset
    native_candidate: Asset
    corrected_reading: Asset
    inspected_pages: list[Page]
    findings: list[Finding]
    reviewer: Literal["Atlas"]
    review_date: Literal["2026-09-17"]
    status: Literal["candidate_defects_confirmed_research_derivative_pending_peer_review"]
    review_method: str
    acquisition_method: Literal["received_review_package"]
    original_http_independently_verified: Literal[False]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    limitations: list[str]


def asset(path: str) -> Asset:
    """Hash one local asset."""
    data = (ROOT / path).read_bytes()
    return Asset(path=path, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def write_once(path: Path, data: bytes) -> None:
    """Preserve any prior output instead of overwriting it."""
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing changed existing output: {path}")
        return
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build() -> Review:
    """Validate exact input identity and construct the bounded review."""
    original = asset("inputs/original.pdf")
    assert original.sha256 == SHA
    doc = pymupdf.open(ROOT / original.path)
    assert len(doc) == 8
    native = [page.get_text() for page in doc]
    expected = "".join(
        f"=== PHYSICAL PDF PAGE {index + 1} ===\n{text}"
        for index, text in enumerate(native)
    )
    assert (ROOT / "native-all.txt").read_text() == expected
    record = json.loads((ROOT / "inputs/canonical-record.jsonl").read_text())
    assert record["sha256"] == SHA and record["size_bytes"] == original.size_bytes
    assert record["acquisition_method"] == "received_review_package"
    findings: list[Finding] = []

    def add(page: int, location: str, kind: str, impact: str, excerpt: str | None,
            reading: str, note: str = "") -> None:
        """Bind a finding to its exact native excerpt when one survives."""
        start = native[page - 1].index(excerpt) if excerpt is not None else None
        end = start + len(excerpt) if start is not None and excerpt is not None else None
        findings.append(Finding(
            id=f"EP-UNSAFE-ATLAS-{len(findings) + 1:03d}", page=page, location=location,
            kind=kind, impact=impact, candidate_excerpt=excerpt,
            candidate_character_start=start, candidate_character_end=end,
            image_supported_reading=reading, qualification=note,
        ))

    add(1, "title", "extraction_error", "cosmetic", "ORDINANCE N0. 18-03",
        "ORDINANCE NO. 18-03")
    add(1, "first WHEREAS", "extraction_error", "substantive",
        native[0].split("WHEREAS,", 1)[1].split("\x00WHEREAS", 1)[0],
        "Full first recital is readable in the image and transcribed in CORRECTED_READING.md.",
        "Words and statutory citation are split internally; a NUL separates recitals. "
        "An automated whitespace join alone cannot safely reconstruct all words.")
    add(1, "second WHEREAS", "extraction_error", "substantive",
        "unincoroorated \n. \nareas of El Paso \n---- Countv· \n- ------,,. \nand",
        "unincorporated areas of El Paso County; and")
    add(1, "fourth WHEREAS", "extraction_error", "substantive",
        native[0].split("rubbish and trash ", 1)[1].split("WHEREAS, pursuant", 1)[0],
        "upon adjacent or nearby properties; and",
        "The rubbish/trash recital itself is in this unsafe-buildings source; do not replace it.")
    add(1, "BE IT FURTHER RESOLVED", "extraction_error", "substantive",
        native[0].split("BE IT FURTHER RESOLVED,", 1)[1].split("Ch\nuck Broerman", 1)[0],
        "The authorization sentence runs through 'on behalf of the' and continues on page2.",
        "Preserve Darryl Glenn or Mark Waller alternatives and page continuation; "
        "stamp is not part of the sentence. Full visible wording is in corrected reading.")
    add(1, "recorder stamp", "extraction_error", "metadata",
        native[0].split("Ch\nuck Broerman", 1)[1],
        "Chuck Broerman; El Paso County, CO; 11/22/2017 09:11:15 AM; "
        "Doc $0.00; Rec $0.00; 8 Pages; 217142026.",
        "Stamp text repeats and is garbled in native extraction. Barcode present, not decoded.")
    add(2, "signature and attestation blocks", "extraction_error", "metadata", None,
        "ATTEST; By; Chuck Broerman / Clerk and Recorder; BOARD OF COUNTY COMMISSIONERS "
        "OF EL PASO COUNTY, COLORADO; By; Darryl Glenn / President; two signatures and seal.",
        "Blocks omitted from candidate. Printed names do not certify signature identity. "
        "Complete overprinted seal text unresolved.")
    add(3, "recitals and Board definition", "extraction_error", "cosmetic", "safeiy",
        "safety", "Also Couniy→County and spurious semicolon in County; Commissioners. "
        "Joined interword spaces are restored only in derivative.")
    add(3, "Section1 purpose", "source_anomaly", "none",
        "not repaired or removed, fire hazards,",
        "not repaired or removed, fire hazards,",
        "Apparent missing predicate is printed in source and retained without completion.")
    add(4, "4.4 Dilapidated", "extraction_error", "cosmetic", "'.vear", "wear")
    add(4, "4.8 Structure", "source_anomaly", "none", "upon real upon real property",
        "upon real upon real property", "Repeated words are printed, not an extraction error.")
    add(4, "4.9 hierarchy", "structure", "substantive", None,
        "Items a-c are indented below item2; retain all and/or connectors and subordinate scope.")
    add(4, "5.2 named-act exemption", "extraction_error", "substantive",
        'Surface Coal ~...1ining Recla..Tiation Act," pursuant to section 34-33-101, ct seq.,',
        'Surface Coal Mining Reclamation Act," pursuant to section 34-33-101, et seq.,',
        "The 'shall not apply' exemption must remain linked to this named act and citation.")
    add(5, "Section7 title and7.2", "extraction_error", "cosmetic", "Vioiation",
        "Violation", "Also t..he→the and tlie→the in7.2; thirty/ten-day values remain source-supported.")
    add(6, "8.3 hearing evidence", "extraction_error", "cosmetic", "aiong wiih", "along with",
        "Pianning→Planning in same sentence; no change to shall/may or evidence scope.")
    add(6, "9.6 surcharge", "extraction_error", "substantive", "surcharge often dollars",
        "surcharge of ten dollars", "Interword join obscures the monetary phrase.")
    add(6, "Section10", "source_anomaly", "none", "an execution determination",
        "an execution determination", "Source says execution here, executive elsewhere; retained.")
    add(7, "11.2 cost-recovery condition", "extraction_error", "substantive",
        native[6].split("11.2 ", 1)[1].split("11.3 ", 1)[0],
        "If the owner fails to pay the cost of securing or removal within ten (10) calendar "
        "days after the Director mails an invoice for such cost, the whole cost thereof, "
        "including five percent (5%) for inspection and incidental costs in connection "
        "therewith, may be assessed upon the lot, parcel or tract ...",
        "Displayed line is legible but extraction is destroyed. Ellipsis here indicates a "
        "finding excerpt, not a complete provision; corrected reading retains the entire "
        "paragraph including lien priority exceptions.")
    add(7, "11.3 collection", "extraction_error", "substantive", "ten percent (I0%)",
        "ten percent (10%)", "Other corruption includes generai/inciuding/arid/propert\"y/"
        "assessn1ents/tJ1is. Corrected paragraph preserves thirty-day trigger and collection terms.")
    add(7, "12.2 warrant affidavit", "extraction_error", "cosmetic", "factuai basis",
        "factual basis", "Also inciuding/reasonabiy/buiiding; all listed predicates retained.")
    add(8, "execution and certification blocks", "extraction_error", "metadata", None,
        "Two signature/name-title blocks, seal and certification appear below the date; "
        "candidate stops at Colorado Springs, Colorado.",
        "Printed Darryl Glenn/President and Chuck Broerman/County Clerk & Recorder are "
        "separate from signature presence. Do not infer obscured certification words.")
    add(8, "seal-overprinted certification", "unresolved", "metadata", None,
        "Certification text is partly obscured by seal; bracketed gaps are retained in reading.",
        "No exact full seal wording or handwriting identity claim.")
    add(8, "Section15 dates", "structure", "substantive", None,
        "Source states first reading October24,2017; full publication November1,2017; "
        "adopted without amendment November21,2017; intended republication November29,2017; "
        "shall take effect January1,2018.",
        "Source date assertions only. This review does not prove republication occurred, "
        "municipality opt-in, or the amendment/repeal chain/current applicability.")
    pages = [Page(
        physical_page=i + 1, image=asset(f"pages/page-{i + 1}.png"),
        native_text_characters=len(text), directly_displayed=True,
        scope="All visible page regions inspected; substantive wording compared with native text.",
        remaining_uncertainties=(
            ["Exact handwriting identity and complete seal text unverified."] if i == 1 else
            ["Seal-overprinted certification words, full seal text and signature identity unresolved."]
            if i == 7 else ["Upper-left handwriting exact identity unverified."] if i == 0 else []
        ),
    ) for i, text in enumerate(native)]
    return Review(
        source_id=record["record_id"], authority_id="CO-COUNTY-EL_PASO", source=original,
        canonical_record=asset("inputs/canonical-record.jsonl"),
        native_candidate=asset("native-all.txt"), corrected_reading=asset("CORRECTED_READING.md"),
        inspected_pages=pages, findings=findings, reviewer="Atlas", review_date="2026-09-17",
        status="candidate_defects_confirmed_research_derivative_pending_peer_review",
        review_method="Direct display of all8 Poppler120dpi PNGs; direct240dpi page8 crop; "
                      "comparison against native PyMuPDF1.28.2 text. Candidate-aware, not blind.",
        acquisition_method="received_review_package", original_http_independently_verified=False,
        legal_currentness="not_verified", answer_safe=False,
        limitations=[
            "Research reading with explicit unresolved regions, not exact glyph/layout reproduction.",
            "All original PDF bytes and canonical metadata remain unchanged.",
            "No atomic rules, full-law currentness, legal effect or municipal opt-in are certified.",
            "No external Grok report was consulted before this root review was written.",
            "Candidate has native text on all8pages; presence is not reliable transcription fidelity.",
            "No inventory review promotion is performed by this packet.",
        ],
    )


if __name__ == "__main__":
    review = build()
    schema = Review.model_json_schema()
    data = review.model_dump(mode="json")
    jsonschema.Draft202012Validator(schema).validate(data)
    write_once(ROOT / "REVIEW.schema.json", (json.dumps(schema, indent=2) + "\n").encode())
    write_once(ROOT / "REVIEW.json", (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())
