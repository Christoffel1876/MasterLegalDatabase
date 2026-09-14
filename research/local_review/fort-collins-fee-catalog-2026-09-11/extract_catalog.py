"""Reproduce and verify one preserved Fort Collins fee-page DOM snapshot offline."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urljoin

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

LOGGER = logging.getLogger(__name__)
EXPECTED_SHA = 'a10bcc173cd8e20bbfa83dd06292203c6c4ddd4720a58338c6f2b5f1eaeceb55'
SOURCE_URL = 'https://www.fortcollins.gov/Business/Building-and-Development/Fee-Schedules'
SHA = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
        'param', 'source', 'track', 'wbr'}
STRUCTURAL = {'div', 'section', 'article', 'main', 'aside', 'p', 'ul', 'ol', 'li',
              'table', 'blockquote', 'dl', 'dt', 'dd', 'figure', 'figcaption',
              'picture', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img'}
HEADINGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
EXCLUDED_TAGS = {'script', 'style', 'noscript', 'template'}
DATE_PATTERN = re.compile(
    r'\b(?:January|February|March|April|May|June|July|August|September|October|'
    r'November|December|Jan\.|Feb\.|Mar\.|Apr\.|Jun\.|Jul\.|Aug\.|Sep\.|'
    r'Oct\.|Nov\.|Dec\.)\s+\d{1,2},?\s+\d{4}\b|\bin 2022\b'
)


class StrictModel(BaseModel):
    """Reject unexpected fields and silent type conversions."""
    model_config = ConfigDict(extra='forbid', strict=True)


class HTTPReceipt(StrictModel):
    """Exact fields of the earlier Atlas HTTP capture; no new retrieval implied."""
    audit_id: Literal['SD004-14']
    requested_url: Literal[SOURCE_URL]
    started_at: AwareDatetime
    completed_at: AwareDatetime
    final_url: Literal[SOURCE_URL]
    status_code: Literal[200]
    content_type: Literal['text/html; charset=utf-8']
    redirect_urls: list[str]
    body_path: Literal['SD004-14.html']
    sha256: Literal[EXPECTED_SHA]
    size_bytes: Literal[142539]
    source_bytes_preserved: Literal[True]
    error: None
    legal_currentness: Literal['not_verified']
    inspection_scope: Literal['not_yet_inspected']


class FileIdentity(StrictModel):
    """Exact file bytes, with a package-relative path."""
    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)


class ByteRange(StrictModel):
    """Half-open byte range in the original UTF-8 HTML."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    sha256: SHA

    @model_validator(mode='after')
    def ordered(self) -> ByteRange:
        """Reject inverted source slices."""
        if self.end < self.start:
            raise ValueError('Inverted source byte range')
        return self


class Attribute(StrictModel):
    """Decoded HTML attribute, preserving original order and duplicate entries."""
    name: str
    value: str | None


class ElementRecord(StrictModel):
    """DOM element locator and exact source envelope; text lives in fragments."""
    locator: str
    parent_locator: str | None
    tag: str
    attributes: list[Attribute]
    source: ByteRange
    start_tag: ByteRange
    end_tag: ByteRange | None


class Fragment(StrictModel):
    """One source text/entity token or explicitly projected br line break."""
    id: str
    element_locator: str
    kind: Literal['text', 'entity', 'character_reference', 'br_break']
    source: ByteRange
    dom_text: str
    dom_text_sha256: SHA


class Cell(StrictModel):
    """One table cell in original row order; no spanning-cell expansion."""
    id: str
    element_locator: str
    tag: Literal['td', 'th']
    rowspan: int = Field(ge=1)
    colspan: int = Field(ge=1)
    fragment_ids: list[str]
    dom_text: str
    normalized_text: str


class Row(StrictModel):
    """One source row, retaining whether cells use th or td."""
    element_locator: str
    cells: list[Cell]


class Block(StrictModel):
    """DOM-ordered content; table text is stored only in its cells."""
    id: str
    kind: Literal['heading', 'paragraph', 'list_item_fragment', 'text_run', 'table', 'image']
    element_locator: str
    source: ByteRange
    component_id: str | None
    heading_context_ids: list[str]
    parent_list_item_locator: str | None
    list_container_locator: str | None
    list_type: Literal['ul', 'ol'] | None
    heading_level: int | None = Field(default=None, ge=1, le=6)
    fragment_ids: list[str]
    dom_text: str | None
    normalized_text: str | None
    table_rows: list[Row]
    image_alt: str | None
    image_src: str | None

    @model_validator(mode='after')
    def distinct_content(self) -> Block:
        """Do not repeat table-cell text as an aggregate block transcript."""
        if self.kind == 'table':
            if self.fragment_ids or self.dom_text is not None or self.normalized_text is not None:
                raise ValueError('Table text must be stored only in cells')
        elif self.table_rows:
            raise ValueError('Non-table has table rows')
        if self.kind == 'image' and self.fragment_ids:
            raise ValueError('Image alt is metadata, not source text fragments')
        return self


class Component(StrictModel):
    """Source-defined accordion/side panel, without inferred fee ownership."""
    id: str
    element_locator: str
    label: str
    block_ids: list[str]


class Anchor(StrictModel):
    """Observed href and label; resolving a URL never opens it."""
    element_locator: str
    raw_href_decoded: str
    resolved_url: str
    normalized_label: str
    title: str | None
    fragment_ids: list[str]
    containing_content_ids: list[str]
    component_id: str | None
    source: ByteRange
    resource_opened_by_this_extraction: Literal[False] = False


class DateMention(StrictModel):
    """Printed date phrase only; event type and applicability stay unclassified."""
    content_id: str
    component_id: str | None
    literal: str
    normalized_start: int = Field(ge=0)
    normalized_end: int = Field(gt=0)
    interpretation: Literal['printed_phrase_unclassified'] = 'printed_phrase_unclassified'


class ExcludedRange(StrictModel):
    """Explicitly excluded source region; original bytes remain preserved."""
    locator: str
    source: ByteRange
    reason: str


class Coverage(StrictModel):
    """Source-token accounting, not legal or fee coverage."""
    selected_element_count: int
    text_fragment_count: int
    nonblank_text_fragment_count: int
    assigned_nonblank_text_fragment_count: int
    unassigned_whitespace_fragment_ids: list[str]
    duplicated_fragment_ids: list[str]
    unassigned_nonblank_fragment_ids: list[str]
    block_count: int
    table_count: Literal[9]
    table_row_count_including_headers: Literal[76]
    table_cell_count: int
    list_item_fragment_count: int
    anchor_count: int


class Extraction(StrictModel):
    """Deterministic source snapshot; no operative fees or rules are created."""
    schema_version: Literal[1] = 1
    source_id: Literal['fort-collins-fee-catalog-atlas-sd004-14'] = (
        'fort-collins-fee-catalog-atlas-sd004-14'
    )
    status: Literal['source_snapshot_structured_pending_semantic_review'] = (
        'source_snapshot_structured_pending_semantic_review'
    )
    legal_currentness: Literal['not_verified'] = 'not_verified'
    source_url: Literal[SOURCE_URL] = SOURCE_URL
    source_html: FileIdentity
    source_http_receipt: FileIdentity
    source_capture_completed_at: AwareDatetime
    source_capture_time_role: Literal['actual prior Atlas HTTP receipt, not extraction time'] = (
        'actual prior Atlas HTTP receipt, not extraction time'
    )
    extraction_program: FileIdentity
    selected_root_locator: str
    selector: Literal['unique element with id=main-content'] = (
        'unique element with id=main-content'
    )
    method: str
    normalization: str
    elements: list[ElementRecord]
    text_fragments: list[Fragment]
    components: list[Component]
    blocks: list[Block]
    anchors: list[Anchor]
    printed_date_mentions: list[DateMention]
    excluded_ranges: list[ExcludedRange]
    coverage: Coverage
    limitations: list[str]

    @model_validator(mode='after')
    def accounting(self) -> Extraction:
        """Require ordered unique blocks and exhaustive nonblank fragment ownership."""
        if self.coverage.duplicated_fragment_ids or self.coverage.unassigned_nonblank_fragment_ids:
            raise ValueError('Missing or duplicated source text')
        if self.coverage.nonblank_text_fragment_count != (
            self.coverage.assigned_nonblank_text_fragment_count
        ):
            raise ValueError('Incomplete fragment accounting')
        if len({b.id for b in self.blocks}) != len(self.blocks):
            raise ValueError('Repeated block ID')
        return self


def sha256(body: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(body).hexdigest()


def normalize(text: str) -> str:
    """Collapse Unicode whitespace only; no NFC, spelling or punctuation correction."""
    return re.sub(r'\s+', ' ', text).strip()


@dataclass
class Node:
    """Private source-offset tree, independent of a browser's repaired DOM."""
    tag: str
    attrs: list[tuple[str, str | None]]
    parent: Node | None
    locator: str
    start: int
    start_end: int
    end_start: int | None = None
    end: int | None = None
    children: list[Node | Fragment] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)

    def attr(self, name: str) -> str | None:
        """Return the first decoded source attribute with this name."""
        return next((value for key, value in self.attrs if key == name), None)


class SourceParser(HTMLParser):
    """Parse bounded UTF-8 source with offsets and fail on unmatched element closures."""

    def __init__(self, body: bytes) -> None:
        super().__init__(convert_charrefs=False)
        self.body = body
        self.text = body.decode('utf-8', errors='strict')
        self.line_starts = [0]
        self.line_starts.extend(match.end() for match in re.finditer('\n', self.text))
        self.byte_prefix = [0]
        for character in self.text:
            self.byte_prefix.append(self.byte_prefix[-1] + len(character.encode('utf-8')))
        self.root = Node('document', [], None, '', 0, 0, len(body), len(body))
        self.current = self.root
        self.nodes: list[Node] = []
        self.fragments: list[Fragment] = []
        self.implicit_closures: list[tuple[str, int]] = []

    def position(self) -> int:
        """Return current callback position in source characters."""
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def byte_range(self, start: int, end: int) -> ByteRange:
        """Build a byte-range receipt."""
        return ByteRange(start=start, end=end, sha256=sha256(self.body[start:end]))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Create an element and retain original start-tag bounds."""
        pos = self.position()
        raw = self.get_starttag_text()
        self.current.counts[tag] += 1
        locator = f'{self.current.locator}/{tag}[{self.current.counts[tag]}]'
        node = Node(tag, attrs, self.current, locator, self.byte_prefix[pos],
                    self.byte_prefix[pos + len(raw)])
        self.current.children.append(node)
        self.nodes.append(node)
        if tag in VOID:
            node.end = node.start_end
            if tag == 'br':
                self.add_fragment(node, 'br_break', node.start, node.end, '\n')
        else:
            self.current = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle XHTML self-closing tags without fabricated closing text."""
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.current.end = self.current.start_end
            self.current = self.current.parent or self.root

    def handle_endtag(self, tag: str) -> None:
        """Retain exact closing-tag bounds and track any parser closure repair."""
        if tag in VOID:
            return
        pos = self.position()
        end = self.text.find('>', pos) + 1
        if end <= pos:
            raise ValueError('Unterminated closing tag')
        cursor = self.current
        while cursor is not self.root and cursor.tag != tag:
            cursor.end = self.byte_prefix[pos]
            self.implicit_closures.append((cursor.locator, cursor.end))
            cursor = cursor.parent or self.root
        if cursor is self.root:
            raise ValueError(f'Unmatched closing tag {tag}')
        cursor.end_start = self.byte_prefix[pos]
        cursor.end = self.byte_prefix[end]
        self.current = cursor.parent or self.root

    def add_fragment(self, node: Node, kind: str, start: int, end: int, text: str) -> None:
        """Keep one exact source token and its explicitly decoded projection."""
        fragment = Fragment(id=f't{len(self.fragments) + 1:06d}',
                            element_locator=node.locator, kind=kind,
                            source=self.byte_range(start, end), dom_text=text,
                            dom_text_sha256=sha256(text.encode('utf-8')))
        node.children.append(fragment)
        self.fragments.append(fragment)

    def handle_data(self, data: str) -> None:
        """Keep raw character data without whitespace changes."""
        pos = self.position()
        if self.text[pos:pos + len(data)] != data:
            raise ValueError('Character-data source mismatch')
        self.add_fragment(self.current, 'text', self.byte_prefix[pos],
                          self.byte_prefix[pos + len(data)], data)

    def handle_entityref(self, name: str) -> None:
        """Preserve and decode one named HTML entity."""
        self.entity(name, 'entity')

    def handle_charref(self, name: str) -> None:
        """Preserve and decode one numeric HTML entity."""
        self.entity('#' + name, 'character_reference')

    def entity(self, name: str, kind: str) -> None:
        """Use the actual source entity spelling, including optional semicolon."""
        pos = self.position()
        length = len(name) + 1
        if self.text[pos + length:pos + length + 1] == ';':
            length += 1
        raw = self.text[pos:pos + length]
        self.add_fragment(self.current, kind, self.byte_prefix[pos],
                          self.byte_prefix[pos + length], html.unescape(raw))


def descendants(node: Node) -> list[Node]:
    """Return descendants in source pre-order."""
    result = [node]
    for child in node.children:
        if isinstance(child, Node):
            result.extend(descendants(child))
    return result


def text_fragments(node: Node) -> list[Fragment]:
    """Return all descendant source fragments in order."""
    result: list[Fragment] = []
    for child in node.children:
        if isinstance(child, Fragment):
            result.append(child)
        else:
            result.extend(text_fragments(child))
    return result


def ancestor(node: Node, predicate: Any) -> Node | None:
    """Return nearest matching source ancestor, including the element itself."""
    current: Node | None = node
    while current is not None:
        if predicate(current):
            return current
        current = current.parent
    return None


def file_identity(path: Path, base: Path) -> FileIdentity:
    """Read a confined non-symlink package file and hash its bytes."""
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('Symlink file path')
    body = path.read_bytes()
    return FileIdentity(path=path.relative_to(base).as_posix(),
                        sha256=sha256(body), size_bytes=len(body))


def extract(base: Path) -> Extraction:
    """Recreate every output field from immutable local source inputs."""
    source = base / 'source/SD004-14.html'
    receipt_path = base / 'source/SD004-14.json'
    receipt = HTTPReceipt.model_validate_json(receipt_path.read_bytes())
    body = source.read_bytes()
    if sha256(body) != EXPECTED_SHA or len(body) != receipt.size_bytes:
        raise ValueError('Source body differs from the known HTTP receipt')
    parser = SourceParser(body)
    parser.feed(parser.text)
    parser.close()
    roots = [node for node in parser.nodes if node.attr('id') == 'main-content']
    if len(roots) != 1:
        raise ValueError('Expected one main-content root')
    root = roots[0]
    nodes = descendants(root)
    paths = {node.locator for node in nodes}
    if any(path in paths for path, _ in parser.implicit_closures):
        raise ValueError('Implicit parser closure inside selected source content')
    if any(node.end is None for node in nodes):
        raise ValueError('Unclosed selected source element')
    fragments = text_fragments(root)
    excluded_nodes = [node for node in nodes if node.tag in EXCLUDED_TAGS]
    if excluded_nodes:
        raise ValueError('New non-content embedded element needs explicit review')
    records = [ElementRecord(
        locator=node.locator, parent_locator=node.parent.locator if node.parent else None,
        tag=node.tag, attributes=[Attribute(name=k, value=v) for k, v in node.attrs],
        source=parser.byte_range(node.start, node.end),
        start_tag=parser.byte_range(node.start, node.start_end),
        end_tag=(parser.byte_range(node.end_start, node.end)
                 if node.end_start is not None else None),
    ) for node in nodes]
    component_nodes = [node for node in nodes if (
        'oc-wysiwyg-container-panel' in (node.attr('class') or '').split()
        or 'consultation-snapshot' in (node.attr('class') or '').split()
    )]
    components: list[Component] = []
    component_by_path: dict[str, str] = {}
    for index, node in enumerate(component_nodes, 1):
        headings = [child for child in node.children
                    if isinstance(child, Node) and child.tag in HEADINGS]
        if len(headings) != 1:
            raise ValueError('Source panel heading changed')
        label = normalize(''.join(f.dom_text for f in text_fragments(headings[0])))
        item = Component(id=f'component-{index:02d}', element_locator=node.locator,
                         label=label, block_ids=[])
        components.append(item)
        component_by_path[node.locator] = item.id
    blocks: list[Block] = []
    heading_stack: list[tuple[int, str]] = []

    def component_id(node: Node) -> str | None:
        match = ancestor(node, lambda n: n.locator in component_by_path)
        return component_by_path[match.locator] if match else None

    def emit(node: Node, kind: str, parts: list[Fragment],
             rows: list[Row] | None = None) -> None:
        bid = f'block-{len(blocks) + 1:04d}'
        item_parent = ancestor(node.parent, lambda n: n.tag == 'li') if node.parent else None
        list_parent = ancestor(node, lambda n: n.tag in {'ul', 'ol'})
        level = int(node.tag[1]) if node.tag in HEADINGS else None
        if level is not None:
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
        dom = ''.join(part.dom_text for part in parts)
        block = Block(
            id=bid, kind=kind, element_locator=node.locator,
            source=parser.byte_range(node.start, node.end),
            component_id=component_id(node),
            heading_context_ids=[value for _, value in heading_stack],
            parent_list_item_locator=item_parent.locator if item_parent else None,
            list_container_locator=list_parent.locator if list_parent else None,
            list_type=list_parent.tag if list_parent else None,
            heading_level=level, fragment_ids=[part.id for part in parts],
            dom_text=None if kind in {'table', 'image'} else dom,
            normalized_text=None if kind in {'table', 'image'} else normalize(dom),
            table_rows=rows or [], image_alt=node.attr('alt') if kind == 'image' else None,
            image_src=node.attr('src') if kind == 'image' else None,
        )
        blocks.append(block)
        if level is not None:
            heading_stack.append((level, bid))

    def visit(node: Node) -> None:
        if node.tag == 'table':
            if any(child.tag == 'table' for child in descendants(node)[1:]):
                raise ValueError('Nested table needs explicit handling')
            rows = []
            for row in (child for child in descendants(node) if child.tag == 'tr'):
                cells = []
                for cell_index, cell in enumerate(
                    (child for child in row.children
                     if isinstance(child, Node) and child.tag in {'td', 'th'}), 1
                ):
                    parts = text_fragments(cell)
                    dom = ''.join(part.dom_text for part in parts)
                    cells.append(Cell(
                        id=f'table-{sum(b.kind == "table" for b in blocks):02d}'
                           f'-row-{len(rows):03d}-cell-{cell_index:02d}',
                        element_locator=cell.locator, tag=cell.tag,
                        rowspan=int(cell.attr('rowspan') or 1),
                        colspan=int(cell.attr('colspan') or 1),
                        fragment_ids=[part.id for part in parts],
                        dom_text=dom, normalized_text=normalize(dom),
                    ))
                rows.append(Row(element_locator=row.locator, cells=cells))
            emit(node, 'table', [], rows)
            return
        if node.tag == 'img':
            emit(node, 'image', [])
            return
        if node.tag in HEADINGS or node.tag in {'p', 'dt', 'dd', 'figcaption'}:
            if any(child.tag in STRUCTURAL for child in descendants(node)[1:]):
                raise ValueError('Nested structural block in atomic paragraph/heading')
            emit(node, 'heading' if node.tag in HEADINGS else 'paragraph', text_fragments(node))
            return
        pending: list[Fragment] = []

        def flush() -> None:
            nonlocal pending
            if any(normalize(part.dom_text) for part in pending):
                emit(node, 'list_item_fragment' if node.tag == 'li' else 'text_run', pending)
            pending = []

        for child in node.children:
            if isinstance(child, Fragment):
                pending.append(child)
            elif child.tag in STRUCTURAL or any(
                descendant.tag in STRUCTURAL for descendant in descendants(child)[1:]
            ):
                flush()
                visit(child)
            else:
                pending.extend(text_fragments(child))
        flush()

    visit(root)
    by_fragment: dict[str, list[str]] = {}
    for block in blocks:
        owners = [(block.id, block.fragment_ids)]
        owners.extend((cell.id, cell.fragment_ids)
                      for row in block.table_rows for cell in row.cells)
        for owner, ids in owners:
            for fid in ids:
                by_fragment.setdefault(fid, []).append(owner)
    for component in components:
        component.block_ids = [block.id for block in blocks if block.component_id == component.id]
    anchors = []
    for node in nodes:
        href = node.attr('href')
        if node.tag != 'a' or href is None:
            continue
        parts = text_fragments(node)
        ids = [part.id for part in parts]
        containing = list(dict.fromkeys(owner for fid in ids
                                        for owner in by_fragment.get(fid, [])))
        anchors.append(Anchor(
            element_locator=node.locator, raw_href_decoded=href,
            resolved_url=urljoin(SOURCE_URL, href),
            normalized_label=normalize(''.join(part.dom_text for part in parts)),
            title=node.attr('title'), fragment_ids=ids,
            containing_content_ids=containing, component_id=component_id(node),
            source=parser.byte_range(node.start, node.end),
        ))
    dates = []
    for block in blocks:
        contents = [(block.id, block.normalized_text or '')]
        contents.extend((cell.id, cell.normalized_text)
                        for row in block.table_rows for cell in row.cells)
        for content_id, text in contents:
            for match in DATE_PATTERN.finditer(text):
                dates.append(DateMention(content_id=content_id, component_id=block.component_id,
                                         literal=match.group(), normalized_start=match.start(),
                                         normalized_end=match.end()))
    nonblank = {part.id for part in fragments if normalize(part.dom_text)}
    assigned = set(by_fragment)
    table_blocks = [block for block in blocks if block.kind == 'table']
    coverage = Coverage(
        selected_element_count=len(nodes), text_fragment_count=len(fragments),
        nonblank_text_fragment_count=len(nonblank),
        assigned_nonblank_text_fragment_count=len(nonblank & assigned),
        unassigned_whitespace_fragment_ids=[part.id for part in fragments
                                            if part.id not in assigned and part.id not in nonblank],
        duplicated_fragment_ids=[fid for fid, owners in by_fragment.items() if len(owners) != 1],
        unassigned_nonblank_fragment_ids=sorted(nonblank - assigned),
        block_count=len(blocks), table_count=len(table_blocks),
        table_row_count_including_headers=sum(len(block.table_rows) for block in table_blocks),
        table_cell_count=sum(len(row.cells) for block in table_blocks for row in block.table_rows),
        list_item_fragment_count=sum(block.kind == 'list_item_fragment' for block in blocks),
        anchor_count=len(anchors),
    )
    return Extraction(
        source_html=file_identity(source, base),
        source_http_receipt=file_identity(receipt_path, base),
        source_capture_completed_at=receipt.completed_at,
        extraction_program=file_identity(base / 'extract_catalog.py', base),
        selected_root_locator=root.locator,
        method='Python html.parser with convert_charrefs=False; strict UTF-8 source offsets. '
               'No browser execution, OCR, network request or inferred fee calculation.',
        normalization='dom_text concatenates unchanged text and html.unescape(entity) fragments; '
                      'br is explicitly projected as LF. normalized_text collapses Unicode '
                      'whitespace to one ASCII space and trims ends. No Unicode normalization, '
                      'spelling/punctuation/number correction, or removal of source anomalies. '
                      'Locators are source-tree tag sibling indices, not browser-repaired XPath.',
        elements=records, text_fragments=fragments, components=components,
        blocks=blocks, anchors=anchors, printed_date_mentions=dates,
        excluded_ranges=[
            ExcludedRange(locator='before selected root',
                          source=parser.byte_range(0, root.start),
                          reason='Document head, scripts/styles, header, navigation, breadcrumbs '
                                 'and other content before #main-content; original bytes retained.'),
            ExcludedRange(locator='after selected root',
                          source=parser.byte_range(root.end, len(body)),
                          reason='Back-to-top, site footer, scripts and closing layout after '
                                 '#main-content; original bytes retained.'),
        ],
        coverage=coverage,
        limitations=[
            'This is the exact September 10, 2026 page snapshot. Extraction does not fetch '
            'today’s '
            'page, follow linked sources, establish complete amendment chains or verify current law.',
            'All source-defined accordion panels, payment instructions, fee prose/lists/tables and '
            'the page-specific Contact Us sidebar are included. The construction-image alt/src '
            'are metadata; no external image was downloaded or visually interpreted.',
            'Components follow source DOM panels, not inferred owners. Heading context alone may '
            'contain nested same-level headings; component_id preserves the surrounding source panel.',
            'Dates are printed phrases with local block/component references, not classified '
            'adoption/effective/revision events. Dates are never copied onto other fee components.',
            'PFA, county, utility and city charges/referrals retain their exact source labels and '
            'service-area text; ownership, legal form and applicability remain for semantic review.',
            'Links, heading-context IDs and DOM envelopes are provenance metadata. Content text '
            'is assigned once per fragment; nested lists are not repeated in parent transcripts, '
            'and table-cell text is not repeated as a table-level transcript.',
            'No RuleUnits, fee totals, legal interpretations, source registry entries, coverage '
            'promotions or raw/control-ledger writes are produced.',
        ],
    )


def serialize(model: BaseModel) -> bytes:
    """Validate exact JSON bytes before any record is written."""
    body = (model.model_dump_json(indent=2) + '\n').encode('utf-8')
    type(model).model_validate_json(body)
    return body


def main() -> int:
    """Write once or verify the deterministic extraction and exported model schema."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    arguments = parser.parse_args()
    base = Path(__file__).resolve().parent
    model = extract(base)
    payload = serialize(model)
    schema = (json.dumps(Extraction.model_json_schema(), indent=2) + '\n').encode()
    if arguments.verify:
        if (base / 'extraction.json').read_bytes() != payload:
            raise ValueError('Extraction differs from deterministic source replay')
        if (base / 'extraction.schema.json').read_bytes() != schema:
            raise ValueError('Exported schema differs from the model')
        Extraction.model_validate_json(payload)
        LOGGER.info('Verified %s blocks, %s tables, %s anchors; no missing or repeated text.',
                    model.coverage.block_count, model.coverage.table_count,
                    model.coverage.anchor_count)
        return 0
    for name, body in [('extraction.json', payload), ('extraction.schema.json', schema)]:
        destination = base / name
        if destination.exists():
            raise FileExistsError(f'Refusing to replace {destination}')
        temporary = base / (name + '.tmp')
        with temporary.open('xb') as stream:
            stream.write(body)
        temporary.replace(destination)
    LOGGER.info('Structured source snapshot written; semantic review remains pending.')
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    sys.exit(main())
