"""Portable read-only seal/schema/custody check; does not import or execute the transaction."""
from __future__ import annotations
import hashlib
import json
import os
import stat
from pathlib import Path
from urllib.parse import urljoin
import jsonschema
import pymupdf
from bs4 import BeautifulSoup
from models import Asset, Manifest, Preparation

HERE = Path(__file__).absolute().parent
EXPECTED_PLAN = "d4c756566d32edcc55fc46137753a515d3663c476a0485a682ddd126b19cf932"
EXPECTED_AUDIT = "254f53e93784937b2d3fa632fce84d64a6beb77218f6052bdb82d9f7115c897d"


def ordinary(root, name):
    path = root / name
    relative = Path(name)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in name
            or relative.as_posix() != name):
        raise ValueError("unsafe reference")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("linked evidence")
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("not an ordinary evidence file")
    return path


def checked(root, item):
    path = ordinary(root, item.path)
    raw = path.read_bytes()
    if len(raw) != item.size_bytes or hashlib.sha256(raw).hexdigest() != item.sha256:
        raise ValueError("evidence pin differs: " + item.path)
    return raw


def typed(root, name, model):
    raw = ordinary(root, name + ".json").read_bytes()
    schema = json.loads(ordinary(root, name + ".schema.json").read_bytes())
    if schema != model.model_json_schema():
        raise ValueError("schema differs")
    jsonschema.validate(json.loads(raw), schema)
    return model.model_validate_json(raw), raw


def verify(root=HERE):
    manifest, _ = typed(root, "FINAL_MANIFEST", Manifest)
    expected = {a.path for a in manifest.files} | {"FINAL_MANIFEST.json"}
    found = set()
    execution = []
    for top, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            p = Path(top) / name
            if p.is_symlink():
                raise ValueError("linked package member")
        for name in files:
            p = Path(top) / name
            if not stat.S_ISREG(p.stat().st_mode):
                raise ValueError("nonordinary package member")
            rel = p.relative_to(root).as_posix()
            if rel.startswith("execution/"):
                execution.append(rel)
            else:
                found.add(rel)
    if len(expected) != len(manifest.files) + 1 or found != expected:
        raise ValueError("closed preparation membership differs")
    for item in manifest.files:
        checked(root, item)
    plan, raw = typed(root, "PREPARATION", Preparation)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_PLAN:
        raise ValueError("preparation identity differs")
    if plan.recommendation_manifest.sha256 != EXPECTED_AUDIT:
        raise ValueError("recommendation seal differs")
    buffers = {a.path: checked(root, a) for a in plan.custody_subset}
    parent_manifest = json.loads(buffers[plan.recommendation_manifest.path])
    pins = {a["path"]: a for a in parent_manifest["files"]}
    for item in plan.custody_subset:
        name = item.path.removeprefix("inputs/audit/")
        if name != "FINAL_MANIFEST.json":
            pin = pins[name]
            if item.sha256 != pin["sha256"] or item.size_bytes != pin["size_bytes"]:
                raise ValueError("partial supporting subset differs from full audit seal")
    source_pages = 0
    for source, provenance in zip(plan.templates, plan.provenance):
        body = buffers[source.source.path]
        with pymupdf.open(stream=body, filetype="pdf") as doc:
            if (doc.page_count != provenance.physical_pages or doc.is_repaired or doc.is_encrypted
                    or not body.rstrip().endswith(b"%%EOF")):
                raise ValueError("source structural identity differs")
            source_pages += doc.page_count
        soup = BeautifulSoup(buffers[provenance.parent.path], "html.parser")
        pairs = {(a.get("href"), " ".join(a.get_text(" ", strip=True).split()))
                 for a in soup.select("a[href]")}
        if ((provenance.original_href, provenance.visible_label) not in pairs
                or soup.find("base") is not None
                or urljoin(provenance.parent_url, provenance.original_href)
                != provenance.requested_url_reported):
            raise ValueError("parent source referral differs")
        headers = json.loads(buffers[provenance.public_headers.path])
        if {k.lower() for k in headers["headers"]} & {
                "set-cookie", "cookie", "authorization", "proxy-authorization"}:
            raise ValueError("private transport header in selected public copy")
    for item in plan.baseline:
        content = checked(root, item.preserved)
        if item.records is not None:
            import io
            count = 0
            with io.BytesIO(content) as stream:
                for line in stream:
                    json.loads(line)
                    count += 1
            if count != item.records or not content.endswith(b"\n"):
                raise ValueError("preserved prefix record count/newline differs")
    allowed_execution = {"execution/LOCK", "execution/INTENT.json", "execution/RECEIPT.json"}
    allowed_execution.update("execution/preimages/" + Path(i.repository_path).name
                             for i in plan.baseline)
    if not set(execution) <= allowed_execution:
        raise ValueError("unknown execution payload")
    return {
        "status": "passed", "closed_payloads": len(manifest.files), "sources": 3,
        "physical_pages": source_pages, "source_bytes": sum(t.source.size_bytes for t in plan.templates),
        "raw_before": plan.raw_before, "raw_after": plan.raw_after,
        "ledger_before": plan.ledger_before, "ledger_after": plan.ledger_after,
        "future_execution_present": bool(execution), "execution_validated": False,
        "legal_currentness": "not_verified", "public_requests": 0, "canonical_mutations": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
