# Task 4 — Heading-aware chunker + fixture vault

Status: todo
Est: 90m
Spec: SPEC.md §8, §14

What: Split cleaned bodies into chunks along heading boundaries with `heading_path` ("Note > H2 > H3"), max-size splitting and a stub filter — plus the synthetic fixture vault every test uses.

Approach: Walk headings as a stack; oversize sections split on paragraph boundaries with a small overlap; heading-less notes fall back to paragraph windows; drop chunks under the stub threshold.

Read first:

- markdown-it-py token stream (reliable headings and fences vs regex)

Watch out for:

- Headings inside code fences aren't headings.
- Embed `title + heading_path + text`, not bare text — a chunk titled "Pros and cons" means nothing alone.
- Fixture vault is synthetic (public repo), ~15 notes: aliases, same name in two folders, a MOC, a template file, callouts, a huge heading-less note, dangling links, links inside code.

Done when: Chunker tests pass; every chunk ≤ max size; no empty chunks.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
