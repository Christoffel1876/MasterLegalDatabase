"""Strict, research-only custody and bounded review records."""
from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class File(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int = Field(ge=0)
class Slice(Strict):
    file: File
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    excerpt: str
    excerpt_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
class Observation(Strict):
    id: str
    event_id: str
    physical_page: int | None
    topic: str
    statement: str
    evidence: list[Slice]
    scope: Literal['selected_source_region', 'official_html_statement']
    legal_currentness: Literal['not_verified'] = 'not_verified'
class NativePage(Strict):
    page: int = Field(ge=1)
    native: File
    image: File | None
    visually_viewed: bool
    limitation: str | None = None
class PDF(Strict):
    event_id: str
    source: File
    pages: int = Field(ge=1)
    repaired: bool
    encrypted: bool
    engine: str
    version: str
    flags: int
    sort: Literal[False] = False
    metadata: dict[str, str | None]
    native_pages: list[NativePage]
    role: str
    date_limits: list[str]
    @model_validator(mode='after')
    def complete(self):
        if [p.page for p in self.native_pages] != list(range(1,self.pages+1)):
            raise ValueError('native page sequence mismatch')
        if any(p.visually_viewed and p.image is None for p in self.native_pages):
            raise ValueError('viewed page missing image')
        return self
class HistoricalRow(Strict):
    line: int
    line_sha256: str
    line_utf8: str
    row: dict
    matches: list[str]
    archive_reference: str | None
    local_availability: str
    local_recomputed_sha256: str | None
class Legacy(Strict):
    input_file: File
    compared_commit: str
    commit_hash_matched: bool
    total_lines: int
    matched_rows: list[HistoricalRow]
    counts_by_event: dict[str, dict[str,int]]
    manual_snapshot: File
    manual_rows: int
    manual_digest_matches: dict[str,int]
    note: str
class LinkBasis(Strict):
    event_id: str
    source_file: str
    source_kind: Literal['parsed_anchor', 'curl_redirect']
    exact_url: str
    exact_label: str | None
class Audit(Strict):
    task_id: Literal['atlas-mesa-grand-junction-directed-gaps-2026-09-11']
    prepared_at: datetime
    public_stop_at: datetime
    public_event_count: int = Field(le=14)
    distinct_requested_urls: int = Field(le=10)
    response_bytes: int
    acquired_pdf_bytes: int
    source_ownership: dict[str,str]
    basis: list[LinkBasis]
    pdfs: list[PDF]
    observations: list[Observation]
    legacy: Legacy
    unopened: list[str]
    limitations: list[str]
    distribution_header_sensitive_paths: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    completeness: Literal['not_assessed'] = 'not_assessed'
    scope: Literal['research_evidence_only'] = 'research_evidence_only'
class Inventory(Strict):
    task_id: str
    created_at: datetime
    exclusions: list[str]
    files: list[File]
    @model_validator(mode='after')
    def unique(self):
        paths=[f.path for f in self.files]
        if len(paths)!=len(set(paths)): raise ValueError('duplicate path')
        return self
