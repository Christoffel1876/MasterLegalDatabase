"""One-time local preparation; contains no network operation."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from models import FileRef, Plan, PlanFreeze, Target

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "ptolemy-sh004-audit"


def now() -> str:
    """Return actual UTC wall time."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def put(path: Path, data: bytes) -> None:
    """Create a new atomic file, refusing an existing destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError(f"already exists: {path}")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(data)
    os.replace(temporary, path)


def ref(path: Path) -> FileRef:
    """Bind exact local bytes."""
    data = path.read_bytes()
    return FileRef(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
                   size_bytes=len(data))


def copy(relative: str, expected: str) -> FileRef:
    """Copy a frozen predecessor member only after its expected hash passes."""
    data = (PRIOR / relative).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"prior evidence changed: {relative}")
    destination = ROOT / "evidence" / relative
    put(destination, data)
    return ref(destination)


def encode(value: str) -> str:
    """Encode observed literal spaces while preserving existing URL syntax."""
    return quote(value, safe=":/?=&%")


def main() -> None:
    """Freeze three observed referral chains without requesting any target."""
    building = copy("parent-proofs/SHEXT003-A002.html",
                    "7b9eafb61f8e505a0dcc5756986ddb8fbf299ebe118c81a6f9e48088d3ceb6dc")
    planning = copy("received/raw/SHEXT004-A001.html",
                    "bdad2052d6747e3066b42c7a857f4905d52f9464c36213d905936e709962e625")
    prior_targets = json.loads((PRIOR / "assignment/TARGETS.json").read_bytes())
    targets = []
    for rank, body_sha, header_sha in [
        (3, "405cac7c193ed4338f0065abd00f220bc087411790f0c89bd5403b8cc338f5d6",
         "743916b2421d26189532920459866a97e7c8cfa8a0c3b09a593e28fbeeef97bc"),
        (4, "35504079c37e870057b11530fc9a3c23aca757b5f57e363c07d0caca8844059b",
         "8a59d077baa7f17c6b2588c2317498bde188c4e1ab4e0993d0c444a422e0762f"),
    ]:
        old = prior_targets[rank - 1]
        soup = BeautifulSoup((ROOT / building.path).read_bytes(), "html.parser")
        anchors = soup.find_all("a", href=old["original_href"])
        assert anchors and soup.find("base")["href"] == old["base_href"]
        assert any(a.get_text(" ", strip=True) == old["visible_label"] for a in anchors)
        notice = copy(f"received/raw/SHEXT004-A00{rank}.bin", body_sha)
        headers = copy(f"received/headers/SHEXT004-A00{rank}.json", header_sha)
        meta = json.loads((ROOT / headers.path).read_bytes())
        location = meta["headers"]["location"]
        notice_soup = BeautifulSoup((ROOT / notice.path).read_bytes(), "html.parser")
        assert notice_soup.find("a")["href"] == location
        assert meta["requested_url"] == old["encoded_requested_url"]
        targets.append(Target(
            target_id=f"CHAFFEE-D00{rank - 2}", authority_id="CO-COUNTY-CHAFFEE", layer_id="08",
            parent_url=old["parent_url"], parent_body=building, base_href=old["base_href"],
            literal_href=old["original_href"], visible_label=old["visible_label"],
            resolved_county_url=urljoin(old["base_href"], old["original_href"]),
            encoded_county_url=old["encoded_requested_url"], prior_redirect_notice=notice,
            prior_header_summary=headers, prior_reported_status=302, raw_location=location,
            request_url=encode(location),
            encoding_rule="urljoin first HTML base and literal href; encode spaces once",
            evidence_limit="Inherited official HTML and received 302 notice/header summary; prior "
            "retrieval command and original response headers were not independently witnessed.",
            anticipated_role=old["purpose"], legal_currentness="not_verified"))
    soup = BeautifulSoup((ROOT / planning.path).read_bytes(), "html.parser")
    href = ("Documents/Departments/Planning & Zoning/Application Forms & Fees/"
            "app_fee_schedule.pdf?t=202503011142110")
    anchor = soup.find("a", href=href)
    assert anchor and anchor.get_text(" ", strip=True) == "Application Fee Schedule"
    base = soup.find("base")["href"]
    resolved = urljoin(base, href)
    targets.append(Target(
        target_id="CHAFFEE-D003", authority_id="CO-COUNTY-CHAFFEE", layer_id="08",
        parent_url="https://www.chaffeecounty.org/departments/"
        "community_planning_natural_resources/application_forms_fees.php",
        parent_body=planning, base_href=base, literal_href=href,
        visible_label="Application Fee Schedule", resolved_county_url=resolved,
        encoded_county_url=encode(resolved), prior_redirect_notice=None, prior_header_summary=None,
        prior_reported_status=None, raw_location=None, request_url=encode(resolved),
        encoding_rule="urljoin first HTML base and literal href; encode spaces once",
        evidence_limit="Exact href in received HTML body; prior acquisition remains a received "
        "claim. Query digits are not an adoption, edition or effective date.",
        anticipated_role="Application fee schedule lead, not yet retrieved or source reviewed.",
        legal_currentness="not_verified"))
    assert len({t.request_url for t in targets}) == 3
    plan = Plan(
        schema_version="chaffee-directed-plan-v1", prepared_at=now(),
        status="PREPARED_NOT_EXECUTED", targets=targets, maximum_actions=3,
        maximum_distinct_urls=3, maximum_body_bytes=20000000, maximum_total_body_bytes=50000000,
        request_seconds=60, connect_seconds=15, no_start_after="2026-09-13T17:45:00Z",
        finish_by="2026-09-13T18:00:00Z", redirects=False, retries=0,
        request_user_agent="Geode-source-custody/1.0 (read-only official-source preservation)",
        authorization="Atlas authorized these three exact public GETs and direct narrow network "
        "escalation because this session already established sandbox DNS failure. No browser "
        "identity, login, cookies, retries, redirect following or additional targets.",
        limitations=["Only source-byte custody and structural PDF parsing are authorized here.",
                     "No canonical intake, source transcription review, legal effect or currentness.",
                     "Any deliberate failed request counts; no budget replenishment.",
                     "Stop remaining requests on unknown, partial or capped response body.",
                     "Prior parent/redirect evidence remains supplied custody; new direct retrieval "
                     "does not retroactively authenticate that acquisition."])
    put(ROOT / "PLAN.json", (plan.model_dump_json(indent=2) + "\n").encode())
    put(ROOT / "PLAN.schema.json", (json.dumps(Plan.model_json_schema(), indent=2) + "\n").encode())
    frozen = PlanFreeze(frozen_at=now(), plan=ref(ROOT / "PLAN.json"),
                        schema_file=ref(ROOT / "PLAN.schema.json"),
                        evidence=[ref(p) for p in sorted((ROOT / "evidence").rglob("*")) if p.is_file()],
                        public_actions_before_freeze=0)
    put(ROOT / "PLAN_FREEZE.json", (frozen.model_dump_json(indent=2) + "\n").encode())
    put(ROOT / "PLAN_FREEZE.schema.json",
        (json.dumps(PlanFreeze.model_json_schema(), indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
