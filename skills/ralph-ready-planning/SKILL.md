---
name: ralph-ready-planning
description: "Plan a coding project so completely that a fresh-context Sonnet, run unattended by Ralph, executes every task without deciding, guessing or asking -- investigate the real repo and APIs FIRST, then write a Definition-of-Ready PRD plus atomic task list, with Codex reviewing the diff cross-model. Use at the very start of a project when Craig says: plan this properly before we build, make this ralph-ready, I want a plan Sonnet can run unattended, investigate first then plan, this needs a definition of ready, set up the Fable-plan / Sonnet-execute / Codex-review pipeline. Use the prd skill for an ordinary feature PRD and ralph to convert a finished plan into prd.json; this is the heavier investigate-first pass that sits on top of both."
---

# Ralph-Ready Planning

The bottleneck in autonomous AI coding is **plan completeness, not execution.** Ralph runs a
**fresh context every iteration** — its only memory is `prd.json`, `progress.txt`, and git
history — so any ambiguity left in the plan becomes a wrong guess repeated at scale. This skill
is how the **planning model (Fable)** produces a plan complete enough that a cold Sonnet instance
never has to decide, guess, or ask.

Use it at the **start** of a project, on top of the snarktank flow (`@create-prd.md` →
`@generate-tasks.md` → `ralph`). It adds the four things those skills assume but don't enforce:
**investigate-first, a Definition-of-Ready bar, cross-model review routing, and a blast-radius
autonomy dial.**

## Prime directive

> **If a fresh Sonnet instance would have to decide, guess, or ask a question anywhere, the plan is not done.**

Everything below serves that one test.

## Model routing

| Stage | Model / tool | Produces | Notes |
|---|---|---|---|
| 0. Investigate | **Fable** | notes on real files / APIs / patterns / constraints | never skip — you can't spoon-feed what you didn't read |
| 1. PRD | **Fable** | `PRD.md` | what / for whom / why / reqs / non-goals / decisions / risks |
| 2. Task list | **Fable** | `prd.json` + `tasks.md` | atomic, Definition-of-Ready (`references/definition-of-ready.md`) |
| 3. Self-gap-check | **Fable** | revised plan | run the prime-directive test on every task |
| 4. Critic (optional) | **Codex** | gap list | high blast radius only (see dial) |
| 5. Execute | **Ralph → Sonnet** | commits + progress | `./scripts/ralph/ralph.sh --tool claude <max_iters>`; autonomous |
| 6. Code review | **Codex** | issue·severity·location·fix | cross-family; review the **diff vs the PRD** |
| 7. Final arch review | **Fable / Opus** | findings | only if structurally risky |

Fable touches only stages 0–4 and (rarely) 7 — all low-token. The high-volume grind (5) runs on
Sonnet, unattended. That is what makes limited Fable time viable.

## Procedure (as Fable)

**Phase 0 — Investigate (never skip).** Read the *actual* repo, target APIs, existing patterns,
and constraints before writing anything. You are gathering the exact file paths, signatures,
conventions, versions, and edge cases you will spoon-feed. Planning from imagination is the #1
cause of Ralph guessing wrong. Record concrete anchors you'll cite in tasks (e.g. "mirror
`internal/foo.go:80`"). If the plan builds a tool, CLI or integration, first check it does not
already exist — the https://axi.md catalog, `npm search`, PyPI, GitHub, and
`~/code/ai-lawnmower/REGISTRY.md`. The PRD records what was checked and the use case the
existing options lack; if nothing is lacking, adopt it instead of planning a build.

**Phase 1 — PRD.** Fill in `references/prd-template.md`. Keep it tight: scope, the decisions
you've *already made* (with the rejected alternative + why), non-goals, risks, and top-level
acceptance criteria. The detail lives in the task list, not here.

**Phase 2 — Decompose to Definition-of-Ready tasks.** Break the PRD into parent tasks → atomic
sub-tasks, each meeting **every** item in `references/definition-of-ready.md`, each completable in
one context window and self-contained for a cold instance. Write them into `prd.json`
(status-tracked) and a human-readable `tasks.md`.

**Phase 3 — Self-gap-check.** For every task, ask the prime-directive question. Any "it depends",
"choose the best", "handle errors appropriately", or missing file/signature ⇒ rewrite. This pass
is what lets you drop the multi-round Codex-on-PRD critique.

**Phase 4 — Critic gate (by blast radius).** See the dial below. High blast radius → **one**
targeted Codex critic pass framed as *"where would a fresh Sonnet get stuck, guess, or make an
undocumented decision?"* — not a broad review. Fold the gaps back in. Low blast radius → skip.

**Phase 5 — Hand to Ralph.** Ensure the repo has `CLAUDE.md` (per-iteration rules: do one atomic
task, run tests, commit, update `progress.txt`, and **append discovered patterns to AGENTS.md**)
and the `prd.json`. Kick off `./scripts/ralph/ralph.sh --tool claude <max_iters>` with a sane
iteration bound. Then walk away.

**Phase 6 — Codex review.** Hand Codex the **diff + the PRD** (not whole files). Ask for
issue·severity·location·fix and completeness vs the PRD. Cross-family is the point.

## Blast-radius → autonomy dial

Autonomy scales **inversely** with what a wrong move breaks. When in doubt, drop a notch.

| Blast radius | Example | Autonomy |
|---|---|---|
| **Low** — reversible, local | a CLI tool, a script, a pure refactor with tests | **Full Ralph.** Let it run to done. |
| **Medium** — service/infra, recoverable | an operator's CRUD + tests, an integration | **Hybrid.** Ralph the boilerplate; supervise + Codex-review the core logic, RBAC, auth. |
| **High** — irreversible / physical / privileged | opens a physical gate; mutates host networking; touches secrets or prod | **PRD-heavy + gated.** Over-specify the safety model (fail-safe defaults, anti-spoof) as testable acceptance criteria; **no unattended loop on the dangerous path**; mandatory Codex review + human sign-off. |

## Handoff formats (keep them disciplined)

- **Plan → execution:** the task carries everything (Phase 2). Never rely on chat context — Ralph won't have it.
- **Execution → review:** pass the **diff + the PRD**, not whole files.
- **Review → you:** structured — issue · severity · location · suggested fix.

## Files

- `references/prd-template.md` — the PRD structure Fable fills in (extends snarktank `create-prd`).
- `references/definition-of-ready.md` — the per-task checklist + the plan-level gate.
- External: snarktank/ai-dev-tasks (create-prd / generate-tasks / process-task-list), snarktank/ralph (the loop).
