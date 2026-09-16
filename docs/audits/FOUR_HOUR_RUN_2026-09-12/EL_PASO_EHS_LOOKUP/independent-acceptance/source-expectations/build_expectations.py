"""Create a finite, source-derived expectation set without reading a new adapter draft."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from expectation_models import Case, Context, Evidence, Expectations, Inventory, Row

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "MasterLegalDatabase"
PACKAGE = "research/local_review/el-paso-ehs-fees-source-qa-2026-09-13"


def save(path: Path, data: bytes) -> None:
    """Write new evidence atomically and never replace existing bytes."""
    if path.exists():
        raise ValueError("Expectation files are immutable")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(data)
    os.replace(temporary, path)


def ref(path: Path, label: str) -> Evidence:
    """Hash an ordinary local file."""
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("Nonordinary evidence")
    return Evidence(path=label, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    size_bytes=path.stat().st_size)


def main() -> None:
    """Freeze manually selected source cases, complete source rows and linked clauses."""
    package = REPO / PACKAGE
    data = json.loads((package / "SOURCE_QA.json").read_bytes())
    rows = {value["row_id"]: Row.model_validate(value) for value in data["rows"]}
    context = {value["context_id"]: Context.model_validate(value) for value in data["contexts"]}
    cases = []

    def case(number: int, query: str | None, row_ids: list[str], purpose: str,
             prohibited: list[str] | None = None, contexts: list[str] | None = None,
             kind: str = "rows", mode: str = "source", source: str | None = None,
             forbidden: dict[str, list[str]] | None = None) -> None:
        selected = [rows[value] for value in row_ids]
        needed = set(contexts or [])
        for row in selected:
            needed.update(row.linked_context)
        cases.append(Case(id=f"EHS-{number:02d}", purpose=purpose,
            source_id=source or "el-paso-boh-ehs-fees-sd011", query=query,
            list_rows=query is None, mode=mode, expected_kind=kind,
            expected_exit=(1 if source else 2) if kind == "refused" else 0,
            expected_rows=selected,
            required_context=[value for key, value in context.items() if key in needed],
            directly_matched_context_ids=contexts or [],
            forbidden_context_links=forbidden or {}, prohibited_inferences=prohibited or [],
            expected_evidence_verified=kind != "refused"))

    case(1, "Property Sale", ["R031", "R032"], "Keep the two physical sale-review rows separate.",
         ["Do not choose a present-day price or assign the 2025 amount to the additional-system row."])
    case(2, "211.50", ["R031"], "Return the entire $211.50 in 2024 ($368 in 2025) cell.",
         ["No loss of either year or amount; no replacement with a single numeric fee."])
    case(3, "368", ["R031"], "Searching the 2025 amount retains its complete 2024/2025 source cell.")
    case(4, "281.00", ["R032"], "The additional-system fee says $281.00 in 2024 only.",
         ["Do not extend it to 2025, 2026 or current applicability."])
    case(5, "complaint investigations", [], "An investigation no-fee note is context only.",
         ["Do not generate a $0 fee row, expose all 65 rows as matches, or generalize a waiver."],
         ["OTHER2"], "context_only")
    case(6, "communicable disease", [], "Preserve the second no-fee investigation category.",
         ["Do not create an unconditional zero-fee schedule."], ["OTHER2"], "context_only")
    case(7, "Section 2", [], "Return full paragraph B with its unresolved Section 2 exception.",
         ["Do not resolve Section 2, make the maximum mandatory, or calculate a penalty."],
         ["B"], "context_only")
    case(8, "100 per day", [], "Preserve not more than, until paid in full, and the Section 2 exception.",
         ["The $100 is a civil-penalty maximum in context, not a service fee row."], ["B"], "context_only")
    case(9, "Retail Food Establishment License", ["R056"],
         "The fee cell is the literal statutory reference Per Section 25-4-1607 C.R.S.",
         ["Do not provide a dollar amount, fetch the cited statute, or claim a current license fee."])
    case(10, "25-4-1607", ["R056"], "A citation search preserves the reference-only fee cell.")
    case(11, "OWTS New Permit", ["R020"], "Preserve the $961.00 fee, asterisk and one-reinspection note.",
         ["Do not attach the included reinspection to every OWTS permit."])
    case(12, "OWTS Reinspection", ["R033"], "Preserve $338.00 and the complete definition (7).",
         ["Keep the closing quote anomaly, additional revisit/inspection wording and well/electrical example."])
    case(13, "OWTS Major Repair", ["R022"], "Preserve $891.00 and explicit definition (5).")
    case(14, "OWTS Minor Repair", ["R023"], "Preserve $554.00 and definition (6) including its exception.",
         ["Do not drop tank baffles, collapsed lines or the as-built drawings limitation."])
    case(15, "Review of Potential Retail Food", ["R051"],
         "Preserve $62.00 per hour, $75.00 maximum and explicit onsite-evaluation definition (1).")
    case(16, "Change of Ownership Inspection", ["R052", "R053"],
         "Keep initial/additional $120/$65 rows separate, both linked to full definition (2).")
    case(17, "HACCP Plan Review", ["R059", "R060"],
         "Keep written and operational rows distinct despite equal $62 hourly/$100 maximum fees.",
         ["Do not swap or merge definitions (3) and (4)."])
    case(18, "Residential / Day Treatment", ["R019"],
         "Retain $282.00 without inventing the routine-inspection classification.",
         ["Complete contextual Childcare definitions may be shown, but no CHILD1 row link may be inferred."],
         forbidden={"R019": ["CHILD1"]})
    case(19, "Special Event Permit", ["R057", "R058"],
         "Retain two stacked amounts for each menu type with their exact event associations.",
         ["Do not add for to $298.00 1 Event or attribute packaging slashes to the source."])
    case(20, "per-visit", [], "Return the complete general per-visit note as context.",
         ["Do not infer precedence over six-month, two-year, hourly or per-person cells."],
         ["OTHER1"], "context_only")
    case(21, None, list(rows), "Return exactly 65 service rows, seven groups and all 37 context records.",
         ["No duplicated context-derived fee rows and no merged-null cells promoted to fees."], list(context))
    case(22, "absent-service-zzq", [], "No matching source passage is not a completeness claim.",
         ["Do not assert that no such regulation or fee exists anywhere."], kind="no_match")
    case(23, "OWTS", [], "Explicit current-law mode must refuse before claiming verified evidence.",
         kind="refused", mode="current-law")
    case(24, "What fee applies today?", [], "Question/applicability language must refuse in default mode.",
         kind="refused")
    case(25, "OWTS", [], "The separate Spanish source must remain unsupported.",
         ["No fallback to English and no translation-equivalence claim."], kind="refused",
         source="el-paso-boh-ehs-fees-spanish-sd011")

    input_refs = []
    for name in ["SOURCE_QA.json", "SOURCE_QA.schema.json", "CUSTODY.json", "FINAL_MANIFEST.json"]:
        source = package / name
        save(HERE / "frozen-inputs" / name, source.read_bytes())
        input_refs.append(ref(source, PACKAGE + "/" + name))
    interface = REPO / "scripts/research_source_lookup.py"
    save(HERE / "frozen-inputs" / "existing-six-source-interface.py", interface.read_bytes())
    input_refs.append(ref(interface, "scripts/research_source_lookup.py"))
    for name in ["validate_review.py", "build_review.py", "review_models.py", "source/original.pdf",
                 "candidate.txt"]:
        input_refs.append(ref(package / name, PACKAGE + "/" + name))

    result = Expectations(recorded_at=datetime.now(timezone.utc),
        status="source_expectations_frozen_before_new_adapter_review",
        source_id="el-paso-boh-ehs-fees-sd011", authority_id="CO-COUNTY-EL_PASO",
        issuer="El Paso County Board of Health", administering_agency="El Paso County Public Health",
        source_sha256=data["source"]["sha256"], package_repo_path=PACKAGE, inputs=input_refs, cases=cases,
        shared_requirements=[
            "Successful row results preserve each full service/fee string, physical page, source group and exact source/native binding.",
            "Each row retains A, B, OTHER1, OTHER2, OTHER3 and its explicit group/marker/definition links.",
            "Return complete passages, not numeric fee calculations or truncated exception snippets.",
            "Context searches do not automatically select all rows linked to a general note.",
            "Preserve 2024/2025 cell years, printed October 25, 2023 approval and January 1, 2024 effective claims without certifying their legal status.",
            "Legal currentness remains not_verified; English review is not translation verification.",
            "Declaring evidence verified means bounded source/hash/association verification, not all El Paso fees or laws.",
            "Tampering with source, candidate, native spans, group, exception links, custody or dependent verifier code must fail before a successful result.",
        ], custody_requirements=[
            "Authority is CO-COUNTY-EL_PASO; issuer is Board of Health and administrator is Public Health, not Colorado Springs municipal government.",
            "Acquisition method remains received_review_package; original HTTP acquisition was not independently witnessed.",
            "Actual repository receipt 2026-09-12T22:59:48.795762Z is not original source acquisition time.",
            "URL 2025/06 and accessibility-check filename are not verified publication, adoption or effective dates.",
            "Historical Sherlock target-cap and lost non-PDF-body qualifications remain available and are not repaired by lookup acceptance.",
        ], untouched_scope=[
            "No new source/PDF visual review, network request, production edit or canonical mutation.",
            "Expectations come from accepted source QA and the pre-existing six-source CLI, before examination of the new adapter draft.",
            "This is not a blind source transcription, external model-diversity review or proof of historical reviewer chronology.",
        ])
    encoded=(result.model_dump_json(indent=2)+"\n").encode()
    Expectations.model_validate_json(encoded)
    save(HERE / "EXPECTATIONS.json", encoded)
    save(HERE / "EXPECTATIONS.schema.json",
         (json.dumps(Expectations.model_json_schema(), indent=2)+"\n").encode())
    print(hashlib.sha256(encoded).hexdigest())


if __name__ == "__main__":
    main()
