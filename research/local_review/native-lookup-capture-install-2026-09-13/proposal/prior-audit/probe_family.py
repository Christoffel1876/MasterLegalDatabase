"""Bounded offline temporal file-substitution probes; production evidence is read-only."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import socket
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / "MasterLegalDatabase"


class Event(BaseModel):
    """One actual isolated reproduction, retaining success or failure without relabeling it."""
    model_config = ConfigDict(strict=True, extra="forbid")
    case: str
    source_id: str
    started_at: str
    completed_at: str
    status: Literal["returned_injected_evidence", "rejected", "not_reproduced"]
    verification_calls: int
    checker_calls: int
    error: str | None
    result: dict[str, Any] | None
    source_files_restored_in_fixture: bool
    public_requests: Literal[0] = 0


class Receipt(BaseModel):
    """Bind the code actually probed, not a later installed revision."""
    model_config = ConfigDict(strict=True, extra="forbid")
    implementation_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    observed_production_sha256_at_start: str
    observed_production_sha256_at_end: str
    events: list[Event]
    public_requests: Literal[0] = 0
    production_writes: Literal[0] = 0
    limit: str


def sha(path: Path) -> str:
    """Hash a fixed existing file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> Any:
    """Load only the saved implementation copy with its installed external dependencies."""
    spec = importlib.util.spec_from_file_location("family_capture_probe", HERE / "research_source_lookup.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def copy_fixture(module: Any, destination: Path) -> None:
    """Copy only fixed local review/intake evidence and required canonical records."""
    for relative in {module.PACKAGE, module.GREELEY_PACKAGE, module.GRID_PACKAGE,
                     module.WELD_PACKAGE, module.WELD_INTAKE, module.SPRINGS_PACKAGE,
                     module.SPRINGS_INTAKE, module.EHS_PACKAGE}:
        shutil.copytree(ROOT / relative, destination / relative)
    for relative in [module.SPRINGS_ACCEPTANCE, module.EHS_ACCEPTANCE]:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    relative = Path("_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, target)
    with (ROOT / relative).open("rb") as handle:
        for line in handle:
            record = json.loads(line)
            if record["record_id"] in [module.SPRINGS_SOURCE_ID, module.EHS_SOURCE_ID]:
                target = destination / record["archive_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / record["archive_path"], target)


def probe(module: Any, root: Path, case: str) -> Event:
    """Perform genuine temporary file swaps around unchanged package checks and real verifiers."""
    started = datetime.now(timezone.utc).isoformat()
    real_run, real_read = module.subprocess.run, Path.read_bytes
    saved: dict[Path, bytes] = {}
    checker_calls, runs = 0, 0
    data_path: Path
    check_name: str
    phase: str
    source = module.EHS_SOURCE_ID
    if case.startswith("ehs"):
        data_path = root / module.EHS_PACKAGE / "SOURCE_QA.json"
        check_name, phase = "_check_ehs_package", "after_second"
    elif case == "springs_fee_native":
        source = module.SPRINGS_SOURCE_ID
        data_path = root / module.SPRINGS_PACKAGE / "SOURCE_QA.json"
        check_name, phase = "_check_springs_package", "after_second"
    elif case == "weld_fee_association":
        source = module.WELD_SOURCE_ID
        data_path = root / module.WELD_PACKAGE / module.WELD_REVIEW
        check_name, phase = "_check_weld_package", "after_first"
    elif case == "greeley_building_context":
        source = module.GREELEY_SOURCE_ID
        data_path = root / module.GREELEY_PACKAGE / module.GREELEY_REVIEW
        check_name, phase = "_check_greeley_package", "after_first"
    elif case in ["impact_fee", "pif_fee"]:
        source = module.IMPACT_SOURCE_ID if case == "impact_fee" else module.PIF_SOURCE_ID
        number, filename, _, _ = module.GRID_SOURCES[source]
        data_path = root / module.GRID_PACKAGE / "historical-packet/baseline" / (
            "EB-PDF-" + number) / filename
        check_name, phase = "_check_grid_package", "after_verifier"
    else:
        source = module.SOURCE_ID
        data_path = root / module.PACKAGE / (
            "access-event.json" if case == "gj_custody" else "SOURCE_QA.json")
        check_name, phase = "_check_package", "after_second" if case == "gj_custody" else "read_aba"
    original_check = getattr(module, check_name)
    data_path.chmod(data_path.stat().st_mode | 0o200)
    saved[data_path] = real_read(data_path)
    injection = "INJECTED UNVERIFIED EVIDENCE"
    expected_marker = injection

    def mutate() -> None:
        """Change only temporary copies; original PDF bytes and production evidence remain intact."""
        nonlocal expected_marker
        data = json.loads(saved[data_path])
        if case == "ehs_fee":
            data["rows"][0]["fee"] = injection
        elif case == "ehs_image":
            data["pages"][1]["image"]["path"] = "../../../../INJECTED_UNVERIFIED_IMAGE.png"
            expected_marker = "INJECTED_UNVERIFIED_IMAGE"
        elif case == "springs_fee_native":
            row = data["fee_rows"][0]
            old = row["fee_as_printed"]["exact_native_text"]
            new = old.replace("258", "000")
            row["fee_as_printed"]["exact_native_text"] = new
            page = data["pages"][row["physical_page"] - 1]
            path = root / module.SPRINGS_PACKAGE / page["native"]["path"]
            path.chmod(path.stat().st_mode | 0o200)
            saved[path] = real_read(path)
            a, b = row["fee_as_printed"]["native_ranges"][0]
            path.write_bytes(saved[path][:a] + new.encode() + saved[path][b:])
            expected_marker = "$000.00"
        elif case == "weld_fee_association":
            first = next(r for r in data["rows"] if r["fee_span"])
            different = next(r for r in data["rows"] if r["fee_span"] and
                             r["fee_span"] != first["fee_span"])
            first["fee_span"] = different["fee_span"]
            data["observations"][0]["statement"] = injection
        elif case == "greeley_building_context":
            data["observations"][0] = injection
        elif case == "impact_fee":
            row = next(r for t in data["tables"] for r in t["rows"] if r["role"] == "fee")
            row["cells"][-1]["text"] = injection
        elif case == "pif_fee":
            data["tables"][0]["rows"][0]["cells"][-1]["display_text"] = injection
        elif case == "gj_custody":
            data["completed_at"] = "2099-01-01T00:00:00Z"
            expected_marker = "2099-01-01"
        else:
            target = data["rows"][0]["fee_span"]
            next(s for p in data["pages"] for s in p["spans"] if s["id"] == target)[
                "text"] = injection
        data_path.write_text(json.dumps(data))

    def restore() -> None:
        """Restore the isolated source set before each check that follows a simulated ABA swap."""
        for path, raw in saved.items():
            path.write_bytes(raw)

    def checked(*args: Any, **kwargs: Any) -> Any:
        """Expose actual checker boundaries without weakening their internal validation."""
        nonlocal checker_calls
        checker_calls += 1
        if phase == "after_verifier" and checker_calls == 2:
            restore()
        value = original_check(*args, **kwargs)
        if (phase == "after_first" and checker_calls == 1 or
                phase == "after_second" and checker_calls == 2):
            mutate()
        return value

    def run(*args: Any, **kwargs: Any) -> Any:
        """Run the genuine pinned offline verifier against restored source bytes."""
        nonlocal runs
        if phase == "after_first":
            restore()
        result = real_run(*args, **kwargs)
        runs += 1
        if phase == "after_verifier":
            mutate()
        return result

    def read(path: Path) -> bytes:
        """Simulate a file change at the vulnerable QA read and immediate restoration."""
        if phase == "read_aba" and path == data_path:
            mutate()
            value = real_read(path)
            restore()
            return value
        return real_read(path)

    setattr(module, check_name, checked)
    module.subprocess.run = run
    Path.read_bytes = read
    result, error, status = None, None, "not_reproduced"
    try:
        output = module.lookup(root, source, list_rows=True)
        result = output.model_dump(mode="json")
        if expected_marker in json.dumps(result) and output.evidence_verified:
            status = "returned_injected_evidence"
    except Exception as exc:
        status, error = "rejected", type(exc).__name__ + ": " + str(exc)
    finally:
        Path.read_bytes = real_read
        module.subprocess.run = real_run
        setattr(module, check_name, original_check)
        restore()
    return Event(case=case, source_id=source, started_at=started,
        completed_at=datetime.now(timezone.utc).isoformat(), status=status,
        verification_calls=runs, checker_calls=checker_calls, error=error, result=result,
        source_files_restored_in_fixture=all(real_read(p) == raw for p, raw in saved.items()))


def main() -> None:
    """Probe exactly seven sources plus one image and one custody boundary, then stop."""
    code_hash = sha(HERE / "research_source_lookup.py")
    before = sha(ROOT / "scripts/research_source_lookup.py")
    module = load()
    original_dns = socket.getaddrinfo
    socket.getaddrinfo = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("No public requests"))
    try:
        with tempfile.TemporaryDirectory(prefix="geode-native-capture-audit-", dir="/private/tmp") as d:
            root = Path(d)
            copy_fixture(module, root)
            events = []
            for case in ["ehs_fee", "ehs_image", "springs_fee_native", "weld_fee_association",
                         "greeley_building_context", "impact_fee", "pif_fee", "gj_custody",
                         "gj_fee_aba"]:
                event = probe(module, root, case)
                events.append(event)
                sys.stdout.write(case + ": " + event.status + "\n")
                sys.stdout.flush()
    finally:
        socket.getaddrinfo = original_dns
    receipt = Receipt(implementation_sha256=code_hash,
        observed_production_sha256_at_start=before,
        observed_production_sha256_at_end=sha(ROOT / "scripts/research_source_lookup.py"),
        events=events, limit="Nine offline temporal-substitution probes over seven fixed sources; "
        "not a full concurrency audit or source-content/currentness review.")
    raw = receipt.model_dump_json(indent=2) + "\n"
    Receipt.model_validate_json(raw)
    with (HERE / "PROBES.json").open("x") as handle:
        handle.write(raw)
    with (HERE / "PROBES.schema.json").open("x") as handle:
        handle.write(json.dumps(Receipt.model_json_schema(), indent=2) + "\n")


if __name__ == "__main__":
    main()
