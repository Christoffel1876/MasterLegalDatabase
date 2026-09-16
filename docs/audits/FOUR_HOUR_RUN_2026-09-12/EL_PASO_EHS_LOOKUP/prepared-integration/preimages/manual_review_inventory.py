"""Inventory exact manual sources and explicitly allowlisted research review scopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord
from geode.utils.file_io import atomic_write_text, iter_jsonl

PACKAGE = Path("research/local_review/manual-source-review-inventory-2026-09-11")
PLAN = PACKAGE / "join-plan.json"
ReviewKind = Literal["native_candidate", "checked_passages", "checked_tables", "source_structure"]
# Exact schema identities, reviewed individually; no directory-name or filename inference.
ALLOWED_REVIEW_SCHEMAS: dict[str, ReviewKind] = {
    "2e25d770a6d69f66088fd711ac0fa58084e4d3a5bfc0a89a1e12d67f38c0d7e4": "checked_passages",
    "d29c8fdee28168161fd2d0e83c10a2d72d0d545cac9525ea17d05bc2549e5b63": "checked_tables",
    "01cce506b8e53c71079d275681c4296bcfe1f7abbe0475e3b2422f9fd579daea": "checked_passages",
    "ade2d62932c258b3cc4f34817dcbf8568c8cd44080ba0ce032c4713f89f3d342": "checked_tables",
    "f05bebf8c6b3cf626da067dfa4e546b4dfd95c37b926d7f3d95a22d789beda5e": "source_structure",
    "2f23a302a62096c4c83b2ca4b41b138baa338f37ce6fdeca7f2eda8cc3a00793": "checked_passages",
    "e9125bea7708fd4d75f1f32f517d0e9fad23c06b54c196b955ff23c75542a18f": "source_structure",
    "8bfb9a3872312a028eb385c78ec02ca643891febfd80cd3128c54a7f31fcec9f": "source_structure",
    "444c2c98e2b08bff1f53ebdca8594668d7f85a8d521aba31d72a53a4bc4f656d": "checked_tables",
    "056f3ba5c55a61987e2417c131a61569e2274798d83b0d8bdd0815e642de02be": "source_structure",
    "d634dc0aa26fbea08cfa7b41bf46ada615dd8dcdc08e98207d5a8da3cfd0b545": "checked_tables",
    "dbaa6a2026720420bb0007eeba85f71937552dbacf3c9e85a6d57966b5f478ea": "checked_tables",
    "b877596c9b3c7a2a13ea4407b73536bd4011b53db1dcc750fcb3171453d7afe7": "checked_tables",
    "0d34834d1eb51aa3595b1801f7fccd27db9dd35e909a3c488965547d67bde9cc": "checked_tables",
    "82e201c93da9a1bcbff5d6486a5fb97e7d4ac22ce7acb4dff20594d61c281bc8": "checked_tables",
    "189864ee39df3c792916045a92a36dd64634495bc7fcf5579b176a0f5059e529": "checked_tables",
    "13e23d55f3dbccef04bd6fbd113e7ca20ccb91bd8dd5dfa07c0454b68f0b6aeb": "checked_tables",
    "a424f4dd025089ba144d4a49d902a2fd549447c6d4d4f0c9931588e61e8c8535": "source_structure",
    "3ece308140181240c4f9c908d522d16f07f00b84b9e780ed10af1306a8a0dfee": "checked_passages",
    "62bd37c307f251742d70f1b9a6df62577ee5079d9333e09a6c4aae624189edc3": "checked_tables",
    "44193e1bd8f0b3186cacdc7ec48e4a004aa6b18208badc290d6dfbe0b14948d9": "checked_tables",
}


class Strict(BaseModel):
    """Reject unexpected fields and implicit scalar coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Artifact(Strict):
    """Identify immutable local bytes within the selected repository."""

    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Document(Strict):
    """Select one JSON object or a zero-based JSONL row without executing package code."""

    artifact: Artifact
    jsonl_row: int | None = Field(default=None, ge=0)


class HttpBinding(Strict):
    """Identify a recorded successful HTTP acquisition, not a repository intake time."""

    document: Document
    sha_pointer: str
    status_pointer: str
    time_pointer: str


class AuthorityJoin(Strict):
    """Bind authority and source identity to an exact provenance record."""

    record_id: str
    authority_id: str
    provenance: Document
    sha_pointer: str
    source_id_pointer: str
    authority_pointer: str
    reported_acquisition_pointers: list[str] = Field(default_factory=list)
    role_pointers: list[str] = Field(default_factory=list)
    qualification_pointers: list[str] = Field(default_factory=list)
    verified_http: HttpBinding | None = None


class ReviewJoin(Strict):
    """Allow one exact schema-backed review and its recorded, bounded scope."""

    record_id: str
    review: Artifact
    review_schema: Artifact
    source_sha_pointer: str
    source_id_pointer: str | None = None
    expected_review_source_id: str | None = None
    authority_pointer: str | None = None
    scope_pointers: list[str] = Field(min_length=1)
    limitation_pointers: list[str] = Field(min_length=1)
    note: str


class JoinPlan(Strict):
    """An explicit source/review allowlist for one immutable manual-manifest snapshot."""

    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    manual_manifest: Artifact
    legacy_ledger: Artifact
    authorities: list[AuthorityJoin]
    reviews: list[ReviewJoin]
    limitations: list[str]


class ReviewBinding(Strict):
    """Recorded review evidence; scopes are never summed across overlapping artifacts."""

    artifact: Artifact
    schema_artifact: Artifact
    review_kind: ReviewKind
    review_source_id: str | None
    scope_fields: dict[str, Any]
    limitations: dict[str, Any]
    note: str
    scope_status: Literal["as_recorded_not_global_certification"] = (
        "as_recorded_not_global_certification"
    )
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class SourceRow(Strict):
    """One canonical manual source with retained provenance and nullable review evidence."""

    record_id: str
    intake_id: str
    authority_id: str
    layer_id: Literal["08_County_Authorities", "10_Municipal_Authorities"]
    source: Artifact
    official_source_url: str | None
    acquisition_method: str
    intake_received_at: AwareDatetime
    verified_http_acquired_at: AwareDatetime | None
    verified_http_evidence: HttpBinding | None
    reported_acquisition: dict[str, Any]
    source_roles: dict[str, Any]
    authority_evidence: Document
    provenance_qualifications: dict[str, Any]
    custody_note: str
    recorded_intake_status: str
    reviews: list[ReviewBinding] | None
    review_status: Literal["metadata_only_review_unknown", "explicit_review_artifacts_linked"]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False


class Inventory(Strict):
    """Research bridge that preserves all custody rows without promoting legal reliance."""

    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    plan: Artifact
    manual_manifest: Artifact
    unchanged_legacy_ledger: Artifact
    sources: list[SourceRow]
    rows_with_review: int
    rows_without_review: int
    limitations: list[str]
    legal_currentness: Literal["not_verified"] = "not_verified"
    answer_safe: Literal[False] = False
    coverage_promotion: Literal[False] = False

    @model_validator(mode="after")
    def _consistent_counts(self) -> Inventory:
        if len({row.record_id for row in self.sources}) != len(self.sources):
            raise ValueError("Duplicate inventory source identity")
        reviewed = sum(row.reviews is not None for row in self.sources)
        if (self.rows_with_review, self.rows_without_review) != (
            reviewed, len(self.sources) - reviewed,
        ):
            raise ValueError("Inventory review counts differ from recorded source rows")
        for row in self.sources:
            expected = ("explicit_review_artifacts_linked" if row.reviews is not None
                        else "metadata_only_review_unknown")
            if row.reviews == [] or row.review_status != expected:
                raise ValueError("Inventory review status differs from recorded artifacts")
        return self


def safe_path(root: Path, relative: str) -> Path:
    """Reject parent traversal, absolute paths and symlinks before resolving evidence."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe evidence path: {relative}")
    full = root / path
    if any(p.is_symlink() for p in (full, *full.parents)):
        raise ValueError(f"Symlinked evidence path: {relative}")
    return full


def normalize_root(root: Path) -> Path:
    """Use one absolute, expanded root while rejecting lexical escape and symlinks."""
    root = root.expanduser().absolute()
    if ".." in root.parts:
        raise ValueError("Repository root must not contain parent traversal")
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("Repository root must not contain symlinks")
    return root


def identity(root: Path, relative: str) -> Artifact:
    """Hash one ordinary file using bounded reads."""
    path = safe_path(root, relative)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return Artifact(path=relative, sha256=digest.hexdigest(), size_bytes=path.stat().st_size)


def _require(root: Path, artifact: Artifact) -> Path:
    if identity(root, artifact.path) != artifact:
        raise ValueError(f"Evidence hash/size mismatch: {artifact.path}")
    return safe_path(root, artifact.path)


def pointer(data: Any, value: str) -> Any:
    """Read an explicit JSON pointer; no expressions, recursive search or inference."""
    if value == "":
        return data
    if not value.startswith("/"):
        raise ValueError(f"Invalid JSON pointer: {value}")
    for token in value[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def _document(root: Path, spec: Document) -> Any:
    path = _require(root, spec.artifact)
    if spec.jsonl_row is None:
        return json.loads(path.read_bytes())
    for number, row in enumerate(iter_jsonl(path)):
        if number == spec.jsonl_row:
            return row
    raise ValueError("Provenance JSONL row is missing")


def _fields(data: Any, pointers: list[str]) -> dict[str, Any]:
    return {key: pointer(data, key) for key in pointers}


def _local_schema(schema: Any) -> None:
    if isinstance(schema, dict):
        if "$ref" in schema and not schema["$ref"].startswith("#"):
            raise ValueError("External schema references are forbidden")
        for value in schema.values():
            _local_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            _local_schema(value)


def _review(root: Path, join: ReviewJoin, row: SourceRow) -> ReviewBinding:
    kind = ALLOWED_REVIEW_SCHEMAS.get(join.review_schema.sha256)
    if kind is None:
        raise ValueError("Review schema is not in the explicit allowlist")
    data = json.loads(_require(root, join.review).read_bytes())
    schema = json.loads(_require(root, join.review_schema).read_bytes())
    _local_schema(schema)
    jsonschema.validate(data, schema)
    if pointer(data, join.source_sha_pointer) != row.source.sha256:
        raise ValueError("Review/source SHA mismatch")
    source_id = pointer(data, join.source_id_pointer) if join.source_id_pointer else None
    if source_id != join.expected_review_source_id:
        raise ValueError("Review source identity mismatch")
    if join.authority_pointer and pointer(data, join.authority_pointer) != row.authority_id:
        raise ValueError("Review authority mismatch")
    return ReviewBinding(
        artifact=join.review, schema_artifact=join.review_schema, review_kind=kind,
        review_source_id=source_id, scope_fields=_fields(data, join.scope_pointers),
        limitations=_fields(data, join.limitation_pointers), note=join.note,
    )


def build_inventory(root: Path, plan_path: str = PLAN.as_posix()) -> Inventory:
    """Verify every raw/provenance/review join and build deterministic research records."""
    root = normalize_root(root)
    plan_asset = identity(root, plan_path)
    plan = JoinPlan.model_validate_json(safe_path(root, plan_path).read_bytes())
    manifest = _require(root, plan.manual_manifest)
    _require(root, plan.legacy_ledger)
    joins = {join.record_id: join for join in plan.authorities}
    if len(joins) != len(plan.authorities):
        raise ValueError("Duplicate authority join")
    records, intake_ids, archive_paths = {}, set(), set()
    for value in iter_jsonl(manifest):
        record = ManualSourceIntakeRecord.model_validate_json(json.dumps(value), strict=True)
        if record.record_id in records or record.intake_id in intake_ids:
            raise ValueError("Duplicate or colliding manual source identity")
        if record.archive_path in archive_paths:
            raise ValueError("Colliding manual archive path")
        if record.source_format != "pdf":
            raise ValueError("This inventory accepts only the selected manual PDFs")
        records[record.record_id] = record
        intake_ids.add(record.intake_id)
        archive_paths.add(record.archive_path)
    if set(records) != set(joins):
        raise ValueError("Authority plan must account for every manual source exactly once")
    result = []
    for key, record in records.items():
        join = joins[key]
        if not Path(record.archive_path).is_relative_to("_RAW_ARCHIVE/manual_intake"):
            raise ValueError("Manual source is outside its immutable archive")
        source = Artifact(path=record.archive_path, sha256=record.sha256,
                          size_bytes=record.size_bytes)
        _require(root, source)
        provenance = _document(root, join.provenance)
        if (pointer(provenance, join.sha_pointer) != record.sha256
                or pointer(provenance, join.source_id_pointer) != key):
            raise ValueError("Authority evidence does not bind the exact source")
        if pointer(provenance, join.authority_pointer) != join.authority_id:
            raise ValueError("Authority identity differs from provenance")
        prefix = {"08_County_Authorities": "CO-COUNTY-",
                  "10_Municipal_Authorities": "CO-MUNICIPAL-"}.get(record.layer_id)
        if prefix is None or not join.authority_id.startswith(prefix):
            raise ValueError("Source authority and layer disagree")
        acquired = None
        if join.verified_http:
            http = _document(root, join.verified_http.document)
            if (pointer(http, join.verified_http.sha_pointer) != record.sha256
                    or pointer(http, join.verified_http.status_pointer) != 200):
                raise ValueError("HTTP evidence does not bind a successful source response")
            acquired = datetime.fromisoformat(
                pointer(http, join.verified_http.time_pointer).replace("Z", "+00:00"))
        result.append(SourceRow(
            record_id=key, intake_id=record.intake_id, authority_id=join.authority_id,
            layer_id=record.layer_id, source=source, official_source_url=record.official_source_url,
            acquisition_method=record.acquisition_method, intake_received_at=record.received_at,
            verified_http_acquired_at=acquired, verified_http_evidence=join.verified_http,
            reported_acquisition=_fields(provenance, join.reported_acquisition_pointers),
            source_roles=_fields(provenance, join.role_pointers),
            authority_evidence=join.provenance,
            provenance_qualifications=_fields(provenance, join.qualification_pointers),
            custody_note=record.custody_note, recorded_intake_status=record.status,
            reviews=None, review_status="metadata_only_review_unknown",
        ))
    by_id = {row.record_id: row for row in result}
    seen_reviews = set()
    for join in plan.reviews:
        if join.record_id not in by_id:
            raise ValueError("Review refers to an unknown manual source")
        if join.review.sha256 in seen_reviews:
            raise ValueError("Duplicate review artifact; overlapping copies are not additive")
        seen_reviews.add(join.review.sha256)
        row = by_id[join.record_id]
        binding = _review(root, join, row)
        row.reviews = [*(row.reviews or []), binding]
        row.review_status = "explicit_review_artifacts_linked"
    _require(root, plan.manual_manifest)
    _require(root, plan.legacy_ledger)
    _require(root, plan_asset)
    reviewed = sum(row.reviews is not None for row in result)
    return Inventory(
        prepared_at=plan.prepared_at, plan=plan_asset, manual_manifest=plan.manual_manifest,
        unchanged_legacy_ledger=plan.legacy_ledger, sources=result, rows_with_review=reviewed,
        rows_without_review=len(result) - reviewed, limitations=plan.limitations,
    )


def _render_outputs(inventory: Inventory) -> dict[str, str]:
    Inventory.model_validate_json(inventory.model_dump_json())
    lines = ["---", "title: Manual source and recorded review inventory",
             "legal_currentness: not_verified", "answer_safe: false", "---", "",
             "# Manual source/review inventory", "",
             f"{len(inventory.sources)} custody rows; "
             f"{inventory.rows_with_review} have an explicit "
             f"review link and {inventory.rows_without_review} have no allowlisted review link.",
             "These are source-custody counts, not statewide coverage or current-law readiness.",
             "", "From the repository root:", "", "```bash",
             "python -m geode.pipeline.manual_review_inventory --root . --check", "```", "",
             "| Source ID | Authority | Recorded review kind |", "| --- | --- | --- |"]
    for row in inventory.sources:
        kinds = ", ".join(sorted({r.review_kind for r in row.reviews or []})) or "metadata only"
        lines.append(f"| {row.record_id} | {row.authority_id} | {kinds} |")
    lines += ["", "## Limits", "", *["- " + note for note in inventory.limitations], "",
              "Exact artifact hashes, recorded scope fields, provenance claims and timestamps "
              "are retained in inventory.json. Linked scopes overlap and must not be summed.", ""]
    return {
        "inventory.json": json.dumps(inventory.model_dump(mode="json"),
                                     ensure_ascii=False, indent=2) + "\n",
        "inventory.schema.json": json.dumps(Inventory.model_json_schema(),
                                            ensure_ascii=False, indent=2) + "\n",
        "README.md": "\n".join(lines),
    }


def _output_paths(root: Path, outputs: dict[str, str]) -> dict[str, Path]:
    paths = {name: safe_path(root, (PACKAGE / name).as_posix()) for name in outputs}
    snapshots = safe_path(root, (PACKAGE / "_SNAPSHOTS").as_posix())
    if snapshots.exists() and not snapshots.is_dir():
        raise ValueError("Snapshot destination is not a directory")
    for path in paths.values():
        if path.exists() and not path.is_file():
            raise ValueError(f"Output is not an ordinary file: {path}")
    return paths


def write_inventory(root: Path, inventory: Inventory) -> None:
    """Preflight all companions, then repair changed output with package-local snapshots."""
    root = normalize_root(root)
    outputs = _render_outputs(inventory)
    paths = _output_paths(root, outputs)
    package = safe_path(root, PACKAGE.as_posix())
    changed = [name for name, path in paths.items()
               if not path.exists() or path.read_bytes() != outputs[name].encode("utf-8")]
    for name in changed:
        atomic_write_text(paths[name], outputs[name], package)


def check_inventory(root: Path, inventory: Inventory) -> None:
    """Verify every deterministic companion without repairing or writing any file."""
    root = normalize_root(root)
    outputs = _render_outputs(inventory)
    for name, path in _output_paths(root, outputs).items():
        if path.read_bytes() != outputs[name].encode("utf-8"):
            raise ValueError(f"Saved inventory companion differs: {name}")


def main(argv: list[str] | None = None) -> int:
    """Build with --write or verify the existing deterministic inventory without writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--plan", default=PLAN.as_posix())
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--write", action="store_true")
    actions.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = normalize_root(args.root)
        inventory = build_inventory(root, args.plan)
        if args.write:
            write_inventory(root, inventory)
        else:
            check_inventory(root, inventory)
        logging.info("Verified %d sources; %d with review links; legal currentness not verified",
                     len(inventory.sources), inventory.rows_with_review)
        return 0
    except (ValueError, OSError, KeyError, IndexError, TypeError, jsonschema.ValidationError,
            jsonschema.SchemaError) as exc:
        logging.error("Manual review inventory failed: %s", exc)
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
