"""Read-only, evidence-based inventory of the checked-out Colorado corpus.

Index classifications describe inherited metadata, not verified legal obligations.
No network requests are made and no local date is treated as proof of currency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from geode.constants import ALL_LAYERS
from geode.schemas.models import LayerIndexRecord
from geode.schemas.validators import validate_record

LOGGER = logging.getLogger(__name__)
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"
MAX_REGISTRY_BYTES = 12_000_000
LOCAL_LAYERS = dict(zip(("county", "district", "municipal"), ALL_LAYERS[7:]))
EXPECTED_CATEGORIES = {
    "county": ("county_codes", "county_ordinances", "land_use_zoning",
               "building_construction", "emergency_fire_restrictions", "permits", "fees"),
    "municipal": ("municipal_code", "ordinances", "zoning_land_use", "building_code",
                  "fire_code", "permits", "fees"),
    "district": ("governing_rules", "permits", "fees", "service_area"),
}
FileStatus = Literal["available", "missing", "lfs_pointer", "unreadable", "directory",
                     "empty", "unsafe_path"]


class ReportModel(BaseModel):
    """Strict base for generated inventory records."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class InputFile(ReportModel):
    """Observed input availability; metadata counts are independent of index counts."""

    path: str
    role: str
    status: FileStatus
    records: int | None = None
    invalid_records: int = 0


class CoverageCounts(ReportModel):
    """Indexed record and distinct-file counts, never a legal completeness score."""

    indexed_rows: int = Field(default=0, ge=0)
    valid_index_rows: int = Field(default=0, ge=0)
    schema_invalid_rows: int = Field(default=0, ge=0)
    duplicate_ids: int = Field(default=0, ge=0)
    record_kinds: dict[str, int] = Field(default_factory=dict)
    raw_evidence_files: dict[str, int] = Field(default_factory=dict)
    derived_files: dict[str, int] = Field(default_factory=dict)
    catalog_sources: int = Field(default=0, ge=0)
    catalog_urls: int = Field(default=0, ge=0)
    download_attempt_rows: int = Field(default=0, ge=0)
    distinct_download_requests: int = Field(default=0, ge=0)
    repeated_attempt_rows: int = Field(default=0, ge=0)
    historical_failure_rows: int = Field(default=0, ge=0)
    latest_recorded_request_failures: int = Field(default=0, ge=0)


class CategoryCoverage(ReportModel):
    """Category coverage for one authority, including undiscovered checklist items."""

    category: str
    expected_checklist_item: bool
    status: str
    counts: CoverageCounts


class JurisdictionCoverage(ReportModel):
    """A real authority identity supported by a registry, directory, or index."""

    authority_id: str
    authority_level: str
    authority_name: str
    identity_sources: list[str]
    index_status: FileStatus
    counts: CoverageCounts
    categories: list[CategoryCoverage]
    currency_status: Literal["not_live_verified"] = "not_live_verified"


class LayerCoverage(ReportModel):
    """Layer totals; unavailable indexes have unknown row counts, not an empty corpus."""

    layer: str
    index_status: FileStatus
    index_records_known: bool
    counts: CoverageCounts
    currency_status: Literal["not_live_verified"] = "not_live_verified"


class CoverageDashboardReport(ReportModel):
    """Reproducible local inventory with explicit limitations and input failures."""

    schema_version: Literal[1] = 1
    generated_at: datetime
    root: str
    currency_status: Literal["not_live_verified"] = "not_live_verified"
    layers: list[LayerCoverage]
    jurisdictions: list[JurisdictionCoverage]
    inputs: list[InputFile]
    download_manifest: CoverageCounts
    municipal_reconciliation: dict[str, Any]
    findings: list[str]
    limitations: list[str]

    @field_validator("generated_at")
    @classmethod
    def aware_timestamp(cls, value: datetime) -> datetime:
        """Require a timezone so the inventory timestamp is unambiguous."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at requires a timezone")
        return value


class _Accumulator:
    """Small sets of identifiers and file paths, not copies of source records."""

    def __init__(self) -> None:
        self.counts = CoverageCounts()
        self.ids: set[str] = set()
        self.raw: dict[str, str] = {}
        self.derived: dict[str, str] = {}
        self.sources: set[str] = set()
        self.urls: set[str] = set()
        self.requests: dict[tuple[str, str], tuple[str, int, bool]] = {}

    def finish(self) -> CoverageCounts:
        self.counts.raw_evidence_files = dict(sorted(Counter(self.raw.values()).items()))
        self.counts.derived_files = dict(sorted(Counter(self.derived.values()).items()))
        self.counts.catalog_sources = len(self.sources)
        self.counts.catalog_urls = len(self.urls)
        self.counts.distinct_download_requests = len(self.requests)
        self.counts.repeated_attempt_rows = self.counts.download_attempt_rows - len(self.requests)
        self.counts.latest_recorded_request_failures = sum(v[2] for v in self.requests.values())
        return self.counts


def _safe_path(root: Path, value: str) -> Path | None:
    value = value.replace("\\", "/")
    # Rebase inherited workstation paths only at a known repository archive marker.
    if re.match(r"^[A-Za-z]:/", value) or value.startswith("/"):
        if "/_RAW_ARCHIVE/" not in value:
            return None
        value = "_RAW_ARCHIVE/" + value.split("/_RAW_ARCHIVE/", 1)[1]
    path = root / value
    if ".." in Path(value).parts or not path.resolve().is_relative_to(root):
        return None
    return path


def _status(path: Path | None) -> FileStatus:
    if path is None:
        return "unsafe_path"
    try:
        if not path.exists():
            return "missing"
        if path.is_dir():
            return "directory"
        with path.open("rb") as stream:
            prefix = stream.read(160)
        if not prefix:
            return "empty"
        return "lfs_pointer" if prefix.startswith(LFS_HEADER) else "available"
    except OSError:
        return "unreadable"


def _rows(path: Path, file: InputFile, findings: list[str]) -> Iterator[dict[str, Any]]:
    if file.status != "available":
        return
    file.records = 0
    try:
        with path.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                file.records += 1
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("expected an object")
                except (ValueError, TypeError):
                    file.invalid_records += 1
                    if file.invalid_records <= 3:
                        findings.append(f"{file.path}:{number}: invalid JSON object")
                    continue
                yield row
    except (OSError, UnicodeError):
        file.status = "unreadable"
        findings.append(f"{file.path}: scan interrupted; counts are partial")


def _registry(root: Path, name: str, inputs: list[InputFile],
              findings: list[str]) -> Any:
    path = root / "_CONTROL_PLANE" / name
    file = InputFile(path=f"_CONTROL_PLANE/{name}", role="registry", status=_status(path))
    inputs.append(file)
    if file.status != "available":
        return {}
    try:
        if path.stat().st_size > MAX_REGISTRY_BYTES:
            raise ValueError("registry exceeds bounded read limit")
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        file.invalid_records += 1
        findings.append(f"{file.path}: invalid or oversized registry")
        return {}


def _kind(row: LayerIndexRecord) -> str:
    if row.entity_type == "local_authority":
        return "authority_identities"
    if (row.semantic_status == "source_preservation_only"
            or row.entity_type.endswith("_acquisition")):
        return "source_preservation_only"
    if row.entity_type in {"rule_unit", "local_rule_unit"}:
        return "extracted_units"
    if row.entity_type == "local_rule" and row.semantic_status != "semantic_ready":
        return "unreviewed_local_records"
    if row.entity_type in {"statute_section", "regulation_rule", "local_rule", "bill",
                           "rulemaking_notice", "executive_order", "session_law", "ag_opinion",
                           "coprrr_review", "federal_standard"}:
        return "substantive_record_declarations"
    return "unclassified_records"


def _category_status(counts: CoverageCounts, index_status: str) -> str:
    if index_status != "available":
        return "index_unavailable"
    if counts.schema_invalid_rows:
        return "schema_errors"
    evidence = {**counts.raw_evidence_files, **counts.derived_files}
    if any(count for state, count in evidence.items() if state != "available"):
        return "evidence_unavailable_or_incomplete"
    if counts.latest_recorded_request_failures:
        return "recorded_source_errors_need_recheck"
    kinds = counts.record_kinds
    if kinds.get("substantive_record_declarations") or kinds.get("extracted_units"):
        return "indexed_evidence_requires_review"
    if kinds.get("source_preservation_only") or kinds.get("unreviewed_local_records"):
        return "preservation_or_unreviewed_only"
    if counts.raw_evidence_files.get("available"):
        return "source_bytes_only"
    return "catalog_only" if counts.catalog_sources else "not_discovered"


def build_coverage_dashboard(root: Path, *, generated_at: datetime | None = None
                             ) -> CoverageDashboardReport:
    """Inventory local indexes, source catalogs, metadata availability, and original references.

    JSONL files are streamed. Only distinct identifiers, paths, and aggregate counts
    are retained. Originals are probed for presence and LFS pointers, not parsed or
    assumed to match an index hash (which may describe extracted text).
    """
    root = root.resolve()
    inputs: list[InputFile] = []
    findings: list[str] = []
    layers = {name: _Accumulator() for name in ALL_LAYERS}
    authorities: dict[str, dict[str, Any]] = {}
    source_map: dict[str, tuple[str, str]] = {}
    probe_cache: dict[str, str] = {}

    def authority(key: str, level: str, name: str, origin: str) -> dict[str, Any] | None:
        if key.endswith("-STATEWIDE") or level not in LOCAL_LAYERS:
            return None
        if key not in authorities:
            authorities[key] = {"level": level, "name": name or key, "origins": set(),
                                "all": _Accumulator(), "categories": {}}
        item = authorities[key]
        if name and item["name"] == key:
            item["name"] = name
        item["origins"].add(origin)
        return item

    def category(item: dict[str, Any], name: str) -> _Accumulator:
        return item["categories"].setdefault(name, _Accumulator())

    def probe(value: str) -> tuple[str, str]:
        path = _safe_path(root, value)
        key = path.relative_to(root).as_posix() if path else value
        if key not in probe_cache:
            probe_cache[key] = _status(path)
        return key, probe_cache[key]

    def original_reference(value: str) -> tuple[str, str]:
        key, status = probe(value)
        if status != "unsafe_path" and not key.startswith("_RAW_ARCHIVE/"):
            status = "not_original_archive"
        return key, status

    state = _registry(root, "SOURCE_REGISTRY.json", inputs, findings)
    for row in state if isinstance(state, list) else []:
        if not isinstance(row, dict) or row.get("target_layer") not in layers:
            continue
        acc = layers[row["target_layer"]]
        if row.get("source_id"):
            acc.sources.add(str(row["source_id"]))
        if row.get("url"):
            acc.urls.add(str(row["url"]))

    municipal: dict[str, Any] = {}
    synthetic_ids: set[str] = set()
    for filename in ("LOCAL_SOURCE_REGISTRY.json", "MUNICIPAL_SOURCE_REGISTRY.json"):
        registry = _registry(root, filename, inputs, findings)
        if not isinstance(registry, dict) or not isinstance(registry.get("pilot", {}), dict):
            findings.append(f"{filename}: registry structure is invalid")
            continue
        if filename.startswith("MUNICIPAL"):
            municipal = registry
        for group, rows in registry.get("pilot", {}).items():
            if not isinstance(rows, list):
                findings.append(f"{filename}: invalid source group {group}")
                continue
            for row in rows:
                if not isinstance(row, dict):
                    findings.append(f"{filename}: invalid source entry")
                    continue
                key, level = str(row.get("authority_id", "")), str(row.get("authority_level", ""))
                if not key or level not in LOCAL_LAYERS:
                    findings.append(f"{filename}: source without a usable authority identity")
                    continue
                name = str(row.get("name", "")) if group in {
                    "counties", "districts", "municipalities"
                } else ""
                item = authority(key, level, name, filename)
                if item is None:
                    synthetic_ids.add(key)
                    continue
                cat = str(row.get("category") or "identity_or_unspecified_source")
                source_id = str(row.get("source_id") or "")
                if source_id:
                    source_map[source_id] = (key, cat)
                for acc in (item["all"], category(item, cat), layers[LOCAL_LAYERS[level]]):
                    if source_id:
                        acc.sources.add(source_id)
                    if row.get("url"):
                        acc.urls.add(str(row["url"]))

    queue = _registry(root, "MUNICIPAL_EXPANSION_QUEUE.json", inputs, findings)
    entries = queue.get("entries", []) if isinstance(queue, dict) else []
    entries = entries if isinstance(entries, list) else []
    directory_names: set[str] = set()
    for row in entries:
        if not isinstance(row, dict) or not row.get("name"):
            continue
        name = str(row["name"]).strip()
        # The archived CML directory misspells the incorporated town Sheridan Lake.
        # Census ACS25 identifies Sheridan Lake town (GEOID 0869700); it is not
        # a synthetic statewide discovery entry and must remain in this inventory.
        if name.casefold() == "sheriden lake":
            name = "Sheridan Lake"
        directory_names.add(name.casefold())
        key = str(row.get("authority_id") or "DIRECTORY-MUNICIPAL-" + name.upper())
        authority(key, "municipal", name, "MUNICIPAL_EXPANSION_QUEUE.json")

    index_files: dict[str, InputFile] = {}
    referenced_derived: set[str] = set()
    for layer, layer_acc in layers.items():
        path = root / layer / "_index.jsonl"
        file = InputFile(path=f"{layer}/_index.jsonl", role="index", status=_status(path))
        inputs.append(file)
        index_files[layer] = file
        for raw in _rows(path, file, findings):
            layer_acc.counts.indexed_rows += 1
            try:
                row = LayerIndexRecord.model_validate(raw)
                if row.layer != layer:
                    raise ValueError("index layer mismatch")
            except (ValidationError, ValueError):
                file.invalid_records += 1
                layer_acc.counts.schema_invalid_rows += 1
                item = authorities.get(str(raw.get("authority_id", "")))
                if item and LOCAL_LAYERS[item["level"]] == layer:
                    cat = str(raw.get("source_category") or "unclassified")
                    for acc in (item["all"], category(item, cat)):
                        acc.counts.indexed_rows += 1
                        acc.counts.schema_invalid_rows += 1
                if file.invalid_records <= 3:
                    findings.append(f"{file.path}: schema-invalid index row {raw.get('id', '?')}")
                continue
            targets = [layer_acc]
            if layer in LOCAL_LAYERS.values():
                level = next(level for level, name in LOCAL_LAYERS.items() if name == layer)
                key = row.authority_id or (row.id if row.entity_type == "local_authority" else "")
                if key:
                    item = authority(key, level, row.authority_name or row.title, file.path)
                    if item is not None:
                        targets += [item["all"], category(
                            item, row.source_category or "unclassified")]
                else:
                    findings.append(f"{file.path}: record {row.id} lacks authority_id")
            for acc in targets:
                if acc is not layer_acc:
                    acc.counts.indexed_rows += 1
                acc.counts.valid_index_rows += 1
                if row.id in acc.ids:
                    acc.counts.duplicate_ids += 1
                    continue
                acc.ids.add(row.id)
                kind = _kind(row)
                acc.counts.record_kinds[kind] = acc.counts.record_kinds.get(kind, 0) + 1
                if kind != "authority_identities":
                    key, status = original_reference(row.source_path)
                    acc.raw[key] = status
                for value in {row.path, row.meta_path} - {None}:
                    key, status = probe(str(value))
                    acc.derived[key] = status
                    referenced_derived.add(key)
        # Malformed JSON rows count toward original rows and schema failure totals.
        parsed_invalid = file.invalid_records - layer_acc.counts.schema_invalid_rows
        layer_acc.counts.schema_invalid_rows += parsed_invalid
        layer_acc.counts.indexed_rows += parsed_invalid

    # Enumerate metadata independently so an unavailable index cannot hide missing units.
    for layer in ALL_LAYERS:
        metadata_paths = set((root / layer / "_meta").glob("*.jsonl"))
        if layer in LOCAL_LAYERS.values():
            metadata_paths.update(root / layer / "_meta" / name for name in (
                "local_authorities.jsonl", "local_rules.jsonl", "local_rule_units.jsonl"))
        for path in sorted(metadata_paths):
            relative = path.relative_to(root).as_posix()
            file = InputFile(path=relative, role="metadata", status=_status(path))
            inputs.append(file)
            if layer in LOCAL_LAYERS.values():
                for row in _rows(path, file, findings):
                    valid, _ = validate_record(row)
                    if not valid:
                        file.invalid_records += 1
            referenced_derived.discard(relative)
    for relative in sorted(referenced_derived):
        inputs.append(InputFile(path=relative, role="indexed_content", status=probe(relative)[1]))

    manifest_acc = _Accumulator()
    manifest_path = root / "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl"
    manifest_file = InputFile(path="_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl",
                              role="download_manifest", status=_status(manifest_path))
    inputs.append(manifest_file)
    for number, row in enumerate(_rows(manifest_path, manifest_file, findings)):
        source_id = str(row.get("source_id") or "")
        url = str(row.get("requested_url") or row.get("source_url") or "")
        if not source_id or not url:
            manifest_file.invalid_records += 1
            continue
        targets = [manifest_acc]
        if source_id in source_map:
            key, cat = source_map[source_id]
            item = authorities[key]
            targets += [item["all"], category(item, cat), layers[LOCAL_LAYERS[item["level"]]]]
        failure = row.get("status") not in {"downloaded", "skipped_existing", "success"}
        stamp = str(row.get("retrieved_at") or "")
        try:
            parsed_stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if parsed_stamp.tzinfo is None or parsed_stamp.utcoffset() is None:
                raise ValueError("ambiguous attempt time")
            stamp = parsed_stamp.astimezone(timezone.utc).isoformat()
        except ValueError:
            manifest_file.invalid_records += 1
            if manifest_file.invalid_records <= 3:
                findings.append(f"{manifest_file.path}: invalid attempt timestamp")
            continue
        request = (source_id, url)
        for acc in targets:
            acc.counts.download_attempt_rows += 1
            acc.counts.historical_failure_rows += int(failure)
            previous = acc.requests.get(request)
            if previous is None or (stamp, number) > previous[:2]:
                acc.requests[request] = (stamp, number, failure)
            if row.get("raw_path"):
                key, status = original_reference(str(row["raw_path"]))
                acc.raw[key] = status
            elif not failure:
                acc.raw[f"missing-reference:{source_id}:{url}"] = "missing_reference"

    results: list[JurisdictionCoverage] = []
    for key, item in sorted(authorities.items()):
        level = item["level"]
        state = index_files[LOCAL_LAYERS[level]].status
        expected = EXPECTED_CATEGORIES[level]
        for cat in expected:
            category(item, cat)
        categories = []
        for cat, acc in sorted(item["categories"].items()):
            counts = acc.finish()
            categories.append(CategoryCoverage(
                category=cat, expected_checklist_item=cat in expected,
                status=_category_status(counts, state), counts=counts))
        results.append(JurisdictionCoverage(
            authority_id=key, authority_level=level, authority_name=item["name"],
            identity_sources=sorted(item["origins"]), index_status=state,
            counts=item["all"].finish(), categories=categories,
        ))
    municipal_rows = [row for row in results if row.authority_level == "municipal"]
    reconciliation = {
        "status": "requires_official_directory_reconciliation",
        "inherited_target": queue.get("incorporated_municipality_target")
        if isinstance(queue, dict) else None,
        "inherited_directory_entries": queue.get("directory_entries")
        if isinstance(queue, dict) else None,
        "inherited_directory_source_retrieved_at": queue.get("source_retrieved_at")
        if isinstance(queue, dict) else None,
        "directory_source_retrieval_status": queue.get(
            "source_retrieval_status", "inherited_unverified"
        ) if isinstance(queue, dict) else "unknown",
        "directory_generated_at": queue.get("generated_at") if isinstance(queue, dict) else None,
        "recounted_directory_names": len(directory_names),
        "authority_identities_in_inventory": len(municipal_rows),
        "registered_authority_ids": sum("MUNICIPAL_SOURCE_REGISTRY.json" in r.identity_sources
                                        for r in municipal_rows),
        "inherited_statewide_target": municipal.get("statewide_target"),
        "excluded_synthetic_authority_ids": sorted(synthetic_ids),
        "explanation": "Inherited target and directory/source counts are distinct from legal "
                       "coverage. Statewide discovery entries are not municipalities. The CML "
                       "spelling Sheriden Lake is normalized to Sheridan Lake, identified by "
                       "Census ACS25 as an incorporated town (GEOID 0869700, as of 2025-01-01). "
                       "These repository recounts do not verify today's active-government total "
                       "or turn directory generation time into source retrieval time.",
    }
    for file in inputs:
        if file.invalid_records:
            findings.append(f"{file.path}: {file.invalid_records} schema or structural errors")
        if file.status != "available":
            findings.append(f"{file.path}: {file.status}; {file.role} availability is incomplete")
    return CoverageDashboardReport(
        generated_at=generated_at or datetime.now(timezone.utc), root=str(root),
        layers=[LayerCoverage(layer=layer, index_status=index_files[layer].status,
                              index_records_known=index_files[layer].status == "available",
                              counts=acc.finish()) for layer, acc in layers.items()],
        jurisdictions=results, inputs=inputs, download_manifest=manifest_acc.finish(),
        municipal_reconciliation=reconciliation, findings=findings,
        limitations=[
            "This offline inventory does not establish live freshness, legal effective dates, "
            "publication cutoffs, repeal status, or complete jurisdiction coverage.",
            "Indexed record kinds are declarations in inherited metadata. Index schemas and local "
            "metadata schemas are checked; full state records and legal text are not "
            "validated here.",
            "Evidence counts are distinct referenced files per group, not record counts. Presence "
            "and LFS pointers are checked; content fidelity and original hashes are not verified.",
            "Download rows describe historical attempts. Repeats are collapsed by source ID and "
            "requested URL; latest recorded outcomes are not a new source check.",
            "The baseline local checklist is a planning minimum. District types and service areas "
            "need a complete official directory; inherited district identities are not "
            "statewide coverage.",
            "Only indexed evidence and local download-manifest references are inventoried. The "
            "historic raw hash manifest and unreferenced archive files require a separate "
            "recovery audit.",
        ],
    )


def render_markdown(report: CoverageDashboardReport) -> str:
    """Render a human-readable dashboard without implying legal currency."""
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["---", "title: Colorado coverage inventory",
             f"generated_at: {report.generated_at.isoformat()}",
             "---", "# Colorado coverage inventory", "", "**Live currency has not been verified.** "
             "Catalog entries, preserved sources, and indexed records are separate measures.", "",
             "| Layer | Index | Indexed rows | Invalid rows | "
             "Identity / preserved / units / substantive | "
             "Original files available / missing or unresolved |", "|---|---|---:|---:|---|---|"]
    for row in report.layers:
        counts, kinds = row.counts, row.counts.record_kinds
        numbers = " / ".join(str(kinds.get(k, 0)) for k in (
            "authority_identities", "source_preservation_only", "extracted_units",
            "substantive_record_declarations"))
        available = counts.raw_evidence_files.get("available", 0)
        absent = sum(counts.raw_evidence_files.values()) - available
        total = (counts.indexed_rows if row.index_records_known
                 else "unknown (partial scan possible)")
        lines.append(f"| {row.layer} | {row.index_status} | {total} | "
                     f"{counts.schema_invalid_rows} | "
                     f"{numbers} | {available} / {absent} |")
    lines += ["", "## Jurisdictions", "", "Catalog sources are discovery entries; a homepage "
              "does not demonstrate collection of codes, ordinances, permits, or fees.", "",
              "| Authority | Level | Catalog sources | Valid index rows | Categories with indexed "
              "substantive declarations or units | Currency |", "|---|---|---:|---:|---|---|"]
    for row in report.jurisdictions:
        substantive = [c.category for c in row.categories if
                       c.counts.record_kinds.get("substantive_record_declarations") or
                       c.counts.record_kinds.get("extracted_units")]
        categories = cell(", ".join(substantive) or "none evidenced in index")
        lines.append(f"| {cell(row.authority_name)} | {row.authority_level} | "
                     f"{row.counts.catalog_sources} | {row.counts.valid_index_rows} | "
                     f"{categories} | not verified |")
    category_totals: dict[tuple[str, str], list[int]] = {}
    for row in report.jurisdictions:
        for category in row.categories:
            key = (row.authority_level, category.category)
            totals = category_totals.setdefault(key, [0, 0, 0, 0])
            totals[0] += 1
            totals[1] += int(category.counts.catalog_sources > 0)
            kinds = category.counts.record_kinds
            totals[2] += int(bool(kinds.get("substantive_record_declarations")
                                 or kinds.get("extracted_units")))
            totals[3] += int(category.status == "evidence_unavailable_or_incomplete")
    lines += ["", "## Category evidence", "",
              "Counts below are authorities, not documents. The JSON report provides each "
              "authority's category status and evidence counts. Catalog discovery is not "
              "collection completeness.", "",
              "| Level / category | Authorities assessed | Catalog entry | Indexed substantive "
              "declarations or units | Missing or unresolved evidence |",
              "|---|---:|---:|---:|---:|"]
    for (level, category), totals in sorted(category_totals.items()):
        values = " | ".join(map(str, totals))
        lines.append(f"| {level} / {cell(category)} | {values} |")
    lines += ["", "## Municipal directory reconciliation", "",
              cell(report.municipal_reconciliation["explanation"]), "",
              "Recounted directory names: "
              f"{report.municipal_reconciliation['recounted_directory_names']}; "
              "registered authority IDs: "
              f"{report.municipal_reconciliation['registered_authority_ids']}.",
              "", "## Input findings", ""]
    lines += [f"- {cell(item)}" for item in report.findings] or ["- No input failures observed."]
    lines += ["", "## Interpretation limits", ""]
    lines += [f"- {cell(item)}" for item in report.limitations]
    return "\n".join(lines) + "\n"


def _atomic_bytes(path: Path, content: bytes) -> None:
    with NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def write_coverage_dashboard(report: CoverageDashboardReport, output_dir: Path) -> dict[str, Path]:
    """Write validated JSON and Markdown outside corpus layers; snapshot earlier report bytes."""
    report = CoverageDashboardReport.model_validate(report.model_dump())
    output_dir = output_dir.resolve()
    root = Path(report.root).resolve()
    reserved = (*ALL_LAYERS, "_RAW_ARCHIVE", "_CONTROL_PLANE", "_SNAPSHOTS", ".git")
    if any(output_dir.is_relative_to(root / name) for name in reserved):
        raise ValueError("dashboard output must be outside corpus and control-plane directories")
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {"json": ("coverage-dashboard.json", report.model_dump_json(indent=2) + "\n"),
                "markdown": ("coverage-dashboard.md", render_markdown(report))}
    outputs: dict[str, Path] = {}
    for kind, (name, value) in payloads.items():
        path, content = output_dir / name, value.encode("utf-8")
        if path.is_symlink():
            raise ValueError("report destination cannot be a symlink")
        if path.exists():
            previous = path.read_bytes()
            if previous == content:
                outputs[kind] = path
                continue
            snapshot_dir = output_dir / "_SNAPSHOTS"
            if snapshot_dir.is_symlink():
                raise ValueError("snapshot directory cannot be a symlink")
            snapshot_dir.mkdir(exist_ok=True)
            snapshot = snapshot_dir / (hashlib.sha256(previous).hexdigest() + path.suffix)
            if snapshot.is_symlink():
                raise ValueError("snapshot cannot be a symlink")
            if snapshot.exists() and snapshot.read_bytes() != previous:
                raise ValueError("snapshot hash collision or corrupt prior snapshot")
            if not snapshot.exists():
                _atomic_bytes(snapshot, previous)
        _atomic_bytes(path, content)
        outputs[kind] = path
    return outputs


def main(argv: list[str] | None = None) -> int:
    """Run the offline inventory, optionally writing a versioned report directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    report = build_coverage_dashboard(args.root)
    if args.output_dir:
        outputs = write_coverage_dashboard(report, args.output_dir)
        LOGGER.info("Coverage dashboard: %s", outputs["markdown"])
    else:
        LOGGER.info("%s", render_markdown(report))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
