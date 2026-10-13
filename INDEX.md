# ask-ragu — Project Index

Single entry point. Graph-aware RAG over a private Obsidian vault, self-hosted for $0 on Oracle Cloud's Always Free tier (an E2.1.Micro, D-014).

Current status: Sprint 4 (Retrieval) in progress: Task 1 done, Task 2 (vector search) next; Task 7 (dev agent on open-weight models, ADR-0022) repo side done, harness + bake-off left. 2026-10-13: no A1 after ~4,100 attempts, so the host is the existing E2.1.Micro (D-014) and there is no local LLM — hosted open-weight providers, optional HF Space (D-015); Sprint 1 is un-parked (Task 3: prepare the Micro). Eval v0 drafts still need the owner's rewrite before any tuning.
Last updated: 2026-10-13

## 30-minute reading order

1. This file (3 min)
2. SPEC.md §1-6 and §13 (10 min) — what the system is and why
3. DEVIATIONS.md (3 min) — what changed from the original plan
4. Each sprint's `sprint.md`: Goal + Outcome only (10 min)
5. ADRs, only for the decisions you're asked about

## Sprints

| Sprint | Phase (SPEC §16) | Status | One-liner |
|---|---|---|---|
| [sprint-1](sprints/sprint-1/sprint.md) | Foundations & Infra | un-parked 2026-10-13 — T3–T6 on the Micro (D-014) | Compose stack on laptop and the Oracle Micro, HTTPS + auth, vault cloned via deploy key |
| [sprint-2](sprints/sprint-2/sprint.md) | Webhook & Incremental Indexing | closed 2026-10-06 (local-first) | Signed push / startup / CLI → rename-aware incremental sync, proven equal to a full index on the real vault |
| [sprint-3](sprints/sprint-3/sprint.md) | Graph Layer | closed 2026-10-10 (local-first) | Links resolved after every sync; query-time MOC/tag hubs; per-hop expansion ≤ 30 notes, p95 < 50 ms on the laptop; `askragu graph` CLI |
| [sprint-4](sprints/sprint-4/sprint.md) | Retrieval | in progress | Lexical + vector → RRF → graph expansion → provenance context, proven by an ablation table |
| [sprint-5](sprints/sprint-5/sprint.md) | Generation, Chain & UI | planned | Config-ordered provider chain (hosted open-weight → optional HF Space, D-015), validated citations, minimal UI |
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
| [0007](adr/0007-oracle-always-free-over-aws.md) | Oracle Always Free over AWS free tier | accepted (shape: ADR-0020) |
| [0008](adr/0008-rrf-hop-decay-over-cross-encoder.md) | RRF + hop decay over a cross-encoder reranker | accepted |
| [0009](adr/0009-exclude-training-free-tiers.md) | Exclude free tiers that train on prompts | proposed |
| [0010](adr/0010-moc-hubs-over-folder-siblings.md) | MOC/tag hubs over folder-sibling edges | accepted |
| [0011](adr/0011-index-is-disposable.md) | Index is derived state: rebuild, don't back up | proposed |
| [0012](adr/0012-raw-sql-over-orm.md) | psycopg 3 + raw SQL over an ORM | accepted |
| [0013](adr/0013-caddy-duckdns-tls.md) | Caddy + DuckDNS for free TLS | proposed |
| [0014](adr/0014-auth-at-proxy-for-public-demo.md) | Basic auth at the proxy for the public demo | proposed |
| [0015](adr/0015-per-hop-queries-over-recursive-cte.md) | Graph expansion as one query per hop, not one recursive CTE | accepted |
| [0016](adr/0016-int8-bge-small-batch-1.md) | int8 bge-small, embedded one chunk at a time | accepted |
| [0017](adr/0017-index-freshness-settings-hash-code-versions.md) | Index freshness: settings hash + code versions; one index per schema | accepted |
| [0018](adr/0018-serialize-syncs-advisory-lock.md) | One sync at a time per index: advisory lock + coalescing runner | accepted |
| [0019](adr/0019-lexical-ored-lexemes-over-websearch.md) | Lexical query = question's lexemes OR-ed, not websearch_to_tsquery | accepted |
| [0020](adr/0020-micro-host-over-waiting-for-a1.md) | Host on the existing E2.1.Micro instead of waiting for an A1 | proposed |
| [0021](adr/0021-hosted-open-weight-inference.md) | Hosted open-weight inference; no local model; optional HF Space | proposed |
| [0022](adr/0022-dev-agents-public-repo-only.md) | Dev agents on open-weight models see public-repo content only | proposed |

Proposed = came out of planning research; review and accept (or supersede) before the dependent task starts.

## Deviations from SPEC.md

Full log in [DEVIATIONS.md](DEVIATIONS.md). Most recent 3:

- D-015 No local-model container: hosted open-weight providers, optional private HF Space model
- D-014 Host is the existing E2.1.Micro (x86, 1 GB) instead of waiting for an A1
- D-013 Graph expansion runs one SQL query per hop instead of one recursive CTE

## Other root files

- [SPEC.md](SPEC.md) — living source of truth
- [BACKLOG.md](BACKLOG.md) — ideas, debt, bugs noticed but not scheduled
- [AGENTS.md](AGENTS.md) — briefing for any engineer or AI agent taking over: the whole working agreement (rewritten 2026-10-13 for open-model agents)

---

How to keep this current: update a sprint's row when it opens or closes (one-liner copied from its Outcome). Add an ADR row when one is written. Deviation text lives only in DEVIATIONS.md — here, just the latest 3 titles.
