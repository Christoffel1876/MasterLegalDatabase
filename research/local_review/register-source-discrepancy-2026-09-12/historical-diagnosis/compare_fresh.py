"""Compare one preserved fresh issue body with the validated archived rows, offline."""

import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replay_offline as old
from geode.connectors.register_daily_parser import (
    DailyNoticeRow,
    decode_register_html,
    parse_register_issue,
    register_html_fingerprint,
)


class MissingRow(BaseModel):
    """An archived notice absent from this exact fresh issue table."""

    model_config = ConfigDict(extra="forbid")
    notice_id: str
    tracking_number: str
    old_notice_row: DailyNoticeRow
    absent_entire_fresh_html: bool
    absent_proposed_table: bool
    no_replacement_row_observed: bool
    old_notice_status_changed: Literal[False] = False


class Comparison(BaseModel):
    """Exact scoped source alteration; notice legal status is undetermined."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["source_table_changed_two_previously_indexed_rows_absent"]
    issue_url: str
    old_source_sha256: str
    old_source_bytes: int
    old_recorded_retrieved_at: datetime
    fresh_source_sha256: str
    fresh_source_bytes: int
    fresh_started_at: datetime
    fresh_finished_at: datetime
    old_content_fingerprint: str
    fresh_content_fingerprint: str
    old_notice_count: int
    fresh_notice_count: int
    old_proposed_count: int
    fresh_proposed_count: int
    common_rows_identical_except_row_number: int
    fresh_ids_matched_to_unchanged_archived_rows: list[str]
    removal_gate_missing_ids: list[str]
    missing: list[MissingRow] = Field(min_length=2, max_length=2)
    fresh_added_row_keys: list[str]
    parsed_rows: list[DailyNoticeRow]
    parser_regression_supported: Literal[False] = False
    source_alteration_demonstrated: Literal[True] = True
    hosted_response_byte_equality: Literal["unknown_not_preserved"]
    hosted_prepared_state_equality: Literal["unknown_not_preserved"]
    disappearance_time: None = None
    explanation_from_publisher: None = None
    legal_currentness: Literal["not_verified"] = "not_verified"
    collector_run: Literal[False] = False
    notices_deleted_or_reidentified: Literal[False] = False
    limitations: list[str]


def row_key(row: DailyNoticeRow) -> tuple[str, str | None, str]:
    """Use source designation/docket/title to compare unresolved table rows."""

    return row.notice_type, row.edocket_tracking_number, row.title


def compare() -> Comparison:
    """Revalidate the old50 identities and fresh48 rows without network or mutation."""

    replay = old.replay()
    state = old.RefreshState.model_validate_json(
        (old.BASELINE / "_CONTROL_PLANE/REGISTER_REFRESH_STATE.json").read_bytes()
    )
    artifact = state.sources[old.URL]
    capture = json.loads((old.HERE / "authorized-route/FETCH_RECEIPT.json").read_bytes())
    assert capture["status"] == "http_200_received" and len(capture["events"]) == 1
    event = capture["events"][0]
    assert event["http_status"] == 200 and event["curl_exit"] == 0
    fresh = (old.HERE / "authorized-route" / event["body_path"]).read_bytes()
    assert len(fresh) == event["body_bytes"]
    assert hashlib.sha256(fresh).hexdigest() == event["body_sha256"]
    old_bytes = (old.BASELINE / artifact.path).read_bytes()
    old_html = decode_register_html(old_bytes, artifact.content_type)
    fresh_html = decode_register_html(fresh, event["content_type"])
    prior_rows = parse_register_issue(old_html, date(2026, 8, 10), old.URL)
    fresh_rows = parse_register_issue(fresh_html, date(2026, 8, 10), old.URL)
    before = {row_key(row): row for row in prior_rows}
    after = {row_key(row): row for row in fresh_rows}
    assert len(before) == len(prior_rows) and len(after) == len(fresh_rows)
    missing_keys = set(before) - set(after)
    new_keys = set(after) - set(before)
    assert not new_keys and len(missing_keys) == 2
    for key in before.keys() & after.keys():
        assert before[key].model_dump(exclude={"row_number"}) == after[key].model_dump(
            exclude={"row_number"}
        )
    missing = []
    for candidate in replay.candidates:
        row = candidate.archived_row
        assert row_key(row) in missing_keys
        assert row.edocket_tracking_number is not None
        assert row.edocket_tracking_number not in fresh_html
        missing.append(MissingRow(
            notice_id=candidate.notice_id, tracking_number=row.edocket_tracking_number,
            old_notice_row=row, absent_entire_fresh_html=True, absent_proposed_table=True,
            no_replacement_row_observed=True,
        ))
    fresh_ids = []
    with (old.BASELINE / "04_Rulemaking/_dataset/register_daily_sources.jsonl").open() as handle:
        for line in handle:
            prior = old.NoticeProvenance.model_validate_json(line)
            if prior.publication_url == old.URL and row_key(prior.row) in after:
                fresh_ids.append(prior.notice_id)
    removed_ids = sorted(set(replay.old_state_ids) - set(fresh_ids))
    assert removed_ids == sorted(item.notice_id for item in missing)
    assert len(fresh_ids) == len(set(fresh_ids)) == 48
    return Comparison(
        status="source_table_changed_two_previously_indexed_rows_absent", issue_url=old.URL,
        old_source_sha256=artifact.sha256, old_source_bytes=len(old_bytes),
        old_recorded_retrieved_at=artifact.retrieved_at,
        fresh_source_sha256=event["body_sha256"], fresh_source_bytes=len(fresh),
        fresh_started_at=event["started_at"], fresh_finished_at=event["finished_at"],
        old_content_fingerprint=register_html_fingerprint(old_bytes),
        fresh_content_fingerprint=register_html_fingerprint(fresh),
        old_notice_count=len(prior_rows), fresh_notice_count=len(fresh_rows),
        old_proposed_count=sum(row.notice_type == "proposed" for row in prior_rows),
        fresh_proposed_count=sum(row.notice_type == "proposed" for row in fresh_rows),
        common_rows_identical_except_row_number=len(before.keys() & after.keys()),
        fresh_ids_matched_to_unchanged_archived_rows=sorted(fresh_ids),
        removal_gate_missing_ids=removed_ids,
        missing=missing, fresh_added_row_keys=[], parsed_rows=fresh_rows,
        hosted_response_byte_equality="unknown_not_preserved",
        hosted_prepared_state_equality="unknown_not_preserved",
        limitations=[
            "Fresh source is a later independent capture, not the unpreserved hosted response.",
            "Pinned local implementation and state are not the hosted prepared Git tree.",
            "No fresh hearing detail, document, alternate issue or Register index was opened.",
            "Archived CCR citations are old linked-detail evidence, not freshly reverified.",
            "Absence from this contents page does not establish withdrawal, termination, "
            "reidentification, repeal or current legal applicability.",
            "This is a snapshot comparison, not a complete statewide or historical refresh.",
        ],
    )


if __name__ == "__main__":
    result = compare()
    if "--schema" in sys.argv:
        sys.stdout.write(json.dumps(Comparison.model_json_schema(), indent=2) + "\n")
    else:
        sys.stdout.write(result.model_dump_json(indent=2) + "\n")
