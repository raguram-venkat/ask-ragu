# Deviations from SPEC.md

Every change to what SPEC.md says — scope change, design correction, ad hoc decision — logged the moment it's accepted. SPEC.md is amended in the same commit, with the `[D-00N]` marker on each changed line, so the spec stays true and this file keeps the history.

Format:

`- D-00N [sprint-N] <what changed> — <why> — <ADR-000X or task file> — SPEC §<sections amended>`

`sprint-0` = found during planning research, before any code.

---

- D-001 [sprint-0] Webhook no longer indexes synchronously: it verifies, returns 202, and runs sync as an in-process background task with a single-flight lock — GitHub fails deliveries not answered within 10 s, and embedding a large push on 2 ARM cores takes longer — ADR-0005 — SPEC §6, §8, §13
- D-002 [sprint-0] `folder_sibling` edges dropped; tags and MOC notes act as traversable hubs instead of materialized pairwise edges — this vault's folders (00 Meta … 04 Fleeting) encode note type, not topic, and a 50-link MOC would be 1,225 pairwise edges — ADR-0010 — SPEC §7, §9
- D-003 [sprint-0] Eval question set moved from Phase 6 to Sprint 2 — SPEC §12 said "built early" but §16 scheduled it last; questions written after tuning get unconsciously biased toward what already works — sprint-2/task_9 — SPEC §12, §16
- D-004 [sprint-0] Scope addition: minimal web UI, plus basic auth and rate limiting — the project will be demoed on a public URL, so §15's "auth out of scope while single-user" no longer holds — ADR-0014 — SPEC §6, §15, §16
- D-005 [sprint-0] Hosted providers carry a `trains_on_data` flag; training free tiers (e.g. Gemini free outside EU/UK/EEA) disabled by default — sending note snippets to a provider that trains on them breaks the §4 privacy principle — ADR-0009 — SPEC §10
- D-006 [sprint-0] Vault-specific rules: Templates/, .obsidian/, Bases/, Attachments/ excluded; dataview/base blocks, Templater tags and callout markers cleaned; note_type from folder used as a ranking prior — found from the real vault's folder layout — sprint-2/task_3 — SPEC §7, §8, §9
- D-007 [sprint-0] Graph expansion bounded per hop (fan-out cap), not only by a total node cap — a MOC or popular tag floods hop 1 before a total cap ever applies; also, Postgres can't LIMIT inside a recursive CTE term, so the implementation choice is deferred to ADR-0015 — sprint-3/task_3 — SPEC §9
