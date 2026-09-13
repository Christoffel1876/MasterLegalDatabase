"""Write this bounded source review once, after independent visual and structural checks."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import AwareDatetime, Field

from review import (
    ROOT, SOURCE_SHA, Asset, Disposition, Observation, Review, Strict, asset,
    check_review, extract_pages, read,
)


class HashCheck(Strict):
    """A reported expected digest compared with the exact retained file."""
    claim: str
    actual: Asset
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matches: bool


class Reconciliation(Strict):
    """Scope and limits of external-report custody, separate from source reading."""
    prepared_at: AwareDatetime
    checks: list[HashCheck]
    source_candidate_copies_equal: bool
    reported_critical_count: int
    reported_classification_count: int
    actual_pass2_finding_ids: list[str]
    timeline_as_reported: dict[str, str]
    method_as_reported: str
    qualifications: list[str]


def new_file(name: str, raw: bytes) -> None:
    """Create an output exactly once inside this new review folder."""
    path = ROOT / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise ValueError("Output already exists: " + name)
    with temporary.open("xb") as handle:
        handle.write(raw)
    temporary.rename(path)


def external_checks() -> Reconciliation:
    """Rehash reported source/candidate/receipt claims without endorsing reported tool actions."""
    receipt = json.loads(read(ROOT, "received/COMPLETION_RECEIPT.json"))
    freeze = json.loads(read(ROOT, "received/PASS1_FREEZE_RECEIPT.json"))
    checks = []
    for key, name in [
        ("original_pdf_sha256", "received/source/original.pdf"),
        ("pass1_frozen_sha256", "received/PASS1_frozen.md"),
        ("pass1_freeze_receipt_sha256", "received/PASS1_FREEZE_RECEIPT.json"),
        ("pass2_review_sha256", "received/PASS2_REVIEW.md"),
        ("candidate_expected_sha256_from_manifest", "received/candidate/candidate.txt"),
        ("packet_manifest_sha256", "packet-proof/MANIFEST.json"),
        ("start_here_instruction_sha256", "packet-proof/START_HERE.md"),
    ]:
        ref = asset(ROOT, name)
        checks.append(HashCheck(claim=key, actual=ref, expected_sha256=receipt[key],
                                matches=ref.sha256 == receipt[key]))
    for row in freeze["page_images"]:
        ref = asset(ROOT, f"received/source/page-{row['physical_page']:04d}.png")
        checks.append(HashCheck(claim=f"Pass1 page {row['physical_page']} image", actual=ref,
                                expected_sha256=row["sha256"], matches=ref.sha256 == row["sha256"]))
    if not all(row.matches for row in checks):
        raise ValueError("External report digest mismatch")
    for kind in ["source", "candidate"]:
        for path in (ROOT / kind).iterdir():
            if read(ROOT, "received/" + kind + "/" + path.name) != path.read_bytes():
                raise ValueError("External source/candidate copy differs")
    return Reconciliation(prepared_at=datetime.now(timezone.utc), checks=checks,
        source_candidate_copies_equal=True, reported_critical_count=receipt["critical_findings"],
        reported_classification_count=receipt["minor_findings"],
        actual_pass2_finding_ids=[f"EB024-P2-{i:03d}" for i in range(1, 5)],
        timeline_as_reported={"start": receipt["utc_start"], "freeze": freeze["utc_freeze"],
                              "candidate_release": receipt["utc_candidate_release"],
                              "completion": receipt["utc_completion"]},
        method_as_reported=receipt["pass2_method"], qualifications=[
            "External Pass1 and Pass2 explicitly declare caption-mediated methods, not direct pixels. "
            "Reported read/reopen and event times are retained claims, not independently witnessed.",
            "Four finding IDs are source anomalies, packaging and an unresolved style issue, not "
            "four proven transcription errors. The report identifies zero critical findings.",
            "Pass1 is a compressed summary, not a complete transcription. Its singular/plural "
            "exigent circumstance[s] notation and paraphrased severability must not replace source text.",
            "PASS2 agreement mentions fee/audit/budget language; this five-page bylaws document "
            "has audit/budget governance text, not a reviewed fee schedule.",
            "This selected check verifies twelve explicit digest claims plus exact copied source/" 
            "candidate equality. It does not reclassify the external report's '13 OK' tool assertion.",
            "The packet manifest and preparation reference another document and uncopied original "
            "packet members. They are historical binding evidence, not this review's closed inventory.",
        ])


def main() -> None:
    """Bind complete reviewed page text and preserve source-owned anomalies without correction."""
    pages, metadata = extract_pages(ROOT)
    observations = [
        Observation(id="A01", pages=[1, 2], paragraph_ids=["P1-B01", "P1-B02", "P1-B04", "P1-B05", "P1-B06", "P2-B03"],
            statement="The source identifies Regulations of the El Paso County Board of Health, "
            "Chapter 1, Bylaws. This is the English Board of Health document.",
            limitation="No claim about Spanish equivalence, the entire county code or present board composition."),
        Observation(id="A02", pages=[1, 2, 3, 4, 5],
            paragraph_ids=["P1-B08", "P2-B16", "P3-B08", "P4-B10", "P5-B12"],
            statement="5/23/2012 is visible at the lower left of every complete page. A separate "
            "page-5 concern was rechecked in fresh PyMuPDF and retained Poppler crops; both show "
            "the date. The root-provided page-5 crop exactly matches the independent PyMuPDF crop.",
            limitation="The footer is unlabeled; it does not by itself establish adoption, effectiveness "
            "or currentness. PDF metadata creation/modification strings are separate unauthenticated claims."),
        Observation(id="A03", pages=[3], paragraph_ids=["P3-B02"],
            statement="Direct source crop confirms visible digit gaps in Section 11-10.5-10 1 "
            "and Section 25-1-5 11. The native candidate retains those spaces. The text 'et seq.' "
            "is visibly italic and underlined. The source also reads 'or, by any Board member'.",
            limitation="Do not silently change these strings to normalized statute numbers or repair "
            "the punctuation; image shape alone does not certify an exact Unicode spacing codepoint."),
        Observation(id="A04", pages=[2, 3, 4], paragraph_ids=["P2-B05", "P2-B08", "P3-B01", "P4-B05"],
            statement="Article 1 appears in earlier references; the page-4 Board Responsibilities "
            "paragraph visibly and natively reads Article I. Both forms remain unchanged.",
            limitation="No reference normalization or determination of which provision was intended."),
        Observation(id="A05", pages=[2, 3, 4, 5], paragraph_ids=["P2-B12", "P3-B01", "P3-B03", "P4-B01", "P4-B09", "P5-B01"],
            statement="Officers continues from page 2 into page 3; Meetings from page 3 into page 4. "
            "Section 1.5 on page 4 ends 'with an' and continues on page 5 with 'opportunity'. "
            "P5-B01 explicitly links to P4-B09. Date footers are separate from these body contexts.",
            limitation="Physical page portions are not separate legal rules; this is source structure."),
        Observation(id="A06", pages=[2, 3, 4, 5], paragraph_ids=["P2-B05", "P2-B11", "P2-B13", "P2-B14", "P3-B04", "P3-B05", "P3-B06", "P3-B07", "P4-B01", "P4-B02", "P4-B04", "P4-B09", "P5-B03", "P5-B07", "P5-B09"],
            statement="Complete paragraph text preserves qualifications and exceptions, including "
            "expense reimbursement, funding availability, December-election alternative, no committee "
            "vote, service availability, emergency notice, quorum adjournment, county-only removal, "
            "agenda timing/requests, closed-session alternatives, personal opinions, September 1, "
            "draft review before plan adoption, parliamentary limits and exigent amendment exception.",
            limitation="No fee calculation, applicability determination, deadline conversion or extracted "
            "semantic rule units are produced."),
        Observation(id="A07", pages=[1, 2, 3, 4, 5],
            paragraph_ids=["P1-B04", "P1-B05", "P1-B06", "P2-B01", "P2-B02", "P2-B03", "P5-B02"],
            statement="Cover Chapter 1, Bylaws and Board heading are bold and underlined. Page-2 "
            "three headings and the ten numbered section headings are bold and underlined. Page 5 "
            "starts with a continuing paragraph, not a separate running title. No table, figure, "
            "handwritten mark, signature or execution block was seen in these five pages.",
            limitation="Native plain text does not encode all visual styling. Exact Unicode typography "
            "comes from retained native bytes, not from a visual codepoint certification."),
        Observation(id="A08", pages=[4, 5], paragraph_ids=["P4-B09", "P5-B03", "P5-B07", "P5-B09", "P5-B11"],
            statement="Source wording remains 'As soon as practical' in Section 1.5 versus "
            "'As soon as practicable' in 1.6; 'Robert’s Rules'; singular 'an exigent circumstance'; "
            "and 'any part of these Bylaws are declared'. No grammar or citation repair is applied.",
            limitation="These are transcription observations, not legal-effect corrections."),
        Observation(id="A09", pages=[1, 2, 3, 4, 5], paragraph_ids=[],
            statement="All 170 nonblank native lines are bound to exact UTF-8 page ranges, source "
            "text geometry and 54 visible heading/paragraph/footer portions. All 12,640 native bytes "
            "are retained unchanged, including blank-line runs. Candidate packaging is reproduced exactly.",
            limitation="Automated extraction/range equality is distinct from the preceding human-model "
            "visual comparison; neither alone certifies legal validity or present completeness."),
    ]
    dispositions = [
        Disposition(external_id="EB024-P2-001", disposition="accepted_source_anomaly", pages=[3],
            source_evidence="Direct crop and complete page show 11-10.5-10 1 and 25-1-5 11; "
            "native retains the same spacing.", qualification="Source-owned spacing, not a candidate error; no correction."),
        Disposition(external_id="EB024-P2-002", disposition="accepted_source_anomaly", pages=[2, 3, 4],
            source_evidence="Earlier Article 1 and page-4 Article I are visible and match native.",
            qualification="Preserve both; do not infer the intended citation or legal effect."),
        Disposition(external_id="EB024-P2-003", disposition="accepted_packaging_classification", pages=[1, 2, 3, 4, 5],
            source_evidence="Blank-line runs are in exact native extraction; PHYSICAL PDF PAGE "
            "markers are external packaging. Page and paragraph continuation order matches the images.",
            qualification="Not a printed-content error or a demonstrated wrong reading order."),
        Disposition(external_id="EB024-P2-004", disposition="resolved_by_direct_visual_review", pages=[1, 2, 3, 4, 5],
            source_evidence="Direct views confirm bold/underlined headings as described in A07, "
            "italic-underlined et seq. on page 3, and no separate page-5 running title.",
            qualification="This resolves the named visual issue within these pages, not arbitrary "
            "font/Unicode equivalence or source legal status."),
    ]
    qa = Review(schema_version="eb024-source-fidelity-1", source_id="el-paso-boh-bylaws-sd011",
        authority_id="CO-COUNTY-EL_PASO", prepared_at=datetime.now(timezone.utc),
        source=asset(ROOT, "source/original.pdf"), candidate=asset(ROOT, "candidate/candidate.txt"),
        source_first_notes=asset(ROOT, "SOURCE_FIRST_NOTES.md"),
        method="Actual source-first: all five complete original packet page images were directly "
        "viewed before native candidate or external reports. Then all native lines were compared "
        "with source context; direct original-PDF crops resolved fine spacing/style and footer checks. "
        "Not certified blind to source identity or prior task context. Full images displayed at "
        "1376x1780 from 2550x3300; technical crops inspected at their full available dimensions.",
        full_pages_directly_viewed=[1, 2, 3, 4, 5],
        crops_directly_viewed=[asset(ROOT, "crops/" + name + ".png") for name in [
            "p3-treasurer-citations", "p4-article-I", "p5-final-rules", "p4-footer-pymupdf",
            "p5-footer-pymupdf", "p5-footer-poppler-crop"]],
        extractor="PyMuPDF 1.28.2; get_text(text), flags=195, sort=False",
        native_bytes=12640, native_lines=400, nonblank_lines=170, pages=pages,
        metadata_as_received=metadata, printed_date="5/23/2012",
        printed_date_role="unlabeled_footer_on_all_five_pages", adoption_date=None, effective_date=None,
        original_acquisition_at=None, acquisition_method="received_review_package",
        repository_received_at_claim="2026-09-12T22:59:48.795762Z", observations=observations,
        external_dispositions=dispositions, limitations=[
            "Research source-fidelity review of exactly this five-page English bylaws PDF; "
            "not all Board regulations, current governance, or Spanish translation equivalence.",
            "Original acquisition and reported transport remain unverified received-package claims. "
            "The frozen custody note's 'only cover inspected' describes its earlier review scope; "
            "this additive record does not edit that historical statement.",
            "No visible adoption, effective-date or signature block. Footer, file-name years, "
            "PDF creation/modification metadata and repository receipt have different roles.",
            "Native all-page equality and complete line allocation do not prove visual fidelity "
            "algorithmically. Direct visual judgment is separately recorded and bounded to these pages.",
            "Prior source-discovery 66/50 target-cap breach and lost non-PDF bodies remain custody "
            "limitations. This review neither repairs nor relabels that acquisition history.",
            "External summaries are not a full transcript; corrected Atlas context comes from "
            "the untouched native source and direct images, with all original reports retained.",
        ], legal_currentness="not_verified", answer_safe=False, canonical_writes=0, public_requests=0)
    check_review(ROOT, qa)
    encoded = qa.model_dump_json(indent=2) + "\n"
    Review.model_validate_json(encoded)
    new_file("SOURCE_QA.schema.json", (json.dumps(Review.model_json_schema(), indent=2) + "\n").encode())
    new_file("SOURCE_QA.json", encoded.encode())
    reconciliation = external_checks()
    encoded_reconciliation = reconciliation.model_dump_json(indent=2) + "\n"
    Reconciliation.model_validate_json(encoded_reconciliation)
    new_file("EXTERNAL_RECONCILIATION.schema.json",
             (json.dumps(Reconciliation.model_json_schema(), indent=2) + "\n").encode())
    new_file("EXTERNAL_RECONCILIATION.json", encoded_reconciliation.encode())
    text = ["---", "status: reviewed_source_only", "legal_currentness: not_verified",
            "answer_safe: false", "---", "", "# Full native text with reviewed page context", "",
            "All native files remain unchanged. The display below removes only blank native lines "
            "between displayed paragraph portions; exact whitespace, UTF-8 ranges and line geometry "
            "remain in SOURCE_QA.json and candidate/page files. This is not a current-law answer.", ""]
    for page in pages:
        text += [f"## Physical page {page.physical_page}", ""]
        for paragraph in page.paragraphs:
            text += [f"### {paragraph.id} — {paragraph.logical_id}", ""]
            if paragraph.continuation_from:
                text += ["Continues " + paragraph.continuation_from + ".", ""]
            text += ["```text", paragraph.exact_native_text.rstrip("\n"), "```", ""]
    new_file("FULL_TEXT_WITH_CONTEXT.md", ("\n".join(text) + "\n").encode())
    sys.stdout.write(json.dumps({"source_qa_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                                "paragraph_portions": 54, "nonblank_lines": 170}) + "\n")


if __name__ == "__main__":
    main()
