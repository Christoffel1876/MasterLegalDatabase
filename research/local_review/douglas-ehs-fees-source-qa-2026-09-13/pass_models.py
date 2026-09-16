"""Model definitions copied from the unchanged original builder, without execution logic."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

class Row(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    row_id: str
    table: Literal['county', 'state']
    authority: str
    program: str
    fee_type: str
    unit: str
    fee: str | None

class Transcript(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal[1] = 1
    reviewer: Literal['Atlas'] = 'Atlas'
    frozen_at: str
    source_sha256: str
    image_sha256: str
    method: str
    headings: list[str]
    rows: list[Row] = Field(min_length=44, max_length=44)
    footnotes: list[str]
    limitations: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'

