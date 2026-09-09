"""Keep daily notices compatible with Python models and the published JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from geode.schemas.models import RulemakingNotice

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "_CONTROL_PLANE" / "MASTER_SCHEMA.json"


@pytest.fixture(scope="module")
def master_validator() -> Draft202012Validator:
    """Load the actual repository schema, retaining its shared references and union."""

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def minimal_notice() -> dict[str, Any]:
    """Return a synthetic notice without invented registry or confidence-route values."""

    return {
        "id": "RM-2026-daily-schema-fixture",
        "notice_type": "terminated",
        "ccr_rule_affected": "8_CCR_1508-1",
        "summary": "Synthetic notice for testing the shared schema contract.",
        "publication_date": "2026-08-25",
        "subject_tags": ["rulemaking"],
        "source_url": (
            "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/25/2026"
        ),
        "confidence": {"overall": 0.0},
    }


def test_default_null_agency_and_confidence_route_validate_both_schemas(
    master_validator: Draft202012Validator,
) -> None:
    """A normal Pydantic serialization must remain valid in the control-plane schema."""

    notice = RulemakingNotice.model_validate(minimal_notice())
    serialized = notice.model_dump(mode="json")

    assert serialized["agency_code"] is None
    assert serialized["confidence"]["route"] is None
    assert serialized["notice_type"] == "terminated"
    master_validator.validate(serialized)
    assert RulemakingNotice.model_validate(serialized) == notice


@pytest.mark.parametrize("notice_type", [
    "proposed", "adopted", "emergency", "amended", "repealed", "terminated",
])
def test_all_notice_fields_validate_in_actual_master_schema(
    master_validator: Draft202012Validator, notice_type: str,
) -> None:
    """Provenance fields previously rejected by JSON Schema must survive both validators."""

    payload = {
        **minimal_notice(),
        "notice_type": notice_type,
        "title": "Synthetic rulemaking notice title",
        "ccr_citation": "8 CCR 1508-1",
        "agency": "State Treasurer",
        "agency_code": None,
        "source_section_heading": "Terminated rulemaking",
        "source_row_number": 4,
        "source_evidence": "CCR #: 8 CCR 1508-1 | Tracking #: 2026-00275",
        "notice_type_source": "register_table_headers",
        "hearing_date": "2026-08-05",
        "effective_date": "2026-09-01",
        "edocket_tracking_number": "2026-00275",
        "edocket_url": "https://www.sos.state.co.us/CCR/eDocketDetails.do?trackingNum=2026-00275",
        "source_path": "_RAW_ARCHIVE/register/daily/" + "a" * 64 + ".html",
        "raw_text_path": "_RAW_ARCHIVE/register/synthetic-schema-fixture.txt",
        "extraction_method": "register_daily_table_v1",
        "field_confidence": {"agency_code": 0.0, "source_evidence": 1.0},
        "confidence": {
            "overall": 0.0,
            "fields": {"agency_code": 0.0},
            "route": "flag_accept",
        },
    }
    notice = RulemakingNotice.model_validate(payload)
    serialized = notice.model_dump(mode="json")

    assert set(serialized) == set(RulemakingNotice.model_fields)
    master_validator.validate(serialized)
    assert RulemakingNotice.model_validate(serialized) == notice


@pytest.mark.parametrize("location", ["record", "confidence"])
def test_unknown_properties_remain_rejected_by_both_schemas(
    master_validator: Draft202012Validator, location: str,
) -> None:
    """Adding supported fields must not loosen either schema's closed object contract."""

    serialized = RulemakingNotice.model_validate(minimal_notice()).model_dump(mode="json")
    master_validator.validate(serialized)
    target = serialized if location == "record" else serialized["confidence"]
    target["unexpected_regulatory_claim"] = "unsupported"

    with pytest.raises(PydanticValidationError):
        RulemakingNotice.model_validate(serialized)
    with pytest.raises(JsonSchemaValidationError):
        master_validator.validate(serialized)
