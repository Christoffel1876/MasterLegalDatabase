"""Typed offline audit and prepared-only directed follow-up."""
from datetime import datetime
from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra="forbid", strict=True)
class FileRef(Strict):
    path: str
    sha256: str=Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int=Field(ge=0)
    @field_validator("path")
    @classmethod
    def safe(cls,v):
        from pathlib import PurePosixPath
        p=PurePosixPath(v)
        if p.is_absolute() or ".." in p.parts or "\\" in v: raise ValueError("unsafe path")
        return v
class Finding(Strict):
    id: str
    disposition: Literal["accepted_with_limits","qualification","correction","unsupported_route"]
    statement: str
    evidence: list[FileRef]=Field(min_length=1)
class PdfObservation(Strict):
    action_id: str
    authority_id: str
    source: FileRef
    first_page_image: FileRef
    physical_pages: int=Field(ge=1)
    viewed_pages: list[int]
    role: str
    printed_claims: list[str]
    limitations: list[str]
class Audit(Strict):
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    assignment_id: Literal["SH-EXT-001"]
    status: Literal["accepted_for_limited_research_with_qualifications"]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    custody: FileRef
    comparison_commit: str
    counts: dict[str,int]
    findings: list[Finding]
    pdf_observations: list[PdfObservation]
    limits: list[str]
class Target(Strict):
    url: str
    purpose: str
    parent: FileRef
    parent_url: str
    exact_href: str
    exact_label: str
class Proposal(Strict):
    schema_version: Literal[1]
    status: Literal["PREPARED_NOT_DISPATCHED"]
    authority_id: Literal["CO-COUNTY-PUEBLO"]
    legal_currentness: Literal["not_verified"]
    max_public_actions: Literal[6]
    max_distinct_urls: Literal[4]
    max_source_bytes: Literal[10000000]
    max_total_body_bytes: Literal[20000000]
    planned_start: None
    planned_stop: None
    targets: list[Target]=Field(min_length=1,max_length=2)
    restrictions: list[str]
class Manifest(Strict):
    schema_version: Literal[1]
    files: list[FileRef]
    excluded_self: Literal["FINAL_MANIFEST.json"]
