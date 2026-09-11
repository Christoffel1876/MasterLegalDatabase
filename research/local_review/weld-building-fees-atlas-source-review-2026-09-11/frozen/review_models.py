"""Portable types for a bounded, candidate-aware PDF source review."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    path: str
    sha256: Digest
    size_bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if not value or path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
            raise ValueError("ordinary normalized package-relative path required")
        return value


class Span(Strict):
    physical_page: int = Field(ge=1, le=5)
    start_byte: int = Field(ge=0)
    end_byte_exclusive: int = Field(gt=0)
    exact_text: str
    sha256: Digest

    @model_validator(mode="after")
    def exact_bytes(self):
        data = self.exact_text.encode("utf-8")
        if len(data) != self.end_byte_exclusive - self.start_byte:
            raise ValueError("span byte length differs from unchanged UTF-8")
        if hashlib.sha256(data).hexdigest() != self.sha256:
            raise ValueError("span digest differs")
        return self


class Line(Strict):
    line_1based: int = Field(gt=0)
    span: Span
    classification: Literal["native_text", "native_whitespace"]


class Page(Strict):
    physical_page: int = Field(ge=1, le=5)
    source_sha256: Digest
    native: Asset
    image: Asset
    layout: Asset
    full_image_directly_viewed: Literal[True]
    lines: list[Line] = Field(min_length=1)
    viewed_crop_ids: list[str]
    observation: str


class Context(Strict):
    context_id: str
    kind: Literal["title", "condition", "footnote", "definition", "date_label", "column_group"]
    evidence: list[Span] = Field(min_length=1)
    association_note: str


class Column(Strict):
    column_id: str
    label: str
    label_origin: Literal["exact_native", "reviewer_structural_label"]
    evidence: list[Span]


class Table(Strict):
    table_id: str
    physical_page: int = Field(ge=1, le=5)
    title: list[Span] = Field(min_length=1)
    columns: list[Column] = Field(min_length=2)
    context_ids: list[str]
    expected_rows: int = Field(gt=0)
    structural_note: str


class Cell(Strict):
    column_id: str
    evidence: list[Span] = Field(min_length=1)
    display_text: str

    @model_validator(mode="after")
    def display_is_whitespace_only(self):
        expected = " ".join("".join(x.exact_text for x in self.evidence).split())
        if expected != self.display_text:
            raise ValueError("display text may only collapse source whitespace")
        return self


class FeeRow(Strict):
    row_id: str
    table_id: str
    physical_page: int = Field(ge=1, le=5)
    row_order: int = Field(gt=0)
    source_evidence: list[Span] = Field(min_length=1)
    cells: list[Cell] = Field(min_length=2)
    context_ids: list[str]
    crop_ids: list[str]
    status: Literal["source_text_and_association_reviewed"]
    annotation: str


class Observation(Strict):
    observation_id: str
    kind: Literal["source_anomaly", "reading_order", "association", "date_role", "scope_limit"]
    evidence: list[Span] = Field(min_length=1)
    related_row_ids: list[str]
    finding: str
    treatment: str


class Review(Strict):
    review_id: Literal["ATLAS-WELD-BUILDING-FEES-2026-09-11"]
    source_id: Literal["weld-building-fees-sd008-01"]
    source: Asset
    candidate: Asset
    preparation: Asset
    crop_manifest: Asset
    completed_at: datetime
    review_mode: Literal["atlas_candidate_aware_not_blind"]
    external_assignment: None
    reviewer: Literal["Atlas (Codex)"]
    scope: Literal["all_five_physical_pages_source_text_and_fee_associations"]
    native_bytes: Literal[14311]
    native_byte_changes: Literal[0]
    legal_currentness: Literal["not_verified"]
    adopted_status: Literal["not_verified"]
    original_http_acquisition: Literal["unconfirmed_supplied_claims_only"]
    official_source_url: None
    received_at: datetime
    supplied_url_claim: str
    pages: list[Page] = Field(min_length=5, max_length=5)
    tables: list[Table] = Field(min_length=1)
    rows: list[FeeRow] = Field(min_length=1)
    contexts: list[Context] = Field(min_length=1)
    observations: list[Observation] = Field(min_length=1)
    limits: list[str] = Field(min_length=1)

    @field_validator("completed_at", "received_at")
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("aware UTC-compatible time required")
        return value

    @model_validator(mode="after")
    def structure(self):
        if [p.physical_page for p in self.pages] != [1, 2, 3, 4, 5]:
            raise ValueError("all five physical pages in source order required")
        for collection, name in [(self.tables, "table_id"), (self.rows, "row_id"),
                                 (self.contexts, "context_id"), (self.observations, "observation_id")]:
            ids = [getattr(item, name) for item in collection]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate {name}")
        tables = {t.table_id: t for t in self.tables}
        contexts = {c.context_id for c in self.contexts}
        row_ids = {r.row_id for r in self.rows}
        for table in self.tables:
            cols = [c.column_id for c in table.columns]
            if len(cols) != len(set(cols)) or not set(table.context_ids) <= contexts:
                raise ValueError("invalid table columns/context")
            rows = [r for r in self.rows if r.table_id == table.table_id]
            if [r.row_order for r in rows] != list(range(1, table.expected_rows + 1)):
                raise ValueError("missing, duplicate, or reordered table row")
        for row in self.rows:
            table = tables.get(row.table_id)
            if table is None or row.physical_page != table.physical_page:
                raise ValueError("row escapes declared table/page")
            if [c.column_id for c in row.cells] != [c.column_id for c in table.columns]:
                raise ValueError("cell/column association mismatch")
            if not set(row.context_ids) <= contexts:
                raise ValueError("unknown row condition/footnote")
            for cell in row.cells:
                for span in cell.evidence:
                    if not any(span.physical_page == bound.physical_page == row.physical_page
                               and bound.start_byte <= span.start_byte < span.end_byte_exclusive <= bound.end_byte_exclusive
                               for bound in row.source_evidence):
                        raise ValueError("cell not within retained row evidence")
        if any(not set(o.related_row_ids) <= row_ids for o in self.observations):
            raise ValueError("observation references absent row")
        return self


class Inventory(Strict):
    inventory_version: Literal[1]
    source_id: Literal["weld-building-fees-sd008-01"]
    files: list[Asset]
    excluded_inventory_self: Literal["evidence-manifest.json"]
    limits: Literal["Hashes establish byte integrity, not legal currentness or independent human accuracy."]

    @model_validator(mode="after")
    def unique_paths(self):
        paths = [x.path for x in self.files]
        if paths != sorted(set(paths)):
            raise ValueError("inventory must use unique sorted paths")
        return self
