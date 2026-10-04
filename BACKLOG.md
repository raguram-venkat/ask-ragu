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
