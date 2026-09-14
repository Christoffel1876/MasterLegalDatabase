"""Regression gates for explicit retired local-source ownership identities."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from geode.connectors import local_sources
from geode.pipeline import county_inventory, county_source_discovery, local_rule_ingest
from geode.pipeline.local_source_ownership import (
    POLICY_PATH,
    OwnershipPolicy,
    load_ownership_policy,
    requires_ownership_policy,
)

REPO = Path(__file__).parents[1]
RETIRED = "county_boulder_code"
CITY_URL = "https://bouldercolorado.gov/services/building-codes-and-regulations"
COUNTY_ID = "CO-COUNTY-BOULDER"
CITY_ID = "CO-MUNICIPAL-BOULDER"


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.fixture()
def policy_root(tmp_path: Path) -> Path:
    """Seed an explicit real ownership policy without copying any corpus data."""
    _json(tmp_path / POLICY_PATH, json.loads((REPO / POLICY_PATH).read_text()))
    return tmp_path


@pytest.fixture()
def policy(policy_root: Path) -> OwnershipPolicy:
    """Load the shared policy exactly as pipeline entry points do."""
    return load_ownership_policy(policy_root)


def test_actual_policy_matches_declared_retirements(policy: OwnershipPolicy) -> None:
    """The actual correction is structurally usable without changing its documentary claims."""
    assert len(policy.retired_source_ids) == 3
    assert len(policy.affected_parent_rule_ids) == 17
    assert len(policy.affected_review_ids) == 86
    assert len(policy.affected_candidate_mappings) == 4
    assert policy.policy_sha256 and len(policy.policy_sha256) == 64


@pytest.mark.parametrize("key", [
    "url", "source_url", "requested_url", "final_url", "discovery_parent_url",
])
def test_exact_owner_url_pair_catches_renamed_source(policy: OwnershipPolicy, key: str) -> None:
    """Renaming a source cannot revive a known wrong authority/URL association."""
    assert policy.source_exclusion_reason({
        "source_id": "new_alias", "authority_id": COUNTY_ID, key: CITY_URL + "#section",
    })


def test_all_retired_source_ids_remain_retired(policy: OwnershipPolicy) -> None:
    """A retired identifier cannot be reused by simply changing the recorded owner."""
    for source_id in policy.retired_source_ids:
        assert policy.source_exclusion_reason({"source_id": source_id, "authority_id": CITY_ID})


@pytest.mark.parametrize("row", [
    {"authority_id": CITY_ID, "url": CITY_URL},
    {"authority_id": COUNTY_ID, "url": "https://bouldercounty.gov/"},
    {"authority_id": COUNTY_ID, "url": "https://bouldercolorado.gov/unreviewed-other-page"},
    {"source_id": RETIRED + "_unrelated", "source_hash": "a" * 64},
    {"authority_id": COUNTY_ID, "url": CITY_URL + "?different=resource"},
    {"source_url": "not a URL"},
    {},
])
def test_no_broad_city_county_host_hash_or_prefix_exclusion(
    policy: OwnershipPolicy, row: dict[str, Any],
) -> None:
    """Correct municipal ownership, other URLs and coincident hashes remain unaffected."""
    assert policy.source_exclusion_reason(row) is None
    assert policy.entity_exclusion_reason(row) is None


@pytest.mark.parametrize("key", [
    "id", "parent_rule_id", "parent_regulation_id", "review_id", "rule_unit_id",
    "candidate_rule_unit_id", "permanent_rule_unit_id",
])
def test_explicit_entity_ids_are_excluded(policy: OwnershipPolicy, key: str) -> None:
    """Every supported explicit entity-reference field enforces the same correction."""
    assert policy.entity_exclusion_reason({key: policy.affected_parent_rule_ids[0]})


@pytest.mark.parametrize("prefix,suffix", [
    ("", "-UNIT-0009"), ("", "_RU_0009"), ("COUNTY-SEM-", "_RU_0009"),
    ("CONDITIONAL-", "-UNIT-0009"), ("CONDITIONAL-COUNTY-SEM-", "_RU_0009"),
])
def test_only_documented_descendant_forms_match(
    policy: OwnershipPolicy, prefix: str, suffix: str,
) -> None:
    """Exact parent relationships cover new units without arbitrary prefix matching."""
    parent = policy.affected_parent_rule_ids[0]
    assert policy.entity_exclusion_reason({"id": prefix + parent + suffix})
    assert policy.entity_exclusion_reason({"id": parent + "-UNIT-0009-other"}) is None


@pytest.mark.parametrize("key", ["candidate_rule_unit", "source", "source_metadata", "metadata"])
def test_nested_metadata_preserves_owner_context(policy: OwnershipPolicy, key: str) -> None:
    """Nested provenance cannot hide a retired identity or known wrong source owner."""
    assert policy.entity_exclusion_reason({"authority_id": COUNTY_ID, key: {"url": CITY_URL}})
    assert policy.entity_exclusion_reason({key: {"id": policy.affected_review_ids[0]}})


def test_mapping_unit_and_nested_cycles(policy: OwnershipPolicy) -> None:
    """Mapped identities are excluded and cyclic caller dictionaries terminate safely."""
    mapping = policy.affected_candidate_mappings[0]
    assert policy.entity_exclusion_reason({"id": mapping.permanent_rule_unit_id})
    row: dict[str, Any] = {"id": "CRS-1-1-1"}
    row["metadata"] = row
    assert policy.entity_exclusion_reason(row) is None
    assert not requires_ownership_policy(row)


@pytest.mark.parametrize("row", [
    {"authority_level": "county"}, {"authority_level": "municipal"},
    {"authority_level": "district"}, {"authority_id": COUNTY_ID},
    {"authority_id": CITY_ID}, {"authority_id": "CO-DISTRICT-TEST"},
    {"layer": "08_County_Authorities"}, {"layer": "09_District_Authorities"},
    {"layer_id": "10_Municipal_Authorities"}, {"id": "LOCAL-RULE-UNRELATED"},
    {"id": "CONDITIONAL-TEST"}, {"review_id": "COUNTY-SEM-TEST"},
    {"source_id": "county_test"}, {"source_id": "municipal_test"},
    {"source_id": "district_test"}, {"metadata": {"source_id": "county_test"}},
    {"candidate_rule_unit_id": "LOCAL-RULE-TEST"},
    {"permanent_rule_unit_id": "LOCAL-RULE-TEST"},
])
def test_local_markers_require_policy_but_do_not_exclude(
    policy: OwnershipPolicy, row: dict[str, Any],
) -> None:
    """Local markers require policy review without broadly disqualifying their records."""
    assert requires_ownership_policy(row)
    assert policy.entity_exclusion_reason(row) is None


@pytest.mark.parametrize("row", [{}, {"id": "CRS-1-1-1"}, {"layer": "02_Regulations_CCR"}])
def test_state_only_rows_do_not_require_local_policy(row: dict[str, Any]) -> None:
    """State-only retrieval does not depend on an irrelevant local policy file."""
    assert not requires_ownership_policy(row)


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(schema_version=2),
    lambda p: p.update(legal_currentness="verified"),
    lambda p: p.update(prepared_at="2026-09-10T00:00:00"),
    lambda p: p.update(replacements=[]),
    lambda p: p["replacements"].append(p["replacements"][0]),
    lambda p: p["replacements"][0]["historical_entry"].update(source_id="other"),
    lambda p: p["replacements"][0]["historical_entry"].update(authority_id="other"),
    lambda p: p["replacements"][0]["historical_entry"].update(url="https://example.org/"),
    lambda p: p["replacements"][0].update(observed_owner_id=COUNTY_ID),
    lambda p: p["affected_parent_rule_ids"].append(""),
    lambda p: p["affected_review_ids"].append(p["affected_review_ids"][0]),
    lambda p: p["affected_candidate_mappings"][0].update(parent_regulation_id="other"),
    lambda p: p["affected_candidate_mappings"][0].update(review_id="other"),
    lambda p: p["input_sha256"].update(bad="not a hash"),
    lambda p: p.update(unrecognized_policy_switch=True),
])
def test_invalid_policy_cannot_disable_gates(
    policy_root: Path, mutation: Callable[[dict[str, Any]], None],
) -> None:
    """Malformed or contradictory correction evidence cannot silently disable exclusions."""
    path = policy_root / POLICY_PATH
    payload = json.loads(path.read_text())
    mutation(payload)
    _json(path, payload)
    with pytest.raises(ValidationError):
        load_ownership_policy(policy_root)


@pytest.mark.parametrize("ancestor", [False, True])
def test_policy_symlink_is_rejected(policy_root: Path, tmp_path: Path, ancestor: bool) -> None:
    """Policy files and their ancestor directories must be ordinary local paths."""
    path = policy_root / POLICY_PATH
    if ancestor:
        moved = policy_root / "saved-control"
        path.parent.rename(moved)
        path.parent.symlink_to(moved, target_is_directory=True)
    else:
        saved = path.with_suffix(".saved")
        path.rename(saved)
        path.symlink_to(saved)
    with pytest.raises(ValueError, match="symlinks"):
        load_ownership_policy(policy_root)


@pytest.mark.parametrize("operation", [
    local_rule_ingest.ingest_local_rules,
    county_source_discovery.discover_county_sources,
    county_inventory.register_county_homepages,
    county_inventory.register_seed_sources,
    county_inventory.update_homepage_coverage,
    county_inventory.update_category_coverage,
    local_sources.retry_failed_linked_sources,
])
@pytest.mark.parametrize("malformed", [False, True])
def test_entry_points_fail_before_writes_without_valid_policy(
    tmp_path: Path, operation: Callable, malformed: bool,
) -> None:
    """Entry points validate ownership before creating output or reaching network code."""
    if malformed:
        _json(tmp_path / POLICY_PATH, {"schema_version": 1})
    before = {
        str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    with pytest.raises((FileNotFoundError, ValidationError)):
        operation(tmp_path)
    after = {
        str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    assert before == after


def test_ingest_excludes_before_identity_repair_and_hash_deduplication(
    policy_root: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    """Retired attempts do not consume a hash or stop a correctly attributed city source."""
    raw = policy_root / "same.html"
    raw.write_text("preserved text " * 70)
    old = {"source_id": RETIRED, "authority_id": COUNTY_ID, "authority_level": "county",
           "raw_path": str(raw), "status": "downloaded", "sha256": "a" * 64}
    city = {**old, "source_id": "municipal_boulder_building_codes", "authority_id": CITY_ID,
            "authority_level": "municipal"}
    manifest = policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl"
    _jsonl(manifest, [old, city])
    before = manifest.read_bytes()
    monkeypatch.setattr(local_rule_ingest, "_known_state_ids", lambda root: set())
    monkeypatch.setattr(local_rule_ingest, "_authority_lookup", lambda root: {CITY_ID: {}})
    monkeypatch.setattr(local_rule_ingest, "_source_registry_lookup", lambda root: {})
    built: list[str] = []
    def build(row: dict[str, Any], *args: Any) -> SimpleNamespace:
        """Capture the identity that reaches the existing extraction writer."""
        built.append(row["source_id"])
        return SimpleNamespace(rule_unit_ids=[])
    monkeypatch.setattr(local_rule_ingest, "_build_rule", build)
    monkeypatch.setattr(local_rule_ingest, "_build_rule_units", lambda *args: [])
    monkeypatch.setattr(local_rule_ingest, "_write_layer_records", lambda *args: None)
    monkeypatch.setattr(local_rule_ingest, "_refresh_manifest", lambda *args: None)
    monkeypatch.setattr(local_rule_ingest, "write_retrieval_catalog", lambda *args: None)
    result = local_rule_ingest.ingest_local_rules(policy_root)
    assert result["ownership_excluded"] == 1
    assert built == ["municipal_boulder_building_codes"]
    assert "retired source ownership" in caplog.text
    assert manifest.read_bytes() == before


def _registry(root: Path, sources: list[dict[str, Any]] | None = None) -> Path:
    path = root / "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json"
    _json(path, {"pilot": {"counties": [{"authority_id": COUNTY_ID}],
                           "county_sources": sources or []}})
    return path


def test_discovery_cannot_reintroduce_old_source_or_renamed_url(
    policy_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Old parent HTML and fresh aliases cannot recreate retired county source registrations."""
    registry = _registry(policy_root)
    old = policy_root / "old.html"
    old.write_text('<a href="https://bouldercounty.gov/old-code">Code</a>')
    valid = policy_root / "current.html"
    valid.write_text(f'<a href="{CITY_URL}">Building Code</a>'
                     '<a href="https://bouldercounty.gov/current-code">Code</a>')
    rows = [{"source_id": RETIRED, "authority_id": COUNTY_ID, "authority_level": "county",
             "status": "downloaded", "requested_url": CITY_URL, "raw_path": str(old)},
            {"source_id": "county_boulder_homepage", "authority_id": COUNTY_ID,
             "authority_level": "county", "status": "downloaded",
             "requested_url": "https://bouldercounty.gov/", "raw_path": str(valid)}]
    manifest = policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl"
    _jsonl(manifest, rows)
    before = manifest.read_bytes()
    monkeypatch.setattr(county_source_discovery, "CATEGORY_TERMS", {"county_codes": ("code",)})
    result = county_source_discovery.discover_county_sources(policy_root, write=True)
    assert result["candidates"] == 1
    assert result["ownership_excluded"] == 2
    sources = json.loads(registry.read_text())["pilot"]["county_sources"]
    assert [row["url"] for row in sources] == ["https://bouldercounty.gov/current-code"]
    assert manifest.read_bytes() == before


def test_discovery_removes_retired_registry_entries_even_without_new_candidates(
    policy_root: Path,
) -> None:
    """An old active registry is repaired even when no additional source is discovered."""
    registry = _registry(policy_root, [{"source_id": RETIRED, "authority_id": COUNTY_ID,
                                     "category": "county_codes", "url": CITY_URL}])
    _jsonl(policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl", [])
    result = county_source_discovery.discover_county_sources(policy_root, write=True)
    assert result["written"] is True and result["candidates"] == 0
    assert json.loads(registry.read_text())["pilot"]["county_sources"] == []


def test_registry_regeneration_replaces_only_retired_county_identity(
    policy_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """County identity regeneration uses the county homepage after discarding the retired row."""
    path = _registry(policy_root)
    data = json.loads(path.read_text())
    data["pilot"]["counties"][0].update(source_id=RETIRED, url=CITY_URL)
    _json(path, data)
    monkeypatch.setattr(county_inventory, "COUNTY_NAMES", ("Boulder",))
    county_inventory.register_county_homepages(policy_root)
    row = json.loads(path.read_text())["pilot"]["counties"][0]
    assert row["source_id"] == "county_boulder_homepage"
    assert row["url"] == "https://bouldercounty.gov/" and row["authority_id"] == COUNTY_ID


def test_seed_registration_excludes_retired_existing_and_new_aliases(
    policy_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seed merging removes known retirements while preserving allowed source aliases."""
    retired = {"source_id": RETIRED, "authority_id": COUNTY_ID, "url": CITY_URL}
    path = _registry(policy_root, [retired])
    safe = {"source_id": "county_safe", "authority_id": COUNTY_ID,
            "url": "https://bouldercounty.gov/legal"}
    monkeypatch.setattr(county_inventory, "SEED_SOURCE_RECORDS", [retired, safe])
    monkeypatch.setattr(county_inventory, "SEED_CATEGORY_ALIASES", {"county_safe": ("roads",)})
    county_inventory.register_seed_sources(policy_root)
    source_ids = {
        row["source_id"] for row in json.loads(path.read_text())["pilot"]["county_sources"]
    }
    assert source_ids == {
        "county_safe", "county_safe_roads",
    }


def test_coverage_ignores_manifest_only_retired_support_and_downgrades_stale_cells(
    policy_root: Path,
) -> None:
    """Neither retired downloads nor their stale cached coverage can support active status."""
    safe = {"source_id": "county_safe", "authority_id": COUNTY_ID,
            "url": "https://bouldercounty.gov/legal", "category": "county_codes"}
    _registry(policy_root, [safe])
    matrix = policy_root / "_CONTROL_PLANE/COUNTY_SOURCE_COVERAGE.json"
    _json(matrix, {"counties": [{"county_id": COUNTY_ID, "overall_status": "complete",
        "homepage": {"source_id": RETIRED, "url": CITY_URL, "status": "downloaded"},
        "source_categories": {
            "county_codes": {"source_ids": [RETIRED], "status": "complete"},
            "administrative_rule_manuals": {"source_ids": [RETIRED], "status": "downloaded"},
            "roads_transportation_access": {"source_ids": [RETIRED, "pending"],
                                           "status": "complete"},
        }}]})
    common = {"authority_id": COUNTY_ID, "authority_level": "county", "status": "downloaded"}
    rows = [{**common, "source_id": "county_boulder_homepage",
             "source_url": "https://bouldercounty.gov/",
             "requested_url": "https://bouldercounty.gov/"},
            {**common, "source_id": "county_safe", "source_url": safe["url"],
             "requested_url": safe["url"]},
            {**common, "source_id": RETIRED, "source_url": CITY_URL, "requested_url": CITY_URL},
            {**common, "source_id": RETIRED, "source_url": CITY_URL,
             "requested_url": "https://bouldercolorado.gov/manual-road-code.pdf"}]
    manifest = policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl"
    _jsonl(manifest, rows)
    before = manifest.read_bytes()
    county_inventory.update_homepage_coverage(policy_root)
    county = json.loads(matrix.read_text())["counties"][0]
    assert county["homepage"]["url"] == safe["url"]  # Last eligible root-page attempt.
    county_inventory.update_category_coverage(policy_root)
    cells = json.loads(matrix.read_text())["counties"][0]["source_categories"]
    assert cells["county_codes"]["source_ids"] == ["county_safe"]
    assert cells["county_codes"]["status"] == "downloaded"
    assert cells["administrative_rule_manuals"]["status"] == "not_started"
    assert cells["roads_transportation_access"]["status"] == "source_identified"
    assert all(RETIRED not in cell["source_ids"] for cell in cells.values())
    assert manifest.read_bytes() == before


def test_retry_excludes_retired_attempt_without_fetch_or_manifest_change(
    policy_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A historical access failure is preserved but not retried after its source is retired."""
    manifest = policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl"
    row = {"source_id": RETIRED, "authority_id": COUNTY_ID, "authority_level": "county",
           "source_url": CITY_URL, "requested_url": CITY_URL + "/document.pdf",
           "raw_path": str(policy_root / "FAILED"), "status": "failed",
           "retrieved_at": "2026-07-20T00:00:00Z", "failure_class": "access_denied"}
    _jsonl(manifest, [row])
    before = manifest.read_bytes()
    monkeypatch.setattr(
        local_sources, "_fetch", lambda *args, **kwargs: pytest.fail("retired fetch"),
    )
    result = local_sources.retry_failed_linked_sources(policy_root)
    assert result.attempted == 0 and result.ownership_excluded == 1
    assert result.ownership_exclusion_reasons == [f"retired source ownership: {RETIRED}"]
    assert manifest.read_bytes() == before
    report = json.loads((policy_root / local_sources.COUNTY_RETRY_REPORT_PATH).read_text())
    assert report["ownership_excluded"] == 1


@pytest.mark.parametrize("origin", ["manifest", "registry"])
@pytest.mark.parametrize("operation", [
    county_inventory.update_homepage_coverage, county_inventory.update_category_coverage,
])
@pytest.mark.parametrize("unaffected_support", [False, True])
def test_exact_excluded_alias_cannot_keep_stale_coverage(
    policy_root: Path, origin: str, operation: Callable, unaffected_support: bool,
) -> None:
    """Known alias support is removed only for its owner, retaining unrelated category evidence."""
    alias = {"source_id": "renamed_city_source", "authority_id": COUNTY_ID,
             "authority_level": "county", "url": CITY_URL, "source_url": CITY_URL,
             "requested_url": CITY_URL, "category": "county_codes", "status": "downloaded"}
    _registry(policy_root, [alias] if origin == "registry" else [])
    _jsonl(policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl",
           [alias] if origin == "manifest" else [])
    cells = {"county_codes": {"source_ids": [alias["source_id"]], "status": "downloaded"}}
    if unaffected_support:
        cells["public_health"] = {"source_ids": ["unaffected_health"], "status": "downloaded"}
    matrix = policy_root / "_CONTROL_PLANE/COUNTY_SOURCE_COVERAGE.json"
    other = {"county_id": "CO-COUNTY-OTHER", "overall_status": "partial",
             "source_categories": {"county_codes": {
                 "source_ids": [alias["source_id"]], "status": "downloaded"}}}
    _json(matrix, {"counties": [{"county_id": COUNTY_ID, "overall_status": "complete",
        "homepage": {"source_id": alias["source_id"], "status": "downloaded"},
        "source_categories": cells}, other]})
    operation(policy_root)
    boulder, remaining = json.loads(matrix.read_text())["counties"]
    assert boulder["source_categories"]["county_codes"]["source_ids"] == []
    assert boulder["source_categories"]["county_codes"]["status"] == "not_started"
    assert "homepage" not in boulder
    assert boulder["overall_status"] == ("partial" if unaffected_support else "not_started")
    assert remaining == other


def test_ingest_checks_owner_again_after_existing_identity_lookup(
    policy_root: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    """A previously unknown owner cannot bypass the URL-pair gate through registry repair."""
    raw = policy_root / "source.html"
    raw.write_text("existing preserved source " * 60)
    row = {"source_id": "renamed_city_source", "authority_id": "old-unknown-id",
           "authority_level": "county", "source_url": CITY_URL, "raw_path": str(raw),
           "status": "downloaded"}
    _jsonl(policy_root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl", [row])
    monkeypatch.setattr(local_rule_ingest, "_known_state_ids", lambda root: set())
    monkeypatch.setattr(local_rule_ingest, "_authority_lookup", lambda root: {COUNTY_ID: {}})
    monkeypatch.setattr(local_rule_ingest, "_source_registry_lookup", lambda root: {
        row["source_id"]: {"authority_id": COUNTY_ID, "authority_level": "county",
                           "url": "https://bouldercounty.gov/"},
    })
    monkeypatch.setattr(local_rule_ingest, "_extract_source", lambda *args: pytest.fail("excluded"))
    monkeypatch.setattr(local_rule_ingest, "_write_layer_records", lambda *args: None)
    monkeypatch.setattr(local_rule_ingest, "_refresh_manifest", lambda *args: None)
    monkeypatch.setattr(local_rule_ingest, "write_retrieval_catalog", lambda *args: None)
    result = local_rule_ingest.ingest_local_rules(policy_root)
    assert result["ownership_excluded"] == 1
    assert "Ownership exclusion after registry lookup" in caplog.text
