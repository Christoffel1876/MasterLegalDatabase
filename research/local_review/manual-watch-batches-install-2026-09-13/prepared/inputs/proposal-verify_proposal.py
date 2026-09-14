"""Verify the planning packet without opening PDFs, HTML, or public URLs."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from proposal_models import FinalManifest, Proposal


def ordinary(root: Path, relative: str) -> Path:
    """Confine reads to ordinary files below a selected root."""
    part = Path(relative)
    if part.is_absolute() or ".." in part.parts:
        raise ValueError("Unsafe relative path")
    path = root / part
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("Symlink in evidence path")
    if not path.is_file():
        raise ValueError("Missing ordinary evidence file: " + relative)
    return path


def sha(data: bytes) -> str:
    """Return an exact-byte SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def pointer(value: object, path: str) -> object:
    """Resolve the limited JSON pointers retained in the proposal."""
    for token in path.strip("/").split("/") if path else []:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def verify(root: Path, repository: Path | None = None) -> dict[str, object]:
    """Check custody and source joins; optionally rehash external metadata only."""
    manifest = FinalManifest.model_validate_json(
        ordinary(root, "FINAL_MANIFEST.json").read_bytes()
    ).model_dump()
    actual = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    if actual != sorted([x["path"] for x in manifest["files"]] + ["FINAL_MANIFEST.json"]):
        raise ValueError("Closed packet membership changed")
    for entry in manifest["files"]:
        data = ordinary(root, entry["path"]).read_bytes()
        if (sha(data), len(data)) != (entry["sha256"], entry["size_bytes"]):
            raise ValueError("Packet payload changed: " + entry["path"])
    proposal = Proposal.model_validate_json(ordinary(root, "PROPOSAL.json").read_bytes())
    schema = json.loads(ordinary(root, "PROPOSAL.schema.json").read_bytes())
    if schema != Proposal.model_json_schema():
        raise ValueError("Proposal schema changed")
    input_files = {
        "inventory": "inputs/inventory.json",
        "raw_manifest": "inputs/manual_manifest.jsonl",
        "current_watch_selection": "inputs/current_selection.json",
    }
    for name, path in input_files.items():
        data = ordinary(root, path).read_bytes()
        pin = proposal.input_pins[name]
        if (sha(data), len(data)) != (pin.sha256, pin.size_bytes):
            raise ValueError("Copied input pin mismatch")
    inventory = json.loads(ordinary(root, input_files["inventory"]).read_bytes())
    selection = json.loads(ordinary(root, input_files["current_watch_selection"]).read_bytes())
    by_id = {x["record_id"]: (n, x) for n, x in enumerate(inventory["sources"])}
    raw = {}
    with ordinary(root, input_files["raw_manifest"]).open("rb") as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            if row["record_id"] in raw:
                raise ValueError("Duplicate raw source identity")
            raw[row["record_id"]] = (index, line, row)
    if len(raw) != 61 or set(raw) != set(by_id):
        raise ValueError("Inventory/raw identity set differs")
    selected = [x["canonical_source_id"] for x in selection["targets"]]
    if selected != proposal.currently_selected:
        raise ValueError("Current selection mismatch")
    for item in proposal.remaining:
        index, row = by_id[item.record_id]
        if item.inventory_zero_based_row != index or item.authority_id != row["authority_id"]:
            raise ValueError("Remaining authority/index mismatch")
        if item.baseline.model_dump() != row["source"]:
            raise ValueError("Remaining baseline mismatch")
        if (item.review_mapped, item.verified_http_mapped) != (
            bool(row["reviews"]), bool(row["verified_http_acquired_at"])
        ):
            raise ValueError("Remaining custody/review classification mismatch")
    for candidate in proposal.candidates:
        _, row = by_id[candidate.record_id]
        index, line, old = raw[candidate.record_id]
        if (candidate.raw_manifest_zero_based_row, candidate.raw_manifest_exact_line_sha256) != (
            index, sha(line)
        ):
            raise ValueError("Raw record line mismatch")
        if candidate.baseline.model_dump() != row["source"] or (
            candidate.baseline.path, candidate.baseline.sha256, candidate.baseline.size_bytes
        ) != (old["archive_path"], old["sha256"], old["size_bytes"]):
            raise ValueError("Raw baseline mismatch")
        if (candidate.historical_raw_url, candidate.historical_acquisition_method) != (
            old["official_source_url"], old["acquisition_method"]
        ):
            raise ValueError("Historical custody rewritten")
        if candidate.authority_id != row["authority_id"] or candidate.intake_id != row["intake_id"]:
            raise ValueError("Candidate authority or intake mismatch")
        if candidate.historical_reported_acquisition != row["reported_acquisition"]:
            raise ValueError("Historical acquisition claim changed")
        review = row["reviews"][0]
        if candidate.review_evidence.artifact.model_dump() != review["artifact"]:
            raise ValueError("Review hash binding changed")
        if candidate.mapped_scope_fields != review["scope_fields"]:
            raise ValueError("Review scope changed")
    checked = 0
    if repository is not None:
        for pin in [*proposal.input_pins.values(), *proposal.metadata_evidence_pins]:
            if Path(pin.path).suffix not in {".json", ".jsonl", ".py", ".md"}:
                raise ValueError("This verifier never opens source PDFs or HTML")
            data = ordinary(repository, pin.path).read_bytes()
            if (sha(data), len(data)) != (pin.sha256, pin.size_bytes):
                raise ValueError("External metadata pin changed: " + pin.path)
            checked += 1
        for candidate in proposal.candidates:
            evidence = candidate.custody_evidence
            path = ordinary(repository, evidence.artifact.path)
            if evidence.jsonl_row is None:
                receipt = json.loads(path.read_bytes())
            else:
                with path.open("rb") as stream:
                    receipt = next(json.loads(line) for n, line in enumerate(stream)
                                   if n == evidence.jsonl_row)
            if pointer(receipt, evidence.pointers[0]) != candidate.baseline.sha256:
                raise ValueError("HTTP source digest mismatch")
            if pointer(receipt, evidence.pointers[1]) != 200:
                raise ValueError("HTTP status mismatch")
            pages = receipt.get("pdf_pages", receipt.get("physical_pages"))
            if pages != candidate.baseline_pages:
                raise ValueError("Declared structural page count mismatch")
    return {"status": "passed", "proposal": "PREPARED_NOT_ACTIVATED", "sources": 61,
            "proposed": 6, "unselected_classified": 59, "external_metadata_checked": checked,
            "pdfs_opened": 0, "network_requests": 0, "legal_currentness": "not_verified"}


def main() -> int:
    """Run read-only packet checks, with an optional repository metadata check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-metadata", type=Path)
    args = parser.parse_args()
    result = verify(Path(__file__).resolve().parent, args.repository_metadata)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
