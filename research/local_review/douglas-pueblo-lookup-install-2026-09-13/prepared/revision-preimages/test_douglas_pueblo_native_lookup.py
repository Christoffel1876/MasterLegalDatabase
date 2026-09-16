"""Exact Douglas County and City of Pueblo source-only lookup regression checks."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts import research_source_lookup as lookup

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/douglas_pueblo_native_lookup/seven-native-sources"


@pytest.fixture(scope="module")
def complete() -> dict[str, Any]:
    """Verify both actual closed packages and retain complete typed results for semantic cases."""
    return {source: lookup.lookup(ROOT, source, list_rows=True) for source in lookup.DP_SOURCES}


@pytest.fixture
def copied(tmp_path: Path) -> Path:
    """Copy only the two immutable packages and exact inputs required by the new adapter."""
    for config in lookup.DP_SOURCES.values():
        relative = Path("research/local_review") / config["folder"]
        shutil.copytree(ROOT / relative, tmp_path / relative)
        acceptance = (Path("docs/audits/FOUR_HOUR_RUN_2026-09-12") /
                      config["acceptance"] / "ACCEPTANCE.json")
        (tmp_path / acceptance).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / acceptance, tmp_path / acceptance)
    relatives = ["execution/RECEIPT.json", "execution/INTENT.json", "execution/records.jsonl",
                 "evidence/preparation/source-provenance.jsonl"]
    for source, config in lookup.DP_SOURCES.items():
        relatives.append("evidence/preparation/custody/" + source + "/" +
                         config["event"] + "/event.json")
    for name in relatives:
        target = tmp_path / lookup.DP_INTAKE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / lookup.DP_INTAKE / name, target)
    manifest = Path("_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl")
    (tmp_path / manifest).parent.mkdir(parents=True, exist_ok=True)
    with (ROOT / manifest).open("rb") as handle, (tmp_path / manifest).open("wb") as output:
        for line in handle:
            record = json.loads(line)
            if record["record_id"] in lookup.DP_SOURCES:
                output.write(line)
                target = tmp_path / record["archive_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / record["archive_path"], target)
    return tmp_path


@pytest.mark.parametrize("source", [
    lookup.SOURCE_ID, lookup.GREELEY_SOURCE_ID, lookup.WELD_SOURCE_ID,
    *lookup.GRID_SOURCES, lookup.SPRINGS_SOURCE_ID, lookup.EHS_SOURCE_ID,
])
def test_existing_seven_outputs_unchanged(source: str) -> None:
    """Existing complete JSON and Markdown retain every byte except normalized root prefix."""
    result = lookup.lookup(ROOT, source, list_rows=True)
    for extension, text in [("json", result.model_dump_json(indent=2) + "\n"),
                            ("md", lookup.render_markdown(result))]:
        assert text.replace(str(ROOT), "__REPOSITORY__") == (
            FIXTURES / f"{source}.{extension}").read_text()


def test_douglas_all_cells_context_and_dates(complete: dict[str, Any]) -> None:
    """County issuer, state caption, blank penalties and awkward source note remain distinct."""
    result = complete[lookup.DOUGLAS_SOURCE_ID]
    assert len(result.rows) == 44 and len(result.context) == 7
    assert [sum(r.table == table for r in result.rows) for table in ["county", "state"]] == [27, 17]
    assert sum(len(r.cells) for r in result.rows) == 220
    blanks = [r.row_id for r in result.rows if r.cells[-1].native_text is None]
    assert blanks == ["STATE-16", "STATE-17"]
    assert sum(len(c.native_spans) for r in result.rows for c in r.cells) == 218
    contexts = {c.context_id: c for c in result.context}
    assert contexts["WORDMARK"].native_status == "image_only_wordmark"
    assert contexts["WORDMARK"].native_spans == []
    assert "November" in contexts["COUNTY-CAPTION"].text
    assert "September" in contexts["STATE-CAPTION"].text
    assert "$43" in contexts["STATE-RETAIL-NOTE"].text
    assert "$55" in contexts["STATE-RETAIL-NOTE"].text
    assert "2025" in contexts["STATE-RETAIL-NOTE"].text
    assert result.source.authority_id == "CO-COUNTY-DOUGLAS"
    assert result.source.native_bytes == 4923
    assert result.source.intake_received_at.isoformat() == "2026-09-13T01:38:28.176844+00:00"
    assert result.source.http_response_completed_at.isoformat() == (
        "2026-09-12T23:34:39.577252+00:00")
    assert result.adoption_date is result.effective_date is None
    assert result.legal_currentness == "not_verified" and not result.answer_safe
    assert "Intial" in lookup.render_markdown(result)


def test_pueblo_all_physical_and_nested_associations(complete: dict[str, Any]) -> None:
    """Physical rows keep 15 paired subcategories and28 bullets without counting87 fees."""
    result = complete[lookup.PUEBLO_SOURCE_ID]
    assert len(result.rows) == 44 and len(result.context) == 4
    assert [sum(r.physical_page == page for r in result.rows)
            for page in range(1, 5)] == [13, 14, 14, 3]
    nested = [n for r in result.rows for n in r.nested]
    assert len(nested) == 43
    assert sum(n.kind == "paired_subcategory" for n in nested) == 15
    assert sum(n.kind == "fee_bullet" for n in nested) == 28
    assert all("2-13-26" in c.text and "Applications" in c.text for c in result.context)
    assert result.source.authority_id == "CO-MUNICIPAL-PUEBLO"
    assert result.source.review_alias == "city-pueblo-planning-fees"
    assert result.source.http_response_completed_at.isoformat() == (
        "2026-09-13T00:23:02.695819+00:00")
    rows = {r.row_id: r for r in result.rows}
    assert rows["P1-11"].cells[1].native_text.count("nor site improvements") == 2
    assert "$150_+" in rows["P3-04"].cells[1].displayed_text
    assert "$150 +" in rows["P3-04"].cells[1].native_text
    assert all(n.inherited_note_line_ids for n in rows["P4-01"].nested)
    assert any("encoded underscore" in a.limitation for a in result.annotations)
    assert all(not r.nested or r.table == "city_applications" for r in result.rows)


@pytest.mark.parametrize("source", list(lookup.DP_SOURCES))
def test_exact_native_spans_and_page_identity(complete: dict[str, Any], source: str) -> None:
    """Every returned substring replays exactly against the correct retained native page."""
    result = complete[source]
    spans = [s for r in result.rows for c in r.cells for s in c.native_spans]
    spans += [s for c in result.context for s in c.native_spans]
    for span in spans:
        data = Path(span.native.path).read_bytes()[span.start:span.end]
        assert data == span.text.encode() and hashlib.sha256(data).hexdigest() == span.sha256
        assert Path(span.image.path).is_file()
    assert result.source.source.sha256 == result.source.canonical_original.sha256
    assert result.source.http_response_completed_at < result.source.intake_received_at


@pytest.mark.parametrize("source,phrase,rows,context_status", [
    (lookup.DOUGLAS_SOURCE_ID, "Penalty Assessment", ["STATE-16", "STATE-17"], "matched"),
    (lookup.DOUGLAS_SOURCE_ID, "transmitted", [], "matched_context_only"),
    (lookup.DOUGLAS_SOURCE_ID, "November", [], "matched_context_only"),
    (lookup.DOUGLAS_SOURCE_ID, "nonexistent-service-xyz", [], "no_matching_row"),
    (lookup.PUEBLO_SOURCE_ID, "Tenant Finish", ["P1-11"], "matched"),
    (lookup.PUEBLO_SOURCE_ID, "fees per plat", ["P4-01"], "matched"),
    (lookup.PUEBLO_SOURCE_ID, "2-13-26", [], "matched_context_only"),
    (lookup.PUEBLO_SOURCE_ID, "nonexistent-service-xyz", [], "no_matching_row"),
])
def test_literal_queries_keep_all_context(
    source: str, phrase: str, rows: list[str], context_status: str,
) -> None:
    """A nested/row match returns the whole physical row and every source context."""
    result = lookup.lookup(ROOT, source, phrase)
    assert result.status == context_status
    assert [r.row_id for r in result.rows] == rows
    assert len(result.context) == lookup.DP_SOURCES[source]["context_count"]
    assert result.source and result.evidence_verified
    text = lookup.render_markdown(result)
    assert "legal_currentness: not_verified" in text
    assert "Source-review qualifications" in text and "Printed source date claims" in text
    if source == lookup.DOUGLAS_SOURCE_ID:
        assert "$43" in text and "$55" in text
        if rows == ["STATE-16", "STATE-17"]:
            assert text.count("blank source cell; not zero") == 2
    else:
        assert "nor site improvements" in text and "not certified as an encoded underscore" in text
        if phrase == "fees per plat":
            assert len(result.rows[0].nested) == 3


@pytest.mark.parametrize("source", list(lookup.DP_SOURCES))
@pytest.mark.parametrize("phrase,mode", [("today", "source"), ("fee", "current-law"),
                                          ("What fee applies?", "source")])
def test_current_law_refusal_without_evidence(source: str, phrase: str, mode: str) -> None:
    """Refusal happens before nonexistent root evidence can be exposed."""
    result = lookup.lookup(Path("/not/a/repository"), source, phrase, mode=mode)
    assert result.status == "refused_current_law"
    assert not result.evidence_verified and result.source is None and not result.rows
    assert "Request refused" in lookup.render_markdown(result)


@pytest.mark.parametrize("source", [
    "pueblo-county-fees", "douglas-state-legislation", "SD-unknown"])
def test_unsupported_sibling_authorities(source: str) -> None:
    """Neither city/county similarity nor a state caption creates another supported source."""
    with pytest.raises(ValueError, match="Unsupported source"):
        lookup.lookup(ROOT, source, list_rows=True)


@pytest.mark.parametrize("source", list(lookup.DP_SOURCES))
@pytest.mark.parametrize("case", ["qa", "schema", "native", "pdf", "verifier", "extra_file",
                                  "extra_dir", "symlink", "acceptance"])
def test_fixed_evidence_tampering_fails_before_zero_results(
    copied: Path, source: str, case: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even an empty query result requires unchanged complete source and acceptance evidence."""
    config = lookup.DP_SOURCES[source]
    package = copied / "research/local_review" / config["folder"]
    targets = {"qa": "SOURCE_QA.json", "schema": "SOURCE_QA.schema.json", "pdf": "original.pdf",
               "verifier": config["verifier"], "native": "candidate-native.txt" if
               source == lookup.DOUGLAS_SOURCE_ID else "native/page-0001.txt"}
    if case in targets:
        path = package / targets[case]
        path.write_bytes(path.read_bytes() + b" ")
    elif case == "extra_file":
        (package / "extra.txt").write_text("unlisted")
    elif case == "extra_dir":
        (package / "extra").mkdir()
    elif case == "symlink":
        (package / "linked").symlink_to(package / "original.pdf")
    else:
        path = (copied / "docs/audits/FOUR_HOUR_RUN_2026-09-12" /
                config["acceptance"] / "ACCEPTANCE.json")
        path.write_bytes(path.read_bytes() + b" ")
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: pytest.fail("Verifier ran"))
    with pytest.raises(ValueError):
        lookup.lookup(copied, source, "no-match-xyz")


@pytest.mark.parametrize("case", ["receipt", "intent", "records", "provenance", "event", "original",
                                  "duplicate_record", "missing_record", "altered_record"])
def test_intake_custody_cannot_be_detached(copied: Path, case: str) -> None:
    """Raw identity, witnessed HTTP and actual repository receipt remain required."""
    source = lookup.DOUGLAS_SOURCE_ID
    tx = copied / lookup.DP_INTAKE
    names = {"receipt": "execution/RECEIPT.json", "intent": "execution/INTENT.json",
             "provenance": "evidence/preparation/source-provenance.jsonl",
             "records": "execution/records.jsonl",
             "event": "evidence/preparation/custody/" + source + "/E017/event.json"}
    if case in names:
        path = tx / names[case]
        path.write_bytes(path.read_bytes() + b" ")
    else:
        manifest = copied / "_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl"
        with manifest.open("rb") as handle:
            lines = list(handle)
        record = json.loads(lines[0])
        if case == "original":
            (copied / record["archive_path"]).write_bytes(b"changed")
        elif case == "duplicate_record":
            with manifest.open("ab") as handle:
                handle.write(lines[0])
        elif case == "missing_record":
            manifest.write_bytes(lines[1])
        else:
            record["custody_note"] = "Different"
            manifest.write_bytes((json.dumps(record) + "\n").encode() + lines[1])
    with pytest.raises(ValueError):
        lookup.lookup(copied, source, "no-match-xyz")


@pytest.mark.parametrize("case", ["timeout", "wrong_result", "changed_after_verify"])
def test_isolated_verifier_failures_are_closed(
    copied: Path, case: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failure, mismatched semantic receipt or in-flight source changes cannot pass."""
    real = lookup.subprocess.run

    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
        """Return a bounded synthetic failure after confirming isolated invocation."""
        assert args[0][1:3] == ["-I", "-B"]
        if case == "timeout":
            raise subprocess.TimeoutExpired(args[0], 45)
        process = real(*args, **kwargs)
        if case == "wrong_result":
            return subprocess.CompletedProcess(args[0], 0, "{}", "")
        path = copied / "research/local_review" / lookup.DP_SOURCES[
            lookup.DOUGLAS_SOURCE_ID]["folder"] / "candidate-native.txt"
        path.write_bytes(path.read_bytes() + b" ")
        return process

    monkeypatch.setattr(lookup.subprocess, "run", run)
    with pytest.raises(ValueError):
        lookup.lookup(copied, lookup.DOUGLAS_SOURCE_ID, "no-match-xyz")


@pytest.mark.parametrize("case", ["span_hash", "span_length", "blank_to_zero", "missing_cell",
                                  "wrong_page", "missing_context", "detached_caption",
                                  "detached_nested", "false_currentness", "wrong_status"])
def test_result_contract_rejects_semantic_mutations(complete: dict[str, Any], case: str) -> None:
    """Strict result models prevent common downstream source/fee association corruption."""
    source = lookup.PUEBLO_SOURCE_ID if case == "detached_nested" else lookup.DOUGLAS_SOURCE_ID
    data = complete[source].model_dump(mode="json")
    row = data["rows"][0]
    if case == "span_hash":
        row["cells"][0]["native_spans"][0]["sha256"] = "0" * 64
    elif case == "span_length":
        row["cells"][0]["native_spans"][0]["end"] += 1
    elif case == "blank_to_zero":
        data["rows"][-1]["cells"][-1]["displayed_text"] = "$0"
    elif case == "missing_cell":
        row["cells"].pop()
    elif case == "wrong_page":
        row["physical_page"] = 2
    elif case == "missing_context":
        data["context"].pop()
    elif case == "detached_caption":
        row["table_caption_id"] = "STATE-CAPTION"
    elif case == "detached_nested":
        target = next(r for r in data["rows"] if r["nested"])
        target["nested"][0]["fee_line_ids"] = ["P9-L999"]
    elif case == "false_currentness":
        data["legal_currentness"] = "verified"
    else:
        data["status"] = "no_matching_row"
    with pytest.raises(ValueError):
        lookup.DpLookupResult.model_validate_json(json.dumps(data))


def test_read_only_cli_outside_repository(copied: Path, tmp_path: Path) -> None:
    """An isolated CLI cannot import an untrusted cwd module or modify source evidence."""
    script = Path(lookup.__file__).absolute()
    before = {str(p): lookup._digest(p) for p in copied.rglob("*") if p.is_file()}
    (tmp_path / "qa_model.py").write_text("raise RuntimeError('untrusted module')")
    process = subprocess.run([sys.executable, "-I", "-B", str(script), "--root", str(copied),
        "--source-id", lookup.PUEBLO_SOURCE_ID, "--query", "Tenant Finish", "--format", "json"],
        cwd=tmp_path, capture_output=True, text=True, timeout=45)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert [r["row_id"] for r in result["rows"]] == ["P1-11"]
    assert all(lookup._digest(Path(path)) == digest for path, digest in before.items())
