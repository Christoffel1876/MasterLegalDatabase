"""Materialize validated local authority identities for the bounded pilot."""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from geode.pipeline.local_release_ownership import ownership_reason_with_parents
from geode.pipeline.local_source_ownership import OwnershipPolicy, load_ownership_policy
from geode.schemas import ConfidenceScores, LayerIndexRecord, LocalAuthority
from geode.utils.file_io import atomic_write_jsonl, iter_jsonl, load_json

LOGGER = logging.getLogger(__name__)
LAYERS = (
    ("county", "08_County_Authorities", "counties"),
    ("municipal", "10_Municipal_Authorities", "municipalities"),
    ("district", "09_District_Authorities", "districts"),
)


def materialize_pilot_authorities(root: Path) -> dict[str, int]:
    """Merge registered identities while preserving unrelated index and metadata records."""

    resolved_root = root.resolve()
    ownership = load_ownership_policy(resolved_root)
    registry = load_json(resolved_root / "_CONTROL_PLANE" / "LOCAL_SOURCE_REGISTRY.json")
    municipal_registry_path = resolved_root / "_CONTROL_PLANE" / "MUNICIPAL_SOURCE_REGISTRY.json"
    if municipal_registry_path.exists():
        municipal_registry = load_json(municipal_registry_path)
        registry.setdefault("pilot", {}).update(municipal_registry.get("pilot", {}))
    pilot = registry["pilot"]
    counts: dict[str, int] = {"ownership_excluded": 0}
    existing_indexes: dict[str, list[dict[str, Any]]] = {}
    indexed: dict[str, dict[str, Any]] = {}
    for _, layer, _ in LAYERS:
        index_path = resolved_root / layer / "_index.jsonl"
        existing = list(iter_jsonl(index_path)) if index_path.exists() else []
        identities = _rows_by_id(existing, str(index_path))
        if indexed.keys() & identities.keys():
            raise ValueError("duplicate existing index ID across local layers")
        indexed.update(identities)
        existing_indexes[layer] = existing

    writes: list[tuple[Path, list[dict[str, Any]]]] = []
    planned_indexes: list[dict[str, Any]] = []
    managed_metadata: dict[str, set[str]] = {}
    output_ids: set[str] = set()
    for level, layer, entries_key in LAYERS:
        records = []
        for entry in pilot.get(entries_key, []):
            reason = ownership_reason_with_parents(ownership, entry, indexed)
            if reason:
                counts["ownership_excluded"] += 1
                LOGGER.warning("Ownership exclusion during pilot materialization: %s", reason)
                continue
            records.append(_authority_from_entry(entry))
        metadata_path = resolved_root / layer / "_meta" / "local_authorities.jsonl"
        metadata = list(iter_jsonl(metadata_path)) if metadata_path.exists() else []
        _rows_by_id(metadata, str(metadata_path))
        generated_metadata = [record.model_dump(mode="json") for record in records]
        generated_indexes = [
            _index_record(record, metadata_path, resolved_root, layer).model_dump(mode="json")
            for record in records
        ]
        index_path = resolved_root / layer / "_index.jsonl"
        merged_index = _merge_authorities(
            existing_indexes[layer], generated_indexes, ownership, indexed, counts,
        )
        merged_metadata = _merge_authorities(
            metadata, generated_metadata, ownership, indexed, counts,
        )
        identities = {row["id"] for row in merged_index}
        if output_ids & identities:
            raise ValueError("generated authority ID collides across local layers")
        output_ids.update(identities)
        relative_meta = metadata_path.relative_to(resolved_root).as_posix()
        managed_metadata[relative_meta] = {row["id"] for row in merged_metadata}
        planned_indexes.extend(merged_index)
        writes.extend(((metadata_path, merged_metadata), (index_path, merged_index)))
        counts[level] = len(records)
    _validate_managed_metadata_references(planned_indexes, managed_metadata)
    for path, rows in writes:
        atomic_write_jsonl(path, rows, resolved_root)
    return counts


def _relative_reference(value: object) -> str:
    """Normalize a repository-relative POSIX reference without accessing the filesystem."""
    if not isinstance(value, str) or not value.strip() or "\\" in value or ":" in value:
        raise ValueError("index reference must be a repository-relative file path")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError("index reference must be a repository-relative file path")
    parts: list[str] = []
    for part in path.parts:
        if part == "..":
            if not parts:
                raise ValueError("index reference escapes the repository")
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        raise ValueError("index reference must name a file")
    return "/".join(parts)


def _validate_managed_metadata_references(
    indexes: list[dict[str, Any]], managed_metadata: dict[str, set[str]],
) -> None:
    """Check both lookup references against all planned managed metadata before any write."""
    for row in indexes:
        for field in ("meta_path", "path"):
            reference = row.get(field)
            if reference is None or reference == "":
                continue
            metadata_ids = managed_metadata.get(_relative_reference(reference))
            if metadata_ids is not None and row["id"] not in metadata_ids:
                raise ValueError(
                    f"managed authority metadata missing for preserved ID: {row['id']}"
                )


def _rows_by_id(rows: list[dict[str, Any]], context: str) -> dict[str, dict[str, Any]]:
    """Reject ambiguous identities without deduplicating or discarding existing records."""
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        identity = row.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError(f"missing or invalid record ID in {context}")
        if identity in indexed:
            raise ValueError(f"duplicate record ID in {context}: {identity}")
        indexed[identity] = row
    return indexed


def _merge_authorities(
    existing: list[dict[str, Any]], generated: list[dict[str, Any]],
    ownership: OwnershipPolicy, indexed: dict[str, dict[str, Any]], counts: dict[str, int],
) -> list[dict[str, Any]]:
    """Replace only targeted authorities in place and append new identities in registry order."""
    replacements = _rows_by_id(generated, "generated authorities")
    merged = []
    for row in existing:
        replacement = replacements.get(row["id"])
        if replacement is not None and row.get("entity_type") != "local_authority":
            raise ValueError(f"authority ID collides with a non-authority record: {row['id']}")
        reason = ownership_reason_with_parents(ownership, row, indexed)
        if reason:
            counts["ownership_excluded"] += 1
            LOGGER.warning("Ownership exclusion during pilot materialization: %s", reason)
        if replacement is not None:
            merged.append(replacements.pop(row["id"]))
        elif not reason:
            merged.append(row)
    merged.extend(replacements.values())
    return merged


def _authority_from_entry(entry: dict[str, object]) -> LocalAuthority:
    """Convert one registry entry into a validated local authority identity."""

    return LocalAuthority(
        id=str(entry["authority_id"]),
        authority_level=str(entry["authority_level"]),
        authority_type=str(entry["authority_type"]),
        name=str(entry["name"]),
        county_names=[str(value) for value in entry.get("county_names", [])],
        district_family=entry.get("district_family"),
        official_url=str(entry["url"]),
        source_url=str(entry["url"]),
        boundary_description="; ".join(str(value) for value in entry.get("known_gaps", [])),
        data_retrieved=date.today(),
        confidence=ConfidenceScores(overall=0.65, route="flag_accept"),
    )


def _index_record(
    record: LocalAuthority, metadata_path: Path, root: Path, layer: str,
) -> LayerIndexRecord:
    """Create a machine-readable index row for one local authority."""

    relative_meta = metadata_path.resolve().relative_to(root.resolve()).as_posix()
    source_hash = hashlib.sha256(str(record.source_url).encode("utf-8")).hexdigest()
    return LayerIndexRecord(
        id=record.id,
        layer=layer,
        entity_type=record.entity_type,
        title=record.name,
        citation=record.id,
        path=relative_meta,
        meta_path=relative_meta,
        source_url=record.source_url,
        source_path=f"_RAW_ARCHIVE/local/{record.authority_level}/{record.id}",
        last_updated=datetime.now(timezone.utc),
        sha256=source_hash,
        tags=[record.authority_type, *(record.county_names or [])],
        confidence=record.confidence.overall,
        authority_id=record.id,
        authority_name=record.name,
        authority_level=record.authority_level,
        authority_type=record.authority_type,
        district_family=record.district_family,
        county_names=record.county_names,
        geographic_scope=record.county_names,
    )
