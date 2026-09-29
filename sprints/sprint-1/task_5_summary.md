# Task 5 — Vault deploy key + sparse clone

Status: todo
Est: 60m
Spec: SPEC.md §11

What: Read-only ed25519 deploy key on the vault repo, mounted as a Docker secret, used to clone only `.md` files into a named volume.

Approach: Generate the key on the VM (private half never leaves it); partial clone (`--filter=blob:none`) plus sparse-checkout for `*.md`, excluding Templates/, .obsidian/, Bases/, Attachments/.

Read first:

- GitHub docs: Managing deploy keys
- git: partial clone, sparse-checkout (non-cone patterns)

Watch out for:

- Pin github.com host keys in known_hosts from GitHub's published fingerprints — never `StrictHostKeyChecking=no`.
- ssh refuses keys readable by others: secret must be 0600 and owned by the container's (non-root) user.
- Sparse exclusions are defence in depth; the indexer's exclusion rules (Sprint 2) stay authoritative.

Done when: `docker compose exec app git -C /vault log -1` shows the latest vault commit; no image or PDF files in the volume.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
