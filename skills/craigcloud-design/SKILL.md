---
name: craigcloud-design
description: "The craigcloud visual language for Craig's own tools and sites -- measured dark palette, JetBrains Mono + Chakra Petch, self-explaining sections, and the accessibility rules that keep it usable. Read this BEFORE choosing any color, font, spacing or layout for anything on craigcloud.io or in his personal tooling -- status pages, dashboards, consoles, upload sites, internal web UIs -- and whenever Craig says: make this look good, make it match, use my theme, craigcloud style, make it look like a product, this page is ugly. Use spectrocloud-brand instead for anything customer-facing or Spectro-branded; this is for HIS surfaces, not the company's."
---

# craigcloud design

One visual language across every surface Craig owns, so that opening the status
page, the console, and an upload site feels like opening three parts of one
product rather than three projects.

**The stylesheet is the source of truth, not this document.**
`craigcloud.css` sits beside this file. Import it or inline it — never
re-derive the palette by eye, and never introduce a second one in a project.

```html
<link rel="stylesheet" href="craigcloud.css">
<!-- or, for a self-contained page, inline the file's contents in a <style> -->
```

Generators inline it. `stylesheet()` in `ai-lawnmower/console/console.py` is the
reference implementation: it reads this file's `:root` token block when present and
falls back to an embedded copy, so the page still renders if the skill is not
installed. (The status page that used to be the reference, `loop/status-page.py`,
was retired on 9/22/26 in favour of the console's work board.)

## What it looks like

Tech-noir, near-black, monospace, cyan. The aesthetic lives in the **frame** —
corner brackets, a masked grid, notched panels, bracketed section rules — and
**never in the data layer**. The standard way this look fails is neon text
nobody can read at 6am on a phone, so:

- **Neon is for accents and STATE only.** Body copy is high-contrast neutral.
- **Magenta is chrome.** At 5.31:1 it can never carry a data column.
- **Cyan is the one structural accent.** One accent per screen; anything else
  coloured that is not a status is a bug.
- **Committed dark.** There is no light mode; paint the background explicitly
  rather than inheriting it.

## The rules that are not negotiable

1. **Hue is never the only signal.** Every status carries a glyph *and* the
   word: `●` ok, `▲` warn, `✕` bad, `◆` running, `○` pending. The naive neon
   triad collapses to ΔE 9.1 under protanopia — ok and warn become the same
   colour. The palette's triad holds ΔE 23.9 worst case.
2. **Every section explains itself — behind an (i), not above the data.** Each
   heading carries a small circled `i` next to its title, and the `.cc-explain`
   line sits inside the heading, revealed on hover or on focus (which is what a
   click, and a tap on a phone, land as). Plain English, saying what it is and
   why it matters. Someone who was not in the design conversation must still be
   able to read the page — and someone who reads it daily must not pay a
   paragraph for it every time. Craig, 9/15/26: *"No need for it to take up
   space always. I never read it."*
   Reference implementation: `explain_toggle()` in `ai-lawnmower/console/console.py`,
   with the disclosure proven in a real browser by `loop/explain_toggle_check.mjs`.
   `craigcloud.css` deliberately does **not** ship the hide/reveal rules: other
   surfaces carry `.cc-explain` as a plain sibling paragraph with no toggle, and
   hiding it there would take their copy away with no way to get it back. Each
   surface opts in locally until Craig says otherwise.
3. **Body text ≥ 4.5:1 and ≥ 12px.** `--cc-dim` (4.7:1) is the floor and is for
   ornaments only.
4. **Touch targets ≥ 44px** with real spacing. A bevelled corner must not eat
   a tap zone.
5. **One animation, and only on genuinely live things.** Behind
   `prefers-reduced-motion: no-preference`, with a blanket kill switch for
   `reduce`. A glitching number is indistinguishable from a broken data feed.
6. **Visible focus.** `:focus-visible` outline in cyan. Never `outline: none`.
7. **Hierarchy by size and weight first, colour second.** If it only works in
   colour it fails in greyscale.
8. **Wide content scrolls inside its own container.** The body never scrolls
   horizontally.

## Type

| role | stack | notes |
|---|---|---|
| data, numbers, everything scanned | `--cc-mono` (JetBrains Mono) | raised x-height at fixed advance; survives 12px on a phone. Tabular by construction, so columns align. |
| headings, labels, tags | `--cc-disp` (Chakra Petch) | the only techno face here readable near body sizes |

Uppercase is fine for labels of three words or fewer and **always** needs
`letter-spacing: .08–.11em`. Never uppercase a sentence, a commit message, a
task title, or a monospace number.

## Components

`.cc-card` / `.cc-card.flag` · `.cc-row` (`.alert`, `.live`) · `.cc-big` +
`.cc-lbl` · `.cc-tag` (`.on`) · `.cc-wrap` + `table` (`tr.head`, `td.n`) ·
`.cc-h1` / `.cc-h2` + `.cc-explain` · `.cc-gl` glyphs · `.cc-pulse`.

Brackets (`.flag`) go **only** on the card asking for attention. On every card
they carry no information.

## Sparklines

Inline SVG, no library, no request. A single number is a point with no trend,
and a point cannot say whether 90% is healthy or falling. The one worked example was
`sparkline()` in the retired status page:
`git -C ~/code/ai-lawnmower show 5e5b26c:loop/status-page.py`.

## Where it is used

`ai-lawnmower` console and its work board · `upload-factory` ·
`mariners-lineup` (old-iPad browser baseline — verify there before shipping a
new CSS feature) · any craigcloud.io surface.
