"""Typed source table evidence; no arithmetic or legal-effect normalization."""
from __future__ import annotations
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal
import hashlib
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')
class Asset(Strict):
    path: str
    sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int=Field(ge=0)
    @field_validator('path')
    @classmethod
    def safe(cls,v):
        p=PurePosixPath(v)
        if p.is_absolute() or '..' in p.parts or str(p)!=v or '\\' in v:raise ValueError('unsafe path')
        return v
class Span(Strict):
    physical_page: int=Field(ge=1,le=5)
    start: int=Field(ge=0)
    end: int=Field(ge=0)
    exact_text: str
    sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    @model_validator(mode='after')
    def bytes_match(self):
        b=self.exact_text.encode()
        if self.end-self.start!=len(b) or hashlib.sha256(b).hexdigest()!=self.sha256:raise ValueError('span bytes')
        return self
class NativeLine(Strict):
    line: int
    bbox: tuple[float,float,float,float]
    span: Span
class Page(Strict):
    physical_page: int=Field(ge=1,le=5)
    native: Asset
    image: Asset
    layout: Asset
    lines: list[NativeLine]
    directly_viewed: Literal[True]=True
class Cell(Strict):
    id: str
    anchor_row: int=Field(ge=0)
    anchor_column: int=Field(ge=0)
    row_span: int=Field(ge=1)
    column_span: int=Field(ge=1)
    bbox: tuple[float,float,float,float]
    geometric_extraction: str
    native_evidence: list[Span]
    blank: bool
class Row(Strict):
    id: str
    row_index: int=Field(ge=0)
    kind: Literal['header','body']
    cell_ids: list[str]
    fee_number_as_printed: str | None
    qualification_ids: list[str]
    annotation: str
class Table(Strict):
    id: str
    physical_page: int=Field(ge=1,le=5)
    title: str
    title_status: Literal['visible_source_title','continued_table_structural_label']
    x_grid: list[float]
    y_grid: list[float]
    extracted_matrix: list[list[str | None]]
    cells: list[Cell]
    rows: list[Row]
    column_meanings: list[str]
    qualification_ids: list[str]
    @model_validator(mode='after')
    def check_grid(self):
        nr=len(self.y_grid)-1;nc=len(self.x_grid)-1
        if [r.row_index for r in self.rows]!=list(range(nr)) or len(self.column_meanings)!=nc:raise ValueError('grid shape')
        if len(self.extracted_matrix)!=nr or any(len(r)!=nc for r in self.extracted_matrix):raise ValueError('matrix shape')
        cells={c.id:c for c in self.cells}
        if len(cells)!=len(self.cells):raise ValueError('duplicate cell')
        for row in self.rows:
            if len(row.cell_ids)!=nc:raise ValueError('row length')
            for col,cid in enumerate(row.cell_ids):
                c=cells[cid]
                if not(c.anchor_row<=row.row_index<c.anchor_row+c.row_span and c.anchor_column<=col<c.anchor_column+c.column_span):raise ValueError('merged cell association')
        return self
class Context(Strict):
    id: str
    physical_page: int
    kind: Literal['title','condition','valuation_note','footnote','unclassified_native_context']
    evidence: list[Span]
    applies_to: list[str]
    annotation: str
class Observation(Strict):
    id: str
    physical_pages: list[int]
    kind: Literal['source_anomaly','scope_limit','association','reading_order','date_role']
    related_ids: list[str]
    evidence: list[Span]
    statement: str
    treatment: str
class Crop(Strict):
    id: str
    physical_page: int
    clip: tuple[float,float,float,float]
    scale: float
    image: Asset
    directly_viewed: Literal[True]=True
class Review(Strict):
    review_id: Literal['ATLAS-MESA-BUILDING-FEES-2026-09-11']
    authority_id: Literal['CO-COUNTY-MESA']
    source: Asset
    candidate: Asset
    acquired_at: datetime
    source_url: str
    final_url: str
    prepared_at: datetime
    completed_at: datetime
    review_mode: Literal['atlas_candidate_aware_not_blind']
    external_assignment: None
    status: Literal['source_text_and_table_associations_reviewed']
    legal_currentness: Literal['not_verified']
    adoption_effectiveness: Literal['not_verified']
    engine: Literal['PyMuPDF']
    engine_version: Literal['1.28.2']
    native_flags: Literal[195]
    native_sort: Literal[False]
    render_scale: Literal[2.0]
    native_bytes: int
    native_byte_changes: Literal[0]
    pages: list[Page]
    tables: list[Table]
    contexts: list[Context]
    crops: list[Crop]
    observations: list[Observation]
    limits: list[str]
    @model_validator(mode='after')
    def references(self):
        if [p.physical_page for p in self.pages]!=[1,2,3,4,5]:raise ValueError('five ordered pages required')
        tids={t.id for t in self.tables};rids={r.id for t in self.tables for r in t.rows};cids={c.id for c in self.contexts}
        if len(tids)!=len(self.tables) or len(cids)!=len(self.contexts):raise ValueError('duplicate identity')
        for t in self.tables:
            if not set(t.qualification_ids)<=cids:raise ValueError('missing table qualification')
            for r in t.rows:
                if not set(r.qualification_ids)<=cids:raise ValueError('missing row qualification')
        for c in self.contexts:
            if not set(c.applies_to)<=tids|rids:raise ValueError('unknown context association')
        if self.native_bytes!=sum(p.native.bytes for p in self.pages):raise ValueError('native total')
        return self
class Inventory(Strict):
    files: list[Asset]
    excluded_self: Literal['evidence-manifest.json']
    @model_validator(mode='after')
    def unique(self):
        paths=[f.path for f in self.files]
        if paths!=sorted(set(paths)):raise ValueError('inventory duplicate/order')
        return self
class Layout(Strict):
    source_sha256: str
    page: int
    native_sha256: str
    text_dict: dict
class Preparation(Strict):
    source: Asset
    prepared_at: datetime
    source_url: str
    acquired_at: datetime
    custody_files: list[Asset]
    mode: Literal['candidate_aware_internal_review']
    note: str
