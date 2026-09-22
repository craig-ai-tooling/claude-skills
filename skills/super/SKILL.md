---
name: super
description: "Query Super (Slite), Spectro Cloud's internal knowledge base, for product capabilities, positioning, competitive plays, pricing, demo scripts, roadmap and internal process. Prefer it over web search for ANY Spectro-specific question -- the public site lags internal docs by weeks -- and use it to spot-check claims in a draft before that draft goes to a customer. The ask-super MCP tool never returns the answer directly; this skill covers the required two-step ask-then-fetch plus the transient first-call error."
---

# Super (Slite) — internal knowledge base

Super is the Spectro Cloud internal knowledge base. It is the authority for
product capabilities, positioning, competitive plays, pricing, demo scripts,
roadmap and internal process. **Prefer it over web search for anything
Spectro-specific** — the public site lags internal docs, often by weeks.

## READ THIS BEFORE THE FIRST CALL

**The first `ask-super` call very often fails with:**

```
Error: Cannot read properties of undefined (reading 'map')
```

This is transient and it is not your fault — **immediately call `ask-super` again with the same
question.** The retry succeeds. Do not report it as an outage, do not switch to web search, do not
tell the user Super is broken. Just fire it again.

Because of this, the reliable pattern is: **send the ask, and if it errors, resend it in the very
next tool block.** When you're asking several questions, fire them all at once — any that error
get resent together, so you lose one round trip, not one per question.

## THE ONE THING TO KNOW

`mcp__super__ask-super` **never returns an answer.** It always replies:

> "The answer is still being prepared. Fetch it with GET /v1/threads/`<id>` in ~15s."

Re-asking does **not** return the pending answer — it creates a brand-new thread
and you loop forever. The workflow is *always* two steps:

```
1. mcp__super__ask-super   -> note the thread id in the reply
2. scripts/super-fetch.sh <thread-id>
```

`scripts/super-fetch.sh` ships with this skill (run it by its full path under the
installed skill directory, e.g. `~/.claude/skills/super/scripts/super-fetch.sh`). It
polls until `status: completed`, reads the API key from `~/.claude.json`, and never
echoes it. It needs `curl` and `jq`.

```bash
scripts/super-fetch.sh 6YnJGYK4jxsy3g            # poll until answered (default)
scripts/super-fetch.sh 6YnJGYK4jxsy3g --json     # raw JSON
scripts/super-fetch.sh 6YnJGYK4jxsy3g --once     # single attempt, no polling
```

Without the script, call the API directly:

```bash
KEY=$(jq -r '.mcpServers.super.env.SUPER_API_KEY
  // (.projects | to_entries[] | .value.mcpServers.super.env.SUPER_API_KEY)' \
  ~/.claude.json | grep -v '^null$' | head -1)
curl -s -H "x-slite-api-key: $KEY" "https://api.slite.com/v1/threads/<thread-id>" \
  | jq -r '.rounds[]?.answer'
```

## Ask several at once

Threads are independent and answer in parallel. When you have three questions,
fire all three `ask-super` calls in **one** message, collect the three thread
ids, then fetch them all. Do not serialize — each round trip is ~15-30s.

## Writing a good question

Super answers a broad question far better than a narrow one, and one big
question beats five small ones because you get a single synthesized answer
instead of five partial ones. Ask for everything you want up front:

> "PaletteAI Inference Launchpad — what is it, what components does it ship,
> what GPUs and inference runtimes does it support, and how do we position it
> against customers building their own DIY inference stack on Kubernetes?"

Good question shapes:
- **Product**: what it is / what ships / what's supported / how it's licensed
- **Positioning**: how do we differentiate vs `<named competitors>`; top
  objections and our answers
- **Demo**: the demo flow, which screens matter, the wow moments, the gotchas
- **Spot-check**: paste a draft claim and ask "is this accurate?"

## Spot-check drafts before they leave

**Use Super to spot-check everything**,
including finished drafts. It has repeatedly caught real errors in SME claims
and in public-docs-derived material — a fabricated performance penalty in a
customer email, a wrong root cause, a recommended setting that contradicted the
pack default. Run the check *before* the draft is sent, not after.

## Reading the answers

- Answers cite internal sources as `{5L1T3-NN}` markers. **Those ids are not
  resolvable** from the API response — treat them as "grounded in an internal
  doc, not independently verified". Strip them from anything customer-facing.
- Super is authoritative on positioning and product, but it is still a
  retrieval-and-synthesis layer over internal docs. Cross-check hard numbers
  (pricing, benchmarks, version numbers) against a second source before putting
  them in front of a customer.
- Internal pricing, roadmap and competitive framing from Super is **internal**.
  It belongs in internal notes or a prep doc, never in a customer docs-site.

## Failure modes

| Symptom | Cause / fix |
| --- | --- |
| `Cannot read properties of undefined (reading 'map')` | Transient MCP error. Just call `ask-super` again. |
| Every call says "still being prepared" | You're re-asking instead of fetching. Use `scripts/super-fetch.sh`. |
| `status=processing` forever | Raise `SUPER_TIMEOUT` (default 180s) and re-run the fetch; the thread id stays valid. |
| `FATAL: no SUPER_API_KEY found` | Key lives in `~/.claude.json` under `mcpServers.super.env.SUPER_API_KEY`, possibly nested under `.projects[]`. |

## Setup

`ask-super` comes from the Super MCP server, which has to be connected in Claude Code
first. The fetch script reads the same `SUPER_API_KEY` from `~/.claude.json`.
