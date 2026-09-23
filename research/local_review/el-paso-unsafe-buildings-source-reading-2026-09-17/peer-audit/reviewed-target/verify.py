"""Replay exact research bindings, not semantic or legal certification."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import subprocess
import tempfile
from pathlib import Path

import jsonschema

from build_review import ROOT, Review, build


def verify(rerender: bool = False) -> None:
    """Check the closed payload and optionally reproduce all inspected images."""
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    expected = {item["path"] for item in manifest["files"]}
    actual = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
    assert actual == expected | {"MANIFEST.json"}, "Unlisted/missing payload"
    assert len(expected) == len(manifest["files"]), "Duplicate manifest entry"
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert not path.is_symlink() and path.resolve().is_relative_to(ROOT)
        data = path.read_bytes()
        assert len(data) == item["size_bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    record = json.loads((ROOT / "REVIEW.json").read_text())
    schema = json.loads((ROOT / "REVIEW.schema.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(record)
    Review.model_validate(record)
    assert build().model_dump(mode="json") == record
    assert [page["physical_page"] for page in record["inspected_pages"]] == list(range(1, 9))
    if rerender:
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            source = ROOT / "inputs/original.pdf"
            subprocess.run(["pdftoppm", "-r", "120", "-png", str(source), str(out / "page")],
                           check=True, capture_output=True)
            for index in range(1, 9):
                assert (out / f"page-{index}.png").read_bytes() == (
                    ROOT / f"pages/page-{index}.png"
                ).read_bytes()
            subprocess.run([
                "pdftoppm", "-f", "8", "-l", "8", "-singlefile", "-r", "240",
                "-x", "150", "-y", "760", "-W", "1690", "-H", "650", "-png",
                str(source), str(out / "crop"),
            ], check=True, capture_output=True)
            assert (out / "crop.png").read_bytes() == (
                ROOT / "page-8-execution-crop.png"
            ).read_bytes()
    logging.info("Verified %s payloads and23 bounded findings", len(expected))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerender", action="store_true")
    verify(parser.parse_args().rerender)
