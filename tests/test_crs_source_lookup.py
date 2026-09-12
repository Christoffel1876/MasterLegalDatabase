"""Offline exact-source, scope, continuation, custody and tamper regression tests."""

import copy
import hashlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import crs_source_lookup as m

SOURCE = m.DEFAULT_SOURCE


@pytest.fixture
def packet(tmp_path):
    root = tmp_path / "source"
    shutil.copytree(SOURCE, root)
    return root


@pytest.fixture
def raw():
    root = SOURCE
    return root, json.loads((root / "SOURCE_QA.json").read_bytes()), json.loads(
        (root / "events/E001.json").read_bytes())


@pytest.fixture(scope="module")
def actual_results():
    return {sid: m.lookup(SOURCE, sid) for sid in m.IDS}


def test_actual_all_three_sections_complete_and_roundtrip(actual_results):
    assert set(actual_results) == set(m.IDS)
    assert [len(r.section.paragraphs) for r in actual_results.values()] == [1, 2, 3]
    assert [len(r.section.ancillary) for r in actual_results.values()] == [2, 3, 4]
    for sid, result in actual_results.items():
        assert result.status == "matched" and result.requested_section_id == sid
        assert m.Result.model_validate_json(result.model_dump_json()) == result
        assert result.custody.source.sha256 == m.SOURCE_SHA
        assert result.custody.legal_effective_date is None
        assert result.legal_currentness == "not_verified" and not result.answer_safe
        assert result.custody.prior_2025_original_custody == "unresolved"


def test_page_four_to_five_continuation_complete(actual_results):
    paragraph = actual_results[m.IDS[1]].section.paragraphs[0]
    assert paragraph.label == "(1)"
    assert [f.physical_page for f in paragraph.fragments] == [4, 5]
    offsets = [(f.native_start, f.native_end) for f in paragraph.fragments]
    assert offsets == [(1139, 1639), (60, 172)]
    assert "in lieu of \nthe \"Colorado Municipal Election Code of 1965\"" in paragraph.text
    assert paragraph.text.endswith("any election. \n")
    assert "Title 1 – Elections" not in paragraph.text
    assert paragraph.text_sha256 == hashlib.sha256(paragraph.text.encode()).hexdigest()


def test_all_page_six_notes_complete_not_section_104(actual_results):
    notes = actual_results[m.IDS[2]].section.ancillary
    assert [n.region_id for n in notes] == ["S103-SOURCE", "S103-EDITOR", "S103-ANN-H", "S103-ANN"]
    assert [n.role for n in notes] == [
        "source_history_note", "editors_note", "annotation_heading", "case_annotation"]
    assert [n.physical_page for n in notes] == [5, 6, 6, 6]
    assert notes[-1].text.endswith("1081. \n \n")
    assert "candidate petitions" in notes[-1].text
    assert "1-1-104." not in "".join(n.text for n in notes)
    assert "two-column" in actual_results[m.IDS[2]].section.scope_note


def test_acquisition_time_is_measured_not_edition_or_legal_date(actual_results):
    custody = actual_results[m.IDS[0]].custody
    assert custody.acquisition_started_at.isoformat() == "2026-09-12T22:13:16.539063+00:00"
    assert custody.acquisition_completed_at.isoformat() == "2026-09-12T22:13:17.603959+00:00"
    assert custody.source_review_prepared_at > custody.acquisition_completed_at
    assert custody.printed_edition_claim == "Colorado Revised Statutes 2026"
    assert custody.pdf_metadata_claims["creationDate"] == "D:20260818155956-06'00'"
    assert custody.total_pdf_pages == 1008 and custody.reviewed_physical_pages == (1, 2, 3, 4, 5, 6)


@pytest.mark.parametrize("sid", [
    "CRS-1-1-104", "1-1-101", "CRS-1-1-101 current", "", "CRS-1", "../SOURCE_QA.json"])
def test_only_exact_selected_ids_no_contents_or_fuzzy_hits(sid, tmp_path):
    result = m.lookup(tmp_path / "absent", sid)
    assert result.status == "outside_scope" and result.section is None and result.custody is None


@pytest.mark.parametrize("mode", [
    "current_law", "current", "calculate", "effective", "source-only", ""])
def test_refuse_every_non_source_mode_without_reading(mode, tmp_path):
    result = m.lookup(tmp_path / "absent", m.IDS[0], mode=mode)
    assert result.status == "refused_mode" and result.section is None


@pytest.mark.parametrize("name", [
    "FINAL_MANIFEST.json", "SOURCE_QA.json", "build_review.py", "acquire.py",
    "events/E001/body.bin", "native/page-0005.txt", "pages/page-0006.png",
    "events/E001.json", "reference/events/E009/body.bin"])
def test_tampering_rejected_before_semantic_execution(packet, monkeypatch, name):
    path = packet / name
    path.write_bytes(path.read_bytes() + b"changed")
    monkeypatch.setattr(m, "semantic_verify", lambda _: pytest.fail("Executed before byte gate"))
    with pytest.raises(ValueError, match="changed"):
        m.lookup(packet, m.IDS[1])


@pytest.mark.parametrize("name", ["surprise.txt", "acquire/__init__.py", "nested/extra.py"])
def test_closed_inventory_rejects_unexpected_files(packet, name):
    path = packet / name
    path.parent.mkdir(exist_ok=True)
    path.write_text("extra")
    with pytest.raises(ValueError, match="unexpected"):
        m.check_packet(packet)


def test_missing_required_evidence(packet):
    (packet / "native/page-0006.txt").unlink()
    with pytest.raises(ValueError, match="Missing"):
        m.check_packet(packet)


@pytest.mark.parametrize("name", [
    "../outside", "./alias", "/absolute", "C:/outside", "a\\b", ".", ""])
def test_path_escape_and_alias_rejected(name):
    with pytest.raises(ValueError, match="Unconfined"):
        m.FileRef(path=name, sha256="0" * 64, size_bytes=0)


def test_symlink_file_parent_root_and_fifo_refused(packet, tmp_path):
    native = packet / "native/page-0001.txt"
    target = tmp_path / "bytes.txt"
    shutil.copyfile(native, target)
    native.unlink()
    native.symlink_to(target)
    with pytest.raises(ValueError, match="Symlink"):
        m.check_packet(packet)
    alias = tmp_path / "alias"
    alias.symlink_to(packet, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked"):
        m.safe_file(alias, "SOURCE_QA.json")
    with pytest.raises(ValueError, match="traversal"):
        m.safe_file(packet / ".." / "source", "SOURCE_QA.json")
    import os
    os.mkfifo(packet / "fifo")
    with pytest.raises(ValueError, match="Symlink|special"):
        m.check_packet(packet)


def test_filesize_and_total_bounds(packet, monkeypatch):
    monkeypatch.setattr(m, "MAX_FILE", 100)
    with pytest.raises(ValueError, match="exceeds bound"):
        m.safe_file(packet, "SOURCE_QA.json")
    monkeypatch.setattr(m, "MAX_FILE", 8_000_000)
    monkeypatch.setattr(m, "MAX_TOTAL", 1)
    with pytest.raises(ValueError, match="total bound"):
        m.check_packet(packet)


def test_growth_during_read_rejected(monkeypatch):
    monkeypatch.setattr(m, "MAX_FILE", 3)
    fake = SimpleNamespace(open=lambda _: io.BytesIO(b"1234"))
    monkeypatch.setattr(m, "safe_file", lambda *_: fake)
    with pytest.raises(ValueError, match="grew"):
        m.read(Path("."), "fake")


def test_duplicate_inventory_and_escaped_refs_refused(packet, monkeypatch):
    file = packet / "FINAL_MANIFEST.json"
    manifest = json.loads(file.read_bytes())
    manifest["files"].append(manifest["files"][0])
    file.write_text(json.dumps(manifest))
    pins = dict(m.PINS, **{"FINAL_MANIFEST.json": m.digest(file.read_bytes())})
    monkeypatch.setattr(m, "PINS", pins)
    with pytest.raises(ValueError, match="Duplicate"):
        m.check_packet(packet)
    manifest["files"][-1]["path"] = "../outside"
    file.write_text(json.dumps(manifest))
    pins["FINAL_MANIFEST.json"] = m.digest(file.read_bytes())
    with pytest.raises(ValueError, match="Unconfined"):
        m.check_packet(packet)


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("fixture", 30),
                                   subprocess.CalledProcessError(1, "fixture"), OSError("fixture")])
def test_semantic_failure_refuses_result(monkeypatch, failure):
    def fail(*args, **kwargs):
        assert args[0][1:4] == ["-I", "-B", "-c"]
        assert kwargs["timeout"] == 30
        raise failure
    monkeypatch.setattr(m.subprocess, "run", fail)
    with pytest.raises(ValueError, match="semantic verifier failed"):
        m.semantic_verify(SOURCE)


def test_semantic_unexpected_output(monkeypatch):
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout="not passed"))
    with pytest.raises(ValueError, match="Unexpected"):
        m.semantic_verify(SOURCE)


def test_child_rechecks_code_without_executing_mutation(packet):
    marker = packet / "MUST_NOT_EXIST"
    (packet / "acquire.py").write_text(f"open({str(marker)!r},'w').write('bad')")
    with pytest.raises(ValueError, match="semantic verifier failed"):
        m.semantic_verify(packet)
    assert not marker.exists()


@pytest.mark.parametrize("attempt", [
    "import socket; socket.socket()", "import subprocess; subprocess.run(['false'])",
    "open(__file__ + '.should-not-exist','w')", "import os; os.unlink(__file__)",
    "import os; os.open(__file__ + '.should-not-exist',os.O_CREAT)"])
def test_child_offline_readonly_defense(packet, monkeypatch, attempt):
    path = packet / "acquire.py"
    path.write_text(attempt)
    expected = path.read_bytes()
    monkeypatch.setattr(m, "PINS", dict(m.PINS, **{"acquire.py": m.digest(expected)}))
    with pytest.raises(ValueError, match="semantic verifier failed"):
        m.semantic_verify(packet)
    assert path.read_bytes() == expected
    assert not (packet / "acquire.py.should-not-exist").exists()


def test_changed_source_during_verifier_and_adaptation_refused(packet, monkeypatch):
    def alter(_):
        (packet / "native/page-0005.txt").write_text("changed")
    monkeypatch.setattr(m, "semantic_verify", alter)
    with pytest.raises(ValueError, match="changed"):
        m.lookup(packet, m.IDS[1])


def test_pre_post_identity_comparison_is_not_skipped(monkeypatch, raw):
    root, qa, receipt = raw
    monkeypatch.setattr(m, "semantic_verify", lambda _: None)
    states = iter([{"identity": "before"}, {"identity": "after"}])
    monkeypatch.setattr(m, "check_packet", lambda _: next(states))
    with pytest.raises(ValueError, match="during semantic"):
        m.lookup(root, m.IDS[0])
    states = iter([{"identity": "before"}, {"identity": "before"}, {"identity": "after"}])
    with pytest.raises(ValueError, match="during adaptation"):
        m.lookup(root, m.IDS[0])


@pytest.mark.parametrize("mutation", [
    "missing_continuation", "reverse_continuation", "missing_p6_note", "wrong_section",
    "wrong_role", "changed_offset", "changed_native", "changed_text", "duplicate_region",
    "missing_page", "changed_ids"])
def test_association_and_native_mutations_are_refused(raw, mutation):
    root, qa, receipt = raw
    qa = copy.deepcopy(qa)
    sid = m.IDS[1]
    if mutation == "missing_continuation":
        qa["selected_sections"][1]["paragraphs"][0]["fragments"].pop()
    elif mutation == "reverse_continuation":
        qa["selected_sections"][1]["paragraphs"][0]["fragments"].reverse()
    elif mutation == "missing_p6_note":
        sid = m.IDS[2]
        qa["selected_sections"][2]["ancillary_regions"].pop()
    elif mutation == "duplicate_region":
        qa["regions"].append(qa["regions"][0])
    elif mutation == "missing_page":
        qa["pages"].pop()
    elif mutation == "changed_ids":
        qa["selected_sections"][2]["section_id"] = "CRS-1-1-104"
    else:
        region = next(r for r in qa["regions"] if r["region_id"] == "S102-B1B")
        key, value = {"wrong_section": ("section_id", m.IDS[0]),
                      "wrong_role": ("role", "case_annotation"),
                      "changed_offset": ("native_start", 61),
                      "changed_native": ("native_sha256", "0" * 64),
                      "changed_text": ("text", "invented")}[mutation]
        region[key] = value
    with pytest.raises(ValueError):
        m._adapt(root, qa, receipt, sid)


def test_swapping_editor_history_roles_refused(raw):
    root, qa, receipt = raw
    qa = copy.deepcopy(qa)
    for region in qa["regions"]:
        if region["region_id"] == "S101-EDITOR":
            region["role"] = "source_history_note"
    with pytest.raises(ValueError, match="misclassified"):
        m._adapt(root, qa, receipt, m.IDS[0])


@pytest.mark.parametrize("field,value", [("legal_effective_date", "2026-01-01"),
                                          ("legal_currentness", "verified"),
                                          ("answer_safe", True), ("research_only", False)])
def test_legal_state_promotions_refused(raw, field, value):
    root, qa, receipt = raw
    qa = copy.deepcopy(qa)
    qa[field] = value
    with pytest.raises(ValueError, match="promotion"):
        m._adapt(root, qa, receipt, m.IDS[0])


@pytest.mark.parametrize("field,value", [("http_status", 403), ("tls_verification_result", 1),
                                          ("response_complete", False),
                                          ("observed_response_url", "https://example.org/"),
                                          ("redirect_location", "https://olls.info/other")])
def test_receipt_mismatch_refused(raw, field, value):
    root, qa, receipt = raw
    receipt = dict(receipt, **{field: value})
    with pytest.raises(ValueError, match="Acquisition"):
        m._adapt(root, qa, receipt, m.IDS[0])


def test_output_models_reject_insertion_scope_and_refusal_leak(actual_results):
    result = actual_results[m.IDS[0]]
    data = json.loads(result.model_dump_json())
    data["section"]["paragraphs"][0]["text"] += " altered"
    with pytest.raises(ValueError, match="Paragraph"):
        m.Result.model_validate_json(json.dumps(data))
    data = json.loads(result.model_dump_json())
    data["section"]["heading"]["native_end"] += 1
    with pytest.raises(ValueError, match="fragment"):
        m.Result.model_validate_json(json.dumps(data))
    data = json.loads(result.model_dump_json())
    data["custody"]["reviewed_physical_pages"] = [1, 2, 3, 4, 5, 6, 6]
    with pytest.raises(ValueError, match="scope"):
        m.Result.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match="Missing"):
        m.Result(status="matched", requested_section_id=m.IDS[0])
    with pytest.raises(ValueError, match="Refusal"):
        m.Result(status="refused_mode", requested_section_id=m.IDS[0], section=result.section)


def test_cli_matched_and_refused(monkeypatch, capsys, actual_results):
    monkeypatch.setattr(sys, "argv", ["lookup.py", "--section", m.IDS[0]])
    monkeypatch.setattr(m, "lookup", lambda *a, **k: actual_results[m.IDS[0]])
    m.main()
    assert json.loads(capsys.readouterr().out)["status"] == "matched"
    monkeypatch.setattr(m, "lookup", lambda *a, **k: m.Result(
        status="refused_mode", requested_section_id=m.IDS[0]))
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert exc.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "refused_mode"


@pytest.mark.parametrize("sid", m.IDS)
def test_real_cli_default_source_outside_checkout(tmp_path, sid):
    """An unrelated working directory still uses the one existing repository source packet."""
    run = subprocess.run(
        [sys.executable, "-I", "-B", str(Path(m.__file__)), "--section", sid],
        cwd=tmp_path, capture_output=True, check=True, timeout=30,
    )
    result = m.Result.model_validate_json(run.stdout)
    assert result.status == "matched" and result.section.section_id == sid
    assert result.custody.source_manifest_sha256 == m.MANIFEST_SHA
    assert result.custody.source_review_sha256 == m.QA_SHA
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("args,status", [
    (["--section", "CRS-1-1-104"], "outside_scope"),
    (["--section", "CRS-1-1-101", "--mode", "current_law"], "refused_mode"),
])
def test_real_cli_refusal_outside_checkout(tmp_path, args, status):
    """Unsupported selections and current-law mode emit no evidence or local files."""
    run = subprocess.run(
        [sys.executable, "-I", "-B", str(Path(m.__file__)), *args],
        cwd=tmp_path, capture_output=True, check=False, timeout=30,
    )
    assert run.returncode == 2
    result = m.Result.model_validate_json(run.stdout)
    assert result.status == status and result.section is None and result.custody is None
    assert not list(tmp_path.iterdir())


def test_default_source_is_existing_repo_packet():
    """Integration cannot silently substitute the old prototype or duplicate its source."""
    repo = Path(m.__file__).resolve().parents[1]
    assert m.DEFAULT_SOURCE == repo / (
        "research/local_review/crs-2026-title1-source-review-2026-09-12")
    assert m.SOURCE_PACKAGE == m.DEFAULT_SOURCE.relative_to(repo)
