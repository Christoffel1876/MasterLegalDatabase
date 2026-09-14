"""Reproduce structural associations selected during Plato's direct image review."""
import hashlib
import json
import re
from pathlib import Path
import pymupdf
from review_models import Asset, Crop, Line, Paragraph, QA, Row

ROOT = Path(__file__).resolve().parent
PACKET = ROOT / 'inputs'
SOURCE = '01-source-only/A01/original.pdf'
CANDIDATE = '02-candidate-text/A01/candidate.txt'


def digest(data: bytes) -> str:
    """Return SHA256 for exact bytes."""
    return hashlib.sha256(data).hexdigest()


def asset(path: Path, base: Path) -> Asset:
    """Measure an existing exact file."""
    data = path.read_bytes()
    return Asset(path=path.relative_to(base).as_posix(), sha256=digest(data), size_bytes=len(data))


def ref(page: int, number: int) -> str:
    """Return the stable zero-based native-line identity."""
    return f'P{page}-L{number:03}'


def refs(page: int, numbers: list[int]) -> list[str]:
    """Bind a selected list of native lines."""
    return [ref(page, n) for n in numbers]


def crop_bytes(path: Path, box: list[int]) -> bytes:
    """Slice RGB samples without rescaling or altering source pixels."""
    image = pymupdf.Pixmap(path)
    x0, y0, x1, y1 = box
    assert image.n == 3 and 0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height
    raw = image.samples
    rows = [raw[y * image.stride + x0 * 3:y * image.stride + x1 * 3] for y in range(y0, y1)]
    return pymupdf.Pixmap(pymupdf.csRGB, x1-x0, y1-y0, b''.join(rows), False).tobytes('png')


def group_numbers(page: int, index: int) -> list[int]:
    """Preserve inspected category hierarchy, including carried nested headings."""
    if page == 2:
        return ([0, 2] if index == 4 else
                ([0, 5] if index == 7 else [0, 81, 8] + ([53] if index == 56 else [])))
    if page == 3:
        if index < 54:
            result = [0, 2]
            if 16 <= index <= 33:
                result += [12, 13, 14]
                if 19 <= index <= 23: result += [17]
                if index == 27: result += [24]
                if index == 31: result += [28]
            if 39 <= index <= 48:
                result += [37]
                if index >= 44: result += [42]
            return result
        return [0, max(n for n in [54, 59, 65, 68, 73, 76] if n < index)]
    if page == 4:
        return [0, 2] + ([75] if 77 <= index <= 81 else [])
    if page == 5:
        result = [0, 1, 2, 3]
        if 58 <= index <= 62: result += [55, 56]
        if 66 <= index <= 73: result += [63, 64]
        if 91 <= index <= 92: result += [86, 87]
        if 124 <= index <= 147:
            result += [120, 121, 122]
            if 128 <= index <= 132: result += [126]
            if 137 <= index <= 138: result += [133]
            if 143 <= index <= 144: result += [139]
        if 190 <= index <= 191: result += [184, 185, 186]
        return result
    if page == 6:
        if index <= 14: return [0]
        if index <= 19: return [0, 15]
        if index <= 24: return [0, 20]
        if index <= 44: return [0, 25] + ([26, 28] if index == 30 else [])
        if index <= 48: return [0, 45]
        return [0, 49, max(n for n in [50, 59, 68, 77] if n < index)]
    return []


def derive(
    buffers: dict[str, bytes] | None = None,
) -> tuple[list[Line], list[Row], list[Paragraph]]:
    """Replay exact native bytes and the reviewed fee/context mapping."""
    def read(name: str) -> bytes:
        return buffers[name] if buffers is not None else (PACKET / name).read_bytes()

    prep = json.loads(read('04-verification/PREPARATION.json'))
    candidate = read(CANDIDATE)
    doc = pymupdf.open(stream=read(SOURCE), filetype='pdf')
    lines: list[Line] = []
    pages: dict[int, list[Line]] = {}
    for pn, page in enumerate(doc, 1):
        native = read(prep['native_pages'][pn-1]['native']['path'])
        start = prep['native_pages'][pn-1]['candidate_start']
        assert candidate[start:start+len(native)] == native
        offset = 0
        plines = []
        for block in page.get_text('dict', flags=195, sort=False)['blocks']:
            for item in block.get('lines', []):
                text = ''.join(span['text'] for span in item['spans']) + '\n'
                data = text.encode()
                assert native[offset:offset+len(data)] == data
                colors = [span['color'] for span in item['spans']]
                line = Line(id=ref(pn, len(plines)), page=pn, start=offset,
                            end=offset+len(data), candidate_start=start+offset,
                            candidate_end=start+offset+len(data), text=text,
                            sha256=digest(data), bbox=list(item['bbox']), colors=colors,
                            visibility=('white_encoded_not_visible'
                                        if set(colors)=={16777215} else 'visible'))
                plines.append(line)
                offset += len(data)
        assert offset == len(native)
        pages[pn] = plines
        lines += plines
    paragraphs = []
    ranges = {2: [(83,85)], 3: [(81,82),(83,87),(87,89)],
              4: [(87,91),(91,94),(95,97)], 5: [(207,208),(208,209)],
              6: [(4,5),(28,29),(31,33),(87,89),(89,93),(93,97)]}
    for pn, spans in ranges.items():
        for a,b in spans:
            paragraphs.append(Paragraph(id=f'C{pn}-{a}', page=pn, heading_refs=[],
                              body_refs=refs(pn,list(range(a,b))),kind='context'))
    for h,a,b in [(1,11,14),(2,14,16),(3,16,21),(4,21,28),(5,28,30),
                  (6,38,43),(7,43,46),(8,46,50),(9,50,60),(10,30,38)]:
        paragraphs.append(Paragraph(id=f'D{h}',page=7,heading_refs=[ref(7,h)],
                          body_refs=refs(7,list(range(a,b))),kind='definition'))
    fee_pattern = re.compile(r'(?:\$[\d,]+|n/a|no charge|n/c|1\.5 x original plan review fee)')
    rows = []
    for pn in range(2,7):
        pl = pages[pn]
        consumed = set()
        for i,line in enumerate(pl):
            if i in consumed or not fee_pattern.fullmatch(line.text.strip()): continue
            if line.visibility != 'visible': continue
            cells = [i]
            if pn == 5:
                assert fee_pattern.fullmatch(pl[i+1].text.strip())
                cells.append(i+1)
                consumed.add(i+1)
            labels = [j for j,l in enumerate(pl) if l.bbox[0] < 580 and
                      abs((l.bbox[1]+l.bbox[3]-line.bbox[1]-line.bbox[3])/2) < 3.0
                      and j not in cells]
            if pn == 5 and i == 187: labels = [184,185,186]
            assert labels, (pn,i)
            context = [p.id for p in paragraphs if p.page in [pn,7]]
            rows.append(Row(id=f'R{pn}-{len([r for r in rows if r.page==pn])+1:03}',page=pn,
                            label_refs=refs(pn,labels),fee_refs=[[ref(pn,j)] for j in cells],
                            columns=['Annual Revocable','Prescribed'] if pn==5 else ['Fee'],
                            group_refs=refs(pn,group_numbers(pn,i)),context_refs=context,
                            note=(
                                'Exact source cells; all listed context and definition records acc'
                                'ompany this row. No fee arithmetic or inferred unit.'
                            )))
    rows.append(Row(id='R4-CLOSEOUT',page=4,label_refs=refs(4,[91,92,93]),
                    fee_refs=[refs(4,[83,84,85])],columns=['Fee'],group_refs=[ref(4,82)],
                    context_refs=[p.id for p in paragraphs if p.page in [4,7]],
                    note=(
                        'Literal fee reference; the no-charge-within-permitted-year except'
                        'ion remains attached.'
                    )))
    return lines, rows, paragraphs


if __name__ == '__main__':
    import sys
    a,b,c = derive()
    sys.stdout.write(
        f'{len(a)} native lines, {len(b)} fee rows, {len(c)} context/definition records\n'
    )
