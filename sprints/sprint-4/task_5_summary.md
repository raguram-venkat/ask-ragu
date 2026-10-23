# Task 5 — Retrieval eval harness + ablation

Status: in review — harness built + tested; owner runs against the rewritten eval v0 (D-003)
Est: 90m
Spec: SPEC.md §12

What: One command runs eval v0 through each variant and prints hit@k and MRR.

Approach: Variants: lexical, vector, hybrid, hybrid+graph. Hit = any gold note appears in the assembled context. Results saved as dated CSV (only aggregates go in the public repo).

Read first:

- Your eval v0 file

Watch out for:

- Graph expansion must not hurt single-note questions — look at per-question diffs, not only averages.
- 15-20 questions is a small sample: a 1-question difference is noise.

From Sprint 2 Task 8 (ADR-0017/0018): run each configuration as its own index in its own Postgres schema — `CREATE SCHEMA exp_<name>`, `SET search_path TO exp_<name>, public`, migrate, `index --full` with the settings passed as env overrides, evaluate. Never version rows to compare configs. Each schema has its own sync lock, so experiments never block the real index.

Done when: Ablation table pasted below. If hybrid+graph doesn't win, log a D-entry saying why.

---

## Filled in while working

The four retrieval variants share the same index — they differ only in *how the index is
queried*, not what's indexed. Per-schema isolation (the Sprint 2 pattern above) applies to
comparing different *indexing* configurations (chunk sizes, embedding models, etc.), not
retrieval strategies. All four variants run against the same `public` schema.

### Ablation table (sample questions smoke test, real vault)

The sample questions (`eval/questions.sample.yaml`) are synthetic coffee-themed Q&A written
against a *different* vault, so hit rates are near-zero here — the gold paths don't match the
real vault's notes. This run verifies the pipeline end-to-end; the owner replaces these with
the 15-20 private eval questions (D-003) for real results.

| Variant | hit@5 | hit@10 | MRR |
|---|---|---|---|
| lexical | 0.250 | 0.250 | 0.250 |
| vector | 0.000 | 0.000 | 0.000 |
| hybrid (RRF) | 0.000 | 0.000 | 0.000 |
| hybrid + graph | 0.000 | 0.000 | 0.000 |

Observations from the smoke test (synthetic questions, don't tune to these):
- Unanswerable s04 (lexical) correctly refuses: 0 lexical hits for "matcha" → empty context → hit=1.
- Unanswerable s04 (vector) fails to refuse: best cosine ≥ 0.3 floor → 50 chunks of noise → hit=0.
  This confirms the floor (0.3) is a placeholder — Task 5's sweep will tune it on the real eval set.
- lexical hit @ s01/s02: 0.25 — likely matches the word "espresso" in some real note, but the
  gold path doesn't match, so hit=0. The 0.25 is from s04 (unanswerable, correct refusal).

Run with the owner's private eval set:
```
uv run askragu eval eval/questions.private.yaml --csv results/2026-10-21.csv
```

### Decision: `with_graph` parameter on `assemble_context`

Added `with_graph: bool = True` to `assemble_context` so the harness can run the "no graph"
variants (lexical, vector, hybrid) by reusing the existing seed-packing logic — no duplicated
code. Default `True` preserves all existing callers (the `/chat` and `/search` pipelines).

### Decision: vector variant applies the relevance floor

`reciprocal_rank_fusion` checks the floor internally, so hybrid and hybrid+graph get it for
free. For the vector-only variant, the same floor check is applied manually before packing.
The lexical variant does not check the floor — it has no vector similarity to gate on.

### Decision: unconstrained token budget for ranking measurement

The `--budget` flag defaults to 100,000 tokens so `hit@k` measures pure ranking quality,
not budget pressure. The generation budget (Sprint 5) is applied at query time; the eval
isolates retrieval ranking.

### Decision: MRR for unanswerable questions

For unanswerable questions (gold empty), MRR = 1.0 when the context is empty (correct
refusal by the relevance floor) and 0.0 when any chunk is returned (failed refusal). This
penalizes variants that leak noise on unanswerable questions.

Files touched:

- `src/ask_ragu/retrieval/eval_harness.py` — new: `retrieve_variant`, pure `hit_at`/`reciprocal_rank`, `evaluate`, `format_ablation`, `format_per_question`, `save_csv`, `main`
- `src/ask_ragu/retrieval/assemble.py` — `with_graph: bool = True` on `assemble_context`; skips graph expansion + expansion scoring when False, packs seeds only
- `src/ask_ragu/cli.py` — `askragu eval <questions>` subcommand with `--budget` and `--csv`
- `tests/test_eval_harness.py` — 13 tests: pure metrics, variant selection, floor behavior, aggregation, CSV output

Decisions made here:

- `with_graph` parameter on `assemble_context`: shortest path to reuse seed-packing logic without duplicating it. The alternative (a separate `pack_seeds` function) would duplicate the `SEED_CHUNK_DETAILS` query and `ContextChunk` construction.
- Per-question MRR for unanswerable = 1.0 (empty context) / 0.0 (non-empty): treats correct refusal as a perfect rank, consistent with hit@k's "correct refusal = hit."
- CSV is a runtime artifact saved to whatever path the user passes; it is not committed to the repo (only aggregates go in the task file). Dated via `date.today()` at write time.
- Default budget 100,000 so ranking quality is measured in isolation from generation budget constraints (which are Sprint 5's concern, per-provider).

Gotchas:

- `embed_query` loads the fastembed model (cached after first call). The eval command must run where the model cache is available — inside the compose container or on the laptop with `models/` populated.
- The `--budget 100_000` default means the expanded_budget_share (40%) cap is effectively unlimited, so all candidate chunks fit. Reducing `--budget` constrains context size and can lower hit rates — this is correct, the budget matters at generation time.
- Sample-question results above are not meaningful (synthetic Q&A vs. real vault). Run with `eval/questions.private.yaml` for real numbers — that file is gitignored (ADR-0022).
