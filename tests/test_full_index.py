"""Full index against a throwaway git vault. The embedder is faked: these tests are about the DB."""

import subprocess

import pytest

from ask_ragu import db
from ask_ragu.index import full
from ask_ragu.settings import settings

CAFE = "02 Concepts/Café — Notes.md"  # non-ASCII path: git quotes it unless -z
CAFE_BODY = "\n---\nBody about [[Espresso]] and #brewing."


@pytest.fixture(autouse=True)
def rules(monkeypatch):
    for name, value in {
        "vault_folder_types": {"02 Concepts": "concept"},
        "vault_default_note_type": "fleeting",
        "vault_excluded_dirs": {"Templates"},
        "vault_stripped_fences": set(),
        "chunk_max_chars": 1500,
        "chunk_merge_below_chars": 200,
        "chunk_overlap_chars": 300,
        "stub_min_chars": 10,
    }.items():
        monkeypatch.setattr(settings, name, value)


@pytest.fixture
def embedded(monkeypatch):
    """Fake embedder; the list records how many texts each call embedded."""
    calls = []

    def fake(texts):
        calls.append(len(texts))
        return [[0.1] * 384 for _ in texts]

    monkeypatch.setattr(full, "embed_passages", fake)
    return calls


@pytest.fixture
def vault(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    def commit(files):
        for path, text in files.items():
            f = tmp_path / path
            if text is None:
                f.unlink()
            else:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c")

    git("init", "-q")
    commit(
        {
            CAFE: "---\ntags: [food]" + CAFE_BODY,
            "02 Concepts/Espresso.md": "## Shot\nHigh pressure, short extraction.",
            "Templates/T.md": "never indexed",
            "Attachments/x.png": "not a note",
        }
    )
    return tmp_path, commit  # vault path, commit({path: text | None})


def rows(conn, sql):
    return conn.execute(sql).fetchall()


def test_full_index_lifecycle(conn, vault, embedded):
    vault, commit = vault
    db.migrate(conn)

    s = full.index_full(conn, vault)
    assert (s.notes, s.written, s.embedded, s.deleted) == (2, 2, 2, 0)
    assert rows(conn, "SELECT path, note_type FROM notes ORDER BY path") == [
        (CAFE, "concept"),
        ("02 Concepts/Espresso.md", "concept"),
    ]
    assert rows(conn, "SELECT raw_target, target_note_id FROM note_links") == [("Espresso", None)]
    assert rows(conn, "SELECT tag FROM note_tags ORDER BY tag") == [("brewing",), ("food",)]
    head = subprocess.run(["git", "-C", str(vault), "rev-parse", "HEAD"], capture_output=True)
    assert rows(conn, "SELECT last_commit FROM index_state") == [(head.stdout.decode().strip(),)]

    # Same commit again: nothing written, nothing embedded.
    embedded.clear()
    s = full.index_full(conn, vault)
    assert (s.written, s.embedded, embedded) == (0, 0, [])

    # Frontmatter-only edit: row, tags rewritten; no re-embedding (SPEC §8 step 4).
    commit({CAFE: "---\ntags: [coffee]" + CAFE_BODY})
    s = full.index_full(conn, vault)
    assert (s.written, s.embedded) == (1, 0)
    assert rows(conn, "SELECT tag FROM note_tags ORDER BY tag") == [("brewing",), ("coffee",)]

    # Body edit: re-embedded, chunks replaced, note id kept.
    (before,) = rows(conn, "SELECT id FROM notes WHERE path LIKE '%Espresso%'")
    commit({"02 Concepts/Espresso.md": "## Shot\nNine bars of pressure, 25 seconds."})
    s = full.index_full(conn, vault)
    assert (s.written, s.embedded) == (1, 1)
    assert rows(conn, "SELECT id FROM notes WHERE path LIKE '%Espresso%'") == [before]
    sql = "SELECT content FROM chunks JOIN notes n ON n.id = note_id WHERE n.path LIKE '%Espr%'"
    assert rows(conn, sql) == [("Nine bars of pressure, 25 seconds.",)]

    # Deleted file: note and everything hanging off it gone.
    commit({CAFE: None})
    s = full.index_full(conn, vault)
    assert s.deleted == 1
    assert rows(conn, "SELECT count(*) FROM note_tags") == [(0,)]


def test_changed_chunk_setting_re_embeds_everything(conn, vault, embedded, monkeypatch):
    vault, _ = vault
    db.migrate(conn)
    full.index_full(conn, vault)
    monkeypatch.setattr(settings, "chunk_max_chars", 1000)
    assert full.index_full(conn, vault).embedded == 2
