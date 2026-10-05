"""Read-only verification of a portable supplementary source/native package.

Usage: python verify_package.py [package_directory]
Requires Pydantic 2 and PyMuPDF; performs no network access or writes.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sys
from urllib.parse import urlsplit

import pymupdf
from pydantic import ValidationError

from package_models import Asset, Manifest, Page, Provenance, Source, Verification


def digest(data: bytes) -> str:
    """Return the SHA-256 of exact bytes."""
    return sha256(data).hexdigest()


def checked_read(root: Path, asset: Asset) -> bytes:
    """Reject symlinks, missing assets, and any size or hash mismatch."""
    path = root / asset.path
    if path.is_symlink() or not path.is_file() or root.resolve() not in path.resolve().parents:
        raise ValueError("missing or unsafe member")
    data = path.read_bytes()
    if len(data) != asset.size_bytes or digest(data) != asset.sha256:
        raise ValueError("asset bytes differ")
    return data


def exact_citation(pages: list[Page], citation: str) -> Page:
    """Only exact hash-and-physical-page references resolve."""
    found = [page for page in pages if page.citation == citation]
    if len(found) != 1:
        raise ValueError("citation not found uniquely")
    return found[0]


def verify(root: Path) -> Verification:
    """Reconcile all members and reproduce native text for every physical page."""
    root = root.resolve()
    manifest_bytes = (root / "MANIFEST.json").read_bytes()
    manifest = Manifest.model_validate_json(manifest_bytes, strict=True)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
              and "__pycache__" not in p.parts}
    expected = {a.path for a in manifest.assets} | {"MANIFEST.json"}
    if actual != expected or len(manifest.assets) != len(expected) - 1:
        raise ValueError("package membership mismatch")
    for asset in manifest.assets:
        checked_read(root, asset)
    provenance = Provenance.model_validate_json((root / "PROVENANCE.json").read_bytes())
    if provenance.collection_request_count > 45 or provenance.collection_charged_bytes > 100000000:
        raise ValueError("collection budget exceeded")
    transfer_paths = sorted((root / "evidence/http").glob("*/RESULT.json"))
    transfer_paths += sorted((root / "evidence/delivery").glob("*/RESULT.json"))
    if {p.parent.name for p in transfer_paths} != {f"{i:04}" for i in range(1, 37)}:
        raise ValueError("request sequence missing or duplicated")
    charged_bytes = 0
    for transfer_path in transfer_paths:
        transfer = json.loads(transfer_path.read_bytes())
        if transfer["charged_bytes"] > 15000000:
            raise ValueError("per-response byte cap exceeded")
        charged_bytes += transfer["charged_bytes"]
        requested = urlsplit(transfer["requested_url"])
        if (requested.scheme != "https" or requested.username or requested.password
            or requested.fragment or requested.port not in (None, 443)
            or requested.hostname not in (
                "coag.gov", "coprrr.colorado.gov", "drive.google.com", "drive.usercontent.google.com"
            )):
            raise ValueError("unexpected transfer destination")
        if datetime.fromisoformat(transfer["ended_at"].replace("Z", "+00:00")) >= datetime(
            2026, 10, 5, 21, 20, tzinfo=timezone.utc
        ):
            raise ValueError("transfer beyond collection stop")
    if (len(transfer_paths), charged_bytes) != (
        provenance.collection_request_count, provenance.collection_charged_bytes
    ):
        raise ValueError("transfer totals differ from provenance")
    sources = [Source.model_validate_json(line, strict=True)
               for line in (root / "sources.jsonl").read_bytes().splitlines()]
    pages = [Page.model_validate_json(line, strict=True)
             for line in (root / "pages.jsonl").read_bytes().splitlines()]
    historical = {x["id"]: x for x in (
        json.loads(line) for line in
        (root / "evidence/inherited-coprrr-records.jsonl").read_bytes().splitlines()
    )}
    if len({s.source_id for s in sources}) != len(sources):
        raise ValueError("duplicate source")
    if len({p.citation for p in pages}) != len(pages):
        raise ValueError("duplicate citation")
    if {p.source_id for p in pages} != {s.source_id for s in sources}:
        raise ValueError("source/page identity mismatch")
    original_bytes = native_bytes = exact_cases = negatives = 0
    for source in sources:
        original = checked_read(root, source.original)
        if not original.startswith(b"%PDF-"):
            raise ValueError("source signature mismatch")
        original_bytes += len(original)
        source_pages = [p for p in pages if p.source_id == source.source_id]
        if [p.physical_page for p in source_pages] != list(range(1, source.page_count + 1)):
            raise ValueError("physical page coverage mismatch")
        if source.historical_index_sha256 != digest(
            historical[source.historical_record_id]["summary"].encode("utf-8")
        ):
            raise ValueError("inherited summary-hash statement mismatch")
        receipt = json.loads(checked_read(root, source.acquisition_receipts[-1]))
        if (receipt["http_status"] != 200 or not receipt["complete_transfer"]
            or receipt["partial_body"] or receipt["body"]["sha256"] != source.original.sha256
            or receipt["body"]["size_bytes"] != len(original)
            or receipt["final_url"] != source.final_response_url):
            raise ValueError("source-to-transfer receipt mismatch")
        subtotal = 0
        with pymupdf.open(stream=original, filetype="pdf") as document:
            if document.is_encrypted or document.is_repaired or document.page_count != source.page_count:
                raise ValueError("unacceptable PDF structure")
            for page in source_pages:
                physical = document[page.physical_page - 1]
                native = checked_read(root, page.native_text)
                if native != physical.get_text("text", sort=False).encode("utf-8"):
                    raise ValueError("native extraction differs")
                if page.native_text_empty_after_strip != (not native.decode("utf-8").strip()):
                    raise ValueError("empty native page flag differs")
                if page.original_sha256 != source.original.sha256:
                    raise ValueError("page bound to another original")
                expected_citation = f"COPRRR-PDF-{source.original.sha256}#page={page.physical_page}"
                if page.citation != expected_citation or exact_citation(pages, expected_citation) != page:
                    raise ValueError("citation is not exact")
                exact_cases += 1
                subtotal += len(native)
        if subtotal != source.native_text_bytes:
            raise ValueError("source native byte total differs")
        native_bytes += subtotal
        for bad in (
            f"COPRRR-PDF-{source.original.sha256}#page=0",
            f"COPRRR-PDF-{source.original.sha256}#page={source.page_count + 1}",
            f"COPRRR-PDF-{source.historical_index_sha256}#page=1",
        ):
            try:
                exact_citation(pages, bad)
            except ValueError:
                negatives += 1
            else:
                raise ValueError("invalid citation resolved")
    if (len(sources), len(pages), original_bytes, native_bytes) != (
        manifest.original_count, manifest.native_page_count,
        manifest.original_bytes, manifest.native_text_bytes
    ):
        raise ValueError("manifest aggregate differs")
    unsafe_cases = 0
    for bad in ("../escape", "/absolute", "folder/../escape", "folder\\file", "./file"):
        try:
            Asset(path=bad, sha256="0" * 64, size_bytes=0)
        except ValidationError:
            unsafe_cases += 1
        else:
            raise ValueError("unsafe asset path accepted")
    hash_cases = 0
    for source in sources:
        broken = source.original.model_copy(update={"sha256": "0" * 64})
        try:
            checked_read(root, broken)
        except ValueError:
            hash_cases += 1
        else:
            raise ValueError("altered hash accepted")
    return Verification(
        verified_at=datetime.now(timezone.utc).isoformat(),
        manifest_sha256=digest(manifest_bytes), manifest_member_count=len(manifest.assets),
        original_count=len(sources), native_page_count=len(pages), original_bytes=original_bytes,
        native_text_bytes=native_bytes, exact_citation_cases=exact_cases,
        verified_request_count=len(transfer_paths), verified_charged_bytes=charged_bytes,
        negative_citation_cases=negatives, hash_mismatch_cases=hash_cases,
        unsafe_path_cases=unsafe_cases,
    )


if __name__ == "__main__":
    package = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    sys.stdout.write(verify(package).model_dump_json(indent=2) + "\n")
