"""Build additive QA from immutable source-first observations and untouched packet inputs."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from review_models import Asset, Block, Crop, Finding, Observation, Page, SourceQA
from review_models import Span, TableFragment, TableRow

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / "ebenezer-023-024"
SOURCE_ID = "larimer-equity-fee-memo-sd007-05"


def ref(path: str) -> Asset:
    """Bind exact local bytes without assigning a new acquisition timestamp."""
    data = (HERE / path).read_bytes()
    return Asset(path=path, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def span(raw: bytes, start: int, end: int) -> Span:
    """Bind one exact original byte slice."""
    return Span(start=start, end=end, sha256=hashlib.sha256(raw[start:end]).hexdigest())


def normalized(text: str) -> str:
    """Compare wording while disclosing typography, bullet and line-wrap normalization."""
    text = unicodedata.normalize("NFKC", text).translate(str.maketrans("‘’“”", "''\"\""))
    text = text.replace("-\n", "-")
    return " ".join(re.sub(r"(?m)^\s*[•:]\s*", "", text).split())


def main() -> None:
    """Copy only selected immutable evidence and write a validated additive review once."""
    original = json.loads((HERE / "SOURCE_FIRST.json").read_bytes())
    packet_manifest = json.loads((PACKET / "MANIFEST.json").read_bytes())
    packet_refs = {v["path"]: v for v in packet_manifest["files"]}
    (HERE / "inputs").mkdir()
    selected: list[dict[str, str]] = []

    def copy(source: str, target: str) -> None:
        """Preserve an exact selected packet payload and verify its original manifest identity."""
        raw = (PACKET / source).read_bytes()
        expected = packet_refs.get(source)
        if expected is not None:
            assert hashlib.sha256(raw).hexdigest() == expected["sha256"]
            assert len(raw) == expected["size_bytes"]
        out = HERE / target
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("xb") as handle:
            handle.write(raw)
        selected.append({"original_packet_path": source, "review_path": target})

    copy("MANIFEST.json", "inputs/PACKET_MANIFEST.json")
    for name in ["MANIFEST.schema.json", "04-verification/PREPARATION.json",
                 "04-verification/PREPARATION.schema.json", "04-verification/OCR_RETRY_RECEIPT.json",
                 "04-verification/OCR_RETRY_RECEIPT.schema.json",
                 "03-custody/manual_source_intake_manifest.jsonl",
                 f"03-custody/{SOURCE_ID}/canonical-record.jsonl"]:
        copy(name, "inputs/" + Path(name).name)
    prefix = f"02-candidate-text/{SOURCE_ID}/"
    copy(prefix + "candidate.txt", "inputs/candidate.txt")
    for page in range(1, 5):
        stem = f"page-{page:04d}"
        copy(prefix + stem + ".native.txt", "inputs/" + stem + ".native.txt")
        for suffix in [".ocr.txt", ".ocr.json"]:
            copy(prefix + "local-framework-retry/" + stem + suffix, "inputs/" + stem + suffix)
    copy(prefix + "local-framework-retry/ocr-engine-result.schema.json",
         "inputs/ocr-engine-result.schema.json")
    notes = HERE.parents[3] / "MasterLegalDatabase/research/local_review/" / (
        "extended-pending-work-2026-09-13/ROOT_EB023_NOTES_UNFINISHED.md")
    shutil.copyfile(notes, HERE / "inputs/ROOT_EB023_NOTES_UNFINISHED.md")
    for asset in original["assets"]:
        name = asset["path"].removeprefix("source/")
        source_name = f"01-source-only/{SOURCE_ID}/" + name
        expected = packet_refs[source_name]
        assert ref(asset["path"]).sha256 == expected["sha256"]
        selected.append({"original_packet_path": source_name, "review_path": asset["path"]})

    mapping: dict[str, list[int]] = {}
    def bind(block: str, *indices: int) -> None:
        """Associate observed source blocks with original engine indexes, never rearranging OCR."""
        mapping[block] = list(indices)
    def group(block: str, start: int, end: int) -> None:
        """Bind inclusive original observation index range."""
        bind(block, *range(start, end + 1))
    group('P1-MASTHEAD',0,1);group('P1-TO',2,3);bind('P1-FROM',4);group('P1-DATE',5,6)
    group('P1-RE',7,8);bind('P1-H1',9);group('P1-P1',10,16);group('P1-P2',17,19)
    bind('P1-H2',20);group('P1-P3',21,25);group('P1-P4',26,31);group('P1-P5',32,33)
    group('P1-GRAPHIC',34,35)
    group('P2-GRAPHIC',0,1);group('P2-B1',2,3);group('P2-B2',4,5);group('P2-B3',6,7)
    group('P2-B4',8,10);bind('P2-H1',11);group('P2-P1',12,14);group('P2-B5',15,16)
    group('P2-B6',17,18);bind('P2-B7',19);group('P2-B8',20,21);bind('P2-B9',22)
    group('P2-P2',23,26);bind('P2-H2',27);group('P2-P3',28,31);bind('P2-P4',32)
    group('P2-B10',33,34);bind('P2-B11',35);bind('P2-PAGE',36)
    group('P3-GRAPHIC',0,1);group('P3-B1',2,3);bind('P3-B2',4);group('P3-B3',5,9)
    group('P3-B4',10,12);group('P3-P1',13,14);group('P3-B5',15,17);bind('P3-B6',18)
    bind('P3-B7',19);group('P3-B8',20,21);bind('P3-H1',22);group('P3-P2',23,25)
    bind('P3-T-H',26,27,43);group('P3-T1-LABEL',28,30);group('P3-T1-FEE',31,35)
    bind('P3-T1-C1',44);group('P3-T1-C2',45,46);bind('P3-T1-C3',47)
    group('P3-T1-C4',48,51);group('P3-T2-LABEL',36,38);group('P3-T2-FEE',39,42)
    bind('P3-T2-C1',52);group('P3-T2-C2',53,54);bind('P3-PAGE',55)
    group('P4-GRAPHIC',0,1);bind('P4-T2-LABEL');bind('P4-T2-FEE',3)
    bind('P4-T2-C3',2,4);group('P4-T2-C4',5,7);group('P4-T3-LABEL',11,13)
    bind('P4-T3-FEE',14,15,16,17,22);group('P4-T3-C1',8,9);bind('P4-T3-C2',10,18)
    bind('P4-T3-C3',18,19,20,21,23);group('P4-T3-C4',24,26);bind('P4-TR-LABEL',27,31)
    bind('P4-TR-FEE',28);group('P4-TR-C1',29,30);group('P4-TR-C2',32,33)
    group('P4-FN1',34,36);bind('P4-H1',37);group('P4-P1',38,40);bind('P4-H2',41)
    group('P4-P2',42,43);group('P4-P3',44,46);bind('P4-GRAPHIC2');bind('P4-H3',47)
    bind('P4-A1',48);group('P4-A2',49,50);bind('P4-PAGE',51)
    candidate = (HERE / "inputs/candidate.txt").read_bytes()
    preparation = json.loads((HERE / "inputs/PREPARATION.json").read_bytes())
    extraction = next(v for v in preparation["extraction"] if v["source_id"] == SOURCE_ID)
    pages: list[Page] = []
    engines: dict[int, dict] = {}
    for item in extraction["pages"]:
        number = item["physical_page"]
        text_path = f"inputs/page-{number:04d}.ocr.txt"
        json_path = f"inputs/page-{number:04d}.ocr.json"
        raw = (HERE / text_path).read_bytes()
        engine = json.loads((HERE / json_path).read_bytes());engines[number] = engine
        assert raw == ("\n".join(v["text"] for v in engine["lines"]) + "\n").encode()
        start, end = item["candidate_start"], item["candidate_end"]
        assert candidate[start:end] == raw
        observations = [];offset = 0
        for index, line in enumerate(engine["lines"]):
            length = len((line["text"] + "\n").encode())
            targets = [block["id"] for block in original["blocks"] if block["page"] == number
                       and index in mapping[block["id"]]]
            assert targets
            observations.append(Observation(id=f"P{number}-O{index:03d}", index=index,
                text=line["text"], bbox=line["bbox"], confidence=float(line["confidence"]),
                page_span=span(raw, offset, offset + length),
                candidate_span=span(candidate, start + offset, start + offset + length),
                reviewed_block_ids=targets))
            offset += length
        assert offset == len(raw)
        pages.append(Page(physical_page=number, image=ref(f"source/page-{number:04d}.png"),
            width=2550, height=3300, native_attempt=ref(f"inputs/page-{number:04d}.native.txt"),
            ocr_json=ref(json_path), ocr_text=ref(text_path),
            candidate_span=span(candidate, start, end), observations=observations))
    blocks: list[Block] = []
    for item in original["blocks"]:
        indices = mapping[item["id"]]
        raw_text = "\n".join(engines[item["page"]]["lines"][i]["text"] for i in indices)
        comparison = "normalized_wording_agrees"
        if item["kind"] == "graphic_note" or not indices:
            comparison = "visual_only_graphic_or_blank"
        elif normalized(item["text"].replace(" | ", " ")) != normalized(raw_text):
            comparison = "ocr_correction_required"
        note = ("Checked against the complete source image. Comparison normalizes Unicode "
                "compatibility forms, quote style, whitespace, leading OCR bullets/colon artifacts "
                "and line-end hyphen continuation; raw OCR remains exact.")
        if item["id"] in ["P4-T3-C2", "P4-T3-C3"]:
            note += (" Original observation18 is shared because OCR conflates parts of these "
                     "two different visible source bullets; it is not accepted as correct text.")
        blocks.append(Block(**item, observation_ids=[f'P{item["page"]}-O{i:03d}' for i in indices],
                            comparison=comparison, comparison_note=note))
    by_id = {b.id: b for b in blocks}
    fragment_specs = [
        ("T1-P3","TIER1",3,[225,2317,2290,2753],"P3-T1-LABEL","P3-T1-FEE",
         [f"P3-T1-C{i}" for i in range(1,5)],None),
        ("T2-P3","TIER2",3,[225,2753,2290,2978],"P3-T2-LABEL","P3-T2-FEE",
         ["P3-T2-C1","P3-T2-C2"],None),
        ("T2-P4","TIER2",4,[225,478,2290,788],"P4-T2-LABEL","P4-T2-FEE",
         ["P4-T2-C3","P4-T2-C4"],"T2-P3"),
        ("T3-P4","TIER3",4,[225,788,2290,1405],"P4-T3-LABEL","P4-T3-FEE",
         [f"P4-T3-C{i}" for i in range(1,5)],None),
        ("ROAD-P4","ROAD",4,[225,1405,2290,1533],"P4-TR-LABEL","P4-TR-FEE",
         ["P4-TR-C1","P4-TR-C2"],None),
    ]
    fragments = [TableFragment(id=i,logical_row=r,page=p,approximate_pixel_box=box,
        label_block=label,fee_block=fee,characteristic_blocks=chars,continuation_from=prior)
        for i,r,p,box,label,fee,chars,prior in fragment_specs]
    rows = []
    for name in ["TIER1","TIER2","TIER3","ROAD"]:
        members = [f for f in fragments if f.logical_row == name]
        rows.append(TableRow(id=name,fragments=[f.id for f in members],
            event_type=" ".join(by_id[f.label_block].text for f in members).strip(),
            fee_text="\n".join(by_id[f.fee_block].text for f in members),
            characteristics=[by_id[b].text for f in members for b in f.characteristic_blocks],
            header_block="P3-T-H",proposal_context="P3-P2",conditional_implementation="P4-P2",
            dnr_footnote=None if name=="ROAD" else "P4-FN1",
            qualification=("Full-road-closure charge is in addition to permit fee; block-party "
                "closures are excluded. No total is calculated." if name=="ROAD" else
                "At least one characteristic is stated in the source header. DNR applicability "
                "and negotiated additional staffing fees remain attached. No tier selection, "
                "fee total or current applicability is inferred.")))
    findings = [Finding(id=b.id,block_ids=[b.id],observation_ids=b.observation_ids,
        finding="OCR differs from the directly checked source wording; use the separate reviewed "
                "text, retaining unchanged raw OCR and its precise byte spans.") for b in blocks
                if b.comparison=="ocr_correction_required"]
    findings += [
        Finding(id="LAYOUT-1",block_ids=["P3-T-H","P3-T2-LABEL","P4-T2-LABEL","P4-T2-FEE"],
            observation_ids=[],finding="Four logical rows occupy five physical fragments; Tier2 "
            "continues onto page4. A blank continuation label is not a new row or missing fee."),
        Finding(id="SCOPE-1",block_ids=["P1-P2","P3-P2","P4-P2","P4-A1","P4-A2"],
            observation_ids=[],finding="Staff recommendation and 'If adopted' remain explicit. "
            "Referenced Attachments A and B are not contained in this four-page PDF."),
        Finding(id="ANOMALIES-1",block_ids=["P1-P2","P3-P1","P4-P3","P4-A1","P4-A2"],
            observation_ids=[],finding="Preserve Staff recommend/recommends, the stated study "
            "years, 'January, 2 2024', and 'Planning and Engineering and Development'. No source "
            "grammar, punctuation or arithmetic is silently repaired."),
        Finding(id="GRAPHIC-1",block_ids=["P4-GRAPHIC2","P4-P3"],observation_ids=[],
            finding="Colored scan marks are visible through the follow-up line; their intent "
            "is unknown. They are not certified as deletion, emphasis or operative change."),
    ]
    crops = [Crop(image_page=n,pixel_box=box,asset=ref("crops/"+name+".png"))
        for n,name,box in [(3,"page3-table",[210,2230,2320,3000]),
                          (4,"page4-table-and-note",[210,470,2330,1700]),
                          (4,"page4-next-steps-attachments",[210,2150,2490,2880])]]
    custody = next(v for v in preparation["inputs"] if v["source_id"]==SOURCE_ID)
    qa = SourceQA(source_id=SOURCE_ID,authority_id="CO-COUNTY-LARIMER",
        status="complete_source_fidelity_review_pending_root_acceptance",
        reviewed_at=datetime.now(timezone.utc).isoformat(),
        review_method="Four complete source PNGs inspected before current-phase OCR and root "
        "notes, then three direct source crops and all181 unchanged OCR observations compared. "
        "Not blind: reviewer prepared this packet earlier and knew parent concerns. No external "
        "Ebenezer report consulted. Exact glyph codepoints are not certified.",
        source=ref("source/original.pdf"),source_first=ref("SOURCE_FIRST.json"),
        candidate=ref("inputs/candidate.txt"),packet_manifest=ref("inputs/PACKET_MANIFEST.json"),
        selected_packet_payloads=selected,
        provenance={k:custody[k] for k in ["official_url_claim","acquisition_method",
                    "repository_received_at","original_acquisition_at","custody_note"]},
        pages=pages,blocks=blocks,table_fragments=fragments,table_rows=rows,findings=findings,
        crops=crops,consulted_root_notes=ref("inputs/ROOT_EB023_NOTES_UNFINISHED.md"),
        root_notes_consulted_after_source_freeze=True,external_ebenezer_reports_consulted=False,
        complete_physical_pages=4,complete_source_blocks=82,original_ocr_observations=181,
        candidate_size_bytes=9796,original_ocr_body_bytes=9344,
        source_type="staff_recommendation_memo",adopted_effect="not_verified",
        legal_currentness="not_verified",limitations=[
            "Full visible wording and associations reviewed, not an adopted resolution or legal opinion.",
            "Packet copy is a selected EB023 subset; the complete packet manifest also names EB024 "
            "and other artifacts deliberately not duplicated here.",
            "OCR confidence, including1.0, does not establish source fidelity; raw errors remain preserved.",
            "Whitespace and typography normalization is declared; exact font glyph encodings are unknown.",
            "Table pixel boxes are approximate visual locators; full page images and exact crops are bound.",
            "Original HTTP acquisition time is unknown; URL/time claims are not independently reverified.",
            "Root unfinished notes were consulted only after source-first freeze and candidate comparison; "
            "their earlier incomplete-review status is historical, not overwritten.",
        ])
    data=qa.model_dump_json(indent=2)+"\n";SourceQA.model_validate_json(data)
    with (HERE/"SOURCE_QA.json").open("x") as handle:handle.write(data)
    with (HERE/"SOURCE_QA.schema.json").open("x") as handle:
        handle.write(json.dumps(SourceQA.model_json_schema(),indent=2)+"\n")
    print("Reviewed blocks",len(blocks),"OCR corrections",[f.id for f in findings
          if f.id.startswith("P")])


if __name__=="__main__":
    main()
