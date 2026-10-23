"""One vault file -> ParsedNote (frontmatter, type, cleaned body, raw links, tags). SPEC §8 step 3.

Pure: no file or DB access. Links are extracted raw; resolving them is Sprint 3.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import yaml

from ask_ragu.settings import settings

log = logging.getLogger(__name__)

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w-]*)")
INLINE_CODE = re.compile(r"(`[^`\n]*`)")  # capturing: re.split keeps code spans at odd indexes
CALLOUT = re.compile(r"^>\s*\[!\w+\][+-]?\s*(.*)$")
TEMPLATER = re.compile(r"<%.*?%>")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
WIKILINK = re.compile(r"(!?)\[\[([^\]]+)\]\]")
# What tag scanning must not see: wikilinks, markdown link targets, bare URLs (they contain '#').
NOT_TAGS = re.compile(r"\[\[[^\]]*\]\]|\]\([^)]*\)|https?://\S+")
TAG = re.compile(r"(?<![\w#&/])#([\w/-]+)")


@dataclass
class ParsedNote:
    path: str
    title: str
    note_type: str
    frontmatter: dict
    body: str
    links: list[tuple[str, str]] = field(default_factory=list)  # (raw_target, "link" | "embed")
    tags: list[str] = field(default_factory=list)


def is_indexable(path: str) -> bool:
    p = PurePosixPath(path)
    return (
        p.suffix == ".md"
        and p.parts[0] not in settings.vault_excluded_dirs
        and not any(part.startswith(".") for part in p.parts)
    )


def parse_note(path: str, text: str) -> ParsedNote | None:
    """None if the path is excluded. Never raises on bad content: a broken note is still indexed."""
    if not is_indexable(path):
        return None
    p = PurePosixPath(path)
    frontmatter, body = _split_frontmatter(path, text.replace("\r\n", "\n"))
    links: dict[tuple[str, str], None] = {}  # dict as an ordered set
    tags = dict.fromkeys(_frontmatter_tags(frontmatter.get("tags")))
    body = _clean(body, links, tags)
    return ParsedNote(
        path=path,
        title=p.stem,
        # Root or unknown folder: a default type rather than silently dropping the note.
        note_type=settings.vault_folder_types.get(
            p.parts[0] if len(p.parts) > 1 else "", settings.vault_default_note_type
        ),
        frontmatter=frontmatter,
        body=body,
        links=list(links),
        tags=list(tags),
    )


def _split_frontmatter(path: str, text: str) -> tuple[dict, str]:
    m = re.match(r"---\n(.*?)^---[ \t]*$\n?", text, re.S | re.M)
    if not m:
        return {}, text
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        log.warning("malformed frontmatter in %s: %s", path, e)
        data = None
    if data is not None and not isinstance(data, dict):
        log.warning("frontmatter in %s is not a mapping, ignored", path)
    data = data if isinstance(data, dict) else {}
    # YAML turns `created: 2024-01-01` into a date, which jsonb can't store; dates become strings.
    return json.loads(json.dumps(data, default=str)), text[m.end() :]


def _frontmatter_tags(value) -> list[str]:
    items = value if isinstance(value, list) else re.split(r"[,\s]+", value or "")
    return [t for t in (str(i).strip().lstrip("#").lower() for i in items) if t]


def _clean(body: str, links: dict, tags: dict) -> str:
    out, in_callout = [], False
    fence, drop_fence = None, False  # open fence marker (e.g. "```"); whether the block is dropped
    for line in body.split("\n"):
        if fence:  # inside a code block: keep verbatim (or drop), extract nothing
            if re.fullmatch(rf"\s*{re.escape(fence)}{re.escape(fence[0])}*\s*", line):
                fence = None
            if not drop_fence:
                out.append(line)
            continue
        if m := FENCE.match(line):
            fence, drop_fence = m.group(1), m.group(2).lower() in settings.vault_stripped_fences
            if not drop_fence:
                out.append(line)
            continue

        if m := CALLOUT.match(line):
            in_callout = True
            line = m.group(1)
            if not line:
                continue
        elif in_callout and line.startswith(">"):
            line = re.sub(r"^>\s?", "", line)
        else:
            in_callout = False

        parts = INLINE_CODE.split(line)
        for i in range(0, len(parts), 2):  # even indexes are outside inline code
            parts[i] = _clean_text(parts[i], links, tags)
        out.append("".join(parts))
    return "\n".join(out).strip()


def _clean_text(text: str, links: dict, tags: dict) -> str:
    text = MD_IMAGE.sub("", TEMPLATER.sub("", text))
    for t in TAG.findall(NOT_TAGS.sub(" ", text)):
        if not t.isdigit():  # Obsidian: #123 isn't a tag
            tags[t.lower()] = None
    return WIKILINK.sub(lambda m: _link(m, links), text)


def _link(m: re.Match, links: dict) -> str:
    """Record the link; return its display text so the body reads like prose.

    `\\|` inside a wikilink is an escaped pipe in Obsidian — must not split
    the target/alias. We swap it for a sentinel before partitioning, then restore.
    """
    embed, inner = m.group(1), m.group(2)
    inner = inner.replace("\\|", "\x00")
    target, _, alias = inner.partition("|")
    target = target.replace("\x00", "|")
    alias = alias.replace("\x00", "|")
    note, _, heading = target.partition("#")
    note = note.strip()
    if embed and PurePosixPath(note).suffix.lower() not in ("", ".md"):
        return ""  # ![[x.png]]: attachment embed, skipped not resolved
    if note:  # [[#Heading]] is a link to the same note: no edge
        links[(note, "embed" if embed else "link")] = None
    if alias.strip():
        return alias.strip()
    heading = "" if heading.startswith("^") else heading.strip()
    return " > ".join(x for x in (note, heading) if x)
