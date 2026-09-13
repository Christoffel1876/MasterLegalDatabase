"""Read-only portable custody checks. Never imports or invokes the network runner."""

import hashlib
import json
import shlex
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urljoin

import fitz
import jsonschema
from bs4 import BeautifulSoup

from models import Attempt, Manifest, Plan, PlanFreeze, Reservation

PLAN_SHA = "625456a31e03b482924bfe4e8430bf897e0960e8dceda34cc1153b725570ba01"
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
        prior = json.loads(captured[target.prior_actual_result.path])
        header = captured[target.prior_public_headers.path]
        locations = [line.split(b":", 1)[1].strip().decode() for line in header.splitlines()
                     if line.lower().startswith(b"location:")]
        notice = BeautifulSoup(captured[target.prior_response_body.path], "html.parser")
        require(locations == [target.raw_location]
                and prior["location"] == target.raw_location == notice.find("a")["href"],
                "exact prior response Location")
        require(prior["requested_url"] == target.prior_request_url and prior["http_status"] == 302,
                "prior actual redirect identity")
        require(target.request_url == target.raw_location.replace(" ", "%20"),
                "exact once space encoding")
        prefix = "evidence/prior-retrieval/"
        prior_manifest = json.loads(captured[target.prior_frozen_manifest.path])
        jsonschema.validate(prior_manifest, json.loads(captured[prefix + "FINAL_MANIFEST.schema.json"]))
        for item in prior_manifest["files"]:
            body = captured[prefix + item["path"]]
            require(len(body) == item["size_bytes"] and hashlib.sha256(body).hexdigest()
                    == item["sha256"], "unchanged historical package")
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
        require(reservation.maximum_body_bytes == min(20000000, 30000000 - total), "body grant")
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
    require(manifest.action_count == 1 and len({r.requested_url for r in results}) == 1
            == manifest.distinct_requested_urls, "one actual request and distinct target")
    require(total == manifest.retained_response_body_bytes <= 30000000, "total response budget")
    require(manifest.pdf_count == sum(r.pdf_parse_ok for r in results)
            and manifest.pdf_pages == sum(r.pdf_pages or 0 for r in results), "PDF aggregate")
    require(manifest.unopened_target_ids == [], "the one admitted target was requested")
    native = json.loads(captured["NATIVE.json"])
    jsonschema.validate(native, json.loads(captured["NATIVE.schema.json"]))
    require(native["source"] == results[0].body.model_dump(), "native source identity")
    combined = b""
    with fitz.open(stream=captured[results[0].body.path], filetype="pdf") as document:
        for page, item in zip(document, native["pages"], strict=True):
            extracted = page.get_text("text", flags=195, sort=False).encode("utf-8")
            require(extracted == captured[item["path"]] and len(extracted) == item["size_bytes"]
                    and hashlib.sha256(extracted).hexdigest() == item["sha256"],
                    "uncorrected per-page native replay")
            combined += extracted
    item = native["combined"]
    require(combined == captured[item["path"]] and len(combined) == item["size_bytes"]
            and hashlib.sha256(combined).hexdigest() == item["sha256"], "combined native replay")
    return {"status": "PASS", "payloads": len(names), "actual_requests": len(results),
            "response_body_bytes": total, "pdf_count": manifest.pdf_count,
            "structural_pdf_pages": manifest.pdf_pages, "source_reviewed_pages": 0,
            "native_bytes": len(combined), "planning_fee_redirect_followed": True,
            "legal_currentness": "not_verified"}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(Path(__file__).absolute().parent)) + "\n")
