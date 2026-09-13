"""Read-only portable custody checks. Never imports or invokes the network runner."""

import hashlib
import json
import shlex
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urljoin

import fitz
from bs4 import BeautifulSoup

from models import Attempt, Manifest, Plan, PlanFreeze, Reservation

PLAN_SHA = "4b9168c1b391fd9d4e39fedaa8c68de0e86609329e057e349fc268acf5015256"
PUBLIC_FIELDS = {
    b"date", b"content-type", b"content-length", b"content-disposition", b"location",
    b"last-modified", b"etag", b"cache-control", b"expires", b"vary", b"content-encoding",
    b"transfer-encoding", b"accept-ranges", b"server", b"connection", b"strict-transport-security",
}


def require(condition: bool, message: str) -> None:
    """Reject any failed recorded invariant without assertion optimization issues."""
    if not condition:
        raise ValueError(message)


def verify(root: Path) -> dict[str, object]:
    """Capture and verify every public member, then inspect only those checked buffers."""
    root = root.absolute()
    require(not any(p.is_symlink() for p in [root, *root.parents]), "symlink root")
    paths = list(root.rglob("*"))
    require(not any(p.is_symlink() for p in paths), "symlink member")
    raw_manifest = (root / "FINAL_MANIFEST.json").read_bytes()
    manifest = Manifest.model_validate_json(raw_manifest)
    names = [item.path for item in manifest.files]
    require(names == sorted(set(names)), "duplicate or unordered manifest")
    actual = {p.relative_to(root).as_posix() for p in paths if p.is_file()}
    require(actual == set(names) | {"FINAL_MANIFEST.json"}, "closed inventory mismatch")
    allowed_dirs = {parent.as_posix() for name in actual for parent in Path(name).parents
                    if parent.as_posix() != "."}
    require({p.relative_to(root).as_posix() for p in paths if p.is_dir()} == allowed_dirs,
            "extra directory")
    captured = {}
    for item in manifest.files:
        data = (root / item.path).read_bytes()
        require(len(data) == item.size_bytes and hashlib.sha256(data).hexdigest() == item.sha256,
                f"member byte identity: {item.path}")
        captured[item.path] = data
    require(hashlib.sha256(captured["PLAN.json"]).hexdigest() == PLAN_SHA, "fixed plan hash")
    plan = Plan.model_validate_json(captured["PLAN.json"])
    freeze = PlanFreeze.model_validate_json(captured["PLAN_FREEZE.json"])
    for item in [freeze.plan, freeze.schema_file, *freeze.evidence]:
        require(len(captured[item.path]) == item.size_bytes
                and hashlib.sha256(captured[item.path]).hexdigest() == item.sha256,
                "pre-request frozen evidence binding")
    require(freeze.plan.sha256 == PLAN_SHA, "freeze plan identity")
    for name, model in [("PLAN", Plan), ("PLAN_FREEZE", PlanFreeze),
                        ("RESERVATION", Reservation), ("RESULT", Attempt),
                        ("FINAL_MANIFEST", Manifest)]:
        require(json.loads(captured[f"{name}.schema.json"]) == model.model_json_schema(),
                f"schema differs: {name}")
    for target in plan.targets:
        parent = BeautifulSoup(captured[target.parent_body.path], "html.parser")
        require(parent.find("base")["href"] == target.base_href, "first HTML base")
        matches = parent.find_all("a", href=target.literal_href)
        require(any(a.get_text(" ", strip=True) == target.visible_label for a in matches),
                "literal county anchor and label")
        require(urljoin(target.base_href, target.literal_href) == target.resolved_county_url,
                "county URL resolution")
        require(quote(target.resolved_county_url, safe=":/?=&%") == target.encoded_county_url,
                "county URL encoding")
        if target.prior_redirect_notice:
            require(target.prior_header_summary is not None, "redirect summary missing")
            meta = json.loads(captured[target.prior_header_summary.path])
            notice = BeautifulSoup(captured[target.prior_redirect_notice.path], "html.parser")
            require(meta["headers"]["location"] == target.raw_location
                    == notice.find("a")["href"], "raw Location and notice mismatch")
            require(meta["requested_url"] == target.encoded_county_url,
                    "prior requested county URL")
            require(quote(target.raw_location, safe=":/?=&%") == target.request_url,
                    "raw Location encoding")
        else:
            require(target.raw_location is None and target.request_url == target.encoded_county_url,
                    "direct href target identity")
    results = []
    previous_completed = freeze.frozen_at
    total = 0
    for number in range(1, manifest.action_count + 1):
        directory = f"events/A{number:03d}"
        reservation = Reservation.model_validate_json(captured[f"{directory}/RESERVATION.json"])
        result = Attempt.model_validate_json(captured[f"{directory}/RESULT.json"])
        target = next(t for t in plan.targets if t.target_id == reservation.target_id)
        require(result.action_id == reservation.action_id == f"A{number:03d}", "action sequence")
        require(result.target_id == target.target_id
                and result.requested_url == reservation.request_url == target.request_url,
                "selected request identity")
        require(reservation.plan_sha256 == PLAN_SHA and reservation.prior_actions == number - 1
                and reservation.prior_body_bytes == total, "reservation baseline")
        require(reservation.maximum_body_bytes == min(20000000, 50000000 - total), "body grant")
        require(previous_completed <= reservation.reserved_at <= result.started_at
                <= result.completed_at, "serial UTC chronology")
        require(result.started_at < plan.no_start_after and result.completed_at <= plan.finish_by,
                "session deadlines")
        require(reservation.maximum_seconds == min(60, int(
            (datetime.fromisoformat(plan.finish_by)
             - datetime.fromisoformat(reservation.reserved_at)).total_seconds())), "time grant")
        require(reservation.runner.path == "retrieve.py"
                and hashlib.sha256(captured["retrieve.py"]).hexdigest()
                == reservation.runner.sha256, "executed runner pin")
        original = Path(reservation.cwd) / directory
        expected_argv = [
            "/usr/bin/curl", "--disable", "--silent", "--show-error", "--request", "GET",
            "--proto", "=https", "--proto-redir", "=https", "--proxy", "", "--noproxy", "*",
            "--retry", "0", "--max-redirs", "0", "--connect-timeout", "15", "--max-time",
            str(reservation.maximum_seconds), "--max-filesize", str(reservation.maximum_body_bytes),
            "--user-agent", plan.request_user_agent, "--dump-header",
            str(original / "transient-private.headers"), "--output", str(original / "response.body"),
            "--write-out", "%{json}", "--url", target.request_url,
        ]
        require(reservation.argv == expected_argv
                and shlex.join(expected_argv) == reservation.shell_display,
                "exact bounded command (no redirect, retry, cookie or auth options)")
        for item in [result.body, result.stdout, result.stderr, result.headers.public_subset]:
            require(item.path.startswith(directory + "/"), "cross-event file binding")
            require(len(captured[item.path]) == item.size_bytes
                    and hashlib.sha256(captured[item.path]).hexdigest() == item.sha256,
                    "result member identity")
        data = captured[result.body.path]
        metadata = json.loads(captured[result.stdout.path])
        require(metadata["http_code"] == result.http_status
                and metadata["exitcode"] == result.process_exit == 0
                and metadata["num_redirects"] == result.curl_reported_redirects == 0
                and metadata["size_download"] == result.curl_reported_download_bytes == len(data)
                and metadata["ssl_verify_result"] == result.tls_verify_result == 0
                and metadata["url_effective"] == result.final_url == target.request_url
                and (metadata["redirect_url"] or None) == result.location,
                "actual complete curl writeout binding")
        require(metadata["proxy_used"] == 0 and metadata["method"] == "GET"
                and metadata["size_upload"] == 0 and metadata["url.user"] is None
                and metadata["url.password"] is None, "ordinary unauthenticated GET metadata")
        require(result.body_complete and not result.partial_or_unknown and not result.cap_reached
                and not result.must_stop and not result.outer_timeout
                and result.elapsed_monotonic_seconds <= reservation.maximum_seconds
                and len(data) < reservation.maximum_body_bytes, "complete bounded response")
        fields = {}
        kept = []
        public = captured[result.headers.public_subset.path]
        for line in public.splitlines():
            if line.startswith(b"HTTP/") or not line.strip():
                continue
            name, value = line.split(b":", 1)
            require(name.lower() in PUBLIC_FIELDS, "nonpublic header retained")
            fields[name.lower()] = value.strip()
            kept.append(name.lower().decode("ascii"))
        require(kept == result.headers.retained_field_names, "public header names")
        require(int(fields[b"content-length"]) == len(data), "content-length body framing")
        require(result.headers.omitted_line_count == len(result.headers.omitted_field_names),
                "omitted header accounting")
        require(result.pdf_magic == data.startswith(b"%PDF-"), "PDF magic binding")
        if result.pdf_magic:
            with fitz.open(stream=data, filetype="pdf") as document:
                require(result.pdf_parse_ok and document.page_count == result.pdf_pages,
                        "PDF physical page count")
            require(result.disposition == "complete_pdf_response_structural_only", "PDF role")
        else:
            require(result.pdf_pages is None and not result.pdf_parse_ok
                    and result.http_status == 302 and result.location is not None,
                    "redirect is not a PDF")
            notice = BeautifulSoup(data, "html.parser")
            require(notice.find("a")["href"] == fields[b"location"].decode() == result.location,
                    "unfollowed new Location equals body anchor")
            require(result.disposition == "redirect_retained_not_followed", "redirect role")
        results.append(result)
        total += len(data)
        previous_completed = result.completed_at
    require(manifest.action_count == 3 and len({r.requested_url for r in results}) == 3
            == manifest.distinct_requested_urls, "3 actual requests and distinct targets")
    require(total == manifest.retained_response_body_bytes <= 50000000, "total response budget")
    require(manifest.pdf_count == sum(r.pdf_parse_ok for r in results)
            and manifest.pdf_pages == sum(r.pdf_pages or 0 for r in results), "PDF aggregate")
    require(manifest.unopened_target_ids == [], "all three planned targets were requested")
    return {"status": "PASS", "payloads": len(names), "actual_requests": len(results),
            "response_body_bytes": total, "pdf_count": manifest.pdf_count,
            "structural_pdf_pages": manifest.pdf_pages, "source_reviewed_pages": 0,
            "planning_fee_redirect_followed": False, "legal_currentness": "not_verified"}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(Path(__file__).absolute().parent)) + "\n")
