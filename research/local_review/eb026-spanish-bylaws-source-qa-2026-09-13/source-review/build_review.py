"""One-time assembly from already inspected Spanish source evidence; never rerun a freeze."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from review_models import Crop, FileRef, NativeLine, Observation, Page, Review, Scope, Segment

ROOT = Path(__file__).absolute().parent
PACKET = ROOT.parent / "ebenezer-preparation"
SID = "el-paso-boh-bylaws-spanish-sd011"

# These boundaries were selected after complete direct-page and candidate comparison.
# The labels describe source location only; they are not semantic rule units.
LAYOUT = {
    1: [(1, 2, "cover", "Portada: título en dos líneas"),
        (3, 3, "cover", "Portada: condado"), (4, 4, "cover", "Portada: capítulo"),
        (5, 5, "cover", "Portada: Estatutos"), (6, 6, "cover", "Portada: Junta"),
        (7, 7, "footer", "Portada: nombre de la organización")],
    2: [(1, 1, "heading", "Título de capítulo"), (2, 2, "heading", "ESTATUTOS"),
        (3, 4, "extraction_whitespace", "Espacios de extracción sin palabras"),
        (5, 5, "heading", "JUNTA DE SALUD DEL CONDADO DE EL PASO"),
        (6, 6, "heading", "SECCIÓN 1.1: ORGANIZACIÓN"),
        (7, 13, "paragraph", "1.1 A. Junta de Salud"),
        (14, 16, "paragraph", "1.1 B. Lugar de Negocios"),
        (17, 17, "heading", "1.1 C. Autoridad de la Junta de Salud"),
        (18, 19, "paragraph", "1.1 C.1"), (20, 23, "paragraph", "1.1 C.2"),
        (24, 25, "paragraph", "1.1 C.3"), (26, 29, "paragraph", "1.1 D. Misión"),
        (30, 30, "heading", "SECCIÓN 1.2: FUNCIONARIOS"),
        (31, 36, "paragraph", "1.2 párrafo introductorio"),
        (37, 39, "paragraph", "1.2 A. Presidente — continúa en página3")],
    3: [(1, 2, "paragraph", "1.2 A. Presidente — continuación de página2"),
        (3, 5, "paragraph", "1.2 B. Vicepresidente"),
        (6, 12, "paragraph", "1.2 C. Secretario"),
        (13, 20, "paragraph", "1.2 D. Tesorero"),
        (21, 21, "heading", "SECCIÓN 1.3: REUNIONES"),
        (22, 32, "paragraph", "1.3 A. Reuniones ordinarias"),
        (33, 36, "paragraph", "1.3 B. Reuniones Extraordinarias"),
        (37, 39, "paragraph", "1.3 C. Quórum"),
        (40, 43, "paragraph", "1.3 D. Asistencia/Remoción — continúa en página4")],
    4: [(1, 9, "paragraph", "1.3 D. Asistencia/Remoción — continuación de página3"),
        (10, 21, "paragraph", "1.3 E. Agenda de la reunión"),
        (22, 27, "paragraph", "1.3 F. Sesiones Ejecutivas"),
        (28, 32, "paragraph", "1.3 G. Sin Autoridad Administrativa"),
        (33, 36, "paragraph", "1.3 H. Declaraciones de política"),
        (37, 41, "paragraph", "1.3 I. Responsabilidades de la Junta")],
    5: [(1, 1, "heading", "SECCIÓN 1.4: COMITÉS"),
        (2, 8, "paragraph", "1.4 párrafo completo"),
        (9, 9, "heading", "SECCIÓN 1.5: AUDITORÍA ANUAL Y PRESUPUESTO ANUAL"),
        (10, 19, "paragraph", "1.5 párrafo completo"),
        (20, 20, "heading", "SECCIÓN 1.6: PLAN DE SALUD DEL CONDADO"),
        (21, 29, "paragraph", "1.6 párrafo completo"),
        (30, 30, "heading", "SECCIÓN 1.7: ACTUALIZACIÓN ANUAL"),
        (31, 33, "paragraph", "1.7 párrafo completo"),
        (34, 34, "heading", "SECCIÓN 1.8: AUTORIDAD PARLAMENTARIA"),
        (35, 37, "paragraph", "1.8 párrafo completo"),
        (38, 38, "heading", "SECCIÓN 1.9: ENMIENDA DE ESTATUTOS"),
        (39, 43, "paragraph", "1.9 párrafo — continúa en página6")],
    6: [(1, 2, "paragraph", "1.9 continuación y oración repetida impresa"),
        (3, 3, "heading", "SECCIÓN 1.10: DIVISIBILIDAD"),
        (4, 7, "paragraph", "1.10 párrafo completo")],
}
LINKS = [("P02-S15", "P03-S01"), ("P03-S09", "P04-S01"), ("P05-S12", "P06-S01")]
CLIPS = [(2, (55, 180, 555, 455)), (2, (55, 545, 555, 705)),
         (3, (55, 140, 555, 370)), (3, (55, 355, 555, 705)),
         (4, (55, 70, 555, 370)), (4, (55, 375, 555, 670)),
         (5, (55, 200, 555, 510)), (5, (55, 510, 555, 715)),
         (6, (55, 70, 555, 185))]


def sha(data: bytes) -> str:
    """Hash unchanged bytes."""
    return hashlib.sha256(data).hexdigest()


def write_new(path: Path, data: bytes) -> None:
    """Atomically publish only a new file."""
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(data)
    os.replace(temporary, path)


def ref(path: Path) -> FileRef:
    """Bind a package-local file."""
    data = path.read_bytes()
    return FileRef(path=path.relative_to(ROOT).as_posix(), sha256=sha(data), size_bytes=len(data))


def export_json(path: Path, model: object) -> None:
    """Validate a typed record and schema before either is published."""
    raw = (model.model_dump_json(indent=2) + "\n").encode()
    type(model).model_validate_json(raw)
    write_new(path, raw)
    write_new(path.with_suffix(".schema.json"),
              (json.dumps(type(model).model_json_schema(), indent=2) + "\n").encode())


def main() -> None:
    """Preserve exact input copies and assemble the manually reviewed context map."""
    if (ROOT / "FINAL_MANIFEST.json").exists():
        raise RuntimeError("Frozen package; do not rerun")
    selected = ["MANIFEST.json", "MANIFEST.schema.json", "SOURCE_ONLY_IDENTITIES.json",
                "SOURCE_ONLY_IDENTITIES.schema.json", "START_HERE.md",
                "04-verification/fontconfig.xml"]
    for directory in [f"01-source-only/{SID}", f"02-candidate-text/{SID}",
                      f"03-custody/{SID}", f"04-verification/render-events/{SID}"]:
        selected.extend(p.relative_to(PACKET).as_posix()
                        for p in sorted((PACKET / directory).rglob("*")) if p.is_file())
    for relative in selected:
        data = (PACKET / relative).read_bytes()
        write_new(ROOT / "inputs" / relative, data)
    original = ROOT / "inputs/01-source-only" / SID / "original.pdf"
    source = ref(original)
    candidate = ROOT / "inputs/02-candidate-text" / SID / "candidate.txt"
    candidate_bytes = candidate.read_bytes()
    pages = []
    cursor = 0
    with pymupdf.open(stream=original.read_bytes(), filetype="pdf") as pdf:
        for n, page in enumerate(pdf, 1):
            native_path = ROOT / "inputs/02-candidate-text" / SID / f"page-{n:04}.native.txt"
            native = native_path.read_bytes()
            if native != page.get_text("text", flags=195, sort=False).encode():
                raise ValueError("Native replay differs")
            marker = f"===== PHYSICAL PDF PAGE {n} OF 6 (PACKAGING MARKER) =====\n".encode()
            closing = f"\n===== END PHYSICAL PDF PAGE {n} (PACKAGING MARKER) =====\n\n".encode()
            if candidate_bytes[cursor:cursor + len(marker)] != marker:
                raise ValueError("Candidate marker differs")
            start = cursor + len(marker)
            cursor = start + len(native)
            if candidate_bytes[start:cursor] != native:
                raise ValueError("Candidate native bytes differ")
            if candidate_bytes[cursor:cursor + len(closing)] != closing:
                raise ValueError("Candidate closing marker differs")
            cursor += len(closing)
            geometry = [line for block in page.get_text("dict", flags=195, sort=False)["blocks"]
                        if block["type"] == 0 for line in block["lines"]]
            lines, offset = [], 0
            for i, (raw, geom) in enumerate(zip(native.splitlines(keepends=True), geometry), 1):
                if raw.decode() != "".join(s["text"] for s in geom["spans"]) + "\n":
                    raise ValueError("Line geometry differs")
                lines.append(NativeLine(
                    id=f"P{n:02}-L{i:03}", physical_page=n, line_number=i,
                    byte_start=offset, byte_end=offset + len(raw),
                    candidate_byte_start=start + offset, candidate_byte_end=start + offset + len(raw),
                    text=raw.decode(), sha256=sha(raw), bbox_pdf_points=list(geom["bbox"])))
                offset += len(raw)
            if offset != len(native):
                raise ValueError("Incomplete native lines")
            segments = []
            for i, (first, last, kind, context) in enumerate(LAYOUT[n], 1):
                member_lines = lines[first - 1:last]
                raw = native[member_lines[0].byte_start:member_lines[-1].byte_end]
                identity = f"P{n:02}-S{i:02}"
                segments.append(Segment(
                    id=identity, physical_page=n, first_line=first, last_line=last,
                    kind=kind, context=context, byte_start=member_lines[0].byte_start,
                    byte_end=member_lines[-1].byte_end, text=raw.decode(), sha256=sha(raw),
                    line_ids=[line.id for line in member_lines],
                    continues_from=next((a for a, b in LINKS if b == identity), None),
                    continues_to=next((b for a, b in LINKS if a == identity), None),
                    visual_disposition=("native_whitespace_only" if kind == "extraction_whitespace"
                                        else "wording_matches_visible_source"),
                    qualification="Unchanged native wording; source grammar and punctuation retained. "
                    "Spacing/codepoint identity is a native-byte claim; visual typography is qualified."
                    if kind != "extraction_whitespace" else
                    "Two native whitespace lines precede the organization title in extraction order; "
                    "they contain no visible word and are not inferred blank form fields."))
            pages.append(Page(
                physical_page=n, image=ref(ROOT / "inputs/01-source-only" / SID /
                                           f"page-{n:04}.png"), native=ref(native_path),
                candidate_native_start=start, candidate_native_end=start + len(native),
                width_points=612.0, height_points=792.0, image_width=2550, image_height=3300,
                full_page_viewed=True, visible_date_footer=None, lines=lines, segments=segments,
                visual_notes="Complete page individually read, including margins. No visible date, "
                "signature, strikeout or handwritten entry observed. Cover organization footer "
                "is retained on page1; page6 has a large blank remainder. Footer pixel crops "
                "were separately checked; native spacing was not used to infer visible blanks."))
    if cursor != len(candidate_bytes):
        raise ValueError("Unaccounted candidate bytes")
    crops = [Crop(
        id=f"C{i:02}", physical_page=n, image=ref(ROOT / "crops" / f"p{n}-{r[1]}-{r[3]}.png"),
        method="pdf_clip_pymupdf", rectangle=list(r), coordinate_unit="pdf_points", viewed=True,
        observation="Dense wording, citation/conditional detail viewed directly; crop edges may "
        "cut neighboring lines. Whole-page and paragraph context remains authoritative.")
        for i, (n, r) in enumerate(CLIPS, 1)]
    crops.extend(Crop(
        id=f"F{n:02}", physical_page=n,
        image=ref(ROOT / "crops" / f"p{n}-footer-exact-pixels.png"),
        method="exact_poppler_pixel_crop", rectangle=[0, 2850, 2550, 3300],
        coordinate_unit="source_png_pixels", viewed=True,
        observation="Organization footer visible." if n == 1 else
        "No date/page-number/footer lettering observed; any partial body at crop top is "
        "caused by the crop boundary, not source clipping.") for n in range(1, 7))
    observations = make_observations()
    qa = Review(
        schema_version="geode.eb026.spanish-bylaws.source-qa.v1", source_id=SID,
        source_sha256=source.sha256, authority_id="CO-COUNTY-EL_PASO",
        layer_id="08_County_Authorities", source=source, candidate=ref(candidate),
        packet_manifest=ref(ROOT / "inputs/MANIFEST.json"),
        packet_manifest_sha256="ace3738bac6375b17f01ae0c4390350d5aeeacb1b9473838c57832dcd09427f5",
        canonical_record=ref(ROOT / "inputs/03-custody" / SID / "canonical-record.jsonl"),
        custody=ref(ROOT / "inputs/03-custody" / SID / "CUSTODY.json"),
        received_at="2026-09-12T22:59:48.795762Z", acquisition_method="received_review_package",
        independently_verified_http_at=None, issue_date=None, adoption_date=None,
        effective_date=None, date_limitation="No dated adoption/execution statement is visible. "
        "The September1 text is an annually recurring budget deadline. URL filename June2025 "
        "is inherited custody metadata, not a printed adoption/effectiveness date.",
        prepared_at=datetime.now(timezone.utc),
        status="initial_direct_source_qa_pending_root_acceptance", review_kind="checked_passages",
        legal_currentness="not_verified", answer_safe=False,
        fullscope=Scope(
            method="preparation_candidate_aware_direct_image_review",
            reviewer="Ptolemy (Codex subagent)", full_physical_pages=list(range(1, 7)),
            full_page_display_size="1376x1780 from 2550x3300 input",
            full_pages_viewed_before_text_comparison=True, prior_preparation_exposure=True,
            external_reports_consulted=False, english_versions_consulted=False,
            translation_equivalence_assessed=False, native_utf8_bytes=13558, native_lines=180,
            nonwhitespace_lines=178, inspected_crops=15,
            excluded_scope=["English-version equivalence", "external-report reconciliation",
                            "legal interpretation", "verified adoption or current law",
                            "canonical rule units or coverage promotion"]),
        pages=pages, crops=crops, observations=observations,
        limitations=[
            "All six complete pages were visually read; deterministic replay cannot certify that judgment.",
            "No source or candidate byte was corrected. No OCR or translation supplied missing text.",
            "Native line order/spacing preserves extraction behavior; the paragraph map links visual context.",
            "Underlying Unicode is preserved as encoded. Similar glyphs and underline appearance do not "
            "independently prove an exact codepoint or a strike/delete operation.",
            "Original HTTP acquisition is not independently verified. The retained official URL and "
            "repository receipt are separate custody claims; no new public source was opened.",
            "Inputs include only this source's selected packet members plus the historical full manifest; "
            "this portable review does not claim custody or QA for the other packet source.",
            "No visible full adoption date, effective date or signature authenticates this source as current.",
            "Nine PDF clips and six exact source-PNG footer crops were actually viewed; no crop expands "
            "the document or repairs a source-owned anomaly."])
    export_json(ROOT / "SOURCE_QA.json", qa)
    document = "---\nsource_id: " + SID + "\nlegal_currentness: not_verified\n---\n\n"
    document += "# Complete Spanish text with source context\n\n"
    document += "Exact native bytes remain in the input text files and typed SOURCE_QA. "
    document += "The fences below preserve native wording and line breaks; headings outside them "
    document += "are review navigation. No translation or legal effect is inferred.\n\n"
    for p in qa.pages:
        document += f"## Physical page {p.physical_page}\n\n"
        for s in p.segments:
            document += f"### {s.id} — {s.context}\n\n"
            document += f"Native bytes [{s.byte_start}, {s.byte_end}); lines {s.first_line}–{s.last_line}. "
            if s.continues_from or s.continues_to:
                document += f"Continuation: {s.continues_from} → {s.id} → {s.continues_to}. "
            document += "\n\n```text\n" + s.text + "```\n\n"
    write_new(ROOT / "FULL_TEXT_WITH_CONTEXT.md", document.encode())


def make_observations() -> list[Observation]:
    """Bind findings from the actual direct visual review without correcting the source."""
    rows = [
        ("source_anomaly", ["P01-S01"], ["REGLAMENTO DEL PASO", "JUNTA DE SALUD DEL CONDADO"], [],
         "Cover order and wording are visibly printed as two lines; do not rearrange into inferred grammar."),
        ("layout", ["P01-S03", "P01-S04", "P01-S05", "P02-S05"],
         ["Capítulo 1", "Estatutos", "Junta de Salud", "SECCIÓN 1.1"], [],
         "Underlines/bold headings are visible; plain native text does not encode their appearance. "
         "Do not classify heading underlines as deleted legal text."),
        ("conditional_wording", ["P02-S06", "P02-S12"],
         ["sin remuneración, excepto", "sujeto a disponibilidad de financiación"], ["C01"],
         "The remuneration exception and mission financing condition stay in their whole paragraphs."),
        ("source_anomaly", ["P02-S09", "P02-S11", "P02-S14", "P02-S15"],
         ["establecidos \nestablecido", "generales \nPolíticas", "las siguiente:",
          "tomará una decisión \ninterés"], ["C01", "C02"],
         "Visible grammar/capitalization oddities match native wording and are not silently repaired."),
        ("layout", ["P02-S15", "P03-S01"], ["para firmar", "a menos que tal poder"], ["C02"],
         "President signing language continues across pages2–3; the exception belongs to the same paragraph."),
        ("source_anomaly", ["P03-S03"], ["C.R.S. El \nEl Director"], ["C03"],
         "Both occurrences of El are visibly printed across the line boundary."),
        ("source_anomaly", ["P03-S04"], ["Sección 11-10.5-10 1", "Sección 25-1-5 11",
                                         "una “El Paso", "únicamente si están certificados"], ["C03"],
         "Numeric gaps, opening quote, CRS punctuation and withdrawal condition are source-owned. "
         "No closing quote or canonical section number is supplied from another source."),
        ("conditional_wording", ["P03-S06", "P03-S07", "P03-S08", "P03-S09"],
         ["Si el servicio es disponible", "tres \ndías", "24 horas", "si no existe quórum",
          "ochenta por ciento (80%)"], ["C04"],
         "Availability, emergency notice, quorum and attendance conditions retain their full context."),
        ("source_anomaly", ["P04-S01"], ["sobre su \nsu continua", "Sólo la junta",
                                         "se limita a hacer recomendaciones"], ["C05"],
         "Repeated su is printed. The removal/recommendation distinction remains literal source wording."),
        ("conditional_wording", ["P04-S02"], ["al menos 24 horas", "cinco (5) días",
                                             "Directorio. Junta \nLos miembros"], ["C05"],
         "Notice and agenda-distribution intervals are distinct. The odd Directorio. Junta wording "
         "and subsequent sentence are printed; no missing conjunction is inferred."),
        ("source_anomaly", ["P04-S03"], ["El presidente votará a los miembros",
                                          "dos tercios (2/3)", "Si, si no se da",
                                          "Sección 24-6-402, C.R.S."], ["C06"],
         "Voting wording and repeated Si are visible source text, alongside the consent/closed-session "
         "condition and cited limitation; no interpretive correction is made."),
        ("conditional_wording", ["P04-S04", "P04-S05"], ["Ningún miembro",
            "a menos que la Junta haya adoptado", "pero a ningún miembro", "como personales"], ["C06"],
         "Administrative and policy prohibitions retain the personal-opinion exception; no isolated "
         "prohibition is substituted for the complete paragraphs."),
        ("typography", ["P04-S06"], ["Parte 5 del Artículo I del Título 25, C.R.S.,"], ["C06"],
         "The source has a straight I-like glyph and native encodes capital Latin I; other numeric "
         "citation spellings are not used to rewrite it. Exact codepoint is a native-byte statement."),
        ("source_anomaly", ["P05-S02", "P05-S08", "P05-S10"], ["ad hoc. \ncomités",
            "decisiones recomendaciones", "escrito Actualización", "deberán regirán",
            "no sean inconsistente"], ["C08"],
         "Source grammar, punctuation and capitalization are retained, including the parliamentary "
         "applicability/inconsistency qualification."),
        ("date_role", ["P05-S04"], ["si las hubiere", "En o antes del 1 \nde septiembre de cada año"],
         ["C07"], "This is an annual budget deadline in the source, not a document adoption, issuance "
         "or effective date. No year is supplied."),
        ("conditional_wording", ["P05-S06"], ["Sección 25-1-504, C.R.S.", "La Junta no \nadoptará",
            "hasta que", "materialmente completo"], ["C07"],
         "The public draft/comment prerequisite remains with the complete health-plan paragraph; "
         "no claim that any actual plan was adopted is made."),
        ("layout", ["P05-S12", "P06-S01"], ["cinco (5)", "Excepto en caso de",
            "al menos un mes", "Los estatutos se presentarán"], ["C08", "C09"],
         "Amendment wording continues across pages5–6 and visibly repeats the one-month draft "
         "sentence on page6. Preserve both plus the urgency exception; do not deduplicate or "
         "decide how the repeated sentence affects that exception."),
        ("layout", ["P06-S03"], ["no hará inaplicables", "los presentes  \nestatutos."], ["C09"],
         "Severability negation and final separate estatutos. line are complete visible text. "
         "The large blank remainder contains no observed signature or date field."),
        ("layout", ["P01-S06"], ["El Paso County Public Health"],
         ["F01", "F02", "F03", "F04", "F05", "F06"],
         "Every bottom-border region was inspected as an exact pixel crop. Only page1 has the "
         "organization footer; no date/footer number was observed on pages2–6. Native and visible "
         "text agree within this reviewed snapshot.")]
    return [Observation(id=f"O{i:02}", kind=k, segment_ids=s, literal_anchors=a, crop_ids=c,
                        disposition="preserve_source", finding=f)
            for i, (k, s, a, c, f) in enumerate(rows, 1)]


if __name__ == "__main__":
    main()
