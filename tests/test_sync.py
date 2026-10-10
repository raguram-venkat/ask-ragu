"""Incremental sync on a real origin + clone. After every step the DB must equal a fresh full
index at the same commit (Task 8's "Done when"). The embedder is faked but deterministic."""

import subprocess
import threading

import pytest

from ask_ragu import db
from ask_ragu.index import full, sync
from ask_ragu.settings import settings

CAFE = "02 Concepts/Café — Notes.md"  # non-ASCII + spaces: needs -z everywhere
RENAMED = "02 Concepts/Café — Renamed.md"
# Several lines: git's rename detection needs >= 50% similar content, so a tiny note with a
# one-character edit would show up as delete + add instead of R0xx.
CAFE_BODY = "\n---\n" + "".join(f"Line {i} about crema, roast and water.\n" for i in range(8))
CAFE_BODY += "About [[Espresso]] and #brewing"


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
        "chunk_metadata_headings": ["Part of"],
        "vault_fetch": True,
        "vault_ref": "origin/main",
    }.items():
        monkeypatch.setattr(settings, name, value)
    # Deterministic fake vectors, so a re-embed of the same text gives the same row.
    monkeypatch.setattr(full, "embed_passages", lambda ts: [[len(t) % 97 / 100] * 384 for t in ts])


def run(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repos(tmp_path):
    """origin (where 'pushes' happen) and vault (the indexer's clone, fetched by sync)."""
    origin, vault = tmp_path / "origin", tmp_path / "vault"
    origin.mkdir()
    run(origin, "init", "-q", "-b", "main")

    def push(files, amend=False):
        for path, text in files.items():
            f = origin / path
            if text is None:
                f.unlink()
            else:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
        run(origin, "add", "-A")
        args = ["--amend"] if amend else []
        run(origin, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c", *args)

    push({
        CAFE: "---\ntags: [food]" + CAFE_BODY + ".",
        "02 Concepts/Espresso.md": "## Part of\n- [[Coffee]]\n### Shot\nHigh pressure, short.",
        "Templates/T.md": "never indexed",
    })  # fmt: skip
    run(tmp_path, "clone", "-q", str(origin), str(vault))
    return vault, push


def snapshot(conn):
    """Everything except surrogate ids, keyed by path."""
    q = {
        "notes": "SELECT path, title, note_type, frontmatter::text, content_hash FROM notes",
        "chunks": "SELECT n.path, chunk_order, heading_path, content, embedding::text"
        " FROM chunks JOIN notes n ON n.id = note_id",
        "links": "SELECT n.path, raw_target, link_kind FROM note_links JOIN notes n"
        " ON n.id = source_note_id",
        "tags": "SELECT n.path, tag FROM note_tags JOIN notes n ON n.id = note_id",
        "state": "SELECT last_commit FROM index_state",
    }
    return {k: sorted(conn.execute(sql).fetchall()) for k, sql in q.items()}


def assert_equals_full_index(conn, vault):
    incremental = snapshot(conn)
    conn.execute("TRUNCATE notes, index_state CASCADE")
    full.index_full(conn, vault, "origin/main")
    assert snapshot(conn) == incremental
    # leave the DB in the incremental result's state: same content, so continuing is fair


def note_id(conn, path):
    return conn.execute("SELECT id FROM notes WHERE path = %s", (path,)).fetchone()


def test_incremental_sync_matches_full_index(conn, repos):
    vault, push = repos
    db.migrate(conn)

    # Empty index_state -> full index.
    assert sync.sync(conn, vault).mode == "full"
    assert sync.sync(conn, vault).mode == "noop"

    # Add + edit + rename-with-edit (git reports R0xx) + frontmatter-only edit, one commit.
    cafe_id = note_id(conn, CAFE)
    push({
        "02 Concepts/Grinder.md": "Burr grinders crush beans evenly. See [[Espresso]].",
        "02 Concepts/Espresso.md": "## Part of\n- [[Coffee]]\n### Shot\nNine bars, 25 s.",
        CAFE: None,
        RENAMED: "---\ntags: [food]" + CAFE_BODY + "!",
    })  # fmt: skip
    s = sync.sync(conn, vault)
    assert (s.mode, s.renamed, s.deleted) == ("incremental", 1, 0)
    assert note_id(conn, RENAMED) == cafe_id  # rename kept the id
    assert_equals_full_index(conn, vault)

    # Frontmatter-only edit, a move into an excluded folder, and a delete.
    push({
        RENAMED: "---\ntags: [coffee]" + CAFE_BODY + "!",
        "02 Concepts/Grinder.md": None,
        "Templates/Grinder.md": "Burr grinders crush beans evenly. See [[Espresso]].",
        "02 Concepts/Espresso.md": None,
    })  # fmt: skip
    s = sync.sync(conn, vault)
    assert (s.mode, s.deleted, s.embedded) == ("incremental", 2, 0)
    assert_equals_full_index(conn, vault)

    # Force-push: rewrite the last commit; the old last_commit is no longer an ancestor.
    push({"02 Concepts/Late.md": "Written after the rewrite, long enough to index."}, amend=True)
    assert sync.sync(conn, vault).mode == "full"
    assert_equals_full_index(conn, vault)


def test_parses_renames_and_odd_paths(repos):
    vault, push = repos
    old = run(vault, "rev-parse", "HEAD").strip()
    push({CAFE: None, "02 Concepts/Café — Moved.md": "---\ntags: [food]" + CAFE_BODY + "."})
    run(vault, "fetch", "-q")
    assert sync.changes(vault, old, "origin/main") == [("R", CAFE, "02 Concepts/Café — Moved.md")]


# --- D-010: settings hash -------------------------------------------------------------------

EMBED_CHANGES = [  # (setting, new value): each must change content_hash and settings_hash
    ("chunk_max_chars", 1000),
    ("chunk_merge_below_chars", 100),
    ("chunk_overlap_chars", 200),
    ("stub_min_chars", 50),
    ("chunk_metadata_headings", ["Part of", "See also"]),
    ("embedding_model", "other/model"),
    ("embedding_model_file", "onnx/other.onnx"),
    ("embedding_pooling", "mean"),
]
PARSE_CHANGES = [  # must change settings_hash only
    ("vault_folder_types", {"02 Concepts": "source"}),
    ("vault_default_note_type", "meta"),
    ("vault_excluded_dirs", {"Templates", "Bases"}),
    ("vault_stripped_fences", {"dataview"}),
]
RUNTIME_KNOBS = [  # must change neither
    ("embedding_batch_size", 64),
    ("embedding_cache_dir", "elsewhere"),
    ("embedding_query_prefix", "query: "),
    ("vault_ref", "HEAD"),
    ("webhook_secret", "x"),
]


@pytest.mark.parametrize("name, value", EMBED_CHANGES + PARSE_CHANGES + RUNTIME_KNOBS)
def test_settings_hash_covers_exactly_the_index_settings(monkeypatch, name, value):
    note = full.parse_note("02 Concepts/A.md", "Some body text here.")
    before = (full.settings_hash(), full.content_hash(note))
    monkeypatch.setattr(settings, name, value)
    after = (full.settings_hash(), full.content_hash(note))
    in_embed = name in dict(EMBED_CHANGES)
    in_parse = name in dict(PARSE_CHANGES)
    assert (before[0] != after[0], before[1] != after[1]) == (in_embed or in_parse, in_embed)


def test_settings_hash_ignores_set_and_dict_order(monkeypatch):
    monkeypatch.setattr(settings, "vault_excluded_dirs", {"A", "B", "C"})
    a = full.settings_hash()
    monkeypatch.setattr(settings, "vault_excluded_dirs", {"C", "B", "A"})
    assert full.settings_hash() == a


def test_embed_setting_change_forces_full_reembed(conn, repos, monkeypatch):
    vault, _ = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    monkeypatch.setattr(settings, "chunk_max_chars", 1000)
    s = sync.sync(conn, vault)
    assert (s.mode, s.embedded) == ("full", 2)
    assert sync.sync(conn, vault).mode == "noop"  # hash recorded: back to normal


def test_parse_only_change_is_a_full_index_that_embeds_nothing(conn, repos, monkeypatch):
    vault, _ = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    monkeypatch.setattr(settings, "vault_folder_types", {"02 Concepts": "source"})
    s = sync.sync(conn, vault)
    assert (s.mode, s.written, s.embedded) == ("full", 2, 0)
    types = conn.execute("SELECT DISTINCT note_type FROM notes").fetchall()
    assert types == [("source",)]
    assert_equals_full_index(conn, vault)


def test_unchanged_settings_stay_incremental(conn, repos):
    vault, push = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    assert sync.sync(conn, vault).mode == "noop"
    push({"02 Concepts/New.md": "A brand new note with enough text."})
    assert sync.sync(conn, vault).mode == "incremental"


def test_null_settings_hash_means_one_full_index_without_reembedding(conn, repos, caplog):
    vault, _ = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    conn.execute("UPDATE index_state SET settings_hash = NULL")  # = a DB from before 0003
    caplog.set_level("INFO")
    s = sync.sync(conn, vault)
    assert (s.mode, s.written, s.embedded) == ("full", 0, 0)
    assert "before migration 0003" in caplog.text
    assert conn.execute("SELECT settings_hash FROM index_state").fetchone() == (
        full.settings_hash(),
    )


# --- D-010: working tree of the system's clone ------------------------------------------------


def head(repo):
    return run(repo, "rev-parse", "HEAD").strip()


def test_fetch_true_resets_working_tree_to_indexed_commit(conn, repos):
    vault, push = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    push({"02 Concepts/New.md": "A brand new note with enough text."})
    sync.sync(conn, vault)
    indexed = conn.execute("SELECT last_commit FROM index_state").fetchone()[0]
    assert head(vault) == indexed == head(vault.parent / "origin")
    assert (vault / "02 Concepts/New.md").exists()  # files on disk match what was indexed
    assert run(vault, "status", "--porcelain") == ""
    # noop syncs reset too, so a clone that fell behind (fresh clone, earlier failure) catches up
    run(vault, "reset", "-q", "--hard", "HEAD~1")
    assert sync.sync(conn, vault).mode == "noop"
    assert head(vault) == indexed


def test_fetch_false_never_touches_the_working_tree(conn, repos, monkeypatch):
    vault, push = repos
    db.migrate(conn)
    before = head(vault)
    push({"02 Concepts/New.md": "A brand new note with enough text."})
    run(vault, "fetch", "-q")  # someone else fetched; the indexer itself must not move files
    monkeypatch.setattr(settings, "vault_fetch", False)
    sync.sync(conn, vault)
    assert conn.execute("SELECT last_commit FROM index_state").fetchone()[0] != before
    assert head(vault) == before
    assert not (vault / "02 Concepts/New.md").exists()


def test_local_edits_block_the_reset_but_not_the_sync(conn, repos, caplog):
    vault, push = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    (vault / "02 Concepts/Espresso.md").write_text("edited by hand on the VM")
    push({"02 Concepts/New.md": "A brand new note with enough text."})
    s = sync.sync(conn, vault)
    assert s.mode == "incremental"  # the index still moved on
    assert (vault / "02 Concepts/Espresso.md").read_text() == "edited by hand on the VM"
    assert "local edits" in caplog.text


def test_failed_reset_is_a_warning_not_a_failed_sync(conn, repos, monkeypatch, caplog):
    vault, push = repos
    db.migrate(conn)
    real_git = sync.git

    def git(v, *args):
        if args[:1] == ("reset",):
            raise subprocess.CalledProcessError(1, "git reset", stderr="read-only file system")
        return real_git(v, *args)

    monkeypatch.setattr(sync, "git", git)
    s = sync.sync(conn, vault)
    assert s.mode == "full"
    assert "could not reset" in caplog.text and "read-only" in caplog.text


# --- ADR-0017: code versions ----------------------------------------------------------------


def test_parse_version_bump_rewrites_links_without_reembedding(conn, repos, monkeypatch):
    vault, _ = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    real_parse = full.parse_note

    def new_parser(path, text):  # a parser change that only alters link extraction
        note = real_parse(path, text)
        note.links = [*note.links, ("Extra", "link")]
        return note

    monkeypatch.setattr(full, "parse_note", new_parser)
    monkeypatch.setattr(full, "PARSE_VERSION", full.PARSE_VERSION + 1)
    s = sync.sync(conn, vault)
    assert (s.mode, s.written, s.embedded) == ("full", 2, 0)
    extra = conn.execute("SELECT count(*) FROM note_links WHERE raw_target = 'Extra'").fetchone()
    assert extra == (2,)
    assert conn.execute("SELECT parse_version FROM index_state").fetchone() == (full.PARSE_VERSION,)


def test_embed_version_bump_reembeds_everything(conn, repos, monkeypatch, caplog):
    vault, _ = repos
    db.migrate(conn)
    sync.sync(conn, vault)
    monkeypatch.setattr(full, "EMBED_VERSION", full.EMBED_VERSION + 1)
    caplog.set_level("INFO")
    s = sync.sync(conn, vault)
    assert (s.mode, s.embedded) == ("full", 2)
    assert f"embed code version 1 -> {full.EMBED_VERSION}" in caplog.text


# --- ADR-0018: one sync at a time per index -------------------------------------------------


def test_second_sync_waits_for_the_first(conn, repos, connect):
    vault, _ = repos
    db.migrate(conn)
    other = connect()  # e.g. the CLI while the app syncs
    done = threading.Event()
    with sync.sync_lock(conn):  # "the app" is mid-sync
        t = threading.Thread(target=lambda: (sync.sync(other, vault), done.set()))
        t.start()
        assert not done.wait(0.5)  # queued behind the lock, not running alongside
    assert done.wait(10)  # runs as soon as the lock is free
    t.join()
    assert conn.execute("SELECT last_commit FROM index_state").fetchone() is not None


def test_a_dead_holder_cannot_leave_the_lock_stuck(conn, connect):
    holder = connect()
    (key,) = holder.execute(sync.LOCK_KEY).fetchone()
    holder.execute("SELECT pg_advisory_lock(%s)", (key,))
    assert conn.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone() == (False,)
    holder.close()  # crash: no unlock ever runs
    assert conn.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone() == (True,)
    conn.execute("SELECT pg_advisory_unlock(%s)", (key,))


def test_other_schemas_have_their_own_lock(conn, connect):
    conn.execute("CREATE SCHEMA IF NOT EXISTS lock_other")
    try:
        other = connect("lock_other")  # e.g. a Sprint 4 experiment index
        with sync.sync_lock(conn):
            (key,) = other.execute(sync.LOCK_KEY).fetchone()
            assert other.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone() == (True,)
            other.execute("SELECT pg_advisory_unlock(%s)", (key,))
    finally:
        conn.execute("DROP SCHEMA lock_other CASCADE")


def test_links_are_re_resolved_across_the_vault_every_sync(conn, repos):
    """Unchanged notes' links follow renames, deletes and new notes (Sprint 3 Task 1)."""
    vault, push = repos
    db.migrate(conn)

    def targets():
        rows = conn.execute(
            "SELECT s.path, l.raw_target, t.path FROM note_links l"
            " JOIN notes s ON s.id = l.source_note_id LEFT JOIN notes t ON t.id = l.target_note_id"
        ).fetchall()
        return {(src, raw): dst for src, raw, dst in rows}

    sync.sync(conn, vault)
    espresso = "02 Concepts/Espresso.md"
    assert targets() == {(CAFE, "Espresso"): espresso, (espresso, "Coffee"): None}

    # A new note fixes a dangling link in a note that didn't change.
    push({"Coffee.md": "The drink, in general terms."})
    sync.sync(conn, vault)
    assert targets()[(espresso, "Coffee")] == "Coffee.md"

    # A rename outside Obsidian breaks the link; deleting the target leaves it dangling too.
    run(vault.parent / "origin", "mv", espresso, "02 Concepts/Ristretto.md")
    push({"Coffee.md": None})
    sync.sync(conn, vault)
    assert targets() == {(CAFE, "Espresso"): None, ("02 Concepts/Ristretto.md", "Coffee"): None}
