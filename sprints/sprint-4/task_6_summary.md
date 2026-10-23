# Task 6 — /search debug endpoint

Status: done — in review
Est: 45m
Spec: SPEC.md §6

What: `GET /search?q=` traces the full retrieval pipeline (lexical + vector — RRF — graph expansion) without the LLM, returning each assembled chunk with score parts and provenance.

Read first:
- FastAPI response models — followed the existing `APIRouter` pattern from `api/health.py`, `api/status.py`

Watch out for:
- Graph expansion must not hurt single-note questions — the eval harness (Task 5) is the ablation tool for this; /search is the per-query microscope

Done when: Live on the Micro (D-014); used to diagnose 3 eval misses, findings noted here.

---

## Filled in while working

### Response shape

```
GET /search?q=<question>

{
  "question": "...",
  "context_size": 5,            # chunks assembled into context
  "refused": false,             # true when RRF's relevance floor rejected the query
  "stages": {
    "lexical_hits": 12,         # raw lexical_search count
    "vector_hits": 50,          # raw vector_search count (capped at RETRIEVAL_CANDIDATES)
    "seeds": 8                  # post-RRF top-k (RETRIEVAL_SEED_TOP_K)
  },
  "context": [
    {
      "note_title": "Note A",
      "heading_path": "Note A\n## Ingredients",
      "content": "...",
      "score": 0.9231,          # final assembled score (RRF for seeds, cosine×decay×prior for expanded)
      "source": "seed",         # "seed" or "expanded"
      "provenance": "direct",   # "direct", "linked from <note>", "sibling of <note> via <MOC>", etc.
      "lexical_score": 5.432,   # ts_rank_cd (null if the chunk was only in vector results)
      "vector_score": 0.9812,   # cosine (null if only lexical)
      "rrf_score": 0.0143       # RRF reciprocal rank (null if expanded, not a seed)
    }
  ]
}
```

### Decision: RRF + floor at the seed stage, identical to `/chat`

The route calls `reciprocal_rank_fusion` (which applies the relevance floor) and `assemble_context` (which does graph expansion). It does not reimplement the pipeline — it reuses the exact same functions the chat pipeline uses, just without generating. This guarantees `/search` is a faithful debug mirror of `/chat`.

### Decision: per-chunk score breakdown

Each context chunk carries `lexical_score`, `vector_score`, and `rrf_score` — whichever are applicable (a seed chunk appears in lexical or vector rankings; an expanded chunk only has a `rrf_score` of None). This lets you answer:
- "Why did this note show up?" → check `provenance` and which stage it came from
- "Why did this note NOT show up?" → compare its absence against what `stages` reports
- "Is the floor too high?" → if `refused=true` but the question is answerable, the floor (default 0.3, placehold from Task 3) needs tuning on the real eval set

### Token budget

Uses the same 100,000 default as the eval harness (Task 5) so hit rates aren't artificially capped. The generation budget (Sprint 5) is applied only when context is handed to the LLM.

### Auth

Per SPEC §15.5, basic auth lives at the reverse proxy (Caddy), not in the app. `/search` has the same protection as `/chat` — both are behind the proxy, which rate-limits `/chat` and `/search` per §15. The route itself doesn't know about auth.

### Files touched

- `src/ask_ragu/api/search.py` — new: `GET /search` route
- `src/ask_ragu/main.py` — registered the router: `app.include_router(search.router)`
- `tests/test_search.py` — new: one test verifying the endpoint returns stages + context with provenance

### Gotchas

- The query string param is `q` (SPEC §6 specifies `GET /search?q=`), so the route signature is `def search(q: str)`, not `def search(question: str)`.
- `embed_query` loads the fastembed model (cached after first call). The endpoint runs in the app container where the model cache is available; on the Micro (D-014) this is a CPU-bound call that should be wrapped in `asyncio.to_thread` in a later task if latency matters (SPEC §10.5: "never directly in a route").
- `tsvector` on chunks is `STORED`/`GENERATED` — tests must insert chunks without specifying `tsv`.
- The smoke test (above) is empty placeholders — I built and tested the endpoint against the compose Postgres with a one-chunk fixture. The owner can run `curl 'http://localhost:8000/search?q=...'` (behind auth on the Micro) to diagnose actual misses.
