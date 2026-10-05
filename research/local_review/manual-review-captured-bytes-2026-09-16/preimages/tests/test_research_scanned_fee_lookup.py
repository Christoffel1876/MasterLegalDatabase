"""Offline integrity and full-context tests for the fixed scanned-fee lookup."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

HERE = Path(__file__).absolute().parent
MODULE = HERE / "research_scanned_fee_lookup.py"
if not MODULE.is_file():
    MODULE = HERE.parent / "scripts/research_scanned_fee_lookup.py"
SPEC = importlib.util.spec_from_file_location("research_scanned_fee_lookup", MODULE)
lookup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lookup
SPEC.loader.exec_module(lookup)
REPO = next(
    candidate for parent in HERE.parents for candidate in [parent, parent / "MasterLegalDatabase"]
    if (candidate / lookup.PACKAGE / "FINAL_MANIFEST.json").is_file()
)


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    """Copy only exact accepted evidence into a disposable repository-shaped fixture."""
    shutil.copytree(REPO / lookup.PACKAGE, tmp_path / lookup.PACKAGE)
    path = tmp_path / lookup.ACCEPTANCE
    path.parent.mkdir(parents=True)
    shutil.copyfile(REPO / lookup.ACCEPTANCE, path)
    return tmp_path


@pytest.fixture
def verified(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip repeated external work; dedicated tests exercise the real verifier separately."""
    monkeypatch.setattr(lookup, "_run_verifier", lambda package: None)


@pytest.fixture
def all_rows(verified: None) -> lookup.LookupResult:
    """Load the pinned grid once per consuming case without altering its bytes."""
    return lookup.lookup(REPO, lookup.SOURCE_ID, list_rows=True)


def test_actual_verifier_and_all_exact_row_bindings(source_root: Path) -> None:
    """All 104 rows preserve every cell, context and source-image reference."""
    result = lookup.lookup(source_root, lookup.SOURCE_ID, list_rows=True)
    package = source_root / lookup.PACKAGE
    grid = json.loads((package / "REVIEWED_GRID.json").read_bytes())
    source_rows = {r["id"]: r for r in grid["rows"]}
    transcript = (package / "REVIEWED_TRANSCRIPTION.txt").read_bytes()
    assert len(result.matches) == 104
    assert [m.fee_row.row.model_dump(mode="json") for m in result.matches] == [
        r for r in grid["rows"] if r["role"] == "fee_row"
    ]
    for match in result.matches:
        assert match.section_header.row.model_dump(mode="json") == source_rows[
            match.fee_row.row.section_header_id
        ]
        for cell in match.fee_row.row.cells:
            observed = transcript[cell.transcript_start_byte:cell.transcript_end_byte]
            assert observed == cell.text.encode()
            assert cell.native_start_byte is None and cell.native_end_byte is None
        image_name = f"page-{match.fee_row.row.physical_page}.png"
        assert match.fee_row.source_image.path.endswith(image_name)
    assert result.source.verified_effective_date is None
    assert result.source.verified_adoption_date is None
    assert result.source.verified_http_acquisition_at is None
    assert result.source.claimed_http_acquisition_at == "2026-09-12T22:01:39Z"
    assert result.source.actual_repository_received_at == "2026-09-12T22:59:48.795762Z"
    assert result.source.source_printed_date_claim == "Fee Schedule- Effective Date May 1, 2026"
    assert not result.answer_safe and result.legal_currentness == "not_verified"


@pytest.mark.parametrize("target", [
    "source/original.pdf", "SOURCE_QA.json", "REVIEWED_GRID.json", "validate_review.py",
    "FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json", "review_models.py",
    "REVIEWED_TRANSCRIPTION.txt", "images/page-3.png", "custody/intake-RECEIPT.json",
])
def test_tamper_fails_before_any_verifier_execution(
    source_root: Path, monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    """Changed source, executable, transcript, pixels or custody never reach execution."""
    path = source_root / lookup.PACKAGE / target
    path.write_bytes(path.read_bytes() + b"\nCHANGED")
    calls = []
    monkeypatch.setattr(lookup, "_run_verifier", lambda package: calls.append(package))
    with pytest.raises(ValueError):
        lookup.lookup(source_root, lookup.SOURCE_ID, "Erosion")
    assert not calls


def test_acceptance_tamper(source_root: Path, verified: None) -> None:
    """Root's accepted-review binding is required independently of the source package."""
    (source_root / lookup.ACCEPTANCE).write_bytes(b"{}")
    with pytest.raises(ValueError, match="acceptance"):
        lookup.lookup(source_root, lookup.SOURCE_ID, "Erosion")


@pytest.mark.parametrize("attack", ["file", "directory", "symlink", "ancestor", "missing"])
def test_path_and_closed_inventory_attacks(source_root: Path, verified: None, attack: str) -> None:
    """Unknown files/directories, missing evidence and symlinked ancestors fail closed."""
    package = source_root / lookup.PACKAGE
    if attack == "file":
        (package / "unlisted.json").write_text("{}")
    elif attack == "directory":
        (package / "unexpected-empty-directory").mkdir()
    elif attack == "symlink":
        path = package / "source/original.pdf"
        path.unlink()
        path.symlink_to(REPO / lookup.PACKAGE / "source/original.pdf")
    elif attack == "ancestor":
        path = package / "images"
        shutil.rmtree(path)
        path.symlink_to(REPO / lookup.PACKAGE / "images", target_is_directory=True)
    else:
        (package / "images/page-1.png").unlink()
    with pytest.raises(ValueError):
        lookup.lookup(source_root, lookup.SOURCE_ID, "Erosion")


@pytest.mark.parametrize("name", ["/tmp/file", "../outside", "source//original.pdf"])
def test_noncanonical_reference_rejected(name: str) -> None:
    """Reject lexical path escapes before attempting to open a referenced file."""
    with pytest.raises(ValueError, match="Noncanonical"):
        lookup._relative(REPO, name)


def test_relative_and_tilde_root_normalization(
    monkeypatch: pytest.MonkeyPatch, verified: None,
) -> None:
    """Relative roots and tilde resolve to the same ordinary checked tree."""
    monkeypatch.chdir(REPO.parent)
    relative = lookup.lookup(Path("MasterLegalDatabase"), lookup.SOURCE_ID, "nothing unmatched")
    assert relative.status == "no_matching_row"
    tilde_root = Path("~") / REPO.relative_to(Path.home())
    tilde = lookup.lookup(tilde_root, lookup.SOURCE_ID, "nothing unmatched")
    assert tilde.status == "no_matching_row"
    with pytest.raises(ValueError, match="Unsafe"):
        lookup.lookup(REPO / ".." / REPO.name, lookup.SOURCE_ID, "Erosion")


def test_global_context_footnotes_and_continuations(all_rows: lookup.LookupResult) -> None:
    """Mandatory exceptions stay attached and cross-page section relationships stay explicit."""
    context = all_rows.mandatory_context
    assert [b.row.id for b in context.source_headers] == ["P1-TITLE", "P1-DATE"]
    assert context.global_footnote.row.cells[0].text == (
        "1. Application fees include a $37.00 technology fee"
    )
    assert [b.row.id for b in context.general_notes] == ["GENERAL-1", "GENERAL-2", "GENERAL-3"]
    refund_text = context.general_notes[1].row.cells[0].text
    assert "Unless an error has occurred by County staff" in refund_text
    rows = {m.fee_row.row.id: m for m in all_rows.matches}
    assert rows["P3-PLAN-01"].section_header.row.physical_page == 2
    assert rows["P3-PLAN-01"].section_continues_from_prior_page
    assert rows["P4-ENG-01"].section_header.row.physical_page == 3
    assert rows["P4-ENG-01"].section_continues_from_prior_page
    assert rows["P3-ENG-14"].unresolved_clipped_label
    assert rows["P3-ENG-14"].fee_row.row.cells[0].text.endswith("submittal")
    assert [b.row.id for b in rows["P1-PLAN-21"].row_footnotes] == ["FN-05"]
    assert "combined maximum of two (2)" in rows["P1-PLAN-21"].row_footnotes[0].row.cells[0].text


def test_blank_and_tbd_never_zero(all_rows: lookup.LookupResult) -> None:
    """Five blank project cells and all literal TBD entries survive unchanged."""
    blanks = [m.fee_row.row.id for m in all_rows.matches
              if m.fee_row.row.cells[2].state == "visibly_blank"]
    assert blanks == ["P1-PLAN-17", "P4-OTHER-01", "P4-OTHER-02", "P4-OTHER-03", "P4-OTHER-04"]
    assert sum(m.fee_row.row.cells[1].text == "TBD" for m in all_rows.matches) == 3
    rendered = lookup.render_markdown(all_rows)
    assert "[visibly blank]" in rendered and "clipped tail unresolved" in rendered
    assert "Verified adoption/effective dates: unknown" in rendered
    assert "included" not in rendered.split("Required context")[0]


@pytest.mark.parametrize("query", [
    "nonexistent teleport permit", "0 square feet", "000 square feet",
])
def test_missing_service_is_not_absence(query: str, verified: None) -> None:
    """No match remains confined to this single snapshot, without an exemption or fee claim."""
    result = lookup.lookup(REPO, lookup.SOURCE_ID, query)
    assert result.status == "no_matching_row" and not result.matches
    assert "does not establish absence" in result.scope


def test_context_only_query_does_not_assign_fee(verified: None) -> None:
    """A global refund-note match is not converted into a fee row or a refund decision."""
    result = lookup.lookup(REPO, lookup.SOURCE_ID, "refunds")
    assert result.status == "matched_context_only" and not result.matches
    assert result.matched_context_ids == ["GENERAL-2"]


@pytest.mark.parametrize("query", [
    "What do I owe?", "current fee", "calculate fees", "does this apply",
])
def test_current_law_refusal_precedes_source_read(query: str, tmp_path: Path) -> None:
    """Current-law/calculation questions cannot generate rows, even without evidence available."""
    result = lookup.lookup(tmp_path, lookup.SOURCE_ID, query)
    assert isinstance(result, lookup.Refusal)
    assert not result.answer_safe
    assert "Request refused" in lookup.render_markdown(result)


@pytest.mark.parametrize("kwargs", [
    {}, {"query": ""}, {"query": "  "}, {"query": "x", "list_rows": True}, {"query": "x" * 201},
])
def test_invalid_query_contract(kwargs: dict) -> None:
    """Ambiguous or empty query requests fail rather than listing silently."""
    with pytest.raises(ValueError):
        lookup.lookup(REPO, lookup.SOURCE_ID, **kwargs)


def test_unknown_source_and_explicit_current_mode(tmp_path: Path) -> None:
    """The isolated tool does not expand to another source or current-law mode."""
    with pytest.raises(ValueError, match="fixed"):
        lookup.lookup(tmp_path, "other-source", "Erosion")
    assert isinstance(lookup.lookup(tmp_path, lookup.SOURCE_ID, "Erosion", mode="current-law"),
                      lookup.Refusal)


def test_matching_normalization_changes_only_search(verified: None) -> None:
    """Compatibility ligatures can match without rewriting source text."""
    a = lookup.lookup(REPO, lookup.SOURCE_ID, "ﬁnal plat")
    b = lookup.lookup(REPO, lookup.SOURCE_ID, "final plat")
    assert a.model_dump() == b.model_dump() and a.matches
    assert not lookup._matches("000", "5,000")
    assert not lookup._matches("0", "5.0")


@pytest.mark.parametrize("field,value", [
    ("native_start_byte", 1), ("pixel_bbox", [0, 0, 2201, 100]),
    ("transcript_end_byte", 999999), ("state", "visibly_blank"), ("superscript_footnotes", [16]),
])
def test_cell_integrity(field: str, value: object, all_rows: lookup.LookupResult) -> None:
    """Native offsets, lost blanks, impossible pixels and invalid superscripts are rejected."""
    cell = all_rows.matches[0].fee_row.row.cells[0].model_dump(mode="json")
    cell[field] = value
    with pytest.raises(ValidationError):
        lookup.Cell.model_validate_json(json.dumps(cell))


@pytest.mark.parametrize("attack", [
    "columns", "section", "table", "notes", "continuation", "clipped",
])
def test_row_relationship_mismatch(attack: str, all_rows: lookup.LookupResult) -> None:
    """Detached fees, section headings, notes or uncertainty cannot validate as full matches."""
    match = next(m for m in all_rows.matches if m.fee_row.row.id == "P3-ENG-14")
    value = match.model_dump(mode="json")
    if attack == "columns":
        value["fee_row"]["row"]["cells"].reverse()
    elif attack == "section":
        value["section_header"]["row"]["id"] = "PLANNING-MINOR"
    elif attack == "table":
        value["fee_row"]["row"]["fee_header_id"] = None
    elif attack == "notes":
        value["fee_row"]["row"]["cells"][0]["superscript_footnotes"] = [5]
    elif attack == "continuation":
        value["section_continues_from_prior_page"] = True
    else:
        value["unresolved_clipped_label"] = False
    with pytest.raises(ValidationError):
        lookup.FeeMatch.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("attack", ["title", "table", "footnote", "general"])
def test_required_context_cannot_be_dropped(attack: str, all_rows: lookup.LookupResult) -> None:
    """The contract enforces complete global notes even when only one row matches."""
    value = all_rows.mandatory_context.model_dump(mode="json")
    if attack == "title":
        value["source_headers"].pop()
    elif attack == "table":
        value["table_header"]["row"]["cells"][1]["superscript_footnotes"] = []
    elif attack == "footnote":
        value["global_footnote"]["row"]["id"] = "FN-02"
    else:
        value["general_notes"].pop()
    with pytest.raises(ValidationError):
        lookup.RequiredContext.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("attack", ["hash", "acceptance", "authority", "currentness"])
def test_output_source_pins_and_limits(attack: str, all_rows: lookup.LookupResult) -> None:
    """Source substitution or promotion cannot be represented by the output model."""
    value = all_rows.source.model_dump(mode="json")
    if attack == "hash":
        value["source_pdf"]["sha256"] = "0" * 64
    elif attack == "acceptance":
        value["acceptance"]["sha256"] = "0" * 64
    elif attack == "authority":
        value["authority_id"] = "CO-MUNICIPAL-COLORADO_SPRINGS"
    else:
        value["legal_currentness"] = "current"
    with pytest.raises(ValidationError):
        lookup.SourceBinding.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("attack", ["duplicate", "status", "partial", "context"])
def test_result_count_status_failures(attack: str, all_rows: lookup.LookupResult) -> None:
    """Output labels cannot hide duplicated rows, partial lists or empty context matches."""
    value = all_rows.model_dump(mode="json")
    if attack == "duplicate":
        value["matches"][1] = copy.deepcopy(value["matches"][0])
    elif attack == "status":
        value["status"] = "no_matching_row"
    elif attack == "partial":
        value["matches"].pop()
    else:
        value["matches"] = []
        value["status"] = "matched_context_only"
    with pytest.raises(ValidationError):
        lookup.LookupResult.model_validate_json(json.dumps(value))


def test_isolated_verifier_options_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Execution uses the pinned script, isolation, no optimization and a bounded timeout."""
    calls = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        """Capture subprocess options without executing a modified command."""
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(lookup.EXPECTED_VERIFICATION))

    monkeypatch.setattr(lookup.subprocess, "run", run)
    lookup._run_verifier(REPO / lookup.PACKAGE)
    command, kwargs = calls[0]
    assert command[1:3] == ["-I", "-B"] and "-O" not in command
    assert kwargs["timeout"] == 90
    assert set(kwargs["env"]) == {"PATH", "PYTHONNOUSERSITE"}
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=1, stdout="{}",
    ))
    with pytest.raises(ValueError, match="verifier"):
        lookup._run_verifier(REPO / lookup.PACKAGE)


def test_second_preflight_catches_during_verification_change(
    source_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A verifier-time data mutation is detected before results are generated."""
    def tamper(package: Path) -> None:
        """Simulate a concurrent transcript change in the disposable package."""
        (package / "REVIEWED_TRANSCRIPTION.txt").write_text("changed")

    monkeypatch.setattr(lookup, "_run_verifier", tamper)
    with pytest.raises(ValueError, match="hash/size"):
        lookup.lookup(source_root, lookup.SOURCE_ID, "Erosion")


def test_markdown_query_is_inert_and_context_readable(verified: None) -> None:
    """Source punctuation is escaped and an untrusted query is never echoed as Markdown."""
    query = '<img src=x onerror=alert(1)> [click](https://example.invalid)'
    result = lookup.lookup(REPO, lookup.SOURCE_ID, query)
    rendered = lookup.render_markdown(result)
    assert query not in rendered and "<img" not in rendered
    assert "\n\napplication\\_fee:" in rendered
    assert "Official URL" in rendered and "https://epc-assets.elpasoco.com" in rendered
    assert "\n\nGeneral" not in rendered  # Notes remain within their full typed row blocks.
    assert lookup._escape('<x>& $[a]') == r'&lt;x&gt;&amp; \$\[a\]'


def test_cli_json_markdown_errors_and_refusal(
    capsys: pytest.CaptureFixture[str], verified: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI preserves deterministic data, readable output and nonzero refusal/failure exits."""
    base = ["--root", str(REPO), "--source-id", lookup.SOURCE_ID]
    assert lookup.main(base + ["--query", "Erosion", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "matched_rows"
    assert lookup.main(base + ["--query", "refunds"]) == 0
    assert "matched\\_context\\_only" in capsys.readouterr().out
    assert lookup.main(base + ["--list-rows", "--mode", "current-law"]) == 2
    assert "Request refused" in capsys.readouterr().out
    assert lookup.main(base + ["--query", ""]) == 1
    assert "failed" in capsys.readouterr().err
    monkeypatch.setattr(lookup, "_run_verifier", lambda p: (_ for _ in ()).throw(
        subprocess.TimeoutExpired("verify", 90)
    ))
    assert lookup.main(base + ["--query", "Erosion"]) == 1
    assert "timed out" in capsys.readouterr().err


def test_cli_refusal_outside_repository(tmp_path: Path) -> None:
    """A real isolated CLI process refuses current-law questions without opening evidence."""
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(MODULE), "--root", str(tmp_path),
         "--source-id", lookup.SOURCE_ID, "--query", "current fee", "--format", "json"],
        capture_output=True, text=True, check=False, cwd=tmp_path,
    )
    assert result.returncode == 2 and json.loads(result.stdout)["status"] == "refused"
