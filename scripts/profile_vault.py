"""Vault profiler (Sprint 2 Task 1). Read-only; stdlib only. See scripts/README.md.

Usage: python3 scripts/profile_vault.py <vault-path>

Prints note titles and tag names to the terminal. Never paste raw output into git.
Regex-based, so it's an estimate; the real parser (Task 3) uses a proper Markdown tokenizer.
"""

import re
import sys
from collections import Counter
from pathlib import Path
from statistics import median, quantiles

EXCLUDED = {"Templates", ".obsidian", "Bases", "Attachments", ".git"}  # D-006
FENCE = re.compile(r"^\s*(```|~~~)\s*([\w+-]*)")
HEADING = re.compile(r"^(#{1,6})\s+\S")
LINK = re.compile(r"(?<!!)\[\[([^\]]+)\]\]")
WIKI_EMBED = re.compile(r"!\[\[([^\]]+)\]\]")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
CALLOUT = re.compile(r"^>\s*\[!(\w+)\]")
INLINE_TAG = re.compile(r"(?<![\w&/#\[])#([\w/-]+)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
TEMPLATER = re.compile(r"<%.*?%>")


def pct(xs, p):
    xs = sorted(xs)
    return xs[0] if len(xs) < 2 else quantiles(xs, n=100, method="inclusive")[p - 1]


def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[4:end], text[end + 4 :]
    return None, text


def fm_list(fm, key):
    """Values of `key:` as inline value/[a, b] or as an indented `- item` list."""
    m = re.search(rf"^{key}:[ \t]*(.*)\n((?:[ \t]+-.*\n?)*)", fm + "\n", re.M)
    if not m:
        return None, []
    inline = [t for t in re.split(r"[,\[\]\s]+", m.group(1)) if t]
    items = re.findall(r"-\s+(.+)", m.group(2))
    style = "list" if items else "inline" if inline else "empty"
    return style, [t.strip().strip("'\"#") for t in inline + items]


def main(vault):
    vault = Path(vault)
    notes = [p for p in vault.rglob("*.md") if not EXCLUDED & set(p.relative_to(vault).parts)]
    names = Counter(p.stem.lower() for p in notes)
    paths = {str(p.relative_to(vault).with_suffix("")).lower() for p in notes}

    c = {
        k: Counter()
        for k in "folder fm_keys type_vs_folder callouts langs tags tag_style "
        "tags_per_note heading_levels link_kinds link_resolution embed_ext image_target "
        "numeric_hash".split()
    }
    sizes, bodies, nhead, links_per, sections, preamble = {}, [], {}, [], [], []
    no_fm, unclosed_fm, code_links, templater, tag_eq_domain, aliases = [], 0, 0, 0, 0, 0

    for p in notes:
        rel = p.relative_to(vault)
        folder = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        c["folder"][folder] += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        sizes[rel] = len(text)
        fm, body = split_frontmatter(text)
        if fm is None:
            unclosed_fm += text.startswith("---\n")
            no_fm.append(str(rel.parent))
            fm = ""
        keys = set(re.findall(r"^([\w][\w -]*):", fm, re.M))
        c["fm_keys"].update(keys)
        aliases += "aliases" in keys or "alias" in keys
        if t := re.search(r"^type:\s*(\S+)", fm, re.M):
            c["type_vs_folder"][f"{folder} -> {t.group(1)}"] += 1
        style, tags = fm_list(fm, "tags")
        c["tag_style"][style or "absent"] += 1
        c["tags_per_note"][len(tags)] += 1
        d = re.search(r"^domain:\s*(.+)$", fm, re.M)
        tag_eq_domain += bool(d) and tags == [d.group(1).strip()]
        tags = set(tags)

        bodies.append(len(body.strip()))
        in_code, n_head, n_link, sec = False, 0, 0, 0
        for line in body.splitlines():
            if f := FENCE.match(line):
                if not in_code:
                    c["langs"][f.group(2) or "(none)"] += 1
                in_code = not in_code
            elif in_code:
                code_links += len(LINK.findall(line)) + len(WIKI_EMBED.findall(line))
            else:
                if h := HEADING.match(line):
                    c["heading_levels"][f"H{len(h.group(1))}"] += 1
                    (sections if n_head else preamble).append(sec)
                    n_head += 1
                    sec = 0
                    continue
                plain = INLINE_CODE.sub("", line)
                templater += len(TEMPLATER.findall(plain))
                for raw in LINK.findall(plain):
                    n_link += 1
                    kind = (
                        "block"
                        if "#^" in raw
                        else "heading"
                        if "#" in raw
                        else "folder"
                        if "/" in raw.split("|")[0]
                        else "plain"
                    )
                    c["link_kinds"][kind + ("+alias" if "|" in raw else "")] += 1
                    target = raw.split("|")[0].split("#")[0].strip().lower()
                    c["link_resolution"][
                        "self (#heading only)"
                        if not target
                        else "by path"
                        if target in paths
                        else "by name, unique"
                        if names[target] == 1
                        else "by name, ambiguous"
                        if names[target] > 1
                        else "dangling"
                    ] += 1
                for e in WIKI_EMBED.findall(plain):
                    c["embed_ext"][Path(e.split("|")[0].split("#")[0]).suffix or "(note)"] += 1
                for target in MD_IMAGE.findall(plain):
                    c["image_target"][
                        "url"
                        if re.match(r"https?://", target)
                        else "Attachments/"
                        if target.startswith("Attachments/")
                        else "other path"
                    ] += 1
                if m := CALLOUT.match(line):
                    c["callouts"][m.group(1).lower()] += 1
                if not HEADING.match(line):
                    found = INLINE_TAG.findall(plain)
                    c["numeric_hash"]["#<digits> (not a tag)"] += sum(t.isdigit() for t in found)
                    tags.update(t for t in found if not t.isdigit())
            sec += len(line.strip()) and len(line) + 1
        (sections if n_head else preamble).append(sec)
        nhead[rel] = n_head
        links_per.append(n_link)
        c["tags"].update(tags)

    n = len(notes)
    s = list(sizes.values())
    sec = sections
    heads = list(nhead.values())
    show = lambda k: print(f"{k}:", dict(c[k].most_common(20)))  # noqa: E731

    print(f"== notes: {n} indexable ({len(list(vault.rglob('*.md'))) - n} .md excluded)")
    show("folder")
    show("type_vs_folder")
    print(f"\n== note size (chars)  median {median(s):.0f}  p95 {pct(s, 95):.0f}  max {max(s)}")
    for t in (300, 1000, 2000, 8000):
        print(f"  notes < {t}: {sum(x < t for x in s)}")
    print(
        "  body after frontmatter, small end:",
        {t: sum(x < t for x in bodies) for t in (50, 100, 200)},
    )
    print(
        f"\n== preamble (text before first heading): empty {preamble.count(0)}  has text "
        f"{len(preamble) - preamble.count(0)}  (heading-less notes count here)"
    )
    print(f"\n== sections: body under a heading, heading line excluded  n={len(sec)}")
    print(
        f"  median {median(sec):.0f}  p90 {pct(sec, 90):.0f}  p95 {pct(sec, 95):.0f}"
        f"  max {max(sec)}"
    )
    print(f"  empty (heading only): {sec.count(0)}")
    for t in (80, 200, 400):
        print(f"  sections < {t}: {sum(x < t for x in sec)}")
    for t in (1000, 1500, 2000, 4000):
        print(f"  sections > {t}: {sum(x > t for x in sec)}")
    print(
        f"\n== headings/note  median {median(heads):.0f}  max {max(heads)}"
        f"  notes with none: {heads.count(0)}"
    )
    show("heading_levels")
    print(
        f"\n== links/note  median {median(links_per):.0f}  p95 {pct(links_per, 95):.0f}"
        f"  max {max(links_per)}  total {sum(links_per)}"
    )
    show("link_kinds")
    show("link_resolution")
    print(f"[[...]] inside code blocks: {code_links}")
    print(
        f"duplicate filenames (same stem, different folders): "
        f"{sum(1 for v in names.values() if v > 1)}"
    )
    print(f"notes with aliases key: {aliases}")
    print("\n== embeds")
    show("embed_ext")
    show("image_target")
    print(
        f"\n== frontmatter  none: {len(no_fm)} (in {dict(Counter(no_fm))})"
        f"  opened but never closed: {unclosed_fm}"
    )
    show("fm_keys")
    show("tag_style")
    show("tags_per_note")
    print(f"tags == [domain]: {tag_eq_domain}")
    print(f"\n== tags  distinct {len(c['tags'])}")
    for tag, k in c["tags"].most_common(10):
        print(f"  {k / n:6.1%}  {k:4d}  {tag}")
    show("numeric_hash")
    print("\n== cleaning targets")
    show("callouts")
    show("langs")
    print(f"templater tags outside code: {templater}")
    print("\n== largest notes")
    for rel, size in sorted(sizes.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {size:6d} chars  {nhead[rel]:2d} headings  {rel}")


if __name__ == "__main__":
    main(sys.argv[1])
