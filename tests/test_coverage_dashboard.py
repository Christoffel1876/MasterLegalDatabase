"""Evidence inventory regression tests: local existence is never legal currency."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from geode.constants import ALL_LAYERS
from geode.pipeline import coverage_dashboard as dashboard

NOW = datetime(2026, 9, 9, tzinfo=timezone.utc)
LFS = b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\nsize 12345\n"


def put(root: Path, name: str, value: object) -> Path:
    """Write a small JSON fixture."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def jsonl(root: Path, name: str, rows: list[dict]) -> Path:
    """Write streamed fixture records."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def index_row(layer: str = ALL_LAYERS[9], **changes: object) -> dict:
    """Build a schema-valid index declaration with an official source URL."""
    row = dict(id="LOCAL-1", layer=layer, entity_type="local_rule", title="A legal record",
               path=f"{layer}/_meta/local_rules.jsonl", meta_path=None,
               source_url="https://www.colorado.gov/example",
               source_path="_RAW_ARCHIVE/local/a.pdf",
               last_updated="2026-07-17T00:54:02Z", sha256="a" * 64, confidence=0.8,
               authority_id="CO-MUNICIPAL-A", authority_name="Town A", authority_level="municipal",
               source_category="ordinances", semantic_status="source_preservation_only")
    row.update(changes)
    return row


def source(**changes: object) -> dict:
    """Build a source catalog entry; it makes no collection claim."""
    row = dict(source_id="source-a", authority_id="CO-MUNICIPAL-A", authority_level="municipal",
               name="Town A", category="ordinances", url="https://www.colorado.gov/example")
    row.update(changes)
    return row


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """Minimal corpus with known-empty indexes and small source registries."""
    for layer in ALL_LAYERS:
        jsonl(tmp_path, f"{layer}/_index.jsonl", [])
        # A blank index is known-empty; a missing or LFS index is unknown.
        (tmp_path / layer / "_index.jsonl").write_text("\n")
    put(tmp_path, "_CONTROL_PLANE/SOURCE_REGISTRY.json", [])
    put(tmp_path, "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json", {"pilot": {}})
    put(tmp_path, "_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json", {"pilot": {}})
    put(tmp_path, "_CONTROL_PLANE/MUNICIPAL_EXPANSION_QUEUE.json", {"entries": []})
    jsonl(tmp_path, "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl", [])
    return tmp_path


def municipal_registry(root: Path, rows: list[dict]) -> None:
    """Install source entries in the municipal catalog."""
    put(root, "_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json",
        {"pilot": {"municipal_sources": rows}})


def report(root: Path) -> dashboard.CoverageDashboardReport:
    """Build deterministic reports for comparisons."""
    return dashboard.build_coverage_dashboard(root, generated_at=NOW)


def test_directory_entries_are_not_collected_legal_coverage(corpus: Path) -> None:
    municipal_registry(corpus, [source(), source(), source(
        source_id="all", authority_id="CO-MUNICIPAL-STATEWIDE", category="registry_discovery")])
    put(corpus, "_CONTROL_PLANE/MUNICIPAL_EXPANSION_QUEUE.json", {
        "incorporated_municipality_target": 273, "directory_entries": 270,
        "entries": [{"name": "Town A", "authority_id": "CO-MUNICIPAL-A"},
                    {"name": "Sheriden Lake"}, {"name": "Town B"}, {"name": "Town B"}],
    })
    result = report(corpus)
    assert len(result.jurisdictions) == 2
    town = result.jurisdictions[0]
    assert town.counts.catalog_sources == town.counts.catalog_urls == 1
    assert town.counts.indexed_rows == 0
    assert town.currency_status == result.currency_status == "not_live_verified"
    assert next(c for c in town.categories if c.category == "ordinances").status == "catalog_only"
    assert next(c for c in town.categories if c.category == "fees").status == "not_discovered"
    reconciliation = result.municipal_reconciliation
    assert reconciliation["recounted_directory_names"] == 2
    assert reconciliation["excluded_synthetic_authority_ids"] == ["CO-MUNICIPAL-STATEWIDE"]
    assert reconciliation["inherited_directory_entries"] == 270
    assert "Live currency has not been verified" in dashboard.render_markdown(result)


def test_lfs_missing_evidence_and_metadata_units_remain_explicit(corpus: Path) -> None:
    county = corpus / ALL_LAYERS[7] / "_index.jsonl"
    county.write_bytes(LFS)
    units = corpus / ALL_LAYERS[7] / "_meta/local_rule_units.jsonl"
    units.parent.mkdir()
    units.write_bytes(LFS)
    put(corpus, "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json", {"pilot": {"counties": [source(
        authority_id="CO-COUNTY-A", authority_level="county")]}})
    jsonl(corpus, f"{ALL_LAYERS[9]}/_index.jsonl", [index_row()])
    result = report(corpus)
    assert not result.layers[7].index_records_known
    assert result.layers[7].index_status == "lfs_pointer"
    town = next(r for r in result.jurisdictions if r.authority_level == "municipal")
    assert town.counts.record_kinds == {"source_preservation_only": 1}
    assert town.counts.raw_evidence_files == {"missing": 1}
    assert any(i.path.endswith("local_rule_units.jsonl") and i.status == "lfs_pointer"
               for i in result.inputs)
    assert "unknown (partial scan possible)" in dashboard.render_markdown(result)
    county.write_text("\n")
    assert report(corpus).layers[7].index_records_known


def test_repeated_attempts_and_partial_errors_do_not_inflate_downloads(corpus: Path) -> None:
    municipal_registry(corpus, [source()])
    raw = corpus / "_RAW_ARCHIVE/local/a.pdf"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"original")
    base = dict(source_id="source-a", requested_url="https://www.colorado.gov/a.pdf",
                status="downloaded", retrieved_at="2026-07-17T00:00:00Z",
                raw_path=r"C:\Users\intern\Geode\_RAW_ARCHIVE\local\a.pdf")
    rows = [base, base, dict(base, status="http_error", retrieved_at="2026-07-18T00:00:00Z"),
            dict(base, requested_url="https://www.colorado.gov/b.pdf", raw_path=None,
                 status="http_error"), {"status": "downloaded"}]
    path = jsonl(corpus, "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl", rows)
    with path.open("a") as stream:
        stream.write('not-json\n[]\n')
    result = report(corpus)
    counts = result.download_manifest
    assert counts.download_attempt_rows == 4
    assert counts.distinct_download_requests == counts.repeated_attempt_rows == 2
    assert counts.historical_failure_rows == counts.latest_recorded_request_failures == 2
    assert counts.raw_evidence_files == {"available": 1}
    assert result.jurisdictions[0].counts.raw_evidence_files == {"available": 1}
    assert next(i for i in result.inputs if i.role == "download_manifest").invalid_records == 3
    assert result.jurisdictions[0].currency_status == "not_live_verified"


def test_index_schema_failures_duplicates_and_declarations_are_separate(corpus: Path) -> None:
    raw = corpus / "_RAW_ARCHIVE/local/a.pdf"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(LFS)
    rows = [index_row(id="identity", entity_type="local_authority"), index_row(), index_row(),
            index_row(id="unit", entity_type="rule_unit", semantic_status=None),
            index_row(id="review", semantic_status="needs_review"),
            index_row(id="good", semantic_status="semantic_ready"),
            index_row(id="unknown", entity_type="novel", semantic_status=None),
            index_row(id="invalid", sha256="bad"), index_row(id="wrong", layer=ALL_LAYERS[7])]
    path = jsonl(corpus, f"{ALL_LAYERS[9]}/_index.jsonl", rows)
    with path.open("a") as stream:
        stream.write('null\n{broken}\n')
    result = report(corpus)
    counts = result.layers[9].counts
    assert counts.indexed_rows == 11
    assert counts.valid_index_rows == 7
    assert counts.schema_invalid_rows == 4
    assert counts.duplicate_ids == 1
    assert counts.record_kinds == dict(authority_identities=1, source_preservation_only=1,
                                       extracted_units=1, unreviewed_local_records=1,
                                       substantive_record_declarations=1, unclassified_records=1)
    assert counts.raw_evidence_files == {"lfs_pointer": 1}
    assert result.jurisdictions[0].counts.schema_invalid_rows == 2
    assert any("schema-invalid" in f for f in result.findings)


def test_state_catalog_and_acquisition_are_separate_from_legal_records(corpus: Path) -> None:
    put(corpus, "_CONTROL_PLANE/SOURCE_REGISTRY.json", [
        dict(source_id="ccr", url="https://www.sos.state.co.us/CCR/", target_layer=ALL_LAYERS[1]),
        dict(target_layer="unknown"), "invalid",
    ])
    rows = [index_row(ALL_LAYERS[1], entity_type="regulation_rule_acquisition", authority_id=None,
                      semantic_status=None), index_row(ALL_LAYERS[1], id="other",
                      entity_type="regulation_rule", semantic_status=None)]
    jsonl(corpus, f"{ALL_LAYERS[1]}/_index.jsonl", rows)
    result = report(corpus)
    assert result.layers[1].counts.catalog_sources == 1
    assert result.layers[1].counts.record_kinds == {
        "source_preservation_only": 1, "substantive_record_declarations": 1}


def test_unsafe_paths_symlinks_empty_and_missing_files(corpus: Path, tmp_path: Path) -> None:
    outside = corpus.parent / "outside-coverage"
    outside.write_text("private")
    (corpus / "leak").symlink_to(outside)
    rows = [index_row(id=str(i), source_path=p) for i, p in enumerate([
        "../outside-coverage", "leak", "/absolute/private", "X:/private",
        "_RAW_ARCHIVE/empty", "_RAW_ARCHIVE/directory"])]
    (corpus / "_RAW_ARCHIVE/directory").mkdir(parents=True)
    (corpus / "_RAW_ARCHIVE/empty").touch()
    jsonl(corpus, f"{ALL_LAYERS[9]}/_index.jsonl", rows)
    counts = report(corpus).layers[9].counts.raw_evidence_files
    assert counts == {"unsafe_path": 4, "directory": 1, "empty": 1}
    assert dashboard._status(corpus / "absent") == "missing"
    observed = dashboard._safe_path(corpus, "/old/root/_RAW_ARCHIVE/file")
    assert observed == corpus / "_RAW_ARCHIVE/file"


def test_invalid_and_unreadable_inputs_are_reported(corpus: Path, monkeypatch: pytest.MonkeyPatch
                                                   ) -> None:
    municipal_registry(corpus, ["bad", source(authority_id=""), source()])
    put(corpus, "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json", {"pilot": {"bad": 1}})
    (corpus / "_CONTROL_PLANE/SOURCE_REGISTRY.json").write_text("{broken")
    metadata = jsonl(corpus, f"{ALL_LAYERS[9]}/_meta/local_rule_units.jsonl", [{"id": "bad"}])
    broken = corpus / ALL_LAYERS[3] / "_index.jsonl"
    broken.write_bytes(b"\xff\xfe")
    result = report(corpus)
    assert result.layers[3].index_status == "unreadable"
    assert any(i.path == metadata.relative_to(corpus).as_posix() and i.invalid_records == 1
               for i in result.inputs)
    assert any("invalid or oversized registry" in f for f in result.findings)
    assert any("invalid source group" in f for f in result.findings)
    assert any("source without" in f for f in result.findings)
    original = Path.open

    def denied(path: Path, *args: object, **kwargs: object):
        if path.name == "deny":
            raise PermissionError("denied")
        return original(path, *args, **kwargs)

    deny = corpus / "deny"
    deny.touch()
    monkeypatch.setattr(Path, "open", denied)
    assert dashboard._status(deny) == "unreadable"


def test_registry_shapes_and_size_limits(corpus: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    put(corpus, "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json", [])
    put(corpus, "_CONTROL_PLANE/MUNICIPAL_EXPANSION_QUEUE.json", {"entries": "invalid"})
    assert any("registry structure is invalid" in f for f in report(corpus).findings)
    monkeypatch.setattr(dashboard, "MAX_REGISTRY_BYTES", 2)
    assert any("oversized registry" in f for f in report(corpus).findings)


def test_writes_are_validated_snapshotted_idempotent_and_safe(corpus: Path) -> None:
    result = report(corpus)
    output = corpus / ".geode_runtime/coverage"
    paths = dashboard.write_coverage_dashboard(result, output)
    original = paths["json"].read_bytes()
    assert dashboard.CoverageDashboardReport.model_validate_json(original) == result
    dashboard.write_coverage_dashboard(result, output)
    assert not (output / "_SNAPSHOTS").exists()
    changed = result.model_copy(update={"findings": ["New evidence finding"]})
    dashboard.write_coverage_dashboard(changed, output)
    snapshot = output / "_SNAPSHOTS" / (hashlib.sha256(original).hexdigest() + ".json")
    assert snapshot.read_bytes() == original
    dashboard.write_coverage_dashboard(result, output)
    dashboard.write_coverage_dashboard(changed, output)
    with pytest.raises(ValueError, match="outside corpus"):
        dashboard.write_coverage_dashboard(result, corpus / "_RAW_ARCHIVE/output")
    paths["json"].unlink()
    paths["json"].symlink_to(corpus / "_CONTROL_PLANE/SOURCE_REGISTRY.json")
    with pytest.raises(ValueError, match="symlink"):
        dashboard.write_coverage_dashboard(result, output)
    with pytest.raises(ValidationError):
        invalid = result.model_copy(update={"currency_status": "current"})
        dashboard.write_coverage_dashboard(invalid, output)
    with pytest.raises(ValidationError, match="timezone"):
        dashboard.build_coverage_dashboard(corpus, generated_at=datetime(2026, 9, 9))


def test_snapshot_integrity_and_atomic_cleanup(
    corpus: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = report(corpus)
    output = corpus / ".geode_runtime/coverage"
    paths = dashboard.write_coverage_dashboard(result, output)
    previous = paths["json"].read_bytes()
    directory = output / "_SNAPSHOTS"
    directory.symlink_to(corpus, target_is_directory=True)
    changed = result.model_copy(update={"findings": ["changed"]})
    with pytest.raises(ValueError, match="snapshot directory"):
        dashboard.write_coverage_dashboard(changed, output)
    directory.unlink()
    directory.mkdir()
    snapshot = directory / (hashlib.sha256(previous).hexdigest() + ".json")
    snapshot.symlink_to(paths["json"])
    with pytest.raises(ValueError, match="snapshot cannot"):
        dashboard.write_coverage_dashboard(changed, output)
    snapshot.unlink()
    snapshot.write_text("corruption")
    with pytest.raises(ValueError, match="corrupt"):
        dashboard.write_coverage_dashboard(changed, output)
    assert paths["json"].read_bytes() == previous

    def fail_replace(*args: object) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(dashboard.os, "replace", fail_replace)
    with pytest.raises(OSError):
        dashboard._atomic_bytes(output / "test.json", b"{}")
    assert not list(output.glob(".test.json.*"))


def test_cli_writes_only_requested_output(corpus: Path, caplog: pytest.LogCaptureFixture) -> None:
    output = corpus / ".geode_runtime/cli"
    assert dashboard.main(["--root", str(corpus), "--output-dir", str(output)]) == 0
    assert (output / "coverage-dashboard.json").exists()
    with caplog.at_level("INFO"):
        assert dashboard.main(["--root", str(corpus)]) == 0
    assert "not been verified" in caplog.text


@pytest.mark.parametrize("kinds,raw,expected", [
    ({}, {}, "not_discovered"),
    ({}, {"available": 1}, "source_bytes_only"),
    ({"substantive_record_declarations": 1}, {"available": 1}, "indexed_evidence_requires_review"),
    ({"source_preservation_only": 1}, {}, "preservation_or_unreviewed_only"),
])
def test_category_interpretation(kinds: dict, raw: dict, expected: str) -> None:
    counts = dashboard.CoverageCounts(record_kinds=kinds, raw_evidence_files=raw)
    assert dashboard._category_status(counts, "available") == expected
    assert dashboard._category_status(counts, "missing") == "index_unavailable"
    counts.schema_invalid_rows = 1
    assert dashboard._category_status(counts, "available") == "schema_errors"


def test_derived_source_path_and_missing_success_reference_are_not_originals(corpus: Path) -> None:
    derived = "07_Supplementary/federal.jsonl"
    jsonl(corpus, derived, [{"id": "federal-derived"}])
    jsonl(corpus, f"{ALL_LAYERS[6]}/_index.jsonl", [index_row(
        ALL_LAYERS[6], entity_type="federal_standard", source_path=derived,
        path=derived, semantic_status=None)])
    municipal_registry(corpus, [source()])
    jsonl(corpus, "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl", [dict(
        source_id="source-a", requested_url="https://www.colorado.gov/a.pdf",
        status="downloaded", retrieved_at="2026-07-17T00:00:00Z")])
    result = report(corpus)
    assert result.layers[6].counts.raw_evidence_files == {"not_original_archive": 1}
    assert result.download_manifest.raw_evidence_files == {"missing_reference": 1}
    counts = dashboard.CoverageCounts(latest_recorded_request_failures=1)
    assert dashboard._category_status(counts, "available") == "recorded_source_errors_need_recheck"
    counts.derived_files = {"missing": 1}
    assert dashboard._category_status(counts, "available") == "evidence_unavailable_or_incomplete"


def test_attempt_order_uses_aware_times_and_rejects_ambiguous_dates(corpus: Path) -> None:
    municipal_registry(corpus, [source()])
    base = dict(source_id="source-a", requested_url="https://www.colorado.gov/a.pdf",
                raw_path="_RAW_ARCHIVE/a.pdf", status="downloaded")
    jsonl(corpus, "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl", [
        dict(base, retrieved_at="2026-07-17T02:00:00+02:00", status="http_error"),
        dict(base, retrieved_at="2026-07-17T01:00:00Z"),
        dict(base, retrieved_at="2026-07-17"), dict(base, retrieved_at="invalid"),
    ])
    result = report(corpus)
    assert result.download_manifest.latest_recorded_request_failures == 0
    assert result.download_manifest.download_attempt_rows == 2
    assert next(i for i in result.inputs if i.role == "download_manifest").invalid_records == 2
    assert any("invalid attempt timestamp" in f for f in result.findings)
    assert any(i.path.endswith("10_Municipal_Authorities/_meta/local_rule_units.jsonl")
               and i.status == "missing" for i in result.inputs)
