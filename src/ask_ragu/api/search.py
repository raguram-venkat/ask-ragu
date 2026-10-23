"""GET /search?q= — retrieval-only debug endpoint (SPEC §6, §9).

Same pipeline as /chat minus the LLM: hybrid seed search (lexical + vector
fused by RRF) -> graph expansion -> best chunk per note -> provenance-tagged
context. Returns the assembled chunks with full score breakdown so you can
debug why a note was or wasn't retrieved, e.g. "this came in via link from
<Note title>" or "the floor at 0.3 refused this correctly."
"""

from fastapi import APIRouter

from ask_ragu import db
from ask_ragu.index.embed import embed_query
from ask_ragu.retrieval.assemble import assemble_context
from ask_ragu.retrieval.fuse import reciprocal_rank_fusion
from ask_ragu.retrieval.lexical import lexical_search
from ask_ragu.retrieval.vector import vector_search

router = APIRouter()


@router.get("/search")
def search(q: str) -> dict:
    """Trace a question through the full retrieval pipeline without generating.

    Query param is `q` (SPEC §6: `GET /search?q=`), not vault content itself —
    only live requests are logged by the proxy, never to git.
    """
    question = q
    with db.connect() as conn:
        db.migrate(conn)
        qv = embed_query(question)

        lexical = lexical_search(conn, question)
        vector = vector_search(conn, qv)

        # RRF fuses lexical+vector; reciprocal_rank_fusion applies the relevance floor.
        # If it clears, it returns ranked seeds; otherwise [].
        seeds = reciprocal_rank_fusion(lexical, vector)

        context = assemble_context(conn, seeds, qv, token_budget=100_000, with_graph=True)

        # Score components for debugging: lexical ranks, vector scores, RRF ranks.
        # lexical[i] = (chunk_id, note_id, ts_rank_cd score); index 0 = rank 1
        lexical_ids = {cid: score for cid, _, score in lexical}
        vector_ids = {cid: score for cid, _, score in vector}
        rrf_ids = {cid: score for cid, _, score in seeds}

        chunk_details = []
        for c in context:
            chunk_details.append(
                {
                    "note_title": c.note_title,
                    "heading_path": c.heading_path,
                    "content": c.content,
                    "score": round(c.score, 4),
                    "source": c.source,
                    "provenance": c.provenance,
                    "lexical_score": lexical_ids.get(c.chunk_id),
                    "vector_score": vector_ids.get(c.chunk_id),
                    "rrf_score": rrf_ids.get(c.chunk_id),
                }
            )

        return {
            "question": question,
            "context_size": len(context),
            "refused": len(seeds) == 0,  # relevance floor rejected the query
            "stages": {
                "lexical_hits": len(lexical),
                "vector_hits": len(vector),
                "seeds": len(seeds),
            },
            "context": chunk_details,
        }
