"""Offline captured-source identity, native fidelity and fail-closed package tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pymupdf as fitz
import pytest

from geode.pipeline import ccr_source_text as text
from geode.pipeline.ccr_current import CCRCurrentRecord, CCRSource, CCRState, CCRVersion

BASE = "https://www.sos.state.co.us/CCR/"
FILENAME = "&fileName=1%20CCR%20100-1"
NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def pdf_bytes(blank: bool = False) -> bytes:
    """Create an actual two-page PDF with a deliberately empty second page."""
    with fitz.open() as document:
        first = document.new_page()
        if not blank:
            first.insert_text((72, 72), "Exact fee $25; except waived applications.")
        document.new_page()
        return document.tobytes()


def source(root: Path, suffix: str, body: bytes, url: str) -> CCRSource:
    """Retain a source and return its collector-compatible exact identity."""
    sha = text._sha(body)
    name = f"_RAW_ARCHIVE/ccr/current/{sha}.{suffix}"
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return CCRSource(url=BASE + url, final_url=BASE + url, path=name, sha256=sha,
                     content_type=f"application/{suffix}", bytes=len(body),
                     first_retrieved_at=NOW)


def repin(root: Path, state: CCRState, records: list[CCRCurrentRecord]) -> text.InputPlan:
    """Publish a fixture snapshot and refresh its deliberately controlled input pins."""
    inventory = text._jsonl(records)
    state = state.model_copy(update={"inventory_sha256": text._sha(inventory)})
    stem = root / (text.PREFIX + f"department-{state.department_id}")
    stem.parent.mkdir(parents=True, exist_ok=True)
    Path(str(stem) + ".jsonl").write_bytes(inventory)
    state_bytes = text._json(state)
    Path(str(stem) + "-state.json").write_bytes(state_bytes)
    return text.InputPlan(departments=[text.DepartmentInput(
        root=str(root), department_id=state.department_id,
        state_sha256=text._sha(state_bytes), inventory_sha256=text._sha(inventory),
    )])


@pytest.fixture
def packet(tmp_path: Path) -> tuple[Path, text.InputPlan, CCRState, CCRCurrentRecord]:
    """Current and future aliases share PDF bytes; history is intentionally not collected."""
    root = tmp_path / "input"
    primary = source(root, "html", b"<html>Recorded rule page</html>", "DisplayRule.do?ruleId=1")
    pdf = source(root, "pdf", pdf_bytes(), "GenerateRulePdf.do?ruleVersionId=1" + FILENAME)
    future_url = BASE + "GenerateRulePdf.do?ruleVersionId=2" + FILENAME
    future = pdf.model_copy(update={"url": future_url, "final_url": future_url})
    doc = source(root, "doc", b"Legacy Word bytes",
                 "GenerateRulePdf.do?type=word&ruleVersionId=1" + FILENAME)
    versions = [
        CCRVersion(version_id="1", source_label="Current version 9/1/2026",
                   designation="current", document_urls=[pdf.url, doc.url],
                   effective_date=date(2026, 9, 1)),
        CCRVersion(version_id="2", source_label="Future version 1/1/2027",
                   designation="future", document_urls=[future.url],
                   effective_date=date(2027, 1, 1)),
        CCRVersion(version_id="3", source_label="History", designation="history",
                   document_urls=[BASE + "GenerateRulePdf.do?ruleVersionId=3"]),
    ]
    record = CCRCurrentRecord(
        id="1_CCR_100-1", ccr_citation="1 CCR 100-1", rule_id="1", department_id="15",
        department_name="Fixture Department", agency_id="1", agency_name="Fixture Agency",
        title="Fixture rule", source_page_url=primary.url,
        source_publication_cutoff=date(2026, 9, 10), observed_at=NOW,
        classification="source_current", classification_evidence="Recorded Current version",
        selected_version_id="1", effective_date=date(2026, 9, 1), versions=versions,
        sources=[primary, pdf, future, doc],
    )
    state = CCRState(
        department_id="15", department_name=record.department_name, catalog_url=primary.url,
        welcome_url=primary.url, agency_ids=["1"], rule_ids=["1"],
        source_publication_cutoff=record.source_publication_cutoff,
        inventory_sha256="0" * 64, sources={item.url: item for item in record.sources},
    )
    return root, repin(root, state, [record]), state, record


def test_portable_full_pages_aliases_and_source_claims(packet: tuple, tmp_path: Path) -> None:
    """Reopened packages preserve aliases, exact pages and source-only status without inputs."""
    root, plan, _, _ = packet
    output = tmp_path / "package"
    manifest = text.build(plan, output)
    assert (manifest.documents, manifest.page_associations) == (3, 4)
    digest = text._sha((output / "MANIFEST.json").read_bytes())
    shutil.rmtree(root)
    moved = tmp_path / "portable"
    output.rename(moved)
    assert text.verify(moved, digest) == manifest
    result = text.query(moved, "EXCEPT WAIVED", limit=1, expected_sha256=digest)
    assert (result.total_matching_pages, result.returned_pages, result.truncated) == (2, 1, True)
    hit = result.hits[0]
    assert hit.native_text == "Exact fee $25; except waived applications.\n"
    assert hit.page.physical_page == 1 and hit.document.empty_native_pages == [2]
    assert hit.document.record.source_publication_cutoff == date(2026, 9, 10)
    assert not result.answer_safe and result.currentness == "not_verified"
    citation = text.query(moved, "1 CCR 100-1", mode="citation")
    assert citation.total_matching_pages == 4
    assert {hit.document.version.designation for hit in citation.hits} == {"current", "future"}
    documents = text._rows((moved / "documents.jsonl").read_bytes(), text.Document)
    assert [doc.extraction_status for doc in documents].count("unsupported_format") == 1
    assert text.query(moved, "unlisted wording").total_matching_pages == 0
    assert "deleted text" in result.warning


@pytest.mark.parametrize("status", ["source_repealed", "future_effective", "ambiguous"])
def test_classifications_never_promoted(packet: tuple, tmp_path: Path, status: str) -> None:
    """Source designations survive without a derived applicability claim."""
    root, _, state, record = packet
    plan = repin(root, state, [record.model_copy(update={"classification": status})])
    output = tmp_path / "package"
    text.build(plan, output)
    hit = text.query(output, "$25").hits[0]
    assert hit.document.record.classification == status and not hit.document.answer_safe


@pytest.mark.parametrize("damage", ["missing", "hash", "lfs", "symlink"])
def test_original_refusals_before_output(packet: tuple, tmp_path: Path, damage: str) -> None:
    """Unavailable or substituted source evidence never publishes a package."""
    root, plan, _, record = packet
    path = root / record.sources[1].path
    if damage == "missing":
        path.unlink()
    elif damage == "hash":
        path.write_bytes(b"Different document")
    elif damage == "lfs":
        path.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
    else:
        body = path.read_bytes()
        path.unlink()
        other = tmp_path / "other.pdf"
        other.write_bytes(body)
        path.symlink_to(other)
    output = tmp_path / "package"
    with pytest.raises(ValueError):
        text.build(plan, output)
    assert not output.exists()


@pytest.mark.parametrize("field,value", [
    ("department_id", "14"), ("department_name", "Wrong owner"), ("agency_id", "2"),
    ("selected_version_id", "999"), ("source_page_url", BASE + "other.do"),
    ("source_publication_cutoff", date(2000, 1, 1)),
])
def test_bad_record_joins(packet: tuple, tmp_path: Path, field: str, value: Any) -> None:
    """Resealed but inconsistent collector metadata fails the cross-record contract."""
    root, _, state, record = packet
    plan = repin(root, state, [record.model_copy(update={field: value})])
    with pytest.raises(ValueError):
        text.build(plan, tmp_path / "package")


@pytest.mark.parametrize("case", ["duplicate_rule", "duplicate_version", "duplicate_url",
                                  "missing_document", "source_map", "foreign_source"])
def test_duplicate_and_incomplete_joins(packet: tuple, tmp_path: Path, case: str) -> None:
    """No duplicate IDs, fabricated source associations or missing version documents."""
    root, _, state, record = packet
    records = [record]
    if case == "duplicate_rule":
        records.append(record)
    elif case == "duplicate_version":
        record = record.model_copy(update={"versions": record.versions + [record.versions[0]]})
    elif case == "duplicate_url":
        version = record.versions[0].model_copy(update={
            "document_urls": [record.sources[1].url, record.sources[1].url]})
        record = record.model_copy(update={"versions": [version]})
    elif case == "missing_document":
        record = record.model_copy(update={"sources": [record.sources[0]]})
    elif case == "source_map":
        sources = dict(state.sources)
        sources[BASE + "unrelated.do"] = sources.pop(record.sources[0].url)
        state = state.model_copy(update={"sources": sources})
    else:
        changed = record.sources[1].model_copy(update={"first_retrieved_at": NOW.replace(day=22)})
        record = record.model_copy(update={"sources": [record.sources[0], changed]})
    if case != "duplicate_rule":
        records = [record]
    plan = repin(root, state, records)
    with pytest.raises(ValueError):
        text.build(plan, tmp_path / "package")


def test_captured_pdf_and_metadata_not_reread(
    packet: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Late disk substitution cannot inject unverified text after capture, including ABA."""
    root, plan, _, record = packet
    original = text._capture

    def capture_then_replace(value: text.InputPlan) -> dict[str, bytes]:
        """Alter disk only after all input buffers have passed their exact checks."""
        buffers = original(value)
        (root / record.sources[1].path).write_bytes(b"Injected after checked capture")
        state = root / (text.PREFIX + "department-15-state.json")
        state.write_bytes(b"not the captured state")
        return buffers

    monkeypatch.setattr(text, "_capture", capture_then_replace)
    output = tmp_path / "package"
    text.build(plan, output)
    assert text.query(output, "Exact fee").total_matching_pages == 2
    assert text.query(output, "Injected").total_matching_pages == 0


@pytest.mark.parametrize("damage", ["page", "schema", "extra", "directory", "symlink",
                                   "duplicate", "self", "resealed_page"])
def test_package_tamper_refusal(packet: tuple, tmp_path: Path, damage: str) -> None:
    """Closed membership and deterministic extraction reject even resealed native edits."""
    output = tmp_path / "package"
    text.build(packet[1], output)
    manifest_path = output / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_bytes())
    if damage in {"page", "resealed_page"}:
        name = next(item["path"] for item in manifest["files"]
                    if item["path"].startswith("native/"))
        (output / name).write_bytes(b"Substituted obligation")
        if damage == "resealed_page":
            for index, asset in enumerate(manifest["files"]):
                if asset["path"] == name:
                    asset = text._asset(name, (output / name).read_bytes())
                    manifest["files"][index] = asset.model_dump()
    elif damage == "schema":
        (output / "schemas/Page.json").write_bytes(b"{}")
    elif damage == "extra":
        (output / "unexpected.txt").write_bytes(b"extra")
    elif damage == "directory":
        (output / "extra_directory").mkdir()
    elif damage == "symlink":
        (output / "link").symlink_to(output / "pages.jsonl")
    elif damage == "duplicate":
        manifest["files"].append(manifest["files"][0])
    else:
        manifest["files"].append(text._asset("MANIFEST.json", b"self").model_dump())
    manifest_path.write_bytes(text._json(manifest))
    with pytest.raises(ValueError):
        text.verify(output)


def test_extraction_empty_corrupt_and_encrypted() -> None:
    """Scanned/blank native text remains empty; corrupt and encrypted PDFs fail closed."""
    assert text.extract_pdf_pages(pdf_bytes(blank=True)) == [b"", b""]
    with pytest.raises(ValueError, match="magic"):
        text.extract_pdf_pages(b"<html>Not a PDF</html>")
    with pytest.raises(ValueError):
        text.extract_pdf_pages(b"%PDF-1.7\ncorrupt")
    with fitz.open(stream=pdf_bytes(), filetype="pdf") as document:
        encrypted = document.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner",
                                     user_pw="reader")
    with pytest.raises(ValueError, match="Encrypted"):
        text.extract_pdf_pages(encrypted)


@pytest.mark.parametrize("cap", ["MAX_TOTAL_BYTES", "MAX_FILES", "MAX_DOCUMENTS",
                                 "MAX_PAGES", "MAX_TEXT_BYTES"])
def test_runtime_caps(packet: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                      cap: str) -> None:
    """Each independent runtime budget stops work before publishing."""
    monkeypatch.setattr(text, cap, 1)
    with pytest.raises(ValueError):
        text.build(packet[1], tmp_path / "package")


@pytest.mark.parametrize("query,mode,limit", [("", "phrase", 10), ("x" * 501, "phrase", 1),
                                            ("fee", "current_law", 1), ("fee", "phrase", 0)])
def test_query_contract_refuses_without_package(query: str, mode: str, limit: int) -> None:
    """No empty inventory dump or legal-answer mode; validate before package access."""
    with pytest.raises(ValueError):
        text.query(Path("missing"), query, mode=mode, limit=limit)


def test_paths_existing_output_and_cli(packet: tuple, tmp_path: Path,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    """CLI build/verify/query is read-only after creation, with meaningful refusal status."""
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(text._json(packet[1]))
    output = tmp_path / "package"
    assert text.main(["build", "--plan", str(plan_path), "--output", str(output)]) == 0
    assert text.main(["verify", "--package", str(output)]) == 0
    assert text.main(["query", "--package", str(output), "--text", "$25"]) == 0
    assert text.main(["build", "--plan", str(plan_path), "--output", str(output)]) == 2
    assert text.main(["verify", "--package", str(output), "--manifest-sha256", "0" * 64]) == 2
    assert "refusal" in capsys.readouterr().err
    with pytest.raises(ValueError):
        text.build(packet[1], tmp_path / "_RAW_ARCHIVE" / "bad")
    with pytest.raises(ValueError):
        text._absolute(tmp_path / ".." / "other")
    with pytest.raises(ValueError):
        text.Asset(path="../escape", sha256="0" * 64, size_bytes=0)
    with pytest.raises(ValueError):
        text.InputPlan(departments=packet[1].departments * 2)


def test_failed_write_leaves_no_valid_partial_package(
    packet: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An ordinary publication exception cleans its exclusively created output."""
    def fail(*args: Any) -> None:
        """Represent an ordinary filesystem failure during publication."""
        raise OSError("Fixture disk write failure")

    monkeypatch.setattr(text.os, "replace", fail)
    output = tmp_path / "package"
    with pytest.raises(OSError):
        text.build(packet[1], output)
    assert not output.exists()


def test_returned_buffer_substitution_fails_even_after_disk_restored(
    packet: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hash the actual consumed bytes, not a later honest reread that hides an ABA change."""
    root, plan, _, record = packet
    original_read = text._read
    target = root / record.sources[1].path

    def dishonest_read(path: Path, limit: int = text.MAX_FILE_BYTES) -> bytes:
        """Return substituted bytes while leaving authentic bytes on disk."""
        body = original_read(path, limit)
        return b"Unverified substitute" if path == target else body

    monkeypatch.setattr(text, "_read", dishonest_read)
    with pytest.raises(ValueError, match="hash/size"):
        text.build(plan, tmp_path / "package")
    assert text._sha(target.read_bytes()) == record.sources[1].sha256


def test_query_uses_captured_text_after_package_disk_change(
    packet: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verified native bytes remain the only query input even if disk changes afterward."""
    output = tmp_path / "package"
    text.build(packet[1], output)
    original_outputs = text._outputs

    def change_after_capture(files: dict[str, bytes]) -> tuple[dict[str, bytes], text.Manifest]:
        """Inject on disk after the verifier has captured all package members."""
        page = next((output / "native").rglob("00001.txt"))
        page.write_bytes(b"Injected later")
        return original_outputs(files)

    monkeypatch.setattr(text, "_outputs", change_after_capture)
    result = text.query(output, "Exact fee")
    assert result.total_matching_pages == 2
    assert all("Injected" not in hit.native_text for hit in result.hits)


def test_version_url_mismatch_rejects_resealed_metadata(packet: tuple, tmp_path: Path) -> None:
    """A version cannot claim the retained bytes of another URL/version identity."""
    root, _, state, record = packet
    version = record.versions[0].model_copy(update={"document_urls": [record.sources[2].url]})
    record = record.model_copy(update={"versions": [version]})
    with pytest.raises(ValueError, match="version/citation"):
        text.build(repin(root, state, [record]), tmp_path / "package")


def test_subprocess_cli_stdout_is_validated_json(packet: tuple, tmp_path: Path) -> None:
    """An external caller receives pure machine JSON, not a deprecated-import notice."""
    package = tmp_path / "package"
    text.build(packet[1], package)
    repo = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-B", "-m", "geode.pipeline.ccr_source_text", "query",
               "--package", str(package), "--text", "waived"]
    run = subprocess.run(command, cwd=tmp_path, capture_output=True, check=False,
                         env=dict(os.environ, PYTHONPATH=str(repo)), timeout=30)
    assert run.returncode == 0, run.stderr.decode()
    result = text.QueryResult.model_validate_json(run.stdout)
    assert result.returned_pages == 2 and not result.answer_safe


@pytest.mark.parametrize("requested,final,valid", [
    ("&deptID=15&agencyID=1", "&deptID=15&agencyID=1", True),
    ("&deptID=12", "&deptID=12", False),
    ("&agencyID=99", "&agencyID=99", False),
    ("", "&deptID=12", False),
    ("", "&agencyID=99", False),
    ("", "&ruleId=999", False),
    ("&deptID=15&deptID=12", "&deptID=15", False),
    ("&deptID=", "", False),
    ("&agencyID=1", "", False),
])
def test_primary_requested_and_redirect_identities(
    packet: tuple, tmp_path: Path, requested: str, final: str, valid: bool,
) -> None:
    """Explicit web identity fields must agree; no CCR citation-prefix inference is used."""
    root, _, state, record = packet
    prior = record.sources[0]
    primary = prior.model_copy(update={"url": prior.url + requested,
                                       "final_url": prior.final_url + final})
    sources = dict(state.sources)
    del sources[prior.url]
    sources[primary.url] = primary
    state = state.model_copy(update={"sources": sources})
    record = record.model_copy(update={"source_page_url": primary.url,
                                       "sources": [primary, *record.sources[1:]]})
    plan = repin(root, state, [record])
    if valid:
        assert text.build(plan, tmp_path / "package").departments == 1
    else:
        with pytest.raises(ValueError):
            text.build(plan, tmp_path / "package")


def test_extended_source_citation_is_exact_and_separate(packet: tuple, tmp_path: Path) -> None:
    """A suffix is preserved in metadata, URL and query identity, never flattened away."""
    root, _, state, record = packet
    citation = "1 CCR 100-1 Appendix A"
    old_part = quote(record.ccr_citation)
    new_part = quote(citation)
    replacements = {
        item.url: item.model_copy(update={
            "url": item.url.replace(old_part, new_part),
            "final_url": item.final_url.replace(old_part, new_part),
        }) for item in record.sources
    }
    sources = {item.url: item for item in replacements.values()}
    versions = [version.model_copy(update={
        "document_urls": [url.replace(old_part, new_part) for url in version.document_urls],
    }) for version in record.versions]
    record = record.model_copy(update={
        "id": text.record_identity(citation, record.rule_id), "ccr_citation": citation,
        "versions": versions, "sources": list(replacements.values()),
    })
    assert record.id == "1_CCR_100-1__rule_1"
    state = state.model_copy(update={"sources": sources})
    package = tmp_path / "package"
    text.build(repin(root, state, [record]), package)
    result = text.query(package, citation, mode="citation")
    assert result.total_matching_pages == 4
    assert all(hit.document.record.ccr_citation == citation for hit in result.hits)
    assert text.query(package, "1 CCR 100-1", mode="citation").total_matching_pages == 0
    flattened = record.model_copy(update={"id": "1_CCR_100-1"})
    with pytest.raises(ValueError, match="identity"):
        text.build(repin(root, state, [flattened]), tmp_path / "bad-package")


@pytest.fixture
def selected_packet(packet: tuple) -> tuple:
    """Two different PDF originals retain complete current/future and Word associations."""
    root, plan, state, record = packet
    with fitz.open() as pdf:
        for _ in range(3):
            pdf.new_page().insert_text((72, 72), "Unselected future fee $900.")
        body = pdf.tobytes()
    prior = record.sources[2]
    other = source(root, "pdf", body, prior.url.removeprefix(BASE))
    sources = [record.sources[0], record.sources[1], other, record.sources[3]]
    state = state.model_copy(update={"sources": {item.url: item for item in sources}})
    record = record.model_copy(update={"sources": sources})
    plan = repin(root, state, [record])
    selection = text.SelectedInputPlan(
        departments=plan.departments, selected_pdf_sha256=[record.sources[1].sha256],
    )
    return root, selection, state, record


def test_v1_schema_bytes_remain_exact() -> None:
    """Preexisting package schema bytes stay compatible, including nested source models."""
    expected = {
        "InputPlan": "67ec07c132afe892f71a8f8d05786941732f965b7686f5816146446d016861ff",
        "Document": "ebca662625d06e5a1b0f24453340b51ef8f09a2dea5dd5010bbd94269b546907",
        "Page": "034dd483ee83982931cb899fd58c5e6f4d8dc914349d1e26e9bc2d3d21a693aa",
        "Manifest": "52679b78ce8883d311f2133d22d4c5685f1204f187bd7fbdc89aad2d19d75258",
        "QueryResult": "9e163cac80bdf8d2bc57c75b111475bc9d9934f2e8459e79fb1f416380e17a5a",
    }
    assert {name: text._sha(body) for name, body in text._schemas().items()} == {
        f"schemas/{name}.json": digest for name, digest in expected.items()
    }


def test_selected_preserves_all_sources_and_explicit_omissions(
    selected_packet: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only selected PDF buffers reach extraction; all source/association custody survives."""
    root, plan, _, record = selected_packet
    original = text.extract_pdf_pages
    extracted = []

    def selected_only(body: bytes) -> list[bytes]:
        """Fail if native extraction touches the intentionally unselected PDF."""
        digest = text._sha(body)
        assert digest in plan.selected_pdf_sha256
        extracted.append(digest)
        return original(body)

    monkeypatch.setattr(text, "extract_pdf_pages", selected_only)
    output = tmp_path / "selected"
    manifest = text.build(plan, output)
    assert isinstance(manifest, text.SelectedManifest) and manifest.version == 2
    assert (manifest.documents, manifest.page_associations,
            manifest.unique_pdf_originals) == (3, 2, 1)
    assert manifest.selection.unselected_pdf_originals == 1
    assert manifest.selection.selected_document_associations == 1
    assert manifest.selection.unselected_document_associations == 1
    assert set(extracted) == set(plan.selected_pdf_sha256)
    for source_record in record.sources:
        assert (output / text._original(source_record)).read_bytes() == (
            root / source_record.path
        ).read_bytes()
    for suffix, name in (("-state.json", "state.json"), (".jsonl", "inventory.jsonl")):
        assert (output / "inputs/15" / name).read_bytes() == (
            root / (text.PREFIX + "department-15" + suffix)
        ).read_bytes()
    documents = text._rows((output / "documents.jsonl").read_bytes(), text.SelectedDocument)
    omitted = next(doc for doc in documents if doc.selection_status == "unselected_pdf")
    assert omitted.extraction_status == "intentionally_unselected"
    assert omitted.physical_pages is None and omitted.empty_native_pages == []
    assert omitted.extraction_method == "not_extracted"
    assert manifest.unsupported_documents == 1
    pin = text._sha((output / "MANIFEST.json").read_bytes())
    shutil.rmtree(root)
    assert text.verify(output, pin) == manifest
    found = text.query(output, "except", expected_sha256=pin)
    assert isinstance(found, text.SelectedQueryResult) and found.total_matching_pages == 1
    missing = text.query(output, "$900", expected_sha256=pin)
    assert missing.total_matching_pages == 0 and missing.selection == manifest.selection
    assert "department-wide absence" in missing.selection_warning
    assert not missing.selection.complete_department_native_text
    assert missing.unsupported_documents == 1 and missing.currentness == "not_verified"


def test_selector_keeps_every_shared_pdf_alias(packet: tuple, tmp_path: Path) -> None:
    """A whole original is indivisible across current/future and URL associations."""
    _, plan, _, record = packet
    plan = text.SelectedInputPlan(
        departments=plan.departments, selected_pdf_sha256=[record.sources[1].sha256],
    )
    output = tmp_path / "aliases"
    manifest = text.build(plan, output)
    assert manifest.selection.selected_document_associations == 2
    assert manifest.selection.unselected_document_associations == 0
    assert manifest.selection.unselected_pdf_originals == 0
    assert not manifest.selection.complete_department_native_text
    result = text.query(output, "1 CCR 100-1", mode="citation")
    assert result.total_matching_pages == 4
    assert {hit.document.version.designation for hit in result.hits} == {"current", "future"}


@pytest.mark.parametrize("case", ["empty", "duplicate", "unsorted", "bad_hash", "pages"])
def test_invalid_selection_structure_refused(packet: tuple, case: str) -> None:
    """No blank, duplicate, noncanonical or page-range selector can split original custody."""
    _, plan, _, record = packet
    digest = record.sources[1].sha256
    data = {"version": 2, "departments": plan.model_dump()["departments"],
            "selected_pdf_sha256": [digest]}
    if case == "empty":
        data["selected_pdf_sha256"] = []
    elif case == "duplicate":
        data["selected_pdf_sha256"] = [digest, digest]
    elif case == "unsorted":
        data["selected_pdf_sha256"] = ["f" * 64, "0" * 64]
    elif case == "bad_hash":
        data["selected_pdf_sha256"] = ["../unknown"]
    else:
        data["selected_pages"] = [1]
    with pytest.raises(ValueError):
        text.PLAN_ADAPTER.validate_python(data)


@pytest.mark.parametrize("case", ["unknown", "word", "catalog_pdf"])
def test_noneligible_hash_selection_fails_before_publication(
    selected_packet: tuple, tmp_path: Path, case: str,
) -> None:
    """Only PDFs associated with admitted versions can be selected, not arbitrary inputs."""
    root, plan, state, record = selected_packet
    if case == "catalog_pdf":
        extra = source(root, "pdf", pdf_bytes(), "unused-catalog.pdf")
        state = state.model_copy(update={"sources": {**state.sources, extra.url: extra}})
        pinned = repin(root, state, [record])
        plan = text.SelectedInputPlan(departments=pinned.departments,
                                      selected_pdf_sha256=[extra.sha256])
    else:
        digest = "0" * 64 if case == "unknown" else record.sources[3].sha256
        plan = text.SelectedInputPlan(departments=plan.departments, selected_pdf_sha256=[digest])
    with pytest.raises(ValueError, match="unknown or noneligible"):
        text.build(plan, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("case", ["changed", "missing", "bad_magic", "corrupt", "encrypted"])
def test_unselected_source_still_fails_closed(
    selected_packet: tuple, tmp_path: Path, case: str,
) -> None:
    """Selection cannot hide missing/hash-changed or structurally invalid original PDFs."""
    root, plan, state, record = selected_packet
    prior = record.sources[2]
    if case in {"changed", "missing"}:
        path = root / prior.path
        if case == "changed":
            path.write_bytes(b"changed original")
        else:
            path.unlink()
    else:
        body = b"not PDF" if case == "bad_magic" else b"%PDF-1.7\nbroken"
        if case == "encrypted":
            with fitz.open(stream=pdf_bytes(), filetype="pdf") as pdf:
                body = pdf.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,
                                   owner_pw="owner", user_pw="reader")
        bad = source(root, "pdf", body, prior.url.removeprefix(BASE))
        sources = [record.sources[0], record.sources[1], bad, record.sources[3]]
        state = state.model_copy(update={"sources": {item.url: item for item in sources}})
        record = record.model_copy(update={"sources": sources})
        pinned = repin(root, state, [record])
        plan = text.SelectedInputPlan(departments=pinned.departments,
                                      selected_pdf_sha256=plan.selected_pdf_sha256)
    with pytest.raises(ValueError):
        text.build(plan, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("case", ["omission_count", "complete_claim", "selected_hash"])
def test_resealed_selection_claims_refused(
    selected_packet: tuple, tmp_path: Path, case: str,
) -> None:
    """Re-sealing cannot erase omitted scope, claim completeness or substitute a selector."""
    output = tmp_path / "package"
    text.build(selected_packet[1], output)
    path = output / "MANIFEST.json"
    manifest = json.loads(path.read_bytes())
    if case == "omission_count":
        manifest["selection"]["unselected_document_associations"] = 0
    elif case == "complete_claim":
        manifest["selection"]["complete_department_native_text"] = True
    else:
        manifest["selection"]["selected_pdf_sha256"] = ["0" * 64]
    path.write_bytes(text._json(manifest))
    with pytest.raises(ValueError):
        text.verify(output)


def test_selected_cli_and_scope_schema(
    selected_packet: tuple, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """V2 CLI results parse under their explicit schema and preserve omissions on no match."""
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(text._json(selected_packet[1]))
    output = tmp_path / "package"
    assert text.main(["build", "--plan", str(plan_path), "--output", str(output)]) == 0
    manifest = text.SelectedManifest.model_validate_json(capsys.readouterr().out)
    assert manifest.version == 2
    assert text.main(["query", "--package", str(output), "--text", "absent"]) == 0
    result = text.SelectedQueryResult.model_validate_json(capsys.readouterr().out)
    assert result.selection.unselected_pdf_originals == 1
    assert result.hits == [] and not result.answer_safe
    with pytest.raises(ValueError):
        text.QueryResult.model_validate_json(result.model_dump_json())
