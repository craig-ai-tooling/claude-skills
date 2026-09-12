---
name: slide-deck-generator
description: Generate a branded Spectro Cloud presentation slide deck -- either 16:9 HTML rendered to PDF via Puppeteer (title, divider, content, quote, timeline, table, and closing layouts) or a Google Slides deck with a shareable link, copied and filled from the 2026 Corporate Template via gws. References spectrocloud-brand for colors, typography, and logos. Owns projected decks only -- for a long-form writeup use doc-writer, for a 1-2 page executive PDF use exec-doc-generator, and for a multi-page docs site use docs-site-generator. See the Deliverable Routing table in doc-writer.
---

# Slide Deck Generator

PDF route: assets/generate-pdf.mjs

Build branded presentation slide decks as HTML files rendered to PDF via Puppeteer. Based on the official 2026 Spectro Cloud Google Slides templates. Used for customer presentations, internal reviews, solution overviews, and technical briefings.

## When to Use

- User asks for a slide deck, presentation, or slides
- User wants a "deck" or "pitch" for a customer or internal audience
- Building materials for meetings, QBRs, webinars, or conferences
- Any request that implies multiple sequential visual pages meant for projection or screen sharing
- Two output forms live here: a rendered PDF (see PDF Generation below) or an editable Google Slides link (see Google Slides Output below)

Not this deliverable? See the Deliverable Routing table in the `doc-writer` skill: it covers long-form writeups, 1-2 page executive PDFs, and multi-page docs sites.

## Brand Foundation

READ the `spectrocloud-brand` skill for authoritative colors, typography, logos, and messaging. This skill defines slide-specific layout and sizing rules; all visual identity comes from the brand skill.

Key brand references:
- Colors: `spectrocloud-brand/references/colors.md`
- Messaging and boilerplates: `spectrocloud-brand/references/messaging.md`
- Logo SVGs: `spectrocloud-brand/assets/spectrocloud-logo-horizontal.svg` (light bg) and `spectrocloud-brand/assets/spectrocloud-logo-horizontal-knockout-white.svg` (dark bg)
- Brand icons: `spectrocloud-brand/assets/icons/` (Diamond, SquaresFour, ShuffleAngular, etc.)

## Slide Sizing and Page Setup

All slides use **16:9 landscape** at **1280x720** viewport.

```css
@page { size: 1280px 720px; margin: 0; }
html, body { margin: 0; padding: 0; width: 1280px; }
.slide {
  width: 1280px; height: 720px;
  position: relative; overflow: hidden;
  page-break-after: always;
  box-sizing: border-box;
  -webkit-print-color-adjust: exact;
}
.slide:last-child { page-break-after: avoid; }
```

## CSS Variables

```css
:root {
  --teal: #1F7A78;
  --teal-dark: #005B5B;
  --teal-darkest: #043736;
  --green: #9EB277;
  --gold: #F0BE65;
  --gold-dark: #DE8D2A;
  --orange: #B94B01;
  --lilac: #7E5C8E;
  --lilac-dark: #441647;
  --paper: #F7F1ED;
  --ink: #012121;
  --neutral-1: #E0DCD7;
  --neutral-3: #9E9C9C;
  --neutral-4: #3C4949;
  --surface: #FFFFFF;
}
```

## Typography for Slides

Font: Plus Jakarta Sans (Google Fonts). Slides use larger sizes than exec-docs since they are projected.

**Load the font via `<link>` tags in `<head>` - NOT `@import` inside `<style>`.** `@import` causes font loading failures in Puppeteer rendering (decks silently fall back to Trebuchet MS).

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700;800&display=swap" rel="stylesheet">
```

```css
body { font-family: 'Plus Jakarta Sans', 'Trebuchet MS', sans-serif; }
```

| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| Title slide headline | 48-56px | 200 (ExtraLight) | Brand display weight |
| Slide title (h2) | 32-36px | 500 (Medium) | Top of content slides |
| Subtitle / tagline | 20-24px | 300 (Light) | Below headlines |
| Body text | 18-22px | 400 (Regular) | Main content |
| Bullet points | 18-20px | 400 | Left-aligned lists |
| Labels / captions | 14-16px | 600 (SemiBold) | Card labels, axis labels |
| Footer text | 11-12px | 400 | Copyright, page info |
| Stat numbers | 40-48px | 800 (ExtraBold) | Large metric callouts |

## Slide Structure Pattern

Every slide follows a three-zone layout:

```
+--[Header Bar]-------------------------------------------+
|  [Logo]                              [Slide Title]      |
+----------------------------------------------------------+
|                                                          |
|                   [Content Area]                         |
|                  580-620px height                        |
|                                                          |
+--[Footer]------------------------------------------------+
|  (c) 2026 Spectro Cloud. All rights reserved.           |
+----------------------------------------------------------+
```

### Header Bar

Height: 56-64px. Background: `var(--teal-darkest)` or slide-specific color. Contains the knockout-white logo (left, ~90px wide) and optional slide title (right-aligned or centered, white text).

```css
.slide-header {
  height: 60px; padding: 0 48px;
  background: var(--teal-darkest);
  display: flex; align-items: center; justify-content: space-between;
}
.slide-header .logo { height: 28px; }
.slide-header .title { color: #fff; font-size: 16px; font-weight: 500; }
```

### Content Area

Padding: 40-48px horizontal, 32-40px vertical. Background varies by slide type.

### Footer

Height: 36-40px. Pinned to bottom of slide.

```css
.slide-footer {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 36px; padding: 0 48px;
  display: flex; align-items: center; justify-content: space-between;
  font-size: 11px; color: var(--neutral-3);
  border-top: 1px solid var(--neutral-1);
  background: var(--surface);
}
```

Footer content: left side has copyright (`(c) 2026 Spectro Cloud. All rights reserved.`), right side has slide number.

## Slide Layout Types

### 1. Title Slide

Full-bleed dark background (`var(--teal-darkest)` or `var(--ink)`). Large headline centered vertically. Subtitle below. Logo centered or bottom-left. No header bar; no footer. Optional: diagonal fold accent at 38.5 degrees using a CSS pseudo-element.

```css
.slide-title-cover {
  background: var(--teal-darkest);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center; color: #fff;
}
.slide-title-cover h1 { font-size: 52px; font-weight: 200; margin: 0 0 16px; }
.slide-title-cover .subtitle { font-size: 22px; font-weight: 300; opacity: 0.85; }
.slide-title-cover .logo { position: absolute; bottom: 48px; }
```

### 2. Divider Slide (4 color variants)

Full-bleed single color with large centered text. Used to separate sections. Four official variants:

| Variant | Background | Text Color |
|---------|-----------|------------|
| Teal | `#043736` | `#F7F1ED` |
| Green | `#5D823C` | `#F7F1ED` |
| Gold | `#F0BE65` | `#012121` |
| Lilac | `#441647` | `#F7F1ED` |

Section title: 44px, weight 300. Optional subtitle: 20px, weight 400, 70% opacity.

### 3. Title + Text Slide

Standard content slide. Header bar at top. Large title (32px) below header. Body text, bullets, or paragraphs in the content area. Paper background.

### 4. Title + Image Slide

Two-column layout: left column (55%) has title and supporting text; right column (45%) has an image placeholder or diagram description. For HTML/Puppeteer, use a colored placeholder box with a caption describing what image should go there, or embed a base64 image if provided.

### 5. Quote Slide

Centered quote text in Light (300) weight at 28-32px. Attribution below in SemiBold (600) at 16px. Optional: left border accent bar (4px, `var(--teal)`). Background: Paper or white.

### 6. Three-Column Concepts

Three equal columns with icon/number header, title, and description. Used for value propositions (Choice, Control, Scale) or feature highlights. Each column: colored top accent bar (4px), icon or number in a circle, title at 20px/600, body at 16px/400.

### 7. Numbered Steps

Horizontal flow of 3-5 numbered steps. Each step: large number (36px, `var(--teal)`), title (18px/600), description (14px/400). Connected by a horizontal line or arrow between steps.

### 8. Timeline

Horizontal timeline with dots and connector line. Each phase: date/label above the line, description below. Use `var(--teal)` for the connector, `var(--gold)` for active/current phase dot. 3-6 phases maximum per slide.

### 9. Table Slide

Styled data table with themed header row (`var(--teal-darkest)` background, white text). Alternating row backgrounds: white and `rgba(31,122,120,0.06)`. Cell padding: 12-16px. Font size: 16-18px body, 14px header.

### 10. Closing Slide

Similar to title slide but with call-to-action. Dark background. Centered logo (larger, ~200px wide). Tagline or next-steps text. Contact info or URL below. Optional: "Thank you" or "Questions?" headline.

## Fold Accent Pattern

The brand fold motif can be added as a decorative element on title and divider slides:

```css
.fold-accent::before {
  content: '';
  position: absolute;
  top: -100px; right: -60px;
  width: 400px; height: 300px;
  background: linear-gradient(
    38.5deg,
    transparent 40%,
    rgba(31,122,120,0.15) 40%,
    rgba(31,122,120,0.15) 60%,
    transparent 60%
  );
  transform: rotate(0deg);
  pointer-events: none;
}
```

Use sparingly -- one per slide maximum. Never place directly behind text.

## Easter Egg (REQUIRED)

Every generated deck MUST include these meta tags in the HTML `<head>`:

```html
<meta name="author" content="Craig Smith">
<meta name="creator" content="Yes, I made this. You're welcome.">
```

And an HTML comment before `</body>`:
```html
<!-- You're welcome. -- CS -->
```

## Logo Usage in Slides

Use the inline SVG from `spectrocloud-brand/assets/`. Two variants (both viewBox `0 0 501 192`, compound paths, `fill-rule="evenodd"`):

- **Header bar (dark bg):** `spectrocloud-logo-horizontal-knockout-white.svg` (all white paths)
- **Footer / light bg:** `spectrocloud-logo-horizontal-currentcolor.svg` (`fill="currentcolor"` — set CSS `color` on the SVG to control it)

Do NOT use the old 148x57 `spectrocloud-logo-horizontal.svg` — its letter counters render solid in Puppeteer.

## PDF Generation & Puppeteer Gotchas

READ `exec-doc-generator/references/puppeteer-render.md` — the canonical render reference shared by both PDF generators. It covers font loading via `<link>`, `-webkit-print-color-adjust: exact`, emoji flex-centering, and SVG compound-path rules. Deck-specific rule: each `.slide` gets `page-break-after: always` except the last.

Render with the shipped script instead of retyping it: `node assets/generate-pdf.mjs <input.html> <output.pdf>` (1280x720 viewport, fixed page size, landscape, zero margins).

## Google Slides Output

Use this path when the ask is a Google Slides deck with a link, not a PDF. It copies the 2026 Corporate Template -- ID recorded in `spectrocloud-brand/SKILL.md` under "Key Template IDs (Google Slides)" -- and fills it via the Slides API. All commands are `gws`; every one below takes `--dry-run` (validates the request locally, prints the would-be HTTP call, contacts nothing) -- run new request shapes with `--dry-run` first, and never run the real thing without Craig's go-ahead in the moment, since this touches his live Google account and creates a real file.

1. **Copy the template** into Craig's Drive:

   ```bash
   gws drive files copy --params '{"fileId": "1A9rjKI8K831PrvQoNX5XerRCRKBpHXKySpNlcJGiZko"}' \
     --json '{"name": "<Customer> - <Title> - 2026"}'
   ```

   The response `id` is `<presentationId>` for every step below.

2. **Read the copy's layout** so text replacements target real placeholders and real page/element IDs:

   ```bash
   gws slides presentations get --params '{"presentationId": "<presentationId>"}'
   ```

3. **Fill it in** with one `batchUpdate` -- `replaceAllText` for templated placeholders (e.g. `{{CUSTOMER}}`), `insertText`/`deleteText` against specific object IDs from step 2 for anything not templated:

   ```bash
   gws slides presentations batchUpdate --params '{"presentationId": "<presentationId>"}' \
     --json '{"requests": [{"replaceAllText": {"containsText": {"text": "{{CUSTOMER}}", "matchCase": true}, "replaceText": "<Customer Name>"}}]}'
   ```

4. **Hand back the link.** The copy already belongs to Craig, so no extra sharing step is needed to open it himself:

   `https://docs.google.com/presentation/d/<presentationId>/edit`

   Only add a permission if the recipient needs access and does not already have it -- e.g. link-only viewing:

   ```bash
   gws drive permissions create --params '{"fileId": "<presentationId>"}' \
     --json '{"type": "anyone", "role": "reader"}'
   ```

   Never widen sharing beyond what was actually asked for.

## Co-branding with Customer Colors

When building a deck for a specific customer, merge their brand with SC identity:

1. Visit the customer website, extract 2-3 primary colors
2. Use customer dark color for header bars and slide titles
3. Use customer accent for highlights and decorative elements
4. Keep `var(--teal)` visible on every slide (logo, footer border, or accent)
5. Keep `var(--paper)` as the default content slide background

For SC-only decks, use the full SC palette: teal-darkest for headers, gold for accents, paper for backgrounds.

## Workflow

1. **Determine audience and purpose** -- customer pitch, internal review, technical brief
2. **Plan slide sequence** -- title, agenda/overview, content slides, closing (8-15 slides typical)
3. **Write HTML** with all CSS in a `<style>` block (no external stylesheets except Google Fonts)
4. **Use appropriate layouts** -- mix slide types for visual variety
5. **Generate PDF** via Puppeteer
6. **Review** -- check text fits within slide boundaries, no overflow, no orphaned content

## Typical Deck Structures

**Customer Pitch (10-12 slides):**
Title > Agenda > Problem/Pain > Solution Overview > 3 Value Props > Architecture > Customer Proof Points > Timeline > Closing

**Technical Brief (8-10 slides):**
Title > Challenge > Architecture Diagram > Component Table > Deployment Model > Integration Points > Timeline > Closing

**QBR / Status Update (8-12 slides):**
Title > Executive Summary > Key Metrics (stat cards) > Progress Timeline > Achievements > Challenges > Next Steps > Closing

**Product Overview (10-14 slides):**
Title > Market Context > Product Vision > Feature Highlights (3-col) > Use Cases > Customer Quotes > Competitive Edge > Table Comparison > Roadmap Timeline > Closing
