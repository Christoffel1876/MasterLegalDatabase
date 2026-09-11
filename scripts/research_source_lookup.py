"""Look up one frozen source table without making current-law or applicability claims."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

SOURCE_ID = "grand-junction-fire-fees-atlas-directed"
REVIEW_SOURCE_ID = "grand-junction-fire-fees-mg-07"
PACKAGE = Path("research/local_review/grand-junction-fire-fees-atlas-source-review-2026-09-11")
PINS = {
    "original.pdf": "1f7faf078188c26fa803e4ec6225d20caad2fcce48f69d2d2ae9563c96732884",
    "SOURCE_QA.json": "8069accad238166936f6ee519eb8cc35dc9a62ceb252597ea21a4ebc5efc520a",
    "MANIFEST.json": "ae22dfaabb6a0793f0e16849dacf5ead0b90e00d01d67c5ceebfb614072cc02f",
    "build_review.py": "9db445db05a1eb6810a649c14319f9451aff601b22722fe3fcaebbdaad565eea",
}
BOUNDARY = (
    "The preserved source states the quoted text. This is a lookup of one checked "
    "57-row snapshot, not current law, an applicability decision or a fee calculation. "
    "No matching row does not establish that a service is free, exempt or unregulated."
)
CURRENT_REQUEST = re.compile(
    r"\b(current(?:ly)?|today|now|latest|applicab\w*|appl(?:y|ies)|effective|"
    r"legal(?:ly)?|in force|calculate|calculation|owe|total cost)\b|"
    r"^\s*(what|how|is|are|can|may|must|do|does|should|will|would)\b|\?",
    re.IGNORECASE,
)


class StrictModel(BaseModel):
    """Keep source-only output fields explicit and reject unexpected fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class SpanBinding(StrictModel):
    """Identify an unchanged reviewed native span, including its exact bytes."""

    id: str
    physical_page: int
    native_path: str
    start: int
    end: int
    sha256: str


class SourceBinding(StrictModel):
    """Identify the canonical source and the review's historical alias separately."""

    canonical_source_id: Literal["grand-junction-fire-fees-atlas-directed"] = SOURCE_ID
    review_source_id: Literal["grand-junction-fire-fees-mg-07"] = REVIEW_SOURCE_ID
    source_url: str
    pdf_sha256: str
    review_sha256: str
    manifest_sha256: str
    verifier_sha256: str
    pdf_path: str
    review_path: str
    reviewed_at: AwareDatetime
    source_retrieved_at: AwareDatetime


class MatchedRow(StrictModel):
    """Preserve the full group, label and fee, including continuation provenance."""

    row_id: str
    physical_page: int
    group: str
    label: str
    fee: str
    group_basis: str
    group_binding: SpanBinding
    label_binding: SpanBinding
    fee_binding: SpanBinding
    page_image_path: str


class LookupResult(StrictModel):
    """A source-reporting result that never authorizes legal reliance."""

    status: Literal["matched", "no_matching_row", "refused_current_law"]
    source_id: Literal["grand-junction-fire-fees-atlas-directed"] = SOURCE_ID
    query: str | None
    evidence_verified: bool
    source: SourceBinding | None = None
    rows: list[MatchedRow]
    observations: list[str]
    page_context: dict[str, list[str]]
    boundary: str = BOUNDARY
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    adoption_date: None = None
    effective_date: None = None
    source_edition_date: None = None


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file(package: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Evidence path leaves the fixed package")
    full = package / path
    if any(p.is_symlink() for p in (full, *full.parents)) or not full.is_file():
        raise ValueError(f"Missing or symlinked evidence: {relative}")
    return full


def _check_package(package: Path) -> bytes:
    for name, expected in PINS.items():
        if _digest(_safe_file(package, name)) != expected:
            raise ValueError(f"Frozen evidence hash mismatch: {name}")
    manifest = json.loads((package / "MANIFEST.json").read_bytes())
    for item in manifest["files"]:
        path = _safe_file(package, item["path"])
        if path.stat().st_size != item["size_bytes"] or _digest(path) != item["sha256"]:
            raise ValueError(f"Package evidence mismatch: {item['path']}")
    return (package / "SOURCE_QA.json").read_bytes()


def _load_verified(package: Path) -> dict:
    before = _check_package(package)
    try:
        subprocess.run(
            [sys.executable, "-I", "-B", str(package / "build_review.py"), "--verify"],
            cwd=package, check=True, capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ValueError("Existing source-package verification failed") from exc
    if _check_package(package) != before:
        raise ValueError("Evidence changed during verification")
    return json.loads(before)


def _search_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def lookup(
    root: Path,
    source_id: str,
    query: str | None = None,
    *,
    list_rows: bool = False,
    mode: Literal["source", "current-law"] = "source",
) -> LookupResult:
    """Validate the fixed package and return unchanged rows for a literal keyword phrase."""
    if source_id != SOURCE_ID:
        raise ValueError("Only grand-junction-fire-fees-atlas-directed is supported")
    if mode not in {"source", "current-law"}:
        raise ValueError("Unsupported lookup mode")
    if list_rows == (query is not None):
        raise ValueError("Choose exactly one of query or list_rows")
    if query is not None and not query.strip():
        raise ValueError("A nonempty keyword phrase is required")
    if mode == "current-law" or (query is not None and CURRENT_REQUEST.search(query)):
        return LookupResult(
            status="refused_current_law", query=query, evidence_verified=False, rows=[],
            observations=["Current-law and question answering are unsupported; use keywords "
                          "only to inspect what this preserved source says."], page_context={},
        )
    root = root.expanduser().absolute()
    if ".." in root.parts:
        raise ValueError("Use a root without parent traversal")
    package = root / PACKAGE
    data = _load_verified(package)
    if data["source_id"] != REVIEW_SOURCE_ID:
        raise ValueError("The review's historical source alias does not match")
    spans = {s["id"]: (p, s) for p in data["pages"] for s in p["spans"]}

    def bind(span_id: str) -> SpanBinding:
        page, span = spans[span_id]
        return SpanBinding(
            id=span_id, physical_page=page["physical_page"],
            native_path=str(package / page["native"]["path"]), start=span["start"],
            end=span["end"], sha256=hashlib.sha256(span["text"].encode()).hexdigest(),
        )

    rows = []
    for row in data["rows"]:
        group = spans[row["group_span"]][1]["text"]
        label = spans[row["label_span"]][1]["text"]
        fee = spans[row["fee_span"]][1]["text"]
        if query is not None:
            needle = _search_text(query)
            left = r"(?<![\w.,])" if needle[0].isdigit() else r"(?<!\w)"
            right = r"(?![\w.,])" if needle[-1].isdigit() else r"(?!\w)"
            phrase = left + re.escape(needle) + right
            if not re.search(phrase, _search_text(group + label + fee)):
                continue
        rows.append(MatchedRow(
            row_id=row["id"], physical_page=row["physical_page"], group=group,
            label=label, fee=fee, group_basis=row["group_basis"],
            group_binding=bind(row["group_span"]), label_binding=bind(row["label_span"]),
            fee_binding=bind(row["fee_span"]),
            page_image_path=str(package / f"page-{row['physical_page']}.png"),
        ))
    event = json.loads((package / "access-event.json").read_bytes())
    source = SourceBinding.model_validate_json(json.dumps({
        "source_url": data["official_url"], "pdf_sha256": PINS["original.pdf"],
        "review_sha256": PINS["SOURCE_QA.json"], "manifest_sha256": PINS["MANIFEST.json"],
        "verifier_sha256": PINS["build_review.py"], "pdf_path": str(package / "original.pdf"),
        "review_path": str(package / "SOURCE_QA.json"), "reviewed_at": data["reviewed_at"],
        "source_retrieved_at": event["completed_at"],
    }))
    return LookupResult(
        status="matched" if rows else "no_matching_row", query=query, evidence_verified=True,
        source=source, rows=rows, observations=[o["statement"] for o in data["observations"]],
        page_context={str(p["physical_page"]): [s["text"] for s in p["spans"]
                      if s["role"] in {"header", "footer"}] for p in data["pages"]},
    )


def _markdown(text: str) -> str:
    escaped = html.escape(text.rstrip("\n"), quote=False)
    return re.sub(r"([\\`*_[\]{}|])", r"\\\1", escaped).replace("\n", "<br>")


def _link(label: str, path: str) -> str:
    safe = path.replace("<", "%3C").replace(">", "%3E").replace("\n", "%0A")
    return f"[{label}](<{safe}>)"


def render_markdown(result: LookupResult) -> str:
    """Render quoted source rows and their evidence links without calculating fees."""
    lines = ["Source-only research lookup — legal_currentness: not_verified; answer_safe: false.",
             "", result.boundary, "",
             "Adoption date: unknown. Effective date: unknown. Source edition date: unknown.", ""]
    if result.status == "refused_current_law":
        return "\n".join(lines + ["Request refused. " + result.observations[0], ""])
    source = result.source
    if source is None:
        raise ValueError("Verified source binding is required")
    lines += [f"Source: `{result.source_id}` (review alias `{source.review_source_id}`).", "",
              f"[Official source]({source.source_url})", "",
              f"- PDF SHA-256: `{source.pdf_sha256}`",
              f"- Review SHA-256: `{source.review_sha256}`",
              f"- Retrieved: {source.source_retrieved_at.isoformat()}; "
              f"reviewed: {source.reviewed_at.isoformat()}.",
              "",
              _link("Source PDF", source.pdf_path) + " · " +
              _link("Checked review", source.review_path), ""]
    if not result.rows:
        lines += ["No matching row in this preserved source snapshot.", ""]
    for row in result.rows:
        lines += [f"**{row.row_id} — physical page {row.physical_page}**", "",
                  f"- Group: {_markdown(row.group)}", f"- Label: {_markdown(row.label)}",
                  f"- The preserved source states: {_markdown(row.fee)}",
                  f"- Group basis: `{row.group_basis}`; spans "
                  f"`{row.group_binding.id}` / `{row.label_binding.id}` / `{row.fee_binding.id}`.",
                  "", _link("Page image", row.page_image_path), ""]
    lines += ["Source-review qualifications:", ""]
    lines += ["- " + _markdown(note) for note in result.observations]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write a qualified research result to stdout; fail closed on invalid evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-id", required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--query")
    action.add_argument("--list-rows", action="store_true")
    parser.add_argument("--mode", choices=["source", "current-law"], default="source")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)
    try:
        result = lookup(args.root, args.source_id, args.query,
                        list_rows=args.list_rows, mode=args.mode)
        output = (result.model_dump_json(indent=2) + "\n" if args.format == "json"
                  else render_markdown(result))
    except (ValueError, OSError, KeyError) as exc:
        logging.error("Research source lookup failed: %s", exc)
        return 1
    sys.stdout.write(output)
    return 2 if result.status == "refused_current_law" else 0


if __name__ == "__main__":
    raise SystemExit(main())
