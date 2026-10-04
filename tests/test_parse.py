import pytest

from ask_ragu.index.parse import is_indexable, parse_note
from ask_ragu.settings import settings


@pytest.fixture(autouse=True)
def vault_rules(monkeypatch):
    """Pin the vault rules so tests don't depend on what .env currently says."""
    for name, value in {
        "vault_folder_types": {"01 MOCs": "moc", "02 Concepts": "concept"},
        "vault_default_note_type": "fleeting",
        "vault_excluded_dirs": {"Templates", "Bases", "Attachments"},
        "vault_stripped_fences": {"dataview", "dataviewjs", "base"},
    }.items():
        monkeypatch.setattr(settings, name, value)


def parse(body, path="02 Concepts/Note.md"):
    return parse_note(path, body)


@pytest.mark.parametrize(
    "path, ok",
    [
        ("02 Concepts/A.md", True),
        ("02 Concepts/Sub/A.md", True),
        ("Root.md", True),
        ("Templates/T.md", False),
        ("Bases/B.md", False),
        ("Attachments/x.md", False),
        (".obsidian/x.md", False),
        ("02 Concepts/.hidden/A.md", False),
        ("02 Concepts/A.png", False),
        ("02 Concepts/A.md.bak", False),
    ],
)
def test_exclusions(path, ok):
    assert is_indexable(path) is ok


def test_note_type_and_title_from_path():
    assert parse("x", "01 MOCs/Hub.md").note_type == "moc"
    assert parse("x", "02 Concepts/Sub/Deep.md").note_type == "concept"
    n = parse("x", "Inbox.md")
    assert (n.title, n.note_type) == ("Inbox", "fleeting")


def test_frontmatter_parsed_and_json_safe():
    n = parse("---\ntype: concept\ncreated: 2024-01-02\ntags:\n  - CS/Graphs\n---\nBody")
    assert n.frontmatter == {"type": "concept", "created": "2024-01-02", "tags": ["CS/Graphs"]}
    assert n.tags == ["cs/graphs"]
    assert n.body == "Body"


def test_malformed_frontmatter_warns_and_keeps_body(caplog):
    n = parse("---\ntags: [unclosed\n---\nStill here")
    assert n.frontmatter == {}
    assert n.body == "Still here"
    assert "malformed frontmatter" in caplog.text


def test_no_frontmatter_and_unclosed_dashes():
    assert parse("Just text").frontmatter == {}
    assert parse("---\nno closing fence").body == "---\nno closing fence"


@pytest.mark.parametrize(
    "md, links, text",
    [
        ("[[Note]]", [("Note", "link")], "Note"),
        ("[[Note|shown]]", [("Note", "link")], "shown"),
        ("[[Note#Heading]]", [("Note", "link")], "Note > Heading"),
        ("[[Note#^abc123]]", [("Note", "link")], "Note"),
        ("[[Folder/Note]]", [("Folder/Note", "link")], "Folder/Note"),
        ("![[Note]]", [("Note", "embed")], "Note"),
        ("![[x.png]]", [], ""),
        ("![[x.PNG|200]]", [], ""),
        ("![alt](Attachments/x.png)", [], ""),
        ("[[#Local heading]]", [], "Local heading"),
        ("[[A]] and [[A|again]]", [("A", "link")], "A and again"),
    ],
)
def test_link_variants(md, links, text):
    n = parse(md)
    assert n.links == links
    assert n.body == text


def test_no_links_or_tags_from_code():
    n = parse("```python\n[[InFence]] #infence\n```\n`[[Inline]] #inline` [[Real]]")
    assert n.links == [("Real", "link")]
    assert n.tags == []
    assert "[[InFence]]" in n.body and "`[[Inline]] #inline`" in n.body


def test_tilde_fence_and_longer_closing_fence():
    n = parse("~~~\n[[In]]\n~~~~\n[[Out]]")
    assert n.links == [("Out", "link")]


@pytest.mark.parametrize(
    "md, tags",
    [
        ("#tag and #Nested/Tag-2", ["tag", "nested/tag-2"]),
        ("# Heading", []),
        ("## Heading with #tag", ["tag"]),
        ("#123 is an issue number", []),
        ("#y2024 is a tag", ["y2024"]),
        ("see https://x.com/page#frag and [l](u#frag) and [[N#H]]", []),
        ("a&#35;b", []),
    ],
)
def test_tags(md, tags):
    assert parse(md).tags == tags


def test_frontmatter_tag_formats():
    assert parse("---\ntags: a, b\n---\n").tags == ["a", "b"]
    assert parse("---\ntags: a, #b\n---\n").tags == ["a"]  # YAML: " #" starts a comment
    assert parse("---\ntags: '#a'\n---\n").tags == ["a"]
    assert parse("---\ntags: [a, b]\n---\n").tags == ["a", "b"]
    assert parse("---\ntags:\n---\n").tags == []


def test_dataview_base_and_templater_stripped():
    md = (
        "Keep\n```dataview\nLIST FROM #x\n```\n```base\nfilters: []\n```\nDate <% tp.date.now() %>!"
    )
    n = parse(md)
    assert n.body == "Keep\nDate !"
    assert n.tags == []


def test_callout_unwrapped_blockquote_kept():
    md = "> [!note] Title here\n> body [[L]]\n>\n> more\n\n> plain quote"
    n = parse(md)
    assert n.body == "Title here\nbody L\n\nmore\n\n> plain quote"
    assert n.links == [("L", "link")]
    assert parse("> [!tip]-\n> folded").body == "folded"
