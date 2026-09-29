# Task 4 — Expansion, scoring & context assembly

Status: todo
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

Done when: Returns a context object with provenance for every eval question.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
