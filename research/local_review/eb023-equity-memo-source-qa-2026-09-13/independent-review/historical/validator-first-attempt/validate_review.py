"""Read-only replay of complete source/OCR custody and reviewed table associations."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import jsonschema
import pymupdf

from review_models import Asset, Manifest, SourceQA

HERE = Path(__file__).resolve().parent
PDF_SHA = "9b8ba4e32fee82e5d632b53a7da19ad626438ef130b750e73e09b591fc9e7b14"
CANDIDATE_SHA = "492c339ed0aac2eafa36228d3810df91eb70ddd555cf7c553b929bbfca544968"
PACKET_SHA = "dbb8f0a6e6b280e5ac9b8f92877c2efb395799664ae80351c889fc62233c2e89"


def digest(raw: bytes) -> str:
    """Hash the actual bytes used by this verifier."""
    return hashlib.sha256(raw).hexdigest()


def load(asset: Asset) -> bytes:
    """Verify a bounded ordinary local payload before consuming its bytes."""
    relative = Path(asset.path)
    path = HERE / relative
    if relative.is_absolute() or ".." in relative.parts or any(
            p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Unsafe review path")
    with path.open("rb") as handle:
        raw = handle.read(20_000_001)
    if len(raw) > 20_000_000 or len(raw) != asset.size_bytes or digest(raw) != asset.sha256:
        raise ValueError("Review payload identity differs: " + asset.path)
    return raw


def check(condition: bool, message: str) -> None:
    """Raise an explicit integrity error even when Python assertions are disabled."""
    if not condition:
        raise ValueError(message)


def verify_content(value: dict) -> dict[str, object]:
    """Validate unchanged evidence and semantic associations without rerunning OCR."""
    qa = SourceQA.model_validate(value)
    source, candidate, first = load(qa.source), load(qa.candidate), json.loads(load(qa.source_first))
    check(digest(source) == PDF_SHA and digest(candidate) == CANDIDATE_SHA, "Fixed source differs")
    check(digest(load(qa.packet_manifest)) == PACKET_SHA, "Original packet manifest differs")
    jsonschema.validate(first, json.loads((HERE / "SOURCE_FIRST.schema.json").read_bytes()))
    check(len(qa.blocks) == 82 and len({b.id for b in qa.blocks}) == 82, "Source block count differs")
    check(len(qa.pages) == 4 and [p.physical_page for p in qa.pages] == [1,2,3,4], "Pages differ")
    block_map = {b.id:b for b in qa.blocks}
    check([b.id for b in qa.blocks] == [b["id"] for b in first["blocks"]], "Block order differs")
    for block, original in zip(qa.blocks, first["blocks"]):
        check(all(getattr(block,k) == original[k] for k in
                  ["id","page","kind","text","association"]), "Source-first wording differs")
    packet = json.loads(load(qa.packet_manifest))
    original_refs = {a["path"]:a for a in packet["files"]}
    names = set()
    for mapping in qa.selected_packet_payloads:
        old, new = mapping["original_packet_path"], mapping["review_path"]
        check(new not in names, "Duplicate custody target")
        names.add(new)
        if old == "MANIFEST.json":
            continue
        ref = original_refs[old]
        load(Asset(path=new,sha256=ref["sha256"],size_bytes=ref["size_bytes"]))
    observations = {}
    reproduced = bytearray()
    total = 0
    for page in qa.pages:
        image = load(page.image)
        pix = pymupdf.Pixmap(image)
        check((pix.width,pix.height) == (2550,3300), "Full image dimensions differ")
        check(load(page.native_attempt) == b"", "Historical native attempt differs")
        engine = json.loads(load(page.ocr_json))
        jsonschema.validate(engine, json.loads((HERE / "inputs/ocr-engine-result.schema.json")
                                               .read_bytes()))
        raw = load(page.ocr_text)
        check(raw == ("\n".join(v["text"] for v in engine["lines"])+"\n").encode(),
              "Unchanged engine serialization differs")
        start,end = page.candidate_span.start,page.candidate_span.end
        check(candidate[start:end] == raw and digest(raw) == page.candidate_span.sha256,
              "Candidate body differs")
        reproduced.extend((f"===== PHYSICAL PDF PAGE {page.physical_page} OF 4 "
                           "(PACKAGING MARKER) =====\n").encode())
        reproduced.extend(raw)
        reproduced.extend((f"\n===== END PHYSICAL PDF PAGE {page.physical_page} "
                           "(PACKAGING MARKER) =====\n\n").encode())
        cursor = 0
        check(len(page.observations) == len(engine["lines"]), "OCR observation count differs")
        for index,(observation,original) in enumerate(zip(page.observations,engine["lines"])):
            check(observation.index == index and observation.id ==
                  f"P{page.physical_page}-O{index:03d}", "OCR index differs")
            check(observation.text == original["text"] and observation.bbox == original["bbox"]
                  and observation.confidence == original["confidence"], "OCR observation differs")
            chunk = (original["text"]+"\n").encode()
            check(observation.page_span.start == cursor and observation.page_span.end ==
                  cursor+len(chunk) and observation.page_span.sha256 == digest(chunk),
                  "Original page span differs")
            check(observation.candidate_span.start == start+cursor and
                  observation.candidate_span.end == start+cursor+len(chunk) and
                  observation.candidate_span.sha256 == digest(chunk), "Candidate span differs")
            check(bool(observation.reviewed_block_ids) and all(
                  block_map[b].page == page.physical_page and observation.id in
                  block_map[b].observation_ids for b in observation.reviewed_block_ids),
                  "Observation/source association differs")
            observations[observation.id] = observation
            cursor += len(chunk)
        check(cursor == len(raw), "Original byte coverage differs")
        total += cursor
    check(bytes(reproduced) == candidate and len(candidate) == 9796 and total == 9344,
          "Complete candidate including markers differs")
    check(len(observations) == 181, "Complete observation coverage differs")
    for block in qa.blocks:
        check(len(block.observation_ids) == len(set(block.observation_ids)),
              "Duplicate block observation")
        for name in block.observation_ids:
            check(block.id in observations[name].reviewed_block_ids, "Reverse association differs")
    shared = {k:v.reviewed_block_ids for k,v in observations.items()
              if len(v.reviewed_block_ids)>1}
    check(shared == {"P4-O018":["P4-T3-C2","P4-T3-C3"]}, "Shared OCR conflation differs")
    expected_fragments = [
        ("T1-P3","TIER1",3,"P3-T1-LABEL","P3-T1-FEE",None),
        ("T2-P3","TIER2",3,"P3-T2-LABEL","P3-T2-FEE",None),
        ("T2-P4","TIER2",4,"P4-T2-LABEL","P4-T2-FEE","T2-P3"),
        ("T3-P4","TIER3",4,"P4-T3-LABEL","P4-T3-FEE",None),
        ("ROAD-P4","ROAD",4,"P4-TR-LABEL","P4-TR-FEE",None),
    ]
    check([(f.id,f.logical_row,f.page,f.label_block,f.fee_block,f.continuation_from)
           for f in qa.table_fragments] == expected_fragments, "Physical table association differs")
    check(block_map["P4-T2-LABEL"].text == "", "Blank continuation changed")
    check([r.id for r in qa.table_rows] == ["TIER1","TIER2","TIER3","ROAD"], "Logical rows differ")
    for row in qa.table_rows:
        fragments = [f for f in qa.table_fragments if f.logical_row == row.id]
        check(row.fragments == [f.id for f in fragments], "Row fragments differ")
        check(row.event_type == " ".join(block_map[f.label_block].text for f in fragments).strip(),
              "Event label differs")
        check(row.fee_text == "\n".join(block_map[f.fee_block].text for f in fragments),
              "Fee-column association differs")
        chars = [b for f in fragments for b in f.characteristic_blocks]
        check(len(chars) == (2 if row.id=="ROAD" else 4) and all(
              block_map[b].association == f"{row.id}/characteristics/{i+1}"
              for i,b in enumerate(chars)), "Characteristic order differs")
        check(row.characteristics == [block_map[b].text for b in chars], "Characteristics differ")
        check(row.dnr_footnote == (None if row.id=="ROAD" else "P4-FN1"), "DNR qualification differs")
    check(len([b for b in qa.blocks if b.kind=="bullet"]) == 19, "Prose bullet count differs")
    check(len([b for b in qa.blocks if b.kind=="attachment"]) == 2, "Attachments differ")
    for crop in qa.crops:
        pix = pymupdf.Pixmap(load(qa.pages[crop.image_page-1].image))
        x0,y0,x1,y1 = crop.pixel_box
        raw = pix.samples
        sliced = b"".join(raw[(y*pix.width+x0)*pix.n:(y*pix.width+x1)*pix.n]
                          for y in range(y0,y1))
        png = pymupdf.Pixmap(pix.colorspace,x1-x0,y1-y0,sliced,pix.alpha).tobytes("png")
        check(png == load(crop.asset), "Source pixel crop differs")
    load(qa.consulted_root_notes)
    with pymupdf.open(stream=source,filetype="pdf") as pdf:
        check(len(pdf) == 4 and not pdf.is_repaired, "Source PDF structure differs")
        check(all(p.get_text("text",sort=False,flags=195)=="" for p in pdf),
              "Source native-text condition differs")
    return {"status":"passed_complete_bounded_source_review", "physical_pages":4,
            "source_blocks":82,"logical_table_rows":4,"physical_table_fragments":5,
            "prose_bullets":19,"attachment_bullets":2,"table_characteristics":14,
            "ocr_observations":181,"ocr_body_bytes":9344,"candidate_bytes":9796,
            "legal_currentness":"not_verified","adopted_effect":"not_verified"}


def main() -> None:
    """Verify frozen custody when present and optionally reproduce complete Poppler images."""
    parser=argparse.ArgumentParser()
    parser.add_argument("--rerender",action="store_true")
    parser.add_argument("--pdftoppm")
    args=parser.parse_args()
    manifest_path=HERE/"FINAL_MANIFEST.json"
    if manifest_path.exists():
        manifest=Manifest.model_validate_json(manifest_path.read_bytes())
        names={v.path for v in manifest.files}
        actual={p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
        check(len(names)==len(manifest.files) and actual==names|{
            "FINAL_MANIFEST.json","FINAL_MANIFEST.schema.json"},"Closed review membership differs")
        for asset in manifest.files:load(asset)
    qa=json.loads((HERE/"SOURCE_QA.json").read_bytes())
    jsonschema.validate(qa,json.loads((HERE/"SOURCE_QA.schema.json").read_bytes()))
    result=verify_content(qa)
    if args.rerender:
        tool=args.pdftoppm or shutil.which("pdftoppm")
        if not tool:raise ValueError("Poppler pdftoppm path is required for rerender")
        with tempfile.TemporaryDirectory(prefix="eb023-review-rerender-") as tmp:
            subprocess.run([tool,"-r","300","-png",str(HERE/"source/original.pdf"),
                            str(Path(tmp)/"page")],check=True,capture_output=True,timeout=60)
            for n in range(1,5):
                check((Path(tmp)/f"page-{n}.png").read_bytes()==(
                    HERE/f"source/page-{n:04d}.png").read_bytes(),"Rerender differs")
        result["rerendered"]=True
    else:result["rerendered"]=False
    sys.stdout.write(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    main()
