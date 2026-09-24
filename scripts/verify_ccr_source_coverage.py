"""Read-only verification of a portable CCR source-availability index; no network calls."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    """Closed, noncoercing index metadata."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """An exact ordinary file relative to the repository root."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0, le=25_000_000)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        """Reject absolute, ambiguous and parent-traversal paths."""
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or str(path) != value or "\\" in value:
            raise ValueError("Noncanonical repository path")
        return value


class Range(Strict):
    """Recorded timestamp bounds, not independently inferred legal dates."""

    minimum: str
    maximum: str


class Department(Strict):
    """Catalog identity and separately qualified retained metadata/source phase."""

    department_id: str = Field(pattern=r"^[1-9][0-9]*$")
    catalog_names: list[str]
    catalog_url: str
    phase: Literal["new_source_snapshot", "existing_metadata_only", "catalog_only"]
    state: Asset | None
    inventory: Asset | None
    publication_cutoff_claim: str | None
    rule_count: int | None
    source_classification_counts: dict[str, int] | None
    source_url_associations: int | None
    declared_unique_original_counts: dict[str, int] | None
    record_observed_range: Range | None
    source_retrieval_range: Range | None
    qualification: str
    review_status: Literal["source_fidelity_not_established_by_this_index"]
    answer_safe: Literal[False] = False
    currentness: Literal["not_verified"] = "not_verified"


class Index(Strict):
    """Portable source coverage; acquisition, extraction, review and currentness stay separate."""

    version: Literal[1] = 1
    prepared_at: str
    catalog: Asset
    catalog_url: str
    catalog_department_ids: list[str]
    departments: list[Department] = Field(min_length=1, max_length=30)
    new_department_ids: list[str]
    new_rule_record_count: int
    new_unique_original_counts: dict[str, int]
    existing_department_ids_excluded_from_new_totals: list[str]
    materialization_status: Literal["verified_local_materialization"]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    limitations: list[str]


def digest(body: bytes) -> str:
    """Hash exact retained bytes."""
    return hashlib.sha256(body).hexdigest()


def ordinary(root: Path, name: str, limit: int = 25_000_000) -> bytes:
    """Read a bounded ordinary repository member, refusing symlinks and LFS pointers."""
    Asset(path=name, sha256="0" * 64, size_bytes=0)
    path = root
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlink refused")
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Missing, nonordinary or oversized file")
    with path.open("rb") as handle:
        body = handle.read(limit + 1)
    if len(body) > limit or body.startswith(b"version https://git-lfs.github.com/spec/"):
        raise ValueError("Unavailable LFS object or oversized bytes")
    return body


def verify(root: Path, index: Index) -> dict[str, int | str]:
    """Replay exact source bindings for new departments and metadata only for existing12."""
    sys.path.insert(0, str(root))
    from geode.pipeline.ccr_current import CCRCurrentRecord, CCRState
    from scripts.publish_ccr_current import validate_payload

    total = 0

    def read(asset: Asset) -> bytes:
        """Capture and bind one index reference under a fixed total read budget."""
        nonlocal total
        body = ordinary(root, asset.path)
        total += len(body)
        if total > 600_000_000:
            raise ValueError("Read-only validation byte budget exceeded")
        if (len(body), digest(body)) != (asset.size_bytes, asset.sha256):
            raise ValueError(f"Index hash/size binding differs: {asset.path}")
        return body

    catalog = read(index.catalog)
    seen, names = set(), {}
    for anchor in BeautifulSoup(catalog, "html.parser").find_all("a", href=True):
        url = urlsplit(urljoin(index.catalog_url, str(anchor["href"])))
        if url.path == "/CCR/NumericalCCRDocList.do":
            values = parse_qs(url.query).get("deptID", [])
            if len(values) != 1 or not values[0].isascii() or not values[0].isdecimal():
                raise ValueError("Malformed source catalog identity")
            seen.add(values[0])
            labels = parse_qs(url.query).get("deptName", [])
            if len(labels) != 1 or not labels[0]:
                raise ValueError("Malformed source department label")
            names.setdefault(values[0], set()).add(labels[0])
    if sorted(seen, key=int) != index.catalog_department_ids:
        raise ValueError("Catalog denominator differs")
    identities = [item.department_id for item in index.departments]
    if len(identities) != len(set(identities)) or set(identities) != seen:
        raise ValueError("Duplicate or missing catalog index identity")
    records_total, new_ids, existing_ids, originals = 0, [], [], {}
    catalog_bound_to_new_state = False
    for item in index.departments:
        if (item.catalog_names != sorted(names[item.department_id])
                or item.catalog_url != index.catalog_url):
            raise ValueError("Catalog name or URL differs")
        if item.phase == "catalog_only":
            if any(value is not None for value in (
                item.state, item.inventory, item.rule_count, item.publication_cutoff_claim,
                item.source_classification_counts, item.source_url_associations,
                item.declared_unique_original_counts, item.record_observed_range,
                item.source_retrieval_range,
            )):
                raise ValueError("Catalog-only quantities must remain unknown")
            continue
        if item.state is None or item.inventory is None:
            raise ValueError("Snapshot metadata missing")
        stem = "02_Regulations_CCR/_verification/current/department-" + item.department_id
        if (item.state.path, item.inventory.path) != (stem + "-state.json", stem + ".jsonl"):
            raise ValueError("Department target path mismatch")
        state_body, inventory_body = read(item.state), read(item.inventory)
        state = CCRState.model_validate_json(state_body, strict=True)
        records = [CCRCurrentRecord.model_validate_json(line, strict=True)
                   for line in io.BytesIO(inventory_body) if line.strip()]
        if (state.department_id != item.department_id
                or state.catalog_url != item.catalog_url
                or digest(inventory_body) != state.inventory_sha256
                or sorted(state.rule_ids) != sorted(record.rule_id for record in records)
                or len({record.rule_id for record in records}) != len(records)
                or any(record.department_id != item.department_id
                       or record.source_publication_cutoff != state.source_publication_cutoff
                       for record in records)
                or len(records) != item.rule_count
                or dict(Counter(record.classification for record in records))
                != item.source_classification_counts
                or state.source_publication_cutoff.isoformat() != item.publication_cutoff_claim
                or len(state.sources) != item.source_url_associations):
            raise ValueError("Recorded metadata counts or identity differ")
        unique = {source.path: source for source in state.sources.values()}
        if (dict(Counter(Path(name).suffix for name in unique))
                != item.declared_unique_original_counts):
            raise ValueError("Declared original formats differ")
        observed = [record.observed_at for record in records]
        retrieved = [source.first_retrieved_at for source in state.sources.values()]
        if (item.record_observed_range != Range(minimum=min(observed).isoformat(),
                                                maximum=max(observed).isoformat())
                or item.source_retrieval_range != Range(minimum=min(retrieved).isoformat(),
                                                        maximum=max(retrieved).isoformat())):
            raise ValueError("Recorded timestamp bounds differ")
        if item.phase == "existing_metadata_only":
            existing_ids.append(item.department_id)
            continue
        new_ids.append(item.department_id)
        records_total += len(records)
        catalog_source = state.sources.get(index.catalog_url)
        if catalog_source and (
            catalog_source.path, catalog_source.sha256, catalog_source.bytes
        ) == (index.catalog.path, index.catalog.sha256, index.catalog.size_bytes):
            catalog_bound_to_new_state = True
        buffers = {item.state.path: state_body, item.inventory.path: inventory_body}
        for source in unique.values():
            buffers[source.path] = read(Asset(path=source.path, sha256=source.sha256,
                                             size_bytes=source.bytes))
            if source.path in originals and originals[source.path] != source.sha256:
                raise ValueError("Conflicting content-addressed original")
            originals[source.path] = source.sha256
        validate_payload(buffers.__getitem__, item.department_id)
    if (not catalog_bound_to_new_state
            or sorted(new_ids, key=int) != index.new_department_ids
            or sorted(existing_ids, key=int)
            != index.existing_department_ids_excluded_from_new_totals
            or records_total != index.new_rule_record_count
            or dict(Counter(Path(name).suffix for name in originals))
            != index.new_unique_original_counts):
        raise ValueError("Aggregate index quantities differ")
    return {"status": "pass", "catalog_departments": len(seen), "new_departments": len(new_ids),
            "new_rule_records": records_total, "new_unique_originals": len(originals),
            "existing_metadata_only_departments": len(existing_ids), "bytes_checked": total}


def main() -> None:
    """Read a portable index/schema and verify against an explicitly selected repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--index-sha256", required=True)
    args = parser.parse_args()
    index_path = args.index or (
        args.root / "_CONTROL_PLANE/CCR_SOURCE_COVERAGE_2026-09-23.json"
    )
    schema_path = args.schema or index_path.with_suffix(".schema.json")
    raw = index_path.read_bytes()
    if digest(raw) != args.index_sha256:
        raise ValueError("Index manifest pin differs")
    if len(raw) > 2_000_000:
        raise ValueError("Index is oversized")
    index = Index.model_validate_json(raw)
    schema = json.loads(schema_path.read_bytes())
    if schema != Index.model_json_schema():
        raise ValueError("Index schema differs")
    print(json.dumps(verify(args.root.resolve(), index), sort_keys=True))


if __name__ == "__main__":
    main()
