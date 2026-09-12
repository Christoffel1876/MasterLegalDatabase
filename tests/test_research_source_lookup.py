"""Verify the one-source research boundary against real frozen table evidence."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import research_source_lookup as lookup

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def copied_root(tmp_path: Path) -> Path:
    """Copy only the frozen small package for destructive evidence probes."""
    shutil.copytree(ROOT / lookup.PACKAGE, tmp_path / lookup.PACKAGE,
                    ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path


def reseal_review(root: Path, data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Update outer test pins so the unchanged verifier must check semantic bindings."""
    package = root / lookup.PACKAGE
    review = package / "SOURCE_QA.json"
    review.write_text(json.dumps(data), encoding="utf-8")
    manifest_path = package / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["files"]:
        if item["path"] == "SOURCE_QA.json":
            item.update(sha256=hashlib.sha256(review.read_bytes()).hexdigest(),
                        size_bytes=review.stat().st_size)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    for path in (review, manifest_path):
        monkeypatch.setitem(lookup.PINS, path.name, hashlib.sha256(path.read_bytes()).hexdigest())


def test_same_label_preserves_groups_operators_and_native_bytes() -> None:
    """Repeated modification labels cannot merge distinct alarm and sprinkler fees."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, "SYSTEM modification")
    assert [row.row_id for row in result.rows] == ["GJF-R007", "GJF-R009"]
    alarm, sprinkler = result.rows
    assert alarm.group == "Fire Alarm Plan Review Fee\n"
    assert sprinkler.group == "Fire Sprinkler System Plan Review Fee\n"
    assert alarm.label == sprinkler.label == "System Modiﬁcation\n"
    assert alarm.fee == " $50 ﬂate fee= < 5 devices/ $50 each inspection\n"
    assert sprinkler.fee == " $50 ﬂat fee (=< 20 heads)/$50 each inspection\n"
    for row in result.rows:
        for binding, text in [(row.group_binding, row.group), (row.label_binding, row.label),
                              (row.fee_binding, row.fee)]:
            raw = Path(binding.native_path).read_bytes()[binding.start:binding.end]
            assert raw.decode() == text
            assert hashlib.sha256(raw).hexdigest() == binding.sha256
    assert result.source.canonical_source_id == lookup.SOURCE_ID
    assert result.source.review_source_id == "grand-junction-fire-fees-mg-07"


def test_page_two_group_is_qualified_cross_page_not_invented_heading() -> None:
    """A continued table keeps its page-one heading reference on page two."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, "mobile food preparation")
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.row_id == "GJF-R035" and row.physical_page == 2
    assert row.group_binding.physical_page == 1 and row.group_binding.id == "P1-L072"
    assert row.group_basis == "continued_table_no_repeated_heading"
    assert row.fee == "$50 per permit (annually)\n"
    assert any("not reprinted" in note for note in result.observations)
    assert "Continued" in result.page_context["2"][0]


def test_list_and_storage_keep_all_rows_and_duplicate_labels() -> None:
    """Neither truncation nor label deduplication may silently lose evidence."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, list_rows=True)
    assert len(result.rows) == len({r.row_id for r in result.rows}) == 57
    assert sum(r.physical_page == 2 for r in result.rows) == 23
    labels = [r.label for r in result.rows]
    assert len(set(labels)) < len(labels)
    storage = lookup.lookup(ROOT, lookup.SOURCE_ID, "storage")
    assert {r.label for r in storage.rows} == {
        "High-piled storage\n", "High-Piled Combustible Storage\n",
        "Energy Storage/Solar PVP Systems\n",
    }


@pytest.mark.parametrize("query", [
    "unlisted submarine refueling service", "0 square feet", "000 square feet",
])
def test_no_matching_service_or_unstated_zero_area_tier(query: str) -> None:
    """No row is not absence of law; zero must not match part of 200 or 5,000."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, query)
    assert result.status == "no_matching_row" and result.rows == []
    assert result.evidence_verified and result.answer_safe is False
    text = lookup.render_markdown(result)
    assert "No matching row in this preserved source snapshot" in text
    assert "does not establish that a service is free" in text


def test_unknown_dates_are_not_metadata_or_retrieval_dates() -> None:
    """Successful results keep legal dates null and receipt roles distinct."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, "tenant finish")
    data = result.model_dump(mode="json")
    assert data["adoption_date"] is data["effective_date"] is data["source_edition_date"] is None
    assert data["source"]["source_retrieved_at"] == "2026-09-11T20:06:17.536965Z"
    assert data["source"]["reviewed_at"] == "2026-09-11T20:18:35.827031Z"
    assert result.legal_currentness == "not_verified" and not result.answer_safe
    assert "Effective date: unknown" in lookup.render_markdown(result)
    with pytest.raises(ValidationError):
        lookup.LookupResult.model_validate({**result.model_dump(), "answer_safe": True})


@pytest.mark.parametrize("phrase", [
    "What does a sprinkler permit cost today?", "current sprinkler fee", "fee applicable to me",
    "calculate my total cost", "do I need a permit", "is this legally effective", "latest fees",
])
def test_current_law_and_questions_refuse_without_rows(
    phrase: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Current/applicability questions cannot become successful source answers."""
    monkeypatch.setattr(lookup, "_load_verified", lambda _: pytest.fail("must not retrieve rows"))
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, phrase)
    assert result.status == "refused_current_law" and result.rows == []
    assert not result.answer_safe and not result.evidence_verified
    assert "Request refused" in lookup.render_markdown(result)


def test_explicit_current_law_list_mode_refuses() -> None:
    """A mode flag cannot convert source rows into a current schedule."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, list_rows=True, mode="current-law")
    assert result.status == "refused_current_law" and result.source is None


@pytest.mark.parametrize("arguments", [
    {"source_id": "another-source", "query": "alarm"},
    {"query": "alarm", "mode": "unsafe"},
    {}, {"query": "alarm", "list_rows": True}, {"query": " \n "},
])
def test_invalid_request_does_not_read_evidence(arguments: dict) -> None:
    """Only the fixed source and exactly one nonempty action are accepted."""
    with pytest.raises(ValueError):
        lookup.lookup(ROOT, **{"source_id": lookup.SOURCE_ID, **arguments})


@pytest.mark.parametrize("name", ["original.pdf", "SOURCE_QA.json", "build_review.py",
                                 "MANIFEST.json", "page-1.native.txt", "page-2.png"])
def test_tampered_frozen_files_fail_before_output(copied_root: Path, name: str) -> None:
    """Changed bytes anywhere in the evidence chain must fail closed."""
    path = copied_root / lookup.PACKAGE / name
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="mismatch"):
        lookup.lookup(copied_root, lookup.SOURCE_ID, "alarm")


@pytest.mark.parametrize("mutation", ["fee", "group", "continued_group", "span", "row_page"])
def test_existing_verifier_rejects_resealed_wrong_associations(
    copied_root: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    """Valid JSON with new test pins must still pass independent geometry checks."""
    data = json.loads((copied_root / lookup.PACKAGE / "SOURCE_QA.json").read_text())
    if mutation == "fee":
        data["rows"][2]["fee_span"], data["rows"][3]["fee_span"] = (
            data["rows"][3]["fee_span"], data["rows"][2]["fee_span"])
    elif mutation == "group":
        data["rows"][6]["group_span"] = "P1-L073"
    elif mutation == "continued_group":
        data["rows"][34]["group_basis"] = "visible_preceding_heading"
    elif mutation == "span":
        data["pages"][0]["spans"][0]["start"] = 1
    else:
        data["rows"][0]["physical_page"] = 2
    reseal_review(copied_root, data, monkeypatch)
    with pytest.raises(ValueError, match="package verification failed"):
        lookup.lookup(copied_root, lookup.SOURCE_ID, "alarm")


def test_verifier_timeout_is_failure(copied_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stalled verifier must not allow a best-effort partial result."""
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("verifier", 30)
    monkeypatch.setattr(lookup.subprocess, "run", timeout)
    with pytest.raises(ValueError, match="verification failed"):
        lookup.lookup(copied_root, lookup.SOURCE_ID, "alarm")


def test_symlinks_parent_traversal_and_missing_files_rejected(copied_root: Path) -> None:
    """Evidence cannot be substituted with a symlink or escaped file path."""
    package = copied_root / lookup.PACKAGE
    with pytest.raises(ValueError, match="leaves"):
        lookup._safe_file(package, "../SOURCE_QA.json")
    with pytest.raises(ValueError, match="parent traversal"):
        lookup.lookup(copied_root / ".." / copied_root.name, lookup.SOURCE_ID, "alarm")
    target = package / "page-2.png"
    content = target.read_bytes()
    target.unlink()
    with pytest.raises(ValueError, match="Missing"):
        lookup.lookup(copied_root, lookup.SOURCE_ID, "alarm")
    sibling = copied_root / "same-bytes.png"
    sibling.write_bytes(content)
    target.symlink_to(sibling)
    with pytest.raises(ValueError, match="symlinked"):
        lookup.lookup(copied_root, lookup.SOURCE_ID, "alarm")


def test_markdown_keeps_operators_visible_and_escapes_html() -> None:
    """Markup rendering must not interpret fee operators or hostile strings as HTML."""
    result = lookup.lookup(ROOT, lookup.SOURCE_ID, "system modification")
    rendered = lookup.render_markdown(result)
    assert "&lt; 5 devices" in rendered and "(=&lt; 20 heads)" in rendered
    assert "[Source PDF](</" in rendered and "[Checked review](</" in rendered
    assert "[Official source](https://" in rendered
    assert "\n\n- Group: " in rendered and "\n- Label: " in rendered
    assert "GJF-R007" in rendered and "GJF-R009" in rendered
    assert lookup._markdown('<script>[x](javascript:bad)</script>') == (
        '&lt;script&gt;\\[x\\](javascript:bad)&lt;/script&gt;')


def test_cli_json_success_refusal_and_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """Exit status distinguishes verified source rows from refusal and invalid evidence."""
    base = ["--source-id", lookup.SOURCE_ID, "--format", "json"]
    assert lookup.main(base + ["--query", "mobile food preparation"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["rows"][0]["physical_page"] == 2 and data["answer_safe"] is False
    assert lookup.main(base + ["--query", "current burn permit fee"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "refused_current_law"
    assert lookup.main(["--source-id", "unsupported", "--list-rows"]) == 1
    assert capsys.readouterr().out == ""


def test_real_cli_is_read_only_with_optimized_parent(copied_root: Path) -> None:
    """The assertion-based verifier runs normally even when the parent uses -O."""
    before = {p.relative_to(copied_root): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in copied_root.rglob("*") if p.is_file()}
    process = subprocess.run(
        [sys.executable, "-O", "-B", str(ROOT / "scripts/research_source_lookup.py"),
         "--root", str(copied_root), "--source-id", lookup.SOURCE_ID, "--query", "burn permit"],
        text=True, capture_output=True, timeout=30,
    )
    assert process.returncode == 0, process.stderr
    assert "answer_safe: false" in process.stdout and "$25 per year" in process.stdout
    after = {p.relative_to(copied_root): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in copied_root.rglob("*") if p.is_file()}
    assert before == after


@pytest.fixture
def greeley_root(tmp_path: Path) -> Path:
    """Use an isolated copy of the actual frozen three-source custody package."""
    shutil.copytree(ROOT / lookup.GREELEY_PACKAGE, tmp_path / lookup.GREELEY_PACKAGE,
                    ignore=shutil.ignore_patterns("__pycache__"), copy_function=shutil.copyfile)
    return tmp_path


def reseal_greeley(root: Path, review: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Update test-only outer identities so the unchanged verifier checks associations."""
    package = root / lookup.GREELEY_PACKAGE
    review_path = package / lookup.GREELEY_REVIEW
    review_path.write_text(json.dumps(review), encoding="utf-8")
    manifest_path = package / "PACKAGE.json"
    manifest = json.loads(manifest_path.read_bytes())

    def replace_ref(value: object) -> None:
        if isinstance(value, dict):
            if value.get("path") == lookup.GREELEY_REVIEW:
                value.update(sha256=lookup._digest(review_path),
                             size_bytes=review_path.stat().st_size)
            for child in value.values():
                replace_ref(child)
        elif isinstance(value, list):
            for child in value:
                replace_ref(child)

    replace_ref(manifest)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    saved_path = package / "VALIDATION.json"
    saved = json.loads(saved_path.read_bytes())
    saved["package"].update(sha256=lookup._digest(manifest_path),
                            size_bytes=manifest_path.stat().st_size)
    saved_path.write_text(json.dumps(saved), encoding="utf-8")
    for path in [review_path, manifest_path, saved_path]:
        monkeypatch.setitem(lookup.GREELEY_PINS, path.relative_to(package).as_posix(),
                            lookup._digest(path))


def test_greeley_complete_distinct_entries_and_native_partition() -> None:
    """List all nineteen whole clauses plus ten contexts without invented fee columns."""
    result = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, list_rows=True)
    assert isinstance(result, lookup.GreeleyLookupResult)
    assert len(result.entries) == len({e.entry_id for e in result.entries}) == 19
    assert len(result.context) == 10
    assert not hasattr(result, "rows")
    assert result.authority_id == result.source.authority_id == "CO-MUNICIPAL-GREELEY"
    blocks = [e.statement for e in result.entries] + result.context
    assert len({b.id for b in blocks}) == 29
    ordered = sorted(blocks, key=lambda b: b.native_start)
    assert ordered[0].native_start == 0 and ordered[-1].native_end == 3236
    assert all(a.native_end == b.native_start for a, b in zip(ordered, ordered[1:]))
    for block in blocks:
        assert block.candidate_start == block.native_start + 56
        raw = Path(block.candidate_path).read_bytes()[block.candidate_start:block.candidate_end]
        assert raw == block.text.encode()
        assert hashlib.sha256(raw).hexdigest() == block.sha256
        assert block.byte_basis == "utf8_candidate_file_with_page_marker"
    assert all("fee" not in entry.model_dump() for entry in result.entries)
    assert result.external_review_status == "pending_not_intaken"


def test_greeley_all_minima_cost_footnotes_and_payment_conditions() -> None:
    """Hourly prices retain their greater-cost footnote and distinct minimum durations."""
    result = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, list_rows=True)
    by_id = {e.entry_id: e for e in result.entries}
    for i in range(1, 5):
        entry = by_id[f"other_{i}"]
        assert "$75.00 per hour1" in entry.statement.text
        assert [b.id for b in entry.footnotes] == ["footnote_1"]
        assert "whichever is the greatest" in entry.footnotes[0].text
        assert "supervision, overhead, equipment, hourly wages" in entry.footnotes[0].text
    assert "minimum charge, two hours" in by_id["other_1"].statement.text
    assert "Section 109.8" in by_id["other_2"].statement.text
    assert "minimum charge, one-half hour" in by_id["other_3"].statement.text
    assert "one-half \nhour" in by_id["other_4"].statement.text
    assert [b.id for b in by_id["other_5"].footnotes] == ["footnote_2"]
    assert "administrative and overhead costs" in by_id["other_5"].footnotes[0].text
    major = by_id["other_6"].statement.text
    assert all(s in major for s in ["Section 106", "time of submitting", "65 percent",
                                    "separate fees", "in \naddition to the permit fees"])
    assert "under 1,000 square feet" in by_id["other_7"].statement.text
    assert ("$175 per application for SFD and $175 for multi-family"
            in by_id["other_9"].statement.text)
    assert "or fraction" in by_id["valuation_8"].statement.text


def test_greeley_displaced_headings_tax_branches_and_uncomputed_formulas() -> None:
    """Each late body keeps its own displaced heading and all branching conditions."""
    tax = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, "sales tax").entries
    assert [e.entry_id for e in tax] == ["sales_tax_body"]
    assert tax[0].headings[-1].id == "sales_tax_heading"
    assert tax[0].headings[-1].native_end < tax[0].statement.native_start
    assert all(s in tax[0].statement.text for s in [
        "4.11% of 45%", "$75,000", "or less per \nunit", "all other construction",
        "4.11% of 50%",
    ])
    electrical = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, "temporary electrical")
    assert [e.entry_id for e in electrical.entries] == ["temporary_electrical_body"]
    item = electrical.entries[0]
    assert item.headings[-1].id == "temporary_electrical_heading"
    assert "$45.00 per inspection" in item.statement.text
    assert "single-family dwellings, multi-family dwellings, and commercial" in item.statement.text
    hourly = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, "whichever is the greatest")
    assert [e.entry_id for e in hourly.entries] == [f"other_{i}" for i in range(1, 5)]


def test_greeley_provenance_and_ambiguous_date_roles_are_separate() -> None:
    """Receipt and filename/year claims cannot become verified acquisition or legal dates."""
    result = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, "major plan review")
    source = result.source
    assert source.official_source_url is source.original_acquisition_time is None
    assert source.acquisition_method == "received_review_package"
    assert source.intake_status == "archived_pending_pipeline"
    assert source.received_at.isoformat() == "2026-09-11T19:15:24.670419+00:00"
    assert source.reported_acquisition_at.isoformat() == "2026-09-11T18:50:31+00:00"
    assert source.reviewed_at.isoformat() == "2026-09-11T19:28:50.209076+00:00"
    assert "greeleyco.gov" in source.official_referral_url
    assert "sitecorecontenthub.cloud" in source.reported_requested_url
    assert result.adoption_date is result.effective_date is result.source_edition_date is None
    assert [d.role for d in result.date_statements] == [
        "schedule_title_year", "effective_heading_year", "unlabeled_footer",
    ]
    assert "2024 Building" in result.date_statements[0].evidence.text
    assert "Effective -2024" in result.date_statements[1].evidence.text
    assert result.date_statements[2].evidence.text == "8/18/2026 \n"
    rendered = lookup.render_markdown(result)
    assert "Official referral page" in rendered and "Reported download URL" in rendered
    assert "[Official source]" not in rendered
    assert "Receipt time is not acquisition time" in rendered
    assert "additional short horizontal mark" in rendered


@pytest.mark.parametrize("field,value", [
    ("answer_safe", True), ("effective_date", "2024-01-01"),
    ("external_review_status", "verified"), ("authority_id", "CO-COUNTY-WELD"),
])
def test_greeley_output_cannot_promote_status(field: str, value: object) -> None:
    """The distinct output contract refuses currentness, owner or external-review changes."""
    empty = lookup.GreeleyLookupResult(
        status="no_matching_row", query="x", evidence_verified=False, entries=[],
        context=[], date_statements=[], observations=[],
    ).model_dump()
    with pytest.raises(ValidationError):
        lookup.GreeleyLookupResult.model_validate({**empty, field: value})


@pytest.mark.parametrize("query", [
    "current fees", "What does a permit cost?", "calculate total cost", "legally effective",
])
def test_greeley_refusal_before_file_access(query: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Question or current-law requests do not execute any package verifier."""
    monkeypatch.setattr(lookup, "_load_greeley_verified", lambda _: pytest.fail("must not load"))
    result = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, query)
    assert result.status == "refused_current_law" and not result.evidence_verified
    assert result.entries == [] and result.context == [] and result.source is None
    assert "Request refused" in lookup.render_markdown(result)


@pytest.mark.parametrize("source", [
    "greeley-development-impact-fees-sd008-07", "greeley-water-sewer-pif-sd008-08", "EB-PDF-016",
])
def test_other_packaged_greeley_sources_inaccessible(source: str) -> None:
    """Verifying the custody package does not expose its other source documents."""
    with pytest.raises(ValueError, match="Unsupported source"):
        lookup.lookup(ROOT, source, list_rows=True)


@pytest.mark.parametrize("mutation", [
    "footnote", "heading_order", "offset", "omitted_span", "minimum", "timing", "tax_condition",
])
def test_greeley_resealed_semantic_mutations_fail(
    greeley_root: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    """Outer hashes are not sufficient when fee/condition/source associations are altered."""
    path = greeley_root / lookup.GREELEY_PACKAGE / lookup.GREELEY_REVIEW
    data = json.loads(path.read_bytes())
    if mutation == "footnote":
        data["footnote_links"]["other_1"] = "footnote_2"
    elif mutation == "heading_order":
        a = data["source_order"].index("sales_tax_heading")
        b = data["source_order"].index("temporary_electrical_heading")
        data["source_order"][a], data["source_order"][b] = (
            data["source_order"][b], data["source_order"][a])
    elif mutation == "offset":
        data["candidate_native_start"] = 55
    elif mutation == "omitted_span":
        data["spans"].pop()
    else:
        label, old = {
            "minimum": ("other_1", " (minimum charge, two hours)"),
            "timing": ("other_6", "the time of submitting plans and specifications for review"),
            "tax_condition": ("sales_tax_body", "or less per \nunit"),
        }[mutation]
        span = next(s for s in data["spans"] if s["label"] == label)
        assert old in span["text"]
        span["text"] = span["text"].replace(old, "")
        span["sha256"] = hashlib.sha256(span["text"].encode()).hexdigest()
    reseal_greeley(greeley_root, data, monkeypatch)
    with pytest.raises(ValueError, match="source-package verification failed"):
        lookup.lookup(greeley_root, lookup.GREELEY_SOURCE_ID, "plan review")


@pytest.mark.parametrize("name", [
    "validate_package.py", "package_models.py", "packet/04-verification/verify_packet.py",
    "source-audits/EB-PDF-016/build_review.py",
    "source-audits/EB-PDF-017/review_models.py",
    "source-audits/EB-PDF-017/validate_source_review.py", lookup.GREELEY_PDF,
])
def test_greeley_dependencies_pinned_before_execution(
    greeley_root: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    """A changed transitive verifier or source cannot run before its pin is checked."""
    path = greeley_root / lookup.GREELEY_PACKAGE / name
    path.write_bytes(path.read_bytes() + b"changed")
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(ValueError, match="mismatch"):
        lookup.lookup(greeley_root, lookup.GREELEY_SOURCE_ID, "inspection")


def test_greeley_no_match_and_exact_numeric_search_boundaries() -> None:
    """A substring of 1,000 is not an unstated zero tier or an exemption."""
    for phrase in ["0 square feet", "unlisted submarine inspection"]:
        result = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, phrase)
        assert result.entries == [] and result.status == "no_matching_row"
        assert result.evidence_verified and not result.answer_safe
        assert "does not establish" in lookup.render_markdown(result)


def test_greeley_cli_portable_read_only_and_isolated(greeley_root: Path) -> None:
    """The actual isolated wrapper runs portably even under an optimized parent."""
    before = {p.relative_to(greeley_root): lookup._digest(p)
              for p in greeley_root.rglob("*") if p.is_file()}
    result = subprocess.run(
        [sys.executable, "-O", "-B", str(ROOT / "scripts/research_source_lookup.py"),
         "--root", str(greeley_root), "--source-id", lookup.GREELEY_SOURCE_ID,
         "--query", "inspections outside", "--format", "json"],
        text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["entries"][0]["entry_id"] == "other_1"
    assert data["entries"][0]["footnotes"][0]["id"] == "footnote_1"
    after = {p.relative_to(greeley_root): lookup._digest(p)
             for p in greeley_root.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink", "oversized"])
def test_greeley_inventory_cannot_hide_substitution(
    greeley_root: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    """Closed scope, ordinary files and size limits apply before execution."""
    package = greeley_root / lookup.GREELEY_PACKAGE
    path = package / "source-audits/EB-PDF-015/page-0001.png"
    if kind == "extra":
        (package / "unlisted.py").write_text("raise RuntimeError('must never run')")
    elif kind == "missing":
        path.unlink()
    elif kind == "symlink":
        original = greeley_root / "same-image.png"
        original.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(original)
    else:
        with path.open("wb") as handle:
            handle.truncate(20_000_001)
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(ValueError):
        lookup.lookup(greeley_root, lookup.GREELEY_SOURCE_ID, "inspection")


@pytest.mark.parametrize("outcome", ["timeout", "failed", "bad_json", "bad_receipt"])
def test_greeley_validator_failure_never_returns_partial_evidence(
    greeley_root: Path, monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    """A complete successful typed scope receipt is required, even after good pins."""
    def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        if outcome == "timeout":
            raise subprocess.TimeoutExpired("frozen verifier", 30)
        if outcome == "failed":
            raise subprocess.CalledProcessError(1, "frozen verifier")
        value = "not-json" if outcome == "bad_json" else json.dumps({"status": "failed"})
        return subprocess.CompletedProcess("frozen verifier", 0, stdout=value, stderr="")
    monkeypatch.setattr(lookup.subprocess, "run", fail)
    with pytest.raises(ValueError, match="source-package verification failed"):
        lookup.lookup(greeley_root, lookup.GREELEY_SOURCE_ID, "inspection")


def test_greeley_post_verification_change_fails(greeley_root: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid verifier result cannot excuse evidence changed during its execution."""
    run = lookup.subprocess.run

    def change(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        result = run(*args, **kwargs)
        path = greeley_root / lookup.GREELEY_PACKAGE / "source-audits/EB-PDF-015/candidate.txt"
        path.write_bytes(path.read_bytes() + b"after verification")
        return result

    monkeypatch.setattr(lookup.subprocess, "run", change)
    with pytest.raises(ValueError, match="mismatch"):
        lookup.lookup(greeley_root, lookup.GREELEY_SOURCE_ID, "inspection")


@pytest.mark.parametrize("field,value", [
    ("candidate_start", 0), ("candidate_end", 1), ("native_start", 1),
    ("text", "changed"), ("sha256", "0" * 64),
])
def test_greeley_binding_does_not_confuse_candidate_with_native(
    field: str, value: object,
) -> None:
    """The output model itself rejects offset, text and hash inconsistencies."""
    data = {
        "id": "example", "text": "A", "candidate_path": "candidate.txt",
        "native_start": 0, "native_end": 1, "candidate_start": 56, "candidate_end": 57,
        "sha256": hashlib.sha256(b"A").hexdigest(),
    }
    with pytest.raises(ValidationError, match="byte binding mismatch"):
        lookup.GreeleyBlock.model_validate({**data, field: value})


@pytest.mark.parametrize("field,value", [
    ("official_source_url", "https://example.gov"),
    ("original_acquisition_time", "2026-09-11T19:15:24.670419Z"),
    ("acquisition_method", "official_download"),
    ("upstream_http_acquisition_independently_verified", True),
])
def test_greeley_custody_model_rejects_acquisition_relabeling(field: str, value: object) -> None:
    """Known receipt custody cannot silently be described as a witnessed official fetch."""
    result = lookup.lookup(ROOT, lookup.GREELEY_SOURCE_ID, "major plan review")
    with pytest.raises(ValidationError):
        lookup.GreeleySourceBinding.model_validate_json(json.dumps({
            **result.source.model_dump(mode="json"), field: value,
        }))


def test_greeley_cli_list_refusal_and_owner_separation(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI returns the distinct adapter and keeps legal refusal and authority IDs explicit."""
    base = ["--source-id", lookup.GREELEY_SOURCE_ID, "--format", "json"]
    assert lookup.main(base + ["--list-rows"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data["entries"]) == 19 and "rows" not in data
    assert data["source_id"] != data["authority_id"]
    assert lookup.main(base + ["--list-rows", "--mode", "current-law"]) == 2
    assert json.loads(capsys.readouterr().out)["entries"] == []
    gj = lookup.lookup(ROOT, lookup.SOURCE_ID, "burn permit")
    assert gj.authority_id == gj.source.authority_id == "CO-MUNICIPAL-GRAND_JUNCTION"
    assert gj.source_id != gj.authority_id


@pytest.fixture
def weld_root(tmp_path: Path) -> Path:
    """Copy the frozen review and only the immutable intake dependencies consumed."""
    shutil.copytree(ROOT / lookup.WELD_PACKAGE, tmp_path / lookup.WELD_PACKAGE,
                    copy_function=shutil.copyfile)
    intake = ROOT / lookup.WELD_INTAKE
    receipt = json.loads((intake / "intake-receipt.json").read_bytes())
    names = ["intake-receipt.json"]
    names += [receipt[k]["path"] for k in (
        "record_stream", "record_schema", "provenance_stream", "source_schema")]
    source = next(s for s in receipt["sources"] if s["source_id"] == lookup.WELD_SOURCE_ID)
    names += [source[k]["path"] for k in ("access_receipt", "public_headers")]
    for name in names:
        path = tmp_path / lookup.WELD_INTAKE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(intake / name, path)
    return tmp_path


@pytest.fixture(scope="module")
def weld_all() -> lookup.WeldLookupResult:
    """Use the real verifier once for association and output-model assertions."""
    return lookup.lookup(ROOT, lookup.WELD_SOURCE_ID, list_rows=True)


def test_weld_every_row_group_and_all_native_bytes_survive(
    weld_all: lookup.WeldLookupResult,
) -> None:
    """All 313 original lines remain reachable without merging any of the 137 rows."""
    source = json.loads((ROOT / lookup.WELD_PACKAGE / lookup.WELD_REVIEW).read_bytes())
    assert len(weld_all.rows) == len({r.row_id for r in weld_all.rows}) == 137
    assert weld_all.status == "matched" and weld_all.evidence_verified
    grouped: dict[str, int] = {}
    bound = {}
    for row, original in zip(weld_all.rows, source["rows"], strict=True):
        assert row.row_id == original["id"]
        assert row.physical_page == original["physical_page"]
        assert row.group.id == original["group_span"]
        assert [b.id for b in row.labels] == original["label_spans"]
        assert (row.fee.id if row.fee else None) == original["fee_span"]
        assert row.fee_cell_status == original["fee_cell_status"]
        assert [b.id for b in row.notes] == original["note_spans"]
        blocks = [row.group, *row.labels, *row.notes, *([row.fee] if row.fee else [])]
        bound.update({b.id: b for b in blocks})
        grouped[row.group.id] = grouped.get(row.group.id, 0) + 1
    assert list(grouped.values()) == [7, 8, 32, 4, 12, 20, 2, 5, 41, 3, 3]
    assert [(p.physical_page, p.header_visible) for p in weld_all.page_context] == [
        (1, True), (2, False), (3, False)]
    for page in weld_all.page_context:
        assert not (set(bound) & {b.id for b in page.spans})
        bound.update({b.id: b for b in page.spans})
    assert len(bound) == 313
    assert sum(len(b.text.encode()) for b in bound.values()) == 7367
    for page in source["pages"]:
        native = (ROOT / lookup.WELD_PACKAGE / "frozen/ehs" / page["native"]["path"]).read_bytes()
        for span in page["spans"]:
            b = bound[span["id"]]
            assert b.text == span["text"] == native[b.start:b.end].decode()
            assert b.sha256 == hashlib.sha256(native[b.start:b.end]).hexdigest()
    assert weld_all.observations == [o["statement"] for o in source["observations"]]
    assert len(weld_all.observations) == 12


def test_weld_blank_printed_zero_clipped_word_and_wrapped_label(
    weld_all: lookup.WeldLookupResult,
) -> None:
    """A blank, actual zero and incomplete source label remain materially different."""
    rows = {r.row_id: r for r in weld_all.rows}
    blank = rows["EHS-R062"]
    assert blank.fee is None and blank.fee_cell_status == "visibly_blank"
    assert "Appendix 5-D" in blank.labels[0].text
    for identity in ("EHS-R016", "EHS-R028"):
        row = rows[identity]
        assert row.fee.text.strip() == "$0.00" and row.fee_cell_status == "printed_text"
        assert "25-4-1607" in row.labels[0].text
    assert "Temproary" in rows["EHS-R032"].labels[0].text
    assert rows["EHS-R033"].labels[0].text.endswith("if applicab\n")
    assert rows["EHS-R033"].fee.text.strip() == "$100.00/hour"
    metals = rows["EHS-R131"]
    assert [b.id for b in metals.labels] == ["P3-L085", "P3-L086"]
    assert metals.labels[1].text == "Nickel, Silver\n"
    assert "Atimony" in metals.labels[0].text and metals.fee.text.strip() == "$23.00"


def test_weld_conditions_caps_duplicates_and_group_scopes(
    weld_all: lookup.WeldLookupResult,
) -> None:
    """No fee math, repaired grammar or cross-group multiplier escapes the source."""
    rows = {r.row_id: r for r in weld_all.rows}
    expected = {
        "EHS-R003": "Application fee of $100 plus $100.00/hour",
        "EHS-R036": "$100.00/hour (not to exceed $895)",
        "EHS-R038": "$100.00/hour (not to exceed $775)",
        "EHS-R039": "$100.00/hour (not to exceed $620)",
        "EHS-R050": "$100.00", "EHS-R051": "$50.00",
        "EHS-R061": "$5.00+", "EHS-R080": "$200.00", "EHS-R081": "$248.00",
        "EHS-R082": "$48.00", "EHS-R084": "$400.00", "EHS-R085": "$100.00/hour",
        "EHS-R086": "3 x Stated Fee", "EHS-R089": "$52.50", "EHS-R090": "$54.50",
        "EHS-R105": "Market Rate", "EHS-R107": "Market Rate", "EHS-R132": "Market Rate",
        "EHS-R007": "$13.00", "EHS-R123": "$14.00",
    }
    for identity, text in expected.items():
        assert rows[identity].fee.text.strip() == text
    assert "<25" in rows["EHS-R045"].labels[0].text
    assert ">25" in rows["EHS-R046"].labels[0].text
    assert ">25" in rows["EHS-R047"].labels[0].text
    assert "1 hour min" in rows["EHS-R060"].labels[0].text
    assert "$.50" in rows["EHS-R061"].labels[0].text
    assert "Transportion" in rows["EHS-R049"].labels[0].text
    assert [b.id for b in rows["EHS-R084"].notes] == ["P2-L073"]
    assert "excess of 4 hours" in rows["EHS-R084"].notes[0].text
    assert rows["EHS-R085"].notes == []
    assert "BACTERIOLOGICAL" in rows["EHS-R086"].group.text
    assert rows["EHS-R007"].group.id != rows["EHS-R123"].group.id


def test_weld_note_queries_page_notes_and_no_match_are_distinct() -> None:
    """Page notes can match without being invented as fee rows or universal conditions."""
    contract = lookup.lookup(ROOT, lookup.WELD_SOURCE_ID, "contract approved")
    assert contract.status == "matched_context_only" and contract.rows == []
    assert contract.matched_context_ids == ["P3-L111"]
    text = lookup.render_markdown(contract)
    assert "Matching page context: P3-L111" in text
    assert "no inferred row applicability" in text and "No matching fee row" in text
    metal = lookup.lookup(ROOT, lookup.WELD_SOURCE_ID, "additional metals")
    assert [r.row_id for r in metal.rows] == ["EHS-R131"]
    notes = {b.id: b.text for p in metal.page_context for b in p.spans}
    assert "market rate" in notes["P3-L088"] and "Cholrite" in notes["P3-L089"]
    assert "contract approved" in notes["P3-L111"]
    excess = lookup.lookup(ROOT, lookup.WELD_SOURCE_ID, "excess of 4 hours")
    assert [r.row_id for r in excess.rows] == ["EHS-R084"]
    absent = lookup.lookup(ROOT, lookup.WELD_SOURCE_ID, "unlisted submarine service")
    assert absent.status == "no_matching_row" and absent.rows == []
    assert len(absent.page_context) == 3 and len(absent.observations) == 12
    assert "does not establish that a service is free" in lookup.render_markdown(absent)


def test_weld_dates_owner_custody_and_qualifications(
    weld_all: lookup.WeldLookupResult,
) -> None:
    """HTTP, review and intake clocks are bound to source records and are not legal dates."""
    d = weld_all.model_dump(mode="json")
    assert d["source"]["source_retrieved_at"] == "2026-09-11T19:49:19.040662Z"
    assert d["source"]["reviewed_at"] == "2026-09-11T19:55:05.808484Z"
    assert d["source"]["received_at"] == "2026-09-11T20:02:02.187060Z"
    assert d["authority_id"] == d["source"]["authority_id"] == "CO-COUNTY-WELD"
    assert d["adoption_date"] is d["effective_date"] is d["source_edition_date"] is None
    assert d["source"]["source_year_assertion"] == "2026"
    assert "curl HTTPS" in d["source"]["acquisition_description"]
    assert d["source"]["intake_status"] == "archived_pending_pipeline"
    assert d["legal_currentness"] == "not_verified" and d["answer_safe"] is False
    assert "environmental-health" in d["boundary"]
    rendered = lookup.render_markdown(weld_all)
    assert "visibly blank (no amount supplied; not zero)" in rendered
    assert "&lt;25" in rendered and "&gt;25" in rendered
    assert "[Preserved PDF](</" in rendered
    assert "[Official source](https://www.weld.gov/" in rendered
    assert "header visible in source render: no" in rendered


@pytest.mark.parametrize("field,value", [
    ("answer_safe", True), ("legal_currentness", "verified"), ("adoption_date", "2026-01-01"),
    ("effective_date", "2026-01-01"), ("authority_id", "CO-MUNICIPAL-WELD"),
])
def test_weld_result_cannot_promote_claims(
    weld_all: lookup.WeldLookupResult, field: str, value: object,
) -> None:
    """The public response model prohibits legal status or jurisdiction promotion."""
    with pytest.raises(ValidationError):
        lookup.WeldLookupResult.model_validate({**weld_all.model_dump(), field: value})


@pytest.mark.parametrize("change", ["blank_zero", "wrong_role", "wrong_page"])
def test_weld_row_model_rejects_ambiguous_binding(
    weld_all: lookup.WeldLookupResult, change: str,
) -> None:
    """A caller cannot silently convert blanks or move notes/fees to another page."""
    data = weld_all.rows[61].model_dump()
    if change == "blank_zero":
        data["fee_cell_status"] = "printed_text"
    elif change == "wrong_role":
        data["labels"][0]["role"] = "fee"
    else:
        data["physical_page"] = 3
    with pytest.raises(ValidationError):
        lookup.WeldRow.model_validate(data)


@pytest.mark.parametrize("field,value", [("start", 1), ("end", 1), ("text", "changed"),
                                         ("sha256", "0" * 64), ("physical_page", 4)])
def test_weld_block_rejects_corrupted_offsets_and_bytes(
    weld_all: lookup.WeldLookupResult, field: str, value: object,
) -> None:
    """Every emitted native line must retain a consistent byte identity."""
    data = weld_all.rows[0].group.model_dump()
    with pytest.raises(ValidationError):
        lookup.WeldBlock.model_validate({**data, field: value})


@pytest.mark.parametrize("query", ["current laboratory fee", "What do I owe?", "effective fees"])
def test_weld_refuses_without_evidence_access(query: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Question and current-law handling stays a refusal before source loading."""
    monkeypatch.setattr(lookup, "_load_weld_verified", lambda _: pytest.fail("must not load"))
    result = lookup.lookup(ROOT, lookup.WELD_SOURCE_ID, query)
    assert result.status == "refused_current_law" and result.rows == result.page_context == []
    assert not result.evidence_verified and "Request refused" in lookup.render_markdown(result)
    with pytest.raises(ValueError, match="Unsupported source"):
        lookup.lookup(ROOT, "weld-ordinance-26-01-atlas-directed", list_rows=True)


@pytest.mark.parametrize("name", [
    lookup.WELD_REVIEW, "frozen/ehs/SOURCE_QA.schema.json", "frozen/ehs/build_review.py",
    lookup.WELD_PDF, "frozen/ehs/page-2.native.txt", "frozen/ehs/page-3.png",
    "package-record.schema.json", "frozen/ordinance/inputs/original.pdf",
])
def test_weld_closed_evidence_changes_fail_before_execution(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    """Even an unchanged EHS review cannot excuse changes to inventoried dependencies."""
    path = weld_root / lookup.WELD_PACKAGE / name
    path.write_bytes(path.read_bytes() + b"changed")
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(ValueError, match="mismatch"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


@pytest.mark.parametrize("kind", ["extra_file", "extra_dir", "missing", "symlink", "oversized"])
def test_weld_inventory_and_paths_fail_closed(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    """Unlisted files/directories, links and excessive bytes fail before subprocesses."""
    package = weld_root / lookup.WELD_PACKAGE
    path = package / "frozen/ehs/page-2.png"
    if kind == "extra_file":
        (package / "extra.py").write_text("raise RuntimeError('must not run')")
    elif kind == "extra_dir":
        (package / "empty").mkdir()
    elif kind == "missing":
        path.unlink()
    elif kind == "symlink":
        path.unlink()
        path.symlink_to(ROOT / lookup.WELD_PACKAGE / "frozen/ehs/page-2.png")
    else:
        with path.open("wb") as handle:
            handle.truncate(20_000_001)
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(ValueError):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


@pytest.mark.parametrize("name", ["intake-receipt.json", "intake-records.final.jsonl",
                                 "source-provenance.final.jsonl",
                                 "evidence/access/retry/ACCESS_RECEIPT.json"])
def test_weld_custody_bytes_pinned_separately_from_mutable_manifest(
    weld_root: Path, name: str,
) -> None:
    """Frozen source-specific receipt records cannot be relabeled as another acquisition."""
    path = weld_root / lookup.WELD_INTAKE / name
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="mismatch"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


def reseal_weld_review(root: Path, data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reseal test-only outer hashes so real native/geometry validation must run."""
    package = root / lookup.WELD_PACKAGE
    review = package / lookup.WELD_REVIEW
    review.write_text(json.dumps(data))
    manifest_path = package / "evidence-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for ref in manifest["files"]:
        if ref["path"] == lookup.WELD_REVIEW:
            ref.update(sha256=lookup._digest(review), size_bytes=review.stat().st_size)
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setitem(lookup.WELD_PINS, lookup.WELD_REVIEW, lookup._digest(review))
    monkeypatch.setitem(lookup.WELD_PINS, "evidence-manifest.json", lookup._digest(manifest_path))


@pytest.mark.parametrize("change", ["same_price_swap", "wrong_group", "wrong_page", "text",
                                    "offset", "source_id", "blank_zero"])
def test_weld_real_verifier_rejects_resealed_semantic_damage(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    """Pinned verifier independently checks source schema, bytes and row geometry."""
    data = json.loads((weld_root / lookup.WELD_PACKAGE / lookup.WELD_REVIEW).read_bytes())
    if change == "same_price_swap":
        data["rows"][1]["fee_span"], data["rows"][3]["fee_span"] = (
            data["rows"][3]["fee_span"], data["rows"][1]["fee_span"])
    elif change == "wrong_group":
        data["rows"][85]["group_span"] = "P2-L070"
    elif change == "wrong_page":
        data["rows"][0]["physical_page"] = 2
    elif change == "text":
        data["pages"][0]["spans"][0]["text"] += "changed"
    elif change == "offset":
        data["pages"][0]["spans"][0]["start"] = 1
    elif change == "source_id":
        data["source_id"] = "weld-ordinance-26-01-atlas-directed"
    else:
        data["rows"][61]["fee_cell_status"] = "printed_text"
    reseal_weld_review(weld_root, data, monkeypatch)
    with pytest.raises(ValueError, match="source-package verification failed"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


@pytest.mark.parametrize("outcome", ["timeout", "failed", "bad_json", "bad_receipt", "stdout"])
def test_weld_verifier_failure_does_not_return_rows(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    """Only the exact success receipt from the frozen direct verifier permits a result."""
    def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        """Simulate an interrupted, malformed or dishonest verifier response."""
        if outcome == "timeout":
            raise subprocess.TimeoutExpired("verifier", 30)
        if outcome == "failed":
            raise subprocess.CalledProcessError(1, "verifier")
        receipt = dict(lookup.WELD_VERIFICATION)
        if outcome == "bad_receipt":
            receipt["rows"] = 136
        stderr = "WARNING:root:" + ("bad JSON" if outcome == "bad_json" else json.dumps(receipt))
        return subprocess.CompletedProcess("verifier", 0, stdout=("extra" if outcome == "stdout"
                                                                 else ""), stderr=stderr)
    monkeypatch.setattr(lookup.subprocess, "run", fail)
    with pytest.raises(ValueError, match="source-package verification failed"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


def test_weld_changes_after_verification_cannot_escape(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rechecking catches changed evidence after a successful validator execution."""
    run = lookup.subprocess.run

    def change(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        """Mutate a retained page after real validation in this disposable copy."""
        result = run(*args, **kwargs)
        path = weld_root / lookup.WELD_PACKAGE / "frozen/ehs/page-2.native.txt"
        path.write_bytes(path.read_bytes() + b"changed")
        return result

    monkeypatch.setattr(lookup.subprocess, "run", change)
    with pytest.raises(ValueError, match="mismatch"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


def test_weld_cli_outside_checkout_optimized_environment_and_no_writes(
    weld_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The direct verifier ignores hostile Python paths/optimization and leaves no artifacts."""
    monkeypatch.setenv("PYTHONOPTIMIZE", "2")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    (tmp_path / "pymupdf.py").write_text("raise RuntimeError('untrusted import')")
    before = {str(p): lookup._digest(p) for p in weld_root.rglob("*") if p.is_file()}
    process = subprocess.run(
        [sys.executable, "-I", "-O", "-B", str(ROOT / "scripts/research_source_lookup.py"),
         "--root", str(weld_root), "--source-id", lookup.WELD_SOURCE_ID,
         "--query", "file review", "--format", "json"],
        cwd=tmp_path, text=True, capture_output=True, timeout=30,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["rows"][0]["fee"] is None and result["rows"][0]["row_id"] == "EHS-R062"
    assert before == {str(p): lookup._digest(p) for p in weld_root.rglob("*") if p.is_file()}


def test_weld_cli_statuses_and_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI handles context-only matches and explicit refusals without changing other sources."""
    base = ["--source-id", lookup.WELD_SOURCE_ID]
    assert lookup.main(base + ["--query", "contract approved", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "matched_context_only"
    assert lookup.main(base + ["--list-rows", "--mode", "current-law"]) == 2
    assert "Request refused" in capsys.readouterr().out
    assert lookup.main(base + ["--query", "file review"]) == 0
    assert "visibly blank" in capsys.readouterr().out
    assert lookup.main(base + ["--root", "/does/not/exist", "--list-rows"]) == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("change", ["duplicate", "wrong_authority", "wrong_received_at"])
def test_weld_resealed_intake_requires_single_consistent_source(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    """Hashes alone do not replace the exact source/authority/time record join."""
    intake = weld_root / lookup.WELD_INTAKE
    receipt_path = intake / "intake-receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    key = "record_stream" if change in {"duplicate", "wrong_received_at"} else "provenance_stream"
    path = intake / receipt[key]["path"]
    with path.open("rb") as handle:
        records = [json.loads(line) for line in handle]
    field = "record_id" if key == "record_stream" else "source_id"
    record = next(r for r in records if r[field] == lookup.WELD_SOURCE_ID)
    if change == "duplicate":
        records.append(dict(record))
    elif change == "wrong_authority":
        record["authority_id"] = "CO-COUNTY-JEFFERSON"
        for source in receipt["sources"]:
            if source["source_id"] == lookup.WELD_SOURCE_ID:
                source["authority_id"] = record["authority_id"]
    else:
        record["received_at"] = "2026-09-11T19:49:19.040662Z"
    path.write_text("".join(json.dumps(r) + "\n" for r in records))
    receipt[key].update(sha256=lookup._digest(path), size_bytes=path.stat().st_size)
    receipt_path.write_text(json.dumps(receipt))
    monkeypatch.setitem(lookup.WELD_INTAKE_PINS, "intake-receipt.json",
                        lookup._digest(receipt_path))
    with pytest.raises(ValueError, match="identity mismatch|relationship mismatch|schema mismatch"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "water")


def test_weld_verifier_uses_direct_isolation_with_assertions(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ignore inherited optimization and never execute the unrelated outer wrapper."""
    monkeypatch.setenv("PYTHONOPTIMIZE", "2")
    run = lookup.subprocess.run
    calls = []

    def inspect(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        """Observe the real subprocess argv rather than imitating its receipt."""
        calls.append(args[0])
        return run(*args, **kwargs)

    monkeypatch.setattr(lookup.subprocess, "run", inspect)
    result = lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "0.00")
    assert len(calls) == 1
    assert calls[0] == [sys.executable, "-I", "-B", str(
        weld_root / lookup.WELD_PACKAGE / "frozen/ehs/build_review.py"), "--verify"]
    assert [r.row_id for r in result.rows] == ["EHS-R016", "EHS-R028"]
    assert all(r.fee_cell_status == "printed_text" for r in result.rows)


def test_weld_review_notes_cannot_be_dropped_without_detection(
    weld_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing row conditions or page exceptions must trip immutable evidence identity."""
    path = weld_root / lookup.WELD_PACKAGE / lookup.WELD_REVIEW
    data = json.loads(path.read_bytes())
    data["rows"][83]["note_spans"] = []
    data["pages"][2]["spans"] = [s for s in data["pages"][2]["spans"]
                                 if s["id"] != "P3-L111"]
    path.write_text(json.dumps(data))
    monkeypatch.setattr(lookup.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(ValueError, match="hash/size mismatch"):
        lookup.lookup(weld_root, lookup.WELD_SOURCE_ID, "methamphetamine")
