"""Preserve exact hearing-detail fields and compare their earlier public source bodies."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from bs4 import BeautifulSoup
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "register-daily-diagnosis/baseline"


class Strict(BaseModel):
    """Validate a bounded local evidence record before writing it."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """Exact local bytes, independent of their interpreted meaning."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class TableField(Strict):
    """A decoded visible table field with its original HTML byte range."""

    label: str
    value: str
    start_byte: int = Field(ge=0)
    end_byte: int = Field(gt=0)
    fragment_sha256: str


class Detail(Strict):
    """Source presence and field comparison; no legal status conclusion."""

    docket: str
    requested_url: str
    acquired_start: AwareDatetime
    acquired_end: AwareDatetime
    http_status: Literal[200]
    old_body: Ref
    fresh_body: Ref
    original_bytes_equal: bool
    old_fields: list[TableField]
    fresh_fields: list[TableField]
    complete_table_field_values_equal: Literal[True]
    visible_hearing_date: str
    explicit_explanation_observed: Literal[False]
    verified_legal_status: None = None


class HeaderDerivative(Strict):
    """Hash-bound removal of cookie header fields for distributable custody."""

    original_private: Ref
    public: Ref
    omitted_field_names: list[str]
    method: Literal["remove sensitive header lines and their folded continuations"]


class Review(Strict):
    """Two accessible details do not establish why issue rows disappeared."""

    reviewed_at: AwareDatetime
    status: Literal["detail_pages_accessible_fields_unchanged_explanation_unresolved"]
    details: list[Detail] = Field(min_length=2, max_length=2)
    header_derivatives: list[HeaderDerivative]
    attempts: Literal[2]
    http_responses: Literal[2]
    redirects: Literal[0]
    corpus_changed: Literal[False]
    legal_currentness: Literal["not_verified"]
    limits: list[str]


def sha(data: bytes) -> str:
    """Hash bytes without normalization."""
    return hashlib.sha256(data).hexdigest()


def ref(path: Path) -> Ref:
    """Reference an ordinary artifact inside this handoff."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(HERE).as_posix(), sha256=sha(data), size_bytes=len(data))


def write_once(path: Path, data: bytes) -> None:
    """Atomically preserve new analysis, never overwrite source or prior reports."""
    if path.exists():
        raise ValueError(f"Existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("xb") as stream:
        stream.write(data)
    temp.replace(path)


def fields(data: bytes) -> list[TableField]:
    """Extract each labeled table row using the publisher's declared ISO-8859-1."""
    result = []
    for match in re.finditer(rb"<tr\b[^>]*>.*?</tr>", data, flags=re.I | re.S):
        soup = BeautifulSoup(match[0].decode("iso-8859-1"), "html.parser")
        label, value = soup.find("th"), soup.find("td")
        if label is None or value is None:
            continue
        result.append(TableField(
            label=label.get_text(" ", strip=True), value=value.get_text(" ", strip=True),
            start_byte=match.start(), end_byte=match.end(), fragment_sha256=sha(match[0]),
        ))
    return result


def main() -> None:
    """Compare all preserved detail fields, with private headers excluded from export."""
    state = json.loads((BASELINE / "_CONTROL_PLANE/REGISTER_REFRESH_STATE.json").read_bytes())
    details, derivatives = [], []
    for number, docket in enumerate(("2026-00337", "2026-00328"), 1):
        folder = HERE / f"target-{number:02d}"
        receipt = json.loads((folder / "FETCH_RECEIPT.json").read_bytes())
        if receipt["status"] != "http_200_received" or len(receipt["events"]) != 1:
            raise ValueError("Expected single successful capture")
        event = receipt["events"][0]
        if event["http_status"] != 200 or event["curl_exit"] != 0:
            raise ValueError("Unsuccessful capture")
        url = event["requested_url"]
        artifact = state["sources"][url]
        old = (BASELINE / artifact["path"]).read_bytes()
        fresh_path = folder / event["body_path"]
        fresh = fresh_path.read_bytes()
        if sha(old) != artifact["sha256"] or sha(fresh) != event["body_sha256"]:
            raise ValueError("Source body identity differs")
        old_path = folder / "archived-detail.html.txt"
        write_once(old_path, old)
        old_fields, new_fields = fields(old), fields(fresh)
        if [(x.label, x.value) for x in old_fields] != [(x.label, x.value) for x in new_fields]:
            raise ValueError("Source table values changed")
        date_rows = [row for row in new_fields if row.label == "Date"]
        if len(date_rows) != 1:
            raise ValueError("Ambiguous hearing date field")
        details.append(Detail(
            docket=docket, requested_url=url,
            acquired_start=datetime.fromisoformat(event["started_at"]),
            acquired_end=datetime.fromisoformat(event["finished_at"]), http_status=200,
            old_body=ref(old_path), fresh_body=ref(fresh_path), original_bytes_equal=old == fresh,
            old_fields=old_fields, fresh_fields=new_fields,
            complete_table_field_values_equal=True, visible_hearing_date=date_rows[0].value,
            explicit_explanation_observed=False,
        ))
        private = folder / event["header_path"]
        header_bytes = private.read_bytes()
        if sha(header_bytes) != event["header_sha256"]:
            raise ValueError("Header identity changed")
        sensitive = {b"set-cookie", b"cookie", b"authorization", b"proxy-authorization",
                     b"www-authenticate", b"proxy-authenticate"}
        kept, omitted, skip = [], set(), False
        for line in header_bytes.splitlines(keepends=True):
            if line.startswith((b" ", b"\t")):
                if not skip:
                    kept.append(line)
                continue
            name = line.split(b":", 1)[0].strip().lower()
            skip = name in sensitive
            if skip:
                omitted.add(name.decode("ascii"))
            else:
                kept.append(line)
        public = folder / "fresh/event-01.public.headers"
        write_once(public, b"".join(kept))
        derivatives.append(HeaderDerivative(
            original_private=ref(private), public=ref(public),
            omitted_field_names=sorted(omitted),
            method="remove sensitive header lines and their folded continuations",
        ))
    record = Review(
        reviewed_at=datetime.now(timezone.utc),
        status="detail_pages_accessible_fields_unchanged_explanation_unresolved",
        details=details, header_derivatives=derivatives, attempts=2, http_responses=2,
        redirects=0, corpus_changed=False, legal_currentness="not_verified", limits=[
            "Each complete fresh table was read and compared with its archived table."
            " No explicit removal/withdrawal explanation was observed in these two pages.",
            "This is a bounded two-page negative observation, not proof that no explanation"
            " exists elsewhere or that either notice remains operative.",
            "Visible hearing dates are source statements, not legal-status determinations.",
            "The original DOCX links were not fetched again; no contact or form was used.",
            "Raw Set-Cookie headers remain local only; any repository package must select"
            " the public derivatives and omit both original .headers files.",
            "Original body bytes differ; this report certifies equal labeled table values,"
            " not whole-HTML identity or the correctness of the publisher's content.",
        ],
    )
    write_once(HERE / "DETAIL_REVIEW.json", record.model_dump_json(indent=2).encode() + b"\n")
    write_once(HERE / "DETAIL_REVIEW.schema.json",
               (json.dumps(Review.model_json_schema(), indent=2) + "\n").encode())
    print(record.status)
    print([(d.docket, len(d.fresh_fields), d.visible_hearing_date) for d in details])


if __name__ == "__main__":
    main()
