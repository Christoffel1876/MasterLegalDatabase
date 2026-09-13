"""Serial, explicit single-target GETs. Never invoked by the offline verifier."""

import argparse
import fcntl
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz

from models import Attempt, HeaderCustody, Plan, PlanFreeze, Reservation
from prepare import now, put, ref

ROOT = Path(__file__).resolve().parent
PLAN_SHA = "4b9168c1b391fd9d4e39fedaa8c68de0e86609329e057e349fc268acf5015256"
PUBLIC_FIELDS = frozenset({
    b"date", b"content-type", b"content-length", b"content-disposition", b"location",
    b"last-modified", b"etag", b"cache-control", b"expires", b"vary", b"content-encoding",
    b"transfer-encoding", b"accept-ranges", b"server", b"connection", b"strict-transport-security",
})


def checked_plan() -> Plan:
    """Read the exact pre-request plan and every immutable referral byte."""
    data = (ROOT / "PLAN.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != PLAN_SHA:
        raise ValueError("plan pin differs")
    frozen = PlanFreeze.model_validate_json((ROOT / "PLAN_FREEZE.json").read_bytes())
    if frozen.plan.sha256 != PLAN_SHA:
        raise ValueError("plan freeze differs")
    for item in [frozen.plan, frozen.schema_file, *frozen.evidence]:
        path = ROOT / item.path
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError("symlink evidence")
        if ref(path) != item:
            raise ValueError("changed frozen evidence")
    return Plan.model_validate_json(data)


def public_headers(path: Path, destination: Path) -> HeaderCustody:
    """Keep exact safe response lines, digest omitted originals, discard secret-bearing bytes."""
    raw = path.read_bytes() if path.exists() else b""
    selected = []
    kept = []
    omitted = []
    previous_safe = False
    for line in raw.splitlines(keepends=True):
        name = line.split(b":", 1)[0].strip().lower()
        if line.startswith(b"HTTP/") or not line.strip():
            selected.append(line)
            previous_safe = False
        elif line[:1] in (b" ", b"\t"):
            if previous_safe:
                selected.append(line)
            else:
                omitted.append("[continuation]")
        elif name in PUBLIC_FIELDS:
            selected.append(line)
            kept.append(name.decode("ascii"))
            previous_safe = True
        else:
            omitted.append(name.decode("ascii", errors="replace"))
            previous_safe = False
    put(destination, b"".join(selected))
    result = HeaderCustody(
        original_sha256=hashlib.sha256(raw).hexdigest(), original_size_bytes=len(raw),
        public_subset=ref(destination), retained_field_names=kept,
        omitted_field_names=omitted, omitted_line_count=len(omitted), original_retained=False,
        limitation="Original header bytes were read transiently and SHA-bound, then deleted. "
        "Only an explicit public field allowlist is retained as exact original lines. Omitted "
        "values cannot be replayed offline; status/framing/public subset remains inspectable.")
    path.unlink(missing_ok=True)
    return result


def execute(target_id: str) -> Attempt:
    """Request one planned target once after consuming an immutable action reservation."""
    plan = checked_plan()
    selected = [target for target in plan.targets if target.target_id == target_id]
    if len(selected) != 1:
        raise ValueError("unknown target")
    target = selected[0]
    events = ROOT / "events"
    events.mkdir(exist_ok=True)
    prior_dirs = sorted(events.iterdir())
    prior = []
    for directory in prior_dirs:
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("unexpected event path")
        reservation = Reservation.model_validate_json((directory / "RESERVATION.json").read_bytes())
        result = Attempt.model_validate_json((directory / "RESULT.json").read_bytes())
        if result.must_stop or reservation.target_id == target_id:
            raise ValueError("previous stop condition or attempted target; no retry")
        if ref(ROOT / result.body.path) != result.body:
            raise ValueError("prior body changed")
        prior.append(result)
    if len(prior) >= plan.maximum_actions:
        raise ValueError("action budget exhausted")
    clock = datetime.now(timezone.utc)
    if clock >= datetime.fromisoformat(plan.no_start_after):
        raise ValueError("document start deadline reached")
    seconds_left = int((datetime.fromisoformat(plan.finish_by) - clock).total_seconds())
    maximum_seconds = min(plan.request_seconds, seconds_left)
    prior_bytes = sum(item.body.size_bytes for item in prior)
    maximum_bytes = min(plan.maximum_body_bytes, plan.maximum_total_body_bytes - prior_bytes)
    if maximum_seconds <= 0 or maximum_bytes <= 0:
        raise ValueError("time or byte budget exhausted")
    action_id = f"A{len(prior) + 1:03d}"
    directory = events / action_id
    directory.mkdir()
    body_path = directory / "response.body"
    transient_headers = directory / "transient-private.headers"
    descriptor = os.open(transient_headers, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)
    argv = [
        "/usr/bin/curl", "--disable", "--silent", "--show-error", "--request", "GET",
        "--proto", "=https", "--proto-redir", "=https", "--proxy", "", "--noproxy", "*",
        "--retry", "0", "--max-redirs", "0", "--connect-timeout", "15",
        "--max-time", str(maximum_seconds), "--max-filesize", str(maximum_bytes),
        "--user-agent", plan.request_user_agent, "--dump-header", str(transient_headers),
        "--output", str(body_path), "--write-out", "%{json}", "--url", target.request_url,
    ]
    reservation = Reservation(
        action_id=action_id, target_id=target_id, reserved_at=now(), plan_sha256=PLAN_SHA,
        request_url=target.request_url, maximum_body_bytes=maximum_bytes,
        maximum_seconds=maximum_seconds, connect_seconds=15, prior_actions=len(prior),
        prior_body_bytes=prior_bytes, argv=argv, shell_display=shlex.join(argv),
        runner=ref(Path(__file__).resolve()), cwd=str(ROOT),
        network_permission="explicitly_authorized_narrow_escalation")
    put(directory / "RESERVATION.json", (reservation.model_dump_json(indent=2) + "\n").encode())
    started = now()
    mono = time.monotonic()
    timed_out = False
    try:
        process = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                 timeout=maximum_seconds + 2, check=False, cwd=ROOT)
        stdout, stderr, process_exit = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, process_exit = error.stdout or b"", error.stderr or b"", None
        timed_out = True
    completed = now()
    elapsed = time.monotonic() - mono
    put(directory / "stdout.writeout.json", stdout)
    put(directory / "stderr.txt", stderr)
    if not body_path.exists():
        put(body_path, b"")
    headers = public_headers(transient_headers, directory / "public-response.headers")
    data = body_path.read_bytes()
    structural_error = None
    try:
        metadata = json.loads(stdout)
        status = int(metadata["http_code"])
        downloaded = int(metadata["size_download"])
        redirects = int(metadata["num_redirects"])
        final_url = metadata["url_effective"]
        location = metadata.get("redirect_url") or None
        tls = int(metadata["ssl_verify_result"])
    except (ValueError, KeyError, TypeError):
        status = downloaded = redirects = tls = None
        final_url = location = None
        structural_error = "Missing or invalid complete curl writeout; no completion inference."
    complete = (process_exit == 0 and not timed_out and elapsed <= maximum_seconds
                and status is not None and status > 0 and downloaded == len(data)
                and redirects == 0 and final_url == target.request_url)
    if complete:
        public = (ROOT / headers.public_subset.path).read_bytes()
        fields = {}
        for line in public.splitlines():
            if b":" in line:
                name, value = line.split(b":", 1)
                fields[name.lower()] = value.strip()
        if b"content-length" in fields and b"transfer-encoding" not in fields:
            try:
                complete = int(fields[b"content-length"]) == len(data)
            except ValueError:
                complete = False
                structural_error = "Invalid Content-Length; completion unknown."
    capped = len(data) >= maximum_bytes or process_exit == 63
    pdf_magic = data.startswith(b"%PDF-")
    parse_ok, pages, parser_version = False, None, None
    if pdf_magic:
        parser_version = fitz.VersionBind
        try:
            with fitz.open(stream=data, filetype="pdf") as document:
                if document.needs_pass:
                    raise ValueError("encrypted PDF requires password")
                pages = document.page_count
                parse_ok = pages > 0
        except Exception as error:
            structural_error = f"PDF structural parse failed: {type(error).__name__}: {error}"
    if not complete:
        disposition = "partial_or_unknown_response_stop"
    elif capped:
        disposition = "body_cap_reached_stop"
    elif status is not None and 300 <= status < 400:
        disposition = "redirect_retained_not_followed"
    elif status == 200 and pdf_magic and parse_ok:
        disposition = "complete_pdf_response_structural_only"
    else:
        disposition = "complete_non_pdf_or_http_error_response"
    result = Attempt(
        action_id=action_id, target_id=target_id, requested_url=target.request_url,
        final_url=final_url, location=location, started_at=started, completed_at=completed,
        elapsed_monotonic_seconds=elapsed, process_exit=process_exit, outer_timeout=timed_out,
        http_status=status, curl_reported_download_bytes=downloaded,
        curl_reported_redirects=redirects, tls_verify_result=tls, body=ref(body_path),
        stdout=ref(directory / "stdout.writeout.json"), stderr=ref(directory / "stderr.txt"),
        headers=headers, body_complete=complete, partial_or_unknown=not complete,
        cap_reached=capped, must_stop=not complete or capped,
        pdf_magic=pdf_magic, pdf_parse_ok=parse_ok, pdf_pages=pages,
        parser_version=parser_version, structural_error=structural_error,
        disposition=disposition, evidence_role="directed_original_response_custody_only",
        reviewed_pages=0, answer_safe=False, legal_currentness="not_verified")
    put(directory / "RESULT.json", (result.model_dump_json(indent=2) + "\n").encode())
    return result


def main() -> None:
    """Require an explicit planned identity and serialize the complete request interval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    with (ROOT / ".runtime.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = execute(args.target)
    sys.stdout.write(json.dumps({"action": result.action_id, "target": result.target_id,
                                 "status": result.http_status, "exit": result.process_exit,
                                 "bytes": result.body.size_bytes, "sha256": result.body.sha256,
                                 "pdf_pages": result.pdf_pages,
                                 "disposition": result.disposition}) + "\n")


if __name__ == "__main__":
    main()
