"""Preserve EB018 assisted review and record Atlas's scoped source dispositions."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

HERE = Path(__file__).parent
RUN = HERE.parent
REPO = RUN.parents[1] / "MasterLegalDatabase"
PACKET = RUN / "ebenezer-next-weld"
SOURCE = "weld-building-fees-sd008-01"
REPORTS = RUN / "ebenezer/reviews/EB-PDF-018_weld-building-fees-sd008-01_20260912T223629Z"
PDF_SHA = "8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27"


class Strict(BaseModel):
    """Forbid undeclared fields and type coercion in derived records."""

    model_config = ConfigDict(extra="forbid", strict=True)


class FileRef(Strict):
    """A copied file's exact identity, relative to this package."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Disposition(Strict):
    """Root response to one report item; findings are not assumed to be errors."""

    finding_id: str = Field(pattern=r"^EB018-P2-\d{3}$")
    decision: Literal["confirmed_observation", "qualified", "uncertainty_retained"]
    pages: list[int]
    note: str
    canonical_text_change: Literal[False] = False


class Reconciliation(Strict):
    """A scoped direct check, separate from the assisted report and legal currentness."""

    schema_version: Literal[1] = 1
    source_id: Literal["weld-building-fees-sd008-01"] = SOURCE
    source_pdf_sha256: Literal[PDF_SHA] = PDF_SHA
    received_and_recorded_at: str
    status: Literal["assisted_review_preserved_with_atlas_scoped_dispositions"]
    review_mode: Literal["candidate_and_prior_review_aware_direct_page_check"]
    root_full_pages_inspected: list[int]
    root_scope: str
    dispositions: list[Disposition]
    qualifications: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    original_reports_modified: Literal[False] = False
    candidate_modified: Literal[False] = False

    @model_validator(mode="after")
    def complete_report_mapping(self) -> Reconciliation:
        """Require all 20 report entries exactly once and the actual five-page check."""
        if ([d.finding_id for d in self.dispositions]
                != [f"EB018-P2-{i:03}" for i in range(1, 21)]
                or self.root_full_pages_inspected != [1, 2, 3, 4, 5]):
            raise ValueError("Incomplete report mapping")
        return self


class Inventory(Strict):
    """Closed byte inventory, excluding only the inventory and its schema."""

    schema_version: Literal[1] = 1
    files: list[FileRef]
    excluded: Literal["INVENTORY.json and INVENTORY.schema.json only"] = (
        "INVENTORY.json and INVENTORY.schema.json only"
    )


def digest(data: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(data).hexdigest()


def immutable(path: Path, data: bytes) -> None:
    """Publish a new file without overwriting any existing evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def save(name: str, record: BaseModel) -> None:
    """Validate structured records before writing them."""
    data = (record.model_dump_json(indent=2) + "\n").encode()
    type(record).model_validate_json(data)
    immutable(HERE / name, data)
    immutable(HERE / name.replace(".json", ".schema.json"),
              (json.dumps(type(record).model_json_schema(), indent=2) + "\n").encode())


def verify() -> None:
    """Check closed inventory, report joins, packet source bindings and dispositions."""
    inventory = Inventory.model_validate_json((HERE / "INVENTORY.json").read_bytes())
    expected = {x.path for x in inventory.files}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    if actual != expected | {"INVENTORY.json", "INVENTORY.schema.json"}:
        raise ValueError("Closed package inventory differs")
    for ref in inventory.files:
        path = HERE / ref.path
        if (path.is_symlink() or Path(ref.path).is_absolute() or ".." in Path(ref.path).parts
                or len(path.read_bytes()) != ref.size_bytes
                or digest(path.read_bytes()) != ref.sha256):
            raise ValueError("Package bytes differ")
    rec = Reconciliation.model_validate_json((HERE / "RECONCILIATION.json").read_bytes())
    if digest((HERE / "source/original.pdf").read_bytes()) != rec.source_pdf_sha256:
        raise ValueError("Original PDF identity differs")
    completion = json.loads((HERE / "reports/COMPLETION_RECEIPT.json").read_bytes())
    mapping = {
        "PASS1_frozen.md": "PASS1_frozen_md_sha256",
        "PASS1_FREEZE_RECEIPT.json": "PASS1_FREEZE_RECEIPT_sha256",
        "PASS1_NOTES.md": "PASS1_NOTES_md_sha256",
        "PASS2_REVIEW.md": "PASS2_REVIEW_md_sha256",
    }
    for name, key in mapping.items():
        if digest((HERE / "reports" / name).read_bytes()) != completion[key]:
            raise ValueError("Report hash join differs")
    if digest((HERE / "source/candidate.txt").read_bytes()) != completion["candidate_sha256"]:
        raise ValueError("Candidate differs")
    for name, sha in completion["page_images_sha256"].items():
        if digest((HERE / "source" / name).read_bytes()) != sha:
            raise ValueError("Image join differs")
    if digest((HERE / "authorization/manifest.json").read_bytes()) != (
            completion["packet_manifest_sha256"]):
        raise ValueError("Packet identity differs")
    sys.stdout.write("PASS: 20 scoped dispositions, unchanged reports/source/candidate.\n")


def build() -> None:
    """Copy delivered artifacts and record explicitly limited root review findings."""
    copies = [(p, HERE / "reports" / p.name) for p in REPORTS.iterdir() if p.is_file()]
    copies += [(p, HERE / "source" / p.name)
               for p in (PACKET / "01-source-only" / SOURCE).iterdir() if p.is_file()]
    copies.append((PACKET / "02-candidate-text" / SOURCE / "candidate.txt",
                   HERE / "source/candidate.txt"))
    copies += [(p, HERE / "native-evidence" / p.name)
               for p in (PACKET / "02-candidate-text" / SOURCE / "native-evidence").iterdir()]
    copies += [(PACKET / name, HERE / "authorization" / name)
               for name in ("START_HERE.md", "SOURCE_ONLY_IDENTITIES.json", "manifest.json")]
    baseline = REPO / "research/local_review/weld-building-fees-atlas-source-review-2026-09-11"
    copies += [(baseline / name, HERE / "prior-review" / Path(name).name)
               for name in ("evidence-manifest.json", "frozen/SOURCE_REVIEW.json",
                            "frozen/SOURCE_REVIEW.md")]
    for src, dst in copies:
        data = src.read_bytes()
        immutable(dst, data)
        if src.read_bytes() != data:
            raise ValueError("Input changed during custody copy")
    notes = [
        ("confirmed_observation", [3], "The footer is visually below the boxed NOTE; native "
         "order puts the footer before it. Preserve native bytes and separate visual order."),
        ("confirmed_observation", [3], "The printed plans.$80.00 abutment is a source feature; "
         "do not add invented leaders or repair the unchanged candidate."),
        ("confirmed_observation", [2], "Demolition amount visibly has two periods: $80..00."),
        ("confirmed_observation", [3], "The printed cost tier is $40,0001 to $60,000; "
         "$571.69 belongs to that row. No numeric repair."),
        ("confirmed_observation", [3], "Revised 012/25 is printed literally, unparsed and "
         "distinct from the January 2026 face label."),
        ("confirmed_observation", [5], "Hotel/Motel Room road fee is printed $2401."),
        ("confirmed_observation", [2, 5], "Page 2 prints $1636.00; page 5 prints $1,636. "
         "Both forms remain separate exact source text."),
        ("confirmed_observation", [1], "$1027.00, $3827.00, $6327.00 and $2000 preserve "
         "the source's missing thousands commas; no arithmetic validation claimed."),
        ("qualified", [4], "The visible matrix has nine IA–VB columns and N.P. markers. "
         "Root checked the full page and reported associations; this is not a fresh "
         "independent cell-by-cell transcription of all 252 cells."),
        ("qualified", [4], "Linearization preserves text but loses explicit grid layout. "
         "Calling it harmless is too broad; retrieval must retain the checked column joins."),
        ("confirmed_observation", [1, 2, 3, 4, 5], "Explicit PHYSICAL PDF PAGE markers are "
         "packaging, not source text or extraction errors."),
        ("qualified", [1, 2, 3, 4, 5], "Printed dot leaders are source glyphs; native "
         "whitespace and reader packaging must not all be conflated as packaging. No "
         "exact leader-count or visual Unicode certification."),
        ("qualified", [1, 3], "Black table headers and the boxed NOTE are visible layout. "
         "Their absence from plain text is a representation limitation, not a fee mismatch."),
        ("uncertainty_retained", [5], "Keep the exact native sq. ft punctuation for each "
         "row; no corrective Unicode or trailing-period claim is made here."),
        ("uncertainty_retained", [2], "The dot following dwellings is adjacent to leaders. "
         "Do not infer a new punctuation correction from that ambiguous segmentation."),
        ("qualified", [1, 2, 3, 4, 5], "Underlines, borders and leaders remain visible in "
         "images; absent layout graphics alone are not incorrect legal wording."),
        ("confirmed_observation", [1, 3], "Face and revision labels do not independently "
         "establish adoption, applicability or currentness."),
        ("confirmed_observation", [1, 2], "Minor plan-review fee has one decimal point "
         "($80.00), unlike the printed demolition $80..00."),
        ("confirmed_observation", [5], "The Agricultural Commercial road label itself "
         "includes 1,000 sq. ft; the value separately says per 1,000 sq. ft. No multiplier "
         "is inferred or calculated."),
        ("qualified", [2], "Reported amounts align with the full source page. Preserve the "
         "complete electrical scope, park-inspection exception and total customer labor/"
         "material basis; condensed Pass 1 prose is not an exhaustive independent transcript."),
    ]
    rec = Reconciliation(
        received_and_recorded_at=datetime.now(timezone.utc).isoformat(),
        status="assisted_review_preserved_with_atlas_scoped_dispositions",
        review_mode="candidate_and_prior_review_aware_direct_page_check",
        root_full_pages_inspected=[1, 2, 3, 4, 5],
        root_scope="All five full source PNGs were directly viewed, with prior source review "
        "and candidate context. Root reviewed all 20 report entries. No new independent "
        "complete transcript, arithmetic, adoption or currentness review is claimed.",
        dispositions=[Disposition(finding_id=f"EB018-P2-{i:03}", decision=d, pages=p, note=n)
                      for i, (d, p, n) in enumerate(notes, 1)],
        qualifications=[
            "Ebenezer explicitly reports caption-mediated assistance, including pre-supplied "
            "image descriptions. This is not a direct blind visual transcription.",
            "Ebenezer lacked the PDF in his remote workdir and bound its SHA from identities. "
            "Atlas independently checks the actual copied PDF and page/candidate identities.",
            "Executor timestamps and freeze chronology are reported; file availability and "
            "hash agreement do not independently prove non-consultation or blind order.",
            "The report's source_sha256 column often contains abbreviated page-image hashes, "
            "not the PDF hash. This package binds PDF and image identities separately.",
            "Seven minor and thirteen informational entries are the external counts, not "
            "twenty confirmed OCR errors. No native word or amount correction is accepted.",
            "Original cropped files may be absent from delivery after the Grok usage limit; "
            "full source PNGs are retained. Do not recreate missing external tool history.",
            "Successful original requested/final URL and acquisition time remain unconfirmed; "
            "received-review-package custody and the older source review's limits persist.",
        ],
    )
    save("RECONCILIATION.json", rec)
    files = [FileRef(path=p.relative_to(HERE).as_posix(), sha256=digest(p.read_bytes()),
                     size_bytes=p.stat().st_size)
             for p in sorted(HERE.rglob("*")) if p.is_file()]
    save("INVENTORY.json", Inventory(files=files))
    verify()


if __name__ == "__main__":
    verify() if "--verify" in sys.argv else build()
