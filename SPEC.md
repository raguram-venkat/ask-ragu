# ask-ragu — System Spec

Version 2.1 — 2026-09-28. Living document: this file always describes the system as currently intended. Lines marked `[D-00N]` were amended after v2 — DEVIATIONS.md says what changed and why.

A retrieval-and-generation system over a personal Obsidian vault, hosted for real (not a notebook demo), designed to be defensible in an interview: every non-obvious choice below has a stated reason and a stated alternative that was rejected.

## 1. Overview

ask-ragu answers questions against a private Obsidian vault by retrieving relevant note content and passing it to an LLM. It treats the vault as what it actually is — a graph of linked notes, not a folder of independent documents — and retrieves accordingly. It runs continuously on free-tier cloud infrastructure, updates itself on every `git push` to the vault's private repo, and degrades gracefully across a chain of inference providers instead of depending on any single model.

## 2. Problem Statement

Two failures show up if you treat this as generic document RAG:

Semantic gap — personal notes are terse and use your own shorthand. A query rarely shares vocabulary with the note that actually answers it. Lexical search alone (the original plan: OpenSearch/BM25) misses these constantly.

Structural loss — an Obsidian vault encodes relationships explicitly through `[[wikilinks]]`, tags, and folder structure. A decision note and the meeting note it originated from are related in ways plain text similarity won't surface, because they may not be semantically similar at all — they're *linked*. Flat retrieval (rank all chunks by similarity, take top-k) throws this structure away.

OpenSearch was dropped from this project, not because it's bad technology, but because it solves neither problem well on its own and adds a second stateful JVM service that isn't earning its keep once retrieval is redesigned around the graph. (It remains a fine thing to learn — just as its own project, not bolted onto this one for the sake of using it.)

## 3. Non-Negotiables

- Fully containerized, reproducible via `docker-compose up`.
- Multi-provider inference fallback chain (a local model plus hosted APIs), reorderable by an admin without a code change.
- Zero recurring cost — must run entirely on free-tier infrastructure.

## 4. Design Principles

- Graph-aware retrieval: use the vault's link structure as a first-class retrieval signal, not metadata.
- One datastore: Postgres + pgvector does full-text search, vector search, graph traversal, and relational metadata. One service to run, back up, and reason about instead of three.
- Privacy by default: raw note content never leaves the host during indexing. Only the specific snippets retrieved for a specific question are ever sent to an LLM provider, and only at query time.
- Provenance over black-box answers: every answer traces back to named notes and states how they were found (direct match vs. linked from a match).
- Proportionate complexity: nothing is added because it's impressive. Each component either serves the actual scale of a single-user vault or is explicitly named as a non-goal below.

## 5. Non-Goals

- Full GraphRAG-style community detection or LLM-generated graph summaries. That technique earns its cost on corpora far larger than one person's vault; here it's a redundant expense.
- Multi-user / multi-tenant support.
- Sub-second indexing latency. A push-to-searchable lag of seconds to low minutes is fine for a personal tool.
- A dedicated graph database or vector database service. Postgres covers both at this scale without the extra operational surface.
- A cross-encoder reranker. Noted as a stretch goal, not core — the hop-decay + hybrid-score fusion below is enough for a single-user corpus.

## 6. Architecture

```
GitHub (private repo, Knowledge base vault)
        |
        | push --> webhook (HMAC-verified)
        v
Oracle Cloud Always Free instance (Docker Compose)
  |
  |-- app container (FastAPI)
  |     /webhook   -> verify HMAC -> 202 -> background: git fetch + diff (rename-aware) -> parse -> chunk -> embed -> upsert  [D-001]
  |     /chat      -> retrieval pipeline -> inference chain -> answer + citations
  |     /search    -> retrieval only, with score breakdown (debug)
  |     /          -> minimal static web UI  [D-004]
  |     /healthz
  |
  |-- postgres (+ pgvector) container
  |     notes, chunks, note_links, note_tags, index_state  [D-002]
  |     full-text (tsvector) + vector (pgvector) + graph (recursive CTE)
  |
  |-- local-model container (llama.cpp or similar, small quantized model)
  |     exposes the same provider HTTP contract as external APIs
  |
  |-- reverse proxy (Caddy or nginx)
        TLS termination + basic auth on every route except /webhook and /healthz, only public entry point  [D-004]
```

Three logical services plus a reverse proxy. No task queue — the webhook acknowledges within GitHub's 10-second delivery window and hands work to an in-process background task guarded by a single-flight lock; a single-user vault pushes rarely enough that Celery/RQ would be solving a load problem this project doesn't have. [D-001]

## 7. Data Model (Postgres)

| Table | Key columns | Purpose |
|---|---|---|
| notes | id, path, title, note_type, frontmatter (jsonb), content_hash, updated_at | One row per note. note_type comes from the vault's numbered folders (meta, moc, concept, source, fleeting) [D-006]. content_hash detects unchanged files to skip re-embedding. |
| chunks | id, note_id (fk), heading_path, content, embedding (vector), tsv (tsvector), chunk_order | Heading-based chunks, not fixed-token windows. tsv is generated for lexical search. |
| note_links | source_note_id, raw_target, target_note_id (nullable), link_kind | Raw wikilinks kept so they can be re-resolved every run; resolved rows are the graph's note→note edges, traversed in both directions. Tags and MOC notes act as hubs traversed at query time instead of materialized pairwise edges; folder_sibling edges dropped — folders in this vault encode note type, not topic [D-002]. |
| note_tags | note_id, tag | Junction table. Tags above a cardinality threshold (e.g. used on >20% of notes) are excluded from edge generation — a generic tag like `#todo` isn't a meaningful relationship. |

Dangling wikilinks (target note doesn't exist) are recorded with a null `target_note_id` and the raw target text, excluded from graph traversal, and available later as a vault-health stretch feature.

## 8. Indexing Pipeline

1. Webhook receives a push event; signature verified before anything else runs; non-default-branch pushes and duplicate `X-GitHub-Delivery` ids ignored; responds 202 within GitHub's 10 s window and indexing continues in a background task [D-001].
2. `git diff --find-renames` against the previous indexed commit, not a full rescan — gives add/modify/delete/rename per file explicitly. Renames update the existing note row's path (preserving id, edges, history) instead of delete+insert. If the last indexed commit no longer exists (force-push, rewritten history), fall back to a full index.
3. For each added/modified file outside the excluded paths (Templates/, .obsidian/, Bases/, Attachments/, non-.md) [D-006]: parse frontmatter into `notes.frontmatter` (malformed YAML logs a warning, never fails the run); strip dataview/base code blocks and Templater tags, unwrap callouts [D-006]; split body by heading into chunks; extract `[[wikilinks]]`, resolving aliases and case-insensitive filename matches against a vault-wide alias map built at index time.
4. Compute `content_hash`; skip re-embedding unchanged notes even if they were touched in the push (e.g. only frontmatter changed).
5. Embed each chunk locally (small CPU-friendly embedding model in the app or a sidecar — embedding is cheap enough to self-host even on the ARM CPU, and doing so means note content never leaves the host during the frequent indexing step, only retrieved snippets do, later, at query time).
6. Upsert notes/chunks/tags in a transaction; recompute outgoing edges for changed notes.
7. For deleted files: delete the note row (cascades to its chunks and edges).
8. Container startup runs one reconciliation pass against the last indexed commit, catching any webhook missed during downtime.

## 9. Retrieval Pipeline

1. Embed the incoming question.
2. Hybrid seed search over `chunks`: fuse full-text (`tsv @@ query`) and vector similarity (`embedding <-> query_vec`) rankings (reciprocal rank fusion), take top-k seed chunks (k≈8).
3. Collect the distinct notes behind those seed chunks as seed nodes.
4. Recursive CTE graph expansion from the seed nodes over resolved `note_links` and tag/MOC hubs, depth ≤ 2, bounded both per hop (fan-out cap, so a MOC or a popular tag can't flood the frontier) and in total (e.g. 30 notes) [D-007]. MOC notes are traversed through but their own chunks are not returned as context [D-002].
5. For each expanded note, pick its own best-matching chunk against the query (not the whole note) — a linked-but-not-top-ranked note contributes only its most relevant excerpt.
6. Score = semantic similarity × hop-decay (hop-1 weighted higher than hop-2) × note_type prior (fleeting and meta lower) [D-006], fuse with the hybrid seed scores, take the top-N that fit the generation context budget.
7. Assemble context with explicit provenance per chunk: note title, and how it was reached (direct match, or "linked from <note>").

## 10. Generation & Inference Chain

- Common provider contract: `generate(prompt, context) -> response`, implemented identically whether the provider is the local model container or an external API — the fallback chain doesn't need to know which.
- Ordered provider list lives in config, not code; admin reorders by editing config and restarting, no redeploy of logic.
- Each provider owns its own failure handling — timeout, rate limit (429), malformed response — and falls through to the next entry on failure.
- Local provider: a small instruction-tuned model (roughly 1-3B parameters, quantized) served via llama.cpp or equivalent, on the ARM CPU. Slow by design; it's the fallback-of-last-resort and the serving-mechanics learning target, not the primary path.
- Hosted providers: 2-3 APIs with usable free tiers. Exact providers and quotas to be verified at implementation time — free-tier terms change often enough that pinning specific names now would likely be wrong by the time this is built. Providers whose free tier trains on prompts (e.g. Gemini's free tier outside the EU/UK/EEA as of mid-2026) are disabled by default via a `trains_on_data` flag in provider config [D-005].
- Prompt requires the model to answer only from supplied context, cite note titles, and explicitly say the vault doesn't cover it rather than guessing — grounding and honest refusal over confident hallucination.

## 11. Hosting & Infrastructure

- Host: Oracle Cloud Always Free, Ampere A1 ARM instance (2 OCPU / 12GB RAM as of the 2026 allocation, not time-limited). Fallback if signup/capacity fails: GCP e2-micro (always-free, 1GB RAM — workable but tighter).
- Repo access: private repo, read-only SSH deploy key, mounted as a Docker secret — never baked into the image or committed to any compose file.
- Webhook security: GitHub's `X-Hub-Signature-256` HMAC verified before any pull runs; payload contents never touch a shell string directly.
- Only the reverse proxy is publicly exposed; Postgres and the local-model container are internal-network-only.
- Persistent named volume holds the vault clone and Postgres data; both survive container restarts.

## 12. Evaluation

- A fixed set of 15-20 real questions written against the actual vault, each with the note(s) that should answer it known in advance. Written in Sprint 2, before any retrieval tuning, and kept out of both the public code repo and the vault (it would get indexed) [D-003].
- Retrieval metric: is the gold note present in the assembled context (hit rate)? Tracked before touching generation, so retrieval and generation quality aren't conflated.
- Generation metric: manual three-way rubric per answer — grounded-and-correct, grounded-but-wrong, hallucinated/ungrounded. Rerun the same set after any change to chunking, retrieval, or provider order to see whether it actually helped.

## 13. Key Decisions & Alternatives Considered

Each row is expanded as an ADR in `adr/` (indexed in INDEX.md).

| Decision | Chosen | Rejected | Why |
|---|---|---|---|
| Search engine | Postgres full-text + pgvector | OpenSearch | Neither lexical-only nor a second JVM service solves the graph-structure problem; Postgres gets hybrid search and graph traversal in one place |
| Graph storage | Edges table + recursive CTE in Postgres | Dedicated graph DB (Neo4j) | At single-user-vault scale, traversal depth ≤2 doesn't need a specialized engine; one fewer stateful service to run and back up |
| Embeddings | Self-hosted small model, generated at index time | External embedding API | Keeps note content from ever leaving the host during the frequent indexing step; only retrieved snippets go out, and only at query time |
| Indexing trigger | Git-diff-based incremental update on push | Full reindex every push | Scales with change size, not vault size; preserves note identity across renames instead of treating them as delete+create |
| Async infra | Ack-fast webhook + in-process background task, single-flight lock [D-001] | Synchronous in-request indexing; task queue (Celery/RQ + Redis) | Synchronous breaks GitHub's 10 s delivery timeout; a queue adds a broker service for a load this project doesn't have |
| Inference | Config-driven fallback chain, uniform local/remote provider contract | Single hardcoded provider | Resilience to any one provider's outage or rate limit, and a concrete design-pattern (Strategy/Chain-of-Responsibility) story |
| Hosting | Oracle Cloud Always Free ARM (12GB RAM, not time-limited) | AWS free tier | AWS's post-2025 free tier is a 6-month credit allowance, not an ongoing free tier — doesn't satisfy an always-on, indefinitely-free requirement |
| Reranking | Hop-decay + hybrid-score fusion | Cross-encoder reranker | Added model and latency cost isn't justified at this corpus size; revisit only if eval shows a real ranking problem it would fix |

## 14. Failure Modes & Edge Cases

- Renamed notes: handled via `git diff --find-renames`, updating path in place rather than losing the note's id and accumulated edges.
- Deleted notes: cascading delete of chunks and edges; no orphaned rows.
- Broken/unresolved wikilinks: recorded, excluded from traversal, not silently dropped (available for a later vault-health report).
- Alias collisions: alias map built fresh each index run from current frontmatter; last-write-wins on conflict, logged as a warning.
- Hub notes (a MOC with dozens of outgoing links): capped max node count in graph expansion prevents one note from dominating every answer's context.
- Oversized notes: heading-based chunking bounds individual chunk size; a note with no headings falls back to fixed-size chunking as an explicit exception path, not silent failure.
- Near-empty stub notes: filtered below a minimum content length before embedding, to avoid noise in the vector index.

## 15. Security Considerations

- Webhook: HMAC signature required; unsigned or invalid requests rejected before any git operation.
- Deploy key: read-only, repo-scoped, stored as a Docker secret.
- Network: Postgres and the local-model container not exposed outside the compose network; only the reverse proxy has a public port.
- The public demo URL puts auth in scope: basic auth at the reverse proxy on every route except /webhook (HMAC-protected) and /healthz, plus app-level rate limiting on /chat and /search — otherwise anyone with the URL can read your notes and exhaust free-tier quotas [D-004].

## 16. Suggested Phasing

For sprint planning, not a fixed schedule — slice further as needed.

1. Infra: Oracle host provisioned, Docker Compose skeleton, Postgres+pgvector running, deploy key working, manual clone verified.
2. Webhook + incremental indexing: signature verification, git-diff-based pipeline, frontmatter/chunk parsing, embeddings, upsert; eval question set written here [D-003].
3. Graph layer: edge computation from wikilinks/tags, alias resolution, recursive CTE traversal.
4. Retrieval: hybrid seed search, graph expansion, per-note best-chunk selection, fused ranking, provenance assembly.
5. Generation: provider interface, local model container, hosted provider integrations, fallback config, grounded prompt design; minimal web UI [D-004].
6. Evaluation + hardening: end-to-end eval run, retrieval/generation metrics, edge-case handling from section 14, security pass from section 15.

## 17. Interview Framing

One-line pitch: a self-hosted, graph-aware RAG system over a personal Obsidian vault — retrieves through the vault's actual link structure instead of treating notes as a flat document pile, stays available through a provider-fallback chain, and runs for $0 on free-tier infrastructure.

Talking points, each backed by section 13 above: why Postgres over a dedicated search/graph/vector stack; why embeddings are self-hosted specifically for privacy; why indexing is incremental and rename-aware instead of naive full-reindex; why there's no task queue; why the inference layer is a pluggable chain instead of a single API call; why Oracle over AWS for the free-tier host, with the actual numbers behind that call.

## 18. Working Convention (Sprints, ADRs, Deviations, Backlog)

One sprint per phase from §16, in `sprints/sprint-<N>/`: `sprint.md` (plan + outcome), `task_N_summary.md` per subtask, `handoff.md` at close. Decisions with a real rejected alternative go in `adr/` (Nygard-lite, numbered). Anything that changes what this spec says gets a `D-` entry in `DEVIATIONS.md` and is amended here in the same commit with a `[D-00N]` marker — so this file stays true while the change history stays visible. Anything noticed but not done now (idea, debt, bug) goes in `BACKLOG.md`. `INDEX.md` is the entry point; `AGENTS.md` briefs any engineer or AI agent taking over. Templates live in `sprints/_templates/` and `adr/_templates/`.
