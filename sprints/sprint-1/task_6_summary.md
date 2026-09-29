# Task 6 — Deploy workflow

Status: todo
Est: 60m
Spec: SPEC.md §11

What: `make deploy` pulls the code on the VM and rebuilds/restarts the stack; compose sets restart policies and CPU/memory limits.

Approach: SSH + `git pull` + `docker compose up -d --build` on the VM, building natively on arm64.

Read first:

- Compose: deploy.resources.limits, restart policies

Watch out for:

- Images built on your x64 laptop won't run on A1 — build on the VM (arm64 CI builds are in BACKLOG).
- RAM budget now: Postgres ~1 GB, app + embeddings ~1 GB, llama.cpp 3-4 GB (Sprint 5), rest for OS and page cache.
- Test `sudo reboot` once: everything must come back on its own.

Done when: A code change on the laptop reaches the VM with one command in under 3 minutes; the stack survives a reboot.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
