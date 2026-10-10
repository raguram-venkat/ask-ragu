"""Link resolution rules (Sprint 3 Task 1): as Obsidian resolves them, plus the alias fallback."""

import logging
import unicodedata

import pytest

from ask_ragu.graph.resolve import resolver

NOTES = [
    ("root", "Note.md", {}),
    ("deep", "02 Concepts/Sub/Note.md", {}),
    ("cafe", "02 Concepts/Café.md", {}),  # NFC on disk
    ("water", "02 Concepts/Water Chemistry.md", {"aliases": ["WC", "Brew water"]}),
    ("tamp", "02 Concepts/Tamping.md", {"aliases": "TP"}),  # a single string
    ("wc2", "05 Fleeting/Water log.md", {"aliases": ["WC"]}),  # alias collision
    ("shadow", "02 Concepts/Shadow.md", {"aliases": ["Note"]}),  # alias vs a real filename
]


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Note", "root"),  # same name in two folders: nearest the root wins
        ("Sub/Note", "deep"),  # the path in the link picks the other one
        ("02 Concepts/Sub/Note", "deep"),
        ("02 Concepts/Sub/Note.md", "deep"),
        ("note", "root"),  # case-insensitive
        ("  NOTE ", "root"),
        ("Other/Note", None),  # a path that doesn't exist doesn't fall back to the name
        (unicodedata.normalize("NFD", "café"), "cafe"),  # macOS-style decomposed accent
        ("tp", "tamp"),  # alias, case-insensitive, string form
        ("brew water", "water"),
        ("Missing", None),  # dangling
        ("Sub", None),  # a folder is not a note
    ],
)
def test_resolves_like_obsidian(raw, expected):
    assert resolver(NOTES)(raw) == expected


def test_alias_collision_is_deterministic_and_warns(caplog):
    with caplog.at_level(logging.WARNING):
        # "02 Concepts/..." and "05 Fleeting/..." are equally deep: alphabetical path decides.
        assert resolver(NOTES)("WC") == "water"
        assert resolver(list(reversed(NOTES)))("WC") == "water"  # not input order
    assert "matches 2 notes" in caplog.text


def test_shared_name_also_warns(caplog):
    with caplog.at_level(logging.WARNING):
        resolver(NOTES)("Note")
    assert "matches 2 notes" in caplog.text
