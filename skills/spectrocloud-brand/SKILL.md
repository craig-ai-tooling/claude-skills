---
name: spectrocloud-brand
description: "The authoritative Spectro Cloud 2025 brand foundation -- exact hex colors (Tranquil Teal, Paper, Ink), Plus Jakarta Sans typography, logo files and usage rules, product naming (Palette, VerteX, VMO), messaging, tagline and tone. Read this before choosing any color, font, logo or tagline for a customer-facing or internal deliverable -- deck, PDF, doc, web page, dashboard or demo app -- and whenever Craig says: make it spectro branded, use our branding, use our colors, what is our logo / tagline / positioning, co-brand this with the customer's colors. Never hand-roll Spectro colors, fonts or messaging without reading this first."
---

# Spectro Cloud Brand Foundation (2025 Rebrand)

Single source of truth for Spectro Cloud visual identity, messaging, and design principles. Other skills (exec-doc-generator, slide-deck-generator, web UI, etc.) should READ this skill for brand details rather than maintaining their own copies.

## When to Use

- Building any customer-facing or internal document, presentation, or web UI
- Need to reference brand colors, logos, typography, or messaging
- Checking correct brand tone, terminology, or visual treatment
- Co-branding materials with customer colors alongside SC identity

## Brand Identity

### Mission

Spectro Cloud's mission is to help organizations simplify their IT infrastructure in order to unlock innovation at scale. Kubernetes is the critical enabler.

### Vision

Be the universal platform orchestrator for modern enterprise IT infrastructure: for every application, in every environment, from far edge to hyperscale cloud.

### Tagline

**"Simplicity that unlocks innovation at scale"**

Turning chaos and complexity into effortless control to help businesses realize their true potential.

### Company Overview

- Founded 2019 by CEO Tenry Fu, VP Engineering Gautam Joshi, CTO Saad Malik
- Series C (late 2024)
- Products: **Palette** (K8s management), **Palette VerteX** (gov/regulated), **PaletteAI**, **Palette VMO** (VM orchestrator)
- Position: mature technology scale-up, NOT a startup

## Design Principles

The 2025 rebrand is built around **the fold** -- inspired by origami:

1. **Simplicity and elegance** -- clean geometric shapes, neat layouts, open space
2. **Control and repeatability** -- tessellations, lattice patterns, repeating shapes (like Cluster Profiles)
3. **Choice, flexibility and versatility** -- origami metaphor: from a simple sheet of paper, endless variety through folding and layering; broad color palette
4. **Trusted platform** -- no cartoons, no off-the-shelf illustrations, no rough edges; platform front-and-center, not people

### The Fold

- Core brand expression: diagonal folded ribbons at **38.5 degrees** (matching the logo Strata mark)
- Color blocking with monochromatic shifts to mimic folding depth
- Crease patterns (thin lines, 0.5-2pt weight) inspired by origami unfolding
- Print patterns inspired by Japanese geometric patterns (evoke structure, consistency, "blueprint" metaphor)
- Do NOT use multiple folded ribbons on a single page ("confetti streamers" effect)
- Do NOT use heavy patterning directly behind text or logos

### Animation Principles (for web/motion)

- Clean, simple, crisp without being sharp
- Tactile, gentle, smooth -- NOT bouncy, playful, mechanical, or fluttery
- Folding/origami motifs with implied 3D through perspective (not drop shadows)
- Typography animation adds emphasis/clarity, never character-by-character
- Product UI demos: let the feature be the star, simplify surrounding elements

## Color Palette

READ `references/colors.md` for the full palette with hex codes, RGB, CMYK, Pantone, overlap colors, neutrals, and accessibility contrast grid.

### Quick Reference

| Name | Hex | Role |
|------|-----|------|
| **Tranquil Teal** | `#1F7A78` | Primary brand color, logo, SC identity |
| Dark Teal | `#005B5B` | Darker teal variant |
| Darkest Teal | `#043736` | Deep teal for strong contrast |
| **Tea Green** | `#9EB277` | Secondary, softer accents |
| **Gold Leaf** | `#F0BE65` | Warm accent, highlights |
| **Sunset Orange** | `#B94B01` | Warm accent, callouts |
| **Soft Lilac** | `#7E5C8E` | Palette product accent |
| **Paper** | `#F7F1ED` | Brand background (warm cream) — NEVER use `#fff`/white as page background |
| **Ink** | `#012121` | Brand text (deep teal-black) |

### Product Colors

| Product | Accent Color | Notes |
|---------|-------------|-------|
| Spectro Cloud | Teal `#1F7A78` | Master brand |
| Palette | Purple `#7E5C8E` / `#441647` | P letterform logo |
| VerteX | Green `#9EB277` / `#5D823C` | V letterform logo |
| Government | Green (VerteX green) | "GOVERNMENT" subhead in all caps |

## Typography

- **Typeface:** Plus Jakarta Sans (Google Fonts, open source)
- **Fallback:** Trebuchet MS
- **Import:** `wght@200;300;400;500;600;700;800`

| Use | Weight | Name |
|-----|--------|------|
| Display headlines | 200 | ExtraLight |
| Subheads | 500 | Medium |
| Body copy | 400 | Regular |
| Quotes | 300 | Light |
| Labels / UI | 600 | SemiBold |
| Compact docs (PDFs) | 700-800 | Bold/ExtraBold (for legibility at small sizes) |

### Text/Background Contrast Rules

On **Paper (#F7F1ED)** backgrounds, these colors pass WCAG AA:
- Dark Lilac `#441647` (12.92:1), Dark Teal `#043736` (11.69:1), Dark Orange `#851A01` (8.74:1)
- Teal `#1F7A78` and Lilac `#7E5C8E` pass AA for large text (4.93:1)

On **Ink (#012121)** backgrounds:
- Gold `#F0BE65` (9.88:1), Green `#9EB277` (7.32:1), Dark Gold `#DE8D2A` (6.41:1)
- Orange `#B94B01` and Lilac pass AA large only (~3.3:1)

## Logos

SVG logo files are in `assets/`. Key variants:

| File | Use |
|------|-----|
| `spectrocloud-logo-horizontal-currentcolor.svg` | Light backgrounds. `fill="currentcolor"`, viewBox `0 0 501 192`, compound paths — safe for Puppeteer/PDF |
| `spectrocloud-logo-horizontal-knockout-white.svg` | All-white for dark backgrounds. Official knockout from Brand Drive, viewBox `0 0 501 192` |
| `spectrocloud-logo-horizontal.svg` | Old website SVG (viewBox `0 0 148 57`), full-color Strata. **Web use only — NEVER for Puppeteer/PDF** (separate paths per letter part; counters fill solid) |

### Logo Rules

- The symbol is called the **Strata** (inspired by origami, S-form, resembles Cluster Profile stack)
- Always use as part of horizontal or vertical logo (not standalone except for favicons/avatars)
- Horizontal logo is preferred; vertical only when horizontal space is limited
- Minimum size: 75px wide (horizontal), 36px wide (vertical)
- Clearspace: equal to the full height of the word "Spectro" on all sides
- Do NOT: recreate, recolor, rotate, distort, add effects, place on busy backgrounds, alter typeface
- **AI tools MUST use the provided SVG files** — never substitute text, initials, shapes, or placeholder graphics for the Strata mark

### Inline SVG Notes

- Wordmark paths use `currentcolor` -- set CSS `color` on the SVG element to control
- Footer usage: `color: var(--ink)` with `opacity: 0.6`
- Header (dark bg): use the knockout-white SVG (`fill="#fff"`)
- Always add `fill-rule="evenodd"` to prevent letter counter fill issues in Puppeteer/Chrome

## Messaging

READ `references/messaging.md` for full boilerplates, value props, customer quotes, and competitive positioning.

### Short Boilerplate

> Turn the chaos of Kubernetes into effortless control, whatever the shape of your business.
>
> Spectro Cloud delivers simplicity and control to organizations running Kubernetes at any scale. With its Palette platform, Spectro Cloud empowers businesses to deploy, manage, and scale Kubernetes clusters effortlessly -- from edge to data center to cloud -- while maintaining the freedom to build their perfect stack.

### Key Phrases

- "Simplicity that unlocks innovation at scale"
- "Turning chaos and complexity into effortless control"
- "For every application, in every environment, from far edge to hyperscale cloud"
- "Choice without the risk, control without complexity, scale without the overhead"

### Tone

- **Mature enterprise** -- we are a technology scale-up, not a startup
- **Platform-forward** -- put Palette/product front and center, not people
- **Real tech terms** -- don't shy away from Kubernetes, clusters, bare metal, edge
- **Pain-focused** -- reference pain points (complexity, drift, vendor lock-in) then benefits
- **No cartoons, no off-the-shelf illustrations** -- geometric shapes only

### Copyright

`© [Year] Spectro Cloud®. All rights reserved.`

For confidential docs: `© [Year] Spectro Cloud® Confidential. All rights reserved.`

## Brand Icons

SVG icons from the brand guide are in `assets/icons/`. These are the official brand icons -- use them instead of emojis or generic icon sets in branded materials.

**Documented exception:** compact Puppeteer-rendered PDF layouts (the `exec-doc-generator` track cards, stack strips, and verdict cards) use emoji glyphs for small in-card icons, because the 32x32 brand SVGs don't scale down legibly at those sizes and text abbreviations render inconsistently. That exception is deliberate and scoped to those components -- everywhere else, brand SVG icons win.

| Icon | File | Use |
|------|------|-----|
| Diamond | `Diamond.svg` | Simplicity, elegance, the fold |
| SquaresFour | `SquaresFour.svg` | Control, repeatability, grid |
| ShuffleAngular | `ShuffleAngular.svg` | Choice, flexibility |
| CheckSquare | `CheckSquare.svg` | Completion, success criteria |
| Ranking | `Ranking.svg` | Performance, scale |
| CirclesFour | `CirclesFour.svg` | Multi-environment, diversity |
| GitFork | `GitFork.svg` | Git ops, branching, development |
| Envelope | `Envelope.svg` | Communication, email |
| Shuffle | `Shuffle.svg` | Versatility, interconnection |
| SealCheck | `SealCheck.svg` | Trusted platform, certification |
| Sparkle | `Sparkle.svg` | Innovation, new features |
| Sliders | `Sliders.svg` | Configuration, control |
| Fingerprint | `Fingerprint.svg` | Security, identity |

Additional icons available in the Brand Drive `Guide assets/Icons/` folder (not yet downloaded): SlackLogo, GoogleDriveLogo

These icons use brand teal (`#1F7A78`) fills with Tea Green (`#9EB277`) opacity backgrounds. All are 32x32 viewBox.

## Google Drive Brand Assets

Official brand assets are in the **Spectro Brand 2025 Google Drive**:

| Folder | Contents |
|--------|----------|
| `_Spectro Cloud Logos/` | All SC, Palette, VerteX, PaletteAI logo variants (SVG, PNG, PDF, EPS, TIF) |
| `_Spectro Cloud Logos/00_Spectro Cloud/` | SC logos: horizontal, vertical, knockout, logomark, favicon, government |
| `_Spectro Cloud Logos/01_Palette/` | Palette product logos |
| `_Spectro Cloud Logos/02_Palette VerteX/` | VerteX product logos |
| `_Spectro Cloud Logos/03_PaletteAI/` | PaletteAI product logos |
| `Templates/` | Google Slides templates (2025, 2026, Government), datasheet/flyer Google Doc, email signatures |
| `Brand Guidelines/` | The official PDF brand guidelines document |
| `Typography/` | Plus Jakarta Sans font files |
| `Subbrands/` | Kairos, Hadron Linux, Elevate, Coffee+Containers, Partner badges, Product cert badges |
| `Animation/` | Animation guidelines doc, After Effects files, logo GIFs, Lottie JSON files |

### Key Template IDs (Google Slides)

- **2026 Corporate Template:** `1A9rjKI8K831PrvQoNX5XerRCRKBpHXKySpNlcJGiZko`
- **2026 Government Template:** `1v8Rrpwp88TmmBpHHi1WW5OJ9CekfrxWpOb7bLEJzmYU`
- **BDM Customer Presentation:** `14Z1B8ZnSrdcmWtLuvCYI__BclIEcb7T8ylCROb06cqU`
- **Datasheet/Flyer Template (Google Doc):** `1Yi6h0xyZg5Dh7b-kNVFuyKrR93KqR7B8I6QfCcV9k_4`

### Slide Layout Types (from 2026 template)

The official Google Slides templates include ~35 slide types:
- Title slides (2 variants), Agenda, Divider slides (4 color variants)
- Title + text, Title + image, Quote slide
- 3-column numbered concepts, concepts with boxes
- 5-item concept grid, step-by-step flows (horizontal numbered, 7-step)
- Timeline (phased with date markers), stages
- Tables, comparison layouts
- Text/background color combo guidance slide
- Closing slide with logo
