# PRD template (Fable fills this in)

Extends snarktank `create-prd`. Keep this document **tight** — its job is to lock the *decisions*
and *context*. The step-by-step detail lives in the task list (`references/definition-of-ready.md`),
not here.

```markdown
# <Feature> — PRD

**Blast radius:** low | medium | high   <!-- sets the autonomy + critic level; see SKILL.md dial -->

## 1. Summary
One paragraph: what we're building, for whom, and why now.

## 2. Goals / success criteria
- Measurable product-level outcomes. What "done and working" looks like to a user.

## 3. Non-goals (explicit)
- What this deliberately does NOT do. Prevents scope creep and wrong guesses.

## 4. Decisions already made
| Decision | Chosen | Rejected alternative | Why |
|---|---|---|---|
|  |  |  |  |
- Every architectural choice is made HERE, before execution — never deferred to Sonnet.

## 5. Context & constraints (from Phase 0 investigation)
- Existing patterns to follow (`file:line`), the APIs used + their quirks, versions, limits,
  auth model, and anything discovered by reading the real code.

## 6. Risks & mitigations
- Especially the safety/security model for medium+ blast radius. Each mitigation should become a
  **testable acceptance criterion**, not a hope.

## 7. Acceptance criteria (top-level)
- The checkable conditions for the whole feature. (Task-level criteria live in the task list.)

## 8. Out of scope / follow-ups
- Parked items, so they're captured without expanding this PRD.
```

## Effort & duration

Most of what this PRD scopes will be executed by Ralph/Sonnet, not a person — size it in
AI-native units, not human calendar time:

- **Effort** is a count (iterations, PRs, tasks) or, where useful, agent-hours/agent-days
  measured from real data already in the target repo (a ledger, run history) — never invented,
  and never copied forward from another PRD without checking the source still exists.
- **Calendar time** (days/weeks/sprints) only for a step a human must actually do, or a real
  soak/cadence wait — both must say which, explicitly.
- Never derive calendar time from AI effort via an assumed human work-week. That's exactly the
  human pace this convention exists to keep out.

## Notes for the author (Fable)

- If section 4 is thin, you haven't investigated enough — go back to Phase 0. A high-quality PRD
  is mostly *decisions already made* plus *context*, so the executor inherits judgment instead of
  making it.
- For **high blast radius**, section 6 is the most important part of the document: write the
  fail-safe behavior, the anti-spoof/abuse model, and the "what must never happen" list as
  explicit, testable requirements.
