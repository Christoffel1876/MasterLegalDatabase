"""Read-only validation of an additive EB016/017 integration audit."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

SHA = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
OLD_MANIFEST_SHA = "0c138f834179a72857ec84c13c6396a535c9ab23ccd99d32bd963e3536a52fc1"
TITLE = "2026 Development Impact Fee Schedule \n"
CROP_SHA = "9d4bcab6286a4da98c71cdee2261a498aa521e5ce1870b3295c1c86080b6325a"
RECT = (1450, 90, 2400, 270)


class Strict(BaseModel):
    """Forbid unknown fields and coercion in new audit records."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """Bind package-relative exact bytes."""

    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(ge=0)]


class Observation(Strict):
    """Keep a candidate-aware visual finding separate from automated checks."""

    assignment_id: Literal["EB-PDF-016", "EB-PDF-017"]
    physical_page: Annotated[int, Field(ge=1, le=3)]
    image: Asset
    directly_viewed: Literal[True]
    observation: str


class Superseding(Strict):
    """Withdraw exact earlier conclusions without overwriting their history."""

    recorded_at: AwareDatetime
    status: Literal["superseding_visibility_disposition"]
    supersedes: list[Asset]
    withdrawn_claim_ids: list[str]
    retained_baseline: Asset
    retained_text: str
    corrected_observation: Literal["running_title_visible_on_pages_1_2_3"]
    affected_pages: list[int]
    source_and_candidate_changed: Literal[False]
    prior_records_changed: Literal[False]
    does_not_withdraw: list[str]
    limitations: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


class Audit(Strict):
    """Record custody, checks and the limited integration recommendation."""

    recorded_at: AwareDatetime
    status: Literal["accept_with_superseding_correction_attached"]
    method: Literal["candidate_aware_independent_local_audit"]
    original_packet_path_claim: str
    original_packet_manifest: Asset
    original_packet_files: int
    original_packet_unchanged: Literal[True]
    header_crop_original_path_claim: str
    header_crops: list[Asset]
    pixel_crop_rectangle: list[int]
    crop_method: str
    observations: list[Observation]
    automated_results: dict[str, Any]
    known_validator_gaps: list[str]
    missing_claimed_artifacts: list[str]
    integration_conditions: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


class Manifest(Strict):
    """Close every audit file except the final manifest itself."""

    recorded_at: AwareDatetime
    status: Literal["closed_additive_integration_audit"]
    files: list[Asset]
    legal_currentness: Literal["not_verified"]


def require(condition: bool, message: str) -> None:
    """Raise explicit errors even when Python assertions are disabled."""
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    """Return SHA256 for exact bytes."""
    return hashlib.sha256(data).hexdigest()


def read(root: Path, relative: str) -> bytes:
    """Read one confined bounded regular file, rejecting every symlink ancestor."""
    path = PurePosixPath(relative)
    require(not path.is_absolute() and str(path) == relative and ".." not in path.parts,
            "unsafe path")
    target = root.joinpath(*path.parts)
    require(not any(p.is_symlink() for p in (target, *target.parents)), "symlink path")
    require(target.is_file() and target.stat().st_size <= 10_000_000, "invalid bounded file")
    return target.read_bytes()


def check(root: Path, asset: dict[str, Any]) -> bytes:
    """Validate exact file identity before using it."""
    data = read(root, asset["path"])
    require(len(data) == asset["size_bytes"] and sha(data) == asset["sha256"],
            f"asset identity differs: {asset['path']}")
    return data


def load(root: Path, relative: str) -> Any:
    """Parse bounded local JSON."""
    return json.loads(read(root, relative))


def check_inventory(root: Path, files: list[dict[str, Any]], excluded: set[str]) -> None:
    """Verify a closed tree before importing or executing any package code."""
    expected = {item["path"] for item in files}
    require(len(expected) == len(files), "duplicate manifest path")
    actual = set()
    dirs = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), "symlink inventory entry")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
        elif path.is_dir():
            dirs.add(path.relative_to(root).as_posix())
        else:
            raise ValueError("nonregular inventory entry")
    require(actual == expected | excluded, "file inventory not closed")
    required_dirs = {str(p) for name in actual for p in PurePosixPath(name).parents
                     if str(p) != "."}
    require(dirs == required_dirs, "directory inventory not closed")
    for asset in files:
        check(root, asset)


def title_bindings(package: Path, supplement: dict[str, Any]) -> int:
    """Replay each title's PDF, native, candidate, page and image association."""
    baseline = load(package, "baseline/EB-PDF-016/SOURCE_QA.json")
    base = "baseline/EB-PDF-016/"
    candidate = read(package, base + "inputs/candidate.txt")
    artifacts = supplement["native_title_artifacts"]
    require([a["physical_page"] for a in artifacts] == [2, 3], "title pages not exactly 2 and 3")
    source = read(package, base + "inputs/original.pdf")
    require(sha(source) == baseline["source"]["sha256"], "title source differs")
    with pymupdf.open(stream=source, filetype="pdf") as pdf:
        require(len(pdf) == 3 and not pdf.is_repaired and not pdf.needs_pass, "title PDF invalid")
        for artifact in artifacts:
            number = artifact["physical_page"]
            page = baseline["pages"][number - 1]
            require(page["physical_page"] == number, "baseline page identity differs")
            image = {**page["image"], "path": base + page["image"]["path"]}
            require(artifact["image"] == image, "title image assigned to wrong page")
            check(package, image)
            native = pdf[number - 1].get_text("text", flags=195, sort=False).encode()
            require(sha(native) == page["native_sha256"], "title native replay differs")
            start, end = artifact["native_start_byte"], artifact["native_end_byte_exclusive"]
            require(type(start) is int and type(end) is int and 0 <= start < end <= len(native),
                    "invalid title native bounds")
            text = artifact["native_text"].encode()
            require(text == TITLE.encode() and native[start:end] == text,
                    "title native slice differs")
            require(sha(text) == artifact["text_sha256"], "title slice digest differs")
            offset = page["candidate_start_byte"]
            require(artifact["candidate_start_byte"] == offset + start
                    and artifact["candidate_end_byte_exclusive"] == offset + end,
                    "title candidate offset does not match page origin")
            require(candidate[offset + start:offset + end] == text, "title candidate slice differs")
            require(native.count(text) == 1, "title occurrence is not unique on page")
    return len(artifacts)


def additional_receipt_checks(package: Path, record: dict[str, Any]) -> int:
    """Resolve activation, source-identity and page hashes omitted by the old validator."""
    activation = sha(read(package, "authorization/ACTIVATION.md"))
    identities_hash = sha(read(package, "authorization/SOURCE_ONLY_IDENTITIES.json"))
    identities = load(package, "authorization/SOURCE_ONLY_IDENTITIES.json")
    count = 0
    for document in record["documents"]:
        number = document["assignment_id"][-3:]
        packet_path = "packet-manifest.json" if number == "016" else "manifest.json"
        packet_digest = sha(read(package, f"baseline/EB-PDF-{number}/inputs/{packet_path}"))
        selected = [d for d in identities["documents"]
                    if d["assignment_id"] == document["assignment_id"]]
        require(len(selected) == 1 and selected[0]["source_id"] == document["source_id"],
                "source-only identity differs")
        for suffix in ("PASS1_FREEZE_RECEIPT.json", "COMPLETION_RECEIPT.json"):
            receipt = load(package, f"reports/EB-PDF-{number}/{suffix}")
            require(receipt["source_id"] == document["source_id"]
                    and receipt["assignment_id"] == document["assignment_id"], "receipt identity")
            require(receipt["expected_pages"] == document["page_count"], "receipt page count")
            hashes = receipt["hashes"] if number == "016" else receipt
            manifest_key = ("packet_manifest_sha256_assignment_supplied_file_not_opened"
                            if number == "016" else "packet_manifest_sha256")
            require(hashes["activation_sha256"] == activation, "activation receipt mismatch")
            require(hashes["SOURCE_ONLY_IDENTITIES_sha256"] == identities_hash,
                    "source identities receipt mismatch")
            require(hashes[manifest_key] == packet_digest, "packet receipt mismatch")
            images = document["source_images"]
            for number_page, image in enumerate(images, 1):
                key = f"page-{number_page:04d}.png"
                claimed = hashes[key] if number == "016" else hashes["page_images_sha256"][key]
                require(claimed == image["sha256"], "receipt page image differs")
                if number == "017":
                    require(hashes["page_images_size_bytes"][key] == image["size_bytes"],
                            "receipt image size differs")
            count += 1
    return count


def header_proof(root: Path) -> list[dict[str, Any]]:
    """Replay exact RGB row slices, without inferring image text through code."""
    rows = []
    x0, y0, x1, y1 = RECT
    for number in range(1, 4):
        prefix = "historical-packet/baseline/EB-PDF-016/inputs/"
        pix = pymupdf.Pixmap(read(root, prefix + f"page-{number:04d}.png"))
        require((pix.width, pix.height, pix.n, pix.alpha) == (2550, 3300, 3, 0),
                "unexpected RGB image geometry")
        samples = pix.samples
        cropped = b"".join(samples[y * pix.stride + x0 * 3:y * pix.stride + x1 * 3]
                           for y in range(y0, y1))
        png = pymupdf.Pixmap(pymupdf.csRGB, x1 - x0, y1 - y0, cropped, False).tobytes("png")
        require(sha(png) == CROP_SHA, "crop replay digest differs")
        require(png == read(root, f"header-crops/page-{number:04d}-header.png"),
                "supplied crop not exact pixel slice")
        dark = sum(sum(cropped[i:i + 3]) < 660 for i in range(0, len(cropped), 3))
        require(dark == 7602, "crop pixel count differs")
        rows.append({"physical_page": number, "sha256": sha(png),
                     "rgb_sum_below_660": dark})
    return rows


def self_tests(package: Path, supplement: dict[str, Any]) -> int:
    """Reject malformed title associations using in-memory mutations only."""
    count = 0
    for field, value in [("native_start_byte", -1), ("native_end_byte_exclusive", 900),
                         ("candidate_start_byte", 0), ("text_sha256", "0" * 64),
                         ("native_text", "Wrong title\n"), ("physical_page", 3)]:
        changed = copy.deepcopy(supplement)
        changed["native_title_artifacts"][0][field] = value
        try:
            title_bindings(package, changed)
        except (ValueError, IndexError):
            count += 1
        else:
            raise ValueError(f"adversarial title mutation accepted: {field}")
    changed = copy.deepcopy(supplement)
    changed["native_title_artifacts"][0]["image"] = changed["native_title_artifacts"][1]["image"]
    try:
        title_bindings(package, changed)
    except ValueError:
        count += 1
    else:
        raise ValueError("wrong page image accepted")
    return count


def verify(root: Path, *, closed: bool = True) -> dict[str, Any]:
    """Check the old packet and additive correction without rewriting evidence."""
    if closed:
        manifest = Manifest.model_validate_json(read(root, "FINAL_MANIFEST.json"))
        require(load(root, "FINAL_MANIFEST.schema.json") == Manifest.model_json_schema(),
                "audit manifest schema differs")
        check_inventory(root, [v.model_dump() for v in manifest.files], {"FINAL_MANIFEST.json"})
    package = root / "historical-packet"
    manifest_bytes = read(package, "FINAL_MANIFEST.json")
    require(sha(manifest_bytes) == OLD_MANIFEST_SHA, "historical manifest identity differs")
    old_manifest = json.loads(manifest_bytes)
    check_inventory(package, old_manifest["files"],
                    {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"})
    command = [sys.executable, "-I", "-B", str(package / "validate_reconciliation.py")]
    run = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
    require(run.returncode == 0, "historical structural validator failed: " + run.stderr[:500])
    original_result = json.loads(run.stdout)
    supplement = load(package, "ATLAS_ADDITIONAL_FINDINGS.json")
    record = load(package, "RECONCILIATION.json")
    title_count = title_bindings(package, supplement)
    receipt_count = additional_receipt_checks(package, record)
    crop_results = header_proof(root)
    mutation_count = self_tests(package, supplement)
    if closed:
        correction = Superseding.model_validate_json(read(root, "SUPERSEDING_DISPOSITION.json"))
        require(load(root, "SUPERSEDING_DISPOSITION.schema.json")
                == Superseding.model_json_schema(),
                "superseding schema differs")
        for asset in correction.supersedes:
            check(root, asset.model_dump())
        check(root, correction.retained_baseline.model_dump())
        require(correction.affected_pages == [2, 3] and correction.retained_text == TITLE,
                "superseding page/text identity differs")
        audit = Audit.model_validate_json(read(root, "AUDIT.json"))
        require(load(root, "AUDIT.schema.json") == Audit.model_json_schema(),
                "audit schema differs")
        for observation in audit.observations:
            check(root, observation.image.model_dump())
        check_inventory(root, [v.model_dump() for v in manifest.files], {"FINAL_MANIFEST.json"})
    return {"status": "integrity_passed_superseding_visual_correction_required",
            "historical_validator": original_result, "title_bindings_replayed": title_count,
            "additional_receipt_records": receipt_count, "header_crops": crop_results,
            "adversarial_title_mutations_rejected": mutation_count,
            "external_chronology_authenticated": False, "legal_currentness": "not_verified"}


def main() -> int:
    """Run only read-only validation of the directory containing this wrapper."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        result = verify(Path(__file__).absolute().parent)
    except Exception as exc:
        sys.stderr.write(f"Validation failed: {type(exc).__name__}: {exc}\n")
        return 1
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
