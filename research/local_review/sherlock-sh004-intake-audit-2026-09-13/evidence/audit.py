"""Portable offline SH004 evidence audit; no transport, dispatch, or canonical writes."""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urljoin, urlsplit

from bs4 import BeautifulSoup
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

ROOT = Path(__file__).absolute().parent
PACKET_SHA = "4485cb16ddbf4dbd0e1b7b7b505961d3d7e67d6fb59bae4194763e4117536c04"
START_SHA = "c5ff150d2d8390ebac122eb25078ad0853f75c40c6759782769ff94a129b8e0e"


class Strict(BaseModel):
    """Reject undeclared fields and coercion in additive audit records."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(Strict):
    """One local immutable byte identity."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Action(Strict):
    """Reported public action versus actually retained bytes."""

    action_id: str
    authority_id: Literal["CO-COUNTY-CHAFFEE"]
    requested_url: str
    reported_final_url: str
    reported_status: int
    reservation_time_claim: AwareDatetime
    finished_time_claim: AwareDatetime
    reported_header_date: str
    body: Ref
    observed_body_kind: Literal["fee_catalog_html", "redirect_notice_html"]
    pdf_magic_present: Literal[False]
    received_header_metadata: Ref
    recorded_command: Ref
    unopened_location: str | None
    original_http_witnessed: Literal[False]


class Finding(Strict):
    """An accepted observation or explicit qualification, never legal promotion."""

    id: str
    disposition: Literal["accepted_local_evidence", "qualified", "unverified_claim"]
    finding: str
    evidence_paths: list[str]


class Facts(Strict):
    """Measured finite evidence counts; unrelated retained duplicates are not actions."""

    received_files: int
    inventory_rows: int
    inventory_hash_failures: list[str]
    inventory_unlisted: list[str]
    hash_summary_rows: int
    hash_summary_failures: list[str]
    reported_actions: Literal[4]
    distinct_requested_urls: Literal[4]
    reported_redirect_hops: Literal[0]
    actual_unique_body_bytes: Literal[166875]
    retained_raw_files: Literal[6]
    retained_raw_file_bytes_including_aliases: Literal[333155]
    retained_pdf_bodies: Literal[0]
    manual_comparison_rows: Literal[64]
    manual_exact_digest_matches: Literal[0]
    manual_exact_url_matches: Literal[0]
    parent_anchor_matches_by_rank: list[int]
    catalog_link_occurrences: Literal[431]
    location_leads: Literal[2]
    unique_derived_urls: Literal[165]
    backlog_rows: Literal[163]
    unique_backlog_urls: Literal[163]
    omitted_derived_urls: list[str]
    backlog_outside_county_host: Literal[43]
    serialized_label_qualifications: list[str]
    url_serialization_qualifications: list[str]
    useful_unopened_fee_lead: str
    actions: list[Action]


class Audit(Strict):
    """Initial offline intake disposition with original acquisition explicitly unverified."""

    schema_version: Literal["geode.sh004.offline-audit.v1"]
    prepared_at: AwareDatetime
    status: Literal["offline_audit_complete_with_qualifications"]
    assignment_manifest_sha256: Literal[PACKET_SHA]
    custody: Ref
    report: Ref
    facts: Facts
    findings: list[Finding]
    source_qa_performed: Literal[False]
    public_requests_by_auditor: Literal[0]
    canonical_writes: Literal[0]
    agent_current_state_verified: Literal[False]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


class Manifest(Strict):
    """Closed audit package, including the untouched delivery and assignment snapshots."""

    created_at: AwareDatetime
    files: list[Ref]
    status: Literal["frozen_offline_audit"]


def need(condition: bool, reason: str) -> None:
    """Fail on an evidence inconsistency."""
    if not condition:
        raise ValueError(reason)


def digest(raw: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def ref(path: str, data: dict[str, bytes]) -> Ref:
    """Bind a captured member."""
    return Ref(path=path, sha256=digest(data[path]), size_bytes=len(data[path]))


def capture(root: Path) -> dict[str, bytes]:
    """Capture ordinary local members, rejecting symlink ancestors and descendants."""
    for p in [root, *root.parents]:
        need(not p.is_symlink(), "Symlink root")
    data = {}
    for p in root.rglob("*"):
        need(not p.is_symlink(), "Symlink member")
        if p.is_file():
            data[p.relative_to(root).as_posix()] = p.read_bytes()
    return data


def measured(data: dict[str, bytes]) -> Facts:
    """Recompute all claimed finite counts and local link/body/clock relationships."""
    need(digest(data["assignment/FINAL_MANIFEST.json"]) == PACKET_SHA, "Assignment pin differs")
    need(digest(data["assignment/START_HERE.md"]) == START_SHA, "Instructions pin differs")
    packet = json.loads(data["assignment/FINAL_MANIFEST.json"])
    for row in packet["files"]:
        raw = data["assignment/" + row["path"]]
        need(digest(raw) == row["sha256"] and len(raw) == row["size_bytes"], "Packet member differs")
    log = json.loads(data["received/ACTION_LOG.json"])
    targets = json.loads(data["assignment/TARGETS.json"])
    need(len(log["reservations"]) == len(log["results"]) == len(targets) == 4, "Wrong action scope")
    # Validate against the frozen assignment's strict Pydantic schema through its captured
    # schema documents; no helper command or network method is executed here.
    import jsonschema
    jsonschema.Draft202012Validator(json.loads(data["assignment/ActionLog.schema.json"])).validate(log)
    inventory = json.loads(data["received/ARTIFACT_INVENTORY.json"])["files"]
    names = [r["path"] for r in inventory]
    need(len(names) == len(set(names)), "Duplicate inventory paths")
    actual = {p[9:] for p in data if p.startswith("received/")}
    failures = [r["path"] for r in inventory if "received/" + r["path"] not in data or
                digest(data["received/" + r["path"]]) != r["sha256"] or
                len(data["received/" + r["path"]]) != r["size_bytes"]]
    summary_failures, summary_count = [], 0
    for line in data["received/hash-summary.txt"].decode().splitlines():
        if not line.strip():
            continue
        h, name, size = re.fullmatch(r"([a-f0-9]{64})  (.*?)  ([0-9]+)", line).groups()
        summary_count += 1
        if digest(data["received/" + name]) != h or len(data["received/" + name]) != int(size):
            summary_failures.append(name)
    manual = [json.loads(line) for line in io.BytesIO(
        data["assignment/comparison/manual_source_intake_manifest.jsonl"])]
    matches, actions, prior_finish, total = [], [], None, 0
    for n, (reservation, result, target) in enumerate(zip(log["reservations"], log["results"], targets), 1):
        aid = f"SHEXT004-A{n:03}"
        need(reservation["action_id"] == result["action_id"] == aid, "Action serial identity differs")
        need(reservation["authority_id"] == "CO-COUNTY-CHAFFEE", "Wrong authority")
        need(reservation["requested_url"] == target["encoded_requested_url"] ==
             result["observed_final_url"], "Wrong target/final URL")
        need(json.loads(data[f"received/reservations/{aid}.json"]) == reservation and
             json.loads(data[f"received/results/{aid}.json"]) == result, "Combined log differs")
        start = datetime.fromisoformat(reservation["reserved_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(result["finished_at"].replace("Z", "+00:00"))
        cutoff = datetime(2026, 9, 13, 17, 45, tzinfo=timezone.utc)
        need(start <= end < cutoff and (end - start).total_seconds() <= 90,
             "Reported time interval exceeds grant")
        need(prior_finish is None or prior_finish <= start, "Reported serial times overlap")
        prior_finish = end
        raw = data[f"received/raw/{aid}.bin"]
        need(not raw.startswith(b"%PDF") and b"<" in raw, "Unexpected body format")
        need(len(raw) == result["observed_body_bytes"] and digest(raw) == result["body_sha256"],
             "Measured body identity differs")
        need(not result["visible_redirect_urls"] and not result["pdf_parse_succeeded"] and
             result["physical_pages"] is None, "Unexpected PDF/hop claim")
        need(len(raw) <= min(20_000_000, 60_000_000 - total), "Recorded body exceeds remaining cap")
        total += len(raw)
        for asset in result["retained_assets"]:
            body = data["received/" + asset["path"]]
            need(digest(body) == asset["sha256"] and len(body) == asset["size_bytes"],
                 "Retained asset differs")
        headers = json.loads(data[f"received/headers/{aid}.json"])
        meta = headers["curl_meta"]
        need(headers["requested_url"] == reservation["requested_url"] == meta["final_url"],
             "Header final/request URL differs")
        need(int(meta["size_download"]) == len(raw) == int(headers["headers"]["content-length"]),
             "Reported header body size differs")
        need(int(meta["http_code"]) == result["observed_http_status"] and
             int(meta["num_redirects"]) == 0, "Reported status/hops differ")
        command = data[f"received/logs/curl_cmd_{aid}.txt"].decode()
        for option in ["--retry 0", "--max-redirs 0", "--proto =https", "--max-filesize 20000000",
                       "--max-time 90", "--connect-timeout 15", reservation["requested_url"]]:
            need(option in command, "Required recorded command bound absent")
        need(" -L " not in command and "--location" not in command and "--insecure" not in command,
             "Unexpected recorded redirect/insecure command")
        location = headers["location_observed_unfollowed"]
        soup = BeautifulSoup(raw, "html.parser")
        if n <= 2:
            need(result["observed_http_status"] == 200 and location is None, "Wrong catalog status")
            need(data[f"received/raw/{aid}.html"] == raw, "HTML/raw aliases differ")
            need(soup.find("base")["href"] == "https://www.chaffeecounty.org/", "Unexpected HTML base")
        else:
            need(result["observed_http_status"] == 302 and soup.title.get_text() == "Document Moved",
                 "Wrong redirect-body claim")
            need(soup.find("a")["href"] == location == headers["headers"]["location"],
                 "Body/header redirect lead differs")
        parent = data["parent-proofs/" + target["parent_action_id"] + ".html"]
        need(digest(parent) == target["parent_sha256"], "Inherited parent digest differs")
        ps = BeautifulSoup(parent, "html.parser")
        base = ps.find("base")["href"]
        anchors = [a for a in ps.find_all("a", href=True) if a["href"] == target["original_href"]
                   and a.get_text(" ", strip=True) == target["visible_label"]]
        need(bool(anchors) and base == target["base_href"], "Inherited parent anchor differs")
        resolved = urljoin(base, target["original_href"])
        need(resolved == target["resolved_url"] and quote(resolved, safe=":/?=&%") ==
             target["encoded_requested_url"], "Inherited href encoding differs")
        matches.append(len(anchors))
        actions.append(Action(
            action_id=aid, authority_id="CO-COUNTY-CHAFFEE", requested_url=reservation["requested_url"],
            reported_final_url=result["observed_final_url"], reported_status=result["observed_http_status"],
            reservation_time_claim=start, finished_time_claim=end,
            reported_header_date=headers["headers"]["date"], body=ref(f"received/raw/{aid}.bin", data),
            observed_body_kind="fee_catalog_html" if n <= 2 else "redirect_notice_html",
            pdf_magic_present=False, received_header_metadata=ref(f"received/headers/{aid}.json", data),
            recorded_command=ref(f"received/logs/curl_cmd_{aid}.txt", data),
            unopened_location=location, original_http_witnessed=False))
    catalogs = json.loads(data["received/derived/catalog_link_leads.json"])
    locations = json.loads(data["received/derived/location_leads.json"])
    backlog = json.loads(data["received/BACKLOG.json"])["entries"]
    soups = {aid: BeautifulSoup(data[f"received/raw/{aid}.html"], "html.parser")
             for aid in ["SHEXT004-A001", "SHEXT004-A002"]}
    label_notes, url_notes = [], []
    for item in catalogs:
        match = re.fullmatch(r"(SHEXT004-A00[12]) literal_href=(.*?) label=(.*?) base=(.*)",
                             item["discovered_from"])
        need(match is not None, "Catalog provenance format differs")
        aid, href, label, base = match.groups()
        href, label = ast.literal_eval(href), ast.literal_eval(label)
        anchors = [a for a in soups[aid].find_all("a", href=True) if a["href"] == href]
        need(bool(anchors) and base == soups[aid].find("base")["href"], "Catalog href not in source")
        if not any(a.get_text(" ", strip=True) == label for a in anchors):
            label_notes.append(item["discovered_from"])
        if urljoin(base, href) != item["url"]:
            url_notes.append(item["discovered_from"])
    derived_urls = {x["url"] for x in catalogs + locations}
    backlog_urls = {x["url"] for x in backlog}
    requested_urls = {x.requested_url for x in actions}
    need(backlog_urls == derived_urls - requested_urls, "Backlog URL projection differs")
    useful = next(a for a in soups["SHEXT004-A001"].find_all("a", href=True)
                  if a.get_text(" ", strip=True) == "Application Fee Schedule")
    return Facts(
        received_files=len(actual), inventory_rows=len(inventory), inventory_hash_failures=failures,
        inventory_unlisted=sorted(actual - set(names)), hash_summary_rows=summary_count,
        hash_summary_failures=summary_failures, reported_actions=4, distinct_requested_urls=4,
        reported_redirect_hops=0, actual_unique_body_bytes=total, retained_raw_files=6,
        retained_raw_file_bytes_including_aliases=sum(len(b) for n, b in data.items()
                                                     if n.startswith("received/raw/")),
        retained_pdf_bodies=0, manual_comparison_rows=len(manual),
        manual_exact_digest_matches=sum(r["sha256"] == a.body.sha256 for r in manual for a in actions),
        manual_exact_url_matches=sum(r.get("official_source_url") == a.requested_url
                                     for r in manual for a in actions),
        parent_anchor_matches_by_rank=matches, catalog_link_occurrences=len(catalogs),
        location_leads=len(locations), unique_derived_urls=len(derived_urls), backlog_rows=len(backlog),
        unique_backlog_urls=len(backlog_urls), omitted_derived_urls=sorted(derived_urls - backlog_urls),
        backlog_outside_county_host=sum(urlsplit(x).hostname not in
            {"www.chaffeecounty.org", "chaffeecounty.org"} for x in backlog_urls),
        serialized_label_qualifications=label_notes, url_serialization_qualifications=url_notes,
        useful_unopened_fee_lead=quote(urljoin("https://www.chaffeecounty.org/", useful["href"]),
                                      safe=":/?=&%"), actions=actions)


def findings() -> list[Finding]:
    """Record the independent audit disposition, keeping claims separate from measurement."""
    rows = [
        ("accepted_local_evidence", "All56 delivered inventory rows and57 hash-summary rows match "
         "their retained files. The complete snapshot has59 delivery files: inventory excludes itself, "
         "hash-summary and the empty accounting lock. Six raw files contain four unique response bodies; "
         "A001/A002 .bin and.html files are byte-identical aliases, not extra actions.",
         ["received/ARTIFACT_INVENTORY.json", "received/hash-summary.txt", "CUSTODY.json"]),
        ("accepted_local_evidence", "The four logged requested/final URLs match the four exact approved "
         "targets, with serial reported intervals inside the cutoff and90-second/20MB limits. Total unique "
         "retained bodies166,875B are below60MB. No hop appears in the reported action log.",
         ["received/ACTION_LOG.json", "assignment/PLAN.json"]),
        ("qualified", "The retained evidence is two fee-catalog HTML bodies and two302 redirect notices, "
         "not ordinance PDFs. The notices' actual anchors match the supplied Location summaries. "
         "Both Revize locations remain unopened; no adoption/execution/currentness follows from labels.",
         ["received/raw/SHEXT004-A003.bin", "received/raw/SHEXT004-A004.bin"]),
        ("qualified", "Headers/curl write-out fields are selected JSON summaries. Original raw header "
         "output, original execution-tool call, full wire sequence and actual launch-time clock check "
         "are absent. Preserve original_html as the delivery's provenance claim, not an independently "
         "witnessed Atlas HTTP acquisition. Recorded timestamps and server dates remain reported claims.",
         ["received/headers/SHEXT004-A001.json", "received/logs/curl_cmd_SHEXT004-A001.txt"]),
        ("qualified", "Saved command text contains an explicit Chrome/Mac browser User-Agent not requested "
         "by the suggested packet command. It is an unquoted display of arguments, not a safely "
         "replayable shell script or proof of execution. No evidence establishes a publisher-denial "
         "bypass; do not describe this as a default curl identity or newly verified ordinary transport.",
         ["received/logs/curl_cmd_SHEXT004-A001.txt", "assignment/START_HERE.md"]),
        ("accepted_local_evidence", "All four inherited targets reproduce from the two exact pinned "
         "SH003 HTML parents, their first base element, literal anchor and space encoding. Rank2 has "
         "two matching anchors. Visible2025 label versus2026 filename mismatch is preserved.",
         ["assignment/TARGETS.json", "parent-proofs/SHEXT003-A001.html",
          "parent-proofs/SHEXT003-A002.html"]),
        ("qualified", "Backlog163 is a URL-deduplicated projection of431 catalog-link occurrences plus "
         "two Locations (165 distinct URLs), removing the two catalogs already opened. This is not "
         "163 single-resource legal priorities or proof of completeness. Forty-three URLs are outside "
         "the county host; CO-COUNTY-CHAFFEE is discovery context, not verified ownership of every target.",
         ["received/BACKLOG.json", "received/derived/catalog_link_leads.json"]),
        ("qualified", "One serialized label retains HTML entity spellings rather than exact visible "
         "text. Two catalog self-links have a trailing empty# removed in the derived URL. These are "
         "explicit minor serialization qualifications, not missing exact href evidence or new requests.",
         ["received/derived/catalog_link_leads.json"]),
        ("accepted_local_evidence", "The Application Fee Schedule PDF is an actual unopened anchor "
         "on A001, with the exact encoded URL retained in facts. A002 chiefly links application forms; "
         "those filenames do not prove fee-table contents. No new document was opened by this audit.",
         ["received/raw/SHEXT004-A001.html", "received/raw/SHEXT004-A002.html"]),
        ("qualified", "The exact64-manual-record comparison has zero exact requested-URL or response "
         "digest matches. This deliberately narrow check does not establish absence from the full legacy "
         "archive, current registry, other source versions or statewide legal universe.",
         ["assignment/COMPARISON.json", "assignment/comparison/manual_source_intake_manifest.jsonl"]),
        ("unverified_claim", "REPORT says completed and stopped. No independent observation of the "
         "external agent's current state or complete hidden traffic exists. The local snapshot is frozen; "
         "that does not certify that the original agent stopped. Only the two pinned SH003 parents were "
         "rechecked here, not every historical SH003 byte.", ["received/REPORT.md"]),
    ]
    return [Finding(id=f"F{n:02}", disposition=d, finding=f, evidence_paths=p)
            for n, (d, f, p) in enumerate(rows, 1)]


def write_new(path: Path, raw: bytes) -> None:
    """Publish only a newly prepared audit artifact."""
    need(not path.exists(), "Refuse overwrite")
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("xb") as handle:
        handle.write(raw)
    os.replace(tmp, path)


def main() -> None:
    """Create once or verify the immutable audit; verification is the default operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = capture(ROOT)
    if args.write:
        need("FINAL_MANIFEST.json" not in data, "Already frozen")
        audit = Audit(schema_version="geode.sh004.offline-audit.v1",
                      prepared_at=datetime.now(timezone.utc),
                      status="offline_audit_complete_with_qualifications",
                      assignment_manifest_sha256=PACKET_SHA, custody=ref("CUSTODY.json", data),
                      report=ref("received/REPORT.md", data), facts=measured(data), findings=findings(),
                      source_qa_performed=False, public_requests_by_auditor=0, canonical_writes=0,
                      agent_current_state_verified=False, legal_currentness="not_verified", answer_safe=False)
        raw = (audit.model_dump_json(indent=2) + "\n").encode()
        Audit.model_validate_json(raw)
        write_new(ROOT / "AUDIT.json", raw)
        write_new(ROOT / "AUDIT.schema.json",
                  (json.dumps(Audit.model_json_schema(), indent=2) + "\n").encode())
        md = "---\nstatus: offline_audit_complete_with_qualifications\nlegal_currentness: not_verified\n"
        md += "answer_safe: false\n---\n\n# SH004 independent offline audit\n\n"
        md += "Four recorded targets; two HTML catalogs, two302 notice bodies, zero PDFs. "
        md += "166,875 unique response bytes. All supplied hashes pass. Original transport was not "
        md += "witnessed; the original agent's stopped state is not independently verified.\n\n"
        for f in audit.findings:
            md += f"## {f.id} — {f.disposition.replace('_', ' ')}\n\n{f.finding}\n\n"
            md += "Evidence: " + ", ".join(f.evidence_paths) + ".\n\n"
        md += "## Portable check\n\nRun `python -B audit.py` from this directory or any working "
        md += "directory using its absolute path. It verifies closed hashes, schemas, exact captured "
        md += "input custody and recomputes all finite facts. It sends no public requests and executes "
        md += "no historical transport/accounting commands. Dependencies: Pydantic2, BeautifulSoup4, "
        md += "jsonschema. `--write` is a one-time builder and refuses an existing freeze. No canonical "
        md += "intake or source QA is approved by this report.\n"
        write_new(ROOT / "AUDIT.md", md.encode())
        write_new(ROOT / "FINAL_MANIFEST.schema.json",
                  (json.dumps(Manifest.model_json_schema(), indent=2) + "\n").encode())
        data = capture(ROOT)
        manifest = Manifest(created_at=datetime.now(timezone.utc),
                            files=[ref(p, data) for p in sorted(data)], status="frozen_offline_audit")
        write_new(ROOT / "FINAL_MANIFEST.json", (manifest.model_dump_json(indent=2) + "\n").encode())
        data = capture(ROOT)
    manifest = Manifest.model_validate_json(data["FINAL_MANIFEST.json"])
    need(set(data) == {f.path for f in manifest.files} | {"FINAL_MANIFEST.json"}, "Closed audit differs")
    need(len(manifest.files) == len({f.path for f in manifest.files}), "Duplicate audit path")
    for item in manifest.files:
        need(ref(item.path, data) == item, "Audit member differs")
    need(json.loads(data["AUDIT.schema.json"]) == Audit.model_json_schema(), "Audit schema differs")
    need(json.loads(data["FINAL_MANIFEST.schema.json"]) == Manifest.model_json_schema(),
         "Manifest schema differs")
    audit = Audit.model_validate_json(data["AUDIT.json"])
    custody = json.loads(data["CUSTODY.json"])
    for item in custody["files"]:
        need(ref(item["path"], data).model_dump() == item, "Original custody capture differs")
    need(audit.facts == measured(data) and audit.findings == findings(), "Audit replay differs")
    sys.stdout.write(json.dumps({"status": "passed", "payloads": len(manifest.files),
                                 "actions": 4, "unique_body_bytes": 166875,
                                 "retained_pdf_bodies": 0, "original_http_witnessed": False,
                                 "agent_stopped_verified": False, "public_requests": 0}) + "\n")


if __name__ == "__main__":
    main()
