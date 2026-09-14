"""Look up nine fixed source reviews without current-law or applicability claims."""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import logging
import os
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

SPRINGS_SOURCE_ID = "colorado-springs-construction-fees-atlas-directed"
SPRINGS_PACKAGE = Path("research/local_review/colorado-springs-construction-fees-qa-2026-09-12")
SPRINGS_ACCEPTANCE = Path(
    "docs/audits/FOUR_HOUR_RUN_2026-09-12/COLORADO_SPRINGS_CONSTRUCTION_QA/ACCEPTANCE.json"
)
SPRINGS_ACCEPTANCE_SHA = "7c415b46fb5e2c0a317bb9071c9f58c21405564b92360791cb3aa617c1a2c659"
SPRINGS_PINS = {
    "FINAL_MANIFEST.json": "9b691fafa9c734adc5b7be1f475ae2946826111b5ac569b45c22e023fdf320b5",
    "FINAL_MANIFEST.schema.json":
        "1dea29ae66c938045546e52a0a33c192d0bc1c411cb901c612823e4bbf595200",
    "SOURCE_QA.json": "cb27452624c2b1be332a4eb241bee03520046466f95f696dee3a59cd7e94dc70",
    "SOURCE_QA.schema.json":
        "44193e1bd8f0b3186cacdc7ec48e4a004aa6b18208badc290d6dfbe0b14948d9",
    "source/original.pdf":
        "e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a",
    "validate_review.py": "9eae696ef79da6c5f4b760873be46c1307aed8ada95e31cef622a408327be1b0",
}
SPRINGS_GLOBAL = ["GENERAL-PLAN-REVIEW", "IMPLEMENTATION", "OTHER-SCHEDULE", "P4-MISC-01"]
SPRINGS_INTAKE = Path("research/local_review/colorado-springs-intake-2026-09-12")
SPRINGS_INTAKE_PINS = {
    "INVENTORY.json": "4bc0e43c6bd61243353b653880c87835461e2d272a3d1739ef1dd0a3010dc50e",
    "INVENTORY.schema.json":
        "a750cd8f6c05a2531c47950dc1129e6fca93b2a55c0cf143dffaa48f4a1834ff",
    "validate_package.py": "fc80d0255bcd1b1f18fa7b265b6bab0e6c4a61709e45baab4e198763f642c7c1",
    "ACCEPTANCE.json": "503b98fb62561d3cee436f938c0555554a458547ef546f94576cf0abcafe5f12",
    "prepared-transaction/execution/RECEIPT.json":
        "59efef8ab0b90059004f85054acca3b82bcf613c34eaaba20b37d5a521b8d5ff",
    "prepared-transaction/execution/INTENT.json":
        "fa9ab7c7a44b2836a8f2fd149472bdf52b872828a21794ee8d903faceebe70ce",
}
SPRINGS_BOUNDARY = (
    "Source-only lookup in one accepted seven-page municipal Construction Services schedule "
    "with 128 rows. Complete global qualifications and linked source definitions accompany "
    "each result; links do not decide applicability. No arithmetic, current-law or adoption "
    "claim is made. No match does not establish free, exempt or unregulated activity. The "
    "separate Code Services schedule is outside this lookup."
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


class SpringsAsset(StrictModel):
    """Bind one exact file from the accepted Colorado Springs source package."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class SpringsPart(StrictModel):
    """Keep complete native lines, geometry and physical-page custody together."""

    page: int = Field(ge=1, le=7)
    line_ids: list[str] = Field(min_length=1)
    exact_native_text: str
    native_ranges: list[list[int]]
    pdf_bboxes: list[list[float]]
    pixel_bboxes: list[list[int]]
    native_file: SpringsAsset
    page_image: SpringsAsset
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    offset_basis: Literal["unchanged_physical_page_native_utf8_half_open"] = (
        "unchanged_physical_page_native_utf8_half_open"
    )

    @model_validator(mode="after")
    def validate_lines(self) -> SpringsPart:
        """Reject detached line ranges, native text hashes or impossible pixel bounds."""
        count = len(self.line_ids)
        if not count == len(self.native_ranges) == len(self.pdf_bboxes) == len(self.pixel_bboxes):
            raise ValueError("Colorado Springs native line/geometry count differs")
        if len(set(self.line_ids)) != count or any(
            not line.startswith(f"P{self.page}-L") for line in self.line_ids
        ):
            raise ValueError("Colorado Springs native line identity differs")
        for pair in self.native_ranges:
            if len(pair) != 2 or not 0 <= pair[0] < pair[1] <= self.native_file.size_bytes:
                raise ValueError("Colorado Springs native range is outside the page")
        length = sum(end - start for start, end in self.native_ranges)
        if length != len(self.exact_native_text.encode()):
            raise ValueError("Colorado Springs native byte length differs")
        if hashlib.sha256(self.exact_native_text.encode()).hexdigest() != self.text_sha256:
            raise ValueError("Colorado Springs native text hash differs")
        for box in self.pdf_bboxes:
            if (len(box) != 4 or not 0 <= box[0] < box[2] <= 612
                    or not 0 <= box[1] < box[3] <= 792):
                raise ValueError("Colorado Springs PDF geometry differs")
        for box in self.pixel_bboxes:
            if (len(box) != 4 or not 0 <= box[0] < box[2] <= 1700
                    or not 0 <= box[1] < box[3] <= 2200):
                raise ValueError("Colorado Springs image geometry differs")
        return self


class SpringsCell(SpringsPart):
    """Retain a cell's reviewed label or fee role without inventing a currency or total."""

    role: Literal["label", "fee_as_printed"]


class SpringsBlock(StrictModel):
    """Retain a complete context block, including definitions crossing physical pages."""

    block_id: str
    kind: Literal["heading", "definition", "table_note", "general_note", "implementation",
                  "other_schedule_reference", "printed_date", "cover", "contents", "footer",
                  "native_whitespace"]
    parts: list[SpringsPart] = Field(min_length=1)
    notes: list[str]


class SpringsTable(StrictModel):
    """Preserve the table's reviewed heading, row order and cross-page scope."""

    table_id: str
    heading_block_id: str
    page_order: list[int]
    row_ids: list[str]
    column_roles: Literal[
        "Unlabeled left description and right fee columns; roles are visual associations, "
        "not invented printed column headings."
    ]


class SpringsRow(StrictModel):
    """Carry both full cells and all recorded global, table and definition relationships."""

    row_id: str
    table_id: str
    physical_page: int = Field(ge=2, le=5)
    label: SpringsCell
    fee_as_printed: SpringsCell
    global_context_ids: list[str]
    table_context_ids: list[str]
    definition_ids: list[str]
    context_rule: Literal[
        "Return the complete global context, linked table notes and definitions with this "
        "source row; conditions remain source wording, not an applicability decision."
    ]

    @model_validator(mode="after")
    def validate_row(self) -> SpringsRow:
        """Prevent label/fee swaps and loss of complete global context."""
        if self.label.role != "label" or self.fee_as_printed.role != "fee_as_printed":
            raise ValueError("Colorado Springs label/fee roles differ")
        if self.label.page != self.physical_page or self.fee_as_printed.page != self.physical_page:
            raise ValueError("Colorado Springs row page differs")
        if self.global_context_ids != SPRINGS_GLOBAL:
            raise ValueError("Colorado Springs global context omitted")
        return self


class SpringsSourceBinding(StrictModel):
    """Separate accepted source acquisition, completed intake and legal-date claims."""

    source_id: Literal["colorado-springs-construction-fees-atlas-directed"] = SPRINGS_SOURCE_ID
    historical_review_source_id: Literal["SD014-02"] = "SD014-02"
    authority_id: Literal["CO-MUNICIPAL-COLORADO_SPRINGS"] = "CO-MUNICIPAL-COLORADO_SPRINGS"
    issuer: Literal["Colorado Springs Fire Department, Division of the Fire Marshal"]
    collector_qualification: str
    source_role: Literal["fee_schedule_as_received"] = "fee_schedule_as_received"
    pdf: SpringsAsset
    review: SpringsAsset
    manifest: SpringsAsset
    acceptance: SpringsAsset
    official_url: str
    request_started_at: AwareDatetime
    response_finished_at: AwareDatetime
    http_status: Literal[200] = 200
    redirect_count: Literal[0] = 0
    acquisition_method: Literal["Atlas direct ordinary HTTPS GET retained complete response"]
    custody_receipts: list[SpringsAsset]
    canonical_intake_verified: Literal[True] = True
    intake_received_at: AwareDatetime
    intake_id: str
    canonical_original: SpringsAsset
    intake_evidence: list[SpringsAsset] = Field(min_length=4)
    intake_qualification: Literal[
        "Completed canonical intake receipt and present original are verified. "
        "Historical proposal text remains unchanged; intake does not establish current law."
    ] = (
        "Completed canonical intake receipt and present original are verified. "
        "Historical proposal text remains unchanged; intake does not establish current law."
    )
    printed_effective_date: Literal["07/01/2026"] = "07/01/2026"
    effective_date_verification: Literal["printed_claim_only"] = "printed_claim_only"
    adoption_verification: Literal["not_verified"] = "not_verified"
    reviewed_at: AwareDatetime
    review_method: str
    native_byte_count: Literal[14423] = 14423
    native_line_count: Literal[410] = 410
    native_byte_basis: str

    @model_validator(mode="after")
    def validate_intake(self) -> SpringsSourceBinding:
        """Keep source identity and the later intake event bound to the same original."""
        if (self.canonical_original.sha256 != self.pdf.sha256
                or self.canonical_original.size_bytes != self.pdf.size_bytes):
            raise ValueError("Colorado Springs intake/source original differs")
        if not self.request_started_at <= self.response_finished_at < self.intake_received_at:
            raise ValueError("Colorado Springs acquisition/intake chronology differs")
        return self


class SpringsLookupResult(StrictModel):
    """Expose a fixed native source with mandatory context and no reliance promotion."""

    status: Literal["matched", "matched_context_only", "no_matching_row", "refused_current_law"]
    source_id: Literal["colorado-springs-construction-fees-atlas-directed"] = SPRINGS_SOURCE_ID
    query: str | None
    evidence_verified: bool
    source: SpringsSourceBinding | None = None
    rows: list[SpringsRow] = Field(max_length=128)
    technology_fee: SpringsRow | None = None
    tables: list[SpringsTable] = Field(max_length=9)
    context: list[SpringsBlock]
    matched_context_ids: list[str]
    global_context_ids: list[str]
    observations: list[str]
    boundary: str = SPRINGS_BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None

    @model_validator(mode="after")
    def validate_context(self) -> SpringsLookupResult:
        """Reject a success without full required definitions, notes and table bindings."""
        if self.status == "refused_current_law":
            if self.evidence_verified or self.source or self.rows or self.context or self.tables:
                raise ValueError("Refused request must not expose verified source results")
            return self
        if not self.evidence_verified or self.source is None or self.technology_fee is None:
            raise ValueError("Colorado Springs verified source/context required")
        if self.technology_fee.row_id != "P4-MISC-01" or self.global_context_ids != SPRINGS_GLOBAL:
            raise ValueError("Colorado Springs technology/global qualification omitted")
        blocks = {block.block_id: block for block in self.context}
        if len(blocks) != len(self.context) or not set(SPRINGS_GLOBAL[:-1]) <= blocks.keys():
            raise ValueError("Colorado Springs shared context missing/duplicated")
        if len([b for b in self.context if b.kind == "definition"]) != 13:
            raise ValueError("Colorado Springs complete definitions required")
        if len([b for b in self.context if b.kind == "table_note"]) != 3:
            raise ValueError("Colorado Springs complete table notes required")
        if ("DEF-REINSPECTION" not in blocks
                or [p.page for p in blocks["DEF-REINSPECTION"].parts] != [6, 7]):
            raise ValueError("Colorado Springs re-inspection continuation omitted")
        tables = {table.table_id: table for table in self.tables}
        if len(tables) != 9 or len(tables) != len(self.tables):
            raise ValueError("Colorado Springs complete table context required")
        if len({row.row_id for row in self.rows}) != len(self.rows):
            raise ValueError("Colorado Springs duplicate matched row")
        for row in [*self.rows, self.technology_fee]:
            table = tables[row.table_id]
            if (row.row_id not in table.row_ids or row.physical_page not in table.page_order
                    or table.heading_block_id not in blocks):
                raise ValueError("Colorado Springs table/row association differs")
            if not set(row.table_context_ids + row.definition_ids) <= blocks.keys():
                raise ValueError("Colorado Springs linked context omitted")
        if bool(self.rows) != (self.status == "matched"):
            raise ValueError("Colorado Springs result status differs")
        if self.status == "matched_context_only" and not self.matched_context_ids:
            raise ValueError("Colorado Springs context match is empty")
        return self


def _check_springs_package(root: Path) -> dict[str, str]:
    """Bind the accepted closed review package before any retained executable runs."""
    package = root / SPRINGS_PACKAGE
    acceptance = _safe_file(root, SPRINGS_ACCEPTANCE.as_posix())
    if _digest(acceptance) != SPRINGS_ACCEPTANCE_SHA:
        raise ValueError("Colorado Springs acceptance pin differs")
    hashes = {str(acceptance): SPRINGS_ACCEPTANCE_SHA}
    for name, digest in SPRINGS_PINS.items():
        path = _safe_file(package, name)
        if path.stat().st_size > 2_000_000 or _digest(path) != digest:
            raise ValueError("Colorado Springs fixed evidence pin differs: " + name)
        hashes[str(path)] = digest
    manifest = json.loads((package / "FINAL_MANIFEST.json").read_bytes())
    refs = manifest["files"]
    names = {r["path"] for r in refs}
    if len(names) != len(refs):
        raise ValueError("Colorado Springs duplicate inventory member")
    expected = names | {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}
    expected_dirs = {str(p) for name in expected for p in Path(name).parents if str(p) != "."}
    files, directories = set(), set()
    for path in package.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Colorado Springs nonordinary package member")
        (directories if path.is_dir() else files).add(path.relative_to(package).as_posix())
    if files != expected or directories != expected_dirs:
        raise ValueError("Colorado Springs closed package membership differs")
    for ref in refs:
        name = ref["path"]
        if Path(name).as_posix() != name or "\\" in name:
            raise ValueError("Colorado Springs noncanonical member path")
        path = _safe_file(package, name)
        if (path.stat().st_size > 10_000_000 or path.stat().st_size != ref["size_bytes"]
                or _digest(path) != ref["sha256"]):
            raise ValueError("Colorado Springs package evidence differs: " + name)
        hashes[str(path)] = ref["sha256"]
    return hashes


def _load_springs_verified(root: Path) -> tuple[dict, dict[str, bytes]]:
    """Replay the unchanged offline source QA verifier with isolation and bounded time."""
    before = _capture_existing(root, "springs")
    package = root / SPRINGS_PACKAGE
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(package / "validate_review.py"),
             "--root", str(package)], cwd=package, check=True, capture_output=True, text=True,
            timeout=90, env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"},
        )
        receipt = json.loads(result.stdout)
        expected = {
            "status": "validated_source_qa_no_currentness_promotion",
            "source_sha256": SPRINGS_PINS["source/original.pdf"], "physical_pages": 7,
            "fee_rows": 128, "tables": 9, "definition_records": 13, "table_notes": 3,
            "native_bytes": 14423, "native_lines": 410, "crops": 12,
            "files_verified": 82, "legal_currentness": "not_verified",
        }
        if receipt != expected:
            raise ValueError("Colorado Springs source verifier receipt differs")
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        raise ValueError("Colorado Springs source-package verification failed") from exc
    if _capture_existing(root, "springs") != before:
        raise ValueError("Colorado Springs package changed during verification")
    return json.loads(before[str(package / "SOURCE_QA.json")]), before


def _check_springs_intake(root: Path) -> dict[str, str]:
    """Pin the closed completed-intake package before its read-only verifier executes."""
    package = root / SPRINGS_INTAKE
    hashes = {}
    for name, expected in SPRINGS_INTAKE_PINS.items():
        path = _safe_file(package, name)
        if path.stat().st_size > 2_000_000 or _digest(path) != expected:
            raise ValueError("Colorado Springs intake pin differs: " + name)
        hashes[str(path)] = expected
    refs = json.loads((package / "INVENTORY.json").read_bytes())["files"]
    names = {r["path"] for r in refs}
    if len(names) != len(refs):
        raise ValueError("Colorado Springs duplicate intake inventory path")
    expected_files = names | {"INVENTORY.json", "INVENTORY.schema.json"}
    expected_dirs = {str(p) for name in expected_files for p in Path(name).parents
                     if str(p) != "."}
    files, directories = set(), set()
    for path in package.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError("Colorado Springs nonordinary intake member")
        (directories if path.is_dir() else files).add(path.relative_to(package).as_posix())
    # The accepted completed transaction retains this empty working directory.
    # Git and portable copies may omit it; no contents or other directories are allowed.
    historical_empty = {"prepared-transaction/execution/.staging"}
    if files != expected_files or directories - historical_empty != expected_dirs:
        raise ValueError("Colorado Springs closed intake inventory differs")
    for ref in refs:
        path = _safe_file(package, ref["path"])
        if path.stat().st_size != ref["size_bytes"] or _digest(path) != ref["sha256"]:
            raise ValueError("Colorado Springs intake evidence differs: " + ref["path"])
        hashes[str(path)] = ref["sha256"]
    return hashes


def _load_springs_intake(root: Path, source: dict) -> dict:
    """Bind actual intake time to the accepted receipt and present canonical source bytes."""
    before = _capture_existing(root, "springs_intake")
    package = root / SPRINGS_INTAKE
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(package / "validate_package.py")],
            cwd=package, check=True, capture_output=True, text=True, timeout=45,
            env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"},
        )
        if json.loads(result.stdout) != {
            "status": "verified_completed_custody", "payloads": 125,
            "raw_records": 61, "ledger_records": 62, "legal_currentness": "not_verified",
        }:
            raise ValueError("Colorado Springs intake verifier receipt differs")
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        raise ValueError("Colorado Springs completed-intake verification failed") from exc
    if _capture_existing(root, "springs_intake") != before:
        raise ValueError("Colorado Springs intake changed during verification")
    receipt = json.loads(before[str(package / "prepared-transaction/execution/RECEIPT.json")])
    selected = [r for r in receipt["intent"]["records"] if r["record_id"] == SPRINGS_SOURCE_ID]
    if len(selected) != 1:
        raise ValueError("Colorado Springs intake source identity differs")
    record = selected[0]
    if (record["sha256"] != source["source"]["sha256"]
            or record["official_source_url"] != source["provenance"]["official_url"]
            or record["layer_id"] != "10_Municipal_Authorities"
            or record["status"] != "archived_pending_pipeline"
            or record["received_at"] != receipt["actual_repository_received_at"]
            or not record["archive_path"].startswith(
                f"_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/{SPRINGS_SOURCE_ID}/")):
        raise ValueError("Colorado Springs completed source/intake binding differs")
    path = _safe_file(root, record["archive_path"])
    original = _capture_source_file(root, path, record["sha256"], 20_000_000)
    if len(original) != record["size_bytes"]:
        raise ValueError("Colorado Springs present canonical original differs")
    return {
        "intake_received_at": record["received_at"], "intake_id": record["intake_id"],
        "canonical_original": {"path": str(path), "sha256": record["sha256"],
                               "size_bytes": record["size_bytes"]},
        "intake_evidence": [
            {"path": str(package / name), "sha256": digest,
             "size_bytes": len(before[str(package / name)])}
            for name, digest in SPRINGS_INTAKE_PINS.items()
        ],
    }


def _lookup_springs(root: Path, query: str | None) -> SpringsLookupResult:
    """Map verified native cells and complete source context without deriving a charge."""
    data, captured = _load_springs_verified(root)
    intake = _load_springs_intake(root, data)
    package = root / SPRINGS_PACKAGE

    def asset(ref: dict) -> dict:
        """Resolve a preverified asset without replacing its source digest."""
        return _captured_reference(captured, package, ref)

    pages = {p["physical_page"]: p for p in data["pages"]}
    native = {n: captured[str(package / p["native"]["path"])] for n, p in pages.items()}

    def part(raw: dict, page: int | None = None) -> dict:
        """Recheck exact native ranges and bind the full cell or context part."""
        page = raw.get("page", page)
        text = b"".join(native[page][a:b] for a, b in raw["native_ranges"])
        if text != raw["exact_native_text"].encode():
            raise ValueError("Colorado Springs output native bytes differ")
        return {**raw, "page": page, "native_file": asset(pages[page]["native"]),
                "page_image": asset(pages[page]["image"]),
                "text_sha256": hashlib.sha256(text).hexdigest()}

    blocks = [SpringsBlock.model_validate_json(json.dumps({
        **raw, "parts": [part(p) for p in raw["parts"]],
    })) for raw in data["blocks"]]
    by_block = {b.block_id: b for b in blocks}
    tables = [SpringsTable.model_validate_json(json.dumps(t)) for t in data["tables"]]
    by_table = {t.table_id: t for t in tables}
    rows = [SpringsRow.model_validate_json(json.dumps({
        **raw, "label": part(raw["label"], raw["physical_page"]),
        "fee_as_printed": part(raw["fee_as_printed"], raw["physical_page"]),
    })) for raw in data["fee_rows"]]
    matched = []
    for row in rows:
        heading = by_block[by_table[row.table_id].heading_block_id]
        haystacks = [row.label.exact_native_text, row.fee_as_printed.exact_native_text,
                     *[p.exact_native_text for p in heading.parts]]
        if query is None or any(_matches(query, text) for text in haystacks):
            matched.append(row)
    context_ids = [] if query is None else [
        b.block_id for b in blocks if b.kind not in {"footer", "native_whitespace", "contents"}
        and any(_matches(query, p.exact_native_text) for p in b.parts)
    ]
    provenance = data["provenance"]
    source = SpringsSourceBinding.model_validate_json(json.dumps({
        "issuer": data["issuer"], "collector_qualification": data["collector_qualification"],
        "pdf": asset(data["source"]),
        "review": asset({"path": "SOURCE_QA.json", "sha256": SPRINGS_PINS["SOURCE_QA.json"],
                         "size_bytes": len(captured[str(package / "SOURCE_QA.json")])}),
        "manifest": asset({"path": "FINAL_MANIFEST.json",
                           "sha256": SPRINGS_PINS["FINAL_MANIFEST.json"],
                           "size_bytes": len(captured[str(package / "FINAL_MANIFEST.json")])}),
        "acceptance": {"path": str(root / SPRINGS_ACCEPTANCE), "sha256": SPRINGS_ACCEPTANCE_SHA,
                       "size_bytes": len(captured[str(root / SPRINGS_ACCEPTANCE)])},
        "official_url": provenance["official_url"],
        "request_started_at": provenance["request_started_at"],
        "response_finished_at": provenance["response_finished_at"],
        "acquisition_method": provenance["method"],
        "custody_receipts": [asset(ref) for ref in provenance["receipts"]],
        "reviewed_at": data["reviewed_at"], "review_method": data["review_method"],
        "native_byte_basis": data["native_byte_basis"], **intake,
    }))
    return SpringsLookupResult(
        status=("matched" if matched else "matched_context_only" if context_ids
                else "no_matching_row"),
        query=query, evidence_verified=True, source=source, rows=matched,
        technology_fee=next(r for r in rows if r.row_id == "P4-MISC-01"), tables=tables,
        context=blocks, matched_context_ids=context_ids, global_context_ids=SPRINGS_GLOBAL,
        observations=[
            *data["comparison_findings"], *data["source_anomalies"], *data["limits"],
        ],
    )


def _render_springs(result: SpringsLookupResult) -> str:
    """Render complete row context without changing any preexisting source renderer."""
    lines = ["Source-only research lookup — legal_currentness: not_verified; answer_safe: false.",
             "", result.boundary, "",
             "Adoption/effective dates: unknown. Printed date is only a source claim.", ""]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    lines += [f"Source: `{source.source_id}`; historical review alias: `SD014-02`.", "",
              _link("Official source", source.official_url), "",
              _link("Source PDF", source.pdf.path) + " · " +
              _link("Source review", source.review.path),
              "", f"PDF SHA256: `{source.pdf.sha256}`; review SHA256: `{source.review.sha256}`.",
              "", f"Ordinary HTTPS response completed: {source.response_finished_at.isoformat()}.",
              "", f"Canonical intake received: {source.intake_received_at.isoformat()}.", "",
              _link("Canonical original", source.canonical_original.path), "",
              _markdown(source.intake_qualification), "",
              "Printed claim: Effective 07/01/2026. "
              "Legal adoption/effectiveness remain unverified.",
              "", _markdown(source.collector_qualification), ""]

    def render_block(block: SpringsBlock) -> list[str]:
        """Keep all parts of a context paragraph together across page boundaries."""
        out = [f"**{_markdown(block.block_id)}**", ""]
        for part in block.parts:
            out += [_markdown(part.exact_native_text), "",
                    _link(f"Physical page {part.page}", part.page_image.path), ""]
        out += [_markdown(note) for note in block.notes]
        return out + [""]

    def render_row(row: SpringsRow) -> list[str]:
        """Display source cell wording, full units and references without doing arithmetic."""
        return [f"**{row.row_id} — physical page {row.physical_page}**", "",
                f"- Label: {_markdown(row.label.exact_native_text)}",
                f"- Source fee text: {_markdown(row.fee_as_printed.exact_native_text)}", "",
                _link("Page image", row.label.page_image.path), ""]

    context = {b.block_id: b for b in result.context}
    lines += ["**Mandatory shared context for every result**", ""]
    for name in SPRINGS_GLOBAL[:-1]:
        lines += render_block(context[name])
    lines += render_row(result.technology_fee)
    lines += ["**Complete source definitions and table notes**", ""]
    for block in result.context:
        if block.kind in {"definition", "table_note"}:
            lines += render_block(block)
    if not result.rows:
        lines += ["No matching fee row in this snapshot.", ""]
    tables = {t.table_id: t for t in result.tables}
    for row in result.rows:
        table = tables[row.table_id]
        lines += render_block(context[table.heading_block_id]) + render_row(row)
        lines += ["Complete linked definitions: " + ", ".join(row.definition_ids) + ".", "",
                  "Complete linked table notes: " + ", ".join(row.table_context_ids) + ".", ""]
    if result.matched_context_ids:
        lines += ["Matched source context: " + ", ".join(result.matched_context_ids) + ".", ""]
    lines += ["Source-review qualifications:", ""]
    lines += ["- " + _markdown(s) for s in result.observations]
    return "\n".join(lines) + "\n"


EHS_SOURCE_ID = "el-paso-boh-ehs-fees-sd011"
EHS_PACKAGE = Path("research/local_review/el-paso-ehs-fees-source-qa-2026-09-13")
EHS_ACCEPTANCE = Path(
    "docs/audits/FOUR_HOUR_RUN_2026-09-12/EL_PASO_EHS_SOURCE_QA/ACCEPTANCE.json"
)
EHS_ACCEPTANCE_SHA = "6771f712028d6ee3c4f737d37b3470f13740fe12e8bd6e01587bfc07bd65bda4"
EHS_PINS = {
    "FINAL_MANIFEST.json": "da8cb23666be686d9182695201819121363f4700755b8e57aadc9accbde77832",
    "SOURCE_QA.json": "55a5e8b088c3b407c20691c71cb62a73491b99e39c0e6d9c0d0e69c2b3746ebf",
    "SOURCE_QA.schema.json": "f35d92def244a848eab1a60130cc9e3ed575a4e7f7c12f99a1c336e6128714db",
    "source/original.pdf": "1b0529fb7514bcc50c0dd36c903ca361f6ab431712b4aebc48bca8e3f5373622",
    "source/canonical-record.jsonl":
        "00dc523f686bbc40fe005c834e0c93b121eaccef6d82a971e3f068ff75db87fa",
    "validate_review.py": "0870bb43190b21819f378665c85369e3dfede891705d7ee52232e166884eca40",
}
EHS_GLOBAL = ["A", "B", "OTHER1", "OTHER2", "OTHER3"]
EHS_BOUNDARY = (
    "Source-only English El Paso County Board of Health schedule: 65 rows in seven groups. "
    "All source context, definitions, civil-penalty exceptions and notes accompany each result. "
    "No current-law, applicability, arithmetic or adoption claim is made. No match does not "
    "establish free, exempt or unregulated activity. Spanish translation equivalence was not "
    "reviewed. Source approval/effective dates and 2024/2025 fee cells remain printed claims."
)


class EhsAsset(StrictModel):
    """An exact local evidence asset for the checked English EHS source."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0)


class EhsSpan(StrictModel):
    """An unchanged native substring and exact physical-page evidence identity."""

    start: int = Field(ge=0)
    end: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    text: str
    native_file: EhsAsset
    image: EhsAsset
    physical_page: int = Field(ge=1, le=5)

    @model_validator(mode="after")
    def bound(self) -> EhsSpan:
        """Reject detached text, lengths and page-native offsets."""
        data = self.text.encode("utf-8")
        if (not self.start < self.end <= self.native_file.size_bytes or
                self.end - self.start != len(data) or
                hashlib.sha256(data).hexdigest() != self.sha256):
            raise ValueError("El Paso EHS native span differs")
        return self


class EhsContext(StrictModel):
    """One complete checked source context; scope links do not decide applicability."""

    context_id: str
    physical_page: int = Field(ge=1, le=5)
    kind: str
    text: str
    applies_to: list[str]
    native: EhsSpan


class EhsRow(StrictModel):
    """A complete service/fee pair, its actual group heading and explicit source notes."""

    row_id: str
    physical_page: int = Field(ge=2, le=4)
    group: str
    group_physical_page: int = Field(ge=2, le=4)
    service: str
    fee: str
    linked_context: list[str]
    label_native: EhsSpan
    fee_native: EhsSpan
    group_native: EhsSpan
    exact_grid_cells: list[str | None] = Field(min_length=2, max_length=2)
    pdf_cell_rectangles: list[list[float] | None] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def associations(self) -> EhsRow:
        """Retain mandatory context and adjacent label/fee identities on the source page."""
        if (self.label_native.physical_page != self.physical_page or
                self.fee_native.physical_page != self.physical_page or
                self.group_native.physical_page != self.group_physical_page or
                self.label_native.end > self.fee_native.start or
                not set(EHS_GLOBAL) <= set(self.linked_context)):
            raise ValueError("El Paso EHS row or global context differs")
        return self


class EhsSource(StrictModel):
    """Keep actual repository custody separate from unverified original HTTP and legal dates."""

    source_id: Literal["el-paso-boh-ehs-fees-sd011"] = EHS_SOURCE_ID
    authority_id: Literal["CO-COUNTY-EL_PASO"] = "CO-COUNTY-EL_PASO"
    issuer: Literal["El Paso County Board of Health"]
    administering_agency: Literal["El Paso County Public Health"]
    pdf: EhsAsset
    candidate: EhsAsset
    canonical_original: EhsAsset
    review: EhsAsset
    manifest: EhsAsset
    acceptance: EhsAsset
    copied_canonical_record: EhsAsset
    official_url: str
    intake_id: str
    intake_received_at: AwareDatetime
    acquisition_method: Literal["received_review_package"]
    original_http_acquired_at: None = None
    original_http_independently_verified: Literal[False] = False
    original_custody_note: str
    reviewed_at: AwareDatetime
    accepted_at: AwareDatetime
    printed_approval_claim: Literal["October 25, 2023"]
    printed_effective_claim: Literal["January 1, 2024"]
    legal_date_verification: Literal["printed_source_claims_only"] = "printed_source_claims_only"
    native_bytes: Literal[8060] = 8060
    source_role: Literal["English fee schedule and civil penalties as received"] = (
        "English fee schedule and civil penalties as received"
    )


class EhsLookupResult(StrictModel):
    """Qualified complete-context results for exactly one reviewed English source."""

    status: Literal["matched", "matched_context_only", "no_matching_row", "refused_current_law"]
    source_id: Literal["el-paso-boh-ehs-fees-sd011"] = EHS_SOURCE_ID
    query: str | None
    evidence_verified: bool
    source: EhsSource | None = None
    rows: list[EhsRow] = Field(max_length=65)
    context: list[EhsContext]
    matched_context_ids: list[str]
    observations: list[str]
    boundary: str = EHS_BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None
    translation_equivalence: Literal["not_reviewed"] = "not_reviewed"

    @model_validator(mode="after")
    def complete_context(self) -> EhsLookupResult:
        """No successful response may drop the full checked source context or invent a row."""
        if self.status == "refused_current_law":
            if self.source or self.evidence_verified or self.rows or self.context:
                raise ValueError("Refused El Paso EHS request exposes evidence")
            return self
        ids = {c.context_id for c in self.context}
        if (not self.source or not self.evidence_verified or len(ids) != 37 or
                len(self.context) != 37 or not set(EHS_GLOBAL) <= ids or
                any(set(r.linked_context) - ids for r in self.rows) or
                len({r.row_id for r in self.rows}) != len(self.rows)):
            raise ValueError("El Paso EHS complete verified context required")
        if bool(self.rows) != (self.status == "matched"):
            raise ValueError("El Paso EHS result status differs")
        if self.status == "matched_context_only" and not self.matched_context_ids:
            raise ValueError("Empty El Paso EHS context match")
        return self


def _check_ehs_package(root: Path) -> dict[str, str]:
    """Pin the closed accepted source package before any retained verifier can run."""
    package = root / EHS_PACKAGE
    acceptance_path = _safe_file(root, EHS_ACCEPTANCE.as_posix())
    if _digest(acceptance_path) != EHS_ACCEPTANCE_SHA:
        raise ValueError("El Paso EHS acceptance differs")
    hashes = {str(acceptance_path): EHS_ACCEPTANCE_SHA}
    for name, digest in EHS_PINS.items():
        path = _safe_file(package, name)
        if path.stat().st_size > 2_000_000 or _digest(path) != digest:
            raise ValueError("El Paso EHS fixed evidence differs: " + name)
        hashes[str(path)] = digest
    acceptance = json.loads(acceptance_path.read_bytes())
    if (acceptance["status"] !=
            "accepted_complete_english_source_fidelity_review_not_current_law" or
            acceptance["legal_currentness"] != "not_verified"):
        raise ValueError("El Paso EHS acceptance scope differs")
    refs = json.loads((package / "FINAL_MANIFEST.json").read_bytes())["files"]
    names = {r["path"] for r in refs}
    expected = names | {"FINAL_MANIFEST.json"}
    expected_dirs = {p.as_posix() for name in expected for p in Path(name).parents
                     if p.as_posix() != "."}
    actual_files, actual_dirs = set(), set()
    for path in package.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("El Paso EHS nonordinary package member")
        (actual_dirs if path.is_dir() else actual_files).add(path.relative_to(package).as_posix())
    if (len(refs) != 41 or len(names) != 41 or actual_files != expected or
            actual_dirs != expected_dirs):
        raise ValueError("El Paso EHS closed membership differs")
    accepted = acceptance["copied_originals"]
    if len(accepted) != 42 or {r["path"] for r in accepted} != expected:
        raise ValueError("El Paso EHS acceptance inventory differs")
    total = 0
    for ref in [*refs, *accepted]:
        path = _safe_file(package, ref["path"])
        size = path.stat().st_size
        if size > 2_000_000 or size != ref["size_bytes"] or _digest(path) != ref["sha256"]:
            raise ValueError("El Paso EHS package member differs: " + ref["path"])
        total += size
        hashes[str(path)] = ref["sha256"]
    if total > 12_000_000:
        raise ValueError("El Paso EHS evidence size bound exceeded")
    return hashes


def _load_ehs_verified(root: Path) -> tuple[dict, dict, dict, dict[str, bytes]]:
    """Replay pinned source/grid verification and bind the current canonical row and original."""
    before = _capture_existing(root, "ehs")
    package = root / EHS_PACKAGE
    try:
        process = subprocess.run([sys.executable, "-I", "-B", str(package / "validate_review.py")],
            cwd=package, check=True, capture_output=True, text=True, timeout=45,
            env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"})
        text = process.stdout
        notice = ("Consider using the pymupdf_layout package for a greatly improved "
                  "page layout analysis.\n")
        if text.startswith(notice):
            text = text[len(notice):]
        verification = json.loads(text)
        expected = {
            "status": "passed", "closed_files": 41, "physical_pages": 5, "service_rows": 65,
            "named_groups": 7, "table_grid_rows": 74, "grid_cells_including_merged_nulls": 148,
            "context_records": 37, "native_bytes": 8060, "native_text_reproduced": True,
            "candidate_offsets_replayed": True, "table_geometry_replayed": True,
            "all_nonwhitespace_native_bytes_bound": True,
            "source_first_freeze_precedes_native_extraction_as_recorded": True,
            "chronology_independently_authenticated": False, "rerendered": False,
            "public_requests": 0, "legal_currentness": "not_verified",
            "translation_equivalence": "not_reviewed",
        }
        if verification != expected:
            raise ValueError("El Paso EHS verifier receipt differs")
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        raise ValueError("El Paso EHS source verification failed") from error
    if _capture_existing(root, "ehs") != before:
        raise ValueError("El Paso EHS package changed during verification")
    copied = before[str(package / "source/canonical-record.jsonl")]
    record = json.loads(copied)
    schema = json.loads(before[str(package / "source/canonical-record.schema.json")])
    jsonschema.Draft202012Validator(schema).validate(record)
    manifest = _safe_file(root, "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl")
    if manifest.stat().st_size > 8_000_000:
        raise ValueError("Manual manifest size bound exceeded")
    digest = _digest(manifest)
    selected = []
    with manifest.open("rb") as handle:
        for line in handle:
            if json.loads(line).get("record_id") == EHS_SOURCE_ID:
                selected.append(line)
    if selected != [copied] or _digest(manifest) != digest:
        raise ValueError("El Paso EHS canonical record identity differs")
    if (record["record_id"] != EHS_SOURCE_ID or record["layer_id"] != "08_County_Authorities" or
            record["acquisition_method"] != "received_review_package" or
            record["sha256"] != EHS_PINS["source/original.pdf"] or
            not record["archive_path"].startswith(
                f"_RAW_ARCHIVE/manual_intake/08_County_Authorities/{EHS_SOURCE_ID}/")):
        raise ValueError("El Paso EHS canonical ownership differs")
    original = _safe_file(root, record["archive_path"])
    before[str(original)] = _capture_source_file(root, original, record["sha256"], 20_000_000)
    if len(before[str(original)]) != record["size_bytes"]:
        raise ValueError("El Paso EHS canonical original differs")
    return (json.loads(before[str(package / "SOURCE_QA.json")]), record,
            json.loads(before[str(root / EHS_ACCEPTANCE)]), before)


def _ehs_matches(query: str, text: str) -> bool:
    """Allow punctuation after a section citation without loosening fee-token boundaries."""
    needle = _search_text(query)
    if re.fullmatch(r"section \d+(?:-\d+)*", needle):
        return re.search(r"(?<!\w)" + re.escape(needle) + r"(?![\w-]|\.\d)",
                         _search_text(text)) is not None
    return _matches(query, text)


def _lookup_ehs(root: Path, query: str | None) -> EhsLookupResult:
    """Return full native cells, source headings and every checked contextual qualification."""
    data, record, acceptance, captured = _load_ehs_verified(root)
    package = root / EHS_PACKAGE
    pages = {p["physical_page"]: p for p in data["pages"]}
    native = {i: captured[str(package / p["native"]["path"])] for i, p in pages.items()}
    bindings = {b["identity"]: b for b in data["bindings"]}

    def asset(ref: dict) -> dict:
        """Resolve an already pinned local evidence reference."""
        return _captured_reference(captured, package, ref)

    def span(raw: dict, page: int) -> EhsSpan:
        """Bind exact native bytes used in the output, not just display normalization."""
        if native[page][raw["start"]:raw["end"]] != raw["text"].encode():
            raise ValueError("El Paso EHS output span differs")
        return EhsSpan(**raw, physical_page=page, native_file=EhsAsset(**asset(
            pages[page]["native"])), image=EhsAsset(**asset(pages[page]["image"])))

    contexts = [EhsContext(**c, native=span(bindings[c["context_id"]]["spans"][0],
                                           c["physical_page"])) for c in data["contexts"]]
    groups = {c.text: c for c in contexts if c.kind == "group_heading"}
    grid = {r["fee_row_id"]: r for t in data["tables"] for r in t["rows"] if r["fee_row_id"]}
    rows = []
    for row in data["rows"]:
        pair = bindings[row["row_id"]]["spans"]
        heading = groups[row["group"]]
        matched = query is None or any(_ehs_matches(query, value) for value in [
            row["service"], row["fee"], row["group"]])
        if matched:
            rows.append(EhsRow(**row, label_native=span(pair[0], row["physical_page"]),
                fee_native=span(pair[1], row["physical_page"]), group_native=heading.native,
                exact_grid_cells=grid[row["row_id"]]["cells"],
                pdf_cell_rectangles=grid[row["row_id"]]["cell_rectangles"]))
    context_ids = ([] if query is None else
                   [c.context_id for c in contexts if _ehs_matches(query, c.text)])
    source = EhsSource.model_validate_json(json.dumps({
        "issuer": data["issuer"], "administering_agency": data["administering_agency"],
        "pdf": asset(data["source"]), "candidate": asset(data["candidate"]),
        "canonical_original": {
            "path": str(root / record["archive_path"]), "sha256": record["sha256"],
            "size_bytes": record["size_bytes"]},
        "review": {"path": str(package / "SOURCE_QA.json"),
                   "sha256": EHS_PINS["SOURCE_QA.json"],
                   "size_bytes": len(captured[str(package / "SOURCE_QA.json")])},
        "manifest": {"path": str(package / "FINAL_MANIFEST.json"),
                     "sha256": EHS_PINS["FINAL_MANIFEST.json"],
                     "size_bytes": len(captured[str(package / "FINAL_MANIFEST.json")])},
        "acceptance": {"path": str(root / EHS_ACCEPTANCE), "sha256": EHS_ACCEPTANCE_SHA,
                       "size_bytes": len(captured[str(root / EHS_ACCEPTANCE)])},
        "copied_canonical_record": {"path": str(package / "source/canonical-record.jsonl"),
            "sha256": EHS_PINS["source/canonical-record.jsonl"],
            "size_bytes": len(captured[str(package / "source/canonical-record.jsonl")])},
        "official_url": record["official_source_url"], "intake_id": record["intake_id"],
        "intake_received_at": record["received_at"],
        "acquisition_method": record["acquisition_method"],
        "original_custody_note": record["custody_note"], "reviewed_at": data["completed_at"],
        "accepted_at": acceptance["checked_at"],
        "printed_approval_claim": data["source_approval_claim"],
        "printed_effective_claim": data["source_effective_claim"],
    }))
    return EhsLookupResult(status="matched" if rows else "matched_context_only" if context_ids
        else "no_matching_row", query=query, evidence_verified=True, source=source, rows=rows,
        context=contexts, matched_context_ids=context_ids,
        observations=[*data["errata"], *data["limitations"]])


def _render_ehs(result: EhsLookupResult) -> str:
    """Expose full conditions with escaped source wording and no implied current fee answer."""
    lines = ["Source-only research — legal_currentness: not_verified; answer_safe: false.", "",
             result.boundary, ""]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("El Paso EHS verified source required")
    lines += [f"Source: `{result.source_id}` — El Paso County Board of Health.", "",
        f"[Official source]({source.official_url})", "",
        _link("Original PDF", source.pdf.path) + " · " +
        _link("Checked review", source.review.path),
        "", f"PDF SHA256: `{source.pdf.sha256}`.", "",
        "Printed approval: October 25, 2023. Printed effective claim: January 1, 2024. "
        "Both remain source claims; current applicability is unverified.", "",
        f"Repository intake: {source.intake_received_at.isoformat()}; "
        f"source review: {source.reviewed_at.isoformat()}.", "",
        "Original HTTP acquisition was not independently witnessed. "
        "Spanish equivalence was not reviewed.", "", _markdown(source.original_custody_note), "",
        "**Complete source context, definitions and exceptions**", ""]
    for context in result.context:
        lines += [f"**{_markdown(context.context_id)} — physical page {context.physical_page}**",
                  "", _markdown(context.native.text), "",
                  _link("Page image", context.native.image.path), ""]
    if not result.rows:
        lines += ["No matching fee row in this preserved snapshot.", ""]
    for row in result.rows:
        lines += [f"**{row.row_id} — physical page {row.physical_page}**", "",
                  "- Group: " + _markdown(row.group),
                  "- Service: " + _markdown(row.label_native.text),
                  "- Fee as printed: " + _markdown(row.fee_native.text),
                  "- Linked source context: " + ", ".join(row.linked_context), "",
                  _link("Page image", row.label_native.image.path), ""]
    lines += ["Source-review qualifications:", ""]
    lines += ["- " + _markdown(s) for s in result.observations]
    return "\n".join(lines) + "\n"


DOUGLAS_SOURCE_ID = "douglas-ehs-fees-atlas-directed"
PUEBLO_SOURCE_ID = "pueblo-planning-fees-atlas-directed"
DP_INTAKE = Path("research/local_review/douglas-pueblo-intake-2026-09-13/prepared-transaction")
DP_RECEIPT_SHA = "7ba1d9fa2f6c58a504551692a1d6ebed3ac8e5fed8d0dcbe459f32ca3bacf620"
DP_INTENT_SHA = "95201319ab531a8eb1b21440b7b784968de5674f639d2d90910e30215d622196"
DP_RECORDS_SHA = "db705e5c5b3397c65934c7601ff0663c76ba5e13e667fe8042f66a8459916865"
DP_PROVENANCE_SHA = "da99636e06d07b308d1718e7784151d7171c0a77a29c13cca13a803bfda733a8"
DP_SOURCES = {
    DOUGLAS_SOURCE_ID: {
        "folder": "douglas-ehs-fees-source-qa-2026-09-13", "authority": "CO-COUNTY-DOUGLAS",
        "issuer": "Douglas County Health Department", "layer": "08_County_Authorities",
        "alias": "douglas-county-ehs-fees-dcr03", "pages": 1, "manifest": "FINAL_MANIFEST.json",
        "count": 64, "verifier": "validate_package.py", "function": "verify",
        "acceptance": "DOUGLAS_EHS_SOURCE_QA", "accepted_field": "accepted_at",
        "accepted_status": "accepted_source_qa_pending_intake",
        "acceptance_sha": "496d29b20b344fc14751ce212759ae470e8c8e3b137241258deb03b27aa78564",
        "event": "E017",
        "event_sha": "3c4f325e664d9c511ba29b3a396019bfaacf82cbab2e8b41af90c9f1a4b4859e",
        "context_count": 7,
        "pins": {
            "FINAL_MANIFEST.json":
                "fc06b21588846a897651ea959f0abfed0ff00a4448bda53130e27b2aff0c3320",
            "SOURCE_QA.json":
                "69f962f1caa58f9fcf90970aed1a05d7ccdbba6bb39b69f78ff0f15012896df4",
            "SOURCE_QA.schema.json":
                "9ac5aaaa32479777aab5f58db6450f75a16bd3cb1fb970d13284f03308ee0cbf",
            "original.pdf":
                "35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687",
            "validate_package.py":
                "a10fc7e8aa34039713d0e3b02d8bdaa713f34393a7120e3ab33917d8208a4458",
        },
    },
    PUEBLO_SOURCE_ID: {
        "folder": "pueblo-planning-fees-source-qa-2026-09-13",
        "authority": "CO-MUNICIPAL-PUEBLO",
        "issuer": "City of Pueblo Planning and Community Development",
        "layer": "10_Municipal_Authorities", "alias": "city-pueblo-planning-fees",
        "pages": 4, "manifest": "MANIFEST.json", "count": 72,
        "verifier": "validate_qa.py", "function": "validate", "acceptance": "PUEBLO_SOURCE_QA",
        "accepted_field": "checked_at",
        "accepted_status": "accepted_complete_city_source_fidelity_review_pending_separate_intake",
        "acceptance_sha": "df1915b82c6e4f8a15015ac1301466589d0599814c02356269ff2628554e0920",
        "event": "E005",
        "event_sha": "abb0e0a81be60ce14de0db0240a36bd216e4a36c67461e3d4f88e81c0cd324b4",
        "context_count": 4,
        "pins": {
            "MANIFEST.json": "d8cde6d0a31c1e69bcedd10ad60a577fb4b19cd516e2da9f41ede56d0cf41a41",
            "SOURCE_QA.json":
                "3d07a5d4de0b89814561e8e40a4bca50501e6c948be0755a57c7bd60fbefdfa2",
            "SOURCE_QA.schema.json":
                "ad8ddef71b5d77a17e59392fc0c50dd87d93bbf89710305c1d40ad127a9ff050",
            "original.pdf":
                "0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b",
            "validate_qa.py": "c096d9c24d1df7de478ee9b95a87d1299c3479813fb0c1a480afc4faf74247a7",
        },
    },
}
DP_BOUNDARY = (
    "Source-only recorded schedule evidence, not a current-law or applicability answer. "
    "Complete physical rows, native bytes, source contexts and review qualifications remain "
    "attached. Blank cells are not zero. Dates and fee-setting captions are printed claims; "
    "no arithmetic, inferred waiver, legal effect or complete jurisdiction coverage is supplied. "
    "A missing match is not evidence of a free, exempt or unregulated activity. "
    "Douglas County and the City of Pueblo are separate issuers; Pueblo County is not this city."
)


class DpSpan(StrictModel):
    """An unchanged native substring, with its page, line and exact source evidence."""

    line_id: str
    physical_page: int = Field(ge=1, le=4)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    native: EhsAsset
    image: EhsAsset
    bbox: list[float] | None

    @model_validator(mode="after")
    def bound(self) -> DpSpan:
        """Reject detached byte lengths, hashes or out-of-range offsets."""
        raw = self.text.encode()
        if (not self.start < self.end <= self.native.size_bytes or
                len(raw) != self.end - self.start or
                hashlib.sha256(raw).hexdigest() != self.sha256):
            raise ValueError("Douglas/Pueblo native span differs")
        return self


class DpCell(StrictModel):
    """One intact source cell; visual normalization is distinct from native bytes."""

    field: Literal["authority", "program", "fee_type", "unit", "fee", "application"]
    displayed_text: str | None
    native_text: str | None
    native_spans: list[DpSpan]
    native_line_ids: list[str]
    unrotated_bbox: list[float] | None = None
    displayed_bbox: list[float] | None = None
    pixel_bbox: list[int] | None = None
    blank_region: list[float] | None = None

    @model_validator(mode="after")
    def exact(self) -> DpCell:
        """Preserve explicit blanks and complete ordered cell/native associations."""
        if self.native_text is None:
            if (self.displayed_text is not None or self.native_spans or self.native_line_ids or
                    self.blank_region is None):
                raise ValueError("Blank cell must remain an evidenced blank")
        elif (self.displayed_text is None or self.blank_region is not None or
                not self.native_spans or
                self.native_text != "".join(s.text for s in self.native_spans)
                or self.native_line_ids != [s.line_id for s in self.native_spans]):
            raise ValueError("Cell native identity differs")
        return self


class DpNested(StrictModel):
    """A paired subcategory or bullet, still attached to its enclosing physical row."""

    id: str
    kind: Literal["paired_subcategory", "fee_bullet"]
    application_line_ids: list[str]
    fee_line_ids: list[str]
    application_display: str
    fee_display: str
    inherited_note_line_ids: list[str]


class DpRow(StrictModel):
    """Complete cells and nested links without flattening or calculating any fee."""

    row_id: str
    physical_page: int = Field(ge=1, le=4)
    table: Literal["county", "state", "city_applications"]
    table_caption_id: str | None
    footnote_id: str | None
    linked_context_ids: list[str]
    cells: list[DpCell]
    nested: list[DpNested]

    @model_validator(mode="after")
    def complete(self) -> DpRow:
        """Reject missing columns, crossed pages and detached nested references."""
        fields = (["application", "fee"] if self.table == "city_applications" else
                  ["authority", "program", "fee_type", "unit", "fee"])
        if ([c.field for c in self.cells] != fields or
                any(s.physical_page != self.physical_page
                    for c in self.cells for s in c.native_spans)):
            raise ValueError("Douglas/Pueblo row columns or page differ")
        app = set(self.cells[0].native_line_ids)
        fee = set(self.cells[-1].native_line_ids)
        if self.table == "city_applications":
            for item in self.nested:
                if (set(item.application_line_ids) - app or set(item.fee_line_ids) - fee or
                        set(item.inherited_note_line_ids) - (app | fee)):
                    raise ValueError("Pueblo nested row association differs")
        elif (self.nested or self.table_caption_id != self.table.upper() + "-CAPTION" or
              self.table_caption_id not in self.linked_context_ids):
            raise ValueError("Douglas caption or nested structure differs")
        return self


class DpContext(StrictModel):
    """All checked captions, notes and page headers, including image-only qualifications."""

    context_id: str
    kind: str
    physical_page: int = Field(ge=1, le=4)
    text: str
    applies_to: list[str]
    native_lines: list[str]
    native_spans: list[DpSpan]
    image: EhsAsset
    unrotated_bbox: list[float] | None = None
    displayed_bbox: list[float] | None = None
    native_status: Literal["bound_native", "image_only_wordmark"]

    @model_validator(mode="after")
    def attached(self) -> DpContext:
        """Do not turn the image-only wordmark into native evidence."""
        if (self.native_lines != [s.line_id for s in self.native_spans] or
                bool(self.native_spans) != (self.native_status == "bound_native")):
            raise ValueError("Context native binding differs")
        return self


class DpAnnotation(StrictModel):
    """Keep source graphics and reviewer corrections separate from source wording."""

    id: str
    kind: str
    affected_rows: list[str]
    pages: list[int]
    statement: str
    limitation: str
    proofs: list[EhsAsset]


class DpSource(StrictModel):
    """Separate government identity, witnessed HTTP, actual intake and source-date claims."""

    source_id: Literal["douglas-ehs-fees-atlas-directed", "pueblo-planning-fees-atlas-directed"]
    review_alias: str
    authority_id: Literal["CO-COUNTY-DOUGLAS", "CO-MUNICIPAL-PUEBLO"]
    issuer: str
    official_url: str
    physical_pages: int = Field(ge=1, le=4)
    native_bytes: Literal[4923] = 4923
    source: EhsAsset
    review: EhsAsset
    review_schema: EhsAsset
    manifest: EhsAsset
    acceptance: EhsAsset
    intake_receipt: EhsAsset
    canonical_original: EhsAsset
    provenance: EhsAsset
    http_event: EhsAsset
    intake_id: str
    intake_received_at: AwareDatetime
    acquisition_method: Literal["manual_official_download"]
    http_request_started_at: AwareDatetime
    http_response_completed_at: AwareDatetime
    http_status: Literal[200]
    reviewed_at: AwareDatetime
    accepted_at: AwareDatetime
    source_date_claims: list[str]
    recorded_custody_note: str
    public_header_evidence: dict[str, Any]
    original_filename: Literal["original.pdf"]
    date_verification: Literal["printed_claims_only_not_legal_effect"] = (
        "printed_claims_only_not_legal_effect")


    @model_validator(mode="after")
    def ownership(self) -> DpSource:
        """Tie source ID to the exact government, original bytes and qualified custody order."""
        config = DP_SOURCES[self.source_id]
        if (self.authority_id != config["authority"] or self.issuer != config["issuer"] or
                self.review_alias != config["alias"] or self.physical_pages != config["pages"] or
                self.source.sha256 != config["pins"]["original.pdf"] or
                self.source.sha256 != self.canonical_original.sha256 or
                self.http_request_started_at > self.http_response_completed_at or
                self.http_response_completed_at >= self.intake_received_at):
            raise ValueError("Douglas/Pueblo source ownership or custody differs")
        return self


class DpLookupResult(StrictModel):
    """Only source evidence; even an empty match retains the verified source context."""

    status: Literal["matched", "matched_context_only", "no_matching_row", "refused_current_law"]
    source_id: Literal["douglas-ehs-fees-atlas-directed", "pueblo-planning-fees-atlas-directed"]
    query: str | None
    evidence_verified: bool
    source: DpSource | None = None
    rows: list[DpRow] = Field(max_length=44)
    context: list[DpContext]
    annotations: list[DpAnnotation]
    matched_context_ids: list[str]
    observations: list[str]
    boundary: str = DP_BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None

    @model_validator(mode="after")
    def scoped(self) -> DpLookupResult:
        """Reject evidence-bearing refusals and incomplete or mismatched result contexts."""
        if self.status == "refused_current_law":
            if (self.source or self.evidence_verified or self.rows or
                    self.context or self.annotations):
                raise ValueError("Refusal exposes Douglas/Pueblo evidence")
            return self
        ids = {c.context_id for c in self.context}
        if (not self.source or not self.evidence_verified or self.source.source_id != self.source_id
                or len(ids) != DP_SOURCES[self.source_id]["context_count"]
                or len(ids) != len(self.context)
                or len({r.row_id for r in self.rows}) != len(self.rows) or
                any(set(r.linked_context_ids) - ids for r in self.rows) or
                set(self.matched_context_ids) - ids or
                bool(self.rows) != (self.status == "matched") or
                (self.status == "matched_context_only" and not self.matched_context_ids)):
            raise ValueError("Complete verified Douglas/Pueblo result required")
        return self


def _dp_capture(base: Path, relative: str, expected: str, limit: int) -> tuple[str, bytes]:
    """Read once within a byte bound and verify the exact buffer that will be consumed."""
    path = _safe_file(base, relative)
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Douglas/Pueblo captured evidence differs: " + relative)
    return str(path), raw


def _dp_asset(base: Path, relative: str, captured: dict[str, bytes]) -> EhsAsset:
    """Construct an asset identity from checked captured bytes, never a later disk read."""
    path = _safe_file(base, relative)
    raw = captured[str(path)]
    return EhsAsset(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def _check_dp_package(root: Path, source_id: str) -> dict[str, bytes]:
    """Capture the closed accepted package; parse only the exact bytes pinned at capture."""
    config = DP_SOURCES[source_id]
    package = root / "research/local_review" / config["folder"]
    acceptance_relative = ("docs/audits/FOUR_HOUR_RUN_2026-09-12/" +
                           config["acceptance"] + "/ACCEPTANCE.json")
    key, raw = _dp_capture(root, acceptance_relative, config["acceptance_sha"], 2_000_000)
    captured = {key: raw}
    accepted = json.loads(raw)
    if (accepted["status"] != config["accepted_status"] or
            accepted["legal_currentness"] != "not_verified"):
        raise ValueError("Douglas/Pueblo acceptance scope differs")
    for name, digest in config["pins"].items():
        key, raw = _dp_capture(package, name, digest, 2_000_000)
        captured[key] = raw
    refs = json.loads(captured[str(package / config["manifest"])])["files"]
    names = {r["path"] for r in refs}
    expected = names | {config["manifest"]}
    dirs = {p.as_posix() for name in expected for p in Path(name).parents if p.as_posix() != "."}
    files, actual_dirs = set(), set()
    for path in package.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Douglas/Pueblo nonordinary package member")
        (actual_dirs if path.is_dir() else files).add(path.relative_to(package).as_posix())
    if (len(refs) != config["count"] or len(names) != len(refs) or
            files != expected or dirs != actual_dirs):
        raise ValueError("Douglas/Pueblo closed membership differs")
    total = 0
    for ref in refs:
        key = str(_safe_file(package, ref["path"]))
        if key in captured:
            raw = captured[key]
        else:
            key, raw = _dp_capture(package, ref["path"], ref["sha256"], 8_000_000)
        if len(raw) != ref["size_bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise ValueError("Douglas/Pueblo package member differs: " + ref["path"])
        total += len(raw)
        if total > 32_000_000:
            raise ValueError("Douglas/Pueblo package byte bound exceeded")
        captured[key] = raw
    schema = json.loads(captured[str(package / "SOURCE_QA.schema.json")])
    jsonschema.Draft202012Validator(schema).validate(
        json.loads(captured[str(package / "SOURCE_QA.json")]))
    return captured


def _load_dp_verified(
    root: Path, source_id: str,
) -> tuple[dict, dict, dict, dict, dict, dict[str, bytes]]:
    """Replay fixed source QA and bind exact immutable transaction and current source row."""
    config = DP_SOURCES[source_id]
    package = root / "research/local_review" / config["folder"]
    before = _check_dp_package(root, source_id)
    wrapper = (
        "import json,runpy,sys;from pathlib import Path;"
        "sys.path.insert(0,sys.argv[1]);"
        "ns=runpy.run_path(sys.argv[2],run_name='checked_source_verifier');"
        "v=ns[sys.argv[3]](Path(sys.argv[1]));"
        "sys.stdout.write(json.dumps(v))"
    )
    try:
        process = subprocess.run([sys.executable, "-I", "-B", "-c", wrapper,
            str(package), str(package / config["verifier"]), config["function"]],
            cwd=package, capture_output=True, text=True, timeout=45, check=True,
            env={"PATH": os.defpath, "PYTHONNOUSERSITE": "1"})
        output = process.stdout
        notice = ("Consider using the pymupdf_layout package for a greatly improved "
                  "page layout analysis.\n")
        if output.startswith(notice):
            output = output[len(notice):]
        verification = json.loads(output)
        expected = ({"status": "verified_source_qa_pending_intake", "physical_pages": 1,
            "rows": 44, "cells": 220, "native_cell_lines": 218, "blank_fee_cells": 2,
            "native_lines": 232, "native_bytes": 4923, "original_render_replayed": True,
            "crops_replayed": 5, "poppler_replayed": False, "legal_currentness": "not_verified",
            "answer_safe": False} if source_id == DOUGLAS_SOURCE_ID else {
            "status": "verified_source_qa_evidence", "pages": 4, "physical_rows": 44,
            "nested_entries": 43, "native_bytes": 4923, "legal_currentness": "not_verified",
            "public_requests": 0})
        if verification != expected:
            raise ValueError("Douglas/Pueblo verifier result differs")
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        raise ValueError("Douglas/Pueblo source verification failed") from error
    if _check_dp_package(root, source_id) != before:
        raise ValueError("Douglas/Pueblo evidence changed during verification")
    intake = root / DP_INTAKE
    pins = {"execution/RECEIPT.json": DP_RECEIPT_SHA, "execution/INTENT.json": DP_INTENT_SHA,
            "evidence/preparation/source-provenance.jsonl": DP_PROVENANCE_SHA,
            "execution/records.jsonl": DP_RECORDS_SHA}
    for relative, digest in pins.items():
        key, raw = _dp_capture(intake, relative, digest, 1_000_000)
        before[key] = raw
    receipt = json.loads(before[str(intake / "execution/RECEIPT.json")])
    intent = json.loads(before[str(intake / "execution/INTENT.json")])
    if (receipt["intent"] != intent or receipt["intent_sha256"] != DP_INTENT_SHA or
            receipt["status"] != "completed_archived_pending_pipeline"):
        raise ValueError("Douglas/Pueblo actual receipt differs")
    selected = [r for r in intent["records"] if r["record_id"] == source_id]
    if len(selected) != 1:
        raise ValueError("Douglas/Pueblo receipt source is not unique")
    record = selected[0]
    if (record["sha256"] != config["pins"]["original.pdf"] or
            record["layer_id"] != config["layer"] or
            record["acquisition_method"] != "manual_official_download" or
            record["received_at"] != receipt["actual_repository_received_at"] or
            record["original_filename"] != "original.pdf" or
            not record["archive_path"].startswith(
                f"_RAW_ARCHIVE/manual_intake/{config['layer']}/{source_id}/")):
        raise ValueError("Douglas/Pueblo canonical identity differs")
    with io.BytesIO(before[str(intake / "execution/records.jsonl")]) as handle:
        frozen_lines = [line for line in handle if json.loads(line).get("record_id") == source_id]
    if len(frozen_lines) != 1 or json.loads(frozen_lines[0]) != record:
        raise ValueError("Douglas/Pueblo frozen canonical line differs")
    manifest = _safe_file(root, "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl")
    if manifest.stat().st_size > 8_000_000:
        raise ValueError("Manual manifest byte bound exceeded")
    digest = _digest(manifest)
    matches = []
    with manifest.open("rb") as handle:
        for line in handle:
            value = json.loads(line)
            if value.get("record_id") == source_id:
                matches.append(line)
    if matches != frozen_lines or _digest(manifest) != digest:
        raise ValueError("Douglas/Pueblo current canonical row differs")
    key, raw = _dp_capture(root, record["archive_path"], record["sha256"], 8_000_000)
    before[key] = raw
    original = _dp_asset(root, record["archive_path"], before)
    if original.sha256 != record["sha256"] or original.size_bytes != record["size_bytes"]:
        raise ValueError("Douglas/Pueblo canonical original differs")
    with io.BytesIO(before[str(intake / "evidence/preparation/source-provenance.jsonl")]) as handle:
        sources = [json.loads(line) for line in handle]
    provenance = [s for s in sources if s["proposed_record_id"] == source_id]
    if (len(provenance) != 1 or provenance[0]["original"]["sha256"] != original.sha256 or
            provenance[0]["authority_id"] != config["authority"]):
        raise ValueError("Douglas/Pueblo provenance ownership differs")
    event_relative = ("evidence/preparation/custody/" + source_id + "/" +
                      config["event"] + "/event.json")
    key, raw = _dp_capture(intake, event_relative, config["event_sha"], 1_000_000)
    before[key] = raw
    event = json.loads(raw)
    if (event["body"]["sha256"] != original.sha256 or event["http_status"] != 200 or
            event["requested_url"] != record["official_source_url"] or
            event["completed_at"] != provenance[0]["response_completed_at"]):
        raise ValueError("Douglas/Pueblo acquisition source association differs")
    data = json.loads(before[str(package / "SOURCE_QA.json")])
    if data["source_id"] != config["alias"] or data["source"]["sha256"] != original.sha256:
        raise ValueError("Douglas/Pueblo source-review alias differs")
    return data, record, provenance[0], event, receipt, before


def _dp_span(raw: bytes, start: int, end: int, line_id: str, page: int,
             native: EhsAsset, image: EhsAsset, bbox: list[float] | None) -> DpSpan:
    """Bind exact bytes without changing whitespace, punctuation or source encoding."""
    part = raw[start:end]
    return DpSpan(line_id=line_id, physical_page=page, start=start, end=end,
        text=part.decode("utf-8"), sha256=hashlib.sha256(part).hexdigest(),
        native=native, image=image, bbox=bbox)


def _dp_douglas(
    package: Path, data: dict, captured: dict[str, bytes],
) -> tuple[list[DpRow], list[DpContext], list[DpAnnotation]]:
    """Preserve all five Douglas columns, explicit blanks and distinct caption/footnote links."""
    native = _dp_asset(package, data["native"]["path"], captured)
    image = _dp_asset(package, data["full_image"]["path"], captured)
    raw = captured[native.path]
    spans = {}
    offset = 0
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        spans[str(number)] = _dp_span(raw, offset, offset + len(line.rstrip(b"\r\n")),
                                     str(number), 1, native, image, None)
        offset += len(line)
    contexts = [DpContext(context_id=c["context_id"], kind=c["kind"], physical_page=1,
        text=c["text"], applies_to=c["applies_to"],
        native_lines=[str(n) for n in c["native_lines"]],
        native_spans=[spans[str(n)] for n in c["native_lines"]], image=image,
        unrotated_bbox=c["unrotated_bbox"], displayed_bbox=c["displayed_bbox"],
        native_status="bound_native" if c["native_lines"] else "image_only_wordmark")
        for c in data["contexts"]]
    rows = []
    for row in data["rows"]:
        cells = []
        for cell in row["cells"]:
            bound = ([] if cell["native_text"] is None else [_dp_span(raw,
                cell["utf8_start"], cell["utf8_end"], str(cell["native_line"]), 1,
                native, image, cell["unrotated_bbox"])])
            cells.append(DpCell(field=cell["field"], displayed_text=cell["displayed_text"],
                native_text=cell["native_text"], native_spans=bound,
                native_line_ids=[s.line_id for s in bound],
                unrotated_bbox=cell["unrotated_bbox"], displayed_bbox=cell["displayed_bbox"],
                blank_region=cell["blank_region"]))
        rows.append(DpRow(row_id=row["row_id"], physical_page=1, table=row["table"],
            table_caption_id=row["table_caption_id"], footnote_id=row["footnote_id"],
            linked_context_ids=[c.context_id for c in contexts if row["row_id"] in c.applies_to],
            cells=cells, nested=[]))
    annotations = [DpAnnotation(id="DOUGLAS-ERRATUM-" + str(i + 1), kind="reviewer_erratum",
        affected_rows=[e["row_id"]], pages=[1],
        statement=("Frozen " + e["field"] + ": " + e["frozen_text"] +
                   "; image-supported source: " + e["image_supported_text"]),
        limitation=e["explanation"], proofs=[_dp_asset(package, e["evidence"]["path"], captured)])
        for i, e in enumerate(data["errata"])]
    return rows, contexts, annotations


def _dp_pueblo(
    package: Path, data: dict, captured: dict[str, bytes],
) -> tuple[list[DpRow], list[DpContext], list[DpAnnotation]]:
    """Return all physical cells and their exact nested pair/bullet and inherited-note links."""
    spans = {}
    contexts = []
    for page in data["pages"]:
        native = _dp_asset(package, page["native"]["path"], captured)
        image = _dp_asset(package, page["image"]["path"], captured)
        raw = captured[native.path]
        for line in page["lines"]:
            bound = _dp_span(raw, line["start_byte"], line["end_byte"], line["id"],
                             page["physical_page"], native, image, line["bbox"])
            if bound.text != line["text"] or bound.sha256 != line["sha256"]:
                raise ValueError("Pueblo output native line differs")
            spans[line["id"]] = bound
        context_spans = [spans[i] for i in page["context_line_ids"]]
        contexts.append(DpContext(context_id="PAGE-" + str(page["physical_page"]),
            kind="page_header_and_date", physical_page=page["physical_page"],
            text="".join(s.text for s in context_spans),
            applies_to=[r["row_id"] for r in data["rows"]
                        if r["physical_page"] == page["physical_page"]],
            native_lines=page["context_line_ids"], native_spans=context_spans, image=image,
            native_status="bound_native"))
    rows = []
    for row in data["rows"]:
        cells = [DpCell(field=cell["role"], displayed_text=cell["reviewed_display"],
            native_text=cell["native_text"], native_spans=[spans[i] for i in cell["line_ids"]],
            native_line_ids=cell["line_ids"], unrotated_bbox=cell["bbox"],
            pixel_bbox=cell["pixel_bbox"]) for cell in [row["application"], row["fee"]]]
        rows.append(DpRow(row_id=row["row_id"], physical_page=row["physical_page"],
            table="city_applications", table_caption_id=None, footnote_id=None,
            linked_context_ids=["PAGE-" + str(row["physical_page"])], cells=cells,
            nested=[DpNested(**item) for item in row["nested"]]))
    annotations = [DpAnnotation(**{k: v for k, v in a.items() if k != "proof_paths"},
        proofs=[_dp_asset(package, p, captured) for p in a["proof_paths"]])
        for a in data["annotations"]]
    return rows, contexts, annotations


def _lookup_dp(root: Path, source_id: str, query: str | None) -> DpLookupResult:
    """Verify all evidence before filtering; return complete rows and full source context."""
    config = DP_SOURCES[source_id]
    data, record, provenance, event, receipt, captured = _load_dp_verified(root, source_id)
    package = root / "research/local_review" / config["folder"]
    builder = _dp_douglas if source_id == DOUGLAS_SOURCE_ID else _dp_pueblo
    rows, contexts, annotations = builder(package, data, captured)
    if len(rows) != 44:
        raise ValueError("Douglas/Pueblo source row count differs")
    selected = [r for r in rows if query is None or any(_matches(query, text)
                for cell in r.cells for text in [cell.displayed_text, cell.native_text]
                if text is not None)]
    context_ids = ([] if query is None else
                   [c.context_id for c in contexts if _matches(query, c.text)])
    acceptance_relative = ("docs/audits/FOUR_HOUR_RUN_2026-09-12/" +
                           config["acceptance"] + "/ACCEPTANCE.json")
    acceptance = json.loads(captured[str(root / acceptance_relative)])
    intake = root / DP_INTAKE
    source = DpSource.model_validate_json(json.dumps({
        "source_id": source_id, "review_alias": config["alias"],
        "authority_id": config["authority"], "issuer": config["issuer"],
        "official_url": record["official_source_url"], "physical_pages": config["pages"],
        "source": _dp_asset(package, "original.pdf", captured).model_dump(),
        "review": _dp_asset(package, "SOURCE_QA.json", captured).model_dump(),
        "review_schema": _dp_asset(package, "SOURCE_QA.schema.json", captured).model_dump(),
        "manifest": _dp_asset(package, config["manifest"], captured).model_dump(),
        "acceptance": _dp_asset(root, acceptance_relative, captured).model_dump(),
        "intake_receipt": _dp_asset(intake, "execution/RECEIPT.json", captured).model_dump(),
        "canonical_original": _dp_asset(root, record["archive_path"], captured).model_dump(),
        "provenance": _dp_asset(
            intake, "evidence/preparation/source-provenance.jsonl", captured).model_dump(),
        "http_event": _dp_asset(intake, "evidence/preparation/custody/" + source_id + "/" +
                                config["event"] + "/event.json", captured).model_dump(),
        "intake_id": record["intake_id"], "intake_received_at": record["received_at"],
        "acquisition_method": record["acquisition_method"],
        "http_request_started_at": event["started_at"],
        "http_response_completed_at": event["completed_at"],
        "http_status": event["http_status"],
        "reviewed_at": data.get("completed_at", data.get("prepared_at")),
        "accepted_at": acceptance[config["accepted_field"]],
        "source_date_claims": provenance["source_date_claims"],
        "recorded_custody_note": record["custody_note"],
        "public_header_evidence": event["public_headers"],
        "original_filename": record["original_filename"],
    }))
    notes = [*data.get("observations", []),
             *data.get("limitations", data.get("qualifications", [])),
             *provenance["qualifications"],
             "The source review's pending-intake/monitoring statements are historical; actual "
             "repository receipt is separately recorded. This lookup enrolls no monitor."]
    return DpLookupResult(status="matched" if selected else "matched_context_only" if context_ids
        else "no_matching_row", source_id=source_id, query=query, evidence_verified=True,
        source=source, rows=selected, context=contexts, annotations=annotations,
        matched_context_ids=context_ids, observations=notes)


def _render_dp(result: DpLookupResult) -> str:
    """Render complete physical cells, nested associations and all qualifications safely."""
    lines = ["Source-only research — legal_currentness: not_verified; answer_safe: false.", "",
             result.boundary, ""]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("Douglas/Pueblo verified source required")
    lines += [f"Source: `{result.source_id}` — {_markdown(source.issuer)}.", "",
        f"[Official source]({source.official_url})", "",
        _link("Original PDF", source.source.path) + " · " + _link("Source QA", source.review.path),
        "", f"PDF SHA256: `{source.source.sha256}`.", "",
        "Printed source date claims (legal effect unverified):", ""]
    lines += ["- " + _markdown(v) for v in source.source_date_claims]
    lines += ["", f"HTTP response: {source.http_response_completed_at.isoformat()}; "
        f"repository receipt: {source.intake_received_at.isoformat()}; "
        f"review: {source.reviewed_at.isoformat()}.", "", _markdown(source.recorded_custody_note),
        "", "**Complete source context**", ""]
    for context in result.context:
        lines += [f"**{context.context_id} — physical page {context.physical_page}**", "",
                  _markdown(context.text), "", _link("Page image", context.image.path), ""]
    if not result.rows:
        lines += ["No matching physical fee row in this preserved snapshot.", ""]
    for row in result.rows:
        lines += [f"**{row.row_id} — physical page {row.physical_page}**", ""]
        for cell in row.cells:
            value = ("[blank source cell; not zero]" if cell.native_text is None
                     else cell.native_text)
            lines += ["- " + cell.field + " — native: " + _markdown(value)]
            if cell.displayed_text is not None and cell.displayed_text != cell.native_text:
                lines += ["  Reviewed display: " + _markdown(cell.displayed_text)]
        lines += ["- Linked context: " + ", ".join(row.linked_context_ids), ""]
        for item in row.nested:
            lines += ["- " + _markdown(item.id) + " (" + item.kind + "): " +
                      _markdown(item.application_display) + " — " + _markdown(item.fee_display),
                      "  Inherited note lines: " + ", ".join(item.inherited_note_line_ids)]
        lines += [""]
    lines += ["Source-review annotations:", ""]
    for note in result.annotations:
        lines += ["- " + _markdown(note.id + ": " + note.statement + " " + note.limitation)]
    lines += ["", "Source-review qualifications:", ""]
    lines += ["- " + _markdown(note) for note in result.observations]
    return "\n".join(lines) + "\n"


def _captured_reference(
    captured: dict[str, bytes], base: Path, ref: dict,
) -> dict:
    """Resolve and validate an authoritative reference against consumed captured bytes."""
    path = _safe_file(base, ref["path"])
    raw = captured[str(path)]
    if (hashlib.sha256(raw).hexdigest() != ref["sha256"] or
            len(raw) != ref["size_bytes"]):
        raise ValueError("Captured source reference differs: " + ref["path"])
    return {**ref, "path": str(path)}


def _capture_source_file(root: Path, path: Path, expected: str, limit: int) -> bytes:
    """Read a bounded ordinary file once and hash the exact buffer that will be consumed."""
    name = path.relative_to(root).as_posix()
    checked = _safe_file(root, name)
    with checked.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Captured source bytes differ: " + name)
    return raw


def _capture_existing(root: Path, family: str) -> dict[str, bytes]:
    """Capture accepted family inputs and rebind manifest references to pinned buffers."""
    if family == "gj":
        base = root / PACKAGE
        _check_package(base)
        checked, anchors = {}, [(base, PINS)]
    elif family == "greeley":
        base = root / GREELEY_PACKAGE
        checked = {str(base / k): v for k, v in _check_greeley_package(base).items()}
        anchors = [(base, GREELEY_PINS)]
    elif family == "weld":
        checked = _check_weld_package(root)
        anchors = [(root / WELD_PACKAGE, WELD_PINS), (root / WELD_INTAKE, WELD_INTAKE_PINS)]
    elif family == "grid":
        checked = _check_grid_package(root)
        anchors = [(root / GRID_PACKAGE, GRID_PINS), (root / GREELEY_PACKAGE, GREELEY_PINS)]
    elif family == "springs":
        checked = _check_springs_package(root)
        anchors = [(root / SPRINGS_PACKAGE, SPRINGS_PINS),
                   (root, {SPRINGS_ACCEPTANCE.as_posix(): SPRINGS_ACCEPTANCE_SHA})]
    elif family == "springs_intake":
        checked = _check_springs_intake(root)
        anchors = [(root / SPRINGS_INTAKE, SPRINGS_INTAKE_PINS)]
    elif family == "ehs":
        checked = _check_ehs_package(root)
        anchors = [(root / EHS_PACKAGE, EHS_PINS),
                   (root, {EHS_ACCEPTANCE.as_posix(): EHS_ACCEPTANCE_SHA})]
    else:
        raise ValueError("Unsupported captured source family")
    captured = {}
    for base, pins in anchors:
        for name, expected in pins.items():
            key = str(base / name)
            if key in checked and checked[key] != expected:
                raise ValueError("Source anchor identity differs")
            captured[key] = _capture_source_file(root, Path(key), expected, 20_000_000)
    manifests = []
    if family == "gj":
        manifests.append((root / PACKAGE, "MANIFEST.json", "files"))
    if family in {"greeley", "grid"}:
        manifests.append((root / GREELEY_PACKAGE, "PACKAGE.json", "payloads"))
    if family == "grid":
        manifests.append((root / GRID_PACKAGE, "FINAL_MANIFEST.json", "files"))
    if family == "weld":
        manifests.append((root / WELD_PACKAGE, "evidence-manifest.json", "files"))
    if family == "springs":
        manifests.append((root / SPRINGS_PACKAGE, "FINAL_MANIFEST.json", "files"))
    if family == "springs_intake":
        manifests.append((root / SPRINGS_INTAKE, "INVENTORY.json", "files"))
    if family == "ehs":
        manifests.append((root / EHS_PACKAGE, "FINAL_MANIFEST.json", "files"))
    references = []
    for base, name, field in manifests:
        values = json.loads(captured[str(base / name)])[field]
        refs = [v["file"] for v in values] if field == "payloads" else values
        references.extend((base, ref) for ref in refs)
    if family == "weld":
        base = root / WELD_INTAKE
        receipt = json.loads(captured[str(base / "intake-receipt.json")])
        references.extend((base, receipt[k]) for k in
                          ["record_stream", "provenance_stream", "record_schema", "source_schema"])
        sources = [s for s in receipt["sources"] if s["source_id"] == WELD_SOURCE_ID]
        if len(sources) != 1:
            raise ValueError("Captured Weld custody source is not unique")
        references.extend((base, sources[0][k]) for k in ["access_receipt", "public_headers"])
    if family == "ehs":
        references.extend((root / EHS_PACKAGE, ref) for ref in json.loads(
            captured[str(root / EHS_ACCEPTANCE)])["copied_originals"])
    for base, ref in references:
        key = str(_safe_file(base, ref["path"]))
        if key in checked and checked[key] != ref["sha256"]:
            raise ValueError("Captured manifest and checked file identities differ")
        if key not in captured:
            captured[key] = _capture_source_file(root, Path(key), ref["sha256"], 20_000_000)
        _captured_reference(captured, base, ref)
    # Include fixed auxiliary files that existing verifiers require; no dynamic code imports.
    for key, expected in checked.items():
        if key not in captured:
            captured[key] = _capture_source_file(root, Path(key), expected, 20_000_000)
    if sum(map(len, captured.values())) > 40_000_000:
        raise ValueError("Captured source family byte bound exceeded")
    return captured


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


def _load_verified(package: Path) -> tuple[dict, dict[str, bytes]]:
    before = _capture_existing(package.parents[2], "gj")
    try:
        subprocess.run(
            [sys.executable, "-I", "-B", str(package / "build_review.py"), "--verify"],
            cwd=package, check=True, capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ValueError("Existing source-package verification failed") from exc
    if _capture_existing(package.parents[2], "gj") != before:
        raise ValueError("Evidence changed during verification")
    return json.loads(before[str(package / "SOURCE_QA.json")]), before


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


def _load_greeley_verified(package: Path) -> tuple[dict, dict, bytes, dict[str, bytes]]:
    """Run only the pinned offline wrapper, with its verified local imports available."""
    before = _capture_existing(package.parents[2], "greeley")
    review = before[str(package / GREELEY_REVIEW)]
    packet = before[str(package / "packet/manifest.json")]
    candidate_path = (
        package / "packet/02-candidate-text" / GREELEY_SOURCE_ID / "candidate.txt"
    )
    candidate = before[str(candidate_path)]
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
    if _capture_existing(package.parents[2], "greeley") != before:
        raise ValueError("Greeley evidence changed during verification")
    return json.loads(review), json.loads(packet), candidate, before


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


def _load_weld_verified(root: Path) -> tuple[dict, dict, dict[str, bytes]]:
    """Run only the pinned EHS verifier; historical absolute paths are never opened."""
    before = _capture_existing(root, "weld")
    package, intake = root / WELD_PACKAGE, root / WELD_INTAKE
    review = before[str(package / WELD_REVIEW)]
    receipt = json.loads(before[str(intake / "intake-receipt.json")])
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
    if _capture_existing(root, "weld") != before:
        raise ValueError("Weld evidence changed during verification")
    rows = {}
    for stream, schema, field in [("record_stream", "record_schema", "record_id"),
                                   ("provenance_stream", "source_schema", "source_id")]:
        validator = jsonschema.Draft202012Validator(json.loads(
            before[str(intake / receipt[schema]["path"])]))
        selected = []
        with io.BytesIO(before[str(intake / receipt[stream]["path"])]) as handle:
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
    event = [e for e in json.loads(before[str(package / "frozen/ehs/ACCESS_RESULT.json")])[
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
    if _capture_existing(root, "weld") != before:
        raise ValueError("Weld evidence changed while reading custody records")
    return data, source, before


def _lookup_weld(root: Path, query: str | None) -> WeldLookupResult:
    """Preserve complete row associations and separately searchable page context."""
    data, provenance, captured = _load_weld_verified(root)
    package = root / WELD_PACKAGE
    base = package / "frozen/ehs"
    spans = {s["id"]: (p, s) for p in data["pages"] for s in p["spans"]}

    def bind(identity: str) -> WeldBlock:
        """Bind one unchanged reviewed line to its physical native page."""
        page, span = spans[identity]
        native = Path(_captured_reference(captured, base, page["native"])["path"])
        _captured_reference(captured, base, page["image"])
        raw = span["text"].encode("utf-8")
        if captured[str(native)][span["start"]:span["end"]] != raw:
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


def _load_grid_verified(
    root: Path, source_id: str,
) -> tuple[dict, dict, bytes, dict, dict, dict[str, bytes]]:
    """Replay the accepted superseding review and bind the selected immutable source."""
    before = _capture_existing(root, "grid")
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
    data = json.loads(before[str(base / review_file)])
    candidate = before[str(base / "inputs/candidate.txt")]
    record = json.loads(before[str(package / "historical-packet/RECONCILIATION.json")])
    correction = json.loads(before[str(package / "SUPERSEDING_DISPOSITION.json")])
    packet = json.loads(before[str(root / GREELEY_PACKAGE / "packet/manifest.json")])
    selected = [d for d in packet["documents"] if d["source_id"] == source_id]
    if len(selected) != 1 or data["source_id"] != source_id:
        raise ValueError("Grid source identity mismatch")
    doc = selected[0]
    if (doc["assignment_id"] != f"EB-PDF-{number}" or doc["expected_pages"] != pages
            or doc["authority_id"] != "CO-MUNICIPAL-GREELEY"
            or doc["original"]["sha256"] != hashlib.sha256(
                before[str(base / "inputs/original.pdf")]).hexdigest()
            or doc["candidate"]["sha256"] != hashlib.sha256(candidate).hexdigest()
            or correction["corrected_observation"] != "running_title_visible_on_pages_1_2_3"
            or correction["affected_pages"] != [2, 3]
            or "ATLAS-EB016-014" not in correction["withdrawn_claim_ids"]
            or correction["source_and_candidate_changed"] is not False):
        raise ValueError("Grid source/correction relationship mismatch")
    if _capture_existing(root, "grid") != before:
        raise ValueError("Grid evidence changed during verification")
    return data, doc, candidate, record, correction, before


def _lookup_grid(root: Path, source_id: str, query: str | None) -> GridLookupResult:
    """Map only the reviewed grids, retaining complete source context on every result."""
    data, doc, candidate, record, correction, captured = _load_grid_verified(root, source_id)
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
        return _captured_reference(captured, base, pages[page]["image"])["path"]

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
        "review_path": str(base / review_file),
        "review_sha256": hashlib.sha256(captured[str(base / review_file)]).hexdigest(),
        "provenance_path": str(root / GREELEY_PACKAGE / "packet/manifest.json"),
        "packet_manifest_sha256": GREELEY_PINS["packet/manifest.json"],
        "reconciliation_path": str(package / "historical-packet/RECONCILIATION.json"),
        "reconciliation_sha256": hashlib.sha256(
            captured[str(package / "historical-packet/RECONCILIATION.json")]).hexdigest(),
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
    data, packet, candidate, captured = _load_greeley_verified(package)
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
    _captured_reference(captured, package / "packet", doc["original"])
    _captured_reference(captured, package / "packet", doc["candidate"])
    _captured_reference(captured, package / "packet", doc["pages"][0]["image"])
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
) -> (LookupResult | GreeleyLookupResult | WeldLookupResult | GridLookupResult |
      SpringsLookupResult | EhsLookupResult | DpLookupResult):
    """Verify a fixed source and return unchanged evidence for a literal keyword phrase."""
    if source_id not in {SOURCE_ID, GREELEY_SOURCE_ID, WELD_SOURCE_ID,
                         *GRID_SOURCES, SPRINGS_SOURCE_ID, EHS_SOURCE_ID, *DP_SOURCES}:
        raise ValueError("Unsupported source; only the nine fixed reviewed sources are available")
    if mode not in {"source", "current-law"}:
        raise ValueError("Unsupported lookup mode")
    if list_rows == (query is not None):
        raise ValueError("Choose exactly one of query or list_rows")
    if query is not None and not query.strip():
        raise ValueError("A nonempty keyword phrase is required")
    if mode == "current-law" or (query is not None and CURRENT_REQUEST.search(query)):
        if source_id in DP_SOURCES:
            return DpLookupResult(status="refused_current_law", source_id=source_id, query=query,
                evidence_verified=False, rows=[], context=[], annotations=[],
                matched_context_ids=[],
                observations=[
                    "Current-law and question answering are unsupported; use source keywords."])
        if source_id == EHS_SOURCE_ID:
            return EhsLookupResult(status="refused_current_law", query=query,
                evidence_verified=False, rows=[], context=[], matched_context_ids=[],
                observations=[
                    "Current-law and question answering are unsupported; use source keywords."])
        if source_id == SPRINGS_SOURCE_ID:
            return SpringsLookupResult(
                status="refused_current_law", query=query, evidence_verified=False,
                rows=[], context=[], tables=[], matched_context_ids=[], global_context_ids=[],
                observations=[
                    "Current-law and question answering are unsupported; use source keywords.",
                ],
            )
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
    if source_id in DP_SOURCES:
        return _lookup_dp(root, source_id, query)
    if source_id == EHS_SOURCE_ID:
        return _lookup_ehs(root, query)
    if source_id == SPRINGS_SOURCE_ID:
        return _lookup_springs(root, query)
    if source_id in GRID_SOURCES:
        return _lookup_grid(root, source_id, query)
    if source_id == WELD_SOURCE_ID:
        return _lookup_weld(root, query)
    if source_id == GREELEY_SOURCE_ID:
        return _lookup_greeley(root / GREELEY_PACKAGE, query)
    package = root / PACKAGE
    data, captured = _load_verified(package)
    if data["source_id"] != REVIEW_SOURCE_ID:
        raise ValueError("The review's historical source alias does not match")
    spans = {s["id"]: (p, s) for p in data["pages"] for s in p["spans"]}

    def bind(span_id: str) -> SpanBinding:
        page, span = spans[span_id]
        native = Path(_captured_reference(captured, package, page["native"])["path"])
        if captured[str(native)][span["start"]:span["end"]] != span["text"].encode():
            raise ValueError("Grand Junction captured native span differs")
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
    event = json.loads(captured[str(package / "access-event.json")])
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
    result: LookupResult | GreeleyLookupResult | WeldLookupResult | GridLookupResult
    | SpringsLookupResult | EhsLookupResult | DpLookupResult,
) -> str:
    """Render quoted source rows and their evidence links without calculating fees."""
    if isinstance(result, DpLookupResult):
        return _render_dp(result)
    if isinstance(result, EhsLookupResult):
        return _render_ehs(result)
    if isinstance(result, SpringsLookupResult):
        return _render_springs(result)
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
