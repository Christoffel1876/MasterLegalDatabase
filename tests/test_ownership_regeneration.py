"""Ownership exclusions survive every remaining legacy regeneration entry point."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from geode.connectors import local_sources
from geode.pipeline import (
    county_semantic_review,
    local_crosswalk,
    local_freshness,
    local_pilot,
    local_review,
)
from geode.pipeline.local_source_ownership import POLICY_PATH, OwnershipPolicy
from geode.utils.file_io import iter_jsonl
from tests.ownership_support import ownership_policy

COUNTY = "CO-COUNTY-BOULDER"
CITY = "CO-MUNICIPAL-BOULDER"
CITY_URL = "https://bouldercolorado.gov/services/building-codes-and-regulations"
RETIRED = "county_boulder_code"
MANIFEST = Path("_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl")


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.mark.parametrize("operation", [
    local_freshness.build_local_source_freshness,
    local_freshness.write_local_source_freshness,
    local_review.build_local_review_queues,
    county_semantic_review.build_county_semantic_review,
    local_pilot.materialize_pilot_authorities,
    local_crosswalk.build_local_crosswalks,
    local_sources.download_pilot_sources,
])
@pytest.mark.parametrize("invalid", ["missing", "malformed"])
def test_policy_preflight_precedes_all_outputs_and_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: Callable, invalid: str,
) -> None:
    """A missing or invalid policy fails before any derived file or HTTP client is created."""
    policy_path = tmp_path / POLICY_PATH
    if invalid == "missing":
        policy_path.unlink()
    else:
        policy_path.write_text("{}", encoding="utf-8")
    _rows(tmp_path / MANIFEST, [{"source_id": RETIRED, "status": "downloaded"}])
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.setattr(
        local_sources, "build_session", lambda **kwargs: pytest.fail("network preflight bypass"),
    )
    with pytest.raises((FileNotFoundError, ValueError)):
        operation(tmp_path)
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_freshness_excludes_redirect_alias_but_preserves_download_history(tmp_path: Path) -> None:
    """Age summaries cannot revive a renamed wrong-owner redirect or erase its prior attempts."""
    base = {"status": "downloaded", "retrieved_at": "2026-07-01T00:00:00Z"}
    rows = [
        {**base, "source_id": RETIRED},
        {**base, "source_id": "alias", "authority_id": COUNTY,
         "requested_url": "https://bouldercounty.gov/old", "final_url": CITY_URL},
        {**base, "source_id": "city_good", "authority_id": CITY, "final_url": CITY_URL},
        {**base, "source_id": "county_good", "authority_id": COUNTY,
         "requested_url": "https://bouldercounty.gov/"},
    ]
    path = tmp_path / MANIFEST
    _rows(path, rows)
    original = path.read_bytes()
    report = local_freshness.write_local_source_freshness(tmp_path, today=date(2026, 7, 15))
    assert report["ownership_excluded"] == 2
    assert "authority/URL" in report["ownership_exclusion_reasons"][1]
    assert {r["source_id"] for r in report["records"]} == {"city_good", "county_good"}
    assert path.read_bytes() == original


@pytest.mark.parametrize("alias_origin", ["manifest", "registry"])
def test_review_filters_retired_entities_and_exact_coverage_support(
    tmp_path: Path, ownership_policy: OwnershipPolicy, alias_origin: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mixed coverage retains valid support and retired units never count as answer safe."""
    monkeypatch.setattr(local_review, "_write_promotion_queue_if_available", lambda *args: None)
    parent = ownership_policy.affected_parent_rule_ids[0]
    alias = {"source_id": "renamed", "authority_id": COUNTY, "final_url": CITY_URL}
    if alias_origin == "manifest":
        _rows(tmp_path / MANIFEST, [alias])
    else:
        _json(tmp_path / "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json",
              {"pilot": {"county_sources": [alias], "note": "ignored non-list metadata"}})
    quarantine = tmp_path / "_QUARANTINE/local_extraction_quarantine.jsonl"
    _rows(quarantine, [
        {"source_id": RETIRED, "reason": "OCR required"},
        {"source_id": "renamed", "authority_id": COUNTY, "reason": "OCR required"},
        {"source_id": "city_good", "authority_id": CITY, "reason": "OCR required"},
    ])
    index = tmp_path / "08_County_Authorities/_index.jsonl"
    meta = "08_County_Authorities/_meta/rules_20260101.jsonl"
    _rows(index, [
        {"id": parent + "-UNIT-0001", "entity_type": "rule_unit",
         "semantic_status": "semantic_ready", "meta_path": meta},
        {"id": "LOCAL-GOOD", "entity_type": "rule_unit", "semantic_status": "needs_review"},
        {"id": "LOCAL-READY", "entity_type": "rule_unit", "semantic_status": "semantic_ready"},
    ])
    _rows(tmp_path / meta, [{"id": parent}])
    _json(tmp_path / "_CONTROL_PLANE/COUNTY_SOURCE_COVERAGE.json", {"counties": [{
        "county_id": COUNTY, "source_categories": {
            "codes": {"status": "downloaded_unreviewed", "source_ids": [RETIRED]},
            "fees": {"status": "downloaded_unreviewed", "source_ids": ["renamed", "good"]},
            "roads": {"status": "blocked", "source_ids": ["renamed"]},
        },
    }, {"county_id": "CO-COUNTY-OTHER", "source_categories": {
        "fees": {"status": "blocked", "source_ids": ["renamed"]},
    }}]})
    preserved = {path: path.read_bytes() for path in (quarantine, index, tmp_path / meta)}
    summary = local_review.build_local_review_queues(tmp_path)
    assert summary.ownership_excluded == 6
    assert len(summary.ownership_exclusion_reasons) == 6
    assert summary.answer_safe_local_rule_units == 1
    assert summary.semantic_review_items == summary.ocr_items == 1
    assert summary.metadata_version_items == 0
    queue = list(iter_jsonl(tmp_path / local_review.QUEUE_PATH))
    coverage = [r for r in queue if "source_ids" in r]
    assert [r["source_ids"] for r in coverage] == [["good"], ["renamed"]]
    assert all(path.read_bytes() == content for path, content in preserved.items())


def test_semantic_review_rejects_parent_and_final_url_before_extraction(
    tmp_path: Path, ownership_policy: OwnershipPolicy,
) -> None:
    """Retired records need not contain extractable text and never generate candidates."""
    path = tmp_path / "08_County_Authorities/_meta/local_rules.jsonl"
    _rows(path, [
        {"id": ownership_policy.affected_parent_rule_ids[0]},
        {"id": "ALIAS", "authority_id": COUNTY, "final_url": CITY_URL},
        {"id": "LOCAL-RULE-GOOD", "authority_id": CITY, "source_url": CITY_URL,
         "full_text": "Applicants must submit the form within 30 days."},
    ])
    original = path.read_bytes()
    report = county_semantic_review.build_county_semantic_review(tmp_path)
    assert report["ownership_excluded"] == 2
    assert len(report["ownership_exclusion_reasons"]) == 2
    assert report["rules_seen"] == report["candidate_rule_units"] == 1
    rows = list(iter_jsonl(tmp_path / county_semantic_review.QUEUE))
    assert rows[0]["parent_rule_id"] == "LOCAL-RULE-GOOD"
    assert rows[0]["candidate_rule_unit"]["semantic_status"] == "needs_review"
    assert path.read_bytes() == original


def test_pilot_filters_identity_and_existing_retired_rules(
    tmp_path: Path, ownership_policy: OwnershipPolicy, caplog: pytest.LogCaptureFixture,
) -> None:
    """Regeneration keeps correct city and county identities without transferring ownership."""
    entry = {"source_id": "county_good", "authority_id": COUNTY, "authority_level": "county",
             "authority_type": "county", "name": "Boulder County",
             "url": "https://bouldercounty.gov/", "county_names": ["Boulder"]}
    registry = tmp_path / "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json"
    _json(registry, {"pilot": {"counties": [
        {**entry, "source_id": RETIRED, "url": CITY_URL}, entry,
    ]}})
    _json(tmp_path / "_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json", {"pilot": {
        "municipalities": [{**entry, "source_id": "city_good", "authority_id": CITY,
                            "authority_level": "municipal", "url": CITY_URL}],
    }})
    index = tmp_path / "08_County_Authorities/_index.jsonl"
    _rows(index, [
        {"id": ownership_policy.affected_parent_rule_ids[0], "entity_type": "local_rule"},
        {"id": "LOCAL-RULE-GOOD", "entity_type": "local_rule"},
        {"id": "OLD-IDENTITY", "entity_type": "local_authority"},
    ])
    original_registry, original_index = registry.read_bytes(), index.read_bytes()
    result = local_pilot.materialize_pilot_authorities(tmp_path)
    assert result == {"ownership_excluded": 2, "county": 1, "municipal": 1, "district": 0}
    assert "retired source ownership" in caplog.text
    assert "affected ownership identity" in caplog.text
    assert {r["id"] for r in iter_jsonl(index)} == {COUNTY, "LOCAL-RULE-GOOD"}
    assert registry.read_bytes() == original_registry
    assert any(p.read_bytes() == original_index for p in (tmp_path / "_SNAPSHOTS").rglob("*.jsonl"))


@pytest.mark.parametrize("excluded_layer", ["08_County_Authorities", "09_District_Authorities"])
def test_crosswalk_excludes_shared_metadata_and_index_only_aliases(
    tmp_path: Path, ownership_policy: OwnershipPolicy, caplog: pytest.LogCaptureFixture,
    excluded_layer: str,
) -> None:
    """A shared metadata path cannot revive a record excluded by its index provenance."""
    path = "08_County_Authorities/_meta/rules.jsonl"
    parent = ownership_policy.affected_parent_rule_ids[0]
    valid_layer = ("09_District_Authorities" if excluded_layer == "08_County_Authorities"
                   else "08_County_Authorities")
    _rows(tmp_path / valid_layer / "_index.jsonl", [
        {"id": "LOCAL-RULE-GOOD", "meta_path": path},
        {"id": "MISSING", "meta_path": "absent.jsonl"},
    ])
    _rows(tmp_path / excluded_layer / "_index.jsonl", [
        {"id": "RENAMED", "authority_id": COUNTY, "final_url": CITY_URL, "meta_path": path},
    ])
    common = {"entity_type": "local_rule", "state_authority_ids": ["CRS-30-28-101"]}
    _rows(tmp_path / path, [
        {**common, "id": "RENAMED"}, {**common, "id": parent},
        {**common, "id": "LOCAL-RULE-GOOD", "source_path": "raw.pdf",
         "source_citation_pages": {"CRS-30-28-101": [2]}, "source_section": "Section 1"},
        {**common, "id": "LOCAL-RULE-GOOD"}, {"id": "IDENTITY"},
    ])
    original = (tmp_path / path).read_bytes()
    result = local_crosswalk.build_local_crosswalks(tmp_path)
    assert result == {"forward": 1, "reverse": 1, "ownership_excluded": 3}
    assert "retired authority/URL attribution" in caplog.text
    rows = list(iter_jsonl(tmp_path / "_CROSSWALKS/local_rule_to_state_authority.jsonl"))
    assert rows[0]["source_id"] == "LOCAL-RULE-GOOD"
    assert rows[0]["source_evidence"] == "raw.pdf#page=2#section=Section 1"
    assert (tmp_path / path).read_bytes() == original


@pytest.mark.parametrize("mode", [{}, {"retry_failed": True}, {"unattempted_registered": True}])
def test_downloader_selection_modes_cannot_reintroduce_retired_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: dict[str, bool],
) -> None:
    """All selection branches apply the policy before fetching and preserve old outcomes."""
    entries = [
        {"source_id": RETIRED, "authority_id": COUNTY, "authority_level": "county",
         "url": CITY_URL},
        {"source_id": "redirect_alias", "authority_id": COUNTY, "authority_level": "county",
         "url": "https://bouldercounty.gov/old", "final_url": CITY_URL},
        {"source_id": "city_good", "authority_id": CITY, "authority_level": "municipal",
         "url": CITY_URL},
    ]
    _json(tmp_path / local_sources.REGISTRY_PATH, {"pilot": {"county_sources": entries}})
    history = [{"source_id": entry["source_id"], "source_url": entry["url"],
                "requested_url": entry["url"], "status": "failed"} for entry in entries]
    _rows(tmp_path / MANIFEST, [] if mode.get("unattempted_registered") else history)
    original = (tmp_path / MANIFEST).read_bytes()
    monkeypatch.setattr(local_sources, "build_session", lambda **kwargs: None)
    monkeypatch.setattr(
        local_sources, "GeodeHttpClient", lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    fetched = []

    def fetch(entry: dict[str, Any], *args: Any, **kwargs: Any) -> list:
        fetched.append(entry["source_id"])
        return []

    monkeypatch.setattr(local_sources, "_download_entry", fetch)
    summary = local_sources.download_pilot_sources(tmp_path, **mode)
    assert fetched == ["city_good"]
    assert summary.ownership_excluded == 2 and len(summary.ownership_exclusion_reasons) == 2
    assert (tmp_path / MANIFEST).read_bytes() == original


def test_age_status_boundaries_do_not_claim_live_currentness(tmp_path: Path) -> None:
    """Unknown dates and older attempts remain distinct from accepted source-age thresholds."""
    rows = [{"source_id": identity, "status": "downloaded", "retrieved_at": timestamp}
            for identity, timestamp in [
                ("no_date", None), ("bad_date", "not-a-date"),
                ("stale", "2025-01-01"), ("attention", "2026-03-01"),
                ("fresh", "2026-07-01T00:00:00Z"), ("fresh", "2026-01-01"),
            ]]
    _rows(tmp_path / MANIFEST, [*rows, {"source_id": "failed", "status": "failed"}, {}])
    report = local_freshness.build_local_source_freshness(tmp_path, today=date(2026, 7, 15))
    assert report["status_counts"] == {"attention": 1, "unknown": 2, "fresh": 1, "stale": 1}
    assert report["network_refresh_performed"] is False
    assert "does not prove live official freshness" in report["boundary"]
    with pytest.raises(ValueError, match="thresholds"):
        local_freshness.build_local_source_freshness(tmp_path, attention_after_days=-1)


def test_review_retains_unrelated_classification_and_version_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ownership filtering does not remove unrelated pending classification or history audits."""
    monkeypatch.setattr(local_review, "_write_promotion_queue_if_available", lambda *args: None)
    _rows(tmp_path / "_QUARANTINE/local_extraction_quarantine.jsonl", [
        {"source_id": "good", "source_category": "unclassified_local_source",
         "source_path": "county-zoning.html", "reason": "Unclassified"},
        {"source_id": "other", "source_category": "unclassified_local_source",
         "source_path": "unknown.html", "reason": "Unclassified"},
        {"source_id": "quarantine", "reason": "Extraction failed"},
    ])
    _rows(tmp_path / "08_County_Authorities/_index.jsonl", [{"entity_type": "local_authority"}])
    inactive = tmp_path / "08_County_Authorities/_meta/old_20250101.jsonl"
    _rows(inactive, [{"id": "OLD-GOOD"}])
    _json(tmp_path / "_CONTROL_PLANE/COUNTY_SOURCE_COVERAGE.json", {"counties": [
        None, {"county_id": COUNTY, "source_categories": {"invalid": None, "pending": {
            "status": "source_identified", "source_ids": ["not_attempted"],
        }}},
    ]})
    summary = local_review.build_local_review_queues(tmp_path)
    assert summary.source_classification_items == 2 and summary.metadata_version_items == 1
    assert summary.total_review_items == 4
    classified = list(iter_jsonl(tmp_path / local_review.CLASSIFICATION_QUEUE_PATH))
    assert [row["suggested_category"] for row in classified] == ["land_use_zoning", None]
    assert inactive.exists() and summary.ownership_excluded == 0


@pytest.mark.parametrize("module", [
    local_freshness, county_semantic_review, local_crosswalk, local_review,
])
def test_command_line_entries_use_the_same_policy_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: Any,
) -> None:
    """CLI runs stay offline and apply the same validated policy as callable entry points."""
    _rows(tmp_path / MANIFEST, [])
    _rows(tmp_path / "08_County_Authorities/_meta/local_rules.jsonl", [{
        "id": "LOCAL-RULE-EMPTY", "full_text": "A descriptive heading without a requirement.",
    }])
    monkeypatch.setattr(local_review, "_write_promotion_queue_if_available", lambda *args: None)
    monkeypatch.setattr(sys, "argv", ["ownership-test", "--root", str(tmp_path)])
    assert module.main() in (None, 0)
    (tmp_path / POLICY_PATH).unlink()
    with pytest.raises(FileNotFoundError):
        module.main()


@pytest.mark.parametrize("operation", ["review", "semantic", "pilot", "crosswalk"])
def test_explicit_active_parent_alias_cannot_regenerate_local_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    """A renamed child still follows its explicit parent to that parent's retired source."""
    parent = "LOCAL-RULE-RENAMED-PARENT"
    child = "LOCAL-RULE-RENAMED-CHILD"
    path = "08_County_Authorities/_meta/local_rules.jsonl"
    _rows(tmp_path / "08_County_Authorities/_index.jsonl", [
        {"id": parent, "entity_type": "local_rule", "source_id": RETIRED, "meta_path": path},
        {"id": child, "entity_type": "rule_unit" if operation == "review" else "local_rule",
         "parent_regulation_id": parent, "semantic_status": "semantic_ready", "meta_path": path},
    ])
    _rows(tmp_path / path, [{
        "id": child, "entity_type": "local_rule",
        "full_text": "Applicants must submit the form within 30 days.",
        "state_authority_ids": ["CRS-30-28-101"],
    }])
    _json(tmp_path / local_sources.REGISTRY_PATH, {"pilot": {}})
    original = (tmp_path / path).read_bytes()
    if operation == "review":
        monkeypatch.setattr(local_review, "_write_promotion_queue_if_available", lambda *a: None)
        report = local_review.build_local_review_queues(tmp_path)
        assert report.answer_safe_local_rule_units == report.semantic_review_items == 0
        assert report.ownership_excluded == 2
    elif operation == "semantic":
        report = county_semantic_review.build_county_semantic_review(tmp_path)
        assert report["candidate_rule_units"] == 0 and report["ownership_excluded"] == 1
    elif operation == "pilot":
        report = local_pilot.materialize_pilot_authorities(tmp_path)
        assert report["ownership_excluded"] == 2
        assert list(iter_jsonl(tmp_path / "08_County_Authorities/_index.jsonl")) == []
    else:
        report = local_crosswalk.build_local_crosswalks(tmp_path)
        assert report["forward"] == report["reverse"] == 0
        assert report["ownership_excluded"] == 2
    assert (tmp_path / path).read_bytes() == original


@pytest.mark.parametrize("redirect_at", ["landing", "direct", "page", "deep", None])
def test_actual_final_urls_survive_downloads_and_stop_retired_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, redirect_at: str | None,
    ownership_policy: OwnershipPolicy,
) -> None:
    """Observed redirects remain auditable and wrong-owner pages cannot spawn child requests."""
    urls = {
        "landing": "https://bouldercounty.gov/old",
        "direct": "https://bouldercounty.gov/one.pdf",
        "page": "https://bouldercounty.gov/building-codes",
        "deep": "https://bouldercounty.gov/two.pdf",
    }
    _json(tmp_path / local_sources.REGISTRY_PATH, {"pilot": {"county_sources": [{
        "source_id": "county_alias", "authority_id": COUNTY, "authority_level": "county",
        "url": urls["landing"],
    }]}})
    html = {
        "landing": '<a href="/one.pdf">Code</a><a href="/building-codes">Building codes</a>',
        "page": '<a href="/two.pdf">Additional code</a>',
    }
    fetched: list[str] = []

    def fetch(client: Any, url: str, **kwargs: Any) -> SimpleNamespace:
        fetched.append(url)
        key = next(key for key, value in urls.items() if value == url)
        content = html.get(key, "Preserved test bytes").encode()
        return SimpleNamespace(
            url=CITY_URL if key == redirect_at else url,
            headers={"Content-Type": "text/html" if key in html else "application/pdf"},
            content=content, text=content.decode(), status_code=200,
        )

    monkeypatch.setattr(local_sources, "_fetch", fetch)
    monkeypatch.setattr(local_sources, "build_session", lambda **kwargs: None)
    monkeypatch.setattr(
        local_sources, "GeodeHttpClient", lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    report = local_sources.download_pilot_sources(tmp_path)
    rows = list(iter_jsonl(tmp_path / MANIFEST))
    assert len(rows) == len(fetched)
    assert all(row["final_url"] for row in rows)
    excluded = [row for row in rows if row["status"] == "ownership_excluded"]
    assert len(excluded) == int(redirect_at is not None)
    assert report.ownership_excluded == len(excluded)
    assert report.downloaded == len(rows) - len(excluded)
    for row in excluded:
        assert row["final_url"] == CITY_URL
        assert ownership_policy.entity_exclusion_reason(row)
        assert Path(row["raw_path"]).is_file()
    if redirect_at == "landing":
        assert fetched == [urls["landing"]]
    elif redirect_at == "page":
        assert urls["deep"] not in fetched
    else:
        assert set(fetched) == set(urls.values())


def test_known_wrong_owner_link_is_not_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicitly retired linked page is excluded before its request, not after download."""
    url = "https://bouldercounty.gov/old"
    _json(tmp_path / local_sources.REGISTRY_PATH, {"pilot": {"county_sources": [{
        "source_id": "county_alias", "authority_id": COUNTY, "authority_level": "county",
        "url": url,
    }]}})
    html = f'<a href="{CITY_URL}">Building codes</a>'
    fetched = []

    def fetch(client: Any, requested: str, **kwargs: Any) -> SimpleNamespace:
        fetched.append(requested)
        assert requested == url
        return SimpleNamespace(url=url, headers={"Content-Type": "text/html"},
                               content=html.encode(), text=html, status_code=200)

    monkeypatch.setattr(local_sources, "_fetch", fetch)
    monkeypatch.setattr(local_sources, "_linked_pages", lambda *args: [CITY_URL])
    monkeypatch.setattr(local_sources, "build_session", lambda **kwargs: None)
    monkeypatch.setattr(
        local_sources, "GeodeHttpClient", lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    report = local_sources.download_pilot_sources(tmp_path)
    assert fetched == [url] and report.ownership_excluded == 1
    rows = list(iter_jsonl(tmp_path / MANIFEST))
    assert rows[-1]["status"] == "ownership_excluded"
    assert rows[-1]["requested_url"] == CITY_URL


def test_retried_redirect_preserves_history_and_is_not_download_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A retry that reaches a known wrong owner retains final provenance and no usable success."""
    url = "https://bouldercounty.gov/old"
    prior = {"source_id": "county_alias", "authority_id": COUNTY, "authority_level": "county",
             "source_url": url, "requested_url": url, "raw_path": str(tmp_path / "FAILED"),
             "status": "failed", "retrieved_at": "2026-07-20T00:00:00Z",
             "failure_class": "network_or_transport_failure"}
    _rows(tmp_path / MANIFEST, [prior])
    response = SimpleNamespace(url=CITY_URL, headers={"Content-Type": "text/plain"},
                               content=b"Preserved bytes", status_code=200)
    monkeypatch.setattr(local_sources, "_fetch", lambda *a, **k: response)
    monkeypatch.setattr(local_sources, "build_session", lambda **kwargs: None)
    monkeypatch.setattr(
        local_sources, "GeodeHttpClient", lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    report = local_sources.retry_failed_linked_sources(tmp_path)
    rows = list(iter_jsonl(tmp_path / MANIFEST))
    assert rows[0] == prior and len(rows) == 2
    assert rows[-1]["final_url"] == CITY_URL and rows[-1]["status"] == "ownership_excluded"
    assert report.downloaded == 0 and report.ownership_excluded == 1


def test_allowed_reuse_preserves_observed_final_url_and_original_retrieval_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid cached city outcome retains its observed redirect and dated provenance."""
    _json(tmp_path / local_sources.REGISTRY_PATH, {"pilot": {"municipal_sources": [{
        "source_id": "city_new_alias", "authority_id": CITY, "authority_level": "municipal",
        "url": CITY_URL,
    }]}})
    prior = {"source_id": "city_good", "authority_id": CITY, "authority_level": "municipal",
             "source_url": CITY_URL, "requested_url": CITY_URL, "final_url": CITY_URL + "/",
             "status": "downloaded", "retrieved_at": "2026-07-20T00:00:00Z",
             "raw_path": str(tmp_path / "raw.html"), "sha256": "a" * 64}
    _rows(tmp_path / MANIFEST, [prior])
    monkeypatch.setattr(
        local_sources, "_download_entry", lambda *a, **k: pytest.fail("fresh fetch"),
    )
    monkeypatch.setattr(local_sources, "build_session", lambda **kwargs: None)
    monkeypatch.setattr(
        local_sources, "GeodeHttpClient", lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    report = local_sources.download_pilot_sources(tmp_path, unattempted_registered=True)
    rows = list(iter_jsonl(tmp_path / MANIFEST))
    assert rows[0] == prior
    assert rows[-1]["final_url"] == prior["final_url"]
    assert rows[-1]["retrieved_at"] == prior["retrieved_at"]
    assert rows[-1]["source_id"] == "city_new_alias"
    assert report.downloaded == 1 and report.ownership_excluded == 0


def test_downloader_does_not_reuse_retired_history_for_correct_new_city_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid city registration must not inherit the retired county attempt's provenance."""
    _json(tmp_path / local_sources.REGISTRY_PATH, {"pilot": {"municipal_sources": [{
        "source_id": "city_good", "authority_id": CITY, "authority_level": "municipal",
        "url": CITY_URL,
    }]}})
    _rows(tmp_path / MANIFEST, [{
        "source_id": RETIRED, "source_url": CITY_URL, "requested_url": CITY_URL,
    }])  # Intentionally lacks fields required for eligible cached outcomes.
    original = (tmp_path / MANIFEST).read_bytes()
    monkeypatch.setattr(local_sources, "build_session", lambda **kwargs: None)
    monkeypatch.setattr(
        local_sources, "GeodeHttpClient", lambda **kwargs: SimpleNamespace(close=lambda: None),
    )
    monkeypatch.setattr(local_sources, "_reuse_record", lambda *args: pytest.fail("retired reuse"))
    fetched = []
    monkeypatch.setattr(
        local_sources, "_download_entry", lambda entry, *a, **k: fetched.append(entry) or [],
    )
    summary = local_sources.download_pilot_sources(tmp_path, unattempted_registered=True)
    assert [entry["source_id"] for entry in fetched] == ["city_good"]
    assert summary.ownership_excluded == 1
    assert "retired source ownership" in summary.ownership_exclusion_reasons[0]
    assert (tmp_path / MANIFEST).read_bytes() == original
