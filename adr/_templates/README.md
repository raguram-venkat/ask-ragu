# ADR Templates — How To Use These

Write an ADR when a decision had a real alternative you seriously considered and rejected. Only one reasonable option → not an ADR, just a line in a task file.

Numbering: sequential across the project, regardless of sprint — 0001, 0002, … Never reused.

File name: `000N-short-kebab-case-title.md`, e.g. `0001-postgres-over-opensearch.md`.

Status:

- `proposed` — raised, not yet agreed. Resolve before the task that depends on it starts.
- `accepted` — in effect.
- `superseded by ADR-000X` — replaced. Keep the old file; add the link at the top.

Density: every field one to three sentences. If Context needs a paragraph, it's probably two decisions.

If accepting an ADR changes what SPEC.md says, it also needs a D-entry in DEVIATIONS.md and a `[D-00N]` marker in SPEC.md.

Worked example (ADR-0001):

> Context: OpenSearch doesn't natively express note-to-note links, and it's a second stateful JVM service for a vault that doesn't need that scale.
>
> Decision: Postgres + pgvector for full-text, vector, and graph retrieval in one datastore.
>
> Alternatives considered: OpenSearch (lexical/hybrid, no native graph); Neo4j + a vector DB (real capability, unjustified operational cost here).
>
> Consequences: One service to run and rebuild. Graph traversal limited to what SQL does well — fine at ≤ 2 hops.

Every ADR gets a row in INDEX.md and a link from the sprint.md or task file that prompted it.
