# ADR-0013: Caddy + DuckDNS for free TLS

Status: proposed
Date: 2026-09-28
Sprint: sprint-0 (planning)

## Context

GitHub webhooks and the demo need a stable HTTPS URL; budget is $0.

## Decision

Free DuckDNS subdomain pointing at the VM; Caddy obtains and renews Let's Encrypt certificates automatically.

## Alternatives considered

- Cloudflare Tunnel — no open ports, but needs your own domain on Cloudflare; quick tunnels have random, changing URLs (bad for webhooks).
- nip.io / sslip.io — shared domains hit Let's Encrypt rate limits.
- nginx + certbot — more moving parts for the same result.

## Consequences

- Ports 80/443 must be open in both Oracle firewalls.
- Caddy's data volume must persist or certificates get re-issued every rebuild.
