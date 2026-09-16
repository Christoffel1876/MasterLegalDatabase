"""Freeze exact root draft and selected packet metadata; no source edits or dispatch."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
from audit_models import Asset, Copy, Custody

HERE = Path(__file__).absolute().parent
PROJECT = HERE.parents[2]
DRAFT = HERE.parent / "atlas-eb025-source-qa"
PACKET = HERE.parent / "ebenezer-preparation"
QA_PIN = "2372e6bde1fa544c56dbaed1a808a7389bf943006f8d2d4c65dd5fa10a8ad46f"
SID = "el-paso-boh-ehs-fees-spanish-sd011"


def main():
    if (HERE / "CUSTODY.json").exists():
        raise ValueError("Captured draft already frozen")
    if hashlib.sha256((DRAFT / "SOURCE_QA.json").read_bytes()).hexdigest() != QA_PIN:
        raise ValueError("Root draft changed")
    items = []
    def save(source, relative):
        raw = source.read_bytes(); target = HERE / relative
        if source.is_symlink() or target.exists():
            raise ValueError("Nonordinary source or existing destination")
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".tmp")
        temp.write_bytes(raw); os.replace(temp, target)
        a = Asset(path=relative, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
        items.append(Copy(original_path=source.relative_to(PROJECT).as_posix(),
                          retained=a, mode="exact"))
    for source in sorted(DRAFT.rglob("*")):
        if source.is_file():
            save(source, "received/" + source.relative_to(DRAFT).as_posix())
    save(DRAFT / "models.py", "review_models.py")
    packet_manifest = (PACKET / "MANIFEST.json").read_bytes()
    for name in ["MANIFEST.json", "MANIFEST.schema.json", "SOURCE_ONLY_IDENTITIES.json",
                 "02-candidate-text/" + SID + "/EXTRACTION.json",
                 "02-candidate-text/" + SID + "/EXTRACTION.schema.json",
                 "03-custody/" + SID + "/CUSTODY.json",
                 "03-custody/" + SID + "/CUSTODY.schema.json",
                 "03-custody/" + SID + "/canonical-record.jsonl",
                 "04-verification/render-events/" + SID + "/RENDER.json",
                 "04-verification/render-events/" + SID + "/RENDER.schema.json"]:
        save(PACKET / name, "packet-evidence/" + name)
    receipt = Custody(
        captured_at=datetime.now(timezone.utc), source_review_sha256=QA_PIN,
        original_root_review_folder=DRAFT.relative_to(PROJECT).as_posix(),
        packet_manifest_sha256=hashlib.sha256(packet_manifest).hexdigest(), items=items,
        packet_scope="Complete current root QA folder plus only selected EB025 packet metadata. "
                     "The shared packet manifest mentions EB026, whose PDF/images/candidate are not copied. "
                     "Historical draft files are retained unchanged and are not current acceptance.",
        root_visual_claims_independently_repeated=False, public_requests=0,
    )
    raw = receipt.model_dump_json(indent=2).encode() + b"\n"
    Custody.model_validate_json(raw)
    (HERE / "CUSTODY.json").write_bytes(raw)
    (HERE / "CUSTODY.schema.json").write_text(json.dumps(Custody.model_json_schema(), indent=2) + "\n")
    print("copied", len(items), "files; custody", hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
