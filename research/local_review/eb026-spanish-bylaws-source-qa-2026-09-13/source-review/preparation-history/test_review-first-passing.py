"""Bounded corruption and portability checks; fixtures never alter received evidence."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from review_models import FileRef, Manifest, Review
from verify_review import capture, main, safe, verify_buffers

ROOT = Path(__file__).absolute().parent


@pytest.fixture(scope="module")
def buffers() -> dict[str, bytes]:
    """Read stable prepared evidence without interpreting historical scripts."""
    return {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in ROOT.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts}


def make_package(destination: Path, buffers: dict[str, bytes]) -> Path:
    """Seal a temporary copy for independent path and closed-inventory tests."""
    destination.mkdir()
    files = []
    for name, raw in sorted(buffers.items()):
        if name in {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}:
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        files.append(FileRef(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    schema = (json.dumps(Manifest.model_json_schema(), indent=2) + "\n").encode()
    (destination / "FINAL_MANIFEST.schema.json").write_bytes(schema)
    files.append(FileRef(path="FINAL_MANIFEST.schema.json", sha256=hashlib.sha256(schema).hexdigest(),
                         size_bytes=len(schema)))
    manifest = Manifest(schema_version="geode.eb026.source-qa.inventory.v1",
                        created_at=datetime.now(timezone.utc), status="frozen_initial_source_qa",
                        files=sorted(files, key=lambda f: f.path), public_requests=0,
                        canonical_writes=0, source_changes=0)
    (destination / "FINAL_MANIFEST.json").write_text(manifest.model_dump_json(indent=2) + "\n")
    return destination


def test_complete_source_and_direct_scope(buffers: dict[str, bytes]) -> None:
    """Every line, paragraph, continuation and crop replays from the fixed source."""
    result = verify_buffers(buffers, rerender=True)
    assert result.native_lines == 180 and result.native_bytes == 13558
    assert result.paragraph_segments == 51 and result.crop_replays == 15
    qa = Review.model_validate_json(buffers["SOURCE_QA.json"])
    assert qa.fullscope.english_versions_consulted is False
    assert qa.fullscope.external_reports_consulted is False
    assert qa.adoption_date is None and qa.effective_date is None
    assert qa.answer_safe is False


@pytest.mark.parametrize("case", [
    "authority", "safe", "date", "omitted_page", "native_negation", "source", "candidate",
    "line_offset", "line_geometry", "line_text", "line_id", "paragraph_text",
    "paragraph_lines", "paragraph_omission", "continuation", "observation_anchor", "crop",
    "crop_page", "candidate_offset", "unmapped_whitespace",
])
def test_corruption_refused(buffers: dict[str, bytes], case: str) -> None:
    """Actual source and contextual mutations cannot become a successful reviewed result."""
    changed = dict(buffers)
    qa = json.loads(changed["SOURCE_QA.json"])
    if case == "authority":
        qa["authority_id"] = "CO-MUNICIPAL_EL_PASO"
    elif case == "safe":
        qa["answer_safe"] = True
    elif case == "date":
        qa["adoption_date"] = "2025-06-01"
    elif case == "omitted_page":
        qa["pages"].pop()
    elif case in {"source", "candidate", "crop"}:
        target = qa[case]["path"] if case != "crop" else qa["crops"][0]["image"]["path"]
        changed[target] += b"altered"
    elif case == "native_negation":
        target = qa["pages"][4]["native"]["path"]
        changed[target] = changed[target].replace(b"La Junta no", b"La Junta si")
    elif case == "line_offset":
        qa["pages"][2]["lines"][1]["byte_start"] += 1
    elif case == "line_geometry":
        qa["pages"][2]["lines"][1]["bbox_pdf_points"][0] += 15.0
    elif case == "line_text":
        qa["pages"][2]["lines"][0]["text"] = "invented\n"
    elif case == "line_id":
        qa["pages"][2]["lines"][0]["id"] = "wrong"
    elif case == "paragraph_text":
        qa["pages"][3]["segments"][4]["text"] = "Ningún miembro.\n"
    elif case == "paragraph_lines":
        qa["pages"][2]["segments"][3]["line_ids"] = ["P03-L001"]
    elif case == "paragraph_omission":
        qa["pages"][3]["segments"].pop()
    elif case == "continuation":
        qa["pages"][1]["segments"][-1]["continues_to"] = "P05-S01"
    elif case == "observation_anchor":
        qa["observations"][0]["literal_anchors"] = ["unsupported quotation"]
    elif case == "crop_page":
        qa["crops"][0]["physical_page"] = 3
    elif case == "candidate_offset":
        qa["pages"][3]["candidate_native_start"] += 1
    elif case == "unmapped_whitespace":
        qa["pages"][1]["segments"][2]["kind"] = "paragraph"
    changed["SOURCE_QA.json"] = json.dumps(qa).encode()
    with pytest.raises(ValueError):
        verify_buffers(changed)


@pytest.mark.parametrize("case", ["added", "missing", "changed", "symlink", "ancestor",
                                  "duplicate", "unsafe", "manifest_schema"])
def test_closed_custody_refusals(tmp_path: Path, buffers: dict[str, bytes], case: str) -> None:
    """Altered files, lexical escapes and links fail before being consumed as review evidence."""
    package = make_package(tmp_path / "package", buffers)
    if case == "added":
        (package / "injected.txt").write_text("extra")
    elif case == "missing":
        (package / "SOURCE_QA.json").unlink()
    elif case == "changed":
        (package / "SOURCE_QA.json").write_text("{}")
    elif case == "symlink":
        (package / "link").symlink_to(package / "SOURCE_QA.json")
    elif case == "ancestor":
        (tmp_path / "linked").symlink_to(package, target_is_directory=True)
        package = tmp_path / "linked"
    elif case in {"duplicate", "unsafe"}:
        raw = json.loads((package / "FINAL_MANIFEST.json").read_bytes())
        if case == "duplicate":
            raw["files"].append(copy.deepcopy(raw["files"][0]))
        else:
            raw["files"][0]["path"] = "../elsewhere"
        (package / "FINAL_MANIFEST.json").write_text(json.dumps(raw))
    elif case == "manifest_schema":
        (package / "FINAL_MANIFEST.schema.json").write_text("{}")
    with pytest.raises((ValueError, FileNotFoundError)):
        capture(package)


@pytest.mark.parametrize("relative", ["../outside", "/absolute", "./SOURCE_QA.json"])
def test_lexical_paths(tmp_path: Path, relative: str) -> None:
    """Unsafe local references never resolve through a different tree."""
    with pytest.raises(ValueError):
        safe(tmp_path, relative)


def test_portable_cli(tmp_path: Path, buffers: dict[str, bytes], monkeypatch, capsys) -> None:
    """The ordinary CLI consumes only the relocated closed package."""
    package = make_package(tmp_path / "relocated", buffers)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["verify_review.py", "--root", str(package)])
    main()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "passed" and not result["visual_judgment_automatically_certified"]
