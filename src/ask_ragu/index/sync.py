"""Incremental sync (SPEC §8 steps 2-8, ADR-0004): git diff last_commit..target -> DB.

Falls back to a full index when a diff can't be trusted: empty index_state, index settings
changed in .env (settings_hash, D-010), or last_commit no longer in the target's history
(force-push, rewritten history). On the VM the clone's files are then reset to the indexed commit.
Ends in the same DB state as a full index at the target commit (tests/test_sync.py checks it).
"""

import logging
import subprocess
from contextlib import contextmanager
from pathlib import Path

import psycopg

from ask_ragu import db
from ask_ragu.index import full
from ask_ragu.index.full import (
    Stats,
    git,
    git_cmd,
    index_full,
    index_paths,
    record_state,
    settings_hash,
)
from ask_ragu.index.parse import is_indexable
from ask_ragu.index.runner import SyncRunner
from ask_ragu.settings import settings

log = logging.getLogger(__name__)


def target_commit(vault: Path) -> str:
    """The commit to index: VAULT_REF after an optional fetch (VM: fetch + origin/main)."""
    if settings.vault_fetch:
        git(vault, "fetch", "--quiet", "--prune", "origin")
    return git(vault, "rev-parse", f"{settings.vault_ref}^{{commit}}").strip()


def _is_ancestor(vault: Path, old: str, new: str) -> bool:
    # Exit 0 = ancestor, 1 = not; anything else (e.g. old commit gone after a force-push) = not.
    cmd = git_cmd(vault, "merge-base", "--is-ancestor", old, new)
    return subprocess.run(cmd, capture_output=True).returncode == 0


def changes(vault: Path, old: str, new: str) -> list[tuple[str, str, str]]:
    """(status, path, new_path) per changed file; new_path == path except for renames/copies."""
    # -z: NUL-separated fields, paths unquoted (spaces, unicode). Renames: "R087\0old\0new".
    out = git(vault, "diff", "--name-status", "-z", "--find-renames", old, new).split("\0")
    result, i = [], 0
    while i < len(out) - 1:
        status = out[i]
        if status[0] in "RC":
            result.append((status[0], out[i + 1], out[i + 2]))
            i += 3
        else:
            result.append((status[0], out[i + 1], out[i + 1]))
            i += 2
    return result


# One lock per schema (= per index): syncs on the same index queue up, whichever process starts
# them; experiments in other schemas (Sprint 4 ablation) and tests never block the real index.
LOCK_KEY = "SELECT hashtext('ask_ragu.sync:' || current_schema())"


@contextmanager
def sync_lock(conn: psycopg.Connection):
    """Session-level Postgres advisory lock (ADR-0018). Released at the end, or by Postgres itself
    when the holder's connection closes (crash, kill), so it can't go stale."""
    (key,) = conn.execute(LOCK_KEY).fetchone()
    if not conn.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone()[0]:
        log.info("another sync holds the lock; waiting for it to finish")
        conn.execute("SELECT pg_advisory_lock(%s)", (key,))  # no timeout: wait out a full index
    try:
        yield
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", (key,))


def sync(conn: psycopg.Connection, vault: Path, full: bool = False) -> Stats:
    """Bring the DB to the target commit; `full` forces a full index (`askragu index --full`).

    Everything — fetch, diff, index, state, working tree — runs under the lock, so two syncs
    never interleave. The target is read after the lock is taken: a sync that waited goes
    straight to whatever is newest by then.
    """
    with sync_lock(conn):
        target = target_commit(vault)
        stats = _sync_to(conn, vault, target, full)
        if settings.vault_fetch:  # the system's own clone (VM); never the laptop's working clone
            _update_working_tree(vault, target)
        return stats


def _full_index_reason(conn: psycopg.Connection, vault: Path, target: str) -> str | None:
    row = conn.execute(
        "SELECT last_commit, settings_hash, embedding_model, embed_version, parse_version"
        " FROM index_state"
    ).fetchone()
    last, stored_hash, model, embed_v, parse_v = row if row else (None,) * 5
    if last is None:
        return "no index yet"
    if stored_hash is None:
        return "no settings hash recorded (index built before migration 0003)"
    if stored_hash != settings_hash():
        # Name what changed when the readable columns can tell; otherwise it was a .env setting.
        changed = [
            f"{what} {old} -> {new}"
            for what, old, new in [
                ("model", model, settings.embedding_model),
                ("embed code version", embed_v, full.EMBED_VERSION),
                ("parse code version", parse_v, full.PARSE_VERSION),
            ]
            if old != new
        ]
        return "index settings changed: " + (", ".join(changed) or "a .env index setting")
    if not _is_ancestor(vault, last, target):
        return f"{last[:12]} is not an ancestor of {target[:12]} (force-push or rewritten history)"
    return None


def _sync_to(conn: psycopg.Connection, vault: Path, target: str, full: bool) -> Stats:
    reason = "--full requested" if full else _full_index_reason(conn, vault, target)
    if reason:
        log.info("full index: %s", reason)
        return index_full(conn, vault, target)
    last = conn.execute("SELECT last_commit FROM index_state").fetchone()[0]
    if last == target:
        log.info("sync: already at %s", target[:12])
        return Stats(mode="noop")
    try:
        return _apply_diff(conn, vault, last, target)
    except (psycopg.Error, subprocess.CalledProcessError):
        # The index is disposable (ADR-0011): a full index repairs whatever the diff tripped on,
        # instead of failing on the same diff at every retry.
        log.exception("incremental sync failed; falling back to a full index")
        return index_full(conn, vault, target)


def _update_working_tree(vault: Path, commit: str) -> None:
    """Make the clone's files match the commit just indexed (D-010).

    The indexer reads git objects, so the index is already right without this; it's for anyone
    (or anything) reading the files on the VM. Runs only after a successful sync, and only when
    VAULT_FETCH says the clone belongs to the system. Never fails the sync.
    """
    try:
        # Tracked files edited in place mean someone uses this clone by hand: don't wipe that.
        if git(vault, "--no-optional-locks", "status", "--porcelain", "--untracked-files=no"):
            log.warning(
                "vault has local edits to tracked files; not resetting it to %s", commit[:12]
            )
            return
        git(vault, "reset", "--hard", "--quiet", commit)
    except (subprocess.CalledProcessError, OSError) as e:
        detail = e.stderr.strip() if isinstance(e, subprocess.CalledProcessError) else e
        log.warning("could not reset vault working tree to %s: %s", commit[:12], detail)


def _apply_diff(conn: psycopg.Connection, vault: Path, last: str, target: str) -> Stats:
    stats, upserts, deletes = Stats(mode="incremental"), [], []
    with conn.transaction():
        for status, path, new_path in changes(vault, last, target):
            if status == "D":
                deletes.append(path)
            elif status == "R" and is_indexable(path) and is_indexable(new_path):
                # Rename: move the row, keeping its id (and later its graph edges).
                conn.execute("UPDATE notes SET path = %s WHERE path = %s", (new_path, path))
                stats.renamed += 1
                upserts.append(new_path)  # title/body may have changed with it
            else:  # A, M, T, C, or a rename into/out of an excluded folder
                if status == "R":
                    deletes.append(path)
                upserts.append(new_path)
        stats.deleted = conn.execute(
            "DELETE FROM notes WHERE path = ANY(%s)", ([p for p in deletes if is_indexable(p)],)
        ).rowcount

    index_paths(conn, vault, target, upserts, stats)
    record_state(conn, target)  # last: a crash before this re-applies the same diff next time
    log.info("sync %s..%s: %s", last[:12], target[:12], stats)
    return stats


def _run() -> Stats:
    with db.connect() as conn:
        return sync(conn, settings.vault_path)


runner = SyncRunner(_run)  # shared by the webhook, startup reconciliation, and /index/status
