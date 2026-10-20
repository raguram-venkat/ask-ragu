# Task 4 — Expansion, scoring & context assembly

Status: done 2026-10-19 (owner review pending commit) — end-to-end hit@k waits for the owner's eval rewrite (D-003)
Est: 90m
Spec: SPEC.md §9 steps 3-7 · D-006, D-007

What: Expand seed notes via Sprint 3, take each expanded note's best chunk for the question, score, dedupe, and pack into a token budget with provenance.

Approach: Seeds keep fused scores; expanded notes score similarity × hop decay × note_type prior; MOC chunks dropped; tokens ≈ chars/4 with a margin; budget is a parameter (per provider in Sprint 5).

Read first:

- SPEC §9
- Liu et al. 2023 "Lost in the Middle" (abstract + figures)

Watch out for:

- Expanded notes can crowd out direct hits — cap their share of the budget (e.g. ≤ 40%).
- Same chunk reached as seed and neighbour: keep once, label it direct.
- Put the strongest context first.

ADR:

- [ADR-0023](../adr/0023-retrieval-meta-vars-are-config.md) — `EXPANDED_BUDGET_SHARE`,
  `CHARS_PER_TOKEN` (from this task), and `RRF_K`, `TOP_K` (from Task 3) moved from
  code constants to `.env` settings. Linked so the task file stays self-contained.

Done when: Returns a context object with provenance for every eval question.

---

Filled in while working

Files touched:

- `src/ask_ragu/retrieval/assemble.py` — `assemble_context(conn, fused_seeds, query_vector, token_budget) -> [ContextChunk]`; seeds pack first, expanded capped at 40% of budget; MOCs excluded; dedup by chunk_id; provenance per chunk
- `tests/test_assemble.py` — 7 tests: seeds+expanded present, MOC excluded, dedup, token budget, expanded 40% cap, empty seeds, score formula (all use seed/MOC/expanded setup with links via a MOC hub)
- `src/ask_ragu/settings.py`, `.env.example` — added `RETRIEVAL_HOP_DECAY_HOP1`, `RETRIEVAL_HOP_DECAY_HOP2`, `RETRIEVAL_RRF_K`, `RETRIEVAL_SEED_TOP_K`, `RETRIEVAL_EXPANDED_BUDGET_SHARE`, `RETRIEVAL_CHARS_PER_TOKEN`
- `adr/0023-retrieval-meta-vars-are-config.md` — decision record for moving retrieval constants to `.env`

Decisions made here:

- Seeds keep their RRF scores from Task 3; expanded notes score cosine × hop_decay × note_type_prior. The two score types are on incomparable scales, so they are NOT merged into one ranking — seeds pack first (direct hits, strongest), expanded fill the remainder up to 40% of the budget. This avoids score normalization and respects "put the strongest context first."
- hop_decay as two settings (0.8 for hop-1, 0.6 for hop-2): hop-1 > hop-2 as SPEC requires. Both placeholder, to be swept on eval.
- note_type_prior hardcoded: fleeting=0.5, meta=0.5, concept/source=1.0. Not a setting — it's a structural decision (D-006), not a tuning knob.
- MOCs excluded at two layers: the best-chunk SQL filters `note_type != 'moc'`, and expand.py already returns `is_moc` results that are filtered before best-chunk lookup.
- Tokens ≈ chars/4, the standard rule of thumb — already a conservative margin for English. No extra buffer factor. `CHARS_PER_TOKEN` is now a setting (`RETRIEVAL_CHARS_PER_TOKEN`) per ADR-0023, though 4 is the rule-of-thumb default.
- Best chunk per expanded note: one `DISTINCT ON (note_id)` query across all expanded notes, not one query per note.
- No end-to-end hit@k: the 18 eval questions are drafts the owner rewrites first (D-003).

Gotchas:

- expand.py adds seeds to the `seen` set, so a seed note can never appear in expansion results — the only dedup path is at the chunk level: an expanded note's best chunk can't be a seed chunk (different note), but the check is defensive.
- The "Lost in the Middle" paper (read) suggests putting strongest context first — the seed-first packing does this by design.
- expanded_budget_share (0.4, the cap from the "watch out for" note) was a module constant; per ADR-0023 it is now `RETRIEVAL_EXPANDED_BUDGET_SHARE` in `.env`, so a guardrail that an operator might want to relax on a larger-vault deploy is tunable without code.
