# ADR-0019: Lexical query = the question's own lexemes OR-ed, not websearch_to_tsquery

Status: accepted
Date: 2026-10-10
Sprint: sprint-4 (task_1)

## Context

Lexical search gets natural-language questions, not search syntax. `websearch_to_tsquery` ANDs every word, so a chunk must contain every non-stopword of the question. Tried on the real vault with 5 made-up questions (not the eval set): 0 matches for all 5.

## Decision

Build the query in SQL from the question's lexemes: `to_tsvector('english', question)` → each lexeme quoted as a tsquery literal → joined with `|` → cast to tsquery (no re-parsing). Rank with `ts_rank_cd`, which favours more matches and heading matches (A 1.0 vs body B 0.4 per match), with ties broken by chunk id. A GIN index on `chunks.tsv` (migration 0005) brings real-vault p50 to 8 ms and p95 to 18 ms.

## Alternatives considered

- `websearch_to_tsquery` (the task's plan): AND semantics, 0 matches for natural questions. It also turns `-word`, quotes and `or` in user input into search syntax.
- Words split with `\w+` and joined by `or` into `websearch_to_tsquery`: splits tokens the index keeps whole (`node.js`, URLs, file names), so they never match.
- BM25-style scoring with IDF: not built yet. `ts_rank_cd` has no IDF, so a common word like "difference" counts as much as a rare proper name. Whether that hurts once vector search and RRF are added is for the Task 5 ablation to show, on the owner's rewritten eval set, not on guesses (BACKLOG).

## Consequences

- Any input is safe: no errors, no injection, no notices. Empty, stopword-only and punctuation-only questions return nothing.
- OR matches many chunks (30% of the vault for a generic question), so precision rests on ranking and on fusion with vector search.
- Lexemes are exactly the indexed ones, including the English stemmer's quirks ("competes" → compet, "competition" → competit).
