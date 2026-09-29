# Task 5 — Retrieval eval harness + ablation

Status: todo
Est: 90m
Spec: SPEC.md §12

What: One command runs eval v0 through each variant and prints hit@k and MRR.

Approach: Variants: lexical, vector, hybrid, hybrid+graph. Hit = any gold note appears in the assembled context. Results saved as dated CSV (only aggregates go in the public repo).

Read first:

- Your eval v0 file

Watch out for:

- Graph expansion must not hurt single-note questions — look at per-question diffs, not only averages.
- 15-20 questions is a small sample: a 1-question difference is noise.

Done when: Ablation table pasted below. If hybrid+graph doesn't win, log a D-entry saying why.

## Ablation

| Variant | hit@5 | hit@10 | MRR |
|---|---|---|---|
| lexical | | | |
| vector | | | |
| hybrid (RRF) | | | |
| hybrid + graph | | | |

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
