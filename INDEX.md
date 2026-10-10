# ask-ragu — Project Index

Single entry point. Graph-aware RAG over a private Obsidian vault, self-hosted for $0 on Oracle Cloud's Always Free tier.

Current status: Sprint 2 closed 2026-10-06 (local-first); Sprint 3 (Graph Layer) in progress: Tasks 1–2 done, Task 3 next. Sprint 1: Tasks 1–2 done; Task 3 blocked on Oracle A1 capacity; Task 7 (A1 retry runner on the Micro) keeps running; Tasks 4–6 wait for the A1 (D-008). Eval v0 drafts need the owner's rewrite before Sprint 4.
Last updated: 2026-10-10

## 30-minute reading order

1. This file (3 min)
2. SPEC.md §1-6 and §13 (10 min) — what the system is and why
3. DEVIATIONS.md (3 min) — what changed from the original plan
4. Each sprint's `sprint.md`: Goal + Outcome only (10 min)
5. ADRs, only for the decisions you're asked about

## Sprints

| Sprint | Phase (SPEC §16) | Status | One-liner |
|---|---|---|---|
| [sprint-1](sprints/sprint-1/sprint.md) | Foundations & Infra | parked — T4–T6 wait for A1 (D-008) | Compose stack on laptop and Oracle A1, HTTPS + auth, vault cloned via deploy key |
| [sprint-2](sprints/sprint-2/sprint.md) | Webhook & Incremental Indexing | closed 2026-10-06 (local-first) | Signed push / startup / CLI → rename-aware incremental sync, proven equal to a full index on the real vault |
| [sprint-3](sprints/sprint-3/sprint.md) | Graph Layer | in progress | Obsidian-style link resolution, tag/MOC hubs, bounded 2-hop expansion |
| [sprint-4](sprints/sprint-4/sprint.md) | Retrieval | planned | Lexical + vector → RRF → graph expansion → provenance context, proven by an ablation table |
| [sprint-5](sprints/sprint-5/sprint.md) | Generation, Chain & UI | planned | Config-ordered provider chain (hosted → local llama.cpp), validated citations, minimal UI |
| [sprint-6](sprints/sprint-6/sprint.md) | Evaluation & Hardening | planned | End-to-end eval, edge-case sweep, security/ops pass, CI, README + demo script |

## ADRs

| ADR | Decision | Status |
|---|---|---|
| [0001](adr/0001-postgres-over-opensearch.md) | Postgres full-text + pgvector over OpenSearch | accepted |
| [0002](adr/0002-graph-in-postgres-over-neo4j.md) | Graph in Postgres over a graph DB | accepted |
| [0003](adr/0003-self-hosted-embeddings.md) | Self-hosted embeddings (fastembed, bge-small) | accepted |
| [0004](adr/0004-incremental-git-diff-indexing.md) | Incremental git-diff indexing over full reindex | accepted |
| [0005](adr/0005-ack-fast-background-sync.md) | Ack-fast webhook + background task over sync/queue | accepted |
| [0006](adr/0006-config-driven-provider-chain.md) | Config-driven provider fallback chain | accepted |
| [0007](adr/0007-oracle-always-free-over-aws.md) | Oracle Always Free over AWS free tier | accepted |
| [0008](adr/0008-rrf-hop-decay-over-cross-encoder.md) | RRF + hop decay over a cross-encoder reranker | accepted |
| [0009](adr/0009-exclude-training-free-tiers.md) | Exclude free tiers that train on prompts | proposed |
| [0010](adr/0010-moc-hubs-over-folder-siblings.md) | MOC/tag hubs over folder-sibling edges | accepted |
| [0011](adr/0011-index-is-disposable.md) | Index is derived state: rebuild, don't back up | proposed |
| [0012](adr/0012-raw-sql-over-orm.md) | psycopg 3 + raw SQL over an ORM | accepted |
| [0013](adr/0013-caddy-duckdns-tls.md) | Caddy + DuckDNS for free TLS | proposed |
| [0014](adr/0014-auth-at-proxy-for-public-demo.md) | Basic auth at the proxy for the public demo | proposed |
| 0015 | Graph traversal implementation (to be written in Sprint 3, Task 3) | — |
| [0016](adr/0016-int8-bge-small-batch-1.md) | int8 bge-small, embedded one chunk at a time | accepted |
| [0017](adr/0017-index-freshness-settings-hash-code-versions.md) | Index freshness: settings hash + code versions; one index per schema | accepted |
| [0018](adr/0018-serialize-syncs-advisory-lock.md) | One sync at a time per index: advisory lock + coalescing runner | accepted |

Proposed = came out of planning research; review and accept (or supersede) before the dependent task starts.

## Deviations from SPEC.md

Full log in [DEVIATIONS.md](DEVIATIONS.md). Most recent 3:

- D-012 Links re-resolved vault-wide after every sync; name/alias collisions take a deterministic tie-break
- D-011 Syncs serialized across processes by a per-schema Postgres advisory lock
- D-010 Index settings or code version changes force a full index (settings hash); the system's clone is reset to the indexed commit

## Other root files

- [SPEC.md](SPEC.md) — living source of truth
- [BACKLOG.md](BACKLOG.md) — ideas, debt, bugs noticed but not scheduled
- [AGENTS.md](AGENTS.md) — briefing for any engineer or AI agent taking over

---

How to keep this current: update a sprint's row when it opens or closes (one-liner copied from its Outcome). Add an ADR row when one is written. Deviation text lives only in DEVIATIONS.md — here, just the latest 3 titles.
