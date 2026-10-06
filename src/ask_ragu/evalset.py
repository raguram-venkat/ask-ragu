"""Eval set v0 (SPEC §12): load and check the questions file against a vault clone.

  uv run python -m ask_ragu.evalset eval/questions.private.yaml [vault-path]

Errors (exit 1): bad schema, gold paths missing or not indexable at the vault's HEAD, a `hop`
whose `via` note doesn't link to its other gold notes, too few questions of a required kind.
Warnings: drafts not yet reviewed, more than 20 questions, no overview question.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import yaml

from ask_ragu.index.full import git, read_blobs
from ask_ragu.index.parse import is_indexable, parse_note
from ask_ragu.settings import settings

KINDS = {"single", "hop", "overview", "unanswerable"}
MINIMUM = {"total": 15, "hop": 4, "unanswerable": 2}  # Task 9 "Done when" + its approach


@dataclass
class Question:
    id: str
    kind: str
    question: str
    gold: list[str]
    via: str | None = None
    origin: str = "owner"


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load(path: Path) -> list[Question]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Question(**q) for q in data["questions"]]


def check(questions: list[Question], vault: Path, commit: str = "HEAD") -> Report:
    r = Report()
    tree = {p for p in git(vault, "ls-tree", "-r", "-z", "--name-only", commit).split("\0") if p}
    seen = set()
    for q in questions:
        where = f"{q.id}:"
        if q.id in seen:
            r.errors.append(f"{where} duplicate id")
        seen.add(q.id)
        if q.kind not in KINDS:
            r.errors.append(f"{where} kind {q.kind!r} not in {sorted(KINDS)}")
        if not q.question.strip():
            r.errors.append(f"{where} empty question")
        if (q.kind == "unanswerable") != (not q.gold):
            r.errors.append(f"{where} gold must be empty exactly when kind is unanswerable")
        for p in q.gold:
            if p not in tree:
                r.errors.append(f"{where} gold {p!r} not in the vault at {commit}")
            elif not is_indexable(p):
                r.errors.append(f"{where} gold {p!r} is excluded from the index")
        if q.kind == "hop":
            _check_hop(q, vault, commit, tree, r)
        if q.origin == "draft":
            r.warnings.append(f"{where} still a draft: rewrite it in your words or drop it")

    kinds = [q.kind for q in questions]
    for kind, need in MINIMUM.items():
        have = len(kinds) if kind == "total" else kinds.count(kind)
        if have < need:
            r.errors.append(f"need at least {need} {kind} questions, have {have}")
    if len(kinds) > 20:
        r.warnings.append(f"{len(kinds)} questions; SPEC §12 suggests 15-20")
    if "overview" not in kinds:
        r.warnings.append("no overview (MOC-level) question")
    return r


def _check_hop(q: Question, vault: Path, commit: str, tree: set[str], r: Report) -> None:
    if not q.via or q.via not in q.gold or len(q.gold) < 2:
        r.errors.append(f"{q.id}: hop needs `via` in gold plus at least one linked note")
        return
    if q.via not in tree:
        return  # already reported as a missing gold path
    links = parse_note(q.via, read_blobs(vault, commit, [q.via])[q.via]).links
    # Link targets are titles (maybe with a folder): compare case-insensitively by name.
    targets = {PurePosixPath(t).name.lower() for t, _ in links}
    for p in q.gold:
        if p != q.via and PurePosixPath(p).stem.lower() not in targets:
            r.errors.append(f"{q.id}: {q.via!r} doesn't link to {p!r}, so it isn't a hop")


def main(argv: list[str]) -> int:
    path = Path(argv[0])
    vault = Path(argv[1]) if len(argv) > 1 else settings.vault_path
    questions = load(path)
    r = check(questions, vault)
    for w in r.warnings:
        print("warning:", w)
    for e in r.errors:
        print("error:", e)
    kinds = {k: [q.kind for q in questions].count(k) for k in sorted(KINDS)}
    print(f"{len(questions)} questions {kinds}: {'OK' if not r.errors else 'FAILED'}")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
