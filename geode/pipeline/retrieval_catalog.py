"""Build a compact retrieval catalog across Geode layer indexes."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from geode.constants import CONTROL_PLANE_DIR
from geode.pipeline.county_semantic_mapping import CandidateMapping
from geode.pipeline.local_release_ownership import ownership_reason_with_parents
from geode.pipeline.local_source_ownership import (
    OwnershipPolicy,
    load_ownership_policy,
    requires_ownership_policy,
)
from geode.utils.file_io import atomic_write_json, atomic_write_jsonl, iter_jsonl, load_json

RETRIEVAL_CATALOG_PATH = Path(CONTROL_PLANE_DIR) / "RETRIEVAL_CATALOG.jsonl"
RETRIEVAL_CATALOG_SUMMARY_PATH = Path(CONTROL_PLANE_DIR) / "RETRIEVAL_CATALOG_SUMMARY.json"


class RetrievalCatalogRecord(BaseModel):
    """One compact record for broad AI-first retrieval."""

    id: str
    layer: str
    entity_type: str | None = None
    title: str | None = None
    citation: str | None = None
    path: str | None = None
    meta_path: str | None = None
    source_id: str | None = None
    source_url: str | None = None
    url: str | None = None
    requested_url: str | None = None
    final_url: str | None = None
    discovery_parent_url: str | None = None
    source_path: str | None = None
    parent_rule_id: str | None = None
    parent_regulation_id: str | None = None
    review_id: str | None = None
    candidate_rule_unit_id: str | None = None
    permanent_rule_unit_id: str | None = None
    mapping_status: str | None = None
    sha256: str | None = None
    publication_year: int | None = None
    last_updated: str | None = None
    authority_id: str | None = None
    authority_name: str | None = None
    authority_level: str | None = None
    authority_type: str | None = None
    district_family: str | None = None
    county_names: list[str] | None = None
    geographic_scope: list[str] | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float | None = None
    semantic_status: str | None = None
    answer_mode: str | None = None
    conditional_reason: str | None = None
    source_category: str | None = None
    source_page: int | None = None
    source_page_end: int | None = None
    source_line_start: int | None = None
    source_line_end: int | None = None
    retrieval_text: str


class RetrievalCatalogSummary(BaseModel):
    """Summary for retrieval catalog coverage."""

    generated_at: datetime
    catalog_path: str
    records_written: int = Field(ge=0)
    layers_indexed: int = Field(ge=0)
    layer_counts: dict[str, int] = Field(default_factory=dict)
    boundary: str


def build_retrieval_catalog(root: Path) -> tuple[list[RetrievalCatalogRecord], RetrievalCatalogSummary]:
    """Build compact retrieval records from layer indexes."""

    resolved_root = root.resolve()
    manifest = _load_dict(resolved_root / CONTROL_PLANE_DIR / "MASTER_MANIFEST.json")
    layers = manifest.get("data_layers") if isinstance(manifest.get("data_layers"), list) else []
    records: list[RetrievalCatalogRecord] = []
    policy: OwnershipPolicy | None = None
    layer_rows: list[tuple[str, list[dict[str, Any]]]] = []
    indexed_rows: dict[str, dict[str, Any]] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = _optional_str(layer.get("id"))
        index_file = _optional_str(layer.get("index_file"))
        if not layer_id or not index_file:
            continue
        rows = _read_jsonl(resolved_root / index_file)
        layer_rows.append((layer_id, rows))
        indexed_rows.update({str(row["id"]): row for row in rows if row.get("id")})
    for layer_id, rows in layer_rows:
        for row in rows:
            if requires_ownership_policy({**row, "layer": layer_id}):
                if policy is None:
                    policy = load_ownership_policy(resolved_root)
                if ownership_reason_with_parents(policy, row, indexed_rows):
                    continue
            record = _catalog_record(layer_id, row)
            if record:
                records.append(record)
    records.extend(_conditional_candidate_records(resolved_root, records, indexed_rows))
    layer_counts = Counter(record.layer for record in records)
    summary = RetrievalCatalogSummary(
        generated_at=datetime.now(timezone.utc),
        catalog_path=RETRIEVAL_CATALOG_PATH.as_posix(),
        records_written=len(records),
        layers_indexed=len(layer_counts),
        layer_counts=dict(sorted(layer_counts.items())),
        boundary=(
            "The retrieval catalog is a compact discovery index. It does not replace source text, "
            "metadata sidecars, validation, or crosswalk records."
        ),
    )
    return records, summary


def write_retrieval_catalog(root: Path) -> RetrievalCatalogSummary:
    """Write the retrieval catalog and summary."""

    resolved_root = root.resolve()
    records, summary = build_retrieval_catalog(resolved_root)
    atomic_write_jsonl(
        resolved_root / RETRIEVAL_CATALOG_PATH,
        (record.model_dump(mode="json", exclude_none=True) for record in records),
        resolved_root,
    )
    atomic_write_json(resolved_root / RETRIEVAL_CATALOG_SUMMARY_PATH, summary, resolved_root)
    return summary


def _catalog_record(layer_id: str, row: dict[str, Any]) -> RetrievalCatalogRecord | None:
    """Convert one layer index row into a retrieval catalog record."""

    record_id = _optional_str(row.get("id"))
    if not record_id:
        return None
    tags = row.get("tags") if isinstance(row.get("tags"), list) else []
    clean_tags = [str(tag) for tag in tags if str(tag).strip()]
    title = _optional_str(row.get("title"))
    citation = _optional_str(row.get("citation"))
    entity_type = _optional_str(row.get("entity_type"))
    retrieval_text = " | ".join(
        item
        for item in [
            record_id,
            layer_id,
            entity_type,
            citation,
            title,
            " ".join(clean_tags),
        ]
        if item
    )
    return RetrievalCatalogRecord(
        id=record_id,
        layer=layer_id,
        entity_type=entity_type,
        title=title,
        citation=citation,
        path=_optional_str(row.get("path")),
        meta_path=_optional_str(row.get("meta_path")),
        source_id=_optional_str(row.get("source_id")),
        source_url=_optional_str(row.get("source_url")),
        url=_optional_str(row.get("url")),
        requested_url=_optional_str(row.get("requested_url")),
        final_url=_optional_str(row.get("final_url")),
        discovery_parent_url=_optional_str(row.get("discovery_parent_url")),
        source_path=_optional_str(row.get("source_path")),
        parent_rule_id=_optional_str(row.get("parent_rule_id")),
        parent_regulation_id=_optional_str(row.get("parent_regulation_id")),
        review_id=_optional_str(row.get("review_id")),
        candidate_rule_unit_id=_optional_str(row.get("candidate_rule_unit_id")),
        permanent_rule_unit_id=_optional_str(row.get("permanent_rule_unit_id")),
        mapping_status=_optional_str(row.get("mapping_status")),
        sha256=_optional_str(row.get("sha256")),
        publication_year=_optional_int(row.get("publication_year")),
        last_updated=_optional_str(row.get("last_updated")),
        authority_id=_optional_str(row.get("authority_id")),
        authority_name=_optional_str(row.get("authority_name")),
        authority_level=_optional_str(row.get("authority_level")),
        authority_type=_optional_str(row.get("authority_type")),
        district_family=_optional_str(row.get("district_family")),
        county_names=[str(value) for value in row.get("county_names", []) if value]
        or None,
        geographic_scope=[str(value) for value in row.get("geographic_scope", []) if value]
        or None,
        tags=clean_tags,
        confidence=_optional_float(row.get("confidence")),
        semantic_status=_optional_str(row.get("semantic_status")),
        answer_mode=_optional_str(row.get("answer_mode")),
        conditional_reason=_optional_str(row.get("conditional_reason")),
        source_category=_optional_str(row.get("source_category")),
        source_page=_optional_int(row.get("source_page")),
        source_page_end=_optional_int(row.get("source_page_end")),
        source_line_start=_optional_int(row.get("source_line_start")),
        source_line_end=_optional_int(row.get("source_line_end")),
        retrieval_text=retrieval_text,
    )


def _conditional_candidate_records(
    root: Path,
    existing: list[RetrievalCatalogRecord],
    indexed_rows: dict[str, dict[str, Any]],
) -> list[RetrievalCatalogRecord]:
    """Expose quarantined county candidates as conditionally citable evidence."""

    queue_path = root / CONTROL_PLANE_DIR / "COUNTY_SEMANTIC_REVIEW_QUEUE.jsonl"
    mapping_path = root / CONTROL_PLANE_DIR / "COUNTY_SEMANTIC_CANDIDATE_MAP.jsonl"
    if not queue_path.exists() or not mapping_path.exists():
        return []
    policy = load_ownership_policy(root)
    existing_status = {record.id: record.semantic_status for record in existing}
    active = {
        **indexed_rows,
        **{str(row["id"]): row for row in _read_jsonl(
            root / "08_County_Authorities/_index.jsonl"
        ) if row.get("id")},
    }
    mapping_rows = list(iter_jsonl(mapping_path))
    mapping_counts = Counter(row.get("review_id") for row in mapping_rows)
    permanent_counts = Counter(row.get("permanent_rule_unit_id") for row in mapping_rows)
    mappings = {row.get("review_id"): row for row in mapping_rows}
    queue_rows = list(iter_jsonl(queue_path))
    review_counts = Counter(row.get("review_id") for row in queue_rows)
    candidate_counts = Counter(
        (row.get("candidate_rule_unit") or {}).get("id") for row in queue_rows
    )
    output: list[RetrievalCatalogRecord] = []
    for row in queue_rows:
        if not row.get("review_disposition"):
            continue
        candidate = row.get("candidate_rule_unit") or {}
        mapping = mappings.get(row.get("review_id")) or {}
        if (mapping_counts[row.get("review_id")] != 1
                or review_counts[row.get("review_id")] != 1
                or candidate_counts[candidate.get("id")] != 1
                or permanent_counts[mapping.get("permanent_rule_unit_id")] != 1
                or not _current_candidate_mapping(row, mapping, active)):
            continue
        if (ownership_reason_with_parents(policy, row, active)
                or ownership_reason_with_parents(policy, mapping, active)):
            continue
        mapped_id = str(mapping.get("permanent_rule_unit_id") or "")
        if mapped_id and existing_status.get(mapped_id) == "semantic_ready":
            continue
        record_id = mapped_id if mapped_id and mapped_id not in existing_status else (
            f"CONDITIONAL-{candidate.get('id') or row.get('review_id')}"
        )
        action = str(candidate.get("action_required") or "").strip()
        section = str(candidate.get("source_section") or "Source text")
        authority_name = str(row.get("authority_name") or "County authority")
        county_scope = _conditional_county_scope(authority_name)
        retrieval_text = " | ".join(
            item for item in (record_id, authority_name, section, action) if item
        )
        output.append(
            RetrievalCatalogRecord(
                id=record_id,
                layer="08_County_Authorities",
                entity_type="rule_unit",
                title=section,
                citation=f"{authority_name} — {section}",
                path=(CONTROL_PLANE_DIR + "/COUNTY_SEMANTIC_REVIEW_QUEUE.jsonl"),
                meta_path=(CONTROL_PLANE_DIR + "/COUNTY_SEMANTIC_REVIEW_QUEUE.jsonl"),
                source_id=_optional_str(row.get("source_id")),
                source_url=_optional_str(row.get("source_url")),
                url=_optional_str(row.get("url")),
                requested_url=_optional_str(row.get("requested_url")),
                final_url=_optional_str(row.get("final_url")),
                discovery_parent_url=_optional_str(row.get("discovery_parent_url")),
                source_path=_optional_str(row.get("source_path")),
                parent_rule_id=_optional_str(row.get("parent_rule_id")),
                parent_regulation_id=str(mapping["parent_regulation_id"]),
                review_id=str(row["review_id"]),
                candidate_rule_unit_id=str(candidate["id"]),
                permanent_rule_unit_id=str(mapping["permanent_rule_unit_id"]),
                mapping_status=str(mapping["mapping_status"]),
                sha256=_optional_str(row.get("source_hash")),
                authority_id=_optional_str(row.get("authority_id")),
                authority_name=_optional_str(row.get("authority_name")),
                authority_level="county",
                authority_type="county_authority",
                county_names=county_scope or None,
                geographic_scope=county_scope or None,
                tags=["conditional_evidence", str(row.get("source_category") or "local")],
                confidence=_optional_float(candidate.get("confidence", {}).get("overall"))
                if isinstance(candidate.get("confidence"), dict)
                else None,
                semantic_status="needs_review",
                answer_mode="conditional",
                conditional_reason=(
                    "The source passage is preserved and retrievable, but its legally responsible "
                    "party, binding status, or permanent identity has not been fully verified."
                ),
                source_category=_optional_str(row.get("source_category")),
                retrieval_text=retrieval_text,
            )
        )
    return output


def _current_candidate_mapping(
    row: dict[str, Any], mapping: dict[str, Any], active: dict[str, dict[str, Any]],
) -> bool:
    """Require a usable mapping bound to this exact candidate and any active records."""

    try:
        validated = CandidateMapping.model_validate(mapping)
    except ValidationError:
        return False
    if (validated.mapping_status not in {"planned_new", "mapped_existing"}
            or not validated.permanent_rule_unit_id):
        return False
    candidate = row.get("candidate_rule_unit") or {}
    parent = str(row.get("parent_rule_id") or candidate.get("parent_regulation_id") or "")
    parent_references = (
        row.get("parent_rule_id"), row.get("parent_regulation_id"),
        candidate.get("parent_rule_id"), candidate.get("parent_regulation_id"),
    )
    if (validated.review_id != row.get("review_id")
            or validated.candidate_rule_unit_id != candidate.get("id")
            or validated.parent_regulation_id != parent
            or any(value is not None and value != parent for value in parent_references)
            or validated.source_hash != row.get("source_hash")
            or validated.source_section != candidate.get("source_section")):
        return False
    if validated.mapping_status == "planned_new" and not re.fullmatch(
        re.escape(parent) + r"-UNIT-\d+", validated.permanent_rule_unit_id
    ):
        return False
    parent_row = active.get(parent)
    if parent_row is not None and parent_row.get("sha256") != validated.source_hash:
        return False
    unit = active.get(validated.permanent_rule_unit_id)
    if unit is None:
        return validated.mapping_status == "planned_new"
    unit_parent = str(unit.get("parent_regulation_id") or unit.get("parent_rule_id") or "")
    if not unit_parent:
        unit_parent = str(unit.get("id") or "").rsplit("-UNIT-", 1)[0]
    return (
        unit.get("entity_type") == "rule_unit"
        and unit_parent == parent
        and all(unit.get(key, parent) == parent for key in (
            "parent_regulation_id", "parent_rule_id"
        ))
        and unit.get("sha256") == validated.source_hash
        and unit.get("source_section") == validated.source_section
    )


def _conditional_county_scope(authority_name: str) -> list[str]:
    """Convert a county authority label into the local geography format."""

    normalized = authority_name.strip()
    if not normalized or normalized == "County authority":
        return []
    if normalized.casefold().startswith("city and county of "):
        return [f"{normalized[19:].strip()} County"]
    if normalized.casefold().endswith(" county"):
        return [normalized]
    return [f"{normalized} County"]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSONL rows if present."""

    if not path.exists() or path.stat().st_size == 0:
        return []
    return list(iter_jsonl(path))


def _load_dict(path: Path) -> dict[str, object]:
    """Load a JSON object, returning empty when absent."""

    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def _optional_str(value: object) -> str | None:
    """Convert a value to a non-empty optional string."""

    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    """Convert a value to an optional integer."""

    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    """Convert a value to an optional float."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    """Build or write retrieval catalog artifacts."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    summary = write_retrieval_catalog(root) if args.write else build_retrieval_catalog(root)[1]
    if args.json:
        print(summary.model_dump_json(indent=2))
        return
    print(f"Retrieval catalog records: {summary.records_written}")


if __name__ == "__main__":
    main()
