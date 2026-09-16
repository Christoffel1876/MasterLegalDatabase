"""Actual source and temporal-substitution regressions for captured native lookup evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import BaseModel, ConfigDict

from scripts import research_source_lookup as lookup

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/native_lookup_capture/nine-native-sources"

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



@pytest.fixture
def copied(tmp_path: Path) -> Path:
    """Only temporary evidence copies are writable in mutation cases."""
    copy_fixture(lookup, tmp_path)
    return tmp_path


@pytest.mark.parametrize("source", [lookup.SOURCE_ID, lookup.GREELEY_SOURCE_ID,
    lookup.WELD_SOURCE_ID, *lookup.GRID_SOURCES, lookup.SPRINGS_SOURCE_ID,
    lookup.EHS_SOURCE_ID, *lookup.DP_SOURCES])
def test_nine_normal_source_outputs_preserved(source: str) -> None:
    """Complete JSON and Markdown retain their exact public contracts and all qualifications."""
    result = lookup.lookup(ROOT, source, list_rows=True)
    for suffix, text in [("json", result.model_dump_json(indent=2) + "\n"),
                          ("md", lookup.render_markdown(result))]:
        assert text.replace(str(ROOT), "__REPOSITORY__") == (
            FIXTURES / (source + "." + suffix)).read_text()


@pytest.mark.parametrize("case", ["ehs_fee", "ehs_image", "springs_fee_native",
    "weld_fee_association", "greeley_building_context", "impact_fee", "pif_fee",
    "gj_custody", "gj_fee_aba"])
def test_actual_former_exploits_cannot_return_injected_evidence(copied: Path, case: str) -> None:
    """Replay the independently preserved failures with actual unchanged source verifiers."""
    result = probe(lookup, copied, case)
    assert result.status in {"rejected", "not_reproduced"}, result.model_dump_json()
    assert result.source_files_restored_in_fixture
    if result.status == "rejected":
        assert result.error.startswith("ValueError:"), result.error
    else:
        assert result.result["evidence_verified"] is True
        assert "INJECTED" not in json.dumps(result.result)
        assert "2099-01-01" not in json.dumps(result.result)


@pytest.mark.parametrize("family,source,relative", [
    ("gj", lookup.SOURCE_ID, lookup.PACKAGE / "access-event.json"),
    ("gj", lookup.SOURCE_ID, lookup.PACKAGE / "SOURCE_QA.json"),
    ("greeley", lookup.GREELEY_SOURCE_ID, lookup.GREELEY_PACKAGE / lookup.GREELEY_REVIEW),
    ("greeley", lookup.GREELEY_SOURCE_ID, lookup.GREELEY_PACKAGE / "packet/manifest.json"),
    ("weld", lookup.WELD_SOURCE_ID, lookup.WELD_PACKAGE / lookup.WELD_REVIEW),
    ("weld", lookup.WELD_SOURCE_ID, lookup.WELD_INTAKE / "intake-receipt.json"),
    ("grid", lookup.IMPACT_SOURCE_ID, lookup.GRID_PACKAGE /
     "historical-packet/baseline/EB-PDF-016/SOURCE_QA.json"),
    ("grid", lookup.PIF_SOURCE_ID, lookup.GRID_PACKAGE /
     "historical-packet/baseline/EB-PDF-017/SOURCE_REVIEW.json"),
    ("springs", lookup.SPRINGS_SOURCE_ID, lookup.SPRINGS_PACKAGE / "SOURCE_QA.json"),
    ("springs", lookup.SPRINGS_SOURCE_ID, lookup.SPRINGS_PACKAGE / "native/page-0002.txt"),
    ("springs_intake", lookup.SPRINGS_SOURCE_ID, lookup.SPRINGS_INTAKE /
     "prepared-transaction/execution/RECEIPT.json"),
    ("ehs", lookup.EHS_SOURCE_ID, lookup.EHS_PACKAGE / "SOURCE_QA.json"),
    ("ehs", lookup.EHS_SOURCE_ID, lookup.EHS_ACCEPTANCE),
])
def test_after_final_capture_swaps_cannot_change_output(
    copied: Path, family: str, source: str, relative: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later disk replacement cannot substitute evidence after the exact verified capture."""
    real = lookup._capture_existing
    calls = 0
    target = copied / relative
    original = target.read_bytes()
    target.chmod(target.stat().st_mode | 0o200)

    def capture(root: Path, name: str) -> dict[str, bytes]:
        """Change only the temporary path after returning a genuine checked buffer."""
        nonlocal calls
        data = real(root, name)
        if name == family:
            calls += 1
            if calls == 2:
                target.write_bytes(b"INJECTED UNVERIFIED EVIDENCE")
        return data

    monkeypatch.setattr(lookup, "_capture_existing", capture)
    result = lookup.lookup(copied, source, list_rows=True)
    assert calls == 2 and target.read_bytes() != original
    assert result.model_dump_json(indent=2).replace(str(copied), "__REPOSITORY__") + "\n" == (
        FIXTURES / (source + ".json")).read_text()
    assert lookup.render_markdown(result).replace(str(copied), "__REPOSITORY__") == (
        FIXTURES / (source + ".md")).read_text()


def test_capture_unknown_family_refused(tmp_path: Path) -> None:
    """No dynamic source family or discovery is admitted."""
    with pytest.raises(ValueError, match="Unsupported captured"):
        lookup._capture_existing(tmp_path, "unknown")


@pytest.mark.parametrize("case", ["hash", "size", "escape", "symlink", "oversize"])
def test_captured_asset_and_buffer_guards(tmp_path: Path, case: str) -> None:
    """Every returned asset binds exact captured bytes with finite confined local reads."""
    path = tmp_path / "file"
    path.write_bytes(b"source")
    ref = {"path": "file", "sha256": hashlib.sha256(b"source").hexdigest(), "size_bytes": 6}
    captured = {str(path): b"source"}
    if case == "hash":
        ref["sha256"] = "0" * 64
    elif case == "size":
        ref["size_bytes"] = 7
    elif case == "escape":
        ref["path"] = "../file"
    elif case == "symlink":
        (tmp_path / "link").symlink_to(path)
        ref["path"] = "link"
    else:
        with pytest.raises(ValueError, match="Captured source bytes differ"):
            lookup._capture_source_file(tmp_path, path, ref["sha256"], 5)
        return
    with pytest.raises(ValueError):
        lookup._captured_reference(captured, tmp_path, ref)
