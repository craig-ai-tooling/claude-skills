---
name: exec-doc-generator
description: Generate polished 2-page executive PDF documents (HTML+Puppeteer). Merges customer brand colors with Spectro Cloud branding. Pinned footers, stat cards, timelines, and professional layouts.
---

# Executive Document Generator

Build polished, executive-grade 2-page PDF documents as HTML files rendered via Puppeteer. Used for customer-facing POC overviews, solution summaries, architecture briefs, and similar deliverables.

## When to Use

- User asks for an executive summary, POC overview, or customer-facing doc
- User wants a "nice looking" or "PDF" document for a customer
- Building deliverables for customer leadership or stakeholders

## Design System

### Page Layout Rules

**CRITICAL — these are non-negotiable:**

1. **Exactly 2 pages** — content must fit cleanly, no spill
2. **Pinned footers** on every page — footer sticks to page bottom regardless of content height
3. **Page structure** uses flex column with `min-height: 100vh` and footer with `margin-top: auto`
4. **Letter size** with tight margins: `@page { size: letter; margin: 12px 22px; }`
5. **Print-safe colors** — always set `-webkit-print-color-adjust: exact`
6. **Body background MUST be `var(--paper)` (`#F7F1ED`)** — the warm cream Paper tone is a core brand element. NEVER use `#FFFFFF` or `white` as the body/page background. White is only for card surfaces (`--surface`).
7. **`@media print` block is REQUIRED** — must include `break-inside: avoid` on `.stat-card`, `.track-card`, `.scope-banner`, `.success-box`, and `break-after: avoid` on `.section-title`. Without this, components split across page boundaries.
8. **Font import MUST use `<link>` tag** in `<head>`, NOT `@import` inside `<style>`. `@import` causes font loading failures in Puppeteer PDF rendering.

### Spectro Cloud Brand

READ the `spectrocloud-brand` skill for the complete 2025 brand palette, design principles, logos, icons, and messaging. Key values for quick reference:

| Token | Hex | Role |
|-------|-----|------|
| Tranquil Teal | `#1F7A78` | SC identity, `--teal` |
| Paper | `#F7F1ED` | Brand background, `--paper` |
| Ink | `#012121` | Brand text, `--ink` |
| Gold Leaf | `#F0BE65` | Warm accent |
| Tea Green | `#9EB277` | Soft accent |

### Color Scheme Strategy

**Always merge customer brand colors with Spectro Cloud teal.** Extract 2-3 primary colors from the customer's website/brand:

| Role | Purpose | Example (banking customer) |
|------|---------|---------------------------|
| `--primary` | Headers, stat numbers, borders | Deep navy `#0A1628` |
| `--primary-mid` | Secondary elements, badges — **MUST differ from `--primary`** | Mid navy `#162D50` |
| `--accent` | Highlights, decorative accents | Gold `#C5963A` |
| `--teal` | Spectro Cloud identity (always present) | `#1F7A78` |
| `--green` | Success/positive indicators | `#1A7A4C` |
| `--ink` | Body text | `#012121` |
| `--paper` | Page background | Warm cream `#F7F1ED` |
| `--surface` | Card backgrounds | White |
| `--border` | Card/table borders | Light gray `#D0D5DD` |
| `--text-dim` | Secondary text | Muted gray `#4A5568` |

**Color enforcement rules:**
- `--primary-mid` MUST be visibly different from `--primary`. If the customer has only one dark color, lighten it 15-20% for `--primary-mid` (e.g., darken `#1B3A4B` → mid `#2C5F7A`). Never set them identical.
- `--paper` MUST always be `#F7F1ED`. `--teal` MUST always be `#1F7A78`. These are Spectro Cloud brand constants.

Also define glow variants for subtle backgrounds:
- `--accent-glow: rgba(accent, 0.10)`
- `--primary-glow: rgba(primary, 0.06)`

**For SC-only docs (no customer co-branding):**
Use the SC palette directly: `--primary: #043736`, `--accent: #F0BE65`, `--teal: #1F7A78`. Use Tea Green or Gold Leaf for highlights. Keep Paper `#F7F1ED` as background.

**How to pick customer colors:**
- Visit the customer's website, note their primary brand color and a secondary/accent
- Dark colors → use for `--primary` (headers, stats)
- Bright/accent colors → use for `--accent` (highlights, decorative elements)
- When in doubt, use deep blues/grays as primary — they're universally professional
- The `--teal` and `--paper` values should always reflect Spectro Cloud branding

### Typography

- **Font:** Plus Jakarta Sans via `<link>` tag (NOT `@import`). Font stack: `'Plus Jakarta Sans', 'Trebuchet MS', -apple-system, sans-serif`
- **Brand weight hierarchy:** ExtraLight (200) for display headlines, Medium (500) for subheads, Regular (400) for body, Light (300) for quotes
- **Exec doc weight hierarchy** (compact 2-page format needs heavier weights for legibility at small sizes): 800 for h1/stats, 700 for section titles, 600 for labels, 400 for body
- **Sizes:** h1: 24px, section titles: 10px uppercase, body: 10-11px, labels: 9px, fine print: 8px
- **Import:** Include weights 200-800: `wght@200;300;400;500;600;700;800`

### Component Library

READ the `references/components.md` file for the full HTML/CSS component patterns. Key components:

1. **Header** — Gradient banner with logo row, badge, h1, and executive summary paragraph
2. **Stat Cards** — 4-column grid with large numbers, labels, and detail text
3. **Data Strip** — Horizontal segmented bar (e.g., data centers, phases)
4. **Hardware/Stack Table** — Compact table with themed header row
5. **Scope Banner** — Dark gradient callout with pill tags
6. **Track Cards** — Side-by-side cards with icon headers and bullet lists
7. **Stack Strip** — Horizontal component strip with icons and labels
8. **Integration Pills** — Inline pill badges with colored dots
9. **Success Box** — 2-column criteria grid with checkmark header
10. **Timeline** — Horizontal timeline with dots and gradient connector
11. **Callout** — Bordered text box for next steps or key info
12. **Verdict Cards** — Icon + text cards for key decisions

### Required CSS Classes (do not invent new ones)

Only use these class names — they are defined in `references/components.md`:

`.page` `.page-break` `.container` `.header` `.header-inner` `.logo-row` `.logo-text` `.logo-divider` `.badge` `.section-title` `.stat-grid` `.stat-card` `.stat-number` `.stat-label` `.stat-detail` `.dc-strip` `.dc-strip-item` `.dc-name` `.dc-hosts` `.dc-label` `.dc-vms` `.dc-badge` `.dc-badge-active` `.dc-badge-migrate` `.hw-table` `.scope-banner` `.scope-pills` `.scope-pill` `.track-grid` `.track-card` `.track-card-header` `.track-card-body` `.dot-navy` `.dot-accent` `.dot-teal` `.icon-wrap` `.stack-strip` `.stack-strip-item` `.stack-icon` `.stack-label` `.stack-desc` `.integration-row` `.int-pill` `.int-dot` `.success-box` `.timeline` `.timeline-step` `.tl-dot` `.tl-label` `.tl-desc` `.verdict` `.verdict-icon` `.callout` `.page-footer` `.footer-left` `.footer-right` `.footer-page`

Track cards MUST use a dot color class (`dot-navy`, `dot-accent`, or `dot-teal`) on the `.track-card-body` div. Without it, bullets have no visible styling.

**Icon enforcement:** Track card headers, stack strip items, and verdict cards MUST use **emoji characters** (e.g., 🏭 🤖 ☸️ 🐧 💾 🔒 📊) inside `.icon-wrap` or `.stack-icon` divs. Do NOT substitute text abbreviations ("K8s", "OS", "PX"), single letters ("I", "A"), or CSS-styled spans. Emojis render cross-platform in Puppeteer and provide visual differentiation that text cannot.

### Page Footer Pattern

Use the inline SVG from `assets/spectrocloud-logo-horizontal-currentcolor.svg` (NOT the old 148x57 website version). This SVG uses `fill="currentcolor"` with `fill-rule="evenodd"` and has **compound paths** that correctly render letter counters (o, p, e, d holes) in Puppeteer. Set `color: var(--ink)` and `style="height: 14px; width: auto;"` on the SVG element.

```html
<div class="page-footer">
  <div class="footer-left">Confidential — Prepared for [Customer] Leadership</div>
  <div class="footer-right">
    <div class="footer-page">Page N of 2</div>
    <!-- READ and inline assets/spectrocloud-logo-horizontal-currentcolor.svg here -->
    <!-- It MUST have: viewBox="0 0 501 192", fill="currentcolor", fill-rule="evenodd" -->
    <!-- Add: style="height: 14px; width: auto; color: var(--ink); opacity: 0.6;" -->
  </div>
</div>
```

**CRITICAL:** For the footer SVG, READ and inline the content of `assets/spectrocloud-logo-horizontal-currentcolor.svg`. Do NOT use the old 148x57 viewBox website SVG — it has separate paths per letter part and letter counters (o, p, e, d, C) will render as solid blobs in Puppeteer. The currentcolor SVG has compound paths that work correctly.

The SVG wordmark uses `currentcolor`, so set `color` on the parent to control the text portion.

**Three logo SVG variants (all in `assets/`, all use compound paths with `fill-rule="evenodd"`):**
- **Footer (light background):** `spectrocloud-logo-horizontal-currentcolor.svg` — viewBox `0 0 501 192`, `fill="currentcolor"` with `fill-rule="evenodd"`. Set `color: var(--ink)` on the SVG element. Uses compound paths so letter counters (o, p, e, d) render correctly.
- **Header (dark background):** `spectrocloud-logo-horizontal-knockout-white.svg` — Same viewBox, `fill="#fff"` with `fill-rule="evenodd"`.
- **DEPRECATED:** `spectrocloud-logo-horizontal.svg` — the old website SVG (viewBox `0 0 148 57`) has separate paths per letter part. Do NOT use this for Puppeteer/PDF — the letter holes (o, p, e, d, C) fill solid regardless of fill-rule. Use the `currentcolor` variant instead.

**Logo enforcement:** The header logo-row MUST include the knockout white SVG. Do NOT substitute text, initials, badges, or placeholder graphics for the Strata mark. "Do not try to recreate the logo" is an explicit brand rule.

**Footer text enforcement:** Footer left text MUST be `Confidential — Prepared for [Customer] Leadership`. Do NOT use page descriptions, document titles, or other text in the footer-left position.

See `references/components.md` for the full inline SVG in both header and footer patterns.

### Easter Egg (REQUIRED)

Every generated document MUST include these meta tags in the HTML `<head>`. They appear only in PDF document properties (File > Properties), not visually on any page:

```html
<meta name="author" content="Craig Smith">
<meta name="creator" content="Yes, I made this. You're welcome.">
```

Also include an HTML comment before `</body>`:
```html
<!-- You're welcome. — CS -->
```

Always include these — no exceptions.

### Page Wrapper Pattern

Each page MUST be wrapped:

```html
<div class="page">
  <!-- header (page 1 only) -->
  <div class="header">...</div>
  <!-- content -->
  <div class="container">...</div>
  <!-- footer OUTSIDE container, INSIDE page -->
  <div class="page-footer">...</div>
</div>

<div class="page page-break">
  <div class="container">...</div>
  <div class="page-footer">...</div>
</div>
```

### CSS for Pinned Footer

```css
.page {
  min-height: calc(100vh - 24px);
  display: flex;
  flex-direction: column;
}
.page > .container, .page > .header { flex-shrink: 0; }
.page > .page-footer { margin-top: auto; }

.page-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 34px 0;
  border-top: 2px solid var(--teal);
}
```

## Puppeteer Rendering

READ `references/puppeteer-render.md` — the canonical render reference shared with `slide-deck-generator`. It covers the non-negotiables (font loading via `<link>`, `-webkit-print-color-adjust: exact`, `networkidle0`), emoji flex-centering, SVG compound-path/letter-counter rules, and page-break rules.

Render with the shipped script instead of retyping it: `node assets/generate-pdf.mjs <input.html> <output.pdf>`.

## Workflow

1. **Identify customer brand colors** — check their website or existing materials
2. **Pick a page 1 / page 2 structure** from the templates (READ `references/components.md`)
3. **Write the HTML** with all CSS inline in a `<style>` block (no external stylesheets)
4. **Test fit** — if content spills past 2 pages, tighten padding/margins/font sizes
5. **Generate PDF** via puppeteer
6. **Iterate** — common fixes: reduce `margin-bottom`, shrink font sizes, tighten `padding`

## Typical Page 1 / Page 2 Layouts

**POC Overview:**
- P1: Header → Stat Cards → DC/Environment Strip → Infrastructure Table → Scope Banner
- P2: Approach Cards → Track Cards → Stack Strip → Integration Pills → Success Criteria → Timeline → Next Steps

**Solution Brief:**
- P1: Header → Problem Statement → Current State Cards → Challenges Grid
- P2: Solution Architecture → Benefits Cards → Comparison Table → Next Steps → Timeline

**Architecture Summary:**
- P1: Header → Architecture Diagram Description → Component Table → Integration Points
- P2: Deployment Model → Security Model → Operational Model → Timeline → Contacts

## Spacing Cheat Sheet (for fitting on 2 pages)

If content overflows, reduce in this order:
1. `@page margin` — go as low as `10px 20px`
2. `.container padding` — go as low as `10px 30px`
3. `.header padding` — reduce vertical padding
4. `margin-bottom` on components — go from 14px → 10px → 8px
5. Font sizes — reduce by 1-2px
6. Card padding — reduce by 2-4px
7. Table cell padding — reduce by 2-3px
8. As last resort, remove or combine sections
