"""An isolated three-section CRS metadata prototype; never a current-law catalog."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from geode.schemas import LayerIndexRecord, StatuteSection

IDS = ("CRS-1-1-101", "CRS-1-1-102", "CRS-1-1-103")
OUTPUT_ROOT = Path(".geode_runtime/research_catalog")
MAX_FILE = 32_000_000
MAX_TOTAL = 64_000_000
# Complete files are custody copies. Only the three selected entities are admitted.
INPUTS = (
    ("01_Statutes_CRS/_index.jsonl", "inputs/index.jsonl", 23094877,
     "85bf299b02e64b1035e0c9f53108a60931790def78214b3519815f6bc0762024"),
    ("01_Statutes_CRS/_meta/crs_title_01_meta.jsonl", "inputs/meta.jsonl", 2346501,
     "32eaf09373a4a13bbe7735fd681665b8a209abf86455914d6bc1fbd8730439ae"),
    ("01_Statutes_CRS/crs_title_01.md", "inputs/body.md", 1484379,
     "6acc70dac37bf035daba04bd0b554b985ac61f4e52424d227d2584e3cfe86ac5"),
)
CATALOG = "RESEARCH_CATALOG.local-subset.v1.jsonl"
BOUNDARY = (
    "Three selected derived CRS records only. Full copied input files do not mean all their "
    "records were validated. Original custody is unresolved; recorded dates, versions and URLs "
    "are inherited claims. No current-law, applicability, completeness or absence conclusion. "
    "Results contain metadata and exact derived-file locations, not verified legal evidence."
)
CURRENT = re.compile(
    r"\b(current|currently|today|now|latest|applicable|applies|apply|effective|legally|legal|"
    r"owe|calculate|calculation)\b|\bin\s+force\b|\?|"
    r"^\s*(what|how|is|are|can|may|must|do|does|should|will|would)\b", re.I,
)


class Strict(BaseModel):
    """Strict records with no inferred legal-state fields."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class FileRef(Strict):
    """Exact package bytes; paths are additionally confined before file access."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0, le=MAX_FILE)


class Span(Strict):
    """Half-open UTF-8 byte location in a frozen derived file."""

    path: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    line: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def ordered(self) -> Span:
        """Reject empty and reversed ranges."""
        if self.end <= self.start:
            raise ValueError("Invalid byte span")
        return self


class Claims(Strict):
    """Inherited source metadata, never verified acquisition or legal dates."""

    recorded_source_url: str
    recorded_original_path: str
    recorded_metadata_retrieved_date: date
    recorded_index_updated_at: AwareDatetime
    recorded_data_version: str
    recorded_publication_year: int | None
    recorded_effective_date: date | None
    interpretation: Literal["inherited_metadata_not_independently_verified"] = (
        "inherited_metadata_not_independently_verified"
    )


class ResearchRecord(Strict):
    """Metadata for one explicitly admitted derived section, with no statutory body."""

    id: str
    title: str
    title_number: Literal["1"] = "1"
    title_name: Literal["ELECTIONS"] = "ELECTIONS"
    article_number: Literal["1"] = "1"
    section_number: str
    authority_level: Literal["state"] = "state"
    input_kind: Literal["derived_record_only"] = "derived_record_only"
    original_custody: Literal["unresolved_nonportable_path"] = "unresolved_nonportable_path"
    index_line: Span
    metadata_line: Span
    heading: Span
    body: Span
    claims: Claims
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Manifest(Strict):
    """Deterministic closed package inventory and validation scope."""

    schema_version: Literal[1] = 1
    subset: Literal["crs-title1-first-three-v1"] = "crs-title1-first-three-v1"
    selected_ids: tuple[str, ...]
    inputs: tuple[FileRef, ...]
    catalog: FileRef
    schema_file: FileRef
    contracts: dict[str, str]
    boundary: str = BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Receipt(Strict):
    """Actual package creation time, separate from every recorded source date."""

    created_at: AwareDatetime
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    event: Literal["isolated_derived_package_created"] = "isolated_derived_package_created"
    original_acquisition_time: None = None


class Result(Strict):
    """Source-only metadata response and stable failure/refusal envelope."""

    status: Literal["built", "matched", "no_matching_record", "refused_current_law", "invalid"]
    records: tuple[ResearchRecord, ...] = Field(default=(), max_length=3)
    package_path: str | None = None
    manifest_sha256: str | None = None
    boundary: str = BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


def _sha(data: bytes) -> str:
    """Hash exact bytes without text normalization."""
    return hashlib.sha256(data).hexdigest()


def _json(data: object) -> bytes:
    """Serialize deterministic UTF-8 JSON with one final newline."""
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode()


def _absolute(path: Path) -> Path:
    """Reject traversal and symlinks before normalizing, including missing targets."""
    if ".." in path.parts:
        raise ValueError("Parent traversal is forbidden")
    path = path.absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink paths are forbidden")
    return path


def _read(base: Path, relative: str, limit: int = MAX_FILE) -> bytes:
    """Read one bounded regular file without following path aliases."""
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("Unconfined package path")
    target = _absolute(base / p)
    if not target.is_file():
        raise ValueError("Required regular file is missing")
    with target.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit or data.startswith(b"version https://git-lfs.github.com/spec/"):
        raise ValueError("Oversized or unhydrated input")
    return data


def _inputs(base: Path, packaged: bool) -> dict[str, bytes]:
    """Read only the three fixed inputs and verify their full custody hashes."""
    output = {}
    for original, copied, size, sha in INPUTS:
        data = _read(base, copied if packaged else original)
        if len(data) != size or _sha(data) != sha:
            raise ValueError("Fixed input identity changed")
        output[copied] = data
    if sum(map(len, output.values())) > MAX_TOTAL:
        raise ValueError("Input package exceeds total bound")
    return output


def _selected(
    data: bytes, path: str, max_lines: int,
) -> dict[str, tuple[dict[str, Any], Span]]:
    """Stream JSONL and locate exactly one line for each selected identity."""
    selected = {}
    offset = 0
    for number, line in enumerate(io.BytesIO(data), 1):
        if number > max_lines or len(line) > 2_000_000:
            raise ValueError("JSONL bounds exceeded")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError("JSONL row must be an object")
        identity = row.get("id")
        if identity in IDS:
            if identity in selected:
                raise ValueError("Duplicate selected identity")
            selected[identity] = (row, Span(path=path, start=offset, end=offset + len(line),
                                            sha256=_sha(line), line=number))
        offset += len(line)
    if set(selected) != set(IDS):
        raise ValueError("Selected identity is missing")
    return selected


def _derive(inputs: dict[str, bytes]) -> tuple[ResearchRecord, ...]:
    """Bind selected index and metadata records to exact Markdown sections."""
    indexes = _selected(inputs["inputs/index.jsonl"], "inputs/index.jsonl", 35_000)
    metadata = _selected(inputs["inputs/meta.jsonl"], "inputs/meta.jsonl", 1_000)
    md = inputs["inputs/body.md"]
    records = []
    for identity in IDS:
        index_raw, index_span = indexes[identity]
        meta_raw, meta_span = metadata[identity]
        index = LayerIndexRecord.model_validate(index_raw)
        section = StatuteSection.model_validate(meta_raw)
        text = meta_raw["full_text"].encode("utf-8")
        if (section.id != index.id or index.id != identity
                or section.section_num != identity.removeprefix("CRS-")
                or index.layer != "01_Statutes_CRS" or index.entity_type != "statute_section"
                or index.path != INPUTS[2][0] or index.meta_path != INPUTS[1][0]
                or index.citation != identity or index.title != f"{identity}: {section.heading}"
                or section.title_num != "1" or section.article_num != "1"
                or section.title_name != "ELECTIONS" or index.source_url != section.source_url
                or index.sha256 != _sha(text) or section.full_text.encode() != text
                or not PureWindowsPath(index.source_path).is_absolute()):
            raise ValueError("Index, metadata and recorded source identity disagree")
        header = f"#### {section.section_num}. {section.heading}\n\n".encode()
        if md.count(header) != 1:
            raise ValueError("Source heading is missing or ambiguous")
        start = md.index(header)
        body_start = start + len(header)
        end = body_start + len(text)
        if md[body_start:end] != text or not md[end:].startswith(b"\n\n#### "):
            raise ValueError("Exact Markdown section body does not match metadata")
        records.append(ResearchRecord(
            id=identity, title=section.heading, section_number=section.section_num,
            index_line=index_span, metadata_line=meta_span,
            heading=Span(path="inputs/body.md", start=start, end=body_start, sha256=_sha(header)),
            body=Span(path="inputs/body.md", start=body_start, end=end, sha256=_sha(text)),
            claims=Claims(recorded_source_url=str(section.source_url),
                          recorded_original_path=index.source_path,
                          recorded_metadata_retrieved_date=section.data_retrieved,
                          recorded_index_updated_at=index.last_updated,
                          recorded_data_version=section.data_version,
                          recorded_publication_year=index.publication_year,
                          recorded_effective_date=section.effective_date),
        ))
    return tuple(records)


def _schema() -> bytes:
    """Export each strict output model as a named JSON Schema."""
    models = (Manifest, Receipt, ResearchRecord, Result)
    return _json({model.__name__: model.model_json_schema() for model in models})


def _contracts() -> dict[str, str]:
    # Fingerprint runtime contracts; never execute code supplied by a package.
    """Fingerprint local implementation and validation contracts."""
    from geode.schemas import models, validators
    from geode import constants
    return {name: _sha(Path(module.__file__).read_bytes()) for name, module in (
        ("models", models), ("validators", validators), ("constants", constants),
    )} | {"research_catalog": _sha(Path(__file__).read_bytes())}


def _payload(
    inputs: dict[str, bytes],
) -> tuple[dict[str, bytes], Manifest, tuple[ResearchRecord, ...]]:
    """Construct validated deterministic payloads without filesystem writes."""
    records = _derive(inputs)
    catalog = b"".join(_json(r.model_dump(mode="json")) for r in records)
    schema = _schema()
    def ref(path: str, data: bytes) -> FileRef:
        """Identify one deterministic payload file."""
        return FileRef(path=path, sha256=_sha(data), size_bytes=len(data))

    manifest = Manifest(selected_ids=IDS, inputs=tuple(ref(p, b) for p, b in inputs.items()),
                        catalog=ref(CATALOG, catalog), schema_file=ref("schema.json", schema),
                        contracts=_contracts())
    files = {**inputs, CATALOG: catalog, "schema.json": schema,
             "manifest.json": _json(manifest.model_dump(mode="json"))}
    return files, manifest, records


def validate_package(package: Path) -> tuple[Manifest, tuple[ResearchRecord, ...]]:
    """Recompute every selected binding from fixed input bytes; never write."""
    package = _absolute(package)
    inputs = _inputs(package, True)
    files, manifest, records = _payload(inputs)
    expected = set(files) | {"receipt.json"}
    actual = set()
    directories = set()
    for p in package.rglob("*"):
        if p.is_symlink():
            raise ValueError("Package symlink is forbidden")
        if p.is_file():
            actual.add(p.relative_to(package).as_posix())
        elif p.is_dir():
            directories.add(p.relative_to(package).as_posix())
        else:
            raise ValueError("Nonregular package entry")
    if actual != expected or directories != {"inputs"}:
        raise ValueError("Package inventory differs")
    for path, content in files.items():
        if _read(package, path) != content:
            raise ValueError("Package bytes or contract differ")
    receipt = Receipt.model_validate_json(_read(package, "receipt.json", 100_000))
    if receipt.manifest_sha256 != _sha(files["manifest.json"]):
        raise ValueError("Receipt binds another manifest")
    return manifest, records


def build_package(root: Path, output: Path) -> Manifest:
    """Create one write-once package under the dedicated ignored research root."""
    root, output = _absolute(root), _absolute(output)
    allowed = root / OUTPUT_ROOT
    if (not root.is_dir() or output.parent != allowed
            or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", output.name)):
        raise ValueError("Output must be a named direct child of the isolated research root")
    if output.exists():
        raise ValueError("Package already exists; verify it instead of overwriting")
    files, manifest, _ = _payload(_inputs(root, False))  # All validation precedes writes.
    receipt = Receipt(created_at=datetime.now(timezone.utc),
                      manifest_sha256=_sha(files["manifest.json"]))
    files["receipt.json"] = _json(receipt.model_dump(mode="json"))
    allowed.mkdir(parents=True, exist_ok=True)
    _absolute(allowed)
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=allowed))
    try:
        for name, content in files.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(content)
        validate_package(staging)
        _absolute(output)
        if output.exists():
            raise ValueError("Output appeared during build")
        os.rename(staging, output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return manifest


def query_package(package: Path, query: str | None = None, *, list_records: bool = False,
                  mode: str = "source") -> Result:
    """Return only selected metadata; question/current-law requests never release evidence."""
    if mode not in {"source", "current-law"} or list_records == (query is not None):
        raise ValueError("Invalid query contract")
    if query is not None and (not query.strip() or len(query) > 512):
        raise ValueError("Query must contain 1–512 characters")
    if mode == "current-law" or (query is not None and CURRENT.search(query)):
        return Result(status="refused_current_law")
    manifest, records = validate_package(package)
    needle = " ".join(query.casefold().split()) if query is not None else None
    matches = tuple(r for r in records if needle is None or needle in " ".join(
        f"{r.id} {r.title_name} {r.title} {r.section_number}".casefold().split()))
    return Result(status="matched" if matches else "no_matching_record", records=matches,
                  package_path=str(_absolute(package)),
                  manifest_sha256=_sha(_json(manifest.model_dump(mode="json"))))


def main(argv: list[str] | None = None) -> int:
    """Build an isolated package, or inspect metadata with explicit research limits."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--root", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    query = commands.add_parser("query")
    query.add_argument("--package", required=True, type=Path)
    action = query.add_mutually_exclusive_group(required=True)
    action.add_argument("--query")
    action.add_argument("--list-records", action="store_true")
    query.add_argument("--mode", choices=["source", "current-law"], default="source")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            manifest = build_package(args.root, args.output)
            result = Result(status="built", package_path=str(_absolute(args.output)),
                            manifest_sha256=_sha(_json(manifest.model_dump(mode="json"))))
        else:
            result = query_package(args.package, args.query, list_records=args.list_records,
                                   mode=args.mode)
    except (ValueError, OSError, KeyError, TypeError):
        result = Result(status="invalid")
    sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    return 1 if result.status == "invalid" else 2 if result.status == "refused_current_law" else 0


if __name__ == "__main__":
    raise SystemExit(main())
