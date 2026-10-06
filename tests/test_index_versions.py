"""Guards EMBED_VERSION / PARSE_VERSION (ADR-0017): the parser's and chunker's output on fixed
sample notes is pinned per version. If you changed parse.py / chunk.py / passage_text and this
fails, the change alters what gets indexed:

  1. bump the version named in the failure (full.py), never reuse a number;
  2. add the new fingerprint printed in the failure to the matching dict below.

The next sync then sees a different settings_hash and runs a full index (re-embedding everything
for EMBED, rewriting changed rows only for PARSE). A refactor that keeps output identical passes
untouched — no bump needed."""

import hashlib
import json

import pytest

from ask_ragu.index import full
from ask_ragu.index.chunk import chunk_note
from ask_ragu.index.embed import passage_text
from ask_ragu.index.parse import parse_note
from ask_ragu.settings import settings

# version -> fingerprint. Append; never edit an old entry.
PARSE_FINGERPRINTS = {1: "eb1555fa35f184018dbdb42c08a135aa5f3ec45c8c8663eb1ee821003423a21d"}
EMBED_FINGERPRINTS = {1: "f530007f6d520cd06b8f5d72c7be8a92b642161cf2e59262403d88fc4d7a2f40"}

LONG = "\n\n".join(f"Paragraph {i}: " + "words " * 60 for i in range(8))
SAMPLES = {
    "02 Concepts/Full — Featured.md": (
        "---\ntype: concept\ncreated: 2024-01-02\ntags:\n  - CS/Graphs\n---\n"
        "## Part of\n- [[Parent MOC]]\n\nIntro with [[A|alias]], [[B#Heading]], [[C#^blk]], "
        "![[Embedded Note]], ![[pic.png]], ![img](Attachments/x.png) and #inline-tag #123.\n"
        "### Section\n> [!note] Callout title\n> callout body [[D]]\n\n"
        "```python\n[[NotALink]] #not-a-tag\n```\n`[[inline]]` <% tp.date.now() %>\n"
        "```dataview\nLIST FROM #x\n```\n### Small\ntiny\n### Big\n" + LONG
    ),
    "01 MOCs/Hub.md": "## Links\n### Group\n- [[One]]\n- [[Two]]\n## Notes\nSome text here.",
    "Root note.md": "No headings at all, just a modest paragraph of text for the window path.",
    "02 Concepts/Stub.md": "tiny",
}


@pytest.fixture(autouse=True)
def pinned(monkeypatch):
    for name, value in {
        "vault_folder_types": {"01 MOCs": "moc", "02 Concepts": "concept"},
        "vault_default_note_type": "fleeting",
        "vault_excluded_dirs": {"Templates"},
        "vault_stripped_fences": {"dataview", "base"},
        "chunk_max_chars": 600,
        "chunk_merge_below_chars": 50,
        "chunk_overlap_chars": 200,
        "stub_min_chars": 10,
        "chunk_metadata_headings": ["Part of"],
    }.items():
        monkeypatch.setattr(settings, name, value)


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def parsed():
    notes = [parse_note(path, text) for path, text in SAMPLES.items()]
    return [[n.path, n.title, n.note_type, n.frontmatter, n.body, n.links, n.tags] for n in notes]


def embedded_texts():
    notes = [parse_note(path, text) for path, text in SAMPLES.items()]
    return [
        passage_text(c.heading_path, c.content) for n in notes for c in chunk_note(n.title, n.body)
    ]


@pytest.mark.parametrize(
    "name, version, fingerprints, output",
    [
        ("PARSE_VERSION", full.PARSE_VERSION, PARSE_FINGERPRINTS, parsed),
        ("EMBED_VERSION", full.EMBED_VERSION, EMBED_FINGERPRINTS, embedded_texts),
    ],
)
def test_output_matches_the_pinned_version(name, version, fingerprints, output):
    assert version == max(fingerprints), (
        f"{name}={version} but the newest pinned is {max(fingerprints)}"
    )
    got = fingerprint(output())
    assert got == fingerprints[version], (
        f"Indexed output changed without a {name} bump: set {name} = {version + 1} in full.py "
        f"and add {version + 1}: {got!r} to {name.split('_')[0]}_FINGERPRINTS here."
    )


def test_samples_exercise_the_rules():
    """The fingerprints are only as good as the samples: make sure they hit the tricky paths."""
    by_path = {p[0]: p for p in parsed()}
    featured = by_path["02 Concepts/Full — Featured.md"]
    assert ["Parent MOC", "link"] in [list(x) for x in featured[5]]
    assert ("Embedded Note", "embed") in featured[5] and "inline-tag" in featured[6]
    texts = embedded_texts()
    assert any(t.startswith("Full — Featured > Big") for t in texts)  # "Part of" not in path
    assert sum(t.startswith("Full — Featured > Big") for t in texts) > 1  # oversize split ran
    assert not any(t.startswith("Stub") for t in texts)  # stub produced no chunks
