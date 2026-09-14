"""Retired ownership must stay blocked through mapping, release and retrieval."""

from pathlib import Path

import pytest

from geode.orchestration.contracts import (
    AuthorityLevel,
    Citation,
    Evidence,
    Intent,
    Provenance,
    QueryState,
    RetrievalStep,
    RetrievalStrategyType,
)
from geode.orchestration.services.retrieval import LocalKnowledgeRetrievalBackend
from geode.pipeline.county_semantic_mapping import build_candidate_mappings
from geode.pipeline.local_promotion import (
    apply_local_promotion_decisions,
    build_local_promotion_queue,
)
from geode.pipeline.local_source_ownership import POLICY_PATH, OwnershipPolicy
from geode.pipeline.retrieval_catalog import build_retrieval_catalog
from geode.utils.file_io import atomic_write_json, atomic_write_jsonl, iter_jsonl
from tests.ownership_support import ownership_policy
from tests.test_conditional_evidence import _queue_row
from tests.test_county_semantic_mapping import _row
from tests.test_local_promotion import RULE_ID, _decision, _make_project


def test_retired_parent_cannot_reserve_mapping(tmp_path: Path) -> None:
    """Even an exact parent/hash match cannot override a source retirement."""

    candidate = _row("C-001", "Section 1")
    atomic_write_jsonl(tmp_path / "08_County_Authorities/_index.jsonl", [{
        "id": candidate["parent_rule_id"], "entity_type": "local_rule",
        "sha256": candidate["source_hash"], "source_id": "county_boulder_code",
    }], tmp_path)
    atomic_write_jsonl(tmp_path / "_CONTROL_PLANE/COUNTY_SEMANTIC_REVIEW_QUEUE.jsonl",
                       [candidate], tmp_path)
    assert build_candidate_mappings(tmp_path)["blocked"] == 1
    result = next(iter_jsonl(tmp_path / "_CONTROL_PLANE/COUNTY_SEMANTIC_CANDIDATE_MAP.jsonl"))
    assert result["permanent_rule_unit_id"] is None
    assert "retired source ownership" in result["mapping_reason"]


def test_manual_approval_cannot_override_retired_owner(tmp_path: Path) -> None:
    """A valid signed reviewer decision cannot release misowned source evidence."""

    _make_project(tmp_path)
    index = tmp_path / "08_County_Authorities/_index.jsonl"
    row = next(iter_jsonl(index))
    row["source_id"] = "county_boulder_code"
    atomic_write_jsonl(index, [row], tmp_path)
    assert build_local_promotion_queue(tmp_path)["queued"] == 0
    _decision(tmp_path)
    result = apply_local_promotion_decisions(tmp_path)
    assert result["promoted"] == 0
    assert any("retired source ownership" in item["error"] for item in result["errors"])
    unit = next(iter_jsonl(tmp_path / "08_County_Authorities/_meta/local_rule_units.jsonl"))
    assert unit["semantic_status"] != "semantic_ready"


@pytest.mark.parametrize("retired_location", ["candidate", "mapping"])
def test_conditional_route_excludes_retired_identity(
    tmp_path: Path, ownership_policy: OwnershipPolicy, retired_location: str
) -> None:
    """Conditional exposure cannot bypass either a retired candidate or stale map."""

    queue, mapping = _queue_row()
    if retired_location == "candidate":
        queue["review_id"] = ownership_policy.affected_review_ids[0]
        mapping["review_id"] = queue["review_id"]
    else:
        mapping["permanent_rule_unit_id"] = (
            ownership_policy.affected_parent_rule_ids[0] + "-UNIT-0999"
        )
    atomic_write_json(tmp_path / "_CONTROL_PLANE/MASTER_MANIFEST.json",
                      {"data_layers": []}, tmp_path)
    atomic_write_jsonl(tmp_path / "_CONTROL_PLANE/COUNTY_SEMANTIC_REVIEW_QUEUE.jsonl",
                       [queue], tmp_path)
    atomic_write_jsonl(tmp_path / "_CONTROL_PLANE/COUNTY_SEMANTIC_CANDIDATE_MAP.jsonl",
                       [mapping], tmp_path)
    assert build_retrieval_catalog(tmp_path)[0] == []


def _catalog_fixture(root: Path, blocked_id: str) -> list[dict[str, object]]:
    """Create a stale catalog containing one excluded and one legitimate city row."""

    rows = [{
        "id": blocked_id, "entity_type": "rule_unit", "authority_level": "county",
        "authority_id": "CO-COUNTY-BOULDER", "semantic_status": "semantic_ready",
        "title": "Owners need a permit", "retrieval_text": "Owners need a permit",
        "confidence": 0.9,
    }, {
        "id": "LOCAL-RULE-CO-MUNICIPAL-BOULDER-GOOD-UNIT-0001",
        "entity_type": "rule_unit", "authority_level": "municipal",
        "authority_id": "CO-MUNICIPAL-BOULDER", "semantic_status": "semantic_ready",
        "source_url": "https://bouldercolorado.gov/services/building-codes-and-regulations",
        "title": "Owners need a permit", "retrieval_text": "Owners need a permit",
        "confidence": 0.9,
    }]
    atomic_write_jsonl(root / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl", rows, root)
    return rows


def test_stale_catalog_search_and_graph_cannot_expose_retired_unit(
    tmp_path: Path, ownership_policy: OwnershipPolicy
) -> None:
    """Runtime filtering blocks stale ready units without suppressing the real city."""

    blocked_id = ownership_policy.affected_parent_rule_ids[0] + "-UNIT-0999"
    rows = _catalog_fixture(tmp_path, blocked_id)
    backend = LocalKnowledgeRetrievalBackend(tmp_path)
    state = QueryState(intent=Intent(raw_query="owners permit"))
    step = RetrievalStep(step_id="local", category_id="local_rules",
                         strategy=RetrievalStrategyType.DISCOVERY_SWEEP,
                         authority_level=AuthorityLevel.COUNTY, targets=["rule_unit"])
    assert backend.search(state, step) == []
    city_step = step.model_copy(update={"authority_level": AuthorityLevel.MUNICIPAL})
    assert [item.citation.canonical_id for item in backend.search(state, city_step)] == [
        rows[1]["id"]
    ]
    atomic_write_jsonl(tmp_path / "_CROSSWALKS/test.jsonl", [{
        "source_id": "CRS-TEST", "target_id": blocked_id, "relationship": "enables",
    }], tmp_path)
    evidence = Evidence(evidence_id="test", text="Owners need a permit", confidence=0.9,
                        citation=Citation(citation_text="CRS-TEST", canonical_id="CRS-TEST",
                                          authority_level=AuthorityLevel.STATE),
                        provenance=Provenance(source_id="CRS-TEST", source_path="test.jsonl"))
    assert backend.traverse(evidence, ["enables"]) == []


@pytest.mark.parametrize("broken", ["missing", "malformed"])
def test_missing_or_malformed_policy_prevents_local_release(
    tmp_path: Path, broken: str
) -> None:
    """Broken safeguards fail before local release writes or catalog exposure."""

    _make_project(tmp_path)
    _catalog_fixture(tmp_path, RULE_ID)
    path = tmp_path / POLICY_PATH
    path.unlink() if broken == "missing" else path.write_text('{"schema_version":1}')
    before = (tmp_path / "08_County_Authorities/_index.jsonl").read_bytes()
    with pytest.raises((FileNotFoundError, ValueError)):
        build_local_promotion_queue(tmp_path)
    state = QueryState(intent=Intent(raw_query="owners permit"))
    step = RetrievalStep(step_id="local", category_id="local_rules",
                         strategy=RetrievalStrategyType.DISCOVERY_SWEEP,
                         authority_level=AuthorityLevel.COUNTY, targets=["rule_unit"])
    with pytest.raises((FileNotFoundError, ValueError)):
        LocalKnowledgeRetrievalBackend(tmp_path).search(state, step)
    assert not (tmp_path / "_CONTROL_PLANE/LOCAL_PROMOTION_QUEUE.jsonl").exists()
    assert (tmp_path / "08_County_Authorities/_index.jsonl").read_bytes() == before
