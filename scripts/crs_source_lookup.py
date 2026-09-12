"""Offline, three-section source-passage lookup in one reviewed 2026 CRS PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_PACKAGE = Path("research/local_review/crs-2026-title1-source-review-2026-09-12")
DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / SOURCE_PACKAGE

IDS = ("CRS-1-1-101", "CRS-1-1-102", "CRS-1-1-103")
SectionID = Literal["CRS-1-1-101", "CRS-1-1-102", "CRS-1-1-103"]
SOURCE_URL = "https://olls.info/crs/crs2026-title-01.pdf"
SOURCE_SHA = "1c6b021e612929ca8024bebf1022ba45f57aa99712d080c404da8f7f7e90cd1d"
MANIFEST_SHA = "ea43aa1d1d2ae4d28a8833642230d22babb18c615a1604b913b52459d181175d"
QA_SHA = "555aefd0cac5b99e74d3bb37937d0f36b1943979202aa3f7d96a4cc55f1109e0"
PINS = {
    "FINAL_MANIFEST.json": MANIFEST_SHA,
    "FINAL_MANIFEST.schema.json":
        "682c4bfb97f5b93d2b3724539d46419cb5ee484cee622b5e8e76e43d18fd8048",
    "SOURCE_QA.json": QA_SHA,
    "build_review.py": "13599485e062a892ec58876de71ccd5a249d5adbed2eec73cb015acf7ee207e1",
    "acquire.py": "329a665f7ac4cee5ddcc4c98a4a001147c95b581d048d7634f5469c1eca822bf",
}
MAX_FILE, MAX_TOTAL = 8_000_000, 16_000_000
BOUNDARY = (
    "Research-only passages from the preserved 2026 PDF, limited to CRS-1-1-101/102/103. "
    "Six pages were reviewed with native-text context; the whole 1008-page title was not "
    "reviewed. Contents listings and the section 104 tail are excluded. Historical/editorial "
    "notes and case commentary remain distinct from statutory paragraphs. No current-law, "
    "effective-date, applicability, interpretation or completeness conclusion. The older "
    "2025 derived catalog and its unresolved original custody remain unchanged."
)
# These are the complete associations accepted in the frozen source review, not search hits.
SPECS = {
    IDS[0]: ("S101-H", ((None, ("S101-B",)),), ("S101-SOURCE", "S101-EDITOR")),
    IDS[1]: ("S102-H", (("(1)", ("S102-B1A", "S102-B1B")), ("(2)", ("S102-B2",))),
             ("S102-SOURCE", "S102-EDITOR", "S102-XREF")),
    IDS[2]: ("S103-H", tuple((f"({i})", (f"S103-B{i}",)) for i in (1, 2, 3)),
             ("S103-SOURCE", "S103-EDITOR", "S103-ANN-H", "S103-ANN")),
}
ROLES = {rid: "statutory_paragraph" for _, paragraphs, _ in SPECS.values()
         for _, fragments in paragraphs for rid in fragments}
ROLES.update({h: "section_heading" for h, _, _ in SPECS.values()})
ROLES.update({"S101-SOURCE": "source_history_note", "S102-SOURCE": "source_history_note",
              "S103-SOURCE": "source_history_note", "S101-EDITOR": "editors_note",
              "S102-EDITOR": "editors_note", "S103-EDITOR": "editors_note",
              "S102-XREF": "cross_references", "S103-ANN-H": "annotation_heading",
              "S103-ANN": "case_annotation"})


class Strict(BaseModel):
    """Immutable records with no undeclared fields or scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class FileRef(Strict):
    """One byte-bound, confined file relative to the source packet."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0, le=MAX_FILE)

    @model_validator(mode="after")
    def confined(self) -> FileRef:
        """Reject absolute paths, aliases and traversal before opening evidence."""
        p = Path(self.path)
        if (p.is_absolute() or PureWindowsPath(self.path).drive or "\\" in self.path
                or ".." in p.parts or str(p) != self.path or self.path in {"", "."}):
            raise ValueError("Unconfined evidence path")
        return self


class SourceManifest(Strict):
    """Exact closed upstream source-review inventory."""

    schema_version: Literal[1]
    files: tuple[FileRef, ...]
    excluded_files: Literal["FINAL_MANIFEST.json and FINAL_MANIFEST.schema.json only"]


class Fragment(Strict):
    """A complete reviewed native region, not normalized or silently corrected."""

    region_id: str
    section_id: SectionID
    role: Literal["section_heading", "statutory_paragraph", "source_history_note",
                  "editors_note", "cross_references", "annotation_heading", "case_annotation"]
    physical_page: int = Field(ge=4, le=6)
    printed_page: str
    native: FileRef
    image: FileRef
    native_start: int = Field(ge=0)
    native_end: int = Field(gt=0)
    text: str
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    visible_location: str
    source_review_qualification: str
    byte_basis: Literal["half_open_utf8_offsets_in_unchanged_native_page"] = (
        "half_open_utf8_offsets_in_unchanged_native_page"
    )

    @model_validator(mode="after")
    def bounds(self) -> Fragment:
        """Check region lengths, text identity and declared native page bounds."""
        raw = self.text.encode("utf-8")
        if (not 0 <= self.native_start < self.native_end <= self.native.size_bytes
                or len(raw) != self.native_end - self.native_start
                or digest(raw) != self.text_sha256):
            raise ValueError("Invalid native fragment")
        return self


class Paragraph(Strict):
    """One complete source paragraph, including every declared continuation fragment."""

    label: str | None
    fragments: tuple[Fragment, ...] = Field(min_length=1)
    text: str
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    continuation_note: str | None
    byte_basis: Literal["ordered_native_fragments_concatenated_without_insertions"] = (
        "ordered_native_fragments_concatenated_without_insertions"
    )

    @model_validator(mode="after")
    def complete(self) -> Paragraph:
        """Reject inserted text or commentary masquerading as statutory body."""
        if (any(f.role != "statutory_paragraph" for f in self.fragments)
                or self.text != "".join(f.text for f in self.fragments)
                or digest(self.text.encode()) != self.text_sha256):
            raise ValueError("Paragraph differs from ordered source fragments")
        return self


class Custody(Strict):
    """Measured source receipt facts, kept separate from publication and legal dates."""

    source_id: Literal["crs-2026-title1-official-pdf"]
    authority_level: Literal["state"] = "state"
    jurisdiction: Literal["Colorado"] = "Colorado"
    publisher_role: Literal["Office of Legislative Legal Services, Colorado General Assembly"]
    source: FileRef
    official_url: Literal[SOURCE_URL]
    acquisition_receipt: FileRef
    acquisition_started_at: AwareDatetime
    acquisition_completed_at: AwareDatetime
    acquisition_basis: Literal["retained_direct_http_receipt_verified_tls_200"] = (
        "retained_direct_http_receipt_verified_tls_200"
    )
    source_review_prepared_at: AwareDatetime
    printed_edition_claim: Literal["Colorado Revised Statutes 2026"]
    catalog_session_claim: str
    pdf_metadata_claims: dict[str, str | None]
    date_qualification: str
    legal_effective_date: None = None
    source_manifest_sha256: Literal[MANIFEST_SHA] = MANIFEST_SHA
    source_review_sha256: Literal[QA_SHA] = QA_SHA
    reviewed_physical_pages: tuple[Literal[1, 2, 3, 4, 5, 6], ...]
    total_pdf_pages: Literal[1008] = 1008
    review_method: Literal["candidate_aware_source_review_not_blind"] = (
        "candidate_aware_source_review_not_blind"
    )
    source_review_limits: tuple[str, ...]
    typography_qualification: str
    prior_2025_original_custody: Literal["unresolved"] = "unresolved"

    @model_validator(mode="after")
    def chronology_and_scope(self) -> Custody:
        """Keep measured acquisition chronology and exactly six reviewed pages explicit."""
        if (not self.acquisition_started_at <= self.acquisition_completed_at
                <= self.source_review_prepared_at
                or self.reviewed_physical_pages != (1, 2, 3, 4, 5, 6)
                or self.source.sha256 != SOURCE_SHA):
            raise ValueError("Invalid custody chronology or review scope")
        return self


class Section(Strict):
    """The whole admitted section selection with distinct ancillary source material."""

    section_id: SectionID
    heading: Fragment
    paragraphs: tuple[Paragraph, ...]
    ancillary: tuple[Fragment, ...]
    scope_note: str

    @model_validator(mode="after")
    def associations(self) -> Section:
        """Require all and only the review's complete section/paragraph/note associations."""
        h, paragraphs, notes = SPECS[self.section_id]
        if (self.heading.region_id != h or self.heading.role != "section_heading"
                or tuple((p.label, tuple(f.region_id for f in p.fragments))
                         for p in self.paragraphs) != paragraphs
                or tuple(f.region_id for f in self.ancillary) != notes):
            raise ValueError("Section associations changed or incomplete")
        parts = (self.heading, *(f for p in self.paragraphs for f in p.fragments), *self.ancillary)
        if (any(f.section_id != self.section_id or f.role != ROLES[f.region_id] for f in parts)
                or any(f.role in {"section_heading", "statutory_paragraph"}
                       for f in self.ancillary)):
            raise ValueError("Cross-section or misclassified evidence")
        return self


class Result(Strict):
    """A source-only response; it never answers a current-law or calculation question."""

    status: Literal["matched", "outside_scope", "refused_mode"]
    requested_section_id: str
    section: Section | None = None
    custody: Custody | None = None
    boundary: Literal[BOUNDARY] = BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    research_only: Literal[True] = True
    answer_safe: Literal[False] = False

    @model_validator(mode="after")
    def outcome(self) -> Result:
        """Ensure refusal envelopes cannot carry source passages."""
        if self.status == "matched":
            if (self.section is None or self.custody is None
                    or self.section.section_id != self.requested_section_id):
                raise ValueError("Missing or mismatched result evidence")
        elif self.section is not None or self.custody is not None:
            raise ValueError("Refusal must not contain evidence")
        return self


def digest(data: bytes) -> str:
    """Hash exact unchanged bytes."""
    return hashlib.sha256(data).hexdigest()


def safe_file(root: Path, name: str) -> Path:
    """Reject traversal, symlinks and special files before opening bounded evidence."""
    FileRef(path=name, sha256="0" * 64, size_bytes=0)
    if ".." in root.parts:
        raise ValueError("Parent traversal in source root")
    path = root.absolute() / name
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Missing, special or symlinked evidence")
    if path.stat().st_size > MAX_FILE:
        raise ValueError("Evidence file exceeds bound")
    return path


def read(root: Path, name: str) -> bytes:
    """Bound a read even if a file grows after its size check."""
    with safe_file(root, name).open("rb") as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise ValueError("Evidence grew past bound")
    return data


def check_packet(root: Path) -> dict[str, str]:
    """Verify every closed packet byte and executable dependency before using any source text."""
    for name, sha in PINS.items():
        if digest(read(root, name)) != sha:
            raise ValueError(f"Pinned source evidence changed: {name}")
    manifest = SourceManifest.model_validate_json(read(root, "FINAL_MANIFEST.json"))
    refs = {r.path: r for r in manifest.files}
    if len(refs) != len(manifest.files):
        raise ValueError("Duplicate source inventory path")
    expected = set(refs) | {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Symlink or special source packet entry")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != expected:
        raise ValueError("Missing or unexpected source packet file")
    hashes, total = {}, 0
    for name in sorted(expected):
        data = read(root, name)
        total += len(data)
        hashes[name] = digest(data)
        if total > MAX_TOTAL:
            raise ValueError("Source packet exceeds total bound")
        if name in refs and (len(data) != refs[name].size_bytes
                             or hashes[name] != refs[name].sha256):
            raise ValueError(f"Source packet bytes changed: {name}")
    return hashes


# Only verified in-memory code is executed; no mutable package imports are searched.
# The old acquisition helper is imported for its Receipt model, never run.
LAUNCHER = r'''
import hashlib,json,os,sys,types
from pathlib import Path
p=Path(sys.argv[1]); pins=json.loads(sys.argv[2])
codes={}
for name in ('acquire.py','build_review.py'):
    f=p/name
    if any(x.is_symlink() for x in (f,*f.parents)): raise ValueError('Symlinked verifier')
    data=f.read_bytes()
    if hashlib.sha256(data).hexdigest()!=pins[name]: raise ValueError('Verifier changed')
    codes[name]=data
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':
        raise RuntimeError('Offline verifier forbids network and subprocess activity')
    if event in {'os.remove','os.rename','os.rmdir','os.mkdir','os.link','os.symlink',
                 'os.truncate','os.chmod','os.chown','os.utime'}:
        raise RuntimeError('Read-only verifier forbids filesystem mutation')
    if event=='open' and ((isinstance(args[1],str) and any(c in args[1] for c in 'wax+'))
                         or (isinstance(args[2],int) and args[2] &
                             (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):
        raise RuntimeError('Read-only verifier')
sys.addaudithook(audit)
m=types.ModuleType('acquire');m.__file__=str(p/'acquire.py');sys.modules['acquire']=m
exec(compile(codes['acquire.py'],m.__file__,'exec'),m.__dict__)
n=types.ModuleType('review_only');n.__file__=str(p/'build_review.py')
sys.modules[n.__name__]=n
exec(compile(codes['build_review.py'],n.__file__,'exec'),n.__dict__)
n.verify()
sys.stdout.write('SOURCE_SEMANTIC_VERIFICATION_PASSED\n')
'''


def semantic_verify(root: Path) -> None:
    """Run the pinned original semantic verifier in an isolated, read-only offline child."""
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", LAUNCHER, str(root.absolute()), json.dumps(PINS)],
            cwd=root, check=True, capture_output=True, text=True, timeout=30,
            env={k: v for k, v in os.environ.items()
                 if not k.startswith("PYTHON") or k == "PYTHONDONTWRITEBYTECODE"},
        )
        if result.stdout != "SOURCE_SEMANTIC_VERIFICATION_PASSED\n":
            raise ValueError("Unexpected semantic verification result")
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Pinned source semantic verifier failed") from exc


def _fragment(root: Path, region: dict, pages: dict[int, dict]) -> Fragment:
    """Bind the full exact reviewed fragment to its native page and visual evidence."""
    page = pages[region["physical_page"]]
    native = FileRef.model_validate(page["native"])
    raw = read(root, native.path)
    if digest(raw) != native.sha256 or region["native_sha256"] != native.sha256:
        raise ValueError("Native page identity changed")
    start, end = region["native_start"], region["native_end"]
    if raw[start:end] != region["text"].encode():
        raise ValueError("Source region offset or text changed")
    return Fragment(
        **{k: region[k] for k in ("region_id", "section_id", "role", "physical_page",
                                  "native_start", "native_end", "text", "text_sha256",
                                  "visible_location")},
        printed_page=page["printed_page"], native=native,
        image=FileRef.model_validate(page["image"]),
        source_review_qualification=region["qualification"],
    )


def _adapt(root: Path, qa: dict, receipt: dict, section_id: SectionID) -> Result:
    """Adapt the complete review associations; no search, omission, cleanup or interpretation."""
    if [s["section_id"] for s in qa["selected_sections"]] != list(IDS):
        raise ValueError("Selected source IDs changed")
    if (qa["legal_effective_date"] is not None or qa["legal_currentness"] != "not_verified"
            or qa["answer_safe"] is not False or qa["research_only"] is not True):
        raise ValueError("Unsupported legal-state promotion")
    pages = {p["physical_page"]: p for p in qa["pages"]}
    regions = {r["region_id"]: r for r in qa["regions"]}
    if len(regions) != len(qa["regions"]) or list(pages) != list(range(1, 7)):
        raise ValueError("Duplicate regions or incomplete reviewed page coverage")
    selected = next(s for s in qa["selected_sections"] if s["section_id"] == section_id)
    fragment = lambda rid: _fragment(root, regions[rid], pages)
    paragraphs = []
    for paragraph in selected["paragraphs"]:
        fragments = tuple(fragment(rid) for rid in paragraph["fragments"])
        text = "".join(f.text for f in fragments)
        paragraphs.append(Paragraph(label=paragraph["label"], fragments=fragments, text=text,
                                    text_sha256=digest(text.encode()),
                                    continuation_note=paragraph["continuation_note"]))
    ancillary_ids = selected["source_note_regions"] + selected["ancillary_regions"]
    section = Section(section_id=section_id, heading=fragment(selected["heading_region"]),
                      paragraphs=tuple(paragraphs), scope_note=selected["scope_note"],
                      ancillary=tuple(fragment(rid) for rid in ancillary_ids))
    if (receipt["body"] != qa["source"] or qa["source"]["sha256"] != SOURCE_SHA
            or receipt["requested_url"] != SOURCE_URL
            or receipt["observed_response_url"] != SOURCE_URL
            or receipt["http_status"] != 200 or receipt["curl_exit"] != 0
            or receipt["tls_verification_result"] != 0 or not receipt["response_complete"]
            or receipt["redirect_location"] is not None):
        raise ValueError("Acquisition/source identity mismatch")
    data = dict(
        source_id=qa["source_id"], publisher_role=qa["publisher_role"], source=qa["source"],
        official_url=qa["source_url"], acquisition_receipt=qa["acquisition_receipt"],
        acquisition_started_at=receipt["started_at"],
        acquisition_completed_at=receipt["completed_at"],
        source_review_prepared_at=qa["prepared_at"], printed_edition_claim=qa["printed_edition"],
        catalog_session_claim=qa["catalog_session_statement"],
        pdf_metadata_claims=qa["pdf_metadata_claims"], date_qualification=qa["date_qualification"],
        reviewed_physical_pages=list(pages), source_review_limits=qa["limits"],
        typography_qualification=qa["typography_qualification"],
    )
    custody = Custody.model_validate_json(json.dumps(data))
    return Result(status="matched", requested_section_id=section_id,
                  section=section, custody=custody)


def lookup(root: Path, section_id: str, *, mode: str = "source_only") -> Result:
    """Return one entire admitted source selection, or refuse unsupported IDs/modes."""
    if mode != "source_only":
        return Result(status="refused_mode", requested_section_id=section_id)
    if section_id not in IDS:
        return Result(status="outside_scope", requested_section_id=section_id)
    before = check_packet(root)
    qa_bytes, receipt_bytes = read(root, "SOURCE_QA.json"), read(root, "events/E001.json")
    semantic_verify(root)
    if check_packet(root) != before:
        raise ValueError("Source packet changed during semantic verification")
    result = _adapt(root, json.loads(qa_bytes), json.loads(receipt_bytes), section_id)
    if check_packet(root) != before:
        raise ValueError("Source packet changed during adaptation")
    return result


def main() -> None:
    """Write one typed JSON response to stdout; never create files or acquire a source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--section", required=True)
    parser.add_argument("--mode", default="source_only")
    args = parser.parse_args()
    result = lookup(args.source, args.section, mode=args.mode)
    sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    if result.status != "matched":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
