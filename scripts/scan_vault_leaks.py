"""Vault-title leak scan for the public repo (ADR-0022). Prints locations and counts, never titles.

    uv run python scripts/scan_vault_leaks.py         # before a commit: changes vs HEAD + untracked
    uv run python scripts/scan_vault_leaks.py --push  # before a push: all tracked files + every
                                                      # commit not on origin/main
Titles come from the real index (TEST_DATABASE_URL in .env, like bench_expansion.py). A hit is a
title as a whole word, case-insensitive. Common-word titles give false positives: look at each
reported line yourself; titles that are generic words (Docker, Python, …) go one per line in
scripts/scan_allow.private.txt (gitignored: it's vault titles too) and are skipped.
Exit 1 if anything matched, so it can gate a commit or push.
"""

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import dotenv_values

HUNK = re.compile(r"^@@ -\S+ \+(\d+)")
ALLOW = Path(__file__).parent / "scan_allow.private.txt"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def added_lines(diff: str) -> list[tuple[str, str]]:
    """(path:line, text) for each '+' line of a unified diff with -U0 (commit headers kept)."""
    out, commit, path, n = [], "", "?", 0
    for line in diff.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1][:12] + " "
        elif line.startswith("+++ "):
            path = line.removeprefix("+++ ").removeprefix("b/")
        elif m := HUNK.match(line):
            n = int(m.group(1))
        elif line.startswith("+"):
            out.append((f"{commit}{path}:{n}", line[1:]))
            n += 1
    return out


def file_lines(paths: list[str]) -> list[tuple[str, str]]:
    out = []
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                out += [(f"{p}:{i}", t) for i, t in enumerate(f, 1)]
        except (IsADirectoryError, FileNotFoundError):
            pass  # submodule dir, or deleted but still listed
    return out


def matcher(titles: list[str]) -> re.Pattern:
    alts = sorted({re.escape(t.strip()) for t in titles if t.strip()}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


def scan(lines: list[tuple[str, str]], pattern: re.Pattern) -> Counter:
    return Counter({where: n for where, text in lines if (n := len(pattern.findall(text)))})


def main() -> None:
    push = "--push" in sys.argv[1:]
    url = dotenv_values(".env")["TEST_DATABASE_URL"]
    with psycopg.connect(url) as conn:
        titles = [t for (t,) in conn.execute("SELECT title FROM notes")]
    allow = {a.strip().lower() for a in ALLOW.read_text().splitlines()} if ALLOW.exists() else set()
    titles = [t for t in titles if t.strip().lower() not in allow]
    if push:
        lines = file_lines(git("ls-files").splitlines())
        lines += added_lines(git("log", "-p", "-U0", "--format=commit %H", "origin/main..HEAD"))
    else:
        lines = added_lines(git("diff", "-U0", "HEAD"))
        lines += file_lines(git("ls-files", "--others", "--exclude-standard").splitlines())
    hits = scan(lines, matcher(titles))
    for where, n in sorted(hits.items()):
        print(f"{where}  ({n} match{'es' if n > 1 else ''})")
    print(f"{len(titles)} titles ({len(allow)} allowed), {len(lines)} lines, {len(hits)} hits")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
