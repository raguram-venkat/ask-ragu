# ask-ragu — Project Index

Single entry point. Graph-aware RAG over a private Obsidian vault, self-hosted for $0 on Oracle Cloud's Always Free tier.

Current status: planning done — next up is Sprint 1, Task 1
Last updated: 2026-09-28

## 30-minute reading order

1. This file (3 min)
2. SPEC.md §1-6 and §13 (10 min) — what the system is and why
3. DEVIATIONS.md (3 min) — what changed from the original plan
4. Each sprint's `sprint.md`: Goal + Outcome only (10 min)
5. ADRs, only for the decisions you're asked about

## Sprints

| Sprint | Phase (SPEC §16) | Status | One-liner |
|---|---|---|---|
| [sprint-1](sprints/sprint-1/sprint.md) | Foundations & Infra | planned | Compose stack on laptop and Oracle A1, HTTPS + auth, vault cloned via deploy key |
| [sprint-2](sprints/sprint-2/sprint.md) | Webhook & Incremental Indexing | planned | Push → HMAC-verified 202 → background git-diff sync → parse/chunk/embed/upsert |
| [sprint-3](sprints/sprint-3/sprint.md) | Graph Layer | planned | Obsidian-style link resolution, tag/MOC hubs, bounded 2-hop expansion |
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
| [0010](adr/0010-moc-hubs-over-folder-siblings.md) | MOC/tag hubs over folder-sibling edges | proposed |
| [0011](adr/0011-index-is-disposable.md) | Index is derived state: rebuild, don't back up | proposed |
| [0012](adr/0012-raw-sql-over-orm.md) | psycopg 3 + raw SQL over an ORM | proposed |
| [0013](adr/0013-caddy-duckdns-tls.md) | Caddy + DuckDNS for free TLS | proposed |
| [0014](adr/0014-auth-at-proxy-for-public-demo.md) | Basic auth at the proxy for the public demo | proposed |
| 0015 | Graph traversal implementation (to be written in Sprint 3, Task 3) | — |

Proposed = came out of planning research; review and accept (or supersede) before the dependent task starts.

## Deviations from SPEC.md

Full log in [DEVIATIONS.md](DEVIATIONS.md). Most recent 3:

- D-007 Graph expansion bounded per hop, not just in total
- D-006 Vault-specific exclusions and note_type priors
- D-005 Free tiers that train on prompts disabled by default

## Other root files

- [SPEC.md](SPEC.md) — living source of truth
- [BACKLOG.md](BACKLOG.md) — ideas, debt, bugs noticed but not scheduled
- [AGENTS.md](AGENTS.md) — briefing for any engineer or AI agent taking over

---

How to keep this current: update a sprint's row when it opens or closes (one-liner copied from its Outcome). Add an ADR row when one is written. Deviation text lives only in DEVIATIONS.md — here, just the latest 3 titles.
