"""Active parent ownership and exact candidate mappings gate local release."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from geode.pipeline.county_semantic_mapping import build_candidate_mappings
from geode.pipeline.local_promotion import (
    apply_local_promotion_decisions,
    build_local_promotion_queue,
    main as promotion_main,
)
from geode.pipeline.local_release_ownership import ownership_reason_with_parents
from geode.pipeline.local_source_ownership import OwnershipPolicy
from geode.pipeline.retrieval_catalog import build_retrieval_catalog, main as catalog_main
from geode.utils.file_io import atomic_write_json, atomic_write_jsonl, iter_jsonl
from tests.ownership_support import ownership_policy
from tests.test_conditional_evidence import _queue_row
from tests.test_local_promotion import RULE_ID, _decision, _make_project

PARENT = "LOCAL-RULE-CO-COUNTY-TEST"
INDEX = "08_County_Authorities/_index.jsonl"
QUEUE = "_CONTROL_PLANE/COUNTY_SEMANTIC_REVIEW_QUEUE.jsonl"
MAPPING = "_CONTROL_PLANE/COUNTY_SEMANTIC_CANDIDATE_MAP.jsonl"


def _write(root: Path, relative: str, rows: list[dict]) -> None:
    atomic_write_jsonl(root / relative, rows, root)


def _parent(**updates: object) -> dict:
    return {"id": PARENT, "entity_type": "local_rule", "sha256": "a" * 64, **updates}


def _conditional(root: Path) -> tuple[dict, dict]:
    queue, mapping = _queue_row()
    atomic_write_json(root / "_CONTROL_PLANE/MASTER_MANIFEST.json", {"data_layers": []}, root)
    _write(root, QUEUE, [queue])
    _write(root, MAPPING, [mapping])
    return queue, mapping


@pytest.mark.parametrize("row", [
    {"id": PARENT + "-UNIT-0001"},
    {"id": "CONDITIONAL-COUNTY-SEM-" + PARENT + "_RU_0001"},
    {"id": "opaque-child", "parent_regulation_id": PARENT},
    {"source_metadata": {"parent_rule_id": PARENT}},
    {"candidate_rule_unit_id": "opaque-child"},
])
def test_follows_only_explicit_or_documented_active_parents(
    ownership_policy: OwnershipPolicy, row: dict,
) -> None:
    """Renamed parent IDs cannot hide a retired source or an active parent chain."""
    active = {
        PARENT: _parent(source_id="county_boulder_code"),
        "opaque-child": {"id": "opaque-child", "parent_rule_id": PARENT},
    }
    assert "retired source" in ownership_reason_with_parents(ownership_policy, row, active)
    assert ownership_reason_with_parents(
        ownership_policy, {"id": PARENT + "-UNIT-0001-other"}, active
    ) is None


def test_parent_cycles_terminate_and_do_not_hide_another_branch(
    ownership_policy: OwnershipPolicy,
) -> None:
    """Cycles have no ownership effect and must not stop other references being checked."""
    a = {"id": "a", "parent_rule_id": "b"}
    b = {"id": "b", "parent_rule_id": "a"}
    a["metadata"] = a
    active = {"a": a, "b": b}
    assert ownership_reason_with_parents(ownership_policy, {"id": "a"}, active) is None
    b["parent_regulation_id"] = PARENT
    active[PARENT] = _parent(source_id="county_boulder_code")
    assert ownership_reason_with_parents(ownership_policy, {"id": "a"}, active)


@pytest.mark.parametrize("explicit_parent", [False, True])
def test_retired_active_parent_blocks_queue_approval_and_catalog(
    tmp_path: Path, explicit_parent: bool,
) -> None:
    """Even reviewer-approved children remain excluded by their present parent metadata."""
    _make_project(tmp_path)
    rows = list(iter_jsonl(tmp_path / INDEX))
    if explicit_parent:
        rows[0]["parent_regulation_id"] = PARENT
    _write(tmp_path, INDEX, [*rows, _parent(source_id="county_boulder_code")])
    atomic_write_json(tmp_path / "_CONTROL_PLANE/MASTER_MANIFEST.json", {"data_layers": [
        {"id": "08_County_Authorities", "index_file": INDEX},
    ]}, tmp_path)
    assert build_local_promotion_queue(tmp_path)["queued"] == 0
    _decision(tmp_path)
    result = apply_local_promotion_decisions(tmp_path)
    assert result["promoted"] == 0
    assert "retired source" in result["errors"][0]["error"]
    assert build_retrieval_catalog(tmp_path)[0] == []
    meta = tmp_path / "08_County_Authorities/_meta/local_rule_units.jsonl"
    assert next(iter_jsonl(meta))["semantic_status"] == "needs_review"


def test_blocked_parent_mapping_has_no_conditional_fallback(tmp_path: Path) -> None:
    """A real blocked mapping remains blocked through the catalog build."""
    _conditional(tmp_path)
    _write(tmp_path, INDEX, [_parent(source_id="county_boulder_code")])
    assert build_candidate_mappings(tmp_path)["blocked"] == 1
    assert build_retrieval_catalog(tmp_path)[0] == []


@pytest.mark.parametrize("key,value", [
    ("mapping_status", "blocked"), ("mapping_status", "unknown"),
    ("permanent_rule_unit_id", None), ("permanent_rule_unit_id", "UNRELATED-UNIT-0001"),
    ("candidate_rule_unit_id", "different-candidate"), ("review_id", "different-review"),
    ("parent_regulation_id", "different-parent"), ("source_hash", "b" * 64),
    ("source_hash", "invalid"), ("source_section", "different-section"),
    ("mapping_status", "mapped_existing"),
])
def test_stale_or_invalid_mapping_is_not_conditionally_citable(
    tmp_path: Path, key: str, value: object,
) -> None:
    """Every identity component must match, not just the review key."""
    _, mapping = _conditional(tmp_path)
    mapping[key] = value
    _write(tmp_path, MAPPING, [mapping])
    assert build_retrieval_catalog(tmp_path)[0] == []


@pytest.mark.parametrize("conflict", [
    "missing-map", "duplicate-map", "duplicate-review", "duplicate-candidate", "reserved-id",
    "candidate-parent", "row-parent", "parent-hash", "parent-owner", "unit-parent",
    "unit-hash", "unit-section", "unit-type", "unit-conflicting-parent",
])
def test_current_bindings_and_unique_reservations_are_required(
    tmp_path: Path, conflict: str,
) -> None:
    """Stale active identities and duplicate queue/map entries cannot revive evidence."""
    queue, mapping = _conditional(tmp_path)
    if conflict == "missing-map":
        (tmp_path / MAPPING).unlink()
    elif conflict == "duplicate-map":
        _write(tmp_path, MAPPING, [mapping, deepcopy(mapping)])
    elif conflict == "duplicate-review":
        _write(tmp_path, QUEUE, [queue, deepcopy(queue)])
    elif conflict in {"duplicate-candidate", "reserved-id"}:
        other_queue, other_mapping = deepcopy(queue), deepcopy(mapping)
        other_queue["review_id"] = other_mapping["review_id"] = "REVIEW-2"
        if conflict == "reserved-id":
            other_queue["candidate_rule_unit"]["id"] = "other-candidate"
            other_mapping["candidate_rule_unit_id"] = "other-candidate"
        else:
            other_mapping["permanent_rule_unit_id"] = PARENT + "-UNIT-0002"
        _write(tmp_path, QUEUE, [queue, other_queue])
        _write(tmp_path, MAPPING, [mapping, other_mapping])
    elif conflict in {"candidate-parent", "row-parent"}:
        target = queue["candidate_rule_unit"] if conflict == "candidate-parent" else queue
        target["parent_regulation_id"] = "different-parent"
        _write(tmp_path, QUEUE, [queue])
    elif conflict.startswith("parent-"):
        updates = {"sha256": "b" * 64} if conflict == "parent-hash" else {
            "source_id": "county_boulder_code",
        }
        _write(tmp_path, INDEX, [_parent(**updates)])
    else:
        unit = {
            "id": mapping["permanent_rule_unit_id"], "entity_type": "rule_unit",
            "parent_regulation_id": PARENT, "sha256": "a" * 64, "source_section": "Section 1",
        }
        key = {"unit-parent": "parent_regulation_id", "unit-hash": "sha256",
               "unit-conflicting-parent": "parent_rule_id",
               "unit-section": "source_section", "unit-type": "entity_type"}[conflict]
        unit[key] = "different"
        _write(tmp_path, INDEX, [unit])
    assert build_retrieval_catalog(tmp_path)[0] == []


@pytest.mark.parametrize("status", ["planned_new", "mapped_existing"])
def test_valid_conditional_mapping_retains_identity_provenance(
    tmp_path: Path, status: str,
) -> None:
    """Usable conditional evidence keeps the identities needed for later rechecks."""
    queue, mapping = _conditional(tmp_path)
    queue["source_id"] = "county_test"
    queue["final_url"] = queue["source_url"]
    mapping["mapping_status"] = status
    _write(tmp_path, QUEUE, [queue])
    _write(tmp_path, MAPPING, [mapping])
    if status == "mapped_existing":
        _write(tmp_path, INDEX, [_parent(), {
            "id": mapping["permanent_rule_unit_id"], "entity_type": "rule_unit",
            "sha256": "a" * 64, "source_section": "Section 1",
        }])
    records, _ = build_retrieval_catalog(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert record.answer_mode == "conditional" and record.semantic_status == "needs_review"
    assert record.parent_rule_id == record.parent_regulation_id == PARENT
    assert record.review_id == "REVIEW-1"
    assert record.candidate_rule_unit_id == queue["candidate_rule_unit"]["id"]
    assert record.permanent_rule_unit_id == mapping["permanent_rule_unit_id"]
    assert record.source_id == "county_test" and record.final_url == queue["source_url"]


def test_index_catalog_retains_source_parent_and_review_fields(tmp_path: Path) -> None:
    """Catalog compaction must not discard the source's recorded ownership identities."""
    _make_project(tmp_path)
    rows = list(iter_jsonl(tmp_path / INDEX))
    fields = {
        "source_id": "county_test", "parent_regulation_id": PARENT, "parent_rule_id": PARENT,
        "review_id": "review-1", "candidate_rule_unit_id": "candidate-1",
        "permanent_rule_unit_id": RULE_ID, "mapping_status": "mapped_existing",
        "url": "https://county.example.gov/one", "requested_url": "https://county.example.gov/one",
        "final_url": "https://county.example.gov/two",
        "discovery_parent_url": "https://county.example.gov/",
    }
    rows[0].update(fields)
    _write(tmp_path, INDEX, rows)
    atomic_write_json(tmp_path / "_CONTROL_PLANE/MASTER_MANIFEST.json", {"data_layers": [
        {"id": "08_County_Authorities", "index_file": INDEX},
    ]}, tmp_path)
    record = build_retrieval_catalog(tmp_path)[0][0].model_dump()
    assert all(record[key] == value for key, value in fields.items())


@pytest.mark.parametrize("updates,reason", [
    ({"source_section": "Document-level source"}, "exact legal section"),
    ({"source_page": None, "source_line_start": None}, "page or line provenance"),
    ({"regulated_entity": "Not separately specified"}, "regulated entity"),
    ({"plain_english_summary": "Source section preserved"}, "placeholder"),
    ({"rule_type": "invented-rule-type"}, "schema validation"),
])
def test_ownership_gate_preserves_existing_semantic_rejection_rules(
    tmp_path: Path, updates: dict, reason: str,
) -> None:
    """Passing ownership does not waive the original semantic evidence requirements."""
    _make_project(tmp_path)
    _decision(tmp_path, **updates)
    result = apply_local_promotion_decisions(tmp_path)
    assert result["promoted"] == 0 and result["blocked"] == 1
    assert reason in result["errors"][0]["error"]


@pytest.mark.parametrize("decision", ["reject", "needs_revision"])
def test_negative_review_never_promotes(tmp_path: Path, decision: str) -> None:
    """Negative reviews remain pending even when all positive schema checks would pass."""
    _make_project(tmp_path)
    _decision(tmp_path, decision=decision)
    result = apply_local_promotion_decisions(tmp_path)
    assert result["promoted"] == 0
    assert result["rejected" if decision == "reject" else "needs_revision"] == 1


def test_missing_active_unit_and_invalid_decision_do_not_promote(tmp_path: Path) -> None:
    """Neither a disconnected unit nor malformed reviewer data can authorize release."""
    _make_project(tmp_path)
    _write(tmp_path, INDEX, [])
    _decision(tmp_path)
    result = apply_local_promotion_decisions(tmp_path)
    assert "not present in the active index" in result["errors"][0]["error"]
    path = tmp_path / "08_County_Authorities/_meta/local_rule_units.jsonl"
    before = path.read_bytes()
    _write(tmp_path, "_CONTROL_PLANE/LOCAL_PROMOTION_DECISIONS.jsonl", [{"decision": "approve"}])
    result = apply_local_promotion_decisions(tmp_path)
    assert result["promoted"] == 0 and result["errors"][0]["line"] == "1"
    assert path.read_bytes() == before and result["snapshots"] == []


@pytest.mark.parametrize("apply", [False, True])
def test_promotion_cli_keeps_retired_parent_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, apply: bool,
) -> None:
    """The public CLI uses the same parent gate for queue construction and decisions."""
    _make_project(tmp_path)
    rows = list(iter_jsonl(tmp_path / INDEX))
    _write(tmp_path, INDEX, [*rows, _parent(source_id="county_boulder_code")])
    _decision(tmp_path)
    monkeypatch.setattr("sys.argv", ["promotion", "--root", str(tmp_path), *(
        ["--apply"] if apply else []
    )])
    assert promotion_main() == 0
    output = capsys.readouterr().out
    assert "'promoted': 0" in output if apply else "'queued': 0" in output


@pytest.mark.parametrize("ready", [False, True])
def test_existing_unit_is_not_duplicated_as_ready_conditional_evidence(
    tmp_path: Path, ready: bool,
) -> None:
    """An existing ready unit suppresses its candidate; pending units retain conditional IDs."""
    queue, mapping = _conditional(tmp_path)
    mapping["mapping_status"] = "mapped_existing"
    _write(tmp_path, MAPPING, [mapping])
    _write(tmp_path, INDEX, [_parent(), {
        "id": mapping["permanent_rule_unit_id"], "entity_type": "rule_unit",
        "sha256": "a" * 64, "source_section": "Section 1",
        "semantic_status": "semantic_ready" if ready else "needs_review",
    }])
    atomic_write_json(tmp_path / "_CONTROL_PLANE/MASTER_MANIFEST.json", {"data_layers": [
        {"id": "08_County_Authorities", "index_file": INDEX},
    ]}, tmp_path)
    conditional = [
        r for r in build_retrieval_catalog(tmp_path)[0] if r.answer_mode == "conditional"
    ]
    assert len(conditional) == (0 if ready else 1)
    if conditional:
        assert conditional[0].id == "CONDITIONAL-" + queue["candidate_rule_unit"]["id"]
    assert build_local_promotion_queue(tmp_path)["queued"] == (0 if ready else 1)


@pytest.mark.parametrize("name,expected", [
    ("", None), ("City and County of Denver", ["Denver County"]), ("Test", ["Test County"]),
])
def test_conditional_geography_remains_source_qualified(
    tmp_path: Path, name: str, expected: list[str] | None,
) -> None:
    """Missing authority names never acquire an invented county label."""
    queue, _ = _conditional(tmp_path)
    queue["authority_name"] = name
    _write(tmp_path, QUEUE, [queue])
    assert build_retrieval_catalog(tmp_path)[0][0].county_names == expected


@pytest.mark.parametrize("write", [False, True])
def test_catalog_cli_preserves_safe_conditional_without_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, write: bool,
) -> None:
    """Preview and write modes retain conditional status and exact provenance."""
    _conditional(tmp_path)
    monkeypatch.setattr("sys.argv", ["catalog", "--root", str(tmp_path), *(
        ["--write", "--json"] if write else []
    )])
    catalog_main()
    output = capsys.readouterr().out
    if write:
        assert json.loads(output)["records_written"] == 1
        record = next(iter_jsonl(tmp_path / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl"))
        assert record["answer_mode"] == "conditional" and record["review_id"] == "REVIEW-1"
    else:
        assert "Retrieval catalog records: 1" in output
        assert not (tmp_path / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl").exists()
