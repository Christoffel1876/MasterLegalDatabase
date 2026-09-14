"""Failure-oriented checks for the fixed derived CRS metadata prototype."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol

import pytest
from pydantic import ValidationError

from geode.pipeline import research_catalog as rc
from geode.schemas import LayerIndexRecord, StatuteSection


class SaveFixture(Protocol):
    """Rewrite synthetic fixture inputs and optionally refresh their test-only pins."""

    def __call__(
        self, values: list[bytes] | None = None, *, repin: bool = True,
    ) -> list[bytes]:
        """Save the selected synthetic bytes."""
        ...


Fixture = tuple[
    Path, Path, list[bytes], list[dict[str, Any]], list[dict[str, Any]], SaveFixture,
]


def dump(value: object) -> bytes:
    """Serialize synthetic fixture data with its original newline."""
    return json.dumps(value, ensure_ascii=False).encode() + b"\n"


@pytest.fixture
def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    """Create three schema-validated synthetic sections and test-only input pins."""
    root = tmp_path / "repository"
    root.mkdir()
    index, metadata = [], []
    markdown = b"# Title 1 - ELECTIONS\n\n"
    for n, identity in enumerate(rc.IDS, 101):
        text = f"Fixture election section {n}; preserve \u00a7, exceptions and conditions."
        heading = f"Heading {n}."
        row = dict(entity_type="statute_section", id=identity, title_num="1",
                   title_name="ELECTIONS",
                   article_num="1", article_name="Elections Generally", section_num=f"1-1-{n}",
                   section_heading=heading, full_text=text,
                   source_url="https://leg.colorado.gov/colorado-revised-statutes",
                   data_retrieved="2026-07-02", data_version="2025_official_sgml",
                   confidence={"overall": 1.0})
        StatuteSection.model_validate(row)
        metadata.append(row)
        ir = dict(id=identity, layer="01_Statutes_CRS", entity_type="statute_section",
                  title=f"{identity}: {heading}", citation=identity, path=rc.INPUTS[2][0],
                  meta_path=rc.INPUTS[1][0], source_url=row["source_url"],
                  source_path="C:/legacy/title01.txt", publication_year=2025,
                  last_updated="2026-07-02T19:53:23Z", sha256=rc._sha(text.encode()),
                  confidence=1.0)
        LayerIndexRecord.model_validate(ir)
        index.append(ir)
        markdown += f"#### 1-1-{n}. {heading}\n\n{text}\n\n".encode()
    markdown += b"#### 1-1-104. Outside admitted scope.\n\nNot selected.\n"
    content = [b"".join(map(dump, index)), b"".join(map(dump, metadata)), markdown]

    def save(
        values: list[bytes] | None = None, *, repin: bool = True,
    ) -> list[bytes]:
        """Write controlled test bytes without changing production input pins."""
        values = content if values is None else values
        pins = []
        for spec, data in zip(rc.INPUTS, values, strict=True):
            path = root / spec[0]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            pins.append((spec[0], spec[1], len(data), rc._sha(data)))
        if repin:
            monkeypatch.setattr(rc, "INPUTS", tuple(pins))
        return values

    save()
    return root, root / rc.OUTPUT_ROOT / "fixture", content, index, metadata, save


def build(fixture: Fixture) -> Path:
    """Build a package entirely inside the synthetic repository."""
    root, output, *_ = fixture
    rc.build_package(root, output)
    return output


def file_state(path: Path) -> dict[str, tuple[int, str]]:
    """Record file bytes and timestamps for read-only assertions."""
    return {p.relative_to(path).as_posix(): (p.stat().st_mtime_ns, rc._sha(p.read_bytes()))
            for p in path.rglob("*") if p.is_file()}


def test_complete_metadata_and_read_only_query(fixture: Fixture) -> None:
    """Preserve exact selected metadata and source offsets without query writes."""
    output = build(fixture)
    before = file_state(output)
    result = rc.query_package(output, list_records=True)
    assert [r.id for r in result.records] == list(rc.IDS)
    assert result.status == "matched" and not result.answer_safe
    for record in result.records:
        assert record.input_kind == "derived_record_only"
        assert record.original_custody == "unresolved_nonportable_path"
        assert record.claims.recorded_original_path == "C:/legacy/title01.txt"
        assert record.claims.recorded_effective_date is None
        assert record.claims.recorded_data_version == "2025_official_sgml"
        assert record.claims.recorded_metadata_retrieved_date.isoformat() == "2026-07-02"
        assert "full_text" not in record.model_dump()
        for span in (record.index_line, record.metadata_line, record.heading, record.body):
            assert rc._sha((output / span.path).read_bytes()[span.start:span.end]) == span.sha256
    assert len(rc.query_package(output, "101").records) == 1
    absent = rc.query_package(output, "not-in-this-subset")
    assert absent.status == "no_matching_record" and not absent.answer_safe
    assert "absence" in absent.boundary
    assert file_state(output) == before


def test_deterministic_payload_and_separate_receipt(fixture: Fixture) -> None:
    """Keep catalog bytes stable while separating actual package creation time."""
    output = build(fixture)
    second = output.with_name("replay")
    rc.build_package(fixture[0], second)
    for name in (rc.CATALOG, "manifest.json", "schema.json"):
        assert (output / name).read_bytes() == (second / name).read_bytes()
    one = rc.Receipt.model_validate_json((output / "receipt.json").read_bytes())
    two = rc.Receipt.model_validate_json((second / "receipt.json").read_bytes())
    assert one.created_at <= two.created_at
    assert one.original_acquisition_time is None
    assert one.manifest_sha256 == two.manifest_sha256
    with pytest.raises(ValueError, match="already exists"):
        rc.build_package(fixture[0], output)


@pytest.mark.parametrize("query,mode", [("What applies?", "source"), ("current law", "source"),
                                        (None, "current-law")])
def test_refusal_never_reads_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: str | None, mode: str,
) -> None:
    """Refuse legal requests before accessing any package evidence."""
    monkeypatch.setattr(rc, "validate_package", lambda p: pytest.fail("Refusal opened evidence"))
    result = rc.query_package(tmp_path / "absent", query, list_records=query is None, mode=mode)
    assert result.status == "refused_current_law" and not result.records
    assert result.package_path is None


@pytest.mark.parametrize("kwargs", [{}, {"query": "x", "list_records": True}, {"query": ""},
                                     {"query": " "}, {"query": "x" * 513},
                                     {"query": "x", "mode": "legal"}])
def test_invalid_query_contract(tmp_path: Path, kwargs: dict[str, Any]) -> None:
    """Reject empty, oversized, ambiguous and unsupported query contracts."""
    with pytest.raises(ValueError):
        rc.query_package(tmp_path, **kwargs)


@pytest.mark.parametrize("kind", ["index_duplicate", "meta_duplicate", "missing", "bad_sha",
    "bad_title", "bad_citation", "bad_path", "bad_meta_path", "bad_url", "bad_layer",
    "bad_entity", "bad_metadata_id", "bad_title_name", "bad_original_path",
    "body_difference", "duplicate_heading", "missing_heading", "body_addition",
    "nonobject", "blank", "unknown_meta_field", "trimmed_text"])
def test_selected_identity_and_body_gates(fixture: Fixture, kind: str) -> None:
    """Reject mismatched or incomplete inputs before writing staging directories."""
    root, output, content, indexes, metadata, save = fixture
    content = list(content)
    if kind == "index_duplicate":
        indexes.append(indexes[0])
    elif kind == "meta_duplicate":
        metadata.append(metadata[0])
    elif kind == "missing":
        indexes.pop()
    elif kind == "bad_sha":
        indexes[0]["sha256"] = "0" * 64
    elif kind == "bad_title":
        indexes[0]["title"] = "Another title"
    elif kind == "bad_citation":
        indexes[0]["citation"] = "CRS-1-1-104"
    elif kind == "bad_path":
        indexes[0]["path"] = "elsewhere.md"
    elif kind == "bad_meta_path":
        indexes[0]["meta_path"] = "elsewhere.jsonl"
    elif kind == "bad_url":
        indexes[0]["source_url"] = "https://www.sos.state.co.us/"
    elif kind == "bad_layer":
        indexes[0]["layer"] = "02_Regulations_CCR"
    elif kind == "bad_entity":
        indexes[0]["entity_type"] = "bill"
    elif kind == "bad_metadata_id":
        metadata[0]["article_num"] = "2"
    elif kind == "bad_title_name":
        metadata[0]["title_name"] = "Other title"
    elif kind == "bad_original_path":
        indexes[0]["source_path"] = "local.txt"
    elif kind == "unknown_meta_field":
        metadata[0]["invented"] = True
    elif kind == "trimmed_text":
        metadata[0]["full_text"] = " " + metadata[0]["full_text"]
    elif kind == "body_difference":
        content[2] = content[2].replace(b"section 101", b"section 999")
    elif kind == "duplicate_heading":
        content[2] += b"#### 1-1-101. Heading 101.\n\n"
    elif kind == "missing_heading":
        content[2] = content[2].replace(b"Heading 101.", b"Wrong heading")
    elif kind == "body_addition":
        content[2] = content[2].replace(
            b"\n\n#### 1-1-102", b"\n\nOmitted clause\n\n#### 1-1-102",
        )
    content[0] = b"".join(map(dump, indexes))
    content[1] = b"".join(map(dump, metadata))
    if kind == "nonobject":
        content[0] += b"[]\n"
    if kind == "blank":
        content[0] += b"\n"
    save(content)
    with pytest.raises((ValueError, KeyError)):
        rc.build_package(root, output)
    assert not (root / rc.OUTPUT_ROOT).exists(), "Validation failure wrote output directories"


@pytest.mark.parametrize("relative", ["manifest.json", rc.CATALOG, "schema.json", "inputs/body.md",
                                      "receipt.json"])
def test_package_tamper_rejected(fixture: Fixture, relative: str) -> None:
    """Reject changes to frozen source, catalog, schema and receipt bindings."""
    output = build(fixture)
    path = output / relative
    path.write_bytes(path.read_bytes() + b" ")
    # Receipt whitespace is semantically harmless; changing its binding is not.
    if relative == "receipt.json":
        data = json.loads(path.read_bytes()); data["manifest_sha256"] = "0" * 64
        path.write_bytes(dump(data))
    with pytest.raises(ValueError):
        rc.query_package(output, list_records=True)


@pytest.mark.parametrize("kind", ["extra_file", "extra_directory", "symlink", "missing", "fifo"])
def test_closed_inventory(fixture: Fixture, kind: str) -> None:
    """Reject missing, extra, symbolic and nonregular package entries."""
    output = build(fixture)
    if kind == "extra_file":
        (output / "unlisted").write_text("x")
    elif kind == "extra_directory":
        (output / "unlisted").mkdir()
    elif kind == "symlink":
        (output / "unlisted").symlink_to(output / "schema.json")
    elif kind == "missing":
        (output / rc.CATALOG).unlink()
    else: os.mkfifo(output / "unlisted")
    with pytest.raises(ValueError): rc.validate_package(output)


@pytest.mark.parametrize("kind", ["input_symlink", "root_symlink", "ancestor_symlink", "outside",
                                  "traversal", "bad_name", "input_hash", "input_pointer"])
def test_build_path_and_input_preflight(fixture: Fixture, tmp_path: Path, kind: str) -> None:
    """Constrain every build path and reject changed or unhydrated inputs."""
    root, output, content, _, _, save = fixture
    if kind == "input_symlink":
        p = root / rc.INPUTS[2][0]; p.unlink(); p.symlink_to(tmp_path / "absent")
    elif kind == "root_symlink":
        link = tmp_path / "link"; link.symlink_to(root, target_is_directory=True); root = link
    elif kind == "ancestor_symlink":
        (root / ".geode_runtime").symlink_to(tmp_path, target_is_directory=True)
    elif kind == "outside":
        output = tmp_path / "outside"
    elif kind == "traversal":
        output = output.parent / ".." / "escape"
    elif kind == "bad_name":
        output = output.with_name(".hidden")
    elif kind == "input_hash":
        (root / rc.INPUTS[2][0]).write_text("changed")
    else:
        values = list(content); values[2] = b"version https://git-lfs.github.com/spec/v1\n"
        save(values)
    with pytest.raises(ValueError): rc.build_package(root, output)
    assert not output.is_dir()


def test_bounds_and_regular_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fixture: Fixture,
) -> None:
    """Enforce independent file, JSONL and total-byte limits."""
    path = tmp_path / "x"; path.write_bytes(b"abcdef")
    with pytest.raises(ValueError): rc._read(tmp_path, "x", 3)
    with pytest.raises(ValueError): rc._read(tmp_path, "../x")
    with pytest.raises(ValueError): rc._read(tmp_path, str(path))
    with pytest.raises(ValueError): rc._read(tmp_path, "missing")
    with pytest.raises(ValueError): rc._selected(b'{}\n{}\n', "x", 1)
    with pytest.raises(ValueError): rc._selected(b'x' * 2_000_001, "x", 10)
    monkeypatch.setattr(rc, "MAX_TOTAL", 1)
    with pytest.raises(ValueError): rc._inputs(fixture[0], False)


def test_stage_failure_cleans_up_and_preserves_inputs(
    fixture: Fixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean failed staging while leaving all original fixture files unchanged."""
    root, output, *_ = fixture
    before = file_state(root)
    monkeypatch.setattr(rc, "validate_package", lambda p: (_ for _ in ()).throw(ValueError("fail")))
    with pytest.raises(ValueError): rc.build_package(root, output)
    assert not output.exists()
    assert list((root / rc.OUTPUT_ROOT).iterdir()) == []
    assert file_state(root) == before


def test_destination_appearing_during_build_is_preserved(
    fixture: Fixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Never replace an output that appears while the staged package is verified."""
    root, output, *_ = fixture
    original = rc.validate_package
    def validate(stage: Path) -> tuple[rc.Manifest, tuple[rc.ResearchRecord, ...]]:
        """Simulate a destination created after staging validation."""
        result = original(stage)
        output.mkdir(); (output / "owned").write_text("preserve")
        return result
    monkeypatch.setattr(rc, "validate_package", validate)
    with pytest.raises(ValueError): rc.build_package(root, output)
    assert (output / "owned").read_text() == "preserve"
    assert not list(output.parent.glob(".staging-*"))


def test_cli_typed_results(fixture: Fixture, capsys: pytest.CaptureFixture[str]) -> None:
    """Return stable JSON success, refusal and invalid-result envelopes."""
    root, output, *_ = fixture
    assert rc.main(["build", "--root", str(root), "--output", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "built"
    assert rc.main(["query", "--package", str(output), "--list-records"]) == 0
    assert len(json.loads(capsys.readouterr().out)["records"]) == 3
    assert rc.main(["query", "--package", str(output), "--query", "current law"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "refused_current_law"
    assert rc.main(["query", "--package", str(output / "missing"), "--list-records"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


def test_result_rejects_legal_promotion_and_reversed_span() -> None:
    """Prevent unsupported legal status fields and invalid source byte spans."""
    changes = [("answer_safe", True), ("legal_currentness", "current"),
               ("effective_date", "2026-01-01")]
    for field, value in changes:
        with pytest.raises(ValidationError): rc.Result(status="matched", **{field: value})
    with pytest.raises(ValidationError):
        rc.Span(path="x", start=2, end=1, sha256="0" * 64)


def test_actual_cli_refusal_outside_repository(tmp_path: Path) -> None:
    """The module entry point returns a typed refusal without a readable package."""
    repo = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(repo), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "-B", "-m", "geode.pipeline.research_catalog", "query",
         "--package", str(tmp_path / "missing"), "--list-records", "--mode", "current-law"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "refused_current_law"
    assert list(tmp_path.iterdir()) == []


def test_unsupported_section_is_not_admitted(fixture: Fixture) -> None:
    """A copied adjacent source section cannot become a searchable admitted record."""
    output = build(fixture)
    result = rc.query_package(output, "CRS-1-1-104")
    assert result.status == "no_matching_record" and not result.records


def test_result_cannot_expand_selected_scope(fixture: Fixture) -> None:
    """A response cannot silently grow beyond the fixed three-record scope."""
    output = build(fixture)
    rows = rc.query_package(output, list_records=True).records
    with pytest.raises(ValidationError):
        rc.Result(status="matched", records=(*rows, rows[0]))
