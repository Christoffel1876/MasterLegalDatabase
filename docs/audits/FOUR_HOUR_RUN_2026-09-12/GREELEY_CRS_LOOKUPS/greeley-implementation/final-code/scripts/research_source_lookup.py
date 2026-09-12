"""Look up five fixed source reviews without current-law or applicability claims."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = "grand-junction-fire-fees-atlas-directed"
REVIEW_SOURCE_ID = "grand-junction-fire-fees-mg-07"
PACKAGE = Path("research/local_review/grand-junction-fire-fees-atlas-source-review-2026-09-11")
PINS = {
    "original.pdf": "1f7faf078188c26fa803e4ec6225d20caad2fcce48f69d2d2ae9563c96732884",
    "SOURCE_QA.json": "8069accad238166936f6ee519eb8cc35dc9a62ceb252597ea21a4ebc5efc520a",
    "MANIFEST.json": "ae22dfaabb6a0793f0e16849dacf5ead0b90e00d01d67c5ceebfb614072cc02f",
    "build_review.py": "9db445db05a1eb6810a649c14319f9451aff601b22722fe3fcaebbdaad565eea",
}
GREELEY_SOURCE_ID = "greeley-building-fees-sd008-06"
GREELEY_PACKAGE = Path("research/local_review/greeley-fees-atlas-source-review-2026-09-11")
GREELEY_REVIEW = "source-audits/EB-PDF-015/SOURCE_QA.json"
GREELEY_PDF = "packet/01-source-only/greeley-building-fees-sd008-06/original.pdf"
GREELEY_PINS = {
    "PACKAGE.json": "e85a4ffdee0ebd68fcd7361e628de3072eaa0adb6cdb19b1e4bd47e3064d6609",
    "PACKAGE.schema.json": "7254e694073e927f876291649156f40d6b35a41ddc1e7d69b56244a40cb6b794",
    "VALIDATION.json": "208124376c98d64215bb8528b33c55fb175cfadf770185a44313849d355cff1d",
    "VALIDATION.schema.json": "14f80f50b0ab430788f36ce7cba0b53fdcc089b471f76bf603d4332a51047f0e",
    "packet/manifest.json": "dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397",
    GREELEY_REVIEW: "6fd2f617a176aa821181a3ef3b52589f1fdc4c7ff64e00477f16149826142979",
    GREELEY_PDF: "fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4",
    "validate_package.py": "71ea4ce0f6d391fde63a4a2d0e58d889409278e8883ee9690f0b8d9c3a6447ef",
    "package_models.py": "ca6e4fa02f0cc9fdf64df688beb908a938770d325462b214197dfec59555c1e3",
    "packet/04-verification/verify_packet.py":
        "65f930c52cc712682d0eb734ed65ffcfb954e2e1a9f5b90b53a8db47a725c818",
    "source-audits/EB-PDF-016/build_review.py":
        "2395bdc5b31de1d9dcaf1c8b29ca8a59dae9c2fe86fbc9d383ce10be80c34691",
    "source-audits/EB-PDF-017/build_review.py":
        "314bb1448f68ecf50c371503219612f2f7db608a8fa19ca4b4c393b2451bf313",
    "source-audits/EB-PDF-017/review_models.py":
        "26a35d40ce44c49e003c6ed3b54ebcaa5af4980eb0e2642ddb2968b64a7da35e",
    "source-audits/EB-PDF-017/validate_source_review.py":
        "1f3510f6c8aeddc8c2ee85ec335914a74cd41212d7c8dcc5ef77909bede63dde",
}
GREELEY_BOUNDARY = (
    "The preserved source states these complete source blocks. This is a lookup of "
    "one checked page with 19 entries and 29 native spans, not current law, an "
    "applicability decision or a fee calculation. No matching entry does not establish "
    "that a service is free, exempt or unregulated. Other sources in the evidence "
    "package are outside this lookup."
)
BOUNDARY = (
    "The preserved source states the quoted text. This is a lookup of one checked "
    "57-row snapshot, not current law, an applicability decision or a fee calculation. "
    "No matching row does not establish that a service is free, exempt or unregulated."
)
WELD_SOURCE_ID = "weld-ehs-fees-2026-atlas-directed"
WELD_PACKAGE = Path("research/local_review/weld-directed-atlas-source-review-2026-09-11")
WELD_INTAKE = Path("research/local_review/weld-directed-intake-2026-09-11")
WELD_REVIEW = "frozen/ehs/SOURCE_QA.json"
WELD_PDF = "frozen/ehs/original.pdf"
WELD_PINS = {
    "evidence-manifest.json":
        "7928dbd366f95db4eddcfece663d6372265e4e1cc09f72b9cf6349220f1e78b0",
    "evidence-manifest.schema.json":
        "96890bd6a6bfc3577cad5784a81c737b6dffac6da328d6e3b5d99afee1824d88",
    "package-record.json":
        "cdb534f7012b5e38d65f7b34cffe69d2cc3c3484cdfbbc0ee6039d883f2238c5",
    WELD_REVIEW: "468658770c7f755c00dc844a2a62d1ce8c6afd458ba760a20fedfef2480ee97e",
    WELD_PDF: "852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3",
    "frozen/ehs/build_review.py":
        "a9411fb842d9cd1d1c7064601c01120121986e03827ee96f7cb1234ed1fe8f65",
}
WELD_INTAKE_PINS = {
    "intake-receipt.json":
        "13e1de8f33a6af1cd36a70d74c9b4275e07c2bcc0a832e53c100e55e3a0dcdaa",
}
WELD_BOUNDARY = (
    "The preserved source states these rows and notes. This is a checked three-page "
    "snapshot of 137 rows in eleven environmental-health service groups, not current "
    "law, an applicability decision or a fee calculation. A visibly blank fee is not "
    "zero; no matching row does not establish that a service is free, exempt or "
    "unregulated. Page notes retain their source scope; no contract replacement "
    "amount, adopting resolution or later amendment was reviewed."
)
WELD_VERIFICATION = {
    "status": "passed", "pages": 3, "native_bytes": 7367, "groups": 11, "rows": 137,
    "printed_fee_cells": 136, "blank_fee_cells": 1, "native_lines": 313,
    "row_geometry_checked": True, "legal_currentness": "not_verified",
}


IMPACT_SOURCE_ID = "greeley-development-impact-fee-memo-sd008-07"
PIF_SOURCE_ID = "greeley-water-sewer-proposed-pif-notice-sd008-08"
GRID_PACKAGE = Path("research/local_review/ebenezer-016-017-reconciliation-2026-09-12")
GRID_PINS = {
    "FINAL_MANIFEST.json": "4b9ca2a54ea75b0d2136500cf6af45e5d760659a1682b81991926efbf840bd6f",
    "SUPERSEDING_DISPOSITION.json":
        "1fb8621bf63e7e383309d4d0bcbe4242812561ed27c89ab6e53f830b81a10948",
    "AUDIT.json": "151afd3fb3f85ad92fda7a542e9ead12ea15f5ba76765df2b30f47725830f7f7",
    "verify_integration.py": "444604a2274d330c18f90a7a122888d27e0b182d5f5c3929c8a76525b2e73bbd",
}
GRID_SOURCES = {
    IMPACT_SOURCE_ID: ("016", "SOURCE_QA.json", 3, 30),
    PIF_SOURCE_ID: ("017", "SOURCE_REVIEW.json", 2, 8),
}
GRID_BOUNDARY = (
    "The preserved source states these reviewed rows, not current law, a computed charge "
    "or a determination of applicability. Printed columns, merged cells, blank cells and "
    "source qualifications remain distinct. No match does not establish free, exempt or "
    "unregulated activity. Legal dates and later adoption remain unverified."
)
PIF_CONDITION = (
    "Greeley is the issuer; Weld County homebuilders, building contractors and plumbing "
    "contractors are addressees, not the issuing county government. The notice proposes "
    "Water and Sewer Board review on December 16, 2020; its March 1, 2021 date is conditional: "
    "assuming they are adopted. The schedule heading alone does not establish adoption."
)
IMPACT_CONDITION = (
    "Greeley Finance Department memorandum, dated November 1, 2025, for the 2026 fee year; "
    "March 1, 2026 is a source-stated effective date, not independently verified. The memo's "
    "separate Water and Sewer adoption in December is prospective, with no explicit "
    "December year or rates, and does not establish adoption of the distinct 2020 PIF notice."
)

CURRENT_REQUEST = re.compile(
    r"\b(current(?:ly)?|today|now|latest|applicab\w*|appl(?:y|ies)|effective|"
    r"legal(?:ly)?|in force|calculate|calculation|owe|total cost)\b|"
    r"^\s*(what|how|is|are|can|may|must|do|does|should|will|would)\b|\?",
    re.IGNORECASE,
)


class StrictModel(BaseModel):
    """Keep source-only output fields explicit and reject unexpected fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class SpanBinding(StrictModel):
    """Identify an unchanged reviewed native span, including its exact bytes."""

    id: str
    physical_page: int
    native_path: str
    start: int
    end: int
    sha256: str


class SourceBinding(StrictModel):
    """Identify the canonical source and the review's historical alias separately."""

    canonical_source_id: Literal["grand-junction-fire-fees-atlas-directed"] = SOURCE_ID
    review_source_id: Literal["grand-junction-fire-fees-mg-07"] = REVIEW_SOURCE_ID
    authority_id: Literal["CO-MUNICIPAL-GRAND_JUNCTION"] = "CO-MUNICIPAL-GRAND_JUNCTION"
    source_url: str
    pdf_sha256: str
    review_sha256: str
    manifest_sha256: str
    verifier_sha256: str
    pdf_path: str
    review_path: str
    reviewed_at: AwareDatetime
    source_retrieved_at: AwareDatetime


class MatchedRow(StrictModel):
    """Preserve the full group, label and fee, including continuation provenance."""

    row_id: str
    physical_page: int
    group: str
    label: str
    fee: str
    group_basis: str
    group_binding: SpanBinding
    label_binding: SpanBinding
    fee_binding: SpanBinding
    page_image_path: str


class LookupResult(StrictModel):
    """A source-reporting result that never authorizes legal reliance."""

    status: Literal["matched", "no_matching_row", "refused_current_law"]
    source_id: Literal["grand-junction-fire-fees-atlas-directed"] = SOURCE_ID
    authority_id: Literal["CO-MUNICIPAL-GRAND_JUNCTION"] = "CO-MUNICIPAL-GRAND_JUNCTION"
    query: str | None
    evidence_verified: bool
    source: SourceBinding | None = None
    rows: list[MatchedRow]
    observations: list[str]
    page_context: dict[str, list[str]]
    boundary: str = BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None
    source_edition_date: None = None


class GreeleyBlock(StrictModel):
    """Bind an unchanged source block to native and packaged candidate UTF-8 bytes."""

    id: str
    text: str
    physical_page: Literal[1] = 1
    byte_basis: Literal["utf8_candidate_file_with_page_marker"] = (
        "utf8_candidate_file_with_page_marker"
    )
    candidate_path: str
    candidate_native_offset: Literal[56] = 56
    native_start: int = Field(ge=0)
    native_end: int = Field(le=3236)
    candidate_start: int
    candidate_end: int
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def check_bytes(self) -> GreeleyBlock:
        """Reject mixed offset bases or a text/hash/length mismatch."""
        raw = self.text.encode("utf-8")
        if (self.native_end <= self.native_start
                or self.native_end - self.native_start != len(raw)
                or self.candidate_start != 56 + self.native_start
                or self.candidate_end != 56 + self.native_end
                or hashlib.sha256(raw).hexdigest() != self.sha256):
            raise ValueError("Source block byte binding mismatch")
        return self


class GreeleyEntry(StrictModel):
    """Keep a complete fee clause and its reviewed headings and footnotes together."""

    entry_id: str
    kind: Literal["valuation_fee", "other_fee", "sales_tax", "temporary_electrical"]
    statement: GreeleyBlock
    headings: list[GreeleyBlock]
    footnotes: list[GreeleyBlock]
    page_image_path: str


class GreeleyDateStatement(StrictModel):
    """Quote a date label without turning it into a verified legal date."""

    role: Literal["schedule_title_year", "effective_heading_year", "unlabeled_footer"]
    evidence: GreeleyBlock
    interpretation: Literal["source_claim_only_not_verified_legal_date"] = (
        "source_claim_only_not_verified_legal_date"
    )


class GreeleySourceBinding(StrictModel):
    """Separate received custody, reported HTTP claims and the municipal source owner."""

    canonical_source_id: Literal["greeley-building-fees-sd008-06"] = GREELEY_SOURCE_ID
    review_source_id: Literal["greeley-building-fees-sd008-06"] = GREELEY_SOURCE_ID
    authority_id: Literal["CO-MUNICIPAL-GREELEY"] = "CO-MUNICIPAL-GREELEY"
    authority_basis: str
    official_source_url: None = None
    official_referral_url: str
    reported_requested_url: str
    reported_final_url: str
    reported_acquisition_at: AwareDatetime
    original_acquisition_time: None = None
    received_at: AwareDatetime
    reviewed_at: AwareDatetime
    acquisition_method: Literal["received_review_package"] = "received_review_package"
    intake_status: Literal["archived_pending_pipeline"] = "archived_pending_pipeline"
    upstream_http_acquisition_independently_verified: Literal[False] = False
    review_mode: Literal["candidate_aware_not_blind"] = "candidate_aware_not_blind"
    acquisition_qualification: str
    pdf_sha256: str
    review_sha256: str
    manifest_sha256: str
    verifier_sha256: str
    candidate_sha256: str
    packet_manifest_sha256: str
    pdf_path: str
    review_path: str
    provenance_path: str


class GreeleyLookupResult(StrictModel):
    """Report EB015 source evidence using its own whole-clause structure."""

    status: Literal["matched", "no_matching_row", "refused_current_law"]
    source_id: Literal["greeley-building-fees-sd008-06"] = GREELEY_SOURCE_ID
    authority_id: Literal["CO-MUNICIPAL-GREELEY"] = "CO-MUNICIPAL-GREELEY"
    query: str | None
    evidence_verified: bool
    source: GreeleySourceBinding | None = None
    entries: list[GreeleyEntry]
    context: list[GreeleyBlock]
    date_statements: list[GreeleyDateStatement]
    observations: list[str]
    boundary: str = GREELEY_BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    external_review_status: Literal["pending_not_intaken"] = "pending_not_intaken"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None
    source_edition_date: None = None


class WeldBlock(SpanBinding):
    """Keep an exact native line and its reviewed role, without text repair."""

    text: str
    role: Literal["blank", "header", "footer", "group", "label", "fee", "note"]

    @model_validator(mode="after")
    def check_bytes(self) -> WeldBlock:
        """Check text length, digest and physical byte coordinates."""
        raw = self.text.encode("utf-8")
        if (self.physical_page not in {1, 2, 3} or self.start < 0
                or self.end - self.start != len(raw) or not raw
                or hashlib.sha256(raw).hexdigest() != self.sha256):
            raise ValueError("Weld native byte binding mismatch")
        return self


class WeldRow(StrictModel):
    """Retain one fee cell, its possibly wrapped label and only its own row notes."""

    row_id: str
    physical_page: Literal[1, 2, 3]
    group: WeldBlock
    labels: list[WeldBlock] = Field(min_length=1)
    fee: WeldBlock | None
    fee_cell_status: Literal["printed_text", "visibly_blank"]
    notes: list[WeldBlock]
    page_image_path: str

    @model_validator(mode="after")
    def check_associations(self) -> WeldRow:
        """A blank is not a printed amount; all row spans retain roles and page."""
        if (self.fee is None) != (self.fee_cell_status == "visibly_blank"):
            raise ValueError("Weld fee presence/status mismatch")
        associations = [(self.group, "group")]
        associations += [(b, "label") for b in self.labels]
        associations += [(b, "note") for b in self.notes]
        if self.fee is not None:
            associations.append((self.fee, "fee"))
        if any(b.role != role or b.physical_page != self.physical_page
               for b, role in associations):
            raise ValueError("Weld row role/page mismatch")
        return self


class WeldPageContext(StrictModel):
    """Separate page notes and native header visibility from row applicability."""

    physical_page: Literal[1, 2, 3]
    header_visible: bool
    page_image_path: str
    spans: list[WeldBlock]
    scope: Literal["page_context_not_inferred_row_applicability"] = (
        "page_context_not_inferred_row_applicability"
    )


class WeldSourceBinding(StrictModel):
    """Bind county ownership, reviewed bytes and three distinct provenance clocks."""

    canonical_source_id: Literal["weld-ehs-fees-2026-atlas-directed"] = WELD_SOURCE_ID
    authority_id: Literal["CO-COUNTY-WELD"] = "CO-COUNTY-WELD"
    source_role: Literal["county_environmental_health_services_fee_schedule"]
    source_url: str
    final_url: str
    http_started_at: AwareDatetime
    source_retrieved_at: AwareDatetime
    reviewed_at: AwareDatetime
    received_at: AwareDatetime
    http_status: Literal[200] = 200
    tls_verified: Literal[True] = True
    acquisition_method: Literal["manual_official_download"] = "manual_official_download"
    acquisition_description: str
    intake_status: Literal["archived_pending_pipeline"] = "archived_pending_pipeline"
    pdf_sha256: str
    review_sha256: str
    manifest_sha256: str
    verifier_sha256: str
    intake_receipt_sha256: str
    pdf_path: str
    review_path: str
    provenance_path: str
    access_receipt_path: str
    access_receipt_sha256: str
    review_mode: Literal["atlas_candidate_aware_direct_source_review"]
    source_year_assertion: Literal["2026"] = "2026"
    year_interpretation: Literal["source_claim_only_not_verified_legal_date"] = (
        "source_claim_only_not_verified_legal_date"
    )


class WeldLookupResult(StrictModel):
    """Expose reviewed EHS evidence with null legal dates and a distinct context match."""

    status: Literal["matched", "matched_context_only", "no_matching_row", "refused_current_law"]
    source_id: Literal["weld-ehs-fees-2026-atlas-directed"] = WELD_SOURCE_ID
    authority_id: Literal["CO-COUNTY-WELD"] = "CO-COUNTY-WELD"
    query: str | None
    evidence_verified: bool
    source: WeldSourceBinding | None = None
    rows: list[WeldRow] = Field(max_length=137)
    page_context: list[WeldPageContext] = Field(max_length=3)
    matched_context_ids: list[str]
    observations: list[str]
    boundary: str = WELD_BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None
    source_edition_date: None = None



class GridBlock(StrictModel):
    """Preserve exact native UTF-8 bytes and their packaged candidate offsets."""

    physical_page: int = Field(ge=1, le=3)
    text: str
    native_start: int = Field(ge=0)
    native_end: int
    candidate_native_offset: int = Field(ge=0)
    candidate_start: int
    candidate_end: int
    candidate_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def check_bytes(self) -> GridBlock:
        """Reject text/hash mismatches and mixed page/candidate offset bases."""
        raw = self.text.encode("utf-8")
        if (not raw or self.native_end - self.native_start != len(raw)
                or self.candidate_start != self.candidate_native_offset + self.native_start
                or self.candidate_end != self.candidate_native_offset + self.native_end
                or hashlib.sha256(raw).hexdigest() != self.sha256):
            raise ValueError("Grid byte binding mismatch")
        return self


class GridCell(StrictModel):
    """Keep reviewed display text separate from exact contributing native strings."""

    column_start: int = Field(ge=1, le=8)
    column_span: int = Field(ge=1, le=8)
    text: str | None
    status: Literal["native_bound_visible_text", "visually_blank"]
    native_spans: list[GridBlock]

    @model_validator(mode="after")
    def check_blank(self) -> GridCell:
        """A blank is neither a zero nor an invented unit or amount."""
        if self.column_start + self.column_span > 9:
            raise ValueError("Grid cell exceeds columns")
        if self.status == "visually_blank":
            if self.text or self.native_spans:
                raise ValueError("Blank grid cell contains text")
        elif not self.text or not self.native_spans:
            raise ValueError("Printed grid cell lacks evidence")
        return self


class GridRowEvidence(StrictModel):
    """Represent one source row, including merged and blank cells."""

    row_id: str
    physical_page: int = Field(ge=1, le=3)
    role: str
    cells: list[GridCell] = Field(min_length=1)

    @model_validator(mode="after")
    def check_columns(self) -> GridRowEvidence:
        """Require ordered contiguous columns and native evidence on the row's page."""
        cursor = 1
        for cell in self.cells:
            if cell.column_start != cursor:
                raise ValueError("Grid columns overlap or have a gap")
            cursor += cell.column_span
            if any(b.physical_page != self.physical_page for b in cell.native_spans):
                raise ValueError("Grid cell belongs to a different physical page")
        return self


class GridMatchedRow(GridRowEvidence):
    """Attach explicit table/group/header associations to each matched fee row."""

    table_id: str
    column_roles: list[str | None]
    column_headers: list[GridRowEvidence]
    group_headers: list[GridRowEvidence]
    table_headings: list[GridBlock]
    association_notes: list[str]
    page_image_path: str


class GridContext(StrictModel):
    """Expose complete source notes without silently converting them into operative rules."""

    id: str
    role: str
    statement: str
    qualification: str
    native_spans: list[GridBlock]
    page_image_paths: list[str]


class GridSourceBinding(StrictModel):
    """Separate source dates, reported acquisition, intake and qualified external review."""

    source_id: Literal[
        "greeley-development-impact-fee-memo-sd008-07",
        "greeley-water-sewer-proposed-pif-notice-sd008-08",
    ]
    authority_id: Literal["CO-MUNICIPAL-GREELEY"] = "CO-MUNICIPAL-GREELEY"
    source_role: Literal["development_impact_fee_memorandum", "proposed_water_sewer_pif_notice"]
    official_source_url: None = None
    official_referral_url: str
    reported_requested_url: str
    reported_final_url: str
    reported_acquisition_at: AwareDatetime
    original_acquisition_time: None = None
    received_at: AwareDatetime
    reviewed_at: AwareDatetime
    external_reconciliation_at: AwareDatetime
    superseding_disposition_at: AwareDatetime
    acquisition_method: Literal["received_review_package"] = "received_review_package"
    acquisition_qualification: str
    pdf_path: str
    pdf_sha256: str
    candidate_path: str
    candidate_sha256: str
    review_path: str
    review_sha256: str
    provenance_path: str
    packet_manifest_sha256: str
    reconciliation_path: str
    reconciliation_sha256: str
    superseding_disposition_path: str
    superseding_disposition_sha256: str
    package_manifest_sha256: str
    verifier_sha256: str


class GridLookupResult(StrictModel):
    """Return source table evidence with mandatory context and unknown legal dates."""

    status: Literal["matched", "matched_context_only", "no_matching_row", "refused_current_law"]
    source_id: Literal[
        "greeley-development-impact-fee-memo-sd008-07",
        "greeley-water-sewer-proposed-pif-notice-sd008-08",
    ]
    authority_id: Literal["CO-MUNICIPAL-GREELEY"] = "CO-MUNICIPAL-GREELEY"
    query: str | None
    evidence_verified: bool
    source: GridSourceBinding | None = None
    rows: list[GridMatchedRow] = Field(max_length=30)
    context: list[GridContext]
    context_tables: list[GridRowEvidence]
    native_pages: list[GridBlock]
    matched_context_ids: list[str]
    date_statements: list[GridContext]
    observations: list[str]
    mandatory_qualification: str
    boundary: str = GRID_BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    external_review_status: Literal["reconciled_with_superseding_qualification"] = (
        "reconciled_with_superseding_qualification"
    )
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None
    source_edition_date: None = None


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file(package: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Evidence path leaves the fixed package")
    full = package / path
    if any(p.is_symlink() for p in (full, *full.parents)) or not full.is_file():
        raise ValueError(f"Missing or symlinked evidence: {relative}")
    return full


def _check_package(package: Path) -> bytes:
    for name, expected in PINS.items():
        if _digest(_safe_file(package, name)) != expected:
            raise ValueError(f"Frozen evidence hash mismatch: {name}")
    manifest = json.loads((package / "MANIFEST.json").read_bytes())
    for item in manifest["files"]:
        path = _safe_file(package, item["path"])
        if path.stat().st_size != item["size_bytes"] or _digest(path) != item["sha256"]:
            raise ValueError(f"Package evidence mismatch: {item['path']}")
    return (package / "SOURCE_QA.json").read_bytes()


def _load_verified(package: Path) -> dict:
    before = _check_package(package)
    try:
        subprocess.run(
            [sys.executable, "-I", "-B", str(package / "build_review.py"), "--verify"],
            cwd=package, check=True, capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ValueError("Existing source-package verification failed") from exc
    if _check_package(package) != before:
        raise ValueError("Evidence changed during verification")
    return json.loads(before)


def _check_greeley_package(package: Path) -> dict[str, str]:
    """Check the closed inventory and pin every executable dependency before import."""
    for name, expected in GREELEY_PINS.items():
        path = _safe_file(package, name)
        if path.stat().st_size > 2_000_000 or _digest(path) != expected:
            raise ValueError(f"Frozen Greeley evidence hash/size mismatch: {name}")
    manifest = json.loads((package / "PACKAGE.json").read_bytes())
    refs = [item["file"] for item in manifest["payloads"]]
    inventory = {item["path"]: item for item in refs}
    if len(inventory) != len(refs):
        raise ValueError("Duplicate Greeley inventory path")
    extra = {"PACKAGE.json", "PACKAGE.schema.json", "VALIDATION.json", "VALIDATION.schema.json"}
    expected = set(inventory) | extra
    actual = set()
    for path in package.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinked Greeley package entry")
        if path.is_file():
            actual.add(path.relative_to(package).as_posix())
    if actual != expected:
        raise ValueError("Missing or uninventoried Greeley package entry")
    hashes = {}
    for name in sorted(expected):
        path = _safe_file(package, name)
        size = path.stat().st_size
        if size > 20_000_000:
            raise ValueError("Oversized Greeley evidence")
        sha = _digest(path)
        if name in inventory:
            ref = inventory[name]
            if size != ref["size_bytes"] or sha != ref["sha256"]:
                raise ValueError(f"Greeley package evidence mismatch: {name}")
        hashes[name] = sha
    return hashes


def _load_greeley_verified(package: Path) -> tuple[dict, dict, bytes]:
    """Run only the pinned offline wrapper, with its verified local imports available."""
    before = _check_greeley_package(package)
    review = (package / GREELEY_REVIEW).read_bytes()
    packet = (package / "packet/manifest.json").read_bytes()
    candidate_path = (
        package / "packet/02-candidate-text" / GREELEY_SOURCE_ID / "candidate.txt"
    )
    candidate = candidate_path.read_bytes()
    launcher = (
        "import runpy,sys; from pathlib import Path; "
        "p=Path(sys.argv[1]); sys.path.insert(0,str(p)); "
        "scope=runpy.run_path(str(p/'validate_package.py')); "
        "sys.stdout.write(scope['verify'](p).model_dump_json())"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", launcher, str(package)],
            cwd=package, check=True, capture_output=True, text=True, timeout=30,
        )
        receipt = json.loads(result.stdout)
        if (receipt["status"] != "passed"
                or receipt["package"]["sha256"] != GREELEY_PINS["PACKAGE.json"]
                or receipt["audit_scope_checks"]["building_native_spans"] != 29
                or receipt["external_report_intake"] is not False
                or receipt["legal_currentness"] != "not_verified"):
            raise ValueError("Greeley verification receipt mismatch")
    except (subprocess.SubprocessError, OSError, ValueError, KeyError) as exc:
        raise ValueError("Existing Greeley source-package verification failed") from exc
    if _check_greeley_package(package) != before:
        raise ValueError("Greeley evidence changed during verification")
    return json.loads(review), json.loads(packet), candidate


def _weld_ref(package: Path, ref: dict[str, Any]) -> Path:
    """Resolve a bounded, hash-bound ordinary artifact without following links."""
    path = _safe_file(package, ref["path"])
    size = path.stat().st_size
    if size > 20_000_000 or size != ref["size_bytes"] or _digest(path) != ref["sha256"]:
        raise ValueError(f"Weld evidence mismatch: {ref['path']}")
    return path


def _check_weld_package(root: Path) -> dict[str, str]:
    """Verify the closed review inventory and only the frozen intake dependencies used."""
    package, intake = root / WELD_PACKAGE, root / WELD_INTAKE
    hashes = {}
    for base, pins in [(package, WELD_PINS), (intake, WELD_INTAKE_PINS)]:
        for name, expected in pins.items():
            path = _safe_file(base, name)
            if path.stat().st_size > 2_000_000 or _digest(path) != expected:
                raise ValueError(f"Frozen Weld evidence hash/size mismatch: {name}")
            hashes[str(path)] = expected
    manifest = json.loads((package / "evidence-manifest.json").read_bytes())
    refs = manifest["files"]
    inventory = {r["path"]: r for r in refs}
    if len(inventory) != len(refs):
        raise ValueError("Duplicate Weld inventory path")
    expected = set(inventory) | {"evidence-manifest.json", "evidence-manifest.schema.json"}
    expected_dirs = {str(p) for name in expected for p in Path(name).parents if str(p) != "."}
    actual, actual_dirs = set(), set()
    for path in package.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinked Weld package entry")
        name = path.relative_to(package).as_posix()
        if path.is_dir():
            actual_dirs.add(name)
        else:
            actual.add(name)
    if actual != expected or actual_dirs != expected_dirs:
        raise ValueError("Missing or uninventoried Weld package entry")
    for ref in refs:
        path = _weld_ref(package, ref)
        hashes[str(path)] = ref["sha256"]
    receipt = json.loads((intake / "intake-receipt.json").read_bytes())
    for key in ["record_stream", "provenance_stream", "record_schema", "source_schema"]:
        ref = receipt[key]
        hashes[str(_weld_ref(intake, ref))] = ref["sha256"]
    sources = [s for s in receipt["sources"] if s["source_id"] == WELD_SOURCE_ID]
    if len(sources) != 1:
        raise ValueError("Weld intake source identity mismatch")
    for key in ["access_receipt", "public_headers"]:
        ref = sources[0][key]
        hashes[str(_weld_ref(intake, ref))] = ref["sha256"]
    return hashes


def _load_weld_verified(root: Path) -> tuple[dict, dict]:
    """Run only the pinned EHS verifier; historical absolute paths are never opened."""
    before = _check_weld_package(root)
    package, intake = root / WELD_PACKAGE, root / WELD_INTAKE
    review = (package / WELD_REVIEW).read_bytes()
    receipt = json.loads((intake / "intake-receipt.json").read_bytes())
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(package / "frozen/ehs/build_review.py"), "--verify"],
            cwd=package / "frozen/ehs", check=True, capture_output=True, text=True, timeout=30,
        )
        prefix = "WARNING:root:"
        if (result.stdout.strip() or not result.stderr.startswith(prefix)
                or json.loads(result.stderr[len(prefix):]) != WELD_VERIFICATION):
            raise ValueError("Weld verification receipt mismatch")
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        raise ValueError("Existing Weld source-package verification failed") from exc
    if _check_weld_package(root) != before:
        raise ValueError("Weld evidence changed during verification")
    rows = {}
    for stream, schema, field in [("record_stream", "record_schema", "record_id"),
                                   ("provenance_stream", "source_schema", "source_id")]:
        validator = jsonschema.Draft202012Validator(json.loads(
            (intake / receipt[schema]["path"]).read_bytes()))
        selected = []
        with (intake / receipt[stream]["path"]).open("rb") as handle:
            for line in handle:
                row = json.loads(line)
                try:
                    validator.validate(row)
                except jsonschema.ValidationError as exc:
                    raise ValueError("Weld frozen intake schema mismatch") from exc
                if row[field] == WELD_SOURCE_ID:
                    selected.append(row)
        if len(selected) != 1:
            raise ValueError("Weld final intake record identity mismatch")
        rows[stream] = selected[0]
    data = json.loads(review)
    source = rows["provenance_stream"]
    record = rows["record_stream"]
    event = [e for e in json.loads((package / "frozen/ehs/ACCESS_RESULT.json").read_bytes())[
        "events"] if e["event_id"] == "ATLAS-WELD-04"][0]
    if (source not in receipt["sources"] or data["source_id"] != WELD_SOURCE_ID
            or source["authority_id"] != "CO-COUNTY-WELD"
            or source["canonical_original"]["sha256"] != WELD_PINS[WELD_PDF]
            or record["sha256"] != WELD_PINS[WELD_PDF]
            or record["layer_id"] != "08_County_Authorities"
            or (record["status"], source["pipeline_status"]) != (
                "archived_pending_pipeline", "archived_pending_pipeline")
            or record["received_at"] != source["repository_received_at"]
            or record["official_source_url"] != source["exact_requested_url"]
            or source["exact_requested_url"] != source["exact_final_url"]
            or event["retained_original"]["sha256"] != record["sha256"]
            or event["exact_target_url"] != source["exact_requested_url"]
            or event["finished_at"] != source["http_completed_at"]):
        raise ValueError("Weld source/custody relationship mismatch")
    if _check_weld_package(root) != before:
        raise ValueError("Weld evidence changed while reading custody records")
    return data, source


def _lookup_weld(root: Path, query: str | None) -> WeldLookupResult:
    """Preserve complete row associations and separately searchable page context."""
    data, provenance = _load_weld_verified(root)
    package = root / WELD_PACKAGE
    base = package / "frozen/ehs"
    spans = {s["id"]: (p, s) for p in data["pages"] for s in p["spans"]}

    def bind(identity: str) -> WeldBlock:
        """Bind one unchanged reviewed line to its physical native page."""
        page, span = spans[identity]
        native = _safe_file(base, page["native"]["path"])
        raw = span["text"].encode("utf-8")
        if native.read_bytes()[span["start"]:span["end"]] != raw:
            raise ValueError("Weld native slice mismatch")
        return WeldBlock(
            **span, physical_page=page["physical_page"], native_path=str(native),
            sha256=hashlib.sha256(raw).hexdigest(),
        )

    rows, used = [], set()
    for row in data["rows"]:
        group = bind(row["group_span"])
        labels = [bind(i) for i in row["label_spans"]]
        fee = bind(row["fee_span"]) if row["fee_span"] is not None else None
        notes = [bind(i) for i in row["note_spans"]]
        blocks = [group, *labels, *notes, *([fee] if fee else [])]
        used.update(b.id for b in blocks)
        if _matches(query, "".join(b.text for b in blocks)):
            rows.append(WeldRow(
                row_id=row["id"], physical_page=row["physical_page"], group=group,
                labels=labels, fee=fee, fee_cell_status=row["fee_cell_status"], notes=notes,
                page_image_path=str(base / data["pages"][row["physical_page"] - 1][
                    "image"]["path"]),
            ))
    context = [WeldPageContext(
        physical_page=p["physical_page"], header_visible=p["header_visible"],
        page_image_path=str(base / p["image"]["path"]),
        spans=[bind(s["id"]) for s in p["spans"] if s["id"] not in used],
    ) for p in data["pages"]]
    matched_context = [b.id for p in context for b in p.spans
                       if query is not None and b.text.strip() and _matches(query, b.text)]
    source = WeldSourceBinding.model_validate_json(json.dumps({
        "source_role": provenance["source_role"],
        "source_url": provenance["exact_requested_url"],
        "final_url": provenance["exact_final_url"],
        "http_started_at": provenance["http_started_at"],
        "source_retrieved_at": provenance["http_completed_at"],
        "reviewed_at": data["reviewed_at"], "received_at": provenance["repository_received_at"],
        "acquisition_description": provenance["acquisition_description"],
        "pdf_sha256": WELD_PINS[WELD_PDF], "review_sha256": WELD_PINS[WELD_REVIEW],
        "manifest_sha256": WELD_PINS["evidence-manifest.json"],
        "verifier_sha256": WELD_PINS["frozen/ehs/build_review.py"],
        "intake_receipt_sha256": WELD_INTAKE_PINS["intake-receipt.json"],
        "pdf_path": str(package / WELD_PDF), "review_path": str(package / WELD_REVIEW),
        "provenance_path": str(root / WELD_INTAKE / "intake-receipt.json"),
        "access_receipt_path": str(root / WELD_INTAKE / provenance["access_receipt"]["path"]),
        "access_receipt_sha256": provenance["access_receipt"]["sha256"],
        "review_mode": data["review_mode"], "source_year_assertion": data["source_year_assertion"],
    }))
    return WeldLookupResult(
        status="matched" if rows else ("matched_context_only" if matched_context
                                       else "no_matching_row"),
        query=query, evidence_verified=True, source=source, rows=rows, page_context=context,
        matched_context_ids=matched_context, observations=[o["statement"] for o in data[
            "observations"]],
    )


def _check_grid_package(root: Path) -> dict[str, str]:
    """Preflight every accepted review asset and frozen custody file before execution."""
    package = root / GRID_PACKAGE
    hashes = {}
    for name, expected in GRID_PINS.items():
        path = _safe_file(package, name)
        if path.stat().st_size > 1_000_000 or _digest(path) != expected:
            raise ValueError(f"Frozen grid evidence hash/size mismatch: {name}")
    manifest = json.loads((package / "FINAL_MANIFEST.json").read_bytes())
    refs = manifest["files"]
    expected = {ref["path"] for ref in refs}
    if len(expected) != len(refs):
        raise ValueError("Duplicate grid inventory path")
    expected.add("FINAL_MANIFEST.json")
    expected_dirs = {str(p) for name in expected for p in Path(name).parents if str(p) != "."}
    files, directories = set(), set()
    for path in package.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinked grid package entry")
        (directories if path.is_dir() else files).add(path.relative_to(package).as_posix())
    if files != expected or directories != expected_dirs:
        raise ValueError("Missing or uninventoried grid package entry")
    for ref in refs:
        path = _safe_file(package, ref["path"])
        if (path.stat().st_size > 10_000_000 or path.stat().st_size != ref["size_bytes"]
                or _digest(path) != ref["sha256"]):
            raise ValueError(f"Grid package evidence mismatch: {ref['path']}")
        hashes[str(path)] = ref["sha256"]
    hashes[str(package / "FINAL_MANIFEST.json")] = GRID_PINS["FINAL_MANIFEST.json"]
    # The complete original packet contains the locally frozen intake/referral evidence.
    hashes.update({str(root / GREELEY_PACKAGE / k): v
                   for k, v in _check_greeley_package(root / GREELEY_PACKAGE).items()})
    return hashes


def _load_grid_verified(root: Path, source_id: str) -> tuple[dict, dict, bytes, dict, dict]:
    """Replay the accepted superseding review and bind the selected immutable source."""
    before = _check_grid_package(root)
    package = root / GRID_PACKAGE
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(package / "verify_integration.py")],
            cwd=package, check=True, capture_output=True, text=True, timeout=45,
        )
        receipt = json.loads(result.stdout)
        old = receipt["historical_validator"]
        if (receipt["status"] != "integrity_passed_superseding_visual_correction_required"
                or receipt["title_bindings_replayed"] != 2
                or receipt["additional_receipt_records"] != 4
                or receipt["adversarial_title_mutations_rejected"] != 7
                or receipt["external_chronology_authenticated"] is not False
                or old["decisions"] != 33 or old["source_checks"][0]["fee_rows"] != 30
                or old["source_checks"][1]["table_rows"] != [7, 1]
                or receipt["legal_currentness"] != "not_verified"):
            raise ValueError("Grid verification receipt mismatch")
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, IndexError) as exc:
        raise ValueError("Existing grid source-package verification failed") from exc
    number, review_file, pages, _ = GRID_SOURCES[source_id]
    base = package / "historical-packet/baseline" / f"EB-PDF-{number}"
    data = json.loads((base / review_file).read_bytes())
    candidate = (base / "inputs/candidate.txt").read_bytes()
    record = json.loads((package / "historical-packet/RECONCILIATION.json").read_bytes())
    correction = json.loads((package / "SUPERSEDING_DISPOSITION.json").read_bytes())
    packet = json.loads((root / GREELEY_PACKAGE / "packet/manifest.json").read_bytes())
    selected = [d for d in packet["documents"] if d["source_id"] == source_id]
    if len(selected) != 1 or data["source_id"] != source_id:
        raise ValueError("Grid source identity mismatch")
    doc = selected[0]
    if (doc["assignment_id"] != f"EB-PDF-{number}" or doc["expected_pages"] != pages
            or doc["authority_id"] != "CO-MUNICIPAL-GREELEY"
            or doc["original"]["sha256"] != _digest(base / "inputs/original.pdf")
            or doc["candidate"]["sha256"] != hashlib.sha256(candidate).hexdigest()
            or correction["corrected_observation"] != "running_title_visible_on_pages_1_2_3"
            or correction["affected_pages"] != [2, 3]
            or "ATLAS-EB016-014" not in correction["withdrawn_claim_ids"]
            or correction["source_and_candidate_changed"] is not False):
        raise ValueError("Grid source/correction relationship mismatch")
    if _check_grid_package(root) != before:
        raise ValueError("Grid evidence changed during verification")
    return data, doc, candidate, record, correction


def _lookup_grid(root: Path, source_id: str, query: str | None) -> GridLookupResult:
    """Map only the reviewed grids, retaining complete source context on every result."""
    data, doc, candidate, record, correction = _load_grid_verified(root, source_id)
    number, review_file, _, expected_rows = GRID_SOURCES[source_id]
    package = root / GRID_PACKAGE
    base = package / "historical-packet/baseline" / f"EB-PDF-{number}"
    pages = {p["physical_page"]: p for p in data["pages"]}
    candidate_path = str(base / "inputs/candidate.txt")

    def bind(span: dict) -> GridBlock:
        """Bind a selected source span to its immutable full native page and candidate."""
        page = pages[span["physical_page"]]
        offset = page["candidate_start_byte"]
        start, end = span["start_byte"], span["end_byte_exclusive"]
        block = GridBlock(
            physical_page=span["physical_page"], text=span["text"], native_start=start,
            native_end=end, candidate_native_offset=offset, candidate_start=offset + start,
            candidate_end=offset + end, candidate_path=candidate_path, sha256=span["sha256"],
        )
        if (end > len(page["native_text"].encode())
                or page["native_text"].encode()[start:end] != block.text.encode()
                or candidate[block.candidate_start:block.candidate_end] != block.text.encode()):
            raise ValueError("Grid native/candidate span mismatch")
        return block

    def image_path(page: int) -> str:
        """Resolve the reviewed physical page without substituting a crop."""
        return str(base / pages[page]["image"]["path"])

    def cell(raw: dict) -> GridCell:
        """Preserve merged cells, explicit blanks and contributing source strings."""
        return GridCell(**{k: raw[k] for k in ["column_start", "column_span", "text", "status"]},
                        native_spans=[bind(s) for s in raw["native_spans"]])

    def row(raw: dict, page: int) -> GridRowEvidence:
        """Map one source grid row without recomputing or inferring any value."""
        return GridRowEvidence(row_id=raw["id"], physical_page=page, role=raw["role"],
                               cells=[cell(c) for c in raw["cells"]])

    rows, table_context, context = [], [], []
    if source_id == IMPACT_SOURCE_ID:
        all_rows = {r["id"]: row(r, t["physical_page"]) for t in data["tables"] for r in t["rows"]}
        for table in data["tables"]:
            for raw in table["rows"]:
                if raw["role"] != "fee":
                    table_context.append(all_rows[raw["id"]])
                    continue
                rows.append(GridMatchedRow(
                    **all_rows[raw["id"]].model_dump(), table_id=table["id"],
                    column_roles=table["column_role_notes"],
                    column_headers=[all_rows[i] for i in table["header_reference_row_ids"]],
                    group_headers=[all_rows[raw["fee_group_header_row_id"]]], table_headings=[],
                    association_notes=table["visual_association_notes"],
                    page_image_path=image_path(table["physical_page"]),
                ))
        for page in data["pages"]:
            for chunk in page["chunks"]:
                if chunk["role"] not in {"table", "layout_whitespace"}:
                    context.append(GridContext(
                        id=chunk["id"], role=chunk["role"], statement="Unchanged source span",
                        qualification=chunk["visibility"], native_spans=[bind(chunk["span"])],
                        page_image_paths=[image_path(page["physical_page"])],
                    ))
        date_ids = {"memo-identity", "eaf-data-period", "notification-effective-date",
                    "utility-separate-future-adoption"}
        for observation in data["observations"]:
            context.append(GridContext(
                id=observation["id"], role="date_claim" if observation["id"] in date_ids
                else observation["kind"], statement=observation["finding"],
                qualification=observation["limitation"],
                native_spans=[bind(s) for s in observation["native_spans"]],
                page_image_paths=[image_path(observation["physical_page"])],
            ))
        observations = data["limits"] + data["provenance_limits"]
    else:
        for table in data["tables"]:
            header = GridRowEvidence(
                row_id=table["table_id"] + "-headers", physical_page=2, role="column_header",
                cells=[GridCell(column_start=h["column"], column_span=1, text=h["display_text"],
                                status="visually_blank" if h["visibly_blank"]
                                else "native_bound_visible_text",
                                native_spans=[] if h["native_span"] is None
                                else [bind(h["native_span"])]) for h in table["headers"]],
            )
            table_context.append(header)
            for raw in table["rows"]:
                rows.append(GridMatchedRow(
                    row_id=raw["row_id"], physical_page=2, role="fee", table_id=table["table_id"],
                    cells=[GridCell(column_start=c["column"], column_span=1,
                                    text=c["display_text"], status="native_bound_visible_text",
                                    native_spans=[bind(c["native_span"])]) for c in raw["cells"]],
                    column_roles=[h["display_text"] for h in table["headers"]],
                    column_headers=[header], group_headers=[],
                    table_headings=[bind(table["heading_span"])],
                    association_notes=[
                        "Separate " + table["source_position"] + " source table; no inferred unit.",
                        "Dollar signs and amount strings are retained as printed, "
                        "without arithmetic.",
                    ], page_image_path=image_path(2),
                ))
        for observation in data["observations"]:
            context.append(GridContext(
                id=observation["id"], role="date_claim" if observation["id"] in {
                    "EB017-O01", "EB017-O03"} else "source_observation",
                statement=observation["finding"], qualification=observation["qualification"],
                native_spans=[bind(s) for s in observation["native_spans"]],
                page_image_paths=[image_path(i) for i in observation["physical_pages"]],
            ))
        for note in data["image_only"]:
            context.append(GridContext(
                id=note["id"], role="image_only", statement="\n".join(note["text_lines"]),
                qualification=note["qualification"], native_spans=[],
                page_image_paths=[image_path(note["physical_page"])],
            ))
        observations = data["limits"]
    if len(rows) != expected_rows or len({r.row_id for r in rows}) != expected_rows:
        raise ValueError("Grid row count/identity mismatch")
    native_pages = [bind({"physical_page": n, "start_byte": 0,
                         "end_byte_exclusive": len(p["native_text"].encode()),
                         "text": p["native_text"], "sha256": p["native_sha256"]})
                    for n, p in pages.items()]
    rows = [r for r in rows if _matches(query, "\n".join(
        [r.row_id, *[c.text for c in r.cells],
         *[c.text or "" for h in [*r.group_headers, *r.column_headers] for c in h.cells],
         *[h.text for h in r.table_headings]]))]
    matches = [c.id for c in context if query is not None and _matches(query, "\n".join(
        [c.statement, *[b.text for b in c.native_spans]]))]
    provenance = doc["provenance"]
    source = GridSourceBinding.model_validate_json(json.dumps({
        "source_id": source_id, "source_role": "development_impact_fee_memorandum"
        if source_id == IMPACT_SOURCE_ID else "proposed_water_sewer_pif_notice",
        "official_source_url": provenance["canonical_official_source_url"],
        "official_referral_url": provenance["official_referral_url"],
        "reported_requested_url": provenance["reported_requested_url"],
        "reported_final_url": provenance["reported_final_url"],
        "reported_acquisition_at": provenance["reported_acquisition_at"],
        "original_acquisition_time": provenance["original_acquisition_time"],
        "received_at": provenance["actual_repository_received_at"],
        "reviewed_at": (data["reviewed_at"] if source_id == IMPACT_SOURCE_ID
                        else data["prepared_at"]),
        "external_reconciliation_at": record["prepared_at"],
        "superseding_disposition_at": correction["recorded_at"],
        "acquisition_qualification": (
            "Received review package. Supplied HTTP acquisition time is not independently "
            "verified; "
            "repository receipt time is distinct. The reported Sitecore URL is linked by retained "
            "official referral HTML, while the canonical official source URL remains null."
        ),
        "pdf_path": str(base / "inputs/original.pdf"), "pdf_sha256": doc["original"]["sha256"],
        "candidate_path": candidate_path, "candidate_sha256": doc["candidate"]["sha256"],
        "review_path": str(base / review_file), "review_sha256": _digest(base / review_file),
        "provenance_path": str(root / GREELEY_PACKAGE / "packet/manifest.json"),
        "packet_manifest_sha256": GREELEY_PINS["packet/manifest.json"],
        "reconciliation_path": str(package / "historical-packet/RECONCILIATION.json"),
        "reconciliation_sha256": _digest(package / "historical-packet/RECONCILIATION.json"),
        "superseding_disposition_path": str(package / "SUPERSEDING_DISPOSITION.json"),
        "superseding_disposition_sha256": GRID_PINS["SUPERSEDING_DISPOSITION.json"],
        "package_manifest_sha256": GRID_PINS["FINAL_MANIFEST.json"],
        "verifier_sha256": GRID_PINS["verify_integration.py"],
    }))
    return GridLookupResult(
        status="matched" if rows else ("matched_context_only" if matches else "no_matching_row"),
        source_id=source_id, query=query, evidence_verified=True, source=source, rows=rows,
        context=context, context_tables=table_context, native_pages=native_pages,
        matched_context_ids=matches, date_statements=[c for c in context if c.role == "date_claim"],
        observations=[*observations,
                      "The superseding disposition retains visible running titles on all three "
                      "EB016 pages. The withdrawn not-visible conclusions must not be used.",
                      "External chronology is not authenticated; EB017 PASS1_NOTES bytes remain "
                      "missing. Review dispositions are source QA, not legal-currentness "
                      "findings."],
        mandatory_qualification=(IMPACT_CONDITION if source_id == IMPACT_SOURCE_ID
                                 else PIF_CONDITION),
    )


def _search_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _matches(query: str | None, text: str) -> bool:
    if query is None:
        return True
    needle = _search_text(query)
    left = r"(?<![\w.,])" if needle[0].isdigit() else r"(?<!\w)"
    right = r"(?![\w.,])" if needle[-1].isdigit() else r"(?!\w)"
    return re.search(left + re.escape(needle) + right, _search_text(text)) is not None


def _lookup_greeley(package: Path, query: str | None) -> GreeleyLookupResult:
    data, packet, candidate = _load_greeley_verified(package)
    documents = [d for d in packet["documents"] if d["source_id"] == GREELEY_SOURCE_ID]
    if len(documents) != 1 or data["source_id"] != GREELEY_SOURCE_ID:
        raise ValueError("Greeley source identity mismatch")
    doc = documents[0]
    if (doc["assignment_id"] != "EB-PDF-015" or doc["expected_pages"] != 1
            or doc["authority_id"] != "CO-MUNICIPAL-GREELEY"):
        raise ValueError("Greeley source scope/authority mismatch")
    spans = {s["label"]: s for s in data["spans"]}
    candidate_path = package / "packet" / doc["candidate"]["path"]

    def bind(label: str) -> GreeleyBlock:
        span = spans[label]
        block = GreeleyBlock(
            id=label, text=span["text"], candidate_path=str(candidate_path),
            native_start=span["start"], native_end=span["end"],
            candidate_start=data["candidate_native_start"] + span["start"],
            candidate_end=data["candidate_native_start"] + span["end"],
            sha256=span["sha256"],
        )
        if candidate[block.candidate_start:block.candidate_end] != block.text.encode():
            raise ValueError("Greeley candidate/source block mismatch")
        return block

    specs = [(f"valuation_{i}", "valuation_fee", [
        "document_title", "table_1a_title", "permit_table_heading", "table_columns",
    ]) for i in range(1, 9)]
    specs += [(f"other_{i}", "other_fee", ["document_title", "other_heading"])
              for i in range(1, 10)]
    specs += [
        ("sales_tax_body", "sales_tax", ["document_title", "sales_tax_heading"]),
        ("temporary_electrical_body", "temporary_electrical", [
            "document_title", "temporary_electrical_heading",
        ]),
    ]
    entries = []
    for label, kind, headings in specs:
        statement = bind(label)
        heading_blocks = [bind(h) for h in headings]
        footnote = data["footnote_links"].get(label)
        footnotes = [bind(footnote)] if footnote else []
        searchable = "\n".join(b.text for b in [statement, *heading_blocks, *footnotes])
        if _matches(query, searchable):
            entries.append(GreeleyEntry(
                entry_id=label, kind=kind, statement=statement, headings=heading_blocks,
                footnotes=footnotes,
                page_image_path=str(package / "packet" / doc["pages"][0]["image"]["path"]),
            ))
    p = doc["provenance"]
    source = GreeleySourceBinding.model_validate_json(json.dumps({
        "authority_id": doc["authority_id"], "authority_basis": doc["authority_basis"],
        "official_source_url": p["canonical_official_source_url"],
        "official_referral_url": p["official_referral_url"],
        "reported_requested_url": p["reported_requested_url"],
        "reported_final_url": p["reported_final_url"],
        "reported_acquisition_at": p["reported_acquisition_at"],
        "original_acquisition_time": p["original_acquisition_time"],
        "received_at": p["actual_repository_received_at"], "reviewed_at": data["prepared_at"],
        "acquisition_method": p["acquisition_method"], "intake_status": p["intake_status"],
        "upstream_http_acquisition_independently_verified":
            p["upstream_http_acquisition_independently_verified_in_this_preparation"],
        "acquisition_qualification": (
            "Received review package; original HTTP acquisition time is unverified. "
            "The reported Sitecore URL appears in saved official referral HTML, but "
            "the direct host is outside the existing intake allowlist. The canonical "
            "official source URL remains null. Receipt time is not acquisition time."
        ),
        "pdf_sha256": GREELEY_PINS[GREELEY_PDF],
        "review_sha256": GREELEY_PINS[GREELEY_REVIEW],
        "manifest_sha256": GREELEY_PINS["PACKAGE.json"],
        "verifier_sha256": GREELEY_PINS["validate_package.py"],
        "candidate_sha256": data["candidate_sha256"],
        "packet_manifest_sha256": GREELEY_PINS["packet/manifest.json"],
        "pdf_path": str(package / GREELEY_PDF), "review_path": str(package / GREELEY_REVIEW),
        "provenance_path": str(package / "packet/manifest.json"),
    }))
    entry_ids = {s[0] for s in specs}
    return GreeleyLookupResult(
        status="matched" if entries else "no_matching_row", query=query, evidence_verified=True,
        source=source, entries=entries,
        context=[bind(label) for label in data["source_order"] if label not in entry_ids],
        date_statements=[GreeleyDateStatement(role=role, evidence=bind(label)) for role, label in [
            ("schedule_title_year", "document_title"),
            ("effective_heading_year", "table_1a_title"),
            ("unlabeled_footer", "unlabeled_footer_date"),
        ]], observations=data["observations"],
    )


def lookup(
    root: Path,
    source_id: str,
    query: str | None = None,
    *,
    list_rows: bool = False,
    mode: Literal["source", "current-law"] = "source",
) -> LookupResult | GreeleyLookupResult | WeldLookupResult | GridLookupResult:
    """Verify a fixed source and return unchanged evidence for a literal keyword phrase."""
    if source_id not in {SOURCE_ID, GREELEY_SOURCE_ID, WELD_SOURCE_ID, *GRID_SOURCES}:
        raise ValueError("Unsupported source; only the five fixed reviewed sources are available")
    if mode not in {"source", "current-law"}:
        raise ValueError("Unsupported lookup mode")
    if list_rows == (query is not None):
        raise ValueError("Choose exactly one of query or list_rows")
    if query is not None and not query.strip():
        raise ValueError("A nonempty keyword phrase is required")
    if mode == "current-law" or (query is not None and CURRENT_REQUEST.search(query)):
        if source_id in GRID_SOURCES:
            return GridLookupResult(
                status="refused_current_law", source_id=source_id, query=query,
                evidence_verified=False, rows=[], context=[], context_tables=[], native_pages=[],
                matched_context_ids=[], date_statements=[], observations=[
                    "Current-law and question answering are unsupported; use source keywords only.",
                ], mandatory_qualification=IMPACT_CONDITION if source_id == IMPACT_SOURCE_ID
                else PIF_CONDITION,
            )
        if source_id == WELD_SOURCE_ID:
            return WeldLookupResult(
                status="refused_current_law", query=query, evidence_verified=False,
                rows=[], page_context=[], matched_context_ids=[], observations=[
                    "Current-law and question answering are unsupported; use keywords "
                    "only to inspect what this preserved source says.",
                ],
            )
        if source_id == GREELEY_SOURCE_ID:
            return GreeleyLookupResult(
                status="refused_current_law", query=query, evidence_verified=False,
                entries=[], context=[], date_statements=[], observations=[
                    "Current-law and question answering are unsupported; use keywords "
                    "only to inspect what this preserved source says.",
                ],
            )
        return LookupResult(
            status="refused_current_law", query=query, evidence_verified=False, rows=[],
            observations=["Current-law and question answering are unsupported; use keywords "
                          "only to inspect what this preserved source says."], page_context={},
        )
    root = root.expanduser().absolute()
    if ".." in root.parts:
        raise ValueError("Use a root without parent traversal")
    if source_id in GRID_SOURCES:
        return _lookup_grid(root, source_id, query)
    if source_id == WELD_SOURCE_ID:
        return _lookup_weld(root, query)
    if source_id == GREELEY_SOURCE_ID:
        return _lookup_greeley(root / GREELEY_PACKAGE, query)
    package = root / PACKAGE
    data = _load_verified(package)
    if data["source_id"] != REVIEW_SOURCE_ID:
        raise ValueError("The review's historical source alias does not match")
    spans = {s["id"]: (p, s) for p in data["pages"] for s in p["spans"]}

    def bind(span_id: str) -> SpanBinding:
        page, span = spans[span_id]
        return SpanBinding(
            id=span_id, physical_page=page["physical_page"],
            native_path=str(package / page["native"]["path"]), start=span["start"],
            end=span["end"], sha256=hashlib.sha256(span["text"].encode()).hexdigest(),
        )

    rows = []
    for row in data["rows"]:
        group = spans[row["group_span"]][1]["text"]
        label = spans[row["label_span"]][1]["text"]
        fee = spans[row["fee_span"]][1]["text"]
        if not _matches(query, group + label + fee):
            continue
        rows.append(MatchedRow(
            row_id=row["id"], physical_page=row["physical_page"], group=group,
            label=label, fee=fee, group_basis=row["group_basis"],
            group_binding=bind(row["group_span"]), label_binding=bind(row["label_span"]),
            fee_binding=bind(row["fee_span"]),
            page_image_path=str(package / f"page-{row['physical_page']}.png"),
        ))
    event = json.loads((package / "access-event.json").read_bytes())
    source = SourceBinding.model_validate_json(json.dumps({
        "source_url": data["official_url"], "pdf_sha256": PINS["original.pdf"],
        "review_sha256": PINS["SOURCE_QA.json"], "manifest_sha256": PINS["MANIFEST.json"],
        "verifier_sha256": PINS["build_review.py"], "pdf_path": str(package / "original.pdf"),
        "review_path": str(package / "SOURCE_QA.json"), "reviewed_at": data["reviewed_at"],
        "source_retrieved_at": event["completed_at"],
    }))
    return LookupResult(
        status="matched" if rows else "no_matching_row", query=query, evidence_verified=True,
        source=source, rows=rows, observations=[o["statement"] for o in data["observations"]],
        page_context={str(p["physical_page"]): [s["text"] for s in p["spans"]
                      if s["role"] in {"header", "footer"}] for p in data["pages"]},
    )


def _markdown(text: str) -> str:
    escaped = html.escape(text.rstrip("\n"), quote=False)
    return re.sub(r"([\\`*_[\]{}|])", r"\\\1", escaped).replace("\n", "<br>")


def _link(label: str, path: str) -> str:
    safe = path.replace("<", "%3C").replace(">", "%3E").replace("\n", "%0A")
    return f"[{label}](<{safe}>)"


def _render_greeley(result: GreeleyLookupResult) -> str:
    lines = [
        "Source-only research lookup — legal_currentness: not_verified; answer_safe: false.",
        "", result.boundary, "",
        "Adoption date: unknown. Verified effective date: unknown. "
        "Verified source edition date: unknown. External review: pending, not intaken.", "",
    ]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("Verified Greeley source binding is required")
    lines += [
        f"Source: `{result.source_id}`. Authority context: `{result.authority_id}`.", "",
        f"[Official referral page]({source.official_referral_url}) · "
        f"[Reported download URL]({source.reported_requested_url})", "",
        "Canonical official source URL: unknown (null). Original acquisition time: unknown.",
        f"- Repository receipt: {source.received_at.isoformat()}.",
        f"- Supplied acquisition claim: {source.reported_acquisition_at.isoformat()} "
        "(not independently verified).",
        f"- Source review recorded: {source.reviewed_at.isoformat()}.",
        f"- PDF SHA-256: `{source.pdf_sha256}`.",
        f"- Review SHA-256: `{source.review_sha256}`.",
        "", source.acquisition_qualification, "",
        _link("Preserved PDF", source.pdf_path) + " · "
        + _link("Checked source review", source.review_path) + " · "
        + _link("Frozen custody", source.provenance_path), "",
        "Source date statements (quoted claims, not verified legal dates):", "",
    ]
    lines += [f"- `{d.role}`: {_markdown(d.evidence.text)}" for d in result.date_statements]
    if not result.entries:
        lines += ["", "No matching entry in this preserved source snapshot.", ""]
    for entry in result.entries:
        block = entry.statement
        lines += ["", f"**{entry.entry_id} — physical page 1**", ""]
        lines += ["- Source heading: " + _markdown(h.text) for h in entry.headings]
        lines += ["- The preserved source states: " + _markdown(block.text)]
        lines += ["- Linked source footnote: " + _markdown(f.text) for f in entry.footnotes]
        lines += [
            f"- Exact UTF-8 candidate bytes [{block.candidate_start}, {block.candidate_end}); "
            f"native page bytes [{block.native_start}, {block.native_end}); "
            "the candidate page marker occupies the first 56 bytes.", "",
            _link("Unchanged candidate", block.candidate_path) + " · "
            + _link("Full page image", entry.page_image_path), "",
        ]
    lines += ["Complete source context spans:", ""]
    lines += [f"- `{b.id}`: {_markdown(b.text)}" for b in result.context]
    lines += ["", "Source-review qualifications:", ""]
    lines += ["- " + _markdown(note) for note in result.observations]
    return "\n".join(lines) + "\n"


def _render_weld(result: WeldLookupResult) -> str:
    """Render exact fee text, explicit blanks and scoped notes without calculation."""
    lines = [
        "Source-only research lookup — legal_currentness: not_verified; answer_safe: false.",
        "", result.boundary, "", "Adoption date: unknown. Effective date: unknown. "
        "Verified source edition date: unknown. Source year assertion: 2026.", "",
    ]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("Verified Weld source binding is required")
    lines += [
        f"Source: `{result.source_id}`. Authority: `{result.authority_id}`.", "",
        f"[Official source]({source.source_url})", "",
        f"- HTTP retrieval: {source.source_retrieved_at.isoformat()}.",
        f"- Source review: {source.reviewed_at.isoformat()}.",
        f"- Repository receipt: {source.received_at.isoformat()}.",
        f"- PDF SHA-256: `{source.pdf_sha256}`.",
        f"- Review SHA-256: `{source.review_sha256}`.", "",
        source.acquisition_description, "",
        _link("Preserved PDF", source.pdf_path) + " · "
        + _link("Checked review", source.review_path) + " · "
        + _link("Frozen intake custody", source.provenance_path), "",
    ]
    if not result.rows:
        lines += ["No matching fee row in this preserved source snapshot.", ""]
    if result.matched_context_ids:
        lines += ["Matching page context: " + ", ".join(result.matched_context_ids) + ".", ""]
    for row in result.rows:
        lines += [f"**{row.row_id} — physical page {row.physical_page}**", "",
                  "- Group: " + _markdown(row.group.text),
                  "- Label: " + _markdown("".join(b.text for b in row.labels))]
        lines += ["- Printed fee: " + _markdown(row.fee.text) if row.fee else
                  "- Fee cell: visibly blank (no amount supplied; not zero)."]
        lines += ["- Linked row note: " + _markdown(b.text) for b in row.notes]
        blocks = [row.group, *row.labels, *row.notes, *([row.fee] if row.fee else [])]
        lines += ["- Native spans: " + ", ".join(
            f"`{b.id}` [{b.start}, {b.end})" for b in blocks) + ".", "",
            _link("Full page image", row.page_image_path), ""]
    lines += ["Complete page context (no inferred row applicability):", ""]
    for page in result.page_context:
        lines += [f"Physical page {page.physical_page}; native header visible in source render: "
                  f"{'yes' if page.header_visible else 'no'}.", ""]
        lines += [f"- `{b.id}` ({b.role}): {_markdown(b.text)}" for b in page.spans
                  if b.role != "blank"]
        lines.append("")
    lines += ["Source-review qualifications:", ""]
    lines += ["- " + _markdown(note) for note in result.observations]
    return "\n".join(lines) + "\n"


def _render_grid(result: GridLookupResult) -> str:
    """Render mapped columns and every condition without presenting current fees."""
    lines = ["Source-only research lookup — legal_currentness: not_verified; answer_safe: false.",
             "", result.boundary, "", result.mandatory_qualification, "",
             "Verified adoption, effective and source edition dates: unknown.", ""]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("Verified grid source binding is required")
    lines += [f"Source: `{result.source_id}`. Issuer: City of Greeley.", "",
              _link("Official referral", source.official_referral_url) + " · "
              + _link("Reported source URL", source.reported_requested_url), "",
              f"- Supplied acquisition claim: {source.reported_acquisition_at.isoformat()}.",
              f"- Repository receipt: {source.received_at.isoformat()}.",
              f"- Source review: {source.reviewed_at.isoformat()}.",
              f"- External reconciliation: {source.external_reconciliation_at.isoformat()}.",
              f"- Superseding disposition: {source.superseding_disposition_at.isoformat()}.",
              f"- PDF SHA256: `{source.pdf_sha256}`.", "", source.acquisition_qualification, "",
              _link("Preserved PDF", source.pdf_path) + " · "
              + _link("Checked source grid", source.review_path) + " · "
              + _link("Superseding disposition", source.superseding_disposition_path), ""]
    if not result.rows:
        lines += ["No matching fee row in this preserved source snapshot.", ""]
    if result.matched_context_ids:
        lines += ["Matching context: " + ", ".join(result.matched_context_ids) + ".", ""]

    def render_row(row: GridRowEvidence) -> list[str]:
        """Display exact cell association, preserving explicit source blanks."""
        output = [f"- `{row.row_id}` (physical page {row.physical_page}, {row.role}):"]
        for cell in row.cells:
            value = _markdown(cell.text) if cell.status != "visually_blank" else (
                "visibly blank; no amount or unit inferred"
            )
            output += [f"  - Column {cell.column_start}, span {cell.column_span}: {value}"]
            output += [f"    - Native [{b.native_start}, {b.native_end}); candidate "
                       f"[{b.candidate_start}, {b.candidate_end}); SHA256 `{b.sha256}`."
                       for b in cell.native_spans]
        return output

    for row in result.rows:
        lines += [f"**{row.row_id} — {row.table_id}, physical page {row.physical_page}**", ""]
        lines += ["- Table title: " + _markdown(b.text) for b in row.table_headings]
        columns = " | ".join(v if v is not None else "[blank]" for v in row.column_roles)
        lines += ["- Column meanings: " + _markdown(columns)]
        for header in [*row.column_headers, *row.group_headers]:
            lines += render_row(header)
        lines += render_row(row)
        lines += ["- Source association: " + _markdown(n) for n in row.association_notes]
        lines += ["", _link("Full page image", row.page_image_path), ""]
    lines += ["Complete source context (including date claims and conditions):", ""]
    for item in result.context:
        lines += [f"- `{item.id}` ({item.role}): {_markdown(item.statement)}",
                  "  - Qualification: " + _markdown(item.qualification)]
        lines += ["  - Source text: " + _markdown(b.text) for b in item.native_spans]
    lines += ["", "Source context grids (headings, explicit blanks and EAF rows):", ""]
    for row in result.context_tables:
        lines += render_row(row)
    lines += ["", "Unchanged native page evidence (not a replacement for table associations):", ""]
    lines += [f"- Physical page {b.physical_page}: " + _link("candidate", b.candidate_path)
              + f"; candidate bytes [{b.candidate_start}, {b.candidate_end}); SHA256 `{b.sha256}`."
              for b in result.native_pages]
    lines += ["", "Source-review limits:", ""]
    lines += ["- " + _markdown(o) for o in result.observations]
    return "\n".join(lines) + "\n"


def render_markdown(
    result: LookupResult | GreeleyLookupResult | WeldLookupResult | GridLookupResult,
) -> str:
    """Render quoted source rows and their evidence links without calculating fees."""
    if isinstance(result, GridLookupResult):
        return _render_grid(result)
    if isinstance(result, WeldLookupResult):
        return _render_weld(result)
    if isinstance(result, GreeleyLookupResult):
        return _render_greeley(result)
    lines = ["Source-only research lookup — legal_currentness: not_verified; answer_safe: false.",
             "", result.boundary, "",
             "Adoption date: unknown. Effective date: unknown. Source edition date: unknown.", ""]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("Verified source binding is required")
    lines += [f"Source: `{result.source_id}` (review alias `{source.review_source_id}`).", "",
              f"[Official source]({source.source_url})", "",
              f"- PDF SHA-256: `{source.pdf_sha256}`",
              f"- Review SHA-256: `{source.review_sha256}`",
              f"- Retrieved: {source.source_retrieved_at.isoformat()}; "
              f"reviewed: {source.reviewed_at.isoformat()}.",
              "",
              _link("Source PDF", source.pdf_path) + " · " +
              _link("Checked review", source.review_path), ""]
    if not result.rows:
        lines += ["No matching row in this preserved source snapshot.", ""]
    for row in result.rows:
        lines += [f"**{row.row_id} — physical page {row.physical_page}**", "",
                  f"- Group: {_markdown(row.group)}", f"- Label: {_markdown(row.label)}",
                  f"- The preserved source states: {_markdown(row.fee)}",
                  f"- Group basis: `{row.group_basis}`; spans "
                  f"`{row.group_binding.id}` / `{row.label_binding.id}` / `{row.fee_binding.id}`.",
                  "", _link("Page image", row.page_image_path), ""]
    lines += ["Source-review qualifications:", ""]
    lines += ["- " + _markdown(note) for note in result.observations]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write a qualified research result to stdout; fail closed on invalid evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-id", required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--query")
    action.add_argument("--list-rows", action="store_true")
    parser.add_argument("--mode", choices=["source", "current-law"], default="source")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)
    try:
        result = lookup(args.root, args.source_id, args.query,
                        list_rows=args.list_rows, mode=args.mode)
        output = (result.model_dump_json(indent=2) + "\n" if args.format == "json"
                  else render_markdown(result))
    except (ValueError, OSError, KeyError) as exc:
        logging.error("Research source lookup failed: %s", exc)
        return 1
    sys.stdout.write(output)
    return 2 if result.status == "refused_current_law" else 0


if __name__ == "__main__":
    raise SystemExit(main())
