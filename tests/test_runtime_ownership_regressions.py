"""Runtime regressions found by independent ownership-gate review."""

from pathlib import Path

import pytest

from geode.orchestration.contracts import (
    AuthorityLevel, Citation, Evidence, Intent, Provenance, QueryState,
    RetrievalStep, RetrievalStrategyType,
)
from geode.orchestration.services.retrieval import LocalKnowledgeRetrievalBackend
from geode.pipeline.local_source_ownership import POLICY_PATH
from geode.utils.file_io import atomic_write_jsonl
from tests.ownership_support import ownership_policy


def _step(level: AuthorityLevel) -> RetrievalStep:
    """Create a simple legal-text search step."""

    return RetrievalStep(step_id="owners", category_id="rules",
                         strategy=RetrievalStrategyType.DISCOVERY_SWEEP,
                         authority_level=level)


def _state_row() -> dict[str, object]:
    """Build a standalone state record unrelated to local ownership."""

    return {"id": "CRS-TEST", "entity_type": "statute_section", "authority_level": "state",
            "retrieval_text": "Owners need a permit", "confidence": 0.9}


@pytest.mark.parametrize("local_first", [True, False])
def test_state_query_ignores_unrelated_local_policy_failure(
    tmp_path: Path, local_first: bool
) -> None:
    """A broken local policy must not abort an unrelated state-only query."""

    (tmp_path / POLICY_PATH).unlink()
    local = {"id": "LOCAL-RULE-COUNTY-TEST", "authority_level": "county",
             "entity_type": "rule_unit", "semantic_status": "semantic_ready",
             "retrieval_text": "Owners need a permit"}
    rows = [local, _state_row()] if local_first else [_state_row(), local]
    atomic_write_jsonl(tmp_path / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl", rows, tmp_path)
    result = LocalKnowledgeRetrievalBackend(tmp_path).search(
        QueryState(intent=Intent(raw_query="owners permit")), _step(AuthorityLevel.STATE)
    )
    assert [item.citation.canonical_id for item in result] == ["CRS-TEST"]


@pytest.mark.parametrize("city_owner", [False, True])
def test_graph_rechecks_cached_origin_against_current_catalog(
    tmp_path: Path, city_owner: bool
) -> None:
    """A cached misowned alias cannot escape through a valid state target."""

    origin_id = "LOCAL-RULE-ALIASED-UNIT-0001"
    level = AuthorityLevel.MUNICIPAL if city_owner else AuthorityLevel.COUNTY
    url = "https://bouldercolorado.gov/services/building-codes-and-regulations"
    origin = {"id": origin_id, "entity_type": "rule_unit", "authority_level": level.value,
              "authority_id": "CO-MUNICIPAL-BOULDER" if city_owner else "CO-COUNTY-BOULDER",
              "source_url": url, "semantic_status": "semantic_ready"}
    atomic_write_jsonl(tmp_path / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl",
                       [origin, _state_row()], tmp_path)
    atomic_write_jsonl(tmp_path / "_CROSSWALKS/links.jsonl", [{
        "source_id": origin_id, "target_id": "CRS-TEST", "relationship": "enables",
    }], tmp_path)
    cached = Evidence(evidence_id="cached", text="Owners need a permit", confidence=0.9,
                      citation=Citation(citation_text=origin_id, canonical_id=origin_id,
                                        authority_level=level),
                      provenance=Provenance(source_id=origin_id, source_path="old.jsonl",
                                            source_url=url))
    reached = LocalKnowledgeRetrievalBackend(tmp_path).traverse(cached, ["enables"])
    assert len(reached) == int(city_owner)


def test_search_follows_active_parent_of_unlisted_child_alias(tmp_path: Path) -> None:
    """A child's old ready flag cannot hide its presently retired parent source."""

    parent = "LOCAL-RULE-ALIASED"
    child = parent + "-UNIT-0001"
    row = {"id": child, "entity_type": "rule_unit", "authority_level": "county",
           "semantic_status": "semantic_ready", "retrieval_text": "Owners need a permit"}
    atomic_write_jsonl(tmp_path / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl", [row], tmp_path)
    atomic_write_jsonl(tmp_path / "08_County_Authorities/_index.jsonl", [{
        "id": parent, "entity_type": "local_rule", "source_id": "county_boulder_code",
    }], tmp_path)
    result = LocalKnowledgeRetrievalBackend(tmp_path).search(
        QueryState(intent=Intent(raw_query="owners permit")), _step(AuthorityLevel.COUNTY)
    )
    assert result == []
