"""Cleaned note body -> heading-aware chunks (SPEC §8 step 3). Sizes are in characters.

1. Split on headings (outside code). heading_path = "Title > H2 > H3"; metadata headings
   (CHUNK_METADATA_HEADINGS, e.g. "Part of") start a section but never join the path.
2. Merge neighbours where one side is small, as long as the result fits the max.
   A merged chunk's heading_path is the shared prefix; the other headings stay in the text.
3. Split anything still over the max on paragraph boundaries, with a small overlap.
"""

import re
from dataclasses import dataclass

from ask_ragu.index.parse import FENCE
from ask_ragu.settings import settings

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


@dataclass
class Section:
    path: list[str]  # title, then each heading above this text
    heading_line: str  # "## H2" ("" for the text before the first heading)
    body: str

    @property
    def size(self) -> int:
        return len(self.heading_line) + len(self.body)


@dataclass
class Chunk:
    heading_path: str
    content: str


def chunk_note(title: str, body: str) -> list[Chunk]:
    if len(body.strip()) < settings.stub_min_chars:  # near-empty note: noise in the index
        return []
    groups: list[list[Section]] = []
    for s in _sections(title, body):
        last = groups[-1] if groups else []
        last_size = sum(x.size for x in last)
        small = min(last_size, s.size) < settings.chunk_merge_below_chars
        if last and small and last_size + s.size <= settings.chunk_max_chars:
            last.append(s)
        else:
            groups.append([s])
    return [c for g in groups for c in _render(g)]


def _sections(title: str, body: str) -> list[Section]:
    sections, stack, fence = [], [], None  # stack: (level, heading text)
    metadata = {h.lower() for h in settings.chunk_metadata_headings}
    current, lines = Section([title], "", ""), []

    def close():
        current.body = "\n".join(lines).strip()
        if current.body:  # heading-only sections vanish; their heading lives on in children's path
            sections.append(current)

    for line in body.split("\n"):
        if fence:
            if re.fullmatch(rf"\s*{re.escape(fence)}{re.escape(fence[0])}*\s*", line):
                fence = None
        elif m := FENCE.match(line):
            fence = m.group(1)
        elif m := HEADING.match(line):
            close()
            level, text = len(m.group(1)), m.group(2)
            stack = [h for h in stack if h[0] < level]
            if text.lower() in metadata:
                # e.g. "## Part of": structure, not topic. Not a heading_path ancestor of what
                # follows; its line stays in the text so "Part of\n- Parent" still reads.
                current, lines = Section([title] + [h[1] for h in stack], "", ""), [line]
                continue
            stack.append((level, text))
            current, lines = Section([title] + [h[1] for h in stack], line.strip(), ""), []
            continue
        lines.append(line)
    close()
    return sections


def _render(group: list[Section]) -> list[Chunk]:
    common = group[0].path
    for s in group[1:]:
        n = 0
        while n < min(len(common), len(s.path)) and common[n] == s.path[n]:
            n += 1
        common = common[:n]
    # A heading goes into the text only if heading_path doesn't already carry it.
    parts = [
        f"{s.heading_line}\n{s.body}" if len(s.path) > len(common) and s.heading_line else s.body
        for s in group
    ]
    path = " > ".join(common)
    return [Chunk(path, text) for text in _split("\n\n".join(parts))]


def _split(text: str) -> list[str]:
    """Pack paragraphs into windows <= max; repeat a short last paragraph as overlap."""
    limit, overlap = settings.chunk_max_chars, settings.chunk_overlap_chars
    if len(text) <= limit:
        return [text]
    pieces = []
    for para in re.split(r"\n\s*\n", text):
        # ponytail: an over-long paragraph is cut per line, then hard at the limit, and its lines
        # are rejoined with blank lines. Rare in this vault; split on sentences if it ever matters.
        for line in para.split("\n") if len(para) > limit else [para]:
            pieces += [line[i : i + limit] for i in range(0, max(len(line), 1), limit)]
    windows, cur = [], []
    for p in pieces:
        if cur and len("\n\n".join(cur + [p])) > limit:
            windows.append("\n\n".join(cur))
            tail = cur[-1]
            cur = [tail] if len(tail) <= overlap and len(tail) + 2 + len(p) <= limit else []
        cur.append(p)
    windows.append("\n\n".join(cur))
    return [w for w in windows if w.strip()]


# Examples (title "T"; real defaults: max 1500, merge below 200, overlap 300, stub 100).
#
# Stub: body "See [[X]]." (under 100 chars) -> [] (no chunks). The note itself is still stored
#   (notes, note_links, note_tags) but has no chunks rows, so only the graph can reach it.
#
# Normal:        ## A / 400 chars / ## B / 400 chars
#   -> ("T > A", "<A text>"), ("T > B", "<B text>")      heading line not repeated in content
#
# Heading-only:  ## A / ### A1 / 400 chars
#   -> ("T > A > A1", "<A1 text>")                       A adds no chunk, only path
#
# Small merge:   ## A / 400 chars / ### A1 / 50 chars / ## B / 400 chars
#   -> ("T > A", "<A text>\n\n### A1\n<A1 text>"), ("T > B", "<B text>")
#      A1 is small, joins A; path = shared prefix "T > A"; A1's heading moves into the text
#
# Preamble:      300 chars / ## A / 400 chars
#   -> ("T", "<preamble>"), ("T > A", "<A text>")
#
# Oversize:      ## A / paragraphs p1..p5, 2,600 chars total
#   -> ("T > A", "p1\n\np2\n\np3"), ("T > A", "p3\n\np4\n\np5")
#      split on paragraphs, each <= 1500; p3 repeated as overlap because it is <= 300 chars
#
# No headings:   3,000 chars of paragraphs -> same as oversize, path "T" on every window
#
# Metadata:      ## Part of / - [[Parent]] / intro (300 chars) / ### Sub / 400 chars
#   -> ("T", "## Part of\n- Parent\n\n<intro>"), ("T > Sub", "<Sub text>")
#      without the rule it would be "T > Part of > Sub"
