"""Retrieval eval harness (SPEC §12, Sprint 4 Task 5).

Runs eval questions through four retrieval variants — lexical, vector, hybrid (RRF),
and hybrid+graph — and prints hit@k and MRR for each, saved as a dated CSV.

Usage (inside compose):
    uv run askragu eval eval/questions.private.yaml
    uv run askragu eval eval/questions.private.yaml --budget 3000 --csv results/2026-10-21.csv

The vault must be indexed first (`askragu index --full`). The four variants share the same
index — they differ only in retrieval strategy, not in what's indexed — so no per-schema
isolation is needed (ADR-0017 that pattern is for comparing index configs, not retrieval
variants).
"""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import UUID

import psycopg

from ask_ragu.evalset import Question
from ask_ragu.evalset import load as load_questions
from ask_ragu.index.embed import embed_query
from ask_ragu.retrieval.assemble import ContextChunk, assemble_context
from ask_ragu.retrieval.fuse import reciprocal_rank_fusion
from ask_ragu.retrieval.lexical import lexical_search
from ask_ragu.retrieval.vector import vector_search
from ask_ragu.settings import settings

VARIANTS = ("lexical", "vector", "hybrid", "hybrid+graph")
HITS_AT = (5, 10)
# Unconstrained budget so hit@k measures ranking quality, not budget pressure.
DEFAULT_BUDGET = 100_000


@dataclass
class EvalResult:
    question_id: str
    kind: str
    variant: str
    hit_at: dict[int, int]  # k -> 0/1
    mrr: float
    context_len: int


def retrieve_variant(
    conn: psycopg.Connection,
    question: str,
    query_vector: list[float],
    variant: str,
    token_budget: int,
) -> list[ContextChunk]:
    """Run one retrieval variant, return the assembled context chunks.

    lexical    — lexical_search only, no graph expansion
    vector     — vector_search only (relevance floor applied), no graph expansion
    hybrid     — RRF of lexical+vector, no graph expansion
    hybrid+graph — RRF of lexical+vector, with graph expansion (the full pipeline)
    """
    lexical = lexical_search(conn, question)
    vector = vector_search(conn, query_vector)

    if variant == "lexical":
        return assemble_context(conn, lexical, query_vector, token_budget, with_graph=False)

    if variant == "vector":
        # Relevance floor applies to vector-only too: the closest semantic match must clear it.
        if vector and vector[0][2] < settings.retrieval_relevance_floor:
            return []
        return assemble_context(conn, vector, query_vector, token_budget, with_graph=False)

    # hybrid and hybrid+graph
    seeds = reciprocal_rank_fusion(lexical, vector)
    return assemble_context(
        conn,
        seeds,
        query_vector,
        token_budget,
        with_graph=variant == "hybrid+graph",
    )


# --- Pure metrics (no DB) — testable without Postgres --------------------------


def hit_at(context_paths: list[str], gold: list[str], k: int) -> int:
    """1 if any gold note is in the top-k context.

    For unanswerable questions (gold empty), hit = 1 iff the top-k context is empty
    (correct refusal by the relevance floor).
    """
    if not gold:
        return 1 if len(context_paths[:k]) == 0 else 0
    return 1 if any(g in context_paths[:k] for g in gold) else 0


def reciprocal_rank(context_paths: list[str], gold: list[str]) -> float:
    """1/rank of the first gold note in context; 1.0 for correct refusal; 0.0 if not found.

    For unanswerable questions (gold empty), a correct refusal returns an empty context -> 1.0.
    A failed refusal (non-empty context) -> 0.0.
    """
    if not gold:
        return 1.0 if not context_paths else 0.0
    for rank, path in enumerate(context_paths, 1):
        if path in gold:
            return 1.0 / rank
    return 0.0


# --- Aggregation ---------------------------------------------------------------


def _note_paths(conn: psycopg.Connection, note_ids: list[UUID]) -> dict[UUID, str]:
    """Map note UUIDs to their vault path in one query."""
    if not note_ids:
        return {}
    rows = conn.execute("SELECT id, path FROM notes WHERE id = ANY(%s)", (note_ids,)).fetchall()
    return dict(rows)


def evaluate(
    conn: psycopg.Connection,
    questions: list[Question],
    token_budget: int = DEFAULT_BUDGET,
) -> list[EvalResult]:
    """Run all variants on all questions; return per-question per-variant results."""
    results: list[EvalResult] = []
    for q in questions:
        query_vector = embed_query(q.question)
        for variant in VARIANTS:
            context = retrieve_variant(conn, q.question, query_vector, variant, token_budget)
            note_ids = list({c.note_id for c in context})
            note_paths = _note_paths(conn, note_ids)
            context_paths = [note_paths.get(c.note_id) for c in context]

            results.append(
                EvalResult(
                    question_id=q.id,
                    kind=q.kind,
                    variant=variant,
                    hit_at={k: hit_at(context_paths, q.gold, k) for k in HITS_AT},
                    mrr=reciprocal_rank(context_paths, q.gold),
                    context_len=len(context),
                )
            )
    return results


def aggregate(results: list[EvalResult]) -> dict[str, dict[str, float]]:
    """Compute hit@k and MRR averages per variant."""
    agg: dict[str, dict[str, float]] = {}
    for variant in VARIANTS:
        rows = [r for r in results if r.variant == variant]
        n = len(rows)
        if n == 0:
            continue
        agg[variant] = {f"hit@{k}": sum(r.hit_at[k] for r in rows) / n for k in HITS_AT}
        agg[variant]["mrr"] = sum(r.mrr for r in rows) / n
    return agg


# --- Output formatting ---------------------------------------------------------


def format_ablation(results: list[EvalResult]) -> str:
    """Print the ablation table: per-variant hit@5, hit@10, MRR."""
    agg = aggregate(results)
    lines = ["| Variant | hit@5 | hit@10 | MRR |", "|---|---|---|---|"]
    for variant in VARIANTS:
        if variant not in agg:
            continue
        a = agg[variant]
        lines.append(f"| {variant} | {a['hit@5']:.3f} | {a['hit@10']:.3f} | {a['mrr']:.3f} |")
    return "\n".join(lines)


def format_per_question(results: list[EvalResult]) -> str:
    """Per-question breakdown so diffs between variants are visible (small sample = noise)."""
    by_q: dict[str, list[EvalResult]] = {}
    for r in results:
        by_q.setdefault(r.question_id, []).append(r)

    lines = [
        "| Q ID | Kind | Variant | hit@5 | hit@10 | MRR | ctx |",
        "|---|---|---|---|---|---|---|",
    ]
    for qid in sorted(by_q):
        for r in by_q[qid]:
            lines.append(
                f"| {r.question_id} | {r.kind} | {r.variant} "
                f"| {r.hit_at[5]} | {r.hit_at[10]} | {r.mrr:.3f} | {r.context_len} |"
            )
    return "\n".join(lines)


def save_csv(results: list[EvalResult], path: str | Path) -> None:
    """Save per-question results as a dated CSV (kept local, never committed)."""
    today = date.today().isoformat()
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["date", "variant", "question_id", "kind", "hit@5", "hit@10", "mrr", "context_size"]
        )
        for r in results:
            w.writerow(
                [
                    today,
                    r.variant,
                    r.question_id,
                    r.kind,
                    r.hit_at[5],
                    r.hit_at[10],
                    f"{r.mrr:.4f}",
                    r.context_len,
                ]
            )


# --- CLI entry point -----------------------------------------------------------


def main(argv: list[str]) -> int:
    """askragu eval <questions.yaml> [--budget N] [--csv path]"""
    import argparse

    parser = argparse.ArgumentParser(
        prog="askragu eval",
        description="Run retrieval eval through lexical/vector/hybrid/hybrid+graph variants.",
    )
    parser.add_argument("questions", help="path to questions YAML (eval/questions.private.yaml)")
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help=f"token budget for assembled context (default: {DEFAULT_BUDGET}, unconstrained)",
    )
    parser.add_argument("--csv", default=None, help="save per-question results as dated CSV")
    args = parser.parse_args(argv)

    from ask_ragu import db

    questions = load_questions(Path(args.questions))
    print(f"{len(questions)} questions, 4 variants (lexical, vector, hybrid, hybrid+graph)")

    with db.connect() as conn:
        db.migrate(conn)
        results = evaluate(conn, questions, args.budget)

    print("\n## Ablation (aggregates)\n")
    print(format_ablation(results))
    print("\n## Per-question\n")
    print(format_per_question(results))

    if args.csv:
        save_csv(results, args.csv)
        print(f"\nSaved per-question results to {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main([]))
