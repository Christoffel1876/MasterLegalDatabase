"""Materialize validated local authority identities for the bounded pilot."""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from geode.pipeline.local_release_ownership import ownership_reason_with_parents
from geode.pipeline.local_source_ownership import load_ownership_policy
from geode.schemas import ConfidenceScores, LayerIndexRecord, LocalAuthority
from geode.utils.file_io import atomic_write_jsonl, iter_jsonl, load_json

LOGGER = logging.getLogger(__name__)


def materialize_pilot_authorities(root: Path) -> dict[str, int]:
    """Write registered county, municipal, and district identities and indexes."""

    resolved_root = root.resolve()
    ownership = load_ownership_policy(resolved_root)
    registry = load_json(resolved_root / "_CONTROL_PLANE" / "LOCAL_SOURCE_REGISTRY.json")
    municipal_registry_path = resolved_root / "_CONTROL_PLANE" / "MUNICIPAL_SOURCE_REGISTRY.json"
    if municipal_registry_path.exists():
        municipal_registry = load_json(municipal_registry_path)
        registry.setdefault("pilot", {}).update(municipal_registry.get("pilot", {}))
    pilot = registry["pilot"]
    counts: dict[str, int] = {"ownership_excluded": 0}
    for level, layer, entries_key in (
        ("county", "08_County_Authorities", "counties"),
        ("municipal", "10_Municipal_Authorities", "municipalities"),
        ("district", "09_District_Authorities", "districts"),
    ):
        records = []
        for entry in pilot.get(entries_key, []):
            reason = ownership.entity_exclusion_reason(entry)
            if reason:
                counts["ownership_excluded"] += 1
                LOGGER.warning("Ownership exclusion during pilot materialization: %s", reason)
                continue
            records.append(_authority_from_entry(entry))
        metadata_path = resolved_root / layer / "_meta" / "local_authorities.jsonl"
        indexes = [_index_record(record, metadata_path, resolved_root, layer) for record in records]
        index_path = resolved_root / layer / "_index.jsonl"
        existing = list(iter_jsonl(index_path)) if index_path.exists() else []
        indexed = {str(row["id"]): row for row in existing if row.get("id")}
        existing_rules = []
        for row in existing:
            if row.get("entity_type") != "local_rule":
                continue
            reason = ownership_reason_with_parents(ownership, row, indexed)
            if reason:
                counts["ownership_excluded"] += 1
                LOGGER.warning("Ownership exclusion during pilot materialization: %s", reason)
            else:
                existing_rules.append(row)
        atomic_write_jsonl(metadata_path, records, resolved_root)
        atomic_write_jsonl(index_path, [*indexes, *existing_rules], resolved_root)
        counts[level] = len(records)
    return counts


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
