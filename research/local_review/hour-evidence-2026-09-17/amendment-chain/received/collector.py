#!/usr/bin/env python3
"""SH-CHAIN-2026-09-17-01 serial public collector. Mac-local. Exact transport evidence."""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

RUN = Path(os.environ["SH_CHAIN_RUN"])
BODIES = RUN / "bodies"
EVENTS = RUN / "events"
LOGS = RUN / "logs"
for d in (BODIES, EVENTS, LOGS):
    d.mkdir(parents=True, exist_ok=True)

CAPS = dict(actions=30, targets=20, total=30_000_000, per=10_000_000)
PUBLIC_STOP = time.strptime("2026-09-17T21:10:00Z", "%Y-%m-%dT%H:%M:%SZ")
PUBLIC_STOP_TS = time.mktime(PUBLIC_STOP)  # local equiv wrong if TZ; use UTC epoch
# Prefer calendar time in UTC via time.timezone-aware:
from datetime import datetime, timezone
PUBLIC_STOP_DT = datetime(2026, 9, 17, 21, 10, 0, tzinfo=timezone.utc)

state = {
    "actions": 0,
    "targets": set(),
    "total_bytes": 0,
    "events": [],
    "queue": [],
    "seen_enqueue": set(),
    "stop_reason": None,
}

UA = "Mozilla/5.0 (compatible; GeodeSherlock/1.0; research; +local)"
SEED = "https://planningdevelopment.elpasoco.com/"

KEYWORDS = re.compile(
    r"22-?401|222141805|board\s*of\s*adjustment|parliamentary|legislative\s+and\s+parliamentary|"
    r"chapter\s*(?:two|2)|land\s+development\s+code|25-?290|rules\s+and\s+procedures|"
    r"boa\b|resolution\s*no\.?\s*22",
    re.I,
)

def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def save_state():
    payload = {
        **{k: (list(v) if isinstance(v, set) else v) for k, v in state.items() if k != "events"},
        "events_count": len(state["events"]),
        "actions": state["actions"],
        "targets_count": len(state["targets"]),
        "total_bytes": state["total_bytes"],
        "queue_len": len(state["queue"]),
        "updated_utc": utcnow(),
    }
    (LOGS / "state.json").write_text(json.dumps(payload, indent=2) + "\n")
    (LOGS / "attempted_urls.jsonl").write_text(
        "".join(json.dumps(e, sort_keys=True) + "\n" for e in state["events"])
    )

def should_stop(before_action=True):
    now = datetime.now(timezone.utc)
    if now >= PUBLIC_STOP_DT:
        state["stop_reason"] = "public_stop_21:10Z"
        return True
    if state["actions"] >= CAPS["actions"]:
        state["stop_reason"] = "action_cap"
        return True
    if len(state["targets"]) >= CAPS["targets"] and before_action:
        # allow if next URL already counted? stop before NEW target
        pass
    if state["total_bytes"] >= CAPS["total"]:
        state["stop_reason"] = "total_bytes_cap"
        return True
    return False

def normalize(url: str) -> str:
    url, _ = urldefrag(url.strip())
    return url

def enqueue(url: str, referrer: str | None, reason: str, priority: int = 50):
    u = normalize(url)
    if not u.startswith("http"):
        return
    host = urlparse(u).netloc.lower()
    # stay on elpasoco / epc-assets / clerk recorder if relevant
    if not any(h in host for h in ("elpasoco.com", "elpasoco.gov", "civicclerk.com", "civicplus.com")):
        # still allow clerk/recorder if linked from official
        if "reception" not in reason.lower() and "22-401" not in reason:
            return
    key = u
    if key in state["seen_enqueue"]:
        return
    state["seen_enqueue"].add(key)
    state["queue"].append({"url": u, "referrer": referrer, "reason": reason, "priority": priority})
    state["queue"].sort(key=lambda x: -x["priority"])

def extract_links(html: str, base: str):
    hrefs = []
    for m in re.finditer(r'''(?is)<a\s[^>]*href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a>''', html):
        href, text = m.group(1).strip(), re.sub(r"<[^>]+>", " ", m.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        absu = urljoin(base, href)
        hrefs.append((absu, text))
    # also bare PDF urls in page
    for m in re.finditer(r'''https?://[^\s"'<>]+\.pdf''', html, re.I):
        hrefs.append((m.group(0), ""))
    return hrefs

def score_link(url: str, text: str) -> int:
    blob = f"{url} {text}"
    sc = 0
    if re.search(r"22-?401", blob, re.I):
        sc += 100
    if re.search(r"222141805", blob, re.I):
        sc += 90
    if re.search(r"parliamentary|legislative\s+and\s+parliamentary|rules\s+and\s+procedures", blob, re.I):
        sc += 80
    if re.search(r"chapter\s*(?:two|2)|land\s+development\s+code|\bldc\b", blob, re.I):
        sc += 70
    if re.search(r"board\s*of\s*adjustment|\bboa\b", blob, re.I):
        sc += 40
    if re.search(r"25-?290", blob, re.I):
        sc += 30
    if url.lower().endswith(".pdf"):
        sc += 10
    if re.search(r"resolution|ordinance|amend", blob, re.I):
        sc += 15
    return sc

def fetch(url: str, referrer: str | None, reason: str):
    url = normalize(url)
    if should_stop(before_action=True):
        return None
    is_new = url not in state["targets"]
    if is_new and len(state["targets"]) >= CAPS["targets"]:
        state["stop_reason"] = "distinct_target_cap"
        return None
    if state["total_bytes"] >= CAPS["total"]:
        state["stop_reason"] = "total_bytes_cap"
        return None

    action_n = state["actions"] + 1
    aid = f"A{action_n:03d}"
    reserved = {
        "action_id": aid,
        "reserved_utc": utcnow(),
        "url": url,
        "referrer": referrer,
        "reason": reason,
        "caps_snapshot": {
            "actions_before": state["actions"],
            "targets_before": len(state["targets"]),
            "total_bytes_before": state["total_bytes"],
        },
    }
    (EVENTS / f"{aid}.reserved.json").write_text(json.dumps(reserved, indent=2) + "\n")

    body_path = BODIES / f"{aid}.body"
    hdr_path = BODIES / f"{aid}.headers.txt"
    # NO -L: record redirects as Location only; follow as separate reserved action if needed
    argv = [
        "curl", "-sS", "-D", str(hdr_path), "-o", str(body_path),
        "--max-time", "60",
        "--max-filesize", str(CAPS["per"]),
        "-A", UA,
        "-H", "Accept: text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
        "--compressed",
        "-w", "%{http_code}\n%{url_effective}\n%{size_download}\n%{redirect_url}\n%{content_type}\n",
        url,
    ]
    t0 = utcnow()
    proc = subprocess.run(argv, capture_output=True, text=True)
    t1 = utcnow()
    exit_code = proc.returncode
    stderr = proc.stderr or ""
    stdout_lines = (proc.stdout or "").strip().split("\n")
    while len(stdout_lines) < 5:
        stdout_lines.append("")
    http_code, url_eff, size_dl, redirect_url, content_type = stdout_lines[:5]

    body_bytes = body_path.read_bytes() if body_path.exists() else b""
    # enforce per-response: if somehow larger, truncate record note (curl --max-filesize should prevent)
    retained = len(body_bytes)
    if retained > CAPS["per"]:
        body_path.write_bytes(body_bytes[: CAPS["per"]])
        retained = CAPS["per"]
        truncated = True
    else:
        truncated = False

    sha = hashlib.sha256(body_bytes[:retained] if truncated else body_bytes).hexdigest() if body_path.exists() else None
    # re-read after possible truncate
    if body_path.exists():
        final_bytes = body_path.read_bytes()
        sha = hashlib.sha256(final_bytes).hexdigest()
        retained = len(final_bytes)
    else:
        final_bytes = b""
        sha = None
        retained = 0

    headers_text = hdr_path.read_text(errors="replace") if hdr_path.exists() else ""
    location = None
    for line in headers_text.splitlines():
        if line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()

    state["actions"] += 1
    state["targets"].add(url)
    state["total_bytes"] += retained

    event = {
        "action_id": aid,
        "url": url,
        "url_effective": url_eff or url,
        "referrer": referrer,
        "reason": reason,
        "start_utc": t0,
        "end_utc": t1,
        "curl_argv": argv,
        "curl_exit_code": exit_code,
        "curl_stderr": stderr[:4000],
        "http_code": http_code,
        "size_download_curl": size_dl,
        "redirect_url_curl": redirect_url,
        "content_type_curl": content_type,
        "location_header": location,
        "body_path": str(body_path.relative_to(RUN)),
        "headers_path": str(hdr_path.relative_to(RUN)),
        "retained_bytes": retained,
        "sha256": sha,
        "truncated": truncated,
        "followed_redirects": False,
        "note": "no -L; Location recorded only",
    }
    (EVENTS / f"{aid}.json").write_text(json.dumps(event, indent=2) + "\n")
    state["events"].append({
        "action_id": aid,
        "url": url,
        "http_code": http_code,
        "curl_exit_code": exit_code,
        "retained_bytes": retained,
        "sha256": sha,
        "location_header": location,
        "reason": reason,
        "referrer": referrer,
        "start_utc": t0,
        "end_utc": t1,
    })
    save_state()

    # enqueue Location as separate target if present and interesting
    if location:
        loc_abs = urljoin(url, location)
        enqueue(loc_abs, url, f"Location from {aid}", priority=60)

    # parse HTML for links
    ct = (content_type or "").lower()
    is_html = ("text/html" in ct) or (final_bytes[:200].lstrip().lower().startswith((b"<!doctype", b"<html")))
    if is_html and exit_code == 0 and http_code.startswith("2"):
        try:
            text = final_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        for absu, anchor in extract_links(text, url_eff or url):
            sc = score_link(absu, anchor)
            if sc >= 15 or KEYWORDS.search(f"{absu} {anchor}"):
                enqueue(absu, url, f"link:{anchor[:80]}", priority=sc)
        # also search page text for reception / resolution mentions without links
        if KEYWORDS.search(text):
            # official search pages
            pass

    # PDF candidate flag
    if final_bytes[:4] == b"%PDF" or url.lower().endswith(".pdf"):
        cand = {
            "action_id": aid,
            "url": url,
            "sha256": sha,
            "bytes": retained,
            "http_code": http_code,
            "reason": reason,
            "referrer": referrer,
        }
        (RUN / "candidates" / f"{aid}.json").write_text(json.dumps(cand, indent=2) + "\n")

    return event

def main():
    enqueue(SEED, None, "START_HERE seed", priority=100)
    # high-value search URLs on same site (not invented PDFs) — site search pages
    # Only add after seed observes search form; for now seed first.

    while state["queue"] and not should_stop():
        item = state["queue"].pop(0)
        url = item["url"]
        if url in state["targets"]:
            continue
        if len(state["targets"]) >= CAPS["targets"] and url not in state["targets"]:
            state["stop_reason"] = "distinct_target_cap"
            break
        if datetime.now(timezone.utc) >= PUBLIC_STOP_DT:
            state["stop_reason"] = "public_stop_21:10Z"
            break
        fetch(url, item.get("referrer"), item.get("reason", ""))
        # brief polite pause
        time.sleep(0.4)

    if not state["stop_reason"]:
        if not state["queue"]:
            state["stop_reason"] = "queue_exhausted"
        else:
            state["stop_reason"] = "loop_end"
    save_state()
    summary = {
        "stop_reason": state["stop_reason"],
        "actions": state["actions"],
        "distinct_targets": len(state["targets"]),
        "total_retained_bytes": state["total_bytes"],
        "remaining_queue": len(state["queue"]),
        "end_utc": utcnow(),
    }
    (LOGS / "collector_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
