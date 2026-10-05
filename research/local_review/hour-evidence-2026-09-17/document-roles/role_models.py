"""Strict source-role decisions; printed claims never become certified legal effects."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from prepare import Asset

class Strict(BaseModel):
    """Reject undeclared data and scalar coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)

class NativeAnchor(Strict):
    """Exact unchanged native byte span supporting a selected visual observation."""
    asset: Asset
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str

class Observation(Strict):
    """Limited direct-image observation, not a complete paragraph transcription."""
    observation_id: str
    physical_page: int = Field(ge=1)
    locator: str
    kind: Literal['printed_claim','blank_field','scope','document_identity','execution','anomaly']
    visual_text: str | None
    finding: str
    crop_ids: list[str]
    native_anchor: NativeAnchor | None

class PageReview(Strict):
    """Coverage of every physical page for role evidence only."""
    physical_page: int
    printed_page: str | None
    image: Asset
    directly_viewed: Literal[True]
    role_scan_note: str
    complete_text_fidelity_checked: Literal[False]

class DateClaim(Strict):
    """Source's words and role, with no operative date inference."""
    literal: str
    role: Literal['source_stated_effective_date_unverified',
                  'source_stated_introduction_date_unverified',
                  'source_stated_adoption_date_unverified',
                  'source_stated_publication_date_unverified',
                  'source_stated_hearing_date_unverified',
                  'source_stated_conditional_effect_unverified']
    observation_id: str
    scope: str
    independently_verified: Literal[False]
    operative_date_certified: Literal[False]

class RoleDecision(Strict):
    """One exact source and its bounded visual document-role assessment."""
    priority: Literal['P04','P07','P08']
    action_id: str
    authority_id: Literal['CO-COUNTY-JEFFERSON','CO-MUNICIPAL-ARVADA']
    source: Asset
    pages: list[PageReview]
    title_as_printed: str
    assessed_role: Literal['policy_with_uncompleted_adoption_metadata',
                          'introduced_bill_with_uncompleted_execution_fields',
                          'ordinance_form_code_with_printed_adoption_claim']
    role_reason: str
    observations: list[Observation]
    dates: list[DateClaim]
    blank_or_incomplete_fields: list[str]
    execution_evidence_in_copy: str
    unverified_external_dependencies: list[str]
    legal_currentness: Literal['not_verified']
    legal_effect_certified: Literal[False]
    complete_text_fidelity_checked: Literal[False]
    intake_or_rule_promotion_authorized: Literal[False]

class Review(Strict):
    """Exact package inputs, actual observation scope and immutable qualifications."""
    schema_version: Literal[1]
    reviewer: Literal['Plato']
    recorded_at: str
    status: Literal['complete_bounded_document_role_review']
    inputs: Asset
    evidence: Asset
    custody: Literal['received_review_package']
    original_http_and_timing_verified: Literal[False]
    source_exposure: str
    visual_method: str
    directly_viewed_full_pages: Literal[28]
    directly_viewed_crops: Literal[10]
    candidate_corrections_performed: Literal[False]
    public_requests: Literal[0]
    documents: list[RoleDecision]
    limitations: list[str]

    @model_validator(mode='after')
    def check_scope(self) -> 'Review':
        """Keep exact three-source role scope and all page observations closed."""
        expected={'P04':(2,'CO-COUNTY-JEFFERSON'),'P07':(2,'CO-MUNICIPAL-ARVADA'),
                  'P08':(24,'CO-MUNICIPAL-ARVADA')}
        if [d.priority for d in self.documents] != list(expected):
            raise ValueError('Wrong or reordered review scope')
        for doc in self.documents:
            count,authority=expected[doc.priority]
            if doc.authority_id != authority or [p.physical_page for p in doc.pages] != list(range(1,count+1)):
                raise ValueError('Wrong issuer or page coverage')
            ids={o.observation_id for o in doc.observations}
            if len(ids)!=len(doc.observations) or any(d.observation_id not in ids for d in doc.dates):
                raise ValueError('Invalid observation/date associations')
        return self

class Manifest(Strict):
    """Closed audit payload list, excluding its own two manifest files."""
    schema_version: Literal[1]
    package: Literal['plato-document-roles']
    sealed_at: str
    files: list[Asset]
