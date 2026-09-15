# craigcloud-design: the section explanation goes behind an (i)

Craig, 9/15/26: *"All the panels on the lawnmower dashboard have descriptions. I would
rather see the desc go into a little circle i next to the panel title that if you mouse
over or click shows the desc text. No need for it to take up space always. I never read
it."*

That shipped in `ai-lawnmower` (`loop/status-page.py`, PR against `craig-ai-tooling/ai-lawnmower`).
This repo carries the *written rule* that produced the old layout — rule 2 of
`craigcloud-design`, "Every section explains itself. A `.cc-explain` line under each
heading" — and it is described there as "the most commonly skipped rule and the one Craig
has asked for by name". Left as-is, the next agent to build a craigcloud surface
faithfully reproduces the thing he just asked to have taken away.

So the rule now describes the disclosure: the explanation still exists, still in plain
English, but it lives inside the heading behind a circled `i` and is revealed on hover or
focus.

## Deliberately NOT changed

`craigcloud.css` keeps `.cc-explain` exactly as it is. The other surfaces that use this
design system — `upload-factory`, `mariners-lineup`, the lawnmower console — render
`.cc-explain` as a plain sibling paragraph with no toggle anywhere in their markup. Adding
`display:none` to the shared class would delete their explanatory copy outright and leave
no affordance to bring it back. The hide/reveal rules stay local to the surface that has
the toggle (`status-page.py`'s own appended CSS, which is applied after the shared sheet
and therefore wins). Whether every craigcloud surface adopts the pattern is Craig's call,
not a side effect of this edit.

## Files touched

```allowlist
skills/craigcloud-design/SKILL.md
ralph/IMPLEMENTATION_PLAN.md
```

## Verify

- `make validate` exits 0.
- `grep -q 'circled `i`' skills/craigcloud-design/SKILL.md` exits 0.
- `git diff` touches no `.css` file: the shared stylesheet is unchanged.
