"""Verify only the public subset offline; historical capture tools must never be executed."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import jsonschema

sys.path.insert(0, str(Path(__file__).absolute().parent))
from public_models import Asset, Manifest, Omissions, PrivacyScan, Verification

ORIGINAL_MANIFEST_SHA = "b6112579ab93bcdcc18b68de714008da202b874e1bb1d831fb93ace524efc3f7"


def require(condition: bool, message: str) -> None:
    """Fail closed rather than treating missing private evidence as verified."""
    if not condition:
        raise ValueError(message)


def ordinary(root: Path, name: str) -> Path:
    """Reject dot paths, symlink ancestors, nonregular files and path escapes."""
    part = Path(name)
    require(bool(name) and not part.is_absolute() and ".." not in part.parts,
            "Unsafe relative evidence path")
    require(part.as_posix() == name and "\\" not in name, "Noncanonical evidence path")
    path = root / part
    require(not any(p.is_symlink() for p in [path, *path.parents]), "Symlinked evidence")
    require(path.is_file(), "Missing ordinary evidence: " + name)
    return path


def sha(path: Path) -> str:
    """Hash source bytes without loading a corpus-sized file into memory."""
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def check_asset(root: Path, ref: Asset) -> Path:
    """Check exact size and digest before consuming retained evidence."""
    path = ordinary(root, ref.path)
    require(path.stat().st_size == ref.bytes and sha(path) == ref.sha256,
            "Evidence hash/size mismatch: " + ref.path)
    return path


def load(root: Path, name: str, model: Any) -> Any:
    """Apply Pydantic and the companion JSON schema to one public control record."""
    raw = ordinary(root, name + ".json").read_bytes()
    schema = json.loads(ordinary(root, name + ".schema.json").read_bytes())
    require(schema == model.model_json_schema(), "Schema/model mismatch: " + name)
    result = model.model_validate_json(raw)
    jsonschema.validate(json.loads(raw), schema)
    return result


def custody(root: Path) -> Manifest:
    """Verify the closed public inventory and exact subset of the frozen original."""
    record = load(root, "PUBLIC_MANIFEST", Manifest)
    require(record.original_manifest_sha256 == ORIGINAL_MANIFEST_SHA,
            "The frozen original manifest pin differs")
    names = [a.path for a in record.files]
    require(len(names) == len(set(names)), "Duplicate public inventory member")
    expected = set(names) | {"PUBLIC_MANIFEST.json"}
    actual, directories = set(), set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Symlink in public package")
        name = path.relative_to(root).as_posix()
        if path.is_file():
            actual.add(name)
        elif path.is_dir():
            directories.add(name)
        else:
            raise ValueError("Nonordinary public package entry")
    require(actual == expected, "Missing/unlisted public package file")
    expected_dirs = {str(p) for n in expected for p in Path(n).parents if str(p) != "."}
    require(directories == expected_dirs, "Missing/unlisted/empty public directory")
    for ref in record.files:
        check_asset(root, ref)
    original_path = ordinary(root, "frozen/FINAL_MANIFEST.json")
    require(sha(original_path) == record.original_manifest_sha256, "Original manifest differs")
    original = json.loads(original_path.read_bytes())
    jsonschema.validate(original, json.loads(ordinary(
        root, "frozen/FINAL_MANIFEST.schema.json").read_bytes()))
    omitted = load(root, "OMISSIONS", Omissions)
    scan = load(root, "PRIVACY_SCAN", PrivacyScan)
    require(omitted.original_manifest.sha256 == record.original_manifest_sha256,
            "Omission manifest pin differs")
    check_asset(root, omitted.original_manifest)
    private = {r["path"]: r for r in original["assets"]
               if r["visibility"] == "local_only_private_headers"}
    require(len(original["assets"]) == 716 and len(private) == 31, "Original counts differ")
    require({o.original.path for o in omitted.omitted_private_headers} == set(private),
            "Omission coverage differs")
    copied = {a.path.removeprefix("frozen/"): a for a in record.files
              if a.path.startswith("frozen/")}
    require(set(copied) == {r["path"] for r in original["assets"]} - set(private)
            | {"FINAL_MANIFEST.json"}, "Public selection differs")
    for old in original["assets"]:
        if old["path"] not in private:
            current = copied[old["path"]]
            require((current.sha256, current.bytes) == (old["sha256"], old["bytes"]),
                    "Copied original changed")
    for item in omitted.omitted_private_headers:
        old = private[item.original.path]
        require(item.original.sha256 == old["sha256"] and item.original.bytes == old["bytes"],
                "Omitted-original reference differs")
        require(item.original.path == f"events/{item.event_id}/private.headers",
                "Unexpected omission path")
        check_asset(root, item.retained_public_derivative)
    require(scan.verbatim_files_scanned == len(copied), "Privacy scan scope differs")
    return record


def verify(root: Path) -> Verification:
    """Replay public schemas, acquisition records, native pages and all retained PNGs."""
    root = root.absolute()
    require(".." not in root.parts, "Use a root without parent traversal")
    before = custody(root)
    frozen = root / "frozen"
    sys.path.insert(0, str(frozen))
    spec = importlib.util.spec_from_file_location(
        "frozen_public_replay", frozen / "verify_discovery.py",
    )
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    require(old.HERE == frozen.resolve(), "Frozen helper root differs")
    discovery = old.load_model("DISCOVERY.json", old.Discovery, "DISCOVERY.schema.json")
    comparison = old.load_model("LEGACY_COMPARISON.json", old.Comparison,
                                "LEGACY_COMPARISON.schema.json")
    baseline = old.load_model("BASELINE_RECEIPT.json", old.Baseline, "BASELINE_RECEIPT.schema.json")
    attempts = old.load_model("ATTEMPT_LOG.json", old.AttemptLog, "ATTEMPT_LOG.schema.json")
    old.load_model("UNOPENED_BACKLOG.json", old.Backlog, "UNOPENED_BACKLOG.schema.json")
    old.load_model("CAPTURE_METHOD.json", old.MethodReceipt, "CAPTURE_METHOD.schema.json")
    omissions = load(root, "OMISSIONS", Omissions)
    by_event = {o.event_id: o for o in omissions.omitted_private_headers}
    events = {}
    for event in attempts.events:
        eid = event.event_id
        observed = old.load_model(f"events/{eid}/event.json", old.Event, "EVENT.schema.json")
        reserved = old.load_model(f"events/{eid}/reservation.json", old.Reservation,
                                  "RESERVATION.schema.json")
        require(observed == event and event.event_id == reserved.event_id
                and event.requested_url == reserved.url and event.basis == reserved.basis
                and event.started_at == reserved.reserved_at <= event.completed_at,
                "Public event/reservation differs")
        omitted = by_event[eid]
        require(event.private_headers.model_dump() == omitted.original.model_dump(),
                "Private reference claim differs")
        require(omitted.retained_public_derivative.model_dump() == {
            **event.public_headers.model_dump(), "path": "frozen/" + event.public_headers.path,
        }, "Public derivative/event binding differs")
        require(event.removed_header_names == omitted.sensitive_header_names,
                "Header omission claim differs")
        raw = old.read_ref(event.public_headers)
        location = None
        for line in raw.splitlines():
            key = line.split(b":", 1)[0].strip().lower()
            require(key not in old.SENSITIVE, "Sensitive field in public headers")
            if key == b"location":
                location = urljoin(event.requested_url, line.split(b":", 1)[1].strip().decode())
        require(location == event.redirect_location, "Public redirect Location differs")
        metadata = old.read_ref(event.metadata).decode("utf-8", errors="replace").splitlines()
        status = int(metadata[0]) if metadata[0].isdigit() and int(metadata[0]) else None
        require(status == event.http_status and metadata[1] == event.final_url
                and (metadata[2] if len(metadata) > 2 else None) == event.content_type,
                "Retained HTTP metadata differs")
        old.read_ref(event.body)
        old.read_ref(event.stderr)
        if status == 200 and event.curl_exit == 0 and "html" in (event.content_type or ""):
            old.verify_html(event)
        events[eid] = event
    require(list(events) == [f"E{n:03}" for n in range(1, 32)], "Public event order differs")
    require(len({e.requested_url for e in events.values()}) == 30, "Public target count differs")
    require(Counter(e.http_status for e in events.values()) == {200: 21, 301: 8, 403: 1, None: 1},
            "HTTP/transport counts differ")
    require(sum(e.body.bytes for e in events.values()) == 14428668, "Response bytes differ")
    documents, rendered = old.verify_pdfs(events, rerender=True)
    require(rendered == 18, "Saved render count differs")
    old.verify_legacy(comparison, events, set(documents))
    for ref in baseline.files:
        old.read_ref(ref)
    for priority in discovery.priorities:
        require(priority.body == events[priority.event_id].body, "Priority body differs")
        for statement in priority.source_statements:
            snippet = statement.evidence
            data = old.read_ref(snippet.text_file)
            exact = snippet.text.encode()
            require(data[snippet.start_byte:snippet.end_byte] == exact
                    and hashlib.sha256(exact).hexdigest() == snippet.text_sha256,
                    "Retained source snippet differs")
    require(len(discovery.priorities) == 12 and len(discovery.checklist) == 24
            and len(discovery.viewed_pages) == 14, "Recorded discovery scope differs")
    require(custody(root) == before, "Public package changed during verification")
    return Verification(
        status="passed_public_subset_limited_replay", public_files=len(before.files),
        limitations=[
            "Private-header bytes are absent. Their derivation was checked before omission only; "
            "this portable run checks public bytes/fields and hash-bound omission claims.",
            "403 native pages and 18 saved renders are mechanical replay, not full visual QA. "
            "Only 14 historical viewed-page records are retained; no new visual review occurred.",
            "Historical working-file hashes remain separate from commit IDs. No committed-blob "
            "equality, raw-size probe, current source request or legal-currentness "
            "check was replayed.",
            "Historical full verifier, capture/build helpers and paths are evidence only. "
            "The private-dependent full verify() was not invoked.",
        ])


def main() -> int:
    """Run the sole supported public verification entrypoint from any directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parent)
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        sys.stderr.write(type(exc).__name__ + ": " + str(exc) + "\n")
        return 1
    sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
