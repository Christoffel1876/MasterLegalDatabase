"""Strict local source-review records; legal currentness is intentionally not established."""
from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    """Refuse unknown or coerced evidence fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """An exact relative payload identity."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Row(Strict):
    """A whole visual service/fee row, preserving uncomputed values and conditions."""
    row_id: str
    physical_page: int = Field(ge=2, le=4)
    group: str
    group_physical_page: int = Field(ge=2, le=4)
    service: str
    fee: str
    linked_context: list[str]


class Context(Strict):
    """Source wording outside the service/fee cells, with explicit applicability links."""
    context_id: str
    physical_page: int = Field(ge=1, le=5)
    kind: Literal['cover', 'heading', 'authority', 'approval_claim', 'note', 'definition',
                  'civil_penalty', 'group_heading', 'column_heading']
    text: str
    applies_to: list[str]


class FirstPass(Strict):
    """Actual source-image-first review, frozen before accessing native text."""
    frozen_at: AwareDatetime
    status: Literal['source_first_visual_transcript_frozen']
    source_id: Literal['el-paso-boh-ehs-fees-sd011']
    source: Ref
    capture: Ref
    page_images: list[Ref] = Field(min_length=5, max_length=5)
    full_pages_viewed: list[int]
    native_text_accessed_before_freeze: Literal[False]
    external_review_consulted: Literal[False]
    method: str
    rows: list[Row] = Field(min_length=65, max_length=65)
    contexts: list[Context]
    limitations: list[str]
    legal_currentness: Literal['not_verified']
    translation_equivalence: Literal['not_reviewed']

    @model_validator(mode='after')
    def links(self) -> FirstPass:
        """Enforce complete ordered row identities and known context references."""
        if self.full_pages_viewed != [1, 2, 3, 4, 5]:
            raise ValueError('All physical pages required')
        if [r.row_id for r in self.rows] != [f'R{i:03d}' for i in range(1, 66)]:
            raise ValueError('Ordered complete row identities required')
        contexts = {c.context_id for c in self.contexts}
        if len(contexts) != len(self.contexts):
            raise ValueError('Duplicate context identity')
        if any(set(r.linked_context) - contexts for r in self.rows):
            raise ValueError('Unknown context reference')
        return self


class Span(Strict):
    """Exact UTF-8 bytes from one unaltered physical native page."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    text: str


class Page(Strict):
    """Complete original native bytes with reproducible extraction settings."""
    physical_page: int = Field(ge=1, le=5)
    native: Ref
    image: Ref
    candidate_start: int = Field(ge=0)
    candidate_end: int = Field(ge=0)


class Binding(Strict):
    """Source row or context associated with its exact native page span."""
    identity: str
    physical_page: int = Field(ge=1, le=5)
    spans: list[Span] = Field(min_length=1)
    normalized_equal: bool
    note: str


class Review(Strict):
    """Additive comparison preserves the frozen source-first reading and native evidence."""
    completed_at: AwareDatetime
    status: Literal['source_visual_and_native_compared_pending_root_review']
    first_pass: Ref
    source: Ref
    candidate: Ref
    extraction_method: str
    extraction_version: str
    extraction_flags: Literal[195]
    extraction_sort: Literal[False]
    pages: list[Page] = Field(min_length=5, max_length=5)
    rows: list[Row] = Field(min_length=65, max_length=65)
    contexts: list[Context]
    bindings: list[Binding]
    errata: list[str]
    limitations: list[str]
    issuer: Literal['El Paso County Board of Health']
    administering_agency: Literal['El Paso County Public Health']
    source_approval_claim: Literal['October 25, 2023']
    source_effective_claim: Literal['January 1, 2024']
    legal_currentness: Literal['not_verified']
    translation_equivalence: Literal['not_reviewed']


class Inventory(Strict):
    """Closed set of every package file except the final manifest itself."""
    files: list[Ref]

    @model_validator(mode='after')
    def unique(self) -> Inventory:
        """Reject duplicate inventory identities."""
        if len({r.path for r in self.files}) != len(self.files):
            raise ValueError('Duplicate member')
        return self


class GridRow(Strict):
    """Two exact table cells, including merged-cell nulls and source geometry."""
    cells: list[str | None] = Field(min_length=2, max_length=2)
    cell_rectangles: list[list[float] | None] = Field(min_length=2, max_length=2)
    fee_row_id: str | None


class Table(Strict):
    """Complete physical table segment with unchanged extraction and explicit continuation."""
    physical_page: int = Field(ge=2, le=4)
    rectangle: list[float] = Field(min_length=4, max_length=4)
    rows: list[GridRow]
    carried_group_from_prior_page: str | None


class CompleteReview(Review):
    """Complete grid and contextual bindings supplement the untouched native pages."""
    tables: list[Table] = Field(min_length=3, max_length=3)
    native_bytes_preserved: Literal[8060]
    source_fee_rows: Literal[65]
    source_groups: Literal[7]
    source_table_grid_rows: Literal[74]
    geometry_method: Literal['PyMuPDF Page.find_tables default line strategy; 1 table on pages 2–4']
