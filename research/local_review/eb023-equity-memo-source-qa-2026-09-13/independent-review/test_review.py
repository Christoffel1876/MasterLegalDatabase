"""Bounded in-memory corruptions must fail without changing original evidence."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import validate_review as review

HERE = Path(__file__).resolve().parent


def baseline() -> dict:
    """Load the unchanged typed review for a fresh isolated mutation."""
    return json.loads((HERE / "SOURCE_QA.json").read_bytes())


def test_complete_review() -> None:
    """All pages, raw OCR bytes and complete physical/logical table associations replay."""
    result = review.verify_content(baseline())
    assert result["source_blocks"] == 82
    assert result["ocr_observations"] == 181
    assert result["logical_table_rows"] == 4


@pytest.mark.parametrize("case", [
    "drop_bullet", "rewrite_source", "tier2_continuation", "swap_fee", "remove_dnr",
    "drop_road_exception", "wrong_byte_offset", "fix_raw_ocr", "invent_acquisition",
    "current_law", "erase_shared_line", "wrong_image", "reverse_phase", "wrong_owner",
])
def test_corruption_refused(case: str) -> None:
    """Reject content, scope and byte-binding changes independently of the final manifest."""
    data = copy.deepcopy(baseline())
    if case == "drop_bullet":
        data["blocks"] = [b for b in data["blocks"] if b["id"] != "P2-B8"]
    elif case == "rewrite_source":
        next(b for b in data["blocks"] if b["id"]=="P4-A1")["text"] = "January 2, 2024"
    elif case == "tier2_continuation":
        data["table_fragments"][2]["logical_row"] = "TIER3"
    elif case == "swap_fee":
        data["table_rows"][0]["fee_text"] = data["table_rows"][1]["fee_text"]
    elif case == "remove_dnr":
        data["table_rows"][1]["dnr_footnote"] = None
    elif case == "drop_road_exception":
        data["table_rows"][3]["characteristics"] = data["table_rows"][3]["characteristics"][:1]
    elif case == "wrong_byte_offset":
        data["pages"][3]["observations"][0]["candidate_span"]["start"] += 1
    elif case == "fix_raw_ocr":
        data["pages"][3]["observations"][12]["text"] = "(>1500"
    elif case == "invent_acquisition":
        data["provenance"]["original_acquisition_at"] = "2026-09-13T04:40:00Z"
    elif case == "current_law":
        data["legal_currentness"] = "verified"
    elif case == "erase_shared_line":
        data["pages"][3]["observations"][18]["reviewed_block_ids"] = ["P4-T3-C3"]
    elif case == "wrong_image":
        data["pages"][3]["image"] = data["pages"][0]["image"]
    elif case == "reverse_phase":
        data["reviewed_at"] = "2020-01-01T00:00:00Z"
    elif case == "wrong_owner":
        data["authority_id"] = "CO-MUNICIPAL-LARIMER"
    with pytest.raises((ValueError, KeyError)):
        review.verify_content(data)
