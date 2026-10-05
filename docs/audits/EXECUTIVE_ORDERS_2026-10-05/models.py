"""Strict portable executive-order source and native-page research contracts."""

from __future__ import annotations

from typing import Literal

from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator

MAX_REQUESTS, MAX_TOTAL, MAX_BODY = 35, 100_000_000, 15_000_000

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int = Field(ge=0, le=MAX_BODY)

class Reservation(Strict):
    sequence: int = Field(ge=1,le=MAX_REQUESTS)
    target_id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$')
    role: Literal['welcome','catalog','listing','history','pdf','word','diagnostic']
    parent_evidence: str
    requested_url: str
    started_at: AwareDatetime
    granted_bytes: int = Field(ge=1, le=MAX_BODY)
    timeout_seconds: float = Field(gt=0,le=30)
    purpose: str
    @field_validator('requested_url')
    @classmethod
    def official(cls, value):
        p=urlsplit(value)
        if p.scheme!='https' or p.hostname not in {'www.colorado.gov','drive.google.com','drive.usercontent.google.com'} or p.username or p.password or p.fragment or any(c.isspace() for c in value):
            raise ValueError('Exact official or explicitly delegated public source HTTPS URL required')
        return value

class Result(Strict):
    reservation_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    sequence: int
    target_id: str
    role: str
    requested_url: str
    observed_final_url: str | None
    started_at: AwareDatetime
    finished_at: AwareDatetime
    http_status: int | None
    curl_exit: int | None
    safe_headers: dict[str,str]
    body: Asset
    stderr: str
    complete_transfer: bool
    charged_bytes: int = Field(ge=0,le=MAX_BODY)
    detected_format: str
    legal_currentness: Literal['not_verified']='not_verified'
    answer_safe: Literal[False]=False

class Row(Strict):
    citation:str=Field(pattern=r'^[BD] 2026 [0-9]{3}$')
    displayed_date:str
    displayed_title:str
    observed_href:str
    direct_download_url:str
    direct_url_basis:Literal['maintained_exec_orders_scraper._download_url_from_exact_observed_href']='maintained_exec_orders_scraper._download_url_from_exact_observed_href'
    inherited_index_match:bool

class Catalog(Strict):
    recorded_at:AwareDatetime
    observation_method:Literal['Chrome read-only DOM table extraction']='Chrome read-only DOM table extraction'
    source_page:Literal['https://www.colorado.gov/governor/2026-executive-orders']='https://www.colorado.gov/governor/2026-executive-orders'
    browser_tab_id:Literal['903489740']='903489740'
    browser_navigation_count:int
    browser_resource_bytes:None=None
    raw_http_html_retained:Literal[False]=False
    inherited_index_path:str
    inherited_index_sha256:str
    inherited_index_records:int
    selector_scope:Literal['2026 B and D order rows only']='2026 B and D order rows only'
    rows:list[Row]
    limitations:list[str]

class Ref(Strict):
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    bytes:int=Field(ge=0)

class Page(Strict):
    source_sha256:str
    citation:str
    physical_page:int=Field(ge=1)
    native_text:Ref
    character_count:int=Field(ge=0)
    extraction:Literal['PyMuPDF get_text(text), sort=False']='PyMuPDF get_text(text), sort=False'
    fidelity_review:Literal['unreviewed']='unreviewed'

class Source(Strict):
    citation:str
    observed_catalog_title:str
    observed_catalog_date:str
    official_catalog_url:str
    catalog_row_index:int=Field(ge=0)
    delegated_view_url:str
    final_download_url:str
    source_received_at:AwareDatetime
    original:Ref
    receipt:Ref
    physical_pages:int=Field(ge=1)
    native_pages:int=Field(ge=1)
    empty_native_pages:int=Field(ge=0)
    native_bytes:int=Field(ge=0)
    citation_string_observed_in_native:bool
    source_review:Literal['machine_native_unreviewed']='machine_native_unreviewed'
    legal_currentness:Literal['not_verified']='not_verified'
    answer_safe:Literal[False]=False

class Package(Strict):
    schema_version: Literal['geode-eo-native-package-1'] = 'geode-eo-native-package-1'
    source_handoff_manifest_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    catalog: Ref
    prior_index: Ref
    source_records: Ref
    page_records: Ref
    source_pdf_count: int = Field(ge=1, le=35)
    physical_page_count: int = Field(ge=1, le=20000)
    native_bytes: int = Field(ge=0, le=100000000)
    metered_http_requests: int = Field(ge=0, le=55)
    charged_response_bytes: int = Field(ge=0, le=130000000)
    browser_navigation_count: int = Field(ge=0, le=5)
    browser_resource_bytes: None = None
    inherited_index_is_historical: Literal[True] = True
    inherited_record_sha256_semantics: Literal['sha256_utf8_stored_full_text']
    historical_pdf_byte_hashes_known: Literal[False]
    canonical_installation: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    batch_limits: dict[str, list[int]]
    limitations: list[str]
class Closure(Strict):
    schema_version: Literal['geode-eo-native-manifest-1'] = 'geode-eo-native-manifest-1'
    excluded: Literal['MANIFEST.json'] = 'MANIFEST.json'
    files: list[Ref] = Field(max_length=999)
class Verification(Strict):
    status: Literal['verified_source_and_native_replay'] = 'verified_source_and_native_replay'
    pdf_originals: int
    physical_pages: int
    native_bytes: int
    metered_http_requests: int
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
class Hit(Strict):
    citation: str
    physical_page: int
    original_sha256: str
    source_url: str
    native_text: str
class Query(Strict):
    mode: Literal['citation', 'phrase']
    text: str
    total_matching_pages: int
    returned_pages: int
    truncated: bool
    hits: list[Hit]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False


class PriorIndexRecord(Strict):
    id: str
    layer: str
    entity_type: str
    title: str
    citation: str
    path: str
    meta_path: str | None
    source_url: str
    source_path: str
    publication_year: int
    last_updated: str
    sha256: str = Field(description='SHA-256 of UTF-8 stored full_text, not original PDF bytes.')
    tags: list[str]
    confidence: float
