"""The identity pilot preserves unrelated index records and fails on ambiguous merges."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from geode.pipeline.local_pilot import materialize_pilot_authorities
from geode.pipeline.local_source_ownership import POLICY_PATH, OwnershipPolicy
from geode.utils.file_io import iter_jsonl
from tests.ownership_support import ownership_policy

COUNTY = "08_County_Authorities"
MUNICIPAL = "10_Municipal_Authorities"
DISTRICT = "09_District_Authorities"
BOULDER = "CO-COUNTY-BOULDER"
REGISTRY = "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json"


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _entry(identity: str = BOULDER, **overrides: Any) -> dict[str, Any]:
    return {
        "source_id": "county_boulder_homepage", "authority_id": identity,
        "authority_level": "county", "authority_type": "county", "name": "Boulder County",
        "url": "https://bouldercounty.gov/", "county_names": ["Boulder"], **overrides,
    }


def _files(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_mixed_entities_metadata_and_order_survive_repeated_materialization(tmp_path: Path) -> None:
    """Refresh only registered authorities; preserve every unrelated row and metadata object."""
    _json(tmp_path / REGISTRY, {"pilot": {"counties": [
        _entry(), _entry("CO-COUNTY-LARIMER", source_id="county_larimer_homepage",
                         name="Larimer County", url="https://www.larimer.gov/"),
    ]}})
    metadata = f"{COUNTY}/_meta/local_authorities.jsonl"
    external = f"{COUNTY}/_meta/rule_units.jsonl"
    unrelated = [
        {"id": "LOCAL-UNIT-READY", "entity_type": "rule_unit", "meta_path": external,
         "semantic_status": "semantic_ready", "sha256": "b" * 64,
         "extension": {"nested": [1, "keep", {"flag": False}]}, "source_page": 4},
        {"id": "UNREGISTERED", "entity_type": "local_authority", "meta_path": metadata,
         "authority_name": "Keep the exact old name", "confidence": 0.89},
        {"id": "LOCAL-RULE-SAFE", "entity_type": "local_rule", "path": "legal.md"},
        {"id": "LOCAL-GAP", "entity_type": "county_gap", "status": "unresolved"},
        {"id": "FUTURE-ENTITY", "entity_type": "future_extension", "custom": ["a", "b"]},
    ]
    target = {"id": BOULDER, "entity_type": "local_authority", "meta_path": metadata,
              "authority_name": "Old registered name"}
    original_index = [unrelated[0], target, *unrelated[1:]]
    _rows(tmp_path / COUNTY / "_index.jsonl", original_index)
    old_meta = [
        {"id": "UNREGISTERED", "entity_type": "local_authority", "name": "Unchanged metadata",
         "source_url": "https://www.larimer.gov/", "review_notes": ["keep"]},
        {"id": BOULDER, "entity_type": "local_authority", "name": "Old registered name"},
        {"id": "UNINDEXED-METADATA", "entity_type": "local_authority", "name": "Keep history"},
    ]
    _rows(tmp_path / metadata, old_meta)
    _rows(tmp_path / external, [{"id": "LOCAL-UNIT-READY", "text": "Exact original text.\n"}])
    (tmp_path / "legal.md").write_text("Untouched local text\n", encoding="utf-8")
    original = _files(tmp_path)

    for _ in range(2):
        report = materialize_pilot_authorities(tmp_path)
        index = list(iter_jsonl(tmp_path / COUNTY / "_index.jsonl"))
        assert [row["id"] for row in index] == [
            *[row["id"] for row in original_index], "CO-COUNTY-LARIMER",
        ]
        preserved = [row for row in index if row["id"] not in {BOULDER, "CO-COUNTY-LARIMER"}]
        assert preserved == unrelated
        assert index[1]["authority_name"] == "Boulder County"
        records = list(iter_jsonl(tmp_path / metadata))
        assert [row["id"] for row in records] == [
            "UNREGISTERED", BOULDER, "UNINDEXED-METADATA", "CO-COUNTY-LARIMER",
        ]
        assert records[0] == old_meta[0] and records[2] == old_meta[2]
        assert report == {"ownership_excluded": 0, "county": 2, "municipal": 0, "district": 0}
        assert (tmp_path / external).read_bytes() == original[external]
        assert (tmp_path / "legal.md").read_bytes() == original["legal.md"]
    snapshots = [p.read_bytes() for p in (tmp_path / "_SNAPSHOTS").rglob("*.jsonl")]
    assert original[f"{COUNTY}/_index.jsonl"] in snapshots
    assert original[metadata] in snapshots
    assert (tmp_path / REGISTRY).read_bytes() == original[REGISTRY]


def test_retired_parents_units_and_metadata_are_excluded_without_owner_transfer(
    tmp_path: Path, ownership_policy: OwnershipPolicy, caplog: pytest.LogCaptureFixture,
) -> None:
    """Known retired evidence and explicit descendants disappear, while correct city data stays."""
    parent = ownership_policy.affected_parent_rule_ids[0]
    metadata = f"{COUNTY}/_meta/local_authorities.jsonl"
    old_city_url = "https://bouldercolorado.gov/services/building-codes-and-regulations"
    _json(tmp_path / REGISTRY, {"pilot": {"counties": [_entry()]}})
    _rows(tmp_path / COUNTY / "_index.jsonl", [
        {"id": BOULDER, "entity_type": "local_authority", "authority_id": BOULDER,
         "source_url": old_city_url, "meta_path": metadata},
        {"id": parent, "entity_type": "local_rule", "source_id": "county_boulder_code"},
        {"id": parent + "-UNIT-0001", "entity_type": "rule_unit",
         "semantic_status": "semantic_ready"},
        {"id": "ALIASED-PARENT", "entity_type": "local_rule", "source_id": "county_boulder_code"},
        {"id": "UNRELATED-READY", "entity_type": "rule_unit", "semantic_status": "semantic_ready"},
    ])
    _rows(tmp_path / metadata, [
        {"id": BOULDER, "entity_type": "local_authority", "authority_id": BOULDER,
         "source_url": old_city_url},
        {"id": parent, "entity_type": "local_rule"},
    ])
    city_row = {"id": "CITY-LEGAL", "entity_type": "rule_unit",
                "authority_id": "CO-MUNICIPAL-BOULDER",
                "source_url": old_city_url, "semantic_status": "semantic_ready"}
    _rows(tmp_path / MUNICIPAL / "_index.jsonl", [
        {"id": "ALIASED-CHILD", "entity_type": "rule_unit",
         "parent_regulation_id": "ALIASED-PARENT"},
        city_row,
    ])
    report = materialize_pilot_authorities(tmp_path)
    assert report["ownership_excluded"] == 7
    assert "retired" in caplog.text and "affected ownership identity" in caplog.text
    assert [row["id"] for row in iter_jsonl(tmp_path / COUNTY / "_index.jsonl")] == [
        BOULDER, "UNRELATED-READY",
    ]
    assert list(iter_jsonl(tmp_path / MUNICIPAL / "_index.jsonl")) == [city_row]
    authority = next(iter_jsonl(tmp_path / metadata))
    assert authority["id"] == BOULDER and authority["source_url"] == "https://bouldercounty.gov/"
    assert len(list(iter_jsonl(tmp_path / metadata))) == 1


@pytest.mark.parametrize("fault", [
    "identical-index-duplicate", "conflicting-index-duplicate", "retired-index-duplicate",
    "metadata-duplicate", "registry-duplicate", "index-type-collision", "metadata-type-collision",
    "cross-layer-existing", "cross-layer-generated", "cross-layer-new-existing",
    "index-missing-id", "index-nonstring-id", "metadata-empty-id",
])
def test_ambiguous_ids_fail_before_any_layer_is_written(tmp_path: Path, fault: str) -> None:
    """Do not silently deduplicate records, overwrite another entity type or choose an owner."""
    registry = {"pilot": {"counties": [_entry()]}}
    _json(tmp_path / REGISTRY, registry)
    duplicate = {"id": "UNRELATED", "entity_type": "rule_unit", "value": 1}
    if fault.endswith("index-duplicate"):
        other = {**duplicate, "value": 2} if fault.startswith("conflicting") else duplicate
        if fault.startswith("retired"):
            duplicate = {**duplicate, "source_id": "county_boulder_code"}
            other = duplicate
        _rows(tmp_path / COUNTY / "_index.jsonl", [duplicate, other])
    elif fault == "metadata-duplicate":
        _rows(tmp_path / DISTRICT / "_meta/local_authorities.jsonl", [duplicate, duplicate])
    elif fault == "registry-duplicate":
        registry["pilot"]["counties"].append(_entry())
        _json(tmp_path / REGISTRY, registry)
    elif fault.endswith("type-collision"):
        path = ("_index.jsonl" if fault.startswith("index") else "_meta/local_authorities.jsonl")
        _rows(tmp_path / COUNTY / path, [{"id": BOULDER, "entity_type": "rule_unit"}])
    elif fault == "cross-layer-existing":
        _rows(tmp_path / COUNTY / "_index.jsonl", [duplicate])
        _rows(tmp_path / DISTRICT / "_index.jsonl", [duplicate])
    elif fault == "cross-layer-generated":
        registry["pilot"]["districts"] = [_entry(authority_level="district")]
        _json(tmp_path / REGISTRY, registry)
    elif fault == "cross-layer-new-existing":
        _rows(tmp_path / DISTRICT / "_index.jsonl", [
            {"id": BOULDER, "entity_type": "local_authority"},
        ])
    elif fault == "index-missing-id":
        _rows(tmp_path / COUNTY / "_index.jsonl", [{"entity_type": "rule_unit"}])
    elif fault == "index-nonstring-id":
        _rows(tmp_path / COUNTY / "_index.jsonl", [{"id": 12, "entity_type": "rule_unit"}])
    else:
        _rows(tmp_path / COUNTY / "_meta/local_authorities.jsonl", [{"id": "  "}])
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="duplicate|collid|invalid record ID"):
        materialize_pilot_authorities(tmp_path)
    assert _files(tmp_path) == before
    assert not (tmp_path / "_SNAPSHOTS").exists()


@pytest.mark.parametrize("location", ["index", "metadata"])
@pytest.mark.parametrize("content", [
    "version https://git-lfs.github.com/spec/v1\noid sha256:" + "a" * 64 + "\nsize 123\n",
    '{"id": "partial"',
])
def test_late_layer_pointer_or_corruption_prevents_earlier_writes(
    tmp_path: Path, location: str, content: str,
) -> None:
    """A later missing LFS payload or corrupt baseline cannot partially rebuild earlier layers."""
    _json(tmp_path / REGISTRY, {"pilot": {"counties": [_entry()]}})
    _rows(tmp_path / COUNTY / "_index.jsonl", [{"id": "SAFE", "entity_type": "rule_unit"}])
    suffix = "_index.jsonl" if location == "index" else "_meta/local_authorities.jsonl"
    path = tmp_path / DISTRICT / suffix
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    before = _files(tmp_path)
    with pytest.raises(ValueError):
        materialize_pilot_authorities(tmp_path)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("mode", ["missing", "malformed"])
def test_failed_policy_precedes_all_reads_and_writes(tmp_path: Path, mode: str) -> None:
    """A missing or malformed ownership policy cannot trigger an index or metadata rewrite."""
    path = tmp_path / POLICY_PATH
    if mode == "missing":
        path.unlink()
    else:
        path.write_text("{}", encoding="utf-8")
    before = _files(tmp_path)
    with pytest.raises((FileNotFoundError, ValueError)):
        materialize_pilot_authorities(tmp_path)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("metadata_present", [False, True])
def test_merge_cannot_orphan_a_preserved_managed_metadata_reference(
    tmp_path: Path, metadata_present: bool,
) -> None:
    """Missing or ownership-excluded managed metadata stops rather than publishing an orphan."""
    _json(tmp_path / REGISTRY, {"pilot": {}})
    metadata = f"{COUNTY}/_meta/local_authorities.jsonl"
    _rows(tmp_path / COUNTY / "_index.jsonl", [
        {"id": "UNCHANGED", "entity_type": "local_authority", "meta_path": metadata},
    ])
    if metadata_present:
        _rows(tmp_path / metadata, [{"id": "UNCHANGED", "source_id": "county_boulder_code"}])
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="managed authority metadata missing"):
        materialize_pilot_authorities(tmp_path)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("reference", [
    f"./{COUNTY}/_meta/local_authorities.jsonl",
    f"{COUNTY}//_meta/./local_authorities.jsonl",
    f"{COUNTY}/_meta/../_meta/local_authorities.jsonl",
    f"{MUNICIPAL}/_meta/local_authorities.jsonl",
])
@pytest.mark.parametrize("field", ["meta_path", "path"])
def test_equivalent_and_cross_layer_references_cannot_be_orphaned(
    tmp_path: Path, reference: str, field: str,
) -> None:
    """Retiring metadata must fail the entire merge even through an equivalent lookup path."""
    _json(tmp_path / REGISTRY, {"pilot": {"counties": [_entry()]}})
    row = {"id": "ALIAS", "entity_type": "local_authority", field: reference}
    if field == "path":
        # Runtime lookup may fall back from meta_path to path; check both references.
        row["meta_path"] = "unmanaged/other.jsonl"
    _rows(tmp_path / COUNTY / "_index.jsonl", [row])
    layer = MUNICIPAL if reference.startswith(MUNICIPAL) else COUNTY
    _rows(tmp_path / layer / "_meta/local_authorities.jsonl", [
        {"id": "ALIAS", "entity_type": "local_authority", "source_id": "county_boulder_code"},
    ])
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="managed authority metadata missing"):
        materialize_pilot_authorities(tmp_path)
    assert _files(tmp_path) == before


def test_consistent_cross_layer_reference_and_unmanaged_metadata_are_preserved(
    tmp_path: Path,
) -> None:
    """A reference to present metadata in another local layer remains unchanged and readable."""
    _json(tmp_path / REGISTRY, {"pilot": {}})
    metadata_path = f"{MUNICIPAL}/_meta/local_authorities.jsonl"
    reference = f"./{MUNICIPAL}/_meta/../_meta/local_authorities.jsonl"
    index = {"id": "SHARED", "entity_type": "future_extension", "meta_path": reference,
             "path": "unmanaged/external-format.jsonl", "details": ["preserve"]}
    metadata = {"id": "SHARED", "entity_type": "future_extension", "details": [1, 2]}
    _rows(tmp_path / COUNTY / "_index.jsonl", [index])
    _rows(tmp_path / metadata_path, [metadata])
    # The merge must not parse unrelated files while resolving managed lookup references.
    external = tmp_path / "unmanaged/external-format.jsonl"
    external.parent.mkdir()
    external.write_text("not managed JSONL", encoding="utf-8")
    for _ in range(2):
        materialize_pilot_authorities(tmp_path)
        assert list(iter_jsonl(tmp_path / COUNTY / "_index.jsonl")) == [index]
        assert list(iter_jsonl(tmp_path / metadata_path)) == [metadata]
        assert external.read_text(encoding="utf-8") == "not managed JSONL"


@pytest.mark.parametrize("reference", [
    "../outside.jsonl", "08_County_Authorities/../../outside.jsonl",
    "/tmp/outside.jsonl", "//host/share/outside.jsonl", r"C:\outside.jsonl",
    "https://example.invalid/outside.jsonl", ".", "08_County_Authorities/..", " ", 12,
])
def test_unsafe_lookup_references_fail_before_all_writes(
    tmp_path: Path, reference: object,
) -> None:
    """Do not resolve or open absolute, escaping, non-POSIX or non-file references."""
    _json(tmp_path / REGISTRY, {"pilot": {"counties": [_entry()]}})
    _rows(tmp_path / DISTRICT / "_index.jsonl", [
        {"id": "UNRELATED", "entity_type": "future_extension", "meta_path": reference},
    ])
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="index reference"):
        materialize_pilot_authorities(tmp_path)
    assert _files(tmp_path) == before
