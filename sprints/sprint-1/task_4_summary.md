# Task 4 — Public HTTPS + auth at the proxy

Status: todo
Est: 75m
Spec: SPEC.md §11, §15 · D-004

What: Caddy container terminates TLS for a free DuckDNS subdomain, reverse-proxies to the app, and requires basic auth everywhere except /webhook and /healthz.

Approach: DuckDNS record → VM public IP; Caddy fetches a Let's Encrypt cert via HTTP-01 on port 80; password hashed with `caddy hash-password`, kept in .env.

Read first:

- Caddy: Automatic HTTPS
- Caddy: reverse_proxy and basic auth directives

Watch out for:

- Oracle has two firewalls: the VCN security list and the Ubuntu image's own iptables rules (with a REJECT rule). Open 80/443 in both, insert ACCEPT above the REJECT, persist it. Don't layer ufw on top.
- Persist Caddy's /data volume or every rebuild re-issues certs and hits Let's Encrypt rate limits.
- /webhook must stay reachable without basic auth — GitHub can't send it; HMAC protects it (Sprint 2).

Done when: From your phone on mobile data: `/healthz` → 200, `/` → 401, `/` with credentials → 200.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
