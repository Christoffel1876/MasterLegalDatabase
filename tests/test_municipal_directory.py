"""Municipal directory identities must retain evidence and honest acquisition dates."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from geode.pipeline import municipal_directory as directory


def fixture(root: Path, items: str) -> Path:
    """Create a bounded archived CML list and an identity-only registry."""
    archive = root / directory.CML_RAW_PATH
    archive.parent.mkdir(parents=True)
    archive.write_text(
        f"<h2>Links to Colorado cities and towns</h2><ul>{items}</ul>Updated May 6, 2024",
        encoding="utf-8",
    )
    registry = root / "_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"pilot": {"municipalities": [
        {"name": "Town of Sheridan Lake", "authority_id": "CO-MUNICIPAL-SHERIDAN_LAKE"},
    ]}}), encoding="utf-8")
    return archive


def output(root: Path) -> dict:
    """Read the generated control-plane fixture through its actual schema."""
    path = root / directory.OUTPUT_PATH
    return directory.MunicipalExpansionQueue.model_validate_json(
        path.read_bytes()
    ).model_dump(mode="json")


def test_sheriden_typo_is_normalized_to_census_municipality_without_exclusion(
    tmp_path: Path,
) -> None:
    archive = fixture(tmp_path, '<li><a href="https://example.org/">Sheriden Lake *</a></li>')
    before = archive.read_bytes()
    result = directory.materialize_municipal_expansion_queue(tmp_path)
    assert result == {"directory_entries": 1, "registered": 1, "not_registered": 0}
    data = output(tmp_path)
    entry = data["entries"][0]
    assert entry["name"] == "Sheridan Lake" and entry["source_name"] == "Sheriden Lake"
    assert entry["authority_id"] == "CO-MUNICIPAL-SHERIDAN_LAKE"
    assert entry["normalization_evidence_url"] == directory.CENSUS_REFERENCE_URL
    assert data["excluded_non_municipal_entries"] == []
    assert archive.read_bytes() == before


def test_spelling_aliases_deduplicate_and_unregistered_names_are_retained(tmp_path: Path) -> None:
    fixture(tmp_path, '<li>Sheriden Lake</li><li>Sheridan Lake</li><li>SHERIDAN LAKE</li>'
            '<li><a href="/town">New &amp; Town</a></li><li> </li>')
    result = directory.materialize_municipal_expansion_queue(tmp_path)
    assert result == {"directory_entries": 2, "registered": 1, "not_registered": 1}
    entry = output(tmp_path)["entries"][1]
    assert entry["name"] == "New & Town" and entry["cml_website"] == "https://www.cml.org/town"
    assert entry["status"] == "not_registered" and entry["authority_id"] is None


def test_generation_time_is_not_invented_as_source_retrieval(tmp_path: Path) -> None:
    fixture(tmp_path, '<li>Sheridan Lake</li>')
    directory.materialize_municipal_expansion_queue(tmp_path)
    data = output(tmp_path)
    assert data["source_retrieved_at"] is None
    assert data["source_retrieval_status"] == "unknown_from_archived_page"
    assert datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00")).tzinfo
    assert data["target_basis"]["as_of"] == "2025-01-01"
    assert data["target_basis"]["incorporated_place_records"] == 273
    assert "not a verified current active-government count" in data["target_basis"]["scope"]
    assert "Bonanza" in data["target_basis"]["scope"]


@pytest.mark.parametrize("text", ["No table", "Links to Colorado cities and towns only"])
def test_missing_archive_markers_fail_without_output(tmp_path: Path, text: str) -> None:
    archive = fixture(tmp_path, '<li>Sheridan Lake</li>')
    archive.write_text(text)
    with pytest.raises(ValueError, match="table was not found"):
        directory.materialize_municipal_expansion_queue(tmp_path)
    assert not (tmp_path / directory.OUTPUT_PATH).exists()


def test_previous_queue_is_snapshotted_before_regeneration(tmp_path: Path) -> None:
    fixture(tmp_path, '<li>Sheridan Lake</li>')
    directory.materialize_municipal_expansion_queue(tmp_path)
    before = (tmp_path / directory.OUTPUT_PATH).read_bytes()
    directory.materialize_municipal_expansion_queue(tmp_path)
    snapshots = list((tmp_path / "_SNAPSHOTS").rglob(directory.OUTPUT_PATH.name))
    assert len(snapshots) == 1 and snapshots[0].read_bytes() == before


@pytest.mark.parametrize("mutation", ["count", "registered", "duplicate", "target", "naive",
                                      "retrieval", "unknown_field"])
def test_queue_schema_rejects_false_counts_and_provenance(tmp_path: Path, mutation: str) -> None:
    fixture(tmp_path, '<li>Sheridan Lake</li>')
    directory.materialize_municipal_expansion_queue(tmp_path)
    data = output(tmp_path)
    if mutation == "count":
        data["directory_entries"] = 2
    elif mutation == "registered":
        data["registered_entries"] = 0
    elif mutation == "duplicate":
        data["entries"].append(data["entries"][0])
    elif mutation == "target":
        data["incorporated_municipality_target"] = 274
    elif mutation == "naive":
        data["generated_at"] = "2026-09-10T00:00:00"
    elif mutation == "retrieval":
        data["source_retrieved_at"] = "2026-09-10T00:00:00Z"
    else:
        data["active_municipality_count"] = 273
    with pytest.raises(ValidationError):
        directory.MunicipalExpansionQueue.model_validate(data)


@pytest.mark.parametrize("changes", [
    {"authority_id": None}, {"source_name": "Sheriden Lake"},
    {"normalization_evidence_url": directory.CENSUS_REFERENCE_URL},
])
def test_entry_requires_consistent_identity_and_alias_evidence(changes: dict) -> None:
    entry = dict(name="Sheridan Lake", cml_website=None, status="registered",
                 authority_id="CO-MUNICIPAL-SHERIDAN_LAKE")
    with pytest.raises(ValidationError):
        directory.MunicipalDirectoryEntry.model_validate({**entry, **changes})
