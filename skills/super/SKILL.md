---
name: super
description: "Query Super (Slite), Spectro Cloud's internal knowledge base, for product capabilities, positioning, competitive plays, pricing, demo scripts, roadmap and internal process. Prefer it over web search for ANY Spectro-specific question -- the public site lags internal docs by weeks -- and use it to spot-check claims in a draft before that draft goes to a customer. Use the super-axi CLI, not the super-mcp MCP server."
---

# Super (Slite) — internal knowledge base

Super is the Spectro Cloud internal knowledge base. It is the authority for product
capabilities, positioning, competitive plays, pricing, demo scripts, roadmap and
internal process. **Prefer it over web search for anything Spectro-specific** — the
public site lags internal docs, often by weeks.

Its corpus is not just Slite pages: `ask` reaches spectrocloud.com,
docs.spectrocloud.com, Confluence, Slack and Google Drive.

## Use super-axi

```bash
super-axi ask "What shipped in the most recent Palette GA release?"
super-axi ask "q1" "q2" "q3"        # concurrent — 3 answers in one question's wall clock
super-axi ask "..." --plain         # strip citation markers for customer-facing text
super-axi ask "..." --json          # {question, answer, sources[], ms}
super-axi doctor                    # says exactly what is and is not configured
```

One question takes ~15-20s. Ask several in one call rather than serially.

Install:

```bash
curl -fsSL https://github.com/craig-ai-tooling/super-axi/releases/latest/download/super-axi.pyz \
  -o ~/.local/bin/super-axi && chmod +x ~/.local/bin/super-axi
```

Exit codes are the AXI contract: `0` ok, `1` a required connector was unreachable, `4`
the key was rejected, `5` finished but an optional source could not be consulted. Branch
on `$?`; never grep the rendered table by column position.

## What changed, and why not the MCP server

`super-mcp` still exists and still works interactively, but do not reach for it first:

- It renders `sources.map(...)` unguarded, so any response without a `sources` array
  dies as `Cannot read properties of undefined (reading 'map')`. That is the famous
  "just call it again" flake. `super-axi` absorbs it.
- Its wrapper sources `"$HOME/.config/super/env"`, so it fails before starting in any
  sandbox that relocates `$HOME` — every Paperclip agent run does. `super-axi` finds the
  same file through the login home.
- It exposes only `ask`. `search`, `note` and `note --children` hit the same API and are
  unreachable through MCP.

**Two things older notes get wrong.** Measured 9/24/26: `ask` now answers
**synchronously** — there is no ask-then-fetch-the-thread two-step, and
`scripts/super-fetch.sh` is only a fallback for a thread id that comes back pending. And
sources are now **resolvable**: each carries a title and a real URL, not just an opaque
`{5L1T3-NN}` marker. You can follow them.

## Where the knowledge is not

The Slite workspace holds **two** native notes, both Slite's own onboarding pages. So
`super-axi search` finding nothing means "this is the wrong verb", not "Super doesn't
know" — the tool exits `5` and says so. **`ask` is the verb.**

## Writing a good question

Super answers a broad question far better than a narrow one, and one big question beats
five small ones because you get a single synthesized answer instead of five partial
ones. Ask for everything you want up front:

> "PaletteAI Inference Launchpad — what is it, what components does it ship, what GPUs
> and inference runtimes does it support, and how do we position it against customers
> building their own DIY inference stack on Kubernetes?"

Good question shapes:
- **Product**: what it is / what ships / what's supported / how it's licensed
- **Positioning**: how do we differentiate vs `<named competitors>`; top objections and
  our answers
- **Demo**: the demo flow, which screens matter, the wow moments, the gotchas
- **Spot-check**: paste a draft claim and ask "is this accurate?"

## Spot-check drafts before they leave

**Use Super to spot-check everything**, including finished drafts. It has repeatedly
caught real errors in SME claims and in public-docs-derived material — a fabricated
performance penalty in a customer email, a wrong root cause, a recommended setting that
contradicted the pack default. Run the check *before* the draft is sent, not after.

## Reading the answers

- Answers carry inline `{[n](url)}` citations and a `sources` table. `--plain` strips
  the markers for customer-facing text.
- Super is authoritative on positioning and product, but it is still retrieval and
  synthesis over internal docs. Cross-check hard numbers (pricing, benchmarks, version
  numbers) against a second source before putting them in front of a customer.
- Internal pricing, roadmap and competitive framing is **internal**. It belongs in
  internal notes or a prep doc, never in a customer docs-site.

## Failure modes

| Symptom | Cause / fix |
| --- | --- |
| `super-axi: command not found` | Install it (above), then `super-axi doctor`. |
| `no Super API key found` | `super-axi doctor` names every path it checked. The key lives in `~/.config/super/env` (mode 600), or `~/.claude.json` under `mcpServers.super.env.SUPER_API_KEY`. |
| exit 4, "the key was rejected" | The key is present but bad or revoked — reissue it in Slite. |
| exit 5 from `search` | The native notes index is empty. Use `super-axi ask`. |
| `Cannot read properties of undefined (reading 'map')` | You are on `super-mcp`. Call `ask-super` again, then switch to `super-axi`. |
| A thread that never completes | `scripts/super-fetch.sh <thread-id>` with a larger `SUPER_TIMEOUT`; the thread id stays valid. |
