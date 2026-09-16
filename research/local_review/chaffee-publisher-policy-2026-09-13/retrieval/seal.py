"""Create a public closed inventory once; no network or source transformations."""

import json
from pathlib import Path

from models import Attempt, Manifest, Reservation
from prepare import now, put, ref

ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Seal original bodies, public logs, evidence and read-only verification tools."""
    results = [Attempt.model_validate_json(p.read_bytes())
               for p in sorted((ROOT / "events").glob("*/RESULT.json"))]
    for name, model in [("RESULT", Attempt), ("RESERVATION", Reservation),
                        ("FINAL_MANIFEST", Manifest)]:
        put(ROOT / f"{name}.schema.json",
            (json.dumps(model.model_json_schema(), indent=2) + "\n").encode())
    manifest = Manifest(
        schema_version="chaffee-directed-public-custody-v1", sealed_at=now(),
        files=[ref(p) for p in sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix())
               if p.is_file()], action_count=len(results),
        distinct_requested_urls=len({r.requested_url for r in results}),
        retained_response_body_bytes=sum(r.body.size_bytes for r in results),
        pdf_count=sum(r.pdf_parse_ok for r in results),
        pdf_pages=sum(r.pdf_pages or 0 for r in results), unopened_target_ids=[],
        limitations=["Two complete PDFs were structurally parsed only; zero pages visually reviewed.",
                     "The third original response is a 302 HTML notice, not the application fee PDF.",
                     "The new fee Location remains unopened; all three authorized actions are spent.",
                     "Exact raw curl stdout/writeout and stderr are retained. Original response "
                     "headers are digest-bound but only public exact-line subsets are retained; "
                     "omitted originals cannot be reconstructed or fully replayed offline.",
                     "Original historical proof bodies are unchanged received evidence. New "
                     "direct retrieval does not change prior acquisition claims.",
                     "Request intervals are actual local UTC/monotonic process measurements. "
                     "Publisher Date and Last-Modified values do not establish legal dates.",
                     "No canonical intake, transcription QA, adoption/effectiveness or currentness.",
                     "Verification is offline evidence replay, not a fresh network check. "
                     "Historical retrieve.py must not be rerun as a validator."])
    put(ROOT / "FINAL_MANIFEST.json", (manifest.model_dump_json(indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
