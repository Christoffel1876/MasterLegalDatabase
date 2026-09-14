"""Read-only, local-only integrity checks for the EB015 reconciliation package."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

SHA = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SOURCE_ID = "greeley-building-fees-sd008-06"
PDF_SHA = "fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4"
CANDIDATE_SHA = "aec7efa7edbd9e26a8ce7bbd9685431c386043fc074567a1b3db334e9f528334"
NATIVE_SHA = "35f7b7448e487369c1874fc31ec7292fe6c9c4bc6210abcac4cac2face620dff"
RECONCILIATION_SHA = "568fe212012d26ed68bd61c674f1afe0ae57ed495cb5e8355c1970d16ddc4288"
PACKET_SHA = "dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397"


class StrictRecord(BaseModel):
    """Reject unknown fields and type coercion in new custody records."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(StrictRecord):
    """Bind one package-relative file to exact bytes."""

    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(ge=0)]


class Copy(Asset):
    """Retain an original path as a historical claim, never as an open target."""

    original_path: str
    role: Literal["packet_provenance", "external_note", "external_crop"]
    supplied_inventory_sha256: SHA | None


class Supplement(StrictRecord):
    """Record additive custody without revising frozen review decisions."""

    captured_at: AwareDatetime
    source_id: Literal["greeley-building-fees-sd008-06"]
    status: Literal["supplement_received_byte_integrity_only"]
    source_and_candidate_changed: Literal[False]
    supplied_created_at_claim: str
    external_history_authenticated: Literal[False]
    legal_currentness: Literal["not_verified"]
    copies: list[Copy]
    crop_paths_reported: list[str]
    crop_paths_received: list[str]
    missing_reported_crop_paths: list[str]
    scope_and_limits: list[str]


class Verification(StrictRecord):
    """Describe checks actually performed, separate from external review claims."""

    verified_at: AwareDatetime
    source_id: Literal["greeley-building-fees-sd008-06"]
    status: Literal["local_integrity_passed_with_scope_limits"]
    checks: dict[str, int | str | bool]
    supplementary_findings: list[str]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


class FinalManifest(StrictRecord):
    """Close the package inventory except for this manifest's own bytes."""

    frozen_at: AwareDatetime
    source_id: Literal["greeley-building-fees-sd008-06"]
    inventory_scope: Literal["all_regular_files_except_FINAL_MANIFEST.json"]
    files: list[Asset]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]


def require(condition: bool, message: str) -> None:
    """Fail closed without relying on optimization-sensitive assertions."""
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    """Return a SHA256 identity."""
    return hashlib.sha256(data).hexdigest()


def local(root: Path, relative: str) -> Path:
    """Permit confined regular files without opening historical paths or symlinks."""
    parts = PurePosixPath(relative)
    require(not parts.is_absolute() and bool(parts.parts), "absolute or empty package path")
    require(str(parts) == relative and ".." not in parts.parts, "noncanonical package path")
    path = root.joinpath(*parts.parts)
    require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink encountered")
    require(path.is_file() and path.stat().st_size <= 10_000_000, "missing or oversized asset")
    return path


def check_asset(root: Path, asset: dict[str, Any]) -> bytes:
    """Check a local asset's exact byte length and digest."""
    data = local(root, asset["path"]).read_bytes()
    require(len(data) == asset["size_bytes"], f"size mismatch: {asset['path']}")
    require(digest(data) == asset["sha256"], f"hash mismatch: {asset['path']}")
    return data


def load(root: Path, path: str) -> Any:
    """Read bounded JSON without external resolution."""
    return json.loads(local(root, path).read_bytes())


def schema_check(root: Path, path: str, schema_path: str) -> Any:
    """Validate only schemas whose references are local definitions."""
    schema = load(root, schema_path)
    for match in re.finditer(r'"\$ref"\s*:\s*"([^"]+)"', json.dumps(schema)):
        require(match.group(1).startswith("#/"), "external schema reference rejected")
    jsonschema.Draft202012Validator.check_schema(schema)
    data = load(root, path)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(data)
    return data


def line_at(root: Path, path: str, number: int) -> bytes:
    """Read one physical line, including its original newline bytes."""
    require(number >= 1, "invalid line number")
    with local(root, path).open("rb") as stream:
        for index, line in enumerate(stream, 1):
            if index == number:
                return line
    raise ValueError("line outside file")


def verify(root: Path, *, closed: bool = True) -> dict[str, int | str | bool]:
    """Validate copied evidence, local replay and references without filesystem writes."""
    require(not any(p.is_symlink() for p in (root, *root.parents)), "symlink package root")
    if closed:
        manifest = FinalManifest.model_validate_json(
            local(root, "FINAL_MANIFEST.json").read_bytes()
        )
        require(load(root, "FINAL_MANIFEST.schema.json") == FinalManifest.model_json_schema(),
                "final manifest schema differs")
        names = [asset.path for asset in manifest.files]
        require(len(names) == len(set(names)), "duplicate inventory path")
        actual = []
        for path in root.rglob("*"):
            require(not path.is_symlink(), "symlink in inventory")
            if path.is_file() and path.relative_to(root).as_posix() != "FINAL_MANIFEST.json":
                actual.append(path.relative_to(root).as_posix())
        require(set(actual) == set(names), "closed file inventory differs")
        expected_dirs = {str(p) for name in names for p in PurePosixPath(name).parents
                         if str(p) != "."}
        actual_dirs = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir()}
        require(actual_dirs == expected_dirs, "closed directory inventory differs")
        for asset in manifest.files:
            check_asset(root, asset.model_dump())
    require(digest(local(root, "RECONCILIATION.json").read_bytes()) == RECONCILIATION_SHA,
            "frozen root reconciliation changed")
    record = schema_check(root, "RECONCILIATION.json", "RECONCILIATION.schema.json")
    baseline = schema_check(root, "baseline/SOURCE_QA.json", "baseline/SOURCE_QA.schema.json")
    require(len(record["copies"]) == 13, "expected thirteen original copies")
    for copied in record["copies"]:
        check_asset(root, {"path": copied["frozen_path"], **copied})
    require(record["source_id"] == baseline["source_id"] == SOURCE_ID, "source mismatch")
    require(record["original_pdf_sha256"] == baseline["source_sha256"] == PDF_SHA,
            "PDF identity mismatch")
    require(record["candidate_sha256"] == baseline["candidate_sha256"] == CANDIDATE_SHA,
            "candidate identity mismatch")
    require(record["legal_currentness"] == baseline["legal_currentness"] == "not_verified",
            "currentness promotion")
    require(record["answer_safe"] is False and record["source_and_candidate_changed"] is False,
            "unsupported result promotion")
    supplement = Supplement.model_validate_json(local(root, "SUPPLEMENT_RECEIPT.json").read_bytes())
    require(load(root, "SUPPLEMENT_RECEIPT.schema.json") == Supplement.model_json_schema(),
            "supplement schema differs")
    for copied in supplement.copies:
        check_asset(root, copied.model_dump())
    packet = schema_check(root, "provenance/packet-manifest.json",
                          "provenance/packet-manifest.schema.json")
    require(digest(local(root, "provenance/packet-manifest.json").read_bytes()) == PACKET_SHA,
            "packet manifest identity mismatch")
    documents = [d for d in packet["documents"] if d["assignment_id"] == "EB-PDF-015"]
    require(len(documents) == 1, "selected packet document not unique")
    document = documents[0]
    require(document["source_id"] == SOURCE_ID and document["expected_pages"] == 1,
            "packet source/page mismatch")
    native_evidence = schema_check(root, "provenance/native-evidence.json",
                                  "provenance/native-evidence.schema.json")
    mappings = {"source.pdf": "source/original.pdf", "page-0001.png": "source/page-0001.png",
                "candidate.txt": "source/candidate.txt",
                "native-evidence.json": "provenance/native-evidence.json",
                "major-review-crop.png": "baseline/major-review-crop.png"}
    require(set(baseline["files"]) == set(mappings), "baseline file set differs")
    for name, relative in mappings.items():
        require(digest(local(root, relative).read_bytes()) == baseline["files"][name],
                f"baseline reference mismatch: {name}")
    for identity, relative in [(document["original"], "source/original.pdf"),
                               (document["candidate"], "source/candidate.txt"),
                               (document["pages"][0]["image"], "source/page-0001.png"),
                               (document["pages"][0]["evidence"],
                                "provenance/native-evidence.json")]:
        check_asset(root, {**identity, "path": relative})
    require(pymupdf.VersionBind == "1.28.2", "replay requires PyMuPDF 1.28.2")
    with pymupdf.open(local(root, "source/original.pdf")) as pdf:
        require(len(pdf) == 1 and not pdf.is_repaired and not pdf.needs_pass,
                "PDF page count, repair or encryption mismatch")
        native = pdf[0].get_text("text", flags=195, sort=False).encode("utf-8")
    candidate = local(root, "source/candidate.txt").read_bytes()
    require(len(native) == 3236 and digest(native) == NATIVE_SHA, "native replay mismatch")
    require(native == candidate[56:3292] == native_evidence["text"].encode("utf-8"),
            "native candidate/evidence slice differs")
    require(native_evidence["flags"] == 195 and native_evidence["sort"] is False,
            "native extraction settings differ")
    require((baseline["candidate_native_start"], baseline["candidate_native_end"]) == (56, 3292),
            "native bounds differ")
    require(baseline["native_bytes"] == 3236 and baseline["native_sha256"] == NATIVE_SHA,
            "baseline native identity differs")
    image = pymupdf.Pixmap(str(local(root, "source/page-0001.png")))
    require((image.width, image.height) == (2550, 3300), "full page dimensions differ")
    spans = baseline["spans"]
    require(len(spans) == 29, "span count differs")
    cursor = 0
    labels = []
    for span in spans:
        require(span["start"] == cursor and cursor < span["end"] <= len(native),
                "span gap, overlap or invalid bounds")
        data = native[span["start"]:span["end"]]
        require(data == span["text"].encode() and digest(data) == span["sha256"],
                "span bytes differ")
        cursor = span["end"]
        labels.append(span["label"])
    require(cursor == len(native) and len(set(labels)) == 29, "span coverage/labels differ")
    require(Counter(labels) == Counter(baseline["source_order"]), "source order not a permutation")
    require(baseline["footnote_links"] == {
        "other_1": "footnote_1", "other_2": "footnote_1", "other_3": "footnote_1",
        "other_4": "footnote_1", "other_5": "footnote_2"}, "footnote links differ")
    expected_ids = [f"EB015-P2-{i:03d}" for i in range(1, 11)]
    expected_ids += [f"E{i}" for i in range(1, 4)] + [f"U{i}" for i in range(1, 7)]
    require([d["claim_id"] for d in record["decisions"]] == expected_ids,
            "decision identity/count differs")
    for decision in record["decisions"]:
        line = line_at(root, decision["report_path"], decision["report_line"])
        require(digest(line) == decision["report_line_sha256"], "decision line hash differs")
        claim = decision["claim_id"]
        prefix = f"{claim[1:]}. " if claim.startswith("U") else f"| {claim} |"
        require(line.decode().startswith(prefix), "decision line points to wrong claim")
        require(decision["source_physical_pages"] == [1], "decision page differs")
        require(set(decision["source_span_labels"]) <= set(labels), "unknown decision span")
    freeze = load(root, "reports/PASS1_FREEZE_RECEIPT.json")
    completion = load(root, "reports/COMPLETION_RECEIPT.json")
    identities = load(root, "authorization/SOURCE_ONLY_IDENTITIES.json")
    for receipt in [freeze, completion]:
        require(receipt["source_id"] == SOURCE_ID and receipt["assignment_id"] == "EB-PDF-015",
                "receipt source/assignment differs")
        require(receipt["authority_id"] == record["authority_id"], "receipt authority differs")
        require(receipt["expected_pages"] == 1 and receipt["original_pdf_sha256"] == PDF_SHA,
                "receipt source/page identity differs")
        for key, relative in [("activation_sha256", "authorization/ACTIVATION.md"),
                              ("source_only_identities_sha256",
                               "authorization/SOURCE_ONLY_IDENTITIES.json"),
                              ("packet_manifest_sha256", "provenance/packet-manifest.json")]:
            require(receipt[key] == digest(local(root, relative).read_bytes()),
                    f"receipt reference differs: {key}")
    check_asset(root, {**freeze["pass1_frozen_md"], "path": "reports/PASS1_frozen.md"})
    require(len(freeze["page_images"]) == 1, "freeze page image count differs")
    check_asset(root, {**freeze["page_images"][0], "path": "source/page-0001.png"})
    for key, relative in [("PASS1_frozen_md_sha256", "reports/PASS1_frozen.md"),
                          ("PASS1_FREEZE_RECEIPT_sha256", "reports/PASS1_FREEZE_RECEIPT.json"),
                          ("PASS2_REVIEW_md_sha256", "reports/PASS2_REVIEW.md"),
                          ("candidate_sha256", "source/candidate.txt")]:
        require(completion[key] == digest(local(root, relative).read_bytes()),
                f"completion binding differs: {key}")
    expected_page_hashes = {"page-0001.png": baseline["files"]["page-0001.png"]}
    require(completion["page_images_sha256"] == expected_page_hashes,
            "completion page binding differs")
    selected = [d for d in identities["documents"] if d["assignment_id"] == "EB-PDF-015"]
    require(len(selected) == 1 and selected[0]["source_id"] == SOURCE_ID,
            "authorization selected identity differs")
    check_asset(root, {**selected[0]["original"], "path": "source/original.pdf"})
    check_asset(root, {**selected[0]["pages"][0]["image"], "path": "source/page-0001.png"})
    require(identities["frozen_packet_manifest"]["sha256"] == PACKET_SHA,
            "authorization manifest binding differs")
    provenance = document["provenance"]
    for key, relative in [("frozen_raw_manifest", "provenance/raw-manifest.jsonl"),
                          ("frozen_intake_receipt", "provenance/intake-receipt.json"),
                          ("frozen_source_provenance", "provenance/source-provenance.jsonl"),
                          ("frozen_referral_html", "provenance/referral.html"),
                          ("frozen_derived_response_headers", "provenance/public-headers.txt")]:
        check_asset(root, {**provenance[key], "path": relative})
    for relative, prefix in [("provenance/raw-manifest.jsonl", "raw_manifest"),
                             ("provenance/source-provenance.jsonl", "provenance")]:
        line = line_at(root, relative, provenance[f"{prefix}_line_number"])
        require(digest(line) == provenance[f"{prefix}_line_sha256"]
                and len(line) == provenance[f"{prefix}_line_size_bytes"],
                "selected provenance line differs")
    inventory = local(root, "supplemental/INVENTORY_sha256.txt").read_text()
    inventory_entries = {}
    for line in inventory.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match and "/EB-PDF-015/" in match[2]:
            relative = "EB-PDF-015/" + match[2].split("/EB-PDF-015/", 1)[1]
            require(relative not in inventory_entries, "duplicate crop inventory item")
            inventory_entries[relative] = match[1]
    received = []
    for copied in supplement.copies:
        if copied.role == "external_crop":
            name = copied.path.removeprefix("supplemental/")
            require(inventory_entries.get(name) == copied.sha256
                    == copied.supplied_inventory_sha256,
                    "supplied crop inventory differs")
            crop = pymupdf.Pixmap(str(local(root, copied.path)))
            require(crop.width > 0 and crop.height > 0, "empty crop")
            received.append(name.removeprefix("EB-PDF-015/"))
    reported = set(freeze["crops_re_read"] + completion["crops_pass1_reread"]
                   + completion["crops_pass2_new"])
    require(len(received) == 19 and set(received) == reported, "crop receipt set differs")
    require(set(supplement.crop_paths_received) == set(received)
            and set(supplement.crop_paths_reported) == reported
            and supplement.missing_reported_crop_paths == [], "supplement crop summary differs")
    if closed:
        for asset in manifest.files:
            check_asset(root, asset.model_dump())
    result = {"original_copies": 13, "decisions": 19, "pdf_pages": 1, "native_bytes": 3236,
            "native_sha256": NATIVE_SHA, "source_spans": 29, "footnote_links": 5,
            "supplied_crops": 19, "external_history_authenticated": False,
            "legal_currentness": "not_verified"}
    if closed:
        receipt = Verification.model_validate_json(
            local(root, "VALIDATION_RECEIPT.json").read_bytes()
        )
        require(load(root, "VALIDATION_RECEIPT.schema.json") == Verification.model_json_schema(),
                "validation receipt schema differs")
        require(receipt.checks == result, "validation receipt result differs")
    return result


def main() -> int:
    """Run a portable, read-only validation and report JSON on stdout."""
    try:
        result = verify(Path(__file__).absolute().parent)
    except Exception as exc:
        sys.stderr.write(f"Validation failed: {type(exc).__name__}: {exc}\n")
        return 1
    sys.stdout.write(json.dumps({"status": "passed", **result}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
