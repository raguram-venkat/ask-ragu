# Task 4 — Grounded prompt + citation validation

Status: todo
Est: 75m
Spec: SPEC.md §10

What: A system prompt that answers only from delimited context, cites as [[Note Title]], and says when the notes don't cover it — then validates citations after generation.

Approach: Context blocks labelled with title + heading_path; after generation, extract [[...]] citations and check each against context titles; strip or flag unknowns; below-floor retrieval skips the LLM entirely.

Read first:

- Anthropic / OpenAI docs on grounding and citations

Watch out for:

- Note text is data, not instructions — clipped web sources can contain injection-looking text.
- Small local models follow citation formats poorly — validation matters most there.

Done when: On eval v0, no unvalidated citation reaches the UI.

---

Filled in while working

Files touched:

- 

Decisions made here:

- 

Gotchas:

- 
