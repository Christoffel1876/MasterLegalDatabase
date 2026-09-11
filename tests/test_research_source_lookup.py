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
