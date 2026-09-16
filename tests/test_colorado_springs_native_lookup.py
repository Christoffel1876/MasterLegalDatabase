"""Actual accepted-source integrity, context preservation and legacy-output checks."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from scripts import research_source_lookup as lookup

HERE = Path(__file__).absolute().parent
ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / lookup.SPRINGS_PACKAGE


@pytest.fixture
def copied_root(tmp_path: Path) -> Path:
    """Copy only this accepted source package and root acceptance into a disposable root."""
    shutil.copytree(PACKAGE, tmp_path / lookup.SPRINGS_PACKAGE)
    destination = tmp_path / lookup.SPRINGS_ACCEPTANCE
    destination.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / lookup.SPRINGS_ACCEPTANCE, destination)
    shutil.copytree(ROOT / lookup.SPRINGS_INTAKE, tmp_path / lookup.SPRINGS_INTAKE)
    receipt = json.loads((ROOT / lookup.SPRINGS_INTAKE /
                          "prepared-transaction/execution/RECEIPT.json").read_bytes())
    row = next(r for r in receipt["intent"]["records"]
               if r["record_id"] == lookup.SPRINGS_SOURCE_ID)
    raw = tmp_path / row["archive_path"]
    raw.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / row["archive_path"], raw)
    return tmp_path


@pytest.fixture(scope="module")
def all_rows() -> lookup.SpringsLookupResult:
    """Verify the real package and retain all 128 exact rows for read-only output checks."""
    return lookup.lookup(ROOT, lookup.SPRINGS_SOURCE_ID, list_rows=True)


def test_all_128_rows_preserve_source_cells_tables_and_410_lines(
    all_rows: lookup.SpringsLookupResult,
) -> None:
    """Every reviewed native line, cell value and geometry remains represented exactly."""
    qa = json.loads((PACKAGE / "SOURCE_QA.json").read_bytes())
    assert len(all_rows.rows) == 128
    assert [t.model_dump(mode="json") for t in all_rows.tables] == qa["tables"]
    line_ids = []
    for output, original in zip(all_rows.rows, qa["fee_rows"], strict=True):
        observed = output.model_dump(mode="json")
        for key in ["label", "fee_as_printed"]:
            part = getattr(output, key)
            native = Path(part.native_file.path).read_bytes()
            assert b"".join(native[a:b] for a, b in part.native_ranges) == (
                part.exact_native_text.encode()
            )
            line_ids.extend(part.line_ids)
            for extra in ["page", "native_file", "page_image", "text_sha256", "offset_basis"]:
                observed[key].pop(extra)
        assert observed == original
    for output, original in zip(all_rows.context, qa["blocks"], strict=True):
        observed = output.model_dump(mode="json")
        for part in observed["parts"]:
            line_ids.extend(part["line_ids"])
            for extra in ["native_file", "page_image", "text_sha256", "offset_basis"]:
                part.pop(extra)
        assert observed == original
    assert len(line_ids) == len(set(line_ids)) == 410
    assert sum(p["native"]["size_bytes"] for p in qa["pages"]) == 14423
    assert all_rows.source.historical_review_source_id == "SD014-02"
    assert all_rows.source.source_id == "colorado-springs-construction-fees-atlas-directed"
    assert all_rows.source.canonical_intake_verified
    assert all_rows.source.intake_received_at.isoformat() == "2026-09-12T23:56:16.492216+00:00"
    assert all_rows.source.canonical_original.sha256 == all_rows.source.pdf.sha256
    assert len(all_rows.source.intake_evidence) == 6
    assert all_rows.source.authority_id == "CO-MUNICIPAL-COLORADO_SPRINGS"
    assert all_rows.source.response_finished_at.isoformat() == "2026-09-12T23:10:47.380038+00:00"
    assert all_rows.adoption_date is None and all_rows.effective_date is None
    assert all_rows.legal_currentness == "not_verified" and all_rows.answer_safe is False


def test_required_global_conditions_and_complete_definitions(
    all_rows: lookup.SpringsLookupResult,
) -> None:
    """Source qualifications are not lost at page breaks or converted into unconditional fees."""
    blocks = {b.block_id: b for b in all_rows.context}
    assert all_rows.global_context_ids == lookup.SPRINGS_GLOBAL
    assert all_rows.technology_fee.label.exact_native_text == (
        "Technology Fee – assessed on all permits \n"
    )
    assert all_rows.technology_fee.fee_as_printed.exact_native_text == "$25.00 \n"
    assert "Unless otherwise noted" in blocks["GENERAL-PLAN-REVIEW"].parts[0].exact_native_text
    assert "two plan reviews" in blocks["GENERAL-PLAN-REVIEW"].parts[0].exact_native_text
    assert "subsequent reviews, trips, and re-inspections" in (
        blocks["GENERAL-PLAN-REVIEW"].parts[0].exact_native_text
    )
    assert blocks["IMPLEMENTATION"].parts[0].exact_native_text == (
        "Implementation: Fees shall be assessed upon the plan approval date. \n"
    )
    assert "high pile storage and hazardous materials" in (
        blocks["OTHER-SCHEDULE"].parts[0].exact_native_text
    )
    definition = blocks["DEF-REINSPECTION"]
    assert [p.page for p in definition.parts] == [6, 7]
    assert definition.parts[1].exact_native_text == (
        "inspection, or a system that has not been pre-tested shall also require a "
        "re-inspection. \n"
    )
    collection = blocks["DEF-CONSTRUCTION-PLAN-CHECK"].parts[0].exact_native_text
    assert "Pikes Peak Regional Building Department (PPRBD)" in collection
    assert "If a full review and" in collection and "will be deducted" in collection
    assert "does not reassign the issuing authority" in all_rows.source.collector_qualification
    assert len([b for b in blocks.values() if b.kind == "definition"]) == 13
    assert len([b for b in blocks.values() if b.kind == "table_note"]) == 3


def test_printed_rate_anomalies_are_not_repaired(all_rows: lookup.SpringsLookupResult) -> None:
    """Preserve missing currency, $336, source tiers and minimum text without calculations."""
    rows = {r.row_id: r for r in all_rows.rows}
    for key in ["P3-CONSTRUCTION-35", "P4-CONSTRUCTION-01"]:
        assert rows[key].fee_as_printed.exact_native_text == "0.04/sq. ft.  \n"
    assert "minimum $2,000" in rows["P4-CONSTRUCTION-01"].label.exact_native_text
    assert rows["P4-SPRINKLER-05"].fee_as_printed.exact_native_text == "$336.00 \n"
    assert "greater than 300" in rows["P4-SPRINKLER-05"].label.exact_native_text
    assert any("50, 000" in r.label.exact_native_text for r in all_rows.rows)
    assert any("R2 " in r.label.exact_native_text for r in all_rows.rows)


@pytest.mark.parametrize("query,expected", [
    ("0.04", ["P3-CONSTRUCTION-35", "P4-CONSTRUCTION-01"]),
    ("$336.00", ["P4-SPRINKLER-05"]),
    ("Technology Fee", ["P4-MISC-01"]),
])
def test_targeted_exact_source_query(query: str, expected: list[str]) -> None:
    """Rates and source labels retrieve exactly their recorded rows and mandatory context."""
    result = lookup.lookup(ROOT, lookup.SPRINGS_SOURCE_ID, query)
    assert [r.row_id for r in result.rows] == expected
    assert result.technology_fee is not None and len(result.context) == 80


@pytest.mark.parametrize("query", [
    "fictional teleporter permit", "0 square feet", "000 square feet",
])
def test_no_match_cannot_establish_absence(query: str) -> None:
    """Missing services remain no-match in this one snapshot with all scope qualifications."""
    result = lookup.lookup(ROOT, lookup.SPRINGS_SOURCE_ID, query)
    assert result.status == "no_matching_row" and not result.rows
    assert "does not establish free" in result.boundary
    assert len(result.context) == 80 and result.technology_fee is not None


def test_context_only_does_not_assign_fee() -> None:
    """The implementation statement is retrievable without assigning it a computed fee."""
    result = lookup.lookup(ROOT, lookup.SPRINGS_SOURCE_ID, "Fees shall be assessed")
    assert result.status == "matched_context_only" and result.rows == []
    assert result.matched_context_ids == ["IMPLEMENTATION"]


@pytest.mark.parametrize("query", [
    "current fee", "What should I pay?", "calculate $336", "does it apply",
])
def test_refusal_before_any_source_read(query: str, tmp_path: Path) -> None:
    """Legal or arithmetic questions refuse before any package or intake access."""
    result = lookup.lookup(tmp_path, lookup.SPRINGS_SOURCE_ID, query)
    assert result.status == "refused_current_law" and not result.evidence_verified
    assert result.source is None and not result.rows
    assert "Request refused" in lookup.render_markdown(result)


@pytest.mark.parametrize("target", [
    "source/original.pdf", "SOURCE_QA.json", "SOURCE_QA.schema.json", "FINAL_MANIFEST.json",
    "FINAL_MANIFEST.schema.json", "validate_review.py", "review_models.py", "row_map.py",
    "native/page-0004.txt", "images/page-4.png", "custody/result.json",
])
def test_altered_source_or_code_never_executes(
    copied_root: Path, monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    """Altered bytes fail the acceptance/package pins before executing a verifier."""
    path = copied_root / lookup.SPRINGS_PACKAGE / target
    path.write_bytes(path.read_bytes() + b"corrupt")
    calls = []
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: calls.append(a))
    with pytest.raises(ValueError):
        lookup.lookup(copied_root, lookup.SPRINGS_SOURCE_ID, "sprinkler")
    assert not calls


@pytest.mark.parametrize("attack", [
    "extra_file", "empty_directory", "symlink", "ancestor", "acceptance",
])
def test_closed_paths_and_acceptance(copied_root: Path, attack: str) -> None:
    """Reject new package members, symlinked evidence and a changed acceptance receipt."""
    p = copied_root / lookup.SPRINGS_PACKAGE
    if attack == "extra_file":
        (p / "unlisted.txt").write_text("x")
    elif attack == "empty_directory":
        (p / "unlisted").mkdir()
    elif attack == "symlink":
        f = p / "source/original.pdf"
        f.unlink()
        f.symlink_to(PACKAGE / "source/original.pdf")
    elif attack == "ancestor":
        shutil.rmtree(p / "images")
        (p / "images").symlink_to(PACKAGE / "images", target_is_directory=True)
    else:
        (copied_root / lookup.SPRINGS_ACCEPTANCE).write_text("{}")
    with pytest.raises(ValueError):
        lookup.lookup(copied_root, lookup.SPRINGS_SOURCE_ID, "sprinkler")


def test_resealed_wrong_fee_hits_existing_source_verifier(
    copied_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even fixture-resealed review bytes cannot replace the distinctive source $336 amount."""
    package = copied_root / lookup.SPRINGS_PACKAGE
    path = package / "SOURCE_QA.json"
    qa = json.loads(path.read_bytes())
    row = next(r for r in qa["fee_rows"] if r["row_id"] == "P4-SPRINKLER-05")
    row["fee_as_printed"]["exact_native_text"] = "$344.00 \n"
    path.write_text(json.dumps(qa), encoding="utf-8")
    manifest = json.loads((package / "FINAL_MANIFEST.json").read_bytes())
    for ref in manifest["files"]:
        if ref["path"] == "SOURCE_QA.json":
            ref.update(sha256=lookup._digest(path), size_bytes=path.stat().st_size)
    (package / "FINAL_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    pins = dict(lookup.SPRINGS_PINS)
    pins.update({name: lookup._digest(package / name)
                 for name in ["SOURCE_QA.json", "FINAL_MANIFEST.json"]})
    monkeypatch.setattr(lookup, "SPRINGS_PINS", pins)
    with pytest.raises(ValueError, match="source-package verification"):
        lookup.lookup(copied_root, lookup.SPRINGS_SOURCE_ID, "$344")


@pytest.mark.parametrize("attack", ["hash", "range", "line_page", "bbox", "pixels", "count"])
def test_native_part_rejects_false_bindings(
    all_rows: lookup.SpringsLookupResult, attack: str,
) -> None:
    """Serialized native spans reject altered text, coordinates and page identities."""
    value = all_rows.rows[0].label.model_dump(mode="json")
    if attack == "hash":
        value["text_sha256"] = "0" * 64
    elif attack == "range":
        value["native_ranges"][0][1] += 1
    elif attack == "line_page":
        value["line_ids"][0] = "P7-L010"
    elif attack == "bbox":
        value["pdf_bboxes"][0][2] = 700.0
    elif attack == "pixels":
        value["pixel_bboxes"][0][2] = 1800
    else:
        value["pixel_bboxes"] = []
    with pytest.raises(ValidationError):
        lookup.SpringsCell.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("attack", ["global", "technology", "definition", "table_note", "page7",
                                  "table", "duplicate", "source", "row_context", "status"])
def test_complete_output_context_is_required(
    all_rows: lookup.SpringsLookupResult, attack: str,
) -> None:
    """A lost qualification, continuation or table relationship cannot be called verified."""
    value = all_rows.model_dump(mode="json")
    if attack == "global":
        value["global_context_ids"].pop()
    elif attack == "technology":
        value["technology_fee"] = None
    elif attack in ["definition", "table_note"]:
        value["context"].pop(next(i for i, b in enumerate(value["context"])
                                  if b["kind"] == attack))
    elif attack == "page7":
        next(b for b in value["context"] if b["block_id"] == "DEF-REINSPECTION")["parts"].pop()
    elif attack == "table":
        value["rows"][0]["table_id"] = "sprinkler"
    elif attack == "duplicate":
        value["rows"][1] = copy.deepcopy(value["rows"][0])
    elif attack == "source":
        value["source"] = None
    elif attack == "row_context":
        value["rows"][0]["definition_ids"] = ["INVENTED"]
    else:
        value["status"] = "no_matching_row"
    with pytest.raises(ValidationError):
        lookup.SpringsLookupResult.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("attack", ["cell_role", "row_page", "global"])
def test_row_associations(all_rows: lookup.SpringsLookupResult, attack: str) -> None:
    """Cell roles, physical pages and global qualifications cannot detach from their row."""
    value = all_rows.rows[0].model_dump(mode="json")
    if attack == "cell_role":
        value["label"]["role"] = "fee_as_printed"
    elif attack == "row_page":
        value["physical_page"] = 3
    else:
        value["global_context_ids"] = []
    with pytest.raises(ValidationError):
        lookup.SpringsRow.model_validate_json(json.dumps(value))


def test_isolation_timeout_and_bad_verifier_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    """The pinned verifier runs without credentials or optimization and rejects false success."""
    calls = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        """Capture invocation and supply a deliberately inadequate success receipt."""
        calls.append((command, kwargs))
        return SimpleNamespace(stdout='{"status":"passed"}')

    monkeypatch.setattr(lookup.subprocess, "run", run)
    with pytest.raises(ValueError, match="verification failed"):
        lookup.lookup(ROOT, lookup.SPRINGS_SOURCE_ID, "sprinkler")
    command, kwargs = calls[0]
    assert command[1:3] == ["-I", "-B"] and "-O" not in command
    assert kwargs["timeout"] == 90 and set(kwargs["env"]) == {"PATH", "PYTHONNOUSERSITE"}


@pytest.mark.parametrize("source", [
    lookup.SOURCE_ID, lookup.GREELEY_SOURCE_ID, lookup.WELD_SOURCE_ID,
    lookup.IMPACT_SOURCE_ID, lookup.PIF_SOURCE_ID,
])
def test_five_existing_sources_return_identical_json_and_markdown(source: str) -> None:
    """Actual all-row results are byte-for-byte identical to the untouched baseline adapter."""
    path = ROOT / "tests/fixtures/research_source_lookup_before_springs.json"
    expected = json.loads(path.read_bytes())
    result = lookup.lookup(ROOT, source, list_rows=True)
    for format_name, value in [("json", result.model_dump_json()),
                               ("markdown", lookup.render_markdown(result))]:
        normalized = value.replace(str(ROOT), "__REPOSITORY__")
        assert hashlib.sha256(normalized.encode()).hexdigest() == expected[source][format_name]



def test_native_lookup_cli_and_markdown_preserve_context(
    capsys: pytest.CaptureFixture[str], tmp_path: Path,
) -> None:
    """The installed-style interface keeps mandatory context readable and refuses current law."""
    base = ["--root", str(ROOT), "--source-id", lookup.SPRINGS_SOURCE_ID]
    assert lookup.main(base + ["--query", "0.04", "--format", "json"]) == 0
    assert len(json.loads(capsys.readouterr().out)["rows"]) == 2
    assert lookup.main(base + ["--query", "Technology"]) == 0
    rendered = capsys.readouterr().out
    assert "GENERAL-PLAN-REVIEW" in rendered and "IMPLEMENTATION" in rendered
    assert "OTHER-SCHEDULE" in rendered and "$25.00" in rendered
    assert "Physical page 6" in rendered and "Physical page 7" in rendered
    assert "PPRBD" in rendered
    assert "Canonical intake received: 2026-09-12T23:56:16.492216+00:00" in rendered
    command = [sys.executable, "-I", "-B", str(ROOT / "scripts/research_source_lookup.py"),
               "--root", str(tmp_path), "--source-id", lookup.SPRINGS_SOURCE_ID,
               "--query", "current fees", "--format", "json"]
    result = subprocess.run(command, capture_output=True, text=True, cwd=tmp_path, check=False)
    assert result.returncode == 2 and json.loads(result.stdout)["status"] == "refused_current_law"


def test_untrusted_query_not_rendered_as_markup() -> None:
    """An unmatched hostile query does not become active Markdown or an invented source row."""
    result = lookup.lookup(ROOT, lookup.SPRINGS_SOURCE_ID, '<img src=x onerror=alert(1)>')
    rendered = lookup.render_markdown(result)
    assert "<img" not in rendered and not result.rows
    assert "No matching fee row" in rendered


@pytest.mark.parametrize("name", [
    "INVENTORY.json", "ACCEPTANCE.json", "validate_package.py",
    "prepared-transaction/execution/RECEIPT.json",
    "prepared-transaction/execution/INTENT.json",
    "prepared-transaction/evidence/preparation/source-provenance.jsonl",
])
def test_actual_intake_evidence_is_checked_before_execution(
    copied_root: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    """Changed intake records or tools cannot execute or imply successful custody."""
    path = copied_root / lookup.SPRINGS_INTAKE / name
    path.write_bytes(path.read_bytes() + b"tamper")
    calls = []
    monkeypatch.setattr(lookup.subprocess, "run", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError):
        lookup._load_springs_intake(copied_root, {})
    assert not calls


@pytest.mark.parametrize("attack", ["missing", "changed", "symlink"])
def test_present_canonical_original_must_match_received_bytes(
    copied_root: Path, attack: str,
) -> None:
    """The completed receipt alone does not certify an absent or changed current original."""
    record = json.loads((copied_root / lookup.SPRINGS_INTAKE /
                         "prepared-transaction/execution/RECEIPT.json").read_bytes())
    selected = next(r for r in record["intent"]["records"]
                    if r["record_id"] == lookup.SPRINGS_SOURCE_ID)
    path = copied_root / selected["archive_path"]
    if attack == "missing":
        path.unlink()
    elif attack == "changed":
        path.write_bytes(path.read_bytes() + b"tamper")
    else:
        path.unlink()
        path.symlink_to(ROOT / selected["archive_path"])
    with pytest.raises(ValueError):
        lookup.lookup(copied_root, lookup.SPRINGS_SOURCE_ID, "Technology")


@pytest.mark.parametrize("attack", ["unknown_directory", "staging_file", "staging_directory"])
def test_completed_intake_allows_only_exact_empty_historical_staging(
    copied_root: Path, attack: str,
) -> None:
    """An optional empty transaction workspace cannot hide extra evidence or code."""
    package = copied_root / lookup.SPRINGS_INTAKE
    staging = package / "prepared-transaction/execution/.staging"
    staging.mkdir(exist_ok=True)
    original = lookup._check_springs_intake(copied_root)
    staging.rmdir()
    assert lookup._check_springs_intake(copied_root) == original
    staging.mkdir()
    if attack == "unknown_directory":
        (package / "unlisted").mkdir()
    elif attack == "staging_file":
        (staging / "unlisted.py").write_text("raise RuntimeError('untrusted')")
    else:
        (staging / "unlisted").mkdir()
    with pytest.raises(ValueError, match="closed intake inventory"):
        lookup._check_springs_intake(copied_root)


def test_intake_verifier_uses_isolation_and_rejects_false_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The assert-based portable intake verifier runs without optimization or credentials."""
    calls = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        """Return a false success marker from an otherwise recorded invocation."""
        calls.append((command, kwargs))
        return SimpleNamespace(stdout='{"status":"passed"}')

    monkeypatch.setattr(lookup.subprocess, "run", run)
    with pytest.raises(ValueError, match="completed-intake verification failed"):
        lookup._load_springs_intake(ROOT, {})
    command, kwargs = calls[0]
    assert command[1:3] == ["-I", "-B"] and "-O" not in command
    assert kwargs["timeout"] == 45 and set(kwargs["env"]) == {"PATH", "PYTHONNOUSERSITE"}


@pytest.mark.parametrize("field,value", [
    ("intake_received_at", "2026-09-12T20:00:00Z"),
    ("canonical_intake_verified", False),
])
def test_source_result_cannot_falsify_intake_chronology(
    all_rows: lookup.SpringsLookupResult, field: str, value: object,
) -> None:
    """An output cannot convert the verified later receipt into an earlier acquisition."""
    data = all_rows.source.model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        lookup.SpringsSourceBinding.model_validate_json(json.dumps(data))
