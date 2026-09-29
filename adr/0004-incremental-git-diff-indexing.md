# ADR-0004: Incremental git-diff indexing over full reindex per push

Status: accepted
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

Most pushes change a handful of notes; embedding the whole vault on ARM CPU takes minutes.

## Decision

Diff `last_indexed_commit..HEAD` with rename detection and apply adds, modifies, deletes, renames. Full index only on first run or when history was rewritten.

## Alternatives considered

- Full reindex every push — simplest and always correct, but cost scales with vault size, not change size.
- File mtimes — unreliable across git checkouts.

## Consequences

- Renames keep note ids (and links) instead of delete + insert.
- Force-push must be detected (last commit missing or not an ancestor) and fall back to full.
- Correctness is testable: incremental result must equal full-index result.
