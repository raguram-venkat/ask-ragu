"""Context assembly (SPEC §9 steps 3-7, Task 4).

Expand seed notes through the graph (Sprint 3), pick each expanded note's best
chunk for the question, score, dedupe seed vs. expanded, and pack into a token
budget with provenance.

Score: seeds keep their RRF score from fusion (Task 3); expanded notes get
cosine × hop_decay × note_type_prior. The two score types live on different
scales, so they aren't merged into one ranking — seeds pack first (they are
direct hits), expanded fill the remainder up to 40% of the budget (Task 4
"watch out for": expanded notes crowding out direct hits).
"""

from dataclasses import dataclass
from uuid import UUID

import psycopg

from ask_ragu.graph.expand import Reached
from ask_ragu.graph.expand import expand as graph_expand
from ask_ragu.settings import settings

# Note-type priors: fleeting and meta are less reliable context sources (D-006).
# Concept and source notes carry full weight. MOCs are never context (filtered in SQL + expand).
NOTE_TYPE_PRIOR = {"fleeting": 0.5, "meta": 0.5}
DEFAULT_PRIOR = 1.0

# EXPANDED_BUDGET_SHARE and CHARS_PER_TOKEN come from settings (ADR-0023).


@dataclass(frozen=True)
class ContextChunk:
    """A chunk in the assembled context, with provenance of how it was reached."""

    chunk_id: int
    note_id: UUID
    note_title: str
    heading_path: str
    content: str
    score: float
    provenance: str  # "direct", "linked from <note>", "sibling of <note> via <MOC>", etc.
    source: str  # "seed" or "expanded"


def _tokens(content: str) -> float:
    """Rough token count: len(content) / settings.retrieval_chars_per_token."""
    return len(content) / settings.retrieval_chars_per_token


# Best chunk (highest cosine to query) per note, excluding MOCs.
BEST_CHUNK_PER_NOTE = """
SELECT DISTINCT ON (c.note_id)
    c.id, c.note_id, n.title, n.note_type, c.heading_path, c.content,
    1 - (c.embedding <=> %(q)s::vector) AS cosine
FROM chunks c
JOIN notes n ON n.id = c.note_id
WHERE c.note_id = ANY(%(note_ids)s) AND n.note_type != 'moc'
ORDER BY c.note_id, cosine DESC, c.id
"""

NOTE_TITLES = "SELECT id, title FROM notes WHERE id = ANY(%(ids)s)"

SEED_CHUNK_DETAILS = """
SELECT c.id, c.note_id, c.heading_path, c.content, n.title, n.note_type
FROM chunks c JOIN notes n ON n.id = c.note_id
WHERE c.id = ANY(%(ids)s)
ORDER BY c.id
"""


def _provenance(reached: Reached, titles: dict) -> str:
    """Format how an expanded note was reached, for context display."""
    from_title = titles.get(reached.from_note, str(reached.from_note))
    if reached.edge_type in ("link", "backlink", "parent", "child"):
        return f"linked from {from_title}"
    if reached.edge_type == "sibling":
        via = titles.get(reached.via_note, str(reached.via_note)) if reached.via_note else "an MOC"
        return f"sibling of {from_title} via {via}"
    if reached.edge_type == "tag":
        return f"shares tag #{reached.via_tag} with {from_title}"
    return f"via {from_title}"


def assemble_context(
    conn: psycopg.Connection,
    fused_seeds: list[tuple[int, UUID, float]],
    query_vector: list[float],
    token_budget: int,
) -> list[ContextChunk]:
    """Steps 3-7 of SPEC §9: expand seeds, best-chunk, score, dedupe, pack.

    Args:
        conn: database connection.
        fused_seeds: (chunk_id, note_id, rrf_score) from Task 3's reciprocal_rank_fusion.
        query_vector: embed_query(question), for finding each expanded note's best chunk.
        token_budget: max tokens for the assembled context (per-provider in Sprint 5).
    """
    if not fused_seeds:
        return []

    seed_note_ids = list({nid for _, nid, _ in fused_seeds})

    # Step 4: graph expansion from seed notes.
    reached = graph_expand(conn, seed_note_ids)
    expanded = [r for r in reached if not r.is_moc]
    expanded_ids = [r.note_id for r in expanded]

    # Fetch every note title we need for provenance (seeds, from_notes, via_notes, expanded).
    title_ids: set[UUID] = set(seed_note_ids) | {r.note_id for r in expanded}
    title_ids |= {r.from_note for r in expanded}
    title_ids |= {r.via_note for r in expanded if r.via_note}
    titles = (
        {r[0]: r[1] for r in conn.execute(NOTE_TITLES, {"ids": list(title_ids)}).fetchall()}
        if title_ids
        else {}
    )

    # Step 5: best chunk per expanded note (by cosine to the query vector).
    best_chunks = conn.execute(
        BEST_CHUNK_PER_NOTE,
        {"q": str(query_vector), "note_ids": expanded_ids},
    ).fetchall()

    hop_map = {r.note_id: r for r in expanded}

    # Step 6: score expanded chunks — cosine × hop_decay × note_type_prior.
    expanded_chunks: list[ContextChunk] = []
    for chunk_id, note_id, title, note_type, hp, content, cosine in best_chunks:
        r = hop_map[note_id]
        decay = (
            settings.retrieval_hop_decay_hop1 if r.hop == 1 else settings.retrieval_hop_decay_hop2
        )
        prior = NOTE_TYPE_PRIOR.get(note_type, DEFAULT_PRIOR)
        expanded_chunks.append(
            ContextChunk(
                chunk_id,
                note_id,
                title,
                hp,
                content,
                cosine * decay * prior,
                _provenance(r, titles),
                "expanded",
            )
        )
    expanded_chunks.sort(key=lambda c: (-c.score, c.chunk_id))

    # Seed chunks keep their RRF scores (ranked already by Task 3).
    seed_ids = [cid for cid, _, _ in fused_seeds]
    rrf_scores = {cid: s for cid, _, s in fused_seeds}
    seed_rows = conn.execute(SEED_CHUNK_DETAILS, {"ids": seed_ids}).fetchall()
    seed_chunks = [
        ContextChunk(cid, nid, title, hp, content, rrf_scores[cid], "direct", "seed")
        for cid, nid, hp, content, title, _ in seed_rows
    ]
    # Re-sort by RRF score (preserves Task 3 ranking; seed_rows may differ in row order).
    seed_chunks.sort(key=lambda c: (-c.score, c.chunk_id))

    # Dedupe: a chunk that's both a seed and an expanded best-match stays a seed (labeled direct).
    seed_chunk_ids = {c.chunk_id for c in seed_chunks}
    expanded_chunks = [c for c in expanded_chunks if c.chunk_id not in seed_chunk_ids]

    # Step 7: pack into token budget — seeds first, expanded fill ≤40%.
    return _pack_budget(seed_chunks, expanded_chunks, token_budget)


def _pack_budget(
    seeds: list[ContextChunk],
    expanded: list[ContextChunk],
    budget: int,
) -> list[ContextChunk]:
    """Seeds pack first (direct hits, strongest first); expanded fill the remaining budget
    up to retrieval_expanded_budget_share of the total."""
    expanded_cap = int(budget * settings.retrieval_expanded_budget_share)

    result: list[ContextChunk] = []
    used = 0
    expanded_used = 0

    for c in seeds:
        tokens = _tokens(c.content)
        if used + tokens <= budget:
            result.append(c)
            used += tokens

    for c in expanded:
        tokens = _tokens(c.content)
        if expanded_used + tokens <= expanded_cap and used + tokens <= budget:
            result.append(c)
            expanded_used += tokens

    return result
