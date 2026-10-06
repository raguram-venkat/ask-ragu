# Backlog

Noticed but not scheduled. One line each. If an item would change what SPEC.md says once done, it also needs a D-entry at that point — not before.

Types: `idea` (new capability) · `debt` (known shortcut to repay) · `bug`

Format: `- [type] <what> — <why it matters> — (found: sprint-N)`

When scheduled: move it into a sprint task and strike it through here with a pointer, e.g. `~~...~~ → sprint-4/task_7`.

---

- [idea] Cross-encoder reranker — only if the Sprint 4 ablation shows ranking, not recall, is the bottleneck — (found: sprint-0)
- [idea] Streaming answers (SSE) in /chat — perceived latency when the chain falls back to the slow local model — (found: sprint-0)
- [idea] Demo mode: index only notes with `publish: true` — lets interviewers use it without seeing private notes — (found: sprint-0)
- [idea] `obsidian://open` deep links on citations — one click opens the source note in local Obsidian — (found: sprint-0)
- [idea] Zero-downtime full reindex (shadow tables + swap) — only if a full reindex visibly blocks queries — (found: sprint-0)
- [idea] Vault health page in the UI (dangling links, orphans, hubs) — reuses Sprint 3's health report — (found: sprint-0)
- [idea] Question decomposition for multi-hop questions — only if eval shows 2-hop questions failing after graph expansion — (found: sprint-0)
- [idea] CD: GitHub Actions arm64 image build → GHCR → VM pulls — removes building on the VM — (found: sprint-0)
- [idea] Terraform (OCI provider) for VCN + instance — rebuilds become one command instead of console clicks; strong interview material — (found: sprint-1)
- ~~[debt] Resize A1 to 2 OCPU / 12 GB if it was acquired at 1/6 — needed before Sprint 5's local model — (found: sprint-1)~~ → sprint-1/task_7 (phase 2, D-009)
- [idea] Revisit ADR-0010 before Sprint 3: in the real vault every note has exactly one tag (= its `domain`), so tag hubs are disjoint domain clusters of 5–42 notes, not cross-cutting labels — (found: sprint-2/task_1)
- [debt] Synthetic fixture vault (~15 notes: aliases, same name in two folders, MOC, template, callouts, Markdown image, no-frontmatter note, dangling links, links in code) for whole-pipeline tests — deferred from sprint-2/task_4; parser/chunker use inline-string unit tests — (found: sprint-2/task_4)
- [debt] 8 code-heavy chunks (0.4%) exceed bge-small's 512 tokens and lose their tail in the vector — fix by capping chunks in tokens (tokenizer, no truncation) instead of chars, if the Sprint 4 eval shows misses on code notes — (found: sprint-2/task_5)
~~[debt] `## Part of` (parent-link metadata section, first heading in 704 of 748 notes) becomes a heading_path ancestor: in 277 notes the body is `###`, so chunks read "Title > Part of > X" and "Part of" is embedded + weight-A in tsv. Fix: metadata headings in .env, left out of heading_path — (found: sprint-2/task_6)~~ → sprint-2/task_6 (follow-up fix)
- [idea] Typed parent edge from the `## Part of` links (concept → MOC → parent MOC) for Sprint 3 hubs / ADR-0010 — (found: sprint-2/task_6)
- [idea] MOC `## Links` sections (lists of note names) score as high as definitions in vector search: useful as graph hubs, weak as LLM context — rank them down in Sprint 4 (note_type prior), keep them for expansion — (found: sprint-2/task_6)
~~[debt] Parser/chunker *code* changes aren't detected (settings_hash covers .env only), and `index --full` skips unchanged rows before rewriting their links/tags — add an INDEX_VERSION constant to the hash groups (bump it with such changes), or a `--rebuild` that truncates first — (found: sprint-2/task_8)~~ → sprint-2/task_8 (ADR-0017)
~~[debt] CLI and the app's runner can sync at the same time (the single-flight lock is per process) — a Postgres advisory lock in `sync()` would serialize them across processes — (found: sprint-2/task_8)~~ → sprint-2/task_8 (ADR-0018)
- [debt] On the VM the working-tree reset runs as root in the container, so rewritten files become root-owned on the host — pick the clone's owner / container user in Sprint 1 Tasks 5–6 — (found: sprint-2/task_8)
- [debt] Hit definition conflict: sprint-4/task_5 says "hit = any gold note in context", eval v0 says `gold` = all notes needed. Report both: hit@k (any gold) and full coverage@k (all gold; the real test for hop questions) — target: sprint-4/task_5 — (found: sprint-2/task_9)
- [debt] Overview questions vs "MOC chunks dropped" (sprint-4/task_4): an overview question's gold is a MOC, so dropping MOC chunks makes it unhittable. Decide: keep a MOC's intro/scope chunk but drop its link-list sections, and/or count an overview as covered when ≥ N of the MOC's member notes are in context — target: sprint-4/task_4 + task_5 — (found: sprint-2/task_9)
- [idea] Eval format v1: several acceptable answers per question — `gold` as alternatives (any one set answers it) plus `gold_all` for parts that must all appear; lets a question be answered by independent notes, linked or not — target: sprint-4/task_5 — (found: sprint-2/task_9)
- [idea] Retrieval metrics beyond hit@k/MRR: recall@k and full coverage@k, nDCG@k, context precision (share of context from gold notes), redundancy (chunks per note, near-duplicates) and diversity (distinct notes), graph contribution (gold reached only via expansion), refusal precision/recall incl. false refusals on answerable questions, everything broken down per question kind (single / hop / overview / unanswerable), stage latency p50/p95, context tokens vs budget — target: sprint-4/task_5 — (found: sprint-2/task_9)
- [idea] Every context item says why it's there: direct match, via a link from X, via MOC hub Y, via tag Z, with its score components — including why an overview/MOC note was pulled in — target: sprint-4/task_4 (assembly) + task_6 (/search) — (found: sprint-2/task_9)
- [idea] Multiple answer blocks: when several notes (linked or not) each answer the question, /chat returns separate blocks, each with its own sources and how it was reached, instead of one blended paragraph; say explicitly when the notes cover only part of the question — target: sprint-5/task_4 (prompt + validation) + task_5 (response shape {blocks[{text, citations}]}) — (found: sprint-2/task_9)
- [idea] Overview answers synthesize, never just list: an answer that only enumerates subtopics or note links counts as a failure; the prompt pulls the member notes' content and explains how the topic fits together — target: sprint-5/task_4 (prompt rule) + sprint-6/task_1 (rubric criterion "list-only") — (found: sprint-2/task_9)
- [idea] Generation metrics: citation precision (each cited note is in context and supports the claim), citation recall (gold notes cited), faithfulness (claims backed by context), completeness on multi-gold questions, refusal correctness, provider used + fallback rate, latency — target: sprint-6/task_1 — (found: sprint-2/task_9)
- [idea] Internal eval & retrieval dashboard (owner only; not the user UI): per query, the retrieved chunks with every score component (lexical, vector, RRF, hop decay, note_type prior), provenance, and gold hit/miss highlighted; experiment runs (one schema each, ADR-0017) side by side with the metric tables above; index status. Reads /search + the eval harness output; eval runs stored in their own schema/table (non-derivable data, ADR-0011), private; behind auth — target: sprint-4 (new task after task_6) — (found: sprint-2/task_9)
