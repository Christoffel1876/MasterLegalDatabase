"""Materialize the statewide municipality expansion queue from the CML directory."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from geode.utils.file_io import atomic_write_json, load_json


CML_SOURCE_ID = "municipal_statewide_cml_directory"
CML_RAW_PATH = Path("_RAW_ARCHIVE/local/municipal") / CML_SOURCE_ID / "landing_page.html"
OUTPUT_PATH = Path("_CONTROL_PLANE") / "MUNICIPAL_EXPANSION_QUEUE.json"
NAME_ALIASES = {"sheriden lake": "Sheridan Lake"}
CENSUS_REFERENCE_URL = (
    "https://tigerweb.geo.census.gov/tigerwebmain/Files/acs25/"
    "tigerweb_acs25_incplace_co.html"
)


class MunicipalDirectoryEntry(BaseModel):
    """A directory identity, retaining an original spelling when normalized."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)
    name: str
    cml_website: str | None
    status: Literal["registered", "not_registered"]
    authority_id: str | None = None
    source_name: str | None = None
    normalization_evidence_url: str | None = None

    @model_validator(mode="after")
    def registration(self) -> MunicipalDirectoryEntry:
        """Require registration identity and documented spelling corrections."""
        if (self.status == "registered") != (self.authority_id is not None):
            raise ValueError("Registered directory entries require an authority ID")
        if (self.source_name is None) != (self.normalization_evidence_url is None):
            raise ValueError("A normalized source name requires its evidence URL")
        return self


class MunicipalityReference(BaseModel):
    """A dated incorporated-place reference, not a claim of active governments today."""

    model_config = ConfigDict(extra="forbid")
    source_url: Literal[CENSUS_REFERENCE_URL] = CENSUS_REFERENCE_URL
    as_of: Literal["2025-01-01"] = "2025-01-01"
    incorporated_place_records: Literal[273] = 273
    scope: str = (
        "Census ACS25 incorporated-place records: 273 distinct Colorado GEOIDs. "
        "This is a dated reference, not a verified current active-government count. "
        "Bonanza has source FUNCSTAT I; Sheridan Lake town is GEOID 0869700."
    )


class MunicipalExpansionQueue(BaseModel):
    """Validate directory counts and distinguish generation from source retrieval."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    state: Literal["CO"] = "CO"
    authority_level: Literal["municipal"] = "municipal"
    source_id: Literal[CML_SOURCE_ID] = CML_SOURCE_ID
    source_url: str
    source_path: str
    source_retrieved_at: None = None
    source_retrieval_status: Literal["unknown_from_archived_page"] = "unknown_from_archived_page"
    generated_at: datetime
    incorporated_municipality_target: int = Field(ge=0)
    target_basis: MunicipalityReference = Field(default_factory=MunicipalityReference)
    directory_entries: int = Field(ge=0)
    registered_entries: int = Field(ge=0)
    not_registered_entries: int = Field(ge=0)
    excluded_non_municipal_entries: list[str] = Field(default_factory=list)
    entries: list[MunicipalDirectoryEntry]

    @field_validator("generated_at")
    @classmethod
    def aware_generation(cls, value: datetime) -> datetime:
        """Do not serialize a timezone-ambiguous generation timestamp."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Generation time requires a timezone")
        return value

    @model_validator(mode="after")
    def counts(self) -> MunicipalExpansionQueue:
        """Reject duplicate normalized names and inconsistent declared totals."""
        names = [_canonical_name(entry.name) for entry in self.entries]
        registered = sum(entry.status == "registered" for entry in self.entries)
        if len(set(names)) != len(names):
            raise ValueError("Directory names must be unique after normalization")
        if (self.directory_entries != len(names) or self.registered_entries != registered
                or self.not_registered_entries != len(names) - registered):
            raise ValueError("Directory totals do not match validated entries")
        if self.incorporated_municipality_target != self.target_basis.incorporated_place_records:
            raise ValueError("Municipality target must match its dated source reference")
        return self


def materialize_municipal_expansion_queue(root: Path) -> dict[str, int]:
    """Create a named queue for municipalities listed by the official CML page."""

    resolved_root = root.resolve()
    source_path = resolved_root / CML_RAW_PATH
    text = source_path.read_text(encoding="utf-8", errors="replace")
    start_marker = "Links to Colorado cities and towns"
    end_marker = "Updated May 6, 2024"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        raise ValueError("CML municipality link table was not found in the archived page")
    table = text[start:end]
    entries: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for item in re.findall(r"<li>(.*?)</li>", table, flags=re.IGNORECASE | re.DOTALL):
        name = re.sub(r"<[^>]+>", " ", item)
        name = html.unescape(re.sub(r"\s+", " ", name)).strip()
        name = re.sub(r"\s*\*\s*$", "", name).strip()
        source_name = name
        name = NAME_ALIASES.get(name.casefold(), name)
        identity = _canonical_name(name)
        if not name or identity in seen:
            continue
        seen.add(identity)
        href_match = re.search(r"href=[\"']([^\"']+)[\"']", item, flags=re.IGNORECASE)
        website = (urljoin("https://www.cml.org/", html.unescape(href_match.group(1)))
                   if href_match else None)
        entry = {"name": name, "cml_website": website, "status": "not_registered"}
        if name != source_name:
            entry.update(source_name=source_name, normalization_evidence_url=CENSUS_REFERENCE_URL)
        entries.append(entry)

    registry_path = resolved_root / "_CONTROL_PLANE" / "MUNICIPAL_SOURCE_REGISTRY.json"
    registry = load_json(registry_path)
    registered = {
        _canonical_name(str(entry["name"])): str(entry["authority_id"])
        for entry in registry.get("pilot", {}).get("municipalities", [])
    }
    for entry in entries:
        authority_id = registered.get(_canonical_name(str(entry["name"])))
        if authority_id:
            entry["status"] = "registered"
            entry["authority_id"] = authority_id

    registered_count = sum(entry["status"] == "registered" for entry in entries)
    payload = MunicipalExpansionQueue.model_validate({
        "schema_version": 1,
        "state": "CO",
        "authority_level": "municipal",
        "source_id": CML_SOURCE_ID,
        "source_url": "https://www.cml.org/home/networking-events/membership/membership",
        "source_path": CML_RAW_PATH.as_posix(),
        # Reading an archived page is not a new source download. Its original
        # retrieval time cannot be recovered from this page alone.
        "source_retrieved_at": None,
        "generated_at": datetime.now(timezone.utc),
        "incorporated_municipality_target": 273,
        "directory_entries": len(entries),
        "registered_entries": registered_count,
        "not_registered_entries": len(entries) - registered_count,
        "excluded_non_municipal_entries": [],
        "entries": entries,
    })
    atomic_write_json(resolved_root / OUTPUT_PATH, payload, resolved_root)
    return {
        "directory_entries": len(entries),
        "registered": sum(entry["status"] == "registered" for entry in entries),
        "not_registered": sum(entry["status"] == "not_registered" for entry in entries),
    }


def _canonical_name(value: str) -> str:
    """Normalize CML names against Geode's descriptive authority names."""

    normalized = re.sub(r"\s+", " ", value).strip().casefold()
    normalized = re.sub(r"^(city and county|city|town)\s+of\s+", "", normalized)
    normalized = NAME_ALIASES.get(normalized, normalized).casefold()
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


if __name__ == "__main__":
    print(json.dumps(materialize_municipal_expansion_queue(Path.cwd()), indent=2))
