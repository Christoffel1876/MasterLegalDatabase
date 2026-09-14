"""Write-once validated closure of the completed, handoff-only source review."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime

from review_models import Asset, Manifest, SourceQA, Strict

HERE = Path(__file__).resolve().parent


class Verification(Strict):
    """Measured validation and honest limits for this source review alone."""
    frozen_at: AwareDatetime
    status: Literal["complete_source_fidelity_review_pending_root_acceptance"]
    qa: Asset
    source_first: Asset
    transcript: Asset
    candidate: Asset
    tests: Asset
    rerender_validation: Asset
    source_pdf_sha256: str
    complete_source_pages: Literal[4]
    source_blocks: Literal[82]
    original_ocr_observations: Literal[181]
    original_candidate_bytes: Literal[9796]
    logical_table_rows: Literal[4]
    physical_table_fragments: Literal[5]
    prose_bullets: Literal[19]
    table_bullets: Literal[14]
    attachment_bullets: Literal[2]
    corrected_ocr_wording_blocks: Literal[5]
    tests_passed: Literal[15]
    in_memory_corruptions_rejected: Literal[14]
    exact_full_page_rerenders: Literal[4]
    source_first_review_was_blind: Literal[False]
    external_report_consulted: Literal[False]
    legal_currentness: Literal["not_verified"]
    adoption: Literal["not_verified"]
    original_acquisition_time: None
    repository_received_at: Literal["2026-09-11T19:01:59.855958Z"]
    selected_packet_subset_only: Literal[True]
    production_writes: Literal[0]
    public_requests: Literal[0]
    limitations: list[str]


def asset(name: str) -> Asset:
    """Measure exact bytes immediately before validated closure."""
    raw = (HERE/name).read_bytes()
    return Asset(path=name,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def save(name: str, value: Verification | Manifest) -> None:
    """Validate JSON before writing each new closed record and exported schema."""
    raw=value.model_dump_json(indent=2)+"\n"
    type(value).model_validate_json(raw)
    with (HERE/name).open("x") as handle:handle.write(raw)
    with (HERE/name.replace(".json",".schema.json")).open("x") as handle:
        handle.write(json.dumps(type(value).model_json_schema(),indent=2)+"\n")


def main() -> None:
    """Close only after actual complete tests and exact rerender logs exist."""
    qa=SourceQA.model_validate_json((HERE/"SOURCE_QA.json").read_bytes())
    tests=(HERE/"tests-final.log").read_text()
    if "15 passed" not in tests or "failed" in tests:
        raise ValueError("Final tests have not passed")
    result=json.loads((HERE/"rerender-validation.log").read_bytes())
    if result["status"]!="passed_complete_bounded_source_review" or not result["rerendered"]:
        raise ValueError("Complete source rerender has not passed")
    corrections=[b for b in qa.blocks if b.comparison=="ocr_correction_required"]
    if len(corrections)!=5:
        raise ValueError("Recorded OCR correction scope differs")
    verification=Verification(frozen_at=datetime.now(timezone.utc),
        status="complete_source_fidelity_review_pending_root_acceptance",
        qa=asset("SOURCE_QA.json"),source_first=asset("SOURCE_FIRST.json"),
        transcript=asset("REVIEWED_TRANSCRIPT.md"),candidate=asset("inputs/candidate.txt"),
        tests=asset("tests-final.log"),rerender_validation=asset("rerender-validation.log"),
        source_pdf_sha256=qa.source.sha256,complete_source_pages=4,source_blocks=82,
        original_ocr_observations=181,original_candidate_bytes=9796,logical_table_rows=4,
        physical_table_fragments=5,prose_bullets=19,table_bullets=14,attachment_bullets=2,
        corrected_ocr_wording_blocks=5,tests_passed=15,in_memory_corruptions_rejected=14,
        exact_full_page_rerenders=4,source_first_review_was_blind=False,
        external_report_consulted=False,legal_currentness="not_verified",adoption="not_verified",
        original_acquisition_time=None,repository_received_at="2026-09-11T19:01:59.855958Z",
        selected_packet_subset_only=True,production_writes=0,public_requests=0,
        limitations=[
            "Complete source-fidelity review of this four-page staff memo only; "
            "the referenced attachments are absent.",
            "No current law, adopted fees, legal applicability or fee calculation is certified.",
            "Review chronology is recorded by the agent; "
            "not independently authenticated blindness.",
            "Reviewed wording normalizes declared typography and wrapping, not original OCR bytes.",
            "The original candidate, raw engine results and source-first freeze remain unchanged.",
            "The complete parent packet manifest names other source artifacts outside this subset.",
            "Root unfinished notes were consulted after direct source "
            "and current-phase OCR review.",
            "No external Ebenezer report or Spanish source was consulted. "
            "No public requests or production writes.",
        ])
    save("VERIFICATION.json",verification)
    files=[asset(p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob("*")) if p.is_file()]
    save("FINAL_MANIFEST.json",Manifest(frozen_at=datetime.now(timezone.utc).isoformat(),
        status="complete_source_fidelity_review_pending_root_acceptance",files=files))


if __name__=="__main__":
    main()
