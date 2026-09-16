"""Reserve one visible public action locally; this helper never performs public requests."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from models import ActionLog, Reservation, Result

ROOT = Path(__file__).resolve().parent
CUTOFF = datetime(2026, 9, 13, 17, 45, tzinfo=timezone.utc)


class Accounting(BaseModel):
    """The measured visible-action counters, without a wire-budget claim."""

    model_config = ConfigDict(extra="forbid", strict=True)
    reserved_actions: int
    charged_visible_actions: int
    distinct_urls: int
    retained_body_bytes: int
    pending_action: str | None
    can_reserve: bool
    stop_reasons: list[str]
    public_requests_by_helper: int = 0


def ordinary(path: Path) -> None:
    """Reject symlinks in all ancestors before accessing local state."""
    for item in [path, *path.parents]:
        if item.is_symlink():
            raise ValueError("Symlinked state path")


def load_log(delivery: Path) -> ActionLog:
    """Load immutable action records in their numerical serial order."""
    ordinary(delivery)
    reservations, results = [], []
    for path in sorted((delivery / "reservations").glob("*.json")):
        ordinary(path)
        reservations.append(Reservation.model_validate_json(path.read_bytes()))
    for path in sorted((delivery / "results").glob("*.json")):
        ordinary(path)
        results.append(Result.model_validate_json(path.read_bytes()))
    return ActionLog(reservations=reservations, results=results)


def counters(log: ActionLog, now: datetime) -> Accounting:
    """Stop continuation after unknown/partial bodies, denial, cutoff or exhausted budgets."""
    reasons = []
    pending = log.reservations[-1].action_id if len(log.reservations) > len(log.results) else None
    if any(r.visible_redirect_urls for r in log.results):
        reasons.append("Unexpected automatic redirect observed; stop")
    by_id = {r.action_id: r.requested_url for r in log.reservations}
    if any(r.observed_final_url not in {None, by_id[r.action_id]} for r in log.results):
        reasons.append("Unexpected final URL observed; stop")
    if pending:
        reasons.append("A reserved action still has no immutable result")
    if now >= CUTOFF:
        reasons.append("Research cutoff reached")
    if any(r.body_size_basis in {"unknown", "retained_partial"} for r in log.results):
        reasons.append("Unknown or partial response-body accounting; stop public activity")
    charged = len(log.reservations) + sum(len(r.visible_redirect_urls) for r in log.results)
    urls = {r.requested_url for r in log.reservations if r.requested_url}
    urls.update(url for result in log.results for url in result.visible_redirect_urls)
    total = sum(r.observed_body_bytes or 0 for r in log.results)
    if charged >= 4:
        reasons.append("Total visible-action budget exhausted")
    if total >= 60_000_000:
        reasons.append("Total recorded response-body budget exhausted")
    return Accounting(reserved_actions=len(log.reservations), charged_visible_actions=charged,
                      distinct_urls=len(urls), retained_body_bytes=total, pending_action=pending,
                      can_reserve=not reasons, stop_reasons=reasons)


def save_new(path: Path, value: BaseModel) -> None:
    """Persist validated bytes atomically without replacing an earlier evidence record."""
    ordinary(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    raw = (value.model_dump_json(indent=2) + "\n").encode()
    type(value).model_validate_json(raw)
    with temporary.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        # link is an atomic no-replace publication; the temporary bytes are already durable.
        os.link(temporary, path)
    finally:
        temporary.unlink()
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def reserve(delivery: Path, value: Reservation, now: datetime) -> Accounting:
    """Validate the next complete serial state before recording the reservation."""
    log = load_log(delivery)
    state = counters(log, now)
    if not state.can_reserve:
        raise ValueError("; ".join(state.stop_reasons))
    if value.action_id != f"SHEXT004-A{len(log.reservations) + 1:03}":
        raise ValueError("Next reservation ID must follow the serial prefix")
    if value.reserved_at != now:
        raise ValueError("Reservation timestamp must be the actual local reservation time")
    # A denied exact endpoint receives no retry, browser alternate or spelling substitution.
    denied = {r.action_id for r in log.results if r.outcome == "access_denied"}
    denied_urls = {r.requested_url for r in log.reservations if r.action_id in denied}
    for result in log.results:
        if result.action_id in denied:
            denied_urls.update(result.visible_redirect_urls)
            denied_urls.add(result.observed_final_url)
    if value.requested_url in denied_urls and value.requested_url is not None:
        raise ValueError("Denied endpoint cannot be retried")
    allowed = {row["encoded_requested_url"] for row in json.loads((ROOT / "TARGETS.json").read_bytes())}
    if value.action_kind == "search" or value.requested_url not in allowed:
        raise ValueError("Only the four exact primary URLs are authorized")
    if value.requested_url in {r.requested_url for r in log.reservations}:
        raise ValueError("No primary target may be retried")
    updated = ActionLog(reservations=[*log.reservations, value], results=log.results)
    save_new(delivery / "reservations" / (value.action_id + ".json"), value)
    return counters(updated, now)


def complete(delivery: Path, value: Result, now: datetime) -> Accounting:
    """Retain even an overrun result, then refuse continuation if the full log violates caps."""
    log = load_log(delivery)
    if len(log.reservations) != len(log.results) + 1:
        raise ValueError("There is no single pending action")
    if value.action_id != log.reservations[-1].action_id:
        raise ValueError("Result does not close the pending reservation")
    for asset in value.retained_assets:
        relative = Path(asset.path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe result asset path")
        path = delivery / relative
        ordinary(path)
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != asset.sha256 or path.stat().st_size != asset.size_bytes:
            raise ValueError("Result asset bytes differ")
    save_new(delivery / "results" / (value.action_id + ".json"), value)
    if value.visible_redirect_urls:
        raise ValueError("Automatic redirects were not authorized; preserve result and stop")
    if value.observed_final_url not in {None, log.reservations[-1].requested_url}:
        raise ValueError("Unexpected final URL; preserve result and stop")
    # Result publication precedes the cap check so a real overrun cannot disappear from history.
    return counters(load_log(delivery), now)


def main() -> int:
    """Perform only local accounting; actual public tools remain the operator's responsibility."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["reserve", "complete", "status"])
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    delivery = args.delivery.absolute()
    ordinary(delivery)
    delivery.mkdir(parents=True, exist_ok=True)
    ordinary(delivery / ".accounting.lock")
    with (delivery / ".accounting.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        now = datetime.now(timezone.utc)
        if args.operation == "status":
            result = counters(load_log(delivery), now)
        elif args.operation == "reserve":
            if args.input is None:
                raise ValueError("Provide a reservation template with --input")
            data = json.loads(args.input.read_bytes())
            data["reserved_at"] = now.isoformat()
            value = Reservation.model_validate_json(json.dumps(data))
            result = reserve(delivery, value, now)
        else:
            if args.input is None:
                raise ValueError("Provide the observed result JSON with --input")
            result = complete(delivery, Result.model_validate_json(args.input.read_bytes()), now)
        sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
