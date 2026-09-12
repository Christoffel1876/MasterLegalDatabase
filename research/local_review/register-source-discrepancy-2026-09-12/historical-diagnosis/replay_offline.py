"""Replay only preserved issue parsing and identity checks; never collect sources."""

import hashlib
import json
import re
import socket
import sys
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "baseline"
URL = (
    "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026"
    "&Volume=49&yearPublishNumber=15&Month=8&Year=2026"
)


def deny_network(*args: object, **kwargs: object) -> None:
    """This replay may not establish any network connection."""

    raise RuntimeError("Offline diagnosis: network prohibited")


socket.create_connection = deny_network
sys.path.insert(0, str(BASELINE))
from geode.connectors.register_daily_parser import (
    DailyNoticeRow,
    decode_register_html,
    parse_edocket_detail,
    parse_register_issue,
)
from geode.pipeline.register_daily import NoticeProvenance, RefreshState, _notice, _row_key
from geode.schemas.models import LayerIndexRecord, RulemakingNotice


class Finding(BaseModel):
    """One old row whose linked source request is absent from the complete job log."""

    model_config = ConfigDict(extra="forbid")
    notice_id: str
    tracking_number: str | None
    notice_type: str
    ccr_citation: str | None
    title: str
    old_row_number: int
    archived_row: DailyNoticeRow
    source_evidence: str
    absent_document_requests: list[str]
    absent_detail_request: str | None
    classification: Literal["candidate_absent_from_hosted_issue_requests"]


class Replay(BaseModel):
    """A bounded offline comparison, not a currentness or removal authorization."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["archived_state_consistent_two_hosted_row_candidates"]
    issue_url: str
    archived_source_sha256: str
    old_state_ids: list[str]
    archived_replayed_ids: list[str]
    provenance_ids: list[str]
    row_count: int
    old_resolution_pages: int
    metadata_rows_schema_checked: int
    index_rows_schema_checked: int
    hosted_request_count: int
    affected_issue_request_number: int
    affected_issue_subsequent_requests: int
    candidates: list[Finding]
    fresh_http_body_available: bool
    fresh_missing_ids: list[str] | None = None
    fresh_added_row_keys: list[str] | None = None
    limitation: str
    currentness: Literal["not_verified"] = "not_verified"


def check_custody() -> None:
    """Verify exact preserved inputs against both immutable custody receipts."""

    for name in ("BASELINE_RECEIPT.json", "SUPPLEMENTAL_BASELINE_RECEIPT.json"):
        receipt = json.loads((HERE / name).read_bytes())
        for asset in receipt["assets"]:
            path = HERE / asset["path"]
            assert not path.is_symlink() and path.is_file()
            data = path.read_bytes()
            assert len(data) == asset["bytes"]
            assert hashlib.sha256(data).hexdigest() == asset["sha256"]


def replay() -> Replay:
    """Apply the copied parser and identity function to complete old source evidence."""

    check_custody()
    state = RefreshState.model_validate_json(
        (BASELINE / "_CONTROL_PLANE/REGISTER_REFRESH_STATE.json").read_bytes()
    )
    artifact = state.sources[URL]
    assert artifact.sha256 == state.issues[URL].source_sha256
    rows = parse_register_issue(
        decode_register_html((BASELINE / artifact.path).read_bytes(), artifact.content_type),
        date(2026, 8, 10), URL,
    )
    metadata = {}
    keys = {}
    with (BASELINE / "04_Rulemaking/_meta/rulemaking_notices_meta.jsonl").open() as handle:
        for line in handle:
            record = RulemakingNotice.model_validate_json(line)
            assert record.id not in metadata
            metadata[record.id] = record
            keys.setdefault(_row_key(record), []).append(record.id)
    index = {}
    with (BASELINE / "04_Rulemaking/_index.jsonl").open() as handle:
        for line in handle:
            record = LayerIndexRecord.model_validate_json(line)
            assert record.id not in index
            index[record.id] = record
    assert set(metadata) == set(index)
    provenance = {}
    with (BASELINE / "04_Rulemaking/_dataset/register_daily_sources.jsonl").open() as handle:
        for line in handle:
            record = NoticeProvenance.model_validate_json(line)
            if record.publication_url == URL:
                assert record.notice_id not in provenance
                provenance[record.notice_id] = record
    log = (HERE / "hosted/register-34694019784.log").read_text()
    requests = re.findall(r"Checking source (\d+): (https://[^\s]+)", log)
    assert [int(number) for number, _url in requests] == list(range(1, 168))
    request_urls = {value for _number, value in requests}
    target_number = next(int(number) for number, value in requests if value == URL)
    result_ids = []
    resolved = 0
    candidates = []
    for original_row in rows:
        row = original_row
        if not row.ccr_rule_affected:
            target = row.edocket_url or row.hearing_detail_url
            source = state.sources[target]
            detail = parse_edocket_detail(
                decode_register_html((BASELINE / source.path).read_bytes(), source.content_type),
                source.final_url,
            )
            assert detail.tracking_number == row.edocket_tracking_number
            row = DailyNoticeRow.model_validate({
                **row.model_dump(), "ccr_citation": detail.ccr_citation,
                "ccr_rule_affected": detail.ccr_rule_affected,
            })
            resolved += 1
        notice = _notice(row, artifact)
        existing = keys.get(_row_key(notice), [])
        assert len(existing) == 1
        identity = existing[0]
        result_ids.append(identity)
        assert provenance[identity].row == row
        assert metadata[identity].model_copy(update={"id": notice.id}) == notice
        absent = [value for value in row.document_urls if value not in request_urls]
        detail_url = row.edocket_url or row.hearing_detail_url
        if absent:
            candidates.append(Finding(
                notice_id=identity, tracking_number=row.edocket_tracking_number,
                notice_type=row.notice_type, ccr_citation=row.ccr_citation, title=row.title,
                old_row_number=row.row_number, archived_row=row,
                source_evidence=original_row.source_evidence, absent_document_requests=absent,
                absent_detail_request=detail_url if detail_url not in request_urls else None,
                classification="candidate_absent_from_hosted_issue_requests",
            ))
    assert len(result_ids) == len(set(result_ids)) == 50
    assert set(result_ids) == set(state.issues[URL].notice_ids) == set(provenance)
    return Replay(
        status="archived_state_consistent_two_hosted_row_candidates", issue_url=URL,
        archived_source_sha256=artifact.sha256, old_state_ids=sorted(state.issues[URL].notice_ids),
        archived_replayed_ids=sorted(result_ids), provenance_ids=sorted(provenance),
        row_count=len(rows), old_resolution_pages=resolved,
        metadata_rows_schema_checked=len(metadata), index_rows_schema_checked=len(index),
        hosted_request_count=len(requests), affected_issue_request_number=target_number,
        affected_issue_subsequent_requests=len(requests) - target_number, candidates=candidates,
        fresh_http_body_available=False,
        limitation=("The hosted failure did not preserve its fresh source bytes or prepared state. "
                    "The authorized local GET failed DNS before any HTTP response. Log omissions "
                    "identify two candidates; they alone cannot prove source removal or reidentity. "
                    "This replay uses pinned local implementation and archived detail sources, "
                    "not an independently recovered copy of the hosted prepared Git tree."),
    )


if __name__ == "__main__":
    result = replay()
    if "--schema" in sys.argv:
        sys.stdout.write(json.dumps(Replay.model_json_schema(), indent=2) + "\n")
    else:
        sys.stdout.write(result.model_dump_json(indent=2) + "\n")
