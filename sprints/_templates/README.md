# Sprint Templates — How To Use These

One sprint = one phase from SPEC.md §16, not a fixed time-box. To open a sprint, copy the three template files into `sprints/sprint-<N>/` (renaming `task_template.md` to `task_1_summary.md`, `task_2_summary.md`, …). Don't edit `_templates/` itself unless changing the convention for everyone.

## The three files

`sprint.md` — plan and summary. Written before the sprint (Goal, Tasks, Definition of Done); Outcome filled in at close. Read this to know what a sprint was about.

`task_N_summary.md` — one per subtask, numbered within the sprint, each sized for one sitting (45-90 min). Top half is the plan, bottom half is filled in while working.

`handoff.md` — written once at close. Not a summary (that's sprint.md) — a snapshot: if someone opened this repo cold, what do they need to keep going?

## Density rule

Every field should read like: "Using FastAPI to set up a simple backend server, with routers to demarcate query from pull." One sentence a competent engineer understands without more context. If a field needs a paragraph, the task is probably two tasks.

## sprint.md fields

- Goal — one sentence.
- Spec reference — SPEC sections plus any D-entries this sprint implements.
- Tasks — one line per task file: checkbox, link, estimate.
- Definition of Done — 3-5 concrete, checkable bullets. "`docker compose up` brings up 2 healthy services" beats "infra works."
- Deviations from plan — D-ids raised during this sprint (text lives in DEVIATIONS.md).
- ADRs touched — written, accepted, or superseded this sprint.
- Outcome — at close: what got built and how it differs from the plan. The paragraph you'd say in an interview.

## task_N_summary.md fields

Plan (written when the sprint opens):

- Status — todo | doing | done | dropped (dropped needs a one-line reason).
- Est / Spec — time estimate; SPEC section.
- What — one sentence.
- Approach — 1-3 sentences: the how, as hints, not a tutorial.
- Read first — docs worth 10 minutes before starting.
- Watch out for — known edge cases and traps, found in advance.
- Done when — the concrete check.

Record (filled while working):

- Files touched — short list.
- Decisions made here — one line each; anything with a real rejected alternative becomes an ADR, linked here.
- Gotchas — what cost real debugging time, so it doesn't cost it twice.

## handoff.md fields

- System state — what runs, what doesn't, one paragraph.
- How to resume — the actual commands, where secrets live, what to check first.
- Open risks / unfinished threads.
- Relevant ADRs and deviations — links only.
- Next sprint starts at — one line.

## Where does a change go?

| It is… | It goes… |
|---|---|
| A change to what SPEC.md says | DEVIATIONS.md (D-entry) + amend SPEC.md with `[D-00N]` marker, same commit |
| A choice with a real rejected alternative | New ADR in `adr/` |
| Noticed but not doing now (idea, debt, bug) | One line in BACKLOG.md |
| A choice with no real alternative | A line under "Decisions made here" in the task file |

The first row is what stops drift: SPEC.md never goes stale, and the D-log shows exactly what cascaded from each change.

## At sprint close

1. Fill Outcome in sprint.md.
2. Write handoff.md.
3. Update the sprint's row in INDEX.md (status + one-liner from Outcome).
4. Resolve any `proposed` ADRs this sprint depended on.
