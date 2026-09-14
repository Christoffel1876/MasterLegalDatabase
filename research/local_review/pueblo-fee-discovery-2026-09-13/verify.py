"""Read-only offline validation of the finite Pueblo discovery packet."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import pymupdf
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).absolute().parent))
from capture import Event, PUBLIC
from models import Manifest, Report


def read(root: Path, name: str) -> bytes:
    """Read confined ordinary bytes, rejecting symlink ancestors and traversal."""
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Unsafe path")
    p = root / relative
    if any(q.is_symlink() for q in (p, *p.parents)) or not p.is_file():
        raise ValueError("Nonordinary path")
    return p.read_bytes()


def verify(root: Path) -> dict:
    """Replay hashes, exact official link/hop, native pages and recorded finite scope."""
    manifest = Manifest.model_validate_json(read(root, "FINAL_MANIFEST.json"))
    report = Report.model_validate_json(read(root, "REPORT.json"))
    for name, model in [("FINAL_MANIFEST.schema.json", Manifest), ("REPORT.schema.json", Report),
                        ("EVENT.schema.json", Event)]:
        if json.loads(read(root, name)) != model.model_json_schema():
            raise ValueError("Schema mismatch")
    expected = {r.path for r in manifest.files} | {"FINAL_MANIFEST.json"}
    expected_dirs = {str(p) for n in expected for p in Path(n).parents if str(p) != "."}
    files, dirs = set(), set()
    for p in root.rglob("*"):
        if p.is_symlink() or not (p.is_dir() or p.is_file()):
            raise ValueError("Nonordinary package member")
        (dirs if p.is_dir() else files).add(p.relative_to(root).as_posix())
    if files != expected or dirs != expected_dirs:
        raise ValueError("Closed file inventory differs")
    for ref in manifest.files:
        body = read(root, ref.path)
        if len(body) != ref.size_bytes or hashlib.sha256(body).hexdigest() != ref.sha256:
            raise ValueError("Hash/size mismatch: " + ref.path)
    events = [Event.model_validate_json(p.read_bytes())
              for p in sorted(root.glob("events/*/event.json"))]
    if len(events) != report.events or len({e.requested_url for e in events}) != report.distinct_urls:
        raise ValueError("Event accounting differs")
    if sum(e.body.size_bytes for e in events) != report.retained_body_bytes:
        raise ValueError("Retained byte accounting differs")
    if len([e for e in events if e.http_status is not None]) != report.http_responses:
        raise ValueError("HTTP/tool-failure distinction differs")
    for e in events:
        body = read(root, e.body.path)
        if len(body) != e.body.size_bytes or hashlib.sha256(body).hexdigest() != e.body.sha256:
            raise ValueError("Event body binding differs")
        if set(e.public_headers) - PUBLIC or e.completed_at > report.limits.hard_stop:
            raise ValueError("Header privacy or deadline violation")
        if e.body.size_bytes > report.limits.maximum_source_bytes:
            raise ValueError("Per-source body cap exceeded")
        if (e.completed_at - e.started_at).total_seconds() > 30:
            raise ValueError("Request deadline exceeded")
    if [e.http_status for e in events] != [None, 200, 403, 301, 200]:
        raise ValueError("Recorded response sequence differs")
    if events[0].body.size_bytes != 0 or events[0].tls_verified is not None:
        raise ValueError("Initial local failure misrepresented")
    if events[0].requested_url != events[2].requested_url:
        raise ValueError("Sandbox correction used a different route")
    if any(e.authority_id == "CO-COUNTY-PUEBLO" for e in events[3:]):
        raise ValueError("Request continued after county denial")
    source = report.sources[0]
    if source.official_parent.model_dump() != events[1].body.model_dump() or (
        source.parent_url != events[1].requested_url or source.event_ids != ["E002", "E004", "E005"]
    ):
        raise ValueError("Parent event identity differs")
    soup = BeautifulSoup(read(root, source.official_parent.path), "html.parser")
    anchors = [a for a in soup.select("a[href]") if a["href"] == source.anchor_href
               and " ".join(a.stripped_strings) == source.anchor_label]
    if len(anchors) != 1 or urljoin(source.parent_url, source.anchor_href) != source.requested_url:
        raise ValueError("Official referral does not bind exact selected URL")
    if events[3].requested_url != source.requested_url or (
        events[3].redirect_to != source.final_url or events[4].requested_url != source.final_url
    ):
        raise ValueError("Redirect chain differs")
    original = read(root, source.original.path)
    if original != read(root, events[4].body.path):
        raise ValueError("PDF is not the exact final response body")
    if (hashlib.sha256(original).hexdigest() != source.original.sha256
            or len(original) != source.original.size_bytes):
        raise ValueError("Source digest differs")
    if not original.startswith(b"%PDF-") or not original.rstrip().endswith(b"%%EOF"):
        raise ValueError("Invalid PDF envelope")
    structure = json.loads(read(root, "sources/city-pueblo-planning-fees/STRUCTURE.json"))
    doc = pymupdf.open(stream=original, filetype="pdf")
    if doc.is_repaired or doc.is_encrypted or len(doc) != 4:
        raise ValueError("PDF structure differs")
    full = b""
    for page, record in zip(doc, structure["pages"], strict=True):
        native = page.get_text("text", flags=195, sort=False).encode()
        if native != read(root, record["native_path"]) or record["start"] != len(full):
            raise ValueError("Native page or order differs")
        full += native
        if record["end"] != len(full):
            raise ValueError("Native byte boundary differs")
    if len(full) != 4923 or full != read(root, "sources/city-pueblo-planning-fees/native/all-pages.txt"):
        raise ValueError("Native concatenation differs")
    # Re-render the fast fallback in memory. Poppler images are hash-bound, not rerun here.
    for page in (1, 4):
        expected_png = read(root, f"sources/city-pueblo-planning-fees/images/pymupdf-page-{page:04d}.png")
        if doc[page - 1].get_pixmap(dpi=160).tobytes("png") != expected_png:
            raise ValueError("Fallback render differs")
    return {"status": "verified_bounded_discovery", "files": len(manifest.files),
            "events": len(events), "distinct_urls": report.distinct_urls,
            "retained_body_bytes": report.retained_body_bytes, "pdfs": 1,
            "structural_pages": 4, "native_bytes": 4923, "directly_viewed_pages": [1, 4],
            "county_gap": "publisher_HTTP403", "legal_currentness": "not_verified"}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(Path(__file__).absolute().parent), indent=2) + "\n")
